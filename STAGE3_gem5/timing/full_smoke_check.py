#!/usr/bin/env python3
"""full_smoke_check.py: is every L1D set full when the test starts under cache_setup `full`?
(wiki/design/SIMSPECT_HOOKS.md "Cache setup strategies").

    python3 full_smoke_check.py <timing_driver out dir> [--stage3 <code>/STAGE3_gem5] [--json out.json]

For every record of the run that kept a trace (traces/<mode>/<stem>.pipeview.txt.gz; run
timing_driver.py with --keep-work or look at hits), it replays the SimSpect L1D hook events
(`fill` sets set/way, `evict` frees the victim's set/way) up to the test start (= the latest
retire tick of an instruction inside the cache_setup block [begin, begin+delta) from the record's
cache_setup_info) and reports:
  occ_min/occ_max   valid ways per set at test start (full = assoc in every set)
  sets_full         sets with all ways valid / number of sets seen in the config
  occupancy is the state the setup leaves: a replay of the L1D events whose actor is the prologue
  (pc < begin) or the setup block only, so late fills (InvisiSpec exposes after retire) count
  setup_fills       L1D fills by setup-block instructions (late_setup_fills: after test start)
  test_fills / test_fills_with_evict   L1D fills after test start, and how many evicted a line
  setup_specld_evicts   L1D evicts with req=specld whose actor pc is in the setup block
                        (a UV1-shaped event caused by the sweep, not by the test)
  test_specld_evicts    the same for actors outside the block
  ann_ok            status ok/hit, no error, xmit PC resolved (cache_setup.prepare already verified
                    every annotation address; a failure there is a per-record error)
Log: prints one line per record and a summary; no files changed except --json.
"""
import argparse, collections, gzip, json, os, shutil, sys, tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--stage3", default="/tests/simspect_alloy_20261108/code_20261109/STAGE3_gem5")
    ap.add_argument("--assoc", type=int, default=8)
    ap.add_argument("--sets", type=int, default=64)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    sys.path.insert(0, a.stage3)
    os.environ.pop("SIMSPECT_CACHE_SETUP", None)
    import gem5_common as gc
    out = Path(a.out)
    rows = []
    for gz in sorted((out / "traces").glob("*/*.pipeview.txt.gz")):
        mode, stem = gz.parent.name, gz.name.split(".")[0]
        rawf = out / "raw" / mode / f"{stem}.json"
        if not rawf.exists():
            continue
        raw = json.loads(rawf.read_text())
        info = raw.get("cache_setup_info") or {}
        if raw.get("cache_setup") != "full" or "begin" not in info:
            continue
        begin = int(info["begin"], 16)
        end = begin + int(info["delta"])
        fd, tp = tempfile.mkstemp(suffix=".pipeview.txt")
        with gzip.open(gz, "rb") as fi, os.fdopen(fd, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        try:
            evs = gc.parse_simspect_events(Path(tp))
            byseq = gc.parse_pipeview_by_seq(Path(tp))
        finally:
            os.unlink(tp)
        t0 = max((r["retire"] for r in byseq.values() if begin <= r["pc"] < end and r["retire"]),
                 default=None)

        def pc_of(e):
            pc = e.get("pc")
            if isinstance(pc, str) and pc.startswith("0x"):
                return int(pc, 16)
            try:
                return byseq[int(e.get("seq"))]["pc"]
            except Exception:
                return None

        def actor(e):   # pre = prologue/_start, setup = the cache_setup block, test = the rest
            pc = pc_of(e)
            if pc is None:
                return "pre" if (t0 is None or e["tick"] <= t0) else "test"
            return "pre" if pc < begin else ("setup" if pc < end else "test")

        r = dict(mode=mode, stem=stem, t0=t0, setup_fills=0, late_setup_fills=0, test_fills=0,
                 test_fills_with_evict=0, setup_specld_evicts=0, test_specld_evicts=0,
                 ann_ok=bool(raw.get("xmit_pc")) and raw.get("status") in ("ok", "hit")
                 and not raw.get("error"), status=raw.get("status"),
                 hit=bool(raw.get("issued_in_window")))
        # same tick: the victim's evict before the replacing fill (their ids can come in either order)
        l1d = sorted((e for e in evs if e.get("struct") == "L1D" and e.get("kind") in ("fill", "evict")),
                     key=lambda e: (e["tick"], e["kind"] != "evict", e["id"]))
        # state the setup leaves = replay of the prologue's and the setup block's own events only
        ways = collections.defaultdict(dict)
        evict_at = collections.defaultdict(int)   # (tick, set) -> evicts
        for e in l1d:
            if not (str(e.get("set")).isdigit() and str(e.get("way")).isdigit()):
                continue
            st, wy, who = int(e["set"]), int(e["way"]), actor(e)
            if e["kind"] == "evict":
                evict_at[(e["tick"], st)] += 1
                if e.get("req") == "specld":
                    r["setup_specld_evicts" if who == "setup" else "test_specld_evicts"] += 1
            if who == "test":
                if e["kind"] == "fill":
                    r["test_fills"] += 1
                    r["test_fills_with_evict"] += bool(evict_at.get((e["tick"], st)))
                continue
            if e["kind"] == "fill":
                ways[st][wy] = e.get("line")
                if who == "setup":
                    r["setup_fills"] += 1
                    r["late_setup_fills"] += bool(t0 is not None and e["tick"] > t0)
            else:
                ways[st].pop(wy, None)
        snap = {s: len(w) for s, w in ways.items()}
        occ = [snap.get(s, 0) for s in range(a.sets)]
        r.update(occ_min=min(occ), occ_max=max(occ), sets_full=sum(o >= a.assoc for o in occ),
                 short_sets={s: sorted(ways.get(s, {}).values()) for s in range(a.sets)
                             if occ[s] < a.assoc})
        rows.append(r)
        print(json.dumps(r))
    n = len(rows)
    summ = dict(records=n, all_sets_full=sum(r["sets_full"] == a.sets for r in rows),
                ann_ok=sum(r["ann_ok"] for r in rows),
                test_fills=sum(r["test_fills"] for r in rows),
                test_fills_with_evict=sum(r["test_fills_with_evict"] for r in rows),
                setup_specld_evicts=sum(r["setup_specld_evicts"] for r in rows),
                test_specld_evicts=sum(r["test_specld_evicts"] for r in rows))
    print("SUMMARY", json.dumps(summ))
    if a.json:
        Path(a.json).write_text(json.dumps(dict(summary=summ, rows=rows), indent=1) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""stl_footprint_offline.py — question (d) of the STL port (2026-11-09, stl-port):
what does today's STAGE3_gem5/check_footprint.py say on an stl_bypass test?

Runs check_footprint.evaluate_trace UNCHANGED, offline (no gem5), on the traces that
stl_hooktest_amulet.py kept, with the same inputs process_one would give it for an
stl_bypass test: lc_pc = the ann's last_committed (absent in these tests), fnc_pc =
the ann's first_noncommitted (= the held store S here), unresolved = [] (the STL
models have no unresolved branch; the xmit branch is excluded as in process_one),
the criterion JSON, and the scheme from the run's gem5 flags. Then it sorts every
offending event the checker reports by (i) who did it: the litmus program's
transient instance (L, the transmitter, or another litmus load the STL squash
removed) or something else (harness epilogue / wrong-path re-fetch after the exit
syscall / an instance squashed by another squash), and (ii) when: inside the STL
window [stl_hold, mem_order_squash] or outside it.
Usage: stl_footprint_offline.py <driver.json> <keepdir> <criterion.json> <out.json>
Env: SIMSPECT_HARNESS (dir holding STAGE3_gem5/ with check_footprint.py).
"""
import collections, gzip, json, os, shutil, sys, tempfile
from pathlib import Path

HARNESS = Path(os.environ.get("SIMSPECT_HARNESS", "/tests/simspect"))
sys.path.insert(0, str(HARNESS / "STAGE3_gem5"))
import check_footprint as cf  # noqa: E402
import gem5_common as gc  # noqa: E402

TESTS = Path("/tests/simspect/testsets/STT_6_stl/stl_bypass/ann")


def main():
    drv, keep, crit_p, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    d = json.loads(drv.read_text())
    crit = cf.load_criterion(crit_p)
    extra = [a for a in (d["env"].get("SIMSPECT_GEM5_EXTRA") or "").split("\x1f") if a]
    scheme = cf.scheme_name_from_args(extra, 2)
    mode = cf.select_actor_mode(crit, scheme, None)
    rows = []
    tmp = Path(tempfile.mkdtemp(prefix="stlfp_"))
    try:
        for r in d["records"]:
            if r.get("status") != "ok" or not (keep / r["name"] / "pipeview.txt.gz").exists():
                continue
            ann = json.loads((TESTS / f"{r['name']}.ann.json").read_text())
            delta = int((r.get("cache_setup_info") or {}).get("delta") or 0)
            cb = ann.get("commit_boundary", {})
            lc = cb.get("last_committed", {}).get("addr")
            fnc = cb.get("first_noncommitted", {}).get("addr")
            tr = tmp / "pipeview.txt"
            with gzip.open(keep / r["name"] / "pipeview.txt.gz", "rb") as f, open(tr, "wb") as g:
                shutil.copyfileobj(f, g)
            res = cf.evaluate_trace(tr, crit, lc + delta if lc else None, fnc + delta if fnc else None,
                                    [], 500, actor_mode=mode, scheme_name=scheme)
            evs = {e["id"]: e for e in gc.parse_simspect_events(tr) if e["id"] is not None}
            lit = set(r.get("litmus_loads_issued") or []) | {r.get("l_first")} | {(r.get("x") or {}).get("seq")}
            lit.discard(None)
            th, tq = r.get("t_hold"), r.get("t_squash")
            cls = collections.Counter()
            for o in res.get("offending", []):
                for i in o.get("event_ids", []):
                    e = evs.get(i)
                    if e is None:
                        continue
                    who = "litmus" if e["seq"] in lit else "other"
                    when = "in_stl_window" if (th is not None and tq is not None and th <= e["tick"] <= tq) else "outside_stl_window"
                    cls[f"{who}/{when}"] += 1
            rows.append(dict(name=r["name"], valid_relaxed=r.get("valid_relaxed"), leak=res.get("leak"),
                             issued_in_window=res.get("issued_in_window"), terms=res.get("terms_fired"),
                             fnc_retire=res.get("fnc_retire"), lc_retire=res.get("lc_retire"),
                             t_hold=th, t_squash=tq, offending_events=dict(cls),
                             status=res.get("status", "ok"), error=res.get("error")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    v = [x for x in rows if x["valid_relaxed"]]
    summ = dict(driver=str(drv), criterion=crit_p, scheme=scheme, actor_mode=mode, n=len(rows),
                n_valid=len(v), leak=sum(1 for x in rows if x["leak"]),
                leak_on_valid=sum(1 for x in v if x["leak"]),
                leak_with_litmus_event_in_stl_window=sum(1 for x in rows if x["offending_events"].get("litmus/in_stl_window")),
                leak_only_from_other_or_outside=sum(1 for x in rows if x["leak"] and not x["offending_events"].get("litmus/in_stl_window")),
                offending_event_classes=dict(sum((collections.Counter(x["offending_events"]) for x in rows), collections.Counter())),
                fnc_retire_after_squash=sum(1 for x in v if x["fnc_retire"] and x["t_squash"] and x["fnc_retire"] > x["t_squash"]),
                no_lc=sum(1 for x in rows if not x["lc_retire"]))
    out.write_text(json.dumps(dict(summary=summ, rows=rows), indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()

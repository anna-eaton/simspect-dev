#!/usr/bin/env python3
"""classify_hits.py: attribute each hit of a timing_driver.py campaign to known
bug signatures, then compute time-to-first-detection (timing-amulet, 2026-11-09).

    python3 classify_hits.py <timing_out_dir> --defense invisispec|cleanupspec|speclfb|stt \
        [--stage3 /tests/simspect_alloy_20261108/code_20261109/STAGE3_gem5]

Signatures (every one reuses an existing, documented rule; a hit can carry several):
  InvisiSpec  UV1        some in-window offending event (the checker's `offending` event ids) is
                         `L1D:evict` with req=specld (AMULET_BUGS_DETECTION_ACCOUNTING.md §2 UV1 row).
              UV1_transient  (2026-11-09, extra, reported beside UV1) such an event whose actor never
                         became visible (offending item vp[seq] = inf: a squashed load).
              other_<struct>  hit whose offending items include no such event (listed by struct).
  CleanupSpec UV4 / UV5 / CS1 / EM_upgrade / unattributed: the per-item causes of
                         STAGE3_gem5/triage/cleanupspec_skip_evidence.py (run unchanged on a shim
                         campaign layout); UV3 is not reachable here (no RMW transmitter in the testset).
  SpecLFB     UV6 (rank-0 speculative load, `uv6_first`), walk_order, jmp_shadow: the per-event tags of
                         speclfb_analyze.py (vendored helpers/analyze.py) after triage.py's disqualifier
                         (in-window events whose req is not ld are dropped).
  STT         S1_xmm4 (firstdet-simspect, 2026-11-09): the transmitter's backward register slice touches
                         %xmm4 (triage/diag/_fv2_slice.transmitter_slice, the static half of
                         diag_stt_xmm4_skip.py; the GPR-twin half is replaced by the parity baseline: T4 on
                         STT_6_fv2, GPR only, hit 0/1000). Needs --testset. Other hits: other_stt. A hit
                         whose record has data_obtained == False (check_ld's canonical data-obtained gate)
                         is `disq_not_obtained(<cache_fate>)`, not a detection.
  H-PAD exclusion (firstdet-simspect, 2026-11-09; Anna's decision in URGENT_TODO "DECIDED 2026-11-09"):
                         with --testset, an event whose instruction PC (event pc, else its seq's pipeview pc)
                         is at or past the end of .text is the harness zero padding (`00 00` = add %al,(%rax),
                         reached by wrong-path fetch in mispredict_taken), not the generated test. A target
                         signature carried only by such events becomes `excluded_HPAD:<sig>` (not counted).
                         .text end = objdump -h of the test rebuilt warm (gem5_common.build_binary) plus the
                         record's cache_setup_info.delta when a cache_setup rewrote it.

  SETUP exclusion (cache-full, 2026-11-09): for a record run with cache_setup `full`, an offending event
                         whose actor PC (event pc, else its seq's pipeview pc) lies inside the setup block
                         [cache_setup_info.begin, +delta) is the harness's own L1D sweep (committed plain loads;
                         with no lc instruction the window starts at tick 0, and on InvisiSpec-Futuristic those
                         loads issue as speculative loads whose evictions look like UV1). Such events are removed
                         from the record's offending items before any rule runs (strip_setup); a target signature
                         carried only by them becomes `excluded_SETUP:<sig>`, and a hit with no other offending
                         event is `excluded_SETUP:no_test_event`. Not applied to warm/cold/random records, so earlier
                         rows reproduce unchanged.

Writes <out>/classes.jsonl (one row per hit: idx, mode, stem, sigs) and <out>/first_detection.json:
per signature, the first idx (0-based order position) whose test carries it, tests-to-first =
idx+1 among tests attempted in order, cumulative gem5 CPU s and total harness CPU s over idx 0..first,
K (tests with the signature) of N (tests finished in the contiguous prefix), and the rate-based
expectation (N+1)/(K+1). Log: <out>/classify.log.
"""
import argparse, collections, gzip, json, os, shutil, subprocess, sys, tempfile, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = {"invisispec": ["UV1", "UV1_transient"], "cleanupspec": ["UV4", "UV3", "UV5"],
           "speclfb": ["UV6", "walk_order", "jmp_shadow"], "stt": ["S1_xmm4"]}


def text_end(testset: Path, mode: str, stem: str, raw: dict, gc) -> int:
    """End of .text of the binary that ran (see H-PAD in the docstring)."""
    import re
    s = testset / mode / "asm" / f"{stem}.s"
    with tempfile.TemporaryDirectory(prefix="hpad_") as td:
        b = gc.build_binary(s, Path(td), cache_setup_ok=True)
        out = subprocess.check_output(["objdump", "-h", str(b)], text=True)
    m = re.search(r"^\s*\d+\s+\.text\s+([0-9a-f]+)\s+([0-9a-f]+)", out, re.M)
    end = int(m.group(2), 16) + int(m.group(1), 16)
    return end + int((raw.get("cache_setup_info") or {}).get("delta") or 0)


def ev_pc(e, byseq):
    pc = e.get("pc")
    if isinstance(pc, int):
        return pc
    if isinstance(pc, str) and pc.startswith("0x"):
        return int(pc, 16)
    seq = e.get("seq")
    try:
        seq = int(seq) if seq is not None else None
    except (TypeError, ValueError):
        seq = None
    r = byseq.get(seq) if seq is not None else None
    return r["pc"] if r else None


def is_pad(e, byseq, tend):
    pc = ev_pc(e, byseq)
    return tend is not None and pc is not None and pc >= tend


def strip_setup(raw, pv, gc):
    """-> (raw with setup-block events removed from `offending`, n events removed). See SETUP above."""
    info = raw.get("cache_setup_info") or {}
    if raw.get("cache_setup") != "full" or "begin" not in info:
        return raw, 0
    b = int(info["begin"], 16)
    e_ = b + int(info["delta"])
    evs = {x["id"]: x for x in gc.parse_simspect_events(pv)}
    byseq = gc.parse_pipeview_by_seq(pv)

    def in_setup(i):
        x = evs.get(i)
        pc = ev_pc(x, byseq) if x else None
        return pc is not None and b <= pc < e_

    new = dict(raw)
    items, removed = [], 0
    for o in raw.get("offending") or []:
        ids = o.get("event_ids") or []
        keep = [i for i in ids if not in_setup(i)]
        removed += len(ids) - len(keep)
        if not keep and ids:
            continue
        o2 = dict(o, event_ids=keep)
        kseq = set()
        for i in keep:
            try:
                kseq.add(int(evs[i].get("seq")))
            except (KeyError, TypeError, ValueError):
                kseq = None
                break
        if kseq is not None and len(keep) < len(ids):
            o2["seqs"] = [q for q in o.get("seqs") or [] if q in kseq]
            if isinstance(o.get("vp"), dict):
                o2["vp"] = {k: v for k, v in o["vp"].items() if str(k).isdigit() and int(k) in kseq}
        items.append(o2)
    new["offending"] = items
    return new, removed


def with_setup_exclusion(fn, raw, pv, gc, targets):
    """Run signature function fn(raw') on the setup-stripped record; tag targets lost to the strip."""
    raw2, n = strip_setup(raw, pv, gc)
    if not n:
        return fn(raw)
    if not raw2["offending"]:
        lost = {x for x in fn(raw) if x in targets}
        return {"excluded_SETUP:no_test_event"} | {f"excluded_SETUP:{x}" for x in lost}
    got = fn(raw2)
    lost = {x for x in fn(raw) if x in targets} - got
    return got | {f"excluded_SETUP:{x}" for x in lost}


def load_rows(out: Path):
    rows = {}
    for l in (out / "results.jsonl").read_text().splitlines():
        try:
            r = json.loads(l)
            rows[r["idx"]] = r
        except Exception:
            pass
    return rows


def gunzip_tmp(gz: Path) -> Path:
    fd, p = tempfile.mkstemp(suffix=".pipeview.txt")
    with gzip.open(gz, "rb") as fi, os.fdopen(fd, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    return Path(p)


def sigs_invisispec(raw, pv, gc, tend=None):
    evs = {e["id"]: e for e in gc.parse_simspect_events(pv)}
    byseq = gc.parse_pipeview_by_seq(pv) if tend is not None else {}
    sigs, structs, padded = set(), set(), False
    for o in raw.get("offending") or []:
        structs.add(o.get("struct"))
        vp = o.get("vp") or {}
        for i in o.get("event_ids") or []:
            e = evs.get(i)
            if e and e["struct"] == "L1D" and e["kind"] == "evict" and e.get("req") == "specld":
                if is_pad(e, byseq, tend):
                    padded = True
                else:
                    sigs.add("UV1")
                    # UV1_transient (cache-full, 2026-11-09; reported next to UV1, never instead of
                    # it): the evicting load never became visible (checker vp = inf, "never"),
                    # i.e. a squashed/transient load, not a load that later committed.
                    v = vp.get(str(e.get("seq")))
                    if isinstance(v, list) and v and v[0] == float("inf"):
                        sigs.add("UV1_transient")
    if padded and "UV1" not in sigs:
        sigs.add("excluded_HPAD:UV1")
    if not sigs:
        sigs |= {f"other_{s}" for s in sorted(structs, key=str)}
    return sigs


def _speclfb_tagsigs(tags):
    sigs = set()
    if "uv6_first" in tags:
        sigs.add("UV6")
    if "walk_order" in tags or any("walk_order" in t for t in tags):
        sigs.add("walk_order")
    if any(t.startswith("jmp_shadow") for t in tags):
        sigs.add("jmp_shadow")
    return sigs


def sigs_speclfb(raw, pv, mode, an, gc=None, tend=None):
    a = an.analyze(raw, str(pv), mode)
    good = [c for c in a.get("causes") or [] if c["ev"].get("req") in ("ld",)]
    if tend is not None:
        byseq = gc.parse_pipeview_by_seq(pv)
        pad = [c for c in good if is_pad(c["ev"], byseq, tend)]
        good = [c for c in good if not is_pad(c["ev"], byseq, tend)]
        excl = _speclfb_tagsigs({c["tag"] for c in pad}) - _speclfb_tagsigs({c["tag"] for c in good})
    else:
        excl = set()
    tags = {c["tag"] for c in good}
    sigs = {f"excluded_HPAD:{x}" for x in excl}
    if "uv6_first" in tags:
        sigs.add("UV6")
    if "walk_order" in tags or any("walk_order" in t for t in tags):
        sigs.add("walk_order")
    if any(t.startswith("jmp_shadow") for t in tags):
        sigs.add("jmp_shadow")
    if not sigs:
        sigs.add("other:" + ("+".join(sorted(tags)) if tags else "disq_non_load_footprint"))
    return sigs


def cleanupspec_all(out: Path, hits, log):
    setup_stripped = {}   # key -> True when no offending item survived the SETUP strip
    shim = out / "cs_evidence"
    shutil.rmtree(shim, ignore_errors=True)
    for r in hits:
        rawf = out / "raw" / r["mode"] / f"{r['stem']}.json"
        if not rawf.exists():
            continue
        d = shim / r["mode"] / "_sweep_raw"
        d.mkdir(parents=True, exist_ok=True)
        rec = json.loads(rawf.read_text())
        rec.pop("workdir", None)
        gz0 = out / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
        if rec.get("cache_setup") == "full" and gz0.exists():   # SETUP exclusion (cache-full)
            import gem5_common as gc
            pv = gunzip_tmp(gz0)
            try:
                rec, n = strip_setup(rec, pv, gc)
            finally:
                pv.unlink(missing_ok=True)
            if n:
                setup_stripped[f"{r['mode']}/{r['stem']}"] = not rec["offending"]
                log.write(f"SETUP-strip {r['mode']}/{r['stem']}: {n} events removed, "
                          f"{len(rec['offending'])} items left\n")
        (d / f"{r['stem']}.json").write_text(json.dumps([rec]))
        td = shim / "diagnostics" / "traces" / r["mode"]
        td.mkdir(parents=True, exist_ok=True)
        gz = out / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
        if gz.exists():
            (td / gz.name).symlink_to(gz)
    p = subprocess.run([sys.executable, str(HERE / "cleanupspec_skip_evidence.py"), str(shim)],
                       capture_output=True, text=True)
    log.write(f"cleanupspec_skip_evidence rc={p.returncode}\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}\n")
    ev = json.loads((shim / "diagnostics" / "cleanupspec_skip_evidence.json").read_text())
    name = {"UV4_split": "UV4", "UV5_older_load": "UV5", "CS1_older_store_upgrade": "CS1",
            "EM_upgrade_squashed": "EM_upgrade", "unattributed": "unattributed"}
    res = {k: {name.get(c, c) for c in v.get("causes", [])} for k, v in ev.items()}
    for k, only in setup_stripped.items():
        if only:
            res[k] = {"excluded_SETUP:no_test_event"}
    return res


def _classify_one(w):
    """One invisispec/speclfb hit -> (idx, sigs, error log text). Module level so --jobs can fork it."""
    r, out, testset, defense = w
    import gem5_common as gc
    an = None
    if defense == "speclfb":
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))
        import speclfb_analyze as an
    gz = out / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
    rawf = out / "raw" / r["mode"] / f"{r['stem']}.json"
    if not gz.exists() or not rawf.exists():
        return r["idx"], {"no_trace"}, ""
    pv = gunzip_tmp(gz)
    try:
        raw = json.loads(rawf.read_text())
        tend = text_end(testset, r["mode"], r["stem"], raw, gc) if testset else None
        fn = ((lambda x: sigs_invisispec(x, pv, gc, tend)) if defense == "invisispec"
              else (lambda x: sigs_speclfb(x, pv, r["mode"], an, gc, tend)))
        return r["idx"], with_setup_exclusion(fn, raw, pv, gc, TARGETS[defense]), ""
    except Exception:
        return r["idx"], {"classify_error"}, \
            f"ERROR idx={r['idx']} {r['mode']}/{r['stem']}\n{traceback.format_exc()}\n"
    finally:
        pv.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--defense", required=True, choices=["invisispec", "cleanupspec", "speclfb", "stt"])
    ap.add_argument("--stage3", default="/tests/simspect_alloy_20261108/code_20261109/STAGE3_gem5")
    ap.add_argument("--testset", default=None,
                    help="testset model dir (<testset_dir>/<model>): enables H-PAD exclusion and STT S1_xmm4")
    ap.add_argument("--jobs", type=int, default=1, help="worker processes for invisispec/speclfb (default 1)")
    args = ap.parse_args()
    testset = Path(args.testset) if args.testset else None
    out = Path(args.out).resolve()
    os.environ["SIMSPECT_STAGE3"] = args.stage3
    sys.path.insert(0, args.stage3)
    log = open(out / "classify.log", "a")
    log.write(f"== start {time.strftime('%F %T')} defense={args.defense}\n")
    rows = load_rows(out)
    hits = [r for r in rows.values() if r.get("hit")]
    cls = {}
    if args.defense == "cleanupspec":
        try:
            m = cleanupspec_all(out, hits, log)
        except Exception:
            log.write(traceback.format_exc())
            m = {}
        for r in hits:
            cls[r["idx"]] = m.get(f"{r['mode']}/{r['stem']}", {"no_evidence"})
    elif args.defense in ("invisispec", "speclfb"):
        import gem5_common as gc
        an = None
        if args.defense == "speclfb":
            sys.path.insert(0, str(HERE))
            import speclfb_analyze as an
        work = [(r, out, testset, args.defense) for r in hits]
        if args.jobs > 1:   # (cache-full 2026-11-09) same per-hit function, in worker processes
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(args.jobs) as ex:
                res = list(ex.map(_classify_one, work, chunksize=8))
        else:
            res = [_classify_one(w) for w in work]
        for idx, sigs, err in res:
            cls[idx] = sigs
            if err:
                log.write(err)
    elif args.defense == "stt" and testset is not None:
        sys.path.insert(0, str(Path(args.stage3) / "triage" / "diag"))
        import _fv2_slice as fs
        for r in hits:
            rawf = out / "raw" / r["mode"] / f"{r['stem']}.json"
            raw = json.loads(rawf.read_text()) if rawf.exists() else {}
            # check_ld's data-obtained gate (CLAUDE.md "Leak criteria"): in-window but never obtained
            # its data (never_executed / spec_read_only / bounced) is a check_ld false positive.
            # data_obtained None (no LSQ record, or br_x) stays ungated.
            if raw.get("data_obtained") is False:
                cls[r["idx"]] = {f"disq_not_obtained({raw.get('cache_fate')})"}
                continue
            sl = fs.transmitter_slice(r["stem"], testset / r["mode"])
            if sl.get("err"):
                cls[r["idx"]] = {"other_stt(slice_err)"}
            else:
                cls[r["idx"]] = {"S1_xmm4"} if sl["xmm4"] else {"other_stt"}
    else:
        for r in hits:
            cls[r["idx"]] = {"hit(no target)"}
    with open(out / "classes.jsonl", "w") as f:
        for i in sorted(cls):
            f.write(json.dumps(dict(idx=i, mode=rows[i]["mode"], stem=rows[i]["stem"], kind=rows[i].get("kind"),
                                    sigs=sorted(cls[i]))) + "\n")
    # contiguous finished prefix 0..N-1 (parallel workers can leave holes at the tail)
    N = 0
    while N in rows:
        N += 1
    cum_g = cum_t = 0.0
    first = {}
    K = collections.Counter()
    st = collections.Counter()
    for i in range(N):
        r = rows[i]
        cum_g += r.get("gem5_cpu_s") or 0
        cum_t += r.get("total_cpu_s") or 0
        st[r.get("status")] += 1
        for s in cls.get(i, ()):
            K[s] += 1
            if s not in first:
                first[s] = dict(first_idx=i, tests_to_first=i + 1, stem=r["stem"], mode=r["mode"],
                                cum_gem5_cpu_s=round(cum_g, 2), cum_total_cpu_s=round(cum_t, 2))
    res = dict(defense=args.defense, N_prefix=N, n_rows=len(rows), status=dict(st),
               hits=sum(1 for i in range(N) if rows[i].get("hit")),
               gem5_cpu_s_total=round(cum_g, 2), total_cpu_s_total=round(cum_t, 2),
               gem5_cpu_s_per_test=round(cum_g / N, 3) if N else None,
               total_cpu_s_per_test=round(cum_t / N, 3) if N else None,
               signatures={s: dict(first.get(s, {}), K=K[s], N=N, expected_tests_to_first=round((N + 1) / (K[s] + 1), 2),
                                   expected_gem5_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_g / N, 2) if N else None,
                                   expected_total_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_t / N, 2) if N else None)
                           for s in sorted(set(K) | set(TARGETS[args.defense]))})
    (out / "first_detection.json").write_text(json.dumps(res, indent=1))
    log.write(json.dumps(res) + f"\n== end {time.strftime('%F %T')}\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

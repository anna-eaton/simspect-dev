#!/usr/bin/env python3
"""firstdet_report.py: SimSpect vs AMuLeT per-bug comparison for the unified footprint experiment
(firstdet-final, 2026-11-10; EVAL_MANIFEST "Footprint model: the unified AMuLeT-comparison experiment").

Reads the three run dirs (timing_driver.py / firstdet_stream.py output, after classify_hits.py and,
for CleanupSpec, classify_cs_rmw.py) and reports per bug:
  K/N        K = tests whose classification carries the bug's signature, N = finished tests
             (every simulation is one test; error rows count as tests and are listed).
  expected   (N+1)/(K+1) tests to first detection (K=0: "> N", the multiple is then an upper bound).
  first      the first detecting test's position (1-based) in (a) the seed-20261109 order of the
             corpus pairs (random.Random(seed).shuffle of the sorted (mode, stem) list =
             timing_driver.build_order), counted among the tests that have run, and (b) stream order.
             When every corpus pair has run, (a) is the final first-detection position.
  multiple   AMuLeT pooled test cases per violation (pooled programs per violation x 140,
             src/benchmark.py:230; EVAL_MANIFEST "AMuLeT per-bug first detection") / expected.
  CPU        SimSpect expected CPU-s to first = expected x (mean total CPU-s per test + amortized
             generation CPU-s per test, --gen-cpu-per-test, TA-7); vs AMuLeT pooled CPU-s per violation.
  minimum    over the 5 known AMuLeT bugs (UV1, UV3, UV4, UV5, UV6); jmp shadow reported separately.
Setups drawn: cache_setup counts over all tests and over each bug's detecting tests.

    python3 firstdet_report.py --invisispec <dir> --cleanupspec <dir> --speclfb <dir> \
        --testset <testset_dir>/<model> [--gen-cpu-per-test X] [--json out.json] [--md out.md]
"""
import argparse, collections, json, random, sys
from pathlib import Path

# AMuLeT pooled programs per violation, and pooled CPU-s per violation (EVAL_MANIFEST
# "AMuLeT per-bug first detection", amulet-perbug 2026-11-09, cafe1 dedicated, 32 x 200 programs).
AMULET = {  # bug: (defense, pooled programs / violation, pooled CPU-s / violation, known AMuLeT bug?)
    "UV1": ("invisispec", 23.7, 270, True),
    "UV3": ("cleanupspec", 27.1, 105, True),
    "UV4": ("cleanupspec", 1600, 6171, True),
    "UV5": ("cleanupspec", 1600, 6171, True),
    "UV6": ("speclfb", 42.7, 115, True),
    "jmp_shadow": ("speclfb", 136, 366, False),
}
INPUTS_PER_PROGRAM = 140
MODES = ["mispredict_not_taken", "mispredict_taken"]


def jl(p: Path):
    if not p.exists():
        return []
    out = []
    for l in p.read_text().splitlines():
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def seed_order(testset: Path, seed: int):
    pairs = []
    for m in MODES:
        a = {p.stem for p in (testset / m / "asm").glob("inst-*.s")}
        n = {p.name[:-len(".ann.json")] for p in (testset / m / "ann").glob("inst-*.ann.json")}
        pairs += [(m, s) for s in sorted(a & n)]
    pairs.sort()
    random.Random(seed).shuffle(pairs)
    return pairs


def defense_rows(d: Path, defense: str, testset: Path = None, guard=True):
    """Rows + classes. With testset (streaming runs): drop a row when (a) its .s/.ann.json changed after it ran
    (sha in order_stream.tsv != current; the producer rebuilt it) or the file is gone, or (b) its current ann fails
    the recipe-v3 provenance guard (firstdet_stream.provenance_ok). Dropped rows are counted, never scored."""
    rows = {r["idx"]: r for r in jl(d / "results.jsonl")}
    dropped = collections.Counter()
    if testset is not None and guard:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import firstdet_stream as fs
        shas = {}
        osf = d / "order_stream.tsv"
        if osf.exists():
            for l in osf.read_text().splitlines():
                f = l.split("\t")
                if len(f) >= 4:
                    shas[int(f[0])] = f[3]
        for i in list(rows):
            r = rows[i]
            sp = testset / r["mode"] / "asm" / f"{r['stem']}.s"
            ap_ = testset / r["mode"] / "ann" / f"{r['stem']}.ann.json"
            try:
                cur = fs.file_sha(sp, ap_)
                ok, _ = fs.provenance_ok(json.loads(ap_.read_text()))
            except Exception:
                dropped["file_gone"] += 1; del rows[i]; continue
            if i in shas and shas[i] != cur:
                dropped["changed_after_run"] += 1; del rows[i]; continue
            if not ok:
                dropped["provenance_guard"] += 1; del rows[i]; continue
    cls = {r["idx"]: set(r["sigs"]) for r in jl(d / "classes.jsonl")}
    if defense == "cleanupspec" and (d / "classes_rmw.jsonl").exists():
        cls = {r["idx"]: set(r["sigs"]) for r in jl(d / "classes_rmw.jsonl")}
    # Snapshot cut (streaming): classification lags the runners, so hits that finished after the classifier
    # read results.jsonl have no class yet (classify_cs_rmw labels them no_evidence). Keep only the prefix of
    # results.jsonl (file = completion order) before the first such pending hit, so K and N come from the same
    # snapshot; the cut rows are counted in dropped["after_classify_snapshot"].
    order_lines = [r["idx"] for r in jl(d / "results.jsonl")]
    cut = None
    for k, i in enumerate(order_lines):
        r = rows.get(i)
        if r is not None and r.get("hit") and (i not in cls or cls[i] <= {"no_evidence"}):
            cut = k
            break
    if cut is not None:
        late = set(order_lines[cut:])
        n0 = len(rows)
        rows = {i: r for i, r in rows.items() if i not in late}
        dropped["after_classify_snapshot"] = n0 - len(rows)
    cls = {i: v for i, v in cls.items() if i in rows}
    return rows, cls, dict(dropped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invisispec"); ap.add_argument("--cleanupspec"); ap.add_argument("--speclfb")
    ap.add_argument("--testset", required=True)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--gen-cpu-per-test", type=float, default=None,
                    help="amortized Alloy + Stage 2 CPU-s per corpus test (TA-7); omitted = execution only")
    ap.add_argument("--no-guard", action="store_true", help="skip the sha/provenance row filter")
    ap.add_argument("--sample", default="", help="per-defense uniform stem-hash subsample to score, e.g. "
                    "invisispec=0.25,speclfb=0.25 (firstdet_stream.in_sample); rows outside it are dropped")
    ap.add_argument("--rows", choices=["auto", "prefix", "all"], default="auto",
                    help="prefix = score only the longest seed-order prefix of the FULL corpus whose tests have all run "
                         "and been classified (the final semantics: first N of the seed-20261109 order); all = every "
                         "finished row (interim, streaming). auto = prefix when the testset has READY/DONE, else all")
    ap.add_argument("--prefix", default="", help="cap the prefix per defense, e.g. invisispec=4000,speclfb=4000")
    ap.add_argument("--json"); ap.add_argument("--md")
    args = ap.parse_args()
    gen_src = "--gen-cpu-per-test" if args.gen_cpu_per_test is not None else None
    pv = Path(args.testset) / "PROVENANCE.json"
    if args.gen_cpu_per_test is None and pv.exists():
        # TA-7 amortized generation CPU per (mode, stem) test, from the producer's PROVENANCE.json (regen-lp):
        # Alloy (Stage 1 core JVMs + Stage 1.5 job JVMs, single-threaded, wall ~ CPU) / (programs_merged x 2 modes)
        # + (Stage 2 parsexml/llc + RMW + jmp post-pass CPU-s, RUSAGE_CHILDREN) / stem_mode_pairs published.
        try:
            P = json.loads(pv.read_text()); c = P["cpu_s"]
            alloy = float(c["stage15_alloy_job_wall_s_sum"]) + sum(float(v.get("wall_s") or 0)
                                                                     for v in (P.get("stage1_cpu_s") or {}).values())
            s2 = float(c["stage2_parsexml_llc"]) + float(c["rmw_postpass"]) + float(c["jmp_postpass"])
            args.gen_cpu_per_test = alloy / (2 * float(P["programs_merged"])) + s2 / float(P["stem_mode_pairs"])
            gen_src = (f"PROVENANCE.json {P.get('updated')}: alloy {alloy:.0f} CPU-s / (2 x {P['programs_merged']} programs) "
                       f"+ stage2+postpasses {s2:.0f} CPU-s / {P['stem_mode_pairs']} pairs")
        except Exception as e:
            gen_src = f"PROVENANCE.json unreadable ({type(e).__name__}: {e}); execution only"
    order = seed_order(Path(args.testset), args.seed)
    pos = {p: i for i, p in enumerate(order)}
    dirs = {"invisispec": args.invisispec, "cleanupspec": args.cleanupspec, "speclfb": args.speclfb}
    res = {"generated_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
           "corpus_pairs_now": len(order), "seed": args.seed, "gen_cpu_per_test": args.gen_cpu_per_test, "gen_cpu_source": gen_src,
           "defenses": {}, "bugs": {}}
    for dfn, dd in dirs.items():
        if not dd:
            continue
        d = Path(dd)
        rows, cls, dropped = defense_rows(d, dfn, Path(args.testset), not args.no_guard)
        mode_rows = args.rows if args.rows != "auto" else (
            "prefix" if any((Path(args.testset) / f).exists() for f in ("READY", "DONE")) else "all")
        if mode_rows == "prefix":
            have = {(r["mode"], r["stem"]): i for i, r in rows.items()}
            L = 0
            cap = dict((kv.split("=")[0], int(kv.split("=")[1])) for kv in args.prefix.split(",") if "=" in kv).get(dfn)
            while L < len(order) and order[L] in have and (cap is None or L < cap):
                L += 1
            keep = {have[p] for p in order[:L]}
            dropped["outside_seed_prefix"] = len(rows) - len(keep)
            rows = {i: r for i, r in rows.items() if i in keep}
            cls = {i: v for i, v in cls.items() if i in rows}
        frac = dict((kv.split("=")[0], float(kv.split("=")[1])) for kv in args.sample.split(",") if "=" in kv).get(dfn, 1.0)
        if frac < 1:
            import firstdet_stream as fs
            n0 = len(rows)
            rows = {i: r for i, r in rows.items() if fs.in_sample(r["stem"], frac)}
            cls = {i: v for i, v in cls.items() if i in rows}
            dropped["outside_sample_%g" % frac] = n0 - len(rows)
        N = len(rows)
        if not N:
            continue
        cpu_t = sum(r.get("total_cpu_s") or 0 for r in rows.values())
        cpu_g = sum(r.get("gem5_cpu_s") or 0 for r in rows.values())
        unclassified_hits = sum(1 for i, r in rows.items() if r.get("hit") and i not in cls)
        setups = collections.Counter(r.get("cache_setup") or "warm" for r in rows.values())
        status = collections.Counter(r.get("status") for r in rows.values())
        # run tests in seed order (only pairs present in the corpus listing now)
        run_seed = sorted((pos.get((r["mode"], r["stem"]), 10**12), i) for i, r in rows.items())
        seed_rank = {i: k + 1 for k, (_, i) in enumerate(run_seed)}
        allsigs = collections.Counter(s for v in cls.values() for s in v)
        res["defenses"][dfn] = dict(dir=str(d), N=N, rows_mode=mode_rows, dropped=dropped, hits=sum(1 for r in rows.values() if r.get("hit")),
                                    unclassified_hits=unclassified_hits, status=dict(status),
                                    cache_setups=dict(setups), total_cpu_s_per_test=round(cpu_t / N, 3),
                                    gem5_cpu_s_per_test=round(cpu_g / N, 3), all_signatures=dict(allsigs),
                                    all_corpus_pairs_run=len(rows) >= len(order))
        for bug, (bd, aprog, acpu, known) in AMULET.items():
            if bd != dfn:
                continue
            det = [i for i, s in cls.items() if bug in s and i in rows]
            K = len(det)
            exp = (N + 1) / (K + 1)
            first_seed = min((seed_rank[i] for i in det), default=None)
            fs_i = min(det, key=lambda i: seed_rank[i]) if det else None
            first_stream = (min(det) + 1) if det else None
            per_test = cpu_t / N + (args.gen_cpu_per_test or 0)
            a_cases = aprog * INPUTS_PER_PROGRAM
            res["bugs"][bug] = dict(
                defense=dfn, known_amulet_bug=known, K=K, N=N, expected_tests=round(exp, 2),
                censored=(K == 0),
                first_seed_order=first_seed,
                first_seed_stem=(f"{rows[fs_i]['mode']}/{rows[fs_i]['stem']}" if fs_i is not None else None),
                first_stream_order=first_stream,
                det_setups=dict(collections.Counter(rows[i].get("cache_setup") or "warm" for i in det)),
                amulet_pooled_programs=aprog, amulet_pooled_test_cases=round(a_cases, 1),
                multiple_tests=round(a_cases / exp, 1),
                simspect_cpu_s_per_test=round(per_test, 3),
                simspect_expected_cpu_s=round(exp * per_test, 1),
                simspect_expected_cpu_s_exec_only=round(exp * cpu_t / N, 1),
                amulet_pooled_cpu_s=acpu, multiple_cpu=round(acpu / (exp * per_test), 2))
    known = [b for b, v in res["bugs"].items() if v["known_amulet_bug"]]
    if known:
        mt = min(known, key=lambda b: res["bugs"][b]["multiple_tests"])
        mc = min(known, key=lambda b: res["bugs"][b]["multiple_cpu"])
        res["minimum"] = dict(bugs_present=sorted(known), all_5=len(known) == 5,
                              tests=dict(bug=mt, multiple=res["bugs"][mt]["multiple_tests"],
                                         upper_bound=res["bugs"][mt]["censored"]),
                              cpu=dict(bug=mc, multiple=res["bugs"][mc]["multiple_cpu"],
                                       upper_bound=res["bugs"][mc]["censored"]))
    js = json.dumps(res, indent=1)
    if args.json:
        Path(args.json).write_text(js)
    lines = ["| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for b, v in res["bugs"].items():
        gt = ">" if v["censored"] else ""
        le = "≤" if v["censored"] else ""
        lines.append(f"| {b} | {v['defense']} | {v['K']}/{v['N']} | {gt}{v['expected_tests']} | "
                     f"{v['first_seed_order'] or '—'} / {v['first_stream_order'] or '—'} | {v['det_setups']} | "
                     f"{v['amulet_pooled_test_cases']:,} | {le}{v['multiple_tests']}x | {gt}{v['simspect_expected_cpu_s']} | "
                     f"{v['amulet_pooled_cpu_s']} | {le}{v['multiple_cpu']}x |")
    if "minimum" in res:
        m = res["minimum"]
        lines.append(f"\nMinimum over known bugs present ({', '.join(m['bugs_present'])}): tests {m['tests']['multiple']}x "
                     f"({m['tests']['bug']}{', upper bound' if m['tests']['upper_bound'] else ''}); "
                     f"CPU {m['cpu']['multiple']}x ({m['cpu']['bug']}{', upper bound' if m['cpu']['upper_bound'] else ''}).")
    md = "\n".join(lines)
    if args.md:
        Path(args.md).write_text(md + "\n")
    print(js)
    print(md)


if __name__ == "__main__":
    main()

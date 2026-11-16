"""Recompute the final paper numbers from this snapshot alone (no node access, standard library only).

Run from the snapshot root:  python3 -I code/recompute_numbers.py
Prints each number next to the value the paper / EVAL_MANIFEST quotes and exits non-zero on any mismatch.

Sources (all inside this snapshot):
  CleanupSpec pool (A-UV3/A-UV4/A-UV5): classes_rmw.jsonl of the five unified-pipeline CleanupSpec runs
    main      results/bigcorpus/cafe3/firstdet/T2g_Footprint_6_u_nov10_s2A_merged            (50,232 tests)
    extra-new results/bigcorpus/cafe3/firstdet/T2g_Footprint_6_u_core_lpP_s2A_new            (90,932 tests)
    round 1   results/bigcorpus/cafe1/firstdet/T2g_Footprint_6_u_nov10_c1_s2A                (50,232)
    round 2   results/bigcorpus/cafe2/firstdet/T2g_Footprint_6_u_nov10_c2_s2A                (50,232)
    round 3   results/bigcorpus/cafe3/firstdet/T2g_Footprint_6_u_nov10_c3_s2A                (50,232)
  InvisiSpec / SpecLFB (first 4,000 seed-order tests): classes.jsonl of T1g / T3g_Footprint_6_u_nov10_s2A (cafe3 copies)
  N = rows with status ok in each run's results.jsonl
  SimSpect fast-path CPU per test: results/timing/cafe3/simspect/T{1,2,3}g_p16_fast/{results.jsonl, fastpath_workers.jsonl}
    (mean total_cpu_s + workers' one-time startup CPU / n, as retime_fast_summary.py)
  AMuLeT clean CPU per test case: results/timing/cafe3/amulet/runs/*/t5_summary.json (total_cpu_s_instances / programs / 140)
"""
import glob
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = {h: os.path.join(ROOT, "results", "bigcorpus", h, "firstdet") for h in ("cafe1", "cafe2", "cafe3")}
bad = []


def rows(path):
    for p in (path, path + ".gz"):
        if os.path.exists(p):
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
            return
    raise FileNotFoundError(path)


def count(run_dir, fname, sig):
    return len({(r["mode"], r["stem"]) for r in rows(os.path.join(run_dir, fname)) if sig in r.get("sigs", [])})


def n_ok(run_dir):
    return len({(r["mode"], r["stem"]) for r in rows(os.path.join(run_dir, "results.jsonl")) if r.get("status") == "ok"})


def check(label, got, want, tol=0.0):
    ok = abs(got - want) <= tol
    print(f"  {'OK ' if ok else 'BAD'} {label}: {got} (quoted {want})")
    if not ok:
        bad.append(label)


print("== CleanupSpec pool (classes_rmw.jsonl)")
cs_runs = [("main", FD["cafe3"] + "/T2g_Footprint_6_u_nov10_s2A_merged", 50232),
           ("extra-new", FD["cafe3"] + "/T2g_Footprint_6_u_core_lpP_s2A_new", 90932),
           ("round1", FD["cafe1"] + "/T2g_Footprint_6_u_nov10_c1_s2A", 50232),
           ("round2", FD["cafe2"] + "/T2g_Footprint_6_u_nov10_c2_s2A", 50232),
           ("round3", FD["cafe3"] + "/T2g_Footprint_6_u_nov10_c3_s2A", 50232)]
tot = {"N": 0, "UV3": 0, "UV4": 0, "UV5": 0}
for name, d, n_quoted in cs_runs:
    n = n_ok(d)
    k = {s: count(d, "classes_rmw.jsonl", s) for s in ("UV3", "UV4", "UV5")}
    print(f"  {name:10} N={n:,} UV3={k['UV3']:,} UV4={k['UV4']:,} UV5={k['UV5']}")
    check(f"{name} N", n, n_quoted)
    tot["N"] += n
    for s in k:
        tot[s] += k[s]
check("pooled N", tot["N"], 291860)
check("pooled A-UV3 K", tot["UV3"], 7288)
check("pooled A-UV4 K", tot["UV4"], 919)
check("pooled A-UV5 K", tot["UV5"], 5)
main = cs_runs[0][1]
check("main-only A-UV3 K", count(main, "classes_rmw.jsonl", "UV3"), 1274)
check("main-only A-UV4 K", count(main, "classes_rmw.jsonl", "UV4"), 162)
check("main-only A-UV5 K", count(main, "classes_rmw.jsonl", "UV5"), 0)

print("== InvisiSpec T1g / SpecLFB T3g (first 4,000 seed-order tests, classes.jsonl)")
t1 = FD["cafe3"] + "/T1g_Footprint_6_u_nov10_s2A"
t3 = FD["cafe3"] + "/T3g_Footprint_6_u_nov10_s2A"
check("T1g N", n_ok(t1), 4000)
check("T3g N", n_ok(t3), 4000)
check("A-UV1 K (InvisiSpec)", count(t1, "classes.jsonl", "UV1"), 2002)
check("A-UV6 K (SpecLFB)", count(t3, "classes.jsonl", "UV6"), 851)
check("walk order K (SpecLFB)", count(t3, "classes.jsonl", "walk_order"), 657)
check("jmp shadow K (SpecLFB)", count(t3, "classes.jsonl", "jmp_shadow"), 527)

print("== SimSpect fast-path CPU-s per test (cafe3, 2026-11-16)")
TM = os.path.join(ROOT, "results", "timing", "cafe3")
for row, want in (("T1g", 1.344), ("T2g", 1.738), ("T3g", 1.2956)):
    d = os.path.join(TM, "simspect", f"{row}_p16_fast")
    ok = [r for r in rows(os.path.join(d, "results.jsonl")) if r.get("status") == "ok"]
    startup = sum(json.loads(l).get("startup_cpu_s", 0) for l in open(os.path.join(d, "fastpath_workers.jsonl")) if '"spawn"' in l)
    v = round(sum(r["total_cpu_s"] for r in ok) / len(ok) + startup / len(ok), 4)
    check(f"{row} fast CPU-s/test (n={len(ok)})", v, want, tol=0.0006)

print("== AMuLeT clean re-time, CPU-s per test case (cafe3, 2026-11-16)")
for dfn, want in (("InvisiSpec", 0.07304), ("CleanupSpec", 0.02337), ("SpecLFB", 0.01935)):
    (run,) = glob.glob(os.path.join(TM, "amulet", "runs", f"{dfn}_r*"))
    s = json.load(open(os.path.join(run, "t5_summary.json")))
    v = s["total_cpu_s_instances"] / s["total_programs"] / 140
    check(f"{dfn} ({os.path.basename(run)}, {s['total_programs']} programs)", round(v, 5), want, tol=0.000006)

print("== E2w OTB check (ReCon-STT on STT_6_u_core_lpP_s2A), results/bigcorpus/cafe3/e2w")
E2W = os.path.join(ROOT, "results", "bigcorpus", "cafe3", "e2w")
bk = json.load(open(os.path.join(E2W, "buckets.json")))["buckets"]
tests = sum(v["tests"] for k, v in bk.items() if k.endswith("/plain") or k.endswith("/rmw"))
rsa8 = sum(n for v in bk.values() for b, n in v["buckets"].items() if b.startswith("R-SA-8 candidate"))
a2 = sum(n for v in bk.values() for b, n in v["buckets"].items() if b.startswith("A2 STLF bypass"))
tr = json.load(open(os.path.join(E2W, "rsa8_trace.json")))
check("E2w tests", tests, 30368)
check("E2w R-SA-8 candidate tests", rsa8, 24)
check("E2w R-SA-8 signature-positive in faithful rerun", sum(1 for v in tr.values() if v.get("rsa8_signature")), 22)
check("E2w A2 STLF bypass (UV2) tests", a2, 1690)

print("\nALL MATCH" if not bad else f"\nMISMATCH: {bad}")
sys.exit(1 if bad else 0)

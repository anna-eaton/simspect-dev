#!/usr/bin/env python3
"""TIME-1 (agent timing, 2026-11-15): summarize the dedicated CPU timing on cafe2 and recompute the CPU-per-detection multiples.

Inputs (cafe2 /tests/timing_20261115 layout, or a copy of it):
  simspect/<row>_p16/results.jsonl       big-corpus sample (1,000 pairs per defense), rows T1g/T2g/T3g
  amulet/runs/<D>_r<R>_n<N>_<UTC>/t5_summary.json   (summarize_t5.py output; the newest run per defense is used)
SimSpect CPU per test = mean total_cpu_s (wait4 rusage of the whole pipeline.py gem5 tree = build + gem5 + checker),
gem5-only = mean gem5_cpu_s. AMuLeT CPU per program = summed instance process-group CPU / programs (summarize_t5.py),
CPU per test case = per program / 140.
Multiples (same estimator both sides): expected tests to a detection = (N+1)/(K+1).
  SimSpect CPU per detection = (N+1)/(K+1) x (CPU per test [+ generation CPU per test]).
  AMuLeT  CPU per detection = (896,000+1)/(K_A+1) x CPU per test case (T5: 6,400 programs x 140 per defense).
  multiple = AMuLeT CPU per detection / SimSpect CPU per detection (> 1: SimSpect cheaper).
Usage: summarize_time1.py <root> [--kn-json <file with extra SimSpect K/N sets>] [--gen 0.93] --out <json> --md <md>
"""
import argparse, glob, json, os, statistics as st, collections

# AMuLeT K per defense from T5 + per-bug replay (EVAL_MANIFEST "AMuLeT per-bug first detection"); N = 6,400 programs x 140.
AM_K = {"UV1": ("InvisiSpec", 270), "UV3": ("CleanupSpec", 236), "UV4": ("CleanupSpec", 4), "UV5": ("CleanupSpec", 4),
        "UV6": ("SpecLFB", 150), "jmp_shadow": ("SpecLFB", 47)}
AM_N_TC = 6400 * 140
# Earlier AMuLeT CPU (T5, 32 instances on cafe1), shown only to quantify the load effect.
T5_CPU_PER_PROGRAM = {"InvisiSpec": 11.4, "CleanupSpec": 3.86, "SpecLFB": 2.69}
ROW_DEF = {"T1g": "InvisiSpec", "T2g": "CleanupSpec", "T3g": "SpecLFB"}


def simspect(path):
    rows = [json.loads(l) for l in open(path)]
    ok = [r for r in rows if r.get("total_cpu_s") is not None]
    by = collections.defaultdict(list)
    for r in ok:
        by[r.get("cache_setup")].append(r["total_cpu_s"])
    return dict(n=len(rows), status=dict(collections.Counter(r["status"] for r in rows)),
                total_mean=st.mean(r["total_cpu_s"] for r in ok), total_median=st.median(r["total_cpu_s"] for r in ok),
                gem5_mean=st.mean(r["gem5_cpu_s"] for r in ok), wall_mean=st.mean(r["wall_s"] for r in ok),
                nongem5_mean=st.mean(r["total_cpu_s"] - r["gem5_cpu_s"] for r in ok),
                by_setup={k: (len(v), round(st.mean(v), 3)) for k, v in sorted(by.items(), key=lambda x: str(x[0]))},
                t_first=min(r["t_start"] for r in rows), t_last=max(r["t_start"] + r["wall_s"] for r in rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--kn-json", default="", help='{"label": {"UV1": ["T1g", K, N], ...}} extra SimSpect K/N sets')
    ap.add_argument("--gen", type=float, default=0.93, help="amortized generation CPU-s per test (TIME-1 re-timed big-corpus value)")
    ap.add_argument("--simspect-suffix", default="", help='read simspect/<row>_p16<suffix>/ (e.g. "_fast" for the fast-path re-time)')
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    R = {"simspect_bc": {}, "amulet": {}}
    for row in ("T1g", "T2g", "T3g"):
        for key, sub in (("simspect_bc", f"{row}_p16{a.simspect_suffix}"),):
            p = f"{a.root}/simspect/{sub}/results.jsonl"
            if os.path.exists(p):
                R[key][row] = simspect(p)
    for D in ("InvisiSpec", "CleanupSpec", "SpecLFB"):
        runs = sorted(glob.glob(f"{a.root}/amulet/runs/{D}_r*/t5_summary.json"))
        if runs:
            s = json.load(open(runs[-1]))
            R["amulet"][D] = dict(run=os.path.dirname(runs[-1]), instances=s["instances"], programs=s["total_programs"],
                                  violations=s["total_violations"], cpu_total=s["total_cpu_s_instances"],
                                  cpu_per_program=s["cpu_s_per_program"], cpu_per_test_case=s["cpu_s_per_program"] / 140,
                                  rusage_children_cpu=(s.get("rusage_children") or {}).get("cpu_total"),
                                  wall=(s.get("rusage_children") or {}).get("wall"))
    kn_sets = {}   # multiples only from --kn-json (big-corpus K/N, Anna 2026-11-15)
    if a.kn_json:
        kn_sets.update({k: {b: tuple(v) for b, v in d.items()} for k, d in json.load(open(a.kn_json)).items()})
    mult = []
    for label, KN in kn_sets.items():
        for cpu_basis in ("simspect_bc",):
            for bug, (row, K, N) in KN.items():
                if row not in R[cpu_basis] or AM_K[bug][0] not in R["amulet"]:
                    continue
                D, KA = AM_K[bug]
                exp_s = (N + 1) / (K + 1)
                exp_a = (AM_N_TC + 1) / (KA + 1)
                c = R[cpu_basis][row]["total_mean"]
                ca = R["amulet"][D]["cpu_per_test_case"]
                am = exp_a * ca
                ss_exec, ss_gen = exp_s * c, exp_s * (c + a.gen)
                mult.append(dict(kn=label, cpu_basis=cpu_basis, bug=bug, defense=D, K=K, N=N, exp_tests=exp_s,
                                 amulet_K=KA, amulet_exp_test_cases=exp_a, simspect_cpu_per_test=c, amulet_cpu_per_test_case=ca,
                                 simspect_cpu_per_det_exec=ss_exec, simspect_cpu_per_det_gen=ss_gen, amulet_cpu_per_det=am,
                                 multiple_exec=am / ss_exec, multiple_gen=am / ss_gen,
                                 multiple_tests=exp_a / exp_s))
    R["multiples"] = mult
    R["gen_cpu_per_test"] = a.gen
    json.dump(R, open(a.out, "w"), indent=1)
    L = ["## SimSpect CPU per test (16 workers, cafe2 CPUs 0-31)", "",
         "| corpus | row | N | status | total CPU-s/test mean (median) | gem5 CPU-s/test | non-gem5 | wall s/test | by setup (n, mean) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for key, lab in (("simspect_bc", "big corpus s2A sample"),):
        for row, s in R[key].items():
            L.append(f"| {lab} | {row} ({ROW_DEF[row]}) | {s['n']} | {s['status']} | {s['total_mean']:.2f} ({s['total_median']:.2f}) | {s['gem5_mean']:.2f} | "
                     f"{s['nongem5_mean']:.2f} | {s['wall_mean']:.2f} | {s['by_setup']} |")
    L += ["", "## AMuLeT CPU per program (instances pinned to CPUs 0-31)", "",
          "| defense | instances | programs | violations | CPU-s per program | CPU-s per test case (/140) | T5 CPU-s per program (32 inst.) | ratio TIME-1 / T5 | RUSAGE_CHILDREN CPU-s vs summed instances |",
          "|---|---|---|---|---|---|---|---|---|"]
    for D, s in R["amulet"].items():
        L.append(f"| {D} | {s['instances']} | {s['programs']} | {s['violations']} | {s['cpu_per_program']:.3f} | {s['cpu_per_test_case']:.4f} | "
                 f"{T5_CPU_PER_PROGRAM[D]} | {s['cpu_per_program'] / T5_CPU_PER_PROGRAM[D]:.2f} | {s['rusage_children_cpu']} vs {s['cpu_total']:.0f} |")
    L += ["", "## CPU-per-detection multiples (AMuLeT CPU per detection / SimSpect CPU per detection; >1 = SimSpect cheaper)", "",
          f"Estimator (N+1)/(K+1) on both sides; AMuLeT N = 896,000 test cases per defense; generation = {a.gen} CPU-s per test.", "",
          "| K/N set | SimSpect CPU basis | bug | SimSpect K/N | exp. tests | AMuLeT K | AMuLeT exp. test cases | multiple (tests) | SimSpect CPU-s/det (exec) | AMuLeT CPU-s/det | multiple exec only | multiple incl. generation |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in mult:
        L.append(f"| {m['kn']} | {m['cpu_basis']} | {m['bug']} | {m['K']}/{m['N']} | {m['exp_tests']:.2f} | {m['amulet_K']} | {m['amulet_exp_test_cases']:.0f} | "
                 f"{m['multiple_tests']:.1f}x | {m['simspect_cpu_per_det_exec']:.1f} | {m['amulet_cpu_per_det']:.1f} | {m['multiple_exec']:.3g}x | {m['multiple_gen']:.3g}x |")
    open(a.md, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

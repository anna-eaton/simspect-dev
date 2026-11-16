import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
DEFENSES = {"T1g": "invisispec", "T2g": "cleanupspec", "T3g": "speclfb"}
AMULET_DEF = {"T1g": "InvisiSpec", "T2g": "CleanupSpec", "T3g": "SpecLFB"}
SEED = 20261109
AMULET_TIMING_R = {"InvisiSpec": 14, "CleanupSpec": 15, "SpecLFB": 13}


def env():
    work = Path(os.environ.get("WORK", ROOT / "work")).resolve()
    gem5 = Path(os.environ.get("GEM5_ROOT", ROOT / "gem5")).resolve()
    return work, gem5


def render(template, name=None):
    work, gem5 = env()
    src = ROOT / template
    txt = src.read_text().replace("@WORK@", str(work)).replace("@GEM5@", str(gem5))
    cfg = json.loads(txt)
    dst = work / "configs" / (name or src.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(cfg, indent=1) + "\n")
    return dst, cfg


def run(cmd, cwd=ROOT, extra_env=None, log=None):
    e = dict(os.environ)
    e.setdefault("TMPDIR", "/tmp")
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e.update(extra_env or {})
    print("+", " ".join(str(c) for c in cmd), flush=True)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f:
            r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=e, stdout=f, stderr=subprocess.STDOUT)
    else:
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=e)
    if r.returncode:
        sys.exit(f"command failed rc={r.returncode}: {' '.join(str(c) for c in cmd)}")


def link_results():
    work, _ = env()
    (work / "results").mkdir(parents=True, exist_ok=True)
    lk = ROOT / "results"
    if lk.is_symlink() or lk.exists():
        if lk.resolve() != (work / "results").resolve():
            sys.exit(f"{lk} exists and does not point to {work / 'results'}")
    else:
        lk.symlink_to(work / "results")


def cmd_corpus(a):
    work, _ = env()
    s2, _ = render("runconfigs/stage2_A.json")
    gtxt = (ROOT / a.gen_config).read_text().replace("@WORK@", str(work))
    g = json.loads(gtxt)
    g["twostage_lp"]["stage2_config"] = str(s2)
    gp = work / "configs" / Path(a.gen_config).name
    gp.write_text(json.dumps(g, indent=1) + "\n")
    ws = work / "ws" / g["twostage_lp"]["corpus"]
    run([PY, "-u", "twostage_lp.py", "--config", gp, "--ws", ws] + (["--alloy-only"] if a.alloy_only else []))
    print(f"corpus: {Path(g['paths']['testset_dir']) / g['twostage_lp']['corpus']}")


def corpus_dir(name):
    work, _ = env()
    return work / "testsets" / name


def cmd_hits(a):
    work, _ = env()
    out = work / "hits" / a.corpus
    ts = corpus_dir(a.corpus)
    tmo = {"SIMSPECT_GEM5_TIMEOUT_S": str(a.gem5_timeout)}
    for row in a.rows:
        cfg, _ = render(f"runconfigs/hits/{row}.json", f"{row}_hits.json")
        d = out / row
        sel = [] if row == "T2g" else ["--seed-prefix", str(a.prefix)]
        run([PY, "STAGE3_gem5/timing/firstdet_stream.py", "--code-root", ROOT, "--config", cfg, "--model", a.corpus,
             "--out", d, "--seed", str(SEED), "--parallel", str(a.parallel)] + sel, extra_env=tmo)
    cmd_classify(a)


def cmd_classify(a):
    work, _ = env()
    out = work / "hits" / a.corpus
    ts = corpus_dir(a.corpus)
    rep = {}
    for row in a.rows:
        d = out / row
        c = out / f"{row}_classified"
        dfn = DEFENSES[row]
        extra = ["--rmw-stems", ts / "rmw_stems.tsv"] if dfn == "cleanupspec" else []
        run([PY, "STAGE3_gem5/bugs/classify.py", "footprint", "--run", d, "--defense", dfn, "--out", c,
             "--testset", ts, "--stage3", ROOT / "STAGE3_gem5", "--jobs", str(a.jobs)] + extra)
        rep[dfn] = c
    args = []
    for dfn, c in rep.items():
        args += [f"--{dfn}", c]
    run([PY, "STAGE3_gem5/timing/firstdet_report.py"] + args +
        ["--testset", ts, "--seed", str(SEED), "--json", out / "report.json", "--md", out / "report.txt"])
    r = json.loads((out / "report.json").read_text())
    rowof = {v: k for k, v in DEFENSES.items()}
    kn = {b: [rowof[v["defense"]], v["K"], v["N"]] for b, v in r.get("bugs", {}).items() if v.get("defense") in rowof}
    (out / "kn.json").write_text(json.dumps({"simspect": kn}, indent=1) + "\n")
    print(f"report: {out / 'report.txt'}; K/N: {out / 'kn.json'}")


def busy_fraction(secs=10):
    def snap():
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        return sum(v), v[3] + v[4]
    t0, i0 = snap()
    time.sleep(secs)
    t1, i1 = snap()
    return 1.0 - (i1 - i0) / max(1, t1 - t0)


def idle_gate(a, label):
    if a.no_idle_check:
        return
    t0 = time.time()
    while True:
        b = busy_fraction()
        print(f"idle check before {label}: busy {b:.1%}", flush=True)
        if b < a.max_busy:
            return
        if time.time() - t0 > a.idle_wait_s:
            sys.exit(f"node not idle before {label} (busy {b:.1%}); rerun on an idle node or pass --no-idle-check")
        time.sleep(60)


def cmd_timing(a):
    work, _ = env()
    out = work / "timing"
    ts = corpus_dir(a.corpus)
    smp = out / "sample"
    if not (smp / "sample.tsv").exists():
        run([PY, "STAGE3_gem5/timing/make_sample.py", "--code-root", ROOT, "--testset", ts, "--n", str(a.n),
             "--seed", str(a.sample_seed), "--out", smp])
    for row in a.rows:
        cfg, _ = render(f"runconfigs/timing/{row}.json", f"{row}_timing.json")
        d = out / "simspect" / f"{row}_p{a.parallel}{a.suffix}"
        idle_gate(a, row)
        pin = ["taskset", "-c", a.cpus] if a.cpus else []
        run(pin + [PY, "STAGE3_gem5/timing/firstdet_stream.py", "--code-root", ROOT, "--config", cfg, "--model", a.corpus,
                   "--out", d, "--seed", str(SEED), "--parallel", str(a.parallel), "--only-file", smp / "sample.tsv",
                   "--n-max", str(a.n), "--poll", "30"], log=d / "stream.stdout")


def amulet_env(a):
    work, gem5 = env()
    t5 = work / "amulet"
    t5.mkdir(parents=True, exist_ok=True)
    repo = Path(a.amulet_repo).resolve()
    if not (t5 / "benchmark_t5.py").exists():
        run([PY, ROOT / "amulet/make_benchmark_t5.py", repo / "src/benchmark.py", t5 / "benchmark_t5.py"])
    if not (t5 / "analyse_ipc_violation_t5.py").exists():
        run([PY, ROOT / "amulet/make_analyse_t5.py", repo / "src/analyse_ipc_violation.py", t5 / "analyse_ipc_violation_t5.py"])
    return t5, repo, {"AMULET_REPO": str(repo), "GEM5_ROOT": str(gem5), "AMULET_PY": a.amulet_py,
                      "AMULET_T5": str(t5), "CPUS": a.cpus or ""}


def cmd_amulet_hits(a):
    t5, repo, e = amulet_env(a)
    out = t5 / "hits"
    runs = {}
    for row in a.rows:
        D = AMULET_DEF[row]
        before = set((out / "runs").glob(f"{D}_r*")) if (out / "runs").exists() else set()
        run(["bash", ROOT / "amulet/run_amulet.sh", D, str(a.instances), str(a.programs), str(a.inputs), out], extra_env=e)
        new = sorted(set((out / "runs").glob(f"{D}_r*")) - before)
        runs[D] = new[-1]
    ae = dict(e, PATH=str(Path(a.amulet_py).parent) + os.pathsep + os.environ.get("PATH", ""))
    for D, r in runs.items():
        run([a.amulet_py, ROOT / "amulet/classify_t5.py", r, D, "--all", "--jobs", str(a.jobs)], cwd=repo / "src", extra_env=ae)
        run([a.amulet_py, ROOT / "amulet/summarize_t5.py", r], cwd=repo / "src", extra_env=ae)
    pb = out / "perbug"
    pb.mkdir(parents=True, exist_ok=True)
    run([a.amulet_py, ROOT / "amulet/perbug_t5.py", pb] + [f"{D}={r}" for D, r in runs.items()], cwd=repo / "src", extra_env=ae)
    print(f"AMuLeT per-bug summary: {pb / 'perbug_summary.json'}")


def cmd_amulet_timing(a):
    work, _ = env()
    t5, repo, e = amulet_env(a)
    out = work / "timing" / "amulet"
    for row in a.rows:
        D = AMULET_DEF[row]
        idle_gate(a, f"AMuLeT {D}")
        inst = a.instances or AMULET_TIMING_R[D]
        before = set((out / "runs").glob(f"{D}_r*")) if (out / "runs").exists() else set()
        run(["bash", ROOT / "amulet/run_amulet.sh", D, str(inst), str(a.programs), str(a.inputs), out], extra_env=e)
        new = sorted(set((out / "runs").glob(f"{D}_r*")) - before)
        run([a.amulet_py, ROOT / "amulet/summarize_t5.py", new[-1]], cwd=repo / "src")


def cmd_compare(a):
    work, _ = env()
    pooled = work / "pool" / "kn_pooled.json"
    kn = Path(a.kn) if a.kn else (pooled if pooled.exists() else work / "hits" / a.corpus / "kn.json")
    out = work / "timing"
    hits = work / "amulet" / "hits"
    run([PY, "STAGE3_gem5/timing/compare.py", out, "--kn-json", kn, "--gen", str(a.gen), "--suffix", a.suffix,
         "--amulet-hits", hits, "--out", out / "compare.json", "--txt", out / "compare.txt"])
    print(f"comparison: {out / 'compare.txt'}")


def cmd_eval(a):
    work, _ = env()
    link_results()
    camps = []
    for row in a.rows:
        cfg, c = render(f"runconfigs/eval/{row}.json", f"{row}_eval.json")
        model = a.model or c["paths"]["model"]
        run([PY, "-u", "testrun.py", "--config", cfg, "--model", model, "--max-new", "2000", "--once", "--resume"],
            extra_env={"SIMSPECT_GEM5_TIMEOUT_S": str(a.gem5_timeout)})
        camps.append({"row": row, "results_name": c["paths"]["results_name"], "model": model, "stt": row in ("E3", "E4")})
    cp = work / "eval" / "campaigns.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(camps, indent=1) + "\n")
    gate = work / "eval" / "gate.json"
    run([PY, "STAGE3_gem5/bugs/classify.py", "gate", "--code-root", ROOT, "--campaigns", cp,
         "--testsets-root", work / "testsets", "--json", gate])
    for c in camps:
        run([PY, "STAGE3_gem5/bugs/classify.py", "bucket", "--row", c["results_name"], "--gate", gate,
             "--json", work / "eval" / f"buckets_{c['row']}.json"] + (["--stt"] if c["stt"] else []))


def t2g_classify_report(corpus, out, a, extra=()):
    ts = corpus_dir(corpus)
    cfg, _ = render("runconfigs/hits/T2g.json", "T2g_hits.json")
    run([PY, "STAGE3_gem5/timing/firstdet_stream.py", "--code-root", ROOT, "--config", cfg, "--model", corpus,
         "--out", out, "--seed", str(SEED), "--parallel", str(a.parallel)] + list(extra),
        extra_env={"SIMSPECT_GEM5_TIMEOUT_S": str(a.gem5_timeout)})
    c = Path(str(out) + "_classified")
    run([PY, "STAGE3_gem5/bugs/classify.py", "footprint", "--run", out, "--defense", "cleanupspec", "--out", c,
         "--testset", ts, "--stage3", ROOT / "STAGE3_gem5", "--jobs", str(a.jobs), "--rmw-stems", ts / "rmw_stems.tsv"])
    rj = Path(str(out) + "_report.json")
    run([PY, "STAGE3_gem5/timing/firstdet_report.py", "--cleanupspec", c, "--testset", ts, "--seed", str(SEED),
         "--json", rj, "--md", Path(str(out) + "_report.txt")])
    return json.loads(rj.read_text())


def cmd_rounds(a):
    work, _ = env()
    s2, _ = render("runconfigs/stage2_A.json")
    src = corpus_dir(a.main) / "xml"
    for r in a.rounds:
        tag = f"c{r}"
        rd = work / "rounds" / tag
        (rd / "src").mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("inst-*.xml")):
            for ext in (".xml", ".txt"):
                g = f.with_suffix(ext)
                lk = rd / "src" / f"{f.stem}_{tag}{ext}"
                if g.exists() and not lk.exists():
                    lk.symlink_to(g.resolve())
        final = f"{a.main}_{tag}"
        if (corpus_dir(final) / "READY").exists():
            print(f"rounds: {final} is complete (READY), Stage 2 skipped")
            t2g_classify_report(final, work / "pool" / f"T2g_{final}", a)
            continue
        run([PY, "-u", "STAGE1_alloy/gen/restream.py", "--src", rd / "src", "--cfg", s2, "--ts", work / "testsets",
             "--final", final, "--ws", rd / "ws", "--jobs", str(a.stage2_jobs), "--chunk", "2000"], log=rd / "stage2.out")
        t2g_classify_report(final, work / "pool" / f"T2g_{final}", a)


def cmd_pool(a):
    work, _ = env()
    pool = work / "pool"
    dd = pool / "dedup"
    run([PY, "STAGE1_alloy/gen/dedup_vs_main.py", "--main", corpus_dir(a.main) / "xml", "--extra", corpus_dir(a.extra) / "xml",
         "--out", dd, "--jobs", str(a.jobs)])
    stems = [l.strip() for l in (dd / "dup_stems.txt").read_text().splitlines() if l.strip()]
    (dd / "dup_pairs.tsv").write_text("".join(f"{m}\t{s}\n" for s in stems for m in ("mispredict_not_taken", "mispredict_taken")))
    reps = {"main": json.loads((work / "hits" / a.main / "report.json").read_text())}
    reps["extra_new"] = t2g_classify_report(a.extra, pool / f"T2g_{a.extra}_new", a, ["--exclude-file", dd / "dup_pairs.tsv"])
    for r in a.rounds:
        rj = pool / f"T2g_{a.main}_c{r}_report.json"
        if rj.exists():
            reps[f"c{r}"] = json.loads(rj.read_text())
    kn = {}
    for bug in ("UV3", "UV4", "UV5"):
        K = sum(rp["bugs"][bug]["K"] for rp in reps.values() if bug in rp.get("bugs", {}))
        N = sum(rp["bugs"][bug]["N"] for rp in reps.values() if bug in rp.get("bugs", {}))
        kn[bug] = ["T2g", K, N]
    main_kn = json.loads((work / "hits" / a.main / "kn.json").read_text())["simspect"]
    for bug, v in main_kn.items():
        kn.setdefault(bug, v)
    (pool / "kn_pooled.json").write_text(json.dumps({"pooled": kn}, indent=1) + "\n")
    parts = {k: {b: [v["K"], v["N"]] for b, v in rp.get("bugs", {}).items() if b in ("UV3", "UV4", "UV5")} for k, rp in reps.items()}
    (pool / "kn_parts.json").write_text(json.dumps(parts, indent=1) + "\n")
    print(f"pooled K/N: {pool / 'kn_pooled.json'}")


def main():
    ap = argparse.ArgumentParser(prog="simspect.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("corpus")
    p.add_argument("--gen-config", default="runconfigs/generate/Footprint_6_u_main.json")
    p.add_argument("--alloy-only", action="store_true")
    p.set_defaults(fn=cmd_corpus)

    for name, fn in (("hits", cmd_hits), ("classify", cmd_classify)):
        p = sub.add_parser(name)
        p.add_argument("--corpus", default="Footprint_6_u_main_A")
        p.add_argument("--rows", nargs="+", default=["T1g", "T2g", "T3g"])
        p.add_argument("--prefix", type=int, default=4000)
        p.add_argument("--parallel", type=int, default=12)
        p.add_argument("--jobs", type=int, default=8)
        p.add_argument("--gem5-timeout", type=int, default=900)
        p.set_defaults(fn=fn)

    p = sub.add_parser("timing")
    p.add_argument("--corpus", default="Footprint_6_u_extra_A")
    p.add_argument("--rows", nargs="+", default=["T1g", "T2g", "T3g"])
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--sample-seed", type=int, default=20261115)
    p.add_argument("--parallel", type=int, default=16)
    p.add_argument("--cpus", default="0-31")
    p.add_argument("--suffix", default="_fast")
    p.add_argument("--max-busy", type=float, default=0.03)
    p.add_argument("--idle-wait-s", type=int, default=7200)
    p.add_argument("--no-idle-check", action="store_true")
    p.set_defaults(fn=cmd_timing)

    for name, fn, inst in (("amulet-hits", cmd_amulet_hits, 32), ("amulet-timing", cmd_amulet_timing, 0)):
        p = sub.add_parser(name)
        p.add_argument("--amulet-repo", default=os.environ.get("AMULET_REPO", str(ROOT / "work" / "amulet-repo")))
        p.add_argument("--amulet-py", default=os.environ.get("AMULET_PY", "python3"))
        p.add_argument("--rows", nargs="+", default=["T1g", "T2g", "T3g"])
        p.add_argument("--instances", type=int, default=inst)
        p.add_argument("--programs", type=int, default=200)
        p.add_argument("--inputs", type=int, default=70)
        p.add_argument("--jobs", type=int, default=18)
        p.add_argument("--cpus", default="" if inst else "0-31")
        p.add_argument("--max-busy", type=float, default=0.03)
        p.add_argument("--idle-wait-s", type=int, default=7200)
        p.add_argument("--no-idle-check", action="store_true")
        p.set_defaults(fn=fn)

    p = sub.add_parser("rounds")
    p.add_argument("--main", default="Footprint_6_u_main_A")
    p.add_argument("--rounds", nargs="+", type=int, default=[1, 2, 3])
    p.add_argument("--stage2-jobs", type=int, default=24)
    p.add_argument("--parallel", type=int, default=16)
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--gem5-timeout", type=int, default=900)
    p.set_defaults(fn=cmd_rounds)

    p = sub.add_parser("pool")
    p.add_argument("--main", default="Footprint_6_u_main_A")
    p.add_argument("--extra", default="Footprint_6_u_extra_A")
    p.add_argument("--rounds", nargs="+", type=int, default=[1, 2, 3])
    p.add_argument("--parallel", type=int, default=16)
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--gem5-timeout", type=int, default=900)
    p.set_defaults(fn=cmd_pool)

    p = sub.add_parser("compare")
    p.add_argument("--corpus", default="Footprint_6_u_main_A")
    p.add_argument("--kn", default="")
    p.add_argument("--gen", type=float, required=True)
    p.add_argument("--suffix", default="_fast")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("eval")
    p.add_argument("--rows", nargs="+", default=["E2", "E3", "E4", "E6"])
    p.add_argument("--model", default="")
    p.add_argument("--gem5-timeout", type=int, default=900)
    p.set_defaults(fn=cmd_eval)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

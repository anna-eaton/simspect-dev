#!/usr/bin/env python3
"""profile_test.py (agent testcost, 2026-11-16): where do a SimSpect test's CPU-seconds go?

Read-only on the production code: imports pipeline.py / gem5_common.py / cache_setup.py /
check_footprint.py from --code-root and wraps their functions IN THIS PROCESS ONLY with
rusage timers (no source file is edited). For each test it replays exactly the per-test path
of `pipeline.py gem5` (sweep grid point + stall injection = pipeline._enumerate_grid_for_corpus +
_materialise_grid_run, then gem5_common.process_one with check_footprint.check_footprint), and
records exclusive CPU per function: own Python CPU (RUSAGE_SELF) and child-process CPU
(RUSAGE_CHILDREN: as/ld/objdump/nm/gem5). Runs single-threaded so the deltas are attributable.

Per test it also records the trace composition (bytes, lines by kind) and gem5's own stats
(hostSeconds = time in the simulation loop; process CPU minus that = gem5 startup/config/teardown),
and, with --gem5-variants, replays the captured gem5 command with (a) no debug flags,
(b) O3PipeView only (no Commit), (c) a trivial exit-only binary, to split gem5 CPU into
startup / simulation / trace writing.

    cd <code-root> && nice -n 19 python3 profile_test.py --code-root . --config <cfg.jsonc> \
        --testset-model <testsets/<model>> --sample sample.tsv --n 15 --out <dir> [--gem5-variants]

Outputs in --out: profile.jsonl (one row per test), profile.log (start/end, every test, every
error with traceback), startup.json (python startup/import costs, if --startup).
"""
import argparse, json, os, resource, shutil, subprocess, sys, tempfile, time, traceback
from pathlib import Path

LOG = None


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOG:
        with open(LOG, "a") as f:
            f.write(line + "\n")


def ru():
    s = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (s.ru_utime + s.ru_stime, c.ru_utime + c.ru_stime, time.monotonic())


class Prof:
    """Exclusive (self, children, wall) per wrapped function name, with a call stack."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.acc = {}
        self.stack = []

    def wrap(self, mod, name, label=None):
        fn = getattr(mod, name)
        if getattr(fn, "_tc_wrapped", False):
            return
        label = label or f"{mod.__name__}.{name}"
        prof = self

        def w(*a, **kw):
            t0 = ru()
            prof.stack.append([0.0, 0.0, 0.0])   # time spent in nested wrapped calls
            try:
                return fn(*a, **kw)
            finally:
                t1 = ru()
                nested = prof.stack.pop()
                d = [t1[i] - t0[i] for i in range(3)]
                if prof.stack:
                    for i in range(3):
                        prof.stack[-1][i] += d[i]
                e = prof.acc.setdefault(label, [0.0, 0.0, 0.0, 0])
                for i in range(3):
                    e[i] += d[i] - nested[i]
                e[3] += 1
        w._tc_wrapped = True
        for attr in ("wants_trace",):
            if hasattr(fn, attr):
                setattr(w, attr, getattr(fn, attr))
        setattr(mod, name, w)
        return w


def trace_stats(p: Path) -> dict:
    out = dict(bytes=p.stat().st_size, lines=0, o3pv=0, simspect=0, commit=0, lsq=0, other=0)
    with open(p, errors="replace") as f:
        for line in f:
            out["lines"] += 1
            if "O3PipeView:simspect:" in line:
                out["simspect"] += 1
            elif "O3PipeView:" in line:
                out["o3pv"] += 1
            elif "system.cpu.commit" in line:
                out["commit"] += 1
            elif "system.cpu.iew.lsq" in line:
                out["lsq"] += 1
            else:
                out["other"] += 1
    return out


def gem5_stats(m5out: Path) -> dict:
    st = m5out / "stats.txt"
    out = {}
    if not st.exists():
        return out
    for line in st.read_text(errors="replace").splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] in ("hostSeconds", "host_seconds", "simTicks", "sim_ticks",
                                     "simInsts", "sim_insts", "hostInstRate", "host_inst_rate",
                                     "hostMemory", "host_mem_usage"):
            out.setdefault(p[0], float(p[1]))
    return out


def run_child(cmd, cwd):
    """Run a command, return (cpu_s, wall_s, rc) of that child via wait4."""
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _, sts, r = os.wait4(p.pid, 0)
    return round(r.ru_utime + r.ru_stime, 4), round(time.monotonic() - t0, 4), \
        (os.WEXITSTATUS(sts) if os.WIFEXITED(sts) else -1)


TRIVIAL_S = """\t.global _start
\t.text
_start:
\tmov $60, %rax
\txor %rdi, %rdi
\tsyscall
"""


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--testset-model", required=True)
    ap.add_argument("--sample", required=True, help="tsv: mode<TAB>stem")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gem5-variants", action="store_true")
    ap.add_argument("--startup", action="store_true")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOG = out / "profile.log"
    code = Path(a.code_root).resolve()
    tsm = Path(a.testset_model).resolve()
    a.sample = str(Path(a.sample).resolve())
    a.config = str(Path(a.config).resolve())
    log(f"START config={a.config} code={code} testset={tsm} n={a.n} variants={a.gem5_variants} "
        f"pid={os.getpid()} nice={os.nice(0)} loadavg={os.getloadavg()}")

    sys.path.insert(0, str(code))
    os.chdir(code)
    import pipeline as pl
    cfg = pl.load_config(Path(a.config))
    env = pl._build_gem5_env(cfg["gem5"], cfg.get("speculation", {}))
    for k, v in env.items():
        if k.startswith("SIMSPECT_"):
            os.environ[k] = v
    sys.path.insert(0, str(code / "STAGE3_gem5"))
    import gem5_common as gc
    import cache_setup as cs
    import check_footprint as cf
    cf._CRIT = cf.load_criterion(os.environ["SIMSPECT_CRITERION"])
    cf._ACTOR_OVERRIDE = os.environ.get("SIMSPECT_CRITERION_ACTOR")
    gc._scheme = int(cfg["gem5"].get("scheme", 2))
    sweep = cfg.get("sweep", {})
    unresolved_stall = int(sweep.get("unresolved_stall_cycles", 0))

    prof = Prof()
    for n in ("build_binary", "_func_base_addr", "_disasm", "_litmus_labels", "binary_has_resolve_hooks",
              "branch_force_plan", "_branch_ann_for_se", "_run_bounded", "parse_pipeview",
              "parse_commit_ticks", "parse_lsq", "parse_commit_squashes", "parse_branch_events",
              "parse_simspect_events", "parse_pipeview_by_seq", "parse_ticks_per_cycle",
              "execution_validity", "load_annotation", "collect_unresolved_branches",
              "fill_retire_from_commit"):
        prof.wrap(gc, n)
    for n in ("prepare", "transform_asm", "remap_annotation", "_nm", "_rows"):
        prof.wrap(cs, n)
    # check_footprint imported these names directly: route them to the wrapped gem5_common ones
    for n in ("parse_pipeview", "parse_pipeview_by_seq", "parse_simspect_events"):
        setattr(cf, n, getattr(gc, n))
    prof.wrap(cf, "evaluate")
    check = prof.wrap(cf, "check_footprint")

    captured = {}
    orig_rb = gc._run_bounded

    def cap_rb(cmd):
        captured["cmd"] = list(cmd)
        return orig_rb(cmd)
    cap_rb._tc_wrapped = True
    gc._run_bounded = cap_rb

    pairs = [l.split("\t")[:2] for l in Path(a.sample).read_text().splitlines() if l.strip()][:a.n]
    trivial_bin = None
    if a.gem5_variants:
        td = out / "_trivial"
        td.mkdir(exist_ok=True)
        (td / "t.s").write_text(TRIVIAL_S)
        subprocess.run(["as", "-o", str(td / "t.o"), str(td / "t.s")], check=True)
        subprocess.run(["ld", "-static", "-o", str(td / "trivial"), str(td / "t.o")], check=True)
        trivial_bin = td / "trivial"

    rows_f = out / "profile.jsonl"
    for i, (mode, stem) in enumerate(pairs):
        row = dict(i=i, mode=mode, stem=stem)
        try:
            gc._force_support.clear()      # per-process cache: production pays it once per test
            prof.reset()
            captured.clear()
            t0 = ru()
            tmp = Path(tempfile.mkdtemp(prefix="tc_", dir=str(out)))
            s_path = tsm / mode / "asm" / f"{stem}.s"
            ann_dir = tsm / mode / "ann"
            per_grid, manifest, mg = pl._enumerate_grid_for_corpus([s_path], ann_dir, sweep)
            files = pl._materialise_grid_run(per_grid[0], tmp / "variant", unresolved_stall)
            chk = tmp / "chk"
            chk.mkdir()
            shutil.copy(files[0], chk / files[0].name)
            shutil.copy(tmp / "variant" / f"{stem}.ann.json", chk / f"{stem}.ann.json")
            t1 = ru()
            r = gc.process_one(chk / f"{stem}.s", chk / f"{stem}.ann.json", check, keep_tmp=True)
            t2 = ru()
            row["stage_cpu"] = round(t1[0] - t0[0] + t1[1] - t0[1], 4)
            row["process_one_self"] = round(t2[0] - t1[0], 4)
            row["process_one_children"] = round(t2[1] - t1[1], 4)
            row["process_one_wall"] = round(t2[2] - t1[2], 4)
            row["funcs"] = {k: [round(v[0], 4), round(v[1], 4), round(v[2], 4), v[3]]
                            for k, v in sorted(prof.acc.items())}
            row["status"] = r.get("status")
            row["issued_in_window"] = r.get("issued_in_window")
            row["leak"] = r.get("leak")
            row["terms_fired"] = r.get("terms_fired")
            row["cache_setup"] = r.get("cache_setup")
            row["error"] = (r.get("error") or "")[:300] or None
            wd = Path(r["workdir"]) if r.get("workdir") else None
            if wd and (wd / "m5out" / "pipeview.txt").exists():
                row["trace"] = trace_stats(wd / "m5out" / "pipeview.txt")
                row["gem5_stats"] = gem5_stats(wd / "m5out")
            if a.gem5_variants and captured.get("cmd") and wd:
                cmd = captured["cmd"]
                gdir = os.environ.get("SIMSPECT_GEM5_DIR")
                var = {}

                def mk(drop_dbg=False, dbg=None, binary=None):
                    c = []
                    for x in cmd:
                        if x.startswith("--outdir="):
                            vd = wd / f"var_{len(var)}"
                            vd.mkdir(exist_ok=True)
                            c.append(f"--outdir={vd}")
                        elif x.startswith("--debug-flags="):
                            if drop_dbg:
                                continue
                            c.append(f"--debug-flags={dbg}" if dbg else x)
                        elif x.startswith("--debug-file=") and drop_dbg:
                            continue
                        elif x.startswith("--cmd=") and binary:
                            c.append(f"--cmd={binary}")
                        elif binary and x.startswith(("--branch-ann-file=", "--branch-ann-base=",
                                                      "--fnc-commit-stall")):
                            continue
                        else:
                            c.append(x)
                    return c
                var["same"] = run_child(mk(), gdir)
                var["no_trace"] = run_child(mk(drop_dbg=True), gdir)
                var["o3pv_only"] = run_child(mk(dbg="O3PipeView"), gdir)
                var["trivial_bin_no_trace"] = run_child(mk(drop_dbg=True, binary=trivial_bin), gdir)
                row["gem5_variants"] = var
            if wd:
                shutil.rmtree(wd, ignore_errors=True)
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            row["exc"] = traceback.format_exc()[-1500:]
            log(f"ERROR test {i} {mode}/{stem}:\n{row['exc']}")
        with open(rows_f, "a") as f:
            f.write(json.dumps(row) + "\n")
        log(f"test {i} {mode}/{stem} cs={row.get('cache_setup')} status={row.get('status')} "
            f"iiw={row.get('issued_in_window')} self={row.get('process_one_self')} "
            f"children={row.get('process_one_children')} trace_lines={(row.get('trace') or {}).get('lines')}")

    if a.startup:
        st = {}
        py = sys.executable
        envc = os.environ.copy()
        def rep(cmd, k, n=5, cwd=str(code)):
            vals = []
            for _ in range(n):
                t0 = time.monotonic()
                p = subprocess.Popen(cmd, cwd=cwd, env=envc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                _, sts, r = os.wait4(p.pid, 0)
                vals.append(r.ru_utime + r.ru_stime)
            st[k] = round(sorted(vals)[len(vals) // 2], 4)
        rep([py, "-c", "pass"], "python_bare")
        rep([py, "-c", "import sys; sys.path.insert(0,'.'); import pipeline"], "import_pipeline")
        rep([py, "-c", "import sys; sys.path.insert(0,'STAGE3_gem5'); import check_footprint"],
            "import_check_footprint_with_env")
        rep([py, "-c", "import sys; sys.path.insert(0,'STAGE3_gem5'); import gem5_common as g; "
                       "g.binary_has_resolve_hooks(g.GEM5_BIN)"], "import_gc_plus_resolve_hook_scan")
        for tool in (["as", "--version"], ["objdump", "--version"]):
            rep(tool, "exec_" + tool[0])
        (out / "startup.json").write_text(json.dumps(st, indent=1))
        log(f"startup {st}")
    log(f"END loadavg={os.getloadavg()}")


if __name__ == "__main__":
    main()

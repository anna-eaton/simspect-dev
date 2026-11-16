#!/usr/bin/env python3
"""micro_gem5.py (agent testcost, 2026-11-16): split gem5's fixed per-process cost.

For one run config, runs gem5 (CPU from os.wait4) on an exit-only static binary with the run's exact
se.py command line (as gem5_common.run_gem5 builds it, minus the per-test --branch-ann-file /
--fnc-commit-stall flags), plus: a no-op config script (binary load + embedded-Python init only),
and the full command with --dump-config= --json-config= (no config.ini/config.json written).
Median of --reps runs each. Read-only: writes only under --out.

    nice -n 19 python3 micro_gem5.py --code-root <code> --config <cfg.jsonc> --out <dir> [--reps 5]
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

TRIVIAL_S = "\t.global _start\n\t.text\n_start:\n\tmov $60, %rax\n\txor %rdi, %rdi\n\tsyscall\n"


def run(cmd, cwd):
    t0 = time.monotonic()
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _, sts, r = os.wait4(p.pid, 0)
    return r.ru_utime + r.ru_stime, time.monotonic() - t0, (os.WEXITSTATUS(sts) if os.WIFEXITED(sts) else -1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    cfgp = Path(a.config).resolve()
    sys.path.insert(0, str(Path(a.code_root).resolve()))
    os.chdir(a.code_root)
    import pipeline as pl
    cfg = pl.load_config(cfgp)
    env = pl._build_gem5_env(cfg["gem5"], cfg.get("speculation", {}))
    gbin, se, cpu = env["SIMSPECT_GEM5_BIN"], env["SIMSPECT_SE_CONFIG"], env.get("SIMSPECT_GEM5_CPU", "X86O3CPU")
    gdir = env.get("SIMSPECT_GEM5_DIR")
    extra = [x for x in env.get("SIMSPECT_GEM5_EXTRA", "").split("\x1f") if x]
    (out / "t.s").write_text(TRIVIAL_S)
    subprocess.run(["as", "-o", str(out / "t.o"), str(out / "t.s")], check=True)
    subprocess.run(["ld", "-static", "-o", str(out / "trivial"), str(out / "t.o")], check=True)
    (out / "noop.py").write_text("print(1)\n")
    base = [f"--cmd={out / 'trivial'}", f"--cpu-type={cpu}", "--caches",
            f"--scheme={cfg['gem5'].get('scheme', 2)}", "--abs-max-tick=100000000000"] + extra
    variants = {
        "noop_config_script": [gbin, f"--outdir={out}/o_noop", str(out / "noop.py")],
        "trivial_bin_full_cfg": [gbin, f"--outdir={out}/o_full", str(se)] + base,
        "trivial_bin_no_cfg_dump": [gbin, f"--outdir={out}/o_nodump", "--dump-config=", "--json-config=",
                                    str(se)] + base,
    }
    res = {}
    for k, cmd in variants.items():
        vals = [run(cmd, gdir) for _ in range(a.reps)]
        cpu_s = sorted(v[0] for v in vals)
        res[k] = dict(cpu_median=round(cpu_s[len(cpu_s) // 2], 4), cpu_all=[round(v[0], 4) for v in vals],
                      rc=[v[2] for v in vals])
    res["gem5_bin"] = gbin
    res["gem5_bin_bytes"] = os.path.getsize(gbin)
    (out / "micro.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res))


if __name__ == "__main__":
    main()

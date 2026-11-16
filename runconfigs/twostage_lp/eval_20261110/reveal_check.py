#!/usr/bin/env python3
"""reveal_check.py -- did a ReCon reveal untaint happen in a hit's run? (regen-lp, 2026-11-10; method of e2-losttaint's
run.py, verdict E2LT-3: reveal untaints enabled by a Stage-2 committed load pair/alias on rsp+0 are a harness artifact).
Faithful rerun of the given (mode, stem) keys with the campaign config verbatim except paths, keep_tmp=true, jobs,
branch_modes=[mode] and no sample_fraction (TMPDIR=/tmp/rv_<mode>, short like the campaign's /tmp), then reads each
test's gem5 stats.txt: system.cpu.lsq0.revealRequests and allowlistedTaintsFromTT (summed over grid points).
Output JSON "<mode>/<stem>" -> {revealRequests, allowlistedTaintsFromTT, n_stats}. Workdirs are deleted afterwards.
Run from the eval code root. Usage: reveal_check.py --config <row config> --model <corpus> --keys <file> --out <json> [--jobs 8]"""
import argparse, glob, json, os, re, shutil, subprocess, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--keys", required=True); ap.add_argument("--out", required=True); ap.add_argument("--jobs", type=int, default=8)
ap.add_argument("--work", default="/tests/simspect_alloy_20261108/loosepin_regen/bugwork/reveal"); a = ap.parse_args()
TS = Path("/tests/simspect_alloy_20261108/testsets_twostage"); W = Path(a.work); W.mkdir(parents=True, exist_ok=True)
keys = [tuple(l.strip().split("/", 1)) for l in open(a.keys) if l.strip()]
res = json.loads(Path(a.out).read_text()) if Path(a.out).exists() else {}
cfg0 = json.loads(re.sub(r"//[^\n]*", "", open(a.config).read()))
log = open(W / "reveal_check.log", "a")
for mode in sorted({m for m, _ in keys}):
    stems = [s for m, s in keys if m == mode and f"{m}/{s}" not in res]
    if not stems:
        continue
    stage = W / "stage" / mode; resd = W / "res" / mode; tmp = Path(f"/tmp/rv_{mode[11:]}")
    for d in (stage, resd, tmp):
        shutil.rmtree(d, ignore_errors=True)
    for sub in ("asm", "ann"):
        (stage / a.model / mode / sub).mkdir(parents=True)
    for s in stems:
        os.symlink(TS / a.model / mode / "asm" / f"{s}.s", stage / a.model / mode / "asm" / f"{s}.s")
        os.symlink(TS / a.model / mode / "ann" / f"{s}.ann.json", stage / a.model / mode / "ann" / f"{s}.ann.json")
    resd.mkdir(parents=True); tmp.mkdir(parents=True)
    cfg = json.loads(json.dumps(cfg0))
    cfg["paths"].update(testset_dir=str(stage), results_dir=str(resd), results_name="rv")
    cfg.setdefault("pipeline", {})["keep_tmp"] = True
    cfg["gem5"]["jobs"] = a.jobs; cfg["gem5"].pop("sample_fraction", None); cfg["speculation"]["branch_modes"] = [mode]
    (stage / "cfg.json").write_text(json.dumps(cfg, indent=1))
    rc = subprocess.run([sys.executable, "-u", "pipeline.py", "gem5", "--model", a.model, "--config", str(stage / "cfg.json"), "--force"],
                        env=dict(os.environ, TMPDIR=str(tmp)), stdout=log, stderr=subprocess.STDOUT).returncode
    log.write(f"{mode}: {len(stems)} stems rc={rc}\n")
    for s in stems:
        rr = al = n = 0
        for st in sorted(set(glob.glob(f"{tmp}/**/gem5_{s}_*/**/stats.txt", recursive=True) + glob.glob(f"{tmp}/**/{s}*/**/stats.txt", recursive=True))):
            t = open(st).read(); n += 1
            rr += sum(int(x) for x in re.findall(r"revealRequests\s+(\d+)", t))
            al += sum(int(x) for x in re.findall(r"allowlistedTaintsFromTT\s+(\d+)", t))
        res[f"{mode}/{s}"] = dict(revealRequests=rr, allowlistedTaintsFromTT=al, n_stats=n)
    shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(stage, ignore_errors=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
print(f"{len(res)} keys in {a.out}")

#!/usr/bin/env python3
"""twostage_lp.py -- the production two-stage, core-pinned, loose-pin generation path (regen-lp, 2026-11-10).

Anna 2026-11-10: "make sure the loose pin and the ultimate are in the production path. and the skeleton enumeration."
One command runs, streaming:
  Stage 1    skeleton enumeration: the family's RI core model (STAGE1_alloy/models/<F>_core_ri.als) split into disjoint
             partitions (partition_stage1.py) and enumerated (launch_stage1.py: a6CountModels per partition, cap,
             timeout, disk guard, status JSON).
  Stage 1.5  as soon as every partition below twostage_lp.stage1.wait_k has ended: stage15lp.py over the cores found so
             far: one model per distinct core = <F>_lpP.als (loose pin, but 8, committed region, prefix IX, no-junk,
             production minimality) + that core as a path-style seed_core; seeded random order (alloy_solver_order),
             shuffled core queue, adaptive per-core budget, cross-core fingerprint dedup.
  Stage 2    stream_fp.py: merge finished Stage-1.5 jobs, stage2_sharded.py with the recipe config (v3:
             runconfigs/regen_lp_20261110/stage2_fv3.jsonc, OTB off), then per batch make_rmw_corpus.py --select
             eligible p 0.5 and make_jmp_corpus.py p 0.5 (uniform), published atomically with MANIFEST.tsv,
             rmw_stems.tsv, jmp_stems.tsv, PROVENANCE.json (CPU-s per stage) and READY at the end.
Nothing here changes pipeline.py / testsetgen.py: old configs behave byte-identically.

Config (JSONC), e.g. runconfigs/twostage_lp/Footprint_6_u.jsonc:
  "paths": {"testset_dir": "/tests/.../testsets_twostage"},
  "twostage_lp": {"family": "Footprint_6_u", "core_model": "Footprint_6_u_core_ri", "lp_model": "Footprint_6_u_lpP",
                  "corpus": "Footprint_6_u_core_lpP_fv3", "stage2_config": "runconfigs/regen_lp_20261110/stage2_fv3.jsonc",
                  "stage1": {"jobs": 8, "cap": 200000, "timeout_s": 10800, "xmx": "8g", "wait_k": 6},
                  "stage15": {"slots": 40, "job_timeout": 300, "budget_s": 5400, "cap": 25, "walk_p": 0.05,
                              "shuffle_seed": 20261110, "spread": 2, "dedup_level": "seed", "xmx": "4g"},
                  "stream": {"interval": 120, "jobs": 24, "min_batch": 50, "max_batch": 150}}
Usage (inside gem5_dev on a cafe node, from the code root):
  python3 twostage_lp.py --config runconfigs/twostage_lp/Footprint_6_u.jsonc --ws /tests/<dir>/twostage_lp_Footprint_6_u
  (make twostage-lp CONFIG=... WS=...). Log: <ws>/logs/twostage_lp.log; every sub-tool logs under <ws>/logs and <ws>/stage1/logs.
"""
import argparse, datetime as dt, json, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LP = ROOT / "STAGE1_alloy/models/proposed/ultimate/loosepin"
PT = ROOT / "STAGE1_alloy/models/proposed_twophase"


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load(p):
    t = Path(p).read_text()
    return json.loads(re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--ws", required=True)
    a = ap.parse_args()
    cfg = load(a.config); T = cfg["twostage_lp"]; ws = Path(a.ws).resolve()
    for d in ("logs", "stage1/parts", "stage1/logs", "runs15", "cfg"):
        (ws / d).mkdir(parents=True, exist_ok=True)
    logf = open(ws / "logs" / "twostage_lp.log", "a", buffering=1)
    def log(m):
        logf.write(f"{now()} {m}\n"); print(m, flush=True)
    models = ROOT / "STAGE1_alloy/models"
    core, lp = models / f"{T['core_model']}.als", models / f"{T['lp_model']}.als"
    log(f"START config={a.config} ws={ws} core={core} lp={lp} corpus={T['corpus']}")
    # Stage 1
    s1 = T.get("stage1", {}); fam = T["core_model"]
    if not (ws / "stage1/parts" / fam / "partitions.json").exists():
        subprocess.run([sys.executable, str(PT / "partition_stage1.py"), str(core), str(ws / "stage1/parts" / fam)], check=True)
    link = ws / "stage1/STAGE1_alloy"
    if not link.exists():
        link.symlink_to(ROOT / "STAGE1_alloy")
    st1 = subprocess.Popen([sys.executable, "-u", str(PT / "launch_stage1.py"), "--ws", str(ws / "stage1"), "--families", fam,
                            "--jobs", str(s1.get("jobs", 8)), "--cap", str(s1.get("cap", 200000)),
                            "--timeout", str(s1.get("timeout_s", 10800)), "--xmx", s1.get("xmx", "8g")],
                           stdout=open(ws / "logs/launch_stage1.out", "a"), stderr=subprocess.STDOUT)
    log(f"stage1 launched pid={st1.pid}")
    parts = json.loads((ws / "stage1/parts" / fam / "partitions.json").read_text())["partitions"]
    wait = [p["name"] for p in parts if p["k"] < s1.get("wait_k", 6)]
    def ended(name):
        lg = ws / "stage1/logs" / f"{fam}__{name}.log"
        return lg.exists() and "VERDICT=" in lg.read_text(errors="replace")
    while not all(ended(n) for n in wait):
        if st1.poll() is not None and not all(ended(n) for n in wait):
            log("stage1 launcher exited before the waited partitions ended"); break
        time.sleep(30)
    cores = [str(ws / "stage1/out" / fam / p["name"] / "stage1_xml") for p in parts
             if p["name"] in wait and (ws / "stage1/out" / fam / p["name"] / "stage1_xml").exists()]
    log(f"stage1 partitions below k={s1.get('wait_k', 6)} ended; Stage 1.5 starts on {cores} (larger partitions keep running; "
        "their cores are not used by this run)")
    # Stage 1.5
    s15 = T.get("stage15", {}); out15 = ws / "runs15" / T["lp_model"]
    p15 = subprocess.Popen([sys.executable, "-u", str(LP / "stage15lp.py"), "--base", str(lp), "--cores", *cores, "--out", str(out15),
                            "--code", str(ROOT), "--slots", str(s15.get("slots", 40)), "--job-timeout", str(s15.get("job_timeout", 300)),
                            "--budget-s", str(s15.get("budget_s", 5400)), "--cap", str(s15.get("cap", 25)),
                            "--walk-p", str(s15.get("walk_p", 0.05)), "--xmx", s15.get("xmx", "4g"),
                            "--spread", str(s15.get("spread", 2)), "--dedup-level", s15.get("dedup_level", "seed")]
                           + (["--shuffle-seed", str(s15["shuffle_seed"])] if "shuffle_seed" in s15 else []),
                           stdout=open(ws / "logs/stage15lp.out", "a"), stderr=subprocess.STDOUT)
    log(f"stage15lp launched pid={p15.pid} out={out15}")
    # Stage 2 stream: recipe config with ONLY paths.testset_dir made absolute (and gem5.jobs = asm compile threads)
    src = ROOT / T["stage2_config"]; txt = src.read_text(); sm = T.get("stream", {})
    txt2 = re.sub(r'"testset_dir"\s*:\s*"[^"]*"', f'"testset_dir": "{cfg["paths"]["testset_dir"]}"', txt, count=1)
    txt2 = re.sub(r'"jobs"\s*:\s*\d+', f'"jobs": {sm.get("jobs", 24)}', txt2, count=1)
    scfg = ws / "cfg" / f"{src.stem}_stream.jsonc"
    scfg.write_text(f"// twostage_lp.py {now()}: copy of {src} with only paths.testset_dir and gem5.jobs (asm threads) changed\n" + txt2)
    ps = subprocess.Popen([sys.executable, "-u", str(LP / "stream_fp.py"), "--s15", str(out15), "--base-name", T["corpus"] + "_base",
                           "--final-name", T["corpus"], "--cfg", str(scfg), "--code", str(ROOT), "--ts-dir", cfg["paths"]["testset_dir"],
                           "--ws", str(ws), "--stage1-logs", f"stage1/logs/{fam}__*.log", "--family-label", T["family"],
                           "--interval", str(sm.get("interval", 120)), "--jobs", str(sm.get("jobs", 24)),
                           "--min-batch", str(sm.get("min_batch", 50)), "--max-batch", str(sm.get("max_batch", 150))],
                          stdout=open(ws / "logs/stream_fp.out", "a"), stderr=subprocess.STDOUT)
    log(f"stream_fp launched pid={ps.pid}")
    rc15 = p15.wait(); log(f"stage15lp ended rc={rc15}")
    rcs = ps.wait(); log(f"stream_fp ended rc={rcs} (READY: {(Path(cfg['paths']['testset_dir']) / T['corpus'] / 'READY').exists()})")
    log("END (Stage-1 partitions at or above wait_k may still be running under launch_stage1.py)")


if __name__ == "__main__":
    main()

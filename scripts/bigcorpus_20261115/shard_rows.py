#!/usr/bin/env python3
"""shard_rows.py -- run one testrun row over disjoint stem shards on several hosts (agent bigcorpus, 2026-11-16). Copy of the idea of
runconfigs/twostage_lp/eval_20261110/shard_eval.py (testrun is GIL-bound, so K processes over disjoint shards run K-way parallel);
checker, gem5_common and testrun.py unchanged.

Stems = the corpus MANIFEST.tsv stems (published in every mode listed), sorted, dealt round-robin into --k shards; this host runs the
shards listed in --mine (e.g. 0-11). Shard s: testset <ts>/<corpus>__<name>_sh<s>/<mode>/{asm,ann} = symlinks to the corpus files
(+ SHARD_STEMS.tsv), config <code>/runconfigs/bigcorpus_20261115/shards/<name>_sh<s>.jsonc = the row config with ONLY
paths.results_name (<name>_sh<s>) changed, and one tmux window in session bc_shards running
`testrun.py --config <cfg> --model <shard testset> --once --max-new 100000` under `nice -n <nice>` (log <O>/logs/shard_<name>_sh<s>.log).
Gate later with STAGE3_gem5/bugs/classify.py gate --campaigns <json listing results_name <name>, model <corpus>> (it merges
results/<name>_sh*__latest and reports duplicates / missing).
Usage (code root, gem5_dev): shard_rows.py --corpus STT_6_u_core_lpP_s2A --config runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc \
    --name bc_E2w_STT_6_u_core_lpP_s2A --k 36 --mine 0-11 [--nice 19] [--dry]
"""
import argparse, json, os, re, subprocess
from pathlib import Path

O = Path("/tests/bigcorpus_20261115"); TS = O / "testsets"; MODES = ("mispredict_not_taken", "mispredict_taken")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True); ap.add_argument("--config", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--k", type=int, required=True); ap.add_argument("--mine", required=True); ap.add_argument("--nice", type=int, default=0)
    ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    lo, hi = (int(x) for x in a.mine.split("-")); corp = TS / a.corpus
    rows = [l.split("\t") for l in (corp / "MANIFEST.tsv").read_text().splitlines()[1:] if l.strip()]
    stems = sorted({r[0] for r in rows})
    cfgtxt = Path(a.config).read_text()
    (Path("runconfigs/bigcorpus_20261115/shards")).mkdir(parents=True, exist_ok=True)
    O.joinpath("logs").mkdir(exist_ok=True)
    if not a.dry:
        subprocess.run("tmux has-session -t bc_shards 2>/dev/null || tmux new-session -d -s bc_shards -n ctl", shell=True)
    for s in range(lo, hi + 1):
        mine = stems[s::a.k]; tsn = f"{a.corpus}__{a.name}_sh{s}"; d = TS / tsn
        n = 0
        for m in MODES:
            for sub, ext in (("asm", ".s"), ("ann", ".ann.json")):
                (d / m / sub).mkdir(parents=True, exist_ok=True)
                for st in mine:
                    src = corp / m / sub / f"{st}{ext}"; dst = d / m / sub / f"{st}{ext}"
                    if src.exists() and not dst.exists():
                        os.symlink(src, dst); n += 1
        if not (d / "xml").exists():
            os.symlink(corp / "xml", d / "xml")
        (d / "SHARD_STEMS.tsv").write_text("mode\tstem\n" + "".join(f"{m}\t{st}\n" for m in MODES for st in mine))
        rn = f"{a.name}_sh{s}"
        cfg = re.sub(r'"results_name"\s*:\s*"[^"]*"', f'"results_name": "{rn}"', cfgtxt, count=1)
        cp = Path(f"runconfigs/bigcorpus_20261115/shards/{rn}.jsonc")
        cp.write_text(f"// shard_rows.py: copy of {a.config} with ONLY paths.results_name = {rn} (shard {s} of {a.k}, {len(mine)} stems)\n" + cfg)
        cmd = (f"cd {Path.cwd()} && export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 && nice -n {a.nice} python3 -u testrun.py --config {cp} "
               f"--model {tsn} --once --max-new 100000 >> {O}/logs/shard_{rn}.log 2>&1; echo EXIT rc=$? $(date -u) >> {O}/logs/shard_{rn}.log")
        print(f"shard {s}: {len(mine)} stems, {n} links, testset {tsn}, config {cp}")
        if not a.dry:
            subprocess.run(["tmux", "new-window", "-d", "-t", "bc_shards", "-n", f"sh{s}", cmd], check=True)


if __name__ == "__main__":
    main()

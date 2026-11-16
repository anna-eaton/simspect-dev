#!/usr/bin/env python3
"""shard_stl.py -- run the store-shadow ReCon row over disjoint stem shards on several hosts (agent reconstlhook, 2026-11-16).
Copy of scripts/bigcorpus_20261115/shard_rows.py with ONLY the root dir, the mode list (stl_bypass) and the tmux session name changed;
checker, gem5_common and testrun.py are the run's code snapshot (<O>/code/SNAPSHOT.md5).

Stems = the corpus MANIFEST.tsv stems that have both .s and .ann.json in stl_bypass, sorted, dealt round-robin into --k shards; this
host runs the shards in --mine (e.g. 0-11). Shard s: testset <O>/testsets/<corpus>__<name>_sh<s>/stl_bypass/{asm,ann} = symlinks
into <O>/testsets/<corpus> (+ SHARD_STEMS.tsv), config <code>/runconfigs/reconstl_20261116/shards/<name>_sh<s>.jsonc = the row config
with ONLY paths.results_name changed, one tmux window in session rstl_shards running testrun.py --once (log <O>/logs/shard_<name>_sh<s>.log,
ends with an EXIT rc= line). Usage (in <O>/code, gem5_dev):
  shard_stl.py --corpus Recon_6_u_stl_core_lpP_s2A --config runconfigs/reconstl_20261116/E2wstl_Recon_6_u_stl_core_lpP_s2A.jsonc \
      --name rstl_E2w_Recon_6_u_stl_core_lpP_s2A --k 20 --mine 0-11 [--nice 10] [--dry]
"""
import argparse, os, re, subprocess
from pathlib import Path

O = Path("/tests/reconstlhook_20261116"); TS = O / "testsets"; MODES = ("stl_bypass",)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True); ap.add_argument("--config", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--k", type=int, required=True); ap.add_argument("--mine", required=True); ap.add_argument("--nice", type=int, default=10)
    ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    lo, hi = (int(x) for x in a.mine.split("-")); corp = TS / a.corpus
    rows = [l.split("\t") for l in (corp / "MANIFEST.tsv").read_text().splitlines()[1:] if l.strip()]
    stems = sorted(r[0] for r in rows if all((corp / m / "asm" / f"{r[0]}.s").exists() and (corp / m / "ann" / f"{r[0]}.ann.json").exists()
                                             for m in MODES))
    print(f"{len(rows)} manifest stems, {len(stems)} with asm+ann in {MODES}")
    cfgtxt = Path(a.config).read_text()
    Path("runconfigs/reconstl_20261116/shards").mkdir(parents=True, exist_ok=True)
    (O / "logs").mkdir(exist_ok=True)
    if not a.dry:
        subprocess.run("tmux has-session -t rstl_shards 2>/dev/null || tmux new-session -d -s rstl_shards -n ctl", shell=True)
    for s in range(lo, hi + 1):
        mine = stems[s::a.k]; tsn = f"{a.corpus}__{a.name}_sh{s}"; d = TS / tsn
        n = 0
        for m in MODES:
            for sub, ext in (("asm", ".s"), ("ann", ".ann.json")):
                (d / m / sub).mkdir(parents=True, exist_ok=True)
                for st in mine:
                    src = corp / m / sub / f"{st}{ext}"; dst = d / m / sub / f"{st}{ext}"
                    if src.exists() and not dst.exists():
                        os.symlink(os.path.realpath(src), dst); n += 1
        (d / "SHARD_STEMS.tsv").write_text("mode\tstem\n" + "".join(f"{m}\t{st}\n" for m in MODES for st in mine))
        rn = f"{a.name}_sh{s}"
        cfg = re.sub(r'"results_name"\s*:\s*"[^"]*"', f'"results_name": "{rn}"', cfgtxt, count=1)
        cp = Path(f"runconfigs/reconstl_20261116/shards/{rn}.jsonc")
        cp.write_text(f"// shard_stl.py: copy of {a.config} with ONLY paths.results_name = {rn} (shard {s} of {a.k}, {len(mine)} stems)\n" + cfg)
        cmd = (f"cd {Path.cwd()} && export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 && nice -n {a.nice} python3 -u testrun.py --config {cp} "
               f"--model {tsn} --once --max-new 100000 >> {O}/logs/shard_{rn}.log 2>&1; echo EXIT rc=$? $(date -u) >> {O}/logs/shard_{rn}.log")
        print(f"shard {s}: {len(mine)} stems, {n} links, testset {tsn}, config {cp}")
        if not a.dry:
            subprocess.run(["tmux", "new-window", "-d", "-t", "rstl_shards", "-n", f"sh{s}", cmd], check=True)


if __name__ == "__main__":
    main()

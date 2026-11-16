#!/usr/bin/env python3
"""TIME-1 (agent timing, 2026-11-15): draw the fixed random SimSpect timing sample from the big corpus.

Run on cafe3 (gem5_dev) against the code snapshot that runs the big-corpus T1g/T2g/T3g rows:
    python3 make_sample.py --code-root /tests/bigcorpus_20261115/code \
        --testset /tests/bigcorpus_20261115/testsets/Footprint_6_u_core_lpP_s2A --n 1000 --seed 20261115 --out <dir>
Candidates = the (mode, stem) pairs that firstdet_stream.py would run right now (asm + ann present, listed in
MANIFEST.tsv, passing provenance_ok); the corpus is still streaming, so this is the set complete at draw time.
Sample = random.Random(seed).sample(sorted(candidates), n). Writes <out>/sample.tsv (mode<TAB>stem),
<out>/files.txt (relative paths to copy), <out>/sample_meta.json (seed, counts, kinds, draw time).
"""
import argparse, json, random, sys, time, collections
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--code-root", required=True)
ap.add_argument("--testset", required=True)
ap.add_argument("--n", type=int, default=1000)
ap.add_argument("--seed", type=int, default=20261115)
ap.add_argument("--out", required=True)
a = ap.parse_args()
sys.path.insert(0, str(Path(a.code_root) / "STAGE3_gem5" / "timing"))
import firstdet_stream as fs  # noqa: E402

ts = Path(a.testset)
modes = ["mispredict_not_taken", "mispredict_taken"]
av = fs.available(ts, modes, True)
cand, bad = [], 0
for m, s in sorted(av):
    ok, _ = fs.provenance_ok(json.loads((ts / m / "ann" / f"{s}.ann.json").read_text()))
    if ok:
        cand.append((m, s))
    else:
        bad += 1
smp = random.Random(a.seed).sample(cand, a.n)
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "sample.tsv").write_text("".join(f"{m}\t{s}\n" for m, s in smp))
files = ["MANIFEST.tsv", "PROVENANCE.json"]
for m, s in smp:
    files += [f"{m}/asm/{s}.s", f"{m}/ann/{s}.ann.json"]
(out / "files.txt").write_text("\n".join(files) + "\n")
kinds = collections.Counter(json.loads((ts / m / "ann" / f"{s}.ann.json").read_text()).get("xmit", {}).get("kind") for m, s in smp)
meta = dict(testset=str(ts), seed=a.seed, n=a.n, candidates=len(cand), failed_provenance=bad,
            complete_pairs=len(av), distinct_stems_in_sample=len({s for _, s in smp}),
            modes=dict(collections.Counter(m for m, _ in smp)), xmit_kinds=dict(kinds),
            ready_at_draw=(ts / "READY").exists(), drawn_utc=time.strftime("%F %T", time.gmtime()))
(out / "sample_meta.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta, indent=1))

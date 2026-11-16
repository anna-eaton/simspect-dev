#!/usr/bin/env python3
"""merge_xml.py — build one deduplicated XML set per footprint-model family from the flat runs.

Inputs : results/footprint_models_20261109/flat/<Model>/<seed>/inst-*.{xml,txt}   (scripts/footprint_testsets/gen_xml.sh)
Checks : (1) every run in runs.jsonl ended CAPPED or EXHAUSTED; (2) the default-order output of the three models
         of a family is identical instance by instance (sha256 of each inst-*.txt), which shows the three files
         define the same problem (their code is identical; only comments differ).
Output : testsets/<Model>/xml/inst-NNNNNN.{xml,txt} for each of the three models of the family (hard links to one
         copy), deduplicated across solver orders by census_flat.fingerprint (isomorphism: program order, flags,
         operand slots with canonical state sharing, rf and ddi edges); provenance.tsv = new name, seed, source
         file, fingerprint sha1. Refuses to overwrite a non-empty testsets/<Model>/xml/.
Usage  : merge_xml.py branch|stl   (log appended to results/footprint_models_20261109/merge_xml.log)
"""
import hashlib, json, os, sys, datetime as dt
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
W = REPO / "results/footprint_models_20261109"
sys.path.insert(0, str(REPO / "STAGE1_alloy/models/proposed/singlestage/tools"))
import census_flat as cf  # noqa: E402
FAM = {"branch": ["InvisiSpec_6", "CleanupSpec_6", "SpecLFB_6"],
       "stl": ["InvisiSpec_6_stl", "CleanupSpec_6_stl", "SpecLFB_6_stl"]}
log = open(W / "merge_xml.log", "a", buffering=1)
def L(m):
    line = f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {m}"
    log.write(line + "\n"); print(line, flush=True)
def die(m):
    L("ERROR " + m); sys.exit(1)
fam = sys.argv[1] if len(sys.argv) > 1 else die("usage: merge_xml.py branch|stl")
models = FAM[fam]; lead = models[0]
L(f"START family={fam} models={models}")
for m in models:
    runs = [json.loads(l) for l in (W / "flat" / m / "runs.jsonl").read_text().splitlines() if l.strip()]
    bad = [r for r in runs if r["verdict"] not in ("CAPPED", "EXHAUSTED")]
    if bad: die(f"{m}: runs not CAPPED/EXHAUSTED: {bad}")
    L(f"{m}: " + ", ".join(f"seed {r['seed']} {r['instances']} {r['verdict']} {r['secs']}s" for r in runs))
# (2) identity of the default-order outputs
def digests(d): return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("inst-*.txt"))}
ref = digests(W / "flat" / lead / "default")
for m in models[1:]:
    got = digests(W / "flat" / m / "default")
    if got != ref:
        diff = sorted(k for k in set(ref) | set(got) if ref.get(k) != got.get(k))
        die(f"default-order output of {m} differs from {lead} in {len(diff)} files, e.g. {diff[:5]}")
    L(f"identical default-order output: {m} == {lead} ({len(ref)} instances)")
# dedup across solver orders of the lead model
seeds = sorted((p.name for p in (W / "flat" / lead).iterdir() if p.is_dir()), key=lambda s: (s != "default", s))
seen, keep, per_seed = {}, [], {}
for s in seeds:
    files = sorted((W / "flat" / lead / s).glob("inst-*.txt")); new = 0
    for t in files:
        fp = hashlib.sha1(repr(cf.fingerprint(cf.load(t))).encode()).hexdigest()
        if fp in seen: continue
        seen[fp] = t; keep.append((s, t, fp)); new += 1
    per_seed[s] = (len(files), new)
    L(f"seed {s}: {len(files)} instances, {new} new distinct programs")
L(f"distinct programs over all orders: {len(keep)}")
first = REPO / "testsets" / lead / "xml"
for m in models:
    out = REPO / "testsets" / m / "xml"
    if out.exists() and any(out.iterdir()): die(f"{out} is not empty; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
with open(W / f"provenance_{fam}.tsv", "w") as prov:
    prov.write("name\tseed\tsource\tfingerprint_sha1\n")
    for n, (s, t, fp) in enumerate(keep, 1):
        name = f"inst-{n:06d}"
        for m in models:
            out = REPO / "testsets" / m / "xml"
            for ext in (".xml", ".txt"):
                src = t.with_suffix(ext) if m == lead else first / (name + ext)
                os.link(src, out / (name + ext))
        prov.write(f"{name}\t{s}\t{t.relative_to(REPO)}\t{fp}\n")
for m in models:
    (REPO / "testsets" / m / "xml" / "PROVENANCE.tsv").write_bytes((W / f"provenance_{fam}.tsv").read_bytes())
L(f"END wrote {len(keep)} instances to testsets/{{{','.join(models)}}}/xml/ (hard links), provenance_{fam}.tsv")

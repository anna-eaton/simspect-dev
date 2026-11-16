#!/usr/bin/env python3
"""make_corpus.py (agent sptrace, 2026-11-16) -- build the Stage-2 input XML dir for the SPT-specific race run from the EXISTING flat
Alloy enumeration of the UNCHANGED production SPT spec STAGE1_alloy/models/SPT_6_oneLP_v2.als (sha256 acb1f2e2..., agent singlestage-spt,
cafe2 /tests/singlestage_20261109/out/SPT/SPT_6_oneLP_v2/{default,1,2,3}; scope 'for 9 but exactly 6 Instruction', cap 10,000 per seed;
default CAPPED at 10,000, seeds 1/2/3 TIMEOUT at 1,500 s with 4,760/4,520/5,108; union 24,388 instances, 16,313 distinct).
No Alloy is run and no model is touched.
Selection (deterministic, no randomness): walk runs in the order default,1,2,3 and files in sorted order; dedup by census_flat.fingerprint
(the isomorphism fingerprint the census used); keep the FIRST instance of each fingerprint whose transmitter kind is TLoad (race_scan.py
scores ld transmitters only). Output stems are renumbered inst-000001.. in that order; manifest.tsv maps each to its source file + sha256.
Usage (in gem5_dev): make_corpus.py <out_xml_dir> <manifest.tsv>
"""
import hashlib, os, sys
from multiprocessing import Pool
SRC = "/tests/singlestage_20261109/out/SPT/SPT_6_oneLP_v2"
sys.path.insert(0, "/tests/singlestage_20261109/tools")
import census_flat as cf
out, man = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
def job(path):
    F = cf.load(path); return path, cf.fingerprint(F), cf.shape(F)["xm_kind"]
files = [os.path.join(SRC, run, f) for run in ("default", "1", "2", "3")
         for f in sorted(x for x in os.listdir(os.path.join(SRC, run)) if x.startswith("inst-") and x.endswith(".txt"))]
with Pool(int(os.environ.get("JOBS", "56"))) as pool:
    res = pool.map(job, files, chunksize=50)   # map keeps input order -> deterministic first-occurrence dedup
seen, kept, kinds = set(), 0, {}
with open(man, "w") as M:
    M.write("stem\tsource_xml\tsha256_xml\tfingerprint_sha1\n")
    for path, fp, k in res:
        if fp in seen:
            continue
        seen.add(fp); kinds[k] = kinds.get(k, 0) + 1
        if k != "TLoad":
            continue
        kept += 1; stem = f"inst-{kept:06d}"; src = path[:-4] + ".xml"
        data = open(src, "rb").read(); open(os.path.join(out, stem + ".xml"), "wb").write(data)
        M.write(f"{stem}\t{src}\t{hashlib.sha256(data).hexdigest()}\t{hashlib.sha1(fp.encode()).hexdigest()}\n")
print(f"instances {len(files)} distinct {len(seen)} xm_kinds {kinds} kept_TLoad {kept}")

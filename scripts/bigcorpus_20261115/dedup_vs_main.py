#!/usr/bin/env python3
"""dedup_vs_main.py -- analysis-time dedup of the EXTRA Footprint corpus against the MAIN one (agent bigcorpus, 2026-11-15; Anna option 3 (b):
"exclude programs whose fingerprint matches a [main-corpus] program ... say how many were duplicates"; no restart, nothing is deleted).
Fingerprint = alloy_solver_order.make_fingerprinter (merge_stage15's rule, the one Stage 1.5 dedups with), on each corpus's xml/.
Writes <out>/dup_stems.txt (extra-corpus stems whose program also exists in the main corpus), <out>/dedup_summary.json.
Usage (code root): dedup_vs_main.py --main <ts>/Footprint_6_u_nov10_s2A/xml --extra <ts>/Footprint_6_u_core_lpP_s2A/xml --out <dir> [--jobs 8]
"""
import argparse, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, ".")
import alloy_solver_order as aso  # noqa: E402
FP = None


def _fp(p):
    global FP
    if FP is None:
        FP = aso.make_fingerprinter(Path("STAGE2_compilation"))
    try:
        return p.stem, FP(p)
    except Exception as e:
        return p.stem, f"ERROR {e}"


def fps(d, jobs):
    with ProcessPoolExecutor(jobs) as ex:
        return dict(ex.map(_fp, sorted(Path(d).glob("inst-*.xml")), chunksize=50))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--main", required=True); ap.add_argument("--extra", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--jobs", type=int, default=8); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    m, x = fps(a.main, a.jobs), fps(a.extra, a.jobs)
    mset = {v for v in m.values() if not v.startswith("ERROR")}
    dup = sorted(s for s, v in x.items() if v in mset)
    (out / "dup_stems.txt").write_text("".join(s + "\n" for s in dup))
    summ = dict(main_programs=len(m), main_fp_errors=sum(v.startswith("ERROR") for v in m.values()), extra_programs=len(x),
                extra_fp_errors=sum(v.startswith("ERROR") for v in x.values()), extra_duplicates_of_main=len(dup),
                extra_unique=len(x) - len(dup))
    (out / "dedup_summary.json").write_text(json.dumps(summ, indent=1)); print(json.dumps(summ))


if __name__ == "__main__":
    main()

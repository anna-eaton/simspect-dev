#!/usr/bin/env python3
"""firstdet_merge.py: merge the run dirs of one first-detection run split across hosts
(firstdet_stream.py --partition K/M, --idx-offset) into one dir that
classify_hits.py / classify_cs_rmw.py / firstdet_report.py read unchanged.

    python3 firstdet_merge.py <dst> <src1> <src2> ...

dst/results.jsonl and dst/order_stream.tsv = concatenation of the sources' files (idx are unique by
construction: each host has its own --idx-offset; a duplicate (mode, stem) or idx is an error and is
logged, keeping the first). dst/raw/<mode>/*.json and dst/traces/<mode>/* = symlinks to the sources'
files. Rewrites results.jsonl / order_stream.tsv each call; leaves classifier outputs in dst alone
(so classify_hits --incremental keeps working). Log: dst/merge.log.
"""
import json, os, sys, time
from pathlib import Path


def main():
    dst = Path(sys.argv[1]); srcs = [Path(a) for a in sys.argv[2:]]
    dst.mkdir(parents=True, exist_ok=True)
    log = open(dst / "merge.log", "a")
    log.write(f"== {time.strftime('%F %T')} merge {[str(s) for s in srcs]}\n")
    seen_pair, seen_idx, rows, n_dup = set(), set(), [], 0
    for s in srcs:
        rj = s / "results.jsonl"
        if not rj.exists():
            log.write(f"  {s}: no results.jsonl\n"); continue
        n = 0
        for l in rj.read_text().splitlines():
            try:
                r = json.loads(l)
            except Exception:
                continue
            k = (r["mode"], r["stem"])
            if k in seen_pair or r["idx"] in seen_idx:
                n_dup += 1
                log.write(f"  DUPLICATE {k} idx={r['idx']} in {s} (kept the first)\n")
                continue
            seen_pair.add(k); seen_idx.add(r["idx"]); rows.append(l); n += 1
        log.write(f"  {s}: {n} rows\n")
        for sub in ("raw", "traces"):
            for f in (s / sub).glob("*/*"):
                t = dst / sub / f.parent.name / f.name
                if not t.exists():
                    t.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(f.resolve(), t)
    tmp = dst / "results.jsonl.tmp"
    tmp.write_text("".join(x + "\n" for x in rows)); tmp.replace(dst / "results.jsonl")
    ost = "".join((s / "order_stream.tsv").read_text() for s in srcs if (s / "order_stream.tsv").exists())
    tmp = dst / "order_stream.tsv.tmp"; tmp.write_text(ost); tmp.replace(dst / "order_stream.tsv")
    log.write(f"  total {len(rows)} rows, {n_dup} duplicates\n")
    print(f"merged {len(rows)} rows, {n_dup} duplicates -> {dst}")


if __name__ == "__main__":
    main()

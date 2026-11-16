#!/usr/bin/env python3
"""nonmin_fp.py -- flag-normalized program fingerprints for the non-minimal corpus.

Read-only. The production dedup fingerprint (alloy_solver_order.DEDUP_RULE = find_duplicates.canonicalize(pass1) + xm flags)
includes every instruction's `resolved` bit. The non-minimal model Footprint_6_u_lpN fixes a non-branch's (inert) bit to
resolved ([lp-9] lp_flagcanon), while the minimal corpus may carry an unresolved non-branch at the boundary
(first_uncommitted). So the overlap between the two corpora is measured with a NORMALIZED fingerprint: the same key with
`resolved` forced True for every non-branch instruction (kinds not starting with "br"). For lpN programs it equals the raw
fingerprint.

Subcommands
  seen   --xml DIR [DIR ...] --out STATE.json      normalized fps of every inst-*.xml -> {"seen": {fp: "minimal:<stem>"}}
                                                   (stream_fp.py --seen-from format), plus raw-vs-normalized stats
  overlap --a DIR --b DIR [--json OUT]             distinct normalized programs in A, in B, shared (and raw-fp shared)
  flags  --xml DIR                                 how many programs have an unresolved non-branch (the bit lp_flagcanon fixes)
"""
import argparse, hashlib, json, sys
from multiprocessing import Pool
from pathlib import Path

CODE = None


def _init(code):
    global CODE
    CODE = code
    sys.path.insert(0, str(Path(code) / "STAGE2_compilation"))
    import os, tempfile
    d = tempfile.mkdtemp(prefix="nonmin_fp_")   # pass1 writes alloy-out/spo_program.ir relative to cwd (scratch, per worker)
    os.makedirs(os.path.join(d, "alloy-out"), exist_ok=True)
    os.chdir(d)


def one(path):
    from parsexml import parse_alloy_xml, pass1_specify_state_a
    from find_duplicates import canonicalize
    try:
        inst = parse_alloy_xml(Path(path).read_text(encoding="utf-8"))
        r1 = pass1_specify_state_a(inst)
        xm = tuple(bool(r.get("xm")) for r in r1["instructions"])
        raw = hashlib.sha256(repr((canonicalize(r1, inst), xm)).encode()).hexdigest()
        unres_nb = sum(1 for r in r1["instructions"] if not str(r["kind"]).startswith("br") and not r["resolved"])
        for r in r1["instructions"]:
            if not str(r["kind"]).startswith("br"):
                r["resolved"] = True
        norm = hashlib.sha256(repr((canonicalize(r1, inst), xm)).encode()).hexdigest()
        return Path(path).stem, raw, norm, unres_nb, None
    except Exception as e:  # noqa: BLE001
        return Path(path).stem, None, None, 0, repr(e)


def scan(dirs, code, jobs):
    files = sorted(str(f) for d in dirs for f in Path(d).glob("inst-*.xml"))
    with Pool(jobs, initializer=_init, initargs=(code,)) as p:
        return list(p.imap(one, files, chunksize=64))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["seen", "overlap", "flags"])
    ap.add_argument("--xml", nargs="+"); ap.add_argument("--out"); ap.add_argument("--a", nargs="+"); ap.add_argument("--b", nargs="+")
    ap.add_argument("--json"); ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--code", default=str(Path(__file__).resolve().parents[5]))
    a = ap.parse_args()
    if a.cmd in ("seen", "flags"):
        rows = scan(a.xml, a.code, a.jobs)
        errs = [r for r in rows if r[4]]
        raw = {r[1] for r in rows if r[1]}; norm = {r[2] for r in rows if r[2]}
        st = {"files": len(rows), "parse_errors": len(errs), "distinct_raw": len(raw), "distinct_norm": len(norm),
              "with_unresolved_nonbranch": sum(1 for r in rows if r[3]), "xml": a.xml}
        print(json.dumps(st, indent=1))
        if a.cmd == "seen":
            seen = {}
            for stem, _, n, _, e in rows:
                if n and n not in seen:
                    seen[n] = f"minimal:{stem}"
            Path(a.out).write_text(json.dumps({"seen": seen, "stats": st, "rule": "nonmin_fp normalized (non-branch resolved=True)"}))
    else:
        ra, rb = scan(a.a, a.code, a.jobs), scan(a.b, a.code, a.jobs)
        na, nb = {r[2] for r in ra if r[2]}, {r[2] for r in rb if r[2]}
        wa, wb = {r[1] for r in ra if r[1]}, {r[1] for r in rb if r[1]}
        res = {"a": a.a, "b": a.b, "files_a": len(ra), "files_b": len(rb), "distinct_norm_a": len(na), "distinct_norm_b": len(nb),
               "shared_norm": len(na & nb), "shared_raw": len(wa & wb),
               "a_unresolved_nonbranch": sum(1 for r in ra if r[3]), "b_unresolved_nonbranch": sum(1 for r in rb if r[3])}
        print(json.dumps(res, indent=1))
        if a.json:
            Path(a.json).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

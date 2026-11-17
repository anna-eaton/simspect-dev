#!/usr/bin/env python3
"""blocker.py (agent invisispec-fut 2026-11-16) -- read-only: for each pilot record whose transmitter issued as a USL, which older
instruction was the LAST to complete before the transmitter's LSQ:safe (gem5's own Futuristic visibility point) -- i.e. what
actually kept the transmitter speculative -- and is it a model instruction (an Alloy pc label), and if so resolved or unresolved?
Usage: python3 blocker.py --run <firstdet dir> --fid <pilot_fidelity json> --code <code root> --testset <corpus> --json out.json
"""
import argparse, collections, gzip, json, re, shutil, sys, tempfile
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ("--run", "--fid", "--code", "--testset", "--json"):
    ap.add_argument(k, required=True)
A = ap.parse_args()
sys.path.insert(0, str(Path(A.code) / "STAGE3_gem5")); sys.path.insert(0, str(Path(A.code) / "STAGE2_compilation"))
import gem5_common as gc, compile_annotate as ca
rows = json.load(open(A.fid))["rows"]
C = collections.Counter(); out = []
for r in rows:
    if "error" in r or not r.get("xmit_usl_at_issue") or r["xmit"].get("safe") is None:
        continue
    mode, stem = r["mode"], r["stem"]
    tmp = Path(tempfile.mkdtemp(prefix="futblk_"))
    try:
        b, base = ca.build_binary(Path(A.testset) / mode / "asm" / f"{stem}.s", tmp)
        lab = {base + o + r["layout_delta"]: pc for pc, o in ca.pc_offsets_from_nm(b, stem, base).items()}
        tr = tmp / "pv.txt"
        with gzip.open(Path(A.run) / "traces" / mode / f"{stem}.pipeview.txt.gz", "rb") as f, open(tr, "wb") as g:
            shutil.copyfileobj(f, g)
        pv = gc.parse_pipeview_by_seq(tr)
        xs, safe = r["xmit"]["seq"], r["xmit"]["safe"]
        older = [q for q in pv.values() if q["seq"] < xs and 0 < q["complete"] <= safe]
        if not older:
            continue
        blk = max(older, key=lambda q: (q["complete"], q["seq"]))
        lo = min(lab) if lab else 0
        if blk["pc"] in lab:
            pc = lab[blk["pc"]]
            src = {s["pc"] for s in r.get("sources", [])}
            where = "model_unresolved_source" if pc in src else "model_resolved_instr"
        elif lab and lo - 0x400 <= blk["pc"] <= max(lab) + 0x40:
            where = "litmus_body_non_label (Stage-2 filler/splice/route or prologue)"
        else:
            where = "outside_litmus (harness / setup)"
        m = re.match(r"\s*(\S+)", blk.get("disasm", "").split(":")[-1])
        op = blk.get("disasm", "").split(":")[0].strip()
        C[(r["category"], where)] += 1
        C[(r["category"], "op:" + op)] += 1
        out.append(dict(mode=mode, stem=stem, cat=r["category"], where=where, disasm=blk.get("disasm"), blk_complete=blk["complete"],
                        xmit_issue=r["xmit"]["issue"], safe=safe))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
Path(A.json).write_text(json.dumps(dict(summary={f"{a}|{b}": v for (a, b), v in C.items()}, rows=out), indent=1))
for (a, b), v in sorted(C.items(), key=lambda x: (x[0][0], -x[1])):
    if not b.startswith("op:") or v >= 5:
        print(f"{a:10s} {b:70s} {v}")

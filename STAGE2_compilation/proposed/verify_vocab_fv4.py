#!/usr/bin/env python3
"""verify_vocab_fv4.py: census + check of a Stage-2 testset built with fanout_v2.vocab_rj (overnight-exp, 2026-11-11).

For every <stem>.ann.json of one mode it re-derives the pass-4 program from the XML exactly as
batch_generate.run_pipeline does (same per-stem seed, reg_naming from the ann, vocab_rj from the ann),
and checks:
  * faithful: the re-derived concrete form of every Alloy pc equals the `; pc=N atom (form)` comment pass 5
    wrote into the .ll (so the census below describes the emitted tests);
  * rf edges: with the RMW forms treated as plain loads (Alloy's semantics) as the base, and the emitted
    program (RMW writes no register, fillers + splices inserted, jmp fillers have no dataflow) as the new
    program, every Alloy instruction's register/memory source still descends from its original Alloy
    writer (measure_xmit_path_alu.all_edges_intact, the same check verify_fanout_v2.py runs);
  * transmitter path: for an ld transmitter fed by a load, the producer still feeds its address;
  * .s: each RMW pc's marker is followed by `orq $0, <mem>`, and every `jmp .Lsimspect_jf<k>` jumps to the
    label on the next line (a direct jmp to the next instruction).
ddi edges are intra-instruction; the one a RMW drops by design is mem -> outreg of a load whose outreg no rf
edge reads (the same rewrite make_rmw_corpus.py made).
Census: per concrete form, how often it was a valid candidate, how often it was chosen, and the expected
count under the uniform draw (sum of 1/|valid|); filler-op counts; tests with >= 1 RMW / jmp filler.
Read-only. Usage: verify_vocab_fv4.py <xml_dir> <testset_mode_dir (holds llvm/ asm/ ann/)> --mode <mode>
"""
import argparse, collections, json, random, re, sys, zlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_xmit_path_alu as M   # noqa: E402  to_ops, all_edges_intact, analyze, producer_of
P = M.P
RMW = P.VOCAB_RJ_RMW["name"]


def r4_for(xml, stem, mode, rn, vrj, excl=None):
    r1 = P.pass1_specify_state_a(P.parse_alloy_xml(xml), write_out=False)
    vseed = zlib.crc32(f"{stem}_v0".encode())
    random.seed(vseed)
    r2 = P.pass2_specify_instructions(r1, write_out=False, vocab_rj=vrj, exclude_tags=excl)
    r25 = P.pass2_5_specify_branches(r2, branch_mode=mode, write_out=False)
    ril = P.pass_interleave(r25, None, random.Random(vseed ^ 0xABCD_1234))
    r3 = P.pass3_assign_operands(ril, write_out=False, reg_naming=rn)
    return r2, P.pass4_ssa(r3, write_out=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("xml_dir"); ap.add_argument("mode_dir")
    ap.add_argument("--mode", required=True); ap.add_argument("--tables", default=None)
    ap.add_argument("--json", default=None, help="write the census + problems here")
    ap.add_argument("--exclude-tags", nargs="*", default=None, help="fanout_v2.vocab_exclude_tags of the run (abs-vocab fv4)")
    a = ap.parse_args()
    if a.tables:
        P.reload_tables(a.tables)
    md = Path(a.mode_dir); tot = collections.Counter(); bad = []
    valid_n = collections.Counter(); chosen_n = collections.Counter(); expect = collections.Counter()
    filler_ops = collections.Counter()
    for annf in sorted((md / "ann").glob("*.ann.json")):
        stem = annf.name[:-9]; ann = json.loads(annf.read_text())
        vr = ann.get("vocab_rj"); fv = ann.get("fanout_v2") or {"fillers": [], "splices": []}
        vrj = {"rmw": vr["rmw"], "jmp": vr["jmp"]} if vr else None
        rnr = ann.get("reg_naming")
        rn = {"mode": "random", "seed": rnr["seed"]} if rnr else {"mode": "sorted"}
        r2, r4 = r4_for((Path(a.xml_dir) / f"{stem}.xml").read_text(), stem, a.mode, rn, vrj, a.exclude_tags)
        tot["tests"] += 1
        ll = (md / "llvm" / f"{stem}.ll").read_text()
        emitted = {int(m.group(1)): m.group(2) for m in re.finditer(r"; pc=(\d+)\s+\S+\s+\((\S+)\)", ll)}
        for rec in r4["instructions"]:
            if rec.get("synthetic"):
                continue
            if emitted.get(rec["pc"]) != rec.get("concrete_instruction"):
                bad.append((stem, "rederive mismatch", rec["pc"], emitted.get(rec["pc"]), rec.get("concrete_instruction")))
        for rec in r2["instructions"]:
            cands = rec.get("candidates") or []
            for c in cands:
                valid_n[c] += 1; expect[c] += 1.0 / len(cands)
            chosen_n[rec.get("concrete_instruction")] += 1
        rmw_pcs = [r["pc"] for r in r4["instructions"] if r.get("concrete_instruction") == RMW]
        if sorted(rmw_pcs) != sorted((vr or {}).get("rmw_pcs", [])):
            bad.append((stem, "ann rmw_pcs != rederived", rmw_pcs, (vr or {}).get("rmw_pcs")))
        tot["tests_with_rmw"] += bool(rmw_pcs); tot["rmw_instrs"] += len(rmw_pcs)
        xm = next((r for r in r4["instructions"] if r.get("xm")), None)
        if xm is not None and xm.get("kind") == "ld":
            tot["ld_xmit_tests"] += 1
            tot["rmw_at_xmit"] += xm.get("concrete_instruction") == RMW
        # dataflow: base = Alloy semantics (RMW as load), new = emitted program
        base_ins = [dict(r, concrete_instruction="load") if r.get("concrete_instruction") == RMW else r
                    for r in r4["instructions"]]
        base = M.to_ops(base_ins)
        new = [dict(o) for o in base]
        for i, r in enumerate(r4["instructions"]):
            if r.get("concrete_instruction") == RMW:
                new[i] = dict(new[i], dsts=set())
        alloy_regs = {x for o in base for x in (o["srcs"] | o["dsts"]) if x.startswith("r:")}
        idx = {o["pc"]: i for i, o in enumerate(base)}   # fillers may sit before a synthetic pc
        ins = []
        for f in fv["fillers"]:
            filler_ops[f["op"]] += 1
            if f["op"] == P.FV2_FILLER_JMP:
                continue
            d = "r:" + f["dst"]
            if d in alloy_regs:
                bad.append((stem, "filler writes Alloy reg", f))
            ins.append((idx[f["before_pc"]], dict(kind="other_n", alu=True, srcs={"r:" + s for s in f["srcs"]},
                                                  dsts={d}, xm=False, pc=-1, synthetic=True, atom="F")))
        for s in fv["splices"]:
            if s.get("shared_with_previous"):
                continue
            r = "r:" + s["reg"]
            ins.append((idx[s["consumer_pc"]], dict(kind="other_n", alu=True, srcs={r}, dsts={r}, xm=False, pc=-1,
                                                    synthetic=True, atom="S%d" % s["consumer_pc"])))
        for pos, op in sorted(ins, key=lambda t: t[0], reverse=True):
            new.insert(pos, op)
        ok = M.all_edges_intact(base, new)
        tot["edges_intact"] += ok
        if not ok:
            bad.append((stem, "rf edge broken"))
        prod, _ = M.producer_of(r4)
        if prod:
            rp, _ra = M.analyze(new, prod)
            tot["ld_xmit_load_fed"] += 1; tot["xmit_path_intact"] += rp
            if not rp:
                bad.append((stem, "xmit path broken"))
        # .s checks
        s_txt = (md / "asm" / f"{stem}.s").read_text()
        lines = [l.strip() for l in s_txt.splitlines()]
        safe = stem.replace("-", "_").replace(".", "_")
        for pc in rmw_pcs:
            try:
                k = lines.index(f"__litmus_{safe}_pc{pc}:")
            except ValueError:
                bad.append((stem, "rmw marker missing", pc)); continue
            nxt = next((l for l in lines[k + 1:] if l and not l.startswith((".globl", "__litmus_", "#"))), "")
            if not re.match(r"orq\s+\$0,\s*-?\d*\(", nxt):
                bad.append((stem, "rmw not orq", pc, nxt))
        nj = 0
        for i, l in enumerate(lines):
            m = re.match(r"jmp\s+(\.Lsimspect_jf\S+)$", l)
            if m:
                nj += 1
                if i + 1 >= len(lines) or lines[i + 1] != m.group(1) + ":":
                    bad.append((stem, "jmp filler target is not the next line", l))
        nf = sum(1 for f in fv["fillers"] if f["op"] == P.FV2_FILLER_JMP)
        if nj != nf:
            bad.append((stem, "jmp filler count .s vs ann", nj, nf))
        tot["tests_with_jmp_filler"] += nf > 0; tot["jmp_fillers"] += nf
        tot["fillers"] += len(fv["fillers"])
    forms = sorted(set(valid_n) | set(chosen_n), key=str)
    census = {f: {"valid": valid_n[f], "chosen": chosen_n[f], "expected_uniform": round(expect[f], 1)} for f in forms}
    out = {"mode": a.mode, "totals": dict(tot), "forms": census, "filler_ops": dict(filler_ops),
           "problems": [list(map(str, b)) for b in bad]}
    print(json.dumps({k: out[k] for k in ("mode", "totals", "forms", "filler_ops")}, indent=1))
    print("problems:", bad[:10], len(bad))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""verify_abs_vocab_fv4.py: asm-level check + per-kind census of a Stage-2 testset built with the fv4 table
(instruction_tables/proposed/fv4_vocab.jsonc; abs-vocab, 2026-11-12). Complements verify_vocab_fv4.py
(which re-derives pass 4 and checks Alloy rf edges + the transmitter path at the record level); this one
reads the emitted .s.

Per test (one mode dir with llvm/ asm/ ann/):
  * every Alloy pc's form comes from the .ll comments `; pc=N atom (concrete)` and `; fv4 form: X`;
  * the first instruction after each pc marker in the .s matches the form:
      load / load_swapidx      movq <mem>, <reg>  (swapidx: probe register as SIB index, or `(,%base)`)
      store / store_swapidx    movq <reg|$0>, <mem>;  store_imm: movq $0, <mem>
      load_rmw_or0             orq $0, <mem>
      fv4 other_n forms        the expected mnemonic occurs before the next marker
  * ld transmitter: ann xmit.addr is the marker (compile_annotate) and the marker's instruction reads memory;
  * branch_forms.br_cmp_pcs: `cmpq $1` + jb/jae in that pc's block; jmp_direct_pcs: a `jmp`.
Census: chosen count per form vs the uniform expectation (sum of 1/|valid candidates|) taken from
verify_vocab_fv4.py --json (its "forms" table), grouped by kind.
Usage: verify_abs_vocab_fv4.py <mode_dir> [--census verify_vocab_fv4.json] [--json out.json]
"""
import argparse, collections, json, re, sys
from pathlib import Path

MNEM = {"mov_rr": r"\bmovq\b", "neg": r"\bnegq\b", "shl3": r"\bshlq\s+\$3,", "addq_rr": r"\baddq\b",
        "sub_rr": r"\bsubq\b|\bnegq\b", "xor_rr": r"\bxorq\b", "and_rr": r"\bandq\b", "or_rr": r"\borq\b",
        "lea_s8": r"\bleaq\s+\(%\w+,\s*%\w+,\s*8\)"}
KIND = {"load": "ld", "load_swapidx": "ld", "load_rmw_or0": "ld", "store": "str", "store_swapidx": "str",
        "store_imm": "str"}


def blocks(s_text, stem):
    """{pc: [instruction lines from that pc marker up to the next pc marker]}"""
    safe = stem.replace("-", "_").replace(".", "_")
    out, cur = {}, None
    for ln in s_text.splitlines():
        m = re.match(rf"__litmus_{safe}_pc(\d+):", ln.strip())
        if m:
            cur = int(m.group(1)); out[cur] = []; continue
        t = ln.strip()
        if cur is None or not t or t.startswith((".", "#")) or t.endswith(":"):
            continue
        out[cur].append(t)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode_dir")
    ap.add_argument("--census", default=None); ap.add_argument("--json", default=None)
    a = ap.parse_args()
    md = Path(a.mode_dir); bad = []; chosen = collections.Counter(); tot = collections.Counter()
    for annf in sorted((md / "ann").glob("*.ann.json")):
        stem = annf.name[:-9]; ann = json.loads(annf.read_text()); tot["tests"] += 1
        ll = (md / "llvm" / f"{stem}.ll").read_text()
        form = {}
        cur = None
        for ln in ll.splitlines():
            m = re.search(r"; pc=(\d+)\s+\S+\s+\((\S+)\)", ln)
            if m:
                cur = int(m.group(1)); form[cur] = m.group(2); continue
            m = re.search(r"; fv4 form: (\S+)", ln)
            if m and cur is not None:
                form[cur] = m.group(1)
            m = re.search(r"; fv4 \S+: same-register inputs, emitted as (\S+)", ln)
            if m and cur is not None:
                tot["alu_same_reg_fallback"] += 1
                form[cur] = m.group(1)
        bl = blocks((md / "asm" / f"{stem}.s").read_text(), stem)
        probe = ((ann.get("reg_naming") or {}).get("infra_registers") or [None, None, None])[2]
        for pc, f in form.items():
            chosen[f] += 1
            ins = bl.get(pc)
            if ins is None:
                bad.append((stem, pc, f, "no marker in .s")); continue
            first = ins[0] if ins else ""
            if f in ("load", "load_swapidx"):
                m = re.match(r"movq\s+(-?\d*)\(([^)]*)\),\s*%\w+$", first)
                if not m:
                    bad.append((stem, pc, f, "first insn not a load: " + first)); continue
                regs = [r.strip() for r in m.group(2).split(",")]
                if f == "load_swapidx":
                    ok = regs[0] == "" or (probe is not None and len(regs) >= 2 and regs[1] == "%" + probe)
                else:
                    ok = regs[0] != "" and (probe is None or regs[0] == "%" + probe)
                if not ok:
                    bad.append((stem, pc, f, "SIB order: " + first))
            elif f in ("store", "store_swapidx", "store_imm"):
                m = re.match(r"movq\s+(\S+),\s*(-?\d*)\(([^)]*)\)$", first)
                if not m:
                    bad.append((stem, pc, f, "first insn not a store: " + first)); continue
                regs = [r.strip() for r in m.group(3).split(",")]
                if f == "store_imm" and m.group(1) != "$0":
                    bad.append((stem, pc, f, "store_imm source: " + first))
                if f == "store_swapidx" and not (regs[0] == "" or (probe and len(regs) >= 2 and regs[1] == "%" + probe)):
                    bad.append((stem, pc, f, "SIB order: " + first))
            elif f == "load_rmw_or0":
                if not re.match(r"orq\s+\$0,\s*-?\d*\(", first):
                    bad.append((stem, pc, f, "rmw: " + first))
            elif f in MNEM:
                if not any(re.search(MNEM[f], i) for i in ins):
                    bad.append((stem, pc, f, "mnemonic missing: " + " | ".join(ins[:4])))
        x = ann.get("xmit") or {}
        if x.get("kind") == "ld" and x.get("pc") in bl:
            first = (bl[x["pc"]] or [""])[0]
            if "(" not in first.split(",")[0] and not first.startswith("orq"):
                bad.append((stem, x["pc"], "xmit", "marker insn does not read memory: " + first))
            tot["ld_xmit"] += 1
        bf = ann.get("branch_forms") or {}
        for pc in bf.get("br_cmp_pcs", []):
            txt = " ".join(bl.get(pc, []))
            tot["br_cmp"] += 1
            if not re.search(r"cmpq\s+\$1,.*\bj(b|ae)\b", txt):
                bad.append((stem, pc, "br_cmp", txt[:120]))
        for pc in bf.get("jmp_direct_pcs", []):
            tot["br_jmp"] += 1
            if not any(i.startswith("jmp") for i in bl.get(pc, [])):
                bad.append((stem, pc, "jmp", " | ".join(bl.get(pc, [])[:3])))
        tot["br_annotated"] += len(ann.get("annotations", []))
    census = {}
    if a.census:
        ref = json.loads(Path(a.census).read_text())["forms"]
        for f, d in ref.items():
            census[f] = {"valid": d["valid"], "chosen": chosen.get(f, 0), "expected_uniform": round(d["expected_uniform"], 1)}
    res = {"mode_dir": str(md), "totals": dict(tot), "chosen": dict(chosen), "census": census,
           "problems": bad[:200], "n_problems": len(bad)}
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "problems"}, indent=1))
    print("problems:", bad[:10], len(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

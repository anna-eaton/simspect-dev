#!/usr/bin/env python3
"""make_loosepin.py -- build a LOOSE-PIN single-stage draft of an ultimate model (loosepin agent, 2026-11-09).

UNAPPROVED DRAFT TOOLING. Writes NEW .als files only, never edits an existing model. Anna's ask (2026-11-09):
"i want the ultimate models fixed with this looser pinning so it comes naturally ... pin the skeletons loosely".

Input: one ultimate model (STT_6_u.als, Recon_6_u.als, SPT_6_u.als, STT_6_rmw_u.als, *_stl.als). Output: a copy in
which ONLY skeleton-side bound/scope/pin/minimality/IX text differs; the defense block (from the
'Specific defense model' banner to the end of the file) is byte-identical, which the script checks. Edits, each
tagged [lp-n] in the output:

  [lp-0] header.
  [lp-1] IX symmetry breaking for a VARIABLE length: N position atoms IX0..IX{N-1}; `idx_surjective` (every atom
         used, so exactly N instructions) is replaced by `idx_prefix` (the first instruction has IX0 and each spo
         successor has the next atom), so an instance of length k uses exactly IX0..IX{k-1}. lt_ix regenerated.
  [lp-2] protection-set fold regenerated N deep (it visits spo positions 0..N-1; stage15-bound S1).
  [lp-3] scope: `for 9 but exactly 6 Instruction` -> `for 9 but N Instruction, K Operand, B Int` (S3, S4).
  [lp-4] PIN: a loose Spectre skeleton, path-style (no exact core edges): (1) a committed region (optional),
         (2) an unresolved gate (branch, or store for the stl flavor) before the transmitter, (3) an access (a load,
         or any instruction that reads memory) whose output reaches the transmitter's leak operand through ANY rf/ddi
         path, so ALUs and memory hops may sit on the path, (4) the transmitter (one_xm/tag_xm, unchanged).
  [lp-5] no junk: `no_extra_inst` (which let operand-free br_n pad the program to exactly 6) becomes "an
         operand-free instruction must be an unresolved branch"; plus `lp_connected`: every instruction with
         operands touches the transmitter's component (rf, ddi, same instruction, or same Mem_s word).
  [lp-6] minimality (--minimality):
         cone  = CORE-RELATIVE (S15-4): leak; RR as production for non-branches (flag canonicalization);
                 an unresolved branch must be necessary (RR) OR relevant (predicate fed by a load = S4's B1, or a
                 predicated branch younger than the transmitter = A3c's B2); the production boundary clause; RS
                 only over the States of the transmitter's backward dataflow cone (extras outside it are free).
         norsc = as cone but no RS at all (junk control = lp_connected only). Admits merges/OTB inputs.
         coneg = as cone but WITHOUT the relevance exemption (regen-lp 2026-11-10, targeting audit TA-4): every
                 unresolved branch, like every other instruction, must be RR-necessary; with --brcap 2 the cap is the
                 only other branch rule. lp_relevant_br is not emitted.
         prod  = the production gen_useful_litmus verbatim (control).
  [lp-7] optional cap on unresolved branches (--brcap K).
  [lp-8] --pin core (regen-lp 2026-11-10, Anna: "I STILL want the skeletons to come from the first round of alloy
         enumeration"): NO generic lp_skeleton. The run conjoins `lp_committed` (some committed, LP-2) and
         `seed_core`, a predicate that is NOT in the draft: stage15lp.py appends one per Stage-1 core (stage_seed.py
         output with every core rf edge relaxed to a path, make_s15_model.py --pin b semantics). The draft alone is
         therefore not runnable; each per-core file is draft + one seed_core.

Usage: make_loosepin.py --base ../STT_6_u.als --minimality cone --out STT_6_u_lpA.als [--n 8 --operands 16
       --intbits 6 --committed required|optional --brcap 0]    (also writes <out>.diff against the base)
"""
import argparse, difflib, hashlib, re, sys
from pathlib import Path

DEFENSE_BANNER = " * Specific defense model"


def die(m):
    sys.exit(f"make_loosepin: {m}")


def find_block(text, start_pat):
    m = re.search(start_pat, text, re.M)
    if not m:
        die(f"anchor not found: {start_pat}")
    if len(re.findall(start_pat, text, re.M)) != 1:
        die(f"anchor not unique: {start_pat}")
    i = text.index("{", m.start()); d = 0
    for j in range(i, len(text)):
        d += (text[j] == "{") - (text[j] == "}")
        if d == 0:
            return m.start(), j + 1
    die(f"unbalanced: {start_pat}")


def once(text, old, new):
    if text.count(old) != 1:
        die(f"expected exactly one occurrence of {old!r}, found {text.count(old)}")
    return text.replace(old, new)


def build(base_text, a):
    t = base_text
    n = a.n
    ixs = [f"IX{k}" for k in range(n)]
    # [lp-1] IX atoms, idx field sum, idx_surjective -> idx_prefix, lt_ix
    sig_pat = r"(?:one sig IX\d+ \{\}.*\n)+"
    if len(re.findall(sig_pat, t)) != 1:
        die("IX sig block not found exactly once")
    t = re.sub(sig_pat, "".join(f"one sig {x} {{}} -- [lp-1] spo position {k}\n" for k, x in enumerate(ixs)), t)
    sum_pat = r"\(IX0(?:\s*\+\s*IX\d+)*\)"
    if len(re.findall(sum_pat, t)) != 2:
        die("expected 2 IX sums (idx field + idx_surjective)")
    m = re.search(r"^fact idx_surjective \{.*\}[ \t]*$", t, re.M)
    if not m:
        die("idx_surjective not found")
    nxt = " + ".join(f"{ixs[k]}->{ixs[k+1]}" for k in range(n - 1))
    t = t[:m.start()] + (
        f"fun lp_ix_next : univ->univ {{ {nxt} }} -- [lp-1]\n"
        "fact idx_prefix { -- [lp-1] replaces idx_surjective: positions are a prefix IX0..IX(k-1), any length k\n"
        "\tfirst_instr.idx = IX0\n"
        "\tall i, j: Instruction | j in i.spo => j.idx = i.idx.lp_ix_next\n"
        "}") + t[m.end():]
    t = re.sub(sum_pat, "(" + " + ".join(ixs) + ")", t, count=1)
    s, e = find_block(t, r"^pred lt_ix\[")
    ors = [f"(a={ixs[k]} and b in {'+'.join(ixs[k+1:])})" for k in range(n - 1)]
    t = t[:s] + "pred lt_ix[a, b: univ] { -- [lp-1] regenerated for " + str(n) + " positions\n\t\t" + "\n\t\tor ".join(ors) + "\n}" + t[e:]
    # [lp-2] fold N deep
    s, e = find_block(t, r"^fun last_committed_protset_p\[")
    blk = t[s:e]
    sig_line = blk[:blk.index("{") + 1]
    sm = re.search(r"a\[p,f\[p\],(hardware_protection_policy(?:\[p\])?)\]", blk)
    if not sm:
        die("fold seed not found")
    expr = sm.group(1)
    for k in range(n):
        expr = f"a[p,f[p]{'.(spo_p[p])' * k},\n\t{expr}]"
    depth_now = blk.count("a[p,")
    if depth_now < n:
        t = t[:s] + f"{sig_line} -- [lp-2] fold regenerated {n} deep (spo positions 0..{n-1})\n\t{expr}\n}}" + t[e:]
    # [lp-5] no padding
    t = once(t, "fact no_extra_inst {no ((Instruction-Branchns) - operands.Operand)}",
             "fact no_extra_inst {no ((Instruction - ((Branchns + Branchxs) & unresolved)) - operands.Operand)} -- [lp-5] only a bare GATE may be operand-free (was: any br_n, padding to exactly 6)\n"
             "// [lp-5] (old) fact no_extra_inst {no ((Instruction-Branchns) - operands.Operand)}")
    # [lp-6] minimality
    lp_defs = (
        "\n// ---- [lp-4..lp-7] loose skeleton pin, core-relative minimality, no-junk rule (loosepin draft) ----\n"
        "fun lp_leakops : Operand { xm.operands & leakage_function } -- [lp-4] the transmitter's leak operand(s)\n"
        "fun lp_cone : Operand { lp_leakops.*(~rf + ~ddi) } -- [lp-4] its backward dataflow cone (operands)\n"
        + ("pred lp_committed { some committed } -- [lp-8] a committed region (LP-2); the skeleton is the Stage-1 core (seed_core, appended per core)\n"
           if a.pin == "core" else "")
        + "pred lp_skeleton { -- [lp-4] loose Spectre skeleton, path-style containment\n"
        + ("\tsome committed -- (1) a committed region\n" if a.committed == "required" else "\t-- (1) committed region: optional in this draft\n")
        + "\tsome g: unresolved & (Branchns + Branchxs + Stores) | xm in g.^spo -- (2) an unresolved gate before the transmitter\n"
          "\tsome acc: Instruction - xm | (acc in Loads or some acc.inmem) and some (acc.outs & lp_cone) -- (3) an access (a load, or any memory reader) whose output reaches the leak operand by any path\n"
          "\t-- (4) the transmitter: one_xm + tag_xm (unchanged skeleton facts)\n"
          "}\n"
          "pred lp_relevant_br[b: Instruction] { -- [lp-6] an unresolved branch that is not RR-necessary may stay only if:\n"
          "\tsome (b.inreg & Loads.outreg.^(rf + ddi)) -- its predicate is data-dependent on a load (S4's B1), or\n"
          "\tor (b in xm.^spo and some b.inreg) -- it is a predicated branch younger than the transmitter (A3c's B2)\n"
          "}\n"
          "fun lp_adj : Operand -> Operand { rf + ~rf + ddi + ~ddi + (~operands).operands + (opstate :> Mem_s).~opstate } -- [lp-5] dataflow, same instruction, same memory word (a shared Reg_s with no rf edge is only a rename)\n"
          "fact lp_connected { all i: Instruction | no i.operands or some (i.operands & xm.operands.*(lp_adj)) } -- [lp-5] no disconnected junk\n")
    if a.brcap:
        lp_defs += f"fact lp_brcap {{ #((Branchns + Branchxs) & unresolved) <= {a.brcap} }} -- [lp-7] cap on unresolved branches\n"
    s, e = find_block(t, r"^let gen_useful_litmus \{")
    if a.pin == "core":
        lp_defs = re.sub(r"pred lp_skeleton \{.*?\n\}\n", "", lp_defs, flags=re.S)
    if a.minimality == "coneg" or (a.pin == "core" and a.minimality != "cone"):   # never emit the TA-4 exemption where unused
        lp_defs = re.sub(r"pred lp_relevant_br\[.*?\n\}\n", "", lp_defs, flags=re.S)
    if a.minimality in ("cone", "norsc", "coneg"):
        rr_br = ("  all b: (unresolved - first_uncommitted) & (Branchns + Branchxs) | secure_speculation_scheme_p[RR->b] -- RR only (no relevance exemption; TA-4)"
                 if a.minimality == "coneg" else
                 "  all b: (unresolved - first_uncommitted) & (Branchns + Branchxs) | secure_speculation_scheme_p[RR->b] or lp_relevant_br[b] -- RR or relevant")
        body = ["  not secure_speculation_scheme_p[no_p] -- the leak (unchanged)",
                "  all i: (unresolved - first_uncommitted) - (Branchns + Branchxs) | secure_speculation_scheme_p[RR->i] -- RR as production, non-branches",
                rr_br,
                "  secure_speculation_scheme_p[RC->first_uncommitted + RR->first_uncommitted] -- boundary (production)"]
        if a.minimality in ("cone", "coneg"):
            body.append("  all s: lp_cone.opstate | secure_speculation_scheme_p[RS->s] -- RS on the skeleton cone's States only")
        new = (f"// [lp-6] (production gen_useful_litmus replaced; minimality={a.minimality})\n"
               "let gen_useful_litmus { -- [lp-6] core-relative minimality\n" + "\n".join(body) + "\n}")
        t = t[:s] + new + t[e:]
    s, e = find_block(t, r"^let gen_useful_litmus \{")
    t = t[:e] + "\n" + lp_defs + t[e:]
    # run block: add the pin
    if a.pin == "core":
        if a.committed != "required":
            die("--pin core needs --committed required (LP-2)")
        t = once(t, "run gen_lit {\n  gen_useful_litmus\n}",
                 "run gen_lit {\n  gen_useful_litmus\n  lp_committed -- [lp-8]\n  seed_core -- [lp-8] Stage-1 core, path-style; appended per core by stage15lp.py\n}")
    else:
        t = once(t, "run gen_lit {\n  gen_useful_litmus\n}", "run gen_lit {\n  gen_useful_litmus\n  lp_skeleton -- [lp-4]\n}")
    # [lp-3] scope
    t = once(t, "for 9 but exactly 6 Instruction", f"for 9 but {n} Instruction, {a.operands} Operand, {a.intbits} Int")
    hdr = ("// =============================================================================\n"
           f"// [lp-0] LOOSE-PIN SINGLE-STAGE DRAFT, NOT APPROVED (loosepin agent, 2026-11-09). New file.\n"
           f"// Generated by proposed/ultimate/loosepin/make_loosepin.py --base {Path(a.base).name} --n {n} --operands {a.operands}\n"
           f"//   --intbits {a.intbits} --minimality {a.minimality} --committed {a.committed} --brcap {a.brcap}" + (f" --pin {a.pin}" if a.pin != "skeleton" else "") + "\n"
           f"// Base sha256 {hashlib.sha256(base_text.encode()).hexdigest()} (unchanged). Defense block byte-identical (checked).\n"
           "// Only [lp-n]-tagged skeleton text differs: IX prefix, fold depth, scope, pin, minimality, no-junk rule.\n"
           "// Docs: wiki/design/TWO_PHASE_MODELS.md '2026-11-09 -- Loose skeleton pin (loosepin)'.\n"
           "// =============================================================================\n")
    return hdr + t


def check(base_text, out_text):
    i = base_text.rindex("/****", 0, base_text.index(DEFENSE_BANNER))
    if base_text[i:] not in out_text:
        die("defense block not byte-identical")
    # every removed base line must be in an allowed region
    allowed = re.compile(r"^(one sig IX|\s*idx: one \(IX0|fact idx_surjective|pred lt_ix|\s*or \(a=IX|\s+\(a=IX|\s*$|"
                         r"fun last_committed_protset_p|\s*a\[p,|\s*\]+\s*$|\}\s*$|\t+\]|fact no_extra_inst|let gen_useful_litmus|"
                         r"\s*//|\s*not secure_speculation_scheme_p\[no_p\]|\s*all i: \(unresolved - first_uncommitted\)|"
                         r"\s*secure_speculation_scheme_p\[RC->|\s*all s: State \| secure_speculation_scheme_p\[RS->s\]|"
                         r"\} for 9 but exactly 6 Instruction|\s*gen_useful_litmus)")
    a, b = base_text.splitlines(), out_text.splitlines()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            for k in range(i1, i2):
                if not allowed.match(a[k]):
                    die(f"base line {k+1} changed outside the allowed regions: {a[k]!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=8); ap.add_argument("--operands", type=int, default=16)
    ap.add_argument("--intbits", type=int, default=6)
    ap.add_argument("--minimality", choices=["cone", "coneg", "norsc", "prod"], default="cone")
    ap.add_argument("--committed", choices=["required", "optional"], default="required")
    ap.add_argument("--brcap", type=int, default=0)
    ap.add_argument("--pin", choices=["skeleton", "core"], default="skeleton",
                    help="skeleton = the generic lp_skeleton (2026-11-09 drafts); core = Stage-1 core pin appended per core [lp-8]")
    a = ap.parse_args()
    base = Path(a.base).read_text()
    out = build(base, a)
    check(base, out)
    Path(a.out).write_text(out)
    diff = difflib.unified_diff(base.splitlines(True), out.splitlines(True), fromfile=Path(a.base).name, tofile=Path(a.out).name)
    Path(str(a.out) + ".diff").write_text("".join(diff))
    print(a.out)


if __name__ == "__main__":
    main()

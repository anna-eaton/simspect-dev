#!/usr/bin/env python3
"""make_footprint_u.py -- build Footprint_6_u.als: the footprint defense block on the ultimate skeleton (regen-lp, 2026-11-10).

UNAPPROVED DRAFT TOOLING. Writes ONE new file (refuses to overwrite unless --force) and never edits an existing model.

Inputs (read-only):
  ../../InvisiSpec_6.als   the footprint model (copy of STT_6.als; defense block shared verbatim by CleanupSpec_6 and
                           SpecLFB_6 up to comments, checked below)
  ../../STT_6.als          the old skeleton
  STT_6_u.als              the ultimate skeleton = STT_6.als + the 4 [u-1] skeleton lines (Operand-typed protection set)

Construction, the same way STT_6's block was put on the ultimate skeleton for STT_6_u:
  1. check that InvisiSpec_6's skeleton (everything before the 'Specific defense model' banner, minus its own
     description comment) is byte-identical to STT_6.als's skeleton;
  2. take STT_6_u's skeleton (everything after its header, up to its defense banner) as the new skeleton;
  3. append InvisiSpec_6's defense block with ONLY the retype the Operand-typed skeleton requires, tagged [fu-n]:
       [fu-1] hardware_protection_policy: State {Mem_s}  ->  [p: PTag->univ]: Operand {Mem_s.(~opstate)}
              (the old skeleton lifted the State set to operands with .(~opstate) inside secure_* and tag_xm; the
              ultimate skeleton drops that lift, so the lift moves into the seed. The skeleton call site passes [p].)
       [fu-2] prot_set_propagation_p[p, i, s: State] : State { s }  ->  [p, i, o: Operand] : Operand { o }
              (identity stays identity: all memory protected, never untainted)
     Clause (1) speculation contract and clause (3) leakage function are byte-identical.
With identity propagation, old protset.(~opstate) = Mem_s.(~opstate) = new protset, and secure_* / tag_xm apply the
same expression to it, so the two models are equal by text for every perturbation; queries/footprint/q_fp_eq.als
checks it in Alloy anyway.

Usage: python3 make_footprint_u.py [--out Footprint_6_u.als] [--force]
"""
import argparse, hashlib, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = HERE.parent.parent
BANNER = " * Specific defense model"


def die(m):
    sys.exit(f"make_footprint_u: {m}")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def split_defense(t):
    i = t.rindex("/****", 0, t.index(BANNER))
    return t[:i], t[i:]


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return "\n".join(l.split("//")[0].split("--")[0].rstrip() for l in t.splitlines() if l.split("//")[0].split("--")[0].strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "Footprint_6_u.als"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--footprint-dir", default="proposed/footprint_v2",
                    help="dir (relative to STAGE1_alloy/models) holding the footprint models; '' = the models dir itself")
    ap.add_argument("--suffix", default="_v2", help="footprint model suffix: _v2 (FP-6, default) or '' (the v1 block)")
    a = ap.parse_args()
    fdir = MODELS / a.footprint_dir if a.footprint_dir else MODELS
    sfx = a.suffix
    inv, cln, lfb, stt, sttu = (fdir / f"InvisiSpec_6{sfx}.als", fdir / f"CleanupSpec_6{sfx}.als", fdir / f"SpecLFB_6{sfx}.als",
                                MODELS / "STT_6.als", HERE / "STT_6_u.als")
    T = {p: p.read_text() for p in (inv, cln, lfb, stt, sttu)}

    # the three footprint models share one defense block (code, comments aside) and one skeleton
    blocks = {p.name: strip_comments(split_defense(T[p])[1]) for p in (inv, cln, lfb)}
    if len(set(blocks.values())) != 1:
        die("InvisiSpec_6 / CleanupSpec_6 / SpecLFB_6 defense blocks differ in code")
    skels = {p.name: strip_comments(split_defense(T[p])[0]) for p in (inv, cln, lfb, stt)}
    if len(set(skels.values())) != 1:
        die("footprint skeletons differ from STT_6.als in code")

    # 1. InvisiSpec_6 skeleton == STT_6 skeleton byte-for-byte, apart from InvisiSpec's description lines
    inv_sk, inv_blk = split_defense(T[inv])
    stt_sk, _ = split_defense(T[stt])
    anchor = "CLEAN MODEL WITH KIND-FIELD REFACTORING"
    if inv_sk[inv_sk.index(anchor):] != stt_sk[stt_sk.index(anchor):]:
        die(f"{inv.name} skeleton is not byte-identical to STT_6.als's (from '{anchor}' on)")

    # 2. ultimate skeleton = STT_6_u minus its header
    sttu_sk, _ = split_defense(T[sttu])
    hdr_end = sttu_sk.index("// =============================================================================\n", 10)
    hdr_end = sttu_sk.index("\n", hdr_end) + 1
    u_sk = sttu_sk[hdr_end:]
    if not stt_sk.lstrip("\n").startswith(u_sk.lstrip("\n")[:200]):
        die("STT_6_u skeleton start does not match STT_6.als")

    # 3. defense block, retyped
    blk = inv_blk
    def once(old, new):
        nonlocal blk
        if blk.count(old) != 1:
            die(f"expected one occurrence of {old!r}")
        blk = blk.replace(old, new)
    once(" * Specific defense model InvisiSpec (footprint; branch shadows)\n",  # same banner in v1 and v2
         " * Specific defense model: footprint (InvisiSpec / CleanupSpec / SpecLFB), ultimate skeleton (Footprint_6_u)  -- [fu-1..fu-2]\n"
         " * Clause lines = InvisiSpec_6.als's (CleanupSpec_6 and SpecLFB_6 have the same code; their paper quotes differ,\n"
         " * see those files). Only the retype the Operand-typed skeleton requires is new, tagged [fu-n].\n")
    hm = re.findall(r"^fun hardware_protection_policy: State \{(.*)\}\n", blk, re.M)
    if len(hm) != 1:
        die("expected one 'fun hardware_protection_policy: State {...}' line")
    hexpr = hm[0]
    once(f"fun hardware_protection_policy: State {{{hexpr}}}\n",
         f"// footprint (old skeleton): fun hardware_protection_policy: State {{{hexpr}}}\n"
         f"fun hardware_protection_policy[p: PTag->univ]: Operand {{({hexpr}).(~opstate)}} -- [fu-1] retype only: the .(~opstate) lift the old skeleton applied in secure_*/tag_xm\n")
    once("fun prot_set_propagation_p[p:PTag->univ,i:Instruction,s:State] : State {\n",
         "fun prot_set_propagation_p[p:PTag->univ,i:Instruction,o:Operand] : Operand { -- [fu-2] retype only (was s: State : State)\n")
    once("\ts // (2) all memory stays protected: there is no visibility-point untaint\n",
         "\to // (2) all memory stays protected: there is no visibility-point untaint  -- [fu-2] (was: s)\n")

    hdr = ("// =============================================================================\n"
           "// Footprint_6_u.als -- footprint defense block (" + (sfx or "v1") + ") (InvisiSpec / CleanupSpec / SpecLFB) on the ULTIMATE skeleton.\n"
           "// DRAFT, NOT APPROVED (regen-lp agent, 2026-11-10). New file, generated by proposed/ultimate/make_footprint_u.py.\n"
           f"//   skeleton  = STT_6_u.als (sha256 {sha(sttu)}) minus its header, i.e. STT_6.als + the four [u-1]\n"
           "//               lines (Operand-typed protection set; see STT_6_u.als's header), byte-identical.\n"
           f"//   defense   = {inv.relative_to(MODELS)} (sha256 {sha(inv)}) block, code shared verbatim with\n"
           f"//               {cln.name} ({sha(cln)[:16]}...) and {lfb.name} ({sha(lfb)[:16]}...);\n"
           f"//               contract = STT_6's, protection set = {{{hexpr}}} never untainted, leakage = Loads.inaddr.\n"
           f"//   [fu-1] hardware_protection_policy retyped State -> Operand: {{{hexpr}}} -> {{({hexpr}).(~opstate)}}.\n"
           "//   [fu-2] prot_set_propagation_p retyped State -> Operand; still the identity.\n"
           "// Equal to its source footprint model by text: with identity propagation the old protset lifted by .(~opstate) is exactly\n"
           "// the new protset, and secure_*/tag_xm apply the same expression to it (Alloy check: queries/footprint/).\n"
           "// Docs: wiki/design/TWO_PHASE_MODELS.md '2026-11-10 -- Loose-pin regeneration (regen-lp)';\n"
           "//       wiki/design/MODELS_AND_BUILDS.md PART 8 (the footprint models).\n"
           "// =============================================================================\n")
    out = hdr + u_sk + blk
    op = Path(a.out)
    if op.exists() and not a.force:
        die(f"{op} exists (use --force to regenerate this draft)")
    op.write_text(out)
    print(op, sha(op))


if __name__ == "__main__":
    main()

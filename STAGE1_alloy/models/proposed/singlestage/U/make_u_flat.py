#!/usr/bin/env python3
"""make_u_flat.py -- family U (ultimate STT_6_u / Recon_6_u) single-stage flat drafts V1-V3.

singlestage-u agent, 2026-11-09. UNAPPROVED DRAFT TOOLING. Writes NEW .als files in this folder only.
It does NOT reimplement anything: it calls the shared generator
  STAGE1_alloy/models/proposed_twophase/stage15_bound/make_s15_model.py   (unchanged)
with --pin none --n 8 --operands 16 --intbits 6 [--shape nospacer] [--minimality leak_rs],
then (1) prepends the brief's header (UNAPPROVED DRAFT, date, exact generator command, base file + sha256),
and (2) checks the result mechanically, refusing to write on any failure:
  - the defense block (from the 'Specific defense model' banner to the end of the base file) appears
    byte-identical in the output;
  - every base line the generator removed/changed lies in a bound-tied region (IX sigs, idx field,
    idx_surjective, lt_ix, the protection-set fold, the run scope line) or, with --minimality, inside
    gen_useful_litmus; every added line is in those regions, the generator header, or the s15_nospacer fact.
Checked by hand on 2026-11-09: make_s15_model.py's anchors (IX sigs, the two '(IX0 + ...)' sums, lt_ix,
the fold seed 'a[p,f[p],hardware_protection_policy[p]]', 'let gen_useful_litmus {', the scope string and the
run needle) all match STT_6_u.als and Recon_6_u.als, so no adapted generator was needed.
Usage: python3 make_u_flat.py            (builds all 6 files)
"""
import difflib, hashlib, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
GEN = REPO / "STAGE1_alloy/models/proposed_twophase/stage15_bound/make_s15_model.py"
BASES = [REPO / "STAGE1_alloy/models/proposed/ultimate/STT_6_u.als",
         REPO / "STAGE1_alloy/models/proposed/ultimate/Recon_6_u.als"]
VARIANTS = {  # suffix -> extra generator args
    "flat_n8_prod": [],
    "flat_n8_prod_nospacer": ["--shape", "nospacer"],
    "flat_n8_leakrs_nospacer": ["--minimality", "leak_rs", "--shape", "nospacer"],
}
COMMON = ["--pin", "none", "--n", "8", "--operands", "16", "--intbits", "6"]
DEFENSE_BANNER = " * Specific defense model"


def regions(lines, minimality):
    """Line-index set of bound-tied regions in a model text (base or output)."""
    keep = set()
    for k, l in enumerate(lines):
        s = l.lstrip()
        if s.startswith("one sig IX") or s.startswith("idx: one (IX0") or s.startswith("fact idx_surjective") \
                or s.startswith("} for 9 but exactly"):
            keep.add(k)
    def block(start_pred, minimal_end=None):
        for k, l in enumerate(lines):
            if start_pred(l):
                depth = 0
                for j in range(k, len(lines)):
                    depth += lines[j].count("{") - lines[j].count("}")
                    depth += lines[j].count("[") * 0
                    keep.add(j)
                    if depth <= 0 and "{" in "".join(lines[k:j + 1]):
                        break
                return
    block(lambda l: l.startswith("fun last_committed_protset_p["))
    block(lambda l: l.startswith("pred lt_ix["))
    if minimality:
        block(lambda l: l.startswith("let gen_useful_litmus {"))
    return keep


def check(base_text, out_text, minimality, nospacer):
    i = base_text.index(DEFENSE_BANNER)
    i = base_text.rindex("/****", 0, i)
    dblock = base_text[i:]
    if dblock not in out_text:
        sys.exit("FAIL: defense block not byte-identical in output")
    a, b = base_text.splitlines(), out_text.splitlines()
    ra, rb = regions(a, minimality), regions(b, minimality)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for k in range(i1, i2):
            if k not in ra:
                sys.exit(f"FAIL: base line {k+1} changed outside bound-tied regions: {a[k]!r}")
        for k in range(j1, j2):
            l = b[k]
            ok = k in rb or (k < 3 and l.startswith("//")) \
                or (nospacer and l in ("fact s15_nospacer { all i: Instruction | some i.operands }", "")) \
                or l in ("  gen_useful_litmus",)  # never expected to change; listed for clarity
            if not ok:
                sys.exit(f"FAIL: output line {k+1} added outside bound-tied regions: {l!r}")
    return len(dblock)


def main():
    for base in BASES:
        btext = base.read_text()
        sha = hashlib.sha256(base.read_bytes()).hexdigest()
        stem = base.stem
        for suf, extra in VARIANTS.items():
            out = HERE / f"{stem}_{suf}.als"
            tmp = HERE / f".{out.name}.tmp"
            args = ["--model", str(base.relative_to(REPO))] + COMMON + extra + ["--out", str(tmp.relative_to(REPO))]
            subprocess.run([sys.executable, str(GEN.relative_to(REPO))] + args, cwd=REPO, check=True,
                           stdout=subprocess.DEVNULL)
            gtext = tmp.read_text(); tmp.unlink()
            n = check(btext, gtext, "--minimality" in extra, "nospacer" in extra)
            hdr = ["// =============================================================================",
                   f"// {out.name} -- UNAPPROVED DRAFT (singlestage-u agent, 2026-11-09). Single-stage flat model, family U.",
                   "// Generator command (repo root):",
                   f"//   python3 {GEN.relative_to(REPO)} " + " ".join(args).replace(str(tmp.relative_to(REPO)), str(out.relative_to(REPO))),
                   f"//   (wrapped by {Path(__file__).relative_to(REPO)}, which adds this header and checks the diff)",
                   f"// Base: {base.relative_to(REPO)}  sha256 {sha}",
                   f"// Defense block ({n} bytes, from the 'Specific defense model' banner) verified byte-identical to the base.",
                   "// =============================================================================", ""]
            out.write_text("\n".join(hdr) + gtext)
            print(f"wrote {out.relative_to(REPO)}  (base sha256 {sha[:12]}..)")


if __name__ == "__main__":
    main()

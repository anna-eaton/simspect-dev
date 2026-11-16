#!/usr/bin/env python3
"""make_ustl_variants.py — build the USTL single-stage (flat) drafts V1-V3 (singlestage session, agent
singlestage-ustl, 2026-11-09). UNAPPROVED DRAFT TOOLING. Writes NEW files only (refuses to overwrite) and
never edits an existing model or make_s15_model.py.

The heavy lifting is the shared generator proposed_twophase/stage15_bound/make_s15_model.py, called unchanged:
its text anchors (IX sigs, '(IX0 + ...)' sums x2, 'pred lt_ix[', the 'fun last_committed_protset_p[' fold
seeded by 'a[p,f[p],hardware_protection_policy[p]]', 'let gen_useful_litmus {', the scope line and the run
needle) all match STT_6_u_stl.als / Recon_6_u_stl.als exactly once. This wrapper only
  (1) prepends the required UNAPPROVED-DRAFT header (date, commands, base file + sha256),
  (2) verifies the result: defense block (from the 'Specific defense model' banner to the end of the base)
      byte-identical in the output; every other differing line falls in a bound-tied category (IX atoms,
      idx/idx_surjective sums, lt_ix, protection-set fold, scope line) or the requested minimality/shape
      clause; check_bound_consistency.py passes,
  (3) prints a verification summary (also captured into RESULTS.json by hand-run commands).
Usage: python3 make_ustl_variants.py [--force]     (from any cwd)
"""
import difflib, hashlib, re, subprocess, sys, tempfile, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = HERE.parents[2]                      # .../STAGE1_alloy/models
GEN = MODELS / "proposed_twophase/stage15_bound/make_s15_model.py"
LINT = HERE.parent / "tools/check_bound_consistency.py"
BASES = [MODELS / "proposed/ultimate/STT_6_u_stl.als", MODELS / "proposed/ultimate/Recon_6_u_stl.als"]
COMMON = ["--pin", "none", "--n", "8", "--operands", "16", "--intbits", "6"]
VARIANTS = {"flat_n8_prod": [], "flat_n8_prod_nospacer": ["--shape", "nospacer"],
            "flat_n8_leakrs_nospacer": ["--shape", "nospacer", "--minimality", "leak_rs"]}
BOUND_TIED = [r"^one sig IX\d+ \{\}", r"^\s*idx: one \(IX0", r"^fact idx_surjective", r"lt_ix|^\s*or \(a=IX|^\s*$",
              r"^\s*(a\[p,|hardware_protection_policy\[p\]\]|\]|// \[stage15-bound\] fold)|^fun last_committed_protset_p\[",
              r"^\s*\} for 9 but exactly \d+ Instruction"]
CLAUSE = {"minimality": r"gen_useful_litmus|secure_speculation_scheme_p\[R[RC]|resolution-min|boundary instr|^\s*//all i: resolved|^\s*$",
          "shape": r"^fact s15_nospacer|^\s*$"}
force = "--force" in sys.argv
ok_all = True
for base in BASES:
    btext = base.read_text(); bsha = hashlib.sha256(btext.encode()).hexdigest()
    di = btext.index("* Specific defense model"); di = btext.rindex("\n", 0, di) + 1
    defense = btext[di:]
    for suffix, extra in VARIANTS.items():
        out = HERE / f"{base.stem}_{suffix}.als"
        if out.exists() and not force:
            sys.exit(f"refusing to overwrite {out} (pass --force)")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "m.als"
            cmd = [sys.executable, str(GEN), "--model", str(base)] + COMMON + extra + ["--out", str(tmp)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            gtext = tmp.read_text()
        rel = lambda p: str(Path(p).relative_to(MODELS.parent.parent))
        gcmd = "python3 " + " ".join([rel(GEN), "--model", rel(base)] + COMMON + extra + ["--out", rel(out)])
        hdr = ("// =============================================================================\n"
               f"// UNAPPROVED DRAFT ({datetime.date.today().isoformat()}, singlestage session, agent singlestage-ustl). Single-stage (flat) USTL variant.\n"
               f"// Base: {rel(base)}  sha256 {bsha}\n"
               f"// Generator (unchanged shared tool): {gcmd}\n"
               f"// Wrapper (adds this header + verifies): python3 {rel(Path(__file__))}\n"
               "// Only bound-tied text (scope, IX atoms, fold depth, Int, operand scope) + the requested shape/minimality\n"
               "// clause differ from the base; the defense block is byte-identical (verified by the wrapper).\n"
               "// =============================================================================\n")
        text = hdr + gtext
        # --- verification ---
        errs = []
        if defense not in text:
            errs.append("defense block NOT byte-identical")
        glines = gtext.splitlines()[3:]          # drop make_s15_model's own 3-line header
        cats = {}
        for line in difflib.unified_diff(btext.splitlines(), glines, lineterm="", n=0):
            if line.startswith(("---", "+++", "@@")):
                continue
            body = line[1:]
            cat = next((f"bound{k}" for k, pat in enumerate(BOUND_TIED) if re.search(pat, body)), None)
            if cat is None and "minimality" in " ".join(extra) and re.search(CLAUSE["minimality"], body):
                cat = "minimality"
            if cat is None and "--shape" in extra and re.search(CLAUSE["shape"], body):
                cat = "shape"
            if cat is None:
                errs.append(f"unexpected diff line: {line!r}")
            cats[cat] = cats.get(cat, 0) + 1
        ix_sigs = re.findall(r"^one sig (IX\d+)", text, re.M)
        ix_sums = re.findall(r"\((IX0(?:\s*\+\s*IX\d+)*)\)", text)
        if ix_sigs != [f"IX{k}" for k in range(8)] or len(ix_sums) != 2 or any(s.replace(" ", "") != "+".join(ix_sigs) for s in ix_sums):
            errs.append(f"IX inconsistent: sigs={ix_sigs} sums={ix_sums}")
        lt = re.search(r"pred lt_ix\[.*?\n\}", text, re.S).group(0)
        if set(re.findall(r"IX\d+", lt)) != set(ix_sigs) or lt.count("(a=IX") != 7:
            errs.append("lt_ix not regenerated for 8 positions")
        out.write_text(text)
        lint = subprocess.run([sys.executable, str(LINT), str(out)], capture_output=True, text=True)
        if lint.returncode != 0:
            errs.append("lint failed: " + lint.stdout.strip())
        ok_all &= not errs
        print(f"{'OK  ' if not errs else 'FAIL'} {out.name}  diff-categories={cats}  {lint.stdout.strip().split(': ',1)[-1]}")
        for e in errs:
            print("    " + e)
sys.exit(0 if ok_all else 1)

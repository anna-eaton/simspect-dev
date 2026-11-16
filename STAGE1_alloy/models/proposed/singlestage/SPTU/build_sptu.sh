#!/usr/bin/env bash
# build_sptu.sh -- build the SPTU single-stage (flat) drafts from proposed/ultimate/SPT_6_u.als
# (singlestage-sptu agent, 2026-11-09). UNAPPROVED DRAFTS. Uses the shared generator UNCHANGED
# (proposed_twophase/stage15_bound/make_s15_model.py --pin none); its anchors all match SPT_6_u.als.
# Then: prepends the draft header, checks the defense block is byte-identical to the base, runs the lint.
# Run from the repo root:  bash STAGE1_alloy/models/proposed/singlestage/SPTU/build_sptu.sh
set -euo pipefail
G=STAGE1_alloy/models/proposed_twophase/stage15_bound/make_s15_model.py
B=STAGE1_alloy/models/proposed/ultimate/SPT_6_u.als
D=STAGE1_alloy/models/proposed/singlestage/SPTU
LINT=STAGE1_alloy/models/proposed/singlestage/tools/check_bound_consistency.py
SHA=$(shasum -a 256 "$B" | cut -d' ' -f1)
build() {  # $1 = out stem, rest = extra generator flags
  local out="$D/$1.als"; shift
  local tmp; tmp=$(mktemp "$D/.gen.XXXXXX")
  local cmd="python3 $G --model $B --pin none --n 8 --operands 16 --intbits 6 $* --out $out"
  python3 "$G" --model "$B" --pin none --n 8 --operands 16 --intbits 6 "$@" --out "$tmp" >/dev/null
  { echo "// UNAPPROVED DRAFT (singlestage-sptu agent, 2026-11-09) -- single-stage flat model, not reviewed by Anna; do not use for production."
    echo "// generator: $cmd   (+ this header, by $D/build_sptu.sh)"
    echo "// base: $B sha256=$SHA"
    echo "// NOTE: spt_public_p (defense block, clause 2) is still the base's 6-step fixpoint; it was NOT re-derived for N=8"
    echo "//       (defense block kept byte-identical by rule). Convergence at N=8 is unverified."
    cat "$tmp"; } > "$out"
  rm -f "$tmp"
  # defense block = from the 'Specific defense model SPT' banner to the end of the base file
  python3 - "$B" "$out" <<'PY'
import sys
b, g = open(sys.argv[1]).read(), open(sys.argv[2]).read()
k = b.index("/*********************************************************************************\n * Specific defense model SPT")
blk = b[k:]
assert g.count(blk) == 1, f"DEFENSE BLOCK NOT BYTE-IDENTICAL in {sys.argv[2]}"
tail = g[g.index(blk) + len(blk):]
print(f"defense block byte-identical ({len(blk)} bytes) in {sys.argv[2]}; appended after it: {tail.strip() or '(nothing)'}")
PY
}
build SPT_6_u_flat_n8_prod
build SPT_6_u_flat_n8_prod_nospacer --shape nospacer
build SPT_6_u_flat_n8_leakrs_nospacer --shape nospacer --minimality leak_rs
python3 "$LINT" "$B" "$D"/SPT_6_u_flat_n8_*.als

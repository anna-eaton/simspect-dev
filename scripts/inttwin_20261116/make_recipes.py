#!/usr/bin/env python3
"""make_recipes.py (agent inttwin 2026-11-16) -- write the integer-twin Stage-2 recipes: each = its FPR recipe with ONLY
fpr.enabled true -> false (text edit of that one key, so comments/order stay), plus a header. Verifies the parsed configs differ
in exactly that key and prints sha256s. Run from the repo root: python3 scripts/inttwin_20261116/make_recipes.py
"""
import hashlib, json, re, sys
from pathlib import Path

OUT = Path("runconfigs/inttwin_20261116")
SRC = {
    "stage2_final_A_int.jsonc": "runconfigs/bigcorpus_20261115/stage2_final_A.jsonc",
    "stage2_stl_A_int.jsonc": "runconfigs/reconstl_20261116/stage2_stl_A.jsonc",
    "stage2_final_A_spt_int.jsonc": "runconfigs/sptrace_20261116/stage2_final_A_spt_SPT_6_oneLP_v2_flat_ld_s2Aspt.jsonc",
}
HDR = ("// inttwin 2026-11-16 (agent inttwin; Anna 2026-11-16, paired register-class design): integer twin of {src}.\n"
       "// Every test comes as a pair from the same Alloy graph: the FPR version ({src}, every consumed load routed through an xmm\n"
       "// register) and this integer version. Differs from the source ONLY in fpr.enabled (true -> false), i.e. only in FPR routing;\n"
       "// instruction table, interleave-only filler table (incl. its dead SSE fillers on xmm14/xmm15), vocab_rj, splices, reg naming\n"
       "// and every seed are unchanged. Brief: scripts/inttwin_20261116/BRIEF.md. Results: wiki/state/EVAL_MANIFEST.md 'Integer twins'.\n")


def load(t):
    return json.loads(re.sub(r"//[^\n]*", "", t))


def diff(a, b, p=""):
    out = []
    for k in sorted(set(a) | set(b)):
        if isinstance(a.get(k), dict) and isinstance(b.get(k), dict):
            out += diff(a[k], b[k], p + k + ".")
        elif a.get(k) != b.get(k):
            out.append(p + k)
    return out


OUT.mkdir(parents=True, exist_ok=True)
for name, src in SRC.items():
    t = Path(src).read_text()
    pat = re.compile(r'("fpr"\s*:\s*\{\s*"enabled"\s*:\s*)true')
    t2, n = pat.subn(r"\1false", t)
    assert n == 1, (src, n)
    body = "\n".join(l for l in t2.splitlines() if not l.startswith("//"))
    t2 = HDR.format(src=src) + body + "\n"
    d = diff(load(t), load(t2))
    assert d == ["fpr.enabled"], (src, d)
    (OUT / name).write_text(t2)
    print(f"{hashlib.sha256((OUT / name).read_bytes()).hexdigest()}  {OUT / name}  (src {src} sha256 "
          f"{hashlib.sha256(Path(src).read_bytes()).hexdigest()[:16]}..., parsed diff {d})")

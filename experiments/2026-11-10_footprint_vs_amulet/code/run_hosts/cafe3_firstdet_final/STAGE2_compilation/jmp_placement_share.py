#!/usr/bin/env python3
"""jmp_placement_share.py: predicted jmp coverage of a compiled testset under make_jmp_corpus.py
(recipe-v3, 2026-11-10). Pure read-only scan of <testset>/<mode>/{asm,ann}; builds nothing.

For each test it combines (a) the jmps parsexml's `branch_forms.jmp_direct` already made
(ann.branch_forms.jmp_direct_pcs; such a jmp replaces the branch at pc q, so it is inside the
window iff u < q < x) with (b) the one jmp make_jmp_corpus.py would insert with the given
--placement/--p/--seed (selection + first candidate; the per-test build checks are ignored,
they passed 800/800 at p 1 in fanoutgaps and every build test since). An inserted jmp before the
marker of pc k is inside the window iff u < k <= x (u = first mispredict* branch pc, x = xmit
pc). Prints, per mode: share of tests with no jmp at all and with no jmp inside the window,
before and after the pass, and the share of inserted jmps that land in the window.

Usage: python3 jmp_placement_share.py <testset dir> [--p 0.5] [--seed 20261109]
           [--placement uniform|window] [--limit N] [--json out.json]
"""
import argparse
import collections
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_jmp_corpus as M  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("testset")
    ap.add_argument("--p", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--placement", choices=M.PLACEMENTS, default="uniform")
    ap.add_argument("--modes", nargs="+", default=["mispredict_not_taken", "mispredict_taken"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    ts = Path(a.testset)
    t0 = time.time()
    print(f"START {time.strftime('%F %T')} testset={ts} p={a.p} seed={a.seed} placement={a.placement}", flush=True)
    out = dict(testset=str(ts), p=a.p, seed=a.seed, placement=a.placement, modes={})
    for mode in a.modes:
        c = collections.Counter()
        files = sorted((ts / mode / "ann").glob("*.ann.json"))
        if a.limit:
            files = files[: a.limit]
        for f in files:
            st = f.name[:-9]
            ann = json.loads(f.read_text())
            s_p = ts / mode / "asm" / f"{st}.s"
            if not s_p.exists():
                c["missing_asm"] += 1
                continue
            w = M._window(ann)
            jd = set((ann.get("branch_forms") or {}).get("jmp_direct_pcs") or [])
            win0 = bool(w) and any(w[0] < q < w[1] for q in jd)
            sel = M.selected(st, a.seed, a.p)
            cands = M.candidates(ann, M.asm_pcs(s_p.read_text(), st), a.placement) if sel else []
            k = M.ordered_candidates(st, a.seed, cands)[0] if cands else None
            ins = k is not None
            iw = ins and M.in_window(ann, k)
            c["n"] += 1
            c["selected"] += sel
            c["inserted"] += ins
            c["inserted_in_window"] += iw
            c["no_window"] += not w
            c["any_before"] += bool(jd)
            c["win_before"] += win0
            c["any_after"] += bool(jd) or ins
            c["win_after"] += win0 or iw
        n = c["n"] or 1
        r = dict(counts=dict(c),
                 no_jmp_any_before=round(1 - c["any_before"] / n, 4),
                 no_jmp_any_after=round(1 - c["any_after"] / n, 4),
                 no_jmp_window_before=round(1 - c["win_before"] / n, 4),
                 no_jmp_window_after=round(1 - c["win_after"] / n, 4),
                 jmp_in_window_after=round(c["win_after"] / n, 4),
                 inserted_share_in_window=round(c["inserted_in_window"] / max(c["inserted"], 1), 4))
        out["modes"][mode] = r
        print(mode, json.dumps(r), flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=2) + "\n")
    print(f"END {time.strftime('%F %T')} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

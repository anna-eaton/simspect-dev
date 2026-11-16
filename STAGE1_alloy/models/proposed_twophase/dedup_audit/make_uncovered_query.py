#!/usr/bin/env python3
"""make_uncovered_query.py — SCRATCH query generator (read-only on models/; writes only its --out file).
Builds: production model + one structural seed predicate per Stage-1 core (stage_seed.build_pred, unchanged)
+ run gen_lit { gen_useful_litmus ; not seed_0 ; ... ; not seed_k }.
SAT  = a production instance at this scope that contains NO Stage-1 core under the Stage-1.5 pin
       (a shape the two-stage corpus can never produce).  UNSAT = the cores cover the flat model at this scope.
Usage: make_uncovered_query.py --model STAGE1_alloy/models/STT_6.als --cores <dir> --out q.als [--scope-from 'exactly 6 Instruction' --scope-to 'exactly 3 Instruction']
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, 'STAGE1_alloy')
import stage_seed
ap = argparse.ArgumentParser()
ap.add_argument('--model', required=True); ap.add_argument('--cores', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--scope-from'); ap.add_argument('--scope-to')
ap.add_argument('--drop-ix', action='store_true')
a = ap.parse_args()
text = Path(a.model).read_text()
needle = "run gen_lit {\n  gen_useful_litmus\n}"
assert text.count(needle) == 1
preds, seen = [], set()
for n, c in enumerate(sorted(Path(a.cores).glob('inst-*.txt'))):
    p = stage_seed.build_pred(stage_seed.parse_txt(str(c)), f'seed_{n}')
    body = p.split('\n', 2)[2]
    if body in seen: continue          # textually identical seeds only; isomorphic ones are harmless here
    seen.add(body); preds.append((f'seed_{n}', p))
run = "run gen_lit {\n  gen_useful_litmus\n" + "".join(f"  not {nm}\n" for nm, _ in preds) + "}"
text = text.replace(needle, run)
if a.scope_from:
    assert text.count(a.scope_from) == 1; text = text.replace(a.scope_from, a.scope_to)
Path(a.out).write_text(text + "\n\n" + "\n\n".join(p for _, p in preds) + "\n")
print(f'{a.out}: {len(preds)} seed predicates negated')

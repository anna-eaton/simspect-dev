#!/usr/bin/env python3
"""amulet-perbug (2026-11-09): evaluate AMuLeT's own CleanupSpec predicates NON-exclusively.

AMuLeT's src/cleanupspec_analysis.py reports ONE cause per violation, in priority order
is_rwm_bug (UV3) > is_split_req (UV4) > is_too_much_cleaning (UV5) > manual hash table. So a
violation labelled UV3 may also satisfy the UV4 or UV5 predicate. This runs the unchanged source
up to (not including) its reporting block, then calls all three predicates on each violation's
cs_classify_t5/ dir (built by classify_t5.py). Sensitivity check only; the per-bug table uses
AMuLeT's exclusive label.
Usage (cwd = amulet-repo/src): cs_nonexclusive_t5.py <violations_CleanupSpec.json> <out.json>
"""
import json
import sys

src = open('cleanupspec_analysis.py').read()
head = src[:src.index("if is_rwm_bug():")]
IN, OUT = sys.argv[1], sys.argv[2]
rows = json.load(open(IN))
out = []
for r in rows:
    d = r['dir'] + '/cs_classify_t5'
    g = {'__name__': 'cs_nonexcl'}
    sys.argv[1:] = [d]
    try:
        exec(compile(head, 'cleanupspec_analysis.py', 'exec'), g)
        res = {'UV3_rwm': g['is_rwm_bug'](), 'UV4_split': g['is_split_req'](), 'UV5_too_much': g['is_too_much_cleaning']()}
    except SystemExit:  # ICache-only / both-caches paths exit early in the unchanged source
        res = {'early_exit': True}
    except Exception as e:
        res = {'error': repr(e)}
    out.append({'dir': r['dir'], 'round': r['round'], 'k': r['k'], 'event': r['event'], 'class': r['class'], **res})
json.dump(out, open(OUT, 'w'), indent=1)

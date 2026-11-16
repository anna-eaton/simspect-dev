#!/usr/bin/env python3
"""Predict which SpecLFB hits AMuLeT's own UV6 patch would close. Read-only; no gem5 run.

The patch is the one AMuLeT committed and then reverted in sith-lab/amulet-gem5 5f9ac78
("Reverting accidental isreallyUnsafe() patch", 2025-02-06; local copy:
wiki/reference/amulet_gem5/5f9ac78_reverting_accidental_isreallyUnsafe_patch.patch). Patched state:
  dyn_inst.hh  isUnsafe() = !isSquashed() && (isCUSL() || ismUSL())      (reallyUnsafe term removed)
  lsq_unit.cc  LSQUnit::updateSafeState walks from loadQueue.begin()     (the LQ head is no longer skipped)

Input: the hooks-v2 campaign triage (cafe2 gem5_dev,
/tests/simspect_fixed_20261030/results/STT_6_speclfb_v2hooks__20261107/triage/triage.json), which records
each offending load's flags at its last translation ("combo").

Class per offending load:
  A  non-head load with cusl=1 or musl=1 (safe only because reallyunsafe=0)  -> the patch makes it unsafe
  B  load-queue head with cusl=0 (never walked)                              -> the patch walks it; unsafe
                                                                               while older branches are unresolved
  C  non-head load with cusl=0 and musl=0 (walk saw "prior branches resolved": jmp shadow) -> unchanged
  U  already unsafe=1 at its last translation (replayed after it became safe)               -> unchanged

Run (from the Mac):  ssh cafe2 "docker exec -i gem5_dev python3 -" < STAGE3_gem5/triage/speclfb_uv6_patch_prediction.py
Write-up: wiki/findings/audits/2026-10-28/hooks_speclfb_and_uv6.md, "Update 2026-11-09".
"""
import collections
import json
import sys

TRIAGE = (sys.argv[1] if len(sys.argv) > 1 else
          '/tests/simspect_fixed_20261030/results/STT_6_speclfb_v2hooks__20261107/triage/triage.json')


def load_class(combo):
    f = {k: int(v) for k, v in (kv.split('=') for kv in combo.split())}
    if f['unsafe']:
        return 'U'
    if not f['lqhead'] and (f['cusl'] or f['musl']):
        return 'A'
    if f['lqhead']:
        return 'B'
    return 'C'


def main():
    d = json.load(open(TRIAGE))
    for mode, hits in d.items():
        by_tag = collections.defaultdict(collections.Counter)
        per_bucket = collections.defaultdict(collections.Counter)
        for h in hits:
            kinds, xmit_a = set(), False
            for e in h['events']:
                k = load_class(e['load']['combo'])
                kinds.add(k)
                by_tag[e['tag']][k] += 1
                if e['load'].get('is_xmit') and k == 'A':
                    xmit_a = True
            c = per_bucket[h['bucket']]
            c['hits'] += 1
            c['offender classes ' + ''.join(sorted(kinds))] += 1
            c['transmitter is a class A offender'] += xmit_a
        print('==', mode)
        print('  offending events by tag and class:')
        for tag, c in sorted(by_tag.items()):
            print('    %-40s %s' % (tag, dict(sorted(c.items()))))
        print('  hits by bucket:')
        for b, c in per_bucket.items():
            print('   ', b)
            for k, v in sorted(c.items()):
                print('       %-40s %d' % (k, v))


if __name__ == '__main__':
    main()

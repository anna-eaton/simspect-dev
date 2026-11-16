#!/usr/bin/env python3
"""AMuLeT per-bug tests to first detection from the T5 runs (amulet-perbug, 2026-11-09).

Usage (cafe1 gem5_dev, after perbug_replay.sh has replayed every violation):
  perbug_t5.py <out_dir> SpecLFB=<run> CleanupSpec=<run> InvisiSpec=<run>

Inputs per run (all written earlier, nothing re-simulated here):
  <run>/t5_classes_all.json     classify_t5.py --all: every violation replayed with AMuLeT's own
                                analyser under debug flags, classified (CleanupSpec by AMuLeT's
                                cleanupspec_analysis.py unchanged).
  <run>/benchmark-out-<D>/t5_instances.json   benchmark_t5.py: per instance (round), each 'Viol:'
                                increase = {viol k, progress P (program index), wall, cpu}.

Violation dir -> (instance, k): the round from config_input1.ini (bench_<p>_config0_round<N>),
k = rank of the dir's elapsed time (AMuLeT names report dirs by time since that fuzzer started)
among that round's violation dirs. Asserted: #dirs per round == #events per round.

Per bug, per instance: the first k whose violation carries the bug -> programs P, program x input
(P * 140, AMuLeT's src/benchmark.py:230 unit), CPU-s of the instance's process group at that
moment (same definitions as summarize_t5.py). mean / median / min over the instances that found
the bug; instances that never found it are counted, not averaged (censored at 200 programs).

SpecLFB jmp-shadow (wiki/findings/bug/speclfb_jmp_shadow/README.md; same rule as
STAGE3_gem5/timing/speclfb_analyze.py 'jmp_shadow', adapted to the native debug output of AMuLeT's
replay): a squashed load that brought in a differing line, never flagged speculative at any
translation (isCUSL = ismUSL = 0), with a direct unconditional JMP/CALL (dump mnemonic `jmp 0x..`
or `call 0x..`) fetched on that load's path between the squashing branch and the load
(squashing sn < jmp sn < load sn, and no other squash in between that would have removed the jmp).
"""
import glob
import json
import os
import re
import statistics as st
import sys
from collections import Counter, defaultdict

INPUTS = 140

BUGS_OF = {
    'SpecLFB': lambda c: {'UV6'} if c == 'UV6' else set(),
    'CleanupSpec': lambda c: {'UV3+UV4': {'UV3', 'UV4'}}.get(c, {c} if c in ('UV3', 'UV4', 'UV5', 'KV2') else set()),
    'InvisiSpec': lambda c: {'UV1': {'UV1'}, 'UV1+other': {'UV1'}, 'UV2_candidate': {'UV2'}}.get(c, set()),
}
BUG_LIST = {'SpecLFB': ['UV6', 'jmp_shadow'], 'CleanupSpec': ['UV3', 'UV4', 'UV5', 'KV2'], 'InvisiSpec': ['UV1', 'UV2']}

RE_XLATE = re.compile(r'^(\d+): SingleDataRequest: Initiating Translation inst \[sn:(\d+)\] sPC (\w+) .*?isCUSL: (\d)\. ismUSL: (\d), isStore: (\d)\. isUnsafe: (\d), isreallyUnsafe: (\d)')
RE_ATTEMPT = re.compile(r'^(\d+): .*Attempting load request - PC (0x\w+), SQ: \[sn:(\d+)\], Paddr (0x\w+)')
RE_SQLOAD = re.compile(r'^(\d+): .*LSQUnit - Squashed Load: PC 0x\w+, SQ: \[sn:(\d+)\]')
RE_SQUASH = re.compile(r'^(\d+): system\.cpu\.(?:branchPred: \[tid:\d+\] Squashing from sequence number (\d+)|iew\.lsq\.thread0: Squashing from \[sn:(\d+)\])')
RE_UNCOND = re.compile(r'^(\d+): system\.cpu\.branchPred: \[tid:\d+\] \[sn:(\d+)\] Creating prediction history for PC \((0x\w+)=>')
RE_MISP = re.compile(r'^(\d+): system\.cpu\.branchPred: analyse_ipc_violation: Mispredicted branch at PC (0x\w+)')


def dump_mnemonics(path):
    m = {}
    for line in open(path, errors='replace'):
        mm = re.match(r'\s*([0-9a-f]+):\s+(.*)$', line)
        if mm:
            m[int(mm.group(1), 16)] = mm.group(2).strip()
    return m


def is_direct_uncond(txt):
    return bool(re.match(r'(jmp|call)\s+0x[0-9a-f]+\s*$', txt or ''))


def speclfb_jmp_shadow(vdir, diffs):
    """Return per-leaking-load evidence and whether any satisfies the jmp-shadow signature."""
    a = f'{vdir}/analysis_t5'
    dumpf = glob.glob(f'{a}/test_case_rvzr.dump')
    mn = dump_mnemonics(dumpf[0]) if dumpf else {}
    out = []
    for run_name, key in (('reference', 'ref_only'), ('primer', 'primer_only')):
        logs = [x for x in glob.glob(f'{a}/{run_name}_log_*.out')]
        if not logs:
            continue
        xl, att, sql, squashes, ctrl = defaultdict(list), [], {}, [], {}
        misp_pc = {}
        for line in open(logs[0], errors='replace'):
            m = RE_XLATE.match(line)
            if m:
                xl[int(m.group(2))].append((int(m.group(1)), int(m.group(4)), int(m.group(5)), int(m.group(7))))
                continue
            m = RE_ATTEMPT.match(line)
            if m:
                att.append((int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4), 16)))
                continue
            m = RE_SQLOAD.match(line)
            if m:
                sql.setdefault(int(m.group(2)), int(m.group(1)))
                continue
            m = RE_SQUASH.match(line)
            if m:
                squashes.append((int(m.group(1)), int(m.group(2) or m.group(3))))
                continue
            m = RE_UNCOND.match(line)
            if m:
                ctrl.setdefault(int(m.group(2)), (int(m.group(1)), int(m.group(3), 16)))
        lines = set()
        for sec, d in diffs.items():
            lines |= {int(x, 16) for x in d[key]}
        seen = set()
        for tick, pc, sn, pa in att:
            if (pa & ~63) not in lines or sn not in sql or sn in seen:
                continue
            seen.add(sn)
            t_sq = sql[sn]
            # squash that removed this load: the squash at its squash tick with the largest sn < load sn
            cand = [x for t, x in squashes if x < sn and abs(t - t_sq) <= 1000]
            X = max(cand) if cand else None
            flags = xl.get(sn, [])
            never_spec = bool(flags) and all(c == 0 and u == 0 for _, c, u, _ in flags)
            jmps = []
            if X is not None:
                for J, (tj, pcj) in ctrl.items():
                    if not (X < J < sn) or not is_direct_uncond(mn.get(pcj)):
                        continue
                    # J must survive until the load's squash: no other squash with X <= sn' < J after J's fetch
                    killed = any(X <= x < J and tj <= t < t_sq - 1000 for t, x in squashes)
                    if not killed:
                        jmps.append({'sn': J, 'pc': hex(pcj), 'insn': mn.get(pcj)})
            Xpc = ctrl.get(X, (None, None))[1] if X is not None else None
            out.append({'run': run_name, 'load_sn': sn, 'load_pc': pc, 'line': hex(pa & ~63),
                        'never_cusl_musl': never_spec, 'flags(tick,cusl,musl,unsafe)': flags[:3],
                        'squash_sn': X, 'squash_pc': hex(Xpc) if Xpc else None,
                        'squash_insn': mn.get(Xpc) if Xpc else None,
                        'direct_jmps_between': jmps,
                        'jmp_shadow': never_spec and bool(jmps) and not is_direct_uncond(mn.get(Xpc))})
    return out


def round_of(vdir):
    """Instance round from config_input1.ini, else config_input2.ini (5 SpecLFB dirs carry the
    process name only in input2)."""
    for n in (1, 2):
        try:
            m = re.search(r'config0_round(\d+)', open(f'{vdir}/config_input{n}.ini').read())
        except OSError:
            continue
        if m:
            return int(m.group(1))
    return None


def violation_order(run, D):
    """dir -> (round, k) with k = 1-based rank of elapsed within the round, matched to the k-th
    'Viol:' increase. A violation in an instance's LAST program never appears on a status line
    (the fuzzer exits first), so when the log's final violation count exceeds the recorded events,
    one synthetic final event is added: programs = the instance's final program count, CPU-s = its
    final CPU (t5_summary.json per_instance). Sanity check: each dir's elapsed (since that fuzzer
    started) must not exceed the matched event's wall (since benchmark launch)."""
    cls = json.load(open(f'{run}/t5_classes_all.json'))
    summ = {p['round']: p for p in json.load(open(f'{run}/t5_summary.json'))['per_instance']}
    by_round = defaultdict(list)
    for v in cls['violations']:
        v['round'] = round_of(v['dir'])
        by_round[v['round']].append(v)
    inst = json.load(open(glob.glob(f'{run}/benchmark-out-*/t5_instances.json')[0]))['instances']
    ev = {r['round']: list(r['events']) for r in inst}
    # a dir whose ini names no round (1 SpecLFB dir): give it to the one round that has more
    # events than dirs and an event 0-3 s after the dir's elapsed time (asserted unique)
    for v in list(by_round.get(None, [])):
        cands = [r for r in ev if len(by_round.get(r, [])) < len(ev[r])
                 and any(0 <= e['wall'] - v['elapsed'] <= 3 for e in ev[r])]
        assert len(cands) == 1, (run, v['dir'], cands)
        v['round'] = cands[0]; v['round_by_time'] = True
        by_round[cands[0]].append(v); by_round[None].remove(v)
    if not by_round.get(None):
        by_round.pop(None, None)
    for r in inst:
        e, p = ev[r['round']], summ[r['round']]
        nd = len(by_round.get(r['round'], []))
        if nd == len(e) + 1:
            last = max(v['elapsed'] for v in by_round[r['round']])
            assert not e or last > e[-1]['wall'], (run, r['round'])
            e.append({'viol': len(e) + 1, 'progress': p['programs'], 'cpu': p['cpu_final'],
                      'wall': p['wall_final'], 'synthetic_final': True})
    mism, order_bad = [], []
    for rnd, vs in by_round.items():
        vs.sort(key=lambda v: v['elapsed'])
        if len(vs) != len(ev.get(rnd, [])):
            mism.append((rnd, len(vs), len(ev.get(rnd, []))))
        for k, v in enumerate(vs, 1):
            v['k'] = k
            e = ev[rnd][k - 1] if k <= len(ev.get(rnd, [])) else None
            v['event'] = e
            if e and e.get('wall') is not None and v['elapsed'] > e['wall']:
                order_bad.append((rnd, k, v['elapsed'], e['wall']))
    return cls, ev, mism + [('elapsed>wall',) + x for x in order_bad], len(inst)


def stats(xs):
    return {'mean': st.fmean(xs), 'median': st.median(xs), 'min': min(xs), 'max': max(xs)} if xs else None


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for arg in sys.argv[2:]:
        D, run = arg.split('=', 1)
        cls, ev, mism, n_inst = violation_order(run, D)
        vs = cls['violations']
        for v in vs:
            v['bugs'] = set(BUGS_OF[D](v['class']))
            if D == 'SpecLFB' and v['class'] != 'not_reproduced':
                js = speclfb_jmp_shadow(v['dir'], v['evidence'].get('diffs', {}))
                v['jmp_shadow_evidence'] = js
                if any(x['jmp_shadow'] for x in js):
                    v['bugs'].add('jmp_shadow')
        per_bug = {}
        for b in BUG_LIST[D] + sorted({x for v in vs for x in v['bugs']} - set(BUG_LIST[D])):
            firsts = []
            for rnd in sorted(ev):
                hits = sorted((v for v in vs if v['round'] == rnd and b in v['bugs']), key=lambda v: v['k'])
                if hits and hits[0]['event']:
                    e = hits[0]['event']
                    firsts.append({'round': rnd, 'k': hits[0]['k'], 'programs': e['progress'], 'cpu': e['cpu'],
                                   'wall': e['wall'], 'dir': os.path.basename(hits[0]['dir'])})
            per_bug[b] = {'instances_found': len(firsts), 'instances': n_inst,
                          'violations_with_bug': sum(1 for v in vs if b in v['bugs']),
                          'programs': stats([f['programs'] for f in firsts]),
                          'program_x_input': stats([f['programs'] * INPUTS for f in firsts]),
                          'cpu_s': stats([f['cpu'] for f in firsts]),
                          'firsts': firsts}
        extra = {}
        if D == 'SpecLFB':
            nonuv6 = [v for v in vs if v['class'] != 'UV6']
            extra = {'violations_with_jmp_shadow': sum('jmp_shadow' in v['bugs'] for v in vs),
                     'jmp_shadow_among_non_UV6': sum('jmp_shadow' in v['bugs'] for v in nonuv6),
                     'non_UV6': len(nonuv6),
                     'non_UV6_by_class_and_jmp': dict(Counter(f"{v['class']}|jmp_shadow={'jmp_shadow' in v['bugs']}" for v in nonuv6)),
                     'non_UV6_squash_insn': dict(Counter(f"{v['class']}|" + ';'.join(sorted({str(x['squash_insn']) for x in v.get('jmp_shadow_evidence', [])})) for v in nonuv6))}
        report[D] = {'run': run, 'violations': len(vs), 'class_counts': dict(Counter(v['class'] for v in vs)),
                     'dir_event_count_mismatch(round,dirs,events)': mism, 'per_bug': per_bug, **extra}
        rows = [{k: (sorted(v[k]) if k == 'bugs' else v[k]) for k in ('round', 'k', 'elapsed', 'class', 'bugs', 'event', 'dir')}
                | ({'jmp_shadow_evidence': v.get('jmp_shadow_evidence')} if D == 'SpecLFB' else {}) for v in vs]
        json.dump(rows, open(f'{out_dir}/violations_{D}.json', 'w'), indent=1)
    json.dump(report, open(f'{out_dir}/perbug_summary.json', 'w'), indent=1)
    for D, r in report.items():
        print(f"== {D}: {r['violations']} violations, classes {r['class_counts']}, mismatches {r['dir_event_count_mismatch(round,dirs,events)']}")
        for b, p in r['per_bug'].items():
            f = lambda s, k: ('-' if not s else f"{s['mean']:.1f}/{s['median']}/{s['min']}" if k else '')
            print(f"  {b}: found {p['instances_found']}/{p['instances']} (viol {p['violations_with_bug']}); programs {f(p['programs'],1)}; PxI {f(p['program_x_input'],1)}; CPU-s {f(p['cpu_s'],1)}")
        for k in ('violations_with_jmp_shadow', 'jmp_shadow_among_non_UV6', 'non_UV6', 'non_UV6_by_class_and_jmp', 'non_UV6_squash_insn'):
            if k in r:
                print(f'  {k}: {r[k]}')


if __name__ == '__main__':
    main()

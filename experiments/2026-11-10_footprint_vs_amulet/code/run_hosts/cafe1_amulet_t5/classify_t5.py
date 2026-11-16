#!/usr/bin/env python3
"""Classify AMuLeT T5 violations by bug class (firstdet-amulet, 2026-11-09).

Usage (cwd = amulet-repo/src, PATH has /opt/amulet-venv/bin first):
  classify_t5.py <run_dir> <Defense> [--all] [--jobs 8]

For each instance (benchmark round) the FIRST violation dir is selected (or every
violation with --all). Mapping violation dir -> instance: the round id in
config_input1.ini (process name bench_<p>_config0_round<N>); first = smallest elapsed
time in the dir name (AMuLeT names report dirs by time since the fuzzer started).

Each selected violation is replayed with AMuLeT's own analyser
(src/analyse_ipc_violation.py; path-only copy analyse_ipc_violation_t5.py) with debug
flags, into <violation>/analysis_t5/, stdout in <violation>/analysis_t5.txt. Then:

  SpecLFB  -> UV6 if a line present in one run but not the other was brought in by a
              squashed load that SpecLFB flagged speculative (isCUSL or ismUSL = 1) but
              not unsafe (isUnsafe = 0, isreallyUnsafe = 0): the 'first speculative load
              not protected' signature (fu-2025-amulet.pdf p12, sec 4.7).
  CleanupSpec -> AMuLeT's own classifier src/cleanupspec_analysis.py (unchanged) on a dir
              holding the replay's cache tags + ProtocolTrace logs:
              'Speculative Store Not Cleaned' = UV3, 'Split Requests Not Cleaned' = UV4,
              'Too Much Cleaning' = UV5, 'difference in ICache ... UnXpec' = KV2.
  InvisiSpec -> UV1 if a differing L1D line is absent in one run because a squashed
              (speculative) load in that run evicted it (ProtocolTrace L1_Replacement while
              the triggering request is SPEC_LD / a squashed load); UV2 if the analyser
              reports a non-speculative access to the differing line (expose delayed);
              otherwise unclassified. (heuristic; see t5_classes.json 'evidence')
Writes <run_dir>/t5_classes.json.
"""
import json
import os
import re
import subprocess
import sys
import glob
from concurrent.futures import ThreadPoolExecutor

T5 = '/tests/simspect_alloy_20261108/timing/amulet_t5'
FLAGS = {
    'SpecLFB': 'LSQUnit,Squashed,Branch,AnalyseIPC,Speclfb',
    'CleanupSpec': 'LSQUnit,Squashed,Branch,ProtocolTrace',
    'InvisiSpec': 'LSQUnit,Squashed,Branch,AnalyseIPC,ProtocolTrace',
    'STT': 'LSQUnit,Squashed,Branch,AnalyseIPC',
}
EXTRA = {
    'SpecLFB': '--SpecLFB',
    'CleanupSpec': '--ruby --CleanupSpec',
    'InvisiSpec': '--ruby --InvisiSpec --InvisiSpec_Futuristic',
    'STT': '--ruby --STT --STT_Futuristic',
}


def elapsed(name):
    m = re.match(r'(\d+)hrs-(\d+)mins-(\d+)secs(?:-(\d+)us)?', name)
    if not m:
        return None
    h, mi, s, us = m.groups()
    return int(h) * 3600 + int(mi) * 60 + int(s) + (int(us) / 1e6 if us else 0)


def violations(run, D):
    base = f'{run}/benchmark-out-{D}/config0results'
    out = []
    for v in sorted(glob.glob(f'{base}/*')):
        if v.endswith('_bugs') or not os.path.isdir(v):
            continue
        try:
            ini = open(f'{v}/config_input1.ini').read()
        except OSError:
            continue
        m = re.search(r'config0_round(\d+)', ini)
        out.append({'dir': v, 'round': int(m.group(1)) if m else None, 'elapsed': elapsed(os.path.basename(v))})
    return out


def replay(v, run, D):
    yaml = glob.glob(f'{run}/*.yaml')[0]
    src = os.getcwd()
    tag = 't5ana_' + D + '_' + re.sub(r'[^0-9A-Za-z]', '', os.path.basename(run))[-12:] + '_' + re.sub(r'[^0-9A-Za-z]', '', os.path.basename(v))
    outtxt = f'{v}/analysis_t5.txt'
    if os.path.exists(outtxt) and os.path.isdir(f'{v}/analysis_t5') and os.listdir(f'{v}/analysis_t5'):
        return outtxt
    cmd = [sys.executable, f'{T5}/analyse_ipc_violation_t5.py', v, '--no-color', '-p', tag,
           '--analysis-dir', f'{v}/analysis_t5',
           '--args', f'-c {yaml} -s {src}/x86/isa_spec/base.json {EXTRA[D]}',
           '--debug-flags', FLAGS[D]]
    with open(outtxt, 'w') as f:
        f.write('cmd: ' + ' '.join(cmd) + '\n')
        f.flush()
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        f.write(f'\nreturncode: {r.returncode}\n')
    # clean the analyser's own debug + gem5 output dirs for this tag
    subprocess.run(['rm', '-rf', f'debug-{tag}'] + glob.glob(f'{run}/m5out-{tag}') + glob.glob(f'{run}/checkpoint-{tag}'))
    return outtxt


def tags_of(path):
    """cache tags file -> {section: set(int)} (AMuLeT plain format)."""
    secs, cur = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith('['):
            cur = line
        elif line.startswith('addresses=') and cur:
            secs[cur] = {int(x) for x in line.split('=', 1)[1].split() if x}
    return secs


def analysis_files(v):
    a = f'{v}/analysis_t5'
    f = {}
    for name in os.listdir(a):
        for pre in ('reference', 'primer'):
            if name.startswith(f'{pre}_cache_tags_') and not name.endswith('.toml'):
                f[f'{pre}_tags'] = f'{a}/{name}'
            if name.startswith(f'{pre}_log_') and name.endswith('.out'):
                f[f'{pre}_log'] = f'{a}/{name}'
    return f


def dcache_diff(f):
    rt, pt = tags_of(f['reference_tags']), tags_of(f['primer_tags'])
    diffs = {}
    for sec in set(rt) | set(pt):
        a, b = rt.get(sec, set()), pt.get(sec, set())
        if a != b:
            diffs[sec] = {'ref_only': sorted(a - b), 'primer_only': sorted(b - a)}
    return diffs


def speclfb_class(v):
    f = analysis_files(v)
    diffs = dcache_diff(f)
    if not diffs:
        return 'not_reproduced', {}
    ev = []
    for run_name, key in (('reference', 'ref_only'), ('primer', 'primer_only')):
        log = open(f[f'{run_name}_log'], errors='replace').read()
        flags = {}
        for m in re.finditer(r'Initiating Translation inst \[sn:(\d+)\] sPC (\w+) .*?isCUSL: (\d)\. ismUSL: (\d), isStore: (\d)\. isUnsafe: (\d), isreallyUnsafe: (\d)', log):
            flags.setdefault(int(m.group(1)), []).append((m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7))))
        squashed = {int(m.group(1)) for m in re.finditer(r'LSQUnit - Squashed Load: PC 0x\w+, SQ: \[sn:(\d+)\]', log)}
        for sec, d in diffs.items():
            for line in d[key]:
                for m in re.finditer(r'Attempting load request - PC (0x\w+), SQ: \[sn:(\d+)\], Paddr (0x\w+)', log):
                    if (int(m.group(3), 16) & ~63) != line:
                        continue
                    sn = int(m.group(2))
                    fl = flags.get(sn)
                    ev.append({'run': run_name, 'cache': sec, 'line': hex(line), 'pc': m.group(1), 'sn': sn,
                               'squashed': sn in squashed, 'flags(spc,isCUSL,ismUSL,isStore,isUnsafe,isreallyUnsafe)': fl})
    K = 'flags(spc,isCUSL,ismUSL,isStore,isUnsafe,isreallyUnsafe)'
    # UV6: a squashed load that SpecLFB saw as speculative (isCUSL or ismUSL) but not unsafe
    uv6 = [e for e in ev if e['squashed'] and any((t[1] or t[2]) and t[4] == 0 for t in (e[K] or []))]
    # squashed load never flagged speculative at any translation (CUSL=mUSL=0): SpecLFB did not
    # see it as speculative (e.g. a shadow it does not track); not one of the paper's classes
    nospec = [e for e in ev if e['squashed'] and e[K] and all(not t[1] and not t[2] for t in e[K])]
    dd = {k: {kk: [hex(x) for x in vv] for kk, vv in d.items()} for k, d in diffs.items()}
    if uv6:
        return 'UV6', {'diffs': dd, 'uv6_loads': uv6[:4]}
    if nospec:
        return 'squashed_load_not_flagged_speculative', {'diffs': dd, 'loads': nospec[:4]}
    # unsafe-flagged squashed load that was stalled by SpecLFB ('LFB Stall') and later re-sent
    # to the cache while still speculative (not one of the paper's classes)
    reissued = []
    for e in ev:
        if not e['squashed']:
            continue
        log = open(f[f"{e['run']}_log"], errors='replace').read()
        n_sent = len(re.findall(rf"Successfully sent out load request - PC {e['pc']}, SQ: \[sn:{e['sn']}\]", log))
        stalled = f"LFB Stall: wasHitUSL now stalled - PC {e['pc']}, SQ: [sn:{e['sn']}]" in log
        if stalled and n_sent >= 2 and all(t[4] == 1 for t in (e[K] or [(0, 0, 0, 0, 0, 0)])):
            reissued.append({**e, 'n_sent': n_sent})
    if reissued:
        return 'unsafe_load_resent_after_LFB_stall', {'diffs': dd, 'loads': reissued[:4]}
    return 'unclassified', {'diffs': dd, 'accesses': ev[:8]}


def cleanupspec_class(v):
    f = analysis_files(v)
    diffs = dcache_diff(f)
    if not diffs:
        return 'not_reproduced', {}
    d = f'{v}/cs_classify_t5'
    os.makedirs(d, exist_ok=True)
    for src, dst in ((f['reference_tags'], 'cache_tags_1'), (f['primer_tags'], 'cache_tags_2'),
                     (f['reference_log'], 'protocol-trace-reference.txt'), (f['primer_log'], 'protocol-trace-primer.txt')):
        if os.path.lexists(f'{d}/{dst}'):
            os.remove(f'{d}/{dst}')
        os.symlink(src, f'{d}/{dst}')
    r = subprocess.run([sys.executable, 'cleanupspec_analysis.py', d], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    cls = 'unclassified'
    if 'Speculative Store Not Cleaned' in out and 'Split' in out:
        cls = 'UV3+UV4'
    elif 'Speculative Store Not Cleaned' in out:
        cls = 'UV3'
    elif 'Split Requests Not Cleaned' in out:
        cls = 'UV4'
    elif 'Too Much Cleaning' in out:
        cls = 'UV5'
    elif 'UnXpec' in out:
        cls = 'KV2'
    elif 'both ICache and DCache' in out:
        cls = 'ICache+DCache (multiple)'
    return cls, {'amulet_classifier_output': out[-600:],
                 'diffs': {k: {kk: [hex(x) for x in vv] for kk, vv in dd.items()} for k, dd in diffs.items()}}


def invisispec_class(v):
    """UV1 (fu-2025-amulet.pdf p10-11): a squashed (speculative) load whose L1D set equals the
    set of a line that is absent in that run (and present in the other) and that run's
    ProtocolTrace shows an L1_Replacement of that line. UV2 candidate (p11): the analyser finds a
    non-speculative access to a differing line (an Expose that did not complete)."""
    f = analysis_files(v)
    diffs = dcache_diff(f)
    l1d = [k for k in diffs if 'L1Dcache' in k]
    if not diffs:
        return 'not_reproduced', {}
    dd = {k: {kk: [hex(x) for x in vv] for kk, vv in d.items()} for k, d in diffs.items()}
    if not l1d:
        return 'L1I_only (KV1-like)', {'diffs': dd}
    d = diffs[l1d[0]]
    nsets = 64  # 32 kB / 64 B / 8 ways (YAML l1d_size, l1d_assoc)
    setof = lambda a: (a >> 6) % nsets
    logs = {r: open(f[f'{r}_log'], errors='replace').read() for r in ('reference', 'primer')}
    absent_in = {'primer': d['ref_only'], 'reference': d['primer_only']}
    expl, unexpl = [], []
    for run_name, lines in absent_in.items():
        log = logs[run_name]
        sq = {int(m.group(1)) for m in re.finditer(r'LSQUnit - Squashed Load: PC 0x\w+, SQ: \[sn:(\d+)\]', log)}
        loads = [(m.group(1), int(m.group(2)), int(m.group(3), 16)) for m in
                 re.finditer(r'Attempting load request - PC (0x\w+), SQ: \[sn:(\d+)\], Paddr (0x\w+)', log)]
        for L in lines:
            cand = [(pc, sn, hex(pa)) for pc, sn, pa in loads if sn in sq and setof(pa) == setof(L)]
            repl = re.search(rf'L1_Replacement\s+\S+\s+\[0x[0-9a-f]+, line {hex(L)}\]', log) is not None
            (expl if (cand and repl) else unexpl).append({'absent_in': run_name, 'line': hex(L), 'set': setof(L),
                                                          'L1_Replacement_seen': repl, 'squashed_loads_same_set': cand[:3]})
    txt = open(f'{v}/analysis_t5.txt', errors='replace').read()
    nonspec = 'Non-speculative violation found!' in txt
    ev = {'diffs': dd, 'explained_by_spec_eviction': expl, 'unexplained': unexpl, 'nonspec_access_to_diff_line': nonspec}
    if expl and not unexpl:
        return 'UV1', ev
    if nonspec and not expl:
        return 'UV2_candidate', ev
    if expl:
        return 'UV1+other', ev
    return 'unclassified', ev


CLASSIFY = {'SpecLFB': speclfb_class, 'CleanupSpec': cleanupspec_class, 'InvisiSpec': invisispec_class}


def main():
    run, D = sys.argv[1].rstrip('/'), sys.argv[2]
    all_ = '--all' in sys.argv
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 8
    vs = violations(run, D)
    sel = vs
    if not all_:
        first = {}
        for x in vs:
            if x['round'] is None or x['elapsed'] is None:
                continue
            if x['round'] not in first or x['elapsed'] < first[x['round']]['elapsed']:
                first[x['round']] = x
        sel = [first[k] for k in sorted(first)]
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(lambda x: replay(x['dir'], run, D), sel))
    res = []
    for x in sel:
        try:
            cls, ev = CLASSIFY.get(D, lambda v: ('no_classifier', {}))(x['dir'])
        except Exception as e:  # keep going; record the error
            cls, ev = 'error', {'error': repr(e)}
        res.append({**x, 'class': cls, 'evidence': ev})
    from collections import Counter
    out = {'defense': D, 'run': run, 'selection': 'all' if all_ else 'first_per_instance',
           'counts': dict(Counter(r['class'] for r in res)), 'violations': res}
    json.dump(out, open(f"{run}/t5_classes{'_all' if all_ else ''}.json", 'w'), indent=1)
    print(json.dumps(out['counts']))
    for r in res:
        print(r['round'], os.path.basename(r['dir']), r['class'])


if __name__ == '__main__':
    main()

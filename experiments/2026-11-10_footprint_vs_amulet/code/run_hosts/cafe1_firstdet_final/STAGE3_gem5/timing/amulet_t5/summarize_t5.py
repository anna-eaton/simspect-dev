#!/usr/bin/env python3
"""Summarize one T5 AMuLeT campaign run dir (firstdet-amulet, 2026-11-09).

Reads <run>/benchmark-out-<D>/{t5_instances.json, t5_rusage_children.json, info.txt}
(written by benchmark_t5.py) and prints + writes <run>/t5_summary.json.

Definitions (from AMuLeT's own code, src/benchmark.py and src/fuzzer.py @ c871bdf):
  - program  = one generated test program (fuzzer.py round); 'Progress: P' = P programs done.
  - test case (AMuLeT's unit for 'Testing Throughput') = program x input; benchmark.py
    counts programs * input_count * 2 ('*2 due to each input being boosted'), i.e. 140
    per program at -i 70.
  - a 'violation' = one violating program (fuzzing_round returns at most one).
  - first violation of an instance: the first event where 'Viol:' increases; its
    'progress' P is the 1-based index of the violating program (the status line is
    printed at the start of round P, after P programs finished).
  - CPU-s = utime+stime(+cutime+cstime) of the instance's process group (cli.py and its
    gem5 IPC workers) read from /proc at that moment.
"""
import json
import statistics as st
import sys
import glob
import os


def q(xs, f):
    return f(xs) if xs else None


def main(run):
    bo = glob.glob(f'{run}/benchmark-out-*')[0]
    d = json.load(open(f'{bo}/t5_instances.json'))
    ru_path = f'{bo}/t5_rusage_children.json'
    ru = json.load(open(ru_path)) if os.path.exists(ru_path) else None
    inputs_per_program = None
    info = open(f'{bo}/info.txt').read() if os.path.exists(f'{bo}/info.txt') else ''
    for line in info.splitlines():
        if line.startswith('input_count:'):
            inputs_per_program = int(line.split(':')[1])
    if inputs_per_program is None:
        inputs_per_program = 140
    inst = d['instances']
    firsts, cpus, walls, censored = [], [], [], []
    tot_prog = tot_viol = 0
    tot_cpu = 0.0
    per = []
    for r in inst:
        ex = r.get('exit') or {}
        progs = r.get('progress_sample')
        # final program count: last Progress seen (benchmark's 'Test Cases' column);
        # the per-instance log has it; fall back to sample
        logf = f"{bo}/log_round{r['round']}_config000"
        if os.path.exists(logf):
            import re
            txt = open(logf, 'rb').read().decode(errors='replace')
            m = re.findall(r'Progress:\s*(\d+)', txt)
            if m:
                progs = int(m[-1])
            v = re.findall(r'Viol:(\d+)', txt)
            nviol = int(v[-1]) if v else 0
        else:
            nviol = r['events'][-1]['viol'] if r['events'] else 0
        cpu_final = max([x for x in [ex.get('rusage_cpu'), ex.get('cpu_sample_before_exit'), r.get('cpu_sample')] if x is not None] or [0])
        tot_prog += progs or 0
        tot_viol += nviol
        tot_cpu += cpu_final
        e0 = r['events'][0] if r['events'] else None
        per.append({'round': r['round'], 'programs': progs, 'violations': nviol, 'cpu_final': cpu_final,
                    'wall_final': ex.get('wall'), 'returncode': ex.get('returncode'),
                    'first_program': e0['progress'] if e0 else None,
                    'first_cpu': e0['cpu'] if e0 else None, 'first_wall': e0['wall'] if e0 else None})
        if e0:
            firsts.append(e0['progress']); cpus.append(e0['cpu']); walls.append(e0['wall'])
        else:
            censored.append(progs)
    s = {
        'run': run, 'instances': len(inst), 'instances_with_violation': len(firsts),
        'censored_instances_programs': censored,
        'inputs_per_program': inputs_per_program,
        'first_programs': {'mean': q(firsts, st.fmean), 'median': q(firsts, st.median), 'min': q(firsts, min), 'max': q(firsts, max), 'all': sorted(firsts)},
        'first_test_cases(programs*inputs)': {'mean': q(firsts, st.fmean) and st.fmean(firsts) * inputs_per_program,
                                              'median': q(firsts, st.median) and st.median(firsts) * inputs_per_program,
                                              'min': q(firsts, min) and min(firsts) * inputs_per_program},
        'first_cpu_s': {'mean': q(cpus, st.fmean), 'median': q(cpus, st.median), 'min': q(cpus, min), 'max': q(cpus, max)},
        'first_wall_s': {'mean': q(walls, st.fmean), 'median': q(walls, st.median), 'min': q(walls, min)},
        'total_programs': tot_prog, 'total_violations': tot_viol,
        'pooled_programs_per_violation': tot_prog / tot_viol if tot_viol else None,
        'total_cpu_s_instances': tot_cpu,
        'cpu_s_per_program': tot_cpu / tot_prog if tot_prog else None,
        'pooled_cpu_s_per_violation': tot_cpu / tot_viol if tot_viol else None,
        'rusage_children': ru,
        'per_instance': per,
    }
    json.dump(s, open(f'{run}/t5_summary.json', 'w'), indent=1)
    p = {k: v for k, v in s.items() if k != 'per_instance'}
    print(json.dumps(p, indent=1))


if __name__ == '__main__':
    main(sys.argv[1].rstrip('/'))

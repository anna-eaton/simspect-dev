#!/usr/bin/env python3
"""summarize.py (agent testcost, 2026-11-16): per-test cost breakdown from run_profile.sh / run_fast.sh outputs.

    python3 summarize.py /tests/testcost_20261116 [--time1 /tests/timing_20261115/simspect] > summary.json

Per build (T1g InvisiSpec, T2g CleanupSpec, T3g SpecLFB), mean CPU-s per test over the profiled tests:
  harness      production total (prod_<R>/results.jsonl total_cpu_s, the whole `pipeline.py gem5` tree) minus
               everything profile_test measured inside process_one + staging = 2 Python interpreters + imports +
               pipeline.py's own work + checker CLI
  hook_scan    gem5_common.binary_has_resolve_hooks (reads the whole gem5 binary, once per checker process)
  toolchain    as/ld (build_binary, twice for non-warm cache setups), objdump/nm (_func_base_addr, _disasm,
               _litmus_labels, cache_setup._nm/_rows) incl. their Python, + transform_asm / remap_annotation
  gem5_startup gem5 on an exit-only binary with the run's exact flags, no trace (variant trivial_bin_no_trace)
  gem5_sim     gem5 variant no_trace minus gem5_startup (simulating the test, incl. cache-setup code)
  gem5_trace   gem5 actual run minus no_trace (writing O3PipeView + Commit + hook lines)
  parse        the 8 trace passes (parse_pipeview, _by_seq x2, parse_simspect_events x2, parse_lsq,
               parse_commit_ticks, parse_commit_squashes)
  checker      check_footprint.evaluate + execution_validity + branch plan + the rest of process_one's Python
Measured on a loaded node (load 60-75 on 64 threads), so every row is also scaled per test by
TIME-1 idle total / this run's production total for the SAME (mode, stem) (column *_idle_est).
"""
import json, statistics as st, sys
from pathlib import Path

B = Path(sys.argv[1])
T1 = Path(sys.argv[sys.argv.index("--time1") + 1]) if "--time1" in sys.argv else None
TOOL = ("gem5_common.build_binary", "gem5_common._func_base_addr", "gem5_common._disasm",
        "gem5_common._litmus_labels", "cache_setup._nm", "cache_setup._rows", "cache_setup.transform_asm",
        "cache_setup.remap_annotation", "cache_setup.prepare")
PARSE = ("gem5_common.parse_pipeview", "gem5_common.parse_pipeview_by_seq", "gem5_common.parse_simspect_events",
         "gem5_common.parse_lsq", "gem5_common.parse_commit_ticks", "gem5_common.parse_commit_squashes",
         "gem5_common.parse_branch_events")
CATS = ("harness", "hook_scan", "toolchain", "gem5_startup", "gem5_sim", "gem5_trace", "parse", "checker")


def rows(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


out = {}
for R in ("T1g", "T2g", "T3g"):
    prof = {(r["mode"], r["stem"]): r for r in rows(B / f"prof_{R}" / "profile.jsonl") if "funcs" in r}
    prod = {(r["mode"], r["stem"]): r for r in rows(B / f"prod_{R}" / "results.jsonl")}
    t1 = {(r["mode"], r["stem"]): r for r in rows(T1 / f"{R}_p16" / "results.jsonl")} if T1 else {}
    fast = {(r["mode"], r["stem"]): r for r in rows(B / f"fast_{R}" / "fast.jsonl") if "cpu_s" in r}
    per = []
    for k, p in prof.items():
        f = p["funcs"]
        tot = lambda n: (f.get(n, [0, 0])[0] + f.get(n, [0, 0])[1])
        v = p.get("gem5_variants") or {}
        gem5_actual = f.get("gem5_common._run_bounded", [0, 0])[1]
        g_start = v.get("trivial_bin_no_trace", [None])[0]
        g_notr = v.get("no_trace", [None])[0]
        inside = p["stage_cpu"] + p["process_one_self"] + p["process_one_children"]
        c = dict(hook_scan=tot("gem5_common.binary_has_resolve_hooks"),
                 toolchain=sum(tot(n) for n in TOOL),
                 parse=sum(tot(n) for n in PARSE))
        if g_start is not None and g_notr is not None:
            c.update(gem5_startup=min(g_start, gem5_actual), gem5_sim=max(0.0, g_notr - g_start),
                     gem5_trace=max(0.0, gem5_actual - g_notr))
        else:
            c.update(gem5_startup=gem5_actual, gem5_sim=0.0, gem5_trace=0.0)
        named = sum(c.values())
        c["checker"] = max(0.0, inside - named)
        pr = prod.get(k)
        c["harness"] = max(0.0, pr["total_cpu_s"] - inside) if pr else None
        row = dict(key=list(k), cache_setup=p.get("cache_setup"), trace_lines=(p.get("trace") or {}).get("lines"),
                   trace_commit=(p.get("trace") or {}).get("commit"), prod_total=pr and pr["total_cpu_s"],
                   prod_gem5=pr and pr["gem5_cpu_s"], prod_hit=pr and pr["hit"], prof_iiw=p.get("issued_in_window"),
                   time1_total=t1.get(k, {}).get("total_cpu_s"), time1_gem5=t1.get(k, {}).get("gem5_cpu_s"),
                   time1_hit=t1.get(k, {}).get("hit"), **{f"c_{x}": c[x] for x in c})
        fr = fast.get(k)
        if fr:
            row.update(fast_cpu=fr["cpu_s"], orig_inproc_cpu=fr.get("orig_cpu_s"), identical=fr.get("identical"),
                       fast_iiw=fr.get("issued_in_window"))
        per.append(row)
    if not per:
        continue
    m = lambda key, rs=per: round(st.mean(r[key] for r in rs if r.get(key) is not None), 3) \
        if any(r.get(key) is not None for r in rs) else None
    summ = dict(n=len(per), prod_total=m("prod_total"), prod_gem5=m("prod_gem5"), time1_total=m("time1_total"),
                time1_gem5=m("time1_gem5"), trace_lines=m("trace_lines"), trace_commit=m("trace_commit"),
                fast_cpu=m("fast_cpu"), orig_inproc_cpu=m("orig_inproc_cpu"),
                identical=sum(1 for r in per if r.get("identical")), n_fast=sum(1 for r in per if "fast_cpu" in r),
                verdict_match_prod=sum(1 for r in per if r.get("prod_hit") is not None and
                                       bool(r.get("prof_iiw")) == bool(r["prod_hit"])),
                verdict_match_time1=sum(1 for r in per if r.get("time1_hit") is not None and
                                        bool(r.get("prof_iiw")) == bool(r["time1_hit"])),
                fast_match_time1=sum(1 for r in per if r.get("time1_hit") is not None and "fast_iiw" in r and
                                     bool(r.get("fast_iiw")) == bool(r["time1_hit"])))
    for x in CATS:
        summ[x] = m(f"c_{x}")
    # idle estimate: scale each test's categories by TIME-1 total / this run's production total (same test)
    sc = [r for r in per if r.get("prod_total") and r.get("time1_total") and r.get("c_harness") is not None]
    if sc:
        summ["load_factor"] = round(st.mean(r["prod_total"] for r in sc) / st.mean(r["time1_total"] for r in sc), 3)
        for x in CATS:
            summ[f"{x}_idle_est"] = round(st.mean(r[f"c_{x}"] * r["time1_total"] / r["prod_total"] for r in sc), 3)
        if any("fast_cpu" in r and r.get("orig_inproc_cpu") for r in sc):
            ff = [r for r in sc if "fast_cpu" in r and r.get("orig_inproc_cpu")]
            summ["fast_idle_est"] = round(st.mean(r["fast_cpu"] / r["orig_inproc_cpu"] *
                                                  (r["time1_total"] - r["c_harness"] * r["time1_total"] / r["prod_total"])
                                                  for r in ff), 3)
    by_cs = {}
    for r in per:
        by_cs.setdefault(r["cache_setup"], []).append(r)
    summ["by_cache_setup"] = {cs: dict(n=len(rs), **{x: m(f"c_{x}", rs) for x in CATS},
                                       prod_total=m("prod_total", rs), trace_lines=m("trace_lines", rs),
                                       fast_cpu=m("fast_cpu", rs), orig_inproc_cpu=m("orig_inproc_cpu", rs))
                              for cs, rs in sorted(by_cs.items())}
    out[R] = dict(summary=summ, tests=per)
for f in ("startup.json",):
    p = B / "prof_T1g" / f
    if p.exists():
        out["startup"] = json.loads(p.read_text())
out["micro"] = {R: json.loads((B / f"micro_{R}" / "micro.json").read_text())
                for R in ("T1g", "T2g", "T3g") if (B / f"micro_{R}" / "micro.json").exists()}
print(json.dumps(out, indent=1))

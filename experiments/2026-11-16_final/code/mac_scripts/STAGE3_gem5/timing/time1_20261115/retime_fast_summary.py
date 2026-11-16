#!/usr/bin/env python3
"""retime_fast_summary.py (agent fastpath, 2026-11-16): TC-4 summary of retime_fast.sh.

Per row (T1g/T2g/T3g), from <root>/simspect/<row>_p<P>_prod2/ (production path, rerun now), <row>_p<P>_fast/ (fast path,
right after it) and <row>_p<P>/ (TIME-1, 2026-11-15):
  - mean CPU-s per test (total_cpu_s = whole per-test tree; for the fast path plus the workers' one-time startup CPU from
    fastpath_workers.jsonl spread over the tests), gem5-only CPU, non-gem5 CPU, per cache setup;
  - speedup prod2 / fast, and prod2 vs TIME-1 (is the node as idle as TIME-1's?);
  - verdict check: for every (mode, stem), the fast row must equal the prod2 row on the result fields (status, hit,
    kind, terms_fired, error, cache_setup, timing_point, stall_points, n_gem5, gem5_rc, pipeline_rc), and for hits the
    raw checker record (raw/<mode>/<stem>.json, minus `workdir`) must be identical. Rows where the rerun differs from
    TIME-1 are counted separately (code or environment drift since 2026-11-15, not a fast-path difference).
  - exec_path counts of the fast rows (all should be "fast").
Exit 1 if any fast-vs-rerun row or record differs or a run is incomplete.
    python3 retime_fast_summary.py /tests/timing_20261115 [--rows "T1g T2g T3g"] [--parallel 16] --json f --md f
"""
import argparse, collections, json, os, re, statistics as st, sys

FIELDS = ("status", "hit", "kind", "terms_fired", "error", "cache_setup", "timing_point", "stall_points", "n_gem5",
          "gem5_rc", "pipeline_rc")
_TMP_RE = re.compile(r"((?:gem5_[A-Za-z0-9_.\-]+?_)|simspect_gem5_|fw_|tmp)[a-z0-9_]{8}(?=[/'\"\s:]|$)")


_BT_RE = re.compile(r"\)\[0x[0-9a-f]+\]")   # glibc backtrace frame addresses of a crashing gem5 (ASLR)


def mask(o):
    if isinstance(o, str):
        return _BT_RE.sub(")[0x<aslr>]", _TMP_RE.sub(r"\1<tmp>", o))
    if isinstance(o, dict):
        return {k: mask(v) for k, v in o.items() if k != "workdir"}
    if isinstance(o, list):
        return [mask(v) for v in o]
    return o


def rows(d):
    p = os.path.join(d, "results.jsonl")
    if not os.path.exists(p):
        return {}
    out = {}
    for l in open(p):
        r = json.loads(l)
        out[(r["mode"], r["stem"])] = r
    return out


def cpu(rs, startup=0.0):
    ok = [r for r in rs.values() if r.get("total_cpu_s") is not None]
    if not ok:
        return None
    by = collections.defaultdict(list)
    for r in ok:
        by[r.get("cache_setup")].append(r["total_cpu_s"])
    tot = st.mean(r["total_cpu_s"] for r in ok)
    return dict(n=len(ok), total_mean=round(tot + startup / len(ok), 4), total_mean_excl_startup=round(tot, 4),
                startup_cpu_s_total=round(startup, 3), gem5_mean=round(st.mean(r["gem5_cpu_s"] for r in ok), 4),
                nongem5_mean=round(st.mean(r["total_cpu_s"] - r["gem5_cpu_s"] for r in ok), 4),
                by_setup={str(k): [len(v), round(st.mean(v), 3)] for k, v in sorted(by.items(), key=lambda x: str(x[0]))})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--rows", default="T1g T2g T3g")
    ap.add_argument("--parallel", type=int, default=16)
    ap.add_argument("--json", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()
    S, bad = {}, 0
    md = ["| row | TIME-1 CPU-s/test | production rerun | fast path | speedup | rows fast = rerun | raw hit records fast = rerun | fast exec_path |",
          "|---|---|---|---|---|---|---|---|"]
    for row in a.rows.split():
        base = f"{a.root}/simspect/{row}_p{a.parallel}"
        t1, pr, fa = rows(base), rows(base + "_prod2"), rows(base + "_fast")
        startup = 0.0
        wj = base + "_fast/fastpath_workers.jsonl"
        if os.path.exists(wj):
            startup = sum(json.loads(l).get("startup_cpu_s", 0) for l in open(wj) if '"spawn"' in l)
        c = dict(time1=cpu(t1), prod2=cpu(pr), fast=cpu(fa, startup))
        keys = sorted(set(pr) | set(fa))
        vd, vt, rd, nraw, diffs = 0, 0, 0, 0, []
        for k in keys:
            f, p_, t = fa.get(k), pr.get(k), t1.get(k)
            if f is None or p_ is None:
                vd += 1; diffs.append(dict(pair=k, why="missing in fast" if f is None else "missing in prod2"))
                continue
            ff, pp = mask({x: f.get(x) for x in FIELDS}), mask({x: p_.get(x) for x in FIELDS})
            if ff != pp:
                vd += 1; diffs.append(dict(pair=k, fast=ff, prod2=pp))
            if t is None or mask({x: t.get(x) for x in FIELDS}) != pp:
                vt += 1   # drift of the rerun vs TIME-1 (code or environment changed since): reported, not a fast-path diff
            if p_.get("hit") or f.get("hit"):
                raws = []
                for d in (base + "_fast", base + "_prod2"):
                    q = f"{d}/raw/{k[0]}/{k[1]}.json"
                    raws.append(mask(json.load(open(q))) if os.path.exists(q) else None)
                nraw += 1
                if not (raws[0] is not None and raws[0] == raws[1]):
                    rd += 1; diffs.append(dict(pair=k, why="raw record differs or missing"))
        paths = dict(collections.Counter(r.get("exec_path", "?") for r in fa.values()))
        sp = (round(c["prod2"]["total_mean"] / c["fast"]["total_mean"], 3) if c["prod2"] and c["fast"] else None)
        S[row] = dict(cpu=c, speedup_prod2_over_fast=sp, pairs=len(keys), verdict_diffs_fast_vs_prod2=vd,
                      rows_prod2_differing_from_time1=vt, raw_hit_records=nraw, raw_diffs_fast_vs_prod2=rd,
                      fast_exec_paths=paths, diffs=diffs[:50])
        bad += vd + rd + (0 if len(keys) >= 1000 else 1)
        g = lambda x: (x or {}).get("total_mean")
        md.append(f"| {row} | {g(c['time1'])} | {g(c['prod2'])} | {g(c['fast'])} | {sp}x | {len(keys) - vd}/{len(keys)} "
                  f"(rerun vs TIME-1 differ on {vt}) | {nraw - rd}/{nraw} | {paths} |")
    md.append("")
    md.append("CPU-s per test = mean total_cpu_s (whole per-test tree); fast path includes its workers' one-time startup "
              "spread over the tests. Per cache setup and gem5-only numbers in summary.json.")
    json.dump(S, open(a.json, "w"), indent=1, default=str)
    open(a.md, "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

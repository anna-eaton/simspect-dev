#!/usr/bin/env python3
"""fast_worker.py (agent testcost, 2026-11-16): PROTOTYPE of a verdict-preserving fast path for one
SimSpect test. Not wired into production; read-only on the production code.

Same per-test work as `pipeline.py gem5` on one test (sweep grid point + stall injection from
pipeline._enumerate_grid_for_corpus / _materialise_grid_run, copy into a temp dir, then
gem5_common.process_one with check_footprint.check_footprint): same binary build, cache setup,
branch forces, stalls, gem5 command line and checker code. Three harness-only changes:

  1. persistent worker: one Python process runs many tests (no per-test `python3 pipeline.py` +
     `python3 check_footprint.py` interpreter start and imports);
  2. resolve-hook detection cached: gem5_common.binary_has_resolve_hooks reads the whole gem5 binary
     (1.1 GB for the AMuLeT InvisiSpec/CleanupSpec builds) once per checker process; here the answer
     is memoized per (realpath, size, mtime_ns), and computed with mmap.find (same bytes test);
  3. one trace read: gem5_common._trace_lines is served from a per-trace cache of the unglued lines,
     split into the line classes each parser can match (every regex/prefix of that parser requires
     the class's literal substring, so a parser never sees a line it could have used); the
     production parser bodies run unchanged on their class.

With --compare-orig every test is also run through the unpatched production functions in the same
process (a second gem5 run) and the two result dicts are compared key by key (minus `workdir`).

    nice -n 19 python3 fast_worker.py --code-root <code> --config <cfg.jsonc> --testset-model <ts/model> \
        --sample <tsv> --n 20 --out <dir> [--compare-orig]

Outputs in --out: fast.jsonl (per test: cpu_s self+children, verdict fields, diff vs orig),
fast.log (start/end, every test, errors with traceback).
"""
import argparse, json, mmap, os, resource, shutil, sys, tempfile, time, traceback
from pathlib import Path

LOG = None


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOG:
        with open(LOG, "a") as f:
            f.write(line + "\n")


def ru():
    s = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime, c.ru_utime + c.ru_stime, time.monotonic()


# ── fast path patches ─────────────────────────────────────────────────────────

_CAT = {"v": None}
_TRACE = {}
_HOOKS = {}

# line class -> literal substrings, one of which every pattern of the parsers in that class requires
LSQ_KEYS = ("system.cpu.iew.lsq", "system.cpu.dcache", "Initiating Translation inst [sn:")
COMMIT_INST_KEY = "Committing instruction with [sn:"      # gem5_common._COMMIT_INST_RE
COMMIT_SQUASH_KEY = "Squashing due to branch mispred PC:"   # gem5_common._COMMIT_SQUASH_RE


def _load_trace(gc, path):
    st = os.stat(path)
    key = (str(path), st.st_size, st.st_mtime_ns)
    if _TRACE.get("key") == key:
        return _TRACE["cats"]
    cats = dict(all=[], o3pv=[], simspect=[], lsq=[], commit_inst=[], commit_squash=[])
    sp = gc.SIMSPECT_PREFIX
    with open(path) as f:
        for raw in f:
            line = gc._unglue(raw)
            cats["all"].append(line)
            if line.startswith("O3PipeView:"):
                (cats["simspect"] if line.startswith(sp) else cats["o3pv"]).append(line)
                continue
            if "system.cpu.commit" in line:
                if COMMIT_INST_KEY in line:
                    cats["commit_inst"].append(line)
                if COMMIT_SQUASH_KEY in line:
                    cats["commit_squash"].append(line)
            if any(k in line for k in LSQ_KEYS):
                cats["lsq"].append(line)
    _TRACE.clear()
    _TRACE.update(key=key, cats=cats)
    return cats


def apply_fastpath(gc, cf):
    orig = {n: getattr(gc, n) for n in ("_trace_lines", "binary_has_resolve_hooks", "parse_pipeview",
                                        "parse_pipeview_by_seq", "parse_simspect_events", "parse_lsq",
                                        "parse_commit_ticks", "parse_commit_squashes")}
    orig_cf = {n: getattr(cf, n) for n in ("parse_pipeview", "parse_pipeview_by_seq", "parse_simspect_events")}

    def trace_lines(trace_path):
        return iter(_load_trace(gc, trace_path)[_CAT["v"] or "all"])

    def with_cat(fn, cat):
        def w(trace_path, *a, **kw):
            prev = _CAT["v"]
            _CAT["v"] = cat
            try:
                return fn(trace_path, *a, **kw)
            finally:
                _CAT["v"] = prev
        return w

    def hooks(gem5_bin):
        p = os.path.realpath(str(gem5_bin))
        try:
            st = os.stat(p)
        except OSError:
            return False
        key = (p, st.st_size, st.st_mtime_ns)
        if key not in _HOOKS:
            with open(p, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                _HOOKS[key] = m.find(gc._FORCE_MARKER) != -1
        return _HOOKS[key]

    gc._trace_lines = trace_lines
    gc.binary_has_resolve_hooks = hooks
    for n, cat in (("parse_pipeview", "o3pv"), ("parse_pipeview_by_seq", "o3pv"),
                   ("parse_simspect_events", "simspect"), ("parse_lsq", "lsq"),
                   ("parse_commit_ticks", "commit_inst"), ("parse_commit_squashes", "commit_squash")):
        setattr(gc, n, with_cat(orig[n], cat))
    for n in orig_cf:
        setattr(cf, n, getattr(gc, n))

    def restore():
        for n, f in orig.items():
            setattr(gc, n, f)
        for n, f in orig_cf.items():
            setattr(cf, n, f)
        _TRACE.clear()
    return restore


def _strip(r):
    return {k: v for k, v in r.items() if k != "workdir"}


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--testset-model", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--compare-orig", action="store_true")
    a = ap.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    LOG = out / "fast.log"
    sample = Path(a.sample).resolve(); cfgp = Path(a.config).resolve(); tsm = Path(a.testset_model).resolve()
    code = Path(a.code_root).resolve()
    t_import0 = ru()
    sys.path.insert(0, str(code)); os.chdir(code)
    import pipeline as pl
    cfg = pl.load_config(cfgp)
    env = pl._build_gem5_env(cfg["gem5"], cfg.get("speculation", {}))
    for k, v in env.items():
        if k.startswith("SIMSPECT_"):
            os.environ[k] = v
    sys.path.insert(0, str(code / "STAGE3_gem5"))
    import gem5_common as gc
    import check_footprint as cf
    cf._CRIT = cf.load_criterion(os.environ["SIMSPECT_CRITERION"])
    cf._ACTOR_OVERRIDE = os.environ.get("SIMSPECT_CRITERION_ACTOR")
    gc._scheme = int(cfg["gem5"].get("scheme", 2))
    sweep = cfg.get("sweep", {})
    unresolved_stall = int(sweep.get("unresolved_stall_cycles", 0))
    t_import1 = ru()
    log(f"START config={cfgp} n={a.n} compare_orig={a.compare_orig} pid={os.getpid()} nice={os.nice(0)} "
        f"loadavg={os.getloadavg()} import_cpu={round(t_import1[0]-t_import0[0], 3)}")
    pairs = [l.split("\t")[:2] for l in sample.read_text().splitlines() if l.strip()][:a.n]
    restore = apply_fastpath(gc, cf)

    def one(mode, stem):
        tmp = Path(tempfile.mkdtemp(prefix="fw_", dir=str(out)))
        try:
            s_path = tsm / mode / "asm" / f"{stem}.s"
            per_grid, manifest, _ = pl._enumerate_grid_for_corpus([s_path], tsm / mode / "ann", sweep)
            files = pl._materialise_grid_run(per_grid[0], tmp / "variant", unresolved_stall)
            chk = tmp / "chk"; chk.mkdir()
            shutil.copy(files[0], chk / files[0].name)
            shutil.copy(tmp / "variant" / f"{stem}.ann.json", chk / f"{stem}.ann.json")
            return gc.process_one(chk / f"{stem}.s", chk / f"{stem}.ann.json", cf.check_footprint, keep_tmp=False)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            _TRACE.clear()

    fo = out / "fast.jsonl"
    for i, (mode, stem) in enumerate(pairs):
        row = dict(i=i, mode=mode, stem=stem)
        try:
            t0 = ru()
            r = one(mode, stem)
            t1 = ru()
            row.update(cpu_s=round(t1[0] - t0[0] + t1[1] - t0[1], 4), self_s=round(t1[0] - t0[0], 4),
                       children_s=round(t1[1] - t0[1], 4), wall_s=round(t1[2] - t0[2], 4),
                       status=r.get("status"), issued_in_window=r.get("issued_in_window"), leak=r.get("leak"),
                       terms_fired=r.get("terms_fired"), cache_setup=r.get("cache_setup"),
                       error=(r.get("error") or "")[:200] or None)
            if a.compare_orig:
                restore()
                gc._force_support.clear()   # production pays the binary scan once per checker process = per test
                t2 = ru()
                ro = one(mode, stem)
                t3 = ru()
                restore = apply_fastpath(gc, cf)
                fa, ob = _strip(r), _strip(ro)
                diff = sorted(k for k in set(fa) | set(ob) if fa.get(k) != ob.get(k))
                row.update(orig_cpu_s=round(t3[0] - t2[0] + t3[1] - t2[1], 4), identical=not diff, diff_keys=diff,
                           orig_issued_in_window=ro.get("issued_in_window"), orig_status=ro.get("status"))
                if diff:
                    (out / f"diff_{i:03d}_{stem}.json").write_text(json.dumps(
                        {k: [fa.get(k), ob.get(k)] for k in diff}, default=str)[:200000])
        except Exception:
            row["exc"] = traceback.format_exc()[-1500:]
            log(f"ERROR {i} {mode}/{stem}:\n{row['exc']}")
        with open(fo, "a") as f:
            f.write(json.dumps(row, default=str) + "\n")
        log(f"test {i} {mode}/{stem} cs={row.get('cache_setup')} iiw={row.get('issued_in_window')} "
            f"cpu={row.get('cpu_s')} orig_cpu={row.get('orig_cpu_s')} identical={row.get('identical')} "
            f"diff={row.get('diff_keys')}")
    log(f"END loadavg={os.getloadavg()}")


if __name__ == "__main__":
    main()

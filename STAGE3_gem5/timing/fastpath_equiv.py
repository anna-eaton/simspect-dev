#!/usr/bin/env python3
"""fastpath_equiv.py (agent fastpath, 2026-11-16): proves the opt-in fast path (gem5.fast_path: true) gives the
SAME per-test records as the production path. Exit status 0 = every compared record identical, 1 = any difference
or harness error, 2 = usage error. Runbook: wiki/state/COMMANDS.md "Fast path (opt-in, 2026-11-16)".

Three checks, each on the same tests and the same run_config (only gem5.fast_path differs):

  driver   the per-test drivers (timing_driver.run_one = firstdet_stream / TIME-1): options 1+2+3.
           Per test, A/B interleaved (production then fast, or --ab prod,prod for an A/A determinism control):
           compares the FULL checker record(s) (every key, minus the temp `workdir` path), the aggregated
           window-results record, the sweep sidecar (stall points), and the results.jsonl row minus timing
           fields. Both runs keep timing_driver's normal output (results.jsonl, raw/ + traces/ for hits), so
           `bugs/classify.py footprint --run <out>/prod` and `.../fast` can be compared afterwards.
             python3 fastpath_equiv.py driver --code-root <code> --config <cfg.jsonc> --model <testset model> \
                 --out <dir> [--sample 300 --seed 20261116] [--pairs-file known.tsv] [--parallel 8] [--ab prod,fast]
  batch    the pipeline.py gem5 / testrun.py path (options 1+2, checker threads): one `pipeline.py gem5` call over
           all tests with fast_path absent, one with true, same jobs; compares every raw checker record per
           (grid point, name), window-results.json and the sweep sidecars.
             python3 fastpath_equiv.py batch --code-root <code> --config <cfg.jsonc> --model <m> --out <dir> \
                 [--sample 300 --seed S] [--pairs-file f] [--jobs 8]
  errcases builds a small synthetic error testset from real tests (assembler failure, ann without xmit.kind ->
           pipeline crash, ann without the transmitter address -> "no xmit x86 PC", an architectural load from an
           unmapped address -> gem5 panic) plus a config copy pointing at it (only paths.testset_dir changes) and a
           pairs file; then run `driver` on it. Timeouts: run `driver` with SIMSPECT_GEM5_TIMEOUT_S=0 in the env.
             python3 fastpath_equiv.py errcases --config <cfg.jsonc> --code-root <code> --model <m> --out <dir> [--n 2]
  stored   compares a `driver` check's prod/ and fast/ results with an EARLIER campaign of the same config (e.g. one run
           with the code before the fast path existed): result fields of every shared (mode, stem) row and the full raw
           record of every shared hit. Shows the default path is unchanged, not just equal to the fast path.
             python3 fastpath_equiv.py stored --run <driver --out dir> --stored <earlier run dir> --out <dir> \
                 --code-roots <this code root>,<the earlier run's code root>
  parsers  offline, no gem5: every wrapped trace parser, production vs routed, on stored traces (plain or .gz)
           plus synthetic edge cases (missing file, empty file, bad UTF-8, glued lines, malformed simspect line);
           exceptions are compared by type and message.
             python3 fastpath_equiv.py parsers --code-root <code> --traces '<glob>' [--max 2000] --out <dir>

Normalizations before comparing (each needed because it differs between two PRODUCTION runs too, shown by the A/A
control): random tempfile directory names; each side's own output dir; glibc-backtrace frame addresses in a crashing
gem5's stderr (ASLR). Nothing else is masked or skipped except the timing fields listed in VOLATILE_ROW.
Inputs: --pairs-file is a tsv `mode<TAB>stem` (extra columns ignored; lines starting with # skipped) of tests that
must be included (known hits, error cases); --sample N adds N seeded random pairs of the testset.
Outputs (--out): equiv.log (start/end, every test, every difference, every error with traceback),
equiv_report.json (summary + per-test rows incl. CPU-s of both paths), diffs/<mode>__<stem>.json per differing test.
"""
from __future__ import annotations

import argparse
import copy
import glob
import gzip
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
_LOCK = threading.Lock()
LOGF = [None]

# row fields that measure time / CPU / where the run happened, not what it computed
VOLATILE_ROW = {"t_start", "wall_s", "total_cpu_s", "gem5_cpu_s", "gem5_wall_s", "trace", "exec_path",
                "fastpath_worker", "fastpath_events", "fastpath_fallback"}
VOLATILE_REC = {"workdir"}


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    with _LOCK:
        print(line, flush=True)
        if LOGF[0]:
            with open(LOGF[0], "a") as f:
                f.write(line + "\n")


def diff_obj(a, b, path="", out=None, limit=200):
    """Field-by-field differences (path, a, b), recursing into dicts and lists."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append((f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>")))
            else:
                diff_obj(a[k], b[k], f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((f"{path}[len]", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff_obj(x, y, f"{path}[{i}]", out, limit)
    elif a != b or type(a) is not type(b):
        out.append((path, a, b))
    return out


def _strip(rec: dict, drop) -> dict:
    return {k: v for k, v in rec.items() if k not in drop}


# tempfile.mkdtemp names (prefix + 8 random chars) differ between ANY two runs, production vs production too;
# an error string can embed one (e.g. a missing-trace path). Masked in string values before comparing.
_TMP_RE = re.compile(r"((?:gem5_[A-Za-z0-9_.\-]+?_)|simspect_gem5_|fw_|tmp)[a-z0-9_]{8}(?=[/'\"\s:]|$)")


# A crashing gem5 prints a glibc backtrace whose frames end in absolute addresses, "(PyEval_EvalCode+0x1d)[0x7a50b369f9fd]";
# ASLR moves them in every process, so two PRODUCTION runs of one panicking test differ there (A/A control, 2026-11-16).
_BT_RE = re.compile(r"\)\[0x[0-9a-f]+\]")


def mask(obj):
    if isinstance(obj, str):
        return _BT_RE.sub(")[0x<aslr>]", _TMP_RE.sub(r"\1<tmp>", obj))
    if isinstance(obj, dict):
        return {k: mask(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask(v) for v in obj]
    return obj


def load_pairs(testset_model: Path, modes, sample: int, seed: int, pairs_file):
    pairs = []
    if pairs_file:
        for line in Path(pairs_file).read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            f = [x.strip() for x in line.split("\t")]
            if len(f) >= 3 and f[0].isdigit():
                f = f[1:]
            if len(f) >= 2 and (f[0], f[1]) not in pairs:
                pairs.append((f[0], f[1]))
    if sample:
        allp = []
        for m in modes:
            a = {p.stem for p in (testset_model / m / "asm").glob("inst-*.s")}
            n = {p.name[:-len(".ann.json")] for p in (testset_model / m / "ann").glob("inst-*.ann.json")}
            allp += [(m, s) for s in sorted(a & n)]
        allp.sort()
        rng = random.Random(seed)
        for p in rng.sample(allp, min(sample, len(allp))):
            if p not in pairs:
                pairs.append(p)
    return pairs


# ═════════════════════════════ driver check ══════════════════════════════════

def _read_wd(wd: Path, mode: str, stem: str) -> dict:
    """Everything a run_one left in its (kept) work dir that carries a result."""
    rs = wd / "res" / "out" / mode
    out = dict(raw=[], window=None, sidecar=None, gem5_rc=None)
    files = sorted((rs / "sweep" / "raw_results").glob("*.json")) + sorted(rs.glob("batch_*_results.json"))
    for rf in files:
        m = re.search(r"_g(?:rid)?(\d{4})_", rf.name)
        try:
            for r in json.loads(rf.read_text()):
                out["raw"].append(dict(grid=int(m.group(1)) if m else None, rec=_strip(r, VOLATILE_REC)))
        except Exception as e:
            out["raw"].append(dict(grid=None, rec={"_unreadable": f"{rf.name}: {e}"}))
    out["raw"].sort(key=lambda x: (x["grid"] if x["grid"] is not None else -1, x["rec"].get("name", "")))
    try:
        out["window"] = json.loads((rs / "window-results.json").read_text())
    except Exception as e:
        out["window"] = f"<missing: {type(e).__name__}>"
    try:
        out["sidecar"] = json.loads((rs / "sweep" / f"{stem}_sweep.json").read_text())
    except Exception:
        out["sidecar"] = None
    return out


def cmd_driver(a) -> int:
    code = Path(a.code_root).resolve()
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(code))
    import timing_driver as td
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOGF[0] = out / "equiv.log"
    cfgp = Path(a.config) if Path(a.config).is_absolute() else code / a.config
    cfg = td.load_jsonc(cfgp)
    tdir = cfg["paths"]["testset_dir"]
    testset_model = (Path(tdir) if Path(tdir).is_absolute() else code / tdir) / a.model
    modes = cfg["speculation"]["branch_modes"]
    sides = a.ab.split(",")
    if len(sides) != 2 or any(s not in ("prod", "fast") for s in sides):
        log("ERROR --ab must be prod,fast | fast,prod | prod,prod | fast,fast")
        return 2
    cfgs = {}
    for s in set(sides):
        c = copy.deepcopy(cfg)
        c["gem5"].pop("fast_path", None)
        if s == "fast":
            c["gem5"]["fast_path"] = True
        cfgs[s] = c
    pairs = load_pairs(testset_model, modes, a.sample, a.seed, a.pairs_file)
    log(f"START driver code_root={code} config={cfgp} model={a.model} pairs={len(pairs)} "
        f"(pairs_file={a.pairs_file}, sample={a.sample}, seed={a.seed}) ab={a.ab} parallel={a.parallel} "
        f"pid={os.getpid()} nice={os.nice(0)} loadavg={os.getloadavg()} TMPDIR={os.environ.get('TMPDIR')}")
    (out / "pairs.tsv").write_text("".join(f"{i}\t{m}\t{s}\n" for i, (m, s) in enumerate(pairs)))
    names = [f"{s}{'2' if i == 1 and sides[0] == sides[1] else ''}" for i, s in enumerate(sides)]
    for n in names:
        (out / n).mkdir(exist_ok=True)
        shutil.copy(cfgp, out / n / "run_config.jsonc")
    done = {}
    rep_f = out / "rows.jsonl"
    if rep_f.exists():   # resumable
        for l in rep_f.read_text().splitlines():
            try:
                r = json.loads(l); done[(r["mode"], r["stem"])] = r
            except Exception:
                pass

    def ns(side_out):
        return argparse.Namespace(code_root=str(code), model=a.model, keep_work=True, keep_all_traces=False)

    def one(i, mode, stem):
        res = dict(i=i, mode=mode, stem=stem)
        got = {}
        for n, s in zip(names, sides):
            o = out / n
            t0 = time.time()
            row = td.run_one(i, mode, stem, cfgs[s], ns(o), o, testset_model)
            wd = o / "work" / f"{i:06d}"
            got[n] = dict(row=row, wd=_read_wd(wd, mode, stem))
            with _LOCK:
                with open(o / "results.jsonl", "a") as f:
                    f.write(json.dumps(row) + "\n")
            res[f"{n}_cpu_s"] = row.get("total_cpu_s")
            res[f"{n}_gem5_cpu_s"] = row.get("gem5_cpu_s")
            res[f"{n}_wall_s"] = round(time.time() - t0, 3)
            res[f"{n}_exec_path"] = row.get("exec_path", "production")
            if not a.keep_work:
                shutil.rmtree(wd, ignore_errors=True)
        A, B = (got[n] for n in names)
        for n in names:   # each side's own output dir appears in some messages (e.g. stall_points_error)
            got[n] = json.loads(json.dumps(got[n], default=str).replace(str(out / n) + "/", "<out>/"))
        A, B = (got[n] for n in names)
        d = []
        d += diff_obj(mask(_strip(A["row"], VOLATILE_ROW)), mask(_strip(B["row"], VOLATILE_ROW)), "row")
        d += diff_obj(mask(A["wd"]["raw"]), mask(B["wd"]["raw"]), "raw")
        d += diff_obj(mask(A["wd"]["window"]), mask(B["wd"]["window"]), "window")
        d += diff_obj(mask(A["wd"]["sidecar"]), mask(B["wd"]["sidecar"]), "sidecar")
        res.update(identical=not d, n_diff=len(d), status=A["row"].get("status"), hit=A["row"].get("hit"),
                   cache_setup=A["row"].get("cache_setup"), kind=A["row"].get("kind"),
                   n_records=len(A["wd"]["raw"]), error=A["row"].get("error"))
        if d:
            (out / "diffs").mkdir(exist_ok=True)
            (out / "diffs" / f"{mode}__{stem}.json").write_text(json.dumps(
                [dict(path=p, a=x, b=y) for p, x, y in d], default=str, indent=1)[:500000])
        return res

    todo = [(i, m, s) for i, (m, s) in enumerate(pairs) if (m, s) not in done]
    log(f"{len(done)} already compared (resume), {len(todo)} to run")
    rows = list(done.values())
    nerr = 0
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        futs = {ex.submit(one, i, m, s): (i, m, s) for i, m, s in todo}
        for f in as_completed(futs):
            i, m, s = futs[f]
            try:
                r = f.result()
            except Exception:
                nerr += 1
                log(f"ERROR harness {i} {m}/{s}:\n{traceback.format_exc()}")
                continue
            rows.append(r)
            with _LOCK:
                with open(rep_f, "a") as fo:
                    fo.write(json.dumps(r) + "\n")
            log(f"test {i} {m}/{s} identical={r['identical']} n_diff={r['n_diff']} status={r['status']} "
                f"hit={r['hit']} setup={r['cache_setup']} records={r['n_records']} "
                + " ".join(f"{n}_cpu={r.get(n + '_cpu_s')} {n}_path={r.get(n + '_exec_path')}" for n in names))
    return _report(out, rows, names, nerr, "driver")


def _report(out: Path, rows, names, nerr, kind) -> int:
    ident = sum(1 for r in rows if r.get("identical"))
    by = {}
    for r in rows:
        k = (r.get("cache_setup") or "?")
        by.setdefault(k, []).append(r)

    def mean(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        return round(sum(xs) / len(xs), 4) if xs else None
    cpu = {n: mean(r.get(f"{n}_cpu_s") for r in rows) for n in names}
    per_setup = {k: dict(n=len(v), **{f"{n}_cpu_mean": mean(r.get(f"{n}_cpu_s") for r in v) for n in names})
                 for k, v in sorted(by.items())}
    paths = {}
    for r in rows:
        p = r.get(f"{names[-1]}_exec_path")
        paths[p] = paths.get(p, 0) + 1
    summ = dict(kind=kind, compared=len(rows), identical=ident, different=len(rows) - ident, harness_errors=nerr,
                hits=sum(1 for r in rows if r.get("hit")),
                statuses={s: sum(1 for r in rows if r.get("status") == s)
                          for s in sorted({str(r.get("status")) for r in rows})},
                cpu_mean=cpu, cpu_ratio=(round(cpu[names[1]] / cpu[names[0]], 4)
                                         if cpu.get(names[0]) and cpu.get(names[1]) else None),
                per_cache_setup=per_setup, exec_paths_side_b=paths,
                differing=[f"{r['mode']}/{r['stem']}" for r in rows if not r.get("identical")][:200])
    (out / "equiv_report.json").write_text(json.dumps(dict(summary=summ, rows=sorted(rows, key=lambda r: r["i"])),
                                                      indent=1, default=str))
    log(f"END {kind}: {ident}/{len(rows)} identical, {len(rows) - ident} different, harness errors {nerr}; "
        f"hits {summ['hits']}; statuses {summ['statuses']}; cpu mean {cpu} ratio {summ['cpu_ratio']}; "
        f"side-B paths {paths}; report {out / 'equiv_report.json'}")
    return 0 if (ident == len(rows) and nerr == 0 and rows) else 1


# ═════════════════════════════ batch check ═══════════════════════════════════

def _batch_records(rs: Path):
    recs = {}
    files = sorted((rs / "sweep" / "raw_results").glob("*.json")) + sorted(rs.glob("batch_*_results.json"))
    for rf in files:
        m = re.search(r"_g(?:rid)?(\d{4})_", rf.name)
        g = int(m.group(1)) if m else None
        for r in json.loads(rf.read_text()):
            recs[(g, r["name"])] = _strip(r, VOLATILE_REC)
    return recs


def cmd_batch(a) -> int:
    code = Path(a.code_root).resolve()
    sys.path.insert(0, str(HERE))
    import timing_driver as td
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOGF[0] = out / "equiv.log"
    cfgp = Path(a.config) if Path(a.config).is_absolute() else code / a.config
    cfg = td.load_jsonc(cfgp)
    tdir = cfg["paths"]["testset_dir"]
    testset_model = (Path(tdir) if Path(tdir).is_absolute() else code / tdir) / a.model
    modes = cfg["speculation"]["branch_modes"]
    pairs = load_pairs(testset_model, modes, a.sample, a.seed, a.pairs_file)
    log(f"START batch code_root={code} config={cfgp} model={a.model} pairs={len(pairs)} jobs={a.jobs} "
        f"pid={os.getpid()} nice={os.nice(0)} loadavg={os.getloadavg()}")
    stage = out / "stage"
    shutil.rmtree(stage, ignore_errors=True)
    for m, s in pairs:
        for sub, suf in (("asm", ".s"), ("ann", ".ann.json")):
            d = stage / a.model / m / sub
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{s}{suf}").symlink_to(testset_model / m / sub / f"{s}{suf}")
    used_modes = sorted({m for m, _ in pairs})
    res = {}
    for side in ("prod", "fast"):
        c = copy.deepcopy(cfg)
        c["gem5"].pop("fast_path", None)
        if side == "fast":
            c["gem5"]["fast_path"] = True
        c["gem5"]["jobs"] = a.jobs
        c["paths"]["testset_dir"] = str(stage)
        c["paths"]["results_dir"] = str(out / "res")
        c["paths"]["results_name"] = side
        c["speculation"]["branch_modes"] = used_modes
        cp = out / f"cfg_{side}.json"
        cp.write_text(json.dumps(c, indent=1))
        shutil.rmtree(out / "res" / side, ignore_errors=True)
        t0 = time.time()
        with open(out / f"pipeline_{side}.log", "w") as lf:
            p = subprocess.Popen([sys.executable, "pipeline.py", "gem5", "--model", a.model, "--config", str(cp),
                                  "--force"], cwd=str(code), stdout=lf, stderr=subprocess.STDOUT)
            _, sts, ru = os.wait4(p.pid, 0)
        res[side] = dict(cpu_s=round(ru.ru_utime + ru.ru_stime, 2), wall_s=round(time.time() - t0, 1),
                         rc=os.WEXITSTATUS(sts) if os.WIFEXITED(sts) else -1)
        log(f"{side}: pipeline gem5 rc={res[side]['rc']} cpu_s={res[side]['cpu_s']} wall_s={res[side]['wall_s']}")
    rows, nerr = [], 0
    for m in used_modes:
        A = _batch_records(out / "res" / "prod" / m)
        B = _batch_records(out / "res" / "fast" / m)
        stems = sorted({k[1] for k in A} | {k[1] for k in B})
        for st in stems:
            ka = sorted(k for k in A if k[1] == st)
            kb = sorted(k for k in B if k[1] == st)
            d = []
            if ka != kb:
                d.append(("grid points", ka, kb))
            for k in sorted(set(ka) & set(kb), key=str):
                d += diff_obj(mask(A[k]), mask(B[k]), f"raw[g{k[0]}]")
            for f in (f"sweep/{st}_sweep.json",):
                pa, pb = out / "res" / "prod" / m / f, out / "res" / "fast" / m / f
                if pa.exists() or pb.exists():
                    try:
                        d += diff_obj(json.loads(pa.read_text()), json.loads(pb.read_text()), "sidecar")
                    except Exception as e:
                        d.append(("sidecar", str(e), ""))
            r0 = A[ka[0]] if ka else {}
            rows.append(dict(i=len(rows), mode=m, stem=st, identical=not d, n_diff=len(d), status=r0.get("status"),
                             hit=bool(r0.get("issued_in_window")), cache_setup=r0.get("cache_setup"),
                             kind=r0.get("xmit_kind"), n_records=len(ka)))
            if d:
                (out / "diffs").mkdir(exist_ok=True)
                (out / "diffs" / f"{m}__{st}.json").write_text(json.dumps(
                    [dict(path=p, a=x, b=y) for p, x, y in d], default=str, indent=1)[:500000])
                log(f"DIFF {m}/{st}: {d[:3]}")
        for f in ("window-results.json",):
            try:
                wa = sorted(json.loads((out / "res" / "prod" / m / f).read_text()), key=lambda r: r["name"])
                wb = sorted(json.loads((out / "res" / "fast" / m / f).read_text()), key=lambda r: r["name"])
                dd = diff_obj(wa, wb, f"{m}/{f}")
                if dd:
                    nerr += 1
                    log(f"DIFF {m}/{f}: {dd[:5]}")
            except Exception:
                nerr += 1
                log(f"ERROR reading {m}/{f}:\n{traceback.format_exc()}")
    for side in ("prod", "fast"):
        if res[side]["rc"] != 0:
            nerr += 1
    want = len(pairs)
    if len(rows) != want:
        log(f"ERROR compared {len(rows)} stems, expected {want}")
        nerr += 1
    log(f"batch CPU (whole pipeline call): prod {res['prod']['cpu_s']} s, fast {res['fast']['cpu_s']} s "
        f"(ratio {round(res['fast']['cpu_s'] / res['prod']['cpu_s'], 4) if res['prod']['cpu_s'] else None})")
    (out / "batch_cpu.json").write_text(json.dumps(res, indent=1))
    return _report(out, rows, ["prod", "fast"], nerr, "batch")


# ═════════════════════════════ vs an earlier campaign ════════════════════════

ROW_FIELDS = ("status", "hit", "kind", "terms_fired", "error", "cache_setup", "timing_point", "stall_points", "n_gem5",
              "gem5_rc", "pipeline_rc")


def cmd_stored(a) -> int:
    run, sto = Path(a.run).resolve(), Path(a.stored).resolve()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOGF[0] = out / "equiv.log"

    def rows(d):
        r = {}
        if (d / "results.jsonl").exists():
            for l in (d / "results.jsonl").read_text().splitlines():
                try:
                    x = json.loads(l); r[(x["mode"], x["stem"])] = x
                except Exception:
                    pass
        return r
    S = rows(sto)
    roots = [r.rstrip("/") for r in (a.code_roots or "").split(",") if r.strip()]

    def cmask(o):   # the code root is part of e.g. criterion_path; two code trees differ only there
        o = mask(o)
        if isinstance(o, str):
            for r in roots:
                o = o.replace(r + "/", "<code_root>/")
            return o
        if isinstance(o, dict):
            return {k: cmask(v) for k, v in o.items()}
        if isinstance(o, list):
            return [cmask(v) for v in o]
        return o
    sides = [n for n in ("prod", "fast") if (run / n / "results.jsonl").exists()]
    log(f"START stored run={run} stored={sto} ({len(S)} stored rows) sides={sides}")
    summ, nd = {}, 0
    for n in sides:
        R = rows(run / n)
        shared = sorted(set(R) & set(S))
        rd = hd = nh = 0
        for k in shared:
            fa = cmask({f: R[k].get(f) for f in ROW_FIELDS if f in S[k] or f in R[k]})
            fb = cmask({f: S[k].get(f) for f in ROW_FIELDS if f in S[k] or f in R[k]})
            if fa != fb:
                rd += 1
                log(f"ROWDIFF {n} {k}: {diff_obj(fa, fb, 'row')[:5]}")
            pa, pb = run / n / "raw" / k[0] / f"{k[1]}.json", sto / "raw" / k[0] / f"{k[1]}.json"
            if pa.exists() and pb.exists():
                nh += 1
                d = diff_obj(cmask(_strip(json.loads(pa.read_text()), VOLATILE_REC)),
                             cmask(_strip(json.loads(pb.read_text()), VOLATILE_REC)), "raw")
                if d:
                    hd += 1
                    log(f"RAWDIFF {n} {k}: {d[:5]}")
            elif pa.exists() != pb.exists() and (R[k].get("hit") or S[k].get("hit")):
                hd += 1
                log(f"RAWDIFF {n} {k}: raw record present on one side only")
        summ[n] = dict(shared_rows=len(shared), row_diffs=rd, shared_hit_records=nh, raw_diffs=hd)
        nd += rd + hd
    (out / "stored_report.json").write_text(json.dumps(summ, indent=1))
    log(f"END stored: {summ}")
    return 0 if nd == 0 and summ else 1


# ═════════════════════════════ synthetic error cases ═════════════════════════

def cmd_errcases(a) -> int:
    code = Path(a.code_root).resolve()
    sys.path.insert(0, str(HERE))
    import timing_driver as td
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOGF[0] = out / "equiv.log"
    cfgp = Path(a.config) if Path(a.config).is_absolute() else code / a.config
    cfg = td.load_jsonc(cfgp)
    tdir = cfg["paths"]["testset_dir"]
    src = (Path(tdir) if Path(tdir).is_absolute() else code / tdir) / a.model
    modes = cfg["speculation"]["branch_modes"]
    model = f"{a.model}_errcases"
    dst = out / "testsets" / model
    shutil.rmtree(dst, ignore_errors=True)
    cases = ("as_fail", "no_kind", "no_xmit_pc", "gem5_panic")
    rng = random.Random(a.seed)
    pairs = []
    for m in modes:
        stems = sorted(p.stem for p in (src / m / "asm").glob("inst-*.s"))
        pick = rng.sample(stems, len(cases) * a.n)
        for sub in ("asm", "ann"):
            (dst / m / sub).mkdir(parents=True, exist_ok=True)
        for i, st in enumerate(pick):
            case = cases[i % len(cases)]
            text = (src / m / "asm" / f"{st}.s").read_text()
            ann = json.loads((src / m / "ann" / f"{st}.ann.json").read_text())
            lines = text.splitlines(keepends=True)
            if case == "as_fail":
                k = next(j for j, l in enumerate(lines) if l.startswith(f'"{st}":'))
                lines.insert(k + 1, "\tthis_is_not_an_instruction %rax\n")
            elif case == "gem5_panic":
                k = next(j for j, l in enumerate(lines) if l.strip() == "movq\t%rsp, %rbp")
                lines[k + 1:k + 1] = ["\tmovabsq\t$0x801fffffe5c0, %rax\n", "\tmovq\t(%rax), %rax\n"]
            elif case == "no_kind":
                ann["xmit"].pop("kind", None)
            elif case == "no_xmit_pc":
                for k in ("addr", "addr_hex", "x86_offset"):
                    ann["xmit"].pop(k, None)
            (dst / m / "asm" / f"{st}.s").write_text("".join(lines))
            (dst / m / "ann" / f"{st}.ann.json").write_text(json.dumps(ann, indent=2))
            pairs.append((m, st, case))
    c = copy.deepcopy(cfg)
    c["paths"]["testset_dir"] = str(out / "testsets")
    (out / "config_errcases.jsonc").write_text(json.dumps(c, indent=1))
    (out / "pairs_errcases.tsv").write_text("# mode\tstem\tcase\n" + "".join(f"{m}\t{s}\t{k}\n" for m, s, k in pairs))
    log(f"errcases: {len(pairs)} tests in {dst} ({', '.join(cases)} x {a.n} per mode); config "
        f"{out / 'config_errcases.jsonc'}; pairs {out / 'pairs_errcases.tsv'}. Next: driver --config "
        f"{out / 'config_errcases.jsonc'} --model {model} --pairs-file {out / 'pairs_errcases.tsv'}")
    return 0


# ═════════════════════════════ parser check ══════════════════════════════════

PARSERS = ("parse_pipeview", "parse_pipeview_by_seq", "parse_simspect_events", "parse_lsq",
           "parse_commit_ticks", "parse_commit_squashes", "parse_branch_events")


def _call(fn, path):
    try:
        return ("ok", fn(path))
    except Exception as e:
        return ("exc", type(e).__name__, str(e))


def cmd_parsers(a) -> int:
    code = Path(a.code_root).resolve()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    LOGF[0] = out / "equiv.log"
    os.environ["SIMSPECT_FAST_PATH"] = "1"
    os.environ["SIMSPECT_FAST_PATH_LOG"] = str(out / "fastpath.log")
    sys.path.insert(0, str(code / "STAGE3_gem5"))
    import gem5_common as gc
    import gem5_fastpath as fp
    assert getattr(gc, "_FASTPATH_INSTALLED", False), "fast path did not install"
    files = sorted(glob.glob(a.traces, recursive=True))
    if a.max and len(files) > a.max:
        files = random.Random(a.seed).sample(files, a.max)
    log(f"START parsers code_root={code} traces={a.traces} files={len(files)}")
    tmp = Path(tempfile.mkdtemp(prefix="fpequiv_"))
    cases = []
    # synthetic edge cases
    good = None
    for f in files[:1]:
        good = f
    syn = tmp / "syn"
    syn.mkdir()
    cases.append(("missing", syn / "does_not_exist.txt"))
    (syn / "empty.txt").write_text("")
    cases.append(("empty", syn / "empty.txt"))
    glued = ("O3PipeView:fetch:1000:0x401000:0:5:jmp\n" + "Ruby. O3PipeView:decode:1500\n"
             + ".   2000: system.cpu.commit: Committing instruction with [sn:5] PC (0x401000=>0x401005)\n"
             + "O3PipeView:simspect:2100:L1D:fill:line=0x40:seq=5:pc=0x401000:victim=-:cause=-:sq=-:id=1\n"
             + "  2200: system.cpu.commit: Squashing due to branch mispred PC:0x401000\n"
             + "O3PipeView:retire:2500:store:0\n")
    (syn / "glued.txt").write_text(glued)
    cases.append(("glued", syn / "glued.txt"))
    (syn / "badsimspect.txt").write_text(glued + "O3PipeView:simspect:2600:L1D:fill:line=0x40:seq\n")
    cases.append(("malformed_simspect", syn / "badsimspect.txt"))
    (syn / "badutf8.txt").write_bytes(glued.encode() + b"\xff\xfe O3PipeView:fetch:9:0x1:0:9:x\n")
    cases.append(("bad_utf8", syn / "badutf8.txt"))
    (syn / "garbled.txt").write_bytes(b"O3PipeView:fetch:notanint:0x1:0:1:x\n" + glued.encode() + b"\xff\n")
    cases.append(("garbled_then_bad_utf8", syn / "garbled.txt"))
    for f in files:
        cases.append(("trace", Path(f)))
    nd = nerr = 0
    rows = []
    for kind, f in cases:
        try:
            p = f
            if str(f).endswith(".gz"):
                p = tmp / "cur.pipeview.txt"
                with gzip.open(f, "rb") as fi, open(p, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
            prod = {n: _call(getattr(gc, n), p) for n in PARSERS}          # outside the scope = production
            with fp.routed_scope() as describe:
                fast = {n: _call(getattr(gc, n), p) for n in PARSERS}
                how = describe()
            bad = [n for n in PARSERS if prod[n] != fast[n]]
            rows.append(dict(kind=kind, file=str(f), identical=not bad, bad=bad, path=how,
                             results={n: (prod[n][0] if prod[n][0] == "ok" else prod[n][1:]) for n in PARSERS}))
            if bad:
                nd += 1
                log(f"DIFF {kind} {f}: parsers {bad}")
            elif kind != "trace":
                log(f"edge case {kind}: identical; production outcome "
                    f"{ {n: (prod[n][0] if prod[n][0] == 'ok' else prod[n][1]) for n in PARSERS} }; fast path {how}")
        except Exception:
            nerr += 1
            log(f"ERROR {kind} {f}:\n{traceback.format_exc()}")
    shutil.rmtree(tmp, ignore_errors=True)
    n_tr = sum(1 for r in rows if r["kind"] == "trace")
    n_fast = sum(1 for r in rows if r["kind"] == "trace" and r["path"].startswith("fast"))
    summ = dict(kind="parsers", cases=len(rows), identical=len(rows) - nd, different=nd, errors=nerr,
                traces=n_tr, traces_served_fast=n_fast)
    (out / "equiv_report.json").write_text(json.dumps(dict(summary=summ, rows=rows), indent=1, default=str))
    log(f"END parsers: {summ}")
    return 0 if (nd == 0 and nerr == 0 and rows) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("driver")
    b = sub.add_parser("batch")
    for p in (d, b):
        p.add_argument("--code-root", required=True)
        p.add_argument("--config", required=True)
        p.add_argument("--model", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--sample", type=int, default=0)
        p.add_argument("--seed", type=int, default=20261116)
        p.add_argument("--pairs-file", default="")
    d.add_argument("--parallel", type=int, default=8)
    d.add_argument("--ab", default="prod,fast")
    d.add_argument("--keep-work", action="store_true")
    b.add_argument("--jobs", type=int, default=8)
    t = sub.add_parser("stored")
    t.add_argument("--run", required=True)
    t.add_argument("--stored", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--code-roots", default="", help="comma list of code roots to mask (the two trees' paths)")
    e = sub.add_parser("errcases")
    e.add_argument("--code-root", required=True)
    e.add_argument("--config", required=True)
    e.add_argument("--model", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--n", type=int, default=2, help="tests per case per mode")
    e.add_argument("--seed", type=int, default=20261116)
    p = sub.add_parser("parsers")
    p.add_argument("--code-root", required=True)
    p.add_argument("--traces", required=True, help="glob of trace files (plain or .gz)")
    p.add_argument("--max", type=int, default=2000)
    p.add_argument("--seed", type=int, default=20261116)
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd in ("driver", "batch") and not a.sample and not a.pairs_file:
        ap.error("give --sample N and/or --pairs-file")
    rc = {"driver": cmd_driver, "batch": cmd_batch, "parsers": cmd_parsers, "errcases": cmd_errcases, "stored": cmd_stored}[a.cmd](a)
    sys.exit(rc)


if __name__ == "__main__":
    main()

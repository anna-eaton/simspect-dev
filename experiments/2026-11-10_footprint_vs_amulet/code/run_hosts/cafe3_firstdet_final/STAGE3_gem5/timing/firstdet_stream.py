#!/usr/bin/env python3
"""firstdet_stream.py: streaming first-detection consumer (firstdet-final, 2026-11-10; Anna: "stream it").

Like timing_driver.py (it reuses timing_driver.run_one unchanged, so every row has the same
fields: gem5/total CPU-s, verdict, cache_setup, stall_points, raw record + trace for hits), but the
corpus is still being written: every --poll seconds it re-lists the testset, takes the
(mode, stem) pairs that are complete (.s and .ann.json present and, when the producer writes one,
listed in MANIFEST.tsv), and runs the ones not yet run, at most --parallel at once.

Order while streaming: within each newly seen batch, pairs run in the rank of
sha256("<seed>:<mode>:<stem>") (stable as the corpus grows). Each row's `idx` is its stream
sequence number (0, 1, 2, ... in submission order), so classify_hits.py / classify_cs_rmw.py work on
the output dir unchanged and their "first detection" is in STREAM order (interim only).
The FINAL number re-orders the finished rows by the seed-20261109 order of the full corpus
(random.Random(seed).shuffle of the sorted pairs = timing_driver.build_order); every verdict is a
per-test property (deterministic per (seed, stem) cache setup and stalls), so the run order does
not change any verdict. firstdet_report.py does that re-ordering.

    TMPDIR=/tmp python3 firstdet_stream.py --code-root <code> --config <cfg> \
        --model Footprint_6_u_core_lpP_fv3 --out <dir> --parallel 16 [--poll 180] [--n-max 0]

Stops when: <out>/STOP exists (graceful: finishes in-flight tests), --max-hours passes, --n-max
tests have run, or the testset has a READY/DONE file and nothing is left to run. Log: <out>/driver.log
(timing_driver's log format) + stream events (poll results, new pairs, sleeps, stop reason).
Outputs: results.jsonl, order_stream.tsv (idx, mode, stem, appended at submission), raw/, traces/, errors/.
"""
import argparse, hashlib, json, os, re, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import timing_driver as td   # noqa: E402

_MODE_RE = re.compile(r"\b(mispredict_not_taken|mispredict_taken|stl_bypass)\b")
_STEM_RE = re.compile(r"\b(inst-[A-Za-z0-9_.\-]+?)(?:\.s|\.ann\.json|\.xml)?(?=\s|$)")


def manifest_pairs(path: Path, modes):
    """Pairs listed in the producer's MANIFEST.tsv (format-tolerant: any line naming an inst-* stem;
    a line with a mode token names that mode only, a line without one names every mode).
    Returns None when there is no manifest (then completeness = .s + .ann.json present)."""
    if not path.exists():
        return None
    out = set()
    for line in path.read_text(errors="replace").splitlines():
        stems = _STEM_RE.findall(line)
        if not stems:
            continue
        ms = _MODE_RE.findall(line)
        for s in stems:
            for m in (ms or modes):
                if m in modes:
                    out.add((m, s))
    return out


def available(testset_model: Path, modes, use_manifest=True):
    pairs = set()
    for m in modes:
        a = {p.stem for p in (testset_model / m / "asm").glob("inst-*.s")}
        n = {p.name[:-len(".ann.json")] for p in (testset_model / m / "ann").glob("inst-*.ann.json")}
        pairs |= {(m, s) for s in a & n}
    if use_manifest:
        mp = manifest_pairs(testset_model / "MANIFEST.tsv", modes)
        if mp is not None:
            pairs &= mp
    return pairs


def provenance_ok(ann: dict):
    """Recipe-v3 guard (coordinator, 2026-11-10): early regen-lp Stage-2 batches may carry v2 settings.
    Pass only if the jmp post-pass placed its jmp uniformly (or there is no jmp_insert) and the fanout_v2
    OTB transform is absent or was not applied. Returns (ok, why)."""
    j = ann.get("jmp_insert")
    if j is not None and not (isinstance(j, dict) and j.get("placement") == "uniform"):
        return False, f"jmp_insert.placement={(j or {}).get('placement') if isinstance(j, dict) else j!r}"
    fv = ann.get("fanout_v2")
    otb = fv.get("otb") if isinstance(fv, dict) else None
    if otb is not None and not (isinstance(otb, dict) and otb.get("applied") is False):
        return False, f"fanout_v2.otb={json.dumps(otb)[:120]}"
    return True, ""


def file_sha(*paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def in_sample(stem: str, frac: float) -> bool:
    """Uniform stem-hash subsample of the corpus (both modes of a stem together), independent of arrival order:
    keep iff sha256("fdsample:<stem>")[:8] / 2**32 < frac. frac >= 1 keeps everything."""
    if frac >= 1:
        return True
    return int(hashlib.sha256(f"fdsample:{stem}".encode()).hexdigest()[:8], 16) / 2**32 < frac


def in_partition(mode: str, stem: str, part: str) -> bool:
    """--partition K/M (multi-host split of one run): keep iff sha256("fdpart:<mode>:<stem>")[:8] mod M == K."""
    if not part:
        return True
    k, m = (int(x) for x in part.split("/"))
    return int(hashlib.sha256(f"fdpart:{mode}:{stem}".encode()).hexdigest()[:8], 16) % m == k


def rank(seed, m, s):
    return hashlib.sha256(f"{seed}:{m}:{s}".encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--parallel", type=int, default=16)
    ap.add_argument("--poll", type=int, default=180)
    ap.add_argument("--n-max", type=int, default=0, help="stop after this many tests (0 = no cap)")
    ap.add_argument("--max-hours", type=float, default=48.0)
    ap.add_argument("--no-manifest", action="store_true", help="ignore MANIFEST.tsv (asm+ann only)")
    ap.add_argument("--sample-frac", type=float, default=1.0,
                    help="run only a uniform stem-hash subsample of the corpus (in_sample); default 1 = all")
    ap.add_argument("--seed-prefix", type=int, default=0,
                    help="once the producer is READY: run only the first N pairs of the seed order of the full corpus "
                         "(timing_driver.build_order), 0 = all. Also, once READY, the queue runs in seed order.")
    ap.add_argument("--priority-file", default="",
                    help="tsv tier<TAB>mode<TAB>stem: run lower tiers first (unlisted = last tier), seed order within a "
                         "tier. Only the ORDER changes; each test keeps its own cache-setup and stall draws")
    ap.add_argument("--only-file", default="", help="tsv mode<TAB>stem (or tier<TAB>mode<TAB>stem): run only these pairs")
    ap.add_argument("--partition", default="", help="K/M: run only pairs in hash partition K of M (in_partition)")
    ap.add_argument("--exclude-file", default="", help="results.jsonl (or tsv of mode<TAB>stem) of pairs another host "
                    "already ran; never run them here")
    ap.add_argument("--idx-offset", type=int, default=0, help="first idx for this host (keeps idx unique when merging hosts)")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--keep-all-traces", action="store_true")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfgp = Path(args.config) if Path(args.config).is_absolute() else Path(args.code_root) / args.config
    cfg = td.load_jsonc(cfgp)
    tdir = cfg["paths"]["testset_dir"]
    testset_model = (Path(tdir) if Path(tdir).is_absolute() else Path(args.code_root) / tdir) / args.model
    modes = cfg["speculation"]["branch_modes"]
    (out / "run_config.jsonc").write_bytes(cfgp.read_bytes())
    td.log(out, f"STREAM START config={cfgp} model={args.model} testset={testset_model} seed={args.seed} "
                f"parallel={args.parallel} poll={args.poll}s n_max={args.n_max} sample_frac={args.sample_frac} TMPDIR={os.environ.get('TMPDIR')} "
                f"cache_setup={cfg['gem5'].get('cache_setup')} sweep={cfg.get('sweep')} pid={os.getpid()} "
                f"loadavg={os.getloadavg()}")
    done, seq = set(), 0
    rj = out / "results.jsonl"
    if rj.exists():
        for l in rj.read_text().splitlines():
            try:
                r = json.loads(l)
                done.add((r["mode"], r["stem"]))
                seq = max(seq, r["idx"] + 1)
            except Exception:
                pass
    osf = out / "order_stream.tsv"
    if osf.exists():   # submitted but unfinished rows of an earlier session: rerun them under new idx
        for l in osf.read_text().splitlines():
            try:
                seq = max(seq, int(l.split("\t")[0]) + 1)
            except Exception:
                pass
    seq = max(seq, args.idx_offset)
    excluded = set()
    if args.exclude_file:
        for l in Path(args.exclude_file).read_text().splitlines():
            try:
                r = json.loads(l); excluded.add((r["mode"], r["stem"]))
            except Exception:
                f_ = l.split("\t")
                if len(f_) >= 2:
                    excluded.add((f_[0], f_[1]))
    only = None
    if args.only_file:
        only = set()
        for l in Path(args.only_file).read_text().splitlines():
            f_ = [x.strip() for x in l.split("\t")]
            if len(f_) >= 3 and f_[0].isdigit():
                f_ = f_[1:]
            if len(f_) >= 2:
                only.add((f_[0], f_[1]))
    td.log(out, f"only-file: {len(only) if only is not None else 'none'} pairs")
    td.log(out, f"resume: {len(done)} done, next idx {seq}, partition={args.partition or 'all'}, "
                f"excluded (run elsewhere)={len(excluded)}")
    deadline = time.time() + args.max_hours * 3600
    skipped = {}   # (mode, stem) -> ann mtime when it failed the provenance guard (rechecked if the file changes)
    spf = out / "skipped_provenance.tsv"
    queue, inflight = [], {}
    last_poll, nrun, stop_reason = 0.0, 0, None
    seedpos = None   # (mode, stem) -> position in the seed order, computed once the producer is READY
    prio = {}
    if args.priority_file:
        for l in Path(args.priority_file).read_text().splitlines():
            f_ = l.split("\t")
            if len(f_) >= 3 and f_[0].strip().isdigit():
                prio[(f_[1], f_[2].strip())] = int(f_[0])
        td.log(out, f"priority file {args.priority_file}: {len(prio)} pairs, tiers "
                    f"{dict(sorted(__import__('collections').Counter(prio.values()).items()))}")
    def _key(p):
        return (prio.get(p, 10**6), seedpos.get(p, 10**12) if seedpos is not None else 0, rank(args.seed, *p))
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        while True:
            if (out / "STOP").exists():
                stop_reason = "STOP file"
            elif time.time() > deadline:
                stop_reason = "max-hours"
            elif args.n_max and nrun + len(done) >= args.n_max and not queue:
                stop_reason = f"n-max {args.n_max}"
            if stop_reason:
                break
            if time.time() - last_poll >= args.poll or (not queue and not inflight):
                try:
                    av = available(testset_model, modes, not args.no_manifest)
                except Exception:
                    td.log(out, f"ERROR listing testset:\n{traceback.format_exc()}")
                    av = set()
                queued = {(m, s) for m, s in queue} | set(inflight.values())
                ready = any((testset_model / f).exists() for f in ("READY", "DONE"))
                if ready and seedpos is None:
                    order = td.build_order(testset_model, modes, args.seed)
                    seedpos = {p: i for i, p in enumerate(order)}
                    (out / "order_seed.tsv").write_text("".join(f"{i}\t{m}\t{s_}\n" for i, (m, s_) in enumerate(order)))
                    queue.sort(key=_key)
                    td.log(out, f"producer READY: seed order of {len(order)} pairs written (order_seed.tsv); queue "
                                f"now runs in seed order" + (f", restricted to its first {args.seed_prefix}" if args.seed_prefix else ""))
                    if args.seed_prefix:
                        queue = [p for p in queue if seedpos.get(p, 10**12) < args.seed_prefix]
                cand = [p for p in av - done - queued - excluded
                        if in_sample(p[1], args.sample_frac) and in_partition(p[0], p[1], args.partition)
                        and (only is None or p in only)
                        and (seedpos is None or not args.seed_prefix or seedpos.get(p, 10**12) < args.seed_prefix)]
                cand.sort(key=_key)
                new, nskip = [], 0
                for (m, st) in cand:
                    ap_ = testset_model / m / "ann" / f"{st}.ann.json"
                    try:
                        mt = ap_.stat().st_mtime
                        if skipped.get((m, st)) == mt:
                            continue
                        ok, why = provenance_ok(json.loads(ap_.read_text()))
                    except Exception as e:
                        ok, why, mt = False, f"unreadable ann: {type(e).__name__}: {e}"[:150], None
                    if ok:
                        skipped.pop((m, st), None)
                        new.append((m, st))
                    else:
                        skipped[(m, st)] = mt
                        nskip += 1
                        with open(spf, "a") as f:
                            f.write(f"{time.strftime('%F %T')}\t{m}\t{st}\t{why}\n")
                if args.n_max:
                    new = new[:max(0, args.n_max - len(done) - len(queued))]
                queue += new
                if prio:
                    queue.sort(key=_key)
                last_poll = time.time()
                td.log(out, f"poll: {len(av)} complete pairs, {len(new)} new, queue {len(queue)}, "
                            f"inflight {len(inflight)}, done {len(done)}, skipped_provenance_new={nskip} "
                            f"(total {len(skipped)}), producer_ready={ready}, "
                            f"loadavg={os.getloadavg()}")
                if ready and not queue and not inflight and not new:
                    stop_reason = "producer READY and nothing left"
                    break
            while queue and len(inflight) < args.parallel:
                m, s = queue.pop(0)
                try:   # sha of the exact .s + .ann.json run (report drops rows whose files changed later)
                    sha = file_sha(testset_model / m / "asm" / f"{s}.s", testset_model / m / "ann" / f"{s}.ann.json")
                except Exception:
                    sha = "unreadable"
                with open(osf, "a") as f:
                    f.write(f"{seq}\t{m}\t{s}\t{sha}\n")
                fut = ex.submit(td.run_one, seq, m, s, cfg, args, out, testset_model)
                inflight[fut] = (m, s)
                seq += 1
            if not inflight:
                time.sleep(min(args.poll, 60))
                continue
            fin, _ = wait(list(inflight), timeout=30, return_when=FIRST_COMPLETED)
            for f in fin:
                m, s = inflight.pop(f)
                try:
                    row = f.result()
                    with open(rj, "a") as fo:
                        fo.write(json.dumps(row) + "\n")
                    done.add((m, s))
                    nrun += 1
                    td.log(out, f"idx={row['idx']} {m}/{s} status={row['status']} hit={row['hit']} kind={row.get('kind')} "
                                f"setup={row.get('cache_setup')} gem5_cpu={row['gem5_cpu_s']}s total_cpu={row['total_cpu_s']}s "
                                f"terms={row.get('terms_fired')}")
                except Exception:
                    td.log(out, f"ERROR {m}/{s}:\n{traceback.format_exc()}")
        td.log(out, f"stopping ({stop_reason}); waiting for {len(inflight)} in-flight tests")
        for f in list(inflight):
            m, s = inflight.pop(f)
            try:
                row = f.result()
                with open(rj, "a") as fo:
                    fo.write(json.dumps(row) + "\n")
                done.add((m, s))
                nrun += 1
            except Exception:
                td.log(out, f"ERROR {m}/{s}:\n{traceback.format_exc()}")
    td.log(out, f"STREAM END reason={stop_reason} ran_this_session={nrun} total_done={len(done)} loadavg={os.getloadavg()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""stream_fp.py -- streaming Stage 1.5 -> Stage 2 (recipe v3) -> publish, for one core-pinned family (regen-lp, 2026-11-10).

Anna 2026-11-10: "once the first stage starts generating skeletons the second stage starts concretizing and the runs start
occurring. i want numbers as soon as possible." Runs inside gem5_dev next to stage15lp.py. Every --interval seconds:

  1. MERGE: every job that stage15lp.py has finished (rows of <s15>/jobs.jsonl) is merged into <base>/xml with global
     fingerprint dedup (the fp in each job's _dedup_map.jsonl = alloy_solver_order's rule), numbered inst-NNNNNN in merge
     order. _stream_map.jsonl: name, core, seed, job dir, source inst, fp, time.
  2. STAGE 2: stage2_sharded.py --config <cfg> --model <base name> (resumable: only stems without .ll are generated,
     then pipeline.py asm compiles the missing .s). <cfg> = runconfigs/regen_lp_20261110/stage2_fv3.jsonc with only
     paths.testset_dir (absolute) and gem5.jobs (asm compile threads) changed.
  (order per cycle: merge, publish ready stems in batches of at most --max-batch, then Stage 2 on the rest)
  3. PUBLISH a batch: stems whose ann exists in every mode (or that failed Stage 2 in some mode for 2 cycles; then only the
     modes that compiled) go into batches/bNNNN/src (symlinks), then make_rmw_corpus.py --select eligible --fraction 0.5
     --seed 20261109 --complete (selection = half of the batch's eligible ld tests), then make_jmp_corpus.py --p 0.5
     --seed 20261109 (placement uniform, the recipe-v3 default) -> batches/bNNNN/jmp. Its asm/ann + the stems' xml are
     copied into <final>/<mode>/{asm,ann} and <final>/xml; rmw_stems.tsv / jmp_stems.tsv / MANIFEST.tsv (stem, core,
     seed, merged_at, published_at, batch, modes) are appended. batches/bNNNN/PUBLISHED marks a finished batch (the relay
     to cafe3 copies only those).
  4. When <s15>/SUMMARY.json exists (stage15lp ended) and everything is published: write <final>/READY (counts and
     provenance) and stop.
Log: <ws>/logs/stream_<final name>.log (every step, rc, counts, errors with tracebacks). State: <ws>/stream/<final>/state.json.
Usage: stream_fp.py --s15 runs15/Footprint_6_u_lpPc --base-name Footprint_6_u_core_lpP_fv3_base --final-name Footprint_6_u_core_lpP_fv3 \
       --cfg code/runconfigs/regen_lp_20261110/stage2_fv3_stream.jsonc --code code [--interval 150 --jobs 16]
"""
import argparse, datetime as dt, hashlib, json, os, resource, shutil, subprocess, sys, time, traceback
from pathlib import Path

B = Path("/tests/simspect_alloy_20261108"); TS = B / "testsets_twostage"; WS = B / "loosepin_regen"   # defaults; --ts-dir / --ws override
STAGE1_LOGS = "stage1/logs/Footprint_6_u_core_ri__*.log"                                                # default; --stage1-logs overrides
MODES = ["mispredict_not_taken", "mispredict_taken"]


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def cpu_children():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def run_cpu(st, key, cmd, **kw):
    """subprocess.run + CPU-s of the whole child tree (RUSAGE_CHILDREN delta; waited-for descendants included)."""
    c0 = cpu_children(); r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    st.setdefault("cpu_s", {}); st["cpu_s"][key] = round(st["cpu_s"].get(key, 0) + cpu_children() - c0, 1)
    return r


def acopy(src, dst):
    """atomic copy: write <dir>/.<name>.tmp then rename (consumers glob *.s / *.ann.json / *.xml)."""
    tmp = dst.parent / f".{dst.name}.tmp"; shutil.copy2(src, tmp); os.replace(tmp, dst)


def write_prov(final, st, s15, base, cfg, code, a, ready=False):
    """PROVENANCE.json at the corpus root (TA-7 generation cost): CPU-s per stage and the (stem, mode) pair count."""
    jobs = [json.loads(l) for l in (s15 / "jobs.jsonl").read_text().splitlines() if l.strip()] if (s15 / "jobs.jsonl").exists() else []
    s1 = {}
    s1f = WS / "stage1" / "status" / "stage1_status.json"
    pairs = sum(len(list((final / m / "ann").glob("*.ann.json"))) for m in MODES)
    prov = {"updated": now(), "complete": ready, "corpus": str(final), "programs_merged": st["n"], "stems_published": len(st["published"]),
            "stem_mode_pairs": pairs, "batches": st["batch"],
            "cpu_s": {"stage1_alloy_cores": "see stage1_cpu_s (wall-clock of each single-threaded Stage-1 JVM partition)",
                      "stage15_alloy_job_wall_s_sum": round(sum(j.get("secs") or 0 for j in jobs), 1),
                      "stage15_note": "sum of per-job wall seconds of one JVM each (a6RandomModels is single-threaded apart from GC threads), all jobs incl. EXHAUSTED/0",
                      "stage2_parsexml_llc": st.get("cpu_s", {}).get("stage2"), "rmw_postpass": st.get("cpu_s", {}).get("rmw"),
                      "jmp_postpass": st.get("cpu_s", {}).get("jmp"),
                      "stage2_note": "RUSAGE_CHILDREN deltas of the whole subprocess tree (user+sys CPU-s)"},
            "stage1_cpu_s": stage1_cpu(), "stage15": str(s15), "base_testset": str(base), "stage2_config": str(cfg), "code": str(code),
            "recipe_version": "v3 (recipe-v3 2026-11-10: fanout OTB off, jmp placement uniform, RMW --select eligible)",
            "code_hashes": {f: hashlib.sha256((code / f).read_bytes()).hexdigest() for f in
                            ("STAGE2_compilation/make_rmw_corpus.py", "STAGE2_compilation/make_jmp_corpus.py", "STAGE2_compilation/parsexml.py",
                             "STAGE2_compilation/batch_generate.py", "runconfigs/regen_lp_20261110/stage2_fv3.jsonc") if (code / f).exists()},
            "stage2_config_sha256": hashlib.sha256(cfg.read_bytes()).hexdigest(),
            "stage15_queue": json.loads((s15 / "QUEUE_ORDER.json").read_text()) if (s15 / "QUEUE_ORDER.json").exists() else None,
            "recipe": "stage2_fv3 (OTB off) -> make_rmw_corpus --select eligible p0.5 seed 20261109 per batch -> make_jmp_corpus p0.5 seed 20261109 uniform"}
    tmp = final / ".PROVENANCE.json.tmp"; tmp.write_text(json.dumps(prov, indent=1)); os.replace(tmp, final / "PROVENANCE.json")


def stage1_cpu():
    """Stage-1 partition wall seconds from run_stage1 logs (START/END timestamps)."""
    out = {}
    for lg in sorted(WS.glob(STAGE1_LOGS)):
        lines = lg.read_text(errors="replace").splitlines()
        try:
            t0 = dt.datetime.fromisoformat(lines[0].split()[0]); t1 = dt.datetime.fromisoformat(lines[-1].split()[0])
            v = [l.split("VERDICT=")[1].split()[0] for l in lines if "VERDICT=" in l]
            out[lg.stem] = {"wall_s": round((t1 - t0).total_seconds()), "verdict": v[-1] if v else "RUNNING"}
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s15", required=True); ap.add_argument("--base-name", required=True); ap.add_argument("--final-name", required=True)
    ap.add_argument("--cfg", required=True); ap.add_argument("--code", required=True)
    ap.add_argument("--ts-dir", default=None, help="testset root (default /tests/simspect_alloy_20261108/testsets_twostage)")
    ap.add_argument("--ws", default=None, help="work dir holding logs/ and stream/ (default .../loosepin_regen)")
    ap.add_argument("--stage1-logs", default=None, help="glob (relative to --ws) of the Stage-1 partition logs, for the CPU-s record")
    ap.add_argument("--family-label", default="Footprint_6_u", help="family name written into READY")
    ap.add_argument("--interval", type=int, default=150); ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--min-batch", type=int, default=50); ap.add_argument("--max-batch", type=int, default=150); ap.add_argument("--git-rev", default="264adea+uncommitted")
    a = ap.parse_args()
    global TS, WS, STAGE1_LOGS
    TS = Path(a.ts_dir) if a.ts_dir else TS; WS = Path(a.ws).resolve() if a.ws else WS; STAGE1_LOGS = a.stage1_logs or STAGE1_LOGS
    (WS / "logs").mkdir(parents=True, exist_ok=True)
    s15, code, cfg = Path(a.s15).resolve(), Path(a.code).resolve(), Path(a.cfg).resolve()
    base, final = TS / a.base_name, TS / a.final_name
    sd = WS / "stream" / a.final_name; sd.mkdir(parents=True, exist_ok=True); (base / "xml").mkdir(parents=True, exist_ok=True)
    final.mkdir(parents=True, exist_ok=True); (final / "xml").mkdir(exist_ok=True)
    for m in MODES:
        for d in ("asm", "ann"):
            (final / m / d).mkdir(parents=True, exist_ok=True)
    logf = open(WS / "logs" / f"stream_{a.final_name}.log", "a", buffering=1)
    def log(msg):
        logf.write(f"{now()} {msg}\n"); print(msg, flush=True)
    stf = sd / "state.json"
    st = json.loads(stf.read_text()) if stf.exists() else dict(merged_jobs=[], n=0, seen={}, info={}, published=[], tries={}, batch=0)
    def save():
        tmp = stf.with_suffix(".tmp"); tmp.write_text(json.dumps(st)); os.replace(tmp, stf)
    log(f"START s15={s15} base={base} final={final} cfg={cfg} interval={a.interval} jobs={a.jobs} (resume: n={st['n']}, published={len(st['published'])})")
    smap = open(base / "xml" / "_stream_map.jsonl", "a", buffering=1)
    man = final / "MANIFEST.tsv"
    if not man.exists():
        man.write_text("stem\tcore\tseed\tmerged_at\tpublished_at\tbatch\tmodes\n")
    for t in ("rmw_stems.tsv", "jmp_stems.tsv"):
        if not (final / t).exists():
            (final / t).write_text("")
    while True:
        t_cycle = time.time()
        try:
            # 1. merge finished jobs
            jf = s15 / "jobs.jsonl"
            rows = [json.loads(l) for l in jf.read_text().splitlines() if l.strip()] if jf.exists() else []
            merged = set(st["merged_jobs"]); added = 0
            for r in rows:
                xd = r.get("xml_dir")
                if not xd or xd in merged:
                    continue
                mp = Path(xd) / "_dedup_map.jsonl"
                for l in (mp.read_text().splitlines() if mp.exists() else []):
                    if not l.strip():
                        continue
                    d = json.loads(l)
                    if d["fp"] in st["seen"]:
                        continue
                    st["n"] += 1; name = f"inst-{st['n']:06d}"; st["seen"][d["fp"]] = name
                    for ext in (".txt", ".xml"):
                        src = Path(xd) / (d["name"][:-4] + ext)
                        if src.exists():
                            tmp = base / "xml" / f".tmp-{name}{ext}"; shutil.copyfile(src, tmp); os.replace(tmp, base / "xml" / f"{name}{ext}")
                    st["info"][name] = dict(core=r["core"], seed=r["seed"], merged_at=now())
                    smap.write(json.dumps({"name": name + ".xml", "core": r["core"], "seed": r["seed"], "job": xd,
                                           "source": d["name"], "fp": d["fp"], "time": now()}) + "\n")
                    added += 1
                st["merged_jobs"].append(xd); merged.add(xd)
            save()
            log(f"merge: +{added} (total {st['n']}) from {len(rows)} finished jobs")
            def publish_all(ready, partial, done15):
                # small batches while the backlog is small (tests flow early); with a big backlog, bigger batches
                # (each RMW+jmp call has ~30 s fixed cost), at most 1,500 stems
                bs = max(a.max_batch, min(1500, len(ready) // 3)) if st["batch"] >= 2 else a.max_batch
                for k0 in range(0, len(ready), bs):
                    chunk = ready[k0:k0 + bs]
                    if len(chunk) < a.min_batch and not done15 and k0 > 0:
                        break
                    publish(chunk, partial)
            def publish(ready, partial):
                st["batch"] += 1; b = f"b{st['batch']:04d}"; bd = sd / "batches" / b
                if bd.exists():
                    shutil.rmtree(bd)
                srcd = bd / "src"; (srcd).mkdir(parents=True)
                os.symlink(base / "xml", srcd / "xml")
                for m in MODES:
                    for d in ("asm", "ann", "llvm"):
                        (srcd / m / d).mkdir(parents=True)
                    for s in ready:
                        if s in partial and m not in partial[s]:
                            continue
                        for d, ext in (("asm", ".s"), ("ann", ".ann.json"), ("llvm", ".ann.json")):
                            p = base / m / d / f"{s}{ext}"
                            if p.exists():
                                os.symlink(p, srcd / m / d / f"{s}{ext}")
                t3 = time.time()
                r3 = run_cpu(st, "rmw", [sys.executable, str(code / "STAGE2_compilation/make_rmw_corpus.py"), "--repo-root", str(code),
                                     "--src", str(srcd), "--dst", str(bd / "rmw"), "--fraction", "0.5", "--seed", "20261109",
                                     "--select", "eligible", "--complete", "--jobs", str(a.jobs), "--git-rev", a.git_rev])
                r4 = run_cpu(st, "jmp", [sys.executable, str(code / "STAGE2_compilation/make_jmp_corpus.py"), "--repo-root", str(code),
                                     "--src", str(bd / "rmw"), "--dst", str(bd / "jmp"), "--p", "0.5", "--seed", "20261109",
                                     "--jobs", str(a.jobs), "--git-rev", a.git_rev]) if r3.returncode == 0 else None
                ok = r3.returncode == 0 and r4 is not None and r4.returncode == 0
                log(f"publish {b}: {len(ready)} stems ({len(partial)} partial) rmw rc={r3.returncode} jmp rc={r4.returncode if r4 else None} "
                    f"secs={round(time.time()-t3)}" + ("" if ok else f"\nRMW STDERR {r3.stderr[-3000:]}\nJMP STDERR {(r4.stderr[-3000:] if r4 else '')}"))
                if ok:
                    out = bd / "out"
                    for m in MODES:
                        for d in ("asm", "ann"):
                            (out / m / d).mkdir(parents=True, exist_ok=True)
                            for p in (bd / "jmp" / m / d).iterdir():
                                shutil.copy2(p, out / m / d / p.name)
                            for p in (bd / "jmp" / m / d).iterdir():
                                if d == "ann":   # .s first, then .ann.json: a consumer that sees the ann sees the final .s
                                    continue
                                acopy(p, final / m / d / p.name)
                        for p in (bd / "jmp" / m / "ann").iterdir():
                            acopy(p, final / m / "ann" / p.name)
                    (out / "xml").mkdir(exist_ok=True)
                    for s in ready:
                        for ext in (".xml", ".txt"):
                            p = base / "xml" / f"{s}{ext}"
                            if p.exists():
                                acopy(p, final / "xml" / p.name); shutil.copy2(p, out / "xml" / p.name)
                    for t, dst in (("rmw/rmw_stems.tsv", "rmw_stems.tsv"), ("jmp/jmp_stems.tsv", "jmp_stems.tsv")):
                        p = bd / t
                        if p.exists():
                            lines = p.read_text().splitlines()
                            agg = final / dst
                            old = agg.read_text()
                            if not old and lines:
                                old = lines[0] + "\n"
                            tmp = agg.parent / f".{agg.name}.tmp"; tmp.write_text(old + "".join(l + "\n" for l in lines[1:])); os.replace(tmp, agg)
                    tpub = now()
                    rows_m = "".join(f"{s}\t{st['info'].get(s, {}).get('core')}\t{st['info'].get(s, {}).get('seed')}\t{st['info'].get(s, {}).get('merged_at')}"
                                     f"\t{tpub}\t{b}\t{','.join(partial.get(s, MODES))}\n" for s in ready)
                    tmp = man.parent / ".MANIFEST.tsv.tmp"; tmp.write_text(man.read_text() + rows_m); os.replace(tmp, man)   # only after asm+ann are final
                    # relay payload: this batch's rows only + checksums of every payload file (relay_cafe3.sh verifies, moves
                    # the files in with renames, and only then appends these rows to cafe3's MANIFEST.tsv / rmw / jmp lists)
                    (out / "MANIFEST_batch.tsv").write_text(man.read_text().splitlines()[0] + "\n" + rows_m)   # header + this batch
                    for t, nm in (("rmw/rmw_stems.tsv", "rmw_batch.tsv"), ("jmp/jmp_stems.tsv", "jmp_batch.tsv")):
                        p = bd / t
                        (out / nm).write_text("".join(l + "\n" for l in (p.read_text().splitlines() if p.exists() else [])))  # header + rows
                    with open(out / "SHA256SUMS", "w") as f:
                        for p in sorted(out.rglob("*")):
                            if p.is_file() and p.name != "SHA256SUMS":
                                f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}\n")
                    st["published"] += ready
                    (bd / "PUBLISHED").write_text(f"{tpub} {len(ready)} stems\n")
                    write_prov(final, st, s15, base, cfg, code, a)
                    log(f"published {b}: total published {len(st['published'])} cpu_s={st.get('cpu_s')}")
                save()
            # 2. publish what is already compiled (small batches, before the next Stage-2 pass so tests flow early)
            pub = set(st['published'])
            pending = [f'inst-{k:06d}' for k in range(1, st['n'] + 1) if f'inst-{k:06d}' not in pub]
            ready, partial = [], {}
            for s in pending:
                have = [m for m in MODES if (base / m / "ann" / f"{s}.ann.json").exists() and (base / m / "asm" / f"{s}.s").exists()]
                if len(have) == len(MODES):
                    ready.append(s)
                else:
                    st["tries"][s] = st["tries"].get(s, 0) + 1
                    if st["tries"][s] >= 4:
                        ready.append(s); partial[s] = have
            done15 = (s15 / "SUMMARY.json").exists()
            if ready and (len(ready) >= a.min_batch or done15):
                publish_all(ready, partial, done15)
            # 3. stage 2 (resumable) on everything merged and not yet published
            pub = set(st['published'])
            pending = [f'inst-{k:06d}' for k in range(1, st['n'] + 1) if f'inst-{k:06d}' not in pub]
            if pending:
                t2 = time.time()
                r2 = run_cpu(st, "stage2", [sys.executable, "STAGE1_alloy/models/proposed_twophase/stage2_sharded.py", "--config", str(cfg),
                                     "--model", a.base_name, "--jobs", str(a.jobs), "--first-fraction", "0"], cwd=str(code))
                log(f"stage2: rc={r2.returncode} secs={round(time.time()-t2)}" + (f"\n{r2.stderr[-3000:]}" if r2.returncode else ""))
            if done15 and st["n"] == len(st["published"]) and all(r.get("xml_dir") in set(st["merged_jobs"]) for r in rows if r.get("xml_dir")):
                n_nt = len(list((final / MODES[0] / "asm").glob("*.s"))); n_t = len(list((final / MODES[1] / "asm").glob("*.s")))
                summ = json.loads((s15 / "SUMMARY.json").read_text())
                (final / "READY").write_text(
                    f"READY {now()} regen-lp: {a.final_name} = {a.family_label} core-pinned loose-pin lpP corpus, streamed.\n"
                    f"Stage 1: {a.family_label}_core_ri RI cores, {s15}/cores.json; Stage 1.5: stage15lp.py {s15} "
                    f"(distinct {summ.get('distinct_global')}, jobs {summ.get('jobs')}, exhausted cores {summ.get('exhausted_cores')}/{summ.get('cores')}); "
                    f"merged into {base}/xml ({st['n']} programs, _stream_map.jsonl).\n"
                    f"Stage 2: {cfg.name} (stage2_fv3 = E3_STT_6_fv2fp options with fanout OTB off) -> per batch make_rmw_corpus --select eligible "
                    f"--fraction 0.5 --seed 20261109 --complete -> make_jmp_corpus --p 0.5 --seed 20261109 (placement uniform); {st['batch']} batches.\n"
                    f"tests not_taken {n_nt}, taken {n_t}; MANIFEST.tsv, rmw_stems.tsv, jmp_stems.tsv; code {code} (CODE_SNAPSHOT.txt, SHA256SUMS).\n")
                write_prov(final, st, s15, base, cfg, code, a, ready=True)
                log(f"READY written: programs {st['n']}, tests {n_nt} + {n_t}")
                break
        except Exception:
            log(f"EXCEPTION\n{traceback.format_exc()}")
        time.sleep(max(5, a.interval - (time.time() - t_cycle)))
    log("END")


if __name__ == "__main__":
    main()

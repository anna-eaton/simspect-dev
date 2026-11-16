#!/usr/bin/env python3
"""stage15lp.py -- Stage 1.5 with a LOOSE (path-style) Stage-1 core pin, seeded random order and an adaptive per-core
budget (regen-lp, 2026-11-10). UNAPPROVED DRAFT TOOLING; writes new files only, never edits a model.

Anna 2026-11-10: "I STILL want the skeletons to come from the first round of alloy enumeration." So each Stage-1.5 run
is one core-pinned model:  <base draft> (make_loosepin.py --pin core: but 8, prefix IX, no-junk, committed region
required, minimality prod or coneg) + seed_core = stage_seed.build_pred(core) with every core rf edge  ob in oa.rf
relaxed to  ob in oa.rf.*(ddi.rf)  (make_s15_model.py --pin b, DA-1(b)), so ALUs and memory hops may sit on a core edge.

Steps
  1. Load the Stage-1 cores (inst-*.txt) and dedup them at the level the pin sees (audit_core_dups.py level 'seed' by
     default: two cores with the same seed fingerprint give the same pin, so the same run). cores.json lists every
     representative and its members.
  2. Write one model per distinct core: models/<core>.als (base text + the path-style seed_core); check_bound lint.
  3. Continuous adaptive scheduler over --slots worker processes. Each job = (core, seed) run through
     alloy_solver_order.run_random_xml (the pipeline's seeded-order machinery: a6RandomModels, or a6CountModels for
     seed "default"; per-job xml dir with fingerprints in _dedup_map.jsonl), --job-timeout seconds, --cap instances.
     First pass: every core gets one job (random seed 1; --first-seed default = stock order). Then, when a slot frees, a core is eligible if it is not
     EXHAUSTED and has started at most (min jobs over active cores) + --spread jobs (so no core is starved); among the
     eligible ones the core with the highest novelty (new fingerprints / instances over its finished jobs; new = not
     seen in ANY earlier finished job of this run) is picked; ties by fewest jobs, then core order. Random seeds per core
     are 1, 2, 3, ... The scheduler also writes jobs.jsonl as each job ends, so stream_fp.py can merge while it runs. No new job starts once elapsed + job-timeout > --budget-s.
  4. Records: stage15lp.log (every decision and error), jobs.jsonl (one row per finished job: core, seed, instances,
     kept, verdict, secs, new_global), cores.json, MERGE_INPUTS.txt (job xml dirs in deterministic order: core order,
     then "default", then seed number; feed it to merge_lp.py --inputs-file), SUMMARY.json.
Usage (inside gem5_dev, from anywhere):
  python3 stage15lp.py --base models/STT_6_u_lpPc.als --cores <stage1_xml dir> [...] --out runs15/STT_6_u_lpPc \
      --code <code root> --slots 24 --job-timeout 900 --budget-s 7200 --cap 10000
"""
import argparse, collections, concurrent.futures as cf, datetime as dt, hashlib, json, os, random, shutil, subprocess, sys, time, traceback
from pathlib import Path


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_job(code, model_file, xml_dir, seed, timeout_s, cap, walk_p, xmx):
    """One (core, seed) enumeration via alloy_solver_order.run_random_xml. Runs in a worker process."""
    sys.path.insert(0, code)
    import alloy_solver_order as aso
    so = {"mode": "random", "seeds": [seed], "walk_p": walk_p, "parallel": False, "timeout_s": timeout_s, "xmx": xmx,
          "keep_raw": False}
    out = {"xml_dir": xml_dir, "seed": seed}
    try:
        rec = aso.run_random_xml({}, so, Path(model_file), Path(xml_dir), Path(code) / "STAGE1_alloy",
                                 Path(code) / "STAGE2_compilation", cap)
        out["rec"] = rec
    except Exception:
        out["error"] = traceback.format_exc()
        p = Path(xml_dir) / "SOLVER_ORDER.json"
        if p.exists():
            out["rec"] = json.loads(p.read_text())
    m = Path(xml_dir) / "_dedup_map.jsonl"
    out["fps"] = [json.loads(l)["fp"] for l in m.read_text().splitlines() if l.strip()] if m.exists() else []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True); ap.add_argument("--cores", nargs="+", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--code", required=True)
    ap.add_argument("--slots", type=int, default=24); ap.add_argument("--job-timeout", type=int, default=900)
    ap.add_argument("--budget-s", type=int, default=7200); ap.add_argument("--cap", type=int, default=10000)
    ap.add_argument("--walk-p", type=float, default=0.05); ap.add_argument("--xmx", default="5g")
    ap.add_argument("--first-seed", choices=["default", "random"], default="random",
                    help="first job per core: random seed 1 (default, spread sample) or the stock a6CountModels order")
    ap.add_argument("--shuffle-seed", type=int, default=None,
                    help="randomize the core queue (first-pass order and tie-breaks) with this recorded seed")
    ap.add_argument("--seed-start", type=int, default=1,
                    help="first random seed per core (later jobs take the next ones); give each extension run its own range")
    ap.add_argument("--resume", action="store_true",
                    help="continue a run in the same --out: per-core state and the seen fingerprints are rebuilt from jobs.jsonl; "
                         "job dirs of unfinished (killed) jobs are deleted and those (core, seed) pairs rerun")
    ap.add_argument("--limit-cores", type=int, default=0, help="smoke tests only: first N distinct cores");
    ap.add_argument("--spread", type=int, default=2); ap.add_argument("--dedup-level", choices=["seed", "exact"], default="seed")
    a = ap.parse_args()
    code = str(Path(a.code).resolve()); out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    if (out / "jobs.jsonl").exists() and not a.resume:
        sys.exit(f"stage15lp: {out}/jobs.jsonl exists (one run per out dir; --resume to continue)")
    logf = open(out / "stage15lp.log", "a", buffering=1)
    def log(m):
        logf.write(f"{now()} {m}\n"); print(m, flush=True)
    t0 = time.time()
    log(f"START base={a.base} sha256={sha(a.base)} cores={a.cores} slots={a.slots} job_timeout={a.job_timeout} "
        f"budget_s={a.budget_s} cap={a.cap} walk_p={a.walk_p} spread={a.spread} dedup_level={a.dedup_level} seed_start={a.seed_start} "
        f"shuffle_seed={a.shuffle_seed} host={os.uname().nodename}")

    # 1. cores + dedup (audit_core_dups.py, imported with an empty argv so its module-level report loop does nothing)
    s1 = Path(code) / "STAGE1_alloy"; sys.path.insert(0, str(s1))
    sys.path.insert(0, str(s1 / "models/proposed_twophase/dedup_audit")); sys.path.insert(0, str(s1 / "models/proposed_twophase/stage15_bound"))
    argv, sys.argv = sys.argv, [sys.argv[0]]
    import audit_core_dups as acd  # noqa: E402
    sys.argv = argv
    import make_s15_model as m15  # noqa: E402
    import stage_seed  # noqa: E402
    files = sorted(f.resolve() for d in a.cores for f in Path(d).glob("inst-*.txt"))
    groups = collections.OrderedDict()
    for f in files:
        groups.setdefault(acd.fp(acd.load(f), a.dedup_level), []).append(str(f))
    exact = len({acd.fp(acd.load(f), "exact") for f in files})
    cores = []
    base_text = Path(a.base).read_text()
    (out / "models").mkdir(exist_ok=True)
    items = list(groups.items())[: a.limit_cores or None]
    for k, (fpv, members) in enumerate(items):
        cid = f"c{k:03d}"
        rels = stage_seed.parse_txt(members[0])
        pin = m15.pin_pred(rels, "b")
        mf = out / "models" / f"{cid}.als"
        mf.write_text(base_text + f"\n\n// ---- [lp-8] Stage-1 core {cid} = {members[0]} (path-style pin, make_s15_model.py --pin b) ----\n" + pin + "\n")
        cores.append({"id": cid, "rep": members[0], "members": members, "model": str(mf), "model_sha256": sha(mf)})
    if a.resume and (out / "cores.json").exists():
        old = json.loads((out / "cores.json").read_text())
        if [c["model_sha256"] for c in old["cores"]] != [c["model_sha256"] for c in cores]:
            sys.exit("stage15lp: --resume but the core models differ from cores.json")
    (out / "cores.json").write_text(json.dumps({"base": a.base, "base_sha256": sha(a.base), "dedup_level": a.dedup_level,
                                                "core_files": len(files), "distinct_exact": exact,
                                                "distinct_at_level": len(cores), "cores": cores}, indent=1))
    log(f"cores: {len(files)} files, {exact} distinct (exact), {len(cores)} distinct ({a.dedup_level}) -> {len(cores)} models")
    lint = Path(code) / "STAGE1_alloy/models/proposed_twophase/dedup_audit/check_bound_consistency.py"
    if lint.exists() and cores:
        r = subprocess.run([sys.executable, str(lint), cores[0]["model"]], capture_output=True, text=True)
        log(f"lint {cores[0]['id']}: rc={r.returncode} {r.stdout.strip()}")
        if r.returncode != 0:
            sys.exit("stage15lp: bound lint failed")

    # 3. scheduler
    st = {c["id"]: dict(started=0, done=0, inst=0, new=0, exhausted=False, next_seed=a.seed_start, running=0, errors=0) for c in cores}
    order = {c["id"]: n for n, c in enumerate(cores)}          # deterministic merge order (MERGE_INPUTS)
    ids = [c["id"] for c in cores]
    if a.shuffle_seed is not None:
        random.Random(a.shuffle_seed).shuffle(ids)
    rank = {c: n for n, c in enumerate(ids)}                   # queue order: shuffled with --shuffle-seed (recorded)
    log(f"queue order: {'shuffled, seed ' + str(a.shuffle_seed) if a.shuffle_seed is not None else 'core index'}; first 10: {ids[:10]}")
    (out / "QUEUE_ORDER.json").write_text(json.dumps({"shuffle_seed": a.shuffle_seed, "order": ids, "set": now()}))
    model = {c["id"]: c["model"] for c in cores}
    seen = set(); inputs = []
    if a.resume and (out / "jobs.jsonl").exists():
        finished = set()
        for l in (out / "jobs.jsonl").read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l); c = r["core"]; s_ = st[c]; seed = r["seed"]
            finished.add((c, str(seed)))
            s_["started"] += 1; s_["done"] += 1
            if seed != "default":
                s_["next_seed"] = max(s_["next_seed"], int(seed) + 1)
            fps = []
            if r.get("xml_dir") and (Path(r["xml_dir"]) / "_dedup_map.jsonl").exists():
                fps = [json.loads(x)["fp"] for x in (Path(r["xml_dir"]) / "_dedup_map.jsonl").read_text().splitlines() if x.strip()]
                inputs.append((order[c], -1 if seed == "default" else int(seed), r["xml_dir"]))
            s_["inst"] += len(fps); s_["new"] += len(set(fps) - seen); seen.update(fps)
            if r.get("verdict") == "EXHAUSTED":
                s_["exhausted"] = True
            if r.get("error") or r.get("verdict") in ("ERROR", "UNKNOWN", None):
                s_["errors"] += 1
                if s_["errors"] >= 2:
                    s_["exhausted"] = True
        removed = 0
        for jd in (out / "jobs").glob("*/s*"):
            if (jd.parent.name, jd.name[1:]) not in finished:
                shutil.rmtree(jd); removed += 1
        log(f"RESUME: {len(finished)} finished jobs, {len(seen)} distinct, {sum(v['exhausted'] for v in st.values())} cores done; "
            f"removed {removed} unfinished job dirs (rerun)")
    jobsf = open(out / "jobs.jsonl", "a", buffering=1)
    def pick():
        act = [c for c in st if not st[c]["exhausted"]]
        if not act:
            return None
        fresh = [c for c in act if st[c]["started"] == 0]
        if fresh:
            return min(fresh, key=rank.get)
        lo = min(st[c]["started"] for c in act)
        el = [c for c in act if st[c]["started"] <= lo + a.spread]
        nov = lambda c: (st[c]["new"] / st[c]["inst"]) if st[c]["inst"] else (1.0 if st[c]["done"] == 0 else 0.0)
        return max(el, key=lambda c: (nov(c), -st[c]["started"], -rank[c]))
    with cf.ProcessPoolExecutor(max_workers=a.slots) as ex:
        fut = {}
        def submit():
            c = pick()
            if c is None:
                return False
            s = st[c]
            seed = "default" if (s["started"] == 0 and a.first_seed == "default") else s["next_seed"]
            if seed != "default":
                s["next_seed"] += 1
            s["started"] += 1; s["running"] += 1
            xd = out / "jobs" / c / f"s{seed}" / "xml"
            f = ex.submit(run_job, code, model[c], str(xd), seed, a.job_timeout, a.cap, a.walk_p, a.xmx)
            fut[f] = (c, seed, time.time())
            log(f"SUBMIT {c} seed={seed} (started={s['started']}, novelty_so_far={s['new']}/{s['inst']})")
            return True
        while len(fut) < a.slots and time.time() - t0 + a.job_timeout < a.budget_s and submit():
            pass
        while fut:
            done, _ = cf.wait(list(fut), return_when=cf.FIRST_COMPLETED)
            for f in done:
                c, seed, ts = fut.pop(f)
                s = st[c]; s["running"] -= 1; s["done"] += 1
                try:
                    r = f.result()
                except Exception:
                    r = {"error": traceback.format_exc(), "fps": [], "xml_dir": None}
                rec = r.get("rec") or {}
                sd = (rec.get("seeds") or [{}])[0]
                new = 0
                for fp in r["fps"]:
                    if fp not in seen:
                        seen.add(fp); new += 1
                s["inst"] += len(r["fps"]); s["new"] += new
                if sd.get("verdict") == "EXHAUSTED":
                    s["exhausted"] = True
                if r.get("error") or sd.get("verdict") in ("ERROR", "UNKNOWN", None):
                    s["errors"] += 1
                    if s["errors"] >= 2:      # never spin on a broken core model: retire it (logged; counts as not covered)
                        s["exhausted"] = True; s["retired_on_error"] = True
                        log(f"RETIRE {c}: {s['errors']} failed jobs")
                row = {"core": c, "seed": seed, "instances": sd.get("instances"), "kept": len(r["fps"]), "verdict": sd.get("verdict"),
                       "secs": sd.get("secs"), "new_global": new, "xml_dir": r.get("xml_dir"), "error": r.get("error")}
                jobsf.write(json.dumps(row) + "\n")
                if r.get("xml_dir") and rec:
                    inputs.append((order[c], -1 if seed == "default" else seed, r["xml_dir"]))
                log(f"DONE {c} seed={seed} kept={len(r['fps'])} new_global={new} verdict={sd.get('verdict')} secs={sd.get('secs')}"
                    + (f" ERROR {r['error'].splitlines()[-1] if r.get('error') else ''}" if r.get("error") else "")
                    + f" | distinct so far {len(seen)}")
                if r.get("error"):
                    log(f"ERROR detail {c} seed={seed}:\n{r['error']}")
            while len(fut) < a.slots and time.time() - t0 + a.job_timeout < a.budget_s and submit():
                pass
    inputs.sort()
    (out / "MERGE_INPUTS.txt").write_text("".join(x[2] + "\n" for x in inputs))
    summ = {"ended": now(), "secs": round(time.time() - t0), "distinct_global": len(seen), "cores": len(cores),
            "per_core": {c: dict(st[c]) for c in st}, "jobs": sum(st[c]["done"] for c in st),
            "exhausted_cores": sum(st[c]["exhausted"] for c in st)}
    (out / "SUMMARY.json").write_text(json.dumps(summ, indent=1))
    log(f"END distinct={len(seen)} jobs={summ['jobs']} exhausted_cores={summ['exhausted_cores']}/{len(cores)} secs={summ['secs']}")


if __name__ == "__main__":
    main()

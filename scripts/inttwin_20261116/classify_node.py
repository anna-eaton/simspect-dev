#!/usr/bin/env python3
"""classify_node.py (agent inttwin 2026-11-16) -- brief step 4 on one node: classify every finished inttwin row (both versions) of this
node with the existing methods, unattended. Runs from the code root inside gem5_dev; loops until every row of the node is done.
A row starts when every shard of BOTH its versions has a logs/q/<shard>.DONE (and, for race rows, its delay-1 control row is done).
Per row -> /tests/inttwin_20261116/cls/<row>/ :
  gate      STAGE3_gem5/bugs/classify.py gate over both versions (campaigns json with the explicit "stt" flag; --fraction = the config's
            sample_fraction; --examples 1000000 so the json lists every stem) -> gate.json, gate.stdout
  race rows merged view results/<rn>_merged/<mode>/_sweep_raw (symlinks to every shard's raw json; duplicates reported), then
            scripts/bigcorpus_20261115/race_scan.py <merged> [--control <same build, same version, delay 1>] -> race_<ver>.json/.txt
  ReCon rows (E2w, E2, E6, E2wstl) = the E2w method (scripts/bigcorpus_20261115/e2w_bucket.sh) with the integer version AS the GPR twin
            (every pair is faithful, so TWIN_STEMS = all pairs; classify.py itself still sends RMW tests down the no-twin path):
            recon_stlf evidence (STAGE3_gem5/triage/rerun_hits_evidence.py --analyzer recon_stlf --extra-debug Commit, per shard campaign,
            --jobs 2) on the version's gated ld hits whose static class is 'other' or whose twin hit; then classify.py bucket
            --twin <int shards> --twin-stems <all pairs> --stlf <evidence> -> bucket_<ver>.json, per_stem_<ver>.json.
            The INT version is bucketed with itself as twin (it has no FPR routes to remove).
  STT rows (E3, E4) bucket --stt yes = the gate class (S1_xmm4 = UV1).
Done marker cls/<row>/DONE. Log /tests/inttwin_20261116/logs/classify_<node>.log (+ each tool's stdout in the row dir).
Usage: python3 scripts/inttwin_20261116/classify_node.py --node cafe3 [--rows <row> ...] [--once]
"""
import argparse, glob, json, os, re, subprocess, sys, time
from pathlib import Path

O = Path("/tests/inttwin_20261116"); QD = O / "logs" / "q"; TS = O / "testsets"
RECON_ROWS = ("E2w_", "E2_", "E6_", "E2wstl_")


def load(p):
    return json.loads(re.sub(r"//[^\n]*", "", Path(p).read_text()))


def sh(cmd, out, log):
    t0 = time.time(); log(f"RUN {cmd} > {out}")
    with open(out, "w") as f:
        rc = subprocess.call(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    log(f"rc={rc} ({int(time.time() - t0)} s) {out}")
    return rc


def shards_done(rn, q):
    items = [i for i in q if i["campaign"] == rn]
    return bool(items) and all((QD / f"{i['name']}.DONE").exists() for i in items), items


def merged(rn, modes, log):
    out = Path(f"results/{rn}_merged")
    for m in modes:
        od = out / m / "_sweep_raw"; od.mkdir(parents=True, exist_ok=True)
        for f in od.glob("*"):
            f.unlink()
        seen, dup, k = set(), 0, 0
        for camp in sorted(glob.glob(f"results/{rn}_sh*__latest")):
            for f in sorted(glob.glob(f"{camp}/{m}/_sweep_raw/*.json")):
                try:
                    recs = json.load(open(f))
                except Exception as e:
                    log(f"WARN {f} {e}"); continue
                for r in recs:
                    n = r.get("name") if isinstance(r, dict) else None
                    if n:
                        dup += n in seen; seen.add(n)
                k += 1; (od / f"{k:05d}_{Path(camp).name}.json").symlink_to(os.path.realpath(f))
        log(f"merged {rn} {m}: {len(seen)} records from {k} files, duplicates {dup}")
    return out


def hits(rn, kind="ld"):
    """(mode, stem) with issued_in_window over all shards (window-results.json, raw checker verdict)."""
    s = set()
    for d in glob.glob(f"results/{rn}_sh*__latest"):
        for f in glob.glob(os.path.realpath(d) + f"/*/{kind}/window-results.json"):
            m = f.split("/")[-3]; x = json.load(open(f))
            recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
            s |= {(m, r["name"].split("__")[0]) for r in recs if isinstance(r, dict) and r.get("issued_in_window")}
    return s


def classify_row(row, camps, q, log):
    D = O / "cls" / row; D.mkdir(parents=True, exist_ok=True)
    c0 = camps[0]; cfg = load(c0["config"]); frac = cfg["gem5"].get("sample_fraction") or 1.0; modes = cfg["speculation"]["branch_modes"]
    cj = D / "campaigns.json"
    cj.write_text(json.dumps([dict(results_name=c["results_name"], model=c["model"], stt=c["stt"], config=c["config"]) for c in camps], indent=1))
    rc = sh(f"python3 STAGE3_gem5/bugs/classify.py gate --code-root . --campaigns {cj} --testsets-root {TS} --fraction {frac} --examples 1000000 --json {D}/gate.json",
            D / "gate.stdout", log)
    if rc:
        return False
    G = json.load(open(D / "gate.json"))["campaigns"]
    byver = {c["version"]: c for c in camps}
    if c0["kind"] == "race":
        for v, c in byver.items():
            mv = merged(c["results_name"], modes, log)
            ctl = re.sub(r"_d\d_", "_d1_", c["results_name"])
            x = f"--control results/{ctl}_merged" if ctl != c["results_name"] and Path(f"results/{ctl}_merged").exists() else ""
            sh(f"python3 scripts/bigcorpus_20261115/race_scan.py {mv} {x} --examples 1000000 --json {D}/race_{v}.json", D / f"race_{v}.txt", log)
            # per-stem gate classes too (bucket --stt yes returns the gate class unchanged; no twin chain on race rows)
            sh(f"python3 STAGE3_gem5/bugs/classify.py bucket --row {c['results_name']} --gate {D}/gate.json --stt yes "
               f"--json {D}/bucket_{v}.json --per-stem {D}/per_stem_{v}.json --examples 1000000", D / f"bucket_{v}.stdout", log)
    elif row.startswith(RECON_ROWS):
        twin_rn = byver["int"]["results_name"]
        tw_dirs = " ".join(sorted(glob.glob(f"results/{twin_rn}_sh*__latest")))
        pairs = TS / byver["int"]["model"] / "FPR_PAIRS.tsv"
        twin_ld = hits(twin_rn, "ld")
        for v, c in byver.items():
            rn = c["results_name"]; g = G.get(rn, {}); keys = set()
            for k, e in g.items():
                if k.endswith("_merge") or "/ld/" not in k:
                    continue
                m = k.split("/")[0]
                for cl, ex in e.get("examples", {}).items():
                    if cl.startswith("disq"):
                        continue
                    for s in ex:
                        if cl.startswith("other") or (m, s) in twin_ld:
                            keys.add(f"{m}/{s}")
            kf = D / f"evidence_keys_{v}.txt"; kf.write_text("".join(k + "\n" for k in sorted(keys)))
            log(f"{rn}: {len(keys)} evidence keys")
            par = D / f"par_{v}"; par.mkdir(exist_ok=True); procs = []
            for i, d in enumerate(sorted(glob.glob(f"results/{rn}_sh*__latest"))):
                if not keys:
                    break
                n = Path(d).name; w = f"/tmp/inttwin_ev_{row}_{v}_{i}"
                cmd = (f"mkdir -p {w}; timeout 14400 nice -n 5 python3 STAGE3_gem5/triage/rerun_hits_evidence.py --campaign {os.path.realpath(d)} "
                       f"--testset-src {TS / c['model']} --code . --work {w} --analyzer recon_stlf --out {par}/{n}.json --kinds ld --keys-file {kf} "
                       f"--batch 64 --jobs 2 --extra-debug Commit > {par}/{n}.log 2>&1; rm -rf {w}")
                procs.append(subprocess.Popen(cmd, shell=True))
                while sum(p.poll() is None for p in procs) >= 14:
                    time.sleep(10)
            for p in procs:
                p.wait()
            ev = {}
            for f in glob.glob(f"{par}/*.json"):
                try:
                    for k, x in json.load(open(f)).items():
                        ev.setdefault(k, x)
                except Exception as e:
                    log(f"WARN evidence {f} {e}")
            json.dump(ev, open(D / f"recon_stlf_{v}.json", "w"), indent=1); log(f"{rn}: evidence for {len(ev)} keys")
            sh(f"python3 STAGE3_gem5/bugs/classify.py bucket --row {rn} --gate {D}/gate.json --twin {tw_dirs} --twin-stems {pairs} "
               f"--stlf {D}/recon_stlf_{v}.json --json {D}/bucket_{v}.json --per-stem {D}/per_stem_{v}.json --examples 1000000", D / f"bucket_{v}.stdout", log)
    else:
        for v, c in byver.items():
            sh(f"python3 STAGE3_gem5/bugs/classify.py bucket --row {c['results_name']} --gate {D}/gate.json --stt {'yes' if c['stt'] else 'no'} "
               f"--json {D}/bucket_{v}.json --per-stem {D}/per_stem_{v}.json --examples 1000000", D / f"bucket_{v}.stdout", log)
    (D / "DONE").write_text(time.strftime("%F %T", time.gmtime()) + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--rows", nargs="*"); ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    L = open(O / "logs" / f"classify_{a.node}.log", "a", buffering=1)
    log = lambda s: L.write(f"[{time.strftime('%F %T', time.gmtime())}] {s}\n")
    allc = [c for c in json.load(open("runconfigs/inttwin_20261116/campaigns.json")) if c["node"] == a.node]
    rows = {}
    for c in allc:
        rows.setdefault(c["row"], []).append(c)
    if a.rows:
        rows = {r: v for r, v in rows.items() if r in a.rows}
    # delay-1 controls first
    order = sorted(rows, key=lambda r: (0 if "_d1_" in r else 1, r))
    log(f"START classify_node pid {os.getpid()} rows {order}")
    while True:
        q = json.load(open(O / f"queue_{a.node}.json"))
        left = [r for r in order if not (O / "cls" / r / "DONE").exists()]
        if not left:
            log("ALL ROWS DONE"); break
        for r in left:
            ok = all(shards_done(c["results_name"], q)[0] for c in rows[r])
            if "_d" in r and re.search(r"_d[34]_", r):
                ok = ok and (O / "cls" / re.sub(r"_d\d_", "_d1_", r) / "DONE").exists()
            if ok:
                try:
                    classify_row(r, rows[r], q, log)
                except Exception as e:
                    import traceback; log(f"ERROR {r}: {e}\n{traceback.format_exc()}")
                    (O / "cls" / r).mkdir(parents=True, exist_ok=True); (O / "cls" / r / "ERROR").write_text(traceback.format_exc())
                    (O / "cls" / r / "DONE").write_text("error\n")
        if a.once:
            break
        time.sleep(120)


if __name__ == "__main__":
    main()

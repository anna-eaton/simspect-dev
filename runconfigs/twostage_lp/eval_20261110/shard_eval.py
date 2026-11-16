#!/usr/bin/env python3
"""shard_eval.py -- run the rest of one eval row's sample as K independent testrun.py processes over disjoint stem shards
(regen-lp, 2026-11-10). Orchestration only: the checker, gem5_common and testrun.py are unchanged.

Why: check_*.py run process_one in a Python thread pool, so one campaign is GIL-bound (~1 core of Python per batch).
K processes over disjoint shards run K-way parallel.

For row <name> (campaigns.json): the stems still to run in each mode = sample_keep(stem, --fraction) over the corpus,
minus every stem that already has a record in results/<name>__latest (the main campaign) or in an earlier shard run.
They are dealt round-robin (sorted) into K shards. Shard k gets
  testsets_twostage/<corpus>__<row>_sh<k>/<mode>/{asm,ann}/   symlinks to the corpus files (+ xml symlink)
  runconfigs/twostage_lp/eval_20261110/shards/<name>_sh<k>.jsonc   = the row config with ONLY paths.results_name
                                                                     (<name>_sh<k>), gem5.jobs (--jobs) changed and
                                                                     gem5.sample_fraction removed (the shard IS the sample)
  SHARD_STEMS.tsv (mode, stem) in the shard testset, and one tmux window <name>_sh<k> in session regenlp_eval running
  `testrun.py --once --max-new 100000` (log <loosepin_regen>/logs/eval_<name>_sh<k>.log).
Merge: eval_gate.py / eval_summary.py read results/<name>__latest plus every results/<name>_sh*__latest and fail on a
stem that appears in two runs (duplicate) -- see eval_gate.py --merge-shards.
Usage (code root, gem5_dev): shard_eval.py --name E3_STT_6_u_core_lpP_fv3 --k 4 --jobs 4 [--fraction 0.1] [--dry]
"""
import argparse, glob, json, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, "STAGE3_gem5")
from gem5_common import sample_keep

TS = Path("/tests/simspect_alloy_20261108/testsets_twostage"); LOGS = Path("/tests/simspect_alloy_20261108/loosepin_regen/logs")
MODES = ("mispredict_not_taken", "mispredict_taken")


def done_stems(name):
    out = {m: set() for m in MODES}
    for d in [f"results/{name}__latest"] + sorted(glob.glob(f"results/{name}_sh*__latest")):
        d = os.path.realpath(d)
        for m in MODES:
            for f in glob.glob(f"{d}/{m}/*/window-results.json"):
                x = json.load(open(f)); recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
                out[m] |= {r["name"].split("__")[0] for r in recs if isinstance(r, dict)}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--name", required=True); ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--fraction", type=float, default=0.1); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--wave", default="", help="label of this sharding wave, part of every shard name (e.g. 25 -> _sh25_<k>); "
                    "required after the first wave so names never collide with an earlier wave")
    a = ap.parse_args()
    camp = next(c for c in json.load(open("runconfigs/twostage_lp/eval_20261110/campaigns.json")) if c["results_name"] == a.name)
    corpus = TS / camp["model"]; row = a.name.split("_")[0]
    src = open(camp["config"]).read(); cfg = json.loads(re.sub(r"//[^\n]*", "", src))
    done = done_stems(a.name)
    todo = {m: sorted(f[:-9] for f in os.listdir(corpus / m / "ann") if sample_keep(f[:-9], a.fraction) and f[:-9] not in done[m]) for m in MODES}
    print({m: (len(done[m]), len(todo[m])) for m in MODES}, "(done, todo) per mode")
    shdir = Path("runconfigs/twostage_lp/eval_20261110/shards"); shdir.mkdir(exist_ok=True)
    tag = f"sh{a.wave}_" if a.wave else "sh"
    if a.dry:
        for k in range(a.k):
            print(f"shard {k}: {sum(len(todo[m][k::a.k]) for m in MODES)} tests -> {camp['model']}__{row}_{tag}{k} (dry: nothing written)")
        return
    for k in range(a.k):
        tsn = f"{camp['model']}__{row}_{tag}{k}"; t = TS / tsn
        if t.exists() or glob.glob(f"results/{a.name}_{tag}{k}__*"):
            sys.exit(f"shard_eval: {tsn} or results/{a.name}_{tag}{k} exists; pick a new --wave")
        rows = []
        for m in MODES:
            for d in ("asm", "ann"):
                (t / m / d).mkdir(parents=True, exist_ok=True)
            for s in todo[m][k::a.k]:
                for d, e in (("asm", ".s"), ("ann", ".ann.json")):
                    dst = t / m / d / f"{s}{e}"
                    if not dst.exists():
                        os.symlink(corpus / m / d / f"{s}{e}", dst)
                rows.append(f"{m}\t{s}")
        if not (t / "xml").exists():
            os.symlink(corpus / "xml", t / "xml")
        (t / "SHARD_STEMS.tsv").write_text("mode\tstem\n" + "".join(r + "\n" for r in rows))
        c = json.loads(json.dumps(cfg)); c["paths"]["results_name"] = f"{a.name}_{tag}{k}"; c["gem5"]["jobs"] = a.jobs
        c["gem5"].pop("sample_fraction", None)
        p = shdir / f"{a.name}_{tag}{k}.jsonc"
        p.write_text(f"// shard {k}/{a.k} of {a.name} (shard_eval.py): {camp['config']} with ONLY paths.results_name, gem5.jobs {a.jobs} and "
                     f"no sample_fraction; testset {tsn} = {len(rows)} (mode, stem) of the remaining sample_keep({a.fraction}) set\n" + json.dumps(c, indent=2) + "\n")
        win = f"{a.name}_{tag}{k}"
        cmd = (f"cd {os.getcwd()} && export TMPDIR=/tmp && python3 -u testrun.py --config {p} --model {tsn} --once --max-new 100000 "
               f">> {LOGS}/eval_{win}.log 2>&1; echo EXIT rc=$? >> {LOGS}/eval_{win}.log")
        print(f"shard {k}: {len(rows)} tests -> {tsn}")
        if True:
            subprocess.run(["tmux", "new-window", "-d", "-t", "regenlp_eval", "-n", win, cmd], check=True)
            with open(LOGS / "launch_eval.log", "a") as f:
                f.write(f"{__import__('datetime').datetime.utcnow():%F %T} LAUNCH {win} {p} model={tsn} tests={len(rows)}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""prep_queue.py (agent inttwin 2026-11-16) -- turn this node's campaigns (runconfigs/inttwin_20261116/campaigns.json, node == --node)
into disjoint stem shards + queue items for run_queue.py (testrun is GIL-bound; same idea as scripts/bigcorpus_20261115/shard_rows.py).
Only campaigns whose corpus is READY (twin READY marker / FPR wrapper present) are queued; re-running is idempotent (adds new items only).
Stems = the corpus's (mode, stem) tests kept by gem5_common.sample_keep(stem, gem5.sample_fraction) (the same rule testrun applies),
sorted and dealt round-robin into K = ceil(tests / --per-shard) shards. Shard s of campaign <rn>: testset
/tests/inttwin_20261116/testsets/<model>__<rn>_sh<s>/<mode>/{asm,ann} (symlinks) + xml link + READY; config
/tests/inttwin_20261116/cfg/shards/<rn>_sh<s>.jsonc = the campaign config with ONLY paths.results_name (<rn>_sh<s>) and gem5.jobs (--jobs)
changed. Queue file /tests/inttwin_20261116/queue_<node>.json (list; FPR and INT shards of a row interleaved so both versions advance
together). Run from the code root: python3 scripts/inttwin_20261116/prep_queue.py --node cafe3 [--per-shard 1200] [--jobs 4] [--only <rn> ...]
"""
import argparse, json, math, os, re, sys
from pathlib import Path

O = Path("/tests/inttwin_20261116"); TS = O / "testsets"
sys.path.insert(0, "STAGE3_gem5")
from gem5_common import sample_keep  # noqa: E402


def load(p):
    return json.loads(re.sub(r"//[^\n]*", "", Path(p).read_text()))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--per-shard", type=int, default=1200)
    ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--only", nargs="*"); a = ap.parse_args()
    camps = [c for c in json.load(open("runconfigs/inttwin_20261116/campaigns.json")) if c["node"] == a.node and (not a.only or c["results_name"] in a.only)]
    qf = O / f"queue_{a.node}.json"; q = json.load(open(qf)) if qf.exists() else []
    have = {i["name"] for i in q}; (O / "cfg" / "shards").mkdir(parents=True, exist_ok=True)
    rows = {}
    for c in camps:
        corp = TS / c["model"]
        ready = (corp / "READY").exists() if c["version"] == "int" else (corp / "MANIFEST.tsv").exists()
        if not ready:
            print(f"skip {c['results_name']}: corpus {corp} not ready"); continue
        cfg = load(c["config"]); frac = cfg["gem5"].get("sample_fraction") or 1.0; modes = cfg["speculation"]["branch_modes"]
        tests = [(m, f[:-9]) for m in modes for f in sorted(os.listdir(corp / m / "ann")) if f.endswith(".ann.json") and (frac >= 1 or sample_keep(f[:-9], frac))]
        k = max(1, math.ceil(len(tests) / a.per_shard)); rn = c["results_name"]; items = []
        for s in range(k):
            name = f"{rn}_sh{s}"
            if name in have:
                continue
            mine = tests[s::k]; d = TS / f"{c['model']}__{name}"
            for m, st in mine:
                for sub, ext in (("asm", ".s"), ("ann", ".ann.json")):
                    (d / m / sub).mkdir(parents=True, exist_ok=True); l = d / m / sub / f"{st}{ext}"
                    if not l.exists():
                        l.symlink_to(corp / m / sub / f"{st}{ext}")
            for m in modes:
                for sub in ("asm", "ann"):
                    (d / m / sub).mkdir(parents=True, exist_ok=True)
            if not (d / "xml").exists():
                (d / "xml").symlink_to(corp / "xml")
            (d / "SHARD_TESTS.tsv").write_text("mode\tstem\n" + "".join(f"{m}\t{st}\n" for m, st in mine)); (d / "READY").touch()
            t = Path(c["config"]).read_text()
            t, n1 = re.subn(r'("results_name"\s*:\s*)"[^"]*"', rf'\1"{name}"', t, count=1)
            t, n2 = re.subn(r'("jobs"\s*:\s*)\d+', rf'\g<1>{a.jobs}', t, count=1)
            assert n1 == 1 and n2 == 1
            cp = O / "cfg" / "shards" / f"{name}.jsonc"
            cp.write_text(f"// prep_queue.py: shard {s}/{k} ({len(mine)} tests) of {c['config']}; ONLY paths.results_name and gem5.jobs changed\n" + t)
            items.append(dict(name=name, campaign=rn, row=c["row"], version=c["version"], cfg=str(cp), model=d.name, tests=len(mine),
                              delay=c.get("commitToIEWDelay"), kind=c["kind"]))
        rows.setdefault(c["row"], []).append(items)
        print(f"{rn}: {len(tests)} tests (frac {frac}) -> {k} shards, {len(items)} new items")
    new = []
    for row, lists in rows.items():   # interleave fpr/int shards of a row
        for i in range(max((len(x) for x in lists), default=0)):
            new += [x[i] for x in lists if i < len(x)]
    q += new; qf.write_text(json.dumps(q, indent=0)); print(f"queue {qf}: {len(q)} items ({len(new)} new)")


if __name__ == "__main__":
    main()

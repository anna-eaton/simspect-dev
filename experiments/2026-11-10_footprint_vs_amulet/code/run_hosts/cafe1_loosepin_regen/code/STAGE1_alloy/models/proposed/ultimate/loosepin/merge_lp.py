#!/usr/bin/env python3
"""merge_lp.py -- merge several loose-pin draft corpora into ONE family corpus with fingerprint dedup (regen-lp, 2026-11-10).

Anna's LP-1 (2026-11-10): run `_lpP` and `_lpA_b2` together, merge them and deduplicate by fingerprint into one corpus
per family. Each input is an xml dir written by alloy_solver_order.py (pipeline.py xml with alloy.solver_order), i.e.
inst-*.xml + _dedup_map.jsonl (name, seed, source, fp) + SOLVER_ORDER.json. The fingerprint is the one already in
_dedup_map.jsonl (alloy_solver_order's rule = merge_stage15's: find_duplicates.canonicalize + xm flags), so within-draft
cross-seed dedup and cross-draft dedup use the same key. Inputs are taken in the order given; within one input, in its
own numbering; an instance whose fingerprint was already kept is dropped. Output numbering is deterministic.

Writes (out dir, refuses if it already has inst-*.xml):
  inst-NNNNNN.xml/.txt   copies (atomic rename, .xml last)
  _merge_map.jsonl       name, draft, draft_inst, seed, seed_source, fp
  _merge_dups.jsonl      draft, draft_inst, seed, fp, duplicate_of
  SOLVER_ORDER.json      family, dedup rule, per draft: model path + sha256, solver_order config (seeds, walk_p,
                         timeout), cap/seed, per-seed {instances, kept_new, duplicates, verdict, secs}, kept, then the
                         merge counts (kept per draft, cross-draft duplicates, total)
  _merge.log             start/end, counts, every error
Usage: merge_lp.py --family Footprint_6_u --out <dir>/xml [--inputs-file A.txt,B.txt] [<xml dir> ...]
"""
import argparse, datetime as dt, json, os, shutil, sys, traceback
from pathlib import Path


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--inputs-file", help="file with one input xml dir per line (e.g. stage15lp.py's MERGE_INPUTS.txt); "
                    "several files may be given comma-separated, taken in that order, before any positional inputs")
    ap.add_argument("inputs", nargs="*")
    a = ap.parse_args()
    pre = []
    for f in (a.inputs_file.split(",") if a.inputs_file else []):
        pre += [l.strip() for l in Path(f).read_text().splitlines() if l.strip()]
    a.inputs = pre + a.inputs
    if not a.inputs:
        sys.exit("merge_lp: no inputs")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if any(out.glob("inst-*.xml")):
        sys.exit(f"merge_lp: {out} already has inst-*.xml")
    logf = open(out / "_merge.log", "a", buffering=1)
    log = lambda m: (logf.write(f"{now()} {m}\n"), print(m, flush=True))
    log(f"START family={a.family} inputs={len(a.inputs)} (first {a.inputs[:3]})")
    rec = {"family": a.family, "started": now(), "host": os.uname().nodename, "inputs": [], "dedup_rule": None}
    seen, n, ndup = {}, 0, 0
    mm, md = open(out / "_merge_map.jsonl", "w"), open(out / "_merge_dups.jsonl", "w")
    try:
        for inp in map(Path, a.inputs):
            so = json.loads((inp / "SOLVER_ORDER.json").read_text())
            rec["dedup_rule"] = rec["dedup_rule"] or so.get("dedup_rule")
            if so.get("dedup_rule") != rec["dedup_rule"]:
                raise RuntimeError(f"{inp}: different dedup rule")
            draft = Path(so["model"]).stem
            rows = [json.loads(l) for l in (inp / "_dedup_map.jsonl").read_text().splitlines() if l.strip()]
            kept = dups = 0
            for r in rows:
                src = inp / r["name"]
                if not src.exists():
                    raise RuntimeError(f"{src} listed in _dedup_map.jsonl but missing")
                if r["fp"] in seen:
                    dups += 1
                    md.write(json.dumps({"input": str(inp), "draft": draft, "draft_inst": r["name"], "seed": r["seed"], "fp": r["fp"],
                                         "duplicate_of": seen[r["fp"]]}) + "\n")
                    continue
                n += 1; name = f"inst-{n:06d}"; seen[r["fp"]] = name; kept += 1
                for ext in (".txt", ".xml"):
                    s = src.with_suffix(ext)
                    if s.exists():
                        tmp = out / f".tmp-{name}{ext}"; shutil.copyfile(s, tmp); os.replace(tmp, out / f"{name}{ext}")
                mm.write(json.dumps({"name": name + ".xml", "input": str(inp), "draft": draft, "draft_inst": r["name"], "seed": r["seed"],
                                     "seed_source": r.get("source"), "fp": r["fp"]}) + "\n")
            ndup += dups
            seeds = [{k: s.get(k) for k in ("seed", "instances", "kept_new", "duplicates", "parse_errors", "verdict", "secs")}
                     for s in so["seeds"]]
            rec["inputs"].append({"draft": draft, "xml_dir": str(inp), "model": so["model"], "model_sha256": so["model_sha256"],
                                  "alloy_jar_sha256": so.get("alloy_jar_sha256"),
                                  "a6RandomModels_java_sha256": so.get("a6RandomModels_java_sha256"),
                                  "solver_order": so["solver_order"], "cap_per_seed": so["cap_per_seed"],
                                  "draft_started": so.get("started"), "draft_ended": so.get("ended"),
                                  "draft_kept": so.get("kept_total"), "draft_cross_seed_duplicates": so.get("duplicates_total"),
                                  "per_seed": seeds, "merged_kept": kept, "merged_cross_draft_duplicates": dups})
            log(f"input {inp}: {len(rows)} distinct in draft, kept {kept}, cross-draft duplicates {dups}")
    except Exception:
        log(f"EXCEPTION\n{traceback.format_exc()}"); rec["error"] = traceback.format_exc(); raise
    finally:
        mm.close(); md.close()
        rec.update(kept_total=n, cross_draft_duplicates_total=ndup, ended=now())
        (out / "SOLVER_ORDER.json").write_text(json.dumps(rec, indent=2))
        log(f"END kept_total={n} cross_draft_duplicates={ndup}")


if __name__ == "__main__":
    main()

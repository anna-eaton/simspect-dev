#!/usr/bin/env python3
"""alloy_solver_order.py — seeded random SAT4J order for the XML phase, with cross-seed dedup (loosepin, 2026-11-09).

Used by pipeline.phase_xml (and so by testsetgen.py) ONLY when the run config sets

    "alloy": {
      "max_instances": 10000,                 // cap PER SEED run
      "solver_order": {
        "mode": "random",                     // "default" or absent = the old a6CountModels path, byte-identical
        "seeds": [1, 2, 3],                   // ints = a6RandomModels seeds; the string "default" = a6CountModels
        "walk_p": 0.05,                       // random-walk probability (a6RandomModels arg 5)
        "parallel": false,                    // true: run all seeds at once, merge in seed order at the end
        "timeout_s": 0,                       // per-seed wall-clock limit, 0 = none
        "xmx": null,                          // e.g. "4g" -> java -Xmx4g (null = JVM default, as the old path)
        "keep_raw": false                     // keep xml/_seeds/<seed>/ after ingest (default: delete it)
      }
    }

What it does. Each seed is enumerated into xml/_seeds/<seed>/ by a6RandomModels (same translation, same formula,
same sol.next() blocking as a6CountModels; only the SAT search order changes, so every instance is a model instance
and a seed that ends below its cap is exhaustive). Instances are ingested as they land (inst-k is complete once
inst-k.txt exists, a6*Models writes the .txt after the .xml): each is fingerprinted and, if its fingerprint is new,
copied (atomic rename) to xml/inst-NNNNNN.xml + .txt with the next number. Sequential mode therefore still streams
into testsetgen's llvm/asm drain. Numbering is deterministic in (model, seeds order, walk_p, cap).

Dedup rule = merge_stage15.py's: STAGE2_compilation/find_duplicates.py:canonicalize(pass1(xml), xml) plus each
instruction's xm flag, sha256 of its repr.

Records (all in xml/):
  SOLVER_ORDER.json      model path + sha256, alloy jar sha256, a6RandomModels.java sha256, the solver_order config,
                         cap, per-seed {instances, kept_new, duplicates, parse_errors, verdict, secs, cmd}, totals,
                         dedup rule, started/ended.
  _dedup_map.jsonl       one row per kept instance: name, seed, source inst, fingerprint.
  _dedup_dups.jsonl      one row per dropped instance: seed, source inst, fingerprint, duplicate_of.
  _solver_order.log      timestamped start/end, every command, every error (stderr tail, traceback).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Callable, Optional

DEDUP_RULE = ("sha256(repr((find_duplicates.canonicalize(pass1_specify_state_a(x), x), "
              "tuple(bool(r.get('xm')) for r in pass1.instructions))))  (= merge_stage15.py)")
DEFAULTS = {"seeds": [1, 2, 3], "walk_p": 0.05, "parallel": False, "timeout_s": 0, "xmx": None, "keep_raw": False}


def configured(cfg: dict) -> Optional[dict]:
    """Normalized solver_order config, or None when the run uses the default (unchanged) path."""
    so = (cfg.get("alloy") or {}).get("solver_order")
    if so is None:
        return None
    if not isinstance(so, dict):
        raise ValueError("alloy.solver_order must be an object")
    mode = so.get("mode", "default")
    if mode == "default":
        return None
    if mode != "random":
        raise ValueError(f"alloy.solver_order.mode must be 'default' or 'random', got {mode!r}")
    unknown = set(so) - set(DEFAULTS) - {"mode"}
    if unknown:
        raise ValueError(f"alloy.solver_order: unknown keys {sorted(unknown)}")
    out = dict(DEFAULTS, **{k: v for k, v in so.items() if k != "mode"})
    seeds = out["seeds"]
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("alloy.solver_order.seeds must be a non-empty list")
    for s in seeds:
        if not (s == "default" or (isinstance(s, int) and not isinstance(s, bool))):
            raise ValueError(f"alloy.solver_order.seeds: {s!r} is not an int or 'default'")
    if len(set(map(str, seeds))) != len(seeds):
        raise ValueError("alloy.solver_order.seeds has duplicates")
    p = out["walk_p"]
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0.0 <= float(p) <= 1.0:
        raise ValueError("alloy.solver_order.walk_p must be a number in [0, 1]")
    out["walk_p"] = float(p)
    out["mode"] = "random"
    return out


def _sha(p: Path) -> Optional[str]:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def make_fingerprinter(stage2_dir: Path) -> Callable[[Path], str]:
    """merge_stage15.py's fingerprint, imported from the repo's Stage-2 code (read-only use)."""
    sys.path.insert(0, str(stage2_dir))
    from parsexml import parse_alloy_xml, pass1_specify_state_a  # noqa: E402
    from find_duplicates import canonicalize  # noqa: E402

    def fp(path: Path) -> str:
        inst = parse_alloy_xml(Path(path).read_text(encoding="utf-8"))
        r1 = pass1_specify_state_a(inst, write_out=False)
        key = (canonicalize(r1, inst), tuple(bool(r.get("xm")) for r in r1["instructions"]))
        return hashlib.sha256(repr(key).encode()).hexdigest()
    return fp


def ensure_random_class(alloy_stage: Path, log: Callable[[str], None]) -> None:
    """Compile STAGE1_alloy/a6RandomModels.java if the .class is missing or older than the source."""
    src, cls = alloy_stage / "a6RandomModels.java", alloy_stage / "a6RandomModels.class"
    if not src.exists():
        raise FileNotFoundError(f"{src} not found")
    if cls.exists() and cls.stat().st_mtime >= src.stat().st_mtime:
        return
    cmd = ["javac", "-cp", "alloy6.jar:.", "a6RandomModels.java"]
    log(f"COMPILE $ {' '.join(cmd)} (cwd {alloy_stage})")
    r = subprocess.run(cmd, cwd=str(alloy_stage), capture_output=True, text=True)
    if r.returncode != 0:
        log(f"COMPILE ERROR rc={r.returncode}\n{r.stderr[-4000:]}")
        raise RuntimeError("javac a6RandomModels.java failed")


def java_cmd(seed, model_file: Path, out_dir: Path, cap: int, so: dict) -> list:
    xmx = [f"-Xmx{so['xmx']}"] if so.get("xmx") else []
    if seed == "default":
        return ["java", *xmx, "-cp", "alloy6.jar:.", "a6CountModels", str(model_file), str(out_dir), str(cap)]
    return ["java", *xmx, "-cp", "alloy6.jar:.", "a6RandomModels", str(model_file), str(out_dir), str(cap),
            str(seed), repr(so["walk_p"])]


class _Merger:
    """Cross-seed dedup + renumbering into xml_dir (state lives in memory; outputs are append-only files)."""

    def __init__(self, xml_dir: Path, fingerprint: Callable[[Path], str], log: Callable[[str], None]):
        self.xml_dir, self.fingerprint, self.log = xml_dir, fingerprint, log
        self.seen: dict = {}
        self.n = 0
        self.mm = open(xml_dir / "_dedup_map.jsonl", "a", buffering=1)
        self.md = open(xml_dir / "_dedup_dups.jsonl", "a", buffering=1)

    def ingest(self, seed, src_xml: Path, stats: dict) -> None:
        try:
            fp = self.fingerprint(src_xml)
        except Exception:
            stats["parse_errors"] += 1
            self.log(f"PARSE_ERROR seed={seed} {src_xml.name}\n{traceback.format_exc()}")
            return
        stats["instances_ingested"] += 1
        if fp in self.seen:
            stats["duplicates"] += 1
            self.md.write(json.dumps({"seed": seed, "source": src_xml.name, "fp": fp, "duplicate_of": self.seen[fp]}) + "\n")
            return
        self.n += 1
        name = f"inst-{self.n:06d}"
        self.seen[fp] = name
        txt = src_xml.with_suffix(".txt")
        for src, ext in ((txt, ".txt"), (src_xml, ".xml")):   # .xml last: consumers glob inst-*.xml
            if src.exists():
                tmp = self.xml_dir / f".tmp-{name}{ext}"
                shutil.copyfile(src, tmp)
                os.replace(tmp, self.xml_dir / f"{name}{ext}")
        stats["kept_new"] += 1
        self.mm.write(json.dumps({"name": name + ".xml", "seed": seed, "source": src_xml.name, "fp": fp}) + "\n")

    def close(self):
        self.mm.close(); self.md.close()


def _complete(seed_dir: Path, done: set, final: bool) -> list:
    """inst-k.xml files ready to ingest, in k order (inst-k.txt exists, or the JVM has exited)."""
    out = []
    for x in sorted(seed_dir.glob("inst-*.xml")):
        if x.name in done:
            continue
        if final or x.with_suffix(".txt").exists():
            out.append(x)
    return out


def run_random_xml(cfg: dict, so: dict, model_file: Path, xml_dir: Path, alloy_stage: Path, stage2_dir: Path,
                   cap: int, fingerprint: Optional[Callable[[Path], str]] = None,
                   cmd_fn: Callable = java_cmd, poll_s: float = 2.0) -> dict:
    """Enumerate every seed, dedup across seeds into xml_dir. Returns the SOLVER_ORDER.json record."""
    xml_dir.mkdir(parents=True, exist_ok=True)
    if any(xml_dir.glob("inst-*.xml")):
        raise RuntimeError(f"{xml_dir} already has inst-*.xml; phase_xml clears it first (use --force)")
    for stale in ("_dedup_map.jsonl", "_dedup_dups.jsonl", "SOLVER_ORDER.json"):
        (xml_dir / stale).unlink(missing_ok=True)
    logf = open(xml_dir / "_solver_order.log", "a", buffering=1)

    def log(msg: str) -> None:
        logf.write(f"{_now()} {msg}\n")
        print(f"[xml/solver_order] {msg.splitlines()[0]}", flush=True)

    rec = {"started": _now(), "host": os.uname().nodename, "model": str(model_file), "model_sha256": _sha(model_file),
           "alloy_jar_sha256": _sha(alloy_stage / "alloy6.jar"),
           "a6RandomModels_java_sha256": _sha(alloy_stage / "a6RandomModels.java"),
           "solver_order": so, "cap_per_seed": cap, "dedup_rule": DEDUP_RULE, "seeds": []}
    log(f"START model={model_file} sha256={rec['model_sha256']} seeds={so['seeds']} walk_p={so['walk_p']} "
        f"cap/seed={cap} parallel={so['parallel']} timeout_s={so['timeout_s']}")
    merger = None
    try:
        if any(s != "default" for s in so["seeds"]) and cmd_fn is java_cmd:
            ensure_random_class(alloy_stage, log)
        fingerprint = fingerprint or make_fingerprinter(stage2_dir)
        merger = _Merger(xml_dir, fingerprint, log)
        seeds_root = xml_dir / "_seeds"

        def start(seed):
            d = seeds_root / str(seed)
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
            cmd = cmd_fn(seed, model_file, d, cap, so)
            log(f"RUN seed={seed} $ {' '.join(cmd)}")
            so_f, se_f = open(d / "_java_stdout.txt", "w"), open(d / "_java_stderr.txt", "w")
            p = subprocess.Popen(cmd, cwd=str(alloy_stage), stdout=so_f, stderr=se_f)
            return dict(seed=seed, dir=d, cmd=cmd, proc=p, t0=time.time(), files=(so_f, se_f), done=set(),
                        stats=dict(seed=seed, instances_ingested=0, kept_new=0, duplicates=0, parse_errors=0))

        def finish(r, stream: bool):
            p = r["proc"]
            timed_out = False
            while True:
                try:
                    rc = p.wait(timeout=poll_s)
                    break
                except subprocess.TimeoutExpired:
                    if so["timeout_s"] and time.time() - r["t0"] > so["timeout_s"]:
                        p.kill(); rc = p.wait(); timed_out = True
                        break
                    if stream:
                        for x in _complete(r["dir"], r["done"], False):
                            merger.ingest(r["seed"], x, r["stats"]); r["done"].add(x.name)
            for f in r["files"]:
                f.close()
            for x in _complete(r["dir"], r["done"], not timed_out and rc == 0):   # after a kill/crash: only .txt-complete ones
                merger.ingest(r["seed"], x, r["stats"]); r["done"].add(x.name)
            out = (r["dir"] / "_java_stdout.txt").read_text(errors="replace")
            n = len(r["done"])
            verdict = ("TIMEOUT" if timed_out else "ERROR" if rc != 0 else "CAPPED" if n >= cap
                       else "EXHAUSTED" if "Total models:" in out else "UNKNOWN")
            if verdict in ("ERROR", "UNKNOWN"):
                tail = "\n".join((r["dir"] / "_java_stderr.txt").read_text(errors="replace").splitlines()[-25:])
                log(f"{verdict} seed={r['seed']} rc={rc} stderr tail:\n{tail}")
            st = dict(r["stats"], instances=n, verdict=verdict, rc=rc, secs=round(time.time() - r["t0"], 1),
                      cmd=" ".join(r["cmd"]))
            rec["seeds"].append(st)
            log(f"DONE seed={r['seed']} instances={n} kept_new={st['kept_new']} dups={st['duplicates']} "
                f"parse_errors={st['parse_errors']} verdict={verdict} secs={st['secs']}")
            if not so["keep_raw"]:
                shutil.rmtree(r["dir"], ignore_errors=True)

        if so["parallel"]:
            runs = [start(s) for s in so["seeds"]]
            for r in runs:          # merge strictly in seed order -> deterministic numbering
                finish(r, stream=False)
        else:
            for s in so["seeds"]:
                finish(start(s), stream=True)
        if not so["keep_raw"] and seeds_root.exists() and not any(seeds_root.iterdir()):
            seeds_root.rmdir()
    except Exception:
        log(f"EXCEPTION\n{traceback.format_exc()}")
        rec["error"] = traceback.format_exc()
        raise
    finally:
        if merger:
            merger.close()
        rec["kept_total"] = merger.n if merger else 0
        rec["duplicates_total"] = sum(s.get("duplicates", 0) for s in rec["seeds"])
        rec["ended"] = _now()
        (xml_dir / "SOLVER_ORDER.json").write_text(json.dumps(rec, indent=2))
        log(f"END kept_total={rec['kept_total']} duplicates_total={rec['duplicates_total']}")
        logf.close()
    if any(s["verdict"] in ("ERROR", "UNKNOWN") for s in rec["seeds"]):
        raise RuntimeError("a seed run failed; see xml/_solver_order.log")
    return rec

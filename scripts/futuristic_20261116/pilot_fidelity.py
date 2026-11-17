#!/usr/bin/env python3
"""pilot_fidelity.py (agent invisispec-fut 2026-11-16) -- read-only: did each pilot run behave as its Futuristic graph says?

For every record of a firstdet run (results.jsonl + raw/<mode>/<stem>.json + traces/<mode>/<stem>.pipeview.txt.gz, i.e. a
firstdet_stream.py run with --keep-all-traces) this joins three things:
  graph   the Alloy instance (testset xml/<stem>.xml via parsexml.pass1_specify_state_a): per Alloy pc kind / resolved /
          committed / xm. Sources = unresolved instructions before xm (Futuristic: every one makes xm speculative).
  layout  every Alloy pc's runtime address: the test's .s rebuilt with compile_annotate.build_binary + pc_offsets_from_nm
          (the __litmus_<stem>_pcN labels); checked against .ann.json's xmit addr (addr_ok).
  trace   O3PipeView records by seq (issue / complete / retire) and SimSpect events (LSQ:safe = gem5's own visibility point,
          why=prev_insts_completed on FuturisticSafeInvisibleSpec; L1D/DTLB footprints; expose/validate; ROB:squash).
Per record it reports: category (branch / nonbranch / mixed); for the transmitter's load micro-op: issue tick, LSQ:safe tick,
issued as a USL (safe > issue), its own footprint events and whether they precede safe; for each source: completion tick and
whether it was still incomplete when the transmitter issued; whether every model-RESOLVED uncommitted older instruction had
completed by then; squash count; and the checker verdict + offending actors (transmitter or other).
Usage (cafe gem5_dev, cwd anywhere): python3 pilot_fidelity.py --run <firstdet dir> --testset <corpus dir> --code <code root>
        --json out.json [--jobs N]
"""
import argparse, collections, gzip, json, shutil, sys, tempfile, traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True)
ap.add_argument("--testset", required=True)
ap.add_argument("--code", required=True)
ap.add_argument("--json", required=True)
ap.add_argument("--jobs", type=int, default=8)
A = ap.parse_args()
CODE = Path(A.code)
for p in (CODE / "STAGE2_compilation", CODE / "STAGE3_gem5"):
    sys.path.insert(0, str(p))


def one(rec):
    import parsexml, compile_annotate as ca, gem5_common as gc
    run, ts = Path(A.run), Path(A.testset)
    mode, stem = rec["mode"], rec["stem"]
    out = dict(mode=mode, stem=stem)
    tmp = Path(tempfile.mkdtemp(prefix="futfid_"))
    try:
        inst = parsexml.parse_alloy_xml((ts / "xml" / f"{stem}.xml").read_text())
        p1 = parsexml.pass1_specify_state_a(inst, out_path=None, write_out=False)
        ins = p1["instructions"]
        xm = [r for r in ins if r.get("xm")][0]
        xpc = xm["pc"]
        srcs = [r for r in ins if r["pc"] < xpc and not r.get("resolved")]
        rold = [r for r in ins if r["pc"] < xpc and r.get("resolved") and not r.get("committed")]
        brs = [r for r in srcs if r["kind"] in ("br_n", "br_x")]   # parsexml._BRANCH_KINDS
        out["category"] = "none" if not srcs else ("branch" if len(brs) == len(srcs) else ("nonbranch" if not brs else "mixed"))
        out["shape"] = " ".join(f"{r['pc']}:{r['kind']}{'!U' if not r.get('resolved') else ''}{'C' if r.get('committed') else ''}"
                                f"{'*X' if r.get('xm') else ''}" for r in ins)
        ann = json.loads((ts / mode / "ann" / f"{stem}.ann.json").read_text())
        binary, base = ca.build_binary(ts / mode / "asm" / f"{stem}.s", tmp)
        offs = ca.pc_offsets_from_nm(binary, stem, base)
        addr = {pc: base + o for pc, o in offs.items()}
        out["addr_ok"] = addr.get(xpc) == ann["xmit"]["addr"]
        rawf = run / "raw" / mode / f"{stem}.json"
        if not rawf.exists():      # timing_driver keeps the raw record only for hits
            out["leak"] = bool(rec.get("hit"))
            out["error"] = "no raw record (not a hit)"
            return out
        raw = json.loads(rawf.read_text())
        # a non-warm cache setup inserts its block before pc0 and re-resolves the annotation (cache_setup.prepare):
        # shift every litmus label by (runtime xmit pc from the raw record - Stage-2 xmit addr); checked against the trace below
        rx = raw.get("xmit_pc")
        delta = (int(rx, 16) - ann["xmit"]["addr"]) if rx else 0
        out["layout_delta"] = delta
        addr = {pc: a_ + delta for pc, a_ in addr.items()}
        out["leak"] = raw.get("leak", raw.get("issued_in_window"))
        out["vp_actor_mode"] = raw.get("actor_mode")
        gz = run / "traces" / mode / f"{stem}.pipeview.txt.gz"
        if not gz.exists():
            out["error"] = "no trace"
            return out
        tr = tmp / "pv.txt"
        with gzip.open(gz, "rb") as f, open(tr, "wb") as g:
            shutil.copyfileobj(f, g)
        pv = gc.parse_pipeview_by_seq(tr)
        evs = gc.parse_simspect_events(tr)
        safe = {}
        for e in evs:
            if e["struct"] == "LSQ" and e["kind"] == "safe" and e["seq"] is not None:
                safe.setdefault(e["seq"], e["tick"])
        expose = {}
        for e in evs:
            if e["kind"] in ("expose", "validate") and e["seq"] is not None:
                expose.setdefault(e["seq"], e["tick"])
        out["n_squash"] = sum(1 for e in evs if e["struct"] == "ROB" and e["kind"] == "squash")
        # transmitter: the load micro-op(s) at its address; the retired instance if any, else the latest
        xa = ann["xmit"]["addr"] + delta
        xr = [r for r in pv.values() if r["pc"] == xa and gc.is_load_micro_op(r.get("disasm", "")) is not False]
        if not xr:
            out["error"] = "xmit not in pipeview"
            return out
        xret = [r for r in xr if r["retire"] > 0]
        x = min(xret, key=lambda r: r["seq"]) if xret else max(xr, key=lambda r: r["seq"])
        xs, xi = x["seq"], x["issue"]
        out["xmit"] = dict(seq=xs, issue=xi, complete=x["complete"], retire=x["retire"], disasm=x.get("disasm", ""),
                           safe=safe.get(xs), expose=expose.get(xs))
        out["xmit_usl_at_issue"] = (safe.get(xs) is None) or safe[xs] > xi
        fp = [e for e in evs if e["seq"] == xs and e["struct"] in ("L1D", "L2", "DIR", "DTLB")
              and e["kind"] in ("fill", "evict", "inv", "coh", "repl_touch")]
        out["xmit_footprints"] = [dict(t=e["tick"], s=e["struct"], k=e["kind"], req=e.get("req")) for e in fp]
        out["xmit_fp_before_safe"] = any(safe.get(xs) is None or e["tick"] < safe[xs] for e in fp)

        def inst_of(pc):
            """latest dynamic instance (all micro-ops) of Alloy pc with seq below the transmitter's"""
            a = addr.get(pc)
            c = sorted((r for r in pv.values() if r["pc"] == a and r["seq"] < xs), key=lambda r: r["seq"])
            if not c:
                return None
            grp = [c[-1]]
            for r in reversed(c[:-1]):
                if r["seq"] == grp[-1]["seq"] - 1:
                    grp.append(r)
                else:
                    break
            return grp

        def done(grp):
            return 0 if any(r["complete"] == 0 for r in grp) else max(r["complete"] for r in grp)

        pcs_in_trace = {r["pc"] for r in pv.values()}
        out["labels_in_trace"] = sum(1 for a_ in addr.values() if a_ in pcs_in_trace)
        out["labels_total"] = len(addr)
        out["sources"] = []
        for r in srcs:
            g = inst_of(r["pc"])
            if g is None:
                out["sources"].append(dict(pc=r["pc"], kind=r["kind"], found=False))
                continue
            ct = done(g)
            out["sources"].append(dict(pc=r["pc"], kind=r["kind"], found=True, complete=ct, issue=min(q["issue"] for q in g),
                                       incomplete_at_xmit_issue=(ct == 0 or ct > xi)))
        found = [s for s in out["sources"] if s["found"]]
        out["all_src_incomplete_at_xmit_issue"] = bool(found) and all(s["incomplete_at_xmit_issue"] for s in found)
        out["any_src_incomplete_at_xmit_issue"] = any(s["incomplete_at_xmit_issue"] for s in found)
        late = []
        for r in rold:
            g = inst_of(r["pc"])
            if g and (done(g) == 0 or done(g) > xi):
                late.append(r["pc"])
        out["resolved_older_incomplete_at_xmit_issue"] = late
        # check_ld rows (STT): the checker's own signal tick; a source still incomplete at it; and whether EVERY older retired
        # instruction had completed by it (branches: their BR resolve_visible tick, i.e. after any resolve hold), in which case
        # the transmitter was already past STT-Futuristic's visibility point (its taint root is older, so also safe).
        sig = raw.get("xmit_signal")
        if sig:
            out.update(xmit_signal=sig, checker_in_window=raw.get("in_window"), issued_in_window=raw.get("issued_in_window"),
                       cache_fate=raw.get("cache_fate"), criteria=raw.get("criteria"))
            for s_ in out["sources"]:
                if s_.get("found"):
                    s_["incomplete_at_signal"] = s_["complete"] == 0 or s_["complete"] > sig
            out["any_src_incomplete_at_signal"] = any(s_.get("incomplete_at_signal") for s_ in out["sources"])
            rv = {}
            for pc_, d_ in gc.parse_branch_events(tr).items():
                for q, dd in d_.items():
                    if "resolve_visible" in dd:
                        rv[q] = dd["resolve_visible"]
            older = [q for q in pv.values() if q["seq"] < xs and q["retire"] > 0]
            eff = lambda q: max(q["complete"], rv.get(q["seq"], 0)) if q["complete"] else 0
            late_ = [q for q in older if eff(q) == 0 or eff(q) > sig]
            out["all_older_complete_at_signal"] = not late_
            out["older_incomplete_at_signal"] = [dict(seq=q["seq"], pc=hex(q["pc"]), disasm=q.get("disasm", ""), done=eff(q))
                                                 for q in late_][:6]
        offs_seqs = sorted({s for o in raw.get("offending") or [] for s in (o.get("seqs") or []) if s is not None})
        out["offending_seqs"] = offs_seqs[:30]
        out["offending_by_xmit"] = xs in offs_seqs
        out["offending_structs"] = sorted({o.get("struct") for o in raw.get("offending") or []}, key=str)
        return out
    except Exception:
        out["error"] = traceback.format_exc()[-1500:]
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


recs = [json.loads(l) for l in open(Path(A.run) / "results.jsonl") if l.strip()]
with ProcessPoolExecutor(A.jobs) as ex:
    rows = list(ex.map(one, recs))
S = collections.Counter()
for r in rows:
    c = r.get("category", "error")
    S[(c, "n")] += 1
    if "error" in r:
        S[(c, "error" if not r["error"].startswith("no raw") else "no_raw_not_hit")] += 1
        continue
    for k in ("issued_in_window", "any_src_incomplete_at_signal", "all_older_complete_at_signal"):
        if k in r:
            S[(c, k)] += bool(r[k])
    if r.get("issued_in_window"):
        S[(c, "hit&all_older_complete_at_signal")] += bool(r.get("all_older_complete_at_signal"))
        S[(c, "hit&any_src_incomplete_at_signal")] += bool(r.get("any_src_incomplete_at_signal"))
    for k in ("addr_ok", "leak", "xmit_usl_at_issue", "xmit_fp_before_safe", "all_src_incomplete_at_xmit_issue",
              "any_src_incomplete_at_xmit_issue", "offending_by_xmit"):
        S[(c, k)] += bool(r.get(k))
    S[(c, "resolved_older_late")] += bool(r.get("resolved_older_incomplete_at_xmit_issue"))
    S[(c, "squashed_run")] += bool(r.get("n_squash"))
summary = {f"{c}/{k}": v for (c, k), v in sorted(S.items())}
Path(A.json).write_text(json.dumps(dict(summary=summary, rows=rows), indent=1))
for k, v in summary.items():
    print(f"{k:55s} {v}")

#!/usr/bin/env python3
"""classify.py: the one hit-attribution orchestrator. Runs the cause modules of STAGE3_gem5/bugs/ (one module per known
cause; disqualifiers first, then real-bug modules) and writes the output formats the existing consumers read.

Subcommands (each replaces an old script, which stays in place as the reference until Anna switches over):

  footprint  replaces STAGE3_gem5/timing/classify_hits.py (+ cleanupspec_skip_evidence.py) and classify_cs_rmw.py
      classify.py footprint --run <timing_driver/firstdet run dir> --defense invisispec|cleanupspec|speclfb|stt \
          --out <dir> [--testset <corpus>] [--rmw-stems <corpus>/rmw_stems.tsv] [--stage3 <code>/STAGE3_gem5] [--jobs N]
          [--in-place] [--incremental] [--no-dg3]
    Reads <run>/results.jsonl, raw/<mode>/<stem>.json, traces/<mode>/<stem>.pipeview.txt.gz (read-only). Writes to --out
    (or into <run> with --in-place, as the old scripts did): classes.jsonl, first_detection.json, classify.log; for
    cleanupspec also cs_evidence/diagnostics/cleanupspec_skip_evidence.json and, with --rmw-stems, classes_rmw.jsonl,
    first_detection_rmw.json. With --out, results.jsonl and order_stream.tsv are symlinked in so firstdet_report.py can
    read --out as the run dir.
  gate       replaces runconfigs/twostage_lp/eval_20261110/eval_gate.py (same arguments + --code-root/--testsets-root)
  bucket     replaces runconfigs/twostage_lp/eval_20261110/bucket_eval.py (same arguments)
  race       counts paper UV6 from diag_stt_vp_squash_race.py output JSON(s): classify.py race <race.json ...> [--json out]

Labels are exactly the old ones (so firstdet_report.py, uv5_* and the figure scripts keep working). The one intended
change is DG-3 option (i) (_dg3.py): over_clean lines are exempt from the net-state replay's outside-window filter, so
the four UV5 records are no longer `inconsistent` (visible in cs_evidence variants); no label changes. --no-dg3 disables it.
"""
import argparse, collections, glob, gzip, json, os, re, shutil, sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import bugs  # noqa: E402
from bugs import _trace, _dg3  # noqa: E402
from bugs import (disq_setup_block as SETUP, disq_hpad_text_end as HPAD, disq_hpad_rmw_padding as HPADRMW,  # noqa: E402
                  disq_speclfb_nonload as NONLOAD, disq_data_obtained as GATE, disq_check_ld_rmw_limm as LIMM,
                  a_uv1_invisispec as UV1, a_uv1_transient as UV1T, a_uv3_cleanupspec_rmw as UV3,
                  a_uv4_cleanupspec_split as UV4, a_uv5_cleanupspec_overclean as UV5, a_uv6_speclfb_first_load as UV6,
                  cs1_older_store_upgrade as CS1, cs_em_upgrade as EM, cs_em_rmw as EMRMW, cs_em_other as EMOTHER,
                  cs_uv3_other_actor as UV3OTHER, uv4_speclfb_walk_order as WALK, uv5_speclfb_jmp_shadow as JMP,
                  uv1_stt_xmm4 as XMM4, uv2_recon_stlf as A2, uv3_recon_oldest_taint as RSA8, r_sa13_recon_sse_load as RSA13,
                  r_sa9_recon_twin_untaint as RSA9, recon_reveal_artifact as REVEAL, uv6_vp_squash_race as RACE)

TARGETS = {"invisispec": [UV1.LABEL, UV1T.LABEL], "cleanupspec": ["UV4", "UV3", "UV5"],
           "speclfb": [UV6.LABEL, WALK.LABEL, JMP.LABEL], "stt": [XMM4.LABEL]}
# CleanupSpec item rules, in apply order (mutually exclusive by construction; first match wins)
CS_ITEM_MODULES = [UV4, CS1, EM, UV5]
CS_LABEL = {UV4.CAUSE: UV4.LABEL, UV5.CAUSE: UV5.LABEL, CS1.CAUSE: CS1.LABEL, EM.CAUSE: EM.LABEL,
            "unattributed": "unattributed"}
RMW_TARGETS = ["UV3", "UV4", "UV5"]
RMW_SEPARATE = ["CS1", "EM_rmw", "EM_other", "UV3_other_actor", "unattributed"]
RMW_EXCLUDED = ["UV3_padding", "EM_padding"]


def _is_stt_row(name, camp=None):
    """STT rows (E3 stt-master, E4 AMuLeT STT) get the STT gate class (S1_xmm4 = UV1) instead of ReCon's R-SA-13 classes.
    An explicit campaigns-json "stt": true/false wins; otherwise the name has an `E3` / `E4` token anywhere (inttwin 2026-11-16:
    the old test `name.split("_")[0] in ("E3", "E4")` missed prefixed names such as `bc_E3_...`, which then got ReCon classes)."""
    if camp is not None and "stt" in camp:
        return bool(camp["stt"])
    return re.search(r"(?:^|_)E[34](?:_|$)", name) is not None


def _stage3(path):
    os.environ["SIMSPECT_STAGE3"] = str(path)
    for p in (str(Path(path) / "triage" / "diag"), str(path)):
        if p in sys.path:
            sys.path.remove(p)
        sys.path.insert(0, p)


# ════════════════════════════ footprint: InvisiSpec ═══════════════════════════

def sigs_invisispec(raw, pv, gc, tend=None):
    evs = {e["id"]: e for e in gc.parse_simspect_events(pv)}
    byseq = gc.parse_pipeview_by_seq(pv) if tend is not None else {}
    sigs, structs, padded = set(), set(), False
    for o in raw.get("offending") or []:
        structs.add(o.get("struct"))
        vp = o.get("vp") or {}
        for i in o.get("event_ids") or []:
            e = evs.get(i)
            if UV1.is_event(e):
                if HPAD.is_pad(e, byseq, tend):
                    padded = True
                else:
                    sigs.add(UV1.LABEL)
                    if UV1T.is_transient(e, vp):
                        sigs.add(UV1T.LABEL)
    if padded and UV1.LABEL not in sigs:
        sigs.add(f"{HPAD.LABEL}:{UV1.LABEL}")
    if not sigs:                       # residue: unexplained InvisiSpec footprint, listed by struct
        sigs |= {f"other_{s}" for s in sorted(structs, key=str)}
    return sigs


# ════════════════════════════ footprint: SpecLFB ══════════════════════════════

def _speclfb_tagsigs(tags):
    sigs = set()
    for m in (UV6, WALK, JMP):
        if m.in_tags(tags):
            sigs.add(m.LABEL)
    return sigs


def sigs_speclfb(raw, pv, mode, gc, cf, tend=None):
    from bugs import _speclfb
    a = _speclfb.analyze(raw, str(pv), mode, gc, cf)
    good = [c for c in a.get("causes") or [] if NONLOAD.is_load_cause(c)]
    if tend is not None:
        byseq = gc.parse_pipeview_by_seq(pv)
        pad = [c for c in good if HPAD.is_pad(c["ev"], byseq, tend)]
        good = [c for c in good if not HPAD.is_pad(c["ev"], byseq, tend)]
        excl = _speclfb_tagsigs({c["tag"] for c in pad}) - _speclfb_tagsigs({c["tag"] for c in good})
    else:
        excl = set()
    tags = {c["tag"] for c in good}
    sigs = {f"{HPAD.LABEL}:{x}" for x in excl}
    sigs |= _speclfb_tagsigs(tags)
    if not sigs:
        sigs.add("other:" + ("+".join(sorted(tags)) if tags else "disq_non_load_footprint"))
    return sigs


def _classify_one(w):
    """One invisispec/speclfb hit -> (idx, sigs, error text). Module level so --jobs can fork it."""
    r, run, testset, defense, stage3 = w
    _stage3(stage3)
    import gem5_common as gc
    import check_footprint as cf
    gz = run / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
    rawf = run / "raw" / r["mode"] / f"{r['stem']}.json"
    if not gz.exists() or not rawf.exists():
        return r["idx"], {"no_trace"}, ""
    pv = _trace.gunzip_tmp(gz)
    try:
        raw = json.loads(rawf.read_text())
        tend = _trace.text_end(testset, r["mode"], r["stem"], raw, gc) if testset else None
        fn = ((lambda x: sigs_invisispec(x, pv, gc, tend)) if defense == "invisispec"
              else (lambda x: sigs_speclfb(x, pv, r["mode"], gc, cf, tend)))
        return r["idx"], SETUP.with_exclusion(fn, raw, pv, gc, TARGETS[defense]), ""
    except Exception:
        return r["idx"], {"classify_error"}, f"ERROR idx={r['idx']} {r['mode']}/{r['stem']}\n{traceback.format_exc()}\n"
    finally:
        pv.unlink(missing_ok=True)


# ════════════════════════════ footprint: CleanupSpec ══════════════════════════

def judge_cs_item(item, tr):
    """-> (cause, why): the first CleanupSpec item module that explains the item, else unattributed."""
    for m in CS_ITEM_MODULES:
        why = m.judge(item, tr)
        if why is not None:
            return m.CAUSE, why
    es, S, reason = _trace.cs_actor(item, tr)
    if es is None:
        return "unattributed", reason
    return "unattributed", f"no rule matched: term {item.get('term')} events {[e['kind'] for e in es]}"


def cleanupspec_evidence(run: Path, hits, out: Path, log, dg3=True):
    """Per hit stem, per offending item, one cause (old cleanupspec_skip_evidence.py run on classify_hits' shim)."""
    import gem5_common as gc
    res, setup_stripped, n_dg3 = {}, {}, 0
    last = {}
    for r in hits:      # one record per (mode, stem): the old shim wrote one file per stem, the last row winning
        last[(r["mode"], r["stem"])] = r
    for r in last.values():
        rawf = run / "raw" / r["mode"] / f"{r['stem']}.json"
        if not rawf.exists():
            continue
        rec = json.loads(rawf.read_text())
        rec.pop("workdir", None)
        if dg3:
            rec, ch = _dg3.normalize(rec)
            if ch:
                n_dg3 += 1
                log.write(f"DG-3 {r['mode']}/{r['stem']}: over_clean exempt from outside-W filter -> "
                          f"inconsistent={rec['inconsistent']}\n")
        gz = run / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
        if rec.get("cache_setup") == "full" and gz.exists():   # SETUP exclusion (cache-full)
            pv = _trace.gunzip_tmp(gz)
            try:
                rec, n = SETUP.strip(rec, pv, gc)
            finally:
                pv.unlink(missing_ok=True)
            if n:
                setup_stripped[f"{r['mode']}/{r['stem']}"] = not rec["offending"]
                log.write(f"SETUP-strip {r['mode']}/{r['stem']}: {n} events removed, {len(rec['offending'])} items left\n")
        if not rec.get("issued_in_window"):
            continue
        key = f"{r['mode']}/{rec['name'].split('__')[0]}"
        try:
            if not gz.exists():
                items = [dict(o, cause="unattributed", why="no trace") for o in rec.get("offending", [])]
            else:
                with gzip.open(gz, "rt", errors="replace") as fh:
                    tr = _trace.cs_parse(fh)
                items = []
                for o in rec.get("offending", []):
                    c, why = judge_cs_item(o, tr)
                    items.append(dict(o, cause=c, why=why))
        except Exception:
            log.write(f"ERROR {key} {rec['name']}\n{traceback.format_exc()}\n")
            items = [dict(cause="unattributed", why="exception (see log)")]
        ent = res.setdefault(key, {"variants": []})
        ent["variants"].append({"record": rec["name"], "terms": rec.get("terms_fired"),
                                "inconsistent": rec.get("inconsistent"), "items": items})
    for key, ent in res.items():
        ent["causes"] = sorted({i["cause"] for v in ent["variants"] for i in v["items"]})
    d = out / "cs_evidence" / "diagnostics"
    d.mkdir(parents=True, exist_ok=True)
    (d / "cleanupspec_skip_evidence.json").write_text(json.dumps(res, indent=1) + "\n")
    log.write(f"cleanupspec evidence: {len(res)} hit stems, DG-3 flag changes {n_dg3}\n")
    cls = {k: {CS_LABEL.get(c, c) for c in v.get("causes", [])} for k, v in res.items()}
    for k, only in setup_stripped.items():
        if only:
            cls[k] = {"excluded_SETUP:no_test_event"}
    return cls, res


def refine_rmw(item, rec, tr, rmw):
    """Old classify_cs_rmw refine(): UV3 / UV3_padding / UV3_other_actor for unattributed items, EM_rmw / EM_padding /
    EM_other for EM items; UV4 / UV5 / CS1 keep their attribution."""
    xpc = int(rec["xmit_pc"], 16) if rec.get("xmit_pc") else None
    dis_by_pc = tr[3]
    cause = item.get("cause")
    if cause == "unattributed" and item.get("term") == "under_clean":
        ch = _trace.rmw_uv3_chain(item, tr)
        if ch is not None:
            S, pc = ch
            if UV3.matches(pc, xpc, rmw):
                return UV3.LABEL, f"S={S} pc={hex(pc)} = xmit RMW; fill req=st; cleanup_skip nohitinfo"
            if HPADRMW.is_padding(pc, xpc, dis_by_pc):
                return "UV3_padding", f"S={S} pc={hex(pc)} ADD_M_R after xmit {rec.get('xmit_pc')} (H-PAD)"
            if UV3OTHER.matches(pc, xpc, rmw):
                return UV3OTHER.LABEL, f"S={S} pc={hex(pc)} xmit={rec.get('xmit_pc')} rmw={rmw}"
        return "unattributed", item.get("why", "")
    if cause == EM.CAUSE:
        pcs, ups = _trace.rmw_em_upgraders(item, tr)
        if len(pcs) == 1:
            pc = pcs.pop()
            U = int(ups[0]["seq"])
            if EMRMW.matches(pc, xpc, rmw):
                return EMRMW.LABEL, f"U={U} pc={hex(pc)} = xmit RMW"
            if HPADRMW.is_padding(pc, xpc, dis_by_pc):
                return "EM_padding", f"U={U} pc={hex(pc)} ADD_M_R after xmit {rec.get('xmit_pc')} (H-PAD)"
            return EMOTHER.LABEL, f"U={U} pc={hex(pc)}"
        return EMOTHER.LABEL, f"{len(pcs)} distinct squashed upgrader pcs"
    return CS_LABEL.get(cause, cause), item.get("why", "")


def cleanupspec_rmw(run: Path, rows, ev, rmw_stems: Path, testset: Path, log):
    rmw = {tuple(l.split("\t")[:2]) for l in rmw_stems.read_text().splitlines()[1:] if l.strip()}
    cls = {}
    for i, r in rows.items():
        if not r.get("hit"):
            continue
        key = f"{r['mode']}/{r['stem']}"
        is_rmw = (r["mode"], r["stem"]) in rmw
        try:
            rec = json.loads((run / "raw" / r["mode"] / f"{r['stem']}.json").read_text())
            gz = run / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
            json.loads((testset / r["mode"] / "ann" / f"{r['stem']}.ann.json").read_text())   # old code read it (missing ann = error)
            if key not in ev or not gz.exists():
                cls[i] = ({"no_evidence"}, [])
                continue
            tr = _trace.rmw_parse_trace(gz)
            items = []
            for v in ev[key]["variants"]:
                for it in v["items"]:
                    c, why = refine_rmw(it, rec, tr, is_rmw)
                    items.append(dict(struct=it.get("struct"), line=it.get("line"), term=it.get("term"), cause=c, why=why))
            cls[i] = ({x["cause"] for x in items}, items)
        except Exception:
            log.write(f"ERROR rmw idx={i} {key}\n{traceback.format_exc()}\n")
            cls[i] = ({"classify_error"}, [])
    return cls, rmw


# ════════════════════════════ footprint: STT ══════════════════════════════════

def stt_label(raw, stem, mode_dir, fs):
    g = GATE.label(raw)
    if g:
        return g
    sl = fs.transmitter_slice(stem, mode_dir)
    if sl.get("err"):
        return "other_stt(slice_err)"
    return XMM4.LABEL if XMM4.matches(sl) else "other_stt"


# ════════════════════════════ footprint: metrics + main ═══════════════════════

def _prefix_stats(rows, cls_sigs):
    N = 0
    while N in rows:
        N += 1
    cum_g = cum_t = 0.0
    first, K, st = {}, collections.Counter(), collections.Counter()
    for i in range(N):
        r = rows[i]
        cum_g += r.get("gem5_cpu_s") or 0
        cum_t += r.get("total_cpu_s") or 0
        st[r.get("status")] += 1
        for s in cls_sigs.get(i, ()):
            K[s] += 1
            if s not in first:
                first[s] = dict(first_idx=i, tests_to_first=i + 1, stem=r["stem"], mode=r["mode"],
                                cum_gem5_cpu_s=round(cum_g, 2), cum_total_cpu_s=round(cum_t, 2))

    def sig(s):
        return dict(first.get(s, {}), K=K[s], N=N, expected_tests_to_first=round((N + 1) / (K[s] + 1), 2),
                    expected_gem5_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_g / N, 2) if N else None,
                    expected_total_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_t / N, 2) if N else None)
    return N, cum_g, cum_t, st, K, sig


def cmd_footprint(a):
    run = Path(a.run).resolve()
    out = run if a.in_place else Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not a.in_place:
        for f in ("results.jsonl", "order_stream.tsv"):
            if (run / f).exists() and not (out / f).exists():
                (out / f).symlink_to(run / f)
    testset = Path(a.testset) if a.testset else None
    _stage3(a.stage3)
    log = open(out / "classify.log", "a")
    log.write(f"== start {time.strftime('%F %T')} bugs/classify.py footprint run={run} defense={a.defense} "
              f"stage3={a.stage3} testset={testset} dg3={not a.no_dg3}\n")
    rows = {}
    for l in (run / "results.jsonl").read_text().splitlines():
        try:
            r = json.loads(l)
            rows[r["idx"]] = r
        except Exception:
            pass
    hits = [r for r in rows.values() if r.get("hit")]
    cls = {}
    if a.defense == "cleanupspec":
        try:
            m, ev = cleanupspec_evidence(run, hits, out, log, dg3=not a.no_dg3)
        except Exception:
            log.write(traceback.format_exc())
            m, ev = {}, {}
        for r in hits:
            cls[r["idx"]] = m.get(f"{r['mode']}/{r['stem']}", {"no_evidence"})
    elif a.defense in ("invisispec", "speclfb"):
        prev = {}
        if a.incremental and (out / "classes.jsonl").exists():
            for l in (out / "classes.jsonl").read_text().splitlines():
                try:
                    c = json.loads(l)
                except Exception:
                    continue
                r0 = rows.get(c["idx"])
                if r0 and r0["mode"] == c["mode"] and r0["stem"] == c["stem"] and "classify_error" not in c["sigs"]:
                    prev[c["idx"]] = set(c["sigs"])
            cls.update({i: v for i, v in prev.items() if rows[i].get("hit")})
            log.write(f"incremental: {len(prev)} hits kept from classes.jsonl\n")
        work = [(r, run, testset, a.defense, a.stage3) for r in hits if r["idx"] not in prev]
        if a.jobs > 1:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(a.jobs) as ex:
                res = list(ex.map(_classify_one, work, chunksize=8))
        else:
            res = [_classify_one(w) for w in work]
        for idx, sigs, err in res:
            cls[idx] = sigs
            if err:
                log.write(err)
    elif a.defense == "stt" and testset is not None:
        import _fv2_slice as fs
        for r in hits:
            rawf = run / "raw" / r["mode"] / f"{r['stem']}.json"
            raw = json.loads(rawf.read_text()) if rawf.exists() else {}
            cls[r["idx"]] = {stt_label(raw, r["stem"], testset / r["mode"], fs)}
    else:
        for r in hits:
            cls[r["idx"]] = {"hit(no target)"}
    with open(out / "classes.jsonl", "w") as f:
        for i in sorted(cls):
            f.write(json.dumps(dict(idx=i, mode=rows[i]["mode"], stem=rows[i]["stem"], kind=rows[i].get("kind"),
                                    sigs=sorted(cls[i]))) + "\n")
    N, cum_g, cum_t, st, K, sig = _prefix_stats(rows, cls)
    res = dict(defense=a.defense, N_prefix=N, n_rows=len(rows), status=dict(st),
               hits=sum(1 for i in range(N) if rows[i].get("hit")),
               gem5_cpu_s_total=round(cum_g, 2), total_cpu_s_total=round(cum_t, 2),
               gem5_cpu_s_per_test=round(cum_g / N, 3) if N else None,
               total_cpu_s_per_test=round(cum_t / N, 3) if N else None,
               signatures={s: sig(s) for s in sorted(set(K) | set(TARGETS[a.defense]))})
    (out / "first_detection.json").write_text(json.dumps(res, indent=1))
    log.write(json.dumps(res) + "\n")
    if a.defense == "cleanupspec" and a.rmw_stems:
        cr, rmw = cleanupspec_rmw(run, rows, ev, Path(a.rmw_stems), testset, log)
        with open(out / "classes_rmw.jsonl", "w") as f:
            for i in sorted(cr):
                r = rows[i]
                f.write(json.dumps(dict(idx=i, mode=r["mode"], stem=r["stem"], kind=r.get("kind"),
                                        rmw=(r["mode"], r["stem"]) in rmw, cache_setup=r.get("cache_setup"),
                                        sigs=sorted(cr[i][0]), items=cr[i][1])) + "\n")
        N, cum_g, cum_t, st, K, sig = _prefix_stats(rows, {i: v[0] for i, v in cr.items()})
        n_rmw = sum((rows[i]["mode"], rows[i]["stem"]) in rmw for i in range(N))
        res2 = dict(N_prefix=N, n_rows=len(rows), n_rmw_in_prefix=n_rmw, status=dict(st),
                    hits=sum(1 for i in range(N) if rows[i].get("hit")),
                    gem5_cpu_s_per_test=round(cum_g / N, 3) if N else None,
                    total_cpu_s_per_test=round(cum_t / N, 3) if N else None,
                    targets={s: sig(s) for s in RMW_TARGETS},
                    separate_non_amulet={s: sig(s) for s in RMW_SEPARATE},
                    excluded_padding={s: sig(s) for s in RMW_EXCLUDED},
                    other={s: sig(s) for s in sorted(set(K) - set(RMW_TARGETS) - set(RMW_SEPARATE) - set(RMW_EXCLUDED))})
        (out / "first_detection_rmw.json").write_text(json.dumps(res2, indent=1))
        log.write(json.dumps(res2) + "\n")
    log.write(f"== end {time.strftime('%F %T')}\n")
    print(json.dumps(res, indent=1))


# ════════════════════════════ gate (STT / ReCon eval rows) ════════════════════

def cmd_gate(a):
    os.chdir(a.code_root)
    _stage3(a.stage3 or os.path.join(a.code_root, "STAGE3_gem5"))
    from gem5_common import sample_keep
    import _fv2_slice as fs
    camps = json.load(open(a.campaigns))
    OUT = {}
    for c in camps:
        n = c["results_name"]
        if "_sh" in n.split("_fv3")[-1]:
            continue
        if a.names and n not in a.names:
            continue
        dirs = [os.path.realpath(x) for x in [f"results/{n}__latest"] + sorted(glob.glob(f"results/{n}_sh*__latest"))]
        dirs = [x for x in dirs if os.path.isdir(x)]
        if not dirs:
            continue
        ts = os.path.join(a.testsets_root, c["model"])
        stt = _is_stt_row(n, c)
        rmw = collections.defaultdict(set)
        for l in open(os.path.join(ts, "rmw_stems.tsv")).read().splitlines()[1:]:
            p = l.split("\t")
            if len(p) > 1:
                rmw[p[0]].add(p[1])
        res = {}
        # stl_bypass (store-shadow corpora) only when the corpus has that mode, and a store-shadow-only corpus has no
        # branch modes; branch corpora are unchanged
        _modes = ("mispredict_not_taken", "mispredict_taken")
        if os.path.isdir(os.path.join(ts, "stl_bypass", "ann")):
            _modes = tuple(m for m in _modes if os.path.isdir(os.path.join(ts, m, "ann"))) + ("stl_bypass",)
        for mode in _modes:
            recs, owner, dups = {}, {}, set()
            for d in dirs:
                for f in sorted(glob.glob(os.path.join(d, mode, "_sweep_raw", "*.json"))):
                    try:
                        x = json.load(open(f))
                    except Exception:
                        continue
                    for r in (x if isinstance(x, list) else []):
                        if isinstance(r, dict) and r.get("name"):
                            st = r["name"].split("__")[0]
                            if owner.get(st, d) != d:
                                dups.add(st)
                            owner[st] = d
                            recs[st] = r
            exp = {f[:-9] for f in os.listdir(os.path.join(ts, mode, "ann")) if a.fraction >= 1 or sample_keep(f[:-9], a.fraction)}
            miss = sorted(exp - set(recs))
            res.setdefault(f"{mode}/_merge", dict(runs=len(dirs), stems=len(recs), duplicates=len(dups), duplicate_examples=sorted(dups)[:5],
                                                  expected=len(exp), missing=len(miss), missing_examples=miss[:5]))
            for s, r in recs.items():
                if not isinstance(r, dict):
                    continue
                if a.fraction < 1 and not sample_keep(s, a.fraction):
                    continue
                kind = r.get("xmit_kind") or "?"
                isr = s in rmw[mode]
                key = f"{mode}/{kind}/{'rmw' if isr else 'plain'}"
                e = res.setdefault(key, dict(tests=0, raw_hits=0, gated_hits=0, classes=collections.Counter(), examples={}))
                e["tests"] += 1
                if not r.get("issued_in_window"):
                    continue
                e["raw_hits"] += 1
                g = GATE.label(r)
                if g:
                    cl = g
                else:
                    e["gated_hits"] += 1
                    sl = fs.transmitter_slice(s, Path(ts) / mode)
                    if sl.get("err"):
                        cl = "other(slice_err)"
                    elif stt:
                        cl = XMM4.LABEL if XMM4.matches(sl) else "other"
                    else:
                        cl = RSA13.gate_class(sl)
                e["classes"][cl] += 1
                if len(e["examples"].setdefault(cl, [])) < a.examples:
                    e["examples"][cl].append(s)
        OUT[n] = {k: (dict(v, classes=dict(v["classes"])) if "classes" in v else v) for k, v in sorted(res.items())}
    for n, v in OUT.items():
        print(f"== {n}")
        for k, e in v.items():
            if k.endswith("/_merge"):
                print(f"  {k:42} runs {e['runs']}  stems {e['stems']} / expected {e['expected']}  MISSING {e['missing']}  DUPLICATES {e['duplicates']}")
                continue
            print(f"  {k:42} tests {e['tests']:5}  raw {e['raw_hits']:4}  gated {e['gated_hits']:4}  {e['classes']}")
    if a.json:
        json.dump(dict(fraction=a.fraction, campaigns=OUT), open(a.json, "w"), indent=1)


# ════════════════════════════ bucket (ReCon / STT eval rows) ══════════════════

def recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf, rev, ot=None):
    """One gated hit -> bucket label. Same chain as the old bucket_eval.py; each signature test is its cause module."""
    if cl.startswith("disq"):
        return cl
    if stt:
        return cl
    if rp == "rmw" or (mode, s) not in tstems:
        sfx = ", RMW" if rp == "rmw" else ""
        e = stlf.get(f"{mode}/{s}") if kind == "ld" else None
        if A2.matches(e):
            return f"A2 STLF bypass (main-run evidence, no twin{sfx})"
        if RSA13.is_static(cl):
            return f"R-SA-13 (static only{sfx})"
        om = (ot or {}).get(f"{mode}/{s}/main")          # oldest_taint_replay evidence (store-shadow rows only)
        if RSA13.sse_annotated_load(om):
            return f"R-SA-13 (annotated load is an SSE load; replay{sfx})"
        if RSA8.confirmed_stl(om):
            return f"{RSA8.LABEL_STL} (main run, no twin{sfx})"
        if RSA13.untainted(e):
            return f"untainted transmitter, no twin (R-SA-13 candidate{sfx})"
        if LIMM.matches(rp, e):
            return LIMM.LABEL
        if e is not None and not e.get("reproduced", True):
            return f"no twin, not reproduced{sfx}"
        return f"unexplained(no twin{sfx}: {cl}{'' if e is None else ', evidence: ' + (e.get('stl') or '')[-28:]})"
    t = twin.get((mode, s))
    if t is None or t[1] != "ok":
        return "twin missing/error"
    if not t[0]:
        return "R-SA-13" if RSA13.is_static(cl) else "R-SA-13 via FP elsewhere (twin held; e2-losttaint idiv-divisor case)"
    otw = (ot or {}).get(f"{mode}/{s}/twin")
    if RSA8.matches(kind, t[0]):
        return RSA8.LABEL_STL if RSA8.confirmed_stl(otw) else RSA8.LABEL
    e = stlf.get(f"{mode}/{s}")
    if e is None:
        return "twin-hit ld, no evidence"
    if not e.get("reproduced", True):
        return "twin-hit ld, not reproduced"
    if A2.matches(e):
        return "A2 STLF bypass"
    if RSA13.untainted(e):
        r = rev.get(f"{mode}/{s}")
        if REVEAL.matches(r):
            return REVEAL.LABEL
        if RSA9.matches(r):
            return RSA9.LABEL
        return "isTainted=0 (reveal not checked)"
    if RSA8.confirmed_stl(otw):
        return f"{RSA8.LABEL_STL} (ld)"
    return "twin-hit ld, other STL signature"


def cmd_bucket(a):
    G = json.load(open(a.gate))["campaigns"][a.row]
    twin, tstems = {}, set()
    for d in a.twin:
        for f in (glob.glob(os.path.join(os.path.realpath(d), "mispredict_*", "*", "window-results.json"))
                  + glob.glob(os.path.join(os.path.realpath(d), "stl_bypass", "*", "window-results.json"))):
            m = f.split("/")[-3]
            x = json.load(open(f))
            recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
            for r in recs:
                if isinstance(r, dict):
                    twin[(m, r["name"].split("__")[0])] = (bool(r.get("issued_in_window")), r.get("status"))
    for t in a.twin_stems:
        tstems |= {tuple(l.split("\t")) for l in open(t).read().splitlines()[1:] if l}
    stlf, rev = {}, {}
    for f in a.stlf:
        stlf.update(json.load(open(f)))
    for f in a.reveal:
        rev.update(json.load(open(f)))
    ot = {}
    for f in a.oldest_taint:
        ot.update(json.load(open(f)))
    stt = _is_stt_row(a.row) if a.stt == "auto" else a.stt == "yes"
    out, per_stem = {}, {}
    for key, v in G.items():
        if key.endswith("/_merge") or "classes" not in v:
            continue
        mode, kind, rp = key.split("/")
        B = collections.Counter()
        EX = collections.defaultdict(list)
        for cl, stems in v["examples"].items():
            for s in stems:
                b = recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf, rev, ot)
                per_stem[f"{key}/{s}"] = b
                B[b] += 1
                if len(EX[b]) < a.examples:
                    EX[b].append(s)
        out[key] = dict(tests=v["tests"], raw=v["raw_hits"], gated=v["gated_hits"], buckets=dict(B), examples=dict(EX))
    for k, e in out.items():
        print(f"{k:40} tests {e['tests']:5} raw {e['raw']:4} gated {e['gated']:4}")
        for b, n in sorted(e["buckets"].items(), key=lambda x: -x[1]):
            print(f"      {n:5}  {b}")
    if a.json:
        json.dump(dict(row=a.row, buckets=out), open(a.json, "w"), indent=1)
    if a.per_stem:
        json.dump(per_stem, open(a.per_stem, "w"), indent=0, sort_keys=True)


# ════════════════════════════ race (paper UV6) ════════════════════════════════

def cmd_race(a):
    recs = []
    for f in a.evidence:
        x = json.load(open(f))
        recs += x if isinstance(x, list) else list(x.values())
    v = collections.Counter(r.get("verdict") for r in recs)
    hit = sorted(r.get("name") for r in recs if RACE.matches(r))
    res = dict(n=len(recs), verdicts=dict(v), race=len(hit), race_stems=hit)
    print(json.dumps({k: res[k] for k in ("n", "verdicts", "race")}))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("footprint")
    f.add_argument("--run", required=True)
    f.add_argument("--defense", required=True, choices=["invisispec", "cleanupspec", "speclfb", "stt"])
    f.add_argument("--out")
    f.add_argument("--in-place", action="store_true")
    f.add_argument("--testset")
    f.add_argument("--rmw-stems")
    f.add_argument("--stage3", default=str(HERE.parent))
    f.add_argument("--jobs", type=int, default=1)
    f.add_argument("--incremental", action="store_true")
    f.add_argument("--no-dg3", action="store_true")
    g = sub.add_parser("gate")
    g.add_argument("--code-root", default=".")
    g.add_argument("--stage3")
    g.add_argument("--campaigns", default="runconfigs/twostage_lp/eval_20261110/campaigns.json")
    g.add_argument("--testsets-root", default="/tests/simspect_alloy_20261108/testsets_twostage")
    g.add_argument("--fraction", type=float, default=1.0)
    g.add_argument("--names", nargs="*")
    g.add_argument("--json")
    g.add_argument("--examples", type=int, default=3)
    b = sub.add_parser("bucket")
    b.add_argument("--row", required=True)
    b.add_argument("--gate", required=True)
    b.add_argument("--twin", nargs="*", default=[])
    b.add_argument("--twin-stems", nargs="*", default=[])
    b.add_argument("--stlf", nargs="*", default=[])
    b.add_argument("--reveal", nargs="*", default=[])
    b.add_argument("--oldest-taint", nargs="*", default=[],
                   help="triage/oldest_taint_replay.py evidence keyed '<mode>/<stem>/{main,twin}' (store-shadow ReCon rows)")
    b.add_argument("--stt", choices=["auto", "yes", "no"], default="auto", help="STT row (auto = E3/E4 token in --row)")
    b.add_argument("--json")
    b.add_argument("--per-stem", help="also write '<mode>/<kind>/<rp>/<stem>' -> bucket (JSON)")
    b.add_argument("--examples", type=int, default=3)
    r = sub.add_parser("race")
    r.add_argument("evidence", nargs="+")
    r.add_argument("--json")
    a = ap.parse_args()
    if a.cmd == "footprint" and not (a.out or a.in_place):
        ap.error("footprint needs --out <dir> or --in-place")
    if a.cmd == "footprint" and a.defense == "cleanupspec" and a.rmw_stems and not a.testset:
        ap.error("--rmw-stems needs --testset")
    {"footprint": cmd_footprint, "gate": cmd_gate, "bucket": cmd_bucket, "race": cmd_race}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

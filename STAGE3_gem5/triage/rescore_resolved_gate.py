#!/usr/bin/env python3
"""rescore_resolved_gate.py -- offline re-score of saved checker records under the resolved-branch
gate (Anna 2026-11-16, option (b); rule and pure function in STAGE3_gem5/resolved_gate.py). No gem5.

Two steps, so the node side is read-only and needs nothing but Python 3.8 + this file:

  extract  (on the node, streams to stdout; writes nothing):
      python3 - extract --layout firstdet|sweep --raw <dir> --ann-root <testset dir> --campaign <name>
               < rescore_resolved_gate.py | gzip > <name>.jsonl.gz
    firstdet = firstdet_stream raw/<mode>/<stem>.json (one record per file);
    sweep    = testrun/_sweep_watcher <campaign>/<mode>/_sweep_raw/*.json (lists of records; every
               record kept, with its batch file name, so grid repeats stay visible);
    list     = one checker --out JSON list (--raw <file>, --mode M, --ann-root = flat dir of
               <stem>.ann.json).
    Each output line = the record's gating-relevant fields + the test's .ann.json subset
    (xmit, commit_boundary, annotations) read from <ann-root>/<mode>/ann/<stem>.ann.json.

  score    (on the Mac):
      rescore_resolved_gate.py score <extract.jsonl.gz> [--labels labels.json] [--json out.json]
               [--removed out_removed.jsonl]
    Applies resolved_gate.evaluate to every record and prints hits before / after / removed,
    removed hits by label (labels = {"<mode>/<kind>/.../<stem>" or "<mode>/<stem>": label}),
    gated branches on the correct vs wrong path, and the committed-branch cross-check
    (every committed resolved branch older than the xmit of a hit must be visible before the signal).

Records without `resolved_branches` are counted as `no_field` and left unchanged (reported).
"""
import argparse, collections, glob, gzip, json, os, sys

KEEP = ("name", "status", "xmit_kind", "issued_in_window", "issued_in_window_unvalidated",
        "xmit_signal", "xmit_complete", "lc_retire", "fnc_retire", "br_resolve_source",
        "resolved_branches", "resolved_before_signal", "criteria", "cache_setup", "stall_points",
        "cache_fate", "packet_tick", "load_squash_tick", "xmit_retire", "data_obtained",
        "branch_resolutions", "leak", "terms_fired", "error")


def _ann(root, mode, stem):
    p = os.path.join(root, mode, "ann", stem + ".ann.json")
    try:
        a = json.load(open(p))
    except Exception as e:  # noqa: BLE001
        return None, f"{p}: {e}"
    return dict(xmit=a.get("xmit"), commit_boundary=a.get("commit_boundary"),
                annotations=a.get("annotations")), None


def extract(a):
    if a.layout == "list":   # one checker --out JSON list, one mode, flat ann dir
        x = json.load(open(a.raw))
        n = 0
        for r in (x if isinstance(x, list) else [x]):
            if not isinstance(r, dict) or not r.get("name"):
                continue
            out = {k: r.get(k) for k in KEEP if k in r}
            if a.br_events:
                out["br_events"] = r.get("br_events")
            out.update(campaign=a.campaign, mode=a.mode, batch=os.path.basename(a.raw),
                       has_br_events=bool(r.get("br_events")))
            p = os.path.join(a.ann_root, r["name"] + ".ann.json")
            try:
                j = json.load(open(p))
                out["ann"] = dict(xmit=j.get("xmit"), commit_boundary=j.get("commit_boundary"),
                                  annotations=j.get("annotations"))
            except Exception as e:  # noqa: BLE001
                out["ann"], out["ann_error"] = None, f"{p}: {e}"
            print(json.dumps(out, separators=(",", ":")))
            n += 1
        print(f"extract {a.campaign}: {n} records", file=sys.stderr)
        return
    modes = [m for m in ("mispredict_not_taken", "mispredict_taken", "stl_bypass")
             if os.path.isdir(os.path.join(a.raw, m))] or [""]
    n = 0
    for mode in modes:
        if a.layout == "firstdet":
            files = sorted(glob.glob(os.path.join(a.raw, mode, "*.json")))
        else:
            files = sorted(glob.glob(os.path.join(a.raw, mode, "_sweep_raw", "*.json")))
        for f in files:
            try:
                x = json.load(open(f))
            except Exception as e:  # noqa: BLE001
                print(json.dumps(dict(campaign=a.campaign, mode=mode, file=f, unreadable=str(e))))
                continue
            for r in (x if isinstance(x, list) else [x]):
                if not isinstance(r, dict) or not r.get("name"):
                    continue
                out = {k: r.get(k) for k in KEEP if k in r}
                if a.br_events:
                    out["br_events"] = r.get("br_events")
                out.update(campaign=a.campaign, mode=mode, batch=os.path.basename(f),
                           has_br_events=bool(r.get("br_events")))
                amode = mode or r.get("mode") or ""
                out["ann"], err = _ann(a.ann_root, amode, r["name"])
                if err:
                    out["ann_error"] = err
                print(json.dumps(out, separators=(",", ":")))
                n += 1
    print(f"extract {a.campaign}: {n} records", file=sys.stderr)


def _rows(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as f:
        for l in f:
            if l.strip():
                yield json.loads(l)


def _label(labels, r):
    m, s, k = r["mode"], r["name"], r.get("xmit_kind") or ""
    for key in (f"{m}/{k}/plain/{s}", f"{m}/{k}/rmw/{s}", f"{m}/{k}/{s}", f"{m}/{s}", s):
        if key in labels:
            return labels[key]
    return "unlabelled"


def score(a):
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    import resolved_gate as rg  # noqa: E402
    labels = json.load(open(a.labels)) if a.labels else {}
    C = collections.Counter()
    removed_by_label = collections.Counter()
    hits_by_label = collections.Counter()
    removed = []
    committed_exc = []
    undecided = []
    race_removed = []
    race_scan = None
    if a.race:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(here)),
                                        "scripts", "bigcorpus_20261115"))
        import race_scan  # noqa: E402
    addr_mismatch = 0
    gated_paths = collections.Counter()      # over hit records: gated branches by path x ok
    gated_stall = collections.Counter()
    for r in _rows(a.extract):
        if "unreadable" in r:
            C["unreadable_batch"] += 1
            continue
        C["records"] += 1
        hit = bool(r.get("issued_in_window"))
        C["hits_before"] += hit
        if "resolved_branches" not in r:
            C["no_field"] += 1
            C["hits_after"] += hit
            if hit:
                C["hits_no_field"] += 1
            continue
        ann = r.get("ann")
        if not ann:
            C["no_ann"] += 1
            C["hits_after"] += hit
            continue
        sig = r.get("xmit_signal") or 0
        res = rg.evaluate(r["resolved_branches"], sig, ann,
                          br_observed=bool(r.get("has_br_events")))
        v = res["value"]
        C[f"value_{v}"] += 1
        # address order vs spo order (resolved entries + xmit + lc), only on the ann
        pts = [(e["branch_pc"], e["branch_addr"]) for e in ann.get("annotations") or []
               if "branch_addr" in e and e.get("branch_pc") is not None]
        x = ann.get("xmit") or {}
        if x.get("pc") is not None and x.get("addr"):
            pts.append((x["pc"], x["addr"]))
        pts = sorted(set(pts))
        if any(pts[i][1] >= pts[i + 1][1] for i in range(len(pts) - 1)
               if pts[i][0] != pts[i + 1][0]):
            addr_mismatch += 1
        if hit:
            lab = _label(labels, r)
            hits_by_label[lab] += 1
            for g in res["gated"]:
                gated_paths[(g["path"], "ok" if g["ok"] else "fail")] += 1
                gated_stall[(g["stall"], "ok" if g["ok"] else "fail")] += 1
            for c in res["committed"]:
                vt = c["visible_tick"]
                # with a signal: visible before it; without one (check_footprint): visible
                # before lc retired (a branch cannot retire before it resolves)
                ref = sig or (r.get("lc_retire") or 0)
                if not (vt and ref and vt < ref):
                    committed_exc.append(dict(mode=r["mode"], name=r["name"], spo=c["spo"],
                                              visible_tick=vt, signal=sig,
                                              lc_retire=r.get("lc_retire"), stall=c["stall"]))
                if vt and r.get("lc_retire") and vt > r["lc_retire"]:
                    C["committed_visible_after_lc_retire"] += 1
            if res["committed"]:
                C["hits_with_committed_rb"] += 1
            if res["gated"]:
                C["hits_with_gated_rb"] += 1
            if v is None and res["gated"]:
                C["hits_gated_rb_undecided"] += 1
                # No signal tick (check_footprint): bound what a tick-based rule would do.
                # never visible -> unresolved through the whole window -> would fail under any
                # signal; all visible at or before lc_retire (window opens after lc_retire)
                # -> would pass; otherwise it depends on the offending events' ticks.
                lr = r.get("lc_retire") or 0
                if any(not g["visible_tick"] for g in res["gated"]):
                    C["nosig_would_fail_any_signal"] += 1
                elif lr and all(g["visible_tick"] <= lr for g in res["gated"]):
                    C["nosig_would_pass_any_signal"] += 1
                else:
                    C["nosig_depends_on_event_tick"] += 1
                undecided.append(dict(mode=r["mode"], name=r["name"], label=lab,
                                      lc_retire=lr, fnc_retire=r.get("fnc_retire"),
                                      gated=res["gated"]))
        if race_scan is not None and r.get("xmit_kind") in ("ld", None):
            # UV6 race metrics (race_scan.py definitions); the race packet is the transmission,
            # so the gate is applied at its access tick (and, for reference, at xmit_signal).
            rv = race_scan.classify(r)
            acc = race_scan.access_tick(r)
            va = rg.evaluate(r["resolved_branches"], acc, ann,
                             br_observed=bool(r.get("has_br_events")))["value"] if acc else None
            if rv == "race":
                C["race_before"] += 1
                C["race_after_access_tick"] += va is not False
                C["race_after_xmit_signal"] += v is not False
                if va is False:
                    race_removed.append(dict(mode=r["mode"], name=r["name"], access=acc))
            if race_scan.wp_obtained(r):
                C["wp_obtained_before"] += 1
                C["wp_obtained_after_access_tick"] += va is not False
        after = hit and v is not False
        C["hits_after"] += after
        if hit and not after:
            removed_by_label[lab] += 1
            removed.append(dict(mode=r["mode"], name=r["name"], kind=r.get("xmit_kind"),
                                label=lab, signal=sig, batch=r.get("batch"),
                                gated=res["gated"], notes=res["notes"]))
    C["hits_removed"] = C["hits_before"] - C["hits_after"]
    out = dict(extract=a.extract, counts=dict(C), addr_order_mismatch_records=addr_mismatch,
               hits_by_label=dict(hits_by_label), removed_by_label=dict(removed_by_label),
               gated_branches_in_hits_by_path=({f"{p}/{o}": n for (p, o), n in gated_paths.items()}),
               gated_branches_in_hits_by_stall=({f"{s}/{o}": n for (s, o), n in
                                                 sorted(gated_stall.items())}),
               race_removed_examples=race_removed[:20],
               committed_check_exceptions=len(committed_exc),
               committed_check_examples=committed_exc[:20])
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
    if a.removed:
        with open(a.removed, "w") as f:
            for x in removed:
                f.write(json.dumps(x) + "\n")
        with open(a.removed.replace(".jsonl", "") + "_undecided.jsonl", "w") as f:
            for x in undecided:
                f.write(json.dumps(x) + "\n")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("extract")
    e.add_argument("--layout", choices=("firstdet", "sweep", "list"), required=True)
    e.add_argument("--mode", default="", help="list layout: the records' branch mode")
    e.add_argument("--br-events", action="store_true",
                   help="also keep br_events (per-instance BR lines) for instance diagnostics")
    e.add_argument("--raw", required=True)
    e.add_argument("--ann-root", required=True)
    e.add_argument("--campaign", required=True)
    s = sp.add_parser("score")
    s.add_argument("extract")
    s.add_argument("--labels")
    s.add_argument("--json")
    s.add_argument("--removed")
    s.add_argument("--race", action="store_true", help="also re-score race_scan's race / wp_obtained")
    a = ap.parse_args()
    extract(a) if a.cmd == "extract" else score(a)


if __name__ == "__main__":
    main()

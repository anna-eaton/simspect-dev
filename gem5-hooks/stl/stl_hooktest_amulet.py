#!/usr/bin/env python3
"""stl_hooktest_amulet.py — STL (store bypass) hook controls on the AMuLeT builds
(InvisiSpec, CleanupSpec, SpecLFB). Adapted copy of stl_hooktest.py (the recon-stl
driver, unchanged), 2026-11-09, session stl-port.

What changed vs stl_hooktest.py, and why:
  * Reads ONLY the O3PipeView trace (no LSQUnit flag). The recon driver keyed
    "L executed" on the LSQUnit line "Executing load" and the transmitter send on
    recon's "Memory request ... was sent" line, which these trees print differently
    (and CleanupSpec's LSQUnit print glues text onto hook lines, SIMSPECT_HOOKS.md
    "Parser hazard"). Here the same facts come from the hooks-v2 lines every one of
    the three builds prints: LSQ:issue (the LSQ offered the load to the D-cache;
    req=ld|specld; SpecLFB adds sent/bounced), LSQ:data (via=mem|sb|stlf), LSQ:stlf,
    and the cache/defense events attributed by seq (L1D/L2 fill/miss/hit, SB,
    cleanup_*, LSQ:unsafe, LSQ:safe, expose/validate).
  * Validity is computed exactly as in stl_hooktest.py (hold for S, the forced
    prediction for L, L's first instance issued before stl_release, a
    mem_order_squash caused by S naming an L first instance), with "issued" =
    first LSQ:issue tick. squash_ok_relaxed also accepts a squash caused by S of
    any instance between S and L (16-byte violation granularity,
    STL_SPECULATION.md "Hook test").
  * Observations instead of one leak bit: for the instances the memory-order
    squash removed (seq >= the violator, allocated before the squash = the
    transient instances), what they did in the window [stl_hold, squash] and
    after it, per defense: issued as ld or specld, cache fills/misses/hits, spec
    buffer, cleanup, SpecLFB unsafe flags, and whether each transient L1D/L2 fill
    was removed again (cleanup_inv, evict, inv) or is still present at the end.
  * Optional cache setup (warm/cold/full) through cache_setup.prepare, which
    re-resolves every annotation address including stl_annotations.
Env (set by run_stl_controls_amulet.sh before this runs): SIMSPECT_GEM5_BIN,
SIMSPECT_SE_CONFIG, SIMSPECT_GEM5_CPU, SIMSPECT_GEM5_EXTRA (0x1f-joined),
SIMSPECT_GEM5_DBG_FLAG=O3PipeView, SIMSPECT_BRANCH_ANN_ENABLE, SIMSPECT_STL_*,
SIMSPECT_CACHE_SETUP, SIMSPECT_HARNESS (dir holding STAGE3_gem5/), TMPDIR=/tmp.

Usage:
  stl_hooktest_amulet.py run <testdir> <out.json> [--limit N] [--jobs 16] [--keep-traces DIR] [--label X]
  stl_hooktest_amulet.py compare <keepdirA> <keepdirB> [--ignore-stl]   # hooks-off equivalence on traces
"""
import argparse, collections, gzip, json, os, re, shutil, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HARNESS = Path(os.environ.get("SIMSPECT_HARNESS", "/tests/simspect"))
sys.path.insert(0, str(HARNESS / "STAGE3_gem5"))


def _gc():
    import gem5_common as gc  # noqa: E402 (env must be set first)
    return gc


def sim_ticks(m5out: Path):
    m = re.search(r"^(?:sim_ticks|simTicks)\s+(\d+)", (m5out / "stats.txt").read_text(), re.M)
    return int(m.group(1)) if m else None


def _first(evs, **kw):
    for e in evs:
        if all(e.get(k) == v for k, v in kw.items()):
            return e
    return None


def analyse(trace: Path, ann: dict, s_pc: int, l_pcs: list, x_pc, kind: str,
            litmus_pcs: set = frozenset()) -> dict:
    gc = _gc()
    ev = sorted(gc.parse_simspect_events(trace), key=lambda e: (e["tick"], e["id"] if e["id"] is not None else -1, e["order"]))
    pv = gc.parse_pipeview_by_seq(trace)
    stl = [e for e in ev if e["struct"] == "STL"]
    r = {}
    holds = [e for e in stl if e["kind"] == "stl_hold" and e["pc"] == s_pc]
    s_seq = holds[0]["seq"] if holds else None
    rels = [e for e in stl if e["kind"] == "stl_release" and s_seq is not None and e["seq"] == s_seq]
    preds = [e for e in stl if e["kind"] in ("pred_no_alias", "pred_alias") and e["pc"] in l_pcs]
    t_hold = holds[0]["tick"] if holds else None
    t_rel = rels[0]["tick"] if rels else None
    r.update(n_hold=len(holds), hold=bool(holds), release=bool(rels), s_seq=s_seq,
             t_hold=t_hold, t_rel=t_rel,
             pred=preds[0]["kind"] if preds else None,
             pred_via_barrier=sum(1 for e in preds if e.get("via") == "barrier"),
             n_pred=len(preds))
    # seq -> pc from every source (pipeview records + attributed events)
    seq_pc = {q: rec["pc"] for q, rec in pv.items()}
    for e in ev:
        if e["seq"] is not None and e["pc"] is not None and e["struct"] not in ("ROB",):
            seq_pc.setdefault(e["seq"], e["pc"])
    lo = s_seq if s_seq is not None else -1
    l_firsts = {}
    for pc in l_pcs:
        qs = [q for q, p in seq_pc.items() if p == pc and q > lo]
        if qs:
            l_firsts[pc] = min(qs)
    l_first = min(l_firsts.values()) if l_firsts else None
    issues = collections.defaultdict(list)
    for e in ev:
        if e["struct"] == "LSQ" and e["kind"] == "issue" and e["seq"] is not None:
            issues[e["seq"]].append(e)
    datas = {}
    for e in ev:
        if e["struct"] == "LSQ" and e["kind"] == "data" and e["seq"] is not None:
            datas.setdefault(e["seq"], e)
    stlf = {e["seq"] for e in ev if e["struct"] == "LSQ" and e["kind"] == "stlf"}

    def ld_info(q):
        if q is None:
            return None
        iss = issues.get(q, [])
        d = datas.get(q)
        sent = [e for e in iss if e.get("sent") in (None, "1")]
        info = dict(seq=q, issue_tick=iss[0]["tick"] if iss else None,
                    issue_req=iss[0].get("req") if iss else None,
                    n_issue=len(iss), first_sent_tick=sent[0]["tick"] if sent else None,
                    n_bounced=sum(1 for e in iss if e.get("bounced") == "1"),
                    data_tick=d["tick"] if d else None, data_via=d.get("via") if d else None,
                    data_lvl=d.get("lvl") if d else None, forwarded=q in stlf)
        uns = [e for e in ev if e["struct"] == "LSQ" and e["kind"] == "unsafe" and e["seq"] == q]
        if uns:
            info["speclfb_unsafe"] = {k: uns[0].get(k) for k in ("unsafe", "cusl", "musl", "reallyunsafe",
                                                                  "prevnounsafe", "prevbrsres", "lqhead")}
        safe = [e for e in ev if e["struct"] == "LSQ" and e["kind"] == "safe" and e["seq"] == q]
        if safe:
            info["invisispec_safe"] = dict(tick=safe[0]["tick"], why=safe[0].get("why"))
        exp = [e for e in ev if e["struct"] == "L1D" and e["kind"] in ("expose", "validate") and e["seq"] == q]
        if exp:
            info["expose_validate"] = [(e["kind"], e["tick"]) for e in exp]
        return info

    li = ld_info(l_first)
    r["l"] = li
    r["l_first"] = l_first
    r["l_before_rel"] = bool(li and li["issue_tick"] is not None and t_rel and li["issue_tick"] < t_rel)
    r["l_data_before_rel"] = bool(li and li["data_tick"] is not None and li["data_via"] == "mem"
                                  and t_rel and li["data_tick"] < t_rel)
    sq = [e for e in stl if e["kind"] == "mem_order_squash"]
    r["n_squash"] = len(sq)
    r["squashes"] = [(e["seq"], hex(e["pc"]) if e["pc"] else None, e["cause"], e["tick"]) for e in sq]
    lfs = set(l_firsts.values())
    strict = [e for e in sq if s_seq is not None and e["cause"] == s_seq and e["seq"] in lfs]
    relaxed = [e for e in sq if s_seq is not None and e["cause"] == s_seq and l_first is not None
               and s_seq < e["seq"] <= max(lfs)]
    r["squash_ok"] = bool(strict)
    r["squash_ok_relaxed"] = bool(relaxed)
    r["valid"] = bool(r["hold"] and r["pred"] == "pred_no_alias" and r["l_before_rel"] and r["squash_ok"])
    r["valid_relaxed"] = bool(r["hold"] and r["pred"] == "pred_no_alias" and r["l_before_rel"]
                              and r["squash_ok_relaxed"])
    msq = (strict or relaxed or [None])[0]
    if msq is None:
        return r
    t_sq, viol = msq["tick"], msq["seq"]
    r["t_squash"], r["violator"] = t_sq, viol
    rob = [e for e in ev if e["struct"] == "ROB" and e["kind"] == "squash" and e["tick"] >= t_sq]
    sqid = rob[0]["sq"] if rob else None
    r["rob_squash_sq"] = sqid
    # transient = squashed by this memory-order squash: seq >= violator, seen by t_sq
    trans = {q for q, rec in pv.items() if q >= viol and rec["fetch"] <= t_sq}
    trans |= {e["seq"] for e in ev if e["seq"] is not None and e["seq"] >= viol and e["tick"] <= t_sq
              and e["struct"] != "ROB"}
    r["n_transient_insts"] = len(trans)
    # litmus = the first instance (younger than S) of every __litmus_<stem>_pc<N>
    # instruction, i.e. the Alloy program's own first pass. The other transient
    # instances are harness code (epilogue pop/ret, _start) and the wrong-path
    # re-fetch of the function after the exit syscall (fall-through in _start).
    lit = set()
    for pc in set(litmus_pcs) | set(l_pcs) | ({x_pc} if x_pc else set()):
        qs = [q for q, p in seq_pc.items() if p == pc and q > lo]
        if qs:
            lit.add(min(qs))
    lit &= trans
    r["n_litmus_transient_insts"] = len(lit)
    t_lo = t_hold or 0

    def counts(seqs):
        win = collections.Counter(); post = collections.Counter()
        for e in ev:
            if e["seq"] not in seqs or e["struct"] in ("ROB", "STL", "BR", "META"):
                continue
            k = f"{e['struct']}:{e['kind']}"
            if e["struct"] == "LSQ" and e["kind"] == "issue":
                k += f":{e.get('req')}"
            if t_lo <= e["tick"] <= t_sq:
                win[k] += 1
            elif e["tick"] > t_sq:
                post[k] += 1
        return dict(sorted(win.items())), dict(sorted(post.items()))

    r["transient_window_events"], r["transient_post_squash_events"] = counts(trans)
    r["litmus_window_events"], r["litmus_post_squash_events"] = counts(lit)
    tl = sorted({e["seq"] for e in ev if e["struct"] == "LSQ" and e["kind"] == "issue" and e["seq"] in trans
                 and t_lo <= e["tick"] <= t_sq})
    r["transient_loads_issued"] = tl
    r["litmus_loads_issued"] = [q for q in tl if q in lit]
    # each transient L1D/L2 fill: removed again, and how?
    fills = []
    for e in ev:
        if e["seq"] in trans and e["struct"] in ("L1D", "L2") and e["kind"] == "fill" and e["line"] is not None:
            how = None
            for f in ev:
                if f["struct"] != e["struct"] or (f["tick"], f["id"] or -1) <= (e["tick"], e["id"] or -1):
                    continue
                if f["kind"] == "evict" and f["victim"] == e["line"]:
                    how = "evict"; break
                if f["kind"] in ("cleanup_inv", "inv") and f["line"] == e["line"]:
                    how = f["kind"]; break
            fills.append(dict(struct=e["struct"], line=hex(e["line"]), seq=e["seq"], tick=e["tick"],
                              in_window=e["tick"] <= t_sq, removed_by=how, litmus=e["seq"] in lit))
    r["transient_fills"] = fills
    r["transient_fill_present_at_end"] = sum(1 for f in fills if f["removed_by"] is None)
    if sqid is not None:
        done = [e for e in ev if e["kind"] == "cleanup_done" and e["sq"] == sqid]
        if done:
            r["cleanup_done"] = dict(tick=done[0]["tick"], bufd=done[0].get("bufd"), merged=done[0].get("merged"))
    if kind == "ld" and x_pc is not None:
        xs = sorted(q for q, p in seq_pc.items() if p == x_pc and l_first is not None and q >= l_first)
        x0 = xs[0] if xs else None
        xi = ld_info(x0)
        r["x"] = xi
        if xi:
            xi["transient"] = x0 in trans
            it = xi["first_sent_tick"] or xi["issue_tick"]
            xi["issued_in_hold"] = bool(it and t_hold and t_rel and t_hold <= it < t_rel)
            xi["issued_before_squash"] = bool(it and it <= t_sq)
            xi["l1d_in_window"] = [e["kind"] for e in ev if e["seq"] == x0 and e["struct"] == "L1D"
                                   and t_lo <= e["tick"] <= t_sq]
            xi["l2_in_window"] = [e["kind"] for e in ev if e["seq"] == x0 and e["struct"] == "L2"
                                  and t_lo <= e["tick"] <= t_sq]
    return r


def one(s_path: Path, ann_path: Path, keep: Path, cache_setup: str) -> dict:
    gc = _gc()
    import cache_setup as cs
    name = s_path.stem
    wd = Path(tempfile.mkdtemp(prefix=f"stlhook_{name}_"))
    r = dict(name=name, cache_setup=cache_setup)
    try:
        binary, ann_use, info = cs.prepare(s_path, ann_path, wd, gc.build_binary, cache_setup)
        if info is not None:
            r["cache_setup_info"] = {k: info.get(k) for k in ("delta", "n_loads", "fill_bytes", "set_cover_exact")}
        ann = json.loads(Path(ann_use).read_text())
        r["kind"] = ann["xmit"]["kind"]
        pairs = ann["stl_annotations"]
        s_pc = int(pairs[0]["store_addr"])
        l_pcs = [int(p["load_addr"]) for p in pairs if int(p["store_addr"]) == s_pc]
        r["n_loads"] = len(l_pcs)
        x_pc = gc.resolve_pc(binary, name, ann["xmit"])
        trace = gc.run_gem5(binary, wd, ann_path=Path(ann_use).resolve(), fnc_pc=None)
        r["sim_ticks"] = sim_ticks(wd / "m5out")
        lit_pcs = set(gc._litmus_labels(binary, name).values())
        r.update(analyse(trace, ann, s_pc, l_pcs, x_pc, r["kind"], lit_pcs))
        if keep is not None:
            kd = keep / name
            kd.mkdir(parents=True, exist_ok=True)
            with open(trace, "rb") as f, gzip.open(kd / "pipeview.txt.gz", "wb") as g:
                shutil.copyfileobj(f, g)
            (kd / "sim_ticks").write_text(f"{r['sim_ticks']}\n")
            shutil.copy2(wd / "m5out" / "config.ini", kd / "config.ini")
        r["status"] = "ok"
    except Exception as e:  # report, never hide
        r["status"] = "error"
        r["error"] = f"{type(e).__name__}: {e}"[:600]
        st = getattr(e, "stderr", None)
        if st:
            r["stderr_tail"] = (st.decode(errors="replace") if isinstance(st, bytes) else str(st))[-600:]
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    return r


def summary(res, label=""):
    ok = [r for r in res if r["status"] == "ok"]
    out = dict(label=label, n=len(res), ran=len(ok), errors=len(res) - len(ok))
    for k in ("hold", "release", "l_before_rel", "l_data_before_rel", "squash_ok", "squash_ok_relaxed",
              "valid", "valid_relaxed"):
        out[k] = sum(1 for r in ok if r.get(k))
    out["pred"] = dict(collections.Counter(r.get("pred") for r in ok))
    v = [r for r in ok if r.get("valid_relaxed")]
    out["valid_relaxed_with_litmus_load_issued"] = sum(1 for r in v if r.get("litmus_loads_issued"))
    for pre in ("litmus", "transient"):
        agg = collections.Counter(); aggp = collections.Counter()
        for r in v:
            for k in r.get(f"{pre}_window_events", {}):
                agg[k] += 1          # number of tests with >= 1 such event
            for k in r.get(f"{pre}_post_squash_events", {}):
                aggp[k] += 1
        out[f"tests_with_{pre}_window_event"] = dict(sorted(agg.items()))
        out[f"tests_with_{pre}_post_squash_event"] = dict(sorted(aggp.items()))
    for pre, sel in (("litmus", lambda f: f["litmus"]), ("harness", lambda f: not f["litmus"])):
        fl = [(r, f) for r in v for f in r.get("transient_fills", []) if sel(f)]
        out[f"tests_with_{pre}_L1D_fill"] = len({r["name"] for r, f in fl if f["struct"] == "L1D"})
        out[f"tests_with_{pre}_L2_fill"] = len({r["name"] for r, f in fl if f["struct"] == "L2"})
        out[f"{pre}_fill_removed_by"] = {f"{st}:{k}": c for (st, k), c in sorted(
            collections.Counter((f["struct"], str(f["removed_by"])) for _, f in fl).items())}
    lds = [r for r in v if r.get("kind") == "ld"]
    out["ld_xmits_valid"] = len(lds)
    out["ld_xmit_transient"] = sum(1 for r in lds if (r.get("x") or {}).get("transient"))
    out["ld_xmit_issued_in_hold"] = sum(1 for r in lds if (r.get("x") or {}).get("issued_in_hold"))
    out["ld_xmit_issue_req"] = dict(collections.Counter((r.get("x") or {}).get("issue_req") for r in lds))
    out["ld_xmit_l1d_in_window"] = dict(collections.Counter(",".join(sorted(set((r.get("x") or {}).get("l1d_in_window") or []))) or "none" for r in lds))
    out["l_issue_req"] = dict(collections.Counter((r.get("l") or {}).get("issue_req") for r in v))
    su = collections.Counter()
    for r in v:
        for who in ("l", "x"):
            u = (r.get(who) or {}).get("speclfb_unsafe")
            if u:
                su[f"{who}:unsafe={u.get('unsafe')},musl={u.get('musl')},reallyunsafe={u.get('reallyunsafe')}"] += 1
    if su:
        out["speclfb_unsafe_at_translation"] = dict(sorted(su.items()))
    out["errors_list"] = [(r["name"], r.get("error")) for r in res if r["status"] != "ok"]
    return out


def compare(a: Path, b: Path, ignore_stl: bool) -> dict:
    stl_re = re.compile(r"^O3PipeView:simspect:\d+:STL:")
    rows, same = [], 0
    names = sorted({p.name for p in a.iterdir() if p.is_dir()} | {p.name for p in b.iterdir() if p.is_dir()})
    for n in names:
        fa, fb = a / n / "pipeview.txt.gz", b / n / "pipeview.txt.gz"
        if not (fa.exists() and fb.exists()):
            rows.append(dict(name=n, ok=False, why="missing")); continue
        la = gzip.open(fa, "rt", errors="replace").read().splitlines()
        lb = gzip.open(fb, "rt", errors="replace").read().splitlines()
        n_stl_a = sum(1 for x in la if stl_re.match(x)); n_stl_b = sum(1 for x in lb if stl_re.match(x))
        if ignore_stl:
            la = [x for x in la if not stl_re.match(x)]; lb = [x for x in lb if not stl_re.match(x)]
        ta, tb = (a / n / "sim_ticks").read_text().strip(), (b / n / "sim_ticks").read_text().strip()
        ok = la == lb and ta == tb
        same += ok
        rows.append(dict(name=n, ok=ok, ticks=(ta, tb), lines=(len(la), len(lb)), stl_lines=(n_stl_a, n_stl_b)))
    return dict(a=str(a), b=str(b), ignore_stl=ignore_stl, n=len(rows), identical=same,
                not_identical=[r for r in rows if not r["ok"]], rows=rows)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("testdir"); p.add_argument("out")
    p.add_argument("--limit", type=int, default=10**9); p.add_argument("--jobs", type=int, default=16)
    p.add_argument("--keep-traces"); p.add_argument("--label", default="")
    c = sub.add_parser("compare")
    c.add_argument("a"); c.add_argument("b"); c.add_argument("--ignore-stl", action="store_true")
    c.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "compare":
        res = compare(Path(a.a), Path(a.b), a.ignore_stl)
        if a.out:
            Path(a.out).write_text(json.dumps(res, indent=1))
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
        return
    testdir = Path(a.testdir).resolve()
    keep = Path(a.keep_traces).resolve() if a.keep_traces else None
    cache_setup = (os.environ.get("SIMSPECT_CACHE_SETUP") or "warm").strip().lower()
    pairs = []
    for s in sorted((testdir / "asm").glob("*.s"))[:a.limit]:
        an = testdir / "ann" / (s.stem + ".ann.json")
        if an.exists():
            pairs.append((s, an))
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda q: one(q[0], q[1], keep, cache_setup), pairs))
    env = {k: os.environ.get(k) for k in sorted(os.environ) if k.startswith("SIMSPECT_") or k == "TMPDIR"}
    summ = summary(res, a.label)
    Path(a.out).write_text(json.dumps(dict(env=env, summary=summ, records=res), indent=1, default=str))
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()

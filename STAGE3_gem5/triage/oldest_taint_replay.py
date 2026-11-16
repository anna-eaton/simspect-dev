#!/usr/bin/env python3
"""oldest_taint_replay.py -- offline replay of gem5-recon's STT taint tracker on a traced rerun (agent rstltriage, 2026-11-16).

Purpose: the store-shadow analogue of rsa8_trace.py for branch transmitters (R-SA-8 / UV3, "only the oldest taint source").
In the store-shadow corpus the transmitter branch is never in the delay unit (shape B of DECIDE RL-12): the oldest-source taint
is already freed when the branch reaches the IQ, so rsa8_trace's "inserted, then released early" signature cannot fire. This
script decides shape B per test from the trace alone (no gem5 change), the way diag_recon_physreg16 does (S3/S4):

  replay the tracker twice over the whole Rename trace, with gem5's exact rules (src/cpu/o3/rename.cc:714-720,
  secure_scheme/taint_tracker.cc:44-131 insert/propagate/getOldestTaint, :134-185 free/clean, decode.cc:686-695 shadow
  insertion, shadow_tracker.cc:162-300 shadow lifting; std::map insert never overwrites, phys flat 16 and invalid regs skipped,
  FP loads never speculative), stepping per tick in gem5's order (rename, then shadow/taint ticks at the end of the tick):
    OLDEST: gem5's rule (a dest inherits only the oldest tainted source);
    UNION : identical except a dest inherits every tainted source (the counterfactual "keep all sources").
  Shape B holds when ALL of:
    B1 the hit reproduces in this rerun and the transmitter branch micro-op (first, pre-squash instance) never entered the
       delay unit (no "Inserting branch [sn:B]") and resolved mispredicted before the store's stl_release;
    B2 gem5 itself agrees with OLDEST: the replayed insert counts equal stats.txt insertedTaints / insertedTaintInsts and
       allowlistedTaintsFromTT == 0, revealRequests == 0 (no ReCon reveal untaint);
    B3 OLDEST: no branch source tainted when the branch enters the IQ (the first addIfReady, inst_queue.cc:1446-1456);
    B4 UNION : a branch source IS tainted then, with the annotated bypass load L among its sources, and L stays speculative
       (its store shadow) past the branch's mispredict resolve;
    B5 the merge that replaced L by an older source O is located (instruction, its disasm), and O's speculation lifted
       before the branch entered the IQ.
  Conservative: rename block parse problems, unknown loads/stores, a branch shadow on O's speculation status (resolve tick
  is an upper bound only via the hook) -> 'unsure', never shape B.
Approximations, both toward 'not shape B': a load counts as speculative at decode only if an older store executes at or
after its rename tick (decode is earlier); store address valid = its LSQ "Executing store" tick (never earlier in gem5).
Usage: oldest_taint_replay.py <run dir with trace.txt.gz, result.json, ts/X/stl_bypass/ann/*.ann.json> [...] [--json out]
"""
import argparse, gzip, json, re, sys
from collections import defaultdict
from pathlib import Path

R_TICK = re.compile(r"^\s*(\d+): ")   # gem5 right-aligns ticks below 1e6
R_PROC = re.compile(r"system\.cpu\.rename: \[tid:0\] Processing instruction \[sn:(\d+)\]")
R_SRC = re.compile(r"Looking up (\w+?)RegClass arch reg (\d+), got phys reg (\d+) \((\w+?)RegClass\)")
R_FLAT = re.compile(r"Register (\d+) \(flat: (\d+)\) \((\w+?)RegClass\)")
R_DST = re.compile(r"Renaming arch reg (\d+) \((\w+?)RegClass\) to physical reg (\d+) \((\d+)\)")
R_DST_ANY = re.compile(r"Renaming arch reg \d+ \(")
R_LDINS = re.compile(r"lsq\.thread0: Inserting load PC .*\[sn:(\d+)\]")
R_STINS = re.compile(r"lsq\.thread0: Inserting store PC .*\[sn:(\d+)\]")
R_STEX = re.compile(r"lsq\.thread0: Executing store PC .*\[sn:(\d+)\]")
R_COMMIT = re.compile(r"system\.cpu\.commit: \[tid:0\] \[sn:(\d+)\] Committing instruction")
R_SQUASH = re.compile(r"system\.cpu\.rename: \[tid:0\] \[squash sn:(\d+)\] Squashing instructions")
R_IQ = re.compile(r"system\.cpu\.iew: \[tid:0\] Issue: Adding PC .* \[sn:(\d+)\] \[tid:0\] to IQ")
R_DU = re.compile(r"Inserting branch \[sn:(\d+)\] into delay_unit")
R_DUREL = re.compile(r"Released tainted branch \[sn:\d+\] from delay_unit")   # prints a pointer, not the sn (delay_unit.cc:153)
R_LDEX = re.compile(r"lsq\.thread0: Executing load PC .*\[sn:(\d+)\]")
R_DULD = re.compile(r"delay_unit: Inserted tainted load \[sn:(\d+)\]")
R_DULDREL = re.compile(r"delay_unit: Released tainted load \[sn:(\d+)\]")
R_FETCH = re.compile(r"^O3PipeView:fetch:(\d+):0x([0-9a-f]+):(\d+):(\d+):\s+(\S+) : (.*)$")
R_BRV = re.compile(r"O3PipeView:simspect:(\d+):BR:resolve_visible:.*:seq=(\d+):pc=(0x[0-9a-f]+):.*mispred=(\d)")


def parse(trace):
    ren = {}                     # sn -> dict(tick, srcs[(cls,phys,flat)], dsts[(cls,phys,flat)], n_dst_any)
    cur = None
    loads, stores, st_exec, commit, iq, du = set(), set(), {}, {}, {}, set()
    squashes, fetch, brv, decode, du_ins, du_rel = [], {}, {}, {}, {}, []
    ld_exec, du_ld_ins, du_ld_rel = {}, {}, {}
    last_fetch = None
    with gzip.open(trace, "rt", errors="replace") as f:
        for line in f:
            if line.startswith("O3PipeView:fetch:"):
                m = R_FETCH.match(line.rstrip("\n"))
                if m:
                    last_fetch = int(m.group(4))
                    fetch.setdefault(last_fetch, (int(m.group(2), 16), m.group(5), m.group(6).strip()))
                continue
            if line.startswith("O3PipeView:decode:"):
                dt = int(line.split(":")[2])
                if last_fetch is not None and dt:
                    decode.setdefault(last_fetch, dt)
                last_fetch = None
                continue
            if "BR:resolve_visible" in line:
                m = R_BRV.search(line)
                if m:
                    brv.setdefault(int(m.group(2)), (int(m.group(1)), m.group(3), int(m.group(4))))
                continue
            mt = R_TICK.match(line)
            if not mt:
                continue
            t = int(mt.group(1))
            if "system.cpu.rename" in line:
                m = R_PROC.search(line)
                if m:
                    sn = int(m.group(1)); cur = dict(tick=t, srcs=[], dsts=[], n_dst_any=0, flats={}); ren[sn] = cur
                    continue
                m = R_SQUASH.search(line)
                if m:
                    squashes.append((t, int(m.group(1)))); cur = None; continue
                if cur is not None:
                    for m in R_SRC.finditer(line):
                        cur["srcs"].append((m.group(4), int(m.group(3)))); cur.setdefault("src_arch", []).append((m.group(1), int(m.group(2))))
                    for m in R_FLAT.finditer(line):
                        cur["flats"][(m.group(3), int(m.group(1)))] = int(m.group(2))
                    for m in R_DST.finditer(line):
                        cur["dsts"].append((m.group(2), int(m.group(3)), int(m.group(4)))); cur.setdefault("dst_arch", []).append((m.group(2), int(m.group(1))))
                    cur["n_dst_any"] += len(R_DST_ANY.findall(line))
                continue
            for rx, coll in ((R_LDINS, loads), (R_STINS, stores)):
                m = rx.search(line)
                if m:
                    coll.add(int(m.group(1)))
            m = R_STEX.search(line)
            if m:
                st_exec.setdefault(int(m.group(1)), t)
            m = R_LDEX.search(line)
            if m:
                ld_exec.setdefault(int(m.group(1)), []).append(t)
            m = R_DULD.search(line)
            if m:
                du_ld_ins.setdefault(int(m.group(1)), t)
            m = R_DULDREL.search(line)
            if m:
                du_ld_rel.setdefault(int(m.group(1)), t)
            m = R_COMMIT.search(line)
            if m:
                commit.setdefault(int(m.group(1)), t)
            m = R_IQ.search(line)
            if m:
                iq.setdefault(int(m.group(1)), t)
            m = R_DU.search(line)
            if m:
                du.add(int(m.group(1))); du_ins.setdefault(int(m.group(1)), t)
            if R_DUREL.search(line):
                du_rel.append(t)
    # loads squashed before dispatch never reach "Inserting load": take the fetch micro-op mnemonic too (ld, ldst, ldis, ldfp...)
    loads |= {s for s, fe in fetch.items() if fe[2].split()[0].startswith("ld") if fe[2]}
    # stores squashed before dispatch were still in the decode-time shadow list (decode.cc:689-690) until the squash
    stores |= {s for s, fe in fetch.items() if s in decode and fe[2] and fe[2].split()[0] in ("st", "stfp", "stul", "stis", "stsplit")}
    return dict(ld_exec=ld_exec, du_ld_ins=du_ld_ins, du_ld_rel=du_ld_rel, decode=decode, du_ins=du_ins, du_rel=du_rel, ren=ren, loads=loads, stores=stores, st_exec=st_exec, commit=commit, iq=iq, du=du,
                squashes=squashes, fetch=fetch, brv=brv)


def is_cond_branch(fe):
    return fe is not None and fe[1].startswith("J") and not fe[1].startswith("JMP") and fe[2].startswith(("wrip", "br"))


def is_fp_load(fe, rec):
    return (fe is not None and fe[2].startswith(("ldfp", "ldifp"))) or any(c == "Float" or c == "Vec" for c, _, _ in rec["dsts"])


def replay(P, union, horizon):
    ren, sq = P["ren"], sorted(P["squashes"])
    fetch = P["fetch"]
    sns = sorted(ren)
    squashed_at = {}
    born = {s: ren[s]["tick"] for s in sns}
    for s, d in P["decode"].items():
        born[s] = min(born.get(s, d), d)
    for t, n in sq:                                        # every sn > n decoded/renamed by t is squashed at t
        for s, b in born.items():
            if s > n and b <= t and s not in squashed_at:
                squashed_at[s] = t
    INF = 1 << 62
    stores = sorted(s for s in P["stores"])
    conds = sorted(s for s in sns if is_cond_branch(fetch.get(s)))
    spec, lift, unsure = {}, {}, {}
    for s in sns:
        if s not in P["loads"]:
            continue
        rt = P["decode"].get(s, ren[s]["tick"]); shadows = []
        for st in stores:
            if st >= s:
                break
            ex = P["st_exec"].get(st, squashed_at.get(st, INF))
            if ex >= rt and squashed_at.get(st, INF) > rt:
                shadows.append(("store", st, ex))
        for b in conds:
            if b >= s:
                break
            rv = P["brv"].get(b, (squashed_at.get(b, INF),))[0]
            if rv >= rt and squashed_at.get(b, INF) > rt:
                shadows.append(("branch", b, rv))
        fp = is_fp_load(fetch.get(s), ren[s])
        spec[s] = bool(shadows) and not fp
        lift[s] = min(max(x[2] for x in shadows) if shadows else 0, squashed_at.get(s, INF))
        unsure[s] = any(x[0] == "branch" for x in shadows)
    # events: rename at tick (before), end-of-tick frees
    taints = {}                                            # (cls, phys) -> frozenset of source sns (OLDEST: 1 element)
    n_ins, n_tinsts = 0, 0
    by_tick = defaultdict(list)
    for s in sns:
        if ren[s]["tick"] <= horizon:
            by_tick[ren[s]["tick"]].append(s)
    def dead(src, t):                                      # source no longer holds its taint at end of tick t
        return P["commit"].get(src, INF) <= t or squashed_at.get(src, INF) <= t or lift.get(src, INF) <= t
    def prune(tt, t):
        nt = {}
        for k, v in tt.items():
            live = frozenset(x for x in v if not dead(x, t))
            if live:
                nt[k] = live if union else v
        return nt
    snaps, at_rename = {}, {}
    ticks = sorted(set(by_tick) | set(P["iq"].values()) | {x for v in P["ld_exec"].values() for x in v})
    for t in ticks:
        if t > horizon:
            break
        # cleanTaints + freeTaints at the end of every earlier tick: a key goes when its (OLDEST) source is dead;
        # UNION keeps the live sources
        taints = prune(taints, t - 1)
        snaps[t] = dict(taints)                            # what rename and IEW see at tick t (before this tick's frees)
        for s in sorted(by_tick.get(t, [])):
            r = ren[s]; dsts = [d for d in r["dsts"]]
            if s in P["loads"] and spec.get(s):
                n_tinsts += r["n_dst_any"]
                for c, p, fl in dsts:
                    if fl == 16:
                        continue
                    n_ins += 1
                    taints.setdefault((c, p), frozenset([s]))
            else:
                srcs = [taints[k] for k in r["srcs"] if k in taints]
                if not srcs:
                    continue
                new = frozenset().union(*srcs) if union else frozenset([min(min(x) for x in srcs)])
                at_rename[s] = (frozenset().union(*srcs), new, {k: taints[k] for k in r["srcs"] if k in taints})
                for c, p, fl in dsts:
                    if fl == 16:
                        continue
                    n_ins += 1
                    taints.setdefault((c, p), new)
    return dict(at_rename=at_rename, snaps=snaps, n_ins=n_ins, n_tinsts=n_tinsts, spec=spec, lift=lift, unsure=unsure, squashed_at=squashed_at)


def state_at(R, t):
    ks = [k for k in R["snaps"] if k <= t]
    return R["snaps"][max(ks)] if ks else {}


def analyze(d):
    d = Path(d); res = json.loads((d / "result.json").read_text()); rec = res.get("record") or {}
    kind = rec.get("xmit_kind") or "br_x"
    out = dict(tag=res.get("tag"), stem=res.get("stem"), kind=kind, hit=bool(rec.get("issued_in_window")), status=rec.get("status"))
    if not out["hit"]:
        out["verdict"] = "not reproduced"; return out
    stl = rec.get("stl") or {}; ps = (stl.get("per_store") or [{}])[0]
    rel, lsn = ps.get("release_tick"), ps.get("load_sn")
    P = parse(d / "trace.txt.gz")
    xpc = int(rec["xmit_pc"], 16) if rec.get("xmit_pc") else None
    if kind == "br_x":
        cand = sorted(s for s, (tk, pc, mp) in P["brv"].items() if int(pc, 16) == xpc and mp == 1 and tk < (rel or 1 << 62))
        X = cand[0] if cand else None
        signal = P["brv"][X][0] if X is not None else None            # the mispredict resolve (redirect)
        tchk = P["iq"].get(X)                                          # first addIfReady: IQ insertion (inst_queue.cc:1446-1456)
        du_in, du_out = (X in P["du"]), None
        ti = P["du_ins"].get(X)
    else:
        signal = rec.get("xmit_signal")
        # the X instance whose execution is the scored signal (the checker's stl.xmit_sn is the first instance, which an
        # unrelated memory-order squash can replace by a re-fetched one inside the store window)
        xs = [s for s, ts in P["ld_exec"].items() if P["fetch"].get(s, (None,))[0] == xpc and signal in ts]
        X = xs[0] if xs else stl.get("xmit_sn")
        out["xmit_sn_checker"] = stl.get("xmit_sn")
        tchk = min(P["ld_exec"].get(X, [0]) or [0]) or None           # STT checks a load's taint at execute (lsq_unit.cc:2095)
        ti = P["du_ld_ins"].get(X); du_in = ti is not None; du_out = P["du_ld_rel"].get(X)
    if X is None or lsn is None or signal is None:
        out["verdict"] = "unsure: transmitter instance / load sn not found"; return out
    lpcs = {int(x, 16) for x in ps.get("loads", [])}
    # every annotated bypass load micro-op of the first instance older than X (the checker's load_sn can be a macro-op's first,
    # non-load micro-op; a test can annotate several loads of one store; an RMW transmitter can itself be an annotated load)
    Ls = [s for s in range(lsn, lsn + 12) if s in P["loads"] and P["fetch"].get(s, (None,))[0] in lpcs and s < X]
    if not Ls:
        out["verdict"] = "unsure: annotated load micro-op not found"; return out
    out.update(xmit_sn=X, xmit_disasm="{}: {}".format(*P["fetch"].get(X, (0, "?", "?"))[1:]), signal=signal, check_tick=tchk,
               stl_release=rel, load_sns=Ls)
    stats = {}
    for l in res.get("stats", []):
        p = l.split()
        if len(p) > 1:
            stats[p[0].split(".")[-1]] = p[1]
    gi, gt = int(stats.get("insertedTaints", -1)), int(stats.get("insertedTaintInsts", -1))
    al, rv = int(stats.get("allowlistedTaintsFromTT", -1)), int(stats.get("revealRequests", -1))
    full = max(P["ren"][s]["tick"] for s in P["ren"])
    O = replay(P, False, full); U = replay(P, True, full)
    out.update(du_inserted=du_in, du_insert_tick=ti, replay_inserts=O["n_ins"], gem5_inserts=gi, replay_taintinsts=O["n_tinsts"],
               gem5_taintinsts=gt, allowlisted=al, reveal_requests=rv,
               load_spec={s: O["spec"].get(s) for s in Ls}, load_lift={s: O["lift"].get(s) for s in Ls},
               load_disasm={s: "{}: {}".format(*P["fetch"].get(s, (0, "?", "?"))[1:]) for s in Ls},
               load_fp=all(is_fp_load(P["fetch"].get(s), P["ren"].get(s, {"dsts": []})) for s in Ls))
    if X not in P["ren"] or not tchk:
        out["verdict"] = "unsure: transmitter rename / check tick not traced"; return out
    tq = ti if ti is not None else tchk                                 # the tick STT first judged X
    srcs = P["ren"][X]["srcs"]
    so, su = state_at(O, tq), state_at(U, tq)
    o_src = sorted({x for k in srcs if k in so for x in so[k]}); u_src = sorted({x for k in srcs if k in su for x in su[k]})
    out.update(oldest_sources_at_check=o_src, union_sources_at_check=u_src)
    # backward register slice of X (rename producers) and the merge where the OLDEST rule dropped L for an older source O
    prod = {}
    for s in sorted(P["ren"]):
        if s >= X:
            break
        for c, p, fl in P["ren"][s]["dsts"]:
            prod[(c, p)] = s
    seen, stack = set(), [X]
    while stack:
        s = stack.pop()
        for k in P["ren"][s]["srcs"]:
            q = prod.get(k)
            if q is None or q in seen or q >= s:
                continue
            seen.add(q); stack.append(q)
    slice_sns = sorted(seen)
    out["slice"] = [f"sn{s} {P['fetch'].get(s, (0, '?', '?'))[1]}: {P['fetch'].get(s, (0, '?', '?'))[2]}" for s in slice_sns][-14:]
    out["L_in_slice"] = [s for s in Ls if s in seen]
    merge = None
    for s in slice_sns + [X]:
        if s <= min(Ls) or s not in O["at_rename"] or s not in U["at_rename"]:
            continue
        osrc = min(O["at_rename"][s][1]); usrc = U["at_rename"][s][0]
        lin = [x for x in Ls if x in usrc]
        if lin and osrc < max(lin):
            fe = P["fetch"].get(s, (0, "?", "?"))
            # carrier of O into the merge: a CC (flags) source, the mov's old-destination operand (gem5's Mov reads its
            # destination, regop.isa:702-704), or an ordinary data source
            r = P["ren"][s]; carriers = set(); darch = set(r.get("dst_arch", []))
            for i, k in enumerate(r["srcs"]):
                if osrc not in U["at_rename"][s][2].get(k, ()):
                    continue
                ca = (r.get("src_arch") or [None] * len(r["srcs"]))[i]
                # pure register moves (no memory operand: MOV_R_R, MOVD/MOVQ xmm<->gpr) do not read their destination on
                # x86; gem5's micro-ops do (old destination / partial xmm half), so that operand is a false dependency
                pure_move = fe[1].startswith("MOV") and "_M" not in fe[1] and "_I" not in fe[1]
                carriers.add("flags" if k[0] == "CC" else f"old_dest({fe[1]})" if pure_move and ca in darch else "data")
            merge = dict(sn=s, disasm=f"{fe[1]}: {fe[2]}", older_source=osrc,
                         older_source_disasm="{}: {}".format(*P["fetch"].get(osrc, (0, "?", "?"))[1:]),
                         older_source_pc=hex(P["fetch"].get(osrc, (0,))[0]),
                         older_lift=min(O["lift"].get(osrc, 1 << 62), P["commit"].get(osrc, 1 << 62), O["squashed_at"].get(osrc, 1 << 62)),
                         older_lift_branch_shadow=O["unsure"].get(osrc), carrier=sorted(carriers))
            break
    out["merge"] = merge
    common = dict(
        counts_no_reveal=(gi == O["n_ins"] and gt == O["n_tinsts"] and al == 0 and rv == 0),
        union_has_L=any(x in u_src and O["spec"].get(x) and (O["lift"].get(x) or 0) > signal for x in Ls),
        signal_before_release=rel is not None and signal < rel,
        merge_found=bool(merge))   # branch shadows are exact: resolve_visible is printed where branchResolved(true) is set (commit.cc:1478-1490)
    od = (merge or {}).get("older_lift") or 1 << 62
    # shape B: never in the delay unit; the oldest-source taint is already dead when STT first judges X
    okB = dict(common, never_in_du=not du_in, oldest_clean_at_check=not o_src, older_dead_before_check=od < tq)
    # shape A: in the delay unit with only the older source O, released one cycle after O's taint died (delayUnit.tick runs
    # before taintTracker.tick in CPU::tick, cpu.cc:487-492). Loads print their sn on release; branches print a pointer
    # (delay_unit.cc:153), so for a branch any release line in that cycle is accepted.
    if kind == "br_x":
        rels = [x for x in P["du_rel"] if ti is not None and ti <= x <= signal]
        tr = next((x for x in rels if od < x <= od + 1000), None)
    else:
        tr = du_out if (du_out is not None and od < du_out <= od + 1000 and du_out <= signal) else None
    first_L = min((x for x in Ls if x in u_src), default=None)
    okA = dict(common, in_du=du_in, release_after_older_death=tr is not None,
               oldest_is_older_only=bool(o_src) and first_L is not None and max(o_src) < first_L)
    out.update(du_release_tick=tr, checks_B=okB, checks_A=okA)
    if all(okB.values()):
        out["verdict"] = "R-SA-8 shape B (store shadow)"
    elif all(okA.values()):
        out["verdict"] = "R-SA-8 shape A (store shadow)"
    else:
        fa = [k for k, v in okA.items() if not v]; fb = [k for k, v in okB.items() if not v]
        out["verdict"] = "not R-SA-8: " + ("A fails " + ",".join(fa) if du_in else "B fails " + ",".join(fb))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("dirs", nargs="+"); ap.add_argument("--json"); a = ap.parse_args()
    allr = {}
    for d in a.dirs:
        try:
            r = analyze(d)
        except Exception as e:
            import traceback; r = dict(verdict="error: " + traceback.format_exc()[-600:])
        allr[Path(d).name] = r
        print(Path(d).name, r.get("verdict"), {k: r.get(k) for k in ("replay_inserts", "gem5_inserts", "replay_taintinsts", "gem5_taintinsts")}, flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(allr, indent=1))

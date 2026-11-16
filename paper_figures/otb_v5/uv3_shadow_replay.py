#!/usr/bin/env python3
"""uv3_shadow_replay.py -- which older load is a UV3 (R-SA-8) transmitter's taint root, and how does it reach the transmitter?
(agent fig8-otb-v5, 2026-11-16, for DECIDE UV3-EVID (c), Anna: report the 17 tests whose transmitter is visibly held and released.)

Replays gem5-recon-modded's speculation and taint rules over one kept trace (O3PipeView + LSQUnit + Commit + DelayUnit + Rename):
  * shadows (decode.cc:685-695, shadow_tracker.cc): at decode a conditional branch micro-op (Jcc `wrip`, microcode `br`) or a store
    micro-op opens a shadow; a load decoded while any shadow is open is speculative; it stops being speculative once every older
    shadow is freed (branch: its BR:resolve_visible tick, else its complete tick; store: its LSQ "Executing store" tick, i.e. its
    address is valid).
  * taint (rename.cc:714-720, taint_tracker.cc:44-155): a load still speculative at its rename taints its destinations with
    itself; any other micro-op gives all its destinations the OLDEST root among its tainted sources; a root's taints are freed once
    it is no longer speculative; flat Int phys 16 is skipped; a phys reg keeps its first taint.
Checks: predicted release of the transmitter = first cycle after its root O stops being speculative, compared with the trace's
"Released tainted branch" tick (one is printed per released branch; the tick must match).
How O reaches the transmitter (static reachability over the same micro-op graph, frees ignored), under four models:
  GEM5    every renamed source;
  NOMOV   minus the destination read of a full-width `mov D, D, S` micro-op (MOV_R_R, CQO's first micro-op, ...);
  NOCC    minus flags (CC) sources that real x86 does not have: a flags source of a micro-op whose x86 instruction does not
          consume flags (only Jcc, SETcc, CMOVcc, ADC, SBB, RCL, RCR do) is dropped for its non-flag destinations, and also for
          its flag destinations unless the instruction leaves some defined flags unchanged (INC, DEC, ROL, ROR, RCL, RCR, BT*,
          CMC, CLC, STC, SAHF); gem5 reads the old flags to merge the bits an instruction does not write (e.g. AF for TEST);
  REAL    NOMOV and NOCC together (an approximation of x86 semantics).
Verdict for O: 'mov' if O is unreachable under NOMOV; 'flags' if unreachable under NOCC but reachable under NOMOV; 'mov+flags'
if reachable under each alone but not under REAL; 'real operand' if reachable under REAL.
Usage: uv3_shadow_replay.py <run dir with pipeview.txt.gz and ts/X/<mode>/ann/<stem>.ann.json> [...] [--json out]"""
import glob, gzip, json, re, sys
from pathlib import Path

R_PROC = re.compile(r"^\s*(\d+): system\.cpu\.rename: \[tid:0\] Processing instruction \[sn:(\d+)\]")
R_SRC = re.compile(r"Looking up (\w+?)RegClass arch reg (\d+), got phys reg (\d+) \((\w+?)RegClass\)")
R_DST = re.compile(r"Renaming arch reg (\d+) \((\w+?)RegClass\) to physical reg (\d+) \((\d+)\)")
R_LD = re.compile(r"lsq\.thread0: Inserting load PC .*\[sn:(\d+)\]")
R_STEX = re.compile(r"^\s*(\d+): system\.cpu\.iew\.lsq\.thread0: Executing store PC .*\[sn:(\d+)\]")
R_FETCH = re.compile(r"^O3PipeView:fetch:(\d+):0x([0-9a-f]+):(\d+):(\d+):\s+(.*)$")
R_BRV = re.compile(r"O3PipeView:simspect:(\d+):BR:resolve_visible:.*:seq=(\d+):pc=")
R_PF = re.compile(r"BR:predict_force:.*:seq=(\d+):pc=(0x[0-9a-f]+):")
R_DUIN = re.compile(r"^\s*(\d+): system\.cpu\.delay_unit: Inserting branch \[sn:(\d+)\]")
R_DUREL = re.compile(r"^\s*(\d+): system\.cpu\.delay_unit: Released tainted branch")
FULL = re.compile(r"^(r[a-d]x|r[sd]i|r[sb]p|r\d+|e[a-d]x|e[sd]i|r\d+d)$")
FLAGUSE = ("J", "SET", "CMOV", "ADC", "SBB", "RCL", "RCR")
# x86 instructions that leave some defined flags unchanged (their new flags really depend on the old ones)
FLAGKEEP = ("INC", "DEC", "ROL", "ROR", "RCL", "RCR", "BT", "CMC", "CLC", "STC", "SAHF")


def parse(W):
    pv = {}; cur = None; ren = {}; rcur = None; loads = set(); stex = {}; brv = {}; pf = {}; duin = []; durel = []
    for l in gzip.open(W / "pipeview.txt.gz", "rt", errors="replace"):
        l = l.rstrip("\n")
        if l.startswith("O3PipeView:") and not l.startswith("O3PipeView:simspect"):
            m = R_FETCH.match(l)
            if m:
                cur = int(m.group(4))
                if cur not in pv:
                    dis = m.group(5).strip()
                    pv[cur] = dict(pc=int(m.group(2), 16), upc=int(m.group(3)), dis=dis, macro=dis.split(" : ")[0].strip(),
                                   uop=(dis.split(" : ", 1)[1].split() or [""])[0] if " : " in dis else dis)
                else:
                    cur = None
                continue
            p = l.split(":")
            if cur is not None and len(p) > 2 and p[1] in ("decode", "rename", "dispatch", "issue", "complete", "retire") and int(p[2]) > 0:
                pv[cur].setdefault(p[1], int(p[2]))
            continue
        m = R_BRV.search(l)
        if m:
            brv.setdefault(int(m.group(2)), int(m.group(1))); continue
        m = R_PF.search(l)
        if m:
            pf.setdefault(int(m.group(2), 16), int(m.group(1))); continue
        m = R_PROC.match(l)
        if m:
            rcur = int(m.group(2))
            if rcur in ren:
                rcur = None
            else:
                ren[rcur] = dict(tick=int(m.group(1)), src=[], dst=[])
            continue
        m = R_LD.search(l)
        if m:
            loads.add(int(m.group(1))); continue
        m = R_STEX.match(l)
        if m:
            stex.setdefault(int(m.group(2)), int(m.group(1))); continue
        m = R_DUIN.match(l)
        if m:
            duin.append((int(m.group(1)), int(m.group(2)))); continue
        m = R_DUREL.match(l)
        if m:
            durel.append(int(m.group(1))); continue
        if rcur is None:
            continue
        m = R_SRC.search(l)
        if m:
            ren[rcur]["src"].append((m.group(1), int(m.group(2)), int(m.group(3)))); continue
        m = R_DST.search(l)
        if m:
            ren[rcur]["dst"].append((m.group(2), int(m.group(1)), int(m.group(3)), int(m.group(4))))
    return pv, ren, loads, stex, brv, pf, duin, durel


def one(W):
    W = Path(W)
    ann = json.load(open(glob.glob(str(W / "ts/X/*/ann/*.ann.json"))[0]))
    xaddr = ann["xmit"]["addr"]; fnc = ann["commit_boundary"]["first_noncommitted"]["addr"]
    pv, ren, loads, stex, brv, pf, duin, durel = parse(W)
    wsn = pf.get(fnc); xf = pf.get(xaddr)
    xs = [s for s in pv if pv[s]["pc"] == xaddr and xf is not None and 0 <= xf - s <= 3 and pv[s]["uop"] == "wrip"] or \
         [s for s in pv if pv[s]["pc"] == xaddr and xf is not None and abs(s - xf) <= 3 and pv[s]["uop"] == "wrip"]
    xsn = min(xs) if xs else xf
    # shadows
    shadows = []
    for s, r in pv.items():
        if "decode" not in r:
            continue
        cond = (r["uop"] == "wrip" and r["macro"].startswith("J") and not r["macro"].startswith("JMP")) or r["uop"] == "br"
        store = r["uop"] in ("st", "stis", "stfp", "stul") or r["uop"].startswith("st")
        # a shadow is freed when resolved (branch) / its address is valid (store); one that never gets there was squashed or
        # committed (cleanVector), so it is freed by its retire tick or, if squashed, by its last recorded stage
        last = max(v for k, v in r.items() if k in ("decode", "rename", "dispatch", "issue", "complete", "retire"))
        if cond:
            free = brv.get(s) or r.get("complete") or r.get("retire") or last
            shadows.append((s, r["decode"], free))
        elif store and s not in loads:
            shadows.append((s, r["decode"], stex.get(s) or r.get("retire") or last))
    shadows.sort()
    spec_end = {}
    for L in loads:
        if L not in pv or "decode" not in pv[L] or L not in ren:
            continue
        dec = pv[L]["decode"]
        older = [f for (s, d, f) in shadows if s < L and d <= dec]
        if older and max(older) > dec:
            spec_end[L] = max(older)
    # taint replay with frees, in rename-tick order
    order = sorted(ren, key=lambda s: (ren[s]["tick"], s))
    taint = {}; xroot = None; xren = None
    for s in order:
        t = ren[s]["tick"]
        for k in [k for k, root in taint.items() if spec_end.get(root, 0) < t]:
            del taint[k]
        srcs = [(c, p) for c, a, p in ren[s]["src"]]
        if s in loads and spec_end.get(s, 0) > t:
            o = s
        else:
            ts = [taint[k] for k in srcs if k in taint]
            o = min(ts) if ts else None
        if o is not None:
            for c, a, p, flat in ren[s]["dst"]:
                if c == "Int" and flat == 16:
                    continue
                taint.setdefault((c, p), o)
        if s == xsn:
            xroot, xren = o, t
            break
    pred_rel = (spec_end.get(xroot) + 500) if xroot in spec_end else None
    xin = [t for t, s in duin if s == xsn]
    # static reachability under the four models (seeds = loads speculative at rename)
    seeds = {L for L in spec_end if L in ren and spec_end[L] > ren[L]["tick"] and L <= xsn}
    def mov_destread(s, c, a):
        r = pv.get(s, {})
        if r.get("uop") != "mov" or c != "Int":
            return False
        ops = [o.strip() for o in r["dis"].split(" : ", 1)[1].split(None, 1)[1].split(",")] if " : " in r.get("dis", "") else []
        return bool(ops) and bool(FULL.match(ops[0])) and any(d[0] == c and d[1] == a for d in ren[s]["dst"])
    reach = {}; merge = {}
    for model in ("GEM5", "NOMOV", "NOCC", "REAL"):
        roots = {}
        for s in sorted(ren):
            if s > xsn:
                break
            r = pv.get(s, {})
            flaguse = r.get("macro", "").startswith(FLAGUSE)
            flagkeep = r.get("macro", "").startswith(FLAGKEEP)
            per_dst = []
            for c, a, p, flat in ren[s]["dst"]:
                if c == "Int" and flat == 16:
                    continue
                u = set()
                for sc, sa, sp in ren[s]["src"]:
                    if model in ("NOMOV", "REAL") and mov_destread(s, sc, sa):
                        continue
                    if model in ("NOCC", "REAL") and sc == "CC" and not flaguse and (c != "CC" or not flagkeep):
                        continue
                    u |= roots.get((sc, sp), set())
                if s in seeds:
                    u = {s}
                per_dst.append(((c, p), u))
            if model == "GEM5" and xroot is not None and wsn is not None and not merge.get("sn"):
                srcroots = {(sc, sa, sp): roots.get((sc, sp), set()) for sc, sa, sp in ren[s]["src"]}
                allr = set().union(*srcroots.values()) if srcroots else set()
                if xroot in allr and any(x > wsn for x in allr):
                    merge.update(sn=s, pc=hex(r.get("pc", 0)), dis=r.get("dis"),
                                 o_enters_via=sorted({f"{sc} arch {sa}" + (" (mov dest read)" if mov_destread(s, sc, sa) else "")
                                                      for (sc, sa, sp), u in srcroots.items() if xroot in u}))
            for k, u in per_dst:
                roots[k] = u          # a renamed destination is a fresh value: overwrite (dataflow, not gem5's taint map)
            if s == xsn:
                xr = set()
                for sc, sa, sp in ren[s]["src"]:
                    xr |= roots.get((sc, sp), set())
                reach[model] = sorted(xr)
    O = xroot
    if O is None:
        verdict = "transmitter untainted at rename"
    else:
        inm = {m: (O in reach.get(m, [])) for m in reach}
        if not inm["GEM5"]:
            verdict = "O not reachable in static model (check)"
        elif not inm["NOMOV"] and inm["NOCC"]:
            verdict = "mov"
        elif not inm["NOCC"] and inm["NOMOV"]:
            verdict = "flags"
        elif not inm["NOMOV"] and not inm["NOCC"]:
            verdict = "mov or flags (each path needs one; both cut)"
        elif not inm["REAL"]:
            verdict = "mov+flags (alternative paths)"
        else:
            verdict = "real operand"
    older_real = [r for r in reach.get("REAL", []) if wsn is not None and r < wsn]
    return dict(run=W.name, window_sn=wsn, xmit_sn=xsn, xmit_inserted_tick=(xin[0] if xin else None),
                release_ticks=durel[:4], O=O, O_dis=pv.get(O, {}).get("dis"), O_pc=hex(pv[O]["pc"]) if O in pv else None,
                O_spec_end=spec_end.get(O), predicted_release=pred_rel,
                release_matches=(pred_rel in durel) if pred_rel else False, reach=reach, verdict=verdict,
                older_roots_under_REAL=older_real, merge=merge)


if __name__ == "__main__":
    args = sys.argv[1:]; out = None
    if "--json" in args:
        i = args.index("--json"); out = args[i + 1]; del args[i:i + 2]
    allr = []
    for W in args:
        try:
            r = one(W)
        except Exception as e:
            import traceback
            r = dict(run=Path(W).name, error=traceback.format_exc(limit=2))
        allr.append(r)
        print(json.dumps({k: r.get(k) for k in ("run", "verdict", "O", "O_pc", "O_dis", "O_spec_end", "predicted_release",
                                                  "release_ticks", "release_matches", "xmit_inserted_tick", "older_roots_under_REAL", "merge", "error")}))
    if out:
        json.dump(allr, open(out, "w"), indent=1)

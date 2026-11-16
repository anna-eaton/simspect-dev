#!/usr/bin/env python3
"""older_root_paths.py -- for one R-SA-8 (UV3) rerun, how does the transmitter's OLDEST taint root reach it?
(agent fig8-otb-v5, 2026-11-16, for DECIDE UV3-EVID (c): the paper's "17 ... older operand reaches the merge through a gem5
x86 instruction that reads its destination register (mov, or cqto)").

Replays gem5-recon's rename-time taint rule (rename.cc:714-720; taint_tracker.cc:108-131: a speculative load taints its
destinations with itself, any other micro-op gives its destinations its OLDEST tainted source; flat Int phys 16 skipped; a
phys reg's first taint sticks) over the Rename trace, seeding every load of the test function (pc in [func_base, xmit addr],
sn < transmitter sn) as speculative. Three dependency models:
  GEM5    : every source gem5 renames (what ReCon sees);
  NOMOV   : drops the destination read of a full-width regop `mov D, D, S` (MOV_R_R, CQO's first micro-op, ...): the value
            does not use the old D on real x86;
  NOMOVCC : NOMOV and also drops CC (flags) sources of every non-branch micro-op (gem5 reads the old flags to merge the
            bits an instruction does not write).
Reports: transmitter (first jcc micro-op at the annotated xmit addr that reads CC), window branch, OLDEST root O of the
transmitter under GEM5, the UNION root sets under the three models, the merge micro-op (first one whose OLDEST is O while
its UNION also holds a root younger than the window branch) and the source through which O enters it.
Verdict: 'mov/cqto' if O is a root under GEM5 but not under NOMOV (every O path uses a mov destination read);
'flags' if O survives NOMOV but not NOMOVCC; 'real operand' if O survives NOMOVCC.
Usage: older_root_paths.py <run dir with pipeview.txt.gz, ts/X/<mode>/ann/<stem>.ann.json> [...] [--json out]"""
import glob, gzip, json, re, sys
from pathlib import Path

R_PROC = re.compile(r"rename: \[tid:0\] Processing instruction \[sn:(\d+)\]")
R_SRC = re.compile(r"Looking up (\w+?)RegClass arch reg (\d+), got phys reg (\d+) \((\w+?)RegClass\)")
R_DST = re.compile(r"Renaming arch reg (\d+) \((\w+?)RegClass\) to physical reg (\d+) \((\d+)\)")
R_LD = re.compile(r"lsq\.thread0: Inserting load PC .*\[sn:(\d+)\]")
R_FETCH = re.compile(r"^O3PipeView:fetch:(\d+):0x([0-9a-f]+):(\d+):(\d+):\s+(.*)$")
R_PF = re.compile(r"BR:predict_force:.*:seq=(\d+):pc=(0x[0-9a-f]+):")
FULL = re.compile(r"^(r[a-d]x|r[sd]i|r[sb]p|r\d+|e[a-d]x|e[sd]i|r\d+d)$")


def one(W):
    W = Path(W)
    ann = json.load(open(glob.glob(str(W / "ts/X/*/ann/*.ann.json"))[0]))
    xaddr = ann["xmit"]["addr"]; fnc = ann["commit_boundary"]["first_noncommitted"]["addr"]; base = ann["func_base_addr"]
    ren, cur, info, loads, pf = {}, None, {}, set(), {}
    for l in gzip.open(W / "pipeview.txt.gz", "rt", errors="replace"):
        m = R_FETCH.match(l.rstrip("\n"))
        if m:
            info.setdefault(int(m.group(4)), (int(m.group(2), 16), int(m.group(3)), m.group(5).strip())); continue
        m = R_PF.search(l)
        if m:
            pf.setdefault(int(m.group(2), 16), int(m.group(1))); continue
        m = R_PROC.search(l)
        if m:
            cur = int(m.group(1))
            if cur in ren:
                cur = None
            else:
                ren[cur] = dict(src=[], dst=[])
            continue
        m = R_LD.search(l)
        if m:
            loads.add(int(m.group(1))); continue
        if cur is None:
            continue
        m = R_SRC.search(l)
        if m:
            ren[cur]["src"].append((m.group(1), int(m.group(2)), int(m.group(3)))); continue
        m = R_DST.search(l)
        if m:
            ren[cur]["dst"].append((m.group(2), int(m.group(1)), int(m.group(3)), int(m.group(4))))
    wsn = pf.get(fnc); xfirst = pf.get(xaddr)
    if xfirst is None or wsn is None:
        return dict(run=W.name, error="no predict_force for xmit or fnc")
    # transmitter = the micro-op at the xmit addr (same macro-op instance, sn >= xfirst - 2) that reads CC and is a wrip
    cands = [s for s in ren if info.get(s, (0,))[0] == xaddr and abs(s - xfirst) <= 3 and "wrip" in info[s][2]]
    xsn = min(cands) if cands else xfirst
    seeds = {s for s in loads if s < xsn and s in info and base <= info[s][0] <= xaddr and s in ren}
    def is_mov_destread(sn, cls, arch):
        dis = info.get(sn, (0, 0, ""))[2]
        mn = dis.split(":", 1)[1].split() if ":" in dis else []
        if not mn or mn[0] != "mov":
            return False
        ops = [o.strip() for o in " ".join(mn[1:]).split(",")]
        if not ops or not FULL.match(ops[0]):
            return False
        return any(d[0] == cls and d[1] == arch for d in ren[sn]["dst"])
    def is_branch(sn):
        d = info.get(sn, (0, 0, ""))[2]
        return "wrip" in d or d.split(" ")[0].startswith("J")
    res = {}
    for model in ("GEM5", "NOMOV", "NOMOVCC"):
        oldest, union, merges = {}, {}, []
        for sn in sorted(ren):
            if sn > xsn or (seeds and sn < min(seeds)):
                continue
            srcs = []
            for cls, arch, phys in ren[sn]["src"]:
                if model in ("NOMOV", "NOMOVCC") and cls == "Int" and is_mov_destread(sn, cls, arch):
                    continue
                if model == "NOMOVCC" and cls == "CC" and not is_branch(sn):
                    continue
                srcs.append((cls, arch, phys))
            if sn in seeds:
                o, u = sn, {sn}
            else:
                ts = [oldest[(c, p)] for c, a, p in srcs if (c, p) in oldest]
                o = min(ts) if ts else None
                u = set().union(*[union[(c, p)] for c, a, p in srcs if (c, p) in union]) if any((c, p) in union for c, a, p in srcs) else set()
                if o is not None and o < wsn and any(r > wsn for r in u) and model == "GEM5":
                    ent = [f"{c} arch {a}" + (" (mov dest read)" if c == "Int" and is_mov_destread(sn, c, a) else "")
                           for c, a, p in srcs if (c, p) in oldest and oldest[(c, p)] == o]
                    merges.append(dict(sn=sn, dis=info.get(sn, (0, 0, "?"))[2], pc=hex(info.get(sn, (0,))[0]), oldest=o,
                                       union=sorted(u), o_enters_via=ent))
            for cls, arch, phys, flat in ren[sn]["dst"]:
                if cls == "Int" and flat == 16:
                    continue
                if o is not None:
                    oldest.setdefault((cls, phys), o)
                if u:
                    union.setdefault((cls, phys), set(u))
            if sn == xsn:
                res[model] = dict(oldest=o, union=sorted(u))
        if model == "GEM5":
            res["merges"] = merges[:3]
    O = res["GEM5"]["oldest"]
    if O is None:
        verdict = "transmitter untainted in replay"
    elif O not in res["NOMOV"]["union"]:
        verdict = "mov/cqto"
    elif O not in res["NOMOVCC"]["union"]:
        verdict = "flags"
    else:
        verdict = "real operand"
    older_real = [r for r in res["NOMOVCC"]["union"] if r < wsn]
    return dict(run=W.name, window_sn=wsn, xmit_sn=xsn, xmit_dis=info.get(xsn, (0, 0, "?"))[2], seeds=sorted(seeds),
                O=O, O_dis=info.get(O, (0, 0, "?"))[2] if O else None, verdict=verdict,
                older_roots_without_false_reads=older_real, **res)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--json"]
    out = None
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]; args.remove(out)
    allr = []
    for W in args:
        try:
            r = one(W)
        except Exception as e:
            r = dict(run=Path(W).name, error=repr(e))
        allr.append(r)
        print(json.dumps({k: r.get(k) for k in ("run", "verdict", "O", "O_dis", "window_sn", "xmit_sn", "older_roots_without_false_reads", "error")}))
        for m in r.get("merges", [])[:1]:
            print("   merge:", json.dumps(m))
    if out:
        json.dump(allr, open(out, "w"), indent=1)

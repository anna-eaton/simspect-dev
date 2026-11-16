#!/usr/bin/env python3
"""uv5_census_cmp.py (agent uv5why 2026-11-16; copy of uv5_timing_scan.py + per-pair S/U form tallies, both modes). Original doc: uv5_timing_scan.py (run e.g. ssh cafe3 "docker exec -i gem5_dev python3 - <testset> mispredict_not_taken 200000 1" < this): static UV5-shape precondition counts (not_taken mode), read-only.
For each test: committed loads U (pc < fnc), squashed loads S (pc > first unresolved branch >= fnc),
static line of each address when it is lea(rsp)+disp (frame is 64-aligned in both corpora? reported),
and an address-ready estimate (dataflow depth from the mfence: ALU=1, load=4, idiv=20, others 1).
usage: uv5_timing_scan.py <testset_dir> <mode> <sample_n> <seed> [stems...]"""
import json, os, re, sys, random, collections
ts, mode, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
asmd = os.path.join(ts, mode, "asm"); annd = os.path.join(ts, mode, "ann")
if len(sys.argv) > 5: stems = sys.argv[5:]
else:
    stems = sorted(f[:-2] for f in os.listdir(asmd) if f.endswith(".s"))
    random.Random(seed).shuffle(stems); stems = stems[:n]
LBL = re.compile(r"^__litmus_\w+?_pc(\d+):$")
REG = re.compile(r"%([a-z0-9]+)")
R64 = {"eax":"rax","ebx":"rbx","ecx":"rcx","edx":"rdx","esi":"rsi","edi":"rdi","al":"rax","cl":"rcx","dl":"rdx"}
def norm(r):
    r = R64.get(r, r)
    if re.fullmatch(r"r\d+[dwb]", r): r = re.sub(r"[dwb]$", "", r)
    return r
def code(l): return l.split("#", 1)[0].strip()
def split_ops(a): return [x.strip() for x in re.split(r",(?![^(]*\))", a)] if a else []
C = collections.Counter(); ex = []
for st in stems:
    try:
        raw = open(os.path.join(asmd, st + ".s")).read().splitlines()
        ann = json.load(open(os.path.join(annd, st + ".ann.json")))
    except Exception:
        C["unreadable"] += 1; continue
    C["tests"] += 1
    cb = ann.get("commit_boundary", {}); fnc = cb.get("first_noncommitted", {}).get("pc")
    brs = sorted(a["branch_pc"] for a in ann.get("annotations", []))
    ubr = [b for b in brs if fnc is not None and b >= fnc]
    if fnc is None or not ubr: C["skip_no_fnc_or_branch"] += 1; continue
    br0 = ubr[0]
    # region: after the last 'mfence' before the first litmus label
    lines = [code(l) for l in raw]
    first_lbl = next(i for i, l in enumerate(lines) if LBL.match(l))
    start = max(i for i in range(first_lbl) if lines[i] == "mfence") + 1
    ready = collections.defaultdict(int); lea_off = {}
    cur = None; seen_pc_instr = set(); acc = []
    for l in lines[start:]:
        if not l: continue
        m = LBL.match(l)
        if m: cur = int(m.group(1)); continue
        if l.endswith(":") or l.startswith("."): 
            if l.startswith(".LBB") or l.startswith(".Ltmp"): 
                if "end_block" in l or True: pass
            continue
        parts_ = l.split(None, 1); op = parts_[0]; args = parts_[1] if len(parts_) > 1 else ""; ops = split_ops(args.strip())
        if op in ("retq", "popq"): break
        mem = [o for o in ops if "(" in o]
        addr_regs = [norm(r) for o in mem for r in REG.findall(o)]
        nonmem = [o for o in ops if "(" not in o]
        dst = None
        if ops and "(" not in ops[-1] and ops[-1].startswith("%") and not op.startswith(("cmp", "test")): dst = norm(ops[-1][1:])
        srcs = [norm(r) for o in nonmem[:-1] if o.startswith("%") for r in REG.findall(o)] if dst else [norm(r) for o in nonmem for r in REG.findall(o)]
        two_op = op.rstrip("q") in ("add","sub","and","or","xor","shl","shr","sar","imul","adc","sbb","not","neg","inc","dec") or op.startswith(("cmov",))
        if dst and two_op: srcs.append(dst)
        if op.startswith("idiv") or op.startswith("div"): srcs += ["rax", "rdx"]; dst = "rax"
        if op == "cqto": srcs = ["rax"]; dst = "rdx"
        a_ready = max([ready[r] for r in addr_regs if r not in ("rsp", "rbp")] + [0])
        lat = 20 if op.startswith(("idiv","div")) else (4 if (mem and not op.startswith("lea") and dst) else 1)
        t = max([ready[r] for r in srcs if r not in ("rsp","rbp")] + [a_ready if mem else 0]) + lat
        if op.startswith("lea") and mem:
            mm = re.match(r"(-?\d*)\(%(rsp|rbp)\)$", mem[0])
            if mm and dst: lea_off[dst] = int(mm.group(1) or 0)
            elif dst: lea_off.pop(dst, None)
        elif dst:
            lea_off.pop(dst, None)
        if mem and not op.startswith("lea") and cur is not None and cur not in seen_pc_instr:
            seen_pc_instr.add(cur)
            mo = mem[0]; mm = re.match(r"(-?\d*)\(%(\w+)(?:,%(\w+))?", mo)
            if mm is None:  # e.g. "(,%rdx)" (index-only, scale 1): treat as index form with unknown base
                mm2 = re.match(r"(-?\d*)\(,%(\w+)", mo); disp = int(mm2.group(1) or 0) if mm2 else 0
                base = norm(mm2.group(2)) if mm2 else "?"; idx = None
            else:
                disp = int(mm.group(1) or 0); base = norm(mm.group(2)); idx = mm.group(3)
            if idx and base not in ("rsp", "rbp") and base not in lea_off and norm(idx) in lea_off:
                base, idx = norm(idx), base  # load_swapidx form "(%data,%lea)": the lea register is the index
            off = (lea_off.get(base, None) if base not in ("rsp","rbp") else 0)
            off = None if off is None else off + disp
            is_store = mo == ops[-1] and len(ops) > 1 and not (op.startswith("or") and ops[0] == "$0")
            kind = "st" if is_store else ("rmw" if op.startswith("or") and ops[0] == "$0" else "ld")
            acc.append(dict(pc=cur, kind=kind, off=off, idx=bool(idx), aready=a_ready, xmm=bool(dst and dst.startswith("xmm"))))
        elif cur is not None:
            seen_pc_instr.add(cur)
        if dst: ready[dst] = t
    U = [a for a in acc if a["pc"] < fnc and a["kind"] in (("ld", "rmw") if os.environ.get("U_RMW") else ("ld",))]
    S = [a for a in acc if a["pc"] > br0 and a["kind"] in ("ld", "rmw")]
    if U: C["A_has_committed_load"] += 1
    if any(u["aready"] > 1 for u in U): C["A2_committed_load_addr_needs_a_producer(>1)"] += 1
    if any(u["aready"] >= 4 for u in U): C["A3_committed_load_addr_behind_load_or_div(>=4)"] += 1
    if U and S: C["B_committed_load_and_squashed_load"] += 1
    pairs = []
    for u in U:
        for s in S:
            same = None
            if u["off"] is not None and s["off"] is not None and not u["idx"] and not s["idx"]:
                same = (u["off"] // 64 == s["off"] // 64)
            elif u["off"] is not None and s["off"] is not None:
                same = abs(u["off"] - s["off"]) < 64  # index unknown: maybe
            pairs.append((u, s, same))
    if any(p[2] for p in pairs): C["C_same_line_pair(static)"] += 1
    cp = [p for p in pairs if p[2]]
    if cp:
        C["C_S_forms:" + "+".join(sorted({p[1]["kind"] for p in cp}))] += 1
        C["C_U_forms:" + "+".join(sorted({"xmm" if p[0]["xmm"] else "gpr" for p in cp}))] += 1
        if any(p[1]["kind"] == "ld" for p in cp): C["C_some_pair_S_plain_ld"] += 1
        if any(p[1]["kind"] == "ld" and p[0]["aready"] > p[1]["aready"] for p in cp): C["D_some_pair_S_plain_ld"] += 1
        if any(p[1]["kind"] == "ld" and p[0]["aready"] >= p[1]["aready"] for p in cp): C["CD_ge_some_pair_S_plain_ld"] += 1
    allS = S
    for s_ in allS: C["S_all_kind:" + s_["kind"]] += 1
    for u_ in U: C["U_all_form:" + ("xmm" if u_["xmm"] else "gpr")] += 1
    if any(p[2] and p[0]["aready"] > p[1]["aready"] for p in pairs):
        C["D_same_line_and_U_addr_later_than_S"] += 1; ex.append(st)
        if any(p[2] and p[0]["aready"] >= p[1]["aready"] + 3 for p in pairs): C["D2_same_line_U_later_by>=3"] += 1
    if any(p[2] and p[0]["aready"] == p[1]["aready"] for p in pairs): C["  same_line_U_addr_same_time"] += 1
    if any(p[2] and p[0]["aready"] < p[1]["aready"] for p in pairs): C["  same_line_U_addr_earlier"] += 1
    C[f"ncommitted_{min(fnc,3)}"] += 1
    if os.environ.get("DUMP"):
        cp = [p for p in pairs if p[2]]
        print("STEM", st, "C" if cp else "-", "D" if any(p[0]["aready"] > p[1]["aready"] for p in cp) else "-",
              ",".join(f'{p[0]["pc"]}{"x" if p[0]["xmm"] else "g"}{p[0]["aready"]}/{p[1]["pc"]}{p[1]["kind"]}{p[1]["aready"]}' for p in cp), file=sys.stderr)
print(json.dumps(dict(sorted(C.items())), indent=1)); print("D examples:", ex[:15])
if os.environ.get("DBG"): print(acc, U, S)

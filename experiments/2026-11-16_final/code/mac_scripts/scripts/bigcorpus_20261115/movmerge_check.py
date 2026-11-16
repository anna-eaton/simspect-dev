#!/usr/bin/env python3
"""movmerge_check.py -- static check of the E2LT-2 shape on R-SA-8 candidates (agent bigcorpus, 2026-11-16): does the transmitter
branch's condition depend, through a reg-reg `mov`, on the OLD value of the mov's destination register, where that old value was
produced by a load? gem5's x86 `mov` micro-op reads its own destination (regop.isa:702-704, URGENT_TODO E2LT-2), so such a mov merges
an older load's taint into the chain (the "x86 mov false dependency"). Static only (no gem5): build the binary (gem5_common.build_binary),
objdump it, start at the instruction at the annotation's xmit addr (the transmitter jcc), take the flag-setting instruction before it,
and walk register definitions backward (within the function body, straight-line) to loads. Reported per key: movmerge (bool), the mov
and the load it merges, the chain. Approximate (straight-line, register-only; memory dependencies not followed); a negative is not proof.
Usage (code root): movmerge_check.py --testset <dir with <mode>/asm,ann> --keys keys.txt --out out.json
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "STAGE3_gem5")
import gem5_common as gc

R64 = {"al": "rax", "eax": "rax", "rax": "rax", "bl": "rbx", "ebx": "rbx", "rbx": "rbx", "cl": "rcx", "ecx": "rcx", "rcx": "rcx", "dl": "rdx",
       "edx": "rdx", "rdx": "rdx", "sil": "rsi", "esi": "rsi", "rsi": "rsi", "dil": "rdi", "edi": "rdi", "rdi": "rdi"}
for i in range(8, 16):
    for s in ("", "d", "w", "b"):
        R64[f"r{i}{s}"] = f"r{i}"


def regs(op):
    return [R64[r] for r in re.findall(r"%([a-z0-9]+)", op) if r in R64]


def parse(binary, func):
    out = subprocess.check_output(["objdump", "-d", "--no-show-raw-insn", str(binary)], text=True)
    ins, on = [], False
    for l in out.splitlines():
        if l.endswith(f"<{func}>:"):
            on = True; continue
        if on and re.match(r"^[0-9a-f]+ <", l) and "<__litmus_" not in l:
            break
        m = re.match(r"\s*([0-9a-f]+):\s+(\S+)\s*(.*)", l)
        if on and m:
            ins.append((int(m.group(1), 16), m.group(2), m.group(3).split("#")[0].strip()))
    return ins


def defs_uses(mn, ops):
    """(dest reg or None, source regs, is_load, is_regreg_mov) for AT&T 'mn src, dst'."""
    parts = [p.strip() for p in re.split(r",(?![^(]*\))", ops)] if ops else []
    dst = parts[-1] if parts else ""; srcs = parts[:-1]
    d = regs(dst)[0] if (dst.startswith("%") and regs(dst)) else None
    if mn.startswith(("cmp", "test", "j", "push")):    # no register destination
        return None, [r for p in parts for r in regs(p)], any("(" in p for p in parts), False
    load = any("(" in s for s in srcs)
    use = [r for s in srcs for r in regs(s)]
    regreg = mn.startswith("mov") and len(parts) == 2 and parts[0].startswith("%") and parts[1].startswith("%")
    if d and not mn.startswith("mov") and not mn.startswith("lea"):
        use.append(d)                       # two-operand ALU reads its destination
    return d, use, load, regreg


def reaches_load(ins, k, depth=0):
    """index of a load in the straight-line backward slice of the value defined at ins[k] (None if none; prologue stack/zeroing loads excluded)."""
    if k is None or depth > 40:
        return None
    d, use, load, _ = defs_uses(ins[k][1], ins[k][2])
    if load and "%rsp" not in ins[k][2] and "%rbp" not in ins[k][2]:
        return k
    if load:
        return None
    for r in set(use):
        p = next((j for j in range(k - 1, -1, -1) if defs_uses(ins[j][1], ins[j][2])[0] == r), None)
        hit = reaches_load(ins, p, depth + 1)
        if hit is not None:
            return hit
    return None


def check(s_path, ann_path, work):
    b = gc.build_binary(Path(s_path), Path(work)); ins = parse(b, Path(s_path).stem)
    xaddr = gc.resolve_pc(b, Path(s_path).stem, gc.load_annotation(Path(ann_path))["xmit"])
    idx = next((i for i, x in enumerate(ins) if x[0] == xaddr), None)
    if idx is None:
        return {"error": f"xmit addr {hex(xaddr)} not found"}
    j = next((i for i in range(idx - 1, -1, -1) if ins[i][1].startswith(("cmp", "test"))), None)
    if j is None:
        return {"error": "no flag-setting instruction before the transmitter"}
    want = set(defs_uses(ins[j][1], ins[j][2])[1]) | set(regs(ins[j][2])); chain = [f"{hex(ins[j][0])} {ins[j][1]} {ins[j][2]}"]; merges = []
    for i in range(j - 1, -1, -1):
        a, mn, ops = ins[i]; d, use, load, regreg = defs_uses(mn, ops)
        if d not in want:
            continue
        chain.append(f"{hex(a)} {mn} {ops}"); want.discard(d)
        if regreg:
            # gem5's mov also reads the OLD destination: find that register's previous definition
            prev = next((k for k in range(i - 1, -1, -1) if defs_uses(ins[k][1], ins[k][2])[0] == d), None)
            ld = reaches_load(ins, prev) if prev is not None else None
            if ld is not None:
                merges.append(dict(mov=f"{hex(a)} {mn} {ops}", old_dest_def=f"{hex(ins[prev][0])} {ins[prev][1]} {ins[prev][2]}",
                                   merged_load=f"{hex(ins[ld][0])} {ins[ld][1]} {ins[ld][2]}"))
        if not load:
            want |= set(use)
    return dict(movmerge=bool(merges), merges=merges, chain=chain[:30])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--testset", required=True); ap.add_argument("--keys", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); res = {}
    for k in [l.strip() for l in open(a.keys) if l.strip()]:
        m, s = k.split("/", 1)
        with tempfile.TemporaryDirectory(prefix="mm_") as w:
            try:
                res[k] = check(f"{a.testset}/{m}/asm/{s}.s", f"{a.testset}/{m}/ann/{s}.ann.json", w)
            except Exception as e:
                res[k] = {"error": str(e)[-300:]}
    json.dump(res, open(a.out, "w"), indent=1)
    print("keys", len(res), "movmerge", sum(1 for v in res.values() if v.get("movmerge")), "errors", sum(1 for v in res.values() if "error" in v))


if __name__ == "__main__":
    main()

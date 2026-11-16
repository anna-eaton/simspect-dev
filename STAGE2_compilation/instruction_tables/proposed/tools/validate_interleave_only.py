#!/usr/bin/env python3
"""Validate the interleave-only instruction table on real gem5 builds (ilv-vocab, 2026-11-12).

For every entry of instruction_tables/proposed/interleave_only.jsonc (``entries`` and ``probe_only``) this
builds a tiny static x86-64 program that runs the entry's inline-asm template exactly as parsexml would emit
it (operands substituted to concrete registers, ``$$`` -> ``$``, ``\\0A`` -> newline, ``${n:k|w|b}`` -> sub-
register names, ``${:uid}`` -> a unique id), on several register assignments (inputs distinct, inputs equal,
inputs = rcx/rdx) and four input vectors. Before each template every GPR except rsp holds a known constant;
after it the program stores the result ($0) and the XOR of every register that must be preserved. The
program writes those words to stdout (write syscall) and exits 0. No libc.

Ground truth = the same binary run natively on the host CPU. Each gem5 build runs it with that build's
run-config flags (binary, config_script, cpu_type, --caches, --scheme, extra_args; no debug flags, no hooks,
since there is no branch to force). An entry passes on a build iff: gem5 exits 0, the program's output equals
the native output, the preserved-register XOR equals the expected value (S1), and gem5's stdout/stderr have
no warn/panic/fatal/"unimplemented"/"Unrecognized" line that the baseline program (no template) does not
also produce.

Usage (inside gem5_dev on a node):
  python3 validate_interleave_only.py --table interleave_only.jsonc --workdir <dir> --jobs 8 \
      --build NAME=<run_config.jsonc> [--build ...]  > <dir>/validate.log 2>&1
Writes <dir>/validate_results.json and a summary table to stdout. Every gem5 tmp dir it creates lives under
<workdir>/runs/ and is deleted at the end unless --keep.
"""
import argparse, concurrent.futures as cf, datetime, json, os, re, shutil, subprocess, sys, traceback

GPRS = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]
SUB = {  # 32 / 16 / 8-bit names
    "rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"), "rdx": ("edx", "dx", "dl"),
    "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil"), "rbp": ("ebp", "bp", "bpl"),
    **{f"r{i}": (f"r{i}d", f"r{i}w", f"r{i}b") for i in range(8, 16)},
}
CONST = {r: (0x1111111111111111 * (i + 1) ^ 0x0F0F0F0F00000000) & 0xFFFFFFFFFFFFFFFF for i, r in enumerate(GPRS)}
# register scenarios: ($0, $1, $2); $0 is never rax/rcx/rdx (parsexml.py _fv2_dead)
SCENARIOS = [("r12", "rsi", "rdi"), ("r13", "rax", "rax"), ("r9", "rcx", "rdx"), ("r15", "r8", "rbx")]
VECTORS = [(0x0123456789ABCDEF, 0xFEDCBA9876543210), (5, 0), (0, 0x8000000000000000), (0xFFFFFFFFFFFFFFFF, 3)]
WARN_RE = re.compile(r"(warn|panic|fatal|unimplemented|Unrecognized|unknown instruction)", re.I)


def log(msg):
    print(f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}", flush=True)


def load_jsonc(path):
    """Strip // comments outside strings, then json.loads."""
    out, s, i, n, ins = [], open(path).read(), 0, None, False
    n = len(s)
    while i < n:
        c = s[i]
        if ins:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(s[i + 1]); i += 2; continue
            if c == '"':
                ins = False
        elif c == '"':
            ins = True; out.append(c)
        elif c == "/" and i + 1 < n and s[i + 1] == "/":
            while i < n and s[i] != "\n":
                i += 1
            continue
        else:
            out.append(c)
        i += 1
    txt = re.sub(r",(\s*[}\]])", r"\1", "".join(out))
    return json.loads(txt)


def render(asm, ops, uid):
    """parsexml inline-asm text -> GNU as text, operands bound to registers."""
    t = asm.replace("\\0A", "\n")
    t = t.replace("${:uid}", str(uid))
    def mod(m):
        reg = ops[int(m.group(1))]
        return "%" + SUB[reg]["kwb".index(m.group(2))]
    t = re.sub(r"\$\{(\d):([kwb])\}", mod, t)
    t = t.replace("$$", "\x00")
    t = re.sub(r"\$(\d)", lambda m: "%" + ops[int(m.group(1))], t)
    return t.replace("\x00", "$")


def make_program(ent, scen):
    """Return (asm_text, expected_preserved_xor_per_vector, n_words)."""
    d, s1, s2 = scen
    form = ent.get("form", "rr")
    lines = [".globl _start", ".text", "_start:", "  subq $512, %rsp", "  movq %rsp, %rbp"]
    # rbp holds the buffer pointer, so it is excluded from the preserved set (it is never written by a template)
    preserved = [r for r in GPRS if r not in (d, "rbp")]
    exp = []
    for vi, (v1, v2) in enumerate(VECTORS):
        for r in GPRS:
            if r == "rbp":
                continue
            lines.append(f"  movabsq ${CONST[r]:#x}, %{r}")
        vals = {}
        if form == "rr":
            lines.append(f"  movabsq ${v1:#x}, %{s1}")
            vals[s1] = v1
            if s2 != s1:
                lines.append(f"  movabsq ${v2:#x}, %{s2}")
                vals[s2] = v2
        lines.append(f"ilvT{vi}:")
        lines.append(render(ent["asm"], [d, s1, s2], f"{vi}"))
        lines.append(f"ilvE{vi}:")
        lines.append(f"  movq %{d}, {vi * 16}(%rbp)")
        lines.append(f"  movq %{preserved[0]}, %{d}")
        x = vals.get(preserved[0], CONST[preserved[0]])
        for r in preserved[1:]:
            lines.append(f"  xorq %{r}, %{d}")
            x ^= vals.get(r, CONST[r])
        lines.append(f"  movq %{d}, {vi * 16 + 8}(%rbp)")
        exp.append(x)
    nbytes = 16 * len(VECTORS)
    lines += ["  movq $1, %rax", "  movq $1, %rdi", "  movq %rbp, %rsi", f"  movq ${nbytes}, %rdx", "  syscall",
              "  movq $60, %rax", "  xorq %rdi, %rdi", "  syscall", ""]
    return "\n".join(lines), exp


def build(asm_text, wd):
    os.makedirs(wd, exist_ok=True)
    sp, op, bp = os.path.join(wd, "t.s"), os.path.join(wd, "t.o"), os.path.join(wd, "t")
    open(sp, "w").write(asm_text)
    r = subprocess.run(["as", "-o", op, sp], capture_output=True, text=True)
    if r.returncode:
        return None, "as: " + r.stderr.strip()
    r = subprocess.run(["ld", "-static", "-o", bp, op], capture_output=True, text=True)
    if r.returncode:
        return None, "ld: " + r.stderr.strip()
    return bp, None


def words(b):
    return [int.from_bytes(b[i:i + 8], "little") for i in range(0, len(b), 8)]


def run_native(bp):
    r = subprocess.run([bp], capture_output=True, timeout=10)
    return r.returncode, r.stdout


def gem5_cmd(cfg, bp, outdir, outfile):
    g = cfg["gem5"]
    cmd = [g["binary"], f"--outdir={outdir}", g["config_script"], f"--cmd={bp}",
           f"--cpu-type={g.get('cpu_type', 'DerivO3CPU')}"]
    if g.get("caches", True):
        cmd.append("--caches")
    cmd.append(f"--scheme={g.get('scheme', 2)}")
    cmd += list(g.get("extra_args") or [])
    cmd.append(f"--output={outfile}")
    return cmd


def run_gem5(cfg, bp, wd, timeout):
    outdir = os.path.join(wd, "m5out")
    outfile = os.path.join(wd, "prog.out")
    cmd = gem5_cmd(cfg, bp, outdir, outfile)
    gdir = cfg["gem5"]["binary"].split("/build/")[0]
    env = dict(os.environ, TMPDIR="/tmp")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=gdir, env=env)
    except subprocess.TimeoutExpired:
        return {"rc": "timeout", "out": b"", "warn": [], "cmd": cmd}
    out = open(outfile, "rb").read() if os.path.exists(outfile) else b""
    w = sorted(set(l.strip() for l in (r.stdout + r.stderr).splitlines() if WARN_RE.search(l)))
    return {"rc": r.returncode, "out": out, "warn": w, "cmd": cmd,
            "tail": (r.stderr.strip().splitlines() or [""])[-3:]}


# gem5-spt backward untaint (defense_src/spt_0d2be0f/src/cpu/o3/rob_impl.hh:850-881): a microop whose name is a
# SUBSTRING (strstr) of this list with a non-zero-register dest, or a microop named exactly "mov", untaints a
# source when its dest is untainted.
SPT_BWD_OPCODES = "add,addi,adc,adci,sub,subi,sbb,sbbi"
EXEC_RE = re.compile(r"@ilvT0(?:\+\d+)?\.\d+\s+:\s+(\S+)\s+:\s+(\S+)\s+(.*?)\s+:\s+(\w+)\s+:")


def microops(cfg, bp, wd, timeout):
    """Run the s0 program with --debug-flags=Exec; return [(macroop, microop, operands, fu_class)] of vector 0's template."""
    outdir = os.path.join(wd, "m5exec")
    cmd = gem5_cmd(cfg, bp, outdir, os.path.join(wd, "prog_exec.out"))
    cmd.insert(2, "--debug-flags=Exec")
    gdir = cfg["gem5"]["binary"].split("/build/")[0]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=gdir, env=dict(os.environ, TMPDIR="/tmp"))
    ops = []
    for l in r.stdout.splitlines():
        m = EXEC_RE.search(l)
        if m:
            ops.append((m.group(1), m.group(2), m.group(3).strip(), m.group(4)))
    return ops


def spt_bwd(ops):
    hits = []
    for mac, mic, opnds, fu in ops:
        dest = opnds.split(",")[0].strip()
        if (mic in SPT_BWD_OPCODES and dest != "t0") or mic == "mov":
            hits.append(f"{mac}:{mic}")
    return hits


def norm_warn(w):
    # drop tick numbers / addresses so baseline lines compare equal
    return re.sub(r"0x[0-9a-f]+|\b\d+\b", "N", w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--build", action="append", required=True, help="NAME=run_config.jsonc")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--only", default="", help="comma list of entry names")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--microops", default="", help="build NAME: also record each entry's gem5 microops/FU classes (Exec trace, scenario s0, vector 0)")
    a = ap.parse_args()
    log(f"START validate_interleave_only table={a.table} workdir={a.workdir} jobs={a.jobs} builds={a.build}")
    tab = load_jsonc(a.table)
    ents = [dict(e, _probe=False) for e in tab["entries"]] + [dict(e, _probe=True) for e in tab.get("probe_only", [])]
    if a.only:
        keep = set(a.only.split(","))
        ents = [e for e in ents if e["name"] in keep]
    ents = [{"name": "__baseline__", "form": "none", "asm": "", "_probe": False}] + ents
    builds = {}
    for b in a.build:
        name, path = b.split("=", 1)
        builds[name] = load_jsonc(path)
        log(f"build {name}: {gem5_cmd(builds[name], '<bin>', '<out>', '<file>')}")
    runs = os.path.join(a.workdir, "runs")
    os.makedirs(runs, exist_ok=True)

    # 1) build + native ground truth
    prog = {}
    for e in ents:
        for si, scen in enumerate(SCENARIOS):
            if e.get("form", "rr") == "none" and si > 0:
                continue
            key = (e["name"], si)
            wd = os.path.join(runs, f"{e['name']}__s{si}")
            asm_text, exp = make_program(e, scen)
            bp, err = build(asm_text, wd)
            if err:
                prog[key] = {"err": err, "wd": wd}
                log(f"BUILD-FAIL {e['name']} s{si}: {err}")
                continue
            rc, out = run_native(bp)
            w = words(out)
            pres_ok = len(w) == 2 * len(VECTORS) and all(w[2 * i + 1] == exp[i] for i in range(len(VECTORS)))
            prog[key] = {"bp": bp, "wd": wd, "native_rc": rc, "native": out, "native_pres_ok": pres_ok,
                         "results": [hex(w[2 * i]) for i in range(len(w) // 2)]}
            log(f"native {e['name']} s{si} rc={rc} preserved_ok={pres_ok} results={prog[key]['results']}")

    # 2) gem5 on every build
    jobs = []
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for key, p in prog.items():
            if "bp" not in p:
                continue
            for bn, cfg in builds.items():
                wd = os.path.join(p["wd"], bn)
                os.makedirs(wd, exist_ok=True)
                jobs.append((key, bn, ex.submit(run_gem5, cfg, p["bp"], wd, a.timeout)))
        res = {}
        for key, bn, fu in jobs:
            try:
                res[(key, bn)] = fu.result()
            except Exception:
                res[(key, bn)] = {"rc": "exc", "out": b"", "warn": [traceback.format_exc()], "cmd": []}

    micro = {}
    if a.microops:
        with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            fut = {k[0]: ex.submit(microops, builds[a.microops], p["bp"], p["wd"], a.timeout)
                   for k, p in prog.items() if k[1] == 0 and "bp" in p}
            for name, fu in fut.items():
                try:
                    ops = fu.result()
                    micro[name] = {"microops": ops, "spt_bwd_hits": spt_bwd(ops)}
                except Exception:
                    micro[name] = {"error": traceback.format_exc()}
                log(f"MICROOPS {name} @ {a.microops}: {micro[name]}")

    base_warn = {}
    for bn in builds:
        r = res.get((("__baseline__", 0), bn))
        base_warn[bn] = set(norm_warn(w) for w in (r or {}).get("warn", []))
        log(f"baseline {bn}: rc={r and r['rc']} warn={sorted(base_warn[bn])}")

    # 3) verdicts
    summary = {}
    for e in ents:
        name = e["name"]
        if name == "__baseline__":
            continue
        per = {}
        for bn in builds:
            probs = []
            for si in range(len(SCENARIOS)):
                p = prog.get((name, si))
                if p is None:
                    continue
                if "err" in p:
                    probs.append(f"s{si} build: {p['err'][:200]}"); continue
                if p["native_rc"] != 0:
                    probs.append(f"s{si} native rc={p['native_rc']}")
                if not p["native_pres_ok"]:
                    probs.append(f"s{si} native: preserved-register XOR mismatch (template writes a register other than $0)")
                r = res[((name, si), bn)]
                if r["rc"] != 0:
                    probs.append(f"s{si} gem5 rc={r['rc']} tail={r.get('tail')}")
                if r["out"] != p["native"]:
                    probs.append(f"s{si} gem5 output {[hex(x) for x in words(r['out'])]} != native {[hex(x) for x in words(p['native'])]}")
                neww = [w for w in r["warn"] if norm_warn(w) not in base_warn[bn]]
                if neww:
                    probs.append(f"s{si} new gem5 warnings: {neww[:5]}")
            per[bn] = "ok" if not probs else probs
            log(f"VERDICT {name} @ {bn}: {'ok' if not probs else 'FAIL'}" + ("" if not probs else " | " + " ; ".join(probs)))
        summary[name] = {"probe": e["_probe"], "class": e.get("class"), "per_build": per,
                         "native_results_s0": prog.get((name, 0), {}).get("results"),
                         "microops": micro.get(name)}
    out = {"table": a.table, "builds": {k: gem5_cmd(v, "<bin>", "<out>", "<file>") for k, v in builds.items()},
           "scenarios": SCENARIOS, "vectors": [[hex(x) for x in v] for v in VECTORS], "baseline_warn": {k: sorted(v) for k, v in base_warn.items()},
           "summary": summary}
    json.dump(out, open(os.path.join(a.workdir, "validate_results.json"), "w"), indent=1)
    bn_list = list(builds)
    print("\nSUMMARY  entry | " + " | ".join(bn_list))
    for name, s in summary.items():
        mo = s.get("microops") or {}
        print(f"{'PROBE ' if s['probe'] else ''}{name} | " + " | ".join("ok" if s["per_build"][b] == "ok" else "FAIL" for b in bn_list)
              + (f" | spt_bwd={bool(mo.get('spt_bwd_hits'))} {mo.get('spt_bwd_hits')} | uops=" + " ".join(f"{u[1]}/{u[3]}" for u in mo.get("microops", [])) if a.microops else ""))
    if not a.keep:
        shutil.rmtree(runs, ignore_errors=True)
        log(f"removed {runs}")
    log("END")


if __name__ == "__main__":
    main()

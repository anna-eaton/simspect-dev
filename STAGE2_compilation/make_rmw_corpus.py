#!/usr/bin/env python3
"""
make_rmw_corpus.py: derive the disjoint RMW corpus (STT_6_rmw) from an existing
concretized testset by post-processing its .s files. parsexml.py, the
instruction tables and the source testset are never touched.

Design: wiki/design/VOCAB_TABLES.md, "RMW agent findings (2026-11-08)" route (d)
and "### RMW disjoint corpus (2026-11-08)" (how to regenerate). RMW tests are a
separate testset that never mixes into STT_6 (except via the fanout option below).

Rewrite rule (only rule): for a test whose transmitter kind is `ld`, the single
instruction inside the transmitter's inline-asm block, right after the marker
label __litmus_<stem>_pc<xmit.pc>:, must be `movq <mem>, %<reg64>`. It becomes
`orq $0, <mem>` (value-neutral RMW on the same address: gem5 OR_M_I =
limm; ldst; or; st). The marker label stays on the instruction.

Gates (a test failing any gate is SKIPPED with a reason, never guessed):
  * xmit kind is ld; the bare annotation (llvm/<stem>.ann.json) and the XML exist;
  * the marker label occurs exactly once and its asm block holds exactly one
    instruction of the form above, or (fv2fp, 2026-11-09) that instruction followed by
    the value-neutral FP route `movq %R,%xmmN; movq $0,%R; movq %xmmN,%R` on the same
    R (liveness is then checked after the block);
  * XML: no rf edge leaves the transmitter's outreg (no Alloy-level consumer);
  * asm liveness: the destination register (any alias) is not read on any path
    from the transmitter before being fully overwritten (32/64-bit write, xor
    idiom); `ret` counts as a read of %rax; an unknown mnemonic on a path skips;
  * annotation re-resolution is faithful: re-resolving the ORIGINAL .s with
    compile_annotate's own functions reproduces the stored annotation exactly
    (after dropping the `atom` keys today's compile_annotate keeps but the stored
    STT_6 annotations lack; see strip_atoms_like);
  * after the rewrite: the disassembly at the new xmit address is an `or` with a
    zero immediate, every annotation field that existed before exists again,
    func_base is unchanged, and every absolute address shifts by exactly the
    same constant (the length change) iff it lies after the transmitter.

Annotations are re-resolved with compile_annotate.py (build_binary,
pc_offsets_from_nm, commit_offsets_from_nm, disassemble_instrs,
update_annotations), i.e. the exact procedure the asm phase uses: absolute
post-link addresses from the pc-marker labels via nm + objdump.

Fanout RMW option (RMW tests mixed into the
regular run): --fraction F --seed S selects a deterministic subset of stems,
selected iff int(sha256(f"{S}:{stem}").hexdigest()[:16], 16) / 2**64 < F (the same
stems in every mode). Only selected stems are rewritten (all gates above still
apply). --complete additionally copies every other stem's .s + .ann.json unchanged
(not selected, not an ld xmit, or skipped by a gate), so <dst> is a full mixed
corpus (RMW + plain loads), and symlinks <dst>/xml to <src>/xml. The RMW stems are
listed in <dst>/rmw_stems.tsv (mode, stem, orig instr, xmit addr). Source XML may be
Alloy text (<stem>.txt) or Alloy XML (<stem>.xml).

Selection among ELIGIBLE tests (--select eligible, the default):
the hash draw above happened BEFORE the gates, so a fraction F of all stems was drawn
and the gates then skipped about 58% of the drawn load-transmitter tests (fv2fp: 13,751
written of 65,049 ld tests per mode = 21%). With --select eligible every stem is run
through all the gates first (nothing is written), and then exactly round(F * E) of the E
eligible stems of a mode are rewritten: the E eligible stems are ranked by
int(sha256(f"{S}:{stem}").hexdigest()[:16], 16) and the lowest round(F * E) are taken.
So F is now the share of ELIGIBLE load-transmitter tests that become RMW. Deterministic
per (seed, eligible set); a stem eligible in both modes gets the same rank in both.
--select hash keeps the old behaviour (draw over all stems, then gate) byte for byte.
provenance.json records n_eligible, n_ld_source and the written share of both.
  python3 make_rmw_corpus.py --repo-root <code> --src testsets_twostage/STT_6_fv2fp_full \
      --dst testsets_twostage/STT_6_fv2fp_rmw --fraction 0.5 --seed 20261109 --complete --jobs 24

Usage (on cafe2, inside gem5_dev):
  python3 make_rmw_corpus.py --repo-root /tests/simspect_fixed_20261030 \
      --src testsets_latest/STT_6 --dst testsets_latest/STT_6_rmw \
      --modes mispredict_not_taken mispredict_taken --jobs 24 [--git-rev <mac HEAD>]
Writes <dst>/<mode>/{asm,ann}/, <dst>/provenance.json, <dst>/make_rmw_corpus.log.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import shutil
import socket
import sys
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RULE = ("ld transmitter `movq <mem>, %reg64` at the xmit pc marker -> `orq $0, <mem>` "
        "(value-neutral RMW, same address); only when the destination register has no "
        "consumer (XML rf + asm liveness); annotations re-resolved with compile_annotate.py")

REG64 = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp"] + [f"r{i}" for i in range(8, 16)]


def _family(r64: str) -> dict:
    """alias -> width for one 64-bit register."""
    if r64.startswith("r") and r64[1:].isdigit():
        return {r64: 64, r64 + "d": 32, r64 + "w": 16, r64 + "b": 8}
    b = r64[1:]                       # ax, cx, si, sp ...
    d = {r64: 64, "e" + b: 32, b: 16}
    if b in ("ax", "bx", "cx", "dx"):
        d[b[0] + "l"] = 8; d[b[0] + "h"] = 8
    else:
        d[b + "l"] = 8
    return d


ALIAS_TO_64 = {a: r for r in REG64 for a in _family(r)}
XMIT_RE = re.compile(r"^movq\s+([-\w]*\(%\w+(?:,%\w+(?:,[1248])?)?\)),\s*%(\w+)$")
LABEL_RE = re.compile(r'^("?[\w.$-]+"?):\s*$')
COND_J = {"je", "jne", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "jo", "jno",
          "js", "jns", "jp", "jnp", "jz", "jnz"}
KILL_MOVS = {"movq", "movl", "leaq", "leal", "popq", "movabsq", "movzbl", "movzwl", "movslq",
             "movzbq", "movzwq", "movsbq", "movswq", "movsbl", "movswl"}
SAFE_PREFIX = ("mov", "lea", "add", "sub", "and", "or", "xor", "not", "neg", "inc", "dec",
               "test", "cmp", "sh", "sa", "ro", "push", "pop", "mfence", "lfence", "sfence",
               "nop", "set", "cmov", "bt",
               # explicit-operand forms only; imul needs >= 2 operands (below)
               "imul", "bswap", "pxor", "por", "pand")
# implicit rax/rdx users (fv2fp division fanout): conservatively a read of rax/rdx
IMPLICIT_RAX_RDX = {"cqto", "cqo", "cltd", "idivq", "divq", "idivl", "divl"}


def _ops(s: str) -> list:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def parse_func(lines: list):
    """-> (instrs[(lineno, mnem, ops)], label->instr index). Function body only."""
    instrs, labels, pending = [], {}, []
    for ln, raw in enumerate(lines):
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        m = LABEL_RE.match(s)
        if m:
            pending.append(m.group(1).strip('"'))
            continue
        if s.startswith("."):
            continue
        parts = s.split(None, 1)
        for p in pending:
            labels[p] = len(instrs)
        pending = []
        instrs.append((ln, parts[0].lower(), _ops(parts[1]) if len(parts) > 1 else []))
    for p in pending:
        labels[p] = len(instrs)
    return instrs, labels


def classify(mnem: str, ops: list, fam: dict, r64: str) -> str:
    """'read' | 'kill' | 'none' | 'unknown' for register family `fam`."""
    if mnem in ("ret", "retq"):
        return "read" if r64 == "rax" else "none"
    pat = re.compile(r"%(" + "|".join(sorted(fam, key=len, reverse=True)) + r")\b")
    hits = [i for i, o in enumerate(ops) if pat.search(o)]
    if mnem in IMPLICIT_RAX_RDX:
        return "read" if (hits or r64 in ("rax", "rdx")) else "none"
    if mnem.startswith("j"):
        return "none" if not hits else "read"
    if not mnem.startswith(SAFE_PREFIX) or (mnem.startswith("imul") and len(ops) < 2):
        return "unknown"
    if not hits:
        return "none"
    last = ops[-1] if ops else ""
    lm = re.fullmatch(r"%(\w+)", last)
    full_w = lm and fam.get(lm.group(1)) in (32, 64)
    if mnem in KILL_MOVS and full_w and hits == [len(ops) - 1]:
        return "kill"
    if mnem in ("xorl", "xorq", "subl", "subq") and len(ops) == 2 and ops[0] == ops[1] and full_w:
        return "kill"
    return "read"


def dst_live_after(instrs, labels, xi: int, r64: str):
    """True if r64 may be read after instruction xi; None if an unknown mnemonic is reachable."""
    fam = _family(r64)
    seen, stack = set(), [xi + 1]
    while stack:
        i = stack.pop()
        if i in seen or i >= len(instrs):
            continue
        seen.add(i)
        _, m, ops = instrs[i]
        c = classify(m, ops, fam, r64)
        if c == "unknown":
            return None
        if c == "read":
            return True
        if c == "kill":
            continue
        if m in ("ret", "retq"):
            continue
        if m.startswith("j"):
            tgt = ops[0].strip('"') if ops else None
            if tgt not in labels:
                return None
            stack.append(labels[tgt])
            if m in COND_J:
                stack.append(i + 1)
            continue
        stack.append(i + 1)
    return False


def xml_outreg_consumed(txt: str, atom: str):
    def rel(n):
        m = re.search(r"^this/(?:Instruction|Operand)<:%s=\{(.*)\}$" % n, txt, re.M)
        d = collections.defaultdict(set)
        if m:
            for a, b in re.findall(r"([\w$]+)->([\w$]+)", m.group(1)):
                d[a].add(b)
        return d
    outreg, rf = rel("outreg"), rel("rf")
    return any(rf.get(o) for o in outreg.get(atom, ()))


def xml_outreg_consumed_alloyxml(txt: str, atom: str):
    """Same check as xml_outreg_consumed, for the Alloy XML instance format
    (<field label="outreg"> / <field label="rf"> tuples)."""
    def rel(n):
        m = re.search(r'<field label="%s"[^>]*>(.*?)</field>' % n, txt, re.S)
        d = collections.defaultdict(set)
        if m:
            for a, b in re.findall(r'<tuple>\s*<atom label="([^"]+)"/>\s*<atom label="([^"]+)"/>\s*</tuple>',
                                   m.group(1)):
                d[a].add(b)
        return d
    outreg, rf = rel("outreg"), rel("rf")
    return any(rf.get(o) for o in outreg.get(atom, ()))


def selected(stem: str, seed: int, fraction: float) -> bool:
    h = int(hashlib.sha256(f"{seed}:{stem}".encode()).hexdigest()[:16], 16)
    return h / 2.0 ** 64 < fraction


def addr_fields(obj, path=""):
    """Flatten every integer *addr field (absolute address) with its path."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if isinstance(v, (dict, list)):
                out.update(addr_fields(v, p))
            elif (k == "addr" or k.endswith("_addr")) and isinstance(v, int):
                out[p] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(addr_fields(v, f"{path}[{i}]"))
    return out


def key_paths(obj, path=""):
    s = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            s.add(f"{path}.{k}"); s |= key_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            s |= key_paths(v, f"{path}[{i}]")
    return s


CA = None  # compile_annotate module (set in worker init)


def _init(repo_root: str):
    global CA
    sys.path.insert(0, str(Path(repo_root) / "STAGE2_compilation"))
    import compile_annotate as ca  # noqa: E402
    CA = ca


def strip_atoms_like(new: dict, ref: dict) -> dict:
    """The stored STT_6 annotations were written by an earlier compile_annotate that
    dropped the Alloy `atom` cross-reference fields; today's keeps them. Drop every
    `atom` key the reference annotation does not have, so the schema is unchanged."""
    def walk(n, r):
        if isinstance(n, dict):
            for k in list(n):
                if k == "atom" and not (isinstance(r, dict) and "atom" in r):
                    del n[k]
                else:
                    walk(n[k], r.get(k) if isinstance(r, dict) else None)
        elif isinstance(n, list):
            for i, v in enumerate(n):
                walk(v, r[i] if isinstance(r, list) and i < len(r) else None)
    walk(new, ref)
    return new


def resolve_ann(s_text: str, stem: str, bare_ann: Path) -> tuple:
    tmp = Path(tempfile.mkdtemp(prefix=f"rmw_{stem}_"))
    try:
        s = tmp / f"{stem}.s"
        s.write_text(s_text)
        binary, base = CA.build_binary(s, tmp)
        pc_map = CA.pc_offsets_from_nm(binary, stem, base)
        commit = CA.commit_offsets_from_nm(binary, stem, base)
        instrs = CA.disassemble_instrs(binary, base)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return CA.update_annotations(bare_ann, pc_map, instrs, base, commit), instrs, base


def process(args: tuple) -> dict:
    """args = (stem, src_mode, dst_mode, xml_dir[, write]). write=False (--select eligible)
    runs every gate and returns the rewritten text/annotation in the result instead of
    writing them (keys new_text, new_ann)."""
    stem, src_mode, dst_mode, xml_dir = (args[0], Path(args[1]), Path(args[2]), Path(args[3]))
    write = args[4] if len(args) > 4 else True
    try:
        ann_p = src_mode / "ann" / f"{stem}.ann.json"
        s_p = src_mode / "asm" / f"{stem}.s"
        bare_p = src_mode / "llvm" / f"{stem}.ann.json"
        ann = json.loads(ann_p.read_text())
        x = ann.get("xmit") or {}
        if x.get("kind") != "ld":
            return dict(stem=stem, skip="xmit_kind_not_ld")
        if not bare_p.exists():
            return dict(stem=stem, skip="no_bare_ann")
        bare = json.loads(bare_p.read_text())
        atom = (bare.get("xmit") or {}).get("atom")
        xml_txt = xml_dir / f"{stem}.txt"
        xml_xml = xml_dir / f"{stem}.xml"
        if not atom or not (xml_txt.exists() or xml_xml.exists()):
            return dict(stem=stem, skip="no_xml_or_atom")
        consumed = (xml_outreg_consumed(xml_txt.read_text(), atom) if xml_txt.exists()
                    else xml_outreg_consumed_alloyxml(xml_xml.read_text(), atom))
        if consumed:
            return dict(stem=stem, skip="xml_outreg_consumed")
        text = s_p.read_text()
        lines = text.split("\n")
        safe = stem.replace("-", "_").replace(".", "_")
        lab = f"__litmus_{safe}_pc{x['pc']}:"
        idx = [k for k, l in enumerate(lines) if l.strip() == lab]
        if len(idx) != 1:
            return dict(stem=stem, skip=f"marker_count_{len(idx)}")
        body = []
        for k in range(idx[0] + 1, len(lines)):
            st = lines[k].strip()
            if st == "#NO_APP":
                break
            if st:
                body.append((k, st))
        fp_route = False
        if len(body) == 4:
            # fv2fp FP route on the transmitter's result, in the same asm block:
            #   movq <mem>, %R ; movq %R, %xmmN ; movq $0, %R ; movq %xmmN, %R
            # The last three only move R's value through xmmN and back (value-neutral for
            # R), so after the rewrite R keeps its pre-xmit value; liveness of R is then
            # checked after the whole block.
            m0 = XMIT_RE.match(body[0][1])
            if m0:
                R = m0.group(2)
                m1 = re.fullmatch(r"movq\s+%" + R + r",\s*%(xmm\d+)", body[1][1])
                if (m1 and re.fullmatch(r"movq\s+\$0,\s*%" + R, body[2][1])
                        and re.fullmatch(r"movq\s+%" + m1.group(1) + r",\s*%" + R, body[3][1])):
                    fp_route = True
        if len(body) != 1 and not fp_route:
            return dict(stem=stem, skip="xmit_block_not_single_instr")
        xl, xs = body[0]
        m = XMIT_RE.match(xs)
        if not m:
            return dict(stem=stem, skip="xmit_operand_form_unusual")
        mem, dst = m.group(1), m.group(2)
        if dst not in REG64:
            return dict(stem=stem, skip="xmit_dst_not_reg64")
        # liveness over the function body
        fstart = next((k for k, l in enumerate(lines) if l.split("#", 1)[0].strip() == f'"{stem}":'), None)
        fend = next((k for k, l in enumerate(lines) if l.strip().startswith(".Lfunc_end0:")), None)
        if fstart is None or fend is None:
            return dict(stem=stem, skip="function_bounds_not_found")
        instrs, labels = parse_func(lines[fstart + 1:fend])
        xi = [i for i, (ln, _, _) in enumerate(instrs) if ln == body[-1][0] - fstart - 1]
        if len(xi) != 1:
            return dict(stem=stem, skip="xmit_not_in_cfg")
        live = dst_live_after(instrs, labels, xi[0], dst)
        if live is None:
            return dict(stem=stem, skip="liveness_unknown_instr")
        if live:
            return dict(stem=stem, skip="asm_dst_live_after_xmit")
        # 1) faithful re-resolution of the original
        orig_re, _, base0 = resolve_ann(text, stem, bare_p)
        if strip_atoms_like(orig_re, ann) != ann:
            return dict(stem=stem, skip="ann_reresolve_mismatch_original")
        # 2) rewrite + re-resolve
        indent = lines[xl][: len(lines[xl]) - len(lines[xl].lstrip())]
        new_lines = list(lines)
        new_lines[xl] = f"{indent}orq\t$0, {mem}"
        new_text = "\n".join(new_lines)
        new_ann, dis, base1 = resolve_ann(new_text, stem, bare_p)
        new_ann = strip_atoms_like(new_ann, ann)
        if base1 != base0:
            return dict(stem=stem, skip="func_base_changed")
        if key_paths(new_ann) != key_paths(ann):
            return dict(stem=stem, skip="ann_fields_changed")
        xa_old, xa_new = ann["xmit"]["addr"], new_ann["xmit"]["addr"]
        at = [d for d in dis if d[0] + base1 == xa_new]
        if not at or not at[0][1].startswith("or") or not re.match(r"\$(0x)?0,", at[0][2]):
            return dict(stem=stem, skip="disasm_at_xmit_not_or0")
        fo, fn = addr_fields(ann), addr_fields(new_ann)
        deltas = {fn[p] - fo[p] for p in fo if fo[p] > xa_old}
        if len(deltas) > 1 or any(fn[p] != fo[p] for p in fo if fo[p] <= xa_old):
            return dict(stem=stem, skip="addr_shift_irregular")
        out = dict(stem=stem, ok=True, mem=mem, dst=dst, delta=(deltas.pop() if deltas else 0),
                   orig=xs + (" +fp_route" if fp_route else ""), xmit_addr=hex(xa_new))
        if write:
            write_rmw(dst_mode, stem, new_text, new_ann)
        else:
            out.update(new_text=new_text, new_ann=new_ann)
        return out
    except Exception:
        return dict(stem=stem, skip="exception", tb=traceback.format_exc())


def write_rmw(dst_mode: Path, stem: str, new_text: str, new_ann: dict) -> None:
    (dst_mode / "asm" / f"{stem}.s").write_text(new_text)
    (dst_mode / "ann" / f"{stem}.ann.json").write_text(json.dumps(new_ann, indent=2) + "\n")


def hash_rank(stem: str, seed: int) -> int:
    return int(hashlib.sha256(f"{seed}:{stem}".encode()).hexdigest()[:16], 16)


def choose_eligible(eligible: list, seed: int, fraction: float) -> list:
    """--select eligible: the round(fraction * E) eligible stems with the lowest sha256 rank."""
    k = int(round(fraction * len(eligible)))
    return sorted(sorted(eligible, key=lambda s: (hash_rank(s, seed), s))[:k])


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--src", required=True, help="source testset dir (relative to repo root or absolute)")
    ap.add_argument("--dst", required=True)
    ap.add_argument("--modes", nargs="+", default=["mispredict_not_taken", "mispredict_taken"])
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0, help="first N stems per mode (testing)")
    ap.add_argument("--git-rev", default="unknown", help="Mac repo HEAD the script came from")
    ap.add_argument("--fraction", type=float, default=1.0,
                    help="rewrite only stems with sha256(seed:stem) < fraction (default 1.0 = all)")
    ap.add_argument("--seed", type=int, default=0, help="selection seed for --fraction")
    ap.add_argument("--select", choices=["eligible", "hash"], default="eligible",
                    help="eligible (default, 2026-11-09): gate every stem, then rewrite round(fraction*E) "
                         "of the E eligible ones; hash: the old draw over all stems before the gates")
    ap.add_argument("--complete", action="store_true",
                    help="also copy every non-rewritten stem unchanged, so dst is a full mixed corpus")
    a = ap.parse_args()
    root = Path(a.repo_root)
    src = Path(a.src) if Path(a.src).is_absolute() else root / a.src
    dst = Path(a.dst) if Path(a.dst).is_absolute() else root / a.dst
    dst.mkdir(parents=True, exist_ok=True)
    log = (dst / "make_rmw_corpus.log").open("a")

    def L(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True); log.write(line + "\n"); log.flush()

    me = Path(__file__).resolve()
    L(f"START src={src} dst={dst} modes={a.modes} jobs={a.jobs} limit={a.limit} fraction={a.fraction} "
      f"seed={a.seed} select={a.select} complete={a.complete} script_md5={md5(me)}")
    rmw_rows = []
    prov = dict(created=time.strftime("%Y-%m-%dT%H:%M:%S"), host=socket.gethostname(),
                source_testset=str(src), dest_testset=str(dst), rule=RULE,
                script=str(me), script_md5=md5(me), script_git_rev_mac=a.git_rev,
                compile_annotate_md5=md5(root / "STAGE2_compilation" / "compile_annotate.py"),
                note="no .o files are written (the checkers build from .s); xml/ is not copied, "
                     "use the source testset's xml/ (same stems)",
                fraction=a.fraction, seed=a.seed, complete=a.complete, select=a.select,
                selection=('int(sha256(f"{seed}:{stem}").hexdigest()[:16],16)/2**64 < fraction'
                           if a.select == "hash" else
                           'all gates on every stem; then the round(fraction*E) eligible stems with the lowest '
                           'int(sha256(f"{seed}:{stem}").hexdigest()[:16],16)'), modes={})
    for mode in a.modes:
        sm, dm = src / mode, dst / mode
        for d in ("asm", "ann"):
            shutil.rmtree(dm / d, ignore_errors=True)
            (dm / d).mkdir(parents=True, exist_ok=True)
        stems = sorted(p.name[:-9] for p in (sm / "ann").glob("*.ann.json"))
        if a.limit:
            stems = stems[: a.limit]
        L(f"mode {mode}: {len(stems)} source stems")
        if a.select == "hash":
            sel = [s for s in stems if selected(s, a.seed, a.fraction)]
            L(f"mode {mode}: {len(sel)} selected by fraction={a.fraction} seed={a.seed}")
        else:
            sel = stems
            L(f"mode {mode}: gating all {len(sel)} stems (select=eligible)")
        work = [(s, str(sm), str(dm), str(src / "xml"), a.select == "hash") for s in sel]
        res = []
        with ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(str(root),)) as ex:
            for i, r in enumerate(ex.map(process, work, chunksize=64)):
                res.append(r)
                if r.get("skip") == "exception":
                    L(f"ERROR {mode}/{r['stem']}:\n{r['tb']}")
                if (i + 1) % 10000 == 0:
                    L(f"  {mode}: {i + 1}/{len(work)}")
        n_eligible = sum(1 for r in res if r.get("ok"))
        if a.select == "eligible":
            chosen = set(choose_eligible([r["stem"] for r in res if r.get("ok")], a.seed, a.fraction))
            for r in res:
                if r.get("ok") and r["stem"] in chosen:
                    write_rmw(dm, r["stem"], r.pop("new_text"), r.pop("new_ann"))
                elif r.get("ok"):
                    r.pop("new_text"); r.pop("new_ann")
                    r.pop("ok"); r["skip"] = "eligible_not_chosen"
            L(f"mode {mode}: {n_eligible} eligible, {len(chosen)} chosen (round({a.fraction} * {n_eligible}))")
        ok = [r for r in res if r.get("ok")]
        okset = {r["stem"] for r in ok}
        n_copied = 0
        if a.complete:
            for s in stems:
                if s in okset:
                    continue
                shutil.copy2(sm / "asm" / f"{s}.s", dm / "asm" / f"{s}.s")
                shutil.copy2(sm / "ann" / f"{s}.ann.json", dm / "ann" / f"{s}.ann.json")
                n_copied += 1
            L(f"mode {mode}: copied {n_copied} non-RMW stems unchanged")
        rmw_rows += [(mode, r["stem"], r["orig"], r["xmit_addr"]) for r in sorted(ok, key=lambda r: r["stem"])]
        skips = collections.Counter(r["skip"] for r in res if "skip" in r)
        n_ld = sum(1 for s in stems
                   if (json.loads((sm / "ann" / f"{s}.ann.json").read_text()).get("xmit") or {}).get("kind") == "ld")
        prov["modes"][mode] = dict(
            n_source=len(stems), n_selected=len(sel), n_ld_source=n_ld, n_written=len(ok),
            n_eligible=(n_eligible if a.select == "eligible" else None),
            share_of_eligible=(round(len(ok) / n_eligible, 4) if a.select == "eligible" and n_eligible else None),
            share_of_ld=(round(len(ok) / n_ld, 4) if n_ld else None),
            n_copied_unchanged=n_copied, skip_counts=dict(skips),
            delta_bytes=dict(collections.Counter(r["delta"] for r in ok)),
            orig_forms=dict(collections.Counter(re.sub(r"%\w+", "%R", r["orig"]) for r in ok)),
            skipped={k: sorted(r["stem"] for r in res if r.get("skip") == k)
                     for k in skips if k not in ("xmit_kind_not_ld", "eligible_not_chosen")},
            skipped_not_ld_count=skips.get("xmit_kind_not_ld", 0))
        L(f"mode {mode}: written={len(ok)} skips={dict(skips)}")
    if a.complete and not (dst / "xml").exists():
        (dst / "xml").symlink_to(src / "xml")
    if a.fraction < 1.0 or a.complete:
        with open(dst / "rmw_stems.tsv", "w") as f:
            f.write("mode\tstem\torig_instr\txmit_addr\n")
            for row in rmw_rows:
                f.write("\t".join(row) + "\n")
        L(f"rmw_stems.tsv: {len(rmw_rows)} (mode, stem) RMW tests")
    (dst / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    L(f"END provenance={dst / 'provenance.json'}")


if __name__ == "__main__":
    main()

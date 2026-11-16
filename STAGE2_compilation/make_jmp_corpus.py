#!/usr/bin/env python3
"""
make_jmp_corpus.py: Stage-2 post-pass that puts one direct `jmp` at a uniformly random
position of the test body in a deterministic share of the tests of a compiled testset
(uniform placement, recipe v3). parsexml.py, the instruction tables and the source testset are never
touched; it works on the compiled <src>/<mode>/{asm,ann}/ exactly as make_rmw_corpus.py.

What it is: a vocabulary option. Compiled code is full of direct unconditional jmps, but the
Alloy models have no jmp and the fv2 vocabulary's `branch_forms.jmp_direct` (parsexml pass 5)
only rewrites an existing resolved, correctly-not-taken, non-transmitter branch, so tests
without such a branch never contain one. This pass adds one direct jmp, value-neutral, at a
position drawn uniformly over the test body.

Rewrite rule (only rule): a test is selected iff
    int(sha256(f"jmp:{seed}:{stem}").hexdigest()[:16], 16) / 2**64 < p
(same stems in every mode). For a selected test the candidate insertion points are, with
--placement uniform (the default, Anna 2026-11-10 TA-2), the pc-marker blocks of EVERY Alloy pc
k whose `__litmus_<stem>_pc<k>` marker is in the .s (the whole test body: committed region,
window and after the transmitter), excluding every k that is the btb_forced_target_pc of a
"mispredict_taken" annotation (the BTB redirect lands on that marker, so a jmp placed before it
would never be fetched on the speculative path). Nothing about the window, the transmitter or
any bug enters the choice. The candidate used is
candidates[int(sha256(f"jmppos:{seed}:{stem}").hexdigest()[:16], 16) % len], and if it fails a
check below the next ones in cyclic order are tried (rare; counted in provenance `tried`).

--placement window is the OLD rule (fanoutgaps, 2026-11-09): only pcs k with u < k <= x, where u
is the smallest branch_pc among annotations whose mode starts with "mispredict" (the first
unresolved branch) and x is xmit.pc. The targeting audit (2026-11-10 TA-2,
wiki/findings/audits/2026-11-10/TARGETING_AUDIT.md S6) found that it targets a known bug's
precondition, so it is kept only for reproducing old smoke runs and is NOT for reported numbers
(the script logs a warning and provenance records the placement).

Right before the `#APP` line that holds pc k's marker it inserts its own inline-asm block

        #APP
        .globl  __litmus_<stem>_jmpins
    __litmus_<stem>_jmpins:
        jmp     .Lsimspect_jmpins
    .Lsimspect_jmpins:
        #NO_APP

i.e. a direct jmp to the next instruction (`eb 00`): value-neutral (no register, flag or
memory effect), on every path into pc k. Labels between the previous code and that `#APP` stay
before the jmp, so every entry into pc k passes through it.

Checks (a test failing all candidates is copied unchanged and listed with the reason):
  * at least one candidate pc (window placement: the annotation has an unresolved branch and an
    xmit pc), each pc marker used occurs exactly once, and .Lsimspect_jmpins is not already used;
  * faithful re-resolution: re-resolving the ORIGINAL .s with compile_annotate.py's own
    functions (build_binary, pc_offsets_from_nm, commit_offsets_from_nm,
    disassemble_instrs, update_annotations), using the stored annotation as the template,
    reproduces the stored annotation exactly (so the corpus does not need llvm/; RMW
    output works as input);
  * after the rewrite: func_base unchanged; the instruction at the __litmus_<stem>_jmpins
    symbol is `jmp` to the next instruction, and pc k's marker is that next instruction;
    every other instruction maps one to one onto the original stream (same mnemonic, same
    operands, jump targets mapped through the same correspondence; an older short jcc whose
    target moved may be relaxed to a longer encoding, so offsets after the jmp shift by 2,
    or more where a jcc grew); every annotation field that existed before exists again, and
    every absolute address field (any `addr` / `*_addr`, make_rmw_corpus.addr_fields) lands
    on the instruction it named before.

Recorded per test: ann["jmp_insert"] = {before_pc, addr, addr_hex, seed, p, n_candidates,
placement, in_window} (addr is the jmp's absolute address; cache_setup.remap_annotation remaps
it like any other address; in_window = first unresolved branch < before_pc <= xmit.pc, recorded
for analysis only), and <dst>/jmp_stems.tsv (mode, stem, before_pc, jmp_addr, n_candidates,
placement, in_window). With p = 0 (or a
stem not selected) the files are byte copies of the source.

Order with the RMW post-pass: run make_rmw_corpus.py first, then this pass on its output
(make_rmw_corpus.py's faithfulness check re-resolves from llvm/ bare annotations, which
know nothing of the jmp).

Usage (inside gem5_dev; needs GNU as/ld/nm + llvm-objdump-15 as compile_annotate does):
  python3 make_jmp_corpus.py --repo-root <code root with STAGE2_compilation/> \\
      --src testsets_twostage/STT_6_fv2fp_rmw --dst testsets_twostage/STT_6_fv2fp_rmw_jmp \\
      --p 0.5 --seed 20261109 --jobs 16 [--placement uniform|window] [--limit N] [--stems-file f]
      [--git-rev <mac HEAD>]
Writes <dst>/<mode>/{asm,ann}/ (every source stem), <dst>/xml -> <src>/xml,
<dst>/jmp_stems.tsv, <dst>/provenance.json, <dst>/make_jmp_corpus.log.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_rmw_corpus import addr_fields, key_paths  # noqa: E402

_RULE = ("one direct `jmp .Lsimspect_jmpins; .Lsimspect_jmpins:` (jmp to the next instruction, marked by "
         "__litmus_<stem>_jmpins) in its own inline-asm block right before the marker block of an Alloy pc k "
         "{where}, k not a mispredict_taken BTB-forced target; selected iff sha256(jmp:seed:stem) < p; "
         "annotations re-resolved with compile_annotate.py")
RULES = {
    "uniform": _RULE.format(where="drawn uniformly over every pc marker in the .s (the whole test body)"),
    "window": _RULE.format(where="with first_unresolved_pc < k <= xmit.pc (OLD window placement; "
                                 "targets jmp shadow, NOT for reported numbers)"),
}
RULE = RULES["uniform"]
PLACEMENTS = tuple(RULES)
LABEL = ".Lsimspect_jmpins"


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest()[:16], 16)


def selected(stem: str, seed: int, p: float) -> bool:
    return _h(f"jmp:{seed}:{stem}") / 2.0 ** 64 < p


def _window(ann: dict):
    """(u, x) = (first unresolved branch pc, xmit pc), or None if either is missing."""
    unres = [e["branch_pc"] for e in ann.get("annotations", [])
             if str(e.get("mode", "")).startswith("mispredict") and e.get("branch_pc") is not None]
    x = (ann.get("xmit") or {}).get("pc")
    if not unres or x is None:
        return None
    return min(unres), x


def _taken_forced(ann: dict) -> set:
    return {e.get("btb_forced_target_pc") for e in ann.get("annotations", [])
            if e.get("mode") == "mispredict_taken"}


def in_window(ann: dict, k: int) -> bool:
    """first unresolved branch < k <= xmit pc (analysis label only; never used to choose k)."""
    w = _window(ann)
    return bool(w) and w[0] < k <= w[1]


def asm_pcs(text: str, stem: str) -> list:
    """Sorted Alloy pcs whose `__litmus_<stem>_pc<k>:` marker label is in the .s."""
    safe = re.escape(stem.replace("-", "_").replace(".", "_"))
    return sorted({int(m.group(1)) for m in re.finditer(rf"^__litmus_{safe}_pc(\d+):\s*$", text, re.M)})


def candidates(ann: dict, pcs: list = None, placement: str = "uniform") -> list:
    """Alloy pcs k before whose marker block the jmp may go (see the module doc).

    uniform: every pc in `pcs` (the markers of the .s) except mispredict_taken BTB-forced targets.
    window (old rule, not for reported numbers): u < k <= x, same exclusion."""
    forced = _taken_forced(ann)
    if placement == "uniform":
        return [k for k in sorted(pcs or []) if k not in forced]
    if placement != "window":
        raise ValueError(f"unknown placement {placement!r}")
    w = _window(ann)
    if not w:
        return []
    u, x = w
    return [k for k in range(u + 1, x + 1) if k not in forced]


def ordered_candidates(stem: str, seed: int, cands: list) -> list:
    if not cands:
        return []
    i = _h(f"jmppos:{seed}:{stem}") % len(cands)
    return cands[i:] + cands[:i]


def marker_app_line(lines: list, stem: str, k: int):
    """Index of the `#APP` line that opens pc k's marker block, or a skip reason."""
    safe = stem.replace("-", "_").replace(".", "_")
    lab = f"__litmus_{safe}_pc{k}:"
    idx = [i for i, l in enumerate(lines) if l.strip() == lab]
    if len(idx) != 1:
        return None, f"marker_count_{len(idx)}"
    j = idx[0] - 1
    while j >= 0 and lines[j].strip().startswith(".globl"):
        j -= 1
    if j < 0 or lines[j].strip() != "#APP":
        return None, "marker_not_after_APP"
    return j, None


def insert_jmp(text: str, at: int, stem: str) -> str:
    lines = text.split("\n")
    js = jmp_symbol(stem)
    lines[at:at] = ["\t#APP", f"\t.globl\t{js}", f"{js}:", f"\tjmp\t{LABEL}", f"{LABEL}:", "\t#NO_APP"]
    return "\n".join(lines)


CA = None  # compile_annotate module (set in worker init)


def _init(repo_root: str):
    global CA
    sys.path.insert(0, str(Path(repo_root) / "STAGE2_compilation"))
    import compile_annotate as ca  # noqa: E402
    CA = ca


def jmp_symbol(stem: str) -> str:
    return f"__litmus_{stem.replace('-', '_').replace('.', '_')}_jmpins"


def nm_syms(binary: Path) -> dict:
    import subprocess
    out = subprocess.check_output(["nm", "--defined-only", str(binary)], text=True)
    return {p[-1]: int(p[0], 16) for p in (l.split() for l in out.splitlines()) if len(p) >= 3}


def resolve_ann(s_text: str, stem: str, template: dict, want_syms: bool = False) -> tuple:
    """Re-resolve every address of `template` against the binary built from s_text."""
    tmp = Path(tempfile.mkdtemp(prefix=f"jmp_{stem}_"))
    try:
        s = tmp / f"{stem}.s"
        s.write_text(s_text)
        t = tmp / "template.ann.json"
        t.write_text(json.dumps(template))
        binary, base = CA.build_binary(s, tmp)
        pc_map = CA.pc_offsets_from_nm(binary, stem, base)
        commit = CA.commit_offsets_from_nm(binary, stem, base)
        instrs = CA.disassemble_instrs(binary, base)
        ann = CA.update_annotations(t, pc_map, instrs, base, commit)
        syms = nm_syms(binary) if want_syms else None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return (ann, instrs, base, pc_map, syms) if want_syms else (ann, instrs, base, pc_map)


_HEX = re.compile(r"0x([0-9a-f]+)")
_BRANCHY = ("j", "call", "loop")


def map_instrs(old: list, new: list, jm: int, base0: int = 0, base1: int = 0):
    """old/new = disassemble_instrs lists; new has one extra instruction (the jmp) at index jm.
    -> {old offset: new offset} if every other instruction is the same (mnemonic, and operand
    text, except that jump/call targets are mapped through the same correspondence, or land on the
    inserted jmp when they named the instruction right after it), else None.
    Lengths may differ (the assembler may relax an older short jcc whose target moved), which
    is why this maps instruction by instruction instead of assuming one constant shift."""
    if len(new) != len(old) + 1:
        return None
    pairs = [(o, new[i if i < jm else i + 1]) for i, o in enumerate(old)]
    omap = {o[0]: n[0] for o, n in pairs}
    for o, n in pairs:
        if o[1] != n[1]:
            return None
        if o[2] == n[2]:
            continue
        if not o[1].startswith(_BRANCHY):
            return None
        ot, nt = _HEX.findall(o[2].split("<")[0]), _HEX.findall(n[2].split("<")[0])
        if len(ot) != 1 or len(nt) != 1:
            return None
        mt, ntt = omap.get(int(ot[0], 16) - base0), int(nt[0], 16) - base1
        if mt != ntt and not (ntt == new[jm][0] and mt == new[jm + 1][0]):
            # the one allowed difference: a jump whose target was the instruction the
            # jmp now precedes may land on the inserted jmp (its label sits before the jmp block,
            # by design: every entry into pc k passes through the jmp)
            return None
    return omap


def try_one(stem, text, ann, k, orig_instrs, orig_pcmap, base0):
    lines = text.split("\n")
    at, why = marker_app_line(lines, stem, k)
    if at is None:
        return None, why
    if k not in orig_pcmap:
        return None, "pc_not_in_nm"
    new_text = insert_jmp(text, at, stem)
    tmpl = json.loads(json.dumps(ann))
    tmpl.pop("jmp_insert", None)
    new_ann, dis, base1, pcmap1, syms = resolve_ann(new_text, stem, tmpl, want_syms=True)
    if base1 != base0:
        return None, "func_base_changed"
    jsym = syms.get(jmp_symbol(stem))
    if jsym is None:
        return None, "jmp_symbol_missing"
    joff = jsym - base1
    at_i = [i for i, d in enumerate(dis) if d[0] == joff]
    if not at_i or dis[at_i[0]][1] != "jmp" or at_i[0] + 1 >= len(dis):
        return None, "disasm_at_insert_not_jmp"
    jm = at_i[0]
    tgt = _HEX.findall(dis[jm][2].split("<")[0])
    if len(tgt) != 1 or int(tgt[0], 16) - base1 != dis[jm + 1][0]:
        return None, "jmp_not_to_next_instr"
    if pcmap1.get(k) != dis[jm + 1][0]:
        return None, "marker_not_right_after_jmp"
    omap = map_instrs(orig_instrs, dis, jm, base0, base1)
    if omap is None:
        return None, "instr_stream_changed"
    if omap.get(orig_pcmap[k]) != dis[jm + 1][0]:
        return None, "insert_not_before_marker_instr"
    if key_paths(new_ann) != key_paths(tmpl):
        return None, "ann_fields_changed"
    fo, fn = addr_fields(tmpl), addr_fields(new_ann)
    for q in fo:
        m = omap.get(fo[q] - base0)
        if m is None or fn[q] != base1 + m:
            return None, "addr_not_on_same_instr"
    delta = len(dis) and (dis[-1][0] - orig_instrs[-1][0])
    abs_j = base1 + joff
    new_ann["jmp_insert"] = dict(before_pc=k, addr=abs_j, addr_hex=hex(abs_j))
    return (new_text, new_ann, delta), None


def process(args: tuple) -> dict:
    stem, src_mode, dst_mode, seed, p = args[0], Path(args[1]), Path(args[2]), args[3], args[4]
    placement = args[5] if len(args) > 5 else "uniform"
    try:
        s_p = src_mode / "asm" / f"{stem}.s"
        a_p = src_mode / "ann" / f"{stem}.ann.json"
        d_s = dst_mode / "asm" / f"{stem}.s"
        d_a = dst_mode / "ann" / f"{stem}.ann.json"

        def copy(**r):
            shutil.copy2(s_p, d_s)
            shutil.copy2(a_p, d_a)
            return dict(stem=stem, **r)

        if not selected(stem, seed, p):
            return copy(skip="not_selected")
        text = s_p.read_text()
        ann = json.loads(a_p.read_text())
        if "jmp_insert" in ann or LABEL in text or jmp_symbol(stem) in text:
            return copy(skip="already_has_jmp_insert")
        cands = candidates(ann, asm_pcs(text, stem), placement)
        if not cands:
            return copy(skip="no_candidate_pc")
        orig_re, instrs0, base0, pcmap0 = resolve_ann(text, stem, ann)
        if orig_re != ann:
            return copy(skip="ann_reresolve_mismatch_original")
        whys = []
        for k in ordered_candidates(stem, seed, cands):
            got, why = try_one(stem, text, ann, k, instrs0, pcmap0, base0)
            if got:
                new_text, new_ann, delta = got
                iw = in_window(ann, k)
                new_ann["jmp_insert"].update(seed=seed, p=p, n_candidates=len(cands), placement=placement,
                                             in_window=iw)
                d_s.write_text(new_text)
                d_a.write_text(json.dumps(new_ann, indent=2) + "\n")
                return dict(stem=stem, ok=True, before_pc=k, jmp_addr=new_ann["jmp_insert"]["addr_hex"],
                            n_candidates=len(cands), delta=delta, tried=len(whys) + 1,
                            xmit_kind=(ann.get("xmit") or {}).get("kind"), in_window=iw)
            whys.append(f"pc{k}:{why}")
        return copy(skip="all_candidates_failed", whys=whys)
    except Exception:
        try:
            shutil.copy2(src_mode / "asm" / f"{stem}.s", dst_mode / "asm" / f"{stem}.s")
            shutil.copy2(src_mode / "ann" / f"{stem}.ann.json", dst_mode / "ann" / f"{stem}.ann.json")
        except Exception:
            pass
        return dict(stem=stem, skip="exception", tb=traceback.format_exc())


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--src", required=True, help="source testset dir (relative to repo root or absolute)")
    ap.add_argument("--dst", required=True)
    ap.add_argument("--modes", nargs="+", default=["mispredict_not_taken", "mispredict_taken"])
    ap.add_argument("--p", type=float, default=0.5, help="per-test probability of a jmp (default 0.5)")
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--placement", choices=PLACEMENTS, default="uniform",
                    help="uniform (default): any pc marker of the test body; window: OLD rule, "
                         "first unresolved branch < k <= xmit (targets jmp shadow; NOT for reported numbers)")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0, help="first N stems per mode (sample)")
    ap.add_argument("--stems-file", default=None, help="only these stems (one per line; sample)")
    ap.add_argument("--git-rev", default="unknown", help="Mac repo HEAD the script came from")
    a = ap.parse_args()
    root = Path(a.repo_root)
    src = Path(a.src) if Path(a.src).is_absolute() else root / a.src
    dst = Path(a.dst) if Path(a.dst).is_absolute() else root / a.dst
    dst.mkdir(parents=True, exist_ok=True)
    log = (dst / "make_jmp_corpus.log").open("a")

    def L(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True); log.write(line + "\n"); log.flush()

    me = Path(__file__).resolve()
    L(f"START src={src} dst={dst} modes={a.modes} p={a.p} seed={a.seed} jobs={a.jobs} limit={a.limit} "
      f"stems_file={a.stems_file} placement={a.placement} script_md5={md5(me)}")
    if a.placement == "window":
        L("WARNING --placement window is the OLD jmp-shadow-window rule (targeting audit 2026-11-10 TA-2): "
          "NOT for reported numbers; use the default --placement uniform")
    only = set(Path(a.stems_file).read_text().split()) if a.stems_file else None
    prov = dict(created=time.strftime("%Y-%m-%dT%H:%M:%S"), host=socket.gethostname(),
                source_testset=str(src), dest_testset=str(dst), rule=RULES[a.placement], p=a.p, seed=a.seed,
                placement=a.placement, for_reported_numbers=(a.placement == "uniform"),
                selection='int(sha256(f"jmp:{seed}:{stem}").hexdigest()[:16],16)/2**64 < p',
                position='candidates[int(sha256(f"jmppos:{seed}:{stem}").hexdigest()[:16],16) % len], '
                         'then the next ones cyclically if a check fails',
                script=str(me), script_md5=md5(me), script_git_rev_mac=a.git_rev,
                compile_annotate_md5=md5(root / "STAGE2_compilation" / "compile_annotate.py"),
                limit=a.limit, stems_file=a.stems_file, modes={})
    rows = []
    for mode in a.modes:
        sm, dm = src / mode, dst / mode
        for d in ("asm", "ann"):
            shutil.rmtree(dm / d, ignore_errors=True)
            (dm / d).mkdir(parents=True, exist_ok=True)
        stems = sorted(q.name[:-9] for q in (sm / "ann").glob("*.ann.json"))
        if only is not None:
            stems = [s for s in stems if s in only]
        if a.limit:
            stems = stems[: a.limit]
        L(f"mode {mode}: {len(stems)} source stems")
        work = [(s, str(sm), str(dm), a.seed, a.p, a.placement) for s in stems]
        res = []
        if a.jobs <= 1:            # in-process (tests, tiny samples)
            _init(str(root))
            it, ex = map(process, work), None
        else:
            ex = ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(str(root),))
            it = ex.map(process, work, chunksize=32)
        for i, r in enumerate(it):
            res.append(r)
            if r.get("skip") == "exception":
                L(f"ERROR {mode}/{r['stem']}:\n{r['tb']}")
            if (i + 1) % 10000 == 0:
                L(f"  {mode}: {i + 1}/{len(work)}")
        if ex is not None:
            ex.shutdown()
        ok = sorted((r for r in res if r.get("ok")), key=lambda r: r["stem"])
        rows += [(mode, r["stem"], str(r["before_pc"]), r["jmp_addr"], str(r["n_candidates"]), a.placement,
                  str(int(r["in_window"]))) for r in ok]
        skips = collections.Counter(r["skip"] for r in res if "skip" in r)
        n_sel = len(res) - skips.get("not_selected", 0)
        prov["modes"][mode] = dict(
            n_source=len(stems), n_selected=n_sel, n_written=len(ok),
            share_written=round(len(ok) / len(stems), 4) if stems else None,
            skip_counts=dict(skips),
            by_kind=dict(collections.Counter(r["xmit_kind"] for r in ok)),
            n_in_window=sum(1 for r in ok if r["in_window"]),
            tried=dict(collections.Counter(r["tried"] for r in ok)),
            delta_bytes=dict(collections.Counter(r["delta"] for r in ok)),
            skipped={k: sorted(r["stem"] for r in res if r.get("skip") == k)
                     for k in skips if k != "not_selected"},
            failed_whys={r["stem"]: r["whys"] for r in res if r.get("skip") == "all_candidates_failed"})
        L(f"mode {mode}: written={len(ok)} selected={n_sel} skips={dict(skips)}")
    if not (dst / "xml").exists() and (src / "xml").exists():
        (dst / "xml").symlink_to((src / "xml").resolve())
    with open(dst / "jmp_stems.tsv", "w") as f:
        f.write("mode\tstem\tbefore_pc\tjmp_addr\tn_candidates\tplacement\tin_window\n")
        for row in rows:
            f.write("\t".join(row) + "\n")
    L(f"jmp_stems.tsv: {len(rows)} (mode, stem) tests with an inserted jmp")
    (dst / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    L(f"END provenance={dst / 'provenance.json'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
diag_rmw_limm_artifact.py: DISQUALIFIER (check_ld checker artifact, RL-10). On the Recon-group
STT builds (gem5-recon-ruby3 = E6, gem5-recon-modded = E2; scheme 2) an RMW transmitter
`orq $imm, <mem>` (gem5 OR_M_I = limm t2,imm; ldst t1,[mem]; or; st) is scored as a
`store_forward` leak although ReCon's delay unit held its load micro-op: the `ldst` executes in the
LSQ, prints `STL_CHECK isTainted=1`, is `Inserted tainted load ... into delay_unit`
(gem5-recon-ruby3 `src/cpu/o3/lsq_unit.cc:2104`) in the same tick, never sends a request, never
completes and is squashed. check_ld takes `xmit_complete` from the pc-wide `best_record`
(`gem5_common.py:816`), which is the leading `limm` micro-op's completion, so the
executed-no-packet bounce is relabelled `store_forward` (`check_ld.py:139`).
Proof: claudelog 2026-11-10 17:10 (recon-rmw), CHECKER_FIX_PROPOSALS.md item 2 addendum, 14
faithful E6 reruns in cafe2 /tests/simspect_alloy_20261108/bugwork/recon_rmw/uop_table.json.

ONE cause. Signature (ALL must hold, else the hit stays NEW):
  1. build: manifest gem5_binary is /work/gem5-recon-ruby3/ or /work/gem5-recon-modded/, scheme 2
     (STT), no `--scheme=<other>` override. Any other build -> False (on stt / stt-master the same
     OR_M_I micro-ops exist but STT blocks the tainted ldst at issue, so the artifact shows up as an
     UNGATED `never_executed` hit, a different checker path this diag does not cover).
  2. form: the transmitter instruction in <mode>/asm/<stem>.s at the xmit label is `orq $imm, <mem>`
     (OR_M_I, the only RMW form traced; Stage 2's fv4 `load_rmw_or0` and the STT_6_rmw corpus
     emit exactly this). Other RMW mnemonics are unproven -> False.
  3. raw records (the campaign's own check_ld _sweep_raw / raw_results): every hitting record of
     this mode/stem has cache_fate == store_forward, data_obtained True, xmit_retire == 0,
     packet_tick 0, and 0 < xmit_complete <= xmit_execute (the completion that tripped the gate is
     not later than the last LSQ execute, so it cannot be the ldst's own forward completion; a real
     forward to an RMW ldst shows complete > execute because the `or` completes after it: the 60/59
     E6 A2 RMW records).
  4. LSQ evidence, from diagnostics/recon_stlf_evidence.json (rerun_hits_evidence.py --analyzer
     recon_stlf, the file diag_recon_stlf_bypass already reads): the faithful rerun reproduced the
     hit, STL_CHECK says isTainted=1 for the xmit, NO "Forwarding from store" line follows its
     execute, and the xmit seq never became "ready within ROB" (ready_tick null).
     No evidence entry -> False (raw signature alone does not exclude a multi-instance load whose
     earlier instance obtained data; see the .md).
  5. optional micro-op evidence, diagnostics/rmw_uop_evidence.json (format of recon_rmw
     uop_table.json): if an entry exists it must show the ldst micro-op with complete 0 and a
     delay_unit insertion, and no ldst among `complete_from`; an entry that disagrees -> False.
PHASE disqualifier: a bucketed hit is not a leak. Bug note: diag_rmw_limm_artifact.md.
"""
import collections, functools, glob, json, re
from pathlib import Path

PHASE = "disqualifier"; CATEGORY = "checker_artifact:RL-10_rmw_limm"; NEEDS_GEM5 = False; ORDER = 30
KINDS = ("ld",)
MODE = None
HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent

BUILDS = ("/work/gem5-recon-ruby3/", "/work/gem5-recon-modded/")
RMW_IMM = re.compile(r"^orq\s+\$-?(0x[0-9a-fA-F]+|\d+)\s*,\s*(-?\w*)\(([^)]*)\)\s*$")


def _jsonc(p):
    txt = Path(p).read_text()
    txt = re.sub(r"(?m)^\s*//.*$", "", txt)
    txt = re.sub(r"(?<![:\"\\])//[^\n\"]*$", "", txt, flags=re.M)
    return json.loads(txt)


@functools.lru_cache(maxsize=1)
def _build_ok():
    """(ok, why) from the campaign manifest (+ its config for the scheme)."""
    try:
        man = json.loads((RUN_DIR / "manifest.json").read_text())
    except (OSError, ValueError):
        return False, "no manifest.json"
    binary = man.get("gem5_binary") or ""
    if not any(binary.startswith(b) for b in BUILDS):
        return False, f"build {binary or '?'} not in scope (RL-10 proven on gem5-recon-ruby3/-modded only)"
    extra = man.get("gem5_extra_args") or []
    over = [a for a in extra if str(a).startswith("--scheme=")]
    if over and over[-1].split("=", 1)[1] not in ("2", "STT"):
        return False, f"scheme override {over[-1]} not STT"
    scheme = None
    for p in (man.get("config"), RUN_DIR / "run_config.jsonc"):
        if not p:
            continue
        try:
            scheme = _jsonc(p).get("gem5", {}).get("scheme")
            break
        except (OSError, ValueError):
            continue
    if scheme != 2:
        return False, f"scheme {scheme!r} (need 2 = STT; unknown is not bucketed)"
    return True, f"{binary.split('/')[2]} scheme 2"


@functools.lru_cache(maxsize=1)
def _raw():
    """(mode, stem) -> list of this campaign's check_ld raw records that hit (issued_in_window)."""
    d = collections.defaultdict(list)
    files = (glob.glob(str(RUN_DIR / "**" / "_sweep_raw" / "*check_ld*.json"), recursive=True)
             + glob.glob(str(RUN_DIR / "**" / "raw_results" / "*check_ld*.json"), recursive=True))
    for f in files:
        mode = next((p for p in Path(f).parts if p.startswith("mispredict_")), None)
        try:
            recs = json.load(open(f))
        except (OSError, ValueError):
            continue
        recs = recs if isinstance(recs, list) else recs.get("results", [])
        for r in recs:
            if isinstance(r, dict) and r.get("status", "ok") == "ok" and r.get("issued_in_window"):
                d[(mode, r["name"].split("__")[0])].append(r)
    return d


@functools.lru_cache(maxsize=1)
def _stlf_ev():
    p = HERE / "recon_stlf_evidence.json"
    return json.loads(p.read_text()) if p.exists() else {}


@functools.lru_cache(maxsize=1)
def _uop_ev():
    p = HERE / "rmw_uop_evidence.json"
    return json.loads(p.read_text()) if p.exists() else {}


def xmit_insn(stem, mode_dir):
    """(asm text of the first instruction after the xmit label, ann xmit addr_hex) or (None, why)."""
    mode_dir = Path(mode_dir)
    try:
        ann = json.loads((mode_dir / "ann" / f"{stem}.ann.json").read_text())
        lines = (mode_dir / "asm" / f"{stem}.s").read_text().splitlines()
    except (OSError, ValueError) as e:
        return None, f"{type(e).__name__}: {e}"
    x = ann.get("xmit", {})
    label = f"__litmus_inst_{stem.split('-')[1]}_pc{x.get('pc')}:"
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == label)
    except StopIteration:
        return None, "no xmit label"
    for l in lines[i + 1:]:
        t = l.split("#")[0].strip()
        if not t or t.endswith(":") or t.startswith("."):
            continue
        return re.sub(r"\s+", " ", t), x.get("addr_hex")
    return None, "no instruction after xmit label"


def judge_raw(recs, xmit_hex=None):
    """Signature 3 over the in-window raw records. (ok, why)."""
    if not recs:
        return False, "no in-window raw record"
    for r in recs:
        ex, co = r.get("xmit_execute") or 0, r.get("xmit_complete") or 0
        if xmit_hex and r.get("xmit_pc") and r["xmit_pc"] != xmit_hex:
            return False, f"raw xmit_pc {r['xmit_pc']} != ann {xmit_hex}"
        if not (r.get("cache_fate") == "store_forward" and r.get("data_obtained") is True):
            return False, f"in-window record cache_fate={r.get('cache_fate')} (not the store_forward path)"
        if (r.get("xmit_retire") or 0) != 0 or (r.get("packet_tick") or 0) != 0:
            return False, "xmit retired or sent a packet"
        if not (0 < co <= ex):
            return False, f"xmit_complete {co} > xmit_execute {ex} (could be the ldst's own completion)"
    return True, f"{len(recs)} in-window record(s), store_forward with xmit_complete <= xmit_execute"


def judge_stlf(e):
    """Signature 4 on one recon_stlf evidence entry. (ok, why)."""
    if not e or e.get("error"):
        return False, "no recon_stlf evidence"
    if not e.get("reproduced"):
        return False, "rerun did not reproduce"
    if "isTainted=1" not in (e.get("stl") or ""):
        return False, f"STL_CHECK not tainted ({e.get('stl')!r})"
    if e.get("fwd"):
        return False, "store forward to the xmit (A2 class, not this artifact)"
    if e.get("ready_tick") is not None:
        return False, "xmit seq became ready within ROB"
    return True, "rerun: tainted, no forward, never ready"


def judge_uop(u):
    """Signature 5 on one uop_table entry (None = no entry = no objection). (ok, why)."""
    if u is None:
        return True, ""
    ld = [v for v in (u.get("uops") or {}).values() if " ldst " in f" {v.get('disasm', '')} "]
    if not ld:
        return False, "uop evidence has no ldst micro-op"
    if any((v.get("complete") or 0) or (v.get("retire") or 0) or not v.get("delay_unit") for v in ld):
        return False, "uop evidence: ldst completed/retired or was not delayed"
    if any("ldst" in str(c) for c in (u.get("complete_from") or [])):
        return False, "uop evidence: completion came from the ldst"
    return True, "; uop trace: ldst delayed, complete 0, completion from limm"


def is_known(stem, xml_dir):
    ok, why = _build_ok()
    if not ok:
        return False, why
    insn, hexpc = xmit_insn(stem, Path(xml_dir).parent / MODE)
    if insn is None:
        return False, f"xmit asm: {hexpc}"
    if not RMW_IMM.match(insn):
        return False, f"xmit {insn!r} is not OR_M_I (orq $imm, mem)"
    ok, rwhy = judge_raw(_raw().get((MODE, stem), []), hexpc)
    if not ok:
        return False, rwhy
    ok, swhy = judge_stlf(_stlf_ev().get(f"{MODE}/{stem}"))
    if not ok:
        return False, swhy
    ok, uwhy = judge_uop(_uop_ev().get(f"{MODE}/{stem}"))
    if not ok:
        return False, uwhy
    return True, f"{why}; {insn}; {rwhy}; {swhy}{uwhy}"

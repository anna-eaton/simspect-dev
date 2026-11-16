#!/usr/bin/env python3
"""
check_st.py — store transmitter checker (store ADDRESS leakage; SPT's contract).

Criterion. SPT (Choudhary et al., MICRO 2021, §7.4 "Loads and Stores", p. 9 of
~/Documents/quail/sources/papers/choudhary-2021-spt.pdf): "For loads/stores,
delaying execution (including TLB accesses, etc.) until the address operands are
untainted is handled by the load/store unit". So a store transmits its address
when it EXECUTES (computes its address and starts translation). The check is

    lc_retire < xmit_signal < fnc_retire   ∧  all annotated branches unresolved

with the same window, branch check and lc-retired disqualifier as check_ld.py.

Signal. `xmit_signal` = the LSQUnit debug line "Executing store PC (0x..) [sn:N]"
(lsq_unit_impl.hh LSQUnit::executeStore, which calls initiateAcc → address
generation + TLB translation). On the SPT build this line is printed only AFTER
SPT's gate: iew_impl.hh (`inst->isStore()` branch) defers a fence-delayed store
("Deferring store due to virtual fence.") and `continue`s BEFORE calling
ldstQueue.executeStore. So the existing LSQUnit flag (already on by default via
SIMSPECT_GEM5_DBG_FLAG=O3PipeView,LSQUnit) gives the tick; no hook is needed.
Fallback when the trace has no store record at the xmit PC: pipeview `complete`.
If several dynamic instances exist at the PC, the earliest execute tick is used.

NOT applied: check_ld's data-obtained gate (reached_cache / store_forward /
spec_read_only). That gate decides whether a LOAD obtained its data; a store's
address is already exposed when it executes/translates, so execution in the
window is the whole criterion.

Note on RMW: an x86 RMW (`add %r, (m)`) has a load and a store micro-op at the
same PC; this checker only looks at the store micro-op's execute line.

Usage:
    python3 check_st.py <input_dir> [--jobs N] [--out results.json] [--scheme N]
"""

import re
from collections import defaultdict

from gem5_common import _trace_lines, best_record, check_branch_resolutions, run_batch

_INSERT_ST = re.compile(r"^\s*(\d+):\s+system\.cpu\.iew\.lsq\..*:\s+Inserting store PC \(0x([0-9a-f]+)=>.*\[sn:(\d+)\]")
_EXEC_ST = re.compile(r"^\s*(\d+):\s+system\.cpu\.iew\.lsq\..*:\s+Executing store PC \(0x([0-9a-f]+)=>.*\[sn:(\d+)\]")


def parse_lsq_stores(trace_path):
    """pc → list of {sn, insert_tick, execute_tick} for store micro-ops."""
    by_sn, by_pc = {}, defaultdict(list)
    for line in _trace_lines(trace_path):
        m = _INSERT_ST.match(line)
        if m:
            rec = dict(sn=int(m.group(3)), insert_tick=int(m.group(1)), execute_tick=0)
            by_sn[rec["sn"]] = rec
            by_pc[int(m.group(2), 16)].append(rec)
            continue
        m = _EXEC_ST.match(line)
        if m:
            sn = int(m.group(3))
            rec = by_sn.get(sn)
            if rec is None:
                rec = dict(sn=sn, insert_tick=0, execute_tick=0)
                by_sn[sn] = rec
                by_pc[int(m.group(2), 16)].append(rec)
            if rec["execute_tick"] == 0:
                rec["execute_tick"] = int(m.group(1))
    return dict(by_pc)


def check_st(by_pc, xmit_pc, lc_pc, fnc_pc, unresolved, ticks_per_cycle,
             lsq_by_pc=None, squash_by_pc=None, trace_path=None):
    xmit_rec = best_record(by_pc.get(xmit_pc, []))
    lc_rec   = best_record(by_pc.get(lc_pc,   [])) if lc_pc  else None
    fnc_rec  = best_record(by_pc.get(fnc_pc,  [])) if fnc_pc else None

    st_recs = parse_lsq_stores(trace_path).get(xmit_pc, []) if trace_path else []
    execs = [r["execute_tick"] for r in st_recs if r["execute_tick"] > 0]
    xmit_execute  = min(execs) if execs else 0
    xmit_complete = xmit_rec["complete"] if xmit_rec else 0
    xmit_signal   = xmit_execute if xmit_execute > 0 else xmit_complete

    lc_retire    = lc_rec["retire"]    if lc_rec  else 0
    fnc_retire   = fnc_rec["retire"]   if fnc_rec else 0
    xmit_retire  = xmit_rec["retire"]  if xmit_rec else 0

    disqualified = (lc_pc is not None) and (lc_retire == 0)
    after_lc   = (lc_retire == 0) or (xmit_signal > lc_retire)
    before_fnc = (fnc_retire == 0) or (xmit_signal < fnc_retire)
    branches_unresolved, branch_details = check_branch_resolutions(
        by_pc, xmit_signal, unresolved, ticks_per_cycle)
    in_window = (not disqualified and xmit_signal > 0 and after_lc
                 and before_fnc and branches_unresolved)

    return dict(
        issued_in_window=in_window,
        in_window=in_window,
        criteria=dict(lc_retired=not disqualified, signal_seen=xmit_signal > 0,
                      after_lc=after_lc, before_fnc=before_fnc,
                      branches_unresolved=branches_unresolved),
        signal_source=("lsq_store_execute" if xmit_execute > 0 else
                       "pipeview_complete" if xmit_complete > 0 else "none"),
        store_records=len(st_recs),
        xmit_signal=xmit_signal,
        xmit_execute=xmit_execute,
        xmit_complete=xmit_complete,
        xmit_issue=xmit_rec["issue"] if xmit_rec else 0,
        xmit_retire=xmit_retire,
        xmit_retired_in_window=xmit_retire > 0,
        lc_retire=lc_retire,
        lc_unretired_but_specified=disqualified,
        fnc_retire=fnc_retire,
        fnc_complete=fnc_rec["complete"] if fnc_rec else 0,
        branches_unresolved=branches_unresolved,
        branch_resolutions=branch_details,
    )


check_st.wants_trace = True


if __name__ == "__main__":
    run_batch(check_st, description="store transmitter: LSQ 'Executing store' in (lc_retire, fnc_retire)")

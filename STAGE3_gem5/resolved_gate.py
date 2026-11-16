#!/usr/bin/env python3
"""Resolved-branch gate (Anna, 2026-11-16, option (b) of URGENT_TODO "DECIDE (sharper now):
resolved_before_signal").

Rule: every model-resolved branch (annotation mode `correctly_not_taken`) that is OLDER than the
transmitter, NOT COMMITTED (spo position after the last committed instruction lc and before
the transmitter) and on the CORRECT PATH (older than the oldest unresolved/mispredicted window
branch; RG-1 = (b), Anna 2026-11-16) must be visibly resolved (`resolve_visible`) strictly before
the transmitter's signal tick. Otherwise the record is not a hit. Wrong-path resolved branches
(after the oldest mispredicted branch) never gate; they are reported in `wrong_path`. A test with
no mispredicted branch (store shadows) has every older uncommitted resolved branch on the correct
path. Committed resolved branches (at or before lc) are
not gated here: a branch cannot retire before it resolves, and the checkers already require
`lc_retire < signal`. Branches younger than the transmitter are not part of the rule.

One pure function, `evaluate`, used by
  * `gem5_common.process_one` (criteria key `resolved_older_before_signal`, ANDed into
    `issued_in_window`), and
  * the offline re-scorer `STAGE3_gem5/triage/rescore_resolved_gate.py` (saved raw records, no
    gem5 rerun).

spo position = the annotation's `branch_pc` (the Alloy program-order index), never the x86
address. A record's `resolved_branches` list is built by process_one in annotation order from the
`correctly_not_taken` entries that carry `branch_addr`; records written since 2026-11-16 also
carry `spo` per entry. Older records are mapped positionally to the same filtered annotation list
(cache_setup remaps addresses but keeps the annotation list, so addresses cannot be used offline).

Value: True / False, or None when the rule does not apply or cannot be decided:
  * no gated branch (none older than the transmitter and uncommitted),
  * no BR lines (binary without resolve hooks: visible ticks are unknown),
  * no signal tick (e.g. check_footprint records, which have no single transmitter signal),
  * the record's resolved_branches cannot be mapped to the annotation.
None never gates (same convention as every other `criteria` key).
"""
from __future__ import annotations

from typing import List, Optional


def _resolved_entries(ann: dict) -> List[dict]:
    """The annotation entries process_one turns into resolved_branches, in order."""
    return [e for e in (ann.get("annotations") or [])
            if e.get("mode") == "correctly_not_taken" and "branch_addr" in e]


def _boundary(ann: dict):
    cb = ann.get("commit_boundary") or {}
    lc = (cb.get("last_committed") or {}).get("pc")
    fnc = (cb.get("first_noncommitted") or {}).get("pc")
    return lc, fnc


def _committed(spo: int, lc: Optional[int], fnc: Optional[int]) -> bool:
    """Committed = at or before lc (equivalently before fnc when only fnc is specified)."""
    if lc is not None:
        return spo <= lc
    if fnc is not None:
        return spo < fnc
    return False


def evaluate(resolved_branches: Optional[List[dict]], signal: Optional[int], ann: dict,
             br_observed: bool = True) -> dict:
    """Apply the rule to one record. Pure: no I/O, no globals.

    resolved_branches  the record's `resolved_branches` (pc, visible_tick, stall[, spo])
    signal             the transmitter's signal tick (`xmit_signal`); falsy = unknown
    ann                the test's .ann.json dict (xmit, commit_boundary, annotations)
    br_observed        False when the binary printed no BR lines (no resolve hooks)

    Returns dict(value, gated, wrong_path, committed, younger, notes). `gated` lists every older,
    uncommitted, correct-path resolved branch (spo, visible_tick, ok); `wrong_path` the older
    uncommitted ones after the oldest mispredicted branch (reported, never gated); `committed` the
    committed older ones (for the lc_retire cross-check, never gated here).
    """
    out = dict(value=None, gated=[], wrong_path=[], committed=[], younger=0, notes=[])
    rb = list(resolved_branches or [])
    if not rb:
        return out
    xm = (ann.get("xmit") or {}).get("pc")
    if xm is None:
        out["notes"].append("no xmit spo")
        return out
    lc, fnc = _boundary(ann)
    ents = _resolved_entries(ann)
    spos = []
    if all(b.get("spo") is not None for b in rb):
        spos = [int(b["spo"]) for b in rb]
    elif len(ents) == len(rb):
        spos = [int(e["branch_pc"]) for e in ents]
    else:
        out["notes"].append(f"cannot map {len(rb)} resolved_branches to {len(ents)} entries")
        return out
    mis = [int(e["branch_pc"]) for e in (ann.get("annotations") or [])
           if str(e.get("mode", "")).startswith("mispredict") and e.get("branch_pc") is not None
           and int(e["branch_pc"]) != int(xm)]
    oldest_mis = min(mis) if mis else None
    sig = int(signal or 0)
    for b, spo in zip(rb, spos):
        if spo >= int(xm):
            out["younger"] += 1
            continue
        vt = int(b.get("visible_tick") or 0)
        ok = bool(vt) and sig > 0 and vt < sig
        row = dict(pc=b.get("pc"), spo=spo, stall=int(b.get("stall") or 0), visible_tick=vt,
                   ok=ok, path=("correct" if oldest_mis is None or spo < oldest_mis
                                else "wrong"))
        if _committed(spo, lc, fnc):
            out["committed"].append(row)
        elif row["path"] == "wrong":
            out["wrong_path"].append(row)
        else:
            out["gated"].append(row)
    if not out["gated"]:
        return out
    if not br_observed:
        out["notes"].append("no BR lines: visible ticks unknown")
        return out
    if sig <= 0:
        out["notes"].append("no signal tick")
        return out
    out["value"] = all(g["ok"] for g in out["gated"])
    if out["value"] is False:
        bad = [f"{g['pc']}(spo {g['spo']}, visible {g['visible_tick']})"
               for g in out["gated"] if not g["ok"]]
        out["notes"].append("older uncommitted correct-path resolved branch not visibly resolved before "
                            f"signal {sig}: " + ", ".join(bad))
    return out

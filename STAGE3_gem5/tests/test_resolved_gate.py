#!/usr/bin/env python3
"""Tests for resolved_gate.evaluate (resolved-branch gate, Anna 2026-11-16 option b; RG-1 (b): correct path only).
Run from the repo root:  python3 -m unittest STAGE3_gem5/tests/test_resolved_gate.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import resolved_gate as rg   # noqa: E402

# spo: 0 resolved (committed, lc), 1 resolved (uncommitted, correct path), 2 mispredicted window
# branch, 3 resolved (wrong path, older than xmit), 4 = xmit, 5 resolved (younger than xmit).
ANN = {"xmit": {"pc": 4, "kind": "ld", "addr": 0x50},
       "commit_boundary": {"last_committed": {"pc": 0, "addr": 0x10},
                           "first_noncommitted": {"pc": 1, "addr": 0x20}},
       "annotations": [
           {"branch_pc": 0, "mode": "correctly_not_taken", "branch_addr": 0x10},
           {"branch_pc": 1, "mode": "correctly_not_taken", "branch_addr": 0x20},
           {"branch_pc": 2, "mode": "mispredict_not_taken", "branch_addr": 0x30},
           {"branch_pc": 3, "mode": "correctly_not_taken", "branch_addr": 0x40},
           {"branch_pc": 5, "mode": "correctly_not_taken", "branch_addr": 0x60}]}


def rb(t0, t1, t3, t5, spo=False):
    out = [dict(pc=hex(a), visible_tick=t, stall=0) for a, t in
           ((0x10, t0), (0x20, t1), (0x40, t3), (0x60, t5))]
    if spo:
        for b, s in zip(out, (0, 1, 3, 5)):
            b["spo"] = s
    return out


class ResolvedGate(unittest.TestCase):
    def test_all_older_resolved_before_signal(self):
        r = rg.evaluate(rb(10, 20, 30, 0), 100, ANN)
        self.assertIs(r["value"], True)
        self.assertEqual([g["spo"] for g in r["gated"]], [1])
        self.assertEqual([g["spo"] for g in r["wrong_path"]], [3])
        self.assertEqual([c["spo"] for c in r["committed"]], [0])
        self.assertEqual(r["younger"], 1)

    def test_younger_and_committed_not_gated(self):
        # committed spo 0 and younger spo 5 resolve late or never: not part of the rule
        self.assertIs(rg.evaluate(rb(500, 20, 30, 0), 100, ANN)["value"], True)

    def test_uncommitted_correct_path_late(self):
        r = rg.evaluate(rb(10, 100, 30, 0), 100, ANN)   # equal to the signal = not before
        self.assertIs(r["value"], False)
        self.assertEqual([g["ok"] for g in r["gated"]], [False])

    def test_wrong_path_never_gates(self):
        # RG-1 (b): spo 3 is after the mispredicted window branch (spo 2): never resolved, or
        # resolved at / after the signal, it must not gate
        for t3 in (0, 100, 150):
            r = rg.evaluate(rb(10, 20, t3, 0), 100, ANN)
            self.assertIs(r["value"], True)
            self.assertEqual([w["ok"] for w in r["wrong_path"]], [False])
        # only a wrong-path resolved branch older than the xmit: rule does not apply
        ann = dict(ANN, annotations=ANN["annotations"][:1] + ANN["annotations"][2:4])
        r = rg.evaluate([dict(pc="0x10", visible_tick=10, stall=0),
                         dict(pc="0x40", visible_tick=0, stall=2500)], 100, ann)
        self.assertIsNone(r["value"])
        self.assertEqual(len(r["wrong_path"]), 1)

    def test_no_window_branch_all_correct_path(self):
        # store-shadow test: no mispredicted branch, so every older uncommitted one gates
        ann = dict(ANN, annotations=[e for e in ANN["annotations"]
                                     if e["mode"] == "correctly_not_taken"])
        self.assertIs(rg.evaluate(rb(10, 20, 0, 0), 100, ann)["value"], False)
        self.assertIs(rg.evaluate(rb(10, 20, 30, 0), 100, ann)["value"], True)

    def test_spo_field_overrides_position(self):
        self.assertIs(rg.evaluate(rb(10, 20, 30, 0, spo=True), 100, ANN)["value"], True)
        # with spo given, a list in another order still maps correctly
        b = rb(10, 0, 30, 30, spo=True)          # spo 1 (correct path) never resolved
        self.assertIs(rg.evaluate(b, 100, ANN)["value"], False)
        b[1]["spo"], b[3]["spo"] = 5, 1          # swap: spo 1 now has visible 30
        self.assertIs(rg.evaluate(b, 100, ANN)["value"], True)

    def test_not_applicable(self):
        self.assertIsNone(rg.evaluate([], 100, ANN)["value"])
        self.assertIsNone(rg.evaluate(rb(10, 0, 0, 0), 0, ANN)["value"])          # no signal
        self.assertIsNone(rg.evaluate(rb(10, 0, 0, 0), 100, ANN,
                                      br_observed=False)["value"])               # no BR lines
        self.assertIsNone(rg.evaluate(rb(10, 0, 0, 0)[:2], 100, ANN)["value"])   # cannot map
        only_committed = dict(ANN, annotations=ANN["annotations"][:1] + ANN["annotations"][2:3])
        self.assertIsNone(rg.evaluate([dict(pc="0x10", visible_tick=0, stall=0)], 100,
                                      only_committed)["value"])

    def test_no_lc_uses_fnc(self):
        ann = dict(ANN, commit_boundary={"first_noncommitted": {"pc": 1}})
        r = rg.evaluate(rb(500, 20, 30, 0), 100, ann)
        self.assertIs(r["value"], True)
        self.assertEqual([c["spo"] for c in r["committed"]], [0])
        ann = dict(ANN, commit_boundary={})
        self.assertIs(rg.evaluate(rb(500, 20, 30, 0), 100, ann)["value"], False)   # spo 0 gated

    def test_xmit_branch_not_counted_as_window_branch(self):
        # a br_x transmitter annotated as mispredict must not define the wrong path
        ann = dict(ANN, annotations=ANN["annotations"][:2] + ANN["annotations"][3:] +
                   [{"branch_pc": 4, "mode": "mispredict_not_taken", "branch_addr": 0x50}])
        r = rg.evaluate(rb(10, 20, 30, 0), 100, ann)
        self.assertEqual([g["spo"] for g in r["gated"]], [1, 3])
        self.assertEqual(r["wrong_path"], [])


if __name__ == "__main__":
    unittest.main()

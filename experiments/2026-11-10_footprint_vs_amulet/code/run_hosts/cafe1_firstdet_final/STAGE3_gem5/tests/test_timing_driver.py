#!/usr/bin/env python3
"""Tests for timing_driver.py's optional transmitter-kind filter (--xmit-kinds, fanoutgaps
2026-11-09): default 'all' gives the same order as before; a kind list keeps a subsequence
of that order. Run: python3 -m unittest STAGE3_gem5/tests/test_timing_driver.py
"""
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "timing"))
import timing_driver as td   # noqa: E402

MODES = ["mispredict_not_taken", "mispredict_taken"]


def _testset(root: Path, n=40):
    kinds = {}
    for m in MODES:
        for d in ("asm", "ann"):
            (root / m / d).mkdir(parents=True)
        for i in range(n):
            s = f"inst-{i:06d}"
            k = ["ld", "br_x", "other_x"][i % 3]
            kinds[(m, s)] = k
            (root / m / "asm" / f"{s}.s").write_text("")
            (root / m / "ann" / f"{s}.ann.json").write_text(json.dumps({"xmit": {"kind": k}}))
    return kinds


class XmitKinds(unittest.TestCase):
    def test_parse(self):
        self.assertIsNone(td.parse_kinds("all"))
        self.assertIsNone(td.parse_kinds(""))
        self.assertIsNone(td.parse_kinds("ld,all"))
        self.assertEqual(td.parse_kinds("ld, br_x"), {"ld", "br_x"})

    def test_default_order_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            _testset(root)
            pairs = sorted((m, f"inst-{i:06d}") for m in MODES for i in range(40))
            random.Random(20261109).shuffle(pairs)   # the pre-2026-11-09 rule
            self.assertEqual(td.build_order(root, MODES, 20261109), pairs)
            self.assertEqual(td.build_order(root, MODES, 20261109, None), pairs)

    def test_filter_is_subsequence(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            kinds = _testset(root)
            full = td.build_order(root, MODES, 20261109)
            ld = td.build_order(root, MODES, 20261109, {"ld"})
            self.assertEqual(ld, [p for p in full if kinds[p] == "ld"])
            two = td.build_order(root, MODES, 20261109, {"ld", "br_x"})
            self.assertEqual(two, [p for p in full if kinds[p] in ("ld", "br_x")])


if __name__ == "__main__":
    unittest.main()

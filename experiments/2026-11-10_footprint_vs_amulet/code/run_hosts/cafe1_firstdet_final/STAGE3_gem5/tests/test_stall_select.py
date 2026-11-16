#!/usr/bin/env python3
"""Tests for pipeline._per_branch_resolved (sweep.resolved_stall_per_branch, firstdet-final
2026-11-10): per-test random resolved-branch stall, one grid point per test, deterministic per
(seed, stem); absent key = legacy grid (byte-identical ann). Run from the repo root:
    python3 -m unittest STAGE3_gem5/tests/test_stall_select.py
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pipeline as pl   # noqa: E402

ANN = {"xmit": {"pc": 9, "kind": "ld"},
       "annotations": [
           {"branch_pc": 2, "mode": "correctly_not_taken"},
           {"branch_pc": 3, "mode": "correctly_not_taken"},
           {"branch_pc": 5, "mode": "mispredict_not_taken"},
           {"branch_pc": 9, "mode": "correctly_not_taken"}]}
RES = {"mode": "random", "choices": [0, 500, 2500], "seed": 0}
UNR = {"mode": "random", "choices": [2500, 5000, 10000], "seed": 0}


def grid_for(stem, sweep):
    """The exact call sequence of pipeline.py's two grid builders."""
    resolved, unresolved = pl._classify_branches(ANN)
    g = pl._grid_points(resolved, sweep.get("points", [0]),
                        unresolved_points=sweep.get("unresolved_points"),
                        max_grid=sweep.get("max_grid"), seed=pl.zlib.crc32(stem.encode()))
    g = pl._per_branch_unresolved(g, unresolved, sweep.get("unresolved_stall_per_branch"),
                                  stem, sweep.get("max_grid"))
    g = pl._per_branch_resolved(g, resolved, sweep.get("resolved_stall_per_branch"), stem)
    return g


class ResolvedSelect(unittest.TestCase):
    def test_absent_key_is_legacy(self):
        for sweep in ({"points": [0]}, {"points": [0, 500, 2500]},
                      {"points": [0], "unresolved_stall_per_branch": UNR}):
            resolved, unresolved = pl._classify_branches(ANN)
            g0 = pl._grid_points(resolved, sweep["points"], seed=pl.zlib.crc32(b"inst-1"))
            g0 = pl._per_branch_unresolved(g0, unresolved, sweep.get("unresolved_stall_per_branch"),
                                           "inst-1", None)
            g1 = grid_for("inst-1", sweep)
            self.assertEqual(g0, g1)
            self.assertEqual([json.dumps(pl._inject_stalls(ANN, s, 5000), indent=2) for s in g0],
                             [json.dumps(pl._inject_stalls(ANN, s, 5000), indent=2) for s in g1])
        self.assertEqual(len(grid_for("inst-1", {"points": [0, 500, 2500]})), 9)  # still sweeps all

    def test_one_point_per_test_from_choices(self):
        sweep = {"points": [0], "resolved_stall_per_branch": RES, "unresolved_stall_per_branch": UNR}
        for i in range(50):
            g = grid_for(f"inst-{i:06d}", sweep)
            self.assertEqual(len(g), 1)
            self.assertIn(g[0][2], RES["choices"])
            self.assertIn(g[0][3], RES["choices"])
            self.assertIn(g[0][5], UNR["choices"])
            self.assertNotIn(9, g[0])   # xmit branch never in the draw
            a = pl._inject_stalls(ANN, g[0], 5000)
            st = {e["branch_pc"]: e["resolve_stall_cycles"] for e in a["annotations"]}
            self.assertEqual(st[9], 0)
            self.assertEqual((st[2], st[3], st[5]), (g[0][2], g[0][3], g[0][5]))

    def test_deterministic_and_seeded(self):
        sweep = {"points": [0], "resolved_stall_per_branch": RES}
        self.assertEqual(grid_for("inst-000007", sweep), grid_for("inst-000007", sweep))
        other = {"points": [0], "resolved_stall_per_branch": dict(RES, seed=1)}
        draws0 = [tuple(grid_for(f"inst-{i}", sweep)[0].values()) for i in range(60)]
        draws1 = [tuple(grid_for(f"inst-{i}", other)[0].values()) for i in range(60)]
        self.assertNotEqual(draws0, draws1)

    def test_roughly_uniform(self):
        sweep = {"points": [0], "resolved_stall_per_branch": RES}
        cnt = {c: 0 for c in RES["choices"]}
        for i in range(3000):
            cnt[grid_for(f"inst-{i:06d}", sweep)[0][2]] += 1
        for c, n in cnt.items():
            self.assertTrue(850 < n < 1150, cnt)

    def test_no_resolved_branches(self):
        ann = {"xmit": {"pc": 9}, "annotations": [{"branch_pc": 5, "mode": "mispredict_taken"}]}
        resolved, _ = pl._classify_branches(ann)
        self.assertEqual(pl._per_branch_resolved([{}], resolved, RES, "x"), [{}])

    def test_bad_mode(self):
        with self.assertRaises(ValueError):
            pl._per_branch_resolved([{}], [2], {"mode": "sweep", "choices": [0]}, "x")


if __name__ == "__main__":
    unittest.main()


class TimingGrid(unittest.TestCase):
    """sweep.timing_grid (2026-11-10): one whole-test (unresolved, resolved) point per test."""
    TG = {"unresolved": [2500, 5000, 10000], "resolved": [0, 500, 2500], "seed": "tgrid-v1"}

    def grid(self, stem, sweep):
        resolved, unresolved = pl._classify_branches(ANN)
        g = pl._grid_points(resolved, sweep.get("points", [0]), seed=pl.zlib.crc32(stem.encode()))
        return pl._per_branch_all(g, resolved, unresolved, sweep, stem)

    def test_absent_is_legacy(self):
        for sweep in ({"points": [0]}, {"points": [0, 500, 2500]},
                      {"points": [0], "unresolved_stall_per_branch": UNR, "resolved_stall_per_branch": RES}):
            self.assertEqual(self.grid("inst-3", sweep), grid_for("inst-3", sweep))
        self.assertIsNone(pl._timing_grid_point("inst-3", {"points": [0]}))

    def test_one_point_all_branches(self):
        sweep = {"points": [0], "timing_grid": self.TG}
        seen = set()
        for i in range(900):
            st = f"inst-{i:06d}"
            g = self.grid(st, sweep)
            self.assertEqual(len(g), 1)
            u, r = pl._timing_grid_point(st, sweep)
            self.assertEqual((g[0][5], g[0][2], g[0][3]), (u, r, r))
            a = pl._inject_stalls(ANN, g[0], 5000)
            stl = {e["branch_pc"]: e["resolve_stall_cycles"] for e in a["annotations"]}
            self.assertEqual((stl[2], stl[3], stl[5], stl[9]), (r, r, u, 0))
            seen.add((u, r))
        self.assertEqual(len(seen), 9)
        self.assertIn((5000, 0), seen)   # the old parity timing is one point

    def test_uniform_and_deterministic(self):
        sweep = {"points": [0], "timing_grid": self.TG}
        import collections
        c = collections.Counter(pl._timing_grid_point(f"inst-{i}", sweep) for i in range(9000))
        for n in c.values():
            self.assertTrue(850 < n < 1150, c)
        self.assertEqual(pl._timing_grid_point("inst-7", sweep), pl._timing_grid_point("inst-7", sweep))

    def test_mix_fixed_keeps_base(self):
        sweep = {"points": [0], "unresolved_stall_per_branch": UNR, "resolved_stall_per_branch": RES,
                 "timing_mix": {"p_fixed": 1.0}}
        self.assertEqual(self.grid("inst-1", sweep), [{2: 0, 3: 0}])   # base grid: resolved at points[0]
        a = pl._inject_stalls(ANN, {}, 5000)
        stl = {e["branch_pc"]: e["resolve_stall_cycles"] for e in a["annotations"]}
        self.assertEqual((stl[2], stl[3], stl[5]), (0, 0, 5000))

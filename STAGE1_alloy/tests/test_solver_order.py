#!/usr/bin/env python3
"""Tests for alloy_solver_order.py + pipeline.phase_xml's seeded random order (loosepin, 2026-11-09).

Run: python3 -m unittest discover -s STAGE1_alloy/tests -v   (repo root). The real-Java test needs a working
`java` + `javac` (JDK 17) on PATH and is skipped otherwise (on the Mac: PATH=/opt/homebrew/opt/openjdk@17/bin:$PATH).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import alloy_solver_order as aso  # noqa: E402
import pipeline  # noqa: E402

FAKE_JAVA = r'''
import sys, pathlib
out, seed = pathlib.Path(sys.argv[1]), sys.argv[2]
progs = {"default": ["A"], "1": ["A", "B", "C"], "2": ["B", "D"], "3": ["D", "A"]}[seed]
for k, body in enumerate(progs, 1):
    (out / f"inst-{k:06d}.xml").write_text(f"<xml>{body}</xml>")
    (out / f"inst-{k:06d}.txt").write_text(body)
print("Total models: %d" % len(progs))
'''


def content_fp(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class ConfigTests(unittest.TestCase):
    def test_default_is_none(self):
        self.assertIsNone(aso.configured({}))
        self.assertIsNone(aso.configured({"alloy": {"max_instances": 5}}))
        self.assertIsNone(aso.configured({"alloy": {"solver_order": {"mode": "default"}}}))

    def test_random_normalized(self):
        so = aso.configured({"alloy": {"solver_order": {"mode": "random", "seeds": [4, "default"], "walk_p": 0.1}}})
        self.assertEqual(so["seeds"], [4, "default"]); self.assertEqual(so["walk_p"], 0.1)
        self.assertFalse(so["parallel"]); self.assertFalse(so["keep_raw"])

    def test_bad_configs(self):
        for bad in ({"mode": "rand"}, {"mode": "random", "seeds": []}, {"mode": "random", "seeds": [1, 1]},
                    {"mode": "random", "seeds": ["x"]}, {"mode": "random", "walk_p": 2},
                    {"mode": "random", "sedes": [1]}, {"mode": "random", "seeds": [True]}):
            with self.assertRaises(ValueError, msg=str(bad)):
                aso.configured({"alloy": {"solver_order": bad}})


class DefaultPathUnchanged(unittest.TestCase):
    """With no solver_order (or mode default) phase_xml must run the old a6CountModels command, unchanged."""

    def _run(self, alloy_cfg):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); (td / "models").mkdir(); (td / "models" / "M.als").write_text("sig A {}\nrun {} for 1\n")
            cfg = {"paths": {"alloy_stage": str(td), "models_dir": str(td / "models"), "stage2_dir": str(td)},
                   "alloy": alloy_cfg}
            calls = []

            def fake_run(cmd, cwd=None, capture_output=None, text=None):
                calls.append((cmd, cwd)); return subprocess.CompletedProcess(cmd, 0, "", "")
            with mock.patch.object(pipeline.subprocess, "run", fake_run):
                pipeline.phase_xml(cfg, "M", td / "ts", False)
            return calls, td

    def test_no_solver_order(self):
        calls, td = self._run({"max_instances": 7})
        self.assertEqual(len(calls), 1)
        cmd, cwd = calls[0]
        self.assertEqual(cmd[:4], ["java", "-cp", "alloy6.jar:.", "a6CountModels"])
        self.assertEqual(cmd[2:], ["alloy6.jar:.", "a6CountModels", cmd[4], cmd[5], "7"])
        self.assertTrue(cmd[4].endswith("models/M.als")); self.assertTrue(cmd[5].endswith("ts/xml"))

    def test_mode_default(self):
        calls, _ = self._run({"max_instances": 7, "solver_order": {"mode": "default", "seeds": [1]}})
        self.assertEqual(len(calls), 1); self.assertEqual(calls[0][0][3], "a6CountModels")


class RandomMerge(unittest.TestCase):
    def _go(self, seeds, parallel=False):
        td = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td)
        (td / "fake.py").write_text(FAKE_JAVA); (td / "M.als").write_text("x")
        so = aso.configured({"alloy": {"solver_order": {"mode": "random", "seeds": seeds, "parallel": parallel}}})
        cmd_fn = lambda seed, model, out, cap, so: [sys.executable, str(td / "fake.py"), str(out), str(seed)]
        rec = aso.run_random_xml({}, so, td / "M.als", td / "xml", td, td, 100, fingerprint=content_fp,
                                 cmd_fn=cmd_fn, poll_s=0.05)
        return td / "xml", rec

    def test_dedup_and_numbering(self):
        x, rec = self._go(["default", 1, 2, 3])
        names = sorted(p.name for p in x.glob("inst-*.xml"))
        self.assertEqual(names, [f"inst-{k:06d}.xml" for k in range(1, 5)])
        self.assertEqual([(x / n).read_text() for n in names], [f"<xml>{c}</xml>" for c in "ABCD"])
        self.assertEqual(sorted(p.name for p in x.glob("inst-*.txt")), [n[:-4] + ".txt" for n in names])
        self.assertEqual(rec["kept_total"], 4); self.assertEqual(rec["duplicates_total"], 4)
        self.assertEqual([s["verdict"] for s in rec["seeds"]], ["EXHAUSTED"] * 4)
        self.assertEqual([s["kept_new"] for s in rec["seeds"]], [1, 2, 1, 0])
        rows = [json.loads(l) for l in (x / "_dedup_map.jsonl").read_text().splitlines()]
        self.assertEqual([(r["name"], r["seed"], r["source"]) for r in rows],
                         [("inst-000001.xml", "default", "inst-000001.xml"), ("inst-000002.xml", 1, "inst-000002.xml"),
                          ("inst-000003.xml", 1, "inst-000003.xml"), ("inst-000004.xml", 2, "inst-000002.xml")])
        dups = [json.loads(l) for l in (x / "_dedup_dups.jsonl").read_text().splitlines()]
        self.assertEqual(len(dups), 4); self.assertEqual(dups[0]["duplicate_of"], "inst-000001")
        prov = json.loads((x / "SOLVER_ORDER.json").read_text())
        self.assertEqual(prov["solver_order"]["seeds"], ["default", 1, 2, 3]); self.assertIn("model_sha256", prov)
        self.assertFalse((x / "_seeds").exists())
        self.assertIn("END kept_total=4", (x / "_solver_order.log").read_text())

    def test_parallel_same_numbering(self):
        a, _ = self._go(["default", 1, 2, 3])
        b, _ = self._go(["default", 1, 2, 3], parallel=True)
        rd = lambda d: [p.read_text() for p in sorted(d.glob("inst-*.xml"))]
        self.assertEqual(rd(a), rd(b))

    def test_refuses_populated_dir(self):
        td = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td)
        (td / "xml").mkdir(); (td / "xml" / "inst-000001.xml").write_text("x")
        so = aso.configured({"alloy": {"solver_order": {"mode": "random"}}})
        with self.assertRaises(RuntimeError):
            aso.run_random_xml({}, so, td / "M.als", td / "xml", td, td, 1, fingerprint=content_fp,
                               cmd_fn=lambda *a: ["true"])


class RealFingerprint(unittest.TestCase):
    def test_same_xml_same_fp(self):
        d = ROOT / "STAGE1_alloy" / "dummy_out"
        xs = sorted(d.glob("inst-*.xml"))[:3]
        if len(xs) < 2:
            self.skipTest("no dummy XMLs")
        try:
            fp = aso.make_fingerprinter(ROOT / "STAGE2_compilation")
            vals = [fp(x) for x in xs]
        except Exception as e:  # parsexml may need the instruction tables etc.
            self.skipTest(f"parsexml unavailable here: {e}")
        td = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td)
        shutil.copy(xs[0], td / "copy.xml")
        self.assertEqual(fp(td / "copy.xml"), vals[0])


def _java_ok():
    try:
        return (subprocess.run(["java", "-version"], capture_output=True).returncode == 0 and
                subprocess.run(["javac", "-version"], capture_output=True).returncode == 0)
    except OSError:
        return False


@unittest.skipUnless(_java_ok(), "needs java + javac (JDK 17) on PATH")
class RealJavaReproducible(unittest.TestCase):
    def test_seed_reproducible_and_seeds_differ(self):
        alloy_stage = ROOT / "STAGE1_alloy"
        td = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, td)
        model = td / "toy.als"
        model.write_text("sig A { r: set A }\nrun {} for 3\n")
        txt_fp = lambda p: hashlib.sha256(Path(p).with_suffix(".txt").read_bytes()).hexdigest()

        def run(seed, sub):
            so = aso.configured({"alloy": {"solver_order": {"mode": "random", "seeds": [seed]}}})
            aso.run_random_xml({}, so, model, td / sub / "xml", alloy_stage, td, 15, fingerprint=txt_fp)
            return [p.read_text() for p in sorted((td / sub / "xml").glob("inst-*.txt"))]
        a, b, c = run(7, "a"), run(7, "b"), run(8, "c")
        self.assertEqual(len(a), 15); self.assertEqual(a, b); self.assertNotEqual(a, c)
        prov = json.loads((td / "a" / "xml" / "SOLVER_ORDER.json").read_text())
        self.assertIn("a6RandomModels", prov["seeds"][0]["cmd"]); self.assertEqual(prov["seeds"][0]["verdict"], "CAPPED")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for fpr.p, the per-load probability of vector-register routing (xmm-fix-agent, 2026-11-16).

Anna 2026-11-16: routing every consumed load through an xmm register (recipe A, fpr without "p") is bad practice; vector routing is meant
as an alternative concretization of a load, next to the integer one. parsexml.py pass5_emit_llvm got an optional fpr_cfg["p"]
(docstring "p"): each eligible load is routed with probability p, decided by its own rng seeded "fpr_p:<func_name>".

  absent  -> .ll and .ann.json byte-identical to the pristine copy proposed/pre_fpr_p_20261116/parsexml.py (the code that built the
             evaluated corpora; sha256 7611a4bc...)
  p = 1   -> same .ll as absent; the ann adds "p" and "n_eligible"
  p = 0   -> same .ll as fpr off; no routes
  0<p<1   -> only the routed loads' lines differ from fpr off; the register/form draws are the same sequence as with p = 1;
             the routed share of eligible loads matches p.
Recipes: runconfigs/bigcorpus_20261115/stage2_final_A.jsonc (frozen) and stage2_final_A_fpralt.jsonc (= A + fpr.p 0.5).
Fixtures: tests/fixtures/vocab_xml/ (24 STT_6_u + 8 CleanupSpec_6 XMLs). Stops at .ll / .ann.json.
Run: python3 -m unittest STAGE2_compilation/tests/test_fpr_p.py  (or python3 -m pytest STAGE2_compilation/tests)
"""
import copy
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
S2 = HERE.parent
ROOT = S2.parent
sys.path.insert(0, str(S2))
import parsexml as P            # noqa: E402
import batch_generate as BG     # noqa: E402

XMLS = sorted((HERE / "fixtures" / "vocab_xml").glob("*.xml"))
MODES = ["mispredict_not_taken", "mispredict_taken"]
PRISTINE = S2 / "proposed" / "pre_fpr_p_20261116" / "parsexml.py"
CFG_A = ROOT / "runconfigs" / "bigcorpus_20261115" / "stage2_final_A.jsonc"
CFG_ALT = ROOT / "runconfigs" / "bigcorpus_20261115" / "stage2_final_A_fpralt.jsonc"


def _jsonc(path):
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'//[^\n]*', '', t)
    return json.loads(t)


def _args(cfg):
    """the keys pipeline.py phase_llvm passes to batch_generate.py"""
    return dict(tables=str(ROOT / cfg["paths"]["instruction_tables"]), interleave=cfg.get("interleave") or None,
                fpr=cfg["fpr"] if cfg.get("fpr", {}).get("enabled") else None,
                reg_naming=cfg.get("reg_naming") or dict(BG.DEFAULT_REG_NAMING),
                fv2=cfg["fanout_v2"] if cfg.get("fanout_v2", {}).get("enabled") else None,
                brcond=cfg["branch_cond"] if cfg.get("branch_cond", {}).get("from_alloy") else None)


A = _args(_jsonc(CFG_A))
ALT = _args(_jsonc(CFG_ALT))


def _with_fpr(a, **kw):
    b = copy.deepcopy(a)
    b["fpr"] = None if kw.get("off") else dict(b["fpr"], **kw)
    return b


def _fns(mod):
    return (mod.parse_alloy_xml, mod.pass1_specify_state_a, mod.pass2_specify_instructions, mod.pass2_5_specify_branches,
            mod.pass2_6_specify_stl, mod.pass_interleave, mod.pass3_assign_operands, mod.pass4_ssa, mod.pass5_emit_llvm,
            mod.emit_branch_annotations)


def gen(xml, mode, a, mod=P, stem=None):
    stem = stem or xml.stem
    mod.reload_tables(a["tables"])
    with tempfile.TemporaryDirectory() as td:
        BG.run_pipeline(xml.read_text(encoding="utf-8"), stem, Path(td), mode, _fns=_fns(mod),
                        interleave_cfg=a["interleave"], fpr_cfg=a["fpr"], reg_naming_cfg=a["reg_naming"],
                        fv2_cfg=a["fv2"], brcond_cfg=a["brcond"])
        ll = (Path(td) / f"{stem}.ll").read_text()
        annb = (Path(td) / f"{stem}.ann.json").read_bytes()
    return ll, annb, json.loads(annb)


def _load_pristine():
    td = Path(tempfile.mkdtemp(prefix="pristine_fpr_p_"))
    shutil.copy(PRISTINE, td / "parsexml.py")
    (td / "instruction_tables").symlink_to(S2 / "instruction_tables")
    spec = importlib.util.spec_from_file_location("parsexml_pristine_fpr_p", td / "parsexml.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m, td


def tearDownModule():
    P.reload_tables(None)


class RecipeFiles(unittest.TestCase):
    def test_fpralt_is_A_plus_p_only(self):
        a, alt = _jsonc(CFG_A), _jsonc(CFG_ALT)
        self.assertEqual(alt["fpr"]["p"], 0.5)
        alt["fpr"].pop("p")
        self.assertEqual(a, alt)
        self.assertNotIn("p", a["fpr"])


class DefaultUnchanged(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.td = _load_pristine()

    @classmethod
    def tearDownClass(cls):
        cls.old.reload_tables(None)
        shutil.rmtree(cls.td, ignore_errors=True)

    def test_absent_byte_identical_to_pristine(self):
        for m in MODES:
            for x in XMLS:
                new, old = gen(x, m, A), gen(x, m, A, mod=self.old)
                self.assertEqual(new[0], old[0], f"{x.name} {m}: .ll differs")
                self.assertEqual(new[1], old[1], f"{x.name} {m}: .ann.json differs")

    def test_fpr_off_byte_identical_to_pristine(self):
        off = _with_fpr(A, off=True)
        for x in XMLS[:8]:
            new, old = gen(x, MODES[0], off), gen(x, MODES[0], off, mod=self.old)
            self.assertEqual(new[:2], old[:2], x.name)


class PExtremes(unittest.TestCase):
    def test_p1_same_ll_as_absent(self):
        for m in MODES:
            for x in XMLS:
                ll_a, _, ann_a = gen(x, m, A)
                ll_1, _, ann_1 = gen(x, m, _with_fpr(A, p=1.0))
                self.assertEqual(ll_1, ll_a, f"{x.name} {m}")
                f1 = dict(ann_1["fpr"])
                self.assertEqual(f1.pop("p"), 1.0)
                self.assertEqual(f1.pop("n_eligible"), len(ann_a["fpr"]["routes"]))
                self.assertEqual(f1, ann_a["fpr"])

    def test_p0_same_ll_as_off(self):
        for m in MODES:
            for x in XMLS:
                ll_off, _, ann_off = gen(x, m, _with_fpr(A, off=True))
                ll_0, _, ann_0 = gen(x, m, _with_fpr(A, p=0.0))
                self.assertEqual(ll_0, ll_off, f"{x.name} {m}")
                self.assertEqual(ann_0["fpr"]["routes"], [])
                self.assertNotIn("fpr", ann_off)

    def test_invalid_p_raises(self):
        for bad in (-0.1, 1.5):
            with self.assertRaises(ValueError):
                gen(XMLS[0], MODES[0], _with_fpr(A, p=bad))


class PHalf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 32 fixtures x 2 modes x 6 stem names (the stem seeds every draw, so a new name = an independent concretization)
        cls.runs = []
        for k in range(6):
            for m in MODES:
                for x in XMLS:
                    st = f"{x.stem}_p{k}"
                    cls.runs.append((x, m, st, gen(x, m, ALT, stem=st), gen(x, m, _with_fpr(A, p=1.0), stem=st),
                                     gen(x, m, _with_fpr(A, off=True), stem=st)))

    def test_routed_share_matches_p(self):
        n = r = 0
        for _, _, _, alt, _, _ in self.runs:
            n += alt[2]["fpr"]["n_eligible"]
            r += len(alt[2]["fpr"]["routes"])
        self.assertGreater(n, 200)
        sd = (n * 0.25) ** 0.5
        self.assertLess(abs(r - 0.5 * n), 4 * sd + 1, (r, n))

    def test_some_tests_integer_only_and_some_routed(self):
        routed = [len(alt[2]["fpr"]["routes"]) for _, _, _, alt, _, _ in self.runs]
        self.assertTrue(any(v == 0 for v in routed))
        self.assertTrue(any(v > 0 for v in routed))

    def test_eligible_count_matches_p1(self):
        for x, m, st, alt, p1, _ in self.runs:
            self.assertEqual(alt[2]["fpr"]["n_eligible"], len(p1[2]["fpr"]["routes"]), f"{st} {m}")

    def test_register_and_form_draws_not_shifted(self):
        key = lambda r: (r["xmm"], r.get("form"), r.get("alu_xmm"))   # noqa: E731
        for x, m, st, alt, p1, _ in self.runs:
            ra = [key(r) for r in alt[2]["fpr"]["routes"]]
            r1 = [key(r) for r in p1[2]["fpr"]["routes"]]
            self.assertEqual(ra, r1[:len(ra)], f"{st} {m}")
            pcs1 = {r["pc"] for r in p1[2]["fpr"]["routes"]}
            self.assertLessEqual({r["pc"] for r in alt[2]["fpr"]["routes"]}, pcs1)

    def test_only_routed_load_lines_differ_from_off(self):
        for x, m, st, alt, _, off in self.runs:
            la, lo = alt[0].splitlines(), off[0].splitlines()
            self.assertEqual(len(la), len(lo), f"{st} {m}")
            diff = [a for a, b in zip(la, lo) if a != b]
            self.assertEqual(len(diff), len(alt[2]["fpr"]["routes"]), f"{st} {m}")
            safe = st.replace("-", "_").replace(".", "_")
            routed = {r["pc"] for r in alt[2]["fpr"]["routes"]}
            for d in diff:
                self.assertIn("%xmm", d)
                pcs = {int(v) for v in re.findall(rf"__litmus_{safe}_pc(\d+):", d)}
                self.assertTrue(pcs & routed, d[:200])

    def test_deterministic(self):
        for x in XMLS[:6]:
            for m in MODES:
                self.assertEqual(gen(x, m, ALT)[:2], gen(x, m, ALT)[:2])


if __name__ == "__main__":
    unittest.main()

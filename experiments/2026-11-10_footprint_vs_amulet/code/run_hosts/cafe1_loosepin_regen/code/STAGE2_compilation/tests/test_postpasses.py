#!/usr/bin/env python3
"""Tests for the Stage-2 post-passes (fanoutgaps, 2026-11-09):
make_rmw_corpus.py --select eligible|hash and make_jmp_corpus.py.

Pure-logic tests run anywhere. The build tests (re-resolve + rewrite a real test) need
the x86-64 GNU toolchain + llvm-objdump-15 that compile_annotate.py uses (cafe gem5_dev)
and are skipped elsewhere. Fixtures are the cache_setup ones (real fv2 / STT tests):
STAGE3_gem5/tests/fixtures/cache_setup/{fv2_otb_twobarrier (not_taken), stt_taken}.
Run: python3 -m pytest STAGE2_compilation/tests
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
S2 = HERE.parent
ROOT = S2.parent
sys.path.insert(0, str(S2))
import make_rmw_corpus as R   # noqa: E402
import make_jmp_corpus as J   # noqa: E402

FIX = ROOT / "STAGE3_gem5" / "tests" / "fixtures" / "cache_setup"
HAVE_TC = bool(shutil.which("llvm-objdump-15") and shutil.which("nm") and shutil.which("as")
               and subprocess.run(["as", "--version"], capture_output=True, text=True).stdout.startswith("GNU"))


class RmwSelection(unittest.TestCase):
    def test_choose_eligible_exact_share(self):
        el = [f"inst-{i:06d}" for i in range(1001)]
        ch = R.choose_eligible(el, 20261109, 0.5)
        self.assertEqual(len(ch), round(0.5 * 1001))
        self.assertEqual(ch, sorted(ch))
        self.assertEqual(ch, R.choose_eligible(list(reversed(el)), 20261109, 0.5))   # order-free
        self.assertEqual(R.choose_eligible(el, 20261109, 0.0), [])
        self.assertEqual(R.choose_eligible(el, 20261109, 1.0), el)

    def test_choose_eligible_lowest_rank(self):
        el = [f"inst-{i:06d}" for i in range(200)]
        ch = set(R.choose_eligible(el, 7, 0.25))
        worst = max(R.hash_rank(s, 7) for s in ch)
        self.assertTrue(all(R.hash_rank(s, 7) > worst for s in el if s not in ch))

    def test_hash_rank_matches_old_selection(self):
        # --select hash keeps the old rule: selected iff rank / 2**64 < fraction
        for s in (f"inst-{i:06d}" for i in range(300)):
            self.assertEqual(R.selected(s, 20261109, 0.5), R.hash_rank(s, 20261109) / 2.0 ** 64 < 0.5)

    def test_seed_changes_choice(self):
        el = [f"inst-{i:06d}" for i in range(400)]
        self.assertNotEqual(R.choose_eligible(el, 1, 0.5), R.choose_eligible(el, 2, 0.5))


def _ann(annots, xpc):
    return {"annotations": annots, "xmit": {"pc": xpc, "kind": "ld"}}


class JmpLogic(unittest.TestCase):
    def test_selection_deterministic_and_share(self):
        st = [f"inst-{i:06d}" for i in range(4000)]
        a = [s for s in st if J.selected(s, 20261109, 0.5)]
        self.assertEqual(a, [s for s in st if J.selected(s, 20261109, 0.5)])
        self.assertTrue(0.46 < len(a) / len(st) < 0.54)
        self.assertFalse(any(J.selected(s, 20261109, 0.0) for s in st))
        self.assertTrue(all(J.selected(s, 20261109, 1.0) for s in st))

    def test_candidates_window(self):
        a = _ann([{"branch_pc": 1, "btb_forced_target_pc": 2, "mode": "mispredict_not_taken"},
                  {"branch_pc": 4, "btb_forced_target_pc": 5, "mode": "correctly_not_taken"}], 6)
        self.assertEqual(J.candidates(a), [2, 3, 4, 5, 6])

    def test_candidates_exclude_taken_forced_target(self):
        a = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "mispredict_taken"},
                  {"branch_pc": 2, "btb_forced_target_pc": 3, "mode": "mispredict_not_taken"}], 3)
        self.assertEqual(J.candidates(a), [2, 3])     # 1 = BTB redirect target: never fetched before it

    def test_candidates_none_without_unresolved(self):
        a = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "correctly_not_taken"}], 3)
        self.assertEqual(J.candidates(a), [])
        self.assertEqual(J.candidates({"annotations": [], "xmit": {}}), [])

    def test_ordered_candidates_rotation(self):
        c = [2, 3, 4, 5]
        o = J.ordered_candidates("inst-000042", 20261109, c)
        self.assertEqual(sorted(o), c)
        i = c.index(o[0])
        self.assertEqual(o, c[i:] + c[:i])
        self.assertEqual(o, J.ordered_candidates("inst-000042", 20261109, c))

    def test_insert_jmp_text(self):
        lines = ["\t#NO_APP", "\t#APP", "\t.globl\t__litmus_inst_000001_pc2", "__litmus_inst_000001_pc2:",
                 "\tmovq\t(%r15), %rax", "\t#NO_APP"]
        at, why = J.marker_app_line(lines, "inst-000001", 2)
        self.assertEqual((at, why), (1, None))
        new = J.insert_jmp("\n".join(lines), at, "inst-000001").split("\n")
        self.assertEqual(new[1:7], ["\t#APP", "\t.globl\t__litmus_inst_000001_jmpins", "__litmus_inst_000001_jmpins:",
                                    "\tjmp\t.Lsimspect_jmpins", ".Lsimspect_jmpins:", "\t#NO_APP"])
        self.assertEqual(new[7:], lines[1:])
        self.assertEqual(J.marker_app_line(lines, "inst-000001", 9)[1], "marker_count_0")

    def test_map_instrs_relaxed_jcc(self):
        base = 0x401000
        old = [(0x0, "jae", "0x401010 <f+0x10>"), (0x2, "movq", "%rax, %rbx"), (0x10, "retq", "")]
        # jmp inserted at 0x2; the jae relaxes from 2 to 6 bytes, so everything after moves by 6
        new = [(0x0, "jae", "0x401016 <f+0x16>"), (0x6, "jmp", "0x401008 <f+0x8>"),
               (0x8, "movq", "%rax, %rbx"), (0x16, "retq", "")]
        self.assertEqual(J.map_instrs(old, new, 1, base, base), {0x0: 0x0, 0x2: 0x8, 0x10: 0x16})
        bad = list(new); bad[2] = (0x8, "movq", "%rax, %rcx")
        self.assertIsNone(J.map_instrs(old, bad, 1, base, base))
        badj = list(new); badj[0] = (0x0, "jae", "0x401008 <f+0x8>")
        self.assertIsNone(J.map_instrs(old, badj, 1, base, base))


def _mini_corpus(td: Path, cases):
    """<td>/src/<mode>/{asm,ann} from fixture dirs: cases = [(fixture dir, mode)]."""
    src = td / "src"
    for case, mode in cases:
        for d in ("asm", "ann"):
            (src / mode / d).mkdir(parents=True, exist_ok=True)
        s = next((FIX / case).glob("inst-*.s"))
        shutil.copy2(s, src / mode / "asm" / s.name)
        shutil.copy2(FIX / case / f"{s.stem}.ann.json", src / mode / "ann" / f"{s.stem}.ann.json")
    return src


def _run_jmp(td: Path, src: Path, p: float, modes):
    dst = td / f"dst_p{p}"
    subprocess.run([sys.executable, str(S2 / "make_jmp_corpus.py"), "--repo-root", str(ROOT), "--src", str(src),
                    "--dst", str(dst), "--p", str(p), "--jobs", "1", "--modes", *modes],
                   check=True, capture_output=True, text=True)
    return dst


class JmpCorpusOff(unittest.TestCase):
    def test_p0_byte_identical(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            src = _mini_corpus(td, [("fv2_otb_twobarrier", "mispredict_not_taken"), ("stt_taken", "mispredict_taken")])
            dst = _run_jmp(td, src, 0.0, ["mispredict_not_taken", "mispredict_taken"])
            for f in src.rglob("*"):
                if f.is_file():
                    self.assertEqual(f.read_bytes(), (dst / f.relative_to(src)).read_bytes(), f)
            self.assertEqual((dst / "jmp_stems.tsv").read_text().count("\n"), 1)


@unittest.skipUnless(HAVE_TC, "needs GNU as/ld/nm + llvm-objdump-15 (cafe gem5_dev)")
class JmpCorpusBuild(unittest.TestCase):
    def test_p1_inserts_and_reresolves(self):
        sys.path.insert(0, str(S2))
        import compile_annotate as ca
        J.CA = ca
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            cases = [("fv2_otb_twobarrier", "mispredict_not_taken"), ("stt_taken", "mispredict_taken")]
            src = _mini_corpus(td, cases)
            dst = _run_jmp(td, src, 1.0, [m for _, m in cases])
            rows = (dst / "jmp_stems.tsv").read_text().splitlines()[1:]
            self.assertEqual(len(rows), 2, (dst / "provenance.json").read_text())
            for _, mode in cases:
                s = next((dst / mode / "asm").glob("*.s"))
                ann = json.loads((dst / mode / "ann" / f"{s.stem}.ann.json").read_text())
                ji = ann["jmp_insert"]
                self.assertIn(ji["before_pc"], J.candidates(ann))
                # re-resolving the written .s reproduces the written annotation
                tmpl = dict(ann); tmpl.pop("jmp_insert")
                re_ann, dis, base, pcm = J.resolve_ann(s.read_text(), s.stem, tmpl)
                tmpl2 = dict(re_ann); self.assertEqual(tmpl2, tmpl)
                at = [d for d in dis if d[0] + base == ji["addr"]]
                self.assertEqual(at[0][1], "jmp")
                self.assertEqual(pcm[ji["before_pc"]] + base, ji["addr"] + 2)
                # the transmitter is still after the jmp, every branch force unchanged in kind
                self.assertGreater(ann["xmit"]["addr"], ji["addr"])


if __name__ == "__main__":
    unittest.main()

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

    def test_candidates_window_old_rule(self):
        a = _ann([{"branch_pc": 1, "btb_forced_target_pc": 2, "mode": "mispredict_not_taken"},
                  {"branch_pc": 4, "btb_forced_target_pc": 5, "mode": "correctly_not_taken"}], 6)
        self.assertEqual(J.candidates(a, placement="window"), [2, 3, 4, 5, 6])

    def test_candidates_exclude_taken_forced_target(self):
        a = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "mispredict_taken"},
                  {"branch_pc": 2, "btb_forced_target_pc": 3, "mode": "mispredict_not_taken"}], 3)
        self.assertEqual(J.candidates(a, placement="window"), [2, 3])     # 1 = BTB redirect target: never fetched before it

    def test_candidates_none_without_unresolved(self):
        a = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "correctly_not_taken"}], 3)
        self.assertEqual(J.candidates(a, placement="window"), [])
        self.assertEqual(J.candidates({"annotations": [], "xmit": {}}, placement="window"), [])


    # ── uniform placement (default; recipe-v3 2026-11-10, Anna TA-2) ──
    def test_candidates_uniform_whole_body(self):
        a = _ann([{"branch_pc": 1, "btb_forced_target_pc": 2, "mode": "mispredict_not_taken"},
                  {"branch_pc": 4, "btb_forced_target_pc": 5, "mode": "correctly_not_taken"}], 6)
        self.assertEqual(J.candidates(a, [0, 1, 2, 3, 4, 5, 6, 7]), [0, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(J.candidates(a, [0, 1, 2, 3, 4, 5, 6, 7], "uniform"), [0, 1, 2, 3, 4, 5, 6, 7])
        # no unresolved branch / no xmit: still placed (the window plays no role)
        b = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "correctly_not_taken"}], 3)
        self.assertEqual(J.candidates(b, [0, 1, 2, 3]), [0, 1, 2, 3])
        self.assertEqual(J.candidates({"annotations": [], "xmit": {}}, [0, 1]), [0, 1])
        self.assertEqual(J.candidates(a, []), [])
        with self.assertRaises(ValueError):
            J.candidates(a, [0], "shadow")

    def test_candidates_uniform_exclude_taken_forced_target(self):
        a = _ann([{"branch_pc": 0, "btb_forced_target_pc": 1, "mode": "mispredict_taken"},
                  {"branch_pc": 2, "btb_forced_target_pc": 3, "mode": "mispredict_not_taken"}], 3)
        self.assertEqual(J.candidates(a, [0, 1, 2, 3, 4]), [0, 2, 3, 4])

    def test_in_window_label(self):
        a = _ann([{"branch_pc": 1, "btb_forced_target_pc": 2, "mode": "mispredict_not_taken"}], 4)
        self.assertEqual([J.in_window(a, k) for k in range(6)], [False, False, True, True, True, False])
        self.assertFalse(J.in_window(_ann([], 4), 2))

    def test_asm_pcs_from_markers(self):
        for case, n in (("stt_taken", 6), ("fv2_otb_twobarrier", None)):
            s = next((FIX / case).glob("inst-*.s"))
            pcs = J.asm_pcs(s.read_text(), s.stem)
            self.assertEqual(pcs, list(range(len(pcs))), case)       # contiguous 0..max
            if n:
                self.assertEqual(pcs, list(range(n)))
            # every marker is usable by marker_app_line
            lines = s.read_text().split("\n")
            self.assertTrue(all(J.marker_app_line(lines, s.stem, k)[1] is None for k in pcs), case)

    def test_uniform_position_is_uniform(self):
        cands = list(range(8))
        cnt = [0] * 8
        n = 16000
        for i in range(n):
            cnt[J.ordered_candidates(f"inst-{i:06d}", 20261109, cands)[0]] += 1
        sd = (n * (1 / 8) * (7 / 8)) ** 0.5
        self.assertTrue(all(abs(c - n / 8) < 4 * sd for c in cnt), cnt)

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

    def test_map_instrs_jump_onto_inserted_jmp(self):
        # a jmp_direct `jmp .Ltmp1` whose label sits right before pc k's block: after the insert it
        # lands on the inserted jmp (which falls through to pc k); allowed, only for that target
        base = 0x401000
        old = [(0x0, "jmp", "0x401002 <f+0x2>"), (0x2, "xorq", "%rcx, %rcx"), (0x5, "retq", "")]
        new = [(0x0, "jmp", "0x401002 <f+0x2>"), (0x2, "jmp", "0x401004 <f+0x4>"),
               (0x4, "xorq", "%rcx, %rcx"), (0x7, "retq", "")]
        self.assertEqual(J.map_instrs(old, new, 1, base, base), {0x0: 0x0, 0x2: 0x4, 0x5: 0x7})
        old2 = [(0x0, "jmp", "0x401005 <f+0x5>"), (0x2, "xorq", "%rcx, %rcx"), (0x5, "retq", "")]
        new2 = [(0x0, "jmp", "0x401002 <f+0x2>"), (0x2, "jmp", "0x401004 <f+0x4>"),
                (0x4, "xorq", "%rcx, %rcx"), (0x7, "retq", "")]
        self.assertIsNone(J.map_instrs(old2, new2, 1, base, base))   # it named another instruction


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


def _run_jmp(td: Path, src: Path, p: float, modes, extra=(), seed=20261109):
    dst = td / f"dst_p{p}_{'_'.join(extra) or 'default'}_{seed}"
    subprocess.run([sys.executable, str(S2 / "make_jmp_corpus.py"), "--repo-root", str(ROOT), "--src", str(src),
                    "--dst", str(dst), "--p", str(p), "--jobs", "1", "--seed", str(seed), "--modes", *modes, *extra],
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
            self.assertTrue((dst / "jmp_stems.tsv").read_text().startswith(
                "mode\tstem\tbefore_pc\tjmp_addr\tn_candidates\tplacement\tin_window\n"))
            prov = json.loads((dst / "provenance.json").read_text())
            self.assertEqual((prov["placement"], prov["for_reported_numbers"]), ("uniform", True))

    def test_window_flag_warns_and_records(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            src = _mini_corpus(td, [("stt_taken", "mispredict_taken")])
            dst = _run_jmp(td, src, 0.0, ["mispredict_taken"], ("--placement", "window"))
            prov = json.loads((dst / "provenance.json").read_text())
            self.assertEqual((prov["placement"], prov["for_reported_numbers"]), ("window", False))
            self.assertIn("NOT for reported numbers", (dst / "make_jmp_corpus.log").read_text())


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
            # a second seed draws other positions; over seeds every uniform pc can be chosen
            seen = set()
            for sd in range(1, 9):
                d2 = _run_jmp(td, src, 1.0, ["mispredict_taken"], (), seed=sd)
                a2 = json.loads(next((d2 / "mispredict_taken" / "ann").glob("*.ann.json")).read_text())
                seen.add(a2["jmp_insert"]["before_pc"])
            self.assertGreater(len(seen), 1)
            self.assertFalse(seen & {1})       # stt_taken: pc1 is the mispredict_taken BTB target
            for _, mode in cases:
                s = next((dst / mode / "asm").glob("*.s"))
                ann = json.loads((dst / mode / "ann" / f"{s.stem}.ann.json").read_text())
                ji = ann["jmp_insert"]
                self.assertIn(ji["before_pc"], J.candidates(ann, J.asm_pcs(s.read_text(), s.stem)))
                self.assertEqual(ji["placement"], "uniform")
                self.assertEqual(ji["in_window"], J.in_window(ann, ji["before_pc"]))
                # re-resolving the written .s reproduces the written annotation
                tmpl = dict(ann); tmpl.pop("jmp_insert")
                re_ann, dis, base, pcm = J.resolve_ann(s.read_text(), s.stem, tmpl)
                tmpl2 = dict(re_ann); self.assertEqual(tmpl2, tmpl)
                at = [d for d in dis if d[0] + base == ji["addr"]]
                self.assertEqual(at[0][1], "jmp")
                self.assertEqual(pcm[ji["before_pc"]] + base, ji["addr"] + 2)
                # the transmitter moved iff the jmp went before it
                if ji["before_pc"] <= ann["xmit"]["pc"]:
                    self.assertGreater(ann["xmit"]["addr"], ji["addr"])


if __name__ == "__main__":
    unittest.main()

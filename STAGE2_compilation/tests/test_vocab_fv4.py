#!/usr/bin/env python3
"""Tests for the three opt-in Stage-2 vocabulary options added 2026-11-11/12 (vocab-tests, 2026-11-12):
  (1) fanout_v2.vocab_rj           RMW `orq $0,<mem>` for loads whose outreg nothing reads; jmp filler
                                   (proposed/vocab_fv4_uniform.diff)
  (2) fv4 table                    instruction_tables/proposed/fv4_vocab.jsonc, branch_forms.uniform,
                                   fanout_v2.vocab_exclude_tags (proposed/abs_vocab_fv4.diff)
  (3) interleave_only              instruction_tables/proposed/interleave_only.jsonc, fanout_v2.interleave_only
                                   and interleave.interleave_only (proposed/interleave_only.diff)
Off = byte-identical to the pristine parsexml.py copy in proposed/pre_vocab_fv4_20261111/ (before all three).

Stops at .ll / .ann.json (no ELF linking). The .s checks need an x86-64-capable clang and are skipped without one.
Fixtures: tests/fixtures/vocab_xml/ (24 STT_6_u q9_a3c XMLs from build/ilv_vocab_20261112, 8 CleanupSpec_6 XMLs).
Run: python3 -m pytest STAGE2_compilation/tests
"""
import copy
import importlib.util
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
S2 = HERE.parent
ROOT = S2.parent
sys.path.insert(0, str(S2))
import parsexml as P            # noqa: E402
import batch_generate as BG     # noqa: E402

FIX = HERE / "fixtures" / "vocab_xml"
XMLS = sorted(FIX.glob("*.xml"))
MODES = ["mispredict_not_taken", "mispredict_taken"]
TBL = S2 / "instruction_tables"
FV2_TABLE = str(TBL / "proposed" / "fv2_vocab.jsonc")
FV4_TABLE = str(TBL / "proposed" / "fv4_vocab.jsonc")
ILV_TABLE = str(TBL / "proposed" / "interleave_only.jsonc")
PRISTINE = S2 / "proposed" / "pre_vocab_fv4_20261111" / "parsexml.py"
RUNCFG = ROOT / "runconfigs" / "overnight_20261111"
RMW = P.VOCAB_RJ_RMW["name"]
TAG = "spt_bwd_invertible"

CLANG = next((c for c in ("clang-15", "/opt/homebrew/opt/llvm/bin/clang", "clang") if shutil.which(c)), None)


def _jsonc(path):
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'//[^\n]*', '', t)
    return json.loads(t)


def _base_cfgs():
    """plain (default table), fv3 (the overnight Stage-2 recipe without any of the three keys), fv3 + chain."""
    fv4 = _jsonc(RUNCFG / "stage2_fv4.jsonc")
    chain = _jsonc(RUNCFG / "stage2_fv4i_chain.jsonc")
    fv2 = copy.deepcopy(fv4["fanout_v2"])
    fv2.pop("vocab_rj", None)
    fv3 = dict(tables=FV2_TABLE, fv2=fv2, fpr=fv4["fpr"], brcond=fv4["branch_cond"],
               reg_naming=fv4["reg_naming"], interleave=None)
    ilv = copy.deepcopy(chain["interleave"])
    ilv.pop("interleave_only", None)
    return {
        "plain": dict(tables=None, fv2=None, fpr=None, brcond=None, reg_naming=dict(BG.DEFAULT_REG_NAMING),
                      interleave=None),
        "fv3": fv3,
        "fv3_chain": dict(fv3, interleave=ilv),
    }


CFGS = _base_cfgs()


def _with(cfg, fv2=None, interleave=None, tables=None):
    c = copy.deepcopy(cfg)
    if fv2:
        c["fv2"] = dict(c["fv2"], **fv2)
    if interleave:
        c["interleave"] = dict(c["interleave"], **interleave)
    if tables:
        c["tables"] = tables
    return c


def _fns(mod, stash):
    def p2(*a, **k):
        r = mod.pass2_specify_instructions(*a, **k)
        stash["r2"] = r
        return r

    def p4(*a, **k):
        r = mod.pass4_ssa(*a, **k)
        stash["r4_pre"] = copy.deepcopy(r)
        stash["r4"] = r
        return r

    def p1(*a, **k):
        r = mod.pass1_specify_state_a(*a, **k)
        stash["r1"] = r
        return r

    return (mod.parse_alloy_xml, p1, p2, mod.pass2_5_specify_branches, mod.pass2_6_specify_stl,
            mod.pass_interleave, mod.pass3_assign_operands, p4, mod.pass5_emit_llvm, mod.emit_branch_annotations)


def gen(xml, mode, cfg, mod=P):
    """One test through batch_generate.run_pipeline -> (ll text, ann bytes, stash of pass results)."""
    mod.reload_tables(cfg["tables"])
    stash = {}
    with tempfile.TemporaryDirectory() as td:
        BG.run_pipeline(xml.read_text(encoding="utf-8"), xml.stem, Path(td), mode, _fns=_fns(mod, stash),
                        interleave_cfg=cfg["interleave"], fpr_cfg=cfg["fpr"], reg_naming_cfg=cfg["reg_naming"],
                        fv2_cfg=cfg["fv2"], brcond_cfg=cfg["brcond"])
        stash["ll"] = (Path(td) / f"{xml.stem}.ll").read_text()
        stash["ann_bytes"] = (Path(td) / f"{xml.stem}.ann.json").read_bytes()
    stash["ann"] = json.loads(stash["ann_bytes"])
    return stash


def _load_pristine():
    td = Path(tempfile.mkdtemp(prefix="pristine_parsexml_"))
    shutil.copy(PRISTINE, td / "parsexml.py")
    (td / "instruction_tables").symlink_to(TBL)
    spec = importlib.util.spec_from_file_location("parsexml_pristine_20261111", td / "parsexml.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m   # dataclass needs the module registered
    spec.loader.exec_module(m)
    return m, td


def _slot(rec, name):
    for sl in rec["slots"].values():
        for s in sl:
            if s["slot"] == name:
                return s
    return None


def _specified(rec):
    return {s["slot"] for sl in rec["slots"].values() for s in sl if s.get("specified")}


def _s_text(ll, td):
    lp = Path(td) / "t.ll"
    lp.write_text(ll)
    r = subprocess.run([CLANG, "--target=x86_64-unknown-linux-gnu", "-O2", "-S", str(lp), "-o", str(lp.with_suffix(".s"))],
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError("clang -S failed: " + r.stderr[:2000])
    return lp.with_suffix(".s").read_text()


def _after_marker(s_text, stem, pc):
    safe = stem.replace("-", "_").replace(".", "_")
    lines = [l.strip() for l in s_text.splitlines()]
    k = lines.index(f"__litmus_{safe}_pc{pc}:")
    return next(l for l in lines[k + 1:] if l and not l.startswith((".globl", "__litmus_", "#")))


def tearDownModule():
    P.reload_tables(None)


# ---------------------------------------------------------------------------------------------------------------
# (a) each option off -> byte-identical to the pristine parsexml.py
# ---------------------------------------------------------------------------------------------------------------
class OffIsByteIdentical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.td = _load_pristine()

    @classmethod
    def tearDownClass(cls):
        cls.old.reload_tables(None)
        shutil.rmtree(cls.td, ignore_errors=True)

    def _same(self, cfg, ref_cfg=None):
        for mode in MODES:
            for x in XMLS:
                new = gen(x, mode, cfg)
                old = gen(x, mode, ref_cfg or cfg, mod=self.old)
                self.assertEqual(new["ll"], old["ll"], f"{x.name} {mode}: .ll differs")
                self.assertEqual(new["ann_bytes"], old["ann_bytes"], f"{x.name} {mode}: .ann.json differs")

    def test_keys_absent(self):
        for name, cfg in CFGS.items():
            with self.subTest(cfg=name):
                self._same(cfg)

    def test_keys_explicitly_disabled(self):
        # interleave_only {"enabled": false} and vocab_exclude_tags [] take the absent path
        off = {"interleave_only": {"enabled": False, "table": ILV_TABLE}, "vocab_exclude_tags": []}
        cfg = _with(CFGS["fv3_chain"], fv2=off, interleave={"interleave_only": {"enabled": False}})
        self._same(cfg, ref_cfg=CFGS["fv3_chain"])


# ---------------------------------------------------------------------------------------------------------------
# (b) fanout_v2.vocab_rj
# ---------------------------------------------------------------------------------------------------------------
RJ = {"vocab_rj": {"rmw": True, "jmp": True}}


class VocabRJ(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _with(CFGS["fv3"], fv2=RJ)
        cls.runs = [(x, m, gen(x, m, cls.cfg)) for m in MODES for x in XMLS]
        P.reload_tables(FV2_TABLE)

    def test_rmw_present_in_batch(self):
        self.assertGreater(sum(len(s["ann"]["vocab_rj"]["rmw_pcs"]) for _, _, s in self.runs), 5)

    def test_rmw_only_on_eligible_loads(self):
        for x, m, s in self.runs:
            rf_src = {t[0] for t in P.parse_alloy_xml(x.read_text()).fields.get("rf", []) if t}
            p1 = {r["pc"]: r for r in s["r1"]["instructions"]}
            for r in s["r2"]["instructions"]:
                cands = r.get("candidates") or []
                if r["kind"] != "ld":
                    self.assertNotIn(RMW, cands, f"{x.name} pc{r['pc']}: RMW offered for kind {r['kind']}")
                    continue
                o = _slot(r, "outreg")
                consumed = bool(o and o.get("operand_atom") in rf_src)
                self.assertEqual(consumed, p1[r["pc"]]["outreg_consumed"], f"{x.name} pc{r['pc']}")
                fits = _specified(r) - {"outreg"} <= P.VOCAB_RJ_RMW["uses"]
                self.assertEqual(RMW in cands, (not consumed) and fits, f"{x.name} pc{r['pc']} {cands}")
            for r in s["r4"]["instructions"]:
                if r.get("concrete_instruction") != RMW:
                    continue
                self.assertEqual(r["kind"], "ld")
                self.assertFalse(r["outreg_consumed"])
                # no later concrete read of the value the load would have written
                o = _slot(r, "outreg")
                if o and o.get("ssa_name"):
                    self.assertNotRegex(s["ll"], r"%" + re.escape(o["ssa_name"]) + r"\b",
                                        f"{x.name} {m} pc{r['pc']}: RMW outreg SSA value is referenced")

    def test_rmw_pcs_ann_and_marker(self):
        for x, m, s in self.runs:
            pcs = [r["pc"] for r in s["r4"]["instructions"] if r.get("concrete_instruction") == RMW]
            self.assertEqual(sorted(pcs), sorted(s["ann"]["vocab_rj"]["rmw_pcs"]), x.name)
            safe = x.stem.replace("-", "_").replace(".", "_")
            for pc in pcs:
                line = next(l for l in s["ll"].splitlines() if f"__litmus_{safe}_pc{pc}:" in l)
                self.assertRegex(line, r"__litmus_\w+_pc%d:\\0Aorq \$\$0, " % pc, f"{x.name} {m} pc{pc}")

    @unittest.skipUnless(CLANG, "needs an x86-64 clang for .s")
    def test_rmw_address_identical_to_plain_load(self):
        n = 0
        with tempfile.TemporaryDirectory() as td:
            for x, m, s in self.runs:
                rmw = [r["pc"] for r in s["r4_pre"]["instructions"] if r.get("concrete_instruction") == RMW]
                if not rmw:
                    continue
                plain = copy.deepcopy(s["r4_pre"])
                for r in plain["instructions"]:
                    if r["pc"] in rmw:
                        r["concrete_instruction"] = "load"
                fv2 = self.cfg["fv2"]
                ll_plain = P.pass5_emit_llvm(plain, func_name=x.stem, fpr_cfg=self.cfg["fpr"], fv2_cfg=fv2,
                                             brcond_cfg=self.cfg["brcond"])
                # The re-emitted plain load has no outreg SSA name (pass 4 gave the RMW none), so pass 5 takes
                # its rarely-used no-output branch, whose probe-addressed form writes `%%rax` (invalid in LLVM
                # inline asm; pre-existing, same text in the pristine copy). Normalize it to compare addresses.
                ll_plain = ll_plain.replace(", %%rax\"", ", %rax\"")
                s_rmw, s_plain = _s_text(s["ll"], td), _s_text(ll_plain, td)
                for pc in rmw:
                    a = re.match(r"orq\s+\$0,\s*(\S+)$", _after_marker(s_rmw, x.stem, pc))
                    b = re.match(r"movq\s+(-?\d*\([^)]*\)),\s*%\w+$", _after_marker(s_plain, x.stem, pc))
                    self.assertTrue(a and b, (x.name, m, pc, _after_marker(s_rmw, x.stem, pc),
                                              _after_marker(s_plain, x.stem, pc)))
                    self.assertEqual(a.group(1), b.group(1), f"{x.name} {m} pc{pc}")
                    n += 1
        self.assertGreater(n, 5)

    def test_jmp_filler_is_direct_jmp_to_next(self):
        jf = 'call void asm sideeffect "jmp .Lsimspect_jf${:uid}\\0A.Lsimspect_jf${:uid}:", ""()'
        total = 0
        for x, m, s in self.runs:
            nf = len(s["ann"]["vocab_rj"]["jmp_filler_before_pcs"])
            self.assertEqual(s["ll"].count(jf), nf, f"{x.name} {m}")
            self.assertEqual(nf, sum(f["op"] == "jmp" for f in s["ann"]["fanout_v2"]["fillers"]))
            self.assertEqual(s["ll"].count("Lsimspect_jf"), 2 * nf)
            total += nf
        self.assertGreater(total, 0)

    @unittest.skipUnless(CLANG, "needs an x86-64 clang for .s")
    def test_jmp_filler_asm_targets_next_line(self):
        n = 0
        with tempfile.TemporaryDirectory() as td:
            for x, m, s in self.runs:
                if not s["ann"]["vocab_rj"]["jmp_filler_before_pcs"]:
                    continue
                lines = [l.strip() for l in _s_text(s["ll"], td).splitlines()]
                for i, l in enumerate(lines):
                    mm = re.match(r"jmp\s+(\.Lsimspect_jf\S+)$", l)
                    if mm:
                        n += 1
                        self.assertEqual(lines[i + 1], mm.group(1) + ":", f"{x.name} {m}")
        self.assertGreater(n, 0)

    def test_rmw_draw_uniform(self):
        # pass 2 alone over 200 seeds: each eligible load picks RMW with p = 1/|valid candidates|
        r1s = [P.pass1_specify_state_a(P.parse_alloy_xml(x.read_text()), write_out=False) for x in XMLS]
        got, exp, var = 0, 0.0, 0.0
        for seed in range(200):
            random.seed(seed)
            for r1 in r1s:
                for r in P.pass2_specify_instructions(r1, vocab_rj={"rmw": True})["instructions"]:
                    c = r["candidates"]
                    if RMW in c:
                        p = 1.0 / len(c)
                        exp += p; var += p * (1 - p); got += r["concrete_instruction"] == RMW
        self.assertGreater(exp, 200)
        self.assertLess(abs(got - exp), 5 * var ** 0.5 + 2, (got, exp))

    def test_jmp_filler_draw_uniform(self):
        # vary func_name (the filler rng seed): jmp should be 1 of the 7 filler ops
        ops = Counter()
        for x, m, s in self.runs[:24]:
            for k in range(15):
                r4 = copy.deepcopy(s["r4_pre"])
                P.pass5_emit_llvm(r4, func_name=f"{x.stem}_s{k}", fpr_cfg=self.cfg["fpr"], fv2_cfg=self.cfg["fv2"],
                                  brcond_cfg=self.cfg["brcond"])
                ops.update(f["op"] for f in r4["fv2"]["fillers"])
        n = sum(ops.values())
        self.assertEqual(set(ops), set(self.cfg["fv2"]["fillers"]["ops"]) | {"jmp"})
        self.assertGreater(n, 300)
        self.assertLess(abs(ops["jmp"] / n - 1 / 7), 0.04, ops)


# ---------------------------------------------------------------------------------------------------------------
# (c) fv4 table
# ---------------------------------------------------------------------------------------------------------------
class Fv4Table(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = _jsonc(FV4_TABLE)
        cls.byname = {(cat, c["name"]): c for cat, v in cls.table["instructions"].items() for c in v}
        cls.tagged = {c["name"] for v in cls.table["instructions"].values() for c in v if TAG in c.get("tags", [])}
        cls.cfg = _with(CFGS["fv3"], fv2=RJ, tables=FV4_TABLE)
        cls.runs = [(x, m, gen(x, m, cls.cfg)) for m in MODES for x in XMLS]
        P.reload_tables(FV4_TABLE)
        cls.r1s = [P.pass1_specify_state_a(P.parse_alloy_xml(x.read_text()), write_out=False) for x in XMLS]

    def test_table_has_tagged_and_branch_uniform(self):
        self.assertTrue(self.tagged)
        self.assertEqual(self.table["branch_forms"]["uniform"], ["test", "cmp", "jmp"])

    def _check_uses(self, r2):
        for r in r2["instructions"]:
            cat = P._KIND_TO_CATEGORY.get(r["kind"], r["kind"])
            if cat == "br":
                continue   # pass 2.5 forces the branch concrete
            spec = _specified(r)
            form = r.get("vocab_form") or r["concrete_instruction"]
            for c in r["candidates"]:
                uses = P.VOCAB_RJ_RMW["uses"] | {"outreg"} if c == RMW else set(self.byname[(cat, c)]["uses"])
                self.assertLessEqual(spec, uses, (r["pc"], c))
            self.assertIn(form, r["candidates"])
            if r.get("vocab_form"):
                self.assertEqual(r["concrete_instruction"], self.byname[(cat, form)]["base"])

    def test_every_form_respects_uses(self):
        for seed in range(60):
            random.seed(seed)
            for r1 in self.r1s:
                self._check_uses(P.pass2_specify_instructions(r1, vocab_rj={"rmw": True}))
                self._check_uses(P.pass2_specify_instructions(r1, vocab_rj={"rmw": True}, exclude_tags=[TAG]))

    def test_vocab_forms_in_ann_match_records(self):
        n = 0
        for x, m, s in self.runs:
            vf = s["ann"].get("vocab_forms", {})
            want = {str(r["pc"]): r["vocab_form"] for r in s["r4"]["instructions"] if r.get("vocab_form")}
            self.assertEqual(vf, want, f"{x.name} {m}")
            n += len(vf)
        self.assertGreater(n, 0)

    def test_branch_uniform_jmp_only_on_safe_branches(self):
        n_jmp = n_br = 0
        for x, m, s in self.runs:
            bf = s["ann"]["branch_forms"]
            self.assertEqual(bf["uniform"], ["test", "cmp", "jmp"])
            recs = {r["pc"]: r for r in s["r4"]["instructions"]}
            for r in s["r4"]["instructions"]:
                if r.get("branch_annotations"):
                    n_br += 1
            for pc in bf["jmp_direct_pcs"]:
                r = recs[pc]
                mode = r["branch_annotations"]["mode"]
                self.assertEqual(mode, "correctly_not_taken", f"{x.name} {m} pc{pc}")
                self.assertTrue(r.get("resolved"), f"{x.name} {m} pc{pc}: jmp on an unresolved branch")
                self.assertFalse(r.get("xm"), f"{x.name} {m} pc{pc}: jmp on the transmitter")
                self.assertIn(r["concrete_instruction"], ("br_cond", "br_uncond"))
                n_jmp += 1
            unres = [a["branch_pc"] for a in s["ann"]["annotations"] if a.get("mode", "").startswith("mispredict")]
            self.assertFalse(set(unres) & set(bf["jmp_direct_pcs"]), x.name)
            self.assertFalse(set(bf["br_cmp_pcs"]) & set(bf["jmp_direct_pcs"]), x.name)
        self.assertGreater(n_br, 0)
        self.assertGreater(n_jmp, 0)

    def test_exclude_tags_removes_exactly_tagged(self):
        for r1 in self.r1s:
            random.seed(1)
            full = P.pass2_specify_instructions(r1, vocab_rj={"rmw": True})["instructions"]
            random.seed(1)
            excl = P.pass2_specify_instructions(r1, vocab_rj={"rmw": True}, exclude_tags=[TAG])["instructions"]
            for a, b in zip(full, excl):
                kept = [c for c in a["candidates"] if c not in self.tagged]
                if kept:
                    self.assertEqual(b["candidates"], kept, a["pc"])
                self.assertFalse(set(b["candidates"]) & self.tagged)
                self.assertNotIn(b.get("vocab_form") or b["concrete_instruction"], self.tagged)
        # whole-table view: what exclusion leaves = table minus tagged, nothing else
        for cat, v in self.table["instructions"].items():
            left = [c["name"] for c in v if TAG not in c.get("tags", [])]
            self.assertEqual(left, [c["name"] for c in v if c["name"] not in self.tagged], cat)

    def test_exclude_tags_through_run_pipeline(self):
        cfg = _with(self.cfg, fv2={"vocab_exclude_tags": [TAG]})
        for x in XMLS[:16]:
            s = gen(x, MODES[0], cfg)
            for r in s["r2"]["instructions"]:
                self.assertFalse(set(r["candidates"]) & self.tagged, x.name)


# ---------------------------------------------------------------------------------------------------------------
# (d) interleave_only
# ---------------------------------------------------------------------------------------------------------------
ILV_ON = {"enabled": True, "table": ILV_TABLE}


class InterleaveOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tab = _jsonc(ILV_TABLE)
        cls.entries = {e["name"]: e for e in tab["entries"]
                       if e.get("status", "ok") == "ok" and int(e.get("weight", 1)) == 1}
        cls.chain_names = {n for n, e in cls.entries.items()
                           if e.get("form", "rr") == "rr" and P._ilv_refs(e["asm"], 1)}
        cls.cfg = _with(CFGS["fv3_chain"], fv2=dict(RJ, interleave_only=ILV_ON),
                        interleave={"interleave_only": ILV_ON})
        cls.runs = [(x, m, gen(x, m, cls.cfg)) for m in MODES for x in XMLS]

    def test_fillers_drawn_from_category_and_outputs_never_read(self):
        n = 0
        for x, m, s in self.runs:
            fv = s["ann"]["fanout_v2"]
            dead = set(fv["dead_registers"])
            used = {sl.get("assigned") for r in s["r4"]["instructions"] for v in r["slots"].values() for sl in v}
            for f in fv["fillers"]:
                self.assertIn(f["op"], self.entries, x.name)
                if "dst" in f:
                    n += 1
                    self.assertIn(f["dst"], dead, f"{x.name} {m}: filler writes a non-dead register")
                    self.assertNotIn(f["dst"], used, f"{x.name} {m}: filler dst {f['dst']} used by the program")
            for k in re.findall(r"%(__fill_\d+) =", s["ll"]):
                self.assertEqual(len(re.findall(r"%" + k + r"\b", s["ll"])), 1, f"{x.name} {m}: %{k} is read")
        self.assertGreater(n, 0)

    def test_chain_steps_only_from_category(self):
        n = 0
        for x, m, s in self.runs:
            for r in s["r4"]["instructions"]:
                if not r.get("synthetic") or r.get("kind") != "other_n":
                    continue
                c = r.get("concrete_instruction") or ""
                if c == "nop":
                    continue   # pass 2.5's synthetic NOP after an xm branch, not a chain step
                self.assertTrue(c.startswith(P.ILV_PREFIX), f"{x.name} {m} pc{r['pc']}: chain step {c!r}")
                self.assertIn(c[len(P.ILV_PREFIX):], self.chain_names)
                self.assertIn(self.entries[c[len(P.ILV_PREFIX):]]["asm"], s["ll"])
                n += 1
        self.assertGreater(n, 0)

    def test_exclude_tags(self):
        icfg = dict(ILV_ON, exclude_tags=[TAG])
        sel = P._ilv_select(icfg)
        self.assertEqual(set(sel), {n for n, e in self.entries.items() if not e.get(TAG)})
        cfg = _with(CFGS["fv3_chain"], fv2=dict(RJ, interleave_only=icfg), interleave={"interleave_only": icfg})
        seen = Counter()
        for x in XMLS:
            for m in MODES:
                s = gen(x, m, cfg)
                for f in s["ann"]["fanout_v2"]["fillers"]:
                    seen[f["op"]] += 1
                    self.assertFalse(self.entries[f["op"]].get(TAG), f["op"])
                for r in s["r4"]["instructions"]:
                    c = r.get("concrete_instruction") or ""
                    if c.startswith(P.ILV_PREFIX):
                        seen[c] += 1
                        self.assertFalse(self.entries[c[len(P.ILV_PREFIX):]].get(TAG), c)
        self.assertTrue(any(k.startswith(P.ILV_PREFIX) for k in seen))

    def test_exclude_everything_raises(self):
        # every entry has a "class": excluding it leaves nothing, which must fail loudly, not fall back
        icfg = dict(ILV_ON, exclude_tags=["class"])
        cfg = _with(CFGS["fv3_chain"], interleave={"interleave_only": icfg})
        with self.assertRaises(ValueError):
            gen(XMLS[0], MODES[0], cfg)
        cfg = _with(CFGS["fv3"], fv2={"interleave_only": icfg})
        with self.assertRaises(ValueError):
            gen(XMLS[0], MODES[0], cfg)

    def test_deterministic(self):
        for x in XMLS[:10]:
            for m in MODES:
                a, b = gen(x, m, self.cfg), gen(x, m, self.cfg)
                self.assertEqual(a["ll"], b["ll"])
                self.assertEqual(a["ann_bytes"], b["ann_bytes"])


if __name__ == "__main__":
    unittest.main()

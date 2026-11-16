#!/usr/bin/env python3
"""build_anon.py -- build the anonymous double-blind artifact at ~/trippel/simspect-anon (agent anonrepo, 2026-11-16).

Copies the live pipeline files from this repo (read-only), strips every comment (strip.py), applies the exact
string replacements below (paths parameterized / identity-free help text), converts JSONC to JSON, and writes the
authored Makefile + simspect.py from scripts/anon_artifact/authored/. Re-runnable: wipes and rebuilds everything
except <OUT>/gem5 and <OUT>/STAGE1_alloy/models/speclfb (built by separate steps).
Every replacement is recorded in <scratch>/build_record.json for the manifest and verify_anon.py.

Usage: python3 scripts/anon_artifact/build_anon.py [--out ~/trippel/simspect-anon]
"""
import argparse, json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import strip  # noqa: E402
sys.path.insert(0, str(HERE / "prune"))
import prune as _prune  # noqa: E402
import spec_parsexml, spec_stage2_sharded, spec_stream_fp, spec_misc  # noqa: E402
import labels as _labels  # noqa: E402
BUG_RENAME = {"STAGE3_gem5/bugs/r_sa13_recon_sse_load.py": "STAGE3_gem5/bugs/recon_sse_load_producer.py"}
IDENT_RENAME = [(r"\bRSA13\b", "SSE"), (r"\bRSA8\b", "OLDEST"), (r"\bA2\b", "STLF"), (r"\br_sa13_recon_sse_load\b", "recon_sse_load_producer"),
                (r"\brsa8_signature\b", "oldest_taint_signature"), (r"\brsa8_evidence\b", "evidence")]

CLASSIFY_V2 = True
PRUNE = {
    "STAGE2_compilation/parsexml.py": spec_parsexml.OPS,
    "STAGE1_alloy/gen/stage2_sharded.py": spec_stage2_sharded.OPS,
    "STAGE1_alloy/gen/stream_fp.py": spec_stream_fp.OPS,
    "pipeline.py": spec_misc.PIPELINE,
    "STAGE3_gem5/gem5_common.py": spec_misc.GEM5_COMMON,
    "STAGE3_gem5/timing/timing_driver.py": spec_misc.TIMING_DRIVER,
    "STAGE3_gem5/timing/firstdet_stream.py": spec_misc.FIRSTDET_STREAM,
    "STAGE1_alloy/gen/stage15lp.py": spec_misc.STAGE15LP,
    "STAGE1_alloy/gen/make_s15_model.py": spec_misc.MAKE_S15,
    "STAGE3_gem5/timing/firstdet_report.py": spec_misc.FIRSTDET_REPORT,
    "STAGE3_gem5/cache_setup.py": spec_misc.CACHE_SETUP,
    "STAGE3_gem5/bugs/classify.py": spec_misc.CLASSIFY + (spec_misc.CLASSIFY_EXTRA if CLASSIFY_V2 else []),
    "twostage_lp.py": spec_misc.TWOSTAGE,
    "STAGE1_alloy/gen/restream.py": spec_misc.RESTREAM,
    "simspect_paths.py": spec_misc.SIMSPECT_PATHS,
    "alloy_solver_order.py": spec_misc.ALLOY_SOLVER_ORDER,
    "STAGE1_alloy/stage_seed.py": spec_misc.STAGE_SEED,
    "STAGE1_alloy/gen/partition_stage1.py": spec_misc.PARTITION,
    "STAGE1_alloy/gen/run_stage1.py": spec_misc.RUN_STAGE1,
    "STAGE3_gem5/bugs/_dg3.py": spec_misc.DG3,
    "amulet/make_benchmark_t5.py": spec_misc.MAKE_BENCH,
    "STAGE2_compilation/find_duplicates.py": [("del_def", "main"), ("drop_if", None, "__name__ == '__main__'", "else", 1)],
}
REMOVED = {"STAGE3_gem5/bugs/__init__.py", "STAGE2_compilation/batch_generate.py", "STAGE2_compilation/make_rmw_corpus.py", "amulet/cs_nonexclusive_t5.py",
           "STAGE3_gem5/bugs/r_sa9_recon_twin_untaint.py", "STAGE3_gem5/bugs/recon_reveal_artifact.py",
           "STAGE3_gem5/bugs/uv6_vp_squash_race.py"} | ({"STAGE3_gem5/bugs/disq_hpad_text_end.py", "STAGE3_gem5/bugs/disq_setup_block.py",
                                                       "STAGE3_gem5/bugs/disq_speclfb_nonload.py"} if CLASSIFY_V2 else set())

LP = "STAGE1_alloy/models/proposed/ultimate/loosepin"
PT = "STAGE1_alloy/models/proposed_twophase"

# (source, destination, [(old, new, expected_count)], why)
PY = [
    ("twostage_lp.py", "twostage_lp.py", [
        ('ROOT / "STAGE1_alloy/models/proposed/ultimate/loosepin"', 'ROOT / "STAGE1_alloy/gen"', 1),
        ('ROOT / "STAGE1_alloy/models/proposed_twophase"', 'ROOT / "STAGE1_alloy/gen"', 1),
    ], "generate: two-stage loose-pin driver (make corpus)"),
    ("pipeline.py", "pipeline.py", [
    ], "engine: config loading, llvm/asm phases, gem5 env bridge, checker dispatch"),
    ("testrun.py", "testrun.py", [
    ], "run: gem5 consumer for the STT/ReCon eval rows (make eval)"),
    ("jobs_registry.py", "jobs_registry.py", [], "imported by testrun.py"),
    ("simspect_paths.py", "simspect_paths.py", [
        ('"instructions.jsonc"', '"instructions.json"', 1),
    ], "imported by pipeline.py / testrun.py / jobs_registry.py"),
    ("alloy_solver_order.py", "alloy_solver_order.py", [], "generate: seeded random Alloy enumeration + fingerprint dedup (stage15lp.py, pipeline.py)"),
    ("STAGE1_alloy/stage_seed.py", "STAGE1_alloy/stage_seed.py", [], "generate: core parsing + pin predicate (stage15lp.py, make_s15_model.py, audit_core_dups.py)"),
    (f"{PT}/partition_stage1.py", "STAGE1_alloy/gen/partition_stage1.py", [], "generate: Stage 1 partitions (twostage_lp.py)"),
    (f"{PT}/launch_stage1.py", "STAGE1_alloy/gen/launch_stage1.py", [
        ('"STAGE1_alloy/models/proposed_twophase/run_stage1.py"', '"STAGE1_alloy/gen/run_stage1.py"', 1),
    ], "generate: Stage 1 launcher (twostage_lp.py)"),
    (f"{PT}/run_stage1.py", "STAGE1_alloy/gen/run_stage1.py", [
        ("STAGE1 = HERE.parent.parent", "STAGE1 = HERE.parent", 1),
    ], "generate: one Stage 1 partition (launch_stage1.py)"),
    (f"{PT}/stage2_sharded.py", "STAGE1_alloy/gen/stage2_sharded.py", [], "concretize: sharded Stage 2 (stream_fp.py)"),
    (f"{PT}/dedup_audit/audit_core_dups.py", "STAGE1_alloy/gen/audit_core_dups.py", [], "generate: core dedup fingerprint (stage15lp.py)"),
    (f"{PT}/dedup_audit/check_bound_consistency.py", "STAGE1_alloy/gen/check_bound_consistency.py", [], "generate: bound lint run by stage15lp.py before Stage 1.5"),
    (f"{PT}/stage15_bound/make_s15_model.py", "STAGE1_alloy/gen/make_s15_model.py", [
        ("STAGE1 = HERE.parents[2]", "STAGE1 = HERE.parent", 1),
        ('f"// [stage15-bound DRAFT 2026-11-08] generated by proposed_twophase/stage15_bound/make_s15_model.py"',
         'f"// generated by make_s15_model.py"', 1),
    ], "generate: path-style core pin (stage15lp.py uses pin_pred)"),
    (f"{LP}/stage15lp.py", "STAGE1_alloy/gen/stage15lp.py", [
        ('s1 / "models/proposed_twophase/dedup_audit"', 's1 / "gen"', 1),
        ('s1 / "models/proposed_twophase/stage15_bound"', 's1 / "gen"', 1),
        ('"STAGE1_alloy/models/proposed_twophase/dedup_audit/check_bound_consistency.py"', '"STAGE1_alloy/gen/check_bound_consistency.py"', 1),
        ('help="nonmin 2026-11-10: drop', 'help="drop', 1),
    ], "generate: Stage 1.5 core-pinned loose-pin enumeration (twostage_lp.py)"),
    (f"{LP}/stream_fp.py", "STAGE1_alloy/gen/stream_fp.py", [
        ('B = Path("/tests/simspect_alloy_20261108"); TS = B / "testsets_twostage"; WS = B / "loosepin_regen"',
         'B = Path("work"); TS = B / "testsets"; WS = B / "ws"', 1),
        ('"fv4 (overnight 2026-11-11: stage2_fv4 = stage2_fv3 + fanout_v2.vocab_rj; RMW and jmp drawn uniformly in Stage 2, no post-passes)"',
         '"A (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2, no post-passes)"', 1),
        ('"v3 (recipe-v3 2026-11-10: fanout OTB off, jmp placement uniform, RMW --select eligible)"',
         '"post-pass recipe (RMW and jmp post-passes)"', 1),
        ('"runconfigs/regen_lp_20261110/stage2_fv3.jsonc"', '"runconfigs/stage2_A.json"', 1),
        ('"runconfigs/overnight_20261111/stage2_fv4.jsonc"', '"runconfigs/stage2_A.json"', 1),
        ('"stage2_fv4 (stage2_fv3 + fanout_v2.vocab_rj rmw+jmp, uniform draws) only, no post-passes"',
         '"stage2_A (fanout_v2.vocab_rj rmw+jmp, uniform draws) only, no post-passes"', 1),
        ('"stage2_fv3 (OTB off) -> make_rmw_corpus --select eligible p0.5 seed 20261109 per batch -> make_jmp_corpus p0.5 seed 20261109 uniform"',
         '"post-passes make_rmw_corpus + make_jmp_corpus"', 1),
        ('help="testset root (default /tests/simspect_alloy_20261108/testsets_twostage)"', 'help="testset root (default work/testsets)"', 1),
        ('help="work dir holding logs/ and stream/ (default .../loosepin_regen)"', 'help="work dir holding logs/ and stream/ (default work/ws)"', 1),
        ('help="path of the UNCHANGED uv5_timing_scan.py: classify every stem D / C / other (MANIFEST column uv5_class), "',
         'help="optional external stem classifier script: classify every stem D / C / other (MANIFEST column uv5_class), "', 1),
        ('default="264adea+uncommitted"', 'default="artifact"', 1),
        ('help="fv4 (overnight-exp 2026-11-11): RMW and jmp come from Stage 2 itself "', 'help="RMW and jmp come from Stage 2 itself "', 1),
        ('help="comma-separated Stage-2 modes (stl-prep 2026-11-12, e.g. stl_bypass); default "',
         'help="comma-separated Stage-2 modes (e.g. stl_bypass); default "', 1),
        ('[sys.executable, "STAGE1_alloy/models/proposed_twophase/stage2_sharded.py"', '[sys.executable, "STAGE1_alloy/gen/stage2_sharded.py"', 1),
        ('f"READY {now()} regen-lp: {a.final_name}', 'f"READY {now()}: {a.final_name}', 1),
        ('(f"Stage 2: {cfg.name} (stage2_fv4 = stage2_fv3 + fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2), no post-passes; "',
         '(f"Stage 2: {cfg.name} (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2), no post-passes; "', 1),
        ('f"Stage 2: {cfg.name} (stage2_fv3 = E3_STT_6_fv2fp options with fanout OTB off) -> per batch make_rmw_corpus --select eligible "',
         'f"Stage 2: {cfg.name} -> per batch make_rmw_corpus --select eligible "', 1),
        ('(f"UV5 SCAN: every stem is published; MANIFEST.tsv column uv5_class = D / C / other (unchanged uv5_timing_scan.py, not_taken). "',
         '(f"STEM SCAN: every stem is published; MANIFEST.tsv column uv5_class = D / C / other. "', 1),
    ], "concretize: streaming merge -> Stage 2 -> publish (twostage_lp.py)"),
    ("scripts/bigcorpus_20261115/nov10_stream.py", "STAGE1_alloy/gen/restream.py", [
        ('ROOT / "STAGE1_alloy/models/proposed/ultimate/loosepin"', 'ROOT / "STAGE1_alloy/gen"', 1),
        ('ws / "nov10_stream.log"', 'ws / "restream.log"', 1),
        ('ws / "stage2_final_A_nov10_stream.jsonc"', 'ws / "stage2_A_restream.json"', 1),
        ('f"// nov10_stream.py {now()}: copy of {a.cfg} with only paths.testset_dir and gem5.jobs changed\\n"',
         'f"// restream.py {now()}: copy of {a.cfg} with only paths.testset_dir and gem5.jobs changed\\n"', 1),
        ('f"READY {now()} nov10_stream: {a.final} = the 2026-11-10 Footprint_6_u_core_lpP_fv3 programs ({len(stems)} stems from {src}) "',
         'f"READY {now()} restream: {a.final} = re-concretized programs ({len(stems)} stems from {src}) "', 1),
    ], "concretize: re-concretize an existing Alloy program set in seed order (make rounds: renamed stems _c1.._c3)"),
    ("scripts/bigcorpus_20261115/dedup_vs_main.py", "STAGE1_alloy/gen/dedup_vs_main.py", [],
     "generate: fingerprint dedup of the extra corpus against the main corpus (make pool)"),
    ("STAGE2_compilation/parsexml.py", "STAGE2_compilation/parsexml.py", [
        ('Path(__file__).parent / "instruction_tables" / "instructions.jsonc"', 'Path(__file__).parent / "instruction_tables" / "instructions.json"', 2),
        ('ILV_TABLE_DEFAULT = "STAGE2_compilation/instruction_tables/proposed/interleave_only.jsonc"',
         'ILV_TABLE_DEFAULT = "STAGE2_compilation/instruction_tables/interleave_only.json"', 1),
    ], "concretize: XML -> LLVM IR (batch_generate.py; fingerprint in alloy_solver_order.py)"),
    ("STAGE2_compilation/batch_generate.py", "STAGE2_compilation/batch_generate.py", [
        ("byte-identical to pre-2026-11-08 output.", "byte-identical to the older output.", 1),
    ], "concretize: per-folder Stage 2 driver (stage2_sharded.py, pipeline.py llvm)"),
    ("STAGE2_compilation/compile_annotate.py", "STAGE2_compilation/compile_annotate.py", [], "concretize: .ll -> .s + resolved .ann.json (pipeline.py asm)"),
    ("STAGE2_compilation/make_rmw_corpus.py", "STAGE2_compilation/make_rmw_corpus.py", [
        ('help="eligible (default, 2026-11-09): gate every stem', 'help="eligible (default): gate every stem', 1),
    ], "library: cache_setup.py imports addr_fields/key_paths (not run as a post-pass)"),
    ("STAGE2_compilation/find_duplicates.py", "STAGE2_compilation/find_duplicates.py", [], "generate: canonical fingerprint (alloy_solver_order.py)"),
    ("STAGE3_gem5/gem5_common.py", "STAGE3_gem5/gem5_common.py", [
        ('os.environ.get("SIMSPECT_GEM5_DIR",  "/work/gem5-recon")', 'os.environ.get("SIMSPECT_GEM5_DIR",  "gem5")', 1),
    ], "run: gem5 invocation, trace parsing, batch runner (all checkers)"),
    ("STAGE3_gem5/gem5_fastpath.py", "STAGE3_gem5/gem5_fastpath.py", [], "run: opt-in fast path (gem5.fast_path, make timing)"),
    ("STAGE3_gem5/cache_setup.py", "STAGE3_gem5/cache_setup.py", [], "run: initial cache state random_all (gem5_common.py)"),
    ("STAGE3_gem5/check_ld.py", "STAGE3_gem5/check_ld.py", [], "run: load-transmitter checker (STT/ReCon rows)"),
    ("STAGE3_gem5/check_br.py", "STAGE3_gem5/check_br.py", [], "run: branch-transmitter checker (STT/ReCon rows)"),
    ("STAGE3_gem5/check_other.py", "STAGE3_gem5/check_other.py", [], "run: other-transmitter checker (STT/ReCon rows)"),
    ("STAGE3_gem5/check_footprint.py", "STAGE3_gem5/check_footprint.py", [
        ('"SimSpect hooks (wiki/design/SIMSPECT_HOOKS.md); cannot decide"', '"SimSpect hooks; cannot decide"', 1),
    ], "run: footprint checker for InvisiSpec/CleanupSpec/SpecLFB rows; classify.py imports it"),
    ("STAGE3_gem5/triage/diag/_fv2_slice.py", "STAGE3_gem5/_fv2_slice.py", [], "classify: transmitter slice helper (classify.py gate imports _fv2_slice)"),
    ("STAGE3_gem5/timing/firstdet_stream.py", "STAGE3_gem5/timing/firstdet_stream.py", [], "run: first-detection consumer (make hits, make timing)"),
    ("STAGE3_gem5/timing/timing_driver.py", "STAGE3_gem5/timing/timing_driver.py", [
        ('str(workdir).startswith(("/tmp", str(wd), "/tests"))', 'str(workdir).startswith(("/tmp", str(wd), "/tmp"))', 1),
        ('"keep raw/ + traces/ for every test, not only hits (smoke checks, e.g. "', '"keep raw/ + traces/ for every test, not only hits "', 1),
        ('"full_smoke_check.py; cache-full 2026-11-09). Default off."', '"(smoke checks). Default off."', 1),
    ], "run: run_one / build_order used by firstdet_stream.py"),
    ("STAGE3_gem5/timing/fastpath_worker.py", "STAGE3_gem5/timing/fastpath_worker.py", [], "run: fast-path worker (timing_driver.py)"),
    ("STAGE3_gem5/timing/firstdet_report.py", "STAGE3_gem5/timing/firstdet_report.py", [
        ('help="amortized Alloy + Stage 2 CPU-s per corpus test (TA-7); omitted = execution only"',
         'help="amortized Alloy + Stage 2 CPU-s per corpus test; omitted = execution only"', 1),
    ], "report: K/N and (N+1)/(K+1) per bug (make hits)"),
    ("STAGE3_gem5/timing/time1_20261115/make_sample.py", "STAGE3_gem5/timing/make_sample.py", [], "timing: fixed 1,000-pair sample (make timing)"),
    ("STAGE3_gem5/timing/amulet_t5/make_benchmark_t5.py", "amulet/make_benchmark_t5.py", [], "amulet: measurement-only benchmark driver from AMuLeT's benchmark.py (make amulet-hits/-timing)"),
    ("STAGE3_gem5/timing/amulet_t5/classify_t5.py", "amulet/classify_t5.py", [
        ("T5 = '/tests/simspect_alloy_20261108/timing/amulet_t5'", "T5 = os.environ.get('AMULET_T5', os.getcwd())", 1),
    ], "amulet: replay + classify AMuLeT violations (make amulet-hits)"),
    ("STAGE3_gem5/timing/amulet_t5/perbug_t5.py", "amulet/perbug_t5.py", [], "amulet: per-bug K from the replayed violations (make amulet-hits)"),
    ("STAGE3_gem5/timing/amulet_t5/cs_nonexclusive_t5.py", "amulet/cs_nonexclusive_t5.py", [], "amulet: CleanupSpec non-exclusive predicate check (make amulet-hits)"),
    ("STAGE3_gem5/timing/amulet_t5/summarize_t5.py", "amulet/summarize_t5.py", [], "amulet: per-run CPU summary read by compare.py (make compare)"),
]
BUGS = sorted(p.name for p in (REPO / "STAGE3_gem5/bugs").glob("*.py") if p.name != "_regress.py")
for b in BUGS:
    PY.append((f"STAGE3_gem5/bugs/{b}", f"STAGE3_gem5/bugs/{b}", [
        ('default="runconfigs/twostage_lp/eval_20261110/campaigns.json"', 'default="work/eval/campaigns.json"', 1),
        ('default="/tests/simspect_alloy_20261108/testsets_twostage"', 'default="work/testsets"', 1),
    ] if b == "classify.py" else [], "classify: hit attribution (classify.py and its cause modules)"))

JAVA = [("STAGE1_alloy/a6RandomModels.java", "STAGE1_alloy/a6RandomModels.java", "generate: seeded random enumerator (alloy_solver_order.py)"),
        ("STAGE1_alloy/a6CountModels.java", "STAGE1_alloy/a6CountModels.java", "generate: Stage 1 enumerator (run_stage1.py)")]

ALS = [(f"STAGE1_alloy/models/{m}.als", f"STAGE1_alloy/models/{m}.als", w) for m, w in [
    ("Footprint_6_u_core_ri", "Stage 1 core model, InvisiSpec/CleanupSpec/SpecLFB family"),
    ("Footprint_6_u_lpP", "Stage 1.5 loose-pin model, InvisiSpec/CleanupSpec/SpecLFB family"),
    ("STT_6_u_core_ri", "Stage 1 core model, STT family (E2/E3/E4 rows)"),
    ("STT_6_u_lpP", "Stage 1.5 loose-pin model, STT family"),
    ("Recon_6_u_core_ri", "Stage 1 core model, ReCon family (E6 row)"),
    ("Recon_6_u_lpP", "Stage 1.5 loose-pin model, ReCon family")]]

TABLES = [("STAGE2_compilation/instruction_tables/proposed/fv4_vocab.jsonc", "STAGE2_compilation/instruction_tables/fv4_vocab.json",
           "recipe A instruction table (stage2_A.json)", ["_refused"]),
          ("STAGE2_compilation/instruction_tables/proposed/interleave_only.jsonc", "STAGE2_compilation/instruction_tables/interleave_only.json",
           "recipe A filler table (fanout_v2.interleave_only.table)", ["validation"])]
CRIT_DOC_KEYS = ["_doc", "_superseded_note", "status", "source", "builds", "not_covered", "out_of_scope", "amulet_checks", "schema_doc"]
CRITS = [(f"specs/leakage/{d}.json", f"specs/leakage/{d}.json", f"check_footprint.py criterion for the {d} hits/timing rows")
         for d in ("invisispec", "cleanupspec", "speclfb")]


PROSE = {"comment", "emitter", "text", "why", "notes", "note", "decided", "agreed", "claims_note", "why_not_observed", "quote",
         "safety", "gem5_uops", "gem5", "rule", "claim", "replay", "item", "reason", "doc", "_doc"}


def prose_drop(o, dropped, path=""):
    if isinstance(o, dict):
        for k in list(o):
            v = o[k]
            if k in PROSE and (isinstance(v, str) or (isinstance(v, list) and all(isinstance(x, str) for x in v))):
                dropped.add(k); del o[k]
            else:
                prose_drop(v, dropped)
    elif isinstance(o, list):
        for v in o:
            prose_drop(v, dropped)
    return o


def str_sub(o, old, new):
    if isinstance(o, dict):
        return {k: str_sub(v, old, new) for k, v in o.items()}
    if isinstance(o, list):
        return [str_sub(v, old, new) for v in o]
    return o.replace(old, new) if isinstance(o, str) else o


def load_jsonc(p):
    t = Path(p).read_text(encoding="utf-8")
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    return json.loads(t)


def dump(obj, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def _gem5(v):
    return v.replace("/work/amulet/", "@GEM5@/").replace("/work/", "@GEM5@/") if isinstance(v, str) else v


RUNCFG = []


def make_configs(out, rec):
    import hashlib
    BC = "runconfigs/bigcorpus_20261115"

    def put(dst, obj, src, why):
        dump(obj, out / dst)
        rec["files"].append(dict(dst=dst, src=src, kind="json-config", why=why, replacements=[]))

    st1 = load_jsonc(REPO / "runconfigs/twostage_lp/Footprint_6_u.jsonc")["twostage_lp"]["stage1"]
    g = load_jsonc(REPO / "runconfigs/twostage_lp/Footprint_6_u.jsonc")
    g["paths"]["testset_dir"] = "@WORK@/testsets"
    g["twostage_lp"].update(corpus="Footprint_6_u_main_A", stage2_config="runconfigs/stage2_A.json")
    put("runconfigs/generate/Footprint_6_u_main.json", g, "runconfigs/twostage_lp/Footprint_6_u.jsonc",
        "make corpus: the main corpus generation (Stage 1 + Stage 1.5 exactly as the main corpus's Alloy run) + Stage 2 recipe A")
    core_sha = hashlib.sha256((out / "STAGE1_alloy/models/Footprint_6_u_core_ri.als").read_bytes()).hexdigest()
    for fam, corpus in (("Footprint_6_u", "Footprint_6_u_extra_A"), ("STT_6_u", "STT_6_u_A"), ("Recon_6_u", "Recon_6_u_A")):
        g = load_jsonc(REPO / f"{BC}/twostage_{fam}.jsonc")
        g["paths"]["testset_dir"] = "@WORK@/testsets"
        g["twostage_lp"].update(corpus=corpus, stage2_config="runconfigs/stage2_A.json")
        if fam == "Footprint_6_u":
            g["twostage_lp"]["stage1"] = {"reuse_cores": [f"@WORK@/ws/Footprint_6_u_main_A/stage1/out/Footprint_6_u_core_ri/{k}/stage1_xml"
                                                          for k in ("k2", "k3")], "reuse_sha256": core_sha}
        else:
            g["twostage_lp"]["stage1"] = dict(st1)
        g["twostage_lp"].pop("stage2_postpasses", None)
        name = "Footprint_6_u_extra" if fam == "Footprint_6_u" else fam
        put(f"runconfigs/generate/{name}.json", g, f"{BC}/twostage_{fam}.jsonc",
            f"make corpus-{'extra' if fam == 'Footprint_6_u' else fam}: generation for {corpus}")
    s2 = load_jsonc(REPO / f"{BC}/stage2_final_A.jsonc")
    s2["paths"].update(instruction_tables="STAGE2_compilation/instruction_tables/fv4_vocab.json", testset_dir="@WORK@/testsets",
                       results_dir="@WORK@/results", results_name="stage2_A")
    s2["gem5"]["binary"] = _gem5(s2["gem5"]["binary"]); s2["gem5"]["config_script"] = _gem5(s2["gem5"]["config_script"])
    s2["fanout_v2"]["interleave_only"]["table"] = "STAGE2_compilation/instruction_tables/interleave_only.json"
    s2 = {"paths": {k: s2["paths"][k] for k in ("stage2_dir", "instruction_tables", "testset_dir", "results_dir", "results_name")},
          "speculation": {"branch_modes": s2["speculation"]["branch_modes"]}, "gem5": {"jobs": s2["gem5"]["jobs"]},
          "interleave": s2["interleave"], "reg_naming": s2["reg_naming"], "fanout_v2": s2["fanout_v2"],
          "branch_cond": s2["branch_cond"], "fpr": s2["fpr"]}
    s2["fanout_v2"].pop("otb", None)
    put("runconfigs/stage2_A.json", s2, f"{BC}/stage2_final_A.jsonc", "Stage 2 recipe A (all corpora, rounds)")

    def runcfg(src, dst, rn, why, model=None):
        c = load_jsonc(REPO / src)
        c["paths"].update(instruction_tables="STAGE2_compilation/instruction_tables/fv4_vocab.json", testset_dir="@WORK@/testsets",
                          results_dir="@WORK@/results", results_name=rn)
        if model:
            c["paths"]["model"] = model
        for k in ("binary", "config_script"):
            c["gem5"][k] = _gem5(c["gem5"][k])
        c["gem5"]["fast_path"] = True
        assert c.get("alloy", {}).get("batch_size", 1000) == 1000
        for k in ("alloy", "filter", "interleave", "reg_naming", "branch_cond", "fanout_v2", "fpr"):
            c.pop(k, None)
        for k in ("instruction_tables", "models_dir", "alloy_stage"):
            c["paths"].pop(k, None)
        c["pipeline"] = {"keep_tmp": c.get("pipeline", {}).get("keep_tmp", False)}
        put(dst, c, src, why)

    for r in ("T1g", "T2g", "T3g"):
        runcfg(f"{BC}/{r}_Footprint_6_u_nov10_s2A.jsonc", f"runconfigs/hits/{r}.json", f"{r}_hits",
               f"make hits: {r} first-detection row (parity config) + fast_path true")
        runcfg(f"STAGE3_gem5/timing/time1_20261115/configs/{r}_time1.jsonc", f"runconfigs/timing/{r}.json", f"{r}_timing",
               f"make timing: {r} timing row + fast_path true")
    for r, src, model in (("E2", "E2_STT_6_u_core_lpP_s2A", "STT_6_u_A"), ("E2w", "E2w_STT_6_u_core_lpP_s2A", "STT_6_u_A"),
                          ("E3", "E3_STT_6_u_core_lpP_s2A", "STT_6_u_A"), ("E4", "E4_STT_6_u_core_lpP_s2A", "STT_6_u_A"),
                          ("E6", "E6_Recon_6_u_core_lpP_s2A", "Recon_6_u_A")):
        runcfg(f"{BC}/{src}.jsonc", f"runconfigs/eval/{r}.json", f"{r}_{model}", f"make eval: {r} row on {model} + fast_path true", model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / "trippel/simspect-anon"))
    ap.add_argument("--record", default=str(HERE / "build_record.json"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    keep = {"gem5", "STAGE1_alloy", "data"}
    for c in out.iterdir():
        if c.name not in keep:
            shutil.rmtree(c) if c.is_dir() else c.unlink()
    s1 = out / "STAGE1_alloy"
    if s1.exists():
        for c in s1.iterdir():
            if c.name != "models":
                shutil.rmtree(c) if c.is_dir() else c.unlink()
        if (s1 / "models").exists():
            for c in (s1 / "models").iterdir():
                if c.name != "speclfb":
                    shutil.rmtree(c) if c.is_dir() else c.unlink()
    rec = {"files": []}
    for src, dst, reps, why in PY:
        if dst in REMOVED:
            rec.setdefault("removed", []).append(dst)
            continue
        text = (REPO / src).read_text()
        res = strip.strip_py(text)
        for old, new, n in reps:
            c = res.count(old)
            if c != n:
                raise SystemExit(f"{src}: replacement count {c} != {n}: {old[:80]}")
            res = res.replace(old, new)
        n_before = len(res.splitlines())
        ops = list(PRUNE.get(dst, []))
        if dst.startswith("STAGE3_gem5/bugs/") and not Path(dst).name.startswith("_") and Path(dst).name != "classify.py":
            ops += spec_misc.BUGS_META
        if ops:
            res = strip._collapse_blank_runs(_prune.apply(res, ops))
        if dst.startswith("STAGE3_gem5/bugs/"):
            res = _labels.relabel(res)
            for pat, new in IDENT_RENAME:
                res = re.sub(pat, new, res)
            dst = BUG_RENAME.get(dst, dst)
        p = out / dst
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(res)
        rec["files"].append(dict(dst=dst, src=src, kind="py", why=why, replacements=[[o, n_] for o, n_, _ in reps],
                                 pruned=bool(ops), lines_before_prune=n_before, lines=len(res.splitlines())))
    for src, dst, why in JAVA:
        p = out / dst
        p.write_text(strip.strip_java((REPO / src).read_text()))
        rec["files"].append(dict(dst=dst, src=src, kind="java", why=why, replacements=[]))
    for src, dst, why in ALS:
        p = out / dst
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(strip.strip_als((REPO / src).read_text()))
        rec["files"].append(dict(dst=dst, src=src, kind="als", why=why, replacements=[]))
    for src, dst, why, drop in TABLES:
        d = load_jsonc(REPO / src)
        if "interleave_only" in src:
            drop = [k for k in d if k != "entries"]
        for k in drop:
            d.pop(k, None)
        pd = set()
        prose_drop(d, pd)
        dump(d, out / dst)
        rec["files"].append(dict(dst=dst, src=src, kind="json", why=why,
                                 replacements=[["drop top-level keys", drop], ["drop prose string fields", sorted(pd)]]))
    for src, dst, why in CRITS:
        d = load_jsonc(REPO / src)
        c = {"schema": d["schema"], "defense": d["defense"],
             "observation": {"structures": d["observation"]["structures"]},
             "actors": {k: d["actors"][k] for k in ("default", "select_by_scheme") if k in d["actors"]},
             "window": {"footprint": {k: v for k, v in d["window"].get("footprint", {}).items() if k == "branches_unresolved"}},
             "terms": {}, "leak": {k: d["leak"][k] for k in ("form", "term") if k in d["leak"]}}
        c["actors"]["modes"] = {m: {"impl": v["impl"]} for m, v in d["actors"]["modes"].items()}
        for t, v in d["terms"].items():
            if isinstance(v, dict) and "kinds" in v:
                c["terms"][t] = {k: v[k] for k in ("kinds", "key") if k in v}
        if "undo_obligations" in d:
            c["undo_obligations"] = d["undo_obligations"]
        if "ownership" in d:
            c["ownership"] = {k: d["ownership"][k] for k in ("kinds", "claims") if k in d["ownership"]}
        dump(c, out / dst)
        rec["files"].append(dict(dst=dst, src=src, kind="json", why=why,
                                 replacements=[["keep only the keys check_footprint.py reads", sorted(c)]]))
    make_configs(out, rec)
    au = HERE / "authored"
    for f in sorted(au.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            rel = f.relative_to(au)
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, p)
            rec["files"].append(dict(dst=str(rel), src=f"scripts/anon_artifact/authored/{rel}", kind="authored",
                                     why="authored for the artifact", replacements=[]))
    Path(a.record).write_text(json.dumps(rec, indent=1))
    print(f"built {len(rec['files'])} files into {out}")


if __name__ == "__main__":
    main()

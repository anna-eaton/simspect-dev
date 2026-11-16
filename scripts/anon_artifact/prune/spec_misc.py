"""Prune ops for the remaining files (see prune.py)."""

PIPELINE = [
    ("del_def", "save_provenance"),
    ("del_def", "phase_xml"),
    ("del_def", "phase_llvm"),
    ("del_def", "phase_asm_gem5_streaming"),
    ("del_def", "phase_clean"),
    ("del_def", "_per_branch_unresolved"),
    ("del_def", "_per_branch_resolved"),
    ("del_def", "_timing_mode"),
    ("replace_def", "_per_branch_all", '''
def _per_branch_all(grid, resolved, unresolved, sweep_cfg, stem):
    tp = _timing_grid_point(stem, sweep_cfg)
    if tp is None:
        raise ValueError("sweep.timing_grid is required")
    u, r = tp
    out = []
    for g in grid:
        e = dict(g); e.update({pc: u for pc in unresolved}); e.update({pc: r for pc in resolved}); out.append(e)
    return out
'''),
    ("replace_def", "main", '''
def main() -> None:
    ap = argparse.ArgumentParser(description="SimSpect engine: asm (compile + annotate) and gem5 (run the checkers) phases.")
    ap.add_argument("phase", choices=["asm", "gem5"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--force", action="store_true", help="Re-run phase even if output already exists")
    args = ap.parse_args()
    config_path = ROOT / args.config
    if not config_path.exists():
        sys.exit(f"error: config file not found: {config_path}")
    cfg = load_config(config_path)
    paths_cfg = cfg["paths"]
    testset_base = resolve(paths_cfg["testset_dir"]) / args.model
    results_base = resolve(paths_cfg["results_dir"]) / paths_cfg.get("results_name", args.model)
    testset_base.mkdir(parents=True, exist_ok=True)
    for m in cfg["speculation"]["branch_modes"]:
        ts_mode = testset_base / m
        ts_mode.mkdir(parents=True, exist_ok=True)
        if args.phase == "asm":
            phase_asm(cfg, args.model, ts_mode, args.force)
        else:
            phase_gem5(cfg, args.model, ts_mode, results_base / m, args.force)
'''),
]

TIMING_DRIVER = [
    ("text", '        row["timing_mode"] = _pl._timing_mode(stem, cfg["sweep"])\n', "", 1),
]

CACHE_SETUP = [
    ("text", '''_S2 = str(Path(__file__).resolve().parent.parent / "STAGE2_compilation")
if _S2 not in sys.path:
    sys.path.append(_S2)
from make_rmw_corpus import addr_fields, key_paths
''', '''

def addr_fields(obj, path=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if isinstance(v, (dict, list)):
                out.update(addr_fields(v, p))
            elif (k == "addr" or k.endswith("_addr")) and isinstance(v, int):
                out[p] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(addr_fields(v, f"{path}[{i}]"))
    return out


def key_paths(obj, path=""):
    s = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            s.add(f"{path}.{k}"); s |= key_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            s |= key_paths(v, f"{path}[{i}]")
    return s
''', 1),
    ("del_def", "_main"),
    ("drop_if", None, "__name__ == '__main__'", "else", 1),
]

CLASSIFY = [
    ("del_def", "cmd_race"),
    ("text", ', "race": cmd_race}', "}", 1),
]

TWOSTAGE = [
    ("text", '''                          + ([] if T.get("stage2_postpasses", True) else ["--no-postpasses"])
                          + (["--modes", ",".join(sm["modes"])] if sm.get("modes") else []),''', ",", 1),
]

RESTREAM = [
    ("text", '"STAGE1_alloy/models/proposed_twophase/stage2_sharded.py"', '"STAGE1_alloy/gen/stage2_sharded.py"', 1),
    ("text", ', "--first-fraction", "0"]', "]", 1),
]

CLASSIFY += [
    ("text", "r_sa13_recon_sse_load as RSA13,\n                  r_sa9_recon_twin_untaint as RSA9, recon_reveal_artifact as REVEAL, uv6_vp_squash_race as RACE)",
             "r_sa13_recon_sse_load as RSA13)", 1),
    ("text", '''        r = rev.get(f"{mode}/{s}")
        if REVEAL.matches(r):
            return REVEAL.LABEL
        if RSA9.matches(r):
            return RSA9.LABEL
        return "isTainted=0 (reveal not checked)"''', '''        return "isTainted=0 (reveal not checked)"''', 1),
    ("text", "def recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf, rev):", "def recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf):", 1),
    ("text", "b = recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf, rev)", "b = recon_bucket(cl, s, mode, kind, rp, stt, twin, tstems, stlf)", 1),
    ("text", '''    stlf, rev = {}, {}
    for f in a.stlf:
        stlf.update(json.load(open(f)))
    for f in a.reveal:
        rev.update(json.load(open(f)))''', '''    stlf = {}
    for f in a.stlf:
        stlf.update(json.load(open(f)))''', 1),
    ("text", '    b.add_argument("--reveal", nargs="*", default=[])\n', "", 1),
    ("text", '''    r = sub.add_parser("race")
    r.add_argument("evidence", nargs="+")
    r.add_argument("--json")
''', "", 1),
]

CLASSIFY_EXTRA = [
    ("text", "from bugs import (disq_setup_block as SETUP, disq_hpad_text_end as HPAD, disq_hpad_rmw_padding as HPADRMW,\n                  disq_speclfb_nonload as NONLOAD, disq_data_obtained as GATE,",
             "from bugs import (disq_hpad_rmw_padding as HPADRMW, disq_data_obtained as GATE,", 1),
    ("replace_def", "sigs_invisispec", '''
def sigs_invisispec(raw, pv, gc):
    evs = {e["id"]: e for e in gc.parse_simspect_events(pv)}
    sigs, structs = set(), set()
    for o in raw.get("offending") or []:
        structs.add(o.get("struct"))
        vp = o.get("vp") or {}
        for i in o.get("event_ids") or []:
            e = evs.get(i)
            if UV1.is_event(e):
                sigs.add(UV1.LABEL)
                if UV1T.is_transient(e, vp):
                    sigs.add(UV1T.LABEL)
    if not sigs:
        sigs |= {f"other_{s}" for s in sorted(structs, key=str)}
    return sigs
'''),
    ("replace_def", "sigs_speclfb", '''
def sigs_speclfb(raw, pv, mode, gc, cf):
    from bugs import _speclfb
    a = _speclfb.analyze(raw, str(pv), mode, gc, cf)
    tags = {c["tag"] for c in a.get("causes") or []}
    sigs = _speclfb_tagsigs(tags)
    if not sigs:
        sigs.add("other:" + ("+".join(sorted(tags)) if tags else "disq_non_load_footprint"))
    return sigs
'''),
    ("text", '''        tend = _trace.text_end(testset, r["mode"], r["stem"], raw, gc) if testset else None
        fn = ((lambda x: sigs_invisispec(x, pv, gc, tend)) if defense == "invisispec"
              else (lambda x: sigs_speclfb(x, pv, r["mode"], gc, cf, tend)))
        return r["idx"], SETUP.with_exclusion(fn, raw, pv, gc, TARGETS[defense]), ""''',
             '''        fn = ((lambda x: sigs_invisispec(x, pv, gc)) if defense == "invisispec"
              else (lambda x: sigs_speclfb(x, pv, r["mode"], gc, cf)))
        return r["idx"], fn(raw), ""''', 1),
]

CLASSIFY_EXTRA += [
    ("drop_if", "cleanupspec_evidence", "rec.get('cache_setup') == 'full' and gz.exists()", "else", 1),
    ("text", "    res, setup_stripped, n_dg3 = {}, {}, 0\n", "    res, n_dg3 = {}, 0\n", 1),
    ("text", '''    for k, only in setup_stripped.items():
        if only:
            cls[k] = {"excluded_SETUP:no_test_event"}
''', "", 1),
]

SIMSPECT_PATHS = [
    ("text", '"instructions.json"', '"fv4_vocab.json"', 1),
]

ALLOY_SOLVER_ORDER = [
    ("text", "r1 = pass1_specify_state_a(inst, write_out=False)", "r1 = pass1_specify_state_a(inst)", 1),
]
FIND_DUPLICATES = [
    ("text", "r1 = pass1_specify_state_a(inst, write_out=False)", "r1 = pass1_specify_state_a(inst)", 1),
]

FIRSTDET_STREAM = [
    ("replace_def", "provenance_ok", '''
def provenance_ok(ann: dict):
    if not isinstance(ann.get("vocab_rj"), dict):
        return False, "not a recipe-A test (no vocab_rj in the annotation)"
    return True, ""
'''),
    ("text", "mispredict_not_taken|mispredict_taken|stl_bypass)", "mispredict_not_taken|mispredict_taken)", 1),
]

STAGE15LP = [
    ("del_def", "relax_nonbranch_resolved"),
    ("drop_if", "main", "a.relax_nonbranch_resolved", "else", 1),
    ("del_stmt", "main", "ap.add_argument('--relax-nonbranch-resolved'", 1),
    ("del_stmt", "main", "ap.add_argument('--limit-cores'", 1),
    ("del_stmt", "main", "ap.add_argument('--first-seed'", 1),
    ("del_stmt", "main", "ap.add_argument('--seed-start'", 1),
    ("del_stmt", "main", "ap.add_argument('--resume'", 1),
    ("text", " relax_nonbranch_resolved={a.relax_nonbranch_resolved} host=", " host=", 1),
    ("text", " dedup_level={a.dedup_level} seed_start={a.seed_start} ", " dedup_level={a.dedup_level} ", 1),
    ("text", "    items = list(groups.items())[: a.limit_cores or None]\n", "    items = list(groups.items())\n", 1),
    ("text", '''            seed = "default" if (s["started"] == 0 and a.first_seed == "default") else s["next_seed"]
            if seed != "default":
                s["next_seed"] += 1''', '''            seed = s["next_seed"]
            s["next_seed"] += 1''', 1),
    ("text", "next_seed=a.seed_start,", "next_seed=1,", 1),
    ("drop_if", "main", "a.resume and (out / 'cores.json').exists()", "else", 1),
    ("drop_if", "main", "a.resume and (out / 'jobs.jsonl').exists()", "else", 1),
    ("text", '''    if (out / "jobs.jsonl").exists() and not a.resume:
        sys.exit(f"stage15lp: {out}/jobs.jsonl exists (one run per out dir; --resume to continue)")''',
             '''    if (out / "jobs.jsonl").exists():
        sys.exit(f"stage15lp: {out}/jobs.jsonl exists (one run per out dir)")''', 1),
]

MAKE_S15 = [
    ("del_def", "fold_parts"), ("del_def", "main"), ("del_def", "xm_leak_edge"), ("del_def", "regen_ix"),
    ("del_def", "explicit_fold"), ("del_def", "gen_fold"), ("del_def", "find_block"), ("del_def", "core_info"),
    ("del_stmt", None, "SHAPES = ", 1),
    ("del_stmt", None, "KIND_SIG = ", 1),
    ("drop_if", None, "__name__ == '__main__'", "else", 1),
    ("replace_def", "pin_pred", '''
def pin_pred(rels, mode):
    if mode != "b":
        raise ValueError(mode)
    base = stage_seed.build_pred(rels, "seed_core")
    out, n = [], 0
    for line in base.splitlines():
        m = re.match(r"^(\\s+)(o\\d+) in (o\\d+)\\.rf$", line)
        if m:
            line = f"{m.group(1)}{m.group(2)} in {m.group(3)}.rf.*(ddi.rf)   // [path pin] edge may be subdivided"
            n += 1
        out.append(line)
    return "\\n".join(out).replace("// AUTO-GENERATED", f"// [path pin, {n} rf edges relaxed] AUTO-GENERATED")
'''),
    ("text", "import argparse\n", "", 1),
]

FIRSTDET_REPORT = [
    ("drop_if", "main", "args.gen_cpu_per_test is None and pv.exists()", "else", 1),
    ("del_stmt", "main", "pv = Path(args.testset) / 'PROVENANCE.json'", 1),
]

PIPELINE += [
    ("drop_if", "_build_gem5_env", "gem5_cfg.get('stl_ann_enable')", "else", 1),
    ("drop_if", "_build_gem5_env", "gem5_cfg.get('cache_setup_seed') is not None", "else", 1),
    ("drop_if", "_build_gem5_env", "gem5_cfg.get('criterion_actor')", "else", 1),
]

GEM5_COMMON = [
    ("drop_if", None, "STL_ANN_ENABLE and ann_path is not None and ann_path.exists()", "else", 1),
    ("del_stmt", None, "STL_ANN_ENABLE = ", 1),
    ("del_stmt", None, "STL_STORE_STALL_CYCLES: int = ", 1),
    ("del_stmt", None, "STL_ALIAS_PRED = ", 1),
]

CACHE_SETUP += [
    ("del_def", "_cold_burst"),
    ("text", '    "cold_burst": _cold_burst,\n', "", 1),
    ("text", 'if strategy in ("cold", "cold_burst", "random"):', 'if strategy in ("cold", "random"):', 1),
]

FIRSTDET_REPORT += [
    ("text", '''AMULET = {
    "UV1": ("invisispec", 23.7, 270, True),
    "UV3": ("cleanupspec", 27.1, 105, True),
    "UV4": ("cleanupspec", 1600, 6171, True),
    "UV5": ("cleanupspec", 1600, 6171, True),
    "UV6": ("speclfb", 42.7, 115, True),
    "jmp_shadow": ("speclfb", 136, 366, False),
}
INPUTS_PER_PROGRAM = 140
''', '''BUGS = {"UV1": "invisispec", "UV3": "cleanupspec", "UV4": "cleanupspec", "UV5": "cleanupspec", "UV6": "speclfb",
        "jmp_shadow": "speclfb"}
''', 1),
    ("text", "        for bug, (bd, aprog, acpu, known) in AMULET.items():", "        for bug, bd in BUGS.items():", 1),
    ("text", "            a_cases = aprog * INPUTS_PER_PROGRAM\n", "", 1),
    ("text", "                defense=dfn, known_amulet_bug=known, K=K, N=N,", "                defense=dfn, K=K, N=N,", 1),
    ("text", '''                amulet_pooled_programs=aprog, amulet_pooled_test_cases=round(a_cases, 1),
                multiple_tests=round(a_cases / exp, 1),
                simspect_cpu_s_per_test''', "                simspect_cpu_s_per_test", 1),
    ("text", '''                simspect_expected_cpu_s_exec_only=round(exp * cpu_t / N, 1),
                amulet_pooled_cpu_s=acpu, multiple_cpu=round(acpu / (exp * per_test), 2))''',
             '''                simspect_expected_cpu_s_exec_only=round(exp * cpu_t / N, 1))''', 1),
    ("text", '''    known = [b for b, v in res["bugs"].items() if v["known_amulet_bug"]]
    if known:
        mt = min(known, key=lambda b: res["bugs"][b]["multiple_tests"])
        mc = min(known, key=lambda b: res["bugs"][b]["multiple_cpu"])
        res["minimum"] = dict(bugs_present=sorted(known), all_5=len(known) == 5,
                              tests=dict(bug=mt, multiple=res["bugs"][mt]["multiple_tests"],
                                         upper_bound=res["bugs"][mt]["censored"]),
                              cpu=dict(bug=mc, multiple=res["bugs"][mc]["multiple_cpu"],
                                       upper_bound=res["bugs"][mc]["censored"]))
''', "", 1),
    ("text", '''             "| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | AMuLeT pooled test cases | multiple (tests) | SimSpect exp. CPU-s (incl. gen) | AMuLeT pooled CPU-s | multiple (CPU) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]''',
             '''             "| bug | defense | K/N | expected tests (N+1)/(K+1) | first (seed order / stream) | setups of detecting tests | SimSpect exp. CPU-s |",
             "|---|---|---|---|---|---|---|"]''', 1),
    ("text", '''                     f"{v['amulet_pooled_test_cases']:,} | {le}{v['multiple_tests']}x | {gt}{v['simspect_expected_cpu_s']} | "
                     f"{v['amulet_pooled_cpu_s']} | {le}{v['multiple_cpu']}x |")''', '''                     f"{gt}{v['simspect_expected_cpu_s']} |")''', 1),
    ("text", '''        le = "≤" if v["censored"] else ""
''', "", 1),
    ("text", '''    if "minimum" in res:
        m = res["minimum"]
        lines.append(f"\\nMinimum over known bugs present ({', '.join(m['bugs_present'])}): tests {m['tests']['multiple']}x "
                     f"({m['tests']['bug']}{', upper bound' if m['tests']['upper_bound'] else ''}); "
                     f"CPU {m['cpu']['multiple']}x ({m['cpu']['bug']}{', upper bound' if m['cpu']['upper_bound'] else ''}).")
''', "", 1),
]

BUGS_META = [("del_stmt", None, x + " = ", None) for x in ("PAPER_LABEL", "ALIASES", "DEFENSES", "PHASE", "VERDICT", "ORDER", "NEEDS_GEM5", "FAMILY")]

DG3 = [("text", 'f"DG-3 would change issued_in_window of {raw.get(\'name\')}"', 'f"over_clean exemption would change issued_in_window of {raw.get(\'name\')}"', 1)]

CLASSIFY += [
    ("text", '''log.write(f"DG-3 {r['mode']}/{r['stem']}: over_clean exempt from outside-W filter -> "''',
             '''log.write(f"over_clean exemption {r['mode']}/{r['stem']}: over_clean exempt from outside-W filter -> "''', 1),
    ("text", 'hit stems, DG-3 flag changes {n_dg3}', 'hit stems, over_clean exemption flag changes {n_dg3}', 1),
    ("text", '''        if "_sh" in n.split("_fv3")[-1]:
            continue
''', "", 1),
    ("text", '''        stt = n.split("_")[0] in ("E3", "E4")''', '''        stt = bool(c.get("stt", False))''', 1),
    ("text", '''    stt = a.row.split("_")[0] in ("E3", "E4")''', '''    stt = a.stt''', 1),
    ("text", '''    b.add_argument("--json")\n    b.add_argument("--per-stem"''', '''    b.add_argument("--stt", action="store_true", help="the row is an STT build (E3, E4): bucket by the gate label only")\n    b.add_argument("--json")\n    b.add_argument("--per-stem"''', 1),
]

STAGE_SEED = [("del_stmt", None, "lines.append(f'// AUTO-GENERATED", 1)]
MAKE_S15 += [
    ("text", 'line = f"{m.group(1)}{m.group(2)} in {m.group(3)}.rf.*(ddi.rf)   // [path pin] edge may be subdivided"',
             'line = f"{m.group(1)}{m.group(2)} in {m.group(3)}.rf.*(ddi.rf)"', 1),
    ("text", '''    return "\\n".join(out).replace("// AUTO-GENERATED", f"// [path pin, {n} rf edges relaxed] AUTO-GENERATED")''',
             '''    return "\\n".join(out)''', 1),
    ("text", "    out, n = [], 0\n", "    out = []\n", 1),
    ("text", "            n += 1\n", "", 1),
]
STAGE15LP += [
    ("text", '''base_text + f"\\n\\n// ---- [lp-8] Stage-1 core {cid} = {members[0]} (path-style pin, make_s15_model.py --pin b) ----\\n" + pin + "\\n"''',
             '''base_text + "\\n\\n" + pin + "\\n"''', 1),
]
PARTITION = [
    ("text", '''        hdr = (f"// [STAGE-1 PARTITION {name}] generated by partition_stage1.py from {Path(a.core).name}"
               f" (sha256 {sha(a.core)[:16]}): {desc}. Everything else is byte-identical.\\n")
''', "", 1),
    ("text", '''            body = body + f"\\n// [STAGE-1 PARTITION {name}]\\nfact stage1_partition {{ {fact} }}\\n"''',
             '''            body = body + f"\\nfact stage1_partition {{ {fact} }}\\n"''', 1),
    ("text", "        p.write_text(hdr + body)", "        p.write_text(body)", 1),
]
TWOSTAGE += [
    ("text", '''        body = core.read_text().split("\\n", 3)[3] if core.read_text().startswith("// production since") else core.read_text()''',
             '''        body = core.read_text()''', 1),
    ("text", '''    scfg.write_text(f"// twostage_lp.py {now()}: copy of {src} with only paths.testset_dir and gem5.jobs (asm threads) changed\\n" + txt2)''',
             '''    scfg.write_text(txt2)''', 1),
]
RESTREAM += [
    ("text", '''    scfg.write_text(f"// restream.py {now()}: copy of {a.cfg} with only paths.testset_dir and gem5.jobs changed\\n" + txt)''',
             '''    scfg.write_text(txt)''', 1),
]
RUN_STAGE1 = [
    ("text", '''_MAC_JAVA = "/opt/homebrew/opt/openjdk@17/bin/java"
_MAC_DISK = "/System/Volumes/Data"
JAVA = os.environ.get("SIMSPECT_JAVA") or (_MAC_JAVA if os.path.exists(_MAC_JAVA) else (shutil.which("java") or "java"))
DISK = os.environ.get("SIMSPECT_DISK") or (_MAC_DISK if os.path.exists(_MAC_DISK) else str(STAGE1))''',
             '''JAVA = os.environ.get("SIMSPECT_JAVA") or shutil.which("java") or "java"
DISK = os.environ.get("SIMSPECT_DISK") or str(STAGE1)''', 1),
]
ALLOY_SOLVER_ORDER += [
    ("text", '["java", *xmx, "-cp", "alloy6.jar:.", "a6CountModels"', '[os.environ.get("SIMSPECT_JAVA", "java"), *xmx, "-cp", "alloy6.jar:.", "a6CountModels"', 1),
    ("text", '["java", *xmx, "-cp", "alloy6.jar:.", "a6RandomModels"', '[os.environ.get("SIMSPECT_JAVA", "java"), *xmx, "-cp", "alloy6.jar:.", "a6RandomModels"', 1),
    ("text", 'cmd = ["javac", "-cp"', 'cmd = [os.environ.get("SIMSPECT_JAVAC", "javac"), "-cp"', 1),
]

MAKE_BENCH = [
    ("text", "isa_spec = os.path.join(os.getcwd(), 'x86/isa_spec/base.json')  # T5: path only", "isa_spec = os.path.join(os.getcwd(), 'x86/isa_spec/base.json')", 1),
    ("text", "# ---------------- T5 measurement helpers (SimSpect firstdet-amulet) ----------------\n", "", 1),
    ("text", "_T5 = {}            # round -> record", "_T5 = {}", 1),
    ("text", '''    """CPU-s of every live process in process group pgid: utime+stime+cutime+cstime
    (dead, reaped descendants are counted in their reaper's cutime/cstime)."""
''', "", 1),
    ("text", "        # fields[0] = state (field 3); pgrp = field 5 -> idx 2; utime..cstime = fields 14..17 -> idx 11..14\n", "", 1),
    ("text", "# ---------------- end T5 helpers ----------------\n", "", 1),
    ("text", "  # T5\\n", "\\n", 5),
]
CACHE_SETUP += [
    ("text", '''    block = ([f"\\t# simspect cache_setup={strategy} (STAGE3_gem5/cache_setup.py)", "\\t#APP",''', '''    block = (["\\t#APP",''', 1),
]

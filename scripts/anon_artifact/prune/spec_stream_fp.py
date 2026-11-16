"""Prune ops for STAGE1_alloy/gen/stream_fp.py: only the recipe-A publish path is kept (RMW and jmp come from
Stage 2 itself via fanout_v2.vocab_rj). Removed: the RMW/jmp post-pass branch (make_rmw_corpus.py /
make_jmp_corpus.py), the external stem-scan hook (--uv5-filter, COUNTS.json), --seen-from / --start-n extension
runs, --git-rev (post-pass only), --modes (stl_bypass prep) and the --no-postpasses switch (now the only behaviour)."""
OPS = [
    ("text", "\n\nNO_POST = False\n", "\n", 1),
    ("text", '''            "stage2_parsexml_llc": st.get("cpu_s", {}).get("stage2"), "rmw_postpass": st.get("cpu_s", {}).get("rmw"),
                      "jmp_postpass": st.get("cpu_s", {}).get("jmp"),''', '''            "stage2_parsexml_llc": st.get("cpu_s", {}).get("stage2"),''', 1),
    ("text", '''            "recipe_version": ("A (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2, no post-passes)"
                               if NO_POST else "post-pass recipe (RMW and jmp post-passes)"),''',
             '''            "recipe_version": "A (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2)",''', 1),
    ("text", '''                            ("STAGE2_compilation/make_rmw_corpus.py", "STAGE2_compilation/make_jmp_corpus.py", "STAGE2_compilation/parsexml.py",
                             "STAGE2_compilation/batch_generate.py", "runconfigs/stage2_A.json",
                             "runconfigs/stage2_A.json") if (code / f).exists()},''',
             '''                            ("STAGE2_compilation/parsexml.py", "STAGE2_compilation/batch_generate.py", "runconfigs/stage2_A.json")
                            if (code / f).exists()},''', 1),
    ("text", '''            "recipe": ("stage2_A (fanout_v2.vocab_rj rmw+jmp, uniform draws) only, no post-passes" if NO_POST else
                       "post-passes make_rmw_corpus + make_jmp_corpus")}''',
             '''            "recipe": "stage2_A (fanout_v2.vocab_rj rmw+jmp, uniform draws)"}''', 1),
    ("text", '''                raise RuntimeError(f"--no-postpasses but {p} has no vocab_rj: Stage-2 config lacks fanout_v2.vocab_rj")''',
             '''                raise RuntimeError(f"{p} has no vocab_rj: Stage-2 config lacks fanout_v2.vocab_rj")''', 1),
    ("del_stmt", "main", "ap.add_argument('--start-n'", 1),
    ("del_stmt", "main", "ap.add_argument('--seen-from'", 1),
    ("del_stmt", "main", "ap.add_argument('--uv5-filter'", 1),
    ("del_stmt", "main", "ap.add_argument('--git-rev'", 1),
    ("del_stmt", "main", "ap.add_argument('--no-postpasses'", 1),
    ("del_stmt", "main", "ap.add_argument('--modes'", 1),
    ("del_stmt", "main", "global NO_POST, MODES", 1),
    ("drop_if", "main", "a.modes", "else", 1),
    ("del_stmt", "main", "NO_POST = a.no_postpasses", 1),
    ("text", "dict(merged_jobs=[], n=a.start_n, seen={}", "dict(merged_jobs=[], n=0, seen={}", 1),
    ("drop_if", "main", "a.seen_from and (not stf.exists())", "else", 1),
    ("text", '''        man.write_text("stem\\tcore\\tseed\\tmerged_at\\tpublished_at\\tbatch\\tmodes" + ("\\tuv5_class" if a.uv5_filter else "") + "\\n")''',
             '''        man.write_text("stem\\tcore\\tseed\\tmerged_at\\tpublished_at\\tbatch\\tmodes\\n")''', 1),
    ("drop_if", "main.publish", "a.no_postpasses", "body", 1),
    ("drop_if", "main.publish", "ok and a.uv5_filter", "else", 1),
    ("text", "                P = list(ready); cls = {}\n", "                P = list(ready)\n", 1),
    ("text", '(("jmp_rows" if a.no_postpasses else "jmp") + "/jmp_stems.tsv", "jmp_stems.tsv")', '("jmp_rows/jmp_stems.tsv", "jmp_stems.tsv")', 1),
    ("text", '(("jmp_rows" if a.no_postpasses else "jmp") + "/jmp_stems.tsv", "jmp_batch.tsv")', '("jmp_rows/jmp_stems.tsv", "jmp_batch.tsv")', 1),
    ("text", '''f"\\t{tpub}\\t{b}\\t{','.join(partial.get(s, MODES))}" + (f"\\t{cls.get(s, 'other')}" if a.uv5_filter else "") + "\\n" for s in P)''',
             '''f"\\t{tpub}\\t{b}\\t{','.join(partial.get(s, MODES))}\\n" for s in P)''', 1),
    ("drop_if", "main.publish", "a.uv5_filter", "else", 1),
    ("text", '''                    + (f"Stage 2: {cfg.name} (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2), no post-passes; "
                       f"{st['batch']} batches.\\n" if a.no_postpasses else
                    f"Stage 2: {cfg.name} -> per batch make_rmw_corpus --select eligible "
                    f"--fraction 0.5 --seed 20261109 --complete -> make_jmp_corpus --p 0.5 --seed 20261109 (placement uniform); {st['batch']} batches.\\n")''',
             '''                    + f"Stage 2: {cfg.name} (fanout_v2.vocab_rj: RMW and jmp drawn uniformly in Stage 2); {st['batch']} batches.\\n"''', 1),
    ("text", '''                    + f"tests not_taken {n_nt}, taken {n_t}; MANIFEST.tsv, rmw_stems.tsv, jmp_stems.tsv; code {code} (CODE_SNAPSHOT.txt, SHA256SUMS).\\n"
                    + (f"STEM SCAN: every stem is published; MANIFEST.tsv column uv5_class = D / C / other. "
                       f"GENERATED (the denominator): {st['counts']['programs']} new programs, {st['counts']['tests']} tests; class D {st['counts']['d_stems']}, "
                       f"C-not-D {st['counts'].get('c_not_d_stems', 0)} (COUNTS.json).\\n"
                       if a.uv5_filter else ""))''',
             '''                    + f"tests not_taken {n_nt}, taken {n_t}; MANIFEST.tsv, rmw_stems.tsv, jmp_stems.tsv; code {code} (SHA256SUMS).\\n")''', 1),
    ("text", '''"--model", a.base_name, "--jobs", str(a.jobs), "--first-fraction", "0"], cwd=str(code))''',
             '''"--model", a.base_name, "--jobs", str(a.jobs)], cwd=str(code))''', 1),
    ("text", ''',
                                                              counts=dict(programs=0, tests=0, d_stems=0, batches={}))''', ")", 1),
]

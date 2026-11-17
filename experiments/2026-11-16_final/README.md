# Snapshot: final paper results (big corpus, UV5 rounds, E2w, fast-path and clean AMuLeT timing), 2026-11-16

Frozen copy of every result behind the final ISCA-27 numbers, taken 2026-11-16 09:30-09:50 UTC by agent snapfinal, because the only copies were on the cafe nodes (holder jobs expire about 2026-11-17 21:40 UTC; node scratch is not guaranteed). It follows the layout of `experiments/2026-11-10_footprint_vs_amulet/`. Taken read-only: every node command was `tar -cf -`, `cat` or `sha256sum` streamed to the Mac (`copy_from_nodes.sh`, log `copy_from_nodes.log`); nothing on cafe1/cafe2/cafe3 was written, moved or deleted. Nothing was running on the nodes at copy time.

**Status: COMPLETE.** Every key number was recomputed from this directory alone and matches (`python3 -I code/recompute_numbers.py`, output `results/recompute_numbers.out`: ALL MATCH; `python3 -I code/figvalues/figvalues_20261116d.py`, output `results/figvalues_20261116d.out`, matches the multiples in EVAL_MANIFEST).

The design and the full narrative live in `wiki/state/EVAL_MANIFEST.md`, sections "Big corpus bug coverage (2026-11-15)" (incl. "MAIN NUMBER RESULTS", the extra corpus, the A-UV5 rounds, E2w, race lines and "Why A-UV5 is not found"), "Dedicated CPU timing (TIME-1, 2026-11-15)" (incl. "Fast path re-time" and "AMuLeT re-time on a clean node (2026-11-16)"), and `wiki/state/RUNNING.md` "Big corpus 2026-11-15". This README summarizes them so the snapshot stands alone.

## What is where

| path | content | in git? |
|---|---|---|
| `README.md` | this file: numbers → files → commands, replication, environment, hashes | yes |
| `copy_from_nodes.sh`, `copy_from_nodes.log` | the read-only pull script (steps `results timing uv5 data code`) and its log | yes |
| `results/bigcorpus/cafe3/` | cafe3 `/tests/bigcorpus_20261115/`: `firstdet/` (every run dir without `raw/`, `traces/`, `work/`: `results.jsonl`, `classes.jsonl`, `classes_rmw.jsonl`, `first_detection*.json`, `run_config.jsonc`, `config.ini`, `order_*.tsv`, `merge.log`, classify logs, `cs_evidence.tar.gz` = the classifier's evidence dir packed), `firstdet/report/` (`nov10_s2A/` = the main report, `extra_dedup/`, `T2g/` interim reports), `uv5verify/` (UV5 inst-061878 reruns with traces), `uv5why/` (census + reruns with traces), `e2w/` (gate, buckets, recon_stlf evidence, `rsa8/` trace excerpts, `rsa8_trace.json`, `movmerge.json`), `code_results_E2w.tar.xz` (all 36 + 12 E2w testrun shard result dirs), `uv5_rounds/` (round 3 `summary.json`, `post.log`, Stage-2 log, `ws/`; STOP files), `ws_nov10/` (Stage-2 stream state, order and prefix pair lists), `ws_Footprint_6_u/` (extra-corpus Stage 1.5 metadata: `jobs.jsonl`, `SUMMARY.json`, `cores.json`, `QUEUE_ORDER.json`, logs, cfg), `logs/`, `code/SNAPSHOT.txt`, `code_fp/SNAPSHOT.txt` | yes |
| `results/bigcorpus/cafe1/` | cafe1: round 1 (`firstdet/T2g_Footprint_6_u_nov10_c1_s2A`, `uv5_rounds/c1/`), UV5 inst-023088_c1 verification (`uv5verify/`, traces), `fp_equiv/` (fast-path equivalence on round 1, traces), recipe-B stopped dirs, `ws_nov10*`, `logs/`, SNAPSHOT.txt files. Files byte-identical to the cafe3 copy were removed (`DEDUP_vs_cafe3.tsv`). Note: cafe1's `T1g/T3g_Footprint_6_u_nov10_s2A/classes.jsonl` are an interim classification; the final one is the cafe3 copy | yes |
| `results/bigcorpus/cafe2/` | cafe2: round 2 (`firstdet/T2g_Footprint_6_u_nov10_c2_s2A`, `uv5_rounds/c2/`), UV5 inst-023722_c2 verification, `race/` (SPT-Fence 24-stem lines at delay 1/4, STT inst-047231 race sanity lines), recipe-B stopped dirs, `logs/`, `STOPPED.txt` | yes |
| `results/bigcorpus/DEDUP_vs_cafe3.tsv` | the 44 cafe1/cafe2 files removed as identical to cafe3's copies | yes |
| `results/uv5_traces/` | the original first-detection pipeview traces and raw records of all 5 UV5 detections (extra inst-061878 not_taken; round 1 inst-023088_c1 both modes; round 2 inst-023722_c2 both modes) | yes |
| `results/timing/cafe3/` | cafe3 `/tests/timing_20261115/`: `simspect/T{1,2,3}g_p16_{prod2,fast}` (per-test CPU records `results.jsonl`, `fastpath_workers.jsonl`, configs, driver logs; no raw/traces), `retime_fast/summary.{json,md}`, `clean_summary.{json,md}`, `amulet/runs/<D>_r<R>_n200_*` (clean AMuLeT runs: `t5_summary.json`, `run.log`, `yaml.diff`, the YAML, `summarize.stdout`, per-instance `log_round*` files; no violation dirs), `amulet/benchmark_t5.py`, `eq_fast/`, `configs/`, `scripts/` (incl. `kn_final.json`), `sample/`, `logs/`, `amulet_repo_state.txt`, `sample_corpus_meta/` | yes |
| `results/timing/cafe2/` | cafe2 `/tests/timing_20261115/`: TIME-1 (production path) SimSpect rows `simspect/T*g_p16`, the cafe2 AMuLeT runs (superseded by the clean cafe3 re-time), `time1_summary.{json,md}`, `kn_bigcorpus.json`, `gen/retime16` (generation re-time) and `gen/s15_inputs/models`, `eq_fast/` (fast-path equivalence 300/300 per defense), `logs/` incl. `time1_loadmon.log` | yes |
| `results/timing/host_loadmon/` | the host-level load monitors from Anna's AFS home (`time1_loadmon_cafe3.log` = fast-path re-time, `time1_loadmon_cafe3_amulet.log` = clean AMuLeT re-time, `time1_loadmon.log` / `_20261115.log` = cafe2 TIME-1) and `time1_loadmon_host.sh` | yes |
| `results/rounds_stem_mapping.tsv.gz` | the round stems: round r program `inst-NNNNNN_c<r>` = main program `inst-NNNNNN`; sha256 of every XML/TXT, verified identical for c1/c2/c3 against the main corpus | yes |
| `results/recompute_numbers.out`, `results/figvalues_20261116d.out` | verification outputs (below) | yes |
| `configs/` | `bigcorpus_20261115/` (every run config as on the node, incl. `T2g_Footprint_6_u_nov10_c{1,2,3}_s2A.jsonc`, `E2w_*`, `shards/`, `stage2_final_A.jsonc`), `overnight_20261111/` (recipe sources), `instruction_tables/` (`fv4_vocab.jsonc`, `interleave_only.jsonc`), `time1_20261115_{cafe3,cafe2}/` (timing configs incl. `*_fast.jsonc`) | yes |
| `models/` | `Footprint_6_u_lpP.als`, `Footprint_6_u_core_ri.als`, `STT_6_u_lpP.als`, `STT_6_u_core_ri.als` as on the node (read-only copies) | yes |
| `code/` | `recompute_numbers.py`; `figvalues/figvalues_20261116{,b,c,d}.py`; `mac_scripts/` (Mac copies of `scripts/bigcorpus_20261115/` and `STAGE3_gem5/timing/time1_20261115/`); `sha256_<host>_<tree>.txt` (sha256 of every file of each node code tree); `mac_vs_bigcorpus_code.tsv`, `mac_vs_timing_simspect_fast.tsv`, `mac_vs_run_hosts.diff` (node trees vs the Mac working tree) | yes |
| `environment/` | `raw_env_{cafe1,cafe2,cafe3}.txt` (CPU, gem5 binary md5/sha256, hook md5, Java, LLVM, Python, AMuLeT venv, container image) and `collect_env.sh` | yes |
| `data/` | compressed corpora and code trees (below) | **no** (gitignored, 270 MB) |
| `SHA256SUMS` | sha256 of every regular file in this directory, `data/` included | yes |

Files over 256 kB in `results/` are gzipped (`*.gz`). 172 symlinks inside copied workspaces (`ws_nov10*/batches/*/jmp`, uv5why testsets) point to node paths and are kept as recorded; they dangle on the Mac.

### data/ (gitignored)

| file | content | size |
|---|---|---|
| `corpus_main_Footprint_6_u_nov10_s2A.tar.xz` | main corpus: 25,116 Alloy programs (`xml/inst-*.{xml,txt}`, byte-identical to the 2026-11-10 `Footprint_6_u_core_lpP_fv3/xml`), the compiled tests (`<mode>/asm/*.s`, `<mode>/ann/*.ann.json`, both modes), `MANIFEST.tsv`, `READY`, `rmw_stems.tsv`, `jmp_stems.tsv` | 21 MB |
| `corpus_extra_Footprint_6_u_core_lpP_s2A.tar.xz` | extra corpus: 62,052 programs + compiled tests + `PROVENANCE.json`; the 45,466 counted programs are those not in `results/bigcorpus/cafe3/firstdet/report/extra_dedup/dup_stems.txt` | 54 MB |
| `corpus_round_c{1,2,3}_compiled.tar.xz` | each UV5 round's compiled tests + MANIFEST/READY/stem lists (no xml: the round XMLs are renames of the main ones, `results/rounds_stem_mapping.tsv.gz`) | 14 MB each |
| `corpus_e2w_STT_6_u_core_lpP_s2A_and_gprtwin.tar.xz` | the STT_6_u corpus E2w ran on (15,184 programs, compiled) and its GPR twin testset | 24 MB |
| `generation_extra_corpus_stage1_cores_stage15.tar.xz` | the 1,411 regen-lp Stage-1 cores (`cores/Footprint_6_u_core_ri`) and the extra corpus's Stage 1.5 workspace (`ws_Footprint_6_u/runs15` with every job's XML and `SOLVER_ORDER.json`, `stage1`, `cfg`, `logs`) | 20 MB |
| `code_cafe3_bigcorpus_code.tar.xz` | cafe3 `/tests/bigcorpus_20261115/code` (the code every counted big-corpus row ran; without `results/`, `generated/`, `__pycache__`) | 29 MB |
| `code_cafe3_bigcorpus_code_fp.tar.xz` | cafe3 `code_fp` (fast-path snapshot; no counted round used it) | 29 MB |
| `code_cafe3_timing_simspect_fast.tar.xz` | cafe3 `/tests/timing_20261115/simspect_fast` (code of the fast-path re-time) | 29 MB |
| `code_cafe2_timing_code.tar.xz` | cafe2 `/tests/timing_20261115/code` (TIME-1 production timing code) | 29 MB |

All counted corpora with their compiled tests come to 161 MB compressed, so no node-side tarball was needed. The `*_base` testsets (Stage-2 `.ll`, about 3.3 GB per corpus) were not copied: they regenerate from XML + code. The main corpus's own Stage 1 / 1.5 generation state (2026-11-10 regen-lp) is in `experiments/2026-11-10_footprint_vs_amulet/data/footprint_vs_amulet_20261110_corpus.tar.gz`.

## Code trees

All counted big-corpus rows ran from `/tests/bigcorpus_20261115/code` on each node (snapshot 2026-11-15 21:44:36 UTC from the Mac, HEAD 264adea + uncommitted tree; `results/bigcorpus/*/code/SNAPSHOT.txt` lists the sha256 of the key files). The cafe1 and cafe2 copies differ from cafe3 only in per-host run configs (`T2g_*_c<r>_s2A.jsonc`, E2w shard configs), `jobs/manifest.jsonl`, `SNAPSHOT.txt` and analysis-only scripts added on cafe3 later (`STAGE3_gem5/bugs/*`, `e2w_bucket.sh`, `movmerge_check.py`): every pipeline, checker and classifier file is identical (`code/sha256_*`). Against the Mac working tree of 2026-11-16 (`code/mac_vs_bigcorpus_code.tsv`): 9,501 files identical, 19 differ, 51 exist only on the node (shard configs, SNAPSHOT, the c3 round config). The non-markdown differences (`code/mac_vs_run_hosts.diff`) are the later opt-in fast path (`gem5_common.py`, `pipeline.py`, `timing_driver.py`, `firstdet_stream.py`, `testrun.py`, default off) plus `.gitignore`, `footprint_launch.sh`, `specs/hit_categories.json`. The fast-path re-time ran from `simspect_fast` (cafe3 = cafe2 copy, identical manifests; it is the Mac tree with the fast path), which differs from the Mac only in docs, `.gitignore`, three bigcorpus launcher scripts and `hit_categories.json`.

## Numbers → source → command

All from this snapshot. Estimator on both sides: expected tests to a detection = (N+1)/(K+1); AMuLeT N = 896,000 test cases per defense (T5, 2026-11-10 snapshot), K_AMuLeT = UV1 270, UV3 236, UV4 4, UV5 4, UV6 150, jmp 47.

| number | value | file(s) | recompute |
|---|---|---|---|
| A-UV1 InvisiSpec K/N | 2,002 / 4,000 | `results/bigcorpus/cafe3/firstdet/T1g_Footprint_6_u_nov10_s2A/classes.jsonl` (+ `results.jsonl.gz` for N) | `code/recompute_numbers.py` |
| A-UV6 / walk order / jmp shadow, SpecLFB K/N | 851 / 657 / 527 of 4,000 | `.../T3g_Footprint_6_u_nov10_s2A/classes.jsonl` | same |
| CleanupSpec main corpus | N 50,232; UV3 1,274, UV4 162, UV5 0 | `.../T2g_Footprint_6_u_nov10_s2A_merged/classes_rmw.jsonl` | same; report `firstdet/report/nov10_s2A/report_same_estimator.md` |
| CleanupSpec extra corpus, new programs | N 90,932; UV3 1,930, UV4 237, UV5 1 | `.../T2g_Footprint_6_u_core_lpP_s2A_new/classes_rmw.jsonl.gz` | same |
| UV5 rounds 1 / 2 / 3 | N 50,232 each; UV5 2 / 2 / 0; UV3 1,400 / 1,338 / 1,346; UV4 181 / 167 / 172 | `cafe1/.../T2g_Footprint_6_u_nov10_c1_s2A`, `cafe2/.../_c2_`, `cafe3/.../_c3_` `classes_rmw.jsonl`; `uv5_rounds/c<r>/summary.json` | same |
| pooled CleanupSpec | N 291,860; A-UV3 7,288, A-UV4 919, A-UV5 5 | the five runs above | same |
| UV5 verification | 5 detections (3 programs) reproduce 2/2 each | `results/bigcorpus/cafe3/uv5verify/`, `cafe1/uv5verify/`, `cafe2/uv5verify/` (verify.json, rerun traces); original traces `results/uv5_traces/` | `scripts/bigcorpus_20261115/uv5_verify.py` on the node (needs gem5) |
| Why A-UV5 is not found | census and RMW→plain-load reruns (3/4 over_clean) | `results/bigcorpus/cafe3/uv5why/` | `results/bigcorpus/cafe3/uv5why/uv5why_census.py` (= Mac `STAGE3_gem5/triage/uv5_shape/uv5_census_cmp.py`, byte-identical; not in the node code tree) |
| E2w (ReCon-STT, OTB check) | 30,368 tests; R-SA-8 candidates 24, signature-positive 22; A2 STLF bypass (UV2) 1,690 | `results/bigcorpus/cafe3/e2w/{buckets.json,rsa8_trace.json}`, shard results `code_results_E2w.tar.xz` | `code/recompute_numbers.py` (counts); full: `e2w_bucket.sh` on the node |
| SimSpect fast-path CPU-s per test | 1.344 / 1.738 / 1.2956 (InvisiSpec / CleanupSpec / SpecLFB) | `results/timing/cafe3/simspect/T*g_p16_fast/{results.jsonl,fastpath_workers.jsonl}`, `retime_fast/summary.json` | `code/recompute_numbers.py`; node: `retime_fast_summary.py` |
| production-path CPU-s per test (rerun / TIME-1) | 3.673 / 3.673 / 2.725 and 3.69 / 3.74 / 2.78 | `results/timing/cafe3/retime_fast/summary.json`, `results/timing/cafe2/time1_summary.json` | `summarize_time1.py` |
| AMuLeT clean CPU-s per test case | 0.07304 / 0.02337 / 0.01935 (R = 14 / 15 / 13 instances × 200 programs × 140) | `results/timing/cafe3/amulet/runs/*/t5_summary.json`, `clean_summary.json` | `code/recompute_numbers.py` |
| generation CPU per test | 0.93 (Alloy 0.56 re-timed + Stage 2 0.38) | `results/timing/cafe2/gen/retime16/summary.json`, extra corpus `PROVENANCE.json` (in `data/corpus_extra_*`) | `gen_retime.py` (EVAL_MANIFEST "Generation CPU") |
| tests multiples | 1,655x / 94x / 565x / 3.7x / 1,264x / 2,463x (UV1/UV3/UV4/UV5/UV6/jmp) | inputs above | `python3 -I code/figvalues/figvalues_20261116d.py` |
| CPU multiples with generation (exec only) | 53x (90x), 0.83x (1.27x), 4.9x (7.6x), 0.032x (0.050x), 11x (19x), 21x (37x); A-UV5 95% 0.007-0.17x | inputs above | same (`results/figvalues_20261116d.out`) |

`figvalues_20261116d.py` has its inputs written in (K/N, CPU per test); `recompute_numbers.py` checks those inputs against the raw records, so together they reproduce every figure value from the snapshot.

## Verification (2026-11-16, from this directory only)

`python3 -I code/recompute_numbers.py` → ALL MATCH: pooled CleanupSpec N 291,860, K 7,288 / 919 / 5; per-run counts as in the table; InvisiSpec/SpecLFB 2,002 / 851 / 657 / 527 of 4,000; fast-path CPU 1.344 / 1.738 / 1.2956; AMuLeT clean 0.07304 / 0.02337 / 0.01935; E2w 30,368 / 24 / 22 / 1,690. `figvalues_20261116d.py` prints the tests multiples 1,655 / 94.4 / 565 / 3.68 / 1,264 / 2,463 and CPU multiples 53.2 / 0.827 / 4.95 / 0.032 / 11.0 / 21.4 (exec only 90.0 / 1.27 / 7.60 / 0.050 / 18.9 / 36.8), identical to EVAL_MANIFEST and `clean_summary.json`. Cross-host checks: the cafe3 copies of the cafe1/cafe2 partitions are byte-identical to the originals; the round XMLs are byte-identical to the main XMLs; gem5 binary md5s are identical on all three nodes and equal to the 2026-11-10 snapshot.

## Replication

Everything runs inside the `gem5_dev` container (image `simspect_gem5_dev:20261109`) with base `O=/tests/bigcorpus_20261115` (scripts hard-code it). Unpack `data/code_cafe3_bigcorpus_code.tar.xz` to `$O/code` (it contains `STAGE1_alloy/alloy6.jar`; recompile the enumerators with `javac -cp alloy6.jar a6CountModels.java a6RandomModels.java` if needed), unpack the corpora to `$O/testsets/`, and use the configs in `configs/bigcorpus_20261115/`. `export TMPDIR=/tmp` for every gem5 run. Stage 2 is deterministic per stem (every draw is seeded from the stem), so the compiled tests regenerate byte-identically from XML + this code (checked on the nodes: cafe1 and cafe3 Stage 2 gave identical `.s`/`.ann.json` for the first 3,000 stems).

1. **Main corpus Stage 2** (from `$O/code`): `python3 scripts/bigcorpus_20261115/nov10_stream.py` with source `/tests/simspect_alloy_20261108/testsets_twostage/Footprint_6_u_core_lpP_fv3/xml` (= the main XMLs in `data/corpus_main_*`), config `runconfigs/bigcorpus_20261115/stage2_final_A.jsonc` (exact copy as run: `results/bigcorpus/cafe3/ws_nov10/stage2_final_A_nov10_stream.jsonc`), output `$O/testsets/Footprint_6_u_nov10_s2A`; log `ws_nov10/nov10_stream.log`. Order and the 4,000-pair prefix: `ws_nov10/{order_seed_pairs,prefix_pairs}.tsv`.
2. **First detection** (`firstdet_stream.py` via `scripts/bigcorpus_20261115/footprint_launch.sh start`, seed 20261109): CleanupSpec `T2g_Footprint_6_u_nov10_s2A.jsonc` over all 50,232 tests (as run: `--partition 0/3` cafe3, `1/3` and `2/3` cafe1 as `_cafe1`, `_cafe1b`), InvisiSpec `T1g_*` and SpecLFB `T3g_*` with `--only-file ws_nov10/prefix_pairs.tsv --seed-prefix 4000`. Merge: `python3 STAGE3_gem5/timing/firstdet_merge.py firstdet/T2g_Footprint_6_u_nov10_s2A_merged firstdet/T2g_Footprint_6_u_nov10_s2A{,_cafe1,_cafe1b}` (20 rows of a killed consumer removed first: `CLEANED.txt`). Exact launches: each run's `run_config.jsonc`, `driver.log`, `results/bigcorpus/cafe1/firstdet/launch.log`, `cafe2/firstdet/launch.log`.
3. **Classification and report**: `python3 STAGE3_gem5/timing/classify_hits.py <run> --defense <d> --stage3 $PWD/STAGE3_gem5 --testset <corpus> --jobs 16`, then for CleanupSpec `python3 STAGE3_gem5/timing/classify_cs_rmw.py <run> --rmw-stems <corpus>/rmw_stems.tsv --testset <corpus>`, then `python3 STAGE3_gem5/timing/firstdet_report.py --invisispec <T1g> --cleanupspec <T2g merged> --speclfb <T3g> --testset <corpus> --json report.json --md report.md` (its own multiple column uses pooled N/K and is not used; the same-estimator table is `report_same_estimator.md`).
4. **Extra corpus**: Stage 1.5 with `twostage_lp.py --alloy-only` (config `configs/bigcorpus_20261115/twostage_Footprint_6_u.jsonc`; the 1,411 cores and every job's model, seed and `SOLVER_ORDER.json` are in `data/generation_extra_corpus_*`), Stage 2 by `stream_fp.py --no-postpasses` with `ws_Footprint_6_u/cfg/stage2_final_A_stream.jsonc`. Dedup against the main corpus: `python3 scripts/bigcorpus_20261115/dedup_vs_main.py --main <ts>/Footprint_6_u_nov10_s2A/xml --extra <ts>/Footprint_6_u_core_lpP_s2A/xml --out firstdet/report/extra_dedup` (16,586 duplicates, 45,466 new). CleanupSpec T2g (`T2g_Footprint_6_u_core_lpP_s2A.jsonc`) over the new programs in three partitions (cafe3, `_cafe1`, `_cafe2`, `--exclude-file` lists in `report/extra_dedup/`), merged to `_all_merged`, restricted to new programs as `_new` (README.txt there), classified as in step 3.
5. **UV5 rounds**: `bash scripts/bigcorpus_20261115/uv5_rounds.sh <first round> <step> [P]` from `$O/code` (round r = the main XMLs linked as `inst-NNNNNN_c<r>`, Stage 2 by `nov10_stream.py`, CleanupSpec T2g with `T2g_Footprint_6_u_nov10_c<r>_s2A.jsonc`), tail by `uv5_round_post.sh <r>`; stopping rule K ≥ 4 pre-registered 02:20 UTC, met after round 3 (STOP files). Rounds 1-3 used the production path (`exec_path` in each `summary.json`). Verification: `python3 scripts/bigcorpus_20261115/uv5_verify.py --run <run> --config <T2g cfg> --model <corpus> --mode M --stem S --out <dir> --reruns 2`.
6. **E2w**: `python3 scripts/bigcorpus_20261115/shard_rows.py --corpus STT_6_u_core_lpP_s2A --config runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc --name bc_E2w_STT_6_u_core_lpP_s2A --k 36 --mine <shards> --nice 19` on the three nodes, then on cafe3 `bash scripts/bigcorpus_20261115/e2w_bucket.sh` (GPR twin, twin run, recon_stlf evidence, `STAGE3_gem5/bugs/classify.py gate` + `bucket`), `runconfigs/twostage_lp/eval_20261110/rsa8_trace.py`, `movmerge_check.py --testset <ts> --keys e2w/rsa8_keys.txt --out e2w/movmerge.json`.
7. **SimSpect timing (fast path)**: sample `make_sample.py --code-root $O/code --testset $O/testsets/Footprint_6_u_core_lpP_s2A --n 1000 --seed 20261115` (`results/timing/*/sample/`); TIME-1 production `run_simspect.sh <row>` on cafe2; fast-path re-time `CODE=/tests/timing_20261115/simspect_fast bash retime_fast.sh` on idle cafe3 (production rerun then fast path, 16 workers pinned to CPUs 0-31; chain `fast_chain.sh` with the idle gate), summary `retime_fast_summary.py`. Equivalence: `fastpath_equiv.py driver` (`eq_fast/`, 300/300 identical per defense).
8. **AMuLeT clean re-time** (cafe3): `DEFS="InvisiSpec:14 CleanupSpec:8 SpecLFB:8" bash scripts/amulet_chain.sh` (idle gate, `run_amulet.sh <D> <R> 200` pinned to CPUs 0-31, auto-calibration to ~16 busy threads: kept R = 14 / 15 / 13; calibration attempts were discarded on the node in `amulet/discard_calib/`, not copied), each run summarized by `summarize_t5.py`; then `summarize_time1.py . --kn-json scripts/kn_final.json --gen 0.93` → `clean_summary.{json,md}`.
9. **Figure values**: `python3 -I code/figvalues/figvalues_20261116d.py`.

## Environment (folded in from `environment/raw_env_*.txt`)

| item | value |
|---|---|
| hosts | cafe1, cafe2, cafe3: Intel Xeon Gold 6226R @ 2.90 GHz, 2 sockets × 16 cores × 2 threads = 64 logical CPUs, 503 GB; timing runs pinned to CPUs 0-31 (one thread per physical core) |
| container | `gem5_dev`, image `simspect_gem5_dev:20261109`, id `sha256:ef9c710614d20674dbb078a3f5b2aa5a6aac5caead2db2319d73c6fecc1f7fbc` |
| InvisiSpec (Futuristic) | `/work/amulet/amulet-gem5-InvisiSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt`, md5 `f45251db6d580f12e549751b9331a3ca`, hooks `simspect_hooks.cc` md5 `ba5d8404be86a29835ae35e7fc434a5e` ver=2 |
| CleanupSpec | `/work/amulet/amulet-gem5-CleanupSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt`, md5 `ec5710cad23e43b265f08657710fcb21`, hooks md5 `f6ae54552e946ced34e1b13f83cf05b0` ver=2 |
| SpecLFB | `/work/amulet/amulet-gem5-SpecLFB_AE-v1.1/build/X86/gem5.opt`, md5 `a84176e23121db26d8f2f9019d586566`, hooks md5 `e80773054bac94e259b565c122ebac5e` ver=2 |
| ReCon-STT (E2w) | `/work/gem5-recon-modded/build/X86/gem5.opt`, md5 `762efbc608e1c803368d19d1101abcbd` |
| STT (race lines) | `/work/stt/build/X86/gem5.opt` (git e3283b9), md5 `b5a38761c2f09a38bc84b315d353b9ab`; `/work/stt-master/build/X86/gem5.opt`, md5 `1fed10b57c16ad26981272ce7fc44c56` |
| SPT-Fence (race lines, cafe1/cafe2 only) | `/work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt` (git 0d2be0f), md5 `89475abc2e19677f3fee9b2feedd5971` |
| Alloy | `alloy6.jar` sha256 `6b8c1cb5bc93bedfc7c61435c4e1ab6e688a242dc702a394628d9a9801edb78d`; OpenJDK 17.0.15 |
| Stage 2 / harness | Python 3.8.10; clang-15 / llc-15 / llvm-objdump-15 15.0.7; clang 10.0.0; gcc 9.4.0; GNU as 2.34 |
| AMuLeT | commit `c871bdf6d143cb298c1e548c64b143bac40af09d` (a copy at `/tests/timing_20261115/amulet/amulet-repo`; untracked files only, `results/timing/*/amulet_repo_state.txt`), `benchmark_t5.py` md5 `fefd24d9828fc93d4cc2b90d45235b41`, venv `/opt/amulet-venv` Python 3.11.8: iced-x86 1.21.0, numpy 2.4.6, protobuf 3.20.0, pydot 4.0.1, pyparsing 3.3.2, PyYAML 6.0.3, toml 0.10.2, types-PyYAML 6.0.12.20260518, unicorn 2.1.4, xxhash 3.7.0 |

All binary md5s and hook md5s are identical across the three nodes and equal to `experiments/2026-11-10_footprint_vs_amulet/environment.md`.

## Not copied

Per-test `raw/` records and pipeview `traces/` of the runs (tens of GB; kept only for the 5 UV5 detections, the UV5 and uv5why reruns, the E2w R-SA-8 excerpts and the fast-path equivalence checks), `work/` dirs, the `*_base` Stage-2 testsets (`.ll`), the recipe-B testsets (dropped recipe; their stopped run metadata is kept), the stopped STT/Recon rows (E2/E3/E4, race rows) and their workspaces, `discard_*` dirs (incl. AMuLeT calibration attempts), AMuLeT violation dirs (`config0results*`) and the AMuLeT repo copy (only its commit and status), the cafe1/cafe2 code trees as tarballs (their file hashes are in `code/sha256_*`), and cafe3 `code_pre_s2_20261115_214550.tgz` (a pre-Stage-2 code backup).

## Hashes

`SHA256SUMS` lists every regular file (symlinks excluded) with its sha256, `data/` included; regenerate with `find . -type f ! -name SHA256SUMS ! -name .DS_Store -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS`.

## Note (2026-11-16 22:30, agent fprescore): re-score with W-3 + RG-1

The InvisiSpec and SpecLFB numbers above (A-UV1 2,002, A-UV6 851, walk order 657, jmp shadow 527 of 4,000; raw hits 4,000 / 1,748) were re-scored with the two checker changes decided after this snapshot (W-3 loads-only footprints for InvisiSpec / SpecLFB; RG-1 resolved-branch gate) by offline replay of the saved traces with the current checker: every number is unchanged, label for label, and so are the multiples and the figure values (`experiments/2026-11-10_footprint_vs_amulet/code/figvalues_20261116e.py`, output identical to d). CleanupSpec numbers are unaffected. Details: `wiki/state/EVAL_MANIFEST.md` "Re-score with W-3 + RG-1 (2026-11-16)"; files `experiments/2026-11-16_fprescore/`.

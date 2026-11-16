# Snapshot: SimSpect vs AMuLeT, unified footprint experiment (2026-11-10)

Anna, 2026-11-10: "save these results somewhere and the exact settings in some kind of snapshot so that we can replicate this experiment. and save all the states of the whole pipeline all the files used in case we change things." This directory is that snapshot, taken by the snapshot agent on 2026-11-10 (about 11:30-11:50 UTC) while firstdet-final was still running the final-protocol rows (T1g/T2g/T3g). It was taken read-only: nothing on cafe1/cafe3 was stopped or changed, apart from one new tarball written to cafe1 `/tests/simspect_alloy_20261108/snapshots/`.

**Status: COMPLETE (results re-copied 2026-11-10 14:52 UTC by firstdet-final with `recopy_results.sh`; same-estimator table and final 18x figure added 2026-11-10 18:58 UTC).** The final-protocol T*g rows finished: CleanupSpec T2g over all 50,232 tests (cafe3 + cafe1, merged), InvisiSpec T1g and SpecLFB T3g over the first 4,000 of the seed-20261109 order; see "Results (complete run)" below. The T*rt rows (per-branch random timing) are an earlier protocol. The ext corpus (`Footprint_6_u_core_lpP_fv3_ext`) never arrived on cafe3 and is not used by any number; `T2g_ext_*` is an empty run dir.

The source of truth for the design is `wiki/state/EVAL_MANIFEST.md`, section "Footprint model: the unified AMuLeT-comparison experiment (Anna, 2026-11-10)". Its protocol is summarized below so this directory stands alone.

## What is where

| path | content | in git? |
|---|---|---|
| `README.md` | this file: protocol, replication commands, results, hashes | yes |
| `environment.md` | gem5 binaries (md5/sha256, source-tree hash, hook version), Alloy jar, Java, Python, toolchain, AMuLeT commit and venv, container image, hosts | yes |
| `environment/` | raw env output per host, AMuLeT venv `pip freeze`, the SimSpect hook sources as built in each AMuLeT tree (+ its `se.py`), the repo hook patch files of that era | yes |
| `code/run_hosts/cafe1_loosepin_regen/` | frozen code root used for corpus generation (Stage 1, 1.5, 2, RMW, jmp): `code/` (with `CODE_SNAPSHOT.txt`, `SHA256SUMS` written by regen-lp) plus `lp/` (loose-pin tools as run) and `tools/` | yes |
| `code/run_hosts/cafe1_recipe_v3/` | recipe-v3 code drop (Stage 2/3 tools, `runconfigs/regen_lp_20261110`) that the other agents copied from | yes |
| `code/run_hosts/cafe3_firstdet_final/` | frozen code root that firstdet-final ran from on cafe3 (`--code-root`): `pipeline.py`, `STAGE3_gem5` (checkers, `cache_setup.py`, `timing/*`), configs, specs | yes |
| `code/run_hosts/cafe1_firstdet_final/` | the same for the cafe1 second consumer (differs only in `firstdet_report.py`, which is not run there) | yes |
| `code/run_hosts/cafe1_amulet_t5/` | AMuLeT T5 scripts as run on cafe1 (incl. host-only `benchmark_t5.py`, `analyse_ipc_violation_t5.py`, `chain_main.sh`) and `perbug/` | yes |
| `code/mac_only/` | files that never lived on a run host: `make_footprint_u.py`, the Mac loose-pin tool dir (incl. `relay_cafe3.sh`), `runconfigs/twostage_lp/*` | yes |
| `code/VERSIONS.tsv`, `code/mac_vs_run_hosts.diff` | sha256 of every pipeline file in each host tree vs the Mac working tree, and the diff wherever they differ | yes |
| `models/` | the exact `.als` files (production copies, the run-host copies, `proposed/ultimate/Footprint_6_u.als`, `footprint_v2/*`), the 363 per-core pinned Stage-1.5 models (tarball), and the Stage-1.5 run metadata (`cores.json`, `QUEUE_ORDER.json`, `SUMMARY.json`, `jobs.jsonl`, `stage15lp.log`) | yes |
| `configs/` | every run config and spec: `firstdet_final_20261110/` (T1rt/T2rt/T3rt, T1g/T2g/T3g, T2u5), `regen_lp_20261110/` (incl. `stage2_fv3_stream.jsonc`, the Stage-2 config actually run), `twostage_lp/`, the parity configs they derive from (`amulet_parity/`, `amulet_parity_fv2/`, `amulet_parity_fv2fp_rmw/`), `specs_leakage/{invisispec,cleanupspec,speclfb}.json` | yes |
| `results/firstdet_final/` | per-record results, classifications, first-detection JSONs, configs, `config.ini`, logs for every first-detection run on cafe3 and cafe1 (no `raw/`, `traces/`, `work/`), the reports, the UV5 diag inputs; `order_seed20261109.tsv` (the one order file shared by all rows) | yes |
| `results/amulet_t5/` | AMuLeT T5 runs (`t5_summary.json`, `t5_classes.json`, `t5_classes_all.json`, `info.txt`, `t5_instances.json`, `t5_rusage_children.json`, `run.log`, `yaml.diff`) and per-bug outputs (`perbug/out/{perbug_summary,violations_*,cs_nonexclusive}.json`, logs) | yes |
| `results/interim/` | earlier comparison tables: first-detection JSONs + configs of cafe1/cafe3 `results_fv2/` (STT_6_fv2, STT_6_fv2fp_rmw rows) and cafe3 `oldfanout/` | yes |
| `results/example_traces/` | gem5 pipeview traces of the UV5 hit inst-021207 (from T2rt, T2u5, T2g) and the first 3 detections per bug (UV1, UV3, UV4, UV5, UV6, jmp-shadow); `SELECTED.tsv` lists them | yes |
| `results/corpus_provenance/` | the corpus `PROVENANCE.json` + `READY`, Stage-1.5 `SUMMARY.json` and `QUEUE_ORDER.json` | yes |
| `results/generation_logs/` | regen-lp logs: `stage15lp_Footprint_6_u_lpPc.out`, `stream_Footprint_6_u_core_lpP_fv3.log`, `stream_fp.out`, `launch_regen_lp.log` | yes |
| `results/figure_interim/` | the v2 bar figure as it stood (`ISCA-27/tikz/*firstdet_bars_v2*`) | yes |
| `data/footprint_vs_amulet_20261110_corpus.tar.gz` | the corpus and its generation state (below) | **no** (gitignored, 72 MB) |
| `recopy_results.sh` | re-pulls the firstdet-final results when T*g finishes, regenerates `SHA256SUMS` | yes |
| `SHA256SUMS` | sha256 of every file in this directory, `data/` included | yes |

Files over about 1-2 MB in `results/` are gzipped (`*.gz`); the per-run `order_seed.tsv` copies were byte-identical and are replaced by `results/firstdet_final/order_seed20261109.tsv` (`ORDER_SEED_DEDUP.txt` lists them).

## What was run (protocol, from EVAL_MANIFEST)

**Purpose.** One fair number for the paper: how many fewer tests SimSpect needs than AMuLeT to find each previously known bug AMuLeT reports on the three defenses both tools cover (InvisiSpec UV1, CleanupSpec UV3/UV4/UV5, SpecLFB UV6), plus SimSpect's new jmp-shadow bug reported separately. The abstract uses the minimum over the five known bugs. STT is excluded.

1. **Model.** One model for all three defenses, `Footprint_6_u`: the footprint defense block (identical in InvisiSpec_6/CleanupSpec_6/SpecLFB_6) with FP-6's protection set on the ultimate skeleton. Contract = after an unresolved branch (STT_6's); protection set = memory + the initial value of every register the test never writes (`Mem_s + (Reg_s - Instruction.outreg.opstate)`), never released; leakage = load addresses only. The port is equivalent to the old-skeleton footprint block (0 counterexamples).
2. **Generation.** Stage 1: RI-minimal cores (`Footprint_6_u_core_ri.als`), all partitions exhausted: 1,411 cores, 363 distinct at the pin level. Stage 1.5: per core, the loose-pin model `Footprint_6_u_lpP.als` at `for 9 but 8 Instruction, 16 Operand, 6 Int` plus a path-style "contains core k" pin; seeded random SAT4J order (`a6RandomModels`, walk p 0.05, seeds 1, 2, … per core), core queue shuffled with seed 20261110, 25 instances / 300 s per job, adaptive per-core budget, cross-core fingerprint dedup; stopped at 25,116 distinct programs after 1,327 jobs. Stage 2 (recipe v3): `stage2_fv3` (fv2 vocabulary, value-neutral splices, FP routing, OTB off), then `make_rmw_corpus.py --select eligible` (p 0.5), then `make_jmp_corpus.py` (uniform placement, p 0.5). Corpus `Footprint_6_u_core_lpP_fv3`: 25,116 programs, 50,232 (stem, mode) tests, RMW 20,588 tests, jmp rows 25,352, 0 Stage-2 failures. Generation cost about 3.0 CPU-s per test.
3. **Runs.** AMuLeT's own gem5 arguments (parity configs) on the AMuLeT artifact builds: InvisiSpec-Futuristic (Ruby, L1D 32 kB/8, TBEs 256), CleanupSpec (Ruby, TBEs 256), SpecLFB (classic caches, BiModeBP). Per test: cache setup `random_all` (warm / cold / full, InvisiSpec warm / full), seed `simspect-cache-random-v1`. Timing: T*rt = per-branch random stalls (unresolved {2500, 5000, 10000}, resolved {0, 500, 2500}); **T*g = the final protocol**, one whole-test point drawn from the 3x3 grid of the same values (`pipeline._timing_grid_point`, seed `tgrid-v1`), so the old parity timing (5000, 0) is one of the nine points. One gem5 run per test, `TMPDIR=/tmp`, all transmitter kinds, the same seed-20261109 order for all three defenses. T2u5 = CleanupSpec on only the 690 UV5-shaped not_taken stems (50% old fixed timing, 50% random), a side run, not part of the main numbers.
4. **Classification.** `classify_hits.py --testset` (UV1 in-window `L1D:evict req=specld`; UV4/UV5/CS-1 via `cleanupspec_skip_evidence.py`; UV6/walk-order/jmp-shadow via `speclfb_analyze.py`), `classify_cs_rmw.py` (UV3 and E→M credited only to the test's own RMW). Exclusions that only lower SimSpect's counts: H-PAD padding hits, setup-block events under `full`. Unexplained hits are reported, never counted.
5. **AMuLeT baseline (T5).** AMuLeT's own fuzzer (c871bdf, `/opt/amulet-venv`), its YAMLs and `benchmark_all.sh` arguments with only gem5 paths changed, CT-SEQ, 32 instances × 200 programs × 140 inputs per defense on cafe1, against the same binaries. Every violation replayed and classified with AMuLeT's own analysers.
6. **Metric.** Per bug, SimSpect expected tests to first detection = (N+1)/(K+1); multiple = AMuLeT pooled test cases per violation ÷ SimSpect expected tests. Abstract number = minimum multiple over UV1, UV3, UV4, UV5, UV6.

## Replicating each step from scratch

All commands run inside the `gem5_dev` container (image `simspect_gem5_dev:20261109`) on a cafe node, with the base directory `B=/tests/simspect_alloy_20261108` (the scripts hard-code it; change it consistently if you use another). Use the frozen code roots from this snapshot, not the live Mac tree: copy `code/run_hosts/cafe1_loosepin_regen/code` to `$B/loosepin_regen/code` (and its `lp/` to `$B/loosepin_regen/lp`), and `code/run_hosts/cafe3_firstdet_final` to `$B/firstdet_final/code`, then put `alloy6.jar` (from the data tarball) at `STAGE1_alloy/alloy6.jar` and compile the enumerators (`javac -cp alloy6.jar a6CountModels.java a6RandomModels.java`).

### 0. Unpack the corpus (to reuse it instead of regenerating)

```bash
cd $B && tar -xzf footprint_vs_amulet_20261110_corpus.tar.gz
# -> testsets_twostage/Footprint_6_u_core_lpP_fv3/, loosepin_regen/{runs15/Footprint_6_u_lpPc,stage1,cores}/, loosepin_regen/code/STAGE1_alloy/alloy6.jar
```

### 1. Stage 1 → 1.5 → 2 (one command)

```bash
cd $B/loosepin_regen/code     # needs twostage_lp.py + STAGE1_alloy/models/{Footprint_6_u_core_ri,Footprint_6_u_lpP}.als (models/production/ here)
python3 twostage_lp.py --config runconfigs/twostage_lp/Footprint_6_u.jsonc --ws $B/twostage_lp_Footprint_6_u
# = make twostage-lp CONFIG=runconfigs/twostage_lp/Footprint_6_u.jsonc WS=...  (config: configs/twostage_lp/Footprint_6_u.jsonc)
# Log: <ws>/logs/twostage_lp.log
```

The production run itself (regen-lp, 2026-11-10) was done step by step with the same settings; `twostage_lp.py` packages those steps. As run:

```bash
# Stage 1 (RI cores, partitioned): partition_stage1.py + launch_stage1.py (STAGE1_alloy/models/proposed_twophase/), model models/production/Footprint_6_u_core_ri.als
#   -> $B/loosepin_regen/stage1/out/Footprint_6_u_core_ri/k{2,3}/stage1_xml  (in the data tarball, with stage1/status and logs)
# Stage 1.5 (core-pinned loose pin), from $B/loosepin_regen:
python3 lp/stage15lp.py --base models/Footprint_6_u_lpPc.als \
   --cores stage1/out/Footprint_6_u_core_ri/k2/stage1_xml stage1/out/Footprint_6_u_core_ri/k3/stage1_xml \
   --out runs15/Footprint_6_u_lpPc --code code --slots 40 --job-timeout 300 --budget-s 5400 --cap 25   # walk_p 0.05, spread 2, dedup seed, shuffle seed 20261110 (stage15lp.log START line)
# Stage 2 + RMW + jmp, streaming per batch, from $B/loosepin_regen:
python3 lp/stream_fp.py --s15 runs15/Footprint_6_u_lpPc --base-name Footprint_6_u_core_lpP_fv3_base --final-name Footprint_6_u_core_lpP_fv3 \
   --cfg code/runconfigs/regen_lp_20261110/stage2_fv3_stream.jsonc --code code --interval 150 --jobs 16
```

`models/Footprint_6_u_lpPc.als` (sha256 `6ad90dc5…`) = the production `Footprint_6_u_lpP.als` minus its 3-line header; `Footprint_6_u_core_ri.als` likewise (body sha256 `e99079eb…`). Each Stage-1.5 job's exact model is in `models/per_core_pinned_Footprint_6_u_lpPc_models.tar.gz` (`c000.als` … `c362.als`), its random order in `SOLVER_ORDER.json` per job (data tarball, `loosepin_regen/runs15/Footprint_6_u_lpPc/jobs/c*/s*/xml/`).

### 2. RMW and jmp post-passes (what `stream_fp.py` runs per batch)

```bash
python3 STAGE2_compilation/make_rmw_corpus.py --repo-root <code> --src <batch>/src --dst <batch>/rmw \
   --fraction 0.5 --seed 20261109 --select eligible --complete --jobs 16 --git-rev <rev>
python3 STAGE2_compilation/make_jmp_corpus.py --repo-root <code> --src <batch>/rmw --dst <batch>/jmp \
   --p 0.5 --seed 20261109 --jobs 16 --git-rev <rev>      # placement uniform is the default
```

Every draw is deterministic per (seed, stem) and recorded in each `.ann.json`; the result lists are `rmw_stems.tsv` and `jmp_stems.tsv` in the corpus.

### 3. First-detection runs

```bash
cd $B/firstdet_final/code     # = code/run_hosts/cafe3_firstdet_final
export TMPDIR=/tmp            # H-STK
# final protocol (T*g); T*rt is the default ROWS:
ROWS="T1g:invisispec T2g:cleanupspec T3g:speclfb" P_T1g=12 P_T2g=36 P_T3g=12 \
  X_T1g="--seed-prefix 4000" X_T3g="--seed-prefix 4000" \
  X_T2g="--partition 0/2 --priority-file $B/firstdet_final/uv5diag/priority_uv5.tsv" \
  bash STAGE3_gem5/timing/firstdet_final_launch.sh start
# second CleanupSpec consumer on cafe1: same command with HOST_TAG=cafe1, ONLY=T2g, X_T2g="--partition 1/2 ..."
# each row = python3 STAGE3_gem5/timing/firstdet_stream.py --code-root <code> --config runconfigs/firstdet_final_20261110/<row>_Footprint_6_u_core_lpP_fv3.jsonc \
#   --model Footprint_6_u_core_lpP_fv3 --out <dir> --seed 20261109 --parallel <P> --sample-frac 1 [extra] --poll 180
```

The order: the sorted (mode, stem) pairs shuffled with `random.Random(20261109)`, `results/firstdet_final/order_seed20261109.tsv` (sha256 `306ea984…`); `order_stream.tsv` in each run dir is the order actually executed while streaming (with `--seed-prefix` / `--priority-file`). The exact launches are in `results/firstdet_final/cafe3/launch.log` and `cafe1/launch.log`.

### 4. Classification and the comparison

```bash
ROWS="T1g:invisispec T2g:cleanupspec T3g:speclfb" bash STAGE3_gem5/timing/firstdet_final_launch.sh classify-once   # or classify-loop
# per row: firstdet_merge.py (split T2 rows) -> classify_hits.py <dir> --defense <d> --stage3 <code>/STAGE3_gem5 --testset <corpus> --incremental
#          -> classify_cs_rmw.py <dir> --rmw-stems <corpus>/rmw_stems.tsv --testset <corpus>   (CleanupSpec)
# comparison: python3 STAGE3_gem5/timing/firstdet_report.py --invisispec <T1 dir> --cleanupspec <T2 merged dir> --speclfb <T3 dir> \
#             --testset <corpus> [--rows all] --json report.json --md report.md
# figure:     python3 STAGE3_gem5/timing/make_firstdet_fig_v2.py report.json --tikz ~/trippel/ISCA-27/tikz
```

### 5. AMuLeT T5 and per-bug replay (cafe1)

```bash
T5=$B/timing/amulet_t5     # scripts = code/run_hosts/cafe1_amulet_t5; repo = AMuLeT c871bdf at $T5/amulet-repo; PATH=/opt/amulet-venv/bin:$PATH
python3 $T5/make_benchmark_t5.py ...                # writes benchmark_t5.py (measurement-only, asserted replacements)
for D in SpecLFB CleanupSpec InvisiSpec; do bash $T5/run_t5.sh $D 32 200 70; done     # = chain.sh; STT: run_t5.sh STT 60 200 70 14400
python3 $T5/summarize_t5.py <run>                   # -> t5_summary.json;  classify_t5.py (cwd amulet-repo/src) -> t5_classes.json
bash $T5/perbug/perbug_replay.sh 18                 # replay EVERY violation -> <run>/t5_classes_all.json
python3 $T5/perbug/perbug_t5.py $T5/perbug/out SpecLFB=<run> CleanupSpec=<run> InvisiSpec=<run>   # -> perbug_summary.json, violations_*.json
python3 $T5/perbug/cs_nonexclusive_t5.py ...        # -> cs_nonexclusive.json
```

Runs used: `SpecLFB_20261110T012205Z`, `CleanupSpec_20261110T013433Z` (the killed first attempt is kept as `FAILED_CleanupSpec_20261110T012934Z`), `InvisiSpec_20261110T015013Z`; `STT_20261110T023428Z` was still running (4 h cap, not part of the comparison).

## Results (complete run, final protocol)

From `results/firstdet_final/cafe3/report/final/complete.md` (classified 2026-11-10 14:50 UTC). Final protocol: AMuLeT's exact parity configs, per-test `random_all` cache setup and one whole-test timing point from the 3x3 grid. CleanupSpec = all 50,232 tests (exact); InvisiSpec and SpecLFB = first 4,000 of the seed order. AMuLeT = pooled test cases per violation (T5).

| bug | defense | K / N | SimSpect expected tests | first (seed order) | AMuLeT pooled test cases | multiple (tests) | multiple (CPU, incl. generation) |
|---|---|---|---|---|---|---|---|
| UV1 | InvisiSpec | 2,002 / 4,000 | 2.00 | 1 | 3,318 | 1,660× | 14.3× |
| UV3 | CleanupSpec | 1,861 / 50,232 | 27.0 | 11 | 3,794 | 141× | 0.42× |
| UV4 | CleanupSpec | 599 / 50,232 | 83.7 | 1 | 224,000 | 2,680× | 8.0× |
| UV5 | CleanupSpec | 4 / 50,232 | 10,047 (95% 4,900-46,100) | 7,430 | 224,000 | 22.3× (95% 4.9-46×) | 0.07× |
| UV6 | SpecLFB | 861 / 4,000 | 4.64 | 1 | 5,978 | 1,290× | 3.2× |
| jmp-shadow (new, separate) | SpecLFB | 555 / 4,000 | 7.20 | 19 | 19,040 | 2,650× | 6.6× |

- Minimum over the five known bugs: **22.3× in tests (UV5, exact, K = 4 in all 50,232)**; in CPU, AMuLeT is cheaper for UV3 (0.42×) and UV5 (0.07×).
- UV5 detections (all cold): inst-021207 and inst-007645, each in both branch modes (`results/firstdet_final/cafe3/report/final/uv5_final_stats.txt`).
- Figure: `ISCA-27/tikz/firstdet_bars_v2_body.tex` + `_standalone_firstdet_bars_v2-1.png` updated with these values (local, not committed).

### Same-estimator table (the paper's numbers; supersedes the "multiple (tests)" column above)

Diligence item DG-2 (EVAL_MANIFEST part 8): the table above pairs SimSpect's (N+1)/(K+1) with AMuLeT's N/K, which favours SimSpect by 1.25x at K = 4. The paper uses (N+1)/(K+1) on both sides, with AMuLeT N = 896,000 test cases (32 instances x 200 programs x 140 inputs) and K = AMuLeT's pooled detections of that bug (T5, `results/amulet_t5/perbug/out/perbug_summary.json`). Recomputed 2026-11-10 from the K/N counts above.

| bug | defense | SimSpect K / N | SimSpect expected tests | AMuLeT K / N | AMuLeT expected test cases | multiple (tests) |
|---|---|---|---|---|---|---|
| UV1 | InvisiSpec | 2,002 / 4,000 | 2.00 | 270 / 896,000 | 3,306 | 1,655× |
| UV3 | CleanupSpec | 1,861 / 50,232 | 26.98 | 236 / 896,000 | 3,781 | 140× |
| UV4 | CleanupSpec | 599 / 50,232 | 83.72 | 4 / 896,000 | 179,200 | 2,140× |
| UV5 | CleanupSpec | 4 / 50,232 | 10,046.6 | 4 / 896,000 | 179,200 | 17.8× |
| UV6 | SpecLFB | 861 / 4,000 | 4.64 | 150 / 896,000 | 5,934 | 1,278× |
| jmp-shadow (new, separate) | SpecLFB | 555 / 4,000 | 7.20 | 47 / 896,000 | 18,667 | 2,594× |

- Minimum over the five known bugs: **18× (UV5)**. 95% interval for the UV5 ratio counting both sides' uncertainty: 3.3-96× (exact conditional test on 4 vs 4); the 4 SimSpect hits are 2 programs, each in both branch modes.
- Figure as it stands in the paper clone (18× version, local and not pushed at the time of this note): `results/figure_final/` (`firstdet_bars_v2_body.tex`, `firstdet_bars_v2_8pt.tex`, `_standalone_firstdet_bars_v2.tex`, `_standalone_firstdet_bars_v2-1.png`). The pushed 23× version is ISCA-27 commit f8890bb.
- The CPU column above still uses AMuLeT's N/K; on dedicated nodes AMuLeT is cheaper in CPU for UV3 and UV5 either way (DG-1).

## Results (interim, at snapshot time)

SimSpect rows from `results/firstdet_final/cafe3/report/report_20261110T112346Z.md` (T*rt, per-branch random timing; seed-order prefix fully run and classified: InvisiSpec 1,352, CleanupSpec 13,456, SpecLFB 2,017 tests). AMuLeT column from T5 (pooled test cases per violation, `results/amulet_t5/perbug/out/perbug_summary.json`).

| bug | defense | K / N | SimSpect expected tests | first (seed order) | AMuLeT pooled test cases | multiple (tests) | multiple (CPU, incl. generation) |
|---|---|---|---|---|---|---|---|
| UV1 | InvisiSpec | 664 / 1,352 | 2.03 | 1 | 3,318 | 1,631× | 13.3× |
| UV3 | CleanupSpec | 514 / 13,456 | 26.1 | 11 | 3,794 | 145× | 0.42× |
| UV4 | CleanupSpec | 153 / 13,456 | 87.4 | 1 | 224,000 | 2,563× | 7.4× |
| UV5 | CleanupSpec | 1 / 13,456 | 6,728.5 | 7,430 | 224,000 | 33.3× | 0.10× |
| UV6 | SpecLFB | 413 / 2,017 | 4.87 | 1 | 5,978 | 1,226× | 2.9× |
| jmp-shadow (new, separate) | SpecLFB | 272 / 2,017 | 7.39 | 19 | 19,040 | 2,576× | 6.2× |

- Minimum over the five known bugs, interim: **33.3× in tests (UV5)**, 0.10× in CPU (UV5).
- UV5 side run T2u5 (690 UV5-shaped stems): 1 detection in 344 tests, inst-021207 (not_taken) at test 188 (`results/firstdet_final/cafe3/T2u5_Footprint_6_u_core_lpP_fv3_merged/first_detection.json`); traces in `results/example_traces/`.
- Final-protocol T*g at snapshot time (`results/firstdet_final/cafe3/report/T2g/report_20261110T112724Z.md`): UV1 60/117 (expected 1.93 tests), UV6 35/181 (5.06), jmp-shadow 25/181 (7.0); CleanupSpec not yet classified. **These are the rows the paper should use once finished** (see the TODO at the top).
- Figure: `results/figure_interim/_standalone_firstdet_bars_v2-1.png` (from the interim report; paper copy `ISCA-27/tikz/firstdet_bars_v2*`).
- Earlier interim (mixed corpora, before this run): minimum about 47× (UV5 on the old flat corpus), `results/interim/`.

## Code versions (run hosts vs Mac)

`code/VERSIONS.tsv` lists 79 pipeline files across the four host trees and the Mac. Findings: 66 identical everywhere they exist. 7 differ between host trees because each tree is the snapshot taken for its own stage (generation on cafe1 `loosepin_regen`, first detection on cafe3 `firstdet_final`); in every one of those the Mac copy equals the firstdet-final copy (`pipeline.py`, `testsetgen.py`, `gem5_common.py`, `cache_setup.py`, `classify_hits.py`, `firstdet_report.py`, `timing_driver.py`). `stream_fp.py` on the Mac was edited after the run (diff in `code/mac_vs_run_hosts.diff`; the as-run copy is `code/run_hosts/cafe1_loosepin_regen/lp/stream_fp.py`). Mac-only: `runconfigs/twostage_lp/Footprint_6_u.jsonc`, `relay_cafe3.sh`, `make_footprint_u.py`. Host-only: `benchmark_t5.py`, `analyse_ipc_violation_t5.py`, `chain_main.sh` (cafe1 T5). The corpus `PROVENANCE.json` `code_hashes` (parsexml, batch_generate, make_rmw_corpus, make_jmp_corpus, stage2_fv3.jsonc) all match the frozen `cafe1_loosepin_regen` copies. Excluded from the code copies: `results/`, `testsets_twostage` symlinks, `__pycache__`, `*.pyc`, `*.class`, `m5out`, AppleDouble `._*` files, `alloy6.jar` (in `data/`), and `STAGE3_gem5/triage/model_audit_20261108/` (38 MB of an unrelated audit).

## Corpus tarball

| item | value |
|---|---|
| file | `data/footprint_vs_amulet_20261110_corpus.tar.gz` (Mac, gitignored); identical copy on cafe1 `/tests/simspect_alloy_20261108/snapshots/footprint_vs_amulet_20261110_corpus.tar.gz` |
| size | 71,971,149 bytes (163,560 entries) |
| sha256 | `08effe5d29a95bfd4f4b7130817c8d434914fe2b3c02de7c51b57685af4b3032` |
| contents | `testsets_twostage/Footprint_6_u_core_lpP_fv3/` (`xml/` 25,116 instances + `.txt`, `mispredict_not_taken/` and `mispredict_taken/` `asm/*.s` + `ann/*.ann.json` (25,116 each), `MANIFEST.tsv`, `PROVENANCE.json`, `READY`, `rmw_stems.tsv`, `jmp_stems.tsv`); `loosepin_regen/runs15/Footprint_6_u_lpPc/` without the per-job `inst-*` files (which are the corpus `xml/` before renumbering) but with every job's `SOLVER_ORDER.json`, `_dedup_*.jsonl`, `_solver_order.log`, plus `cores.json`, `jobs.jsonl`, `SUMMARY.json`, `QUEUE_ORDER.json`, `MERGE_INPUTS.txt`, `stage15lp.log`, `models/`; `loosepin_regen/stage1/` (Stage-1 cores, partitions, status, logs); `loosepin_regen/cores/`; `alloy6.jar` |

Corpus index files (sha256): `MANIFEST.tsv` `c426306d0b3cc8551f58a9304d0ab3074d6170ae837f60d33fdeeea98fafb461`, `PROVENANCE.json` `2b177149e7667f0fa6bb25d461b88c7d8649b209deb790bbee1945ad4532dd62`, `rmw_stems.tsv` `a61415be9ff275607d73ee58af329321a62ffd213b253a8f54d6900001ca1116`, `jmp_stems.tsv` `81db579cead7c07c60c4f130bb9178a9987e4678746073aaf9112587d36c606c`.

## Hash manifest (key files; everything is in `SHA256SUMS`)

| file | sha256 |
|---|---|
| `models/production/Footprint_6_u_core_ri.als` | `99fc25f25c949c7ee3206cbbb231e1ab9ed53e6232549c488fceb784fcee5441` (body = run-host copy `e99079ebd7c4d32ccc5e1120e036b41241bf02d6a08db8236d251b958b3b41fc`) |
| `models/production/Footprint_6_u_lpP.als` | `0e3acd406943321efe7378da88d3e74b4414ce936994c0e8fabf2ed8a1cdd0b5` (body = run-host `Footprint_6_u_lpPc.als` `6ad90dc59c056986506c5142e488f27c99ae02aab273bea4d2b27520e902ebf0`) |
| `models/proposed_ultimate/Footprint_6_u.als` | `1719c3b61a655a3f9ae3c32dc8354063ccfba7046fbc6ef659f6ddb851efa423` (= run host) |
| `models/footprint_v2/InvisiSpec_6_v2.als` | `a4804dec47d818a5a8b58c420ca00629100743b3db6983e5a069ffffef7322ad` |
| `models/footprint_v2/CleanupSpec_6_v2.als` | `54febab754239e651aaa4e98e8cd933eaa174da3611bf831a6df043aa309556e` |
| `models/footprint_v2/SpecLFB_6_v2.als` | `27ae3955733fdf4e2bd913ed14b720de80b9c81ecf43972c315071872261292b` |
| `models/per_core_pinned_Footprint_6_u_lpPc_models.tar.gz` | `e8236b91ae338b2e332e860adf896c9a1c243969c613a6065468559ba22babda` |
| `configs/regen_lp_20261110/stage2_fv3_stream.jsonc` | `cf34f373864750532027370e45de6f31c8067ab6509a3c728932a7647d50a384` (= `PROVENANCE.json` `stage2_config_sha256`) |
| `results/firstdet_final/order_seed20261109.tsv` | `306ea984cc7981d3cf86404560f46fd7fa77d2323c1f96ef8870cafaa6f0aa5f` |
| `alloy6.jar` (in `data/`) | `6b8c1cb5bc93bedfc7c61435c4e1ab6e688a242dc702a394628d9a9801edb78d` |
| `data/footprint_vs_amulet_20261110_corpus.tar.gz` | `08effe5d29a95bfd4f4b7130817c8d434914fe2b3c02de7c51b57685af4b3032` |

Check with `shasum -a 256 -c SHA256SUMS` from this directory (the `data/` line fails on a clone without the tarball).

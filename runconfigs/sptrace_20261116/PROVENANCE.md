# SPT-specific VP/squash race run (agent sptrace, 2026-11-16)

Goal (Anna, 2026-11-16): run the race on SPT-Fence using tests generated from SPT's own current specification, `STAGE1_alloy/models/SPT_6_oneLP_v2.als` (sha256 `acb1f2e21e5e6c3b98e7dfd8eec71bc9d9282578303626655334768addb61e8d`), instead of the 24 June "a5" stems from the older SPT model. Node: cafe2, container `gem5_dev`, run dir `/tests/sptrace_20261116/` (a copy of this file sits there as `PROVENANCE.md`). Results: `wiki/state/EVAL_MANIFEST.md` "Race rows", claudelog 2026-11-16.

## Corpus: `SPT_6_oneLP_v2_flat_ld_s2Aspt` (4,964 programs × 2 branch modes)

- **Stage 1 (reused, no Alloy run, no model touched):** the flat enumeration of the unchanged `SPT_6_oneLP_v2.als` that agent singlestage-spt made on 2026-11-10 (`STAGE1_alloy/models/proposed/singlestage/SPT/RESULTS.json`, variant V0; cafe2 `/tests/singlestage_20261109/out/SPT/SPT_6_oneLP_v2/{default,1,2,3}`). Scope `for 9 but exactly 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool`, **cap 10,000 per seed**: the default order was CAPPED at 10,000 (1,186 s), and seeds 1/2/3 TIMED OUT at 1,500 s with 4,760 / 4,520 / 5,108. That is 24,388 instances, 16,313 distinct (census_flat fingerprint), with transmitters TLoad 4,964 / TBranchx 5,727 / TStore 5,622. **Not exhaustive.**
- **Why flat and not two-stage:** the SPT_6_oneLP_v2 Stage 1 cores exist (k3 546; k4 capped at 200,000), but Stage 1.5 needs a loose-pin `SPT_6_oneLP_v2_lpP.als`, and none exists. Only `SPT_6_u_lpPc.als` exists, which is built from a different base (SPT_6_u, DECIDE SPT-BOUND). Generating a new lp model is a model change, so I didn't do it. The flat corpus comes from the specification byte for byte.
- **Selection (deterministic, no sampling):** `scripts/sptrace_20261116/make_corpus.py` walks the runs in the order default,1,2,3 and the files in sorted order, dedups by `census_flat.fingerprint`, and keeps the first instance of every distinct program whose transmitter is a load. That gives 4,964 programs, which equals the census's TLoad count. Only load transmitters are kept because `race_scan.py` scores `ld` records only. The stems are renumbered `inst-000001…` in that order. `corpus_manifest.tsv` (sha256 `97a7b3ab49d3a824e5799e0027529d4357e46a1dcb4f5b48f3b195e228b268e7`) maps each stem to its source XML and the XML's sha256. Hash of all the XML concatenated in stem order: `1b9dbb42…2a61f54ca05d1e18695e785a32831`.
- **Stage 2:** recipe A, SPT variant = `runconfigs/sptrace_20261116/stage2_final_A_spt_SPT_6_oneLP_v2_flat_ld_s2Aspt.jsonc`. It is a copy of `runconfigs/overnight_20261111/stage2_final_A_spt.jsonc`, the config the SPT corpora use: splices off, table `instructions.jsonc` without the `spt_bwd_invertible` forms (DECIDE SPT-VOCAB), fillers, FPR routing, random reg naming seed 0. Only `testset_dir`, `results_name` and `jobs` changed. `testsetgen.py` ran with both branch modes; all 4,964 programs compiled in each mode with 0 errors (13:03-13:06Z). asm hashes (cat of all `.s`): not_taken `67e72586…`, taken `eb534453…`.

## gem5 runs (SPT-Fence)

- Build: `/work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt` (sha256 `dc6acb70…`), `se_exp.py` (sha256 `9bfddfe1…`; reads `SIMSPECT_COMMIT_IEW_DELAY`). Flags: `--scheme=SpectreSafeFence --applyDDIFT=1 --fwdUntaint=1 --bwdUntaint=1 --configImpFlow=Lazy --freeParam=3`, `DerivO3CPU`, BTB branch forcing on, fnc commit stall 0, `random_all` cache setup (64 kB fill), timing grid unresolved {2500, 5000, 10000} × resolved {0, 500, 2500} (seed tgrid-v1), unresolved stall 5000.
- Configs `runconfigs/sptrace_20261116/race_sptfence_d{1,3,4}_SPT_6_oneLP_v2_flat_ld_s2Aspt.jsonc` are copies of `runconfigs/bigcorpus_20261115/race_sptfence_d4_STT_6_u_core_lpP_s2A.jsonc`, the paper's SPT race config. Changed: the paths (testset and results), `sample_fraction` 0.1 → 1.0, `jobs`, and `race_knobs.commitToIEWDelay`.
- Harness: code snapshot = Mac HEAD 2738274 plus the working tree, 2026-11-16T13:02Z (`/tests/sptrace_20261116/code/SNAPSHOT.txt` holds the sha256s: check_ld `2640e5d6…`, gem5_common `3db80376…`, testrun `adb0e8ef…`, race_scan `b8ac6b12…`). testrun's fast path was on, the default since 2026-11-16 (equivalence-verified, EVAL_MANIFEST "Fast path adopted").
- Execution: the first 2,000 tests per mode ran as one testrun campaign per delay (`results/sptrace_fence_d{1,4}_<T>__latest`). The rest ran as disjoint stem shards (`scripts/sptrace_20261116/shard_run.py`; testrun is GIL-bound) with the same configs; only `results_name` and `jobs` changed. `merge.py` builds `results/sptrace_fence_d<d>_<T>_merged/` (0 duplicate stems; all 4,964 stems in each mode). Delay 3 ran sharded only.
- Safety (coordinator request 2026-11-16 15:45Z, /scr at 62-83 GB free): `guard.sh` checks every 60 s. Below 40 GB free it SIGSTOPs testrun/check_ld (pause), at 45 GB or more it resumes them, below 25 GB it stops the shards, and it kills any gem5 whose trace passes 3 GB. The d1/d4 shards ran with `SIMSPECT_GEM5_TIMEOUT_S=900`. The d3 shards ran with 300 s and `SIMSPECT_GEM5_MAX_TICK=2e9` (the longest legit test ends near 2.4e7 ticks). Three runaway d1/d4 gem5 runs (5-8 GB traces) were killed by hand at 15:45Z, and those tests count as errors.

## Scoring

`scripts/bigcorpus_20261115/race_scan.py` on the merged campaigns: strict `race`, `wp_obtained` (check_ld's data-obtained gate), and paired delay-induced = wp_obtained at delay d but not at delay 1 for the same stem and mode (both records status ok). Outputs: `/tests/sptrace_20261116/race/{d1_merged,d4_vs_d1_merged,d3_vs_d1_merged}.{json,txt}`, `FINAL.txt`.

UV6 confirmation (`scripts/sptrace_20261116/confirm_uv6.sh`): `diag_stt_vp_squash_race.py` reran gem5 on the first 40 not_taken delay-induced stems whose campaign record drew `warm`. Only warm draws can be rerun faithfully, because the diag builds binaries directly and gem5_common applies non-warm setups only in `process_one`. The rerun used the d4 config with `cache_setup` warm and the campaign's exact per-test stalls, materialised with `pipeline._enumerate_grid_for_corpus` / `_materialise_grid_run`. Then `STAGE3_gem5/bugs/classify.py race` scored the output, giving **40 / 40 `stt_vp_squash_race`** (UV6), every one with packet = resolve + 1,000 ticks and squash = packet + 1,000 ticks (`race/uv6_confirm_d4_stalled.json`). A first attempt without the stalls gave 34 `not_real_access` (window too short, so the load never executes) + 4 race + 2 timeouts (`race/uv6_confirm_d4.json`, superseded).

## Commands

```
# from the Mac
bash scripts/sptrace_20261116/launch.sh            # snapshot code -> cafe2, tmux sptrace: corpus + Stage 2 + first passes
# in gem5_dev on cafe2, code root /tests/sptrace_20261116/code
python3 scripts/sptrace_20261116/shard_run.py --delays 1,4 --k 14 --jobs 3
bash scripts/sptrace_20261116/chain.sh             # waits, merges, scans, then d3 shards (k 20, jobs 2), FINAL.txt
bash scripts/sptrace_20261116/guard.sh             # disk guard
bash scripts/sptrace_20261116/confirm_uv6.sh       # UV6 rerun sample + classify.py race
python3 scripts/sptrace_20261116/merge.py 1 4 3 && python3 scripts/bigcorpus_20261115/race_scan.py results/sptrace_fence_d4_SPT_6_oneLP_v2_flat_ld_s2Aspt_merged --control results/sptrace_fence_d1_SPT_6_oneLP_v2_flat_ld_s2Aspt_merged
```

Logs: `/tests/sptrace_20261116/logs/` (`main.log`, `s2.log`, `gem5_d{1,4}.out`, `shard_d*_sh*.log`, `chain.log`, `guard.log`, `diskwatch.log`, `confirm_uv6*.log`).

## Results

Final (2026-11-16 16:31Z; `race/FINAL.txt`). Counts per mode, not_taken / taken. 4,964 tests per mode at each delay. Records that were not status-ok (gem5 timeouts/runaways) are excluded from the ld count: none at delay 1, 8 / 26 at delay 4, 10 / 18 at delay 3.

| commitToIEWDelay | ld records | race (strict) | wp_obtained | paired delay-induced vs delay 1 |
|---|---|---|---|---|
| 1 (default) | 4,964 / 4,964 | 0 / 0 | 1,658 / 1,657 | — |
| 3 | 4,954 / 4,946 | 2,931 / 2,371 | 4,697 / 4,688 | **3,045 / 3,040** (0 / 0 the other way) |
| 4 | 4,956 / 4,938 | 2,992 / 2,428 | 4,758 / 4,750 | **3,106 / 3,101** (0 / 0 the other way) |

- **The race is generic on the SPT corpus.** At delay 3 or 4, about 62% of the tests become wrong-path loads that obtain their data and that do not do so at delay 1. Not one test goes the other way. In the strict signature the access lands 2 cycles after the guarding branch's observed resolution and 2 cycles before the LSQ squash (2,991 of 2,992 at delay 4 not_taken, 2,426 of 2,428 taken; the rest 3 cycles after the resolution and 1 cycle before the squash), the same 1-cycle-gap mechanism as UV6 on STT (rob_impl.hh:812).
- **Example (replaces the June a5 example):** `inst-000002` (source `SPT_6_oneLP_v2/default/inst-000005.xml`), not_taken, warm draw, timing point unresolved 5,000. pc0 is a forced-mispredict `jne` (0x401c4a), pc1 a load whose value is routed through xmm2 into `%r8`, and pc3 the transmitter `movq (%r10,%r8), %r15` on the wrong path. At delay 4: branch resolution (visible) 5,449,000, transmitter packet to cache 5,450,000, LSQ squash 5,451,000 (`reached_cache`). At delay 1 the same test's transmitter never executes. The diag rerun reproduces the same three ticks (`race/uv6_confirm_d4_stalled.json`).
- **Not explained here (open):** at delay 1, 1,658 / 1,657 wrong-path load transmitters obtain their data BEFORE the branch resolves (all 1,658 not_taken), and 1,379 / 1,290 records are check_ld in-window hits (809 `reached_cache`, 45 `store_forward`, 525 `never_executed` gated out, not_taken). This is the first run of the SPT_6_oneLP_v2 specification on gem5-spt. The manifest's E11 row expects such hits to classify as constant-derived transmitters (P3) or reads made public by unfed reads (P5), plus SPT's own untaint rules. None of them has been bucketed, so they are neither counted as bugs nor as artifacts. The paired race count excludes them by construction.


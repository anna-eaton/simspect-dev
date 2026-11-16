# Squash-race figure v4: trace of SPT test inst-000125 at commitToIEWDelay 4 (2026-11-16, inspector-v7-agent)

Data behind ISCA-27 `tikz/squashrace_v4_8pt.tex` (new file; v3 and the paper text untouched). v3 drew STT test inst-047231 from the old slowed-pipeline run (commitToIEWDelay 4, iewToCommitDelay 30, squashWidth 1). Under the final race settings (only commitToIEWDelay raised) that test's fnc retires before the packet, so it is not an Inspector hit (URGENT_TODO DECIDE PT-1), and no final-settings STT race run with traces exists (the big-corpus STT race rows were stopped on 2026-11-15, EVAL_MANIFEST "Race rows"). v4 therefore uses one of the 40 confirmed UV6 tests on SPT-Fence (claudelog 2026-11-16 17:30).

## Test and verdict

`SPT_6_oneLP_v2_flat_ld_s2Aspt` `inst-000125`, `mispredict_not_taken`. Program (`inst-000125.s`): pc0 a load (committed); pc1 = lc, an ALU chain on pc0's value ending in `rdx` (0x401c61); pc2 = fnc, the mispredicted branch `jne` (0x401c83, forced not taken, held 2,500 cycles by the campaign's timing draw); pc3 = xmit `movq (%rcx,%rdx), %rdi` (0x401c8a), whose address uses lc's result; two resolved branches after it. Chosen among the 40 because it has a committed lc, a plain-load transmitter (no RMW) and the shortest chain between branch and transmitter.

Rerun record (`record_inst-000125_spt_d4.json`): `stt_vp_squash_race`, `reached_cache`, branch resolve 4258500, packet 4259500, load squash 4260500, identical to the confirmation record in cafe2 `/tests/sptrace_20261116/race/uv6_confirm_d4_stalled.json`. Three more stems re-run the same way (inst-000002, inst-000004, inst-000012) also matched their confirmation records exactly (`raw/race_v4_bundle.tgz`).

Cycles (c = (tick - 2945500)/500, 0 = lc's fetch): lc fetch 0, decode 1, issue 11, retires 14 (window opens). fnc fetch 119 (forced prediction), decode 120, issue 124, hold from 125 (`BR:resolve_hold stall=2500`), hold released 2625, resolution visible 2626 (`BR:resolve_visible` and Commit `Squashing due to branch mispred PC:0x401c83`), retires 2640. xmit fetch 119 and decode 120 (no pipeview record: the squashed load's neighbours seq 611 and 613 share both ticks), LSQ insert 123, ready 124 (its last operand, `rcx`, completes), held by SPT until the branch resolves, released at 2626 (the cycle the resolution becomes visible; SPT's release itself is not printed), executes and sends its read packet at 2628 (`Executing load`, `successfully sent out packet(s) for inst [sn:612]`), data returns and the squash lands at 2630 (`Completing instruction [sn:612] access at addr 35c0`, `Load Instruction PC (0x401c8a...) squashed`): 4 cycles after Commit's squash, i.e. commitToIEWDelay.

SPT mechanism (gem5-spt `0d2be0f`, read 2026-11-16): `src/cpu/o3/lsq_unit_impl.hh:1144-1146` stalls a load with tainted arguments while it is not unsquashable; `src/cpu/o3/rob_impl.hh:557-561` makes an instruction unsquashable once `isPrevBrsResolved()` (the Spectre model, `isFuturistic` false for `SpectreSafeFence`, `cpu.cc:448-452`).

## How it was run

cafe2, container `gem5_dev`, workspace `/tests/race_v4_20261116` (`rerun_keep.sh` here; log `logs/rerun.log`). It re-runs stems exactly as `scripts/sptrace_20261116/confirm_uv6.sh` did: code tree `/tests/sptrace_20261116/code`, staged inputs `/tests/sptrace_20261116/uv6_stage` (read-only; each `.ann.json` carries the campaign's per-test stalls from `pipeline._enumerate_grid_for_corpus`/`_materialise_grid_run`), config `uv6_stage/diag_d4_warm.jsonc` (sha256 `219d1cae…7914b`) = `runconfigs/sptrace_20261116/race_sptfence_d4_SPT_6_oneLP_v2_flat_ld_s2Aspt.jsonc` with `cache_setup` warm, env `TMPDIR=/tmp SIMSPECT_COMMIT_IEW_DELAY=4 SIMSPECT_GEM5_TIMEOUT_S=900`. The only change is a copy of `diag_stt_vp_squash_race.py` (sha256 `db0cfb7e…37914b`) whose final `shutil.rmtree(wd)` records the workdir instead, and whose `REPO` points at the same code tree (diff in the log).

gem5: `/work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt` (md5 `89475abc2e19677f3fee9b2feedd5971`), `configs/example/se_exp.py`, `--cpu-type=DerivO3CPU --caches --scheme=2`, the BTB-force branch annotation, debug flags `O3PipeView,LSQUnit,Commit`, then `extra_args` `--applyDDIFT=1 --fwdUntaint=1 --bwdUntaint=1 --configImpFlow=Lazy --freeParam=3 --scheme=SpectreSafeFence`; `se_exp.py` sets `cpu.commitToIEWDelay` from `SIMSPECT_COMMIT_IEW_DELAY`. The kept `m5out/config.ini` shows `commitToIEWDelay=4`, `iewToCommitDelay=1`, `squashWidth=8` (the last two are gem5's defaults).

## Files

| File | sha256 |
|---|---|
| `pipeview_inst-000125_spt_d4.txt.gz` (32,510 lines; uncompressed sha256 `91761a56…613501a`) | `d10d39764d957f497465f4685547257147754b7e49bbcda52fb6c39b67dc9f6c` |
| `record_inst-000125_spt_d4.json` | `a6ab59f0558f55e7d2207be3ec2ba39a9abe07873235ac120c48dbdb361e78ee` |
| `inst-000125.s`, `inst-000125.ann.json` (the staged inputs, with the campaign stalls) | `b8e80be6…`, `0dbf3ced…` |
| `raw/race_inst-000125_zj4o8qm_.tgz` (whole kept workdir: binary, patched .s, `branch_ann_se.json`, `m5out/`) | `0ec80f498d6fb879556d03db17ff463d0f5a2e49723ab32a487c98d2ca22ebdb` |
| `raw/race_v4_inst-000125_results_logs.tgz` (node `out/`, `logs/rerun.log`, `rerun_keep.sh`, `diag_keep.py`) | `980de34a523f21d88e184eed8894b8fa533c7a87c3831abedb5aa3bb7bfa2af3` |
| `raw/race_v4_bundle.tgz` (the first rerun of inst-000002/000004/000012, with their workdirs and the confirmation JSON) | `64ef1bd1aa1545bcc4b79799a15e2d757dd67e81bafdf175bf218e5d8a38ffc1` |
| `rerun_keep.sh` | `051f6115bbbdf067f2b79ae818c1f5898685c62613e1a2108b7015bfad27f4d4` |

## Figure

ISCA-27 `tikz/squashrace_v4_8pt.tex`, `tikz/_standalone_squashrace_v4_8pt.tex`, `tikz/_standalone_squashrace_v4_8pt-1.png` (standalone 112.2pt tall). Labels `fig:racev2` and `fig:race`, as v3. To use it, change `\input{tikz/squashrace_v3_8pt}` in `sections/results.tex` (line 71 at ISCA-27 9f1c1e8) to `\input{tikz/squashrace_v4_8pt}`. The UV6 paragraph (`results.tex` line 70) still describes inst-047231 (cycles 77/79/81), so it needs new text with the figure; a proposed sentence is in the agent report and `paper_figures/FIGURES.md` "Squash-race figure v4".

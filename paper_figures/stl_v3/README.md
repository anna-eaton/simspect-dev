# Timeline figures v3/v5/v7c: run data (2026-11-16, agent figs-stl-race-v3)

Data behind three new ISCA-27 figure files (new files only; paper text, `\input` lines and every existing figure untouched; no git writes in either repo): `tikz/reconstl_v3_8pt.tex` (Fig. 7, UV2), `tikz/squashrace_v5_8pt.tex` (Fig. 10, UV6) and `tikz/checkerwindow_v7c_8pt.tex` (Fig. 5, Inspector), each with `_standalone_*.tex` and a 200 dpi `-1.png`. The style rules they follow are in `paper_figures/FIGURES.md` "Timeline figure style"; every drawn cycle is listed with its tick and trace line in each `.tex` header.

## Fig. 7 v3: ReCon-STT store-to-load forwarding (UV2)

**Test.** `STT_6_u_core_lpP_s2A` inst-014536, `mispredict_not_taken`. It is one of the 1,690 UV2 tests the paper counts for row E2w (ReCon's implementation of STT: `/work/gem5-recon-modded`, X86O3CPU, `--scheme=2`, warm cache, BTB-force branch annotation, 3x3 timing grid; config `runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc`): cafe3 `/tests/bigcorpus_20261115/e2w/buckets_per_stem.json` labels `mispredict_not_taken/ld/plain/inst-014536` "A2 STLF bypass" (GPR-twin evidence), the campaign record (`code/results/bc_E2w_STT_6_u_core_lpP_s2A_sh27__latest`) has `issued_in_window true`, and the campaign's recon_stlf evidence (`e2w/par/bc_E2w_..._sh27__latest.json`) has `STL_CHECK isTainted=1 isSpeculative=1`, forwarded, ready 2676500 < window end 5174000. inst-014912 (the v2 figure's test) comes from the 2026-06-02 `Recon_6` campaign and is not one of the 1,690 (the E2w corpus's inst-014912 is a different program and is not in the A2 bucket).

**Why this test.** `rank_uv2.py` (run on cafe3, read-only) ranks the 598 not_taken plain A2 tests by graph size; ten have five instructions (a committed load, store or ALU op, the branch, a load, the store, the transmitter load), each with the store's and the transmitter's address from the same producer. inst-014536 is the only one of those ten with no splice on any operand and one filler (`lea` before the branch); its program is: pc0 (lc) `movq (%r14,%rdx), %xmm3; pxor; por; movq %xmm7, %r14`; filler `leaq (%r14,%r14), %r15`; pc1 (fnc) `movq %r14,%rax; andq $0,%rax; orq $1,%rax; testq; jne` (forced not taken); pc2 `movq (%r14,%rdx), %r14` + route through `xmm6`; pc3 store `movq %r14, (%rdx,%r14)`; pc4 (xmit) `movq (%r14,%rdx), %rdi`. Execution graph (the Alloy instance `xml/inst-014536.{xml,txt}`): i0 Load (committed), i1 Branch_n (unresolved), i2 Load, i3 Store, i4 Load (xmit); every register operand is `Reg_s$0` (r0), every memory operand `Mem_s$0` (m0); ddi i2 m0 to r0 and i3 r0 to m0; rf i0 r0 to i1 and to i2's address; rf i2 r0 to i3's address and data and to i4's address; rf i3 m0 to i4's m0 (a store-to-load edge, which v2's graph did not have).

**Run.** `rerun_stl_v3.sh vec mispredict_not_taken inst-014536` on cafe3 in `gem5_dev` (2026-11-16 17:32 UTC; node copy `/tests/bigcorpus_20261115/e2w/rerun_stl_v3.sh`, output `/tests/bigcorpus_20261115/e2w/stl_v3/vec_not_taken_inst-014536/`, copied here as `run/vec_not_taken_inst-014536/`). It is a copy of the Fig. 8 agent's `rerun_otb_v5.sh` with only the output directory changed: the campaign's code snapshot (`/tests/bigcorpus_20261115/code`, 2026-11-15 21:44 UTC), the E2w row config with only `paths`, `keep_tmp`, `jobs`, `branch_modes` changed and the print-only debug flags Commit, DelayUnit, Rename, IEW added, `TMPDIR=/tmp` (so the work-dir path has the campaign's length, BUGS.md H-STK), `nice -n 19`, `pipeline.py gem5 --force`. The timing point is the campaign's own draw for the stem (`sweep/manifest.json`: branch pc1 held 5,000 cycles). Result: hit, `issued_in_window true`, `cache_fate store_forward`, `data_obtained true`, xmit issue 2675000 / complete 2675500, lc_retire 2628000, fnc_retire 5174500, branch `resolve_hold` 2673500 (stall 5000), `resolve_visible` 5174000, `load_squash_tick` 5174500 (record: `run/.../sweep/raw_results/20261116173207_grid0000_batch0001_check_ld.py.json`).

**Cycles drawn** (c = (tick − 2618500)/500, 0 = lc's fetch; from `run/.../pipeview.txt.gz`):

| Row | Event | Tick | Cycle | Trace line |
|---|---|---|---|---|
| i0 lc (seq 546, 0x401c19) | fetch | 2618500 | 0 | O3PipeView fetch |
| | retires (window opens) | 2628000 | 19 | O3PipeView retire |
| i1 fnc (wrip seq 563, 0x401c45) | fetch | 2670000 | 103 | O3PipeView fetch; `BR:predict_force taken=0` |
| | hold starts | 2673500 | 110 | `BR:resolve_hold stall=5000 fire=5173500` |
| | resolves | 5174000 | 5111 | `BR:resolve_visible`; Commit "Squashing due to branch mispred PC:0x401c45" |
| | retires | 5174500 | 5112 | O3PipeView retire |
| i3 store (seq 570, 0x401c5f) | fetch | 2670500 | 104 | O3PipeView fetch |
| | address and data in the store queue | 2675500 | 114 | "Executing store ... [sn:570]", "Doing write to store idx 261, addr 0x35c0" |
| | squashed | 5174500 | 5112 | "Store Instruction ... squashed, idx:262 [sn:570]" |
| i4 xmit (seq 571, 0x401c63) | fetch | 2670500 | 104 | O3PipeView fetch |
| | tainted, speculative; forwarded; completes | 2675500 | 114 | "Executing load ... [sn:571]", "STL_CHECK: load PC 0x401c63 isTainted=1 isSpeculative=1", "Forwarding from store idx 262 to load to addr 0x7fffffffe5c0", O3PipeView complete 2675500 |
| | squashed (window closes) | 5174500 | 5112 | "Load Instruction PC (0x401c63...) squashed, [sn:571]" |

Not drawn: xmit's writeback 2676000 and Commit "ready within ROB" 2676500 (the evidence's `ready_tick`). `STL_CHECK` is SimSpect's own debug print of ReCon's taint tracker (`cpu->taintTracker.isTaintedInst`, placed just before the store-queue search; `gem5-hooks/gem5-recon-modded/recon-modded_src.diff:339`), not a ReCon check; ReCon's taint check that holds a tainted load (`lsq_unit.cc:2095-2104`, `delayUnit.insertTaintedLoad`) sits on the cache path after the store-queue search, and a forwarded load returns before it (`lsq_unit.cc:2019-2031`, source read on cafe3 `/work/gem5-recon-modded/src/cpu/o3/lsq_unit.cc`). The figure and caption therefore say "ReCon's taint tracker", not "ReCon's check".

## Fig. 10 v5: visibility-point/squash race (UV6)

Same test and trace as v4 (`paper_figures/race_v4/`: SPT test `SPT_6_oneLP_v2_flat_ld_s2Aspt` inst-000125, SPT-Fence, `commitToIEWDelay` 4), redrawn in the new style, plus one rerun to replace v4's one inferred cycle (the release, which the v4 trace does not print).

**Reruns (cafe2 `gem5_dev`, `/tests/race_v5_20261116/`, logs and outputs copied to `race_v5/node/`).** Both restore v4's kept work dir (`race_v4/raw/race_inst-000125_zj4o8qm_.tgz`) at its original path, so the binary, `branch_ann_se.json` and argv (stack layout) are those of the v4 run, and run the exact command `gem5_common.run_gem5` built for it (cwd `/work/gem5-spt`, `SIMSPECT_COMMIT_IEW_DELAY=4`, `se_exp.py ... --scheme=2 --abs-max-tick=100000000000 --branch-ann-file=... --branch-ann-base=0x401020` + the config's `extra_args`), at `nice -n 19`.

1. `rerun_track.sh` added gem5-spt's own instruction tracking (`--trackInstsFile` with the transmitter's PC 0x401c8a; prints only). gem5 aborted at tick 3006500, when the tracked load entered the ROB: `regfile.hh:280: PhysRegFile::partialTaintVecAsInt: Assertion 'size + offs < taintVec.size()' failed` in `BaseDynInst::toString` (`race_v5/node/gem5_stderr.txt`). The trace matched v4 up to the abort. Not used.
2. `rerun_iq.sh` added the print-only debug flags IEW and IQ instead. `check_subsequence.py` confirms all 32,510 lines of the v4 trace appear unchanged and in the same order in the new 84,052-line trace (the extra lines come from IEW, IQ, IEW's LSQ prints and `global`), and `sim_ticks` is 4287000 in both, so the run is the same. (The script's built-in check reports "DIFFERS" only because its filter missed IEW's LSQ-named and `global` lines; read `check_subsequence.py`'s result.)

New trace lines for xmit (seq 612, 0x401c8a; cycle c = (tick − 2945500)/500): IQ "Issuing instruction ... [sn:612]" 3007500 = 124; IEW "Execute: Processing ... [sn:612]" and "Deferring load due to virtual fence." 3008000 = 125 (SPT's hold starts); IQ "(addReadyMemInst) Instruction is ready to issue" and "Issuing instruction ... [sn:612]" 4259000 = 2627 (released, one cycle after the branch's resolution becomes visible at 2626); "Executing load" + "successfully sent out packet(s)" 4259500 = 2628; "Completing instruction [sn:612] access at addr 35c0" + "Load Instruction ... squashed" 4260500 = 2630. v4 drew the hold from 124 (operands ready) and the release at 2626 (inferred); v5 draws the hold from 125 (deferred) to 2627 (released). All other cycles are v4's (lc fetch 0, retires 14; fnc fetch 119, hold 125, resolves 2626, retires 2640; xmit fetch 119 from its in-order neighbours seq 611/613).

## Fig. 5 v7c: Inspector

v7's test, run and trace (`paper_figures/inspector_v7/`), redrawn in the new style: no F/D/I ticks, one row of cycle numbers, every label on its mark or on a leader. Cycles: lc fetch 0, retires 20; fnc fetch 116, hold 124, resolves 2625, retires 2639; xmit fetch 231 (in-order neighbours), address ready 238 (held by STT from there), squash lands 2626. No rerun.

## Files

| File | sha256 |
|---|---|
| `rank_uv2.py` (candidate ranking, read-only) | `c1b864f23412d7fd721f919df437990fe886bd15a75fb6ae87ebb3089defd028` |
| `rerun_stl_v3.sh` | `ef253269d2ebe08a8481bd58b3124095dd025d4c1fa09cfae5b5309529322567` |
| `run/vec_not_taken_inst-014536/pipeview.txt.gz` (169,179 lines) | `3f87cd030f8c1c2d7c49de7e06b414e0532f34dac692bff5839962874fb9819a` |
| `run/vec_not_taken_inst-014536/workdir.tgz` (binary, patched .s, branch annotation, m5out) | `9aefd7029565801f5c9d24042c7c09c7171905b8669df4d691e51ab9ad5ae258` |
| `run/vec_not_taken_inst-014536/sha256s.txt` | every other run file, the gem5 binary (`44e14c11…`) and the corpus `.s`/`.ann.json` (identical to the staged copies) |
| `race_v5/rerun_track.sh` / `race_v5/rerun_iq.sh` | `732321b1c2f78664a5a7540d145fc9e00315a31f82d4d5252dd5d3173dfa4fca` / `99da5f3fe7dcd1ca608bf082f0281dd2d59501c6c28467fd4e044601799c77cd` |
| `race_v5/node/pipeview_v5_iq.txt.gz` (84,052 lines) | `f19849bf2fa97b3f0384a726111e1e73a5ee2dddd7a94a5ff399d0098b9dc855` |
| `race_v5/node/gem5_stderr.txt` (the tracking abort) | `509022e383473a768181ab2c83604932a09ccc0ae473ba95389bd05e0c2f7c3d` |
| `race_v5/check_subsequence.py` | faithfulness check, run as `python3 check_subsequence.py ../../race_v4/pipeview_inst-000125_spt_d4.txt.gz node/pipeview_v5_iq.txt.gz` (exit 0) |

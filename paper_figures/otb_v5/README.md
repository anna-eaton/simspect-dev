# Fig. 8 v5 (fig:otb): ReCon's oldest-taint bug on a generated test

Agent fig8-otb-v5, 2026-11-16. Replaces the hand-built test of `recon_otb_v4_8pt` with a real generated test from row E2w (ReCon's implementation of STT, `gem5-recon-modded`, scheme 2, warm cache, 3x3 timing grid, corpus `STT_6_u_core_lpP_s2A`). Paper files (new, nothing overwritten): ISCA-27 `tikz/recon_otb_v5_8pt.tex`, `tikz/_standalone_recon_otb_v5_8pt.tex`, `tikz/_standalone_recon_otb_v5_8pt-1.png` (200 dpi). `paper_page9_crop300.png` is the figure as it renders on page 9 of a scratch build of the paper with v5 swapped in.

## Test chosen and why

Figure test: **inst-003908, integer version (`STT_6_u_core_lpP_s2A_gprtwin`), mispredict_not_taken**, timing-grid point unresolved 2500 / resolved 500 (`pipeline.py:_timing_grid_point`, sha256("tgrid-v1:inst-003908") mod 9 = 1; the campaign's sweep record and every rerun show stalls {pc2: 500, pc4: 2500}). The campaign scored it a hit in both modes and both versions (corpus shard `bc_E2w_STT_6_u_core_lpP_s2A_sh19`, integer shard `..._gprtwin_sh9`, all `issued_in_window` true). The integer version is drawn because it is the one `rsa8_trace.py` confirmed (the R-SA-8 bucket needs the integer twin's hit) and it has fewer instructions; the vector version (the corpus test) reproduces with the same key ticks (release 2978500, transmitter resolve 2980000, window-branch fire 3979000) and the same merge (seq 687 `mov rax, rax, rsi`).

The brief preferred one of the 3 signature tests that `movmerge_check.py` found without a mov false dependency. Neither turned out to be one:

- **inst-003908 does use the mov false dependency.** The merge is gem5's `MOV_R_R` micro-op `mov rax, rax, rsi` for `movq %rsi, %rax` at 0x401cf9 (the first instruction of i7's block), which lists the old rax as a source. The old rax is i5's quotient, and i5 carries i3's taint because gem5's `CQO_R_R` micro-op `mov rdx, rdx, rax` lists the old rdx (i3's load result) as a source. `taint_replay_min.py` (gem5-recon's rename-time rule, `rename.cc:714-720`, `taint_tracker.cc:108-131`) shows the two roots meet only at seq 679: OLDEST keeps 611 (i3), UNION = {611, 677}. `movmerge_check.py` missed it because its static slice ignores implicit operands (it treats `idivq %rcx` as writing rcx and `cqto` as writing rdx without reading it).
- **not_taken inst-013804 is not a clean R-SA-8 trace.** Its transmitter (seq 54, 0x401080) never enters the delay unit; the release line `rsa8_trace.py` counted (tick 155000) belongs to the window branch (seq 46, inserted at 135000). The vector version has no delay-unit insertion at all. Its grid point is (10000, 0).

So the figure uses a mov-dependency test, as the brief allowed. inst-003908 was kept over the 19 statically flagged ones because it is the one Anna's brief named, it reproduces in both modes and both versions, and its transmitter is visibly inserted into the delay unit and released one cycle after the older load's branch resolves (shape A). Checked alternatives (integer, not_taken): inst-001710 (shape A; its lc is an RMW, and the older taint enters at `xorq $85, %rax`, whose gem5 micro-op also reads the flags the RMW's chain wrote: replay merge at seq 587, roots 566 and 585), inst-004774 (shape A; merge not traced), inst-005443 (shape A at resolved delay 0; the older source is lc itself, no resolved branch in the body), inst-000366 (transmitter never in the delay unit, like inst-013804).

## Key cycles (cycle 0 = lc's fetch, tick 2724500; cycle = (tick - 2724500)/500)

From `extract_cycles.py runs/int_not_taken_inst-003908` (full list with the trace line of each event: `cycles_int_not_taken_inst-003908.json`). Graph roles from `test/inst-003908.xml` (i<k> = pc<k>).

| Instruction | Event | Cycle |
|---|---|---|
| i2 Branch_n (`jae`, 0x401c85, guards i3) | fetch / resolve held (500) / resolves (correct) / retires | -1 / 6 / 507 / 508 |
| i3 Load = lc (`movq (%r13,%rsi), %rdx`, 0x401c8f), older source | fetch / load request sent / completes / retires (window opens) | 0 / 6 / 8 / 508 |
| i4 Branch_x = fnc (`jne`, 0x401ca6), forced mispredict | fetch / resolve held (2500) / Commit squash (resolves) / squash lands, retires (window closes) | 1 / 9 / 2510 / 2511 |
| i5 Other_x (`cqto` 0x401cd6: `mov rdx, rdx, rax`) | renamed (takes i3's taint through rdx) | 108 |
| i6 Load (`movq (%r13,%rsi), %rsi`, 0x401cf1), younger source | fetch / issue / load request sent / completes / squashed | 110 / 125 / 126 / 128 / 2511 |
| i7 merge (`movq %rsi, %rax`, 0x401cf9) | fetch / renamed (oldest taint = i3) / executes | 111 / 121 / 131 |
| i7 Branch_x = xmit (`jb`, 0x401d00) | fetch / enters delay unit (tainted) / released / issues / mispredict detected, redirects fetch / Commit squash | 213 / 216 / 508 / 509 / 510 / 511 |

Both loads read address 0x35c0 (LSQ `ReadResp [35c0:35c7]`).

## Signature and gate

- **R-SA-8 signature** (`rsa8_check.py` = `rsa8_trace.py`'s rule): true in all three 003908 reruns, with the campaign's ticks (release 2978500 < transmitter mispredict resolve 2980000 < window-branch fire 3979000). Stricter than `rsa8_trace.py`: the transmitter itself (seq 684) is inserted ("Inserting branch [sn:684] into delay_unit as it has tainted operands", 2832500), it executes at 2979500, right after the release at 2978500, and its taint root is i3 (the replay above).
- **Gate.** The data-obtained gate (`check_ld._xmit_cache_fate`) applies to load transmitters only; a br_x record has no `data_obtained` and stays ungated (`STAGE3_gem5/bugs/disq_data_obtained.py`). The branch analogue holds: i6 obtained its data (request sent at 126, complete at 128), and i7 computed its outcome from it and redirected fetch at 510 ("Branch mispredict detected ... Redirecting fetch") inside the window (lc retire 508, squash lands 2511). check_br record (`runs/int_not_taken_inst-003908/res/rr/mispredict_not_taken/sweep/raw_results/*.json`): `issued_in_window` true, every criterion true (`lc_retired`, `signal_seen`, `branch_redirected`, `after_lc`, `before_fnc`, `branches_unresolved`, `resolved_correct`, `window_opened`, `stall_applied`, `force_applied`). With Commit tracing on, its signal is the Commit squash (2980000, cycle 511); the campaign ran without Commit tracing, so its signal was the complete tick (2979500, cycle 510). Both are inside the window.

## Commands

Reruns (inside cafe3 `gem5_dev`, one test at a time, nice 19, ~5 s each; full outputs also under `cafe3:/tests/bigcorpus_20261115/e2w/otb_v5/`):

```
/tests/bigcorpus_20261115/e2w/rerun_otb_v5.sh int mispredict_not_taken inst-003908   # = rerun_otb_v5.sh here
/tests/bigcorpus_20261115/e2w/rerun_otb_v5.sh vec mispredict_not_taken inst-003908
/tests/bigcorpus_20261115/e2w/rerun_otb_v5.sh int mispredict_taken     inst-003908
```

The script copies the test, writes `cfg.json` from `runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc` changing only paths, `keep_tmp`, `jobs`, `branch_modes` and adding the print-only debug flags Commit, DelayUnit, Rename (as `rsa8_trace.py`) and IEW, runs `pipeline.py gem5` with `TMPDIR=/tmp` (the campaign's, so the work-dir path length matches, H-STK), keeps `pipeview.txt.gz`, `config.ini`, `stats.txt`, the branch-annotation files and `res/`, logs start/end/rc in `run.log`, and writes `sha256s.txt` (incl. `gem5.opt` 44e14c11..., `se.py` 052281d5...).

Analysis (Mac, from this directory): `python3 rsa8_check.py runs/<run>`; `python3 extract_cycles.py runs/int_not_taken_inst-003908 --json cycles_int_not_taken_inst-003908.json`; `python3 taint_replay_min.py runs/int_not_taken_inst-003908/pipeview.txt.gz 600 684 611 677`; `python3 dataflow_trace.py <pipeview.txt.gz> 684 9`; `python3 pv_table.py <pipeview.txt.gz> 2724500 600 700`.

## Runs kept here

`runs/int_not_taken_inst-003908` (figure), `runs/int_taken_inst-003908`, `runs/vec_not_taken_inst-003908`, `runs/{int,vec}_not_taken_inst-013804` with full traces; `runs/int_not_taken_inst-{000366,001710,004774,005443}` with `pipeview_excerpt.txt.gz` only (hook, delay-unit and LSQ lines; full traces on cafe3). Each run has its `sha256s.txt` (computed in the container on the full trace). sha256 here: `runs/int_not_taken_inst-003908/pipeview.txt.gz` 4c3ad53d81a19ad9960e37e0d73811a6b669ce4df96451afc16ab05339a9b56d, `runs/vec_not_taken_inst-003908/pipeview.txt.gz` 31a1a5d612c0baf4549d70c0d422ca8b8d21762a7119a08df51157f6c5ce1881, `runs/int_taken_inst-003908/pipeview.txt.gz` d42dc13dfa445657308856c50d41d480c55160ea67f099dd7ecbdbfbfe78303b, `test/inst-003908.xml` e6988a00545afcbeaf5cf19b543a3eb90128c65ddc014a7fb6bdad3d189e8cff.

## Findings for the E2w UV3 count (not fixed here; DECIDE in URGENT_TODO)

1. `movmerge_check.py` undercounts the mov false dependency: inst-003908 (both modes) gets its older operand through gem5's `cqto` and `mov` micro-ops reading their destination registers, so at least 21 of the 22 signature keys use it, not 19.
2. `rsa8_trace.py`'s verdict does not check that the inserted and released branch is the transmitter. In 5 of the 22 signature keys (inst-000366 and inst-008487 in both modes, not_taken inst-013804) the transmitter never enters the delay unit and the counted release is the window branch's. They may still be R-SA-8 of shape B (oldest taint already freed when the transmitter reaches the IQ, as on the store-shadow row), but this trace does not show it; 17 keys have the transmitter inserted.
3. Release without a swept delay: inst-005443 (grid resolved = 0) is shape A with no resolved branch in its body (its older source is lc), so "option 2 occurs only at sweep points that delay i0's resolution" (resolutiontiming caption) does not hold for E2w.

## UV3-EVID check (decided (c) by Anna, 2026-11-16: the paper reports 17)

The 17 keys (integer versions; transmitter inserted into the delay unit and released in each): mispredict_not_taken inst-001710, -003901, -003908, -004774, -005443, -007681, -011455, -014667, -015158; mispredict_taken inst-001710, -003901, -003908, -004774, -007681, -011455, -014667, -015158. Reruns: `runs/batch_uv3evid.log` (12 new; cafe3 keeps full traces under `/tests/bigcorpus_20261115/e2w/otb_v5/`, here only `pipeview_excerpt.txt.gz` for the new ones). One rerun (taken inst-001710) collided with a concurrent inttwin run of the same stem in /tmp; the script refused it, and its trace was recovered from the one work dir left (the other run's dir was already deleted by its owner; noted in that run's `run.log`).

`uv3_shadow_replay.py <run dirs> --json uv3_17_replay.json` replays gem5-recon's speculation (decode-time shadows of unresolved conditional branches and stores with unknown addresses) and taint rules, names the transmitter's root O, predicts its release tick (equal to the trace's "Released tainted branch" tick in all 17), and checks static reachability of O under four models: GEM5 (every renamed source), NOMOV (minus a full-width `mov D, D, S` reading D, which covers `cqto`'s first micro-op), NOCC (minus flags reads that real x86 does not make: an ALU/test result never depends on the old flags, and old flags carry over only for INC/DEC/rotates/BT*/CMC/CLC/STC/SAHF), REAL (both). Result: O reaches the transmitter under REAL in none of the 17. A `mov`/`cqto` destination read is on every path in 12 (inst-003901, -003908, -007681, -011455, -014667 in both modes; inst-004774 in both modes, which also needs a flags read on every path). A flags read alone is on every path in 4 (inst-001710 and inst-015158, both modes; their lc is an RMW `orq $0, (mem)`; for inst-001710 the first merge is `xorq $85, %rax` at 0x401c94, which reads the old flags). not_taken inst-005443 has paths of both kinds. The earlier `older_root_paths.py` seeded every load as speculative and is superseded by `uv3_shadow_replay.py`.

## Fig. 8 v6 (shared timeline style)

ISCA-27 `tikz/recon_otb_v6_8pt.tex` + `_standalone_recon_otb_v6_8pt.tex` + `-1.png` (new files; v5 untouched): v5's data in the style of `paper_figures/FIGURES.md` "Timeline figure style" (macros copied from `squashrace_v5_8pt`): no F letters (each bar starts with a closing tick at its fetch cycle), every label on a leader from its mark, 12 pt per cycle, one row of cycle numbers. To fit one column, 507 and 2511 keep their marks and axis ticks but carry no number (their neighbours 508 and 2510 are numbered), and v5's "Reads cache" mark on i6 (cycle 126) is dropped; everything else is unchanged. The two "Squashed" labels hang from the cross's left arm so they stay inside the window. Scratch paper build with v6 swapped in: 19 pages, Fig. 8 on p. 9, Related Work on p. 13, the same four overfull warnings as with v5; `paper_page9_crop300_v6.png`.

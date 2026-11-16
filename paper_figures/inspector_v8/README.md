# Running example in integer form: Figs. 4 and 5 v8/v9 data (2026-11-16, agent stt-int-fig)

Data behind ISCA-27 `tikz/concretization_example_v2_8pt.tex` (Fig. 4), `tikz/checkerwindow_v8_8pt.tex` / `v8b` (Fig. 5, committed by the coordinator in ISCA-27 59cd83e) and their timeline-style successors `tikz/checkerwindow_v9_8pt.tex` (STT, no hit) / `v9b` (undefended Unsafe build, hit). Every drawn cycle is listed with its tick in each `.tex` header.

## Which test, and why the integer version was built here

The running example is `inst-023734` of corpus **`STT_6_u_core_lpP_fv3`** (recipe v3, parsexml `6e5c5238`, Stage-1.5 seed 20261113; `paper_figures/fig2_concretization_example.md` §7), mode `mispredict_not_taken`. It is **not** a test of the big corpus `STT_6_u_core_lpP_s2A`: s2A has stems `inst-000001`..`inst-015184` only, and no s2A program has this program's Stage-1.5 fingerprint (`alloy_solver_order.make_fingerprinter` over all 15,184 s2A XMLs, 0 matches; fingerprint `bd5b1737…`). So the inttwin corpus `STT_6_u_core_lpP_s2Aint` has no twin of it, and the integer version was built here with the inttwin rule: the corpus's own Stage-2 code and recipe with ONLY `fpr.enabled` false.

**Stage 2 (cafe3, `run_inspv8.sh s2`).** Code `/tests/simspect_alloy_20261108/loosepin_regen/code_eval` (parsexml `6e5c5238`, batch_generate `3fc8a94f` = the code_hashes of the corpus PROVENANCE.json), recipe `runconfigs/regen_lp_20261110/stage2_fv3.jsonc` (sha256 `1c24c5e8…`), `pipeline.py llvm` + `asm`, both modes. Neither fv3 post-pass touches this stem (not in `rmw_stems.tsv` / `jmp_stems.tsv`).

- With FPR on, the rebuild reproduces the corpus `.s` and `.ann.json` byte for byte in both modes (`d07ec290…b4b1978`, `d62b1a50…51ec28` for not_taken), so the build path is faithful.
- With FPR off (the integer version): `scripts/inttwin_20261116/pairdiff.py` → 2 pairs, `route_only` 2, bad 0, route blocks 4 = `ann.fpr.routes` 4, ann differences 0. The only `.s` differences are the two route blocks: after pc0 `movq %r15,%xmm0; movq $0,%r15; movq %xmm0,%r15`, after pc2 `movq %r8,%xmm11; pxor %xmm5,%xmm5; por %xmm11,%xmm5; movq $0,%r8; movq %xmm5,%r8`. The integer version contains **no xmm register at all** (fv3's filler table has no SSE fillers, so there is no dead xmm14/xmm15 filler either). Integer `.s` (not_taken) sha256 `c18d9148…f1c6`, `.ann.json` `bc5d6ccd…c2`.

## Verdicts and cycles (mode mispredict_not_taken)

Config: `runconfigs/inttwin_20261116/E3_STT_6_u_core_lpP_s2A_int.jsonc` (the reported E3 config, int version) with only `paths.*`, `pipeline.keep_tmp: true`, `branch_modes: [mispredict_not_taken]` and `gem5.jobs: 1` changed; the undefended baseline swaps `gem5.binary`, `config_script`, `cpu_type`, `scheme` to E1's (`runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc`), as v7b did. Timing draw for this stem: (unresolved 2500, resolved 500); the test has no resolved branch, so the branch is held 2,500 cycles. Cache setup `random_all` draws **warm** for this stem on both builds (seed `simspect-cache-random-v1`). Cycle = (tick − lc fetch tick)/500.

| Run | Verdict | Cycles (0 = lc fetch) |
|---|---|---|
| E3 STT, integer (`/work/stt-master` md5 `1fed10b5…`, scheme 2) | **no hit**: `issued_in_window false`, `cache_fate never_executed` | lc fetch 0, issue 15, retires 20 (window opens); fnc (JNB wrip, seq 571) fetch 115, issue 121, hold 122 (stall 2500, fire 2622), resolves 2623, retires 2637; xmit (seq 580, no pipeview record) fetch 116 (neighbours 579/581), LSQ insert 120, address ready 127 (seq 579 completes), never executes, squash lands 2624 |
| E1 Unsafe, integer (`/work/gem5-recon-modded` md5 `762efbc6…`, scheme 0) | **hit**: `issued_in_window true`, `data_obtained true` | lc fetch 0, issue 14, retires 19; fnc (seq 564) fetch 103, issue 108, hold 109 (fire 2609), resolves 2610, retires 2611; xmit (seq 573) fetch 104, issue 115, cache access 116 (`Memory request (pkt: ReadResp [35c0:35c7]) … was sent`, `#stores occupied: 0`), complete 118, squash lands 2611 |
| E3 STT, vector (control) | no hit, `never_executed` | identical to v7's record and trace (pipeview sha256 `535f22be…bbb983d`, 31,036 lines) |
| E1 Unsafe, vector (control) | hit | identical to v7b's record and trace (pipeview sha256 `67c0fc14…bb5b215`, 27,039 lines) |

check_ld labels the E1 transmitter `store_forward` in both versions, but the trace shows a cache read with an empty store queue: the known Recon-build gate mislabel (`wiki/findings/bug/recon_cache_reach_gate/README.md`); the verdict is unaffected and the figures draw a cache access.

**Integer vs vector beyond the routes.** The programs and annotations differ only in the route lines. The runs give the same verdicts with the same cache setup and timing draw; the cycles shift because the route lines move code: in the integer version xmit (0x401c5f) sits on the same 64-byte line as the branch (0x401c41), and is fetched one cycle after it (116 vs 115), while in the vector version xmit (0x401c8a) is on the next line and is fetched at 231 (branch at 116). lc's ticks are identical in both (retires 2898500 on STT, 2628000 on Unsafe).

## Figures

- `concretization_example_v2_8pt.tex` (Fig. 4): integer `.s` lines 299, 318–319, 326, 334, 343 verbatim; `...` = fillers 301–307, branch-condition setup 313–315, base reload 322, lea splice 329, add/sub splice 337–338. Committed in 59cd83e.
- `checkerwindow_v8_8pt.tex` / `v8b` (committed in 59cd83e): first drawing; it does not meet the "Timeline figure style" in `paper_figures/FIGURES.md` (written by figs-stl-race-v3 while v8 was drawn): it has F letter ticks without dots and the "2,500-cycle hold" label sits under "Resolves".
- `checkerwindow_v9_8pt.tex` / `v9b` (new, generated by `make_v9.py`, macro block copied from `checkerwindow_v7c_8pt.tex`): same data in that style (12pt per cycle, one row of numbers, labels beside their mark or on vertical leaders, hold label under the fnc bar, no F/D/I ticks). Standalone height 108.9pt (v8 105.5pt, v7 112.0pt). `textgap.py` finds no two text lines closer than 1.5pt. Scratch paper builds (ISCA-27 59cd83e worktree with the `\input` swapped to v9, then v9b): 19 pages as HEAD, the same 4 overfull-box warnings as HEAD, Fig. 4 on p. 6 and Fig. 5 on p. 7 as HEAD, Related Work still starts on p. 13; p. 7's right column ends one line earlier than with v8. Checked at 150 and 300 dpi.

## How it was run

Node cafe3, container `gem5_dev`, workspace `/tests/inspector_v8_20261116` (`run_inspv8.sh code|s2|gem5`, log `logs/run.log`, all at nice 19, one process at a time; Stage 2 2026-11-16 17:42:18–21Z, the four gem5 runs 17:42:28–32Z). gem5 code = a copy of `/tests/inttwin_20261116/code` (gem5_common `9f67f809`, the code that scored E3_int; no resolved gate), run through `pipeline.py gem5` (what `testrun.py` runs per batch) with `run_queue.py`'s env (`TMPDIR=/tmp`, `SIMSPECT_GEM5_TIMEOUT_S=900`, `SIMSPECT_GEM5_MAX_TICK=2e9`). The kept workdirs are `/tmp/gem5_inst-023734_{o7keazxe (E3 int), jhw45s9y (E1 int), 6mbvwf35 (E3 vec), 40xcdwmt (E1 vec)}` on cafe3.

## Files

| File | sha256 |
|---|---|
| `pipeview_E3_int.txt.gz` (31,548 lines; uncompressed `4f582cea…ba1a3413`) | `acdfb525a70e2fb8eec003418d06a6ba0e7e956a8a8f37970e8dc8c2a5309b96` |
| `pipeview_E1_int.txt.gz` (27,263 lines; uncompressed `078c9c58…1e55c5c5`) | `aaa04a71ff54603253a9d4b8e7a7d7232e5cb7cffece59b070853e4f23476228` |
| `record_E3_int.json` / `record_E1_int.json` (check_ld records from `sweep/raw_results/`) | `0bef139c2c04b8e45f2e55e12ee2d40905d670a87b394cee176d3c5bbad57ca7` / `44399223ebb5a030db2a4d6a749cafdbbc506e08f6ec407c07ba743c9ba426e1` |
| `record_E3_vec.json` / `record_E1_vec.json` | `9e664644264d50bb7776c8011e54f17ffffd47c6492593588f660b0e58fa3f84` / `19998637579c9d070e7bef2866e2ff321a960ae954ea7e302dd5b088381c436a` |
| `raw/E3_int_gem5_inst-023734_o7keazxe.tgz` (whole kept workdir: binary, patched `.s`, `branch_ann_se.json`, `force_plan.json`, `m5out/`) | `1a590465f1429d74439355c9d93a5395ac16d78c83188f3d1890a64a4e22e729` |
| `raw/E1_int_gem5_inst-023734_jhw45s9y.tgz` | `b8602d1166fa756dafa71258952b7ad43381c3594213ef0d076a556047ac45b7` |
| `raw/results_configs_logs.tgz` (node `configs/`, `logs/`, `results/`, `s2check/pairdiff.json`, `run_inspv8.sh`) | `962b17e0a11a7b3f91d2e1275cc7b2a3cc4c45c44d9b645150b8e61554ef6077` |
| `raw/testsets_int_vec.tgz` (both versions, both modes: xml, `.ll`, `.s`, `.ann.json`) | `4e48805e1e4bfdf1cc915e0ab92d0a96652ef6e0670a33e72e6c6c828a82d17a` |
| `run_inspv8.sh` (the node script) | `95a08cc2c11941c639134cc7bd5746d5bcdd8144cf3a400e57a66da21ade6b73` |
| `events.py` (prints every drawn event from a trace: `events.py <pipeview> <lc_pc> <fnc_pc> <xmit_pc>`) | `cbb4faa6860c72ce82008410ead8e298cc0c3f4d1351a04aa17337feb1556cd9` |
| `textgap.py` (text-line gap check on a PDF page) | `56a0d6eaec26feda71b63bd4e6d534cee7a7de3c6c3782d01301bf7df830f8d4` |
| `make_v9.py` (writes v9/v9b; refuses to overwrite) | `3e6580a5dda9b28ba869be3ffb1c9708cb8878a537ca5af7ca430c350e2976f2` |
| `build_preview.sh` (standalone → 200 dpi `-1.png`) | `5109887295e2b81461fad2d95874c1b88d1bb5a1688ff964581c9312a4b6e2c8` |
| ISCA-27 `tikz/concretization_example_v2_8pt.tex` | `2c618d5ff85230b15c31b653dc525496ea048dc32e4c78a759688b3564393a5c` |
| ISCA-27 `tikz/checkerwindow_v8_8pt.tex` / `v8b` | `a2146057be0eb800402079cb2c6afac0c0e6e1898dbc7300d60b586ebae3fe96` / `381823dab34d18876a65420aa31b3de36f6e1ed46dea942a396525641d67f790` |
| ISCA-27 `tikz/checkerwindow_v9_8pt.tex` / `v9b` | `f6f77b32169b8c456e4be4976158c4f44b570d90b0243b9b01485112f44d4886` / `eb0f5c285ed1bc5fea76e87d2b593c895b51e859b7ace93ae14f23990e873351` |

The vector versions' traces are not stored again: they equal `paper_figures/inspector_v7/pipeview_E{3_stt,1_unsafe}.txt.gz` byte for byte.

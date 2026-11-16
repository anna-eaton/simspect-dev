# Inspector figure v7 / v7b: traces of inst-023734 (2026-11-16, inspector-v7-agent)

Data behind ISCA-27 `tikz/checkerwindow_v7_8pt.tex` (STT, no hit) and `tikz/checkerwindow_v7b_8pt.tex` (undefended Unsafe build, hit). Test: `STT_6_u_core_lpP_fv3` `inst-023734`, mode `mispredict_not_taken` (the clean running example of `paper_figures/fig2_concretization_example.md` §7). Every cycle drawn in the figures is listed with its tick in each `.tex` header.

## Verdicts

| Run | Build | Verdict | Key ticks (cycle = (tick - lc fetch)/500) |
|---|---|---|---|
| E3 rerun | `/work/stt-master` (md5 `1fed10b5…`), DerivO3CPU, `--scheme=2` (STT) | no hit: `issued_in_window false`, `cache_fate never_executed` | lc retires 2898500 (20); branch held from 2950500 (124) for 2,500 cycles, resolves 4201000 (2625); xmit's address ready 3007500 (238), never executes; squash lands on xmit 4201500 (2626); fnc retires 4208000 (2639) |
| E1 twin | `/work/gem5-recon-modded` (md5 `762efbc6…`), X86O3CPU, `--scheme=0` (Unsafe) | hit: `issued_in_window true`, `data_obtained true` | lc retires 2628000 (19); branch held from 2674000 (111), resolves 3924500 (2612); xmit issues 2725000 (213), reads the cache 2725500 (214), completes 2726500 (216); squash lands on xmit and fnc retires 3925000 (2613) |

The E3 rerun reproduces the campaign record exactly (`E3_STT_6_u_core_lpP_fv3_sh100_1__20261110_185333`, cafe3: `issued_in_window false`, `never_executed`, `lc_retire 2898500`, `fnc_retire 4208000`, `fnc_complete 2950500`, `resolve_hold 2950500`, `resolve_hold_fire 4200500`, `resolve_visible 4201000`). No E1 campaign covered this corpus before (§7.5), so the E1 result is new.

**Cache-fate label on the E1 run.** check_ld labels the E1 transmitter `store_forward`, but the trace shows a cache read: at 2725500 the LSQ logs `Doing memory access for inst [sn:585]` and `Memory request (pkt: ReadResp [35c0:35c7]) from inst [sn:585] was sent`, and the store queue is empty (`#stores occupied: 0`). This is the known gate mislabel on the Recon builds (`wiki/findings/bug/recon_cache_reach_gate/README.md`: those builds never print `successfully sent out packet(s)`, so every completed load is relabelled `store_forward`). The verdict (data obtained inside the window, hit) is unaffected; v7b draws the event as a cache access.

**xmit's front end on the E3 run.** The STT transmitter (seq 592) has no O3PipeView record (a squashed load that never issued). Its fetch (3004000) and decode (3004500) are those of its in-order neighbours seq 591 and seq 593, which share both ticks; the LSQ inserts it at 3006000.

## How it was run

Node: cafe3, container `gem5_dev`, workspace `/tests/inspector_v7_20261116` (script `run_inspv7.sh` here, log `logs/run.log`, inside `raw/results_configs_logs.tgz`). Code: the campaign's own code snapshot `/tests/simspect_alloy_20261108/loosepin_regen/code_eval` (Mac tree 264adea + uncommitted, 2026-11-10T13:58Z). Run through `pipeline.py gem5` with `TMPDIR=/tmp`, as the campaign did (BUGS.md H-STK).

Config: the shard config that produced the record, `runconfigs/twostage_lp/eval_20261110/shards/E3_STT_6_u_core_lpP_fv3_sh100_1.jsonc`, with only `paths.testset_dir/results_dir/results_name` (this workspace), `pipeline.keep_tmp: true`, `speculation.branch_modes: ["mispredict_not_taken"]` and `gem5.jobs: 1` changed. The E1 twin also swaps `gem5.binary`, `config_script`, `cpu_type` and `scheme` to E1's gem5 block (`runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc`; these four keys are the only differences between the E1 and E3 gem5 blocks). Both keep `branch_ann_enable: true`, `fnc_commit_stall_cycles: 0`, debug flags `O3PipeView,LSQUnit` (+ Commit, added by `gem5_common.run_gem5`), warm cache (no `cache_setup` key), and no `extra_args`.

Timing: the campaign's per-test draw, `sweep.timing_grid` `{unresolved [2500, 5000, 10000], resolved [0, 500, 2500], seed tgrid-v1}` → `pipeline._timing_grid_point("inst-023734")` = (2500, 500). pipeline.py's sweep path materialises it itself (`_enumerate_grid_for_corpus` → `sweep/manifest.json` = `{"inst-023734": [{"1": 2500}]}`; `_materialise_grid_run` writes the annotation with `resolve_stall_cycles: 2500` on pc1). The test has no resolved branch, so only the 2,500-cycle hold applies; both traces show `BR:resolve_hold ... stall=2500`.

gem5 command (from `gem5_common.run_gem5`; `<wd>` = the kept workdir, `/tmp/gem5_inst-023734_y6z0i4y9` for E3, `/tmp/gem5_inst-023734_fg6_mzv1` for E1):

```
/work/stt-master/build/X86/gem5.opt --outdir=<wd>/m5out --debug-flags=O3PipeView,LSQUnit,Commit --debug-file=pipeview.txt /work/stt-master/configs/example/se.py --cmd=<wd>/inst-023734 --cpu-type=DerivO3CPU --caches --scheme=2 --abs-max-tick=100000000000 --branch-ann-file=<wd>/branch_ann_se.json --branch-ann-base=0x401020
```

E1 differs only in `/work/gem5-recon-modded/build/X86/gem5.opt`, `/work/gem5-recon-modded/configs/example/se.py`, `--cpu-type=X86O3CPU` and `--scheme=0`.

## Files

| File | sha256 |
|---|---|
| `pipeview_E3_stt.txt.gz` (31,036 lines; uncompressed sha256 `535f22be…bbb983d`) | `9e1e9e1f70702fa356d99b0721942e8aa04f3eef9a28ccac29f21c4f83648f5a` |
| `pipeview_E1_unsafe.txt.gz` (27,039 lines; uncompressed sha256 `67c0fc14…bb5b215`) | `49261dbc4fd2dfe7dd000373b24cad6631df0ff60cdafd89ccfc2ac78257d166` |
| `record_E3_stt.json` (check_ld record, `sweep/raw_results/20261116155833_grid0000_batch0001_check_ld.py.json`) | `bcbff41839c711819c148e3f7084a0ea5a5cf3c538c6e950de2fd49172b23738` |
| `record_E1_unsafe.json` (`20261116155835_grid0000_batch0001_check_ld.py.json`) | `86db190914e164bbb2fccf617d2f865717f28b8812813ca9308cbf02a41cc8ec` |
| `raw/E3_gem5_inst-023734_y6z0i4y9.tgz` (whole kept workdir: binary, patched .s, `branch_ann_se.json`, `force_plan.json`, `m5out/` with config.ini/json, stats) | `b53db4f3cc955288d117c859a8ceb73062223d500c83b3a0191d82d0fc61df79` |
| `raw/E1_gem5_inst-023734_fg6_mzv1.tgz` | `c608b06300b8de0a43a7be118a3d9457a15448a43ee71729a3bf12adf6377b05` |
| `raw/results_configs_logs.tgz` (node `results/`, `configs/INSPV7_E{3,1}.json`, `logs/run.log`, `run_inspv7.sh`) | `5e2330fa82760026be467b026eab7a6b712470cd4d179d01cf1549b8627750e4` |
| `run_inspv7.sh` (the node script) | `fa8276df27d3a11dee2e74d36a405effd0ef256009104f3616f56f912cd56863` |
| `build_preview.sh` (builds an ISCA-27 standalone in a scratch dir and writes its 200 dpi `-1.png`) | see file |

Source test files (unchanged, sha256 checked on the node): `inst-023734.s` `d07ec290…b4b1978`, `inst-023734.ann.json` `d62b1a50…51ec28`.

## Figures

New ISCA-27 files only (paper text, existing figures and the `\input` untouched; no git writes): `tikz/checkerwindow_v7_8pt.tex`, `tikz/_standalone_checkerwindow_v7_8pt.tex`, `tikz/_standalone_checkerwindow_v7_8pt-1.png`, and the same three for `v7b`. Both carry `\label{fig:checkerwindow}` and a plain proposed caption ending in a `\reviewtag`. To use one, change `\input{tikz/checkerwindow_v6_8pt}` in `sections/pipeline.tex` (line 113 at ISCA-27 dd7a730) to `\input{tikz/checkerwindow_v7_8pt}` or `_v7b_`. Standalone height 112.0pt each (v6 as currently built: 104.2pt; its 2026-11-16 preview: 94.7pt); the extra comes from the two-line criterion box and the second tier of cycle numbers that keeps every event's cycle readable.

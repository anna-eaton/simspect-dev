# Brief: integer twins for the taint-tracking defenses, then rerun (Anna, 2026-11-16)

**Goal.** Every test on the taint-tracking defenses (STT, ReCon, SPT) comes as a pair from the same Alloy execution graph: an *FPR version* (today's recipe A: every load whose result is used is routed through a vector register) and an *integer version* (the same program with that routing off, so every used load result stays in an integer register). The two versions must have identical instructions, memory accesses, branch directions, and timing draws; they may differ only in the FPR route lines. This replaces the per-load `fpr.p` idea (that option stays in `parsexml.py`, unused). Not for the invisible-speculation (AMuLeT-comparison) corpora: InvisiSpec, CleanupSpec, and SpecLFB stay as they are.

**Rules.** Read `CLAUDE.md` (git write lock: no git writes; never edit `.als`; careful logs; reproduce runs exactly as their run config did) and `claudenotes.md`; claim the work there first. Do not edit the frozen recipe `runconfigs/bigcorpus_20261115/stage2_final_A.jsonc`; write new configs under `runconfigs/inttwin_20261116/`. Log every run (start, end, what ran, errors) under the run dir; durable summaries in `wiki/state/EVAL_MANIFEST.md` (new "Integer twins" section) and a dated `claudelog.md` entry per stage.

## 1. Build the integer-twin recipe

- New recipe `runconfigs/inttwin_20261116/stage2_final_A_int.jsonc` = `stage2_final_A.jsonc` with ONLY `fpr.enabled: false`. Header comment: why (Anna 2026-11-16, paired register-class design), and that it differs from A only in FPR routing.
- Check that turning FPR off changes no other draw: the FPR draws use their own RNG seeded `fpr:<stem>` (see `parsexml.py` FPR docstring near line 2090 and `_fpr_loads` near 2288), and RMW eligibility (`outreg_consumed`, parsexml.py:599) and jmp insertion (`jmp_insert` before a PC) should not depend on it. Prove it on 50 programs of each corpus below: diff the twin `.s` against the corpus `.s`; the ONLY differences allowed are the 4-line route blocks (`movq %out,%xmmK; movq $0,%out; movq %xmmK,%out` and the `direct`/`_alu` forms) and their PC-label offsets. If anything else differs (fillers, RMW, jmp, register choices), stop and report; the old `runconfigs/twostage_lp/eval_20261110/make_gpr_twin.sh` dropped RMW/jmp stems for this reason, and that is not acceptable here: every stem must get a faithful twin.
- SSE fillers: recipe A's interleave-only filler table (`STAGE2_compilation/instruction_tables/proposed/interleave_only.jsonc`) contains dead SSE fillers on xmm14/xmm15. Keep the filler table identical in both versions (so pairs differ only in routing). Record in the manifest that the integer version can still contain those dead SSE fillers.

## 2. Generate the twins (same Stage 1.5 XMLs as the reported corpora)

| Defense | Reported corpus (FPR version) | Integer twin to build |
|---|---|---|
| STT (also ReCon-STT E2w, SPT-Fence race on the STT corpus) | `STT_6_u_core_lpP_s2A` | `STT_6_u_core_lpP_s2Aint` |
| ReCon | `Recon_6_u_core_lpP_s2A` | `Recon_6_u_core_lpP_s2Aint` |
| ReCon store shadows | `Recon_6_u_stl_core_lpP_s2A` (recipe `runconfigs/reconstl_20261116/stage2_stl_A.jsonc`) | `Recon_6_u_stl_core_lpP_s2Aint` (the stl recipe with `fpr.enabled: false`) |
| SPT | `SPT_6_oneLP_v2_flat_ld_s2Aspt` (recipe `runconfigs/sptrace_20261116/stage2_final_A_spt_*.jsonc`) | `SPT_6_oneLP_v2_flat_ld_s2Asptint` |

Find each corpus's XMLs and Stage 2 launcher from `EVAL_MANIFEST.md` (big-corpus section, E2w-stl row, sptrace) and reuse the same launcher (`stage2_sharded.py` / `scripts/bigcorpus_20261115/*`) with the new recipe. Verify per corpus: same stem set and count in both versions, 0 missing, and the pair-diff check of step 1 on a 1% sample.

## 3. Rerun everything for the taint-tracking defenses, both versions, today's code

Run each reported taint-tracking campaign on BOTH the FPR corpus and its integer twin with today's code (fast path default), so each pair is scored by the same code. Configs: copy each existing config into `runconfigs/inttwin_20261116/` changing only the corpus path and results name (`<name>_fpr` / `<name>_int`); keep every gem5 block, hook, stall grid, cache setup, and seed exactly.

- STT corpus: `E3_STT_6_u_core_lpP_s2A` (stt-master), `E4_STT_6_u_core_lpP_s2A` (AMuLeT STT), `E2w_STT_6_u_core_lpP_s2A` (ReCon-STT), `E2_STT_6_u_core_lpP_s2A`; race rows `race_stt_d{1,3,4}`, `race_sttmaster_d{1,3,4}`, `race_sptfence_d{1,4}` (all in `runconfigs/bigcorpus_20261115/`).
- ReCon: `E6_Recon_6_u_core_lpP_s2A`; store shadows `runconfigs/reconstl_20261116/E2wstl_Recon_6_u_stl_core_lpP_s2A.jsonc` (build `/work/gem5-recon-modded-stl`).
- SPT: `runconfigs/sptrace_20261116/race_sptfence_d{1,3,4}_SPT_6_oneLP_v2_flat_ld_s2Aspt.jsonc`, plus the paired `race_scan.py` and the faithful UV6 confirmation (`scripts/sptrace_20261116/confirm_uv6.sh`) on each version.

Nodes: cafe1 and cafe3 are idle (Anna); check `claudenotes.md` for unattended jobs first. Results names must start with `E3_` / `E4_` (not `bc_E3_`), because `STAGE3_gem5/bugs/classify.py gate` applies the STT labels (`S1_xmm4` = UV1) only to names with those prefixes; alternatively fix that prefix match in `classify.py` (a real bug; note it in claudelog) before scoring.

## 4. Classify and report

For every campaign and both versions: `STAGE3_gem5/bugs/classify.py gate` + `bucket` (and `race` for race rows). Report a per-bug table with counts for FPR, integer, and pairs where they differ (e.g., UV1 should appear only in FPR versions; UV2, UV3 and UV6 in both if they do not depend on the register class). Write it to `EVAL_MANIFEST.md` "Integer twins" with paths, sha256s of the twin recipes, and runtimes; log in `claudelog.md`; mark the `claudenotes.md` claim DONE. Do not edit the paper; the paper session updates Pass 6 ("each graph yields an integer version and a version with every used load result in a vector register") and the Results numbers from your table.

## Addendum 2026-11-16: E2w and E2w-stl with random_all

**Decision (Anna, 2026-11-16).** Every reported campaign draws its initial cache state per test (`gem5.cache_setup: "random_all"`) except E2w (ReCon's implementation of STT on the STT corpus) and E2w-stl (store shadows), which start warm only because their configs copied an older protocol (`runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc` line 2; `runconfigs/reconstl_20261116/E2wstl_Recon_6_u_stl_core_lpP_s2A.jsonc` copied E2w's gem5 block). Anna chose to rerun both rows with `random_all`, in both register versions, so the paper can say every run draws its cache state at random. The warm inttwin E2w / E2wstl rows on cafe3 keep running unchanged.

**Configs** (`runconfigs/inttwin_20261116/`, agent e2wra): `E2w_STT_6_u_core_lpP_s2A_{fpr,int}_ra.jsonc`, `E2wstl_Recon_6_u_stl_core_lpP_s2A_{fpr,int}_ra.jsonc` = the inttwin E2w / E2wstl configs with ONLY `gem5.cache_setup: "random_all"`, `gem5.cache_setup_fill_bytes: "64kB"` (E2's values, `runconfigs/bigcorpus_20261115/E2_STT_6_u_core_lpP_s2A.jsonc`) and `results_name` ending `_ra`. Checked: 64 kB 2-way is the dcache of both builds (gem5 `config.ini` from se.py with no `--l1d_size`; `Options.py:148` default); `cache_setup.py` allows warm/cold/full on `gem5-recon-modded-stl` (not in `CLFLUSH_UNSUPPORTED`; the match is a substring of the binary path and the only recon key is `gem5-recon-ruby3`); parsed-JSON diff vs the source config = exactly those three keys.

**Rows** appended to `campaigns.json` (rows `E2w_STT_6_u_core_lpP_s2A_ra`, `E2wstl_Recon_6_u_stl_core_lpP_s2A_ra`) with `node: "cafe3ra"`: physical cafe3, but a separate queue name, so `prep_queue.py --node cafe3ra` wrote a separate queue file (`/tests/inttwin_20261116/queue_cafe3ra.json`, 154 shards) and the running `queue_cafe3.json` / cafe3 classifier (which read `campaigns.json` at start and filter on `node == cafe3`) are untouched. The node copy of `campaigns.json` was replaced (old copy `logs/campaigns.json.before_e2wra`; the first 34 rows are byte-for-byte the old list) and the 4 configs added; the change is appended to `code/SNAPSHOT.txt`. No other code file was shipped: the node code is still the inttwin snapshot (gem5_common 9f67f809, no resolved gate).

**Smoke** (`scripts/inttwin_20261116/smoke_ra.sh`, cafe3 `/tests/inttwin_20261116/smoke_ra/`): 10 tests per config, all four rc 0; every record `cache_setup_mode: random_all`, all three setups drawn; status ok except E2wstl inst-000001 and inst-000004 (invalid in both versions, and also invalid in the warm E2w-stl run).

**Run** (cafe3, tmux `e2wra`; started 2026-11-16 17:00Z): window `queue` = `python3 scripts/inttwin_20261116/run_queue.py --node cafe3ra --slots 6`, raised to 8 at 17:05Z via the slots file (cafe3 load 44 of 64 cores) (slots file `/tests/inttwin_20261116/slots_cafe3ra`, FINISH marker already set, log `logs/queue_cafe3ra.log`, per shard `logs/q/<shard>.log`); window `classify` = `python3 scripts/inttwin_20261116/classify_node.py --node cafe3ra` (log `logs/classify_cafe3ra.log`; per row `cls/<row>/`: gate + recon_stlf evidence + bucket, the integer version as twin, exactly as the inttwin ReCon rows). The inttwin disk guard (`guard.sh`, tmux `inttwin:guard`) covers these shards too (it matches `testrun.py --config /tests/inttwin_20261116/cfg/`). Results → `wiki/state/EVAL_MANIFEST.md` "Integer twins" (E2w and E2w-stl with `random_all`).

**First check (17:12Z):** 6 shards done rc 0 (740 s per 1,168 tests); E2w sh0 1,168/1,168 status ok in both versions, warm 390 / cold 374 / full 404, raw hits 694 (FPR) vs 321 (int). cafe3 load ~56/64, /tmp 1.3 TB free. ETA: gem5 ~21:30Z (154 shards at 8 slots), then `classify_node.py` (recon_stlf evidence reruns, est. 1-2 h).

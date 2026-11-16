# diag_rmw_limm_artifact: RMW `store_forward` hits on the Recon builds are a check_ld limm artifact (RL-10)

**Verdict: check_ld checker artifact, not a defense bug.** ReCon's delay unit holds the RMW's load micro-op correctly; check_ld scores the wrong micro-op. `PHASE = "disqualifier"`, `CATEGORY = "checker_artifact:RL-10_rmw_limm"`, `ORDER = 30`, `NEEDS_GEM5 = False` (it reads rerun evidence that already exists). The real fix is the checker change in `wiki/findings/audits/2026-11-10/CHECKER_FIX_PROPOSALS.md` item 2 (score the LSQ-sn micro-op), which is still Anna's open DECIDE (URGENT_TODO, check_ld multi-micro-op, 2026-11-08). This diagnostic only keeps the artifact out of NEW until then.

## Issue and signature

The fv4 vocabulary (`fanout_v2.vocab_rj`, `load_rmw_or0`) and the `STT_6_rmw` corpus emit RMW transmitters as `orq $0, <mem>`. gem5 decodes that as `OR_M_I`: `limm t2, 0; ldst t1, [mem]; or t1, t1, t2; st t1, [mem]`, four micro-ops at one pc. On gem5-recon-ruby3 / gem5-recon-modded (scheme 2, ReCon-STT) the tainted `ldst` executes in the LSQ, prints `STL_CHECK ... isTainted=1`, and in the same tick is `Inserted tainted load [sn:N] into delay_unit` (`/work/gem5-recon-ruby3/src/cpu/o3/lsq_unit.cc:2104`). It is never released, never sends a request, has pipeview `complete 0`, and is squashed at branch resolve. check_ld takes `xmit_complete` from the pc-wide `best_record` (`STAGE3_gem5/gem5_common.py:816`), which is the `limm` micro-op's completion, so the `executed_no_packet` bounce becomes `store_forward` with `data_obtained` true (`STAGE3_gem5/check_ld.py:139`).

The diagnostic buckets a hit only when all of these hold (see the docstring for the exact rules):

1. Build: the campaign `manifest.json` names `/work/gem5-recon-ruby3/` or `/work/gem5-recon-modded/`, the config's `gem5.scheme` is 2, and no `--scheme=` override says otherwise.
2. Form: the instruction at the xmit label in `<mode>/asm/<stem>.s` is `orq $imm, <mem>` (OR_M_I).
3. Raw records: every hitting check_ld record of the mode/stem is `store_forward`, `data_obtained` true, `xmit_retire` 0, `packet_tick` 0, and `0 < xmit_complete <= xmit_execute`.
4. Rerun evidence, `diagnostics/recon_stlf_evidence.json` (`STAGE3_gem5/triage/rerun_hits_evidence.py --analyzer recon_stlf`, the same file `diag_recon_stlf_bypass` reads): reproduced, `STL_CHECK isTainted=1`, no `Forwarding from store` line, `ready_tick` null.
5. Optional micro-op evidence, `diagnostics/rmw_uop_evidence.json` in the format of cafe2 `bugwork/recon_rmw/uop_table.json`: if an entry exists, its `ldst` must have `complete 0`, `retire 0`, a `delay_unit` insertion, and the completion must not come from the `ldst`.

Why rule 3 alone is not enough: a raw record keeps only the latest LSQ execute tick and one pc-wide completion. A test whose `ldst` ran twice (an earlier instance that obtained data and a later one that was bounced) would also show `complete <= execute`. Rule 4 rules that out with the rerun's own LSQ trace. So the diagnostic needs the recon_stlf evidence to be present for the campaign, and a hit with no evidence entry stays NEW.

## Evidence

- Claudelog `2026-11-10 17:10 — recon-rmw — RL-10 resolved`; URGENT_TODO RL-10 (closed); CHECKER_FIX_PROPOSALS.md item 2 addendum.
- 14 faithful E6 reruns (config `runconfigs/twostage_lp/eval_20261110/E6_Recon_6_u_core_lpP_fv3.jsonc`, flags `LSQUnit,DelayUnit,Commit,O3PipeView,DelayDebug`): inst-000847, inst-000711, inst-001007, inst-011193 in both modes, plus inst-007123, inst-008465, inst-009338 (not_taken) and inst-003001, inst-011170, inst-012691 (taken), the last six from the `complete == execute` group. All 14 show the picture above. Micro-op table: cafe2 `/tests/simspect_alloy_20261108/bugwork/recon_rmw/uop_table.json`; scans `scan_e6.txt`, `scan_ev.txt` in the same directory.
- The RL-10 set (regen-lp `loosepin_regen/bugwork/e6_stlf/recon_stlf_evidence.json`, RMW, `isTainted=1`, no forward, never ready) is 302 not_taken / 298 taken records, and all have `xmit_complete <= xmit_execute` (268 / 265 strictly less, 34 / 33 equal; the equal case is the `limm` completing in the tick the `ldst` is bounced).
- Contrast: the E6 RMW records with a real forward (A2, `fwd` true and ready) are 60 / 59, and every one has `xmit_complete > xmit_execute`.

## Validation (2026-11-12, rl10-diag, read-only on cafe2)

The test ran the diagnostic's own `is_known` (with the loaders pointed at the E6 data) on every hitting (mode, stem) of the current E6 `Recon_6_u_core_lpP_fv3` main + shard campaigns (twins excluded) in `loosepin_regen/code_eval/results`. The evidence came from regen-lp `recon_stlf_evidence.json` and `bugwork/recon_rmw/uop_table.json`. The harness was piped over ssh, nothing was written and nothing was rerun; the copy is in the session scratchpad. Both sets have grown since RL-10 (shards sh25/sh100 landed after the 302/298 scan), so the counts are larger.

- RMW, evidence `isTainted=1`, no forward, never ready (the RL-10 class): **2742 / 2720 (not_taken / taken) bucketed, 0 missed.**
- RMW with a real forward (A2 class, `fwd` true): 573 / 565, all NEW.
- RMW with `isTainted=0`: 14 / 15, all NEW.
- RMW with no evidence entry: 3469 / 3501, all NEW. Tonight's campaigns need `rerun_hits_evidence.py --analyzer recon_stlf` before this diagnostic can bucket anything.
- Plain (non-RMW) loads: 0 bucketed out of about 5,250 per mode.
- The 8 uop-table entries (inst-000711, -000847, -001007, -011193, both modes): all pass rule 5.

## Scope

- **Proven:** gem5-recon-ruby3 (E6), by the 14 reruns and the 302/298 evidence records.
- **Applied, per-record evidence required:** gem5-recon-modded scheme 2 (E2). It has the same `src/cpu/o3` (RL-9: `diff -rq` shows no difference, `lsq_unit.cc` sha256 identical), and the E2 raw records show 292 / 291 RMW `store_forward` hits with the same signature. E2 was not rerun for RL-10, so on E2 the diagnostic buckets only records whose own recon_stlf rerun passes rule 4.
- **Not applied (returns False):** every other build or scheme. That includes gem5-recon-modded schemes 1 (NDA) and 3 (DoM): DoM decides on misses, not on taint, and neither scheme was traced. On `/work/stt` and `/work/stt-master` the RMW has the same OR_M_I micro-ops, but STT blocks the tainted `ldst` at issue (`fenceDelay(isArgsTainted())`, `stt-master lsq_unit_impl.hh:1013`). The LSQ never executes it, so the hit is an ungated `never_executed` record whose window signal is the `limm` completion (the 309 STT RMW artifacts of the 2026-11-08 DECIDE). That is a different checker path, and this diagnostic never sees it: rule 3 requires `store_forward`. A separate disqualifier for it would be `cache_fate == never_executed` on an OR_M_I transmitter. That is option (b) of the same DECIDE, so it is left to Anna.
- **Corpus:** any testset whose ld transmitter is `orq $imm, <mem>` (fv4 `vocab_rj` corpora, `STT_6_rmw`). It matches nothing on a corpus without RMWs.

## What it does NOT cover (stays NEW)

- RMW hits with a real store forward to the `ldst` (A2 / R-SA-9 class, `diag_recon_stlf_bypass`, real bug).
- RMW `store_forward` hits with `xmit_complete > xmit_execute` (not traced; the item 2 fix decides them on the `ldst`'s own record).
- RMW hits whose STL_CHECK says `isTainted=0` (R-SA-12/13 lost-taint classes), or whose xmit became ready within the ROB.
- Any hit without a recon_stlf evidence entry, other RMW mnemonics (`addq $imm`, register-source `orq %r, mem` = OR_M_R, which has no leading `limm`), and plain loads.
- Campaigns where a test has several hitting records (grid points) and any one of them fails rule 3.

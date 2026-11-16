# Source audit: AMuLeT CleanupSpec_AE-v1.1 + SpecLFB_AE-v1.1 (2026-11-08, initial results + round 2)

This is a read-only manual audit of AMuLeT's AE trees. The `src/` and `configs/` were copied read-only from cafe2 `gem5_dev:/work/amulet/amulet-gem5-{CleanupSpec,SpecLFB}_AE-v1.1/` to `~/trippel/defense_src/amulet-{CleanupSpec,SpecLFB}_AE-v1.1/`, and paths below are relative to their `src/`. Nothing was built or run. The only cafe2 access beyond the copy was reading existing E13 traces (two in round 1, a scan of the kept ones in round 2). The criteria are `specs/leakage/{cleanupspec,speclfb}.json`, with E13/E14 in `wiki/state/EVAL_MANIFEST.md`. Papers: CleanupSpec (MICRO'19, PDF pages), SpecLFB (USENIX Sec'24, printed pages), AMuLeT (ASPLOS'25). The audit was paused at Anna's request, so it gives at most 3 findings per defense, and the rest is listed under "Not reviewed". **Labels:** IDs like SL-1 (SpecLFB finding 1) and CS-1 (CleanupSpec finding 1) are local to this doc and are only for cross-reference. "Class A/B/C" means: A = the code contradicts the paper's guarantee as our criterion encodes it; B = our criterion and the code (or paper) disagree, which is a question for Anna; C = outside what the paper claims to protect. Round 2 (later on 2026-11-08) answered Anna's reactions; see "Round 2" below.

## Summary

| ID | Defense | Class | Confidence | Claim | Known? |
|---|---|---|---|---|---|
| SL-1 | SpecLFB | A | confirmed by reading; gem5 2026-11-09: reached in `inst-055160`, masked by UV6 | A cache-line-crossing (split) unsafe load bypasses SpecLFB entirely. The USL/HitUSL flags go only on `_mainReq`, but the packets sent to the cache are built from the fragment requests, which carry no flag. So the load misses, fills L1D and L2 speculatively, and is never refused or stalled. | new (the SpecLFB sibling of CleanupSpec UV4; AMuLeT reports only UV6 for SpecLFB) |
| SL-2 | SpecLFB | A per the paper; currently out of our criterion's scope by our choice | confirmed by reading | There is no exception-shadow protection. The paper (§5 item 4, p637-638) says loads after a possibly faulting instruction are MUSLs to protect, but the code tracks only control (`controlUSL`) and store-address (`memUSL`) sources. | new as a code fact; the criterion already lists it as `not_covered` |
| SL-3 | SpecLFB | C | confirmed by reading | Hook interaction: for split loads, `LSQ:unsafe … requsl=` prints `_mainReq->isUSL()` (`cpu/o3/lsq.cc:1172`), so a split load shows `requsl=1` while its cache packets print `usl=0`. | new |
| CS-1 | CleanupSpec | B | **confirmed from traces** | Both "NEW" E13 hits (`inst-101824`, `inst-102050`; victim-only under_clean on 0x3cc0) have the same cause. An **older, non-squashed store** (seq 562, older than the squashing branch) hits the line that a squashed load installed in E and upgrades it to M. The cleanup then skips at M (`Inv_CLEANUP st=M`), so the victim is never restored. The paper says this skip is intended (§3.4 p7), but the "count as both" rule charges the victim to the squashed load. | explains the 2 open NEW hits; a sibling of the known RMW E→M case, with a non-squashed upgrader |
| CS-2 | CleanupSpec | A | confirmed by reading (mechanism); **real but not reached** (round 5, 2026-11-09: 0 retried / out-of-order cleanup sends in 2,843 kept traces + 360 scratch reruns; the send-failure precondition is a 16-entry Sequencer limit or a one-cycle in-flight race, not the TBE pool) | The paper's reverse-order cleanup (Fig. 8b p7) can be violated. A younger squashed load whose cleanup send fails is skipped and retried on the next call, after older loads' cleanups have already been issued. If the younger load had evicted the older load's install from the same L1 set, the older cleanup finds the line gone (NP) and skips both its invalidate and its rollback. The younger cleanup then restores the secret-dependent line. | new |
| CS-EM | CleanupSpec | A | **confirmed from traces + code** (round 4, 2026-11-09) | A squashed RMW transmitter's `ldst` hits a squashed load's E install and upgrades it to M (`MESI_Two_Level-L1cache.sm:2294-2298`, no speculation check); the load's cleanup then skips at M (`:2701-2705`), so its install (and victim) stay. 72 cold / 44 random / 10 warm stems; plain-load controls 0. | UV3 family (speculative RFO), distinct path; not in AMuLeT's list; AMuLeT's UV3 patch does not cover it (by reading) |
| CS-3 | CleanupSpec | C | confirmed by reading | Robustness: a `PUTINV` reaching an L2 line that is already NP recycles forever (`MESI_Two_Level-L2cache.sm:1147-1149`; the `C_NP` handling is commented out at `:1150-1160`), so the test deadlocks (an error, not a leak). Also, the in-flight L2-cleanup decision uses `tbe.lineInL2`, sampled from the L2 tags when the L1 TBE is allocated (`L1cache.sm:1499,1514,1952`). If the L2 changes before the GETS arrives, the result can be stale (L2 residue or over-clean), but the race is narrow. | new |
| H-PAD | harness (all builds) | artifact | **confirmed from traces** (round 6, 2026-11-09) | In `mispredict_taken` tests the function ends in a backward `jmp`; fetch falls through past `.text` into zeros, decoded as `add %al,(%rax)` (an RMW). On E13 its write request reaches UV3 (`why=nohitinfo`) or CS-EM (E→M). That is 29/52 NEW per testset (fv2 inst-005142, inst-029763). | new (harness) |
| H-STK | harness (all builds) | artifact | **confirmed by rerun** (round 6) | The SE initial stack holds the workdir path (`process.cc:770-774, 907-920`), so the stack lines depend on the TMPDIR length. bucket-fv2's 18 E13 'did not reproduce' hits are this, not Ruby nondeterminism. With TMPDIR=/tmp a rerun is identical to the campaign (inst-005142 4703 events; inst-009280 2117). | new (harness) |

## SpecLFB

### SL-1 (A). Split loads bypass the USL check

- **Code:**
  - `cpu/o3/lsq.cc:1099-1145` (`SplitDataRequest::initiateTranslation`) creates `_mainReq` and the per-line fragments `_reqs` through `addReq` (`:1242-1249`, plain `_flags`).
  - The SpecLFB tagging applies only to `_mainReq`: `:1153-1155` `if(_inst->isUnsafe()&&!_inst->isStore()){ _mainReq->setUnsafe(); _mainReq->setHitUSL(); }`.
  - `buildPackets` builds the cache packets from the fragments: `:1421-1423` `for (int i = 0; i < _reqs.size() …) { RequestPtr req = _reqs[i]; PacketPtr pkt = … Packet::createRead(req)`.
  - `sendPacketToCache` sends those packets (`:1468-1476`).
  - Compare the single-line path, which tags the request that is actually sent: `:1049-1052` `_reqs.back()->setUnsafe(); _reqs.back()->setHitUSL();`.
- **Mechanism:**
  1. The cache decides only on `pkt->req->isHit_USL()` (`mem/cache/base.cc:586-617`, `:1940-1944`, `:3236-3239`).
  2. For a fragment that flag is false, so a miss allocates an MSHR and fills L1D and then L2 like a safe load.
  3. In the LSQ, the stall decision reads `request->mainReq()->isHit_USL()` (`cpu/o3/lsq_unit.cc:1877`, `:1891`). The cache never clears it on `_mainReq`, so the load is never `SpeclfbStalled`.
  4. Fragment requests do carry the seq (`lsq.cc:1147`), so the hook fill lines are attributed to the right instruction (`base.cc:123`).
- **Contradicts:** SpecLFB §6.1 p637 ("Only when the security check mechanism determines that it is safe, can the data be refilled into the L1D cache") and §7 p640 (both levels in gem5), as encoded in `speclfb.json` `leak` (any actor fill or evict in L1D/L2 inside W).
- **Litmus:**
  1. A slow bounds branch (cold length line), mispredicted.
  2. A sacrificial first speculative load, so that UV6 and walk-order do not apply.
  3. The access load `mov rbx,[secret]`, then `shl rbx,6`.
  4. The transmitter `mov rcx,[probe+rbx+60]`: an 8-byte load at line offset 60 crosses into the next line.
  5. No `jmp`/`call` in the shadow, to exclude jmp-shadow.
  6. Control: offset 56 (no split) should be refused and stalled.
- **SimSpect:**
  - Cannot generate it today. Stage 2 emits 8-aligned `i64` slots (`parsexml.py:2131`, `align 8`), so loads never cross a line.
  - `check_footprint` would detect it as is (fill by an actor in W).
  - Generating it would need a stimulus with line-crossing loads. Anna parked the misaligned-load option (round 2), so SL-1 stays a by-reading finding for now.
  - **Correction (2026-11-09, gem5 check below):** the "cannot generate" bullet is wrong. The slots are 8-aligned, but a load whose index register holds a computed value (e.g. `not` of a zero register = -1) addresses `rsp-1`, an 8-byte load at line offset 0x3f. Our existing tests do this without any misaligned-load option.

### SL-1 gem5 check (bug-investigate-sl1, 2026-11-09)

**Verdict: real and reached by our pipeline, but never the only cause of a hit.** One generated test, `inst-055160` (both modes), runs a protected split load that SpecLFB lets fill L1D and L2. The same test also has a UV6 first-load fill, so SL-1 adds offending events to a test that is a hit anyway. Found by us: ☑ 2026-11-09 (reached, masked by UV6).

- **Experiment:** reran the whole E14_STT_6_fv2 1% ld sample (668 stems per mode, from cafe2 `results_fv2/E14_STT_6_fv2__latest/<mode>/ld/window-results.json`) with the campaign config copied exactly, changing only paths, `keep_tmp: true` and `jobs: 8` (cafe2 `/tests/simspect_alloy_20261108/bugwork/sl1/{setup.sh,cfg.json,run.log}`). The rerun's `issued_in_window` matches the campaign on 668/668 stems in each mode. The checker's offending seqs come from the campaign's own `_sweep_raw` records. Seqs match the rerun; physical lines are shifted by 0x80 (stack placement), which keeps the line offset. The scan (`bugwork/sl1/scan.py` → `split_loads.jsonl`) reads every `LSQ:unsafe … split=1` hook event.
- **Split loads in our tests:** 36 split load executions in 18 stems (×2 modes), all at `vaddr=0x7fffffffe53f size=8`, i.e. `rsp + (-1)`, because the index register holds -1 (e.g. `inst-005391` pc2 `mov (%r10,%rdi,1),%rdi` after `not %rdi`). Every one is in its test's offending list.
  - 34 of 36 have `unsafe=0 lqhead=1 prevnounsafe=1`: the split load is itself the oldest speculative load, the UV6 case. These are unprotected anyway, so the split changes nothing.
  - 2 of 36 (`inst-055160`, not_taken and taken) have `unsafe=1 cusl=1 reallyunsafe=1 lqhead=0 requsl=1`: these are SL-1.
- **SL-1 trace (`inst-055160` not_taken; kept at `bugwork/sl1/keep/gem5_inst-055160_5c53ji97/m5out/pipeview.txt`):** the branch at `0x4042c7` is forced not-taken (it is architecturally taken), so pc1..pc5 are wrong-path. The load at pc5 `0x4042fc` `mov (%rdi,%r12,1),%r9` has `r12 = ~rdx`:
  - `15496500 LSQ:unsafe seq=3072 pc=0x4042fc unsafe=1 cusl=1 reallyunsafe=1 lqhead=0 split=1 requsl=1 vaddr=0x7fffffffe53f`
  - `15496500 L1D:miss line=0x7500 seq=3072 addr=0x753f size=1 usl=0 hitusl=0`, then `LSQ:issue line=0x7500 … sent=1 bounced=0 usl=0 hitusl=0`. The second fragment (`0x7540`, size 7) hits.
  - `15557000 L2:fill line=0x7500 seq=3072`, `15567500 L1D:fill line=0x7500 seq=3072`, then `15568500 LSQ:data seq=3072 … usl=1 hitusl=1`. `_mainReq` keeps its flags and the fragment packets never had them, as SL-1 predicts (`lsq.cc:1153-1155` vs `:1421-1423`). The load's `cusl` clears only at `20419000` (`by=rob`), just before the squash. `fnc_retire` is `20423500`, so the fill falls inside W.
  - **Control in the same trace:** four non-split loads 3 to 5 cycles earlier, seqs 3075/3078/3081/3084 (pcs `0x404306`..`0x40430b`), have identical flags (`unsafe=1 cusl=1 reallyunsafe=1 requsl=1`). Each is refused: `L1D:miss … usl=1 hitusl=1 touch=0`, then `LSQ:issue … sent=0 bounced=1`. The only difference is `split`.
- **Why it is not a sole-cause hit:** the campaign record for `inst-055160` not_taken has `offending` = seq 3061 (L2+L1D fill `0x75c0`) and seq 3072 (L2+L1D fill `0x7580`). Seq 3061 is pc2 `0x4042e2` with `unsafe=0 lqhead=1` (UV6). The taken record also lists seq 3086. Without SL-1 the test is still a hit. UV6, walk-order and jmp-shadow dominate E14, so an SL-1-only hit needs a split load that is not the first speculative load, in a test with no other unprotected fill.
- **Scope:** checked only E14_STT_6_fv2 at 1% (1336 runs). The fv2fp copy and the 2% top-up were not scanned. A diagnostic would match `LSQ:unsafe … split=1 unsafe=1` plus a fill or evict by that seq inside W. None is deployed.

### `replayed_after_safe(jmp_in_shadow)` is jmp-shadow seen at a replay (bug-investigate-e14new, 2026-11-09)

**Verdict: the same jmp-shadow bug, not a separate replay bug and not an artifact.** The tag (`STAGE3_gem5/timing/speclfb_analyze.py:153-160`) marks a load that was `unsafe=1` at translation, bounced, and was re-sent. In all 5 traced stems the flag that released it was cleared by the ROB walk while the older mispredicted branch was still unresolved, with a generated direct `jmp` (`JMP_I`) between that branch and the load. The ROB walk can only clear `CUSL` when `prevBrsResolved` is true at the load (`rob.cc:461-471` in the live tree; the unresolved-branch `false` at `:530`). An unresolved older branch sets it false, and only the direct-unconditional reset (`prevBrsResolved = isDirectCtrl() && isUncondCtrl()`, live `rob.cc:538`) sets it back to true. The replay is just the order of events: the load first translated while something younger still held it (a younger conditional branch, an `mUSL` from an older store, or the IEW-before-commit order of the two walks), bounced, and then went out once that cleared. That makes it the same mechanism as `jmp_shadow`.

- **Experiment:** reran 5 E14_STT_6_fv2 not_taken NEW stems (inst-012796, -013826, -038066 with `uv6_first` co-firing; inst-035848, -075754 with only this tag) with the campaign config `code_20261109/runconfigs/twostage_fv2_20261109/E14_STT_6_fv2.jsonc` copied exactly, changing only paths, `branch_modes` (not_taken only), `keep_tmp` and `jobs` (cafe2 `/tests/simspect_alloy_20261108/bugwork/e14new/{cfg.json,run.log}`). 5/5 hit again. `bugwork/e14new/replay_why.py` → `replay_why.out` prints, for each replayed load, when it bounced, when the ROB cleared its flags, when it was re-sent, the squashing branch's `BR:resolve_visible` (set in `Commit::markCompletedInsts` together with `setCanCommit`, `commit.cc:1397-1407`), and every control op in between.
- **inst-035848 (kept: `bugwork/e14new/keep/inst-035848_not_taken_pipeview.txt.gz`):** pc0 `JNB_I` 0x401c38 (seq 557) is forced not-taken and held until 6142000. The generated pc4 `jmp .Ltmp1` (`JMP_I` 0x401c62, seq 573) and the pc5 bypass `jae` (`JNB_I` 0x401c6b, seq 579, predicted right) follow. The epilogue `popq %r14` / `popq %rbp` / `retq` loads (seqs 582/585/588) translate `unsafe=1 cusl=1 prevbrsres=0` and bounce at 3713500-3714500, because seq 579 is not yet resolved. At `3714500 BR:resolve_visible seq=579`, the ROB walk clears `cusl` on all three in the same tick (`f=cusl:v=0:by=rob`). They are re-sent at 3715500 and get data from memory at 3728500-3731000, which is 2.4 M ticks before seq 557 resolves (`6142500 ROB:squash seq=557`). Without the jmp's reset, seq 557 would keep `prevBrsResolved` false at those loads until the squash.
- **inst-038066 (kept):** pc2 `JB_I` 0x40440d (seq 3129) is squashed at 16060500. Generated `JMP_I` 0x404418 (seq 3134), then the bypass `JNB_I` 0x404425 (seq 3141, visible at 16002000). Epilogue pops 3144/3147 clear `cusl` by the ROB walk at 16002000 (jmp-shadow). They are still held by `musl=1` (an older store's address is unresolved) and re-sent at 16060000 when `musl` clears at 16059000. Then they fill L2 and L1D at 16092000/16102500. The `mUSL` release is legitimate on its own; the load can go only because the jmp already removed `CUSL` while seq 3129 was unresolved. inst-012796 has the same shape (`cusl=0 prevbrsres=1` from the first translation, released by `musl=0` at 16057500, squash at 16059000).
- **inst-075754 (kept) and inst-013826:** the generated `JMP_I` (0x4042d8, 0x40442e) is the only control op left in the shadow. The load bounces and gets `cusl=0:rob` in the same tick (15418000; 16002500), because IEW's LSQ walk sets `CUSL` before commit's ROB walk reaches the new load in that cycle (`cpu.cc:468-470`: `iew.tick()` runs before `commit.tick()`). It is re-sent next cycle and fills while the squashing branch is held (squash at 17917500; 16062500).
- **The loads are harness epilogue stack pops** (`POP_R`, `RET_NEAR`), and the jmp is the generated body `jmp` (`jmp_direct` branch form in the fv2 vocabulary), not the harness's closing jmp. So in not_taken mode the generated tests reach jmp-shadow through their own jmp. The same stems in mispredict_taken are already bucketed `jmp_shadow` (inst-013826, -035848, -075754; `speclfb_evidence.json`).
- **No other release path appeared.** In all 5 stems the `cusl` clear comes before the squashing branch's `resolve_visible` (its `setCanCommit`): 16057500 vs 16059000 (inst-012796, `musl` clear; `cusl` was never set), 16002500 vs 16062500 (-013826), 3714500 vs 6142500 (-035848), 16002000 vs 16060500 (-038066), 15418000 vs 17917500 (-075754). The re-sends come 1 cycle (inst-012796, -038066) to 2.4 M ticks earlier. So no load was released by a mispredicted branch that was already `canCommit` with its squash still pending.
- **Scope:** 5 of the 274 fv2 stems were traced. The tag always requires a `JMP_I`/`CALL_NEAR_I` between the squashing branch and the load (`speclfb_analyze.py:110-116`). The traces show the only release path is the jmp reset. A conservative diagnostic would also check that the clear tick comes before the squashing branch's `resolve_visible`. The evidence JSON has only tags, not that tick, so a future `rerun_hits_evidence` field (`released_before_squash_resolve`) would let `diag_speclfb_jmp_shadow` accept the tag without that assumption. A counterfactual on the campaign config was not possible: the existing one-line-fix build (`/work/amulet/jmpshadow_probe/cf/`) has only v1 hooks and lacks the branch-ann flag. Building a new one would be a gem5 edit.
- **Recommendation for the URGENT_TODO DECIDE:** option (a). Count `replayed_after_safe(jmp_in_shadow)` as jmp-shadow by adding it to `diag_speclfb_jmp_shadow`'s known set, ideally with the release-before-resolve field above. With UV6 co-firing in 265 of 274, those hits become UV6 + jmp-shadow (known), and the two tag-only stems become jmp-shadow.

### SL-2 (B). Exception MUSLs are not implemented

- **Code:** the only unsafe sources are `controlUSL` and `memUSL` (`cpu/o3/dyn_inst.hh:174-186`; `isUnsafe()` at `:640-641`). The ROB walk looks at faults only on control instructions (`cpu/o3/rob.cc:528` `if (!inst->readyToCommit() || inst->getFault()!=NoFault …)` inside `if (inst->isControl())`).
- **Mechanism:** a load after an older faulting load or divide (a Meltdown-style shadow, no branch) gets `PrevBrsResolved` and `PrevStoreResolved`, so it is never CUSL or mUSL and fills freely.
- **Contradicts:** paper §5 item 4 and §6.2.2, p637-638 ("loads causing cache misses in the subsequent instructions … are the MUSLs to be protected"). The paper requires this protection. Our criterion currently lists exception MUSLs ("misses by unsafe speculative loads") as `not_covered`, so leaving them out is our choice, not the paper's. Round 2 says what covering them would take.
- **SimSpect:** no fault stimulus in STT_6, so it cannot generate this.

### SL-3 (C). `requsl` hook field is misleading for split loads

Noted only so that nobody reads `requsl=1` as "protected" on a split load (`lsq.cc:1172` vs `base.cc:166`). Hook bugs are out of scope (HOOK_AUDIT).

## CleanupSpec

### CS-1 (B). The 2 NEW E13 hits are an older committed store claiming the squashed install

- **Trace evidence** (cafe2 `/tests/simspect_fixed_20261030/results/STT_6_cleanupspec_v2hooks__20261107/main_tbe8/kept/mispredict_taken/inst-101824.pipeview.txt.gz`):
  - `3862500 L1D:evict line=0x34c0 seq=574 victim=0x3cc0` and `L1D:fill line=0x34c0 seq=574 … nst=E` (a squashed load, younger than the branch seq 572).
  - `3863000 L1D:hit line=0x34c0 seq=562 req=st … st=E:nst=M` (an older store, non-squashed).
  - `6352500 ROB:squash seq=572`.
  - `6353500 L1D:cleanup_skip line=0x34c0 seq=574 … ev=Inv_CLEANUP:st=M`.
  - `inst-102050` is identical: the same store seq 562 and `cleanup_skip … st=M`.
- **Code:** `mem/protocol/MESI_Two_Level-L1cache.sm:2701-2705` `transition(M, Inv_CLEANUP) { clirs2_cleanup_L12InvRoll_skip; …}` skips the L1 invalidate, the rollback and the L2 invalidate.
- **Reading:** the paper intends this. §3.4 p7: "Changes made to the cache by older non-squashed loads that execute after squashed loads due to re-ordering, need to be preserved … corresponding invalidations / restorations are skipped." The ownership rule claims the install for the older store, but it keeps charging the victim 0x3cc0 to the squashed load, which produces a victim-only under_clean.
- **Why it is probably not a leak:** with random L1 replacement (`configs/common/Scheme.py:81`), the store in a non-speculative run would also have evicted a uniformly random line of the same set (set 3, fixed by a non-secret, architecturally accessed address). So the victim's identity carries no information. This is an argument, not a measurement.
- **Decision for Anna:** see round 2 (CS-1) below.

#### CS-1 sole-cause check (2026-11-09, bug-investigate-cs1)

**Answer first.** CS-1 is the **only** cause in every hit where it appears. No hit has it together with UV3, UV4, UV5, CS-EM, H-PAD or H-STK. That makes 18 hit records in 5 runs: 7 stem-mode pairs, 5 distinct tests. It is **not a defense bug**: the code does what CleanupSpec §3.4 p7 says ("corresponding invalidations / restorations are skipped"). The only thing flagged is the victim that our own ownership rule leaves charged to the squashed load. So among the three options, it is **(c): an artifact of our criterion, not of the pipeline or of gem5**. It stays "explained, pending" until Anna answers the existing CS-1 DECIDE (un-charge the victim on random-replacement builds). If she keeps the victim charge, these become sole-cause hits of a behavior the paper intends, still not a deviation from the paper. **No gem5 rerun was needed:** every trace below is the campaign's own kept trace (keep_tmp, TMPDIR `/tmp`), so H-STK does not apply. Nothing was written to `/tmp`.

**Hits covered** (cafe2, under `/tests/simspect_fixed_20261030/results/`):

| run | stems (mode) | S → victim V, upgrader U |
|---|---|---|
| E13 `STT_6_cleanupspec_v2hooks__20261107/main_tbe8` | taken inst-101824, inst-102050 | S=574 / 572 fills 0x34c0, V=0x3cc0, U=562 |
| warm RMW `STT_6_rmw_cleanupspec_footprint__20261109_002545` | nt inst-043313, -072476, -074723; t inst-072476, -074723 | V=0x3980 / 0x3980 / 0x3d80; 0x3d80 / 0x3780 |
| warm control `STT_6_rmwstems_cleanupspec_footprint_ctrl_warm__20261109_060609` | same 5, same seqs and lines | same |
| random RMW `STT_6_rmw_cleanupspec_footprint_random__20261109_094026` | nt inst-043313, -072476; t inst-072476 | same lines (from round 4's `bugwork/cleanupspec_em/em_evidence.json`) |
| random control `STT_6_rmwstems_cleanupspec_footprint_random__20261109_094026` | same 3 | same |

The BUGS.md count "12 tests in 3 runs" missed the 6 random-run records, which round 4 had already attributed as CS-1.

**What was verified, on the 12 E13 + warm traces** (the 6 random-run records rest on round 4's evidence file, each with the single cause `CS1_older_store_upgrade` and a single victim item; I did not re-scan their traces) (`bugwork/cs1/cs1_check.py`, which reuses `judge()` from `STAGE3_gem5/triage/cleanupspec_skip_evidence.py`; output `bugwork/cs1/cs1_check_12.out`):

1. **The CS-1 chain is complete:** fill by S, then E→M store hit by U, then `cleanup_skip … ev=Inv_CLEANUP:st=M`, and no `cleanup_restore` of V.
2. **U is an older, committed instruction of the generated test,** not H-PAD. U's pc is inside the function, U is older than the squashing branch, and U committed. For example, E13 inst-101824's U is `pc1: movq %rax, 8(%rsi)` (rsp+0x30), and warm inst-043313's U is `pc2/last_committed: movq %rdi,(%rsi,%rax)` (rsp+0x3f, a line-crossing store).
3. **No other known signature is anywhere in the trace:** 0 `cleanup_skip why=split` (UV4), 0 `why=nohitinfo` (UV3 / padding RMW), 0 `cleanup_inv` (UV5), and U committed (so not CS-EM).
4. **The hit has only the victim item under today's criterion.** The E13 `triage.json` records came from the checker as it was before the ownership rule, and they also list the install line 0x34c0. Re-running today's `check_footprint` + `specs/leakage/cleanupspec.json` on the kept traces (`bugwork/cs1/reeval_e13.py`, output `reeval_e13.out`, no gem5) gives `issued_in_window=true`, `terms_fired=[under_clean]`, `offending=[L1D 0x3cc0]` for both stems. The 16 RMW-campaign records were already evaluated with the ownership rule, each with a single `under_clean` victim item.

**Trace lines** (E13 inst-101824, `main_tbe8/kept/mispredict_taken/inst-101824.pipeview.txt.gz`):

- `3854000 LSQ:issue line=0x34c0 seq=574 pc=0x401c6c addr=0x34e8 … vaddr=0x7fffffffe4e8`
- `3862500 L1D:evict line=0x34c0 seq=574 victim=0x3cc0 … set=3:way=0:ev=L1_Replacement_OnInstall:st=M:nst=M_I`, plus the `L1D:fill` (DATA_EXCLUSIVE)
- `3863000 L1D:hit line=0x34c0 seq=562 pc=0x401c53 req=st addr=0x34f0 … st=E:nst=M`
- `6352500 ROB:squash seq=572 sq=4`
- `6353000 L1D:cleanup_req line=0x34c0 seq=574 … rb=0x3cc0`
- `6353500 L1D:cleanup_skip line=0x34c0 seq=574 … ev=Inv_CLEANUP:st=M:nst=M`

The warm and control stems show the same shape on line 0x3580 / set 6 (round 3 has the lines).

**Context that bears on the DECIDE, not on attribution:**

1. **In all 7 stem-modes the squashed load S is the access load `movq (%rsi),%rax` at a constant stack slot.** Its vaddr is always 0x7fffffffe4e8 or 0x7fffffffe5a8 (rsp+0x28), and it never depends on a speculative value. U's line is architectural. So in these tests, the line and set involved carry no speculative data.
2. **U and S share a line only because of Stage-2 stack layout.** Alloy's distinct memory slots are placed at adjacent 8-byte offsets in one 64 B line: rsp+0x28 and +0x30, or a store at rsp+0x3f.
3. **The L1D uses random replacement:** `type=RandomReplacementPolicy`, assoc 4, 2 kB (E13 `inst-101824.config.ini:1047-1049`). All five runs use `Cleanup_FOR_L1L2`.
4. **The round-1/2 argument therefore holds for these hits:**
   - Without speculation, U would miss L, install it, and evict a uniformly random way of the same set.
   - Under speculation, S did exactly that, and U then hit.
   - That argument is still analysis, not a measurement. A measurement would mean comparing victim distributions over seeds, which I did not run.

**What I did not do:**

- No gem5 rerun.
- No check of the E13 tbe2 arm, where the same two stems do not hit: `lc_retire` there is about 2000 ticks later.
- `reeval_e13.py` rebuilt the unresolved-branch list from the ann as empty (the stall comes from the sweep), so its window check ran without the branch-unresolved condition. Its `lc_retire` and `fnc_retire` match the campaign record exactly.
- No new diagnostic: `diag_cs1_store_upgrade.py` is already deployed in both warm runs. It is not deployed in E13 (different layout) or in the random runs, which need a `cleanupspec_skip_evidence.json`.

**Scratch:** cafe2 `/tests/simspect_alloy_20261108/bugwork/cs1/` (60 kB: 2 scripts, the builder copy, 2 outputs). I unzipped two trace copies for the re-evaluation and then deleted them.

### CS-2 (A, speculative). Skipped cleanups are retried after older ones, which breaks reverse order

- **Code:**
  - `cpu/o3/lsq_unit_impl.hh:2478-2640` (`issueBufferedCleanupReqs`) walks from `loadTail` (youngest first).
  - On a failed send, `:2557-2560` / `:2610-2613` call `setCleanupReqSkipped(true); setSquashBuffered(true)` and the loop **continues to older loads**. The skipped load is retried only on the next call (`:2524`).
- **Failure sources:**
  - `Sequencer::makeRequest` BufferFull (`mem/ruby/system/Sequencer.cc:859-860`, at least 16 outstanding).
  - The in-flight path returning Aliased when the read-table entry is already gone, or when a side-effect entry or tag already exists (`Sequencer.cc:256-277`, `:1294-1301`).
- **Consequence:**
  1. Older squashed load S1 installs L (evicting V). Younger S2 evicts L from the same set.
  2. Order S1→S2: `transition({NP, I}, Inv_CLEANUP) { clirs_cleanup_L1InvRoll_skip … }` (`L1cache.sm:2678-2683`) skips S1's invalidate **and** its V-rollback.
  3. S2's cleanup then restores L (its recorded victim), possibly from memory after S1's L2 invalidate.
  4. Final state: L (secret-dependent) present, V absent.
- **Contradicts:** Fig. 8b p7 ("Cleanup Executed Loads in reverse order of Load ID") and §1 p2 ("as if the transient loads did not access the cache").
- **Reachability:** the windows I found are narrow, mostly within one Ruby wakeup, except BufferFull. The E13 L1D has only 8 sets, which helps.
- **Detection:** `check_footprint` would flag it (V under_clean; L over_clean after churn, or a net-replay residue).
- **Cheap check:** grep the existing E13 traces for `cleanup_req` lines of one `sq` whose seq order is not descending, followed by a `cleanup_skip … ev=Inv_CLEANUP:st=NP|I`. Round 2 did this check; see below.

## Reviewed and found consistent (brief)

- **SpecLFB:**
  - Both safety walks (`rob.cc:431-563`, `lsq_unit.cc:871-981`): jmp-shadow, the LQ-head skip and sticky PrevNoUnsafe all match the known items. No new sibling was found in the walk itself.
  - Cache refusal of HitUSL misses (`base.cc`).
  - The PC-keyed `Unsafe` set and MSHR "unsafe target" code are dead or commented out (`mshr.cc:667-695`; callers of `update_unsafestate` are commented out).
  - Stalled-load replay happens only after the load becomes safe (`inst_queue.cc:1194-1215`).
- **CleanupSpec:**
  - Correct-path loads are blocked while the LQ is squashing: dispatch through `iew_impl.hh:772-779`, and younger-than-squash instructions are deferred at execute (`:1308-1321`). This matches §3.4.
  - The executed-load L2 invalidate uses the real hit level (`max_depth`, `L1cache.sm:1436-1447`).
  - The Cleanup_FOR_L1L2 knobs are plumbed (`Scheme.py:76-83,133-136`; `MESI_Two_Level.py:167`).
  - The NP-skip when a correct-path access evicted the install is distribution-preserving under random replacement.

## Not reviewed (resume here; round 2 did not get to these)

- **SpecLFB:**
  - Memory-order USL details (stalled loads are excluded from violation checks, `lsq_unit.cc:537,595`).
  - The consistency-model source (§5).
  - Software prefetch.
  - The TLB-miss / deferred-translation flag snapshot.
  - SMT / multi-thread walks.
  - `noncoherent_cache.cc` / `cache.cc` `LFB_RF` paths.
  - Store-forwarding partial overlap.
- **CleanupSpec:**
  - The full L1 cleanup-table state machine (`cleanup_prev_to_set`, `Waiting_Rollback_CLEANUP`, the rollback-space replacement at `L1cache.sm:795-815`).
  - Inflight-cleanup corner cases (`Drop_Load_Cleanup_Inflight`, `Skip_Inflight_Cleanup` with a recycled load).
  - The S-state silent drop on `Inv_CLEANUP` (no PUTS to L2).
  - InternalInterferenceHit's delayed-load queue and its interaction with in-flight classification.
  - Multiple overlapping squashes (`lsq_unit_impl.hh:1934-1940`; an assert on a younger squash).
  - Side-effect-table reservation returns (`CacheMemory.cc:476-487`).
  - The L1I "OTHER L1" replacement on a data miss (`L1cache.sm:~888`, L1I out of scope).
  - Locked RMW / `ldstl`.

## Round 2 (2026-11-08, after Anna's reactions)

### CS-1: why the victim stays charged (origin and reason)

- **Where it comes from:** `URGENT_TODO.md:147` (the CleanupSpec ownership item, decided 2026-11-08), implemented in `STAGE3_gem5/check_footprint.py` `_eval_balance` (comment at `:303`), recorded in `claudelog.md` ("hooks-v2/configs — CleanupSpec ownership rule") and in `specs/leakage/cleanupspec.json` `ownership.rule` ("The victim S's install evicted stays charged to S (never restored → under_clean)").
- **The reason, in plain words:**
  - The rule was added to stop one kind of over-flagging. When an older, non-squashed access uses a line that a squashed load brought in, the paper says that line must be kept (§3.4 p7), so keeping it must not count as a leak. Removing it counts as "too much cleanup" (AMuLeT's UV5).
  - Your condition for approving it was "yes if it cannot miss leaks the other way" (same TODO item). To meet that condition, the change was kept as small as possible: it only stops counting the *line itself*. The *victim* (the line the squashed load pushed out) was left charged, so that any victim that is never put back is still reported. Choosing that was the conservative default, not a judgment about the paper.
  - At the time, the open question was the line, not the victim. The proposal noted that the 2 NEW hits would "stay flagged on the victim term only" and accepted that as a cost of not hiding anything.
- **What is new since then:**
  - The traces show the claimer in both hits is an older *store* that upgrades the line from E to M. The hardware then skips the whole cleanup, both the invalidate and the victim restore (`MESI_Two_Level-L1cache.sm:2701-2705`).
  - The same paper sentence covers the victim: "corresponding invalidations / restorations are skipped" (§3.4 p7). So the paper expects the victim *not* to be restored in this case.
- **Does un-charging the victim "miss leaks the other way"?**
  - The leak would be "an observer can tell that a squashed load touched this set".
  - In these hits, the older non-squashed access touches the same line, hence the same set, on its own. In a run without speculation it would have missed and evicted a line of that set itself.
  - With random L1 replacement (`configs/common/Scheme.py:81`, on for Cleanup_FOR_L1L2), which line gets evicted is random either way. So the observable outcome has the same distribution, and nothing about the squashed load is revealed.
  - This argument depends on random L1 replacement and on the claimer being older and non-squashed. Both are already conditions of the claim.
- **Restated recommendation (yours to decide):**
  - When an older non-squashed access claims a squashed load's install, also stop charging that load's victim, but only on a build with random L1 replacement. Everything else stays as it is. This removes the 2 hits and keeps every other flag.
  - If you would rather not change the criterion, the fallback is to leave the rule as is and treat these 2 hits as explained (older store claims the line, cleanup skipped at M), with this section as the record.

### SL-2: what covering SpecLFB exception shadows would take

Leaving them out is our choice; the paper requires them (§5 item 4, §6.2.2, p637-638). Covering them needs three things:

1. **Stimulus.** Tests where the access and transmitter loads sit behind an older instruction that faults, with no unresolved branch. Today no model or Stage-2 path produces a faulting instruction. It would take a new speculation source in an Alloy model variant (the STL drafts are the precedent for adding a source) plus Stage-2 emitting a faulting op, e.g. a load from an unmapped address or a divide by zero. Both are model or concretization changes, so they need your sign-off.
2. **A run that survives long enough.** In SE mode an unmapped-address fault panics when it reaches commit (`arch/x86/faults.cc:162-166`, "Tried to … unmapped address"). The speculative fills happen before that, so they would be in the trace, but I have not checked that the O3PipeView output is flushed on panic. That needs one smoke test.
3. **Criterion and checker.** `speclfb.json` would get an exception actor mode: squashed by the fault's squash, with the window ending when the fault reaches commit and no "branches unresolved" condition. `check_footprint` would then need to tell a fault squash from a branch squash in the trace, and I have not checked whether the current `ROB:squash` hook line carries the cause.

The code side needs nothing: the gem5 build has no exception source at all (SL-2), so any such test should leak, and that would be the finding.

### CS-2: what the existing traces say

A read-only scan of the 995 kept E13 traces (`/tests/simspect_fixed_20261030/results/STT_6_cleanupspec_v2hooks__20261107/*/kept/`) found that **no squash ever issued more than one cleanup request**: 638 traces have 0 and 357 have 1. CS-2 needs at least two executed cleanups in one squash, so its precondition never arose there. That is not evidence either way at scale; CS-2 stays a by-reading, speculative item. Kept traces are not a random sample of all runs.

### Parked or dropped per Anna

- No misaligned-load option for now, so SL-1 is not pipeline-generated.
- No differential testing.

## Questions for Anna

- **CS-1:** stop charging the victim when an older non-squashed access claims the install (random-replacement builds only)? Recommendation: yes. Fallback: keep the rule and record the 2 hits as explained.
- **SL-2:** cover exception shadows now (needs a model source, a faulting Stage-2 op, an SE smoke test, and a criterion mode), or keep them out of scope this round as our stated choice? No recommendation strength beyond this: it is a scope call. If kept out, `speclfb.json` should say it is our choice and that the gem5 build has no exception protection.

## Round 3 (2026-11-09, unexplained-hits): every NEW CleanupSpec hit in the warm 590-stem runs is explained

**Answer first.** The 6 NEW hits in the warm RMW run (`results/STT_6_rmw_cleanupspec_footprint__20261109_002545`) and the 6 NEW hits in the plain STT_6 warm control on the same stems (`results/STT_6_rmwstems_cleanupspec_footprint_ctrl_warm__20261109_060609`) are **the same 6 tests** (not_taken inst-039102, -043313, -072476, -074723; taken inst-072476, -074723), with the same seqs, lines and events in both runs; the RMW rewrite of the transmitter plays no part (none of the offending events is by the transmitter). Five are **CS-1** (older committed store upgrades a squashed load's E install to M; cleanup skipped; victim never restored). One, not_taken inst-039102, is **AMuLeT UV5** (too much cleaning): the first UV5 our pipeline has produced. All 17 "…_plus_other" hits are also single-cause: the "other" item is always the victim evicted by the same load (UV4 split: 7/7; RMW E→M: 10/10). Nothing is left unexplained. cafe2 paths below are under `/tests/simspect_fixed_20261030/`.

**Method.** Read-only on gem5, models and checkers. Per offending (struct, line, event ids) from each hit's raw check_footprint record, the new `STAGE3_gem5/triage/cleanupspec_skip_evidence.py` follows the actor's events in the kept trace (`diagnostics/traces/<mode>/<stem>.pipeview.txt.gz`, v2 `O3PipeView:simspect:` lines) and the Commit debug lines ("Committing instruction with [sn:N]", needed because committed stores have no O3PipeView retire record in these traces). Output `diagnostics/cleanupspec_skip_evidence.{json,log}` in both runs; 0 items unattributed. No test was re-run.

| Cause | RMW warm (23 hits) | STT_6 control warm (13 hits) | Verdict |
|---|---|---|---|
| UV4 split (line + same load's victim) | 7 | 7 | real defense bug, known (AMuLeT UV4) |
| RMW E→M upgrade by the squashed transmitter (line + same load's victim) | 10 | 0 | known cause, DECIDE pending (URGENT_TODO "CleanupSpec E→M case") |
| CS-1 older committed store E→M | 5 | 5 | known cause, criterion DECIDE pending (CS-1 above) |
| UV5 over-clean after an older committed load | 1 | 1 | real defense bug, known (AMuLeT UV5) |

### CS-1 (5 stems): mechanism with trace lines

Example, control not_taken inst-043313 (`movq %rdi,(%rsi,%rax)` is the last-committed pc2 at 0x401c53; the access load `movq (%rsi),%rax` at 0x401c68 reads rsp+0x28; branch at 0x401c61, held 5000 cycles):
- `3870000 L1D:evict line=0x3580 seq=568 pc=0x401c68 victim=0x3980 … st=M:nst=M_I` and `L1D:fill line=0x3580 seq=568 … st=NP:nst=IS` (Data_Exclusive → E). Seq 568 never retires: it is squashed.
- `3870500 L1D:hit line=0x3580 seq=561 pc=0x401c53 req=st addr=0x35bf size=1 … st=E:nst=M` (plus the second half at 0x35c0: a line-crossing store). Seq 561 committed at 3863000 (Commit trace) and is older than the branch (seq 566). It drained from the store buffer only after S's fill, because S's GETS held the line.
- `6362000 ROB:squash seq=566 sq=4`; `6363000 L1D:cleanup_skip line=0x3580 seq=568 … ev=Inv_CLEANUP:st=M`; no `cleanup_restore` of 0x3980.

The other four: not_taken inst-072476 (S=580 fills 0x3580, evicts 0x3980; U=573 store to 0x35b0, committed 3863500; skip at 6362000), not_taken inst-074723 (S=570, V=0x3d80, U=563), taken inst-072476 (S=575, V=0x3d80, U=568), taken inst-074723 (S=599, V=0x3780, U=592). In every case the upgrader is an Alloy-level committed store to the access load's stack line, and the leaking access (S) is squashed. **Verdict:** CS-1 as in round 1-2: the code does what the paper says (§3.4 p7, "corresponding invalidations / restorations are skipped"); the hit exists because the ownership rule keeps the victim charged. Not a real bug unless Anna keeps the victim charge (open DECIDE). With these, CS-1 has 12 stems over 3 runs (E13 2 + 5 + 5).

### UV5 (inst-039102, not_taken): mechanism with trace lines

Control run (the RMW run is identical up to a 500-tick shift of U's hit):
- Program: lc (pc2, 0x401c4b) is `movq (%rsi,%rax),%rdi` with rsi = rsp+0x40, an 8-byte load at 0x35bf that crosses into 0x35c0 (seq 557); the access load (pc4, 0x401c60, seq 564) is `movq (%rsi),%rax` at rsp+0x28 = 0x35a8, the same line 0x3580; the branch is seq 562 (0x401c59), held until 6361000.
- `3869500 L1D:evict line=0x3580 seq=564 victim=0x3d80` + `L1D:fill line=0x3580 seq=564 … st=NP:nst=IS` → E. S=564 is squashed.
- `3869500 LSQ:issue line=0x3580 seq=557 … addr=0x35bf size=8 split=1 line2=0x35c0`, then `3870000 L1D:hit line=0x3580 seq=557 req=ld addr=0x35bf size=1 st=E:nst=E`. U=557 is older than S and the branch, and committed (retire 3871500 = lc_retire).
- `6361500 ROB:squash seq=562 sq=4`; `6362000 L1D:cleanup_req line=0x3580 seq=564 … rb=0x3d80`; `6362500 L1D:cleanup_inv line=0x3580 seq=564 … ev=Inv_CLEANUP:st=E:nst=M_I` (+ PUTX to L2); `6375500 L1D:cleanup_restore line=0x3d80 seq=564`.
- Final state: 0x3580 absent from L1D although a committed load used it after S's fill; without speculation U would have missed and installed it (evicting a random way of set 6). So the cache state is not "as if the transient loads did not access the cache" (§1 p2).

**Code (why it is not caught):** the paper says such reorderings "can be detected by the LQ-SEFE, and corresponding invalidations / restorations are skipped" (§3.4 p7). This build has no such check. The cleanup entry's `toEvict_L1` comes only from the squashed load's own hit level (`mem/ruby/system/Sequencer.cc:1300-1346`), `issueBufferedCleanupReqs` decides per squashed load from its own flags only (`cpu/o3/lsq_unit_impl.hh:2510-2600`), and `transition(E, Inv_CLEANUP, M_I)` invalidates unconditionally (`MESI_Two_Level-L1cache.sm:2692-2699`). Only a store's E→M upgrade escapes, by the M-state skip (CS-1). The `InternalInterferenceHit` delay queue (`lsq_unit_impl.hh:249-257, 3033-3110`) only fixes the older load's timing, and skips split loads anyway (`:3041`). So this is not specific to the split older load: any older committed load that hits a younger squashed load's install gets its line removed.

**Verdict:** real defense implementation bug, the known AMuLeT UV5 (too much cleaning), reached by the pipeline for the first time (1 stem per warm run; it was "not seen in the sample" before). Adversarially: S's address here is a constant stack slot, so this test does not leak a secret, but the mechanism makes "is L present after the run" depend on whether a squashed load touched L, which is the UV5 channel. **Checker caveat:** the record is flagged `inconsistent`: the count reports `over_clean` (its rule needs only a window squash), while the net-state replay puts 0x3580 in `outside_window`, because S's fill (3869500) is before lc_retire (3871500): the lc is U itself, which retired late. `issued_in_window` = count ∨ net, so the hit stands; the disagreement is a DECIDE (URGENT_TODO, "UV5 / over_clean window").

### Diagnostics written (both warm runs)

- `diag_uv4_split.py` + `.md` (`PHASE real_bug`, UV4): 7 + 7 stems.
- `diag_cs1_store_upgrade.py` + `.md` (`PHASE known_pending`, so it is ranked after real bugs and kept out of NEW without being called an artifact): 5 + 5 stems.
- Canonical copies in `STAGE3_gem5/triage/diag/` (README updated); evidence builder `STAGE3_gem5/triage/cleanupspec_skip_evidence.py` (also on cafe2). `bucket_hits.py` now leaves NEW = 11 in the RMW run (10 RMW E→M, waiting for its DECIDE; 1 UV5) and NEW = 1 in the control (UV5). No UV5 diagnostic yet: one stem, not a recurrence. Not deployed to the E13 run (different layout) or to the cold / TBE-sweep campaigns (the cache-random session's runs); they need their own evidence file.

### Other AMuLeT builds (latest runs, read-only)

- **SpecLFB v2hooks** (`results/STT_6_speclfb_v2hooks__20261107`): the 4 `NEW_other` hits (taken inst-035498, -059424, -104466, -124367) **are the jmp-shadow**, as the triage said. In all four the load is a stack pop after a `JMP_I` that follows the held branch (e.g. inst-059424: branch seq 588, `JMP_I` seq 598, pop seq 603); `LSQ:unsafe … cusl=0:musl=1:prevbrsres=1` (CUSL never set because of the jmp-shadow); first `LSQ:issue … sent=0:bounced=1:usl=1`; then `LSQ:usl_flag … f=musl:v=0:by=rob` (the older store resolved, 3721000 / 3730000 / 3730500 / 3730000); then `LSQ:issue … sent=1:usl=0` and `L1D:fill line=0x3d40` while the branch is still held (resolves at ~6213000-6220500). Without the jmp-shadow, `cusl=1` would have kept it USL. Attribution holds; they belong to the jmp-shadow candidate, not a new cause.
- **InvisiSpec v2hooks** Spectre and Futuristic (`results/STT_6_invisispec_v2hooks_{spectre,futuristic}__20261107`): 0 NEW (Spectre README; claudelog 2026-11-08 hooks-v2 for both); nothing to add.
- **CleanupSpec E13** (`results/STT_6_cleanupspec_v2hooks__20261107`): its 2 NEW are CS-1 (rounds 1-2). The cold runs (RMW cold 0 NEW; control cold 10 UV4) were not re-examined.

## Round 4 (2026-11-09, bug-investigate-em): the RMW E→M cleanup skip (CS-EM) is root-caused

**Answer first.** The E→M hits are a **real CleanupSpec defect of the UV3 family** (it breaks the same paper assumption, "RFOs are issued non-speculatively", p8 §4) **through a different protocol path from UV3**: the squashed RMW transmitter's `ldst` *hits* a line that an older squashed load S installed in E and upgrades it to M at execute time; S's cleanup then meets M and takes the CS-1 skip transition, which the paper meant only for older non-squashed stores (§3.4 p7). It is not CS-1 (the upgrader is squashed, not an older committed store), not a checker artifact (the plain-load controls on the same stems never hit), and not in AMuLeT's list. AMuLeT's UV3 patch (hit metadata in `writeCallback`, AMuLeT §4.6 p11) would give the RMW an `L1Hit` and leave L in M, so by reading it does not fix this path (unverified: no patched build run). No test was re-run; everything below comes from the campaigns' own kept traces.

**Protocol path (paths relative to the AE tree's `src/`).**
1. The RMW's `ldst` carries `StoreCheck`, so `Sequencer::makeRequest` issues `RMW_Read` with secondary type `ST` (`mem/ruby/system/Sequencer.cc:984-993`); the L1 maps `ST` to `Event:Store` (`mem/protocol/MESI_Two_Level-L1cache.sm:329-341`), and the mandatory-queue data path triggers it with no speculation check (`:855-905`; only `LD` has the cleanup-inflight drop, `:863-869`).
2. `transition({E,M}, Store, M)` (`:2294-2298`): E→M at execute, by a squashable instruction. A plain load would take `transition({S,E,M}, {Load, Expose})` (`:2257`) and leave E.
3. After the squash, younger first: the RMW's cleanup is `cleanup_skip why=l1hit` (it installed nothing); S's `CLEANUP_EXECUTED` request finds M and `transition(M, Inv_CLEANUP)` (`:2701-2705`, action `clirs2_cleanup_L12InvRoll_skip` `:1737-1749`) marks S's L1 invalidate, L1 rollback and L2 invalidate done without doing them.

**Trace, cold run not_taken inst-021314** (cafe2 `/tests/simspect_fixed_20261030/results/STT_6_rmw_cleanupspec_footprint_cold__latest/diagnostics/traces/mispredict_not_taken/inst-021314.pipeview.txt.gz`): S = seq 3098 `MOV_R_M ld rax, DS:[rax + rsi]` (0x4042f0); U = seq 3100 `OR_M_I ldst t1, DS:[rax + rsi]` (0x4042f4, the xmit); branch seq 3091 (0x4042e3), held 5000 cycles. `17064500 L1D:fill line=0x75c0 seq=3098 … msg=DATA_EXCLUSIVE` → E; `17066000 L1D:hit line=0x75c0 seq=3100 pc=0x4042f4 req=st msg=ST … ev=Store:st=E:nst=M`; `19417500 ROB:squash seq=3091 sq=4`; `19418000 L1D:cleanup_skip line=0x75c0 seq=3100 … why=l1hit`; `19418000 L1D:cleanup_req line=0x75c0 seq=3098 … mode=exec:lvl=MEM`; `19418500 L1D:cleanup_skip line=0x75c0 seq=3098 … ev=Inv_CLEANUP:st=M:nst=M`. Offending: L1D 0x75c0 (event 4450) and L2 0x75c0 (event 4392), `under_clean`.

**Counts** (new `STAGE3_gem5/triage/cleanupspec_em_evidence.py`, which reuses `cleanupspec_skip_evidence.py` and re-checks each chain strictly: S and U never committed and younger than the squashing branch, U at the xmit pc, exactly one E→M hit, U `why=l1hit`, exactly one st=M skip; output cafe2 `/tests/simspect_alloy_20261108/bugwork/cleanupspec_em/`):

| Campaign (cafe2 `results/`) | NEW before | E→M (pure) | rest of NEW |
|---|---|---|---|
| `STT_6_rmw_cleanupspec_footprint_cold__latest` | 82 | 72 (all cold; items L1D + L2 on S's line) | 9 UV4 split, 1 E→M + UV4 mixed (not_taken inst-126731: a split RMW, half E→M, half `why=split`) |
| `STT_6_rmw_cleanupspec_footprint_random__latest` | 58 | 44 (42 cold, 2 warm) | 9 UV4, 3 CS-1, 1 UV5, 1 mixed (inst-126731) |
| `STT_6_rmw_cleanupspec_footprint__20261109_002545` (warm) | 11 | 10 (items: S's line + S's victim; = round 3's "RMW E→M" set) | 1 UV5 |
| `STT_6_rmwstems_cleanupspec_footprint_random__latest` (plain-load control) | 14 | 0 | 10 UV4, 3 CS-1, 1 UV5 |

The 72 cold stems with the original plain-load transmitter: 72/72 not hit in `STT_6_rmwstems_cleanupspec_tbe_l2_3_dc_2_cold__latest` (cold, `L2_TBEs=3`) and 72/72 not hit in `STT_6_rmwstems_cleanupspec_footprint_random__latest`. So the speculative E→M upgrade is what disables S's cleanup. In all 252 E→M items S is older than U, and S is the access load that produces U's address register, so U hits S's line only for one class of loaded values: whether L survives the squash depends on the speculatively loaded value (the information UV3 leaks, here through S's line). Example stems: not_taken inst-001690, -003983, -017175, -020424, -021314, -030059; warm: not_taken inst-021314, -037689, -067666, -073452, -073892, taken inst-017175.

**E13 fanout-v2 campaigns** (`/tests/simspect_alloy_20261108/results_fv2/E13_STT_6_fv2{,fp}__latest`): cannot contain this case: the fv2 vocabulary has no memory RMW (`fv2_vocab.jsonc`; the `orq $0` in those tests is register-form) and their 18 + 16 hits have no kept traces. Not examined further.

**Diagnostic (drafted, not deployed):** `STAGE3_gem5/triage/diag/diag_cleanupspec_em.py` + `.md` (`PHASE real_bug`, `CATEGORY UV3-EM`, reads `cleanupspec_em_evidence.json`). Installing it in the three RMW campaigns would take NEW from 82 → 10, 58 → 14 and 11 → 1; adding the UV4/CS-1 diags (not installed in the cold/random runs yet) would leave cold 1 and random 2 (the mixed inst-126731 and one UV5).

**Decision for Anna** (URGENT_TODO "CleanupSpec E→M case", updated): (a) count it under UV3 (same broken assumption); (b) count it as a separate CleanupSpec bug found by us ("UV3 family, E→M path"), with its own diagnostic; (c) (b), but only after the cheap confirmation that a build with AMuLeT's UV3 `writeCallback` patch still leaks on these 72 stems (a separate gem5 build; gem5 edit needs your OK). Recommendation: (c) for the claim, and install the diagnostic as real_bug now so the NEW lists shrink to the genuinely unexplained.

## Round 5 (2026-11-09, bug-investigate-cs2): CS-2 reverse-order cleanup is real but not reached

**Answer first.** CS-2 is a real defect, and it would leak if it happened. Our tests have never triggered it. In 2,843 kept CleanupSpec traces and 360 scratch reruns, every cleanup send succeeded on the first try, in descending seq order. There were 0 retried sends, 0 out-of-order sends and 0 `Inv_CLEANUP` skips at NP/I. Shrinking the L1 TBE pool, the stimulus proposed earlier, cannot trigger it: TBE exhaustion never makes a send fail, and `--L1_TBEs` ≤ 2 deadlocks this build. Verdict: **real but not reached**. Not found by us. Paths below are relative to the AE tree's `src/`.

**What must happen (all of it, in one squash):**
1. **Two executed squashed loads in one set.** An older squashed load S1 misses L1, installs L (secret-dependent address) and evicts V. A younger squashed load S2 misses into the same L1 set, and random replacement (`configs/common/Scheme.py:81`) picks L as its victim. With E13 geometry (2 kB, 4-way, 8 sets) the second step has probability 1/4 per same-set miss.
2. **S2's cleanup send fails, while S1's send succeeds in the same `issueBufferedCleanupReqs` call.** The walk goes youngest-first (`cpu/o3/lsq_unit_impl.hh:2510-2627`). A failed send sets `CleanupReqSkipped` and the walk continues to S1 (`:2557-2560`, `:2610-2613`). S2 is re-sent only on a later call (`:2524-2527`, or `reissueSkippedCleanupReq` `:2920-2970`). A send fails only when `dcachePort->sendTimingReq` returns false (`:2725-2733`), which happens in exactly these cases:
   - **Executed mode (S2 already returned):** only `Sequencer::makeRequest` BufferFull, i.e. `m_outstanding_count >= m_max_outstanding_requests` (`mem/ruby/system/Sequencer.cc:859-860`). The count covers only distinct-line entries in the read/write request tables (`:234`, `:301`), and the limit is fixed at 16. `--max_outstanding_requests` is parsed (`configs/ruby/Ruby.py:89`) but never passed to `RubySequencer` (`configs/ruby/MESI_Two_Level.py:165-169`), so `Sequencer.py:72`'s default of 16 holds. The cleanup itself is always `Issued` (`Sequencer.cc:279-284`), and the L1 mandatory queue is unbounded (`MESI_Two_Level.py:180`, `MessageBuffer()`). A full L1 TBE pool only recycles requests inside the L1, so it never rejects a send.
   - **In-flight mode (S2 issued, not returned):** `Aliased` in three cases: the line is in the write table only (`Sequencer.cc:269-272`); the line is in neither table (`:274-276`); or the fill and eviction already happened (`issueCleanupRubyRequest`, `:1300-1302`, MSHR victim or tag present). Since an NP load allocates its L1 entry only at the fill (`MESI_Two_Level-L1cache.sm:2144-2151`), the third case is the window between S2's Ruby fill and the LSQ marking S2 returned. That window is about one response latency. It is also exactly the window in which S2 has just evicted L. So this is the realistic path: S2 fails as in-flight, S1's executed cleanup goes out in the same call, and S2 is re-sent as executed on the next call.
3. **The order then breaks the rollback.** S1's cleanup meets L absent: `transition({NP, I}, Inv_CLEANUP)` (`MESI_Two_Level-L1cache.sm:2678-2683`) skips both S1's invalidate and its restore of V. S2's cleanup then invalidates its own line and restores its victim, which is L.

**Security direction.** The final L1 state is L present and V absent. That is S1's footprint, the state after S1 ran with no cleanup at all. If S1's address depends on a secret (S1 is the transmitter, or it feeds one), the attacker can probe L's presence in the set. So this is a **leak (under-cleaning)**, the same channel CleanupSpec exists to close (§1 p2; Fig. 8b p7 requires reverse order). V's identity is random under random replacement and carries nothing. L does carry the secret. `check_footprint` would flag it: V `under_clean` plus L restored by a load that never installed it.

**Hook observability.** The v2 hook prints `L1D:cleanup_req` only on a successful send (`lsq_unit_impl.hh:2735-2752`). A failed send prints nothing (only `DPRINTF(IEW)` / `DPRINTF(LSQUnit)`, which our runs do not enable). The trace signature of CS-2 is therefore a `cleanup_req` whose seq is **younger** than an earlier `cleanup_req` of the same `sq`, or any `cleanup_req` of an `sq` at a later tick than that sq's first send. Its consequence would show as a `cleanup_skip … ev=Inv_CLEANUP:st=NP|I`.

**Scan of existing traces** (scanner `cs2_scan.py`, output `scan_all.{json,log}`, cafe2 `/tests/simspect_alloy_20261108/bugwork/cs2/`):

| Trace set (cafe2 `/tests/simspect_fixed_20261030/results/`) | traces | with a send | squashes with ≥ 2 sends | out-of-order / retried | NP/I `Inv_CLEANUP` skips |
|---|---|---|---|---|---|
| `STT_6_cleanupspec_v2hooks__20261107/*/kept` (E13 v2hooks; 1,032 headtail) | 2,027 | 357 (313 in-flight sends, all first-try) | 0 | 0 | 0 |
| `STT_6_rmw_cleanupspec_footprint_cold__20261109_060609` | 489 | 489 | 372 | 0 | 0 |
| `STT_6_rmw_cleanupspec_footprint_random__20261109_094026` | 267 | 264 | 189 | 0 | 0 |
| warm RMW + 3 plain-load controls | 60 | 43 | 5 | 0 | 0 |
| **total** | **2,843** | **1,153 (1,764 sends)** | **566 (max 3 sends)** | **0** | **0** |

All 566 multi-send squashes issued every send in one tick, in descending seq order (e.g. random not_taken `inst-132084`: `19718000 cleanup_req seq=3143 line=0x7e00`, then `seq=3123 line=0x7580`, both `mode=exec lvl=MEM`). No pair of sends in one sq overlapped (no S2 rollback line equal to S1's line). **The two-stage E13 campaigns** (`/tests/simspect_alloy_20261108/code_20261109/results/E13_STT_6_fv2{,fp}__latest`) **cannot be scanned**. Their `_sweep_raw/*.json` records carry only check_footprint's per-line counts and `n_squashes`, no hook events, and the campaigns kept no traces (`keep_tmp` off). Checking them would mean re-running with `keep_tmp`. Given the 0/566 result on the closest stimulus, I did not do that.

**Scratch reruns (TBE knob only).** 240 stems: the first 120 per mode of the RMW cold stems whose traces have a ≥ 2-send squash. The config is an exact copy of `runconfigs/footprint/run_config_STT_6_rmw_cleanupspec_footprint_cold.jsonc`, differing only in `--L1_TBEs`, `gem5.jobs` 4 → 8, the explicit stem list instead of `sample_fraction`, and the output paths. Diffs and configs are in `bugwork/cs2/run_config_cs2_l1tbe*.json`; logs are `run_l1tbe*.log`.

| `--L1_TBEs` | runs | result | multi-send squashes | out-of-order |
|---|---|---|---|---|
| 8 (control, not_taken) | 120 | 120/120 hit (reproduces the campaign) | 120 | 0 |
| 4 (not_taken; the taken half was stopped for disk space) | 120 | 120/120 hit | 120 | 0 |
| 2 | 240 | 240/240 `panic: Possible Deadlock detected` | n/a | n/a |
| 1 | 240 | 240/240 `panic: Possible Deadlock detected` | n/a | n/a |

Kept traces: `bugwork/cs2/kept_traces/cs2_l1tbe{8_ctrl,4}__inst-001690.pipeview.txt.gz`. The rerun workdirs were deleted (`--keep-tmp` costs ~334 MB per test; don't use it for sweeps).

**What stimulus would reach it.** Either of these:
- **(a) BufferFull:** ≥ 16 distinct-line loads/stores outstanding in the Sequencer at the moment the squash's cleanups are issued, plus two same-set executed squashed misses. That means a long wrong-path burst of independent cold misses to distinct lines. With L1_TBEs=8 the extra requests wait in the Sequencer table, so they would count. Our tests have about 2-6 memory ops in the window, and the wrong-path loads after the transmitter are `not_issued`.
- **(b) The in-flight race:** S2's data must reach the L1, evict L and allocate, in the same cycle that `issueBufferedCleanupReqs` runs, before S2's response marks it returned. That needs the squash cleanup pass, which waits for the squash head to reach the ROB head (`lsq_unit_impl.hh:2488-2493`), to coincide with S2's fill. It also needs S2 in S1's set and random replacement choosing L. Our 5000-cycle branch holds mean every in-window load has long returned by squash time. That is why the 313 in-flight sends in E13 all found their load still in the read table.

Neither (a) nor (b) is reachable by a config knob on this build: the TBE knob does not cause send failures and deadlocks below 4, and `--max_outstanding_requests` is not plumbed. (a) needs a generated test with ≥ 16 distinct-line wrong-path misses plus a same-set pair, which is a model/Stage-2 shape (owner approval). (b) needs a short branch hold tuned to S2's fill latency, which is a stimulus change.

**Verdict:** real (by code), a secret-dependent leak if reached, **not reached** by any generated test so far (0 / 1,764 sends; 0 / 566 multi-send squashes). Not found by us.

## Round 6 (2026-11-09, bug-investigate-e13new): the E13 fanout-v2 NEW hits are a harness artifact feeding known UV3 / CS-EM, plus a stack-address reproducibility artifact

**Answer first.** Of the 52 NEW hits per E13 testset (fv2 and fv2fp alike), 29 (all `mispredict_taken`, `ld`) are **known UV3 / CS-EM, triggered by an RMW that the harness creates, not the test**: in `mispredict_taken` tests the function ends in a backward `jmp` to `end_block` (2993/3000 taken tests; 0/3000 not_taken, which end in `retq`). The BTB does not know this jmp yet, so fetch falls through past the end of `.text` into zero bytes, and `00 00` decodes as `add %al,(%rax)` (`ADD_M_R`, an RMW). Its `ldst` issues a write request on whatever line `rax` points to (the test's stack frame), and CleanupSpec cannot undo it. Cold lines: a `req=st` GETX miss-install, then `cleanup_skip why=nohitinfo` = the UV3 signature exactly (`diag_uv3_rmw.md`). Lines already in E from a squashed load: an E→M hit, then the load's cleanup skips at M = CS-EM (round 4). So inst-029763 is CS-EM *with* an RMW, the padding one. The 18 NEW stems that "did not reproduce" are not Ruby nondeterminism: **gem5 SE puts the binary path on the initial stack, so the stack address depends on the length of TMPDIR**. The campaign ran in `/tmp` and the bucket-fv2 reruns ran in `bugwork/bucket_fv2/tmp/<batch>` (a 97-char TMPDIR vs 4). That shifted every stack line by 0xc0, which changes L1 set conflicts. With TMPDIR=/tmp, a rerun is bit-identical to the campaign. Verdicts: UV3 / CS-EM are real defense bugs, already known (no new CleanupSpec bug). The padding RMW is a **harness artifact** (an actor outside the generated test). The TMPDIR dependence is a **harness reproducibility artifact**, not a gem5 bug. Nothing is left unexplained except 3 non-padding NOREPRO stems that look like UV4 but are not traced (below), and the 16 br_x hits (UV4 evidence; existing DECIDE).

**Padding RMW, trace** (fv2 taken inst-005142, cold; bucket-fv2 rerun trace cafe2 `/tests/simspect_alloy_20261108/bugwork/bucket_fv2/shim_E13_fv2/diagnostics/traces/mispredict_taken/inst-005142.pipeview.txt.gz`; the rerun is stack-shifted, so the campaign's line is 0x75c0, not 0x7500):
- The asm ends `pc5: movq %rsi,%rdx; imulq %r10,%rdx; jmp .LBB0_5` (`.LBB0_5` = end_block, earlier in the function). The local build (same as/ld steps as `gem5_common.py:127-147`) ends `.text` at 0x401c99, with zeros after it. `cache_setup_info.delta` 10146 maps that to 0x40443b, the first fetch past the jmp.
- `O3PipeView:fetch:17296500:0x00404439:2:3164: JMP_I : wrip` and then `0x0040443b … ADD_M_R : st t1b, DS:[rax]` (seq 3165-3167), `0x0040443d … ADD_M_R`. Here rax = `leaq 64(%rsp)`, the transmitter's base.
- `17299500 LSQ:issue line=0x7500 seq=3165 pc=0x40443b … req=ld`; `17300000 L1D:miss … req=st:msg=ST … ev=Store:st=NP:nst=IM` + `L1D:fill`; `17304000 L2:fill … msg=GETX`. `17300000 ROB:squash seq=3164` (the jmp resolves taken) squashes 3165, while the window branch seq 3127 is held to 18484000.
- `18485000 L1D:cleanup_skip line=0x7500 seq=3165 pc=0x40443b … why=nohitinfo`. The line stays in L1D and L2, so `under_clean` (L1D + L2). This is UV3 exactly.

**CS-EM via padding, trace** (fv2 taken inst-029763, warm; copy in `bugwork/e13new/traces/fv2_taken_inst-029763.rerun_bucketfv2.pipeview.txt.gz`): `.text` ends at 0x401c9e (local build: `401c9c: eb c9 jmp 401c67`, then zeros). S = seq 574 `ld r13,[r11+0x8]` (0x401c7b): `3864500 L1D:fill line=0x34c0 … msg=DATA_EXCLUSIVE` and `L1D:evict … victim=0x36c0`. U = seq 585 `ADD_M_R : ldst t1b, DS:[rax]` at 0x401c9e: `3929500 L1D:hit line=0x34c0 seq=585 … req=st … ev=Store:st=E:nst=M`. After the squash, `6354500 L1D:cleanup_skip … seq=585 … why=l1hit` and `6355000 L1D:cleanup_skip line=0x34c0 seq=574 … ev=Inv_CLEANUP:st=M:nst=M`, so S's install and victim are never undone. This is the round-4 path (`MESI_Two_Level-L1cache.sm:2294-2298`, then `:2701-2705`), with the padding RMW as U. The fv2 vocabulary indeed has no RMW. The RMW comes from the harness layout.

**Counts** (cafe2/cafe3 `bugwork/e13new/classify_padding.py` → `classify_fv2{,fp}.json`, campaign raw records only, no gem5. A hit is "padding" when a campaign `skip_drop` entry on an offending line has pc ≥ the test's `.text` end, plus the cold delta; every hit has padding fetches, but only these touch an offending line):

| E13 NEW (per testset, fv2 = fv2fp) | stem-modes | class | verdict |
|---|---|---|---|
| taken ld, padding actor on the offending line | 29 (18 traced: fv2 17 UV3-shaped `why=nohitinfo` + 1 CS-EM; fv2fp 15 + 3 CS-EM [inst-032677, -068118, -077935]; 11 not traced, padding pc found in the campaign records) | UV3 / CS-EM via padding RMW | known defense bugs; harness actor |
| ld, no padding, did not reproduce | 7 (not_taken inst-009280, -054084, -072971, -073020; taken inst-009280, -054084, -072971) | taken inst-009280 rerun with TMPDIR=/tmp: identical to the campaign (2117 events), S = seq 574 `split=1` → `cleanup_skip why=split` = **UV4**; the others have the same line+victim shape (0x3580 + 0x3b80/0x3d80/0x3780), not traced | UV4 (1 confirmed, 6 probable) |
| br_x | 16 (8 per mode) | UV4 evidence (bucket-fv2) | existing DECIDE (UV4 for br_x) |

**Reproducibility, mechanism and test.** `gem5_common.process_one` makes the workdir with `tempfile.mkdtemp(prefix=f"gem5_{name}_")` (`gem5_common.py:1170`) and passes `--cmd=<workdir>/<stem>` (`:400-410`). gem5's x86 SE loader copies `filename` = argv[0] and the argv strings onto the initial stack, then sets rsp = `stack_min` (`src/arch/x86/process.cc:770-774, 907-920, 962-963, 1042`). So rsp moves down by about 2× the path-length change (16-aligned), and the test's `andq $-64,%rsp` keeps the shift whenever it crosses 64 B. Experiment (cafe2 `bugwork/e13new/rerun_tmpdir.py`: the campaign config verbatim; only TMPDIR and the explicit stem differ):

| stem (taken) | TMPDIR | events | hit | offending |
|---|---|---|---|---|
| inst-005142 | campaign (`/tmp`) | 4703 | yes | L1D/L2 0x75c0 |
| inst-005142 | `/tmp` (rerun) | 4703 | yes | L1D/L2 0x75c0 (identical) |
| inst-005142 | 123-char `bugwork/e13new/tmp_long…` | 4715 | yes | 0x74c0 |
| inst-009280 | campaign (`/tmp`) | 2117 | yes | L1D 0x3580 + 0x3b80 |
| inst-009280 | `/tmp` (rerun) | 2117 | yes | identical |
| inst-009280 | 123-char | 2152 | **no** | — |

**Does it matter?** (1) It is not a gem5 bug, and it is not Ruby nondeterminism to report: gem5 is deterministic for a fixed argv. (2) It does matter for our methodology. Results depend on a hidden input (the workdir path length), so a test's stack lines, its L1 set conflicts and, on the 2 kB/4-way L1D, its hit/no-hit can change with where the run happens. Hit counts are stable as a population, but the per-stem attribution of E13 (and E12a; inst-042604's 196 vs 207 events is very likely the same cause, not checked) needs reruns at the campaign's path length. (3) Fix for triage now: rerun with a TMPDIR whose path length equals the campaign's (`/tmp`, or a symlink of the same length). Fix for the harness: a DECIDE (URGENT_TODO), e.g. pass a fixed-length `--cmd` (a short fixed symlink or a cwd-relative `./t`).

**What I did not do.** I did not trace the 11 padding NOREPRO stems or the 6 probable-UV4 stems (the keep_tmp limit), and I deployed no diagnostic. A `diag_padding_rmw` (offending line touched by an actor pc ≥ `.text` end; PHASE disqualifier, category "harness actor") is drafted only as the classifier above. The decision is Anna's: a disqualifier (artifact) or credit as UV3/CS-EM. Scratch: cafe2 `/tests/simspect_alloy_20261108/bugwork/e13new/` (1.4 MB; 3 cited traces in `runs/` + `traces/`); cafe3 `…/bugwork/e13new/` (classifier output). The 4 gem5 workdirs I created were deleted (listed in each `runs/*/created_workdirs.txt`).

## UV5 count (2026-11-09, bug-investigate-uv5)

**Answer first.** UV5 occurs **0 times** in the four E13 CleanupSpec campaigns at the 2% sample (STT_6_fv2, STT_6_fv2fp, STT_6_u_fv2, STT_6_u_fv2fp; 14,900 ok records, 384 hits). It occurs exactly once in each of the four 590-stem STT_6 CleanupSpec runs where round 3 found it (not_taken inst-039102, sole cause), and 0 times in the cold RMW run and the cold TBE control. So UV5 stays at **1 test** (1 stem, 4 runs). The E13 count needed no rerun: the campaigns' raw check_footprint records already carry the exact signature for every test (hits and non-hits), and the scan finds no test in which an older non-squashed access ever claimed a squashed load's line (0 claims of any kind, so also 0 CS-1). A conservative one-cause diagnostic is drafted, not deployed.

**UV5 signature, from the source and from inst-039102's trace.**

- A squashed load S (younger than the squashing branch) misses L1D and installs line L in E, evicting V: `3869500 L1D:evict line=0x3580 seq=564 victim=0x3d80`, `L1D:fill line=0x3580 seq=564 … st=NP:nst=IS`.
- An older load U (seq < S, older than the branch, never squashed, committed) then hits L: `3870000 L1D:hit line=0x3580 seq=557 req=ld … st=E:nst=E` (U = the last-committed split load, retire 3871500).
- After the squash, S's own cleanup invalidates L anyway and restores V: `6362000 L1D:cleanup_req line=0x3580 seq=564 … rb=0x3d80`, `6362500 L1D:cleanup_inv line=0x3580 seq=564 … ev=Inv_CLEANUP:st=E:nst=M_I`, `6375500 L1D:cleanup_restore line=0x3d80 seq=564`. The removed line is one S installed, but a committed load used it, so by CleanupSpec §3.4 p7 the invalidation must be skipped. The cleanup message that over-cleans is S's `Inv_CLEANUP` (`MESI_Two_Level-L1cache.sm:2692-2699`, unconditional at E); the build has no LQ-SEFE check (`Sequencer.cc:1300-1346`, `lsq_unit_impl.hh:2510-2600`).
- Footprint: L ends absent though committed U used it (without speculation U would have missed and installed L). In check_footprint's record (ownership rule, `specs/leakage/cleanupspec.json` "ownership") the line's `per_line` entry has `claimed_by_older ≥ 1` (claim `actor_seq` 564, `owner_seq` 557), `invalidated ≥ 1`, `d_install < 0`, `d_victim = 0`, and the offending item is `over_clean`. inst-039102: L1D 0x3580 only (L2 keeps the line: the L1 invalidate sends PUTX). The record is `inconsistent` (replay puts L outside W because S's fill precedes lc_retire, U being the lc): the open DECIDE "UV5 / over_clean window".

**What distinguishes it.** UV5 is the only cause whose offending item is `over_clean` (a line removed that should stay); every other CleanupSpec cause leaves something behind (`under_clean`):

| cause | actor and path | what the cleanup does | record shape |
|---|---|---|---|
| **UV5** | squashed load installs L; an older committed **load** hits L | S's `Inv_CLEANUP` at E invalidates L (should be skipped) | claim + invalidation on L → `over_clean` on L |
| CS-1 | squashed load installs L; an older committed **store** hits L (E→M) | S's cleanup skips at M; V never restored | claim, no invalidation; victim `under_clean` |
| UV3 | speculative store/RMW miss-installs L | `cleanup_skip why=nohitinfo` | L `under_clean` (L1D + L2) |
| UV4 | squashed split load | `cleanup_skip why=split` | L + victim `under_clean` |
| CS-EM | squashed RMW hits S's E line (E→M) | S's cleanup skips at M | S's line (+ victim) `under_clean`, no claim (U squashed) |
| H-PAD | padding `add %al,(%rax)` past `.text` (harness actor) | then UV3 or CS-EM | `under_clean`; actor pc ≥ `.text` end |
| H-STK | TMPDIR-length stack shift in reruns | n/a | reproducibility artifact; this count reads the campaigns' own records, so it does not apply |

**Method.** `uv5_scan.py` (cafe2 `/tests/simspect_alloy_20261108/bugwork/uv5/`, copies on cafe3 and cafe1) reads every `<mode>/_sweep_raw/*.json` record of a campaign (latest batch wins) and counts: records with any claim, the UV5 shape (claim + invalidation + `d_install < 0`), `over_clean` offending or outside-window items, any negative-balance line, `inconsistent` records, and lines that the net-state replay finds absent versus the reference but that are not offending. Positive control: on the four 590-stem runs it returns inst-039102 and nothing else. The hook emits the `hit` events the claim needs in this configuration (238 `L1D:hit` lines, parsed as kind `hit` by `code_20261109/STAGE3_gem5/gem5_common.py`, in the e13new trace `bugwork/e13new/traces/fv2_taken_inst-029763…`), and the campaigns' criterion copy has the ownership rule. Output: `scan_<campaign>_<host>.json`. No gem5 was run; no `/tmp` dirs were created.

| campaign (host, `code_20261109/results/E13_STT_6_<t>__latest`) | mode | records (ok / error) | hits | records with any claim | UV5 matches | UV5 as sole cause |
|---|---|---|---|---|---|---|
| fv2 (cafe2) | not_taken | 1864 / 8 | 31 | 0 | 0 | 0 |
| fv2 (cafe2) | taken | 1864 / 8 | 60 | 0 | 0 | 0 |
| fv2fp (cafe3) | not_taken | 1864 / 8 | 31 | 0 | 0 | 0 |
| fv2fp (cafe3) | taken | 1864 / 8 | 60 | 0 | 0 | 0 |
| u_fv2 (cafe3) | not_taken | 1861 / 13 | 37 | 0 | 0 | 0 |
| u_fv2 (cafe3) | taken | 1861 / 13 | 59 | 0 | 0 | 0 |
| u_fv2fp (cafe1) | not_taken | 1861 / 13 | 37 | 0 | 0 | 0 |
| u_fv2fp (cafe1) | taken | 1861 / 13 | 69 | 0 | 0 | 0 |
| 590-stem warm control, warm RMW, random control, random RMW (cafe2 `/tests/simspect_fixed_20261030/results/`) | not_taken | 294 each | 6 / 11 / 7 / 133 | 3-4 | 1 each (inst-039102) | 1 each |
| same four runs | taken | 296 each | 7 / 12 / 7 / 134 | 2 | 0 | 0 |
| cold RMW, cold TBE control | both | 294 / 296 | 242+247 / 4+6 | 1 per mode | 0 | 0 |

There are no `over_clean` items at all in the E13 records, inside or outside the window, and no negative-balance line. The only replay-vs-reference absences that are not offending (21, 17, 35 and 25 records, all `mispredict_taken`) are actor-evicted victims outside the window (`under_clean_outside_window`, checked item by item), not over-cleaning.

**Draft diagnostic (not deployed).** cafe2 `/tests/simspect_alloy_20261108/bugwork/uv5/diag_draft/diag_cleanupspec_uv5.{py,md}` (`PHASE real_bug`, `CATEGORY UV5`, `ORDER 23`, kinds ld/br_x/other_x, `NEEDS_GEM5 False`). It reads the run's own raw record and buckets a hit only when every offending item is `over_clean` with a claim by an older access (`owner_seq < actor_seq`), `invalidated ≥ 1`, `d_install < 0` and `d_victim ≥ 0`; mixed hits stay NEW. Self-test (`python3 diag_cleanupspec_uv5.py <run_dir>…`, log `diag_draft/selftest_cafe2.log`): exactly inst-039102 in the four 590-stem runs, 0 in the cold runs and all four E13 campaigns. Deployed to the warm control it would take that run's NEW from 1 to 0 and the warm RMW run's from 11 to 10 (the CS-EM stems).

**What I verified and what I did not.** Verified: the record-level signature on the four runs where the trace chain was proven (round 3), the E13 counts over every ok record, that the claim machinery and the `hit` events are live in the E13 code and config. Not verified: the 8-13 error records per mode (no footprint record), whether "non-squashed" always means "committed" outside inst-039102 (holds in an `ok` run; trace-checked only there), and why the fanout-v2 corpora never produce an older access that touches a squashed load's line after its fill (0 claims, also no CS-1). A UV5 variant without U's own `hit` event (U fed by S's fill) would be invisible to this signature; it was not observed, and the Ruby Sequencer rejects a load to a line with a pending load as `Aliased` (`mem/ruby/system/Sequencer.cc:311-318`), so the LSQ retries it and it then hits.

## Why the fanout corpus never produces UV5 (2026-11-09, uv5-shape)

**Answer first.** UV5 needs an older committed load U whose address becomes ready *after* a younger squashed load S to the same line has missed. In the fanout corpus `STT_6_fv2fp_rmw` no committed load ever has a computed address: 0 of 93,041 not_taken tests, against 1.7% of the old flat STT_6. Nothing in the model forbids it. Two-stage generation loses it through the Stage-1.5 solver order. The 2-ALU address chain that made inst-039102 work fires only on warm caches. One committed load in U's address chain makes UV5 fire on warm and cold caches (hand variant inst-939102). So the missing precondition is a **committed load with a late address**. The proposal below adds that generally, at Stage 2. Old-corpus UV5 rate: **1 in 590** (warm), 0 in 590 (cold).

**1. What UV5 needs (inst-039102 traces, the code, AMuLeT Table 9).**

- Program shape: an older load U that commits, a mispredicted branch, and a younger load S on the squashed path. U and S touch the same 64-byte line. In inst-039102, U is pc2 `movq (%rsi,%rax),%rdi` at rsp+63 (the lc, a split load), and S is pc4 `movq (%rsi),%rax` at rsp+40, line 0x3580.
- Cache state: S must miss L1D and install the line. Warm runs use the shrunk 2 kB L1D, where the prologue zero-fill evicts the lowest frame lines, so 0x3580 is absent (evicted at 3709500 by fill seq 534). Cold runs flush every frame line.
- Timing: S's request must reach L1D before U's. Then U is held, because a load to a line with a pending miss is retried (`Sequencer.cc:311-318`), and U hits S's fill. Warm trace: S issues at 3861000 (address from `leaq 40(%rsp)`) and misses. U's address sits behind `mov; not; lea`, so U issues 1 cycle later (3861500), is retried at 3862500-3868000, and hits at 3870000 after S's fill at 3869500.
- Then CleanupSpec invalidates the line anyway (`cleanup_inv … Inv_CLEANUP st=E`, `MESI_Two_Level-L1cache.sm:2692-2699`).
- AMuLeT Table 9 (`fu-2025-amulet.pdf` p12) has the same shape with a much larger gap. The NSL at PC 0x40113c, older than the SL at 0x40114d, executes at cycle 1423, 273 cycles after the SL (1150). That is consistent with an NSL whose address waits on a memory access. AMuLeT's own campaign also finds UV5 rarely: 4 of 32 instances (PB-2).

**Cold rerun of inst-039102 (cafe3, same CleanupSpec footprint config, `--L2_TBEs=3`, `TMPDIR=/tmp`): no UV5.**

- Warm reproduces the hit (`claimed_by_older` 1, over_clean).
- Cold: U issues first (17222500), misses and fills. S issues after U's data (17443500), hits, and its cleanup is skipped (`cleanup_skip why=l1hit`).
- The cause: during the long clflush+mfence prologue, the 2-ALU chain finishes before any load may issue, so the older U wins.
- So a short ALU chain is not enough in general; U's address must wait on something that cannot finish before the barrier, such as a load.

**Hand variant inst-939102.** It is inst-039102 plus two committed instructions after pc1: `movq 1024(%rsp),%rcx; addq %rcx,%rax`. The change is value-neutral (the slot is zero-filled and rcx is otherwise unused). Annotation addresses at or after pc2 were shifted by +11, checked with clang+nm. Result: **UV5 in both warm and cold**. Cold trace: S misses at 17287500 and fills at 17491500; U issues at 17492000 and hits; `cleanup_inv` at 19789000.

Files on cafe3 under `/tests/simspect_alloy_20261108/bugwork/uv5shape/`: configs `cfg*_{warm,cold}.json`, logs `run*_*.log`, traces `traces/*.pipeview.txt.gz`, and `inst-939102_v1.README`. Own `/tmp` dirs were deleted.

**2. Measuring each precondition in the corpus.** Tools: `STAGE3_gem5/triage/uv5_shape/uv5_timing_scan.py` (asm + ann, not_taken, static dataflow depth: ALU 1, load 4, div 20) and `committed_rf_scan.py` (XML).

| precondition (not_taken) | old flat STT_6 (20,000 random of 100k) | STT_6_fv2fp_rmw (all 93,041) |
|---|---|---|
| any committed instruction | 56% | 11.4% |
| a committed load U | 3,963 (19.8%) | 2,052 (2.2%) |
| U and a squashed load S on the same line (static) | 3,548 (17.7%) | 1,797 (1.9%) |
| U's address needs a producer | 348 (1.7%) | **0** |
| same line and U's address ready after S's | 317 (1.6%) | **0** |
| same, U later by ≥3 (behind a load or div) | 170 (0.85%) | 0 |

The 590-stem sample (294 not_taken stems) has 8 stems with the last row's shape (U's address ready after S's). One of them is inst-039102, the UV5 hit (warm). Its other claimed stems (inst-043313, -072476, -074723) are CS-1, where U is a store.

**XML level: is the gap in Stage 1.5 or in Stage 2?** It is in Stage 1.5. Stage-1.5 XML (`STT_6_fv2fp_full/xml`, 20,000 random) has **0 rf edges into any committed instruction** and 0 committed loads with an rf-fed `inaddr`.

| source | rf edge into a committed instruction | committed load with rf-fed address |
|---|---|---|
| old STT_6 XML (9,931) | 7.4% | 1.0% |
| today's `STT_6.als`, flat (`results/dedup_audit_2026-11-09/randprobe/flat_{default,seed11,seed12}`, 1,999 each) | 6.6-9.6% | 0.8-1.6% |
| Stage 1.5 on one core, default order (600) | 0 (and only 2 of 600 have any committed instruction) | 0 |
| Stage 1.5 on the same core, seeded random order (`out_seed1`, 600) | 4 (299 have committed instructions) | 1 |

So the model allows the shape, and Stage 1.5's capped default-order runs (2,326 per core) fill the cap with programs that put all 3 added instructions in the speculative region. Minimality is not the cause. Stage 2 cannot add it either: fv2 fillers are register-only and may not touch memory (`parsexml.py:2025-2045`, rules 1-3, 6), and splices only re-route edges that already exist.

**3. Proposal (for Anna; nothing implemented).**

- **(A) Randomized Stage-1.5 order (the existing DA-3).** This keeps the corpus model-exact and fills the committed region (50% of tests in the one-core probe). But rf-fed committed loads stay rare (1/600), and the chains it produces are ALU chains, which fire UV5 only on warm caches. Necessary for coverage in general, not sufficient for UV5.
- **(B, recommended) A Stage-2 "committed access" fanout option.**
  - What it adds: with probability p per test, one read-only committed load L from a slot drawn uniformly from the test's own Mem pool, placed before the lc.
  - What it changes: with probability q, the value of L (0, because sandbox slots are zero-filled) is added value-neutrally into the address index of one existing committed access, so that access's address waits on a load.
  - Where it lives: in `parsexml.py` pass 5 fv2, as a new filler class (this relaxes fv2 rule "no memory" only before the window). Or, with less risk to the existing pipeline, as a post-pass like `make_rmw_corpus.py` (asm rewrite + verified annotation re-resolution) producing a new corpus `STT_6_fv2fp_rmw_ca`.
  - Why it is general: it adds "older non-speculative memory traffic that races the window's accesses", which every load defense orders against. That covers CleanupSpec's missing LQ-SEFE check (UV5, and CS-1 if a store variant is allowed), InvisiSpec expose/validate ordering, and SpecLFB's first-speculative-load rule. It is also the missing precondition of ReCon R-SA-6: 0/3,746 E6 tests have a committed pair.
  - What else it changes:
    - (i) More committed loads delay lc_retire, so the window starts later. The inconsistent inst-039102 record comes from exactly this (the open "UV5 / over_clean window" DECIDE).
    - (ii) For STT the inserted instructions are committed and value-neutral, so they do not change the model's leak claim. For ReCon and SPT, a new committed load can reveal or declassify, which can remove a model-predicted leak (fewer hits, never invented ones). The test then no longer matches its Alloy instance exactly. Record it in the ann (`fanout_v2.committed_access`) so it can be excluded or bucketed.
    - (iii) Every PC shifts, so this means a new corpus build (Stage 2 only, no Alloy).
  - Tuning risk: moderate. The motivation is UV5, but the knob never looks at S's line or the defense. The slot is uniform over the test's own pool, and those slots share S's line about 88% of the time only because Alloy's memory atoms live in 1-2 frame lines. Keep p and q in provenance, and before adopting, measure on a 1,000-test sample how every defense's hit buckets move, not only UV5.
- **(C) An Alloy forcing partition** ("a committed load whose `inaddr` is rf-fed"). This is model-checked but targeted, and a model-side change. Not recommended.

**4. UV5 rate in the old corpus, honestly.** 1 test in the 590-stem warm sample (294 not_taken + 296 taken), so 1/590. The 95% Poisson interval is about 1/23,000 to 1/106. The sample is the RMW-eligible ld-transmitter subset, not a uniform draw. The same stem repeats in the 4 warm or random runs, but that is one observation. Cold: 0/590, explained above. Static check: in the full old corpus 1.6% of not_taken tests have the shape, and 1 of the sample's 8 such stems fired, which is consistent with roughly 1 in 600-1,000 not_taken warm tests. With the shape absent, the expected count in the 12,000+ fanout tests is 0, which matches what was observed. (If the fanout had the old rate of the shape, about 12 UV5 hits would be expected.)

## UV5 on the footprint corpus (uv5-footprint, 2026-11-10)

**Answer first.** The D shape does fire on the new corpus. Footprint D stem **inst-010868** (not_taken) gives a UV5 under `cold` with the same mechanism as old inst-048191: it fires at unresolved stall 2500, 5000 and 10000 and under the old fixed timing, and does not fire under `warm` or `full`. firstdet-final drew `warm` for it (random_all). Per cold D-shaped test the two corpora have the same rate: old 2/211 (0.9%, all 211 old D stems run cold: exactly the known inst-048191 and inst-039460), footprint 1/180 (0.6%; 1/150 + 0/30, run cold under T2rt's random timing). The "about 3%" expectation was too high. At about 0.8%, the 152 cold D tests firstdet-final ran should give about 1.2 hits, so 0 has p of about 0.3. Hypothesis 1 (timing randomization) is rejected and hypothesis 3 (`full`) cannot fire. The rest is chance plus dilution: random_all puts only a third of tests in `cold`, the only setup that can fire.

**Rerun evidence** (cafe2 `/tests/simspect_alloy_20261108/bugwork/uv5_footprint/`, TMPDIR=/tmp, configs in `cfg/` derived by `mkcfg.py`, which changes only testset_dir, results_name and, where named, cache_setup or the sweep block):
- inst-048191 and inst-039460 reproduce under the old T2r config with both the old (cafe3 oldfanout) and the new (firstdet_final) code (E1/E2). Under the new T2rt sweep with cold forced, both fire at every unresolved stall {2500, 5000, 10000} × resolved {0, 500, 2500} tried (E3). The resolved stall never applies: these tests have no resolved Alloy branch, and neither do 323 of the 338 D rows firstdet-final had finished. Neither fires under warm, full (T2rt or old timing) or a 4×L1D full sweep.
- inst-010868: cold old timing hit; cold u2500/u5000/u10000 hit; warm (its random_all draw), full, verbatim T2rt: no hit (E7).
- Old D 211 cold: 2 hits; footprint D 150 cold: 1 hit; footprint D 30 cold and 30 full: 0 (E5/E6).

**Mechanism (all three firing tests)**, from `uv5_race.py` over the kept traces. The chain head H is a committed load to line A that misses to memory. U's address waits on H's data. U is the committed load to line B. S is a squashed load to B whose address does not depend on H (in all three it comes from a store-forwarded speculative load). S is fetch-bound behind the cold code's L1I misses, so it issues its miss to B before H's data returns. U is then held behind S's outstanding miss and hits S's install 500 ticks after S's fill, and CleanupSpec's cleanup invalidates the line U owns.

| test | H (line A) issue → data | S (line B) fetch / issue / fill | U (line B) issue, result |
|---|---|---|---|
| old inst-048191 | 3123 (0x7580) 17233000 → 17453501 | 3156: 17419500 / 17424000 / 17507000 | 3130 17507500, L1 hit on S's install |
| old inst-039460 | 3124 (0x7580) 17224000 → 17404501 | 3164: – / 17407500 / 17477500 | 3134 17478000, L1 hit on S's install |
| footprint inst-010868 | 3124 (0x7580) 17234500 → 17455001 | 3187: – / 17426000 / 17509000 | 3134 17509500, L1 hit on S's install |

**Why most D tests do not fire (both corpora): the static proxy is loose.** For the S that touches U's line first, the race needs S's issue to come before H's data. That held in 2/97 old D tests with a same-line pair and in 1/119 footprint D tests (0/21 in the D30 sample). Three patterns block it. Each is shown below against inst-048191.
- **S's address depends on the committed chain** (register-sourced shape). In footprint inst-002726, the xmit address `rsi` is `r10`, the output of committed pc1. S is fetched at 17411500 but issues only at 17530500, after H's data (17444501) and after U (17449500, which misses and installs B). S then hits. About 40% of the footprint D30 S's wait over 100k ticks between fetch and issue like this.
- **The chain head is on S's line**, so the line is installed by a committed load before S exists. In footprint inst-000229, H (3117) is `(rsp+64+r8)` = line 0x75c0 itself: it misses at 17222000 and its data arrives at 17407501. S is fetched at 17413500 and hits. With zero-filled memory every indexed address equals its base, and the bases rsp+40..64 cover only two lines, so this is common.
- **U is store-forwarded** (no cache access). In footprint inst-008227, pc1 stores to `(r9,rax)` and U = pc2 loads the same address (stlf at 17410500). This pattern appears in 26/150 footprint D tests.
- **Where the static proxy falls short:** the D scan's "U's address later" counts ALU ops as 1, so U being 1-2 ALU ops later is invisible against a ~180k-tick memory miss. Its same-line test uses |Δoff| < 64 whenever an index register is present, so it is a "maybe". Dynamically, what matters is the memory-miss chain head and S's fetch time.
- **The firing race is narrow.** In inst-048191, H's miss took 220k ticks against about 185k in the D30 footprint tests, consistent with queueing behind the cold setup's last clflush writeback (0x7e00, MEMORY_WB 17252500) and the ifetch misses. S's fetch (about 17.41-17.42M) and H's data (about 17.40-17.46M) are within tens of thousands of ticks in most tests.

**`full`.** It cannot produce this UV5, for two reasons. (1) On the CleanupSpec build the L1D uses `RandomReplacementPolicy` (run `config.ini` `[system.ruby.l1_cntrl0.L1Dcache.replacement_policy]`). A sweep of exactly the L1D size (8 lines per set) therefore evicts each set's resident frame line with probability of only about 1/8, and the frame lines stay in L1D: in the D30 full sample, litmus committed loads were 59 hits against 6 misses (cold: 29 hits, 37 misses). In inst-048191's full trace, frame line 0xd580 survives in set 22 while sweep line 0x2580 is evicted. `cache_setup.py`'s docstring ("the prologue zero-fill's sandbox lines are evicted from L1D by the sweep") holds only for LRU. (2) Even with a 4×L1D sweep (`cache_setup_fill_bytes=131072`; U loads then miss L1D, 40 misses against 27 hits), 0/33 fire: H's data comes back from L2 long before S is fetched, so U always goes first.

**Verdict and general fixes.** This is not a corpus or model regression: the footprint corpus contains the shape, it fires at about the same rate, and the zero is sampling. No timing knob is implicated. General, non-targeted options, for Anna to DECIDE:
- (a) Accept it. UV5 of this shape is a cold-only event in about 1% of D-shaped tests, and it will appear with more cold samples.
- (b) Make `full` match its documented intent on random-replacement builds. Use a sweep of several L1D sizes (a config-only knob, `gem5.cache_setup_fill_bytes`), or fix the docstring. This matters for every CleanupSpec `full` result, not for UV5.
- (c) Fanout diversity. More squashed loads whose address comes from a non-cache source independent of the committed chain (stlf, constant) would raise the precondition rate. That is a property of the corpus, not a forcing.
- Recommendation: (a) for UV5 plus (b) as a separate cleanup.

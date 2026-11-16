# SPT v2 and hit triage: findings of the resolve-hooks session (2026-11-07 to 11-09)

What this session found while classifying the fixed-harness hits, consolidating the SPT model into `SPT_6_oneLP_v2.als`, and checking it. The canonical v2 change table and Anna's decisions are in [`../../../state/EVAL_MANIFEST.md`](../../../state/EVAL_MANIFEST.md) ("SPT_6_oneLP_v2: what changed"); the per-campaign hit tables are in [`../../bug/BRANCH_ANNOTATION_AND_FORCE.md`](../../bug/BRANCH_ANNOTATION_AND_FORCE.md) §7. This page records the reasoning, evidence, tools and gotchas that live nowhere else. Open items are in [`../../../state/OPEN.md`](../../../state/OPEN.md) ("2026-11-09 — resolve-hooks").

## 1. Bottom line

- **Every round-2 and round-4 hit is classified; 0 are left NEW.** recon-modded (E2) = the known real bug A2, 185 / 185 test×mode runs in round 4. Every SPT (E11) hit is a model or concretization artifact: each transmitter operand is public under SPT's own taint rules. STT upstream (E3) has 0 hits.
- **A second checker gap was found and fixed:** gem5 sometimes prints no O3PipeView record for the lc/fnc instruction, which made `before_fnc` pass vacuously or `lc_retired` fail. The retire tick is now filled from the Commit trace. It is in git HEAD and in both cafe2 copies (`/tests/simspect`, `/tests/simspect_fixed_20261030`), checked 2026-11-09 21:15.
- **SPT was consolidated into `STAGE1_alloy/models/SPT_6_oneLP_v2.als`** (sha256 `acb1f2e2…`; the original `SPT_6_oneLP.als`, 713d0904, is unchanged). Anna approved v2 as the SPT model on 2026-11-08.
- **Later correction (model-audit S-1, not this session):** my v2-4 change, which narrows declassification, combines with the model's transitive check so that declassifying a load-derived value never takes effect. This errs toward too many tests, as Anna asked, but it gives guaranteed false-positive hits and hides the feature that separates SPT from STT. A fix is drafted as `proposed/SPT_6_oneLP_v3.als` (Option A). Whether to run v2 or v3 is Anna's open call (URGENT_TODO DA-8 and "which SPT model and testset shape").
- **The "does v2 lose any old test" check is inconclusive.** All three runs timed out without a counterexample, and the 8 h cafe2 run never started the SAT search (§6.3).

## 2. What the checker checks, with respect to resolved and committed

`check_ld` (`STAGE3_gem5/check_ld.py:78-159`) scores a load transmitter as in the window only if every criterion below passes. Each is written per record to `window-results.json` as `criteria.*`.

| criterion | passes when | source |
|---|---|---|
| `lc_retired` | the instruction the model names as last-committed (lc) actually retires in gem5; otherwise the record is disqualified as a setup artifact | `check_ld.py:95-99` |
| `signal_seen` | the transmitter has a signal tick: the LSQ "Executing load" tick, or the pipeview complete tick as a fallback | `check_ld.py:84-87` |
| `after_lc` | signal > lc's retire tick | `check_ld.py:107` |
| `before_fnc` | signal < the first-not-committed (fnc) instruction's retire tick | `check_ld.py:108` |
| `branches_unresolved` | every branch the model marks unresolved is still unresolved at the signal. "Resolved" = `resolve_visible`, the commit-side `setCanCommit()` tick every defense keys on; a branch that was held and then squashed never resolves | `gem5_common.py:1026-1060` |
| `data_obtained` | the load got its data inside the window, from a cache packet or a store forward; applies only when the LSQ trace exists | `check_ld.py:115-145` |

Validity (did gem5 run the shape the model asked for; `gem5_common.execution_validity`, `:1088-1147`): `resolved_correct` (no correctly-not-taken branch mispredicted on the correct path), `window_opened` (the oldest non-transmitter unresolved branch mispredicted), `stall_applied` (every stalled branch that resolved was held), `force_applied` (every planned force printed `predict_force`). `resolved_before_signal` is reported but does not gate (`gem5_common.py:970, 1281`); see §8 item 3.

Commit boundaries come from the pipeview retire tick. Since 2026-11-07 a missing lc/fnc record is filled from the Commit trace's first `Committing instruction` tick (`gem5_common.parse_commit_ticks` + `fill_retire_from_commit`, flagged `retire_from_commit_trace`). Where both exist they agree on 273 / 282 instructions and differ by exactly one cycle on the other 9.

## 3. SPT's taint rules, from the gem5-spt source (cafe2 `/work/gem5-spt/src/cpu/o3/`)

These are what `spt_cond_slice.py` implements and what every SPT verdict here rests on. They match the SPT paper §6 "Untaint rules".

- `rob_impl.hh:236-250`: a load always taints its destination; any other instruction taints its destination iff an argument is tainted.
- `commit_impl.hh:944` (`--configImpFlow=Lazy`): a branch's squash is delayed iff its arguments are tainted. gem5 prints "(Lazy) A branch ... made pending" when that happens, so the absence of that line for a transmitter branch is gem5-spt's own verdict that its arguments were public.
- `lsq_unit_impl.hh:1185-1207, 1262-1279` and `cpu.cc:2132`: a transmitter reaching the visibility point untaints its arguments (declassification).
- `rob_impl.hh:800`: forward untaint (an output whose inputs are all public becomes public).
- `rob_impl.hh:853-878`: backward untaint only through `mov`, and through `add`/`sub`/`adc`/`sbb` with exactly one tainted source.
- Not usable: `--trackInstsFile=all` aborts at the first 64-bit register (`regfile.hh:280` asserts `size + offs < taintVec.size()`, an off-by-one in the logging helper). The triage uses the "made pending" lines and the `VPUntaints` stat instead.

## 4. Hit classification, rounds 2 and 4

Tables: `BRANCH_ANNOTATION_AND_FORCE.md` §7.2 (round 2) and §7.6 (round 4).

- **Round 2 ran on stale testsets (my mistake).** The 10-30 fixed configs read `testsets/`, which was built before the 2026-06-03 models (e298a9e) existed. Round 4 reran on `testsets_latest` with `runconfigs/fixed_20261030/*_fixed_latest.jsonc` (`sample_fraction` 0.02). Provenance hashes: `STAGE3_gem5/triage/testset_provenance.py`.
- **Round 4** (2% sample, cafe2 `/tests/simspect_fixed_20261030/results/*_fixed_latest__20261108_012818`):
  - STT_6 / stt: 0.
  - STT_6 / recon-modded, ld: 91 / 94 tests (not_taken / taken), all A2.
  - SPT, ld: 57 / 48. The x86 slice finds 87 constant and 18 declassified.
  - SPT, str: 74 / 60. The slice finds 95 constant and 39 declassified. No store checker exists (§8).
  - SPT, br_x: 51 / 51. The slice finds 73 constant and 29 declassified. All 102 reproduced, and gem5 never made the branch pending.
- **How the SPT verdicts were proven:**
  - (1) The x86 slice under the rules in §3 gives a constant or declassified operand for every hit, and none tainted.
  - (2) Faithful re-runs at each hit's grid point never print "made pending" for the transmitter. `VPUntaints` is 0 on the constant cases and 1 on the declassified ones.
  - (3) Two equal-length counterfactual edits flip the result: inst-043417 with its store's address register changed, and inst-080310 with its constant source replaced by a load. In both, gem5 now makes every transmitter instance pending and the hit disappears (cafe2 `triage/counterfactual/`).
- **Why the SPT hits exist:** the old model's protection set contains values SPT does not protect (§5 items 1, 5, 6), and concretization feeds constants into unfed reads.

## 5. SPT model problems found in `SPT_6_oneLP.als` (pre-v2), and where each went

| # | problem | evidence | status |
|---|---|---|---|
| 1 | no `rf_from_most_recent_writer` (skeleton drift; only `STT_6.als:161-170` had it) | 63% of a 3,000-instance sample has an rf edge past a newer writer, so parsexml's program is not the instance; 68% of the old testset | fixed in v2-1 |
| 2 | protection seed ignores perturbations, so minimality can never shrink it and the RI-only SPT core is empty | simspect-c8's probe; old RO+RI core = 0 at `but 3` | fixed in v2-2 (simspect-c8's fix, audited here, §6.1) |
| 3 | `one_insecure_…` (exactly one leaker) instead of the skeleton's `not secure_…` (at least one) | SPT alone pruned two-leaker tests | fixed in v2-3 |
| 4 | declassification removed the whole rf+ddi backward cone (`.*(~op_edges_p)`), so it declassified values SPT still protects and their leaks were never generated | SPT untaints backward only per §3 | v2-4 narrowed it to `.*(~(rf_p[p]))`, but that overshoots (S-1, §1); v3 Option A drafted |
| 5 | one-step propagation lag: chains of constants stay protected | constant-derived transmitters 2.4% of old instances → 9.6% under v2 | P3, left out on purpose (Anna prefers too many tests); classified by `diag_constaddr_load` / `diag_brx_const_condition` |
| 6 | unfed reads: an input reads a state with no rf edge, so concretization supplies a constant | 28% → 33% of instances | P5, a skeleton-wide fact for all models; not applied |

Also found by another session: the 4-bit `Int` wrap in the `#`-based operand caps (URGENT_TODO 🚨 CHECK). It is inherited from the skeleton; this session did not touch it.

## 6. v2: audit, validation, and the "lost" checks

### 6.1 Why the seed fix (v2-2) loses nothing

At no perturbation the new seed equals the old one (simspect-c8's `eq_base` query: 0 counterexamples). Under every perturbation the new seed is a subset of the old one. The propagation is monotone (each subtracted term grows as the set shrinks), and so is `secure_*`. The non-monotone exactly-one clause is evaluated only at `no_p`. So an instance that was useful under the old seed is useful under the new one. Their log's label "sha 65eae944" is the SHA-1 of the unchanged file, not a different base.

### 6.2 Validation (Mac, `results/spt_v2_20261108/`)

- **Satisfiable:** 50 instances in 9 s, and 3,000 in 2 min, at `exactly 6`.
- **Shape census, old → v2** (`spt_testset_shapes.py`):
  - stale rf 63% → 0;
  - clean 23% → 58%;
  - unfed read 28% → 33%;
  - constant-derived transmitter 2.4% → 9.6%.
- **Differential, both sides under v2's facts** (so only realizable instances count):
  - in both: ≥500 (capped);
  - gained by v2: ≥500. A census of 300 gained: 227 clean, 72 constant-derived, 1 unfed read.
  - sanity (`old_only_check`: old-useful instances exist under v2's facts): ≥50 (capped), so the lost query below is not vacuous.
- **Cores derived from v2**, all in `STAGE1_alloy/models/proposed_twophase/`:

| core | `but 3` | `but 4` |
|---|---|---|
| RI-only `SPT_6_oneLP_v2_core_ri.als` (used) | 546 | 5,000 (capped) |
| conservative, no RO/RI | 546 | |
| RO+RI | 6 | nothing in 15 min |

The later full Stage-1 run (simspect-c8) gave k4 ≈ 145,000 with no convergence, so SPT has no small core set. That is URGENT_TODO "SPT has no small core set".

### 6.3 The "lost" checks: old-useful and not v2-useful

| run | scope | result |
|---|---|---|
| Mac, 2026-11-08 14:51-16:21 | v2 as a whole (`results/spt_v2_20261108/differential/lost.als`) | timed out at 90 min, no counterexample. `run.log` says `rc=0` because of a wrapper bug: it read `$?` after `$(date)` (noted in the log) |
| simspect-c8, Mac, 4 h | v2-2 alone | timed out, no counterexample (claudelog 2026-11-08 18:36) |
| cafe2 `gem5_dev`, 2026-11-09 00:22-08:22 UTC | v2 as a whole, same `lost.als` (sha256 aab0b0c9 on both machines) | `exit=124` (timeout), no count. `lost_cafe2.out` ends at Kodkod's "translating to cnf …", so in 8 h the solver **never started the SAT search**. This is no evidence either way |

What stands: v2-1 drops only instances no register machine can realize; v2-2 loses none by §6.1; v2-3 only adds. Only v2-4 can lose an old instance, through minimality, because a larger protection set can keep a perturbed program insecure. That remains unproven. A cheaper check that would finish is in OPEN.md.

## 7. Recon A2: store-to-load forwarding bypasses the STT check

Bug write-up: [`../../bug/recon_SLF_stlf_bypass/NOTE.md`](../../bug/recon_SLF_stlf_bypass/NOTE.md). This session re-verified it on the fixed harness.

- **Round 2:** 7 tests × 2 modes, all 14 with the signature.
- **Round 4:** 185 / 185.
- **The signature** (`STAGE3_gem5/triage/recon_stlf_check.py`):
  - the LSQ prints `STL_CHECK: load PC <xmit> isTainted=1 isSpeculative=1` right after the transmitter executes;
  - `Forwarding from store idx N to load` follows;
  - Commit marks the load ready in the ROB before the window-opening branch's `resolve_visible`.
- **Load→load shapes:** in 4 of the 7 round-2 tests the Alloy shape is load→load. At run time every value is 0, so the address still equals an older store's and the mechanism is the same.
- **Checker fix:** the first version of the checker looked only at the transmitter's first execution, and a squashed first execution can come before the one that forwards. It now checks every execution.

## 8. Not understood (kept open)

1. Why gem5-spt keeps committed stores' DynInsts alive to the end of the run, which is why their O3PipeView records are missing. §2's fill handles the effect; the cause is untraced.
2. inst-043417's transmitter branch is re-fetched and re-mispredicts about every 15 cycles while the window is open (seq 565, 603, 641, …). Only the first instance is scored. The likely cause is a wrong-path `retq` returning into the function; untraced.
3. `resolved_before_signal` is False in every hit record of 450 / 600 round-2 SPT ld tests, 32 / 50 br_x tests, and 3 / 14 recon test×mode pairs.
   - Many of the late branches are younger than the transmitter or on the wrong path.
   - The sweep grid's resolved-branch stall holds others: inst-080310 hits only at grid points 1-2 because its fnc is a resolved branch.
   - The criterion counts younger resolved branches, which may be the wrong rule.
4. **SPT store transmitters (`str`) have no checker.** `check_ld`'s fallback scores the store's complete tick. Anna's 2026-11-08 decision puts speculative-store transmitters out of scope for KV3 (STT, D-TLB). Whether that also covers E11's `str` kind has not been decided.

## 9. Tools (`STAGE3_gem5/triage/`; run inside the cafe2 container from `/tests/simspect_fixed_20261030`)

| tool | does |
|---|---|
| `hit_facts.py` | per-hit-record window and branch-instance facts (`facts_*.json`) |
| `spt_cond_slice.py` | x86 backward slice of a transmitter's operand (ld address, str address, br_x flags) under §3's rules → const / declassified / tainted / unknown |
| `spt_taint_probe.py` | faithful re-run of `stem:grid` (same grid stalls), reads "made pending" lines and SPT stats; `--keep` keeps the workdir |
| `run_spt_brx_triage.sh` | the three above for one campaign |
| `fnc_commit_check.py` | re-derives fnc commit ticks from the Commit trace |
| `testset_provenance.py` | `.als` / parsexml hashes from each testset's `provenance.tar.gz` against git history |
| `spt_testset_shapes.py` | census of stale_rf, stale_rf_on_x, x_no_load_cone, unfed_read over Alloy XML |
| `recon_stlf_check.py` | A2 signature per ld hit, over every execution of the transmitter; `--only <mode>/<stem>` |
| `diag/bucket_hits.py` | runs every `diag_*.py` (`is_known`, PHASE/ORDER/KINDS/MODE) over a campaign; multi-kind |
| `diag/diag_brx_const_condition.py`, `diag_brx_declassified_condition.py`, `diag_recon_stlf_bypass.py` | this session's diagnostics |

Outputs are in cafe2 `/tests/simspect_fixed_20261030/triage/`: round 2 at the top level, `spt_brx_r2/`, `counterfactual/`, `r4/`, `spt_v2/`. The round-4 `diagnostics/` folders are not deployed, because the June SPT XML diagnostics are testset-specific and ld/str need slicer-based ones.

## 10. Gotchas for the next session

- **Check the testset's provenance before trusting a campaign.** Round 2's configs silently pointed at the pre-June-3 testsets.
- **Re-run a hit at its own grid point** (`stem:grid`). inst-080310 hits only at grid 1/2.
- **The slicer must strip assembler directives** (`raw.split("#")[0].strip()`).
- **In a wrapper, save `rc=$?` right after the command,** before any `$(date)`.
- **The container's Python is 3.8:** f-strings with nested quotes fail inside remote heredocs, so put scripts in files.
- **Write `specs/alloy_models.json` back with `indent=1`,** or the whole file reindents.
- **Briefs are deleted once the manifest absorbs them,** per Anna's 2026-11-08 rule. The v2 brief is gone: deleted in sync 9b9d64f, recoverable with `git show 9b9d64f^:wiki/design/MANIFEST_BRIEF_SPT_v2.md`. 45 `.als` header comments still point at it, so read EVAL_MANIFEST's SPT v2 section instead.
- **The repo moved to `~/trippel/simspect` on 2026-11-09.** This session ran from the old path. Its earlier files came across unchanged: the v2 model and cores have the same hashes.

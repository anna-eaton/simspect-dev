# 📋 STATUS — for Anna (SimSpect project)

Human-readable rollup of the SimSpect pipeline/research workspace, **kept current by every
Claude session** from `claudelog.md` (durable findings) + `claudenotes.md` (right-now) +
the review `.md`s. One file to see where everything stands: what to read, what needs your
call, what's running, the development front, and what's parked.

⚠️ *Run/sweep state below is "as last logged" — always trust `claudenotes.md` for the live
picture and re-verify a sweep is actually alive before relying on it.*

*Last refreshed: 2026-11-12 06:30 by `morning-rollup` (agent of `overnight-1111`: overnight rollup section below + decision index at the top of URGENT_TODO). Before that: 2026-11-09 21:20 by `resolve-hooks` (session close: SPT v2 / hit-triage findings in `wiki/findings/audits/2026-11-08/SPT_V2_AND_HIT_TRIAGE.md`, pickup in `wiki/state/OPEN.md`; the v2 "lost" check finished inconclusive). Before that: 2026-11-09 19:45 by `migration-uv6fix` (targeted footprint models for InvisiSpec/CleanupSpec/SpecLFB specced in `wiki/design/MODELS_AND_BUILDS.md` PART 8, decisions FP-1..FP-5 in URGENT_TODO, no `.als` touched; SpecLFB walk order: AMuLeT's own reverted UV6 patch, amulet-gem5 `5f9ac78`, would close it, so the 'six new bugs' condition in results.tex:55 fails; DECIDE 'walk-order count' in URGENT_TODO, read `wiki/findings/audits/2026-10-28/hooks_speclfb_and_uv6.md` 'Update 2026-11-09'. Repo-move check: CLAUDE.md and memory intact, 5 sessions still on the old path, 10 scripts with the old path, TODO Anna in URGENT_TODO). Before that: 2026-11-09 ~20:55 by `singlestage` (single-stage runs FINISHED for every unchanged model incl. STT_6_rmw_u (two-stage cannot seed RMW cores), nothing live in `/tests/singlestage_20261109`; two-stage drops ALU-feeds-transmitter programs in every family and never finished for SPT_6_u; write-up in `wiki/design/TWO_PHASE_MODELS.md`, DECIDE DA-6..DA-9 in URGENT_TODO; 8 bug checks done, BUGS.md rows + audit docs updated: R-SA-2/3/4 and R-SA-16 real by hand test on the Recon builds, R-SA-15 observable by hand test, R-SA-5/6 real by reading, CS-1 sole cause in 18 hits and waiting on its DECIDE, UV5 still 1 test, IS-2 no new leak on one core; single-stage flat model runs done, see `wiki/state/RUNNING.md`). Prior: 2026-11-09 by `dedup-audit-s15` (read: `wiki/design/TWO_PHASE_MODELS.md` '2026-11-09 — Dedup and shape-coverage audit'; two-stage corpus misses ALU-on-path shapes, 5 DECIDEs DA-1..5 in URGENT_TODO). Prior: 2026-11-08 by `simspect-c8` (eval manifest + approved eval set). Prior: 2026-11-08 by `hooks-v2` session (first STT_6 runs through hooks v2 on the AMuLeT builds). Prior: 2026-11-07 by `hooks-v2` session (amulet hooks v2 done). Prior: 2026-11-02 by `paper-figs` session (paper figures section). Prior: 2026-11-02 by `resolve-hooks` session (round-2 results). Prior: 2026-10-30 by `resolve-hooks` session (harness section at top). Prior: 2026-10-30 by `stl-spec` session (threat-model flag). Prior: 2026-10-29 by `commit-boundary-fix` session. Prior: 2026-10-26 by `alloy-minimality` session — Alloy two-stage / minimality / OTB workstream.
👉 **[`URGENT_TODO.md`](URGENT_TODO.md)** (OTB shape decision — needs your call ASAP) · **[`TODO.md`](TODO.md)**
(active workstream) · open questions → [`wiki/state/OPEN.md`](wiki/state/OPEN.md). Prior refresh:
2026-10-20 19:45 by `system setup` — session rig + dashboard fix + `/session-log`
routine. 🔴 **GIT CORRUPTED** (disk-full event → empty-tree commit pushed to remotes; files intact on
disk; GIT WRITE LOCK now in force — recovery is Anna's). Live state → `wiki/state/RUNNING.md`; pickup
list → `wiki/state/OPEN.md`. Prior: cleanuprepo repo cleanup + Mac↔cafe2 git reconciliation.*

---

## 🧪 2026-11-15 — Big corpus for all 11 paper bugs + race on STT and SPT (agent bigcorpus; RUNNING as last logged 22:10 UTC)

Final recipe A (and B after it) on big Footprint_6_u / STT_6_u / Recon_6_u corpora, cafe3 + cafe2; race sweep commitToIEWDelay 1/3/4 on /work/stt and stt-master, 1/4 on SPT-Fence (cross-model). How to resume: `wiki/state/RUNNING.md` "Big corpus 2026-11-15"; bug table (pending): `wiki/state/EVAL_MANIFEST.md` "Big corpus bug coverage (2026-11-15)". Done so far: SPT-Fence race on the 24 a5 stems, 0/24 at delay 1, 7/23 at delay 4. Decide: URGENT_TODO BC-1 (how to count the race), BC-2 (cross-model SPT), BC-3 (sampling).

## 🌙 Overnight 2026-11-11/12 (overnight-1111): what got done, what's blocked, what to decide

Trail: `claudenotes.md` (overnight-1111 lines), `wiki/state/RUNNING.md` "Overnight autopilot 2026-11-11", tonight's `claudelog.md` entries, the protcheck section at the bottom of this file. Decisions: index at the top of [`URGENT_TODO.md`](URGENT_TODO.md).

**Done (all local / read-only on nodes):**

- **Declutter:** 34 superseded paths moved to `~/trippel/oldsimspectstuff/` (manifest `oldsimspectstuff/MOVED_20261111.tsv`; shows as deleted in `git status` until you commit); comment pass on 56 code files, AST-verified (pristine copies in `oldsimspectstuff/precomment_20261111/`); declutter-2 still doing the rest. New `README.md`, git-ignored `build/`, `scripts/run_als.sh` (docs in `wiki/state/COMMANDS.md`).
- **RMW + jmp first-class vocab** (opt-in `fanout_v2.vocab_rj`, uniform weight; key absent = byte-identical 1,760/1,760; verify-x1 re-checked on 343 other XMLs).
- **fv4 table** (`instruction_tables/proposed/fv4_vocab.jsonc`): more concrete forms per Alloy kind, gem5 micro-tested on 9 builds, byte-identical when off.
- **Interleave-only category** (`instruction_tables/proposed/interleave_only.jsonc`, 69 entries, gem5-validated on 9 builds; side find: `xchgq %r,%r` same-register gives 0 on stt-master / recon-modded / /work/stt, dropped).
- **Unit tests:** `STAGE2_compilation/tests/test_vocab_fv4.py` (20 tests; suite 40 pass, 1 skip); dormant `%%rax` codegen bug in an unused parsexml path (TODO).
- **Launcher fixes** (verify-x1, `.orig` kept): twostage_lp `--alloy-only`, launch_gem5 stdin/L1D-regex/never-exits, launch_stage2 guard + SPT configs. X2b Stage-2 configs `runconfigs/overnight_20261111/stage2_final_{A,B,A_spt,B_spt}.jsonc` generated.
- **RL-10 diag:** `STAGE3_gem5/triage/diag/diag_rmw_limm_artifact.{py,md}` (disqualifier; E6 validation 2742/2720 bucketed, 0 missed).
- **STL prep (X4):** `stl_final_A.jsonc`, `launch_stl.sh`, new STL lpPc drafts. **stl-fail:** the ~2.7% stl_bypass Stage-2 failures = 15 `cmov_rr`/`inc` missing in `parsexml._stl_arch_values` (:1235, predates tonight) + 2 legit OOB skips; fix proposed in URGENT_TODO, evidence `scripts/overnight_20261111/stl_fail/`.
- **Protcheck:** STT_6_u / Recon_6_u protection sets OK; SPT issues (section at bottom).
- **usage_pace.py fix:** cap = median of the 3 most recent limit samples (27.1M), after a limit hit ~02:00.

**Blocked: nothing ran on the cafe nodes.** The permission classifier refused the agents' ssh writes (code snapshot + tmux) to the nodes; Slurm holders are RUNNING (~1d18h left at 05:19; cafe1 227G, cafe3 1418G free). Commands from RUNNING.md, in order:

1. X2a Alloy: `scripts/overnight_20261111/launch_alloy.sh cafe3 STT_6_u` and `scripts/overnight_20261111/launch_alloy.sh cafe1 Recon_6_u`
2. X2b Stage 2: `scripts/overnight_20261111/launch_stage2.sh cafe3 STT_6_u` and `... cafe1 Recon_6_u`
3. X3 gem5: `scripts/overnight_20261111/launch_gem5.sh cafe3` (E2, E3) and `... cafe1` (E6; see OVN-E6)
4. X4 STL: `scripts/overnight_20261111/launch_stl.sh cafe3 STT_6_u_stl`, `... cafe1 Recon_6_u_stl` (`NOWAIT=1` on cafe1 if E6 SKIPs), then score `launch_stl.sh cafe2 STT_6_u_stl score cafe3` and `... cafe2 Recon_6_u_stl score cafe1`

**Caveats for the first numbers:** RMW is the transmitter in ~53% of ld-transmitter tests (102/194 local sample), so the RL-10 limm artifact will inflate hits; `diag_rmw_limm_artifact` can bucket them only with recon_stlf rerun evidence per campaign. OVN-E6: `gem5-recon-ruby3` and `gem5-spt` exist only on cafe2, but E6 is planned on cafe1 (launch_gem5 will SKIP it). SPT is not run tonight (SPT-BOUND).

**Files to review:** diffs `STAGE2_compilation/proposed/vocab_fv4_uniform.diff`, `abs_vocab_fv4.diff`, `interleave_only.diff`; tables `instruction_tables/proposed/fv4_vocab.jsonc`, `interleave_only.jsonc`; new unreviewed `.als` drafts generated tonight `STAGE1_alloy/models/proposed/ultimate/loosepin/{SPT_6_u_lpPc,STT_6_u_stl_lpPc,Recon_6_u_stl_lpPc}.als` (+ `.als.diff`); `oldsimspectstuff/MOVED_20261111.tsv` (9 PROPOSED rows need you).

---


## 📝 2026-11-11 — Paper TODOs (simspect-c8)

- [ ] **Alloy engine, for the paper's tool description (Anna asked to record this).** We run Alloy 6.2.0 (`STAGE1_alloy/alloy6.jar`, Bundle-Version 6.2.0.202501090817), which bundles Kodkod (517 `kodkod/*` classes) and solves with SAT4J: `SATFactory.DEFAULT` resolves to `kodkod.solvers.SAT4JRef` (checked with a one-line probe), and `a6RandomModels.java` uses a seeded `kodkod.solvers.SAT4J`. We do **not** use AlloyStar (Alloy*). Wickerson's memalloy does: its repo pulls `johnwickerson/alloystar` (branch `extra_features`) as a submodule (`.gitmodules`, read 2026-11-11). Decide whether the paper should say "Alloy 6 (Kodkod, SAT4J)" and whether to contrast with memalloy's Alloy*. Bib entries `kodkod` and `sat4j` are now in ISCA-27 `sections/references.bib`. SAT4J's site asks academics to cite Le Berre & Parrain, JSAT 7 (2010) 59–64 (sat4j.org, read 2026-11-11). Alloy's site (alloytools.org home/about/documentation/book pages and the GitHub README) gives no citation instructions; its book page points to Jackson's *Software Abstractions*.

## ⭐ 2026-11-08 — Eval manifest (what we run, on what, from which model) → [`wiki/state/EVAL_MANIFEST.md`](wiki/state/EVAL_MANIFEST.md)

- Anna approved the eval set: Unsafe control, STT ×3 run separately (Kaxiras recon-modded, upstream `/work/stt`, AMuLeT's build; plus SPT's STT sub-mode if it exists), ReCon, ReCon OTB, NDA, DoM, Doppelganger, SPT, InvisiSpec, CleanupSpec, SpecLFB (AMuLeT builds on AMuLeT's own flags). Rows E1-E14, machine copy in `specs/defense_units.json` (dashboard unit inspector → "Eval recipe").
- Everything is NOT RUN for the eval (Anna): all testsets regenerate from the two-stage models (Stage 1 cores exist as drafts for STT_6, Recon_6, SPT_6_oneLP (conservative = default), STT_6_stl (306), Recon_6_stl (running); Stage 1.5 not built). Interim flat testsets: cafe2 `/tests/simspect_fixed_20261030/testsets_latest/{STT_6,SPT_6_oneLP,Recon_6}` (150k per mode, from today's exact `.als`).
- SPT model for the final batch: `SPT_6_oneLP_v2.als`, approved 2026-11-08; v3 (S-1 fix) is a draft, and DA-8 decides v2 vs v3. Footprint rows E12a/E12b/E13/E14 run the shrunk configs (`runconfigs/footprint/`); AMuLeT-parity runs T1-T5 only for timing and bug confirmation (`runconfigs/amulet_parity/`). AMuLeT-STT (E4) unblocked (glue fixed). Open: OTB testset; P-2/P-3/P-5 + clock for the eval rows; `sample_fraction` (templates still 0.02); `make sync` before the final batch.

## 🚨 URGENT before the AMuLeT timing/throughput experiment (Anna, 2026-11-08)

- [ ] **URGENT (Anna, 2026-11-08): run AMuLeT itself, with its own parameters, on ALL our defenses, including Recon (and the STT/Recon-STT family, SPT, InvisiSpec, CleanupSpec, SpecLFB).** This is the head-to-head comparison, and it uses AMuLeT's flags (`runconfigs/amulet_parity/`, AMuLeT repo on cafe2 `/work/amulet-repo` @ c871bdf). It needs AMuLeT's trace extraction ported to the builds AMuLeT never tested (Recon, SPT, `/work/stt`) and a parity config for each, taken from that build's own authors' defaults where AMuLeT has none. Plan it before running.
- [ ] **Timing comparisons with AMuLeT must use AMuLeT's exact configuration, not our shrunk caches.** Our footprint runs deliberately use a 1-2 kB L1D (and InvisiSpec 2 TBEs, CleanupSpec 8); AMuLeT's defaults are 32kB/8 L1D, 256 TBEs and a 2GHz clock. Run the speed experiment only from `runconfigs/amulet_parity/` (being written 2026-11-08), and check its `config.ini` against `wiki/findings/audits/2026-10-28/full_configs.md` "Comparison with AMuLeT's flags" before trusting any number. The paper's structure-size paragraph (ISCA-27 `sections/discussion.tex`, proposed note) promises this.

## 📄 2026-11-02 — Paper figures (paper-figs session) → drafts in [`paper_figures/drafts/`](paper_figures/drafts/), plans + decisions in [`paper_figures/plans/`](paper_figures/plans/), DECIDEs in [`URGENT_TODO.md`](URGENT_TODO.md)

- **→ RESUME the 2026-11-02 paper-figures session from [`paper_figures/SESSION_HANDOFF.md`](paper_figures/SESSION_HANDOFF.md)** (all TODOs, figure status, rules). Fact audit (IMPORTANT): [`paper_figures/plans/BIGFIG_FACT_AUDIT.md`](paper_figures/plans/BIGFIG_FACT_AUDIT.md).

- DSL: Anna 2026-11-02: DSL means domain-specific language; removed the acronym from all figures (no DSL mention needed).
- Drafts: vertical pipeline figure (`_standalone_pipeline_vertical`), (a) execution-graph syntax, (b) relaxation, (c) interleave + audit of all existing figures (`plans/AUDIT_existing_figures.md`), (d) instrumentation table, (e) checker window. Shared style: `paper_figures/plans/VISUAL_LANGUAGE.md`.

## 🚩🚩 2026-10-30 — HARNESS FIXED: every earlier campaign is suspect → [`wiki/findings/bug/BRANCH_ANNOTATION_AND_FORCE.md`](wiki/findings/bug/BRANCH_ANNOTATION_AND_FORCE.md)

- **Proven in gem5:** gem5-spt and gem5-recon-modded loaded 0 branch annotations in mainline runs (no force, no stall). The old BTB force was wrong on every build: decode-squashed on gem5-22 builds, wrong-path start on old builds. Taken-side layouts broke the natural prediction. The resolve-stall hook froze runs when the CPU slept.
- **Built:** BR resolve lines + forced-not-taken + CPU-wake in all 8 hooked builds (backups kept), derived branch force, `resolve_visible` gating, execution-validity gate (`status="invalid"`), criteria in every checker. Design: [`wiki/design/RESOLUTION_HOOKS.md`](wiki/design/RESOLUTION_HOOKS.md). Hook audit: `STAGE3_gem5/hook_audit.py`.
- **✅ amulet-InvisiSpec fixed 2026-11-07:** hooks-v2 finished on all three amulet builds (InvisiSpec, CleanupSpec, SpecLFB) and verified print-only on 10 cases (identical ticks and pipeview vs reference builds). Spec: [`wiki/design/SIMSPECT_HOOKS.md`](wiki/design/SIMSPECT_HOOKS.md). New SpecLFB finding there (both speculative loads treated as safe; DECIDE in `URGENT_TODO.md`). **2026-11-08: first STT_6 runs through the hooks on all three builds** (3000 tests per build/scheme, cafe2 `/tests/simspect_fixed_20261030/results/STT_6_*_v2hooks__20261107/`): UV1 (InvisiSpec), UV4 (CleanupSpec) and UV6 (SpecLFB) found at scale. NEW SpecLFB bug "jmp-shadow" (148 tests) **verified as real** (a porting bug from DOLMA, independent of UV6): [`wiki/findings/bug/speclfb_jmp_shadow/README.md`](wiki/findings/bug/speclfb_jmp_shadow/README.md). UV2, KV1, UV5 and unXpec are visible in the trace but not flagged by the checker. CleanupSpec deadlocks on 62% of tests at L1_TBEs=2. Per-bug table: `wiki/findings/mdsToRead/AMULET_BUGS_DETECTION_ACCOUNTING.md` "CURRENT". New DECIDEs in `URGENT_TODO.md`.
- **Round 2 classified (2026-11-07), 0 NEW:** SPT ld (336 / 264 tests) and br_x (28 / 22) are model/concretization artifacts (constant-derived values over-tainted by the model; values declassified by a non-speculative transmitter). recon-modded 7 / 7 = known real bug A2 (STLF taint bypass), re-confirmed on the fixed harness. stt 0. **But round 2 ran on pre-June-3 testsets**, so round 4 now runs on `testsets_latest` with a new lc/fnc checker fix (`results/*_fixed_latest__20261108_012818`). Write-up: `wiki/findings/bug/BRANCH_ANNOTATION_AND_FORCE.md` §7.
- **Round 4 done (2026-11-08; current models + lc/fnc fix):** stt 0. recon-modded ld 91 / 94 tests, all the known real bug A2. SPT ld 57 / 48, str 74 / 60, br_x 51 / 51: every operand is public under SPT's own rules, so they're all model or concretization artifacts. **`SPT_6_oneLP.als` and `Recon_6.als` lack `rf_from_most_recent_writer`** (68% of the current SPT testset reads a register past a newer writer). The fix plan P1–P5 awaits your call: `wiki/state/ALLOY_MODEL_CHANGES.md`.
- **SPT consolidated (2026-11-08):** `STAGE1_alloy/models/SPT_6_oneLP_v2.als` (original kept). It adds the rf fact, the other sessions' seed fix (audited: loses nothing), the skeleton's ≥1-leaker clause and narrower declassification. **Approved by you 2026-11-08.** Since then: model-audit S-1 found that v2-4 makes declassifying a load-derived value never take effect, so v3 is drafted and v2 vs v3 is DA-8. The v2 "lost" check finished inconclusive (8 h cafe2 timeout). Write-up: `wiki/findings/audits/2026-11-08/SPT_V2_AND_HIT_TRIAGE.md`; pickup: `wiki/state/OPEN.md` (resolve-hooks).
- **Your calls** (now in `URGENT_TODO.md`): `--delete` the zipped originals; gate on `resolved_before_signal` or not; review `STT_6_commitsplit.als`; which hits to triage first; `make sync`.

## 🚩🚩 2026-10-30 — THREAT MODEL: which STT is each build? (read before interpreting any STL / Futuristic result) → [`wiki/design/FUTURISTIC_MODEL.md`](wiki/design/FUTURISTIC_MODEL.md)

- **2026-11-07: one Alloy model per STT threat model, checked end to end** → [`wiki/design/STT_VS_RECON_STT.md`](wiki/design/STT_VS_RECON_STT.md). `STT_6_shadows` (Recon-STT, **draft awaiting your approval** in `STAGE1_alloy/models/proposed/`) admits branch and store sources only. On gem5 Recon-STT holds (branch-only 1/60, the known SLF gadget; aliasing store-only 0/32 sent) while Unsafe leaks (49/60, 32/32). Store-source alias: the proposed atom-based alias fact gives 60/60 concretizable store tests (how the alias is checked: `STT_VS_RECON_STT.md`, "How a store-source test gets its alias"). **Futuristic parked 2026-11-07** (Anna: not STT's only mode); its model, config and branch-only check (0/60 vs Unsafe 43/60) are kept in `FUTURISTIC_MODEL.md`. Open: approve shadows, and the store-alias question (`URGENT_TODO.md`).
- **2026-11-08: STL model + split core for every main model; full defense manifest** → [`STAGE1_alloy/models/MANIFEST.md`](STAGE1_alloy/models/MANIFEST.md) (machine copy `specs/defense_units.json` `model_families` + `stl_scope`, shown in the dashboard unit inspector). STT: `STT_6_stl` (approved) + draft core, SAT. Recon: draft `Recon_6_stl` (60/60 concretize) + draft core, SAT; Stage-1 runs for both STL cores started 13:58. **SPT: draft `SPT_6_oneLP_stl` generates nothing** (its RS-minimality conflicts with the alias fact; a one-line fix gives 60, needs your call). Only `gem5-recon-stl` can run STL tests, and it is stale. Four DECIDEs in `URGENT_TODO.md`.
- **Two different STTs — don't call both "STT".** **STT-Spectre** = `/work/stt` (upstream code; speculative only behind older unresolved *branches*). **Recon-STT** = `gem5-recon*` scheme 2 (Recon's re-implementation; behind older unresolved branches **or stores with no address**). Recon-STT protects a superset, so STL tests are only meaningful on Recon-STT (or STT-Futuristic). Side-by-side with code lines → [`wiki/design/STT_VS_RECON_STT.md`](wiki/design/STT_VS_RECON_STT.md); each build's `threat_model` is now in `specs/gem5_builds.json`.
- **gem5-recon / gem5-recon-modded STT = control + store shadows**, not Spectre and not Futuristic. A load is unsafe while an older conditional branch is unresolved **or an older store has no address** (Recon paper Sec. 3, 6; `decode.cc:686-695`, `shadow_tracker.cc`). So **STL bypass tests are in scope there**, and Futuristic-only sources (slow ALU ops, loads, faults) are not: a "leak" from those on Recon builds is expected by design.
- **/work/stt** has both: `--threatModel=Spectre` (branches only, what the harness pins, `gem5-hooks/stt/se_exp.py:332`) and `Futuristic` (all older instructions completed, `rob_impl.hh:493-512`).
- **`STAGE1_alloy/models/STT_6_futuristic.als`: PARKED 2026-11-07** (written, SAT, unreviewed). Its decisions are parked in `URGENT_TODO.md`.
- **STL hooks built + tested**: `/work/gem5-recon-stl`. On 60 tests, Unsafe leaks 28/28 load transmitters, STT 0/28, and the `alias` and zero-hold controls give 0 → [`wiki/design/STL_SPECULATION.md`](wiki/design/STL_SPECULATION.md).
- 🔴 **check_ld gate gap on Recon builds**: the data-obtained gate can't see a real cache send there, so squashed-before-complete leaks are scored as non-leaks → [`wiki/findings/bug/recon_cache_reach_gate/README.md`](wiki/findings/bug/recon_cache_reach_gate/README.md).

## 🚨 2026-10-29 — commit boundary + branch-annotation fixes (local, needs `make sync`) → [`wiki/design/COMMIT_BOUNDARY.md`](wiki/design/COMMIT_BOUNDARY.md)

- 🔴 **gem5-spt and gem5-recon-modded never loaded any branch annotation** (no BTB force, no resolve stall) in mainline runs. Their past results need re-running before you interpret them. Fixed in `gem5_common.py`.
- 🔴 **Interleaved testsets put fnc on a synthetic chain step** in 35-53% of tests. Fixed in `parsexml.py`; regenerate interleaved testsets from `llvm` (audit with `STAGE2_compilation/audit_commit_boundary.py`).
- **Needs your review:** `STAGE1_alloy/models/STT_6_commitsplit.als` (new copy, C/D/U commit split + each-unresolved-necessary); the print-only resolve-tick hooks for 8 builds (`wiki/design/RESOLUTION_HOOKS_SURVEY.md`, needs rebuild approval).

## 🔬 2026-10-30 — Protection-set re-evaluation (SEPARATE issue) → [`PROTECTION_SET_REEVAL.md`](wiki/findings/mdsToRead/PROTECTION_SET_REEVAL.md)

**This is a separate concern from the two-stage/minimality build and must not be folded into it** (Anna, 2026-10-30). Agent re-evaluated the protection-set clauses in STT_6 / SPT_6_oneLP / Recon_6 against the defense papers (all read locally from `quail/sources/papers/`). **Key finding — A1 is SPT-ONLY:** the const-address / `no_hold` over-approximation comes from SPT's operand-based seed (`SPT_6_oneLP.als:341` `hardware_protection_policy = Instruction.operands - …`, protecting ~all operands). **STT_6 and Recon_6 do NOT share it** — both seed from `Mem_s` (memory *states*; `STT_6.als:326`, `Recon_6.als:316-318`), so a const-ALU register output is never forward-reachable and the FP never arises. So `ALLOY_MODEL_CHANGES.md`'s rerun matrix is imprecise (it marks STT_6/Recon_6 as needing A1; they don't) — **not yet corrected, awaiting Anna's confirm**. Papers: STT seeds from load outputs (Yu 2019 §6.1), SPT likewise (Choudhary 2021 §2.2.1), ReCon = Mem_s minus revealed public addrs (Aimoniotis 2023). 5 open questions for Anna in the doc. No `.als` edits without Anna's per-change sign-off.

## 🚨 2026-10-26 — ACTIVE: Alloy two-stage / minimality / OTB  → **[`URGENT_TODO.md`](URGENT_TODO.md)** · **[`TODO.md`](TODO.md)**

Active workstream this session. Goal: factor the in-use model as **true-minimal baseline + interleave**,
make the baseline **complete (exhaustive to UNSAT)**, keep the net **identical**, **bound-agnostic/scalable**
(STT first, then SPT). Four max-effort agents produced analysis docs; a build agent is verifying STT now.

- 🔴 **URGENT — OTB shape decision** (`URGENT_TODO.md` #1): the 2-load→ALU→xmit `getOldestTaint` gadget
  **cannot emerge from minimality** (OR-taint ⇒ minimality drops the 2nd load; measured 0/300). Decide
  whether OTB is an **interleave** phenomenon (add a 2nd contributing source to a minimal core — recommended)
  vs a **distinct enumerated core** vs **diversity enumeration**. Blocks the "net == in-use" claim.
- **New analysis docs** (all PROPOSAL — owner sign-off before any `.als` edit):
  `wiki/state/ALLOY_MODEL_CHANGES.md` (pending edits A1/A2/B1-5 + rerun matrix) ·
  `wiki/findings/mdsToRead/REACH_UNSAT_ENUMERATION.md` (never reached UNSAT; staged-bounds + core-quotient) ·
  `…/MINIMALITY_TAGALONG_FIX.md` (per-element necessity; ≥2 unresolved branches UNSAT at scope 6) ·
  `…/SPT_MINIMALITY_MCM.md` (leak = PATH not cycle; minimal-leak-witness; relax branches/keep states) ·
  `…/TWO_STAGE_STT_FEASIBILITY.md` (building) · `wiki/results/TO_WRITEUP_PAPER.md` (MCM count vs ours).
- Full active list + checkboxes → **[`TODO.md`](TODO.md)**; hot decisions → **[`URGENT_TODO.md`](URGENT_TODO.md)**.

---

## 🧹 2026-10-20 — repo cleanup & git sync (cleanuprepo session)

The Mac and cafe2 container had **diverged uncommitted** from Jun 8 in different directions and the
container couldn't even auth to GitHub. All reconciled, nothing lost — **Mac = origin = container**.
- **Git unified:** cafe2's June work (bugsynth/, bug demos, staged-enum tooling, 2 protected
  `.als`) + Mac's Oct work (dashboard rewrite, sim rig, wiki/) merged on `main`, pushed.
- **Container GitHub auth fixed** (repo-scoped deploy key on persistent `/work` mount) — it can
  `git pull`/`push` directly now. See `wiki/state/INFRA.md`.
- **gem5 hooks backed up** → `gem5-hooks/` (they lived only in the ephemeral container; Recon builds
  weren't even git repos). `gem5-recon` = base, `gem5-recon-modded` = change. See `gem5-hooks/README.md`.
- **Layout consolidated:** dashboard → `dashboard/`; root `.md` → `wiki/design/` + `wiki/results/`;
  `RECAP.md` → `old/`. Only `CLAUDE.md`/`STATUS.md`/`claudelog.md`/`claudenotes.md` stay at root.
  Inventory: `wiki/state/REPO_MAP.md`. Full divergence writeup: `wiki/state/SYNC_DIVERGENCE.md`.
- **Still parked:** findings dirs (`bug/`, `mdsToRead/`, `docs/`) → `wiki/findings/` (next pass);
  a `scripts/sim capture-hooks` subcommand; dashboard `vscode://` open-links.

---

## 🚨 STANDING NEED (Anna, top priority): a far more robust BRANCH-CHANNEL check
**The branch transmitter checker (`STAGE3_gem5/check_br.py`) is the weakest link in the whole pipeline and
needs a principled rewrite.** Why this is urgent (collected across many sessions):
- **It misses real branch-channel bugs entirely.** The nmosier **pending-squash** leak is a secret-dependent
  *squash-signal timing* channel — `check_br` cannot express it at all; we had to write a bespoke differential
  (`bugsynth/pendsquash_diff.py`). A general branch checker must be able to catch redirect/squash-timing
  channels, not just "did a redirect happen."
- **No taint/secrecy gate.** `check_br` flags a redirect regardless of whether the branch condition is
  secret-derived → inflated branch hit rates (the historical STT br_x "leaks" were check_br FALSE POSITIVES;
  see `project_stt_branch_leak_cause`).
- **Coarse redirect criterion.** `branch_redirected` ≈ "xmit completed AND fall-through never retired",
  which conflates a genuine in-speculative-window redirect with any squash. It was patched to key on the
  *squash-broadcast* tick (not the complete tick), but still doesn't robustly enforce the
  `(lc_retire, fnc_retire)` window the way `check_ld` does, nor distinguish redirect causes.
- **What "robust" should mean:** (1) enforce the speculative window properly; (2) gate on whether the branch
  condition is actually tainted/secret; (3) key on the real fetch-redirect / squash-broadcast event; (4)
  handle *differential* secret-dependent-timing channels (squash-signal, resolve-coincidence) as first-class,
  not just operand-in-protset; (5) clearly separate real speculative-window redirects from generic squashes.
- Anna's own TODOs already flag this ("audit on the branch checker script", "branch concretization charts").
  **This is the #1 checker debt.** A correct branch-channel check would also be what lets pending-squash (and
  future branch-timing bugs) be found by the *mainline* pipeline instead of bespoke scripts.
- **Design workshop / proposal: `bugsynth/BRANCH_CHANNEL_CHECK_DESIGN.md`** — taxonomy of the 5 branch-channel
  types (A direct-direction, B redirect-timing/pending-squash, C squash-order, D implicit-flow, E window-modulation)
  and a unifying **non-interference (differential) checker**: vary the secret, flag any *public/untainted* branch
  observable (redirect tick, fetch schedule, squash order, window width) that moves with it. Single-run window
  checks can't cover B/C/D/E; the differential frame subsumes A–C (and D/E once generated).
- **PROTOTYPE built: `bugsynth/check_br_differential.py`** — non-interference frame, channel type B, with
  BOTH a taint-flip and a faithful **value-flip** secret parameterization + a forward-dataflow taint
  classifier. **It paid for itself immediately:** the value-flip mode showed the pending-squash
  reproduction is INVALID (0/12; public observables secret-invariant) — the taint-flip's 18/20 was a
  two-binary artifact. So the framework correctly catches both false negatives (the bug) AND, here, a
  false *positive* in our own repro. No-FP + self-consistency checks pass. Next: observable projections for
  channels A/C, fold into pipeline. See design doc §Prototype + claudelog 2026-06-09.
- **POSITIVE AUDIT (2026-06-09): `bugsynth/stt_branch_soundness_audit.py`** — used the same value-flip
  non-interference test for a positive result: **12/12 gadgets show STT's branch defense is SOUND** (the full
  public fetch-redirect timeline is secret-invariant). Principled confirmation that STT's branch defense works
  and the historical STT br_x "leaks" were check_br FALSE POSITIVES. Same framework, same value-flip that
  retracted the pending-squash repro — it correctly reports both.

---

## 🆕 bugsynth — BOTH STT bugs REPRODUCED from the Alloy up (isolated, nothing live touched) — 2026-06-08
Everything under `/tests/simspect/bugsynth/` (own pipeline.py, STAGE2/3, models, configs, testsets,
results). **READ FIRST — decision page: `bugsynth/FINDINGS_SUMMARY.md`** (one-page rollup: what's settled,
what needs your call). Then bug explainers: `bugsynth/NMOSIER_PENDING_SQUASH_BUG.md` +
`bugsynth/RECON_OLDEST_TAINT_BUG.md`. Reproductions (for you): `bugsynth/PENDING_SQUASH_BUG_REVIEW.md` +
`bugsynth/OTB_BUG_REVIEW.md`. Every change: `bugsynth/WALKTHROUGH.md`.**
- **🔴 Pending-squash (nmosier `18e304f`, bug B) — REPRODUCTION UNDER REVIEW / NOT YET VALID (2026-06-09).**
  The faithful VALUE-FLIP non-interference test (vary the in-memory secret 0 vs 1 on the SAME binary so bo's
  direction flips) shows **0/12 leak** — the public observables (fetch-redirect broadcasts, by's pending
  tick) are INVARIANT to the secret; only **bo's own** pending differs (the tainted branch — protected,
  allowed). The earlier 17/20 (`pendsquash_diff.py`) / 18/20 (`check_br_differential.py` taint mode) used a
  TAINT-FLIP that compared two DIFFERENT binaries — and `by` is intrinsically made-pending in the tainted-bo
  binary regardless of the secret (gem5 treats by's condition as tainted), so that "leak" is a binary/codegen
  artifact, not a secret channel. **Root cause refined (2026-06-09):** by is made-pending even with a PROVABLY-CLEAN `xorq` condition
  — so it is NOT a condition-taint issue; the same-cycle bo/by COINCIDENCE that the bug needs simply isn't
  firing in a way that makes a PUBLIC observable secret-dependent (matches the long-standing
  `project_coincidence_gap` / Anna's "why can't we have the coincidence fire?"). **To get a valid repro:**
  force bo & by to resolve the SAME cycle so bo (older,tainted) wins instCausingSquash and delays by's PUBLIC
  redirect secret-dependently; validate ONLY with the value-flip. Likely needs a dedicated /work/stt
  taint-debug build to trace argProducer + squash priority. See claudelog 2026-06-09 + `NMOSIER_PENDING_SQUASH_BUG.md`
  (the bug *mechanism* is still correct; our *gadget* doesn't yet exhibit it). The differential FRAMEWORK
  (`check_br_differential.py`) is what caught this and is sound. The Alloy channel `STT_6_pendsquash.als` +
  parsexml routing stand as infrastructure; the *demonstration* needs the fixes above.
- **✅ OTB (recon getOldestTaint, bug A) — 30/30 gadgets leak on /work/gem5-recon-modded scheme2+allow_leaked.**
  **Bug explainer: `bugsynth/RECON_OLDEST_TAINT_BUG.md`** (mechanism, validity matrix, the fix, + honest
  "where we're at": still forced via `otb_class`, not yet emergent from the model).
  Gadget generated DIRECTLY in Alloy `models/STT_6_otb2.als` (2-load→ALU→xmit; la under correctly-not-taken
  branch, lb under mispredict). Differential `otb_check.py` (`python3 bugsynth/otb_check.py 10 2500 9000`):
  the xmit is released (issues+accesses cache) while lb is still speculative ONLY when la resolves first;
  control (both resolve together) holds it → the getOldestTaint oldest-taint early-free (taint_tracker.cc:119
  + freeTaints:134). KEY FIX: recon-modded se.py reads `branch_pc_addr_hex`/`x86_branch_offset_hex` not
  `branch_addr_hex` → added the alias in `compile_annotate.py` (this was the long-standing "xmit never
  issues" blocker). Reference oldest_taint_bug.s leaks identically (control).
  - **Awaiting your call:** fold `STT_6_pendsquash.als` / `STT_6_otb2.als` + the parsexml tainted-branch
    routing + the compile_annotate alias into mainline, or keep as dedicated repros? **No mainline `.als`/
    pipeline modified.** Regression (not run): post-fix builds → 0 leaks.

### 🔭 bugsynth — future directions / open questions (2026-06-09): do the bugs come FROM the model?
**Honest status: NEITHER bug emerges from the unmodified base model — both needed predicates we wrote.**
- **OTB** — the base model's `secure_speculation_scheme_p` *does* flag it (xmit addr ∈ protset), but (a) the
  enumeration never produces the 2-load→ALU→xmit shape (**0/100k** — simple direct-load shapes fill the cap;
  re-tested 2026-06-09: relaxed driver w/o `otb_class` → 0/60 natural), and (b) the per-branch RR-minimality
  PRUNES multi-source merges (resolving one load's branch leaves the other tainted → "not minimal"). So
  `otb_class` HAND-FORCES the shape. The leak is in the model's definition; the *generation* is forced.
- **Pending-squash** — the base data-flow security predicate calls it SECURE (younger branch untainted). The
  leak is a **timing/squash-signal channel the model cannot express**; `pending_squash_insecure_p` is a NEW
  channel we ADDED (a real model extension, like implicit-flow), not the base model finding it.
- **TODO — make OTB emerge (principled):** (1) relax per-branch minimality to allow **multi-source leaks**
  (general: a leak may have ≥2 contributing spec sources), (2) fix enumeration **COVERAGE** so rare/complex
  skeletons appear (the real work — see Diversity). Then OTB would appear without `otb_class`.
- **TODO — implicit-flow channel:** `if(secret)x=A else x=B; load(arr[x])` is STRUCTURALLY inexpressible in
  the base model (branch has no outreg/ddi/rf → secret can't reach a later value via control). Needs a `cdep`
  control-dependence edge folded into `op_edges_p` + parsexml if/else concretization (owner-gated). Same
  category as pending-squash (a channel the data-flow model lacks). [xref claudelog 8:alloyCheckUpdated]
- **TODO — DIVERSITY (the core generation problem):** the enumerator is biased to the SIMPLEST instances
  (symmetry-breaking + minimality + SAT solve-order = simplest-first), so (a) complex gadgets like OTB never
  appear naturally, and (b) within a forced shape only register/value varies (OTB = 1 structural template;
  the `exactly 6 Instruction` scope leaves no room for context; pending-squash has 7 shapes). Candidate fixes:
  **(i) skeleton-stratified enumeration + blocking clauses** (after K instances of a structural skeleton, add
  a fact excluding it → solver forced to a NEW skeleton → covers the shape space incl. OTB with no bug-specific
  predicate); **(ii) larger instruction scope** (6→8, for in-context variation; needs IX6/IX7 + bigger SAT);
  **(iii) randomized SAT var-ordering** for statistical coverage. RECOMMEND prototyping (i).
  **MEASURED 2026-06-09:** 2000 relaxed-minimality instances (no otb_class) → 0 OTB-shaped, 0 even route the
  xmit addr through an ALU — yet they ARE kind-diverse (59 skeletons; 1001 have 2 loads, 811 have 2 ALUs).
  So the gap is the **DATAFLOW TOPOLOGY around the transmitter** (xmit addr always direct-from-load; the ALUs
  sit on other paths), NOT kind-counts. ⇒ blocking clauses must cover **rf/ddi dataflow skeletons** (block
  "xmit-addr direct-from-load" after K to force "xmit-addr through ALU"), not kind-sequences. That makes OTB
  appear as one covered topology with no bug-specific predicate. (claudelog 2026-06-09.)
  **DEFINITIVE (2026-06-09):** even FORCING an ALU on the xmit address path (general, no 2-load pinning)
  → 280/300 have a 1-input ALU, 20/300 a 2-input ALU with the other operand a CONSTANT, **0/300 the 2-load
  merge**. ROOT: one tainted operand already satisfies the leak, so minimality MINIMIZES load-fed operands
  and structurally avoids the multi-source merge. ⇒ OTB's leak is in the model's *definition* but its 2-source
  *gadget* cannot emerge from minimality-guided enumeration; forcing the merge (otb_class's "≥2 distinct loads
  feed the ALU") is FUNDAMENTALLY NECESSARY, not a shortcut. (Blocking-clause coverage would have to target
  the #load-fed-operands dimension, which reduces to the same constraint.) Diversity question CLOSED for OTB.

---

## 🗒️ Anna's personal TODO notes (verbatim — Anna's own dump, not Claude's analysis)
*Captured 2026-06-07 from a brain-dump. Kept as-is; reminders to herself for the code/pipeline
branch — not acted on, not verified. The "?"/asides are Anna's.*

**Branches / sweeps**
- Start inspecting branch hits.
- Resolved br sweep windows.
- Generating more unresolved branches ??? take off relaxation.
- Two-phase alloy??
- Tune IEW to commit delay etc.
- End block is not at the end??

**Recon / OTB / coincidence bugs**
- Eventually go back to Recon to concretize the bugs we've got there, and also check if the ORB bug is generating.
- Figure out why the two bugs we know of aren't triggering on STT Recon yet.
- Is the OTB bug ever generated :(
- Do some test sweeps on the oldest-taint bug; show results about timing etc.
- Make sure that bug isn't real.
- Gotta eventually rerun duplicate-PC bugs.
- Have to figure out why the one with two coincidences isn't hitting.
- Leftover question: why can't we have the coincidence fire?

**Checkers / scripts / audits**
- Let's do an audit on the branch checker script.
- Should I really update the shared checkld diagnostic script?
- Did we not make a triage script for slowcomm?
- Audit the models to see if there's anything out of date with the others.
- Audit the 1234 low cases.
- Force a clean recompute (if you suspect a stale count): `rm results/.sweep_monitor_cache.json`.

**Timing sweeps (before bed)**
- Run something with natural timing for a second sweep, and a sweep with shorter timing windows for delays.
- Natural timing necessary for the slow-regime hits.
- Run natural timing for a bunch of stuff before bed; also a short timing sweep before bed.
- Post-nap: run the baby ones for AMuLeT, run other lil experiments, make the figures, write the paper.

**Alloy / model**
- Alloy: make it able to emit the other transmitter.
- Gosh we don't build implicit-flow gadgets right??

**Charts**
- Gen charts for: branch concretization; transmitter detection.
- Run vs scheme 0 in a lot of them to see if that's good.

**SPT**
- Does a load output unprotected when it's non-speculative — yea?
- SPT flag stickiness flaw???

**Config**
- ShadowL1 on vs off.

**Logistics / submission**
- Figure out if the authors have to be fixed by the time I submit the abstract — if so, do Nick + Prof. Mitchell go on there.

**Open questions**
- Who are we to say what is irrelevant variation?

---

## 🛡️ Ongoing project — SOTA load-defense bug reproduction (InvisiSpec / SpecLFB / CleanupSpec / STT)
**Living rollup → `mdsToRead/AMULET_LOAD_DEFENSES_PROJECT_LOG.md`** (read this first for the defense work).
Aim: reproduce **every** AMuLeT-reported bug on the real gem5 build (or give a precise source why-not).
**As of 2026-06-09: 6/9 demonstrated** — UV1 (InvisiSpec evict), UV6 (SpecLFB first-load), KV1 (InvisiSpec
L1I), KV3 (STT store→TLB), UV4 (CleanupSpec split), unXpec (CleanupSpec undo-as-channel). **UV2** reachable
but empirical demo blocked (spec data loads don't issue GETSPEC in a gadget). **UV3** precise why-not.
**UV5** (over-clean) = next to build. Per-defense builds/observation-points + repro commands in the doc.

## 📖 To read (review docs for you, newest first)
- **`docs/AMULET_VS_SIMSPECT_SCOPE.md`** (headline section) — 📐 **ADVISOR-FACING: why InvisiSpec / footprint-
  hiding defenses are OUT OF SCOPE.** Definitional argument: our oracle is transmitter-level (did the
  transmitter fire in the window?), which matches the comprehensive transmitter-blocking defenses (STT/SPT/
  Recon/…); InvisiSpec lets the transmitter fire and hides the footprint → type-mismatched oracle → needs a
  whole-µarch differential defense-specific check (AMuLeT's job). Hand straight to advisor. (2026-06-10.)
- **`mdsToRead/ENUMERATION_OVERSPECIFICATION.md`** — 🔴 **enumeration over-specifies: 100k tests = ~10 leak-
  cores (98% on 2 shapes); minimality kills control-multiplicity, simplest-first SAT + no instr-minimality
  waste the budget on padding.** Built+validated `STT_6_multisource.als` (relax minimality) + `a6DiverseModels.java`
  (leak-core diversity driver). (2026-06-09/10.)
- **`results/STT_6_cleanupspec_residue/uv5_demo/NOTE.md`** — 🟡 **NEW: CleanupSpec UV5 (over-clean) EXAMINED
  → empirical demo BLOCKED** (mechanism source-confirmed). Free-way path: CleanupSpec correct (spec line
  cleaned, committed neighbour stays resident, 0 over-clean). The eviction path UV5 needs trips the
  defense-independent assoc-thrash `Resource Stall` storm (ON==OFF) at assoc-2 AND assoc-4 → can't stage.
  Same blocker class as UV2. (2026-06-09, 5:invisispec.)
- **`results/STT_6_cleanupspec_residue/unxpec_demo/`** — ✅ **NEW: CleanupSpec unXpec EMPIRICALLY
  DEMONSTRATED** (reproducible `run_unxpec_demo.py`). The undo *itself* is the channel: spec-load MISS
  (cold) → 7 cleanup events (L1+L2+dir invalidation cascade); HIT (pre-warmed) → 0. Cleanup footprint is
  secret-dependent (`lsq_unit_impl.hh:142-160`, `pkt->isL1Hit()`). **6th AMuLeT bug demoed.** (2026-06-09.)
- **`bug/uv2_demo/`** — ✅ **NEW: InvisiSpec UV2 (MSHR/TBE contention) EMPIRICALLY DEMONSTRATED**
  (`run_uv2_demo.py`). 4 spec loads on a TLB-warm page exhaust the 2-entry TBE pool: `--L1_TBEs=2` → 248
  retry GETSPECs + 122k-tick serialization; `=8` → 4 clean concurrent. Unblocked via the **TLB-warm-page
  trick** (committed access warms the page so the speculative TLB miss isn't deferred). **7th bug demoed →
  7/9; only UV5 (over-clean) empirical gap left + UV3 why-not.** (2026-06-09, 5:invisispec loop.)
- **`bug/kv1_demo/`** — ✅ **NEW: InvisiSpec KV1 (L1I fetch channel) EMPIRICALLY DEMONSTRATED**
  (reproducible `run_kv1_demo.py`). A branch forced (BTB) to predict TAKEN to a far code label reached
  only speculatively → that label's L1I line installs (`Ifetch NP>IS`) under the misprediction but NOT
  in the correctly-predicted control. InvisiSpec makes data loads invisible but **not** instruction
  fetches. **5th AMuLeT bug demoed (UV1, UV6, KV3, UV4, KV1).** (2026-06-09, 5:invisispec loop.)
- **`bug/STT_KV3_TLB_REVIEW.md`** — ✅🔴 **NEW: STT KV3 (spec store → TLB) EMPIRICALLY DEMONSTRATED**
  (source chain + a controlled gadget `bug/kv3_demo/`, reproducible). STT protection is loads-only
  (`isTransmit()=isLoad()`; `Request::SPEC` set only in `readMem`); a wrong-path STORE translates at
  execute and **fills the TLB for a secret-dependent cold page** unprotected. 2×2 control on the live
  STT build: store walks the cold page under **both** STT and Unsafe (= unprotected = KV3); load walks
  under Unsafe but **NOT** under STT (= STT protects loads). The 3rd AMuLeT bug demoed in SimSpect
  (after UV1, UV6). Reachable unlike CleanupSpec UV3 (translation is pre-commit). (2026-06-08, 5:invisispec loop.)
- **`results/STT_6_cleanupspec_residue/CLEANUPSPEC_RESIDUE_REVIEW.md`** — 🔴 **NEW: CleanupSpec
  residue watcher built + validated.** On STT_6 ld the defense WORKS (0 residue; a "3 RESIDUE"
  reading was a checker FP — spec *hit* on a committed line — caught by gem5 verification + fixed).
  UV3 precise why-not (loads-only cleanup + squashed stores never touch cache). **✅ UV4 EMPIRICALLY
  DEMONSTRATED** (`uv4_demo/`): split spec load installs 2 lines, gets 0 cleanup (residue), vs the
  aligned control which is cleaned — source `isSplit=false` + single `cleanupReq`. assoc-2 deadlock
  RULED OUT as a bug (ON==OFF). (2026-06-08, 5:invisispec loop.)
- **`mdsToRead/AMULET_BUGS_DETECTION_ACCOUNTING.md`** — 🔴 **full accounting: every AMuLeT bug ×
  our detection (+ WHY-not).** Detected 2/9 (InvisiSpec UV1, SpecLFB UV6); the other 7 are out of
  our formulation for precise reasons (store/I-fetch transmitter, TLB/I-cache observation, timing
  channel, or post-squash residue = final-state diff). Includes observation points per defense +
  why, the lc/fnc-window fix + parallel lc/fnc-OFF analysis, the cache-size flag, and the pipeline
  changes needed to generate each undetected bug. **This is the master doc for this work.**
- **`mdsToRead/INVISISPEC_UV1_CONFIRMED.md`** — 🔴 **InvisiSpec UV1 (speculative L1 eviction)
  CONFIRMED** via the compound hardware-structure watcher on the real Ruby defense. Patch-OFF
  29/30 evict speculatively; the AMuLeT fix → 0/30 (airtight). Generalizes to STT-interleave.
  Real bug, NOT a test-gen artifact. UV2 (MSHR/TBE) surface also present.
- **`PAPER_RESULTS.md`** — findings by defense (recon OTB+STL, STT/SPT VP-squash race, AMuLeT
  scope + SpecLFB UV6, targeting 17%→100%, timing sweeps). UV6 reframed to **DEMONSTRATED**.
- **`results/STT_6_speclfb/SPECLFB_UV6_REVIEW.md`** — SpecLFB UV6 confirmed; the 68 hits are
  **valid dataflow leaks, NOT const-addr FPs** (corrected). ⚠️ this corrected an earlier verdict.
- **`docs/COMPOUND_TRANSMISSION_CRITERION.md`** — the all-µarch-structures load criterion + per-
  defense hook map (design; partially implemented for InvisiSpec).
- **`docs/AMULET_VS_SIMSPECT_SCOPE.md`** — which AMuLeT bugs are in/out of SimSpect's scope.
- Methods docs: `METHODS_LEAKAGE_KNOBS.md` / `METHODS_CONCRETIZATION.md` / `METHODS_INSTRUMENTATION.md`.
- **Paper (S&P 2027) review docs** (in `/tests/SimSpect-S-P-2027/toread/` + `paper_figures/`):
  - `paper_figures/reviews/DISCUSSION_AND_FINAL.md` — PC debate + 3 finals on the YArch mini-paper
    (all **Weak Reject**; flip-it deliverable = one bug end-to-end + negative control).
  - `paper_figures/YARCH_PORT_PLAN.md` — what to port from YArch (related work, pipeline fig, etc.).
  - `…/toread/technical-review.md` — per-paragraph grades on `model.tex` + `pipeline.tex`.
  - `…/toread/reconstl_figure_critique.md` — critique of the ReCon STL figure.

## ✅ TODO (from 5:invisispec autonomous run — AMuLeT bug replication)
- **DONE this run:** lc/fnc gate-cheat reverted (kept STRICT); ported the **fnc-commit-stall hook**
  (non-defense) to the InvisiSpec + SpecLFB builds + rebuilt; **UV1 (11/12) and UV6 (11/12) confirmed
  in the STRICT lc/fnc window** with `fnc_commit_stall_cycles=150`. (The amulet builds had lacked the
  standard window-widener recon/STT use — that, not the gate, was why the slow touches fell out.)
- **Write a paper section on the CACHE-SIZE CONSTRAINT** (amplification): litmus-test µarch defense
  testing needs a small-L1D / few-MSHR knob so short tests reach the full-set/contention conditions
  where conflict/eviction/interference bugs manifest. Used `--l1d_size=1kB --l1d_assoc=2`. Details +
  paper framing in `mdsToRead/AMULET_BUGS_DETECTION_ACCOUNTING.md` §4. ← *flagged for you.*
- **Make UV1/UV6 hits secret-dependent** (concretization): seed a non-zero value into the
  speculatively-loaded location so the evicted victim / installed line varies with the secret
  (today index=0 from the zero-init prologue → structural touch confirmed, victim is fixed).
- **CleanupSpec UV3/4/5 — NOW detectable (reclassified):** residue traces to the in-window
  `L1_Replacement_OnInstall` + MISSING/OVER post-squash cleanup (`Inv_CLEANUP`/`Load_ROLLBACK`,
  ProtocolTrace-visible) → EVENT-correlation watcher (NOT a final-state diff). Build: port the
  fnc-stall hook to the CleanupSpec build (`X86_MESI_Two_Level`, --ruby) + write the install↔cleanup
  correlator. Recipe known.
- **Still need new transmitter types / channels:** STT KV3 (store-address transmitter + D-TLB watcher),
  InvisiSpec UV2 (MSHR-timing watcher), KV1 (L1I watcher). See accounting doc §5.

## ✋ Needs your call / approval pending
- **🆕 Staged enumeration — new `STT_6_core.als` to eyeball (2026-06-10).** New optional XML
  producer (minimal cores → STT_6 flesh-out) to fight enumeration over-specification: enumerate
  maximally-minimized leak cores once, then cap fleshed-out tests **per core** so one shape can't
  fill the cap. Files: `STAGE1_alloy/{models/STT_6_core.als, stage_seed.py, stage_pipeline.py}`.
  `STT_6_core.als` is a pure **copy of STT_6.als** + 3 flagged changes (idx/ordering rules removed,
  `exactly 6`→`but 6`, all relaxations RO+RI on); STT defense byte-identical. Verified E2E (2 cores
  → 8 XMLs → 8/8 `.ll`). **Doc: `mdsToRead/STAGED_ENUMERATION.md`.** Additive — flat pipeline + all
  existing `.als` untouched. Your sign-off on the new model + whether to make it a `pipeline.py` phase.
- **Alloy `rf_from_most_recent_writer` fact** — owner-approved but **NOT yet applied** to
  `SPT_6_oneLP` + `Recon_6` (`STT_6` already has it, L163-169). Until applied, rf-clobber is
  filtered gem5-side instead of ruled out in Alloy → **regen all affected testsets after applying.**
- **const-addr proper-closure fix** (`.als` L341) — DESIGNED but **UNAPPROVED**; data-taint only,
  must NOT apply to STT/Recon.
- **Any `.als` edit needs your sign-off** (standing rule). SPT model has 2 approved fixes
  (inaddr-cleanup L356 + stores-in-leakage_function) that imply a **regen**.
- **`check_br.py` taint-at-redirect gate** — recommended (branch hits are check_br FPs); your call.
- **Paper:** where to `\input` the new `tikz/reconstl.tex` (ReCon STL conceptual figure) — left
  un-placed; if used early it needs "transmitter"/"bound-to-squash" defined first. Also decide
  whether to port YArch's related work into the **empty `sections/related.tex`**.

## 🏃 Runs / work last logged (verify before trusting)
- **150k regen** of `STT_6`, `SPT_6_oneLP`, `Recon_6` alloys + fresh testsets via `testsetgen`
  (logs `latestmodels/<m>_gen150.log`) — *launched 06-03, confirm completion.*
- **recon-modded gem5 watchers** jobs=12 sweeping the (stale pre-RS) `testsets/STT_6` — *check alive.*
- **InvisiSpec compound checker** built (`STAGE3_gem5/check_ld_invisispec_compound.py` +
  launcher `results/STT_6_invisispec_compound/run_invisispec_compound.py`) and **FIRES**: with
  `--ruby` + small L1D (`--l1d_size=1kB --l1d_assoc=2`, AMuLeT-style amplification) + default
  patch-OFF, **UV1 confirmed** (29/30 STT_6, 10/14 interleave); `--patch-on` → 0 (control).
  See `mdsToRead/INVISISPEC_UV1_CONFIRMED.md`. `check_ld.py` untouched.

## 🔭 Development front
- **InvisiSpec on Ruby — scoping + rehooking with denser transmit-point checks** (ongoing). 🔴
  prior InvisiSpec/CleanupSpec runs were on CLASSIC caches (defense inactive). Moving the load-leak
  test off the single cache-install check to the **compound criterion**: re-hooking the checker to
  flag a speculative USL that touches **any** forbidden µarch structure (L1 tag/LRU/evict,
  MSHR/TBE, L2, dir `SpecFetch`, TLB) via Ruby `ProtocolTrace`. Scope: `docs/COMPOUND_TRANSMISSION_
  CRITERION.md`. Compound checker built (`STAGE3_gem5/check_ld_invisispec_compound.py`); next:
  missing-line corpus + `--patch-off` to actually fire UV1.
- **Alloy bug cleaning** (ongoing) — pushing model-level false-leak sources back into the `.als` so
  they're *ruled out in Alloy* instead of filtered gem5-side: `rf_from_most_recent_writer` fact
  (→ `SPT_6_oneLP`, `Recon_6`), SPT inaddr-cleanup + stores-in-leakage, and the pending const-addr
  closure. Each implies a **regen**. Owner-approval + regen status tracked under "✋ Needs your call."
- **SpecLFB UV6** — demonstrated; the dataflow signal stands.
- **STT/SPT VP↔squash race** — the one confirmed real-bug-class signal (untaint on resolved/
  completed not committed); ~3807 genuine SPT load signal + STT load race.
- **Two gadgets to get *into* the testset** (ongoing — each with a bug diagnosis in progress):
  - **OTB / `getOldestTaint`** — recon merges two still-speculative tainted loads into the xmit
    address and untaints on the *oldest* source resolving (should track the *youngest*). Absent from
    default enumeration but **legal when forced** (`otb_shape` predicate + `interleave.enabled=true`).
    Work: enumerate the forced OTB testset + ship the recon youngest-vs-oldest-taint diagnosis.
  - **Double-squash (nmosier two-branch coinciding squash)** — our `/work/stt` build IS vulnerable
    (HEAD not ancestor of fix `18e304f`) but unreachable today: model emits only 1 unresolved branch;
    bug needs ≥2 mispredicted, mixed-taint branches with coinciding squash. Work: model/config change
    to emit the ≥2-branch shape (owner ok) + the coinciding-squash diagnosis.
- **Paper (S&P 2027)** `/tests/SimSpect-S-P-2027` (current; old copy archived `/tests/old/`). Infra
  done (IEEEtran bib, two-tier logs, `toread/`, this dashboard's paper analogue). Figures: added
  `tikz/reconstl.tex` (ReCon STL); `images/pipeline.png`+`examplefigure.png` still never
  `\includegraphics`'d; `sections/related.tex` empty. The reviewers' bar for any bug claim:
  **one discrepancy carried end-to-end through a falsification protocol + a negative control** —
  state both explicitly (ties to the VP-squash race + recon SLF results).

## 🗂️ Scoped / flagged for future
- *(OTB / getOldestTaint and the nmosier two-branch coinciding-squash bug are now **active** — see
  "Two gadgets to get into the testset" under 🔭 Development front.)*
- **`commitToIEWDelay`≥3** wiring into `_build_gem5_env` to faithfully reproduce the VP-squash race
  (not in stock pipeline; ≥5 livelocks gem5).
- **branch xmit rework** — in progress; STT relaunch deferred; regen from parsexml for br_x.
- **dup-PC codegen bug** — parsexml xm-branch NOP injection duplicates a PC label → ~6% of br_x
  tests fail compile; fix Stage 2, relaunch from parsexml.

## Protection-set / unprotection check before the overnight runs (protcheck, 2026-11-11)

Read-only check (no `.als`, parsexml, gem5 or config edited). It builds on the 2026-11-08 model audit (`wiki/findings/audits/2026-11-08/MODEL_AUDIT_SPT_RECON.md`), the SOURCE_AUDIT_*.md files, the 2026-11-09 ultimate write-ups (`wiki/state/ALLOY_MODEL_CHANGES.md` 'ultimate … STT/ReCon/SPT') and the 2026-06-10 freeParam config bug (`claudelog.md` 2026-06-10). Papers read from `~/Documents/quail/sources/papers/{yu-2019-stt,aimoniotis-2023-recon,choudhary-2021-spt}.pdf` (SPT printed page = PDF page + 606); SPT and STT configs read from `~/trippel/defense_src/{spt_0d2be0f,stt_e3283b9}` and `gem5-hooks/{stt-master,gem5-spt}/*.diff`. Cafe-only files (the cafe `se.py` copies) were not read; they are cited through the hook diffs.

**Bottom line.** STT_6_u and Recon_6_u unprotect correctly for tonight. SPT_6_u is correct at exactly 6 instructions; at `but 8` its 6-step untaint fixpoint is unproven (SPT-CONV, the Alloy result is below), and the overnight plan's "SPT_6_u bound-8 lpP" contradicts Anna's LP-4 decision (SPT stays exactly 6). The one config that is really wrong: every root `runconfigs/run_config_SPT_6*.jsonc` has SPT untaint switched off (no `--freeParam`), and most of them also have the implicit-flow defense off. E11 must copy `runconfigs/fixed_20261030/SPT_6_oneLP_fence_fixed_latest.jsonc` instead.

### K1a: models

Defense blocks, from the "Specific defense model" banner to EOF, are byte-identical (md5) between each base and every derivative: STT `70c55b87…` (STT_6_u, STT_6_u_core_ri in proposed/ and models/, STT_6_u_lpP in loosepin/ and models/); ReCon `64e1efa4…` (Recon_6_u, both core_ri copies, both lpP copies); SPT `ef3dbbfd…` (SPT_6_u, SPT_6_u_core, SPT_6_u_core_ri, loosepin SPT_6_u_lpA/lpB); STT STL `732cdeed…` (STT_6_u_stl, _stl_core_ri, _stl_lpA/lpB); ReCon STL `3e58daaf…` (Recon_6_u_stl, _stl_core_ri, _stl_lpA/lpB). The production `models/*_lpP.als` differ from their loosepin source drafts only in the 3-line provenance header and the `--pin core` run text (`lp_committed` + `seed_core`). No SPT lpP file exists (only lpA = cone minimality, lpB = norsc).

| # | Model | What the model does | Paper / implementation | Over- or under-protects | Overnight impact |
|---|---|---|---|---|---|
| M1 | STT_6_u (+core_ri, lpP) — **OK** | Taint seed = memory read of every load in the contract (`STT_6_u.als:384`), forward taint along `^op_edges` (`:286`), propagation identity (`:393`). A value leaves the protection set only when its youngest root load stops being speculative, i.e. no older unresolved branch (`:360`). No declassification, no reveal. | STT p5 §6.1 "an instruction has reached the visibility point if all older control-flow instructions have resolved"; p6 §6.2 "If a load is unsafe, its output is always tainted" and "when all the data dependencies … become untainted, the instruction's output is untainted"; gem5 `rob_impl.hh:489-520, 709-813` (per the model's citations, stt_e3283b9). | Matches. Known under-taint in the skeleton only: a load's address does not flow to its output (`ld_ddi`, `:193`) and SK2 optional ddi edges. These under-generate; they never cause false hits. | Fine on E3 and E2. On E2 (Recon-STT) gem5 also treats store shadows as speculation (`decode.cc:686-695`, STL_SPECULATION.md:182), so gem5 is stricter than the model there. Fewer hits, no wrong ones. |
| M2 | Recon_6_u (+core_ri, lpP) — **OK** | STT block, plus the seed minus revealed reads (`Recon_6_u.als:456`). A read is revealed when an earlier committed direct pair LD1→LD2 (`:422-424`) read the same word and no resolved or committed store wrote that word in between (`:436, :446-452`). Reveal does not depend on timing ("MAY be untainted", `:443-445`). | ReCon §4.1 "marks this value as revealed when the second load commits"; §4.3 "only … load pairs with a direct dependence"; §5.1 "the earliest that LD2 becomes non-speculative is … its visibility point … we opt for implementing load-pair detection in the commit stage"; §5.2 conceal on store commit; §5.4 a revealed load untaints its destination; gem5 `lsq_unit.cc:869-959`, `taint_tracker.cc:138-150`. Recon-STT's oldest-source taint (`taint_tracker.cc:108-131`) is the OTB bug; the model keeps STT's union semantics, which is correct. | Matches. Timing-free reveal under-protects relative to gem5, so it under-generates; it never causes false hits. | E6 (ruby3, `--allow_leaked`): Stage-1 cores never contain a committed pair. lpP's required committed region can add one, but rarely (URGENT_TODO 'how do ReCon-specific tests reach the two-stage corpus'). Expect E2LT-3 hits, where a pair or alias created by concretization reveals the word: ReCon working as designed, existing DECIDE. On E2, reveal is off (no `--allow_leaked`, EVAL_MANIFEST:266-269), so the Recon corpus behaves as Recon-STT there. |
| M3 | SPT_6_u at exactly 6 (+core, core_ri) — **OK** | Protects every transmitter operand outside the public set U (`SPT_6_u.als:422`). U = initial registers (load-immediates) + addresses of non-speculative loads and stores (declassification, `:438-447`), closed under forward untaint (`:454-456`), backward untaint on `InvOp` (`:461-463`) and STL with STLPublic (`:468-490`), over 6 nested steps (`:499-502`), proven converged at ≤ 6 instructions (query `spt_E_conv.als` conv_nop). Branch predicates are not declassified (`:445-446`). Shadow L1 (memory untaint, §6.8) is not modelled. | SPT p612 §6.3 "all program data … starts off as tainted", "the operands of transmitters/branches are untainted when the instruction becomes non-speculative"; p613 §6.6 forward/backward rules and convergence; p613 §6.7 STLPublic; gem5 `rob_impl.hh:751-990` (`queueLimit = freeParam`, `:764`), `lsq_unit_impl.hh:1189-1209`. E11 runs `enableShadowL1` off (authors' default in `run_spt.py:56` without `--enable-shadow-l1`). | Matches gem5 for E11. Not declassifying branch predicates over-protects relative to the paper's wording, but matches gem5 (DECIDE B1 in the SPT_6_u DECIDE, recommendation: keep). | Fine if E11 runs the exactly-6 model. |
| M4 | SPT_6_u at `but 8` (loosepin lpA/lpB; "SPT_6_u bound-8 lpP" in the RUNNING.md X2 plan) — **suspicious** | Same block, but the fixpoint is still 6 steps while N = 8 (`check_bound_consistency.py` warns `fixpt`, TWO_PHASE_MODELS.md:527). If 6 steps do not reach the fixpoint, U is too small. | Paper: untaint is applied "until convergence" (p613 §6.6). | Possible over-protection: the model would flag transmitters that SPT untaints, and those become expected hits on E11. My hand bound: with xm and an unresolved branch firing no rule, at most 6 instructions can fire, so 6 steps are probably enough for verdict-relevant operands. The Alloy query was still running at write-up time; see SPT-CONV. | Anna decided LP-4 on 2026-11-10: "SPT stays on its unchanged exactly-6 model". The X2 plan contradicts this. → DECIDE SPT-BOUND. |
| M5 | SPT_6_u vs Stage 2 — **caveat** | `InvOp` (`:513-518`) is the Stage-2 contract: an ALU outside InvOp must be emitted as an op gem5-spt has no backward rule for. | gem5 backward rule covers add/addi/sub/… and mov (`rob_impl.hh:855-880`). | Base vocabulary is consistent: `add`→`leaq`, `bitnot`→`movq`+`notq` (`parsexml.py:2760-2781`). The fv vocabulary is not: `inc` = `movq`+`incq` (addi, SPT A1), and splices `add0`/`add_sub` (`parsexml.py:1455-1468`) are gem5-invertible whatever InvOp says. Then gem5 can untaint what the model keeps tainted: expected hits, not bugs. | Run E11 Stage 2 with base options only (no fv splices, `inc` or `cmov_rr`), as RUNNING.md autopilot (c) already says for SPT. Also: SPT leaks through store addresses (`:418`), but store transmitters have no checker. The `check_ld` fallback scores them (`pipeline.py:334-336`), so report `str` hits separately, unscored. |
| M6 | Fold depth vs bound — **OK** | `last_committed_protset_p` is regenerated 8 deep in every `but 8` file (e.g. `STT_6_u_lpP.als:267`, `Recon_6_u_lpP.als:285`, `SPT_6_u_lpA.als:297`). In all `_u` blocks `prot_set_propagation_p` is the identity, so the fold returns the seed at any depth. | n/a | The "fold 7 deep invents leaks at N ≥ 8" trap (TWO_PHASE_MODELS.md:480) applies only to the old location folds (STT_6/Recon_6/STL `_6_stl`). It does not apply to `_u`. | None for STT/Recon lpP. SPT's real bound issue is the fixpoint (M4), not the fold. |

### K1b: run configs (what the overnight runs should copy)

| Row | Config to copy | Flags | Untaint on as the authors intend? |
|---|---|---|---|
| E3 stt-master | `runconfigs/twostage_fv2_20261109/E3_STT_6_u_fv2.jsonc` (same gem5 block as `fixed_20261030/STT_6_sttmaster_fixed_latest.jsonc`) | `/work/stt-master/build/X86/gem5.opt`, `se.py`, `DerivO3CPU`, `scheme: 2`, no extra_args. The glue sets `STT=1, threatModel='Spectre', implicitChannel=1, needsTSO=0` (`gem5-hooks/stt-master/stt_worktree_vs_e3283b9.diff:134-139`); `moreTransmitInsts` stays at its Param default 0, because the glue bypasses config_scheme (`stt_e3283b9/src/cpu/o3/O3CPU.py:173`). | **Yes.** STT untaint at the visibility point has no knob. needsTSO 0 (authors use 1) is the known HOOK_AUDIT decision. `--threat_model` is ignored when `--scheme` is set (HOOK_AUDIT #18), so do not add it. |
| E2 recon-modded (Recon-STT) | `runconfigs/twostage_fv2_20261109/E2_STT_6_u_fv2.jsonc` | `/work/gem5-recon-modded/build/X86/gem5.opt`, `se.py`, `X86O3CPU`, `scheme: 2` (= STT in the Kaxiras enum, HOOK_AUDIT.md:30), classic caches, no `--allow_leaked` | **Yes**, for Recon-STT. Reveal is off by design (every reveal path is gated on `allowLeaked`). Never add `--allow_leaked` on classic caches: reveal is dead there (R-SA-1). |
| E6 recon-ruby3 (authors' ReCon) | `runconfigs/twostage_fv2_20261109/E6_Recon_6_u_base.jsonc` (gem5 block identical to `runconfigs/recon_ruby3/Recon_6_recon_ruby3_authors.jsonc`) | `/work/gem5-recon-ruby3/build/X86/gem5.opt`, `se_ruby.py`, `scheme: 2`, `allow_leaked: true` (→ `--allow_leaked`, `gem5_common.py:430`), `--ruby --l0d_size=65536 --l0i_size=65536 --l0d_assoc=8 --l0i_assoc=8 --l1d_size=2MB --l1d_assoc=16 --l2_size=16MB --l2_assoc=32 --cacheline_size=64` | **Yes** (validated 2026-11-08: revealRequests sent and marked, EVAL_MANIFEST E6). |
| E11 SPT | **`runconfigs/fixed_20261030/SPT_6_oneLP_fence_fixed_latest.jsonc`**, with only `paths` changed to the new testset and base `instructions.jsonc`. There is no ultimate-era E11 campaign config (`twostage_fv2_20261109/make_campaign_configs.py:19`). | `/work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt`, `se.py`, `DerivO3CPU`, `scheme: 2`, extra_args `--applyDDIFT=1 --fwdUntaint=1 --bwdUntaint=1 --configImpFlow=Lazy --freeParam=3 --scheme=SpectreSafeFence` | **Yes, only this file**: it equals the authors' `run_spt.py:56` for `--untaint-method bwd` (`--freeParam=3`, Lazy, fwd = bwd = 1), except needsTSO 0 and classic caches (known decision). Both fwd and bwd must be set (cpu.cc:504 ANDs fwd into bwd, `gem5-hooks/gem5-spt/gem5-spt.patch:108-109`). |
| ✗ WRONG | `runconfigs/run_config_SPT_6.jsonc`, `_full`, `_oneLP`, `_FuturisticFence`, `_SpectreInvisibleSpec`, `_FuturisticInvisibleSpec`, `_disableUntaint` | All 7 lack `--freeParam`. `Options.py:346` defaults it to 0, `CpuConfig.py:185` assigns it unconditionally, and `rob_impl.hh:764` uses it as the untaint queue limit, so **forward and backward untaint are inert**. 5 of the 7 also use `--configImpFlow=Ignore` (no implicit-flow defense, so branch transmitters are unprotected). Two run the InvisibleSpec schemes (unprotected, SPT B2; decided not to run). | **No.** Must not be copied for E11. They belong to the archive move (C1) or need a header warning. |

### K1c: STL models

- **Skeleton:** `STT_6_u_stl` and `Recon_6_u_stl` differ from their branch bases only in the clause-1 selector line (`STT_6_u_stl.als:362`) and the `[u-3]` flavor facts placed inside the defense block (`u_stl_no_branch_speculation`, `u_stl_alias_atom`). The skeleton is verbatim, and clauses 2 and 3 are byte-identical to the branch model (plain `diff`). **OK.**
- **Speculation primitive:** the contract is "uncommitted and after an older store whose address is unresolved" (`u_store_shadow_p`), with branches forced resolved and a true alias fact. This is right for the build it runs on (`/work/gem5-recon-stl`, Recon-STT: store shadows count as speculation, `decode.cc:686-695`, `shadow_tracker.cc`). On `/work/stt-master` (Spectre: branches only) STL is out of scope (STL_SPECULATION.md:185), so STL tests must not be scored there. In the ReCon STL flavor an unresolved store does not conceal (§4.5.2 Table 1 case 1; open DECIDE). gem5-recon-stl is a classic-cache build without `--allow_leaked`, so on it the Recon STL corpus = Recon-STT. Its reveal semantics cannot be tested tonight; there is no STL + ruby3 build.
- **Legacy `STAGE1_alloy/models/*_6_stl.als`:** `STT_6_stl` puts its STL source block in the skeleton region (`STT_6_stl.als:277-300`, against the defense-block rule), uses the rf-based alias, and keeps STT_6's location fold, so it **inherits the UNSOUND R-1 clause** (`:371`, MODEL_AUDIT_SPT_RECON.md). CleanupSpec/InvisiSpec/SpecLFB `_6_stl` are `STT_6_stl` with only the leakage function changed to load addresses (verified by diff), on the old skeleton. The branch footprint models are on the ultimate skeleton (`Footprint_6_u`), so branch and STL footprint models no longer share a skeleton.
- **Blocking tonight:** STL-1 (check_footprint scores the wrong window) blocks scoring footprint STL. STL-4 (no run config points at the STL AMuLeT copies) blocks footprint STL runs. STL-2 (CleanupSpec cold `L2_TBEs`) blocks only CleanupSpec cold. STL-3 (SpecLFB counting) blocks only how SpecLFB STL hits are counted. U2 (atom- vs rf-alias) is a model choice, open. For STT/Recon STL there is a bigger gap: **no STL window checker exists** (STL_SPECULATION.md:209 "not built"; `gem5_common.py` has no `stl_window`). `check_ld`'s branch window `lc_retire < signal < fnc_retire` counts the architectural replay (STL_SPECULATION.md:220), so its STL numbers are not meaningful. Only `gem5-hooks/stl/stl_hooktest.py` scores the [hold, release) window. Also, `/work/gem5-recon-stl` predates the 2026-10-30 resolve hooks (`specs/gem5_builds.json:38`).
- **SPT-CONV (blocked, skipped):** scratch query `STAGE1_alloy/models/proposed/ultimate/queries/spt_conv8_lpA.als` (SPT_6_u_lpA + a 7th step; commands conv8_facts, conv8_gen, conv8_gen_xmflip) hit its 40-min timeout on the Mac (exit 124) while Kodkod was still translating, before any command ran, so there is no result. Until it runs (preferably on a cafe node), treat `but 8` SPT as unproven; the hand bound in M4 suggests 6 steps are enough.
- **What can run tonight:** generating `STT_6_u_stl` / `Recon_6_u_stl` corpora (Alloy + Stage 2 `stl_bypass`) is safe. The models are right and generation needs no decision except U2 (the atom alias is the drafted default). Running them on `/work/gem5-recon-stl`, scored with `stl_hooktest.py` and labelled "no STL window checker; stale build", is OK as a draft campaign, as RUNNING.md (e)(1) already says. Do not score STL with check_ld/check_br or check_footprint as if those numbers were results.

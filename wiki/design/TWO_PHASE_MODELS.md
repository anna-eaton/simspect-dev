# Two-phase (Stage 1 core → Stage 1.5 flesh-out) Alloy models — drafts for review

> **⛔ UNAPPROVED DRAFTS.** `STAGE1_alloy/models/proposed_twophase/SPT_6_oneLP_core.als` and `Recon_6_core.als` are new, unreviewed `.als` files. They, and anything enumerated from them (`testsets/*__twophase_draft/`), must **not** feed any production testset, campaign or paper number until Anna signs off clause by clause. No existing `.als` was modified (sha256 of `STT_6.als`, `SPT_6_oneLP.als`, `Recon_6.als`, `STT_6_core.als`, `STT_6_stl.als` re-checked unchanged after the runs started).

Written 2026-11-03 by the two-phase-models session (Anna's ask: "make sure we have two phase models for each alloy model we have, and they are up to date with all of our design decisions and grounded in the spec", then "start alloy runs of the finished models' first stages"). Scope was cut mid-task by the coordinator to the three production models (STT_6, SPT_6_oneLP, Recon_6); variants are inventoried but not drafted.

## TL;DR

- **STT_6** already has a two-phase version: `STAGE1_alloy/models/STT_6_core.als` (Stage 1) + `STT_6.als` itself (Stage 1.5, via `stage_seed.py` / `stage_pipeline.py`). It is **not stale**: re-deriving it from today's `STT_6.als` with the same three changes gives a file identical to `STT_6_core.als` once comments and whitespace are ignored. Only its comment is wrong ("same idx/IX symmetry-breaking as STT_6.als", `STT_6_core.als:285-286`; idx was removed) and its doc path is old (`mdsToRead/` → `wiki/findings/mdsToRead/`). Not edited.
- **SPT_6_oneLP** and **Recon_6** had none. Drafted `SPT_6_oneLP_core.als` and `Recon_6_core.als` with `proposed_twophase/derive_core.py`, which applies exactly the prototype's three changes and refuses if any anchor isn't found exactly once. Defense blocks and every other line are byte-identical to the production models.
- Tiny-scope checks: STT_6_core and Recon_6_core load and are SAT at `but 3` (the same 2 cores each: the Spectre-v1 skeleton with a load or a `br_x` transmitter). **SPT_6_oneLP_core loads but no core was found**: UNSAT at `but 3` (exhausted in 72 s) and 0 instances in 7–9 min at `but 4` / `but 5`, while SPT's own RR+RC+RS semantics on the same skeleton give 200 instances in 31 s at `but 4`. Its satisfiability is open; the Stage-1 run below is the test.
- **Stage-1 runs started** (background, at most 3 at once, cap 100000, 6 h timeout, disk guard) for STT_6, Recon_6 and SPT_6_oneLP. See "Runs".
- The big open call is still **RO+RI vs RI-only** in Stage 1 (URGENT_TODO #2, BIGFIG_FACT_AUDIT D4). The drafts follow the prototype (RO+RI), which is what the paper text says; new evidence below.

## Inventory

Status from `specs/alloy_relaxations.json` (`enumerated_final`), `specs/alloy_models.json`, `STAGE1_alloy/models/MANIFEST.md`; builds from `specs/defense_units.json`.

| Defense | Production file | Status | gem5 build(s) run against | Two-phase version? | Notes |
|---|---|---|---|---|---|
| STT | `STT_6.als` (sha256 `7a6ac4c0…`) | production, enumerated_final | `/work/stt` (STT-Spectre); `gem5-recon-modded` scheme 2 (Recon-STT), schemes 1/3 (Delay, DoM); `gem5-spt` STT-like subimpl; amulet SpecLFB / InvisiSpec / CleanupSpec reuse STT_6 | **yes, existing** `STT_6_core.als` (`d1fd8a64…`), up to date | Stage-1 run started (existing file, read only) |
| SPT | `SPT_6_oneLP.als` (`713d0904…`) | production, enumerated_final | `gem5-spt` (SpectreSafeFence + Futuristic / InvisibleSpec / disableUntaint variants) | **draft** `proposed_twophase/SPT_6_oneLP_core.als` (`63611dc1…`) | no core found at tiny scope yet; Stage-1 run started |
| Recon | `Recon_6.als` (`01252c82…`) | production, enumerated_final | `gem5-recon-modded` | **draft** `proposed_twophase/Recon_6_core.als` (`dfb81a80…`) | reveal clause is a no-op (R-1), so its cores equal STT_6's; Stage-1 run started |
| STT (STL) | `STT_6_stl.als` | variant, Anna-approved as a new file | `/work/gem5-recon-stl` | no (out of reduced scope) | RO+RI core is UNSAT by construction (see D4 evidence); RI-only is SAT (129 raw at `but 3`) |
| STT | `STT_6_commitsplit.als` | variant, clause review pending (URGENT_TODO) | `/work/stt` candidate testset | no | replaces clauses (b)/(c); needs its own core once reviewed |
| STT | `STT_6_futuristic.als` | variant, unreviewed | `/work/stt --threatModel=Futuristic` (planned) | no | |
| STT (OTB) | `STT_6_multisource.als` | variant, never enumerated | `gem5-recon-modded` (`recon_otb` unit) | no | OTB now lives in Stage 2 interleave (decision 2026-10-30), so a core is not needed for OTB |
| SPT | `SPT_6.als` (= `SPT_6_full.als`), `SPT_6_oneLP_noSTLF.als` | variants | `gem5-spt` | no | |

## How the two-phase models are built (and the decisions they encode)

**Stage 1 = `<X>_core.als`**, a copy of `<X>.als` with exactly the three changes of the prototype (`diff -u STT_6.als STT_6_core.als`; `wiki/findings/mdsToRead/STAGED_ENUMERATION.md:28-38`): (1) idx/IX0..IX5 symmetry-breaking removed so a core is not pinned to 6 positions; spo program-order facts kept; (2) operand-minimality (e) `all o: Operand | secure_speculation_scheme_p[RO->o]` and instruction-minimality (f) `all i: Instruction | secure_speculation_scheme_p[RI->i]` added to `gen_useful_litmus`, on top of the model's own RR + RC + RS (and, for SPT, its exactly-one-leak-point clause, kept verbatim); (3) scope `exactly 6 Instruction` → `but 6`. **Stage 1.5 = `<X>.als` itself** plus the structural `seed_core` predicate from `stage_seed.py`, spliced in by `stage_pipeline.py:58-65`; the needle it needs (`run gen_lit {\n  gen_useful_litmus\n}`) is present exactly once in all three production models (checked), so no Stage-1.5 model file is needed.

Decisions encoded, with where they come from:

- Stage 1 enforces every relaxation (RI, RO, RS, RC, RR); the first interleaving round turns RI and RO off but keeps state-sharing: paper `sections/pipeline.tex:28-52` ("we enforce that our graph is minimal along certain dimensions", the five relaxations) and `:58` ("we define a first round of instruction interleaving, which we do in the Alloy by removing some of the relaxations … we still require all instructions to share state that is necessary to the leakage backbone"; the commented line under it names RI and RO). Stage 1.5 keeping RS + `no_extra_inst` is that state-sharing rule.
- Figure `tikz/pipeline_full_8pt1col.tex` Stage 1.5 slabs: "+4. Pin: graph contains target Stage-1 graph", "1. Same as Stage 1", "2′. Loosened minimality", "3. Same as Stage 1": the seed + unchanged skeleton + unchanged defense block.
- Stage 1.5 becomes a real pipeline stage (Anna, 2026-11-02, `URGENT_TODO.md:32-33`): the drafts are written so `stage_pipeline.py --core-model proposed_twophase/<X>_core.als --flesh-model <X>.als` works unchanged. Wiring it into `pipeline.py` is not done.
- OTB is manufactured in Stage 2 interleave, not in the baseline (Anna, 2026-10-30, `URGENT_TODO.md:81-83`): the cores stay single-source; nothing added for OTB.
- The defense lives in the three-clause defense block; everything else is copied (CLAUDE.md): `derive_core.py` touches only the idx block, `gen_useful_litmus` and the `run` scope. Model-specific source facts (SPT's `one_insecure_speculation_scheme_p`, Recon's `p`-parameterized `hardware_protection_policy`) are copied as they are.
- Not encoded because still undecided: RO+RI vs RI-only (D4), `rf_from_most_recent_writer` alignment, the commit split, the resolution-flag-only-on-branches/stores question, and every defense-block paper fix below.

## Exact diffs against the production models

### STT_6.als → STT_6_core.als (existing prototype, unchanged)

Hunks: idx/IX removal (change 1), RO/RI clauses plus relabelled comments (change 2), scope (change 3). The comment block at the top of `gen_useful_litmus` is the stale one.

```diff
--- STT_6.als	2026-10-13 15:32:00
+++ STT_6_core.als	2026-10-20 17:10:14
@@ -34,18 +34,12 @@
 one sig TOthern  extends InstrType {} // ALU/reg->reg, doesnt xmit
 one sig TOtherx  extends InstrType {} // ALU/reg->reg, xmits
 
-// fixed position atoms for symmetry-breaking index (one sig = no atom permutation)
-one sig IX0 {} -- spo position 0 (first)å
-one sig IX1 {} -- spo position 1
-one sig IX2 {} -- spo position 2
-one sig IX3 {} -- spo position 2
-one sig IX4 {} -- spo position 2
-one sig IX5 {} -- spo position 2
+// [STAGE-1 CORE] idx/IX symmetry-breaking REMOVED (ordering rules stripped per
+// staged-enum design) so cores are not pinned to a fixed length/positions.
 
 // single concrete instruction sig
 sig Instruction {
 	kind: one InstrType,
-	idx: one (IX0 + IX1 + IX2 + IX3 + IX4 + IX5),  -- bijection to fixed position atoms
 
 	spo: lone Instruction,
 
@@ -273,48 +267,49 @@
 }
 
 /*********************************************************************************
- * Symmetry breaking — works because Instruction is now a concrete sig
+ * [STAGE-1 CORE] Symmetry breaking (idx/IX ordering rules) REMOVED.
+ * spo program-order facts (spo_acyclic/spo_prior/spo_total) are kept — they are
+ * execution semantics, not symmetry-breaking. a6CountModels runs symmetry=80.
  */
 
--- idx bijection: each instruction gets a unique fixed position atom
-fact idx_bijective { all disj a, b: Instruction | a.idx != b.idx }
-fact idx_surjective { (IX0 + IX1 + IX2 + IX3 + IX4 + IX5) = Instruction.idx }
 
--- IX0 < IX1 < IX2 is a fixed static ordering (no atom permutations possible)
-pred lt_ix[a, b: univ] { (a=IX0 and b in IX1+IX2+IX3+IX4+IX5) 
-				or (a=IX1 and b in IX2+IX3+IX4+IX5)
-				or (a=IX2 and b in IX3+IX4+IX5)
-				or (a=IX3 and b in IX4+IX5)
-				or (a=IX4 and b=IX5)
-
-}
-
--- idx rank mirrors spo rank: position 0 = first in spo, 1 = second, 2 = third
-fact idx_matches_spo {
-	all disj a, b: Instruction | lt_ix[a.idx, b.idx] <=> b in a.^spo
-}
-
-
 /*********************************************************************************
  * Run
  */
-let gen_useful_litmus {
-  not secure_speculation_scheme_p[no_p]
+// ─────────────────────────────────────────────────────────────────────────────
+// STAGE-1 "CORE" VARIANT (copy of STT_6.als; staged-enumeration base).
+// ONLY change vs STT_6.als = gen_useful_litmus turns on EVERY perturbation-
+// minimality clause, so each emitted instance is a MAXIMALLY-MINIMIZED leak core:
+// no removable operand (RO) and no removable instruction (RI) on top of STT_6's
+// existing resolution- (RR), commit- (RC) and state- (RS) minimality. Same sigs,
+// same STT defense, same idx/IX symmetry-breaking as STT_6.als -> instances are
+// re-imposable on STT_6.als with ZERO translation. Stage 2 seeds each core into
+// the real STT_6 (RO/RI OFF) and lets it add extra operands/instructions, capped
+// N per core. See mdsToRead/STAGED_ENUMERATION.md.
+// ─────────────────────────────────────────────────────────────────────────────
+let gen_useful_litmus {
+  not secure_speculation_scheme_p[no_p]                                        // (a) it leaks
 
-  //all i: resolved | secure_speculation_scheme_p[RR->i] or secure_speculation_scheme_p[RC->first_uncommitted]
-  // resolution-min on all unresolved EXCEPT the boundary instr
+  // (b) resolution-min on all unresolved EXCEPT the boundary instr
   all i: (unresolved - first_uncommitted) | secure_speculation_scheme_p[RR->i]
-  // boundary instr (first_uncommitted): necessity tested by commit AND resolve together
+  // (c) boundary instr (first_uncommitted): necessity tested by commit AND resolve together
   secure_speculation_scheme_p[RC->first_uncommitted + RR->first_uncommitted]
-
+  // (d) state-minimality (each State atom individually necessary)
   all s: State | secure_speculation_scheme_p[RS->s]
+
+  // (e) operand-minimality: every operand necessary (no removable operand)
+  all o: Operand     | secure_speculation_scheme_p[RO->o]
+  // (f) instruction-minimality: every instruction necessary (no removable instr)
+  all i: Instruction | secure_speculation_scheme_p[RI->i]
 }
 
 fact no_extra_inst {no ((Instruction-Branchns) - operands.Operand)} //no extra instrs except branches, while interleave fake
 
+// [STAGE-1 CORE] length restriction relaxed: 'exactly 6' -> 'up to 6' Instruction.
+// RI-minimality keeps cores small; this is just the upper bound for the search.
 run gen_lit {
   gen_useful_litmus
-} for 9 but exactly 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
+} for 9 but 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
 
 
 /*********************************************************************************
```

### SPT_6_oneLP.als → proposed_twophase/SPT_6_oneLP_core.als (draft)

Hunk 1: draft header. Hunks 2–3: change 1 (idx/IX sigs, `idx` field, symmetry-breaking facts). Hunk 4: change 2, (e) RO + (f) RI appended after SPT's own RR/RC/RS clauses; the oneLP leak clause `one_insecure_speculation_scheme_p[no_p]` is untouched. Hunk 5: change 3, scope.

```diff
--- SPT_6_oneLP.als	2026-10-13 15:31:59
+++ proposed_twophase/SPT_6_oneLP_core.als	2026-11-03 01:58:51
@@ -1,3 +1,13 @@
+// =============================================================================
+// [STAGE-1 CORE DRAFT — UNAPPROVED, do not use for production testsets]
+// Derived from SPT_6_oneLP.als (sha256 713d0904d91aa9cb5a25a33c1e60ae1156a38caea0d9c1173d4a7959aa898809) by
+// STAGE1_alloy/models/proposed_twophase/derive_core.py --minimality rori.
+// Same three changes as the STT_6_core.als prototype: idx/IX symmetry-breaking
+// removed, minimality (e) RO + (f) RI added to gen_useful_litmus, scope 'exactly 6'
+// -> 'but 6' Instruction. Everything else (skeleton, source facts, defense
+// block) is byte-identical to SPT_6_oneLP.als. Stage 1.5 = SPT_6_oneLP.als itself +
+// stage_seed.py seed (stage_pipeline.py). Review: wiki/design/TWO_PHASE_MODELS.md
+// =============================================================================
 
 
 /*********************************************************************************
@@ -34,18 +44,12 @@
 one sig TOthern  extends InstrType {} // ALU/reg->reg, doesnt xmit
 one sig TOtherx  extends InstrType {} // ALU/reg->reg, xmits
 
-// fixed position atoms for symmetry-breaking index (one sig = no atom permutation)
-one sig IX0 {} -- spo position 0 (first)å
-one sig IX1 {} -- spo position 1
-one sig IX2 {} -- spo position 2
-one sig IX3 {} -- spo position 2
-one sig IX4 {} -- spo position 2
-one sig IX5 {} -- spo position 2
+// [STAGE-1 CORE] idx/IX symmetry-breaking REMOVED (ordering rules stripped per
+// staged-enum design) so cores are not pinned to a fixed length/positions.
 
 // single concrete instruction sig
 sig Instruction {
 	kind: one InstrType,
-	idx: one (IX0 + IX1 + IX2 + IX3 + IX4 + IX5),  -- bijection to fixed position atoms
 
 	spo: lone Instruction,
 
@@ -284,28 +288,12 @@
 }	
 
 /*********************************************************************************
- * Symmetry breaking — works because Instruction is now a concrete sig
+ * [STAGE-1 CORE] Symmetry breaking (idx/IX ordering rules) REMOVED.
+ * spo program-order facts (spo_acyclic/spo_prior/spo_total) are kept — they are
+ * execution semantics, not symmetry-breaking. a6CountModels runs symmetry=80.
  */
 
--- idx bijection: each instruction gets a unique fixed position atom
-fact idx_bijective { all disj a, b: Instruction | a.idx != b.idx }
-fact idx_surjective { (IX0 + IX1 + IX2 + IX3 + IX4 + IX5) = Instruction.idx }
 
--- IX0 < IX1 < IX2 is a fixed static ordering (no atom permutations possible)
-pred lt_ix[a, b: univ] { (a=IX0 and b in IX1+IX2+IX3+IX4+IX5) 
-				or (a=IX1 and b in IX2+IX3+IX4+IX5)
-				or (a=IX2 and b in IX3+IX4+IX5)
-				or (a=IX3 and b in IX4+IX5)
-				or (a=IX4 and b=IX5)
-
-}
-
--- idx rank mirrors spo rank: position 0 = first in spo, 1 = second, 2 = third
-fact idx_matches_spo {
-	all disj a, b: Instruction | lt_ix[a.idx, b.idx] <=> b in a.^spo
-}
-
-
 /*********************************************************************************
  * Run
  */
@@ -320,13 +308,20 @@
   secure_speculation_scheme_p[RC->first_uncommitted + RR->first_uncommitted]
 
   all s: State | secure_speculation_scheme_p[RS->s]
+
+  // [STAGE-1 CORE] (e) operand-minimality: every operand necessary (no removable operand)
+  all o: Operand     | secure_speculation_scheme_p[RO->o]
+  // [STAGE-1 CORE] (f) instruction-minimality: every instruction necessary (no removable instr)
+  all i: Instruction | secure_speculation_scheme_p[RI->i]
 }
 
 fact no_extra_inst {no ((Instruction-Branchns) - operands.Operand)} //no extra instrs except branches, while interleave fake
 
+// [STAGE-1 CORE] length restriction relaxed: 'exactly 6' -> 'up to 6' Instruction.
+// RI-minimality keeps cores small; this is just the upper bound for the search.
 run gen_lit {
   gen_useful_litmus
-} for 9 but exactly 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
+} for 9 but 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
 
 
 /*********************************************************************************
```

### Recon_6.als → proposed_twophase/Recon_6_core.als (draft)

Same hunks and reasons as SPT. The `p`-parameterized `hardware_protection_policy[p]` defense clause is untouched.

```diff
--- Recon_6.als	2026-10-13 15:31:59
+++ proposed_twophase/Recon_6_core.als	2026-11-03 01:58:51
@@ -1,3 +1,13 @@
+// =============================================================================
+// [STAGE-1 CORE DRAFT — UNAPPROVED, do not use for production testsets]
+// Derived from Recon_6.als (sha256 01252c82c6c0b75522e7c465b92b1c7e9631c94a9bd7a9fa6d7d7b8fc5ab8247) by
+// STAGE1_alloy/models/proposed_twophase/derive_core.py --minimality rori.
+// Same three changes as the STT_6_core.als prototype: idx/IX symmetry-breaking
+// removed, minimality (e) RO + (f) RI added to gen_useful_litmus, scope 'exactly 6'
+// -> 'but 6' Instruction. Everything else (skeleton, source facts, defense
+// block) is byte-identical to Recon_6.als. Stage 1.5 = Recon_6.als itself +
+// stage_seed.py seed (stage_pipeline.py). Review: wiki/design/TWO_PHASE_MODELS.md
+// =============================================================================
 
 
 /*********************************************************************************
@@ -34,18 +44,12 @@
 one sig TOthern  extends InstrType {} // ALU/reg->reg, doesnt xmit
 one sig TOtherx  extends InstrType {} // ALU/reg->reg, xmits
 
-// fixed position atoms for symmetry-breaking index (one sig = no atom permutation)
-one sig IX0 {} -- spo position 0 (first)å
-one sig IX1 {} -- spo position 1
-one sig IX2 {} -- spo position 2
-one sig IX3 {} -- spo position 2
-one sig IX4 {} -- spo position 2
-one sig IX5 {} -- spo position 2
+// [STAGE-1 CORE] idx/IX symmetry-breaking REMOVED (ordering rules stripped per
+// staged-enum design) so cores are not pinned to a fixed length/positions.
 
 // single concrete instruction sig
 sig Instruction {
 	kind: one InstrType,
-	idx: one (IX0 + IX1 + IX2 + IX3 + IX4 + IX5),  -- bijection to fixed position atoms
 
 	spo: lone Instruction,
 
@@ -263,28 +267,12 @@
 }
 
 /*********************************************************************************
- * Symmetry breaking — works because Instruction is now a concrete sig
+ * [STAGE-1 CORE] Symmetry breaking (idx/IX ordering rules) REMOVED.
+ * spo program-order facts (spo_acyclic/spo_prior/spo_total) are kept — they are
+ * execution semantics, not symmetry-breaking. a6CountModels runs symmetry=80.
  */
 
--- idx bijection: each instruction gets a unique fixed position atom
-fact idx_bijective { all disj a, b: Instruction | a.idx != b.idx }
-fact idx_surjective { (IX0 + IX1 + IX2 + IX3 + IX4 + IX5) = Instruction.idx }
 
--- IX0 < IX1 < IX2 is a fixed static ordering (no atom permutations possible)
-pred lt_ix[a, b: univ] { (a=IX0 and b in IX1+IX2+IX3+IX4+IX5) 
-				or (a=IX1 and b in IX2+IX3+IX4+IX5)
-				or (a=IX2 and b in IX3+IX4+IX5)
-				or (a=IX3 and b in IX4+IX5)
-				or (a=IX4 and b=IX5)
-
-}
-
--- idx rank mirrors spo rank: position 0 = first in spo, 1 = second, 2 = third
-fact idx_matches_spo {
-	all disj a, b: Instruction | lt_ix[a.idx, b.idx] <=> b in a.^spo
-}
-
-
 /*********************************************************************************
  * Run
  */
@@ -298,13 +286,20 @@
   secure_speculation_scheme_p[RC->first_uncommitted + RR->first_uncommitted]
 
   all s: State | secure_speculation_scheme_p[RS->s]
+
+  // [STAGE-1 CORE] (e) operand-minimality: every operand necessary (no removable operand)
+  all o: Operand     | secure_speculation_scheme_p[RO->o]
+  // [STAGE-1 CORE] (f) instruction-minimality: every instruction necessary (no removable instr)
+  all i: Instruction | secure_speculation_scheme_p[RI->i]
 }
 
 fact no_extra_inst {no ((Instruction-Branchns) - operands.Operand)} //no extra instrs except branches, while interleave fake
 
+// [STAGE-1 CORE] length restriction relaxed: 'exactly 6' -> 'up to 6' Instruction.
+// RI-minimality keeps cores small; this is just the upper bound for the search.
 run gen_lit {
   gen_useful_litmus
-} for 9 but exactly 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
+} for 9 but 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool
 
 
 /*********************************************************************************
```

## Tiny-scope checks (local, `java -cp alloy6.jar:. a6CountModels`, scratch copies with the scope edited)

| Model | Scope | Result | Time | Exhausted (UNSAT reached)? |
|---|---|---|---|---|
| STT_6_core (RO+RI) | but 3 | 2 cores: `br_n(unresolved) → ld → ld[xm]`, `br_n(unresolved) → ld → br_x[xm]` | 300 s timeout | no (matches the 2026-10-26 finding that the proof is slow without idx) |
| Recon_6_core (RO+RI) | but 3 | the same 2 cores | 15 s | yes |
| SPT_6_oneLP_core (RO+RI) | but 3 / 4 / 5 | 0 / 0 / 0 | 72 s / 420 s timeout / 544 s timeout | yes / no / no |
| STT_6 RI-only (scratch) | but 3 | 129 raw (= the 80 canonical of TWO_STAGE_STT_FEASIBILITY.md §6) | 8 s | yes |
| Recon_6 RI-only (scratch) | but 3 | 129 raw | 24 s | yes |
| SPT_6_oneLP RI-only (scratch) | but 3 / 4 | 0 / 0 | 33 s / 544 s timeout | yes / no |
| SPT_6_oneLP RR+RC+RS on the idx-free skeleton (scratch) | but 4 / 5 | 200 (cap) / 200 (cap) | 31 s / 33 s | capped |
| STT_6_stl RO+RI (scratch, not a repo draft) | but 3 | 0 | 4 s | yes |
| STT_6_stl RI-only (scratch) | but 3 | 129 raw | — | yes |

Peak RSS was 250–400 MB per JVM. In every STT/Recon core only the gate branch is unresolved; no load or ALU op carries an unresolved flag, so the flag-duplicate worry (`URGENT_TODO.md:15`) does not show up in Stage 1 at this scope. Copies and outputs: `results/twophase_stage1_2026-11-03/` (`derived/`, `tiny/`, the `diff_*.txt` files and `tools/`; moved out of the session scratchpad 2026-11-04, the PDF text extracts were not kept).

## Defense blocks vs. the papers (not changed; proposals only)

All three drafts keep the production defense block byte-identical, so they inherit these. The disagreements were found by the 2026-10-28 audits (`wiki/findings/audits/2026-10-28/alloy_STT_6.md`, `alloy_SPT_6_oneLP.md`, `alloy_Recon_6.md`, `APPROVALS.md`). This session re-checked each quote below against the PDFs in `~/Documents/quail/sources/papers/` (PDF page numbers, `pdftotext` per page). Nothing new was found beyond the audits.

**STT (`yu-2019-stt.pdf`).** Matches: speculation contract `uncommitted & has_unresolved_brs_p` = p5 "In the Spectre model, an instruction has reached the visibility point if all older control-flow instructions have resolved"; `leakage_function = Loads.inaddr + Branchxs.inreg` = p5 "Classifying only loads as transmitters will block memory system-related explicit covert channels" plus "classify explicit branch instructions"; stores left out = p5 "We assume that stores trigger a cache coherence invalidation only on retirement, or else are defined as transmitters". Disagreements: (1) untaint is per memory **state**, not per load instance (`STT_6.als:331`), but p6 says "If a load is unsafe, its output is always tainted"; proposed (STT-3, not applied): seed taint from `(Loads & has_unresolved_brs_p[p]).outreg` and test reachability from it. (2) The store-to-load forwarding implicit branch is missing: p5 "identify the implicit branches that represent additional sources of data-dependent resource usage, e.g., store-to-load forwarding", p8 "store-to-load forwarding creates an implicit channel because the load M2 accesses the cache only if it does not alias with the store S"; proposed (STT-1): `fun leakage_function : Operand {Loads.inaddr + Branchxs.inreg + (Stores & (^spo).Loads).inaddr}`.

**SPT (`choudhary-2021-spt.pdf`).** Matches: contract = p3 "in the Spectre model (which covers control-flow speculation), it is when all older control-flow instructions have resolved"; seed of almost all operands = p6 "all program data (memory and architectural registers) starts off as tainted"; declassification = p6 "the operands of transmitters/branches are untainted when the instruction becomes non-speculative"; forward ALU rule = p7 "if all of the instruction's operands are untainted, then its output register becomes untainted". Disagreements: (1) backward untaint removes the whole backward cone (`SPT_6_oneLP.als:349`), but p7 allows only "For register MOV instructions (r2 = r1): if the output is untainted, then the operand is untainted" and "For invertible arithmetic instructions (e.g., ADD): if the output is untainted and all but one of the inputs are untainted, then the remaining input is untainted" (SPT-2: per-instruction rules). (2) The STL untaint (`:357`) ignores STLPublic: p7 "STLPublic(S, L) holds if and only if L's address is untainted, and the addresses of all stores older than L and younger than S (including S) are untainted"; p8 Fig. 5 "Naive untaint propagation over store-to-load forwarding leaks tainted data" (SPT-3: gate on both addresses). (3) The final `^op_edges` closure (`:259/271/280`) re-taints what the STL rule untainted, against p7 rule ① "If S's data operand gets untainted, then L's output register should be untainted" (SPT-1: drop the closure term). (4) One forward pass in spo order, but p7 "untainting of a register by instruction I can cause instructions both younger and older than I to untaint registers" (run the 6-step fold 2–3 times).

**ReCon (`aimoniotis-2023-recon.pdf`, a 3-page extraction).** Paper: reveal happens only at commit of a direct load pair, p2 §5.2 "When the second load (LD2) of a load-pair commits, the address accessed by the first load (LD1) is marked as revealed", p1 §4.3 "RECON limits its detection to only the leakage of load pairs with a direct dependence"; conceal on store commit, p2 §5.2 "upon the commit of a store instruction, the bit of the corresponding word is cleared"; speculation sources, p1 §3.1 "For evaluation, we use only speculation cast by control flow and store instructions". Model: the reveal term in `hardware_protection_policy[p]` (`Recon_6.als:316-318`) only removes states the STT fold at `:323` already removes (R-1), so Recon_6 behaves as STT_6 minus `rf_from_most_recent_writer`. **Corroborated today:** Recon_6_core and STT_6_core give the same 2 cores at `but 3`, and their RI-only versions the same 129. Proposed (R-2, not applied): a single-hop reveal `fun revealed_p[p] : State { (Loads.inmem).opstate & (~opstate).((~inmem).(Loads & (rf_p[p].((Loads - speculation_contract_p[p]).inaddr)).~outreg)) }` with LD2 restricted to `committed_p`, a store-commit conceal, and instance-based untaint; plus a store-shadow contract if the build's threat model needs it.

## Runs (Stage 1 only, started 2026-11-03 03:19–03:20 PST, local Mac)

Free disk at start 88–94 GB (`df -h /System/Volumes/Data`). Runner: `STAGE1_alloy/models/proposed_twophase/run_stage1.py`, the repo's `a6CountModels` driver as `pipeline.py:phase_xml` calls it, `-Xmx4g`, cap 100000 (= `alloy.max_instances` in `runconfigs/*.jsonc`), timeout 21600 s (6 h), refuses to start under 50 GB free and kills java under 40 GB. The log records start/end, the exact command, the model sha256, the scope line, progress every 60 s, the verdict (`EXHAUSTED` = solver reached UNSAT below the cap = bounded-exhaustive at `but 6` up to symmetry=80; `CAPPED`; `TIMEOUT`; `DISK_GUARD`; `ERROR`) and the full java stdout/stderr.

| Model | Runner PID | java PID | Core file | Output (gitignored) | Log |
|---|---|---|---|---|---|
| STT_6 | 67090 | 67093 | `STAGE1_alloy/models/STT_6_core.als` | `testsets/STT_6__twophase_draft/stage1_xml/` | `~/Library/Logs/simspect/twophase_STT_6.log` |
| Recon_6 | 67091 | 67094 | `proposed_twophase/Recon_6_core.als` | `testsets/Recon_6__twophase_draft/stage1_xml/` | `~/Library/Logs/simspect/twophase_Recon_6.log` |
| SPT_6_oneLP | 67140 | 67142 | `proposed_twophase/SPT_6_oneLP_core.als` | `testsets/SPT_6_oneLP__twophase_draft/stage1_xml/` | `~/Library/Logs/simspect/twophase_SPT_6_oneLP.log` |

Launch command (one per model, from `STAGE1_alloy/models/proposed_twophase/`): `nohup python3 -u run_stage1.py --name <M> --model <core.als> --out <repo>/testsets/<M>__twophase_draft/stage1_xml --log ~/Library/Logs/simspect/twophase_<M>.log > ~/Library/Logs/simspect/twophase_<M>.nohup.txt 2>&1 &`. Monitor: `tail -f ~/Library/Logs/simspect/twophase_*.log` (look for `VERDICT=`), or `ls testsets/<M>__twophase_draft/stage1_xml | grep -c xml`. Kill: `kill <runner PID> <java PID>` (killing only the runner leaves java running; kill both, or `pkill -f a6CountModels`). The runner refuses to reuse a non-empty output dir; delete it to rerun. Stage 1.5 was not run; when a core set is in hand: `cd STAGE1_alloy && python3 stage_pipeline.py --core-model models/proposed_twophase/<X>_core.als --flesh-model models/<X>.als --out-xml-dir ../testsets/<X>__twophase_draft/xml` (note it re-runs Stage 1 itself; it doesn't yet accept existing cores).

## Open decisions for Anna

- [ ] DECIDE: approve, change or drop the drafts `SPT_6_oneLP_core.als` and `Recon_6_core.als` (diffs above), and whether `proposed_twophase/` is the right home (the dashboard's model table globs `STAGE1_alloy/models/*.als` non-recursively, so drafts and their runs are not visible there yet).
- [ ] DECIDE (D4, URGENT_TODO #2): Stage 1 minimality RO+RI (prototype, matches `pipeline.tex:45-58`) or RI-only (rebuilds in-use exactly at N=3, TWO_STAGE_STT_FEASIBILITY.md §9). New evidence: at `but 3`, RO+RI gives 2 STT/Recon cores vs 129 raw RI-only; RO deletes the STL mechanism outright (the store's `outmem` is required by `stl_alias_pair` but never on the leak path, so `secure[RO->s.outmem]` always fails: 0 at `but 3`, exhausted in 4 s); SPT gives 0 under both at `but 3`/`4`. Recommendation: RI-only if Stage 1.5 must reproduce the in-use corpora (and for STL it is the only option); RO+RI only if you want a smaller, different corpus.
- [ ] DECIDE: SPT's Stage 1. If the SPT run ends `TIMEOUT` with 0 cores, either SPT's one-leak-point clause plus RI/RO has no small solution, or the search is just slow. Options: (a) RI-only for SPT; (b) keep SPT flat (no Stage 1) until A1 / SPT-1..3 land; (c) a longer run on cafe2. Recommendation: wait for the run, then (a) with a longer bound.
- [ ] DECIDE: "bounded exhaustive" needs the Stage-1 verdict `EXHAUSTED`. Without idx symmetry-breaking even STT at `but 3` didn't prove UNSAT in 300 s. If the 6 h runs time out, accept "bounded, non-exhaustive" wording, or add a length-agnostic symmetry break to the cores (a model change).
- [ ] DECIDE: the cores copy `rf_from_most_recent_writer` verbatim, so STT_6_core has it and the SPT/Recon drafts don't (same open item as `URGENT_TODO.md:31`). Align all models (and cores) before any staged campaign?
- [ ] DECIDE: Recon_6_core equals STT_6_core in practice (R-1). Run Recon's Stage 1/1.5 at all before the R-2 reveal rewrite?
- [ ] DECIDE: draft two-phase versions for the variants too (STT_6_stl needs RI-only; STT_6_commitsplit / _futuristic after their reviews)?
- [ ] DECIDE: the paper disagreements above (STT-1, STT-3, SPT-1..3, R-1/R-2) are existing items in `URGENT_TODO.md:74-76`; any fix there changes the production model and the core together (re-run `derive_core.py`).
- [ ] TODO (not a decision): fix the stale comment in `STT_6_core.als:279-289` when you next touch it (it claims idx is kept).

## 2026-11-07 — RESOLVED: why SPT Stage-1 produced 0 (and it is NOT RO over-pruning)

The 6 h Stage-1 runs finished (2026-11-03): STT_6 → 2 skeletons, Recon_6 → 2, **SPT_6_oneLP → 0** (`VERDICT=EXHAUSTED`, genuine UNSAT, no crash). Anna asked for the root cause: is SPT mis-modeled, or does the SPT case need a different minimality rule. Investigated 2026-11-07 (deep-dive session); evidence below is reproducible.

**Isolation sweep (scratch copies outside `models/`, scope 5, cap 150; STT as control):** each perturbation applied alone.

| variant | STT (control) | SPT |
|---|---|---|
| base (no RO/RI; RR+RC+RS only) | 150 (capped, 5 s) | **150 (capped, 17 s)** |
| RI-only | 129 | **0** |
| RO-only | 67 | **0** |
| RO+RI | 2 | **0** |

**Finding 1 — it is not RO.** For SPT, **RI-only *and* RO-only each independently give 0**; RR/RC/RS necessity (present in the base run) are fine. So the earlier "RO over-prunes" framing (`RIONLY_BASELINE_PROOF.md`) is the wrong diagnosis for SPT: *no* SPT leak is minimal under removing *any* instruction *or* *any* operand, even though SPT base leaks are abundant (150+). STT is non-zero under every rule. This is SPT-specific and structural.

**Finding 2 — it is not the base-predicate mismatch.** SPT's base is `one_insecure_speculation_scheme_p` (exactly one leaker) while necessity is tested with `secure_speculation_scheme_p` (zero leakers); STT uses `not secure_speculation_scheme_p` (≥1) for both. Swapping SPT's base to STT's `not secure` form **still gave 0** under RI-only / RO-only / both (scope 5). So the mismatch is not the cause.

**Finding 3 — root cause (strongly supported, one confirmation step pending): SPT's protection-set *seed* is unperturbed and computed over the *whole* program.** `SPT_6_oneLP.als:341` — `fun hardware_protection_policy: Operand {Instruction.operands - ((Inreg + Inaddr) - Instruction.outreg.rf)}` — has no `[p]` parameter and references the full `Instruction`/`Instruction.outreg.rf`. So when RI removes an instruction (or RO an operand), the protected set does **not** shrink: the transmitter stays protected, so the leak survives almost every removal → no leaking instance is minimal → UNSAT. STT avoids this because its seed is `STT_6.als:326` `fun hardware_protection_policy: State {Mem_s}` — a pure sig, genuinely independent of which instructions exist — and *all* instruction-sensitivity lives in the **perturbed** `prot_set_propagation_p[p,…]`, so removals do shrink STT's protection and minimal instances exist. This is the same operand-based seed already flagged as the A1 protection-set issue (`wiki/findings/mdsToRead/PROTECTION_SET_REEVAL.md`). *Pending confirmation:* build an SPT variant with a perturbation-aware seed `hardware_protection_policy_p[p]` (over `i_p[p]`) and check RI/RO necessity becomes SAT — this is a semantics change, so it needs Anna's sign-off before trying.

**Consequence for the two-phase build.** The RO+RI "most-minimal skeleton" Stage-1 is **incompatible with SPT's current model** — not fixable by dropping RO (RI-only is also 0). STT/Recon are unaffected (2 cores each). Options for SPT, Anna-leaning-conservative ("over-generate, rule out"): (1) SPT Stage-1 = **no removal-minimality** (base + RR/RC/RS only, capped + dedup) → over-generates, works today; (2) **scope-ladder minimality** (enumerate N=3..6, dedup by fingerprint, keep smallest distinct shapes) → small cores without the broken removal test; (3) **fix the seed** to be perturbation-aware (Finding 3 / A1 rework) → correct long-term, changes SPT semantics, needs approval. Decision is Anna's; see URGENT_TODO.

**2026-11-08 — conservative run done (option 1, Anna-approved "simplest, run ASAP").** New file `STAGE1_alloy/models/proposed_twophase/SPT_6_oneLP_core_conservative.als` = SPT core with the RO (line 314) and RI (line 317) clauses commented; base `one_insecure` + RR/RC/RS untouched; scope `up to 6`. Enumerated **20000 instances (CAPPED at 20000)** in ~12 min → `testsets/SPT_6_oneLP__twophase_draft_conservative/stage1_xml/` (host MacBook-Pro-146, local). Confirms at full scope that no-removal-minimality over-generates heavily (full set > 20000). This is SPT's Stage-1 corpus for round 2 until/unless the seed fix (option 3 / A1) is done. No existing `.als` edited.

## 2026-11-08 — STL split cores (stl-spec session)

Each main model now has an STL draft (`STAGE1_alloy/models/MANIFEST.md`, `wiki/design/STL_SPECULATION.md` "STL for every main model"), and each STL model has a Stage-1 core draft made by `derive_core.py`. No existing file in this folder was edited.

| Core draft | From | Minimality | Small-scope check | Stage-1 run |
|---|---|---|---|---|
| `proposed_twophase/STT_6_stl_core.als` | `STT_6_stl.als` (approved) | RI-only (`--minimality ri`; RO+RI is UNSAT for STL by construction, D4 evidence above) | 200 (capped) at ≤3 in 12 s, at ≤4 in 67 s | **EXHAUSTED: 306 cores at ≤6** (13:58–14:20): `testsets/STT_6_stl__twophase_draft/stage1_xml`, log `~/Library/Logs/simspect/twophase_STT_6_stl.log` |
| `proposed_twophase/Recon_6_stl_core.als` | `proposed/Recon_6_stl.als` (draft) | RI-only | 200 at ≤3 in 31 s, at ≤4 in 165 s | started 2026-11-08 13:58, same settings: `testsets/Recon_6_stl__twophase_draft/stage1_xml`, `twophase_Recon_6_stl.log` |
| `proposed_twophase/SPT_6_oneLP_stl_core_conservative.als` | `proposed/SPT_6_oneLP_stl.als` (draft) | none (RI line commented, the SPT conservative convention) | UNSAT at ≤3 and ≤4: SPT's RS-minimality conflicts with the alias fact (see the STL doc) | not run (nothing to enumerate until the RS DECIDE) |

The RI-only cores are not small: both hit the 200 cap at ≤3, unlike the RO+RI STT_6 core (2 cores). That is the known RI-only trade-off (#2). Stage 1.5 for these cores waits on the Stage-1.5 machinery, which isn't built for any family yet.

## 2026-11-09 — Dedup and shape-coverage audit of Stage 1 → 1.5 → 2 (dedup-audit-s15 session)

Anna's ask: where can the pipeline deduplicate much more (Stage 1.5 especially, and the concretization stage), can Stage 1.5 form all the shapes including bigger ones with unnecessary instructions, is there a good way to randomize the Kodkod search in the second phase, and track the protection-set fold when the bound grows. Read-only audit: no `.als`, `parsexml.py`, launcher or hook was edited. Tools (tracked): `STAGE1_alloy/models/proposed_twophase/dedup_audit/`. Data and scratch queries (gitignored, 232 MB): `results/dedup_audit_2026-11-09/`. cafe2 numbers come from `/tests/simspect_alloy_20261108` (read-only, `remote_measure.py`).

### Headline finding: the two-stage corpus is a strict subset of the flat model at exactly 6

Fresh flat samples of today's `STT_6.als` (sha `7a6ac4c0…`, `exactly 6`), 4,000 instances each, checked with `flat_core_coverage.py` (does the instance contain any of the 129 Stage-1 cores under exactly the `stage_seed.build_pred` semantics; validated on 400 Stage-1.5 outputs, 400/400 contain their core):

| flat sample | contain a core (current pin) | contain no core | of those, an ALU feeds the transmitter | contain a core under the path pin |
|---|---|---|---|---|
| default SAT4J order | 4,000 | 0 | 0 | 4,000 |
| random seed 11 | 3,947 | 53 | 53 | 4,000 |
| random seed 12 | 3,940 | 60 | 60 | 4,000 |
| random seed 13 | 3,940 | 60 | 60 | 4,000 |

So about 1.4% of randomly ordered flat instances are valid production leaks that Stage 1.5 can never emit, and every one of them is the same class: an ALU op (`other_n`/`other_x`) sits on the dataflow into the transmitter (`ld → other → xmit`, including the OTB precursor `other.outreg → xm.inaddr`). Examples: `results/dedup_audit_2026-11-09/randprobe/flat_seed11/inst-000049.txt`, `flat_seed13/inst-000004.txt`, `flat_seed12/inst-000027.txt`. The default order shows 0 only because of the known order bias (0/300 ALU-on-path unforced, stage15-bound).

Mechanism (from the model text, consistent with every Stage-1 k4/k5/k6 partition exhausting at 0): the RI perturbation bridges the hole when it removes an instruction (`fix_rf_hole_p`, `STT_6.als:218`: `rf.(ddi :> removed.operands).rf`), so an on-path ALU is never removal-necessary and the minimal core of `br, ld, other, xmit` is the 3-instruction core with a direct `ld.outreg → xmit` edge. The Stage-1.5 pin then demands that exact direct edge (`ob in oa.rf`, `stage_seed.py`), and `one_entering_rf` forbids the transmitter operand from also reading the ALU. Stage 1 minimizes with bridging, Stage 1.5 pins without it. The path pin (`ob in oa.rf.*(ddi.rf)`, pin (b) of the stage15-bound section, `make_s15_model.py --pin b`) is the exact inverse of the bridge, and with it 12,000/12,000 random flat instances contain a core. The "RI-only ⊕ flesh is expected exact at every N" argument in `TWO_STAGE_STT_FEASIBILITY.md` §8 (verified only at N=3) is therefore false at N=6 under the current pin. Two solver confirmations did not finish (not results): the exact query "flat instance containing no core" (`q_uncovered_STT_6_exactly6.als`, 129 negated seeds) was still translating after 9.5 min, and "an on-path ALU that is RI-necessary" gave no instance in 4 min.

What this means for results so far: the Stage-1.5 XML corpora (STT_6 93,041 etc.) have no ALU on the transmitter path in Alloy; the fanout-v2 Stage-2 splice adds one after the fact (996/1,301 ld tests) but that is not model-checked, and for SPT/ReCon an added instruction can declassify. Nothing already found is invalidated; the gap is coverage.

### Dedup: measured waste and where it is

| where | measured | cause | fix |
|---|---|---|---|
| Stage 1 cores | STT_6 129 → 80 distinct (38% redundant), STT_6_stl 306 → 252 (18%), Recon_6_stl 858 → 396 (54%) | cores drop the IX symmetry break, so the same core comes back under atom renamings | fingerprint cores before Stage 1.5 (`audit_core_dups.py`; agrees exactly with the `merge_stage15.py` fingerprint) |
| Stage 1.5 STT_6 | 296,170 produced → 93,041 kept; 21,726 dropped copies came from an identical core, 181,403 from a different core | a 6-instruction program contains several cores; each core's run re-enumerates it | see options below |
| Stage 1.5 budget | 125/129 STT_6 core runs CAPPED at 2,326, only 4 EXHAUSTED; 47 cores kept < 10% new, 2 kept 0. STT_6_stl: 266/306 capped, 36 cores kept 0, 119 kept < 10% | first-core-wins merge plus a deterministic solver order: later cores spend their cap re-finding earlier cores' instances and never reach their own | randomized order, core dedup, adaptive top-up |
| copies per distinct STT_6 instance | 1: 36,202; 2: 19,008; 3: 9,047; 4: 9,394; 5–9: 14,429; 10+: 4,961 | same | same |
| Stage 2 exact duplicates | STT_6_fv2 93,041 tests → 93,041 distinct asm; STT_6_u_fv2 93,157 → 93,157; Recon_6_u_base 93,092 → 93,088 distinct asm text, 93,092 distinct asm+ann | the XML fingerprint already separates everything concretization separates | nothing to gain from an asm-hash dedup inside one corpus |
| across families | STT_6 ∩ STT_6_u = 91,962 of 93,041 / 93,157; STT_6_u ∩ Recon_6_u = 92,081 of 93,157 / 93,092 (XML fingerprints) | three Stage-1.5 runs, three merges and five Stage-2 compiles of ~99% the same programs; the u-vs-base gem5 comparison reran them | one fingerprint-keyed corpus with family tags; run only the set difference (≈1,100–1,200 programs) for a new family on a build that already ran the old one |

Within one core's run there are 0 duplicates (IX symmetry break at `exactly 6`), and the merge fingerprint is sound on the cores (matches an independent isomorphism check that minimizes over same-slot operand orderings). Stage-2 random choices are seeded from the stem name (`batch_generate.py:110`, `parsexml.py:2307/2356/2561`), so the same XML under a different number concretizes differently; a cross-family cache needs the seed to come from the XML fingerprint instead (a concretization change, needs approval).

Options for the cross-core repeats, cheapest first: (1) dedup cores first, which removes 38% of STT_6 core runs and raises the per-core cap from 2,326 to 3,750 at the same budget (mechanical). (2) Randomize the solver order with a per-core seed (below), so a capped run is a spread sample instead of the same lexicographic corner. (3) Adaptive top-up: after each merge, give the next round's budget to cores by their new-instance rate, stop a core at EXHAUSTED. (4) Ownership rule (`not seed_j` for every earlier distinct core `j` in core `i`'s run) makes the runs disjoint by construction and makes EXHAUSTED counts add up to an exact total, but negated seeds are expensive: the 129-negation query did not finish translating in 9.5 min, so this needs a per-core cost test before relying on it. (5) Re-partition Stage 1.5 by kind sequence instead of by core (disjoint by construction, loses per-core balance).

### Randomizing Kodkod in Stage 1.5: yes, with a seeded SAT4J

Alloy 6.2.0 (`alloy6.jar` manifest) takes any `SATFactory` in `A4Options.solver`; the default is `kodkod.solvers.SAT4JRef` → `SolverFactory.defaultSolver()`. The jar ships `org.sat4j.minisat.orders.RandomLiteralSelectionStrategy` (public static `RAND`, fixed seed 123456789) and `RandomWalkDecorator` (private `rand`, same fixed seed), both read with `javap`. `dedup_audit/a6RandomModels.java` is `a6CountModels` with a custom factory: MiniLearningHeap + random phase + random-walk decisions (p = 0.05), both generators seeded from the command line. Same translation, same formula, same `sol.next()` blocking, so every instance is a model instance and a run that ends below its cap is still exhaustive; only the order changes.

Probe on one seeded STT_6 core (`cores_STT_6_core_ri/inst-000005`, 600 instances each): default 6.7 s, seeds 1 and 2 7.4 s and 7.2 s. Distinct kind sequences in the first 100 / all 600: default 24 / 92, seed 1 67 / 213, seed 2 68 / 235. Overlap of the 600: default ∩ seed 1 = 25, default ∩ seed 2 = 19, seed 1 ∩ seed 2 = 149; union of the three = 1,619. A rerun of seed 1 gives the identical sequence, so a run is reproducible from (model sha, seed, p). On the flat model it is slower (4,000 in ~2.1–2.7 min) and, unlike the default order, reaches the ALU-on-path class without a forcing predicate. It is not uniform sampling (two seeds still share 25%). Other routes that do not touch the solver: forcing-predicate partitions and `a6DiverseModels.java` (blocks whole skeletons); both are complementary.

### Expansion: how much room Stage 1.5 has, and what it may add

Stage 1 is `but 6`, Stage 1.5 is `exactly 6`, so a core of size k gets exactly 6 − k added instructions, never fewer and never more. Measured core sizes: STT_6 (129), STT_6_stl (306), Recon_6_stl (858) are all size 3 (k4, k5, k6 partitions exhausted at 0), so every STT/Recon program is core + 3. SPT v2 has cores up to k5 (cafe2 `out/SPT_6_oneLP_v2_core_ri/k5_*`: 83 + 83 + 45), which get only 1 added instruction; a k6 core would get 0 (none exists today). What the added 3 may be under the production minimality and the current pin (stage15-bound, re-read in `STT_6.als:301-313`): anything with an operand that shares the core's states (RS), bare `br_n` padding (`no_extra_inst` exempts Branchn), no extra unresolved instruction unless it is necessary (RR), and nothing on a core edge (the finding above). To get bigger shapes: Stage 1.5b at N = core size + Δ or a fixed N = 8/10 (decisions S15-1..6 in `STAGE1_alloy/models/proposed_twophase/stage15_bound/SECTION_for_TWO_PHASE_MODELS.md`, which is still waiting to be pasted into this doc).

### Fold depth and the other bound-tied text when N grows (tracked)

Everything that must grow with N: the protection-set fold (7 deep in every production and `_u` model, so N ≤ 7 is safe and N ≥ 8 silently skips later positions and invents leaks, stage15-bound S1), the IX atoms (S2), the Int bitwidth once more than 9 operands are in scope (S3) and the operand scope (S4). New read-only lint `dedup_audit/check_bound_consistency.py M.als …` checks fold depth ≥ N, IX count vs N, and Int when `#` is used with more than 9 operands; exit 1 on failure. Today: all of `STT_6`, `SPT_6_oneLP`, `Recon_6`, `STT_6_stl`, `STT_6_u`, `Recon_6_u`, `SPT_6_u`, `STT_6_skel_demo`, `STT_6_core_ri` pass at 6; a scratch `STT_6` with only the scope changed to `exactly 8` fails (fold 7 vs 8, IX 6 vs 8). Gaps: no launcher calls a check like this (`launch_stage15.py` also hard-codes "exactly 6" in its status text); `derive_core_u.py resize` regenerates fold + IX + operand scope but does not add `6 Int`, and it only works on models with the `//@@N-BEGIN` markers, which `STT_6_u.als`, `Recon_6_u.als` and `SPT_6_u.als` do not have (only `SKELETON_u.als` / `STT_6_skel_demo.als` do); `make_s15_model.py` covers the production-style text.

### Decisions for Anna (also in `URGENT_TODO.md`)

- [ ] DECIDE DA-1 (pin, same as S15-2 with new evidence): (a) keep the exact-edge pin and leave ALU-on-path to the Stage-2 splice (not model-checked); (b) path pin, re-run Stage 1.5 (covers 12,000/12,000 random flat instances; changes `stage_seed.py` output, not any model); (c) keep the pin and add a forced ALU-on-path partition. Recommendation: (b).
- [ ] DECIDE DA-2 (cross-core repeats, extends the "Stage-1.5 budget after dedup" item): core dedup + randomized seeds + adaptive top-up (recommended), or the ownership rule after a cost test, or just 3x the budget (keeps the first-core bias: 125/129 runs are capped).
- [ ] DECIDE DA-3 (randomized enumeration): adopt `a6RandomModels` for Stage 1.5 with seed = hash(core, round) recorded in PROVENANCE, keep the default order, or run both and merge. Recommendation: both for the final batch (default keeps continuity with the 93k corpus).
- [ ] DECIDE DA-4 (bound, same as S15-1): fixed 6, N = core size + Δ, or a 1.5b at 8/10. Recommendation unchanged from stage15-bound (1.5b at 8, STT/Recon up to 10), with the lint as a launcher precondition.
- [ ] DECIDE DA-5 (one corpus across families): keep one testset per family, or a fingerprint-keyed corpus with family tags so Stage 2 and gem5 run each program once per build. Recommendation: the shared corpus; it needs Stage-2 seeds keyed by fingerprint.

## 2026-11-09 — Single-stage (flat) runs of the unchanged models, and size-8 drafts (singlestage session + 6 agents)

**Outcome.** Every production and ultimate model was run single-stage, unchanged, at its own `exactly 6` scope, and all of them produce instances at a usable rate. The two-stage corpus is a strict subset of what the unchanged model produces in every family: the exact Stage-1.5 pin drops every program where an ALU feeds the transmitter, `STT_6_stl` has a second missed class that the path pin does not recover, SPT has programs with no Stage-1 core at all, the two-stage `SPT_6_u` run never finished (72 of 58,758 cores pinned), and two-stage cannot run on `STT_6_rmw_u` at all (`stage_seed.py:50` has no `TRmw`, KeyError on any RMW core). Anna's direction (2026-11-09): no new models; skip Stage 1 and 1.5 where they do not work. The choice is DECIDE DA-6 in `URGENT_TODO.md`.

**Setup.** cafe2 `/tests/singlestage_20261109/` (`tools/run_flat.py`, `tools/census_flat.py`; outputs `out/<FAMILY>/<model>/<seed>/inst-*.{xml,txt}`, `runs.jsonl`, `census.json`; logs in `logs/`). Seeds: SAT4J default order plus random seeds 1, 2, 3 (`a6RandomModels`, p = 0.05). Cap 10,000 per seed, timeout 1,500 s (`SPT_6_u` 7,200 s), node load 40 to 64 throughout so speeds are lower bounds. Ultimate models and all size-8 files are UNAPPROVED drafts. Per-family detail is in `STAGE1_alloy/models/proposed/singlestage/<FAMILY>/RESULTS.json` (the SPTU file is partial; its final numbers are in `claudelog.md` 2026-11-09 20:45). Core containment uses the Stage-1 cores from `/tests/simspect_alloy_20261108` and `/tests/simspect_alloy_20261109u`. Only the STT_6_u, Recon_6_u, STT_6_u_stl, Recon_6_u_stl and SPT_6_u numbers were read from the census files by the main session; the rest are agent reports.

| Unchanged model, size 6 | Instances, 4 seeds | Distinct | ALU feeds transmitter | No Stage-1 core, exact pin | No Stage-1 core, path pin | Default order to 10,000 |
|---|---|---|---|---|---|---|
| `STT_6` | 35,857 | 21,141 | 415 | 415 | 0 | 659 s |
| `Recon_6` | 23,132 | 16,775 | 392 | 392 | 0 | 812 s |
| `STT_6_stl` | 40,000 | 25,842 | 754 | 1,086 | 337 | 489 s |
| `Recon_6_stl` | 25,328 | 17,879 | 311 | 311 | 0 | 824 s |
| `STT_6_u` | 40,000 | 21,982 | 257 | 257 | 0 | 433 s |
| `Recon_6_u` | 36,512 | 21,584 | 292 | 292 | 0 | 753 s |
| `STT_6_u_stl` | 40,000 | 23,455 | 296 | 296 | 0 | 468 s |
| `Recon_6_u_stl` | 40,000 | 24,013 | 380 | 380 | 0 | 753 s |
| `SPT_6_oneLP_v2` | 24,388 | 16,313 | 5,167 | 37 of a 300 sample | 36 of a 300 sample | 1,186 s |
| `SPT_6_oneLP_v3` | 20,573 | 14,677 | 5,053 | not run | not run | 1,358 s |
| `SPT_6_u` | 40,000 | 30,125 | 25,649 | not run | not run | 2,802 s |
| `STT_6_rmw_u` | 40,000 | 21,258 | 143 | not run, Stage 1.5 cannot seed RMW cores | not run | 417 s |

**What the table shows.** (1) For the STT and Recon families the programs with no core under the exact pin are exactly the ALU-feeds-transmitter programs (cross-tabbed for `STT_6`, `Recon_6`, `STT_6_u_stl`; equal counts elsewhere), about 1.2 to 2.3 percent of sampled distinct programs. (2) `STT_6_stl` has 337 programs with no core even under the path pin: one load takes the rf alias edge from the store and a different load of the same memory atom feeds the transmitter; all Stage-1 STL cores have 3 instructions. The cause is only partly characterized (2,186 covered programs share the property). (3) SPT is where the pin matters most: an ALU feeds the transmitter in 32 percent of distinct `SPT_6_oneLP_v2` programs and 85 percent of `SPT_6_u` programs. The v2 Stage-1 core set has 200,757 cores with k4 stopped at its 200,000 cap, and 36 of 300 sampled flat programs contain no core. (4) Every run ended CAPPED or TIMEOUT, so no full flat corpus size is known. Random seeds are 2 to 3 times slower than default order and share roughly 40 to 55 percent of their programs with each other at this cap; for `SPT_6_u` the default order shares under 600 of 10,000 with any random seed.

**Two-stage on the ultimate drafts, for comparison** (`/tests/simspect_alloy_20261109u/logs/{launcher,stage15_launcher}.log`). `STT_6_u` and `Recon_6_u`: 296,230 Stage-1.5 instances each, 125 of 129 cores CAPPED. `STT_6_u_stl` and `Recon_6_u_stl`: 266,600 each, 716 of 858 CAPPED. `SPT_6_u`: Stage 1 gave 58,758 cores with 11 partitions ended DISK_GUARD; Stage 1.5 pinned 72 cores at about 658 s for 6 instances each, then the launcher ended.

**Size-8 drafts (parked).** Variants per base: `_flat_n8_prod` (production minimality), `_flat_n8_prod_nospacer` (every instruction has an operand), `_flat_n8_leakrs_nospacer` (leak plus RS-minimality only), generated by the unchanged `make_s15_model.py --pin none --n 8 --operands 16 --intbits 6`; defense blocks byte-identical to the base in every draft. Distinct programs in 4 seeds at 1,500 s (prod / nospacer / leak_rs): `STT_6` 9,028 / 8,010 / 12,902; `Recon_6` 3,565 / 2,198 / 5,018; `STT_6_stl` 16,577 / 12,587 / 21,590; `Recon_6_stl` 6,169 / 5,705 / 6,895; `STT_6_u` 20,141 / 17,985 / 22,513; `Recon_6_u` 11,596 / 11,991 / 16,494; `STT_6_u_stl` 21,770 / 15,756 / 22,875; `Recon_6_u_stl` 11,932 / 11,607 / 15,368; `SPT_6_oneLP_v2` 860 / 493 / 1,528; `SPT_6_oneLP_v3` 422 (prod only); `SPT_6_u` not run (translation alone took over 10 minutes); `STT_6` at size 10 gave 523 in 25 minutes. Findings: about 4.5 to 5 of the 8 instructions are off the transmitter's rf/ddi cone, and `nospacer` only swaps empty instructions for disconnected ones that touch state; the default SAT4J order found 0 ALU-feeds-transmitter programs at size 8 or 10, only random seeds did; seeds barely overlap at size 8, so counts measure solver speed, not coverage; the loose variant admits 2 to 6 unresolved branches (or extra unresolved stores in STL); SPT at size 8 runs at about 9 instances per JVM-minute.

**Questions that only matter if size 8 is revived** (not DECIDE lines, per Anna's "no new models"): fold depth exactly N or N + 1; what the loose minimality should mean (core-relative minimality, S15-4, is the agents' recommendation); operand scope 16 or 24; whether the ultimate SPT `spt_public_p` fixpoint (6 nested `spt_step_p`, inside the defense block) must be 8 deep at size 8; forced shape partitions plus random seeds for enumeration. `check_bound_consistency.py` now prints `WARN fixpt` for a fixed-depth nesting shallower than N.

**Open decisions.** `URGENT_TODO.md` DA-6 (single-stage for the ultimate families, unchanged models; recommended), DA-7 (the 36 SPT programs with no core), DA-8 (SPT base v2 or v3), DA-9 (the `STT_6_stl` separate-alias-load shape).

## 2026-11-09 — Loose skeleton pin (loosepin)

Anna's ask: "i dont want the uv5 shape i want the ultimate models fixed with this looser pinning so it comes naturally ... basically we need to pin the skeletons loosely and then it will work better", plus "build the seeded random order" and "why cant i transition from stage 1 to stage 2 with a shape contains". This section has the design, new draft models for every ultimate family, single-stage measurements on cafe1, and the seeded random order wired into the real XML phase. **All `_lp*.als` files are UNAPPROVED drafts.** No existing `.als`, `parsexml.py` or gem5 file was edited, and no gem5 campaign was run. Tools and results: `STAGE1_alloy/models/proposed/ultimate/loosepin/` (results in `results/`). Run directory: cafe1 `/tests/simspect_alloy_20261108/loosepin/` (`out/<model>/<seed>/`, `logs/`, `census/`, `stage2/`).

### Design (one Alloy run per family, no Stage-1 → 1.5 handoff)

- **Bound:** `for 9 but 8 Instruction, 16 Operand, 6 Int` [lp-3]. The protection-set fold is regenerated 8 deep [lp-2]. `check_bound_consistency.py` passes for every draft. For SPT it warns `fixpt`: `spt_public_p` nests `spt_step_p` 6 deep against N = 8, inside the defense block, so it was left alone.
- **Variable-length symmetry breaking [lp-1]:** IX0..IX7 as a prefix. `idx_surjective` (every IX used, so exactly N instructions) becomes `idx_prefix`: the first instruction gets IX0 and each spo successor gets the next atom. A k-instruction instance therefore uses IX0..IX(k-1). Measured within-seed duplicates (census fingerprint, which minimizes over same-slot operand orders): random seeds 0 to 0.3%; the default order 4 to 8%.
- **Loose pin `lp_skeleton` [lp-4], path-style, no exact core edges:** (1) `some committed` (a committed region); (2) an unresolved gate (branch, or store for the stl flavor) before the transmitter; (3) an access (a load, or any instruction with an `inmem`) whose output is in the transmitter's backward rf/ddi cone, so ALUs and memory hops may sit on the path; (4) the transmitter, through the unchanged `one_xm`/`tag_xm`. For STT/ReCon, (2)-(4) follow from `tag_xm`, so the pin adds only the committed region. That is the point: a loose pin is the leak itself.
- **No junk [lp-5]:** `no_extra_inst` no longer lets an operand-free `br_n` pad the program, so an operand-free instruction must be an unresolved branch. `lp_connected` requires every instruction with operands to touch the transmitter's component through rf, ddi, the same instruction, or the same `Mem_s` word. A shared `Reg_s` with no rf edge does not count, because it is only a rename.
- **Minimality [lp-6]:** `_lpA` = **core-relative** (S15-4): the leak; RR as in production for non-branches (flag canonicalization); an unresolved branch must be RR-necessary or relevant (its predicate is fed by a load, S4's B1; or it is a predicated branch younger than the transmitter, A3c's B2); the production boundary clause; RS only over the States of the transmitter's backward dataflow cone, so instructions outside the cone are free. `_lpB` = the same without RS (junk control is `lp_connected` only). `STT_6_u_lpP` = the production `gen_useful_litmus` with the committed region optional (control).
- **Generator:** `make_loosepin.py` writes each draft plus `<draft>.als.diff` against its ultimate base. It refuses if the defense block (from the "Specific defense model" banner to EOF) is not byte-identical, or if any base line changes outside the IX / fold / scope / `no_extra_inst` / `gen_useful_litmus` / run text. Drafts: `STT_6_u`, `Recon_6_u`, `STT_6_rmw_u`, `STT_6_u_stl`, `Recon_6_u_stl`, `SPT_6_u`, each `_lpA` and `_lpB`, plus `STT_6_u_lpP`.

### Runs (cafe1, 2026-11-10 05:25-05:51 UTC; SPT rerun 06:27-07:27; `_b2` 06:28-06:53)

**One fix during the work (SPT only).** Round 1 had clause (3) as "an instruction with an `inmem`". For STT, ReCon, RMW and STL that is implied by `tag_xm`: the taint source is a speculative load's `inmem`, and its only edge is the ddi to the load's output. So the weaker clause in the current files leaves their instance sets unchanged. The round-1 file hashes are in `results/round1/MODELS_ROUND1_SHA256.txt`. For SPT the old clause was wrong: SPT taints every loaded value, so the leaking load needs no `inmem`, and under `_lpA` an `inmem` on the cone must be RS-necessary, which SPT never makes it. Round-1 `SPT_6_u_lpA` had an ALU on the leak path in 5.4% of 1,099 programs, against 77.2% for the exactly-6 flat `SPT_6_u` (round-1 JSON kept in `results/round1_superseded_spt/`). SPT was rerun with the fixed clause (06:27-07:27 UTC, alone on the node apart from the `_b2` runs).

`launch_lp.sh` ran `run_flat.py` (singlestage tools, unchanged) for 13 drafts × seeds default, 1, 2, 3 (`a6RandomModels`, p = 0.05). Each seed was capped at 10,000 with a 1,500 s timeout (SPT 3,600 s), and all 52 JVMs ran at once (load about 60 of 64 cores). **Every run ended TIMEOUT**, so these counts are throughput, not corpus size. Census: `census_lp.py` (new, read-only) on all instances, deduplicated with the census_flat isomorphism fingerprint. JSON: `results/round1/<model>.json`.

| draft | instances default / s1 / s2 / s3 | distinct | sum of pairwise seed overlaps | sizes 3-4 / 5-6 / 7-8 | unresolved branches 1 / 2 / 3+ |
|---|---|---|---|---|---|
| STT_6_u_lpA | 1,242 / 300 / 669 / 477 | 2,350 | 339 | 1,185 / 452 / 713 | 1,571 / 567 / 212 |
| STT_6_u_lpB | 3,863 / 377 / 764 / 613 | 5,070 | 380 | 1,552 / 519 / 2,999 | 1,948 / 1,734 / 1,388 |
| STT_6_u_lpP (production min.) | 915 / 765 / 480 / 871 | 2,415 | 768 | 1,312 / 508 / 595 | 2,415 / 0 / 0 |
| Recon_6_u_lpA | 832 / 165 / 144 / 262 | 1,281 | 98 | 913 / 179 / 189 | 1,079 / 190 / 12 |
| Recon_6_u_lpB | 1,177 / 512 / 649 / 585 | 2,575 | 386 | 1,625 / 488 / 462 | 1,905 / 640 / 30 |
| STT_6_rmw_u_lpA | 487 / 49 / 37 / 47 | 616 | 3 | 301 / 257 / 58 | 547 / 61 / 8 |
| STT_6_rmw_u_lpB | 584 / 62 / 75 / 66 | 775 | 12 | 332 / 337 / 106 | 681 / 88 / 6 |
| STT_6_u_stl_lpA | 2,994 / 1,184 / 1,142 / 1,428 | 5,398 | 2,138 | 1,510 / 2,589 / 1,299 | gate = store (0 branches) |
| STT_6_u_stl_lpB | 4,193 / 1,469 / 1,591 / 1,448 | 7,199 | 2,444 | 1,910 / 3,803 / 1,486 | gate = store |
| Recon_6_u_stl_lpA | 1,366 / 776 / 650 / 526 | 2,588 | 1,214 | 863 / 1,143 / 582 | gate = store |
| Recon_6_u_stl_lpB | 3,895 / 1,178 / 1,281 / 1,129 | 6,142 | 2,234 | 1,768 / 3,172 / 1,202 | gate = store |
| STT_6_u_lpA_b2 (`--brcap 2`, 06:28-06:53, 16 JVMs on the node) | – | 5,227 | 676 | 1,818 / 866 / 2,543 | 2,727 / 2,500 / 0 |
| Recon_6_u_lpA_b2 (same) | – | 1,557 | 102 | 1,041 / 280 / 236 | 1,237 / 320 / 0 |
| SPT_6_u_lpA (rerun, fixed clause (3), 3,600 s) | 656 / 225 / 204 / 216 | 1,174 | 140 | 798 / 108 / 268 | 982 / 178 / 14 |
| SPT_6_u_lpB (rerun, 3,600 s) | 935 / 490 / 504 / 531 | 2,279 | 213 | 1,192 / 380 / 707 | 1,847 / 391 / 41 |

**Throughput is the cost.** Per seed this is 5 to 10 times slower than the singlestage `exactly 8` production drafts (about 5,000 per random seed in 1,500 s). The CNF is the same size (STT_6_u_lpA 317k variables against 280k for `STT_6_u_flat_n8_prod`), so the difference is search difficulty. A Mac probe (STT_6_u_lpA, seed 1, 5 min, 5 JVMs sharing the Mac) gave 16 instances for the draft as written, 73 with `lp_connected` removed, 41 with the committed-region pin removed, and 7 with `exactly 8`. The connectivity closure costs about 4.5× and the committed region about 2.5×. Seeds barely overlap (STT_6_u_lpA: 339 shared of 2,688), so the space is far from exhausted and more seeds × time buys new programs almost linearly.

### Shape census against the current corpora (distinct programs, percent)

Baselines: single-stage `exactly 6` unchanged ultimate models (cafe2 `/tests/singlestage_20261109/out`, 2,500 sampled per seed, union of 4 seeds); singlestage `exactly 8` production (`_flat_n8_prod`); the two-stage Stage-1.5 corpora (cafe2 `testsets_twostage/<family>/xml`, 5,000 sampled). JSON: `results/baseline/`.

| corpus | distinct | UV5 pre: committed load, rf-fed address | … reading the same `Mem_s` as a speculative load | any rf into a committed instr | committed LD→LD pair | pair + later re-load | OTB merge (ALU in cone reads ≥ 2 loads) | ALU on leak path | RMW transmitter |
|---|---|---|---|---|---|---|---|---|---|
| two-stage STT_6_u | 4,985 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | – |
| two-stage Recon_6_u | 4,975 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | – |
| two-stage STT_6_u_stl | 4,947 | 0 | 0 | 0.02 | 0 | 0 | 0 | 0 | – |
| single-stage exactly-6 STT_6_u | 8,201 | 1.41 | 0.11 | 12.3 | 0.34 | 0.04 | 0.01 | 0.90 | – |
| single-stage exactly-6 Recon_6_u | 8,314 | 1.80 | 0.14 | 11.4 | 0.73 | 0 | 0.04 | 1.05 | – |
| single-stage exactly-6 STT_6_rmw_u | 8,174 | 0.99 | 0 | 5.9 | 0.22 | 0 | 0 | 0.48 | 28.3 |
| single-stage exactly-6 STT_6_u_stl | 8,436 | 1.08 | 0.12 | 7.0 | 0.21 | 0 | 0 | 0.92 | – |
| single-stage exactly-8 prod STT_6_u | 8,735 | 0.21 | 0.07 | 1.5 | 0.15 | 0.08 | 0 | 0.84 | – |
| **STT_6_u_lpA** | 2,350 | **2.81** | **1.02** | 17.6 | **2.51** | **0.77** | **0.77** | 1.32 | – |
| STT_6_u_lpB | 5,070 | 1.78 | 0.85 | 26.1 | 1.66 | 0.61 | 0.22 | 0.55 | – |
| STT_6_u_lpP | 2,415 | 3.40 | 2.48 | 11.0 | 2.98 | 2.11 | 0.37 | 2.77 | – |
| **Recon_6_u_lpA** | 1,281 | 1.80 | 0.70 | 4.4 | 1.64 | 0.47 | 0.08 | 0.31 | – |
| Recon_6_u_lpB | 2,575 | 2.80 | 0.93 | 5.5 | 2.45 | 0.50 | 0.39 | 0.93 | – |
| STT_6_rmw_u_lpA | 616 | 1.14 | 0 | 2.8 | 0.97 | 0.16 | 0 | 0.16 | 45.6 |
| STT_6_rmw_u_lpB | 775 | 1.81 | 0 | 3.9 | 1.68 | 0 | 0.13 | 0.52 | 45.9 |
| STT_6_u_stl_lpA | 5,398 | 2.85 | 0.87 | 14.1 | 2.33 | 0.46 | 0.06 | 0.56 | – |
| Recon_6_u_stl_lpA | 2,588 | 1.89 | 0.39 | 5.1 | 1.78 | 0.04 | 0.08 | 0.43 | – |
| STT_6_u_lpA_b2 | 5,227 | 2.75 | 1.36 | 19.8 | 2.64 | 1.22 | 0.88 | 1.45 | – |
| Recon_6_u_lpA_b2 | 1,557 | 1.93 | 0.32 | 5.3 | 1.61 | 0.32 | 1.28 | 1.61 | – |
| single-stage exactly-6 SPT_6_u | 9,155 | 5.20 | 0 | 47.3 | 0.23 | 0 | 0.01 | 77.2 | – |
| SPT_6_u_lpA (rerun) | 1,174 | 6.81 | 1.36 | 16.3 | 3.75 | 0.68 | 0.34 | **4.51** | – |
| SPT_6_u_lpB (rerun) | 2,279 | 8.47 | 2.11 | 20.1 | 4.08 | 0.75 | 0.44 | **8.86** | – |

**SPT open point.** With clause (3) fixed, SPT_6_u_lpA/lpB still have an ALU on the leak path in only 4.5 / 8.9% of programs, against 77.2% in the exactly-6 flat SPT_6_u. Clause (3) was therefore not the main cause. The candidates are the committed-region pin, `lp_connected` and the no-padding rule; this was not diagnosed (LP-4). Every other SPT shape rate is at or above the flat run's.

**UV5 precondition at the assembly level** (`STAGE3_gem5/triage/uv5_shape/uv5_timing_scan.py`, unchanged; not_taken mode). Input: 600 XMLs per draft (random seeds first), concretized with the unchanged Stage 2 of `code_20261109` (`lp_stage2.sh`: `pipeline.py llvm` + `asm`). Every draft compiled 600/600, RMW included, so variable-length instances need nothing new in Stage 2. A2 = a committed load whose address needs a producer; C = a committed load on the same line as a squashed load; D = C with the committed load's address ready later than the squashed load's (the UV5 shape). Results (A2 / C / D of 600): STT_6_u_lpA 29 / 161 / **1**; STT_6_u_lpB 33 / 189 / **4**; STT_6_u_lpP 26 / 78 / **8**; Recon_6_u_lpA 28 / 162 / **7**; Recon_6_u_lpB 30 / 179 / **4**; STT_6_rmw_u_lpA 7 / 141 / **2**. Reference values (uv5-shape, claudelog 2026-11-09 19:33): old flat STT_6 A2 1.7% and D 1.6% of 20,000; the fanout corpus STT_6_fv2fp_rmw D **0** of 93,041. **Reading:** the loose pin brings the precondition back in every family: A2 is 4.3 to 5.5% (RMW 1.2%) against 1.7% in the old flat corpus. Committed LD→LD pairs appear 2 to 8 times as often as in the exactly-6 flat runs, and pair + re-load and the OTB merge, which are near 0 there (0 in two-stage), reach 0.1 to 0.8%. The UV5 *timing* (D) stays rare, 0.2 to 1.3% of tests (old flat 1.6%), because in most of these programs the committed load and the squashed load share one address chain, so their addresses are ready at the same time (in STT_6_u_lpA, 117 of the 161 tests with a same-line pair). With 600 tests per draft this is a coarse rate (1 to 8 tests). No forcing predicate was added (Anna: no bug-specific shapes).

**Unresolved branches.** Production minimality allows exactly 1 (lpP: 2,415 / 0 / 0). Core-relative `_lpA` admits relevant extras: STT_6_u 33% have 2 or more (3+: 9%), Recon_6_u 16%, rmw 11%. Without RS (`_lpB`), STT_6_u reaches 3+ in 27%. Proposal: cap at 2 (`make_loosepin.py --brcap 2`, which adds `fact lp_brcap`), keeping the S4 (B0 + B1) and A3c (B1 + B2) two-branch shapes while removing the 3-4-branch pile-up. Measured as `_lpA_b2` (STT_6_u, Recon_6_u): the shape rates stay the same or rise (table below), but 48% of STT_6_u programs then carry 2 unresolved branches. The relevance test accepts any load-fed predicate, committed loads included, so it is loose; tightening it to an *uncommitted* load is an option under LP-1. The `_b2` runs had 16 JVMs on the node against 52 in round 1, so their larger counts (5,227 against 2,350) are mostly node load, not the cap.

### Answer: why can't Stage 1 go straight to Stage 2 with a shape-contains pin?

Stage 1.5 already is "the production model plus a contains-the-core pin". `stage_pipeline.py` splices `stage_seed.build_pred` into the unchanged production model at `exactly 6`, runs it with the default SAT4J order, and caps each core's run (2,326 per core for STT_6; 125 of 129 cores CAPPED). Three things in that recipe lose shapes, and none is the idea of a contains pin itself.

1. **The pin is exact, not loose.** Each core rf edge becomes `ob in oa.rf`, a direct edge, and `one_entering_rf` forbids a second producer. So no ALU or memory hop can ever sit between the core's access and its transmitter, and the OTB merge input cannot attach (two-stage: 0 ALU on the leak path; flat: 0.9 to 1.0%, SPT 32 to 85%).
2. **The bound is exactly 6.** A 3-instruction core gets exactly 3 more instructions, no fewer and no more, and the slack goes into operand-free `br_n` padding (`no_extra_inst` exempts them). So bigger shapes (committed context + gate + access chain + merge) do not fit, and short programs are padded to 6.
3. **Default order + per-core cap + first-core-wins merge.** Each core sees only the lexicographically first ~2,326 completions, and the corner the default order explores has no committed context: in two-stage, 88% of programs have 0 committed instructions and 0 have any rf edge into a committed instruction, against 12% with such an edge in the same model run flat. This is what removed the UV5 precondition (uv5-shape), not minimality.

**Does a loose contains pin over a single-stage `but N` run replace Stage 1.5? Yes.** With the path-style pin (`ob in oa.rf.*(ddi.rf)`, DA-1(b)), every flat exactly-6 STT/ReCon program already contains a Stage-1 core (12,000 of 12,000, dedup-audit; 0 uncovered in the singlestage census). The loose contains-core pin is therefore implied by the leak predicate: "Stage 1 + loose pin" equals the flat model, cut into overlapping per-core slices. The only thing Stage 1 still adds is a partition key for balancing the budget, and random seeds spread the search without one. It is also not a complete partition everywhere: `STT_6_stl` has 337 flat programs with no core even under the path pin, and SPT v2 36 of 300. So the drafts here drop the Stage-1 core altogether. Their pin is the generic skeleton above (committed region + gate + path-reachable access + transmitter), with variable length (`but 8` + IX prefix), no padding, core-relative minimality, and seeded random order with fingerprint dedup across seeds. Stage 1 → Stage 2 in one step is then just `pipeline.py xml` on the draft with `alloy.solver_order` set.

### Seeded random order in the real pipeline (wired, tested)

- `pipeline.phase_xml` (and therefore `testsetgen.py`) calls `alloy_solver_order.run_random_xml` only when the config has `alloy.solver_order.mode = "random"`. With the key absent, or `"mode": "default"`, the old `a6CountModels` command runs exactly as before (unit test checks the argv).
- Config: `{"mode": "random", "seeds": [1, 2, 3], "walk_p": 0.05, "parallel": false, "timeout_s": 0, "xmx": null, "keep_raw": false}`. A seed may be the string `"default"`. `max_instances` is the cap per seed.
- Each seed enumerates into `xml/_seeds/<seed>/`. Each instance is fingerprinted as it lands, using merge_stage15's rule (`find_duplicates.canonicalize` + xm flags), and copied atomically to `xml/inst-NNNNNN.xml` only if it is new. Sequential mode therefore still streams into Stage 2; `parallel: true` merges in seed order at the end. Numbering is deterministic in (model, seeds, p, cap).
- Provenance: `xml/SOLVER_ORDER.json` (model sha256, jar sha256, `a6RandomModels.java` sha256, config, per-seed instances / kept_new / duplicates / verdict / secs / cmd), `xml/_dedup_map.jsonl`, `xml/_dedup_dups.jsonl`, `xml/_solver_order.log`. testsetgen's manifest adds `alloy_solver_order` and `model_sha256`, only when the key is set.
- Files: `alloy_solver_order.py`, `STAGE1_alloy/a6RandomModels.java` (copy of the dedup-audit probe, compiled on demand), the hooks in `pipeline.py:121-136` and `testsetgen.py`, tests in `STAGE1_alloy/tests/test_solver_order.py` (10 tests, all pass on the Mac: config validation, default argv unchanged, cross-seed dedup and numbering with a fake JVM, parallel equals sequential, the real fingerprint, and a real-Java seed reproducibility check).
- End-to-end: `pipeline.py xml` on `STT_6_u_lpA` (seeds 1, 2, cap 12) kept 24, with streaming verified. Example config: `runconfigs/loosepin/run_config_STT_6_u_lpA.jsonc` (UNAPPROVED model). Commands: `wiki/state/COMMANDS.md`.

### Limits

All runs were TIMEOUT at 25 min, so the absolute counts measure solver speed, and the Mac perf probe ran with 5 JVMs sharing the Mac. Shape rates on samples of 600 to 7,000 distinct programs have wide intervals for the rare classes (UV5 D: 1 to 8 tests). The census "same `Mem_s`" is an XML-level proxy for "same line". The `_lpA` RS-on-cone rule blocks a merge whose second input is a tainted state; it allows the OTB form where one input is untainted (0.77% in STT_6_u_lpA). Core-relative minimality is new model text, so whether it is the minimality Anna wants is LP-1.

### Decisions for Anna (also in `URGENT_TODO.md`)

- [ ] DECIDE LP-1 (minimality for the loose single-stage model): (a) `_lpA` core-relative (RS on the transmitter cone, relevant extra branches allowed); (b) `_lpB` no RS (2× throughput, more junk-like fan-in and branch pile-up); (c) production minimality at `but 8` with the loose pin (`_lpP`: the highest UV5/pair rates in this sample, exactly 1 unresolved branch, so no S4/A3c shapes). Recommendation: (a) with `--brcap 2` (the measured `_lpA_b2` keeps the shape rates; tighten the relevance test to uncommitted-load-fed predicates if 48% two-branch programs is too many), and (c) as a second corpus if S4/A3c are not needed.
- [ ] DECIDE LP-2 (committed region in the pin): required (Anna's skeleton; about 2.5× slower; every program has committed context) or optional (exactly-6 flat: 22% of programs have none; two-stage 88%). Recommendation: required, because the committed-free programs are already covered by today's corpora.
- [ ] DECIDE LP-3 (no-junk rule): keep `lp_connected` (dataflow + same instruction + same `Mem_s`; about 4.5× slower), weaken it to one hop to the cone, or drop it and rely on minimality. Recommendation: keep it and buy throughput with more seeds.
- [ ] DECIDE LP-4 (bound per family): N = 8 for STT/ReCon/RMW/STL as measured. SPT: SPT_6_u at `but 8` runs (1,174 / 2,279 distinct in 4 × 60 min, about 2 to 4 times slower than STT), but its `spt_public_p` fixpoint is 6 deep against N = 8 (defense block, untouched), and ALU on the leak path falls from 77% to 4.5 to 9% (cause not found). Options: (a) N = 8 as drafted, plus a separate approval to deepen the fixpoint to 8 (a defense-block edit); (b) the loose pin at N = 6 for SPT; (c) keep SPT on the unchanged exactly-6 single-stage model (DA-6). Recommendation: (c) for now, and diagnose the ALU drop before (a).
- [ ] DECIDE LP-5 (seeded order in production): approve `alloy.solver_order` for the final batch (pipeline code only, default unchanged), with seeds 1..K and, for continuity, `"default"`. Recommendation: K = 16 parallel seeds per family at 10,000 cap / 2 h timeout on one cafe node, dedup across seeds.
- [ ] DECIDE LP-6 (replace Stage 1.5): adopt the loose-pin single-stage drafts as the ultimate-family generators in place of Stage 1 → 1.5 (extends DA-6, which proposed the unchanged exactly-6 models). Recommendation: yes, after LP-1..LP-3; keep the existing two-stage corpora as they are (they stay valid, only incomplete).

## 2026-11-10 — Loose-pin regeneration (regen-lp)

Agent regen-lp (of hooks-v2) built and ran the loose-pin regeneration Anna approved (LP-1, LP-2, LP-4), then followed her later decisions the same day: (1) the footprint block for the AMuLeT defenses moves to FP-6 (memory + unwritten registers); (2) TA-4: `_lpA_b2g` only if it can produce 2-branch programs, never `lp_relevant_br`; (3) "I STILL want the skeletons to come from the first round of alloy enumeration", so the pin is a Stage-1 core contained path-style, not the generic `lp_skeleton`; (4) footprint first and only, streamed end to end ("once the first stage starts generating skeletons the second stage starts concretizing and the runs start occurring"); (5) the loose pin, the ultimate skeleton and the skeleton enumeration go into the production path. Every `.als` below is a NEW file; no existing model, `parsexml.py` or gem5 file was edited.

### Footprint_6_u: the footprint block on the ultimate skeleton

`STAGE1_alloy/models/proposed/ultimate/Footprint_6_u.als`, built by `make_footprint_u.py`. Skeleton = `STT_6_u.als` minus its header, byte-identical (that is STT_6.als plus the four [u-1] lines: Operand-typed protection set, no `.(~opstate)` lift in `secure_*`/`tag_xm`). Defense block = `proposed/footprint_v2/InvisiSpec_6_v2.als`'s (the CleanupSpec/SpecLFB v2 files have the same code; the script checks this and that all three share STT_6.als's skeleton) with only the retype the skeleton requires (diff `proposed/ultimate/Footprint_6_u.defense.diff`):

- [fu-1] `fun hardware_protection_policy: State {Mem_s + (Reg_s - Instruction.outreg.opstate)}` → `fun hardware_protection_policy[p: PTag->univ]: Operand {(Mem_s + (Reg_s - Instruction.outreg.opstate)).(~opstate)}`. The old skeleton lifted the State set to operands inside `secure_*` and `tag_xm`; the ultimate skeleton has no lift, so the lift moves into the seed. The call site passes `[p]`, which the seed ignores.
- [fu-2] `prot_set_propagation_p[p, i, s: State] : State { s }` → `[p, i, o: Operand] : Operand { o }`: identity stays identity (never untainted).
- Contract (STT_6's branch shadow) and leakage (`Loads.inaddr`) byte-identical.

**Equivalence.** With identity propagation the old protection set lifted by `.(~opstate)` is exactly the new one and `secure_*`/`tag_xm` apply the same expression to it, so the models are equal by text. Alloy check anyway (`queries/footprint/build_q_fp_eq.py` puts the old-skeleton semantics into the new file as `*_old` functions; `run_q_fp_eq.sh`, results in `queries/footprint/runs.log`): at exactly 6, flag sets equal for no_p, RR, RC, RC+RR, RS, RI and RO, tag equal, `gen_useful_litmus` + tag equal: **0 counterexamples in every check**; `gen_sanity` SAT; the negative control (closure term dropped) finds a counterexample, so the checks are not vacuous. The first port (v1 block, memory only, before FP-6) passed the same checks at exactly 6 and at `but 8` on its loose-pin drafts; its files are in `loosepin/results/superseded_footprint_v1/`. Observation (DECIDE RL-3): the v2 seed reads the unperturbed `Instruction.outreg`, which the derive_core_u lint forbids; kept verbatim so the port equals the approved block.

### Loose-pin drafts, the TA-4 probe and OTB

- `make_loosepin.py` gained `--minimality coneg` (core-relative RS without the `lp_relevant_br` exemption) and `--pin core` (no generic skeleton; run = `gen_useful_litmus` + `lp_committed` + `seed_core`, the core appended per run). `_lpP` drafts are now built with the committed region required (Anna). The superseded committed-optional `STT_6_u_lpP` is kept in `loosepin/results/superseded_lpP_committed_optional/`. Every draft passes `check_bound_consistency.py` with the fold 8 deep for N = 8, and the generator still refuses any change outside the allowed skeleton text.
- **TA-4 probe:** `STT_6_u_lpA_b2g` + "exactly 2 unresolved branches" is UNSAT at `but 8` (1,071 s); the Recon_6_u probe timed out at 30 min with no instance. Production RR-minimality gives one unresolved branch per program in every sample (round-1 lpP 2,415 / 0 / 0; short b2g runs 1,222 and 968 programs, all 1-branch). So `_lpP` only.
- **OTB census** (new `census_lp.py` column `otb_complete`: an ALU whose output reaches the leak operand has two different inputs fed by an older load with no unresolved branch before it and a younger load behind one; distinct programs): round-1 STT_6_u_lpP 10 / 2,415 (0.41%), STT_6_u_lpA 19 / 2,350 (0.81%), Recon_6_u_lpA 2 / 1,281 (0.16%), STT_6_u_lpA_b2 46 / 5,227 (0.88%), Recon_6_u_lpA_b2 19 / 1,557 (1.22%); today's generic-skeleton lpP (committed required, 16 seeds, stopped early) STT 74 / 5,832 (1.27%), Recon 95 / 3,467 (2.74%); short `_lpA_b2g` (4 seeds × 20 min) STT 6 / 1,222 (0.49%), Recon 1 / 968 (0.10%). The older `otb_merge` column (ALU in the cone reading two loads directly) gives similar numbers. JSON: cafe1 `/tests/simspect_alloy_20261108/loosepin_regen/census_otb/`.

### Generic-skeleton runs (comparison only, stopped)

STT_6_u_lpP and Recon_6_u_lpP (generic `lp_skeleton`, committed required) ran on cafe1 from 09:18 UTC with 16 random seeds + default and were stopped at 09:47 for the footprint priority (raw per-seed instances kept in `loosepin_regen/runs/<draft>/xml/_seeds/`: 8,985 and 4,863 instances, 5,832 and 3,467 distinct by the census fingerprint). The `_lpA_b2` runs were stopped at 09:21 by the TA-4 hold (`runs_aborted/`). None of these feeds a corpus.

### Footprint corpus: Stage 1 → core-pinned Stage 1.5 → Stage 2 v3, streamed (cafe1, 2026-11-10 09:46–10:50 UTC)

- **Stage 1 (skeleton enumeration):** `Footprint_6_u_core_ri.als` (`derive_core.py --minimality ri` on Footprint_6_u; skeleton identical to `STT_6_u_core_ri.als`), 8 partitions (`partition_stage1.py`), `launch_stage1.py` with 8 jobs. Every partition EXHAUSTED: k1 0, **k2 11, k3 1,400**, k4 0, k5 0, k6 0 (k6_Loads took 1,928 s). 1,411 cores (STT_6_u has 129: protecting unwritten registers adds cores whose secret is an initial register, AMuLeT's UV6 shape). Dedup: 771 distinct at the exact level, **363 distinct at the level the pin sees** (DECIDE RL-4); 363 runs.
- **Stage 1.5 (`stage15lp.py`):** per distinct core, `Footprint_6_u_lpPc.als` (= production `Footprint_6_u_lpP.als`) + that core as `seed_core`, path-style. Jobs of 25 instances / 300 s through `alloy_solver_order.run_random_xml` (seeded `a6RandomModels`, walk p 0.05, per-job fingerprints); 40 parallel slots; core queue shuffled with seed 20261110 (`QUEUE_ORDER.json`; the run was resumed once at 10:01 to add the shuffle, the first 253 jobs having run in index order); first pass one random seed per core, then top-ups to the most novel core among those within min jobs + 2. Stopped at the coordinator's call (Anna: numbers ASAP) after 1,327 jobs: **25,116 distinct programs** (fingerprint = alloy_solver_order's rule). Verdicts: 1,321 CAPPED, 6 EXHAUSTED (all 6 at 0 programs: the core is unsatisfiable under the loose pin + committed region). Jobs per core: 4 for 310 cores, 3 for 14, 2 for 6, 1 for 33 (the 6 exhausted and 27 whose jobs were in flight at the stop). New distinct programs per core: min 0, p10 31, p25 63, median 76, p75 84, p90 89, max 97. Pin check: 120/120 sampled instances contain their own core; another sampled core in 115/1,320 pairs (`queries/footprint/pin_check/pin_contains.py`).
- **Stage 2 (recipe v3, streamed):** `stream_fp.py` every 2 min merged finished jobs into `testsets_twostage/Footprint_6_u_core_lpP_fv3_base/xml`, ran `stage2_sharded.py` with `stage2_fv3_stream.jsonc` (= `stage2_fv3.jsonc`, only `testset_dir` and the asm thread count changed; OTB off), and published batches through `make_rmw_corpus.py --select eligible --fraction 0.5 --seed 20261109 --complete` and `make_jmp_corpus.py --p 0.5 --seed 20261109` (placement uniform). Code hashes equal cafe1 `recipe_v3/code` (make_jmp 6be3573e…, make_rmw 213d9a02…, parsexml 6e5c5238…, stage2_fv3 1c24c5e8…), recorded in PROVENANCE.json. `relay_cafe3.sh` copied each batch to cafe3 (SHA256 verified, rows appended last). First tests on cafe3 at 10:06 UTC; READY on cafe1 10:48, on cafe3 10:50.
- **Corpus** `testsets_twostage/Footprint_6_u_core_lpP_fv3/` (cafe1 and cafe3): 25,116 programs, **50,232 (stem, mode) tests** (both modes for every stem, 0 Stage-2 failures), 28 batches; RMW 20,588 tests (`rmw_stems.tsv`), jmp rows 25,352 (`jmp_stems.tsv`); `MANIFEST.tsv` (stem, core, seed, merged/published time, batch), `PROVENANCE.json` (per-core distribution, CPU-s), `READY`.
- **Generation cost (TA-7):** Stage 1 3,900 JVM-s (single-threaded partitions); Stage 1.5 113,598 JVM-s (sum of job wall seconds, one JVM each); Stage 2 13,701 CPU-s; RMW 12,631 CPU-s; jmp 7,955 CPU-s (RUSAGE_CHILDREN). Total 151,785 s: about 3.0 CPU-s per (stem, mode) test, 2.3 of it Alloy (6.0 per program).
- **UV5 shape** (`uv5_timing_scan.py`, all stems, not_taken): committed load whose address needs a producer 6,264 (24.9%; old flat 1.7%, STT_6flat_fv2fp_rmw_jmp 2.1%); committed load on the same line as a squashed load 10,849 (43.2%); full UV5 timing shape 690 (2.75%; old flat 1.6%, oldfanout 1.8%). XML level: committed load in 80% of programs, with an rf-fed address in 20.6%.

### UV5 extension attempt (11:40–11:44 UTC, stopped)

Anna asked for more footprint tests for UV5 (the abstract number). `stage15lp.py --seed-start` (cafe1 seeds 101+, shuffle 20261111, 40 slots; cafe2 seeds 201+, shuffle 20261112, 60 slots; cap 40 per job) and the extended `stream_fp.py` (`--s15` several dirs, `--start-n 1000000`, `--seen-from` the corpus state so only new programs count, `--uv5-filter` = the unchanged `uv5_timing_scan.py` through `uv5_dstems.py`, which reads the scan's D list and records C stems via a temporary `Counter.__setitem__` hook; MANIFEST column `uv5_class` D / C / other; `COUNTS.json` with every generated program and test as the UV5 denominator) were started, with `relay_jobs.sh` moving cafe2 jobs to cafe1. The coordinator then stopped everything after about 4 min (Anna had 15 minutes left; new tests could not be generated and run in time). Kept: 127 finished jobs, 4,396 distinct programs, 3,685 of them new against the corpus (711 already in it); 123 had gone through Stage 2 into cafe1 `testsets_twostage/Footprint_6_u_core_lpP_fv3_ext_base`; no RMW/jmp and nothing published (no ext corpus). Recorded in the corpus PROVENANCE.json (`extension_20261110_stopped`, cafe1 and cafe3). The wrapper's C list matches the scan's own counter (b0003: C 496 = 22 D + 474 C-not-D). Note from firstdet-final: a UV5 hit came from a static class-C test (inst-007645), so a D-only selection would bias the rate; the extension was changed to publish every test with the class as an ordering column before it was stopped.

### STT_6_u and Recon_6_u corpora (cafe2, 2026-11-10 13:55–15:05 UTC; Anna away, coordinator's experiment)

Same production flow through `twostage_lp.py` (configs `runconfigs/twostage_lp/{STT_6_u,Recon_6_u}.jsonc`), with Stage 1 **reused**: cafe2's 2026-11-09 enumeration of exactly the installed core models (`/tests/simspect_alloy_20261109u/out/<F>_core_ri/`, sha256 checked by `twostage_lp.py`; every partition EXHAUSTED except k6_Branchxs, unfinished with 0 cores, DECIDE RL-6): 129 cores each, 80 distinct at both levels. Stage 1.5: 28 slots per family, 100 instances / 600 s per job (RL-7), shuffle seeds 20261113 / 20261114, stop at 25,000 distinct. **STT_6_u: 26,954 programs** (366 jobs, 0 cores exhausted, 36 min); **Recon_6_u: 26,506** (393 jobs, 0 exhausted, 69 min). Stage 2 v3 streamed as for Footprint; the streamers were restarted by hand with 32 publish threads and 3,000-stem batches after Stage 1.5 ended (RMW + jmp, not compilation, was the bottleneck). Corpora: cafe2 `testsets_twostage/{STT_6_u,Recon_6_u}_core_lpP_fv3/`; STT relayed to cafe3 for the E2/E3/E4 campaigns.

**Census** (`census_lp.py`, distinct programs by the census fingerprint, percent):

| corpus | distinct | sizes 3-5 / 6-7 / 8 | unresolved brs = 1 | UV5 pre (committed load, rf-fed address) | … same `Mem_s` as a speculative load | any rf into a committed instr | committed LD→LD pair | pair + re-load | OTB merge | OTB-complete | ALU on leak path | ALU feeds xmit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Footprint_6_u_core_lpP_fv3 | 24,314 | 8,740 / 5,153 / 10,421 | 100% | 21.23 | 12.08 | 54.65 | 15.56 | 8.04 | 2.01 | 0.61 | 35.87 | 50.35 |
| STT_6_u_core_lpP_fv3 | 26,404 | 5,089 / 6,488 / 14,827 | 100% | 14.42 | 8.07 | 39.37 | 11.21 | 5.47 | 0.58 | 0.60 | 3.96 | 3.83 |
| Recon_6_u_core_lpP_fv3 | 25,925 | 6,318 / 7,216 / 12,391 | 100% | 10.54 | 3.94 | 32.40 | 7.70 | 0.87 | 1.09 | 1.10 | 6.03 | 5.94 |
| (round-1 generic STT_6_u_lpA, for scale) | 2,350 | – | 67% | 2.81 | 1.02 | 17.6 | 2.51 | 0.77 | 0.77 | 0.81 | 1.32 | – |

Core-pinned lpP multiplies the committed-context shapes 4-6× over the generic loose pin (UV5 precondition 14% vs 3% for STT), keeps exactly one unresolved branch (production minimality), and transmitters split loads / branches about 62 / 38 for STT and Recon (Footprint: loads only). Footprint's 36% ALU-on-path comes from unwritten-register secrets (FP-6). JSON: cafe2 `loosepin_regen/census/`, cafe3 `loosepin_regen/census/`.

### Production path (Anna: "make sure the loose pin and the ultimate are in the production path. and the skeleton enumeration")

New files `STAGE1_alloy/models/Footprint_6_u_core_ri.als` and `STAGE1_alloy/models/Footprint_6_u_lpP.als`, each the source draft byte-identical below a 3-line header ("production since 2026-11-10 per Anna; source draft <path>, sha256 …"). One command: `python3 twostage_lp.py --config runconfigs/twostage_lp/<F>.jsonc --ws <dir>` (`make twostage-lp CONFIG=… WS=…`) runs Stage 1 → Stage 1.5 → Stage 2 v3 streamed, with the same tools and logs as above (smoke-tested end to end on cafe1 with tiny budgets: 66 programs, READY). `pipeline.py` and `testsetgen.py` are unchanged, so every old config behaves byte-identically. `specs/alloy_models.json` has both models (tier production). STT_6_u / Recon_6_u configs exist (`runconfigs/twostage_lp/`), but their core and loose-pin models are not installed or run (Anna: footprint only for now).

### Decisions for Anna (also in `URGENT_TODO.md`)

- [ ] DECIDE RL-1: sign off the Footprint_6_u port (FP-6 block, one retype; equivalence holds). Recommendation: approve.
- [ ] DECIDE RL-3: the FP-6 seed reads the unperturbed `Instruction.outreg` (affects only RI/RO checks, i.e. Stage-1 core minimality). Recommendation: switch to `Reg_s - (i_p[p].outreg & o_p[p]).opstate` in a separate approved edit; the Stage-1.5 corpus is unaffected.
- [ ] DECIDE RL-4: dedup cores at the pin level (363) rather than the exact level (771). Recommendation: pin level, as done.

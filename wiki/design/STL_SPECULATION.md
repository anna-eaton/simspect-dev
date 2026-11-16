# Store-to-load (STL) speculation: model, concretization, gem5 hooks, window check

*Living doc, overwrite-in-place. Written 2026-10-28, updated 2026-10-30 (hooks built + tested), 2026-11-08 (STL for every main model; manifest handoff) and 2026-11-09 (port to the three AMuLeT builds). This is the one place for everything known about STL in SimSpect. Paper table row: [`SPEC_PRIMITIVE_INSTANCES.md`](SPEC_PRIMITIVE_INSTANCES.md) (h, i).*

## Manifest handoff (2026-11-08): the active STL builds, models and experiments

**Consolidated 2026-11-08 into [`../state/EVAL_MANIFEST.md`](../state/EVAL_MANIFEST.md)** (eval rows, two-stage families incl. the STL cores, STL per defense). This section stays as the STL detail and evidence; when STL status changes, update the manifest and `specs/defense_units.json` too.

For the agent writing the manifest of active builds, models and experiments. Everything below is current as of 2026-11-08 14:40 PST; sections further down hold the evidence. "Draft" = unapproved, in `STAGE1_alloy/models/proposed/` or `proposed_twophase/`, which the pipeline does not read.

**What STL is here.** Store-to-load speculation: an older store's address is held unresolved, the memory-dependence predictor is forced to say "no alias", a younger load to the same address reads the stale value, and the store's address resolution squashes it (memory-order violation). The window is load issue → that squash. Spectre v4. The other direction (predict alias, addresses differ) opens no window in gem5 and is only a negative control.

### Builds

| Build | STL hooks? | Status | Notes |
|---|---|---|---|
| `/work/gem5-recon-modded-stl` (cafe3 tree; binary + configs also on cafe1) | **yes** | **active, current (2026-11-16)** | Copy of today's `gem5-recon-modded` (the E2w binary, with the resolve hooks) + `apply_stl_hooks.py` unchanged. md5 `06240ccea173d11b3b2be61adcdbe387`. Without STL flags its records equal recon-modded's. Section "gem5-recon-modded-stl (2026-11-16)". Registry id `gem5-recon-modded-stl`. |
| `/work/gem5-recon-stl` (cafe2) | yes | superseded by `gem5-recon-modded-stl`; **stale** | Copy of `gem5-recon-modded` taken before the 2026-10-30 resolve hooks: no BR lines, old-style branch force, no CPU-wake fix (`wiki/findings/audits/2026-11-07/HOOK_AUDIT.md`, verdict BORDERLINE). `gem5.opt` md5 `9ac3ac66…`. Flags `--stl-ann-file`, `--stl-store-stall-cycles N`, `--stl-alias-pred {no_alias,alias,off}`. Schemes as recon-modded: 0 Unsafe, 1 Delay/NDA-like, 2 STT, 3 DoM. Registry: `specs/gem5_builds.json` id `gem5-recon-stl`. |
| `/work/amulet/hooks_stl_work/{InvisiSpec,CleanupSpec,SpecLFB}` (cafe2, copies of the three AMuLeT hooks-v2 trees, built 2026-11-09) | **yes** | built and verified; no run config points at them yet | Same flags and `STL:` lines as recon-stl; with no STL flag the trace is byte-identical to the in-place binary. md5 InvisiSpec `376198d5…`, CleanupSpec `c7989d25…`, SpecLFB `f2e3e9fe…`. Registry ids `amulet-<Build>-stl`. Section "Port to the AMuLeT builds (2026-11-09)". The in-place amulet trees are unchanged and have no STL hooks. |
| every other build (`/work/stt`, `gem5-recon-modded`, `gem5-spt`, the in-place amulet trees, amulet-STT) | no | port needed to run STL | Port = `gem5-hooks/stl/apply_stl_hooks.py <gem5_root>` (anchor-based, idempotent, refuses unless every anchor matches once) + rebuild. `stl_hooks_vs_gem5_v22.0.0.2.diff` is an older upstream reference, before the 2026-10-30 barrier/alias fixes. Rebuilds need Anna's OK (DECIDE). |

### Which defenses have STL in their threat model

| Unit (`specs/defense_units.json`) | STL in scope? | STL model | Runnable today? |
|---|---|---|---|
| 1 STT-Spectre, `/work/stt` | **no**: STT-Spectre casts no store shadow (`rob_impl.hh:444-495`); a bypass leak there is expected by design | (`STT_6_stl` only as a labelled control) | no hooks |
| 2 Recon-STT, recon scheme 2 | yes (`decode.cc:686-695` inserts stores into the shadow tracker) | `STT_6_stl` | **yes**, on `gem5-recon-stl` |
| 3 SPT-Fence (Spectre configs), `gem5-spt` | no (branch-only visibility point) | — | no hooks |
| 4 SpecLFB, amulet | yes (memory-order MUSLs, SpecLFB Sec. 5) | `STT_6_stl` as stimulus | on the STL copy (2026-11-09, Port section) |
| 5 ReCon, recon-modded | yes (same shadow tracker) | `Recon_6_stl` (draft) | partly: `gem5-recon-stl` has the hooks; ReCon mode there not verified |
| 6 InvisiSpec, amulet | Futuristic mode only (InvisiSpec Sec. IV Table I) | `STT_6_stl` as stimulus | on the STL copy (2026-11-09, Port section) |
| 7 CleanupSpec, amulet | yes (every transient instruction unsafe, Sec. 2.1) | `STT_6_stl` as stimulus | on the STL copy (2026-11-09, Port section) |
| 8 ReCon OTB | n/a (two-source merge shape) | — | — |
| 9 STT on SPT's sub-implementation | no | — | no hooks |
| 10 SPT variants, `FuturisticSafe*` configs | yes | `SPT_6_oneLP_stl` (draft, **generates nothing** yet) | no hooks |
| 11 Delay/NDA (recon scheme 1), 12 DoM (scheme 3) | probably (same shadow tracker; not verified in code) | `STT_6_stl` | on `gem5-recon-stl --scheme=1/3`, untested |
| STT-Futuristic (`/work/stt` + `configs/example/se_futuristic.py`) | yes | `STT_6_stl` | **PARKED** by Anna 2026-11-07 (`FUTURISTIC_MODEL.md`) |

### Models

| Model | Where | State | Generation result |
|---|---|---|---|
| `STT_6_stl` | `STAGE1_alloy/models/STT_6_stl.als` | **approved** 2026-10-28; `rf`-based alias fact | SAT; 60 in 5 s (500 earlier); 60/60 concretize |
| `Recon_6_stl` | `proposed/Recon_6_stl.als` | draft 2026-11-08, atom-based alias | 60 in 10 s; 60/60 concretize |
| `SPT_6_oneLP_stl` | `proposed/SPT_6_oneLP_stl.als` | draft 2026-11-08, atom-based alias | **0 in 900 s**: SPT's state-minimality (RS) vs the alias fact (section "STL for every main model"); a one-line RS exemption gives 60 in 10 s, 59/60 concretize (DECIDE) |
| `STT_6_shadows` | `proposed/STT_6_shadows.als` | draft 2026-11-07: Recon-STT's branch **or** store contract, no alias fact | minimal instances have one source, so its tests = `STT_6`'s + `STT_6_stl`'s (`STT_VS_RECON_STT.md`) |
| `STT_6_stl_core` (split, Stage 1) | `proposed_twophase/STT_6_stl_core.als` | draft, RI-only (RO+RI makes an STL core impossible) | **Stage-1 EXHAUSTED: 306 cores at ≤6 instructions** (Mac, 23 min) → `testsets/STT_6_stl__twophase_draft/stage1_xml`, log `~/Library/Logs/simspect/twophase_STT_6_stl.log` |
| `Recon_6_stl_core` (split) | `proposed_twophase/Recon_6_stl_core.als` | draft, RI-only | Stage-1 **running** since 13:58 (858 at 40 min; cap 20000, 4 h) → `testsets/Recon_6_stl__twophase_draft/stage1_xml`, log `twophase_Recon_6_stl.log` |
| `SPT_6_oneLP_stl_core_conservative` (split) | `proposed_twophase/` | draft, no RO/RI (SPT conservative convention) | UNSAT at ≤3 and ≤4 (same RS cause); not run |
| Stage 1.5 (pin + add) for any STL core | — | not built (the two-phase session owns Stage 1.5 for every family) | — |

Tools: `STAGE1_alloy/models/proposed/derive_stl.py` (main model → STL draft; reproduces `STT_6_stl` from `STT_6`), `STAGE1_alloy/model_source_matrix.py` (which speculation sources a model admits; `str_alias_atom` predicate), `proposed_twophase/derive_core.py` + `run_stage1.py` (split cores). Concretization: `parsexml.py` branch mode `stl_bypass` (`pass2_6_specify_stl`). Run config: `runconfigs/run_config_STT_6_stl.jsonc` (gem5-recon-stl, scheme 2, hold D = 5000, `no_alias`, fnc 150, `max_instances` 100000).

### Experiments

| Experiment | State | Result / where |
|---|---|---|
| Hook test: 60 `STT_6_stl` tests on `gem5-recon-stl`, configs A–F | **done** 2026-10-30 | valid bypass 58/60; STT 0/28 load transmitters sent in the window vs Unsafe 28/28; `alias` and D = 0 controls 0. cafe2 `results/STT_6_stl_hooktest/controls/` (section "Hook test") |
| Shadows store-only + alias: 60 tests, STT vs Unsafe vs `alias` | **done** 2026-11-07 | 59/60 valid; STT 0/32 sent vs Unsafe 32/32; `alias` 0. cafe2 `results/STT_6_shadows_draft/` (`stl_A_stt.json`, `stl_B_unsafe.json`, `stl_C_stt_alias.json`, `cfg_stl.jsonc`) |
| Full `STT_6_stl` testset + sweep (Recon-STT, unit 2) | **planned, blocked** | needs the STL window checker (not written; `check_ld`/`check_br` verdicts are not meaningful for STL tests: no `lc`, `fnc` = the store) and, ideally, a refreshed `gem5-recon-stl`. Until then score with `gem5-hooks/stl/stl_hooktest.py` |
| `Recon_6_stl` on `gem5-recon-stl` (unit 5) | planned | needs the draft approved; ReCon mode on that build unverified |
| ReCon on store shadows, row E2w-stl (`Recon_6_u_stl_core_lpP_s2A`, 60,342 tests, `gem5-recon-modded-stl`) | **done** 2026-11-16 | UV2 2,906; 58 br_x twin-hit candidates; R-SA-13 23,659; `../state/EVAL_MANIFEST.md` row E2w-stl |
| `STT_6_stl` on schemes 1 and 3 (units 11, 12) | planned | untested; shadow-tracker sharing across schemes not verified |
| STL on amulet ×3 (units 4, 6, 7) | **hooks built, controls done** 2026-11-09 | 60 `STT_6_stl` tests per build, in copies of the trees; section "Port to the AMuLeT builds (2026-11-09)". `gem5-spt` (unit 10) not started |
| SPT STL generation | blocked | RS DECIDE |
| Stage-1 STL cores | 1 done (STT, 306), 1 running (Recon), 1 blocked (SPT) | see Models |

### Open decisions (all in `URGENT_TODO.md`)

- Approve `Recon_6_stl` (recommended) and, after the RS call, `SPT_6_oneLP_stl`.
- SPT STL: (a) exempt the alias location from RS (recommended), (b) drop RS, or (c) skip SPT STL for now.
- Alias fact: `rf` (approved `STT_6_stl`) vs atom-based (the new drafts; superset, works without `rf_from_most_recent_writer`). Re-deriving `STT_6_stl` with `--alias atom` gives 60 in 7 s, 60/60.
- Approve `STT_6_shadows`, and whether it needs a true-alias fact.
- STL hooks: (i) rebuild `gem5-recon-stl` from today's recon-modded (recommended first), (ii) port to amulet ×3 + `gem5-spt`.
- `stl_bypass` annotates every aliasing load, not only the first: OK as the semantics?
- Window checker design (below), including accepting a squash caused by S of any load at or before L (gem5 checks violations at 16-byte granularity).
- Contract granularity: every instruction after an unresolved store (encoded), or only loads that may alias it?
- Whether the forced memory-dependence prediction counts as "the predictor" under the hook rule (HOOK_AUDIT borderline).

### Lessons (things that produced wrong answers or failures)

- **Shared `Mem_s` atom ≠ `rf` edge.** The model lets a store and a load name the same location with no `rf` edge; they still alias in the concrete program. An `rf`-based alias filter misses them (37/60 of atom-alias instances had no `rf` edge).
- **A store-source instance without a true alias doesn't concretize**: its store usually has no location (`outmem` is `set`, can be empty), so `stl_bypass` fails with "no specified outmem". Under Recon-STT such a load is still "speculative", but nothing transient happens.
- **Minimality keeps one source per instance**: branch + store together found nothing in 25 min, because the older source's shadow covers the younger one.
- **RO+RI minimality makes an STL core impossible**; RI-only is required (306 cores at ≤6).
- **SPT protects a load's output regardless of the location read**, which is why its RS-minimality kills every aliasing instance.
- **gem5 detects memory-order violations at 16-byte granularity**: the squash can name an older load 8 bytes from S.
- **Hook bugs fixed 2026-10-30**: the litmus setup `mfence` sends dispatch down the barrier path (override applied there too); priming the store set fails for `alias` (the load now depends on the store's seqNum directly).
- **Harness gotchas**: `stl_hooktest.py` needs an absolute testdir (fixed in the repo copy 2026-11-07); ship tarballs to cafe2 with `COPYFILE_DISABLE=1` (macOS `._*` files break asm); cafe2 has no `a6CountModels.class`, so generate XML on the Mac.
- **Signal on recon builds**: the real cache send is `Memory request (pkt: …) from inst [sn:N] was sent` (`lsq_unit.cc:1546`), not `Doing memory access`; `check_ld`'s gate keys on a line that doesn't exist there (`wiki/findings/bug/recon_cache_reach_gate/`).

## Status

| Piece | State |
|---|---|
| Model `STAGE1_alloy/models/STT_6_stl.als` | written (Anna approved new `.als` files), SAT, 500 instances enumerated locally in a few seconds |
| Concretization, branch mode `stl_bypass` | written + tested: 500/500 instances concretize and compile to x86; the existing modes are byte-identical before/after (120/120 STT_6 `.ll` + `.ann.json`). 2026-10-30: every true-alias load is annotated, not only the first (2/60 tests gain a second one) |
| Harness flags (`gem5.stl_*` → `SIMSPECT_STL_*` → `--stl-*`) | written; off unless a config sets `gem5.stl_ann_enable` |
| gem5 hooks `gem5-hooks/stl/` | **built** into `/work/gem5-recon-stl` (copy of gem5-recon-modded, 2026-10-30); two hook bugs found and fixed by the controls; all controls pass on 60 tests (see Hook test). 2026-11-09: ported to copies of the three AMuLeT builds, controls pass there too (Port section) |
| Window checker | **built 2026-11-16** (agent reconstlhook): store-shadow mode in `gem5_common.process_one`, keyed off `stl_annotations`; section "Window check (built 2026-11-16)" |
| STL models for the other main models (2026-11-08) | drafts `proposed/Recon_6_stl.als`, `proposed/SPT_6_oneLP_stl.als` via `proposed/derive_stl.py`; split cores in `proposed_twophase/`. Recon works; SPT generates nothing yet (see "STL for every main model") |

## The primitive: a false-negative alias prediction

The store's address is unresolved when a younger load to the same address issues. The memory-dependence predictor says "no alias", so the load does not wait. It reads the stale value (the store's queue entry has no address yet, so the forwarding scan skips it), and its dependents, the transmitter among them, run on that value. When the store's address resolves, the LSQ sees that a younger load to the same address already executed (a memory-order violation) and squashes from that load. The window is load issue → that squash. This is Spectre v4 (speculative store bypass), and the analog of an unresolved, mispredicted branch: the bypass path only ever runs speculatively.

The false-positive direction (predict alias, addresses differ) opens no window in gem5: O3's store sets only make the load wait; there is no predictive forwarding. It is kept as a negative control (`--stl-alias-pred=alias`).

STT's paper covers this only in its Futuristic threat model, **but the Recon builds' STT does cover it** (see Threat model below). STT p5: "In the Spectre model, an instruction has reached the visibility point if all older control-flow instructions have resolved. In the Futuristic model, an instruction has only reached this point if it cannot be squashed." STT §6.4.2 frames memory-dependence speculation as "simply a prediction of the store-to-load forwarding implicit branch". Source: `~/Documents/quail/sources/papers/yu-2019-stt.pdf`.

## Generation: `STT_6_stl.als`

A copy of `STT_6.als`, with changes only in the STL block and the defense block. `STT_6.als` is untouched. Every instance has an unresolved store S, a load L after it that reads S's `Mem_s`, and L's value flowing to the transmitter. In the 500 enumerated instances, 500/500 have the transmitter fed by a load of S's location, which the state-minimality clause (`all s: State | secure[RS->s]`) forces. 39/40 of a first sample have no committed instructions (S is the first non-committed).

```diff
+fun has_unresolved_strs_p[p: PTag->univ] : Instruction {
+	((unresolved_p[p] & Stores).(^(spo_p[p]))) // all the instructions that come after a store with an unresolved address
+}
+fun no_unresolved_strs_p[p: PTag->univ] : Instruction {
+	i_p[p] - has_unresolved_strs_p[p]
+}
+
+// control-flow speculation is off in this model
+fact stl_no_unresolved_branches {no (unresolved & (Branchxs+Branchns))}
+
+// true alias (the false-negative prediction): some load at or before the xmit
+// reads the memory state an older unresolved store writes (rf = most recent
+// writer, so no intervening store to that state)
+fact stl_alias_pair {
+	some s: unresolved & Stores, l: uncommitted & Loads |
+		some (s.outmem.rf & l.inmem) and l in xm + xm.^(~spo)
+}
 ...
-fun speculation_contract_p[p: PTag->univ] : Instruction {uncommitted_p[p] & has_unresolved_brs_p[p]}
+fun speculation_contract_p[p: PTag->univ] : Instruction {uncommitted_p[p] & has_unresolved_strs_p[p]}
 ...
-	s - (Loads & no_unresolved_brs_bf_or_is_p[p] & i).inmem.opstate
+	s - (Loads & no_unresolved_strs_p[p] & i).inmem.opstate // loads with no unresolved-address store before them remove their inmem state from the protset
```

- **Speculation source.** `has_unresolved_strs_p` mirrors `has_unresolved_brs_p`: everything after a store whose address is unresolved (`isresolved` on a store = its address is known).
- **Contract.** Uncommitted and after an unresolved store, in place of after an unresolved branch.
- **Protset propagation.** A load with no unresolved store before it declassifies its location, mirroring the branch rule.
- **No control-flow speculation.** All branches are resolved, as asked. The transmitter branch keeps the existing xmit override in concretization: it is the observable, not the speculation source.
- **True alias.** The fact is the generation half of "false negative": without it, a load past an unresolved store is speculative under the contract but never squashed in gem5, and the value it reads is the architectural one.
- **Minimality.** The existing `all i: (unresolved - first_uncommitted) | secure[RR->i]` already ranges over stores, so every unresolved store must matter. Unresolved loads or ALU ops can't appear except as the boundary instruction.

To check against the papers (Anna, 2026-10-28: "we will have to read the papers again"): whether STT's Futuristic contract marks every instruction after an unresolved store as unsafe (what this encodes), or only loads that may alias it.

## Concretization: branch mode `stl_bypass`

Turned on only by putting `"stl_bypass"` in `speculation.branch_modes` (or `batch_generate.py --mode stl_bypass`). The other modes never call the new code. Output goes to its own per-mode tree, `testsets/<model>/stl_bypass/`, so it is a parallel pipeline.

- `pass2_5_specify_branches` accepts the mode and refuses an instance with an unresolved non-xmit branch (STT_6 XMLs are rejected, 3/3 tried). Resolved branches become `correctly_not_taken` exactly as before.
- New `pass2_6_specify_stl` pairs each unresolved store S with its bypass load L: the first uncommitted load after S that reads S's `Mem_s` before another store writes it (the model's most-recent-writer rule). Pairs are tags on the instruction records, because `pass_interleave` renumbers PCs. A missing pair raises, so the test is skipped and logged.
- **Making the alias real at runtime.** A load or store with a specified `inaddr` is emitted as `probe_mem + reg` and ignores its `Mem_s` slot, so model-level aliasing isn't guaranteed. When neither S nor L has `inaddr`, they share the `mem_base` slot and nothing changes (487/500). Otherwise (13/500) S is re-emitted at L's runtime address, relative to L's base and keeping S's own index register: `movq src, D(base, r_S, 1)` or `movq src, D(base)`. D comes from a small architectural evaluator over the straight-line program (`_stl_arch_values`). It mirrors the emitted asm, evaluates twice to check L's address doesn't depend on the re-targeted store, and raises on anything it can't evaluate exactly. Loads and stores are already inline asm, so LLVM cannot fold the store→load.
- `.ann.json` gains `"stl_annotations": [{store_pc, load_pc, mem_atom, mode}]`, and `compile_annotate.py` adds absolute `store_addr` / `load_addr` (the pc marker sits on the `movq` itself).

## gem5 hooks (`gem5-hooks/stl/`)

`apply_stl_hooks.py <gem5_root> [--dry-run]` inserts both hooks by anchor string, not line number (Recon's o3 files are heavily modified). It is idempotent (marker `SimSpect-STL`), writes nothing unless every anchor matches exactly once, and saves originals as `<file>.pre-stl`. `stl_hooks_vs_gem5_v22.0.0.2.diff` is the reference diff from applying it to upstream gem5 v22.0.0.2, which is the version whose `iew.cc` line numbers match Recon's (`recon-modded_src.diff` hunks at `iew.cc:1247`).

| Flag | Hook | Where |
|---|---|---|
| `--stl-ann-file <ann.json>` | supplies the (store_addr, load_addr) pairs | `configs/example/se.py` → CPU params |
| `--stl-store-stall-cycles N` | **store address-generation hold.** An annotated store is sent back to the mem-dep replay list (`IEW::rescheduleMemInst`, the LSQ's own path for a load it can't execute yet) instead of computing its address, and an event replays it N cycles after it first issued. An early replay re-defers it. | `cpu/o3/iew.{hh,cc}` |
| `--stl-alias-pred {no_alias,alias,off}` | **prediction override** for the annotated loads: `no_alias` ignores the store-set answer (false negative, the primitive); `alias` makes the load depend directly on the paired store's in-flight seqNum, so it waits (false-positive control). Both modes also apply when a load barrier is in flight (`via=barrier`); `off` = unmodified | `cpu/o3/mem_dep_unit.{hh,cc}` |

Why the existing pieces weren't reused: the recon-modded store "resolve stall" placeholder (`iew.cc` ~1247) fires *after* `executeStore`, so the address is already known. The unwired `AnnotatedStoreSet` (`store_set_annot.cc`) primes the store set in the load's `checkInst`, after the store has already been inserted into the LFST without a set ID, so the forced dependence would miss the first dynamic instance.

Print-only trace lines, under the existing `O3PipeView` flag in the [`SIMSPECT_HOOKS.md`](SIMSPECT_HOOKS.md) format:

```
O3PipeView:simspect:<tick>:STL:stl_hold:line=-:seq=<S sn>:pc=<S pc>:victim=-:cause=-:sq=-:id=-
O3PipeView:simspect:<tick>:STL:stl_release:line=-:seq=<S sn>:pc=<S pc>:...        # hold over; S computes its address now
O3PipeView:simspect:<tick>:STL:pred_no_alias:line=-:seq=<L sn>:pc=<L pc>:...:cause=<dep sn>
O3PipeView:simspect:<tick>:STL:mem_order_squash:line=-:seq=<L sn>:pc=<L pc>:...:cause=<S sn>   # every violation, annotated or not
```

Harness: run config `gem5.stl_ann_enable`, `gem5.stl_store_addr_stall_cycles`, `gem5.stl_alias_pred` → `pipeline._build_gem5_env` → `SIMSPECT_STL_*` → `gem5_common.run_gem5` appends `--stl-ann-file=<test>.ann.json --stl-store-stall-cycles=N --stl-alias-pred=X`. Example config: `runconfigs/run_config_STT_6_stl.jsonc`. Its D = 5000 mirrors `sweep.unresolved_stall_cycles` in `run_config_STT_6.jsonc`.

## Threat model of the build (answered 2026-10-30)

`gem5-recon` / `gem5-recon-modded` / `gem5-recon-stl` STT (scheme 2) is **not** STT's Spectre model: a load is unsafe while any older conditional branch is unresolved **or any older store has no address yet**. So the STL primitive is in scope there.

- Recon paper Sec. 3: "For evaluation, we use only speculation cast by control flow and store instructions"; Sec. 6: "Speculation state is tracked through shadows [...] triggered by control and store instructions", "closer to the Spectre threat model [...] rather than the Futuristic threat model" (`~/Documents/quail/sources/papers/aimoniotis-2023-recon.pdf`).
- Code: `src/cpu/o3/decode.cc:686-695` inserts every conditional branch and every store into the shadow tracker and marks a load speculative if any shadow exists; `secure_scheme/shadow_tracker.cc` frees a store shadow when `effAddrValid()` and a branch shadow when `branchResolved()`; `taint_tracker.cc:138` untaints when the load is no longer speculative. Exceptions are tracked but never inserted ("Currently unused").
- `/work/stt` is different: `--threatModel` Spectre (branches only) or Futuristic (all older instructions completed, `rob_impl.hh:493-512`); the SimSpect harness pins it to Spectre (`gem5-hooks/stt/se_exp.py:332`), where STL is out of scope. See [`FUTURISTIC_MODEL.md`](FUTURISTIC_MODEL.md).

## Hook test (2026-10-30)

Build: `/work/gem5-recon-stl/build/X86/gem5.opt` (md5 `9ac3ac66…`), built with `/usr/bin/scons` (SCons 3.1.2; `/usr/local/bin/scons` 2.5.1 doesn't run on Python 3.8). Applied diff: `gem5-hooks/stl/stl_hooks_vs_gem5-recon-modded.diff`. Testset: 60 `STT_6_stl` instances (XML from the Mac, cafe2 has no `a6CountModels.class`), `testsets/STT_6_stl/stl_bypass/` on cafe2. Driver: `gem5-hooks/stl/stl_hooktest.py <testdir> <scheme> <out.json>` (env `SIMSPECT_GEM5_BIN`, `SIMSPECT_SE_CONFIG`, `SIMSPECT_STL_*`, `LC_ALL=C.UTF-8`); per-config JSONs in cafe2 `results/STT_6_stl_hooktest/controls/`.

| config | valid bypass (hold + no-alias + L before release + squash caused by S) | ld transmitter (28) sent to memory inside [hold, release) |
|---|---|---|
| A: STT (scheme 2), no_alias, D=5000 | 58/60 | **0/28**: STT's delay unit holds every one |
| B: Unsafe (0), no_alias, D=5000 | 58/60 | **28/28**: the primitive opens a real window |
| C: STT, alias | 0/60 (no load bypasses) | 0 |
| E: Unsafe, alias | 0/60 | 0 |
| F: Unsafe, no_alias, D=0 | 0 (no hold) | 0 |

The 2 non-valid tests in A/B (`inst-000020`, `-023`) did bypass: gem5 checks memory-order violations at 16-byte granularity, so the squash names an older load 8 bytes from S, and L is squashed with it. The gate should accept a squash caused by S of any load at or before L.

Bugs the controls found, both fixed:
1. **Hook:** the litmus setup `mfence` (`parsexml.py:2058`) is still in flight when S and L dispatch, so `MemDepUnit::insert` takes the barrier path and never asks the predictor. The override now also applies there (`via=barrier`).
2. **Hook:** priming the store set does not work for `alias`. `StoreSet::issued()` drops the held store from the LFST as soon as it issues, so a load dispatched after that got no dependence (9/60 still bypassed). Now the load depends directly on the paired store's seqNum (`MemDepUnit::stlAliasDep`).
3. **Concretization:** only the first aliasing load was annotated; in `inst-000006` a second load of the same slot feeds the transmitter and bypassed through the cold predictor even under `alias`. `pass2_6_specify_stl` now tags every load of S's location before the next writer; `.ann.json` gets one entry per load (`role` bypass/alias), keeping only loads whose runtime address equals S's.

**Signal on recon builds.** The real cache send is `Memory request (pkt: …) from inst [sn:N] was sent` (`lsq_unit.cc:1546`). `Doing memory access` is not a send: STT's delay unit bounces a tainted load after it (`lsq_unit.cc:2104`). See the gate finding in `wiki/findings/bug/recon_cache_reach_gate/`.

## gem5-recon-modded-stl (2026-11-16)

*Agent reconstlhook, Anna's option (a) of 2026-11-16: make ReCon's store-shadow tests runnable and scorable on the build of the reported ReCon rows.*

- **Build.** cafe3 `cp -a /work/gem5-recon-modded /work/gem5-recon-modded-stl` (source binary md5 `762efbc608e1c803368d19d1101abcbd`, the E2w binary, which has the 2026-10-30 resolve hooks), then `python3 gem5-hooks/stl/apply_stl_hooks.py /work/gem5-recon-modded-stl` (unchanged script; all 7 files' anchors matched once; `*.pre-stl` backups), then `cd /work/gem5-recon-modded-stl && nice -n 10 /usr/bin/scons build/X86/gem5.opt -j 24`. The first build failed because 6 generated include stubs in `build/X86/mem/ruby/protocol/` (`DataBlock.hh`, `Set.hh`, `TimerTable.hh`, `WriteMask.hh`, `TBETable.hh`, `BoolVec.hh`) hold an absolute `#include "/work/gem5-recon/build/..."` from the tree the recon-modded build was originally made in; they were repointed to `/work/gem5-recon-modded-stl/build/...`. Logs: cafe3 `/tests/reconstlhook_20261116/logs/build{,2}.log`. `gem5.opt` md5 **`06240ccea173d11b3b2be61adcdbe387`**; the binary and `configs/` were copied to cafe1 at the same path (same md5). `/work/gem5-recon-modded` itself was not touched.
- **Hook diff:** `gem5-hooks/stl/stl_hooks_vs_gem5-recon-modded_20261116.diff` (5 `src/cpu/o3` files + `configs/common/Options.py` + `configs/example/se.py`). Same hooks and `STL:` lines as `gem5-recon-stl`; every resolve-hook (`BR:`) line is still there.
- **Hooks off = recon-modded.** 12 E2w stems x 2 modes through `pipeline.py gem5` with the E2w config on the new binary vs `gem5-recon-modded`: 24/24 records byte-identical.
- **Store stays unresolved for the stall:** every valid test has `stl_hold` and `stl_release` 5000 cycles apart (e.g. inst-000006: hold 2672500, release 5173000 at 500 ticks/cycle), and the `stl_hold` gate fails a test when the hook did not fire.
- **Address resolution.** The window ends at `stl_release`, printed immediately before `LSQ::executeStore`, the call that computes the store's address (`effAddrValid`, where ReCon's `shadow_tracker.cc` frees the store shadow) and runs `checkViolations` (the `mem_order_squash` lands at the same tick in every validation test). So the hook's "address resolves" and ReCon's coincide; no decision was needed.

## Window check (built 2026-11-16)

Implemented as a mode of the existing checkers, not a new checker: `gem5_common.process_one` calls `stl_pairs_of(ann)`; only when the `.ann.json` has `stl_annotations` (every `stl_bypass` test, never a branch test) does it apply `stl_window` + `stl_transient_view`:

1. **Window = the branch window + the store shadow.** Each annotated store S becomes an extra entry in the `unresolved` list that `check_branch_resolutions` gates on (`source: "stl"`): the transmission signal must come before S's `stl_release`. lc / fnc keep their meaning (fnc = S, so `before_fnc` is implied). This mirrors how check_ld / check_br use branch resolution for branch-shadow tests.
2. **Transient view.** The checker sees only pipeview records fetched, LSQ records inserted and commit squashes broadcast before the earliest memory-order squash S causes. After that squash L and X replay with the right value (architectural); matching by PC alone would score the replay.
3. **Validity gates** (`criteria.stl_hold/stl_pred/stl_bypass/stl_squash`; any False = `status: invalid`, never a hit, verdict kept in `issued_in_window_unvalidated`): the hook held S; a `pred_no_alias` for an annotated load (only with `--stl-alias-pred=no_alias`); the first annotated load instance executed before `stl_release`; a `mem_order_squash` caused by S of a load younger than S and at or before that instance (16-byte granularity).
4. **Transmission criteria unchanged:** check_ld's data-obtained gate (incl. `store_forward`), check_br's redirect (Commit `Squashing due to branch mispred`). One support change: `stl_transient_view` returns a `CommitSquashes` dict marked `commit_traced`, and check_br reads that marker, because check_br infers "the Commit flag was on" from a non-empty squash dict, which is false for a store-shadow test with no branch mispredict at all (a first draft without the marker fell back to "branch completed" and scored 32/32 false positives at scheme 2). `run_gem5` always adds the Commit flag.
5. **Informational only:** `parse_lsq` gains `sent_tick` (Recon's real send, `Memory request ... was sent`, `lsq_unit.cc:1546`), and each record's `stl.xmit_sent_tick` is the transient X's send. Not part of any verdict (the recon gate finding, `wiki/findings/bug/recon_cache_reach_gate/`, is still Anna's call); it counts X loads that sent inside the window but the gate scores as not obtained.
6. Record fields: `stl` (stores, per-store hold/release/squash ticks and seqs, load sn, gates, notes, `t_squash`, `xmit_sn`, `xmit_sent_tick`); `branch_resolutions` holds the store entries.

**Branch-shadow scoring is byte-identical:** 12 E2w stems x 2 modes (6 ld + 6 br_x per mode, incl. the UV3 stems inst-003908 / inst-013804 / inst-000685), `pipeline.py gem5` with the E2w config on `gem5-recon-modded`, HEAD `gem5_common.py` vs the new one: 24/24 records identical (cafe3 `/tests/reconstlhook_20261116/results/e2w_regress_{old,new}`, `regdiff.py`).

**Validation** (E2w gem5 block + hold 5000, `no_alias` unless noted; cafe3 `/tests/reconstlhook_20261116/results/val_*`):

| run | 60 minimal `STT_6_stl` tests (28 ld, 32 br_x) | 40 corpus tests (24 ld, 14 br_x valid) |
|---|---|---|
| scheme 0 (Unsafe) | ld 27/28, br_x 32/32 hit | ld 22/24, br_x 13/14 |
| scheme 2 (ReCon) | **ld 0/28, br_x 0/32** | ld 15/24, br_x 8/14 (fanout/fpr tests; classified with the corpus) |
| scheme 0, `alias` control | 0 hits; 60/60 invalid (no bypass) | 0 hits; 40/40 invalid |

Hand-checked test `STT_6_stl` inst-000006: S `movq %r9,(%rsi)`, L `movq (%rsi),%r15`, alias load `movq (%rsi),%rax`, X `movq (%rsi,%rax),%r11`. S held 2672500 → released 5173000; L executes at 2672500; the squash names L, caused by S. Scheme 0: X sends at 2675000, hit. Scheme 2: X executes, never sends (delay unit), no hit. The one scheme-0 minimal ld non-hit sent inside the window but scored not obtained: the recon gate gap.

## Proposed window check (design of 2026-10-30; built as above with the differences noted there)

Per test: S, L and the xmit X are known by address from the ann. All times come from one pipeview trace (`O3PipeView` + `LSQUnit`).

1. **The primitive fired: validity gates.** If any gate fails, the test is `stl_invalid` with the reason, counted neither as leak nor as no-leak.
   - `stl_hold` for S's first dynamic instance (else the hooks aren't in this binary).
   - With `no_alias`, a `pred_no_alias` line for L.
   - L's first dynamic instance executes (LSQUnit "Executing load") before `stl_release`: the bypass happened.
   - Its fate isn't `store_forward`.
   - A `mem_order_squash` with `cause` = S and `seq` = an instance at or before L's first instance (16-byte violation granularity can name an older neighbour): the alias was real. No squash means a concretization bug.
2. **Which X counts.** Only X's *first* dynamic instance: younger than S, at or after L's first instance, and squashed by that `mem_order_squash`. After the squash, L and X re-execute with the right value, and that replay is architectural. That differs from the branch checkers, which match the xmit by PC.
3. **Window.** `t(stl_hold) ≤ signal < t(stl_release)` is the strict contract bound: X transmits while S's address is unresolved. Also record `signal < t(mem_order_squash)`, the transient bound; the two differ by a cycle or two. Don't reuse the branch window `lc_retire < signal < fnc_retire`. There is usually no committed instruction (no `lc`). `fnc` = S retires after the squash and the commit stall, so the replayed X would land in-window: a false positive.
4. **Signal and gate per transmitter kind.**
   - For `ld`: the real-send tick (`Memory request … was sent` on recon builds; `successfully sent out packet(s)` on /work/stt and gem5-spt) or store-forward completion, keyed by X's instance seq, not by PC. The shared `check_ld._xmit_cache_fate` cannot be reused as-is on recon builds (see the gate finding).
   - For `br_x`, the redirect tick check_br already uses, now with the window enforced (closing check_br's known gap for these tests).
   - Implement this as one shared `stl_window(trace, ann)` in `gem5_common.py` that `check_ld` / `check_br` call when `ann` has `stl_annotations`, not as a new checker family.
5. **Controls, run before reading any STT hit.**
   - Unsafe baseline (scheme 0) + `no_alias`: nearly every valid test should leak, which shows the primitive works.
   - Any scheme + `alias`: L waits for S, no squash, so 0 leaks. A hit here is a checker bug.
   - Hold sweep, e.g. D ∈ {0, 50, 500, 5000}: at D = 0 the bypass should mostly vanish.
6. **Bucketing.** `stl_invalid` reasons become an error-bucketing diagnostic in the run's `diagnostics/`, per the diagnostics rules.

## Open

- **Answered:** build = copy `/work/gem5-recon-stl` (Anna, 2026-10-30); threat model = control + store shadows (above).
- **Window checker** built 2026-11-16 ("Window check (built 2026-11-16)"). The full ReCon store-shadow corpus run is in `../state/EVAL_MANIFEST.md` (row E2w-stl).
- **Contract granularity.** Is "everything after an unresolved store" right for STT Futuristic, or only loads that may alias it? See Generation.
- **Other defenses.** Drafted 2026-11-08 (next section). The hooks still port by re-running `apply_stl_hooks.py` on each tree; `/work/gem5-recon-stl` and, since 2026-11-09, the copies `/work/amulet/hooks_stl_work/<Build>` of the three AMuLeT builds have them (Port section).

## STL for every main model (2026-11-08)

`STAGE1_alloy/models/proposed/derive_stl.py <main>.als <out>.als [--alias atom|rf]` applies exactly the edits that turned `STT_6.als` into `STT_6_stl.als`: the STL source block (`has_unresolved_strs_p`, `no_unresolved_strs_p`, all branches resolved), the alias fact, the contract switched to stores, and the branch-keyed protection-set line switched to stores where the model has one. Every anchor must match once or it refuses. Self-check: `--alias rf` on `STT_6.als` gives code identical to `STT_6_stl.als` (ignoring comments and whitespace).

The drafts use the atom-based alias (`--alias atom`, default): every unresolved store has a younger uncommitted load at or before the transmitter naming the same `Mem_s`, with no other store to it in between. Reasons: it is a superset of the `rf` version (more tests); Recon_6 and SPT_6_oneLP lack `rf_from_most_recent_writer`, which the `rf` version relies on for "no store in between"; and in SPT an `rf` edge from the store would let its forwarding rule treat the bypassing load as getting the store's value, which is the opposite of a bypass.

| Model | Alloy, exactly 6 | `stl_bypass` concretization | Split core (Stage 1) |
|---|---|---|---|
| `STT_6_stl` (approved, `rf` alias) | 60 in 5 s | 60/60 | `STT_6_stl_core.als`, RI-only: 200 (capped) at ≤3 in 12 s and at ≤4 in 67 s |
| `STT_6` + atom alias (scratch, for comparison) | 60 in 7 s | 60/60 | — |
| `Recon_6_stl` (draft) | 60 in 10 s | 60/60 | `Recon_6_stl_core.als`, RI-only: 200 at ≤3 in 31 s, at ≤4 in 165 s |
| `SPT_6_oneLP_stl` (draft) | **0 in 900 s** | — | `SPT_6_oneLP_stl_core_conservative.als` (no RO/RI): **UNSAT** at ≤3 (34 s) and ≤4 (326 s) |

**Why SPT generates nothing.** SPT's protection seed protects every operand except unfed register/address inputs (`SPT_6_oneLP.als:341`), so a speculative load's output is protected whatever location it reads. The aliased `Mem_s` is then never necessary for the leak, and state-minimality (`all s: State | secure[RS->s]`) rejects every instance in which the store and the load share it, which the alias fact requires. Probes on the ≤3 core: RS off gives 50 instances in 5 s; the alias fact off gives 50 in 16 s; the perturbation-aware seed from the 2026-11-07 SPT probe still gives 0; RS with the alias location exempt (`all s: State - (unresolved & Stores).outmem.opstate | ...`) gives 50 in 8 s, and on the full model 60 in 10 s at exactly 6, of which 59/60 concretize. The one failure is a `parsexml` edge case: `stl_bypass: bypass load address probe+-1 out of bounds` in `_stl_store_retargets` (`parsexml.py:1208`), not investigated. The fix is a generation-predicate choice, so it is a DECIDE in `URGENT_TODO.md`; the draft stays as derived.

**Running STL tests needs the STL hooks** (store-address hold and the forced no-alias prediction): `/work/gem5-recon-stl`, and since 2026-11-09 the AMuLeT copies in `/work/amulet/hooks_stl_work/` (next section). That build is stale: it predates the 2026-10-30 resolve hooks (`wiki/findings/audits/2026-11-07/HOOK_AUDIT.md`). Which defenses have STL in their threat model, per build: `STAGE1_alloy/models/MANIFEST.md` ("Defenses we test").

## Port to the AMuLeT builds (2026-11-09)

*Session stl-port, Anna's ask of 2026-11-09. Everything here was run on cafe2 (`gem5_dev`) unless a line says "by reading". Work dir `/work/amulet/hooks_stl_work/` (20 GB: tree copies 7.6 + 7.1 + 4.5 GB, run outputs 250 MB; `/work` 157 GB free after). The in-place trees `/work/amulet/amulet-gem5-<Build>_AE-v1.1` were only read; their `gem5.opt` md5s are unchanged (InvisiSpec `f45251db6d580f12e549751b9331a3ca`, CleanupSpec `ec5710cad23e43b265f08657710fcb21`, SpecLFB `a84176e23121db26d8f2f9019d586566`) and no file under their `src/` or `configs/` is newer than the copy.*

### Binaries and flags

| Build | STL binary (copy) | md5 | defense flags (= `runconfigs/footprint/*.jsonc` `extra_args`) | defense off |
|---|---|---|---|---|
| InvisiSpec | `/work/amulet/hooks_stl_work/InvisiSpec/build/X86_MESI_Two_Level/gem5.opt` | `376198d5f5f4fd77cb022ba19d5d4924` | `--ruby --scheme=SpectreSafeInvisibleSpec` (or `FuturisticSafeInvisibleSpec`) `--needsTSO=1 --allowSpecBuffHit=1 --l1d_size=1kB --l1d_assoc=2 --l1i_size=32kB --l1i_assoc=4 --l2_size=2MB --l2_assoc=16 --L1_TBEs=2 --L2_TBEs=2 --DC_TBEs=2` | `--scheme=UnsafeBaseline` |
| CleanupSpec | `/work/amulet/hooks_stl_work/CleanupSpec/build/X86_MESI_Two_Level/gem5.opt` | `c7989d25487c18b5aeec78a1e7108afc` | `--ruby --scheme_invisispec=UnsafeBaseline --scheme_cleanupcache=Cleanup_FOR_L1L2 --needsTSO=0 --l1d_size=2kB --l1d_assoc=4 --l1i_size=32kB --l1i_assoc=4 --l2_size=2MB --l2_assoc=16 --L1_TBEs=8 --L2_TBEs=3 --DC_TBEs=2 --abs-max-tick=3000000000` | `--scheme_cleanupcache=UnsafeBaseline` |
| SpecLFB | `/work/amulet/hooks_stl_work/SpecLFB/build/X86/gem5.opt` | `f2e3e9fe1419a67d5ce1aba9a51805d8` | `--scheme=Speclfb --l2cache --l1d_size=1kB --l1d_assoc=2 --l1i_size=32kB --l1i_assoc=8 --l2_size=2MB --l2_assoc=16` | `--scheme=unsafebaseline` (the tree's own choice; the defense is on only when the string equals `Speclfb`, `iew.cc:107`, `lsq_unit.cc:287`) |

STL flags: `--stl-ann-file=<test>.ann.json --stl-store-stall-cycles=5000 --stl-alias-pred=no_alias` (D = 0 or `alias` for the controls). The harness (`gem5_common.run_gem5`) adds `--cpu-type=DerivO3CPU --caches --scheme=2 --abs-max-tick=100000000000 --branch-ann-file … --branch-ann-base …` and debug flags `O3PipeView,Commit`; no fnc stall; `TMPDIR=/tmp`. Branch annotations on and no fnc stall are the settings of the 2026-10-30 hook test (cafe2 `results/STT_6_stl_hooktest/run_config.jsonc`, and `stl_hooktest.py` passes `fnc_pc=None`). Registry: `specs/gem5_builds.json` ids `amulet-InvisiSpec-stl`, `amulet-CleanupSpec-stl`, `amulet-SpecLFB-stl`.

### How it was built, and how to re-apply

1. Copy, inside `gem5_dev`: `gem5-hooks/stl/copy_amulet_trees_for_stl.sh` (tar of the whole tree including `build/`, minus the `build/*/gem5.opt.*` backup binaries; log `/work/amulet/hooks_stl_work/copy_trees.log`).
2. Apply: `python3 gem5-hooks/stl/apply_stl_hooks_amulet.py /work/amulet/hooks_stl_work/<Build> --build <Build> [--dry-run]`. It is anchor-based (every anchor must match exactly once or nothing is written), idempotent (marker `SimSpect-STL`), saves `*.pre-stl` backups, and refuses an in-place `amulet-gem5-*` tree. Equivalent: `patch -p1 < gem5-hooks/amulet-<Build>/stl_hooks.diff` from the copy's root (that diff is the script's `--diff` output after applying). Files: InvisiSpec and CleanupSpec `src/cpu/o3/{O3CPU.py,iew.hh,iew_impl.hh,mem_dep_unit.hh,mem_dep_unit_impl.hh}`; SpecLFB `src/cpu/o3/{BaseO3CPU.py,iew.hh,iew.cc,mem_dep_unit.hh,mem_dep_unit.cc}`; all three `configs/common/Options.py` and `configs/example/se.py`. `lsq_unit*` needed no change (the hold never calls `executeStore`).
3. Build: `gem5-hooks/stl/build_stl_amulet.sh <Build>` with `J=16` (Ruby trees `python2 /usr/local/bin/scons`, SCons 2.5.1; SpecLFB `python3 /usr/bin/scons --ignore-style`; the same as `gem5-hooks/verify/build_simspect_hooks.sh`). Incremental builds, all rc=0: InvisiSpec 04:50:46–04:52:12 UTC, CleanupSpec 04:52:12–04:53:38, SpecLFB 04:50:46–04:55:12 (2026-11-10 UTC). Logs `/work/amulet/hooks_stl_work/build_<Build>_stl.log`. Each binary contains the 5 `STL:` format strings; the in-place binaries contain none.
4. Verify: `gem5-hooks/stl/run_stl_off_verify.sh` (check (a)), `gem5-hooks/stl/run_stl_controls_amulet.sh <Build>` (check (a) on STL tests, and (b); driver `gem5-hooks/stl/stl_hooktest_amulet.py`), `gem5-hooks/stl/stl_footprint_offline.py` (d). Outputs on cafe2: `/work/amulet/hooks_stl_work/{verifyoff,stlruns/<Build>,checkerq}/`; each `stlruns/<Build>/run.log` records every config's exact env and flags. The driver imports a copy of the Mac harness in `/work/amulet/hooks_stl_work/harness/` (gem5_common, cache_setup, check_ld, check_footprint, make_rmw_corpus, the three criteria), not `/tests/simspect`, which other sessions run.

### Where the port differs from the recon-stl hooks

- **`mem_order_squash` prints only in a run given `--stl-ann-file` with at least one pair** (IEW member `stlTraceOn`); recon-stl prints it in every run. Otherwise a run without STL flags would print an extra line at every memory-order violation and could not be byte-identical to the in-place hooks-v2 binary. In an STL run it still prints for every violation, annotated or not.
- **InvisiSpec and CleanupSpec keep one memory-dependence producer per instruction** (`producing_store`), where gem5 v22 keeps a list. In `alias` mode with a load barrier in flight, the load waits on the younger of the barrier and the paired store. A paired store younger than the barrier itself waits on a barrier (`insertBarrier` sets `storeBarrier` together with `loadBarrier`), and an older one commits before the barrier executes, so the load still waits for both. 52/60 tests take this path (`via=barrier` lines), and both `alias` controls still give 0 bypasses.
- **Old-gem5 syntax only** in InvisiSpec and CleanupSpec: `params->`, `DynInstPtr &`, `Impl::MaxThreads`, optparse `add_option`, `options.` in `se.py`, and a non-const copy of the instruction captured by the release event. CleanupSpec's `iew_impl.hh` is re-indented (2 spaces), so its anchors carry that indentation.
- **SpecLFB:** the violation site is `squashDueToMemOrder(inst,violator, tid)` (SpecLFB added the store argument). Every other edit is the recon-stl text verbatim; the script imports it from `apply_stl_hooks.py`.
- **Unchanged from recon-stl:** the hold is the same issue-and-bounce through `rescheduleMemInst`/`replayMemInst`, so HOOK_AUDIT's BORDERLINE notes (a) and (b) apply unchanged; the release event wakes the CPU; the forced prediction touches only the memory-dependence unit; no defense file is edited. By reading: SpecLFB keys "store resolved" on `effAddrValid()` (`rob.cc` `preStoreResolved`), which stays false during the hold because `executeStore` is not called.

### (a) Hooks off: identical to the in-place binary

| check | InvisiSpec | CleanupSpec | SpecLFB |
|---|---|---|---|
| hooks-v2 verify cases, no STL flag: sim ticks and every line of the debug file (`run_stl_off_verify.sh`, `verify_simspect_hooks.py --ref-se`) | inv_uv1 5691000, inv_fut 5699500, inv_014986 5699500: 3/3 identical | cln_uv4align 1252000, cln_uv4split 1251500, cln_uv5clean 1378000, cln_inst002014 6383500: 4/4 identical | lfb_uv6x 1110500, lfb_uv6dep 1109500, lfb_inst002014 6227500: 3/3 identical |
| 60 STT_6_stl tests, no STL flag, defense on: whole trace and ticks | 60/60 identical | 60/60 | 60/60 |
| 60 STT_6_stl tests, `--stl-ann-file` + D = 0 + `off`, against the in-place binary with no flag: trace without `STL:` lines, and ticks | 60/60 identical | 60/60 | 60/60 |

The ticks equal the 2026-11-08 table in [`SIMSPECT_HOOKS.md`](SIMSPECT_HOOKS.md) "How to verify" (the work dir path has the same length as that run's), and `check_v2_trace.py` passes all hard checks on the 10 new traces. Log `/work/amulet/hooks_stl_work/verifyoff/run_stl_off_verify.log`; STL-test comparisons `stlruns/<Build>/compare_*.json`.

### (b) Controls on the 60 STT_6_stl tests

Same 60 tests as the recon hook test (cafe2 `/tests/simspect/testsets/STT_6_stl/stl_bypass`: 28 load transmitters, 32 branch transmitters), warm cache unless marked. "valid" = an `stl_hold` for S, the forced `pred_no_alias` for L, L's first instance issued (`LSQ:issue`) before `stl_release`, and a `mem_order_squash` caused by S that names L's first instance; "relaxed" also accepts a squash of an instance between S and L (16-byte violation granularity). "x" = the load transmitter's first instance.

| config | InvisiSpec | CleanupSpec | SpecLFB | recon-stl 2026-10-30 |
|---|---|---|---|---|
| B: defense off, `no_alias`, D = 5000 | valid 58/60 (relaxed 60/60); x issued in [hold, release) 28/28 | 58/60 (60/60); 28/28 | 58/60 (60/60); 28/28 | 58/60; 28/28 sent |
| E: defense off, `alias` | 0 bypasses; 2 squashes of an older neighbour (inst-000020, -023) | same | same | 0/60 |
| F: defense off, `no_alias`, D = 0 | 0 holds, 0 valid | same | same | 0 |
| A: defense on, `no_alias`, D = 5000 | Spectre 58/60 (60/60); Futuristic 58/60 (60/60) | 58/60 (60/60) | 58/60 (60/60) | STT 58/60 |
| C: defense on, `alias` | Spectre and Futuristic: 0 bypasses; the same 2 neighbour squashes | 0; same 2 | 0; same 2 | 0/60 |
| A with the sandbox out of L1D (InvisiSpec `full`, the others `cold`) | Spectre 58/60, Futuristic 58/60 | 51/53 (7 of 60 panic, below) | 56/58 (2 do not bypass, below) | — |

The primitive works on all three builds as on recon-stl, the `alias` and D = 0 controls never bypass, and the two non-valid tests are the same two as on recon (`inst-000020`, `-023`).

**What each defense does to the bypass load L and its dependents.** These are observations, not verdicts. "Litmus" means the first instance of an Alloy instruction that the store's squash removes. Two kinds of harness instance are left out of the counts: the epilogue loads, and the wrong-path re-fetch of the test function. The re-fetch happens because `_start` falls through past its exit `syscall` into the function again; it sits behind that pass's `mfence`.

| defense | defense off (B) | defense on (A) |
|---|---|---|
| InvisiSpec Spectre (STL is outside its threat model, table above) | x issues as `ld` and misses, fills and evicts in L1D inside the hold in 27/28; litmus L1D fills stay | the same: x `ld`, 27/28 miss + fill + evict, fills stay. 15/60 L issue as `specld`, then become safe (`LSQ:safe why=prev_brs_resolved`) and are exposed. Nothing hides the bypass, as expected for IS-Spectre. |
| InvisiSpec Futuristic | — | every L and x issue as `specld` (60/60, 28/28); no litmus L1D fill; every spec-buffer entry is released at the squash (`SB:buf_release`, 60/60 tests). But a squashed `specld` evicts an L1D line inside the hold in 30/60 tests (x in 27/28): the **UV1** signature (`BUGS.md` "UV1", `L1D:evict req=specld ev=L1_Replacement`; e.g. inst-000006, x seq 572 evicts 0x3980 at 3220500, hold 3173500–5674000). Same with `full`. |
| CleanupSpec, warm | x hits L1D in 28/28; litmus L1D fills in 26 tests, none removed | x hits L1D; litmus L1D fills in 17 tests, 17/17 removed by `cleanup_inv` with a rollback restore; hits need no undo (`cleanup_skip`) |
| CleanupSpec, cold | x misses and fills L1D and L2 in 27/28; litmus fills in 59 tests, none removed | 7/60 panic (below). In the 53 that run, litmus loads fill L1D and L2 in 52; 66/69 L1D and 66/69 L2 fills are removed by `cleanup_inv`. The 3 kept (inst-000017, -018, -019) were in M when `Inv_CLEANUP` arrived (`cleanup_skip st=M`, the skip CleanupSpec takes for an M line), on the aliasing store's own line; not traced further. Today's balance checker reports 0 leaks there (below). |
| SpecLFB, warm | x misses and fills in 27/28; fills stay | x misses, fills and evicts in 24/28; fills stay. At translation 25/28 x print `musl=1 prevnounsafe=1 reallyunsafe=0 unsafe=0`; the 3 with `unsafe=1` do not fill. L is the load-queue head (`lqhead=1`) and is never marked `musl` (54/60). Mechanism (inst-000006): the ROB walk sets the sticky `PrevNoUnsafe` on x at 3711500, before the LSQ walk sets x's `musl` at 3712000, and the LSQ walk skips the head load, so no older load is ever unsafe. This is the known head-skip + sticky-`PrevNoUnsafe` mechanism ([`hooks_speclfb_and_uv6.md`](../findings/audits/2026-10-28/hooks_speclfb_and_uv6.md), `lsq_unit.cc:817`, `rob.cc:464`), here on SpecLFB's memory-order USLs instead of its control USLs. |
| SpecLFB, cold | x fills in 27/28 | x is `unsafe=1` in 19/26 and fills in only 5/26. L, the first unsafe load, still fills (57 tests): the published UV6 first-load exemption. In 2 tests (inst-000041, -042) L is not the head; it is `unsafe=1`, its access is bounced, and it gets S's value by forwarding after the release, so there is no bypass. That is the defense working. |

**CleanupSpec cold panics.** 7/60 (inst-000006, -013, -016, -040, -044, -052, -054) end in `panic: Runtime Error at MESI_Two_Level-L2cache.sm:308: Invalid L1 forwarded request type`. That is CleanupSpec's own cleanup (in inst-000006 the store's squash sends 4 cleanup requests in one tick), the same class SIMSPECT_HOOKS.md "Cache setup strategies" records for cold at `L2_TBEs=2`. With D = 0 (no squash) inst-000006 runs. With `--L2_TBEs=4` or `8` all 7 run (cafe2 `diag/one_cleanupspec_cold.py`). So the footprint config's `L2_TBEs=3`, crash-free for STT_6, is not crash-free for STL cold (DECIDE STL-2).

### (d) Can `check_footprint.py` score an `stl_bypass` test today? (report only; nothing changed)

**By reading: it runs and returns a verdict, but not an STL verdict.**

- **Window.** For these tests `commit_boundary` has no `last_committed` (59/60), `first_noncommitted` is the store S, and there is no unresolved non-transmitter branch. So `lc_fnc_unresolved` gives the window [0, S's retire). S retires after the memory-order squash (60/60), so this is a superset of the STL window [stl_hold, mem_order_squash].
- **Actors.** In `spec` mode every squashed instruction is an actor. That includes the litmus transients, but also the harness instances the same squash removes and anything squashed by a branch transmitter's mispredict. InvisiSpec's `futuristic` mode (`before_visibility_point`) ignores the window altogether.
- **No validity gate.** Nothing checks that the primitive fired (hold, forced prediction, L issued before release, a squash caused by S). A run where it did not fire (no hooks, a missing flag, `alias`, D = 0) is scored as an ordinary run, with no warning.
- **CleanupSpec's balance** keys on each squash's `cleanup_done`, which works for the store's squash as for a branch squash.

**Measured.** `stl_footprint_offline.py` runs the unchanged `evaluate_trace` on the kept traces, with the inputs `process_one` would pass (cafe2 `checkerq/`):

| run | leak | leaks with a litmus event inside [hold, squash] | leaks only from other instances |
|---|---|---|---|
| SpecLFB off / on, warm | 30 / 27 | 30 / 27 | 0 / 0 |
| SpecLFB off / on, cold | 60 / 57 | 60 / 57 | 0 / 0 |
| CleanupSpec off / on, warm | 32 / 0 | 26 / 0 | 6 / 0 |
| CleanupSpec off / on, cold (53 ran with cleanup on) | 43 / 0 | 27 / 0 | 16 / 0 |
| InvisiSpec off / Spectre / Futuristic, warm | 60 / 60 / 60 | 60 / 60 / 60 | 0 |
| InvisiSpec off / Spectre / Futuristic, `full` | 60 / 60 / 60 | 60 / 60 / 60 | 0 |

Under Futuristic most offending events are outside the STL window (9,587, against 223 litmus events inside it, warm). The litmus events inside it are `DTLB:repl_touch` (60/60 tests), the UV1 `L1D:evict` (30), `L2:coh` (30), `DIR:coh` (27) and `L2:fill` (17). Ruby L2 events are attributed through the per-line most-recent-cause map (SIMSPECT_HOOKS.md "Attribution"); the `L2:fill` lines were not checked further.

**Minimal addition (a design for Anna, not built).** One shared `stl_window(trace, ann)` in `gem5_common.py`, as in "Proposed window check" above, returning the validity gates and the window [t(stl_hold), t(mem_order_squash)]. Then, in `check_footprint.evaluate`, when the ann has `stl_annotations`:

1. a record that fails a gate gets `status: stl_invalid`, like `execution_validity`;
2. `in_W` uses that window instead of `lc_fnc_unresolved`;
3. actors are only the instructions squashed by the `ROB:squash` that follows the `mem_order_squash`, and ideally only litmus PCs (first instances of `__litmus_<stem>_pc<N>`), so harness instructions do not count.

The window would be declared in each criterion JSON (e.g. `window.footprint_stl` with `impl: stl_hold_squash`), so the JSON stays the source of truth. Whether Futuristic's window-free actor rule should also be clipped to the STL window for STL tests is part of the same decision (DECIDE STL-1).

### Open

DECIDE items STL-1 to STL-4 in `URGENT_TODO.md`: (1) the STL window and actor rule in `check_footprint` (above); (2) CleanupSpec STL cold: `L2_TBEs` 3 → 4; (3) SpecLFB: count the store-bypass head-skip leak with the existing UV6 / walk-order item or separately; (4) whether and how campaigns use the STL copies (no run config points at them; the in-place trees, which other campaigns run, stay as they are).

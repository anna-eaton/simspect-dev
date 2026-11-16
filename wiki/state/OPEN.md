# OPEN — pickup list (TODOs + questions for Anna)

*Living doc, overwrite-in-place. The place leftover work lands so it survives a killed session.
Dated, grouped. Refreshed by `/session-log`. Newest context at top of each group.*

## 🔴 Critical — owner: Anna (git write lock in force; Claude is read-only on git)
- **Recover git after the disk-full corruption (2026-10-20).** A 98%-full-disk event corrupted git
  objects and an **empty-tree commit was pushed to all remotes**. Symptoms: locally `git ls-files`
  = 0, `HEAD` tree empty, yet "up to date with origin/main". **All working-tree files are intact on
  disk** (just untracked) — nothing is lost locally. Needs a careful restore of a good tree + push,
  by Anna. Until then the repo is untracked; `/session-log` writes are plain files on disk (safe).
  ⚠️ During recovery, make sure the container's untracked June work is preserved — esp. the `.als`
  models `STAGE1_alloy/models/STT_6_core.als`, `STT_6_multisource.als` (approval-only; see
  `wiki/state/SYNC_DIVERGENCE.md`).
  - **Looks resolved (checked read-only 2026-11-09 21:15, resolve-hooks):** `git ls-files` = 9,397, `main` tracks `origin/main` with nothing unpushed, and regular `make sync` commits since 11-08 (latest 264adea). Anna: confirm and delete this item.
- **The `GIT WRITE LOCK`** is now in `CLAUDE.md` (top), `~/Documents/CLAUDE.md`, and memory
  (`git-write-lock`). Claude hands git-write commands to Anna; never runs them.

## 2026-11-09 — resolve-hooks (SPT v2, hit triage) — pickup

Findings: [`../findings/audits/2026-11-08/SPT_V2_AND_HIT_TRIAGE.md`](../findings/audits/2026-11-08/SPT_V2_AND_HIT_TRIAGE.md). Nothing from this session is running; the cafe2 lost check finished (inconclusive).

**Questions for Anna**

- **SPT store transmitters (E11 `str`): score them, drop them, or leave them on the fallback?** No store checker exists; `check_ld`'s fallback scores the store's complete tick. Round 4 had 134 `str` hit tests, every one with a public address under SPT's rules. Your 11-08 decision puts speculative-store transmitters out of scope for KV3 (STT, D-TLB); it doesn't say whether that covers SPT. Options:
  - (a) Write a store criterion before the final batch. Pick the observable event first (address translation, or the write-intent fill at execute).
  - (b) Report E11 `str` as unscored and list it as a known gap.
  - (c) Keep the fallback and classify with the slicer.
  - Recommendation: (b) for the final batch, if the KV3 decision extends to SPT. Otherwise (a).
- **The v2 "lost" check never finished. Does it still matter?** All three runs timed out. The 8 h cafe2 run never got past CNF translation (findings §6.3). Only v2-4 can lose an old test. If DA-8 picks v3, which rewrites v2-4's clause, the question moves to v3. Options:
  - (a) Drop it: v2-4 errs toward more protection, your conservative direction.
  - (b) A check that finishes: enumerate about 300 old-useful instances (`results/spt_v2_20261108/differential/old_only_check.als`, uncapped) and evaluate the chosen model's `useful_new` on each fixed instance.
  - (c) Rerun `lost` at `exactly 5`.
  - Recommendation: (b), on whichever model DA-8 picks.
- **`resolved_before_signal`:** same call as URGENT_TODO "DECIDE (sharper now)". Evidence in findings §8.3.
- **45 `.als` header comments point at the deleted `wiki/design/MANIFEST_BRIEF_SPT_v2.md`** (v2, its cores, v3_core_ri, and the `proposed/ultimate/` SPT queries copied the header). The edit is comment-only, but they're `.als` files, so it's your call. If OK: `cd ~/trippel/simspect && grep -rlI "MANIFEST_BRIEF_SPT_v2.md" STAGE1_alloy --include='*.als' | xargs sed -i '' 's#wiki/design/MANIFEST_BRIEF_SPT_v2.md#wiki/state/EVAL_MANIFEST.md (SPT v2 section)#'`. That changes each file's sha256 (v2's acb1f2e2 included), so the manifest's hashes would need refreshing. Recommendation: leave them; the findings page explains it.

**TODOs (future sessions)**

- Slicer-based `diag_*` for SPT ld/str/br_x (call `spt_cond_slice.py`, bucket constant vs declassified), deployed as each E11 campaign's `diagnostics/`. Then `bucket_hits.py` classifies SPT without hand runs. Needed before anyone reads the final batch's E11.
- Final-batch configs: `runconfigs/fixed_20261030/*_fixed_latest.jsonc` are validation templates with `sample_fraction` 0.02 (also in EVAL_MANIFEST's pipeline list).
- P5 (the skeleton-wide unfed-read fact, all models) is still undecided (EVAL_MANIFEST decisions list). P3 is folded into the DA-8 / "which SPT model" DECIDEs (`P3_const` bucket).
- `STT_6_interleave` in the fixed dir was built from the 05-19 XML of the old STT_6. Regenerate it from the current STT_6 before any interleave campaign means anything.
- Not understood, low priority (findings §8):
  - why gem5-spt keeps committed stores' DynInsts alive;
  - inst-043417's re-fetch loop;
  - the gem5-spt `--trackInstsFile` off-by-one (`regfile.hh:280`).
- cafe2 `/tests/simspect_fixed_20261030/triage/` is this session's evidence (small JSONs and logs). Keep it while the findings page cites it.

## Infra follow-ups
- **`make mini-clone`** (after `make mini-bootstrap`) — give the Mac mini the driver-harness clone
  so `make sync` reaches it and the mini can drive cafe2. (Deferred — blocked until git is recovered,
  since cloning from a corrupted remote would pull the bad tree.)
- **Persistent Claude on the mini** — the always-on driver: a long-lived Claude in the mini's
  `simspect` tmux so work continues with the laptop closed. Set up after the clone exists.
- **Verify the dashboard VSCode links end-to-end** from the laptop (Remote-SSH URIs
  `vscode://vscode-remote/ssh-remote+cafe2/…` for container files; `vscode://file/…` for local).
  The 3-tab redesign + links are deployed and serving; confirm clicking actually opens VSCode.
- **Container zombie cleanup** (optional): `gem5_dev` accumulates `<defunct>` procs (no reaper).
  Harmless; a `docker restart gem5_dev` (when nothing's running) or adding `tini` would clear it.

## Pending Alloy model edits (owner-gated — Anna's sign-off per change)
- **Full list → [`ALLOY_MODEL_CHANGES.md`](ALLOY_MODEL_CHANGES.md)** (created 2026-10-26). The `.als`
  changes to **block out** the known false-positive shapes we triaged on STT/SPT, so re-enumeration
  stops regenerating artifacts we then re-triage. Highest priority:
  - **A1 — source-derived taint closure** (fixes const-addr FPs ~99.9% of SPT `ld` + SPT-Fence
    `no_hold`): seed protset from `Loads.outreg`+memory only, forward closure, union semantics.
  - **A2 — `rf` most-recent-writer fact** (fixes clobber, ~58.6% of `SPT_6_oneLP`): forbid an
    intervening same-state writer; Option A validated on a copy (still SAT).
  - Plus coverage edits (B1–B5: diversity driver, joint minimality, instruction-minimality, var
    length, extended vocabulary) and the rerun matrix.
  - **Rerun cost:** each is a Stage-1 change → full STT + SPT regen (`xml --force`) + re-sweep. Batch
    the edits so we pay the regen once. Nothing applied yet — show Anna the diff and wait.

## Research (carried forward — pre-dates this session)
- **SPT `str` (store-address) hits: classified, but still no store checker** (updated 2026-11-09, resolve-hooks). The June `str` hits are superseded by round 4: all 134 `str` hit tests slice to a public address under SPT's rules (95 constant, 39 declassified; `wiki/findings/audits/2026-11-08/SPT_V2_AND_HIT_TRIAGE.md` §4). `bucket_hits.py` is now multi-kind. They still fall through to `check_ld`'s fallback (wrong criterion); the scoring question is in the resolve-hooks group above.
- **Next experiments** (none launched this session — "decide after seeing state"): branch-hit
  sweeps / resolved-br windows, and the natural + short-timing sweeps, per Anna's TODO in `STATUS.md`.

## Dashboard / views follow-ups
- **Consolidate enumeration so we don't enumerate a model "by bound."** Right now a model is
  enumerated at a fixed instruction scope (`exactly 6 Instruction`), and the dashboard model views
  treat each bound as its own corpus. Eventually we want to **enumerate all bounds together** —
  one logical testset per model spanning its scopes — and the dashboard view should present the
  model as a single consolidated entity (aggregate counts across bounds), not a separate row/corpus
  per bound. (Raised 2026-10-21 while building the Utilities Alloy-models/gem5-builds/hooks tables.)

## Questions for Anna
- After git recovery: is cafe2's container the authority for the untracked June `.als`/`stage_pipeline.py`
  work, or the laptop? (Determines sync direction once git is healthy.)
- Do you want persistent-Claude-on-mini wired now, or only after git + mini-clone are settled?
- ~~**(2026-10-28)** Is instance (h) generated, and in which direction?~~ **Answered 2026-10-28 (Anna):** false negative (predict no alias, actually alias). Now generated by `STT_6_stl.als` + branch mode `stl_bypass`; gem5 hooks written in `gem5-hooks/stl/`, not yet built. → [`design/STL_SPECULATION.md`](../design/STL_SPECULATION.md)
- **(2026-10-28, STL)** Build the SimSpect-STL hooks into which build first (`/work/gem5-recon-modded` is the STT_6 build), and is a rebuild in place OK while other sweeps use that binary? Also: which threat model does that build's STT run in? Under STT's Spectre model, loads past an unresolved store are not protected (STT p5), so STL hits would be out of scope by construction. → [`design/STL_SPECULATION.md`](../design/STL_SPECULATION.md) §Open
- **(2026-10-28)** Table rows (a), (e), (f) (resolved-taken noop skip; unresolved but correctly predicted) aren't generated by `parsexml.py`: build them, or label them design intent?

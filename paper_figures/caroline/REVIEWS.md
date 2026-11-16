# Be-Caroline reviews (ISCA-27)

Each full review lives in its own file under `reviews/` (newest first per section). Act on the per-section **action items**; the reviews are the backing record (assessment, line-by-line directive audit, numbered fixes). A newer review of a section supersedes the older one: it restates every item still true and drops the fixed ones.

## Intro

- Action items: [REVIEW_ACTION_ITEMS_INTRO.md](REVIEW_ACTION_ITEMS_INTRO.md)
- [2026-11-15 18:12 — intro (7c1d69f)](reviews/2026-11-15_1812_intro.md): first full pass. The later re-reads (last pass, 2026-11-16) are in the action items.

## Background

- Action items: [REVIEW_ACTION_ITEMS_BACKGROUND.md](REVIEW_ACTION_ITEMS_BACKGROUND.md)
- [2026-11-15 23:13 — background (5f00495)](reviews/2026-11-15_2313_background.md): **current**. Ambiguity, uncited claims, missing refs, and what is missing from Background.
- [2026-11-15 19:25 — background (805e684)](reviews/2026-11-15_1925_background.md): superseded by the 23:13 review.

## Defense Specification (§3)

- Action items: [REVIEW_ACTION_ITEMS_MODEL.md](REVIEW_ACTION_ITEMS_MODEL.md)
- [2026-11-16 00:46 — model (f599ef0)](reviews/2026-11-16_0046_model.md): **current**. Polarity of the leakage predicate, the STT protection set vs the evaluated model, coverage of the six defenses, transmission criteria, LCM framing of §3.1 (candidate execution, spo≈tfo, consistency-predicate counterpart), provenance of the clauses, Table 1 and Fig. 2 whitespace.
- (An earlier review, started 2026-11-16, was stopped at Anna's request before it finished; no file.)

## Synthesizer (§4)

- Action items: [REVIEW_ACTION_ITEMS_SYNTHESIZER.md](REVIEW_ACTION_ITEMS_SYNTHESIZER.md)
- [2026-11-16 01:12 — synthesizer (263fda7)](reviews/2026-11-16_0112_synthesizer.md): **current**. The UNSAT/"every backbone" completeness claims vs the run record (STT/ReCon k6 unfinished, 6 footprint backbones with no Stage-1b graph, SPT's generator), no counts anywhere, the annotation/timing contradiction with §5, the missing x86 vocabulary (RMW, jmp/call, xmm) that Results rely on, unevaluated Pass 4 and store bypass, the duplicate timing paragraph, "Stage 3" in Table 2, Stage-1b term, CheckMate's minimal "security litmus test", Fig. 3 and Table 2 whitespace.

## Executor (§5)

- Action items: [REVIEW_ACTION_ITEMS_EXECUTOR.md](REVIEW_ACTION_ITEMS_EXECUTOR.md)
- [2026-11-16 01:16 — executor (d5c3d90)](reviews/2026-11-16_0116_executor.md): **current**. Checked every mechanism claim against the checkers (`check_ld.py`, `check_br.py`, `check_footprint.py`, `gem5_common.py`). Covers: the violation window as written vs as implemented (resolved-branch condition, squash vs resolution, UV6); the footprint criterion (CleanupSpec cleanup, InvisiSpec Futuristic mode, load vs instruction); cache states and timing vs the runs; §5 vs §3's new criteria and Table 2; the result vocabulary vs Results; the "probe" term clash; redundancy (one paragraph with no goal, one fully redundant); Fig. 4 placement and whitespace; Table 3 whitespace; paste-ready R-1 to R-3.

## Results

- Action items: [REVIEW_ACTION_ITEMS_RESULTS.md](REVIEW_ACTION_ITEMS_RESULTS.md) (audit of the results agent's commit `d9a466c`; no full review yet)

## Related Work

- Action items: [REVIEW_ACTION_ITEMS_RELATED.md](REVIEW_ACTION_ITEMS_RELATED.md)
- [2026-11-15 23:56 — related (9006a33)](reviews/2026-11-15_2356_related.md) — every characterization of a cited paper checked against the paper, §12 wording-audit items restated, missing related work with bib status, cross-section consistency with intro, Background, Results and Discussion

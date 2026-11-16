# Be-Caroline reviews (ISCA-27)

Each full review lives in its own file under `reviews/` (newest first per section). Act on the per-section **action items**; the reviews are the backing record (assessment, line-by-line directive audit, numbered fixes). A newer review of a section supersedes the older one: it restates every item still true and drops the fixed ones.

## Intro

- Action items: [REVIEW_ACTION_ITEMS_INTRO.md](REVIEW_ACTION_ITEMS_INTRO.md) (rewritten 2026-11-16 08:20: 41 items, 8 possible cuts of about 14 lines, 12 decisions)
- [2026-11-16 08:20 — intro (9e48df1)](reviews/2026-11-16_0820_intro.md): **current**, second pass on the abstract, §1 and Fig. 1. Overclaims (five prior bugs, "first" vs AMuLeT's "state-of-the-art", the race at "above one cycle", efficiency "because" targeting, UV4 as new), Fig. 1's STT example vs §2.2/§3.3 and Protean Tab. I, tone toward prior work ("luck", "spurious", "false leaks", "advertised", "underreported") and defensive phrasing, abstract terms ("high-level", "compact", "per bug"), section refs and pinpoints, a possible-cuts tier.
- [2026-11-15 18:12 — intro (7c1d69f)](reviews/2026-11-15_1812_intro.md): superseded by the 2026-11-16 08:20 review (first full pass; its live items are folded into the current action items).

## Background

- Action items: [REVIEW_ACTION_ITEMS_BACKGROUND.md](REVIEW_ACTION_ITEMS_BACKGROUND.md) (rewritten 2026-11-16 08:25: 16 items, 7 possible cuts of about 7 lines, 3 decisions)
- [2026-11-16 08:25 — background (9e48df1)](reviews/2026-11-16_0825_background.md): **current**, second pass. The unsupported wSNI corollary, undefined "standard contracts" and an uncited STT store exclusion in the projection argument, "speculation primitive" in two senses, a two-goal paragraph and a doubly defined adversary model, pinpoints (Serberus, LCM), Oxford commas, a possible-cuts tier.
- [2026-11-15 23:13 — background (5f00495)](reviews/2026-11-15_2313_background.md): superseded by the 2026-11-16 08:25 review.
- [2026-11-15 19:25 — background (805e684)](reviews/2026-11-15_1925_background.md): superseded by the 23:13 review.

## Defense Specification (§3)

- Action items: [REVIEW_ACTION_ITEMS_MODEL.md](REVIEW_ACTION_ITEMS_MODEL.md)
- [2026-11-16 08:29 — model (9f1c1e8, quotes re-checked at 1fb5771)](reviews/2026-11-16_0829_model.md): **current**, second pass. The criterion attached to two objects (predicate vs leakage contract vs defense), "the other five specifications" (there are four), ReCon's execution contract vs the two evaluated ReCon models, SPT's register protection and "conservative", "test"/"trace"/synthesizer/Inspector prefetches in §3, spo undefined, "leak" in Fig. 2, §3.3's two goals, pinpoints (STT §6.1, SPT §9.1), Oxford commas, In/Out hyphenation, possible cuts (Fig. 2 caption; Table 1 optional).
- [2026-11-16 00:46 — model (f599ef0)](reviews/2026-11-16_0046_model.md): superseded by the 08:29 review. Polarity of the leakage predicate, the STT protection set vs the evaluated model, coverage of the six defenses, transmission criteria, LCM framing of §3.1 (candidate execution, spo≈tfo, consistency-predicate counterpart), provenance of the clauses, Table 1 and Fig. 2 whitespace.
- (An earlier review, started 2026-11-16, was stopped at Anna's request before it finished; no file.)

## Synthesizer (§4)

- Action items: [REVIEW_ACTION_ITEMS_SYNTHESIZER.md](REVIEW_ACTION_ITEMS_SYNTHESIZER.md)
- [2026-11-16 08:29 — synthesizer (9f1c1e8, quotes re-checked at 1fb5771)](reviews/2026-11-16_0829_synthesizer.md): **current**, second pass. SPT's tests come from a flat capped enumeration with its own Stage-2 table (not Stages 1a–1b), the false "every backbone gets a test" (6 footprint backbones have no Stage-1b graph), Pass 6 vector routing vs the corpora and the paired design, Pass 2's branch forms (test/cmp on every branch), "each is an asm sideeffect block" vs branches, independent reasons for the eight-instruction bound, RR/RC/RS, connectivity, random order, both directions, register naming and -O2, terms ("the leak", "abstract", "PC", vector vs floating-point), Fig. 4's graph vs Fig. 2, possible cuts (opener, list, Fig. 3 caption and one-pane option, Fig. 4 annotation).
- [2026-11-16 01:12 — synthesizer (263fda7)](reviews/2026-11-16_0112_synthesizer.md): superseded by the 08:29 review. The UNSAT/"every backbone" completeness claims vs the run record (STT/ReCon k6 unfinished, 6 footprint backbones with no Stage-1b graph, SPT's generator), no counts anywhere, the annotation/timing contradiction with §5, the missing x86 vocabulary (RMW, jmp/call, xmm) that Results rely on, unevaluated Pass 4 and store bypass, the duplicate timing paragraph, "Stage 3" in Table 2, Stage-1b term, CheckMate's minimal "security litmus test", Fig. 3 and Table 2 whitespace.

## Executor (§5)

- Action items: [REVIEW_ACTION_ITEMS_EXECUTOR.md](REVIEW_ACTION_ITEMS_EXECUTOR.md)
- [2026-11-16 08:22 — executor (1e6a9ea)](reviews/2026-11-16_0822_executor.md): **current**, second pass. The window's two meanings of "resolution" (W-1, with STT §6.4.2 as an independent reason for the squash end), the resolution-to-squash scan's real scope, the window rule false for InvisiSpec's Futuristic runs, "count changes" vs CleanupSpec's undo and InvisiSpec's D-TLB, the cache-state reasons (ReCon warm, random draw), hold vs delay, the hit definition, stale Discussion statements about the executor (store check, store bypass), Fig. 5 v7 kept brief, 7 possible cuts.
- [2026-11-16 01:16 — executor (d5c3d90)](reviews/2026-11-16_0116_executor.md): superseded by the 08:22 review. Checked every mechanism claim against the checkers (`check_ld.py`, `check_br.py`, `check_footprint.py`, `gem5_common.py`). Covers: the violation window as written vs as implemented (resolved-branch condition, squash vs resolution, UV6); the footprint criterion (CleanupSpec cleanup, InvisiSpec Futuristic mode, load vs instruction); cache states and timing vs the runs; §5 vs §3's new criteria and Table 2; the result vocabulary vs Results; the "probe" term clash; redundancy (one paragraph with no goal, one fully redundant); Fig. 4 placement and whitespace; Table 3 whitespace; paste-ready R-1 to R-3.

## Results

- Action items: [REVIEW_ACTION_ITEMS_RESULTS.md](REVIEW_ACTION_ITEMS_RESULTS.md)
- [2026-11-16 05:51 — results (3946771)](reviews/2026-11-16_0551_results.md): **current**. First full review of §6 and its seven figures. Numbers traced to EVAL_MANIFEST, the 2026-11-16 snapshot and the cited papers. Key: UV6 is not an Inspector hit as implemented (W-1/PT-1) and has no STT count; UV4 is A-UV6 by AMuLeT's own patch; UV3 vs Kvalsvik; the A-KV1 cite misreads InvisiSpec fn. 2; A-UV3 (a store bug) vs A-KV3; "AMuLeT's own campaigns" are our runs; UV1's 98/100 is a controlled re-run; no results reported for SPT or ReCon itself; targeting attribution without ablation; about 0.85 page recoverable (delete Figs. 6 and 9, trim captions, run-in heads).
- (Earlier: the numbers audit of the results agent's commit `d9a466c`, kept in the action items file until now; its open items are folded into the current action items, its fixed ones listed under "Not carried over".)

## Related Work

- Action items: [REVIEW_ACTION_ITEMS_RELATED.md](REVIEW_ACTION_ITEMS_RELATED.md)
- [2026-11-16 08:22 — related (1e6a9ea)](reviews/2026-11-16_0822_related.md): **current**, second pass. No Background repetition left; open characterizations re-checked against AMuLeT, Protean, Pensieve, SpecCheck, rtl2µspec, RTL2MµPATH and Kvalsvik's thesis; new: "each hit names its transmitter" overclaims for the footprint criteria, AMuLeT's predictor state stated in its own words (§3.2), "closest" not "only" (R-6), our STT builds vs the pending-squash fix (R-9), tone of the AMuLeT contrast here and in Results/Discussion, 6 possible cuts.
- [2026-11-15 23:56 — related (9006a33)](reviews/2026-11-15_2356_related.md): superseded by the 08:22 review — every characterization of a cited paper checked against the paper, §12 wording-audit items restated, missing related work with bib status, cross-section consistency with intro, Background, Results and Discussion

## Discussion And Limitations (§8) and Conclusion (§9)

- Action items: [REVIEW_ACTION_ITEMS_DISCUSSION.md](REVIEW_ACTION_ITEMS_DISCUSSION.md) (19 items, 12 decisions; paste-ready rewrites R-D1 to R-D9 and a full replacement Conclusion inside the items)
- [2026-11-16 13:52 — discussion + conclusion (4b017ee)](reviews/2026-11-16_1352_discussion.md): **current**, first review. Covers: the window rule's non-sequitur justification and the race scan's coverage; Stage 1a exhaustiveness (ReCon unfinished; the Conclusion has it backwards); R-SA-13 listed as unreachable although the pipeline reaches it; a stale store-check claim; a missing specifications/trust-base paragraph (SPT conservative, ReCon store shadows unexercised and ReCon bugs from STT's specification, Futuristic builds vs Spectre specifications); threat-model citations for the harness argument and the new branch-predictor sentence (STT §6.4.1); Protean as the source of the missed pending-squash bug; redundancy with §4–§6; bold run-in heads; deletion of ¶9, the three optional paragraphs and the hidden to-do list; a Conclusion rewritten in the style of Helium's and Protean's (contributions and results only, 127 words).

## References pass

- Action items: [REVIEW_ACTION_ITEMS_REFS.md](REVIEW_ACTION_ITEMS_REFS.md) (2026-11-16, ISCA-27 `c0cdc5b`): missing section/figure refs, citation pinpoints, wrong pinpoints and stale refs in §§2–6 and the captions they input; 41 items (7 Background, 5 Model, 5 Synthesizer, 3 Executor, 19 Results, 2 captions), each pinpoint checked against the local PDF.

## Design-decision justification

- Action items: [REVIEW_ACTION_ITEMS_JUSTIFICATION.md](REVIEW_ACTION_ITEMS_JUSTIFICATION.md) (2026-11-16, ISCA-27 `f927bc0`): every design decision in §§3–5, Table 3 and the Discussion paragraphs that justify a choice (67), each classified as independent, independent but under-supported, bug-only, or no reason, with an independent justification from a source read in the pass and a `\reviewnote{}` insertion point for every flagged one (34 items, 6 decisions, full decision table). Covers the bug-justified timing delays, cache states, race scan and commit-to-IEW delay; back-references from Results bugs to mechanisms; the paired vector-register design.

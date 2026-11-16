# BF4: split (line-crossing) speculative loads, DoM R-SA-14 + SpecLFB SL-1

Status 2026-11-10 (agent BF4): proposed figure built and compiling. New files only in `~/trippel/ISCA-27/tikz/`: `prop_splitload_8pt.tex` (body + caption, label `fig:splitload`), `_standalone_prop_splitload.tex` (preview wrapper, inputs `sscolors` and the body) and `_standalone_prop_splitload-1.png` (300 dpi). TikZ picture is 240.4pt wide (-2 to 238.4pt), all text 8pt via `\figfont`. No paper text edited, no git writes; compiled in the session scratchpad.

## What it shows

Top: the abstract test in the graph notation of reconstl/squashrace: i0 unresolved mispredicted `Branch_n`; tan speculative band over i1 `r1 <- not r0` (r0 = 0, so r1 = -1), i2 the split load `r2 <- [sp+r1]` (8 bytes at sp-1) and i3 a non-split speculative load that misses. Middle: a byte strip with the cache-line boundary at sp, line 0x7500 (red, filled) and line 0x7540, i2's 8 bytes framed, fragment 1 = 0x753f (1 B) and fragment 2 = 0x7540-46 (7 B). Bottom: two lanes. Left (i3, lavender = protected): the request sent to L1 is marked (DoM L1-only, SpecLFB unsafe), its L1 miss is refused, no MSHR, no fill. Right (i2): only the parent request is marked (SpecLFB) or none (DoM), fragments go out unmarked, the miss allocates an MSHR and fills line 0x7500 before the squash (red). Blue defense-specific box: the code lines.

## Facts and sources

DoM: only `SingleDataRequest::buildPackets` sets L1-only for speculative DoM loads, `lsq.cc:1443-1446`; `SplitDataRequest::buildPackets` `:1470-1515` never does; L1-only miss refusal `mem/cache/base.cc:462-471` (cafe2 `/work/gem5-recon-modded/src`). Trace inst-005391 cold: sn:3057 misses `[753f]` and `[7540:7546]` at 11154000, fills 0x7500/0x7540 at 11218000/11223000, squash 13654000; non-split speculative loads sn:3070-3079 refused. Counts: cold split, 70/76 runs, all 140 fragments miss and fill in window; control 957 non-split speculative fragments, all `l1only_fail` (up to 12 may be forwards). Source: `wiki/findings/audits/2026-11-08/SOURCE_AUDIT_RECON.md` 'R-SA-14 gem5 check' (lines 365-392); claudelog 2026-11-09 18:40.

SpecLFB: flags only on `_mainReq` (`lsq.cc:1153-1155`), packets built from fragment `_reqs` (`:1421-1423`), single-line path tags the sent request (`:1049-1052`), AMuLeT SpecLFB AE tree. inst-055160 not_taken seq 3072: fragment 0x753f size 1 misses `usl=0`, `L2:fill`/`L1D:fill line=0x7500` at 15557000/15567500, fnc_retire 20423500; fragment 0x7540 size 7 hits; seqs 3075-3084 same flags, `bounced=1`. Source: `wiki/findings/audits/2026-11-08/SOURCE_AUDIT_CLEANUPSPEC_SPECLFB.md` 'SL-1' (lines 21-46) and 'SL-1 gem5 check' (48-62); claudelog 2026-11-09 06:05; BUGS.md rows SL-1 (line 51), R-SA-14 (line 76).

## LaTeX caption (already in the body file)

\textbf{A speculative load that crosses a cache line escapes the defense} (DoM in ReCon's gem5 and SpecLFB). Top: the test in the notation of Table~\ref{tab:execvocab}; i1 sets an index register to $-1$, so the speculative load i2 reads 8 bytes at $sp-1$, one byte below the line boundary at $sp$. gem5 splits i2 into one request per line. Both defenses mark only a request that stays in one line (i3, lavender), and refuse its L1 miss. i2's fragments go to the cache unmarked, so fragment~1 misses and fills line 0x7500 inside the violation window (red). Under DoM (test inst-005391, no cache warm-up) the split load fills both lines in 70 of 76 runs, while 957 non-split speculative fragments are all refused; under SpecLFB (inst-055160) the fragment fills the L1D and the L2 while four non-split loads with the same flags are refused.

## Where it goes

`sections/results.tex`, subsection "Unknown bugs found by \toolname{}": a new subsubsection for split loads (e.g. after UV5, before UV6 at line 69) with the line `\input{tikz/prop_splitload_8pt}% split-load bypass, DoM R-SA-14 + SpecLFB SL-1 (2026-11-10)`. Anna pastes the line and the prose; nothing was edited.

## Open questions (DECIDE for Anna)

- DECIDE whether these count as found bugs in the paper: both are masked in their campaigns (E9: every split-load record is already an L1-hit transmitter hit; E14: inst-055160 also has a UV6 fill, so no SL-1-only hit). Options: (a) present as "reached by our tests, masked", (b) source-audit finding only, (c) leave out until the DoM miss criterion DECIDE (URGENT_TODO) is settled. Recommendation: (a), with the masking stated in the prose.
- The address is not secret-dependent (sp-1 comes from an index of -1), so the figure shows a defense bypass, not a secret footprint; the caption says nothing about a secret, keep it that way unless a secret-indexed split test is built.
- The figure merges two different gem5 trees with different line numbers (`lsq.cc:1443` is ReCon's tree, `:1153` is SpecLFB's); check the blue box reads clearly enough, or split it into two lines with tree names.
- "SpecLFB: unsafe" in the left lane is shorthand for `setUnsafe()` + `setHitUSL()`; DoM's 70/76 is a cold-cache rerun, not the campaign (warm: 60/76 fill line 0x7500). Confirm the cold count is the one to cite.
- The test is drawn abstractly (`[sp+r1]`; the real inst-005391 load is `mov (%r10,%rdi,1),%rdi` after `not %rdi`), not from one XML; confirm abstract is acceptable for a bug figure or ask for one drawn from inst-005391.xml.

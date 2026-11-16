# Figure heights (FIG-H, 2026-11-11)

How I measured: in a private temp copy of ~/trippel/ISCA-27, using the main.tex preamble (acmart sigconf, review), I typeset each figure file in a 241.15pt-wide box (the real `\columnwidth` after `\maketitle`) and read `\ht+\dp`. "Total" includes the caption; "graphic" is the same box with `\caption` emptied. ACM column text height = **626pt** (`\textheight`; `\textfloatsep` = 15pt plus 8pt). 40% of the column = **250pt**. Every build had 0 errors. pipeline_full_8pt1col* was skipped (FIG-B2 owns it).

Result: almost every figure is over 250pt once you count its caption. For most of them the caption is 100–210pt of that, so the graphic is not the main lever. Captions are paper text, so cutting them is your call (see the last section). I made shorter NEW versions of the six figures whose graphics were tallest and could be tightened without dropping content. With the four live swaps the temp paper build goes from 18 to 17 pages (0 errors).

## Every figure (pt; flag = total > 250pt)

| figure (tikz/) | live? | total old | graphic old | new file | total new | graphic new | flag / note |
|---|---|---|---|---|---|---|---|
| intro_threelayer_v2_8pt | live (intro) | 272 | 205 | (none) | | | slightly over; caption 67 |
| intro_threelayer_v3_8pt | proposed | 262 | 195 | (none) | | | slightly over |
| execvocab_v2_8pt (table) | live (model) | 153 | 97 | (none) | | | ok |
| execvocab_v3_8pt (table) | proposed | 203 | 147 | (none) | | | ok |
| dataflow_8pt | live (model) | 244 | 114 | (none) | | | ok; caption 130 |
| dataflow_v2_8pt | proposed | 240 | 110 | (none) | | | ok |
| relaxation | live (pipeline) | 525 | 381 | relaxation_v2_short | 396 | 252 | FLAG; caption 144 |
| relaxation_v2 | proposed | 469 | 325 | relaxation_v2_short | 396 | 252 | FLAG |
| interleave_v4_8pt | live (pipeline) | 387 | 177 | (none) | | | FLAG, caption is 210 of it |
| instrtable_v2_8pt (table) | live (pipeline) | 481 | 337 | instrtable_v2_short | 421 | 277 | FLAG; caption 144 |
| resolutiontiming | live (pipeline) | 309 | 154 | (none) | | | FLAG, caption 155 |
| checkerwindow_v4_8pt | live (pipeline) | 339 | 217 | (none) | | | FLAG, caption 122 |
| reconstl_v2_8pt | live (results) | 432 | 266 | reconstl_v2_short | 411 | 245 | FLAG; caption 166 |
| recon_otb_v2_8pt | live (results) | 376 | 210 | (none) | | | FLAG, caption 166 |
| recon_otb_v3_8pt | proposed (FIG-C) | 398 | 210 | (none) | | | FLAG, caption 188 |
| squashrace_v2_8pt | live (results) | 466 | 322 | squashrace_v2_short | 437 | 293 | FLAG; caption 144 |
| firstdet_bars_v2_8pt | live (results) | 315 | 138 | (none) | | | FLAG, caption 177 |
| bugtable_v4_8pt (table) | proposed (FIG-C) | **630** | 552 | (not touched, FIG-C2 owns it) | | | **does not fit a column (630 > 626pt)**; needs table* or a split |
| prop_csem_8pt | proposed | 350 | 195 | (none) | | | FLAG, caption 155 |
| prop_jmpshadow_8pt | proposed | 292 | 170 | (none) | | | FLAG, caption 122 |
| prop_nda_stl_8pt | proposed | 425 | 270 | prop_nda_stl_short | 406 | 251 | FLAG; caption 155 |
| prop_rsa13_sse_8pt | proposed | 400 | 245 | (none) | | | FLAG, caption 155 |
| prop_s1_xmm4_8pt | proposed | 367 | 223 | (none) | | | FLAG, caption 144 |
| prop_splitload_8pt | proposed | 452 | 297 | prop_splitload_short | 439 | 284 | FLAG; caption 155 |
| prop_spt_backuntaint_8pt | proposed | 407 | 285 | (none) | | | FLAG; already at an 11.5pt row pitch, so cutting more means dropping one of its three panels (your call) |

## The \input swaps

| where (line numbers as of 2026-11-11; another agent is editing sections/, so match the text) | change |
|---|---|
| sections/pipeline.tex:46 | `\input{tikz/relaxation}` -> `\input{tikz/relaxation_v2_short}` (or, if you already took relaxation_v2: `relaxation_v2` -> `relaxation_v2_short`) |
| sections/pipeline.tex:103 | `\input{tikz/instrtable_v2_8pt}` -> `\input{tikz/instrtable_v2_short}` |
| sections/results.tex:53 | `\input{tikz/reconstl_v2_8pt}` -> `\input{tikz/reconstl_v2_short}` |
| sections/results.tex:69 | `\input{tikz/squashrace_v2_8pt}` -> `\input{tikz/squashrace_v2_short}` |
| wherever you place the proposed figures | `prop_splitload_8pt` -> `prop_splitload_short`, `prop_nda_stl_8pt` -> `prop_nda_stl_short` |

Every new file has `tikz/_standalone_<name>.tex` and `tikz/_standalone_<name>-1.png` next to it. All new files are untracked in ~/trippel/ISCA-27; nothing is committed and no existing file was changed.

## What each short version cuts (no facts dropped, all text still 8pt, captions unchanged)

| new file | what changed |
|---|---|
| relaxation_v2_short | Panes (a)–(c) use a 16pt row pitch instead of 22pt, with 22pt between panes instead of 26pt. The ddi/rf edge labels are drawn once, in the backbone (d); the same edges in (a)–(c) are unlabeled. The gray rf label on (b)'s removed edge moved right of its dashed edge. The `\rlAlab` RO-vs-RS knob is kept. Graphic 325 -> 252pt. |
| instrtable_v2_short | The Stage 2 and Stage 3 columns are merged into one 150pt column. Each cell leads with bold "Stage 2:" … "Stage 3:", so the prose wraps in fewer lines. Rule padding 4 -> 3pt. Every cell's text is identical. Graphic 337 -> 277pt. |
| reconstl_v2_short | Spacing only: graph row pitch ~15 -> 13.5pt, graph-to-trace gap 36 -> 30pt, trace rows 32 -> 28pt, rule box 4pt closer. Graphic 266 -> 245pt. |
| squashrace_v2_short | Spacing only: graph pitch 15 -> 14pt, extra gaps 7 -> 5pt, timeline rows 30 -> 26pt, graph-to-timeline 38 -> 30pt, rule box 4pt closer. Graphic 322 -> 293pt. |
| prop_splitload_short | Spacing only: graph pitch 14 -> 13pt, memory strip 6pt closer, lane headers 3pt closer, box gaps 8 -> 6pt, rule box 2pt closer. Graphic 297 -> 284pt. |
| prop_nda_stl_short | Spacing only: graph 3pt closer to the legend, trace row pitch 18 -> 15pt, trace 2pt closer, rule box 3pt closer. Graphic 270 -> 251pt. The 1.4pt overfull in its standalone is already in the original. |

## Not cut, and why

I kept the blue "rule" boxes in reconstl, squashrace, nda_stl and splitload. Each is the only defense-specific (blue) element and the target of the figure's "Defense-specific" legend, and reconstl's caption refers to it ("(blue)"). Moving a box into the caption would save only ~20pt net (the caption grows by ~25pt) and would lose the palette cue.

## Decisions for Anna

- DECIDE: caption length. Captions are 100–210pt in most figures, the biggest remaining lever (interleave_v4_8pt 210, recon_otb_v3 188, firstdet 177, reconstl 166). Option (a): trim each caption to 2–3 sentences and move the trace detail to the body text. Option (b): keep them, accept ~1 figure per column. Recommendation: (a) for interleave and firstdet first.
- DECIDE: bugtable_v4_8pt is 630pt, more than the 626pt column, so as a single-column `table` it cannot be placed. Options: `table*` (two columns), split it into confirmed and candidate tables, or drop rows. This is FIG-C2's file; I flagged it and did not touch it.
- DECIDE: prop_spt_backuntaint (407pt) can only get shorter by dropping one of its three panels (a/b/c), or by keeping two and moving the third to the text.

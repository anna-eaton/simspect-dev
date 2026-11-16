# FIG-B: pipeline and methodology figures (2026-11-10, cut short by deadline)

Status: audit only. I wrote no new tikz files, made no edits in ~/trippel/ISCA-27, and ran no git writes. Compiles ran in a private copy (scratch figB.2rrs) under acmart sigconf with \columnwidth = 241.15pt. No live figure has an overfull hbox.

## Measured widths

| figure | width | notes |
|---|---|---|
| pipeline_full_8pt1col | 241.0pt | 610pt tall; figure plus caption is about 706pt |
| interleave_v4_8pt | 240.2pt | OK |
| checkerwindow_v4_8pt | 239.6pt | OK |
| resolutiontiming | 240.2pt | OK |
| instrtable_v2_8pt | table at \columnwidth | OK |

## Problems found

- pipeline_full_8pt1col (sections/model.tex:69): in the rendered PNG, the text of slabs 3b ("propagation") and 3c ("transmit") wraps to a second line and runs over the bottom border of its box. The fix: give those slabs a larger minimum height, or shorten the text to one line. The figure is also 610pt tall and, with its caption, about 706pt; this is over the 626pt \textheight that my harness reported for sigconf, so the float may not fit in a column. Verify that against a full compile of the paper in a temp copy. Duplicates: tikz/pipeline_full is only commented out (sections/pipeline.tex:16), so it is not live. tikz/pipeline_full_8pt.tex (double wide) is unused; keep one of the two.
- interleave_v4_8pt: the caption writes $f_0$, $f_1$, $r_0$ with subscripts, but the figure says f0/f1/r0, and the subscripts would set below 8pt in the figure. DECIDE (Anna): the mechanism the figure shows is out of date. Chain interleaving is off in every eval config, and the getOldestTaint result comes from the fanout v2 OTB merge (pipeline.tex:82 auditnote; VOCAB_TABLES.md:369). Options: (a) redraw the figure as the OTB merge (second load after a resolved branch, xor into the transmitter address), or (b) keep this figure but caption it as a capability. Recommendation: (a).
- checkerwindow_v4_8pt: DECIDE (Anna). The figure and its caption close the window at the branch's resolution, while instrtable row 4 and check_ld/check_br/check_other use lc_retire < signal < fnc_retire (VOCAB_TABLES.md:828,859; CLAUDE.md). One of the two must change so the paper agrees with the code.
- resolutiontiming, instrtable_v2_8pt: not reviewed visually (TODO). Widths are fine and the font grep found no \tiny, \scriptsize or \footnotesize.

## TODO for next pass

Write pipeline_full_8pt1col_v2.tex with the slab fix plus a height trim, and interleave_v5_8pt.tex once Anna decides. Render the remaining PNGs and check them at high zoom. The harness to reuse is in mk.sh in the scratch copy, which renders a figure as a non-float at 241pt.

## FIG-B2 fixes (2026-11-11)

New files only, all compiled in a private temp copy (scratch figB2.VtS6, acmart sigconf harness at 241.15pt). No existing tikz file was modified (tikz/pipeline_full_8pt1col.tex still shows only Anna's own uncommitted edit). No git writes.

pipeline_full_8pt1col_v2: new tikz/pipeline_full_8pt1col_v2.tex, plus tikz/_standalone_pipeline_full_8pt1col_v2.tex and its -1.png. It is based on Anna's current working-tree file, with the same stages (1a, 1b, 2, 3), slabs 1-3c, 4/1/2'/3, 7 passes, and the same caption and labels. Every slab is now one line, which fixes the 3b/3c overrun. The wording is shortened: 2 "Defense-agnostic minimality (load-bearing)", 3b "Protection set and its propagation", 3c "Leakage contract: transmitting operands", 2' "Looser minimality ⇒ more flexible graphs", 4 "Pin: graph contains a target Stage-1a graph". Other changes: one-line language tags "(Alloy relational language): …"; the Alloy Analyzer pill is one line, "Alloy Analyzer (Kodkod + SAT) + bound"; output captions are two lines each (Stage 1b's output drops "defense-specific" and "parallelizable"; Stage 2's reads "Per branch mode × interleave variant"); the Stage 2 pass pitch goes from 11.9 to 10.4pt; and "(gem5)" moves into the Stage 3 title, which pulls Stage 3 up 6pt. The figure is now 241.0 × 507pt, down from 610pt. With the caption and its current URGENT note it is about 630pt (borderline against the 626pt textheight); with notes hidden it is about 570pt. Width is 241.0pt and nothing in the figure is set below 8pt. One-line change for Anna, at sections/model.tex:69: `\input{tikz/pipeline_full_8pt1col}` → `\input{tikz/pipeline_full_8pt1col_v2}`. Please check the shortened wordings above.

interleave_v4b_8pt: new tikz/interleave_v4b_8pt.tex, plus tikz/_standalone_interleave_v4b_8pt.tex and its -1.png. The figure labels now read $f_0$, $f_1$, $r_0$, $m_0$ (including "$f_1$'s register" in the step-5 note), set through a new \ilv macro whose subscript digit is 8pt upright, so nothing falls below 8pt. Layout and caption are unchanged, and the size is 240.2 × 166pt. I used the name v4b because v5 is reserved for the redraw still awaiting Anna's decision (above). One-line change, at sections/pipeline.tex:77: `\input{tikz/interleave_v4_8pt}` → `\input{tikz/interleave_v4b_8pt}`. Caption follow-up for Anna: the caption still writes "protected $m0$"; change it to $m_0$ to match.

resolutiontiming and instrtable_v2_8pt: checked visually in the 250dpi renders. Neither has an overrun or text under 8pt, so I made no new versions. resolutiontiming uses r0/m1 without subscripts, and so does its caption, so the two agree. The open caption question ("no violation"/"violation") is still Anna's decision (pipeline.tex:123-127).

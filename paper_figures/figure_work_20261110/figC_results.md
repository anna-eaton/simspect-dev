# FIG-C: results figures audit (2026-11-10, stopped at coordinator deadline)

Status: audit done for all six results figures; NO new tikz files written (deadline hit before edits). No changes to the paper repo. Rendered in a private temp copy with the ACM preamble from main.tex.

Live inputs: `sections/results.tex:55` reconstl_v2_8pt, `:61` recon_otb_v2_8pt, `:72` squashrace_v2_8pt, `:76` firstdet_bars_v2_8pt; bugtable_v3_8pt is commented out (`:86`). The second \input of reconstl/recon_otb/squashrace (`:166/:172/:177`) are comments ("moved to UV2/UV3/UV6"), so each figure appears once. That is intended, nothing to fix.

## firstdet_bars_v2_8pt (+ _body): OK, numbers current

Every bar value, AMuLeT label and ratio matches EVAL_MANIFEST "Complete run" plus the same-estimator table (UV1 1,655x→1,700x, UV3 140x, UV4 2,140x→2,100x, UV5 17.8x→18x, UV6 1,278x→1,300x, jmp 2,594x→2,600x; AMuLeT (896,001)/(K+1) with K = 270/236/4/4/150/47). The ~18x correction (DG-2) is applied. No overfull box, all text \figfont 8pt. No change needed. The paper copy is newer than `experiments/2026-11-10_footprint_vs_amulet/results/figure_final/` (it adds error bars), so that frozen copy is stale. TODO: re-copy it if it should match the paper.

## recon_otb_v2_8pt: caption has a STALE claim (most important fix)

The caption ends "This test was built by hand; our bounded enumeration does not reach this shape within its instance cap." BUGS.md:61 (R-SA-8) now records generated hits: ☑ 2026-11-08, the fanout_v2 OTB merge, 100/100 vs 0/100. claudelog 2026-11-10 16:55 (e2-losttaint) adds E2 br_x inst-016600, an untargeted hit with OTB off, through x86 `mov` reading its destination. Caveat: the targeting audit (claudelog 2026-11-10 02:10) flags the OTB merge as targeted. So how to word this is Anna's decision (DECIDE). A suggested sentence: "The figure uses a hand-built test; generated tests also hit this bug, including one with the targeted merge turned off, where an x86 \texttt{mov} that reads its destination supplies the older source."

Second issue: the listing flags i0 and i1 "committed", as in the Alloy XML (lc = pc1, ann.json). The note and the caption, though, call i1 "speculative under branch i0" and an "older tainted source". In gem5, i0 is a slow-resolving branch, so i1 does run speculatively. Readers will see a contradiction. Anna should decide whether to relabel (e.g. "committed in the model, resolves at cycle 0"). Minor: the caption writes $r_0$/$r_1$ while the figure writes r0/r1. Width OK, 8pt OK.

## reconstl_v2_8pt: OK

Cycles 5/6/7/9 match `wiki/findings/bug/recon_SLF_stlf_bypass/trace_excerpt_sn600.txt` (2681500/2682000/2682500/2683500, base 2679000, /500). Width and font OK. No change.

## squashrace_v2_8pt: window frame vs decided rule (check)

The file header says the window rule was decided 2026-11-08 ("a branch counts as unresolved until its squash lands; draw the violation window to the squash at cycle 81"). The rendered figure and caption still draw and describe the "Committed window (lc retires to fnc retires)", 0 to 261. TODO: a v3 that frames the window at the squash (81) and rewords the caption sentence. It is a framing call for Anna, so I did not do it. I did not re-verify the ticks against provenance.json (TODO). Width and font OK.

## bugtable_v3_8pt (hidden): stale, too small, too wide; needs a v4

(1) It uses `\footnotesize`, which is 7pt in acmart: violates the 8pt rule. (2) It overflows the table* by 9.7pt (columns sum to 516pt). (3) By Anna's 2026-11-03 request it has no "found by" column. The coordinator brief asks for one, which conflicts with her request: DECIDE. (4) Many rows are stale against BUGS.md "State of the world" and the complete run. UV3 and UV5 say "AMuLeT-reported, not reproduced", but they are now hit: UV3 1,861/50,232 and UV5 4/50,232 (EVAL_MANIFEST complete run). Also stale: UV4 (599/50,232), UV1 (2,002/4,000), UV6 (861/4,000), and OTB "not enumerated" (now generated, see above). (5) It is missing confirmed bugs: STT S1 xmm4 taint drop (source audit, then generated with FP routing; targeting audit says BUGS.md:55 "simspect tests" is wrong); SpecLFB jmp-shadow (SimSpect runs; 555/4,000; AMuLeT's own runs also trigger it 47 times); CleanupSpec CS-EM (hooks-v2 runs); ReCon R-SA-13, R-SA-16, R-SA-2/3/4 (hand tests); NDA R-SA-18; DoM R-SA-14 and R-SA-15; SPT A1/A2/A3 (hand-edited tests) and A5 (race); SL-1 (reached, masked); Mosier pending-squash (real, not hit). Found-by attributions are in BUGS.md:31-84, column 3. TODO: write `tikz/bugtable_v4_8pt.tex` from those rows, at \figfont, in one column or a width-checked table*.

## Hard decisions for Anna

- OTB caption: how to state that generated tests reach it, given the targeted-merge caveat.
- OTB listing: i0/i1 shown "committed" vs described as "speculative".
- Race figure: frame the window to the squash (81) as the 11-08 rule says, or keep lc→fnc.
- Bug table: keep a "found by" column (brief) or drop it (Anna 11-03); fold walk-order into UV6 or list it separately.

## Update after the coordinator's correction: new files written (all compile in a private temp copy, 0 overfull, all text 8pt)

- `ISCA-27/tikz/bugtable_v4_8pt.tex` (+ `_standalone_bugtable_v4_8pt.tex`, `_standalone_bugtable_v4_8pt-1.png`). A single-column `table` (241pt), every text \figfont 8pt, 29 rows over 7 defense groups, with a Found-by column. Rows come from BUGS.md "State of the world"; UV1/UV3/UV4/UV5/UV6/jmp counts come from the EVAL_MANIFEST complete run. The source comments say what was left out (candidates and by-reading-only items) and why. S1 is attributed to "audit", which follows the targeting audit and not BUGS.md:55. Walk-order is folded into UV6, per BUGS.md:49 (Anna). The pending-squash row says "upstream fix"; the bib has no entry for that report, so it has no cite. New label `tab:bugsv4`.
- To use it, change `sections/results.tex:86` from `% \input{tikz/bugtable_v3_8pt}...` to `\input{tikz/bugtable_v4_8pt}`.
- `ISCA-27/tikz/recon_otb_v3_8pt.tex` (+ standalone, -1.png) is recon_otb_v2_8pt with only the caption's last sentence replaced: generated tests now reach R-SA-8, through the merge step and one test without it. The label stays `fig:otb`.
- To use it, change `sections/results.tex:61` from `\input{tikz/recon_otb_v2_8pt}` to `\input{tikz/recon_otb_v3_8pt}`.
- firstdet: no new version needed. The numbers are sourced and current (18×), and `_standalone_firstdet_bars_v2-1.png` (16:50) is newer than the body (16:49).
- Still TODO: squashrace v3 (window framed to the squash at 81: Anna's call), and the OTB listing's committed flags.
- Numbers I could not source: none in the new files. The "98/100" (S1), "121/123" (R-SA-13) and "8/467" (NDA) cells are BUGS.md's own counts from different campaigns, not the footprint corpus, so the caption's K/N definition covers only the AMuLeT-bug rows plus jmp. Anna may want those three cells marked or reworded.

## v4 fit options (2026-11-11)

bugtable_v4_8pt renders 630pt tall (one column is 626pt), so it cannot sit in a column. Two new options, both with the same 23 table rows and cells as v4 (verified by diffing the row lines), all text \figfont 8pt, same palette (blue group headers, red "yes" for new), 0 overfull boxes, 0 errors in a private temp compile of the full paper. Measured: acmart \textwidth = 506.295pt, \columnwidth = 241pt, \textheight = 626pt. The heights below are the whole float, caption included, measured as the box height in each standalone (log line BTHEIGHT).

Option A, `ISCA-27/tikz/bugtable_v4_wide_8pt.tex` (+ `_standalone_bugtable_v4_wide_8pt.tex`, `-1.png`): a `table*` across both columns, the rows in two side-by-side halves. Left half: InvisiSpec, CleanupSpec, SpecLFB, STT, SPT. Right half: "(cont.)", ReCon, then the not-reached section. Caption is v4's unchanged; label `tab:bugsv4`. Height 311.6pt. To fit, tabcolsep is 2.5pt (v4: 3pt) and arraystretch 1.0 (v4: 1.05). To use it, replace `sections/results.tex:82` (the brief said :86; the line has moved, it is the `% \input{tikz/bugtable_v3_8pt}...` line) with `\input{tikz/bugtable_v4_wide_8pt}`. A table* floats to the top of the next page, so it may land a page after its text.

Option B, two single-column tables. `ISCA-27/tikz/bugtable_v4_split_8pt.tex` (label `tab:bugsv4`, 336.6pt): the 11 reached bugs first reported by this work (Found by = SimSpect or audit), grouped CleanupSpec / SpecLFB / STT / SPT / ReCon. Every row there is new, so this table drops the New column and the caption says "All are new: none was reported before this work." `ISCA-27/tikz/bugtable_v4_split2_8pt.tex` (label `tab:bugsv4b`, 319.1pt): the AMuLeT bugs our tests reproduce (UV1, UV3, UV4, UV5, UV6), the walk-order row under UV6 (Found by SimSpect, New = no*, counted as broader UV6 per BUGS.md:49), and the six real bugs not reached. Its caption is short and points to Table~\ref{tab:bugsv4} for the column definitions. Each has a `_standalone_..._8pt.tex` + `-1.png`. To use them, replace `sections/results.tex:82` with `\input{tikz/bugtable_v4_split_8pt}`. Put `\input{tikz/bugtable_v4_split2_8pt}` right after it (same spot, so the two float together), or later in the results section if the text discusses the AMuLeT replication separately.

Layout choices for Anna (not content changes, easy to undo): (1) in B, the walk-order row sits with the AMuLeT bugs, not in "first reported by this work", because it is New = no (broader UV6). (2) In B, table 1 drops the New column and says it in the caption. (3) Both options tighten spacing a little (tabcolsep 2.5pt, arraystretch 1.0). The pre-existing "Float too large by 138.7pt" warning in the full-paper compile comes from `tikz/pipeline_full_8pt1col.tex`, not from these tables.

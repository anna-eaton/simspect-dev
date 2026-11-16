# FIG-A: intro / background / model figures (2026-11-10)

Scope: the figures in ~/trippel/ISCA-27/tikz that sections/*.tex \input. Four are live in the ACM build (main.tex): intro_threelayer_v2_8pt (intro.tex:42), execvocab_v2_8pt (model.tex:25), dataflow_8pt (model.tex:68) and relaxation (pipeline.tex:57). Three are not live: statetable (only in sections/pendingfigures.tex, which main.tex does not \input), and alloyviolation and xmitcriteria_8pt (both commented out). I checked the live four in a private temp copy: a full main.tex build (0 errors) plus a standalone render of each at 241pt. None of the four causes an overfull box; every overfull in main.log comes from body or note text. They already use \figfont (8pt) everywhere and follow the palette.

I wrote four NEW files, each with a `_standalone_<name>.tex` and a `-1.png` preview in tikz/. I also swapped all four into the temp copy of the full paper: 0 errors, still 19 pp, and no overfull box comes from these figures (the two extra overfulls are body text in background.tex that reflowed). No existing file was edited and nothing was committed.

## 1. relaxation -> relaxation_v2 (most important)

What's wrong: (1) The figure is 384pt tall, more than half a column, because every pane has its own header line and wide gaps. (2) Arrow (a) is labeled RO, but RO is enforced in no model; what actually removes (a) is RS. Evidence: STT_6.als:214 (o_p drops the operands on a removed state) and :310 (the RS check); the existing auditnote at pipeline.tex:61 says the same. (3) The flag "unresolved" on Load i1 in (c) and the dashed edge in (b) are not explained (auditnote pipeline.tex:59).

What I changed: each pane's note now sits on its relaxation arrow ("RO: unneeded r1", "RI: extra load i3", "RR: resolve i1"). Each pane letter is on its i0 row, and the word "backbone" is inside box (d). The figure is now 329pt tall (55pt shorter), with the same content and the same caption. Arrow (a)'s label is one knob, `\def\rlAlab{RO}`, so RO vs RS is still your call.

Files: tikz/relaxation_v2.tex, tikz/_standalone_relaxation_v2.tex, tikz/_standalone_relaxation_v2-1.png.

Change at pipeline.tex:57: `\input{tikz/relaxation}` -> `\input{tikz/relaxation_v2}`

## 2. execvocab_v2_8pt -> execvocab_v3_8pt

What's wrong: five captions say the graphs are drawn "in the notation of Table I", but the table gives no drawing notation (this is the figure auditnote that sat in v2's Operands row). The note's line break also put a double space after "outputs" whenever the note was shown.

What I changed: added a "Drawn as" row. It covers: `r1 <- m1` (output <- inputs); `[r]` (an address); `?` (unspecified); r/m for Reg/Mem; the flags *unresolved* and *xmit* (rows with no flag are resolved and uncommitted); the thick arrow for the leak path; a lavender "protected" swatch; a tan "speculative rows" swatch; gray/dashed for what a relaxation removes. I removed the now-answered auditnote. The caption is unchanged.

Files: tikz/execvocab_v3_8pt.tex, tikz/_standalone_execvocab_v3_8pt.tex, tikz/_standalone_execvocab_v3_8pt-1.png.

Change at model.tex:25: `\input{tikz/execvocab_v2_8pt}` -> `\input{tikz/execvocab_v3_8pt}`

## 3. dataflow_8pt -> dataflow_v2_8pt

The content is correct against the STT defense block (STT_6.als:320-332). Mem_s is protected. A load lifts that protection only when no unresolved branch precedes it, so m1, read by the speculative load i1, stays protected. The leakage function is Loads.inaddr + Branchxs.inreg.

What's wrong: i0's "unresolved" is in the explanation column here, but every other graph puts flags in the flag column.

What I changed: moved "unresolved" to the flag column, shortened the note to "so i1–i3 are speculative", and trimmed 4pt of bottom slack. The caption is unchanged.

Files: tikz/dataflow_v2_8pt.tex, tikz/_standalone_dataflow_v2_8pt.tex, tikz/_standalone_dataflow_v2_8pt-1.png.

Change at model.tex:68: `\input{tikz/dataflow_8pt}` -> `\input{tikz/dataflow_v2_8pt}`

## 4. intro_threelayer_v2_8pt -> intro_threelayer_v3_8pt

What's wrong: the box title broke as "Defense security / guarantee (leakage predicate)".

What I changed: the title now breaks after "guarantee", so "(leakage predicate)" gets its own line. The gaps between layers go from 31pt to 26pt, making the figure 10pt shorter (199pt instead of 209pt). The caption is unchanged.

Files: tikz/intro_threelayer_v3_8pt.tex, tikz/_standalone_intro_threelayer_v3_8pt.tex, tikz/_standalone_intro_threelayer_v3_8pt-1.png.

Change at intro.tex:42: `\input{tikz/intro_threelayer_v2_8pt}` -> `\input{tikz/intro_threelayer_v3_8pt}`

## Decisions for Anna

- [ ] DECIDE: what should arrow (a) of the relaxation figure be labeled? Option RS: it matches the model; set `\rlAlab` to RS in relaxation_v2.tex and say in the caption that RS removes (a). Option RO: keep it, and add "RO is defined but not enforced". My recommendation is RS.

## Paper-text issues (paper text is read-only to me; you edit these)

- model.tex:51 says "Figure \ref{tab:execvocab}"; it should say "Table".
- model.tex:62 says I1/I3; the figure says i1/i3.
- Fig. 1 is never referenced in the text (reviewnote intro.tex:46).
- The execvocab caption says "only the defense block differs", which is not true for Recon_6 or SPT_6_oneLP (auditnote model.tex:27).
- Proposed sentence to add to the relaxation caption: "Unflagged rows are resolved and uncommitted; dashed = a removed edge."

## Not done

- statetable: errors when compiled standalone (it needs macros the build does not load) and is not live. Not reviewed.
- alloyviolation and xmitcriteria_8pt: hidden in the paper. Not reviewed.

# In/Out lines: proposal (2026-11-16, inout-agent)

Proposal only: the ISCA-27 files are untouched and no git writes were run. Every variant was built on a copy of the repo (`latexmk -pdf`, build exit 0, no new overfull boxes; the 4 overfull boxes in the log were already there) and rendered to PNG to check it.

## What is wrong with the current lines

- **The chain is broken in three places.** Stage 1b's In ("a leakage backbone") is singular, but Stage 1a's Out is plural. Stage 2's In ("a violating execution graph") does not match Stage 1b's Out ("extended execution graphs"). §5's In ("a security litmus test: …") is singular, but Stage 2's Out is plural.
- **"transmission criteria" (plural) in §5's In** disagrees with §5's opening ("the defense's transmission criterion") and with §3.2 ("Each leakage contract also has a *transmission criterion*").
- **Wrapping:** 7 of the 12 lines wrap. Three of them hyphenate mid-word ("pro-|tection set)" in §4 and Stage 1a), and the wrapped text starts again under the label, at the left margin.
- **Redundant definitions:** Stage 1a's Out and Stage 1b's Out restate definitions that the §4 opening paragraph gives ("a minimal violating graph", "grows each backbone into … larger violating graphs") and that Stage 1b's own paragraph gives ("The graph must contain the backbone").

## Proposed six pairs (Option A, recommended; rendered)

Format: an object that is a tuple is written `object: (tuple)`; an object that is bounded is written `object of at most N instructions`. Things that exist once per defense are singular ("a defense specification", "a run configuration"); things that are generated are plural. Each Out is word for word the next In. The ⏎ marks a fixed `\newline`, so a wrapped line always breaks at the same point and the second line hangs under the text, not under the label.

| Place | Current In (lines) | Current Out (lines) | Proposed In (lines) | Proposed Out (lines) |
|---|---|---|---|---|
| §3 Defense Specification | a defense's paper (1) | a defense specification: (leakage contract, execution contract, protection set) (2) | a defense's paper (1) | a defense specification:⏎(leakage contract, execution contract, protection set) (2) |
| §4 Synthesizer | a defense specification: (leakage contract, execution contract, protection set) (2, hyphenated) | security litmus tests: (program, target execution) (1) | a defense specification:⏎(leakage contract, execution contract, protection set) (2) | security litmus tests: (program, target execution) (1) |
| §4.1 Stage 1a | a defense specification: (leakage contract, execution contract, protection set) (2, hyphenated) | leakage backbones: minimal violating execution graphs of at most six instructions (2) | a defense specification:⏎(leakage contract, execution contract, protection set) (2) | leakage backbones of at most six instructions (1) |
| §4.2 Stage 1b | a leakage backbone (1) | extended execution graphs: violating execution graphs of at most eight instructions that contain the backbone (2) | leakage backbones of at most six instructions (1) | extended execution graphs of at most eight instructions (1) |
| §4.3 Stage 2 | a violating execution graph (1) | security litmus tests: (program, target execution) (1) | extended execution graphs of at most eight instructions (1) | security litmus tests: (program, target execution) (1) |
| §5 Executor | a security litmus test: (program, target execution), with a run configuration and the defense's transmission criteria (2) | a gem5 trace and a verdict: hit or no hit (1) | security litmus tests: (program, target execution),⏎a run configuration, and the defense's transmission criterion (2) | a gem5 trace and a verdict: hit or no hit (1) |

Total: 18 rendered lines now, 16 with Option A. No line hyphenates, and every wrapped line breaks at a fixed point. Measured widths (column 241.1pt): "(leakage contract, execution contract, protection set)" is 184pt, so it fits on its hung line (20pt indent). "Out: a defense specification: (leakage contract, …)" is 287pt, so the specification cannot fit on one line at body size even in `\small`.

**Stage 2's In now says "extended execution graphs".** This was checked against the production flow: Stage 2 consumes the Stage 1.5 (= 1b) output (`wiki/state/EVAL_MANIFEST.md:342-345`, "cores → Stage 1.5 → Stage 2 → gem5"). The old "a violating execution graph" was more general than what actually runs.

## Option B (denser; built only as width measurements)

Drop the tuples too, keeping only the object and its bound, because each section's opening sentence gives the tuple right below the In/Out lines (§3: "It has three clauses …: a leakage contract, an execution contract and a protection set"; §4: "each a (program, target execution) pair"). The pairs would be: §3 `a defense's paper` → `a defense specification`; §4 and Stage 1a `a defense specification` → `security litmus tests` / `leakage backbones of at most six instructions`; Stage 1b and Stage 2 as in Option A, with Stage 2's Out shortened to `security litmus tests`; §5 `security litmus tests,⏎a run configuration, and the defense's transmission criterion` → `a gem5 trace and a verdict: hit or no hit`. That makes 13 lines (every line except §5's In fits on one line, from the measured widths), 3 fewer than Option A. The cost is that the In/Out block no longer shows what a specification or a test consists of.

## Proposed macro

The new macro puts each label in a fixed-width box as wide as "**Out:**␣", so the In and Out text start at the same x, and wrapped text hangs under the text, not under the label. It turns hyphenation off inside the lines, keeps the In line and the Out line together with the first line of the paragraph (`\nopagebreak`), and keeps the existing `\smallskip` before the paragraph. It stays italic with bold labels, adds no box, and adds no vertical space. Without the `\nopagebreak`, Stage 2's In fell at the bottom of page 5's right column and its Out at the top of page 6 (seen in the first render). The spacing to the heading and to the first paragraph looked dense and even in the renders (pages 4–7), so it is unchanged.

A one-line "In → Out" form was considered and dropped. Even the shortest pair ("In: leakage backbones → Out: extended execution graphs", with no bounds) is 206pt, so with bounds no pair fits on one line.

## Renders

- Before, page 5 (§4, Stage 1a, Stage 1b): [[INOUT_before_p5.png]]
- After (Option A, with `\nopagebreak`), page 5: [[INOUT_after_p5.png]]. The 3 lines saved let the §4.3 heading reach the foot of the right column, so the `\nopagebreak` sends the heading and its In/Out lines together to the top of page 6. The right column of page 5 is therefore stretched (the paper uses flush-bottom columns); that will change as the text around it changes. §3 (page 4) and §5 (page 7) render as in the table.

## Exact edits (Option A)

`sections/model.tex` line 2: `\providecommand{\stageio}[2]{\par\noindent{\itshape\textbf{In:} #1}\par\noindent{\itshape\textbf{Out:} #2}\par\smallskip}% per-stage input/output line (Anna 2026-11-16)` → 

```latex
\newlength{\stageiolab}% per-stage In/Out lines (Anna 2026-11-16): labels in a fixed-width box, wrapped text hangs after the label, no hyphenation; \newline in an argument sets a clean break
\providecommand{\stageioline}[2]{\par\noindent\hangindent=\stageiolab\hangafter=1\makebox[\stageiolab][l]{\textbf{#1}}#2\par}
\providecommand{\stageio}[2]{\par{\itshape\hyphenpenalty=10000\exhyphenpenalty=10000\settowidth{\stageiolab}{\textbf{Out:}\ }\stageioline{In:}{#1}\nopagebreak\stageioline{Out:}{#2}}\nopagebreak\smallskip}
```

`sections/model.tex` line 3: `\stageio{a defense's paper}{a defense specification: (leakage contract, execution contract, protection set)}` → `\stageio{a defense's paper}{a defense specification:\newline (leakage contract, execution contract, protection set)}`

`sections/pipeline.tex` line 3: `\stageio{a defense specification: (leakage contract, execution contract, protection set)}{security litmus tests: (program, target execution)}` → `\stageio{a defense specification:\newline (leakage contract, execution contract, protection set)}{security litmus tests: (program, target execution)}`

`sections/pipeline.tex` line 28: `\stageio{a defense specification: (leakage contract, execution contract, protection set)}{leakage backbones: minimal violating execution graphs of at most six instructions}` → `\stageio{a defense specification:\newline (leakage contract, execution contract, protection set)}{leakage backbones of at most six instructions}`

`sections/pipeline.tex` line 60: `\stageio{a leakage backbone}{extended execution graphs: violating execution graphs of at most eight instructions that contain the backbone}` → `\stageio{leakage backbones of at most six instructions}{extended execution graphs of at most eight instructions}`

`sections/pipeline.tex` line 72: `\stageio{a violating execution graph}{security litmus tests: (program, target execution)}` → `\stageio{extended execution graphs of at most eight instructions}{security litmus tests: (program, target execution)}`

`sections/pipeline.tex` line 106: `\stageio{a security litmus test: (program, target execution), with a run configuration and the defense's transmission criteria}{a gem5 trace and a verdict: hit or no hit}` → `\stageio{security litmus tests: (program, target execution),\newline a run configuration, and the defense's transmission criterion}{a gem5 trace and a verdict: hit or no hit}`

## Related prose inconsistency (not an In/Out edit; for Anna)

The last sentence of §3's opening paragraph says "and the transmission criteria the only one to the Inspector". Everywhere else the paper uses the singular ("a transmission criterion" per leakage contract, §3.2; "the defense's transmission criterion", §5). A suggested fix: "and its transmission criterion the only one to the Inspector".

## Decisions for Anna

- **DECIDE IO-1:** Option A (keep the tuples, 16 lines) or Option B (object + bound only, 13 lines). Recommendation: A, because the In/Out block then shows what each object consists of; choose B if the space is needed.

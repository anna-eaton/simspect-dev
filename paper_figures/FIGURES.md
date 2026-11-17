# Paper figures: all current drafts

One page with every draft. Sources (`_standalone_*.tex`) and previews (`*-1.png`) live in [`drafts/`](drafts/). Previews show the figure only, with blank space where the caption will go; the proposed captions are in the **Captions** section at the bottom, for Anna to edit and paste into each `\caption{}`. Plans, citations and open decisions per figure are in [`plans/`](plans/); the shared style is [`plans/VISUAL_LANGUAGE.md`](plans/VISUAL_LANGUAGE.md); the audit of every figure already in the paper is [`plans/AUDIT_existing_figures.md`](plans/AUDIT_existing_figures.md). Updated 2026-11-02.

## Which figure replaces what (proposal; Anna decides)

| Draft | Replaces in the paper (`test-paper`) | Status |
|---|---|---|
| Pipeline (vertical) | `tikz/threelayer.tex` (intro, Fig 1: wider than the column, 5pt text, never referenced) | draft; shape redesign in progress |
| (a) Execution-graph vocabulary table (`execvocab`) | nothing (syntax is prose only at `sections/pipeline.tex:9`) | new; vocab table |
| (b) Relaxation (`relaxation_v4`) | `tikz/relaxation.tex` (Fig 3), and possibly `tikz/alloyviolation.tex` (Fig 2) if merged | v4 draft, shared graph notation |
| (c) Interleave (`interleave_v4`) | `tikz/interleave.tex` | v4 draft: the Stage 2 round |
| (d) Instrumentation table | `tikz/sptable_v2.tex` / `sptable.tex` and `tikz/resolutiontiming_v2.tex` / `resolutiontiming.tex` | v2 draft, one column |
| (e) Checker window | `tikz/checkerwindow.tex` | v4 draft |
| (f) Transmission criteria | nothing (new) | draft, full width |
| (not redone yet) | `tikz/statetable.tex`, `tikz/squashrace.tex` (results) | keep; restyle per the audit |

## Pipeline (CURRENT, in the paper as tikz/pipeline_full.tex: text-rich direction A v2, 251 × 620 pt)

![](drafts/design_mocks/mock_A_full_v2-1.png)

Previous main version (still in drafts): `drafts/_standalone_pipeline_vertical-1.png`; text-rich A v1: `drafts/design_mocks/mock_A_full-1.png`.

Rejected earlier versions (no left column) are in `drafts/old/`. A shape-language redesign (how to make components meaningfully shaped instead of walls of text) is being drafted by an agent: `plans/BIGFIG_SHAPE_DESIGN.md` + `drafts/design_mocks/` when done; a fact audit of every label: `plans/BIGFIG_FACT_AUDIT.md` when done.

## Pipeline: shape-language redesign mocks (for comparison; Anna picks)

Brief and shape vocabulary: [`plans/BIGFIG_SHAPE_DESIGN.md`](plans/BIGFIG_SHAPE_DESIGN.md). The mocks predate the latest wording edits (e.g. "on implementation", "processor model", "parallelizable", the language lines), which carry over to whichever direction is chosen.

**A: shape-coded blobs** (agent's recommendation; 252 × 375 pt)

![](drafts/design_mocks/mock_A-1.png)

**B: one spine** (252 × 415 pt)

![](drafts/design_mocks/mock_B-1.png)

**C: merged Alloy stage** (252 × 345 pt)

![](drafts/design_mocks/mock_C-1.png)

## (a) Execution-graph vocabulary table

![](drafts/_standalone_execvocab-1.png)

`execvocab`: 251 × 257 pt, one column, TransForm Table I style. The old boxes-and-dots draft is `drafts/_standalone_execgraphsyntax-1.png`.

**2026-11-02 v4 (current; v3 Alloy-first rejected):** `drafts/execvocab_v4_8pt.tex`, preview `drafts/_standalone_execvocab_v4_8pt-1.png`. One row per section (Instructions, Booleans, Operands, State, Relations), 252 × 108pt. Details in `plans/fig_a_execgraphsyntax.md`.

## (b) Relaxation

![](drafts/_standalone_relaxation_v4-1.png)

v4: 251 × 111 pt, in the shared graph notation (`plans/VISUAL_LANGUAGE.md`, "Graph notation"). v3 is `drafts/_standalone_relaxation_v3-1.png`.

## (c) Interleave: the Stage 2 round

![](drafts/_standalone_interleave_v4-1.png)

v4: 251 × 165 pt. The base rows are a real forced-shape STT_6 instance; c0 and c1 are the injected chain (see `plans/fig_c_interleave.md`, 2026-11-02 section). v3 is `drafts/_standalone_interleave_v3-1.png`.

## (d) Instrumentation table

![](drafts/_standalone_instrtable_v2-1.png)

v2: one column, 251 × 189 pt (v1, full width, is `drafts/_standalone_instrtable-1.png`).

## (e) Checker window

![](drafts/_standalone_checkerwindow_v4-1.png)

v4: 251 × 179 pt (v3 is `drafts/_standalone_checkerwindow_v3-1.png`).


## (f) Load-transmitter transmission criteria per defense (full width, new)

![](drafts/_standalone_xmitcriteria-1.png)

## Reference: how Caroline Trippel's papers draw these things

13 papers and 17 figure crops in [`reference_papers/crops/`](reference_papers/crops/); conventions with page cites in [`plans/TRIPPEL_FIGURE_STYLE.md`](plans/TRIPPEL_FIGURE_STYLE.md).

## Captions (proposed; Anna edits and pastes into `\caption{}`)

**Pipeline.** The \toolname{} pipeline. Stage~1 uses Alloy to enumerate, exhaustively up to a bound, minimal abstract execution graphs that satisfy a defense's leak definition, which is translated manually from the defense specification into the \toolname{} DSL. Stage~1.5 re-enumerates with loosened minimality, pinned to each Stage-1 graph, to reach more complex graphs. Stage~2 concretizes each graph into x86 programs with annotations, one per branch mode and interleave variant. Stage~3 runs each program on the defense's gem5 build under a harness that applies speculation and timing directives; an inspection program checks the pipeline trace for the defense's transmission criteria inside the speculative window. Gray marks defense-specific parts and sources of truth. *("Bounded exhaustive" holds once Stage 1 runs to completion at the bound; see `URGENT_TODO.md`.)*

**(a) Execution-graph vocabulary table (`execvocab`).** \textbf{Execution-graph vocabulary shared by every SimSpect defense model.} An execution is a graph: instruction nodes in program order whose operands name abstract locations, three Boolean flags per instruction, and two operand-to-operand relations. \emph{Graph}: how Figs.~X and~Y draw each element; \emph{Alloy}: its name in the model. Only the defense block (speculation contract, protection set, leakage function) differs between models.

**(b) Relaxation (v4).** \textbf{A violating STT execution before minimization (enumerated instance inst-047231).} Each row is one instruction in program order: its id, its kind, its operands written output $\leftarrow$ input ($[\,]$: an address, ?: left unspecified), and its flags as italic words (a branch without \textit{resolved} is unresolved; \textit{xmit} marks the target transmitter). Arrows are labelled rf (reads-from, between instructions) and ddi (data-dependence internal); vocabulary in Table~X. Black is the violation: protected memory $m_0$ (gray: STT protects all memory) flows through i3 into the address of transmitter i5 (thick arrows), and i5 is speculative because branch i2 is unresolved. Red marks what the relaxations remove while the execution still violates: instructions i0, i1 and i4 (RI), the state $r_1$ (RS), and i5's unresolved flag (RR). Minimization deletes them, leaving the three-instruction backbone i2, i3, i5.

**(c) Interleave (v4).** \textbf{Stage~2 interleaving makes a two-source merge that no Stage~1 instance contains.} Rows i0--i5 are an STT Alloy instance, in the notation of Table~X: protected $m_0$ (gray) flows through i3 and the ALU op i4 into the address of transmitter i5 (thick arrows), and i3--i5 are speculative because branch i2 is unresolved. i4's second input is left unspecified (?). Concretization step~4 (interleave) injects a chain of synthetic instructions, here c0 (a load) and c1 (an ALU op), at random positions after the committed prefix; chain steps carry no flags, and their outputs $f_0$, $f_1$ take registers from a free pool. Step~5 (register assignment) fills every unspecified operand from the same pool, so i4's ? can receive $f_1$'s register, which creates the dashed rf edge: i4 now merges c0's value, which is speculative only under the older branches i0 and i1, with i3's value, which stays speculative under i2. This is the shape behind the ReCon \texttt{getOldestTaint} bug: ReCon keeps only the oldest taint source of an ALU result, so once c0's speculation resolves it untaints i4's result even though i3's value ($r_0$) should still be protected, and i5 transmits.

**(d) Instrumentation table (v2).** \textbf{How concretization instruments each execution-graph element.} Rows are graph fragments in the notation of Fig.~X (xmit: the test's one target transmitter; lc, fnc: last committed, first non-committed). Stage~2 also annotates each element's PC, each branch's mode and predicted target, and the xmit's kind; Stage~3 uses the annotation and marks a run invalid if a force or hold did not take effect. Every instruction is an inline-asm block with a global PC label, after a prologue that zeroes state and runs \texttt{mfence}; no other instruction is hooked. Not generated: correctly predicted unresolved branches, taken resolved branches. *(Agent suggests moving the last two sentences into the text.)*

**(e) Checker window (v4).** \textbf{How the checker decides a violation, on a real gem5 trace} (InvisiSpec build, test inst-002014). Each bar is one instruction from fetch (F) through decode (D) and issue (E) to retirement; dotted stretches are elided cycles. The roles lc (last committed), fnc (first non-committed, here the unresolved branch) and xmit (transmitter) are labels carried from the Alloy instance, and the unresolved window runs from lc's retirement to the branch's resolution. Inside that window the checker applies the defense's transmission criterion (gray): xmit's L1D eviction ($\star$) meets InvisiSpec's criterion before xmit is squashed, so the test is reported as a violation.

**(f) Transmission criteria.** \textbf{Load-transmitter transmission criteria per defense.} For each defense build, what the Stage~3 inspection program counts as a load transmitting, what it deliberately ignores, and which trace line it reads. InvisiSpec, SpecLFB and CleanupSpec each have a defense-specific criterion (gray), stated over \toolname{}'s cache-event hook lines and scoped to the structures the defense's paper protects. STT-Spectre and Recon-STT have no such criterion and use the generic load gate.

## Results figures (2026-11-02)

Evidence, per-figure verdicts, pre/post-harness-fix status, other bug candidates, decisions (R1–R4) and suggested paper text: [`plans/RESULTS_FIGURES.md`](plans/RESULTS_FIGURES.md). Bug-example figures first (Anna); `bugtable_v2` and `targeteff_v2` are not drawn yet.

**Recon STL bypass (`reconstl_v2`, real trace inst-014912, 250 × 220 pt; would replace `tikz/reconstl.tex`)**

![](drafts/_standalone_reconstl_v2-1.png)

*Proposed caption* (`drafts/captions/reconstl_v2.tex`): \textbf{Recon-STT lets a tainted load complete through store-to-load forwarding} (gem5-recon-modded, STT scheme, test inst-014912). Top: the wrong-path fragment; i3 loads speculatively, so \%rax and every address built from it are tainted, and the store i4 and the transmitter i5 use the same tainted address. Bottom: the two instructions in the gem5 trace (cycle = (tick $-$ 2679000)/500). At cycle 5 Recon's own check reports i5 tainted and speculative, yet i5 takes i4's value from the store queue and completes at cycle 7 ($\star$), before the squash at 9. STT requires a tainted-address load, and the forwarding decision itself, to wait until the address is untainted (STT, Sec.~6.4.2, 6.5). In Recon the taint check sits only on the cache path, after the forwarding path has returned (gray).

**Visibility-point/squash race (`squashrace_v2`, real trace inst-047231, 250 × 265 pt; would replace `fig:trace` and `tikz/squashrace.tex`)**

![](drafts/_standalone_squashrace_v2-1.png)

*Proposed caption* (`drafts/captions/squashrace_v2.tex`): \textbf{The visibility-point/squash race in STT, on a real gem5 trace} (STT build with commitToIEWDelay $=4$, test inst-047231; flag-setting instructions omitted from the listing). The transmitter i5 is ready to issue at cycle 49 but is held because its address comes from the speculative load i3. At cycle 77 the mispredicted branch i2 resolves; STT immediately stops treating i3's result as tainted, and i5 issues at 78 and sends a cache packet at 79 ($\star$). The squash caused by the same resolution reaches the load queue only at 81. Cycle 0 is the retirement of the last committed instruction; the committed window closes when fnc retires at 261. At stock timing (commitToIEWDelay $=1$) the squash wins and no packet is sent. *(Window wording depends on decision R1.)*

**Recon OTB / getOldestTaint (`recon_otb_v2`, hand-built test, real pipeview ticks, 250 × 261 pt drawn; would replace `tikz/otbtwobranch.tex`, `fig:otb`)**

![](drafts/_standalone_recon_otb_v2-1.png)

*Proposed caption* (`drafts/captions/recon_otb_v2.tex`): \textbf{Recon-STT releases a transmitter whose address still depends on a speculative load} (\texttt{getOldestTaint}; \texttt{/work/gem5-recon}, STT scheme, hand-built test). Top: the test as an execution graph in the notation of Table~X. The ALU op i4 merges $r_0$ from the older load i1, speculative under branch i0, with $r_1$ from the younger load i3, speculative under the mispredicted branch i2; its result is the address of transmitter i5 (thick arrows: the flow from i3). Bottom: the gem5 pipeline trace (cycle = (tick $-$ 2803000)/500). i0 resolves at cycle 0, and i5 issues at cycle 8 ($\star$), as soon as i4's result is ready and at the same cycle as with no defense, while i2 stays unresolved until cycle 92. Recon gives i4's result only the taint of its oldest tainted source and frees it when that source stops being speculative (gray), so the dependence on i3 is lost. This test was built by hand; our bounded enumeration does not reach this shape within its instance cap. *(The star marks issue only: the scheme-2 pipeview records no completion for the xmit; see `plans/RESULTS_FIGURES.md` §7.)*

**Bug table (`bugtable_v2`, full width `table*`, B&W, 514 × 236 pt; replaces `tab:bugs` in `results.tex:20-55`)**

![](drafts/_standalone_bugtable_v2-1.png)

*Proposed caption* (`drafts/captions/bugtable_v2.tex`): \textbf{Speculative-execution defense bugs, grouped by defense:} where each bug was first known, which tool exhibits it (\toolname{}, AMuLeT, both, or neither), whether it falls in \toolname{}'s leakage model, the verdict, and the evidence behind it. \emph{Pre-fix, re-run}: the evidence predates our 2026-10-30 fix of the branch-annotation and resolve-stall harness, and the run is being repeated. The ReCon \texttt{getOldestTaint} bug is confirmed by a hand-built test that our bounded enumeration does not reach; the ReCon store-to-load forwarding bug rests on one trace and remains a candidate. The pending-squash race (a secret-dependent squash signal, fixed upstream by Mosier) is a real STT bug that \emph{neither} automated tool found. The InvisiSpec and CleanupSpec rows are collateral transmitter-side channels, not logic bugs in a comprehensive defense, and lie outside \toolname{}'s scope. \textdagger\ A violation if the speculative window ends when the first non-committed instruction retires; not one if it ends when the guarding branch resolves. \textdaggerdbl\ Not a bug: STT's specification does not treat stores as transmitters, so a tainted-store$\to$TLB leak is outside the property STT claims to enforce.


## Suggested paper text (collected 2026-11-02; Claude never edits paper prose — Anna pastes)

- Interleave (c): the figure now shows Stage 2 interleaving; say so in the subsection text, and the old caption's reg0 should be reg1.
- Relaxation (b): `pipeline.tex:20` cites `fig:relaxation`; the new figure carries that label, so the reference resolves now.
- DSL: not used (Anna: DSL means domain-specific language; dropped).

### Vocab table (a)

Proposed prose trim (for Anna): if the figure goes in, the middle of `pipeline.tex:9` ("typed as transmitters … track information flow to transmitters.") can shrink to one sentence pointing at Fig.~\ref{fig:execsyntax}. That pays back roughly 4 lines of text.

### Instrumentation table (d): text moved out of the table

Source: `plans/fig_d_instrtable.md`.

Every instruction is emitted as its own inline-asm block that carries a global PC label, so nothing can sit between the label and the instruction; the annotation rewrites each label as an x86 address. A prologue zeroes the memory slots, the probe array (when used) and the live-in registers, then runs \texttt{mfence}. Address operands index the probe array, and the program is compiled with clang \texttt{-O2}. Stage~3 adds no hook for ordinary instructions: it reads transmission from gem5's O3PipeView, LSQUnit and Commit traces, with the checker chosen by the xmit's kind (Load, Store, Branch\_x, or Other\_x, a zero-skip multiply or a divide). Branch conditions are constants (\texttt{movq \$1} or \texttt{xorq}), and a Branch\_x that is not the xmit is handled like a Branch\_n. A branch xmit that is the last instruction is followed by a \texttt{nop}; divides other than the xmit get \texttt{orq \$1} on their divisor so they cannot fault. Store bypass is its own run mode, with all branches resolved, on a gem5 build with store-bypass hooks; when an address register is involved, the store is re-emitted at the load's runtime address. All values are those of the evaluated campaigns.

(Sources: Row 6 and Rows 1, 2, 5 bullets above.)

### Instrumentation table (d): where the paper text disagrees with the code

Source: `plans/fig_d_instrtable.md`.

1. `sections/pipeline.tex:46`: "For resolved branches … insert a skipped block of noops if they are taken". Code generates resolved branches only as correctly predicted not-taken (row 3).
2. `pipeline.tex:48` and `:86`: STL "only in the false positive direction … enforce that the load and store have different addresses". Code does the false-negative direction with the load and store at the same address (row 1; Anna's 2026-10-28 answer in SPEC_PRIMITIVE_INSTANCES.md "Open").
3. `pipeline.tex:86`: "runs are launched bare at $s_U = 0$" and "the commit-stall over {0, 150} cycles". The fixed configs use $s_U = 5000$ and commit stall 0 (rows 2, 4).
4. `pipeline.tex:86`: the BTB-forced target forces "the modeled mispredicted (taken) path". On hooked builds every annotated branch now gets a derived force in either direction, resolved branches included (rows 2, 3, 5).
5. `pipeline.tex:83`: the annotation carries "the resolution time of every speculation primitive". Stage 2 never writes timing; Stage 3 adds `resolve_stall_cycles` on the sweep path and the store hold comes from config (CONCRETIZATION_PASSES.md §4.3).
6. `pipeline.tex:57`: "all branches guarding the transmitter are still unresolved". The gate is the model's unresolved branches, measured at `resolve_visible` (row 2).
7. `pipeline.tex:88`: "the same nine source sites". The builds now also carry the resolve hooks (BR print lines, forced not-taken via target 1, release wakes the CPU) and, on gem5-recon-stl, the STL hooks.

Suggested caption (Anna pastes, if she wants it): "How concretization instruments each execution-graph element. Stage 2 emits the program and its annotation; the Stage 3 harness reads the annotation to force predictions, hold resolutions, and bound the window in which the target transmitter must transmit. Values are those of the evaluated campaigns."

### Transmission criteria (f): where the paper text disagrees

Source: `plans/fig_f_xmitcriteria.md`.

- `sections/pipeline.tex:63` describes the load signal as LSQUnit ticks "(… on newer builds an additive `memaccess` tick for SpecLFB and an `expose` tick for InvisiSpec)". Those are the legacy checkers (`check_ld_speclfb.py`, `check_ld_invisispec.py`); the JSON criteria use SimSpect cache-event hook lines instead.
- `pipeline.tex:55, 90` say detection reads only the existing `O3PipeView`, `LSQUnit` and `Commit` streams and that "No cache or defense code is instrumented to *see* a leak". The footprint criteria read SimSpect print hooks added to the cache code (`SIMSPECT_HOOKS.md`), and every row's window uses the BR resolve hook lines.
- `pipeline.tex:57`: "all branches guarding the transmitter are still unresolved". The gate is the model's unresolved branches, at `resolve_visible` (same note as fig d).

### Results section (Recon, race, caveats)

Source: `plans/RESULTS_FIGURES.md`.

**Recon (new paragraph).** We also ran SimSpect on ReCon's gem5 implementation of STT, which treats both unresolved branches and stores with unresolved addresses as sources of speculation. It exposes a bug in how ReCon applies STT's load rule: ReCon checks a load's taint only on its cache path, after store-to-load forwarding has already returned. A speculative load whose address is tainted therefore completes with a forwarded value whenever an in-flight store has the same address (Fig.~\ref{fig:reconstl}). STT names exactly this case an implicit branch and requires the forwarding decision to wait until the address is untainted, or the forwarded value to be written only when the memory access would have completed [STT, §6.4.2, §6.5]. The completion time of the load therefore reveals whether a secret-derived address matches a store address the attacker chose.

**Recon OTB (if kept).** ReCon's taint tracker also keeps only the oldest taint source when an instruction merges two tainted operands. When the older source's branch resolves, the result is untainted even though it still depends on a younger speculative load, and a dependent transmitter issues. We confirmed this with a hand-built two-branch test; our bounded enumeration does not reach this shape within its instance cap.

**Race (revised framing; depends on R1).** In STT, a transmitter's address stops being tainted the moment every older branch resolves. When that branch was mispredicted, the same event starts the squash, which reaches the load queue `commitToIEWDelay` cycles later. In inst-047231 the held transmitter issues one cycle after resolution and sends a cache packet two cycles before its squash (Fig.~\ref{fig:race}). At stock timing the squash wins.

**Caveat (pre-fix numbers).** The counts in this section (race instances, the stall and fragility sweeps, SpecLFB detection speed) come from campaigns run before we fixed the branch-annotation and resolve-stall harness on 2026-10-30; on the SPT and ReCon builds those campaigns ran without the intended forced mispredicts and stalls. We are re-running them; the two traces shown here do not depend on the fix, since their mispredictions occur naturally.


## 8pt-minimum versions (in the paper as of 2026-11-02)

Every figure in the paper now uses its `_8pt` version (all text at least 8pt, including arc labels); the 7pt versions are kept in `drafts/`. Previews: `drafts/_standalone_<name>_8pt-1.png` for intro_threelayer_v2, execvocab, relaxation_v4, interleave_v4, instrtable_v2, checkerwindow_v4, xmitcriteria, reconstl_v2, squashrace_v2, recon_otb_v2, bugtable_v2; pipeline: `drafts/design_mocks/mock_A_full_v2_8pt1col-1.png` (one column, in the paper next to the 7pt one; keep one) and `mock_A_full_v2_8pt-1.png` (double wide, not used).

## Defenses out of scope (proposed text) — 2026-11-02

Proposed paragraph (for Anna to edit and paste; not in the paper): We evaluate SimSpect on defenses whose authors released a gem5 implementation that we could build and instrument with our print-only hooks: STT, Recon, SPT, SpecLFB, InvisiSpec, and CleanupSpec, with Delay and DoM run as schemes of the Recon build. For InvisiSpec and CleanupSpec, the leaks SimSpect finds (the UV1 eviction channel and post-squash cleanup residue) lie outside the protection each paper claims, so we report them as collateral channels rather than as violations of the defense's own guarantee. We did not evaluate SDO: its public source is available, but we have not yet built it or added our hooks, so it is left for future work. [Placeholder: one sentence on the remaining defenses (NDA, SafeSpec, MuonTrap, DOLMA, SpecShield, ConTExT, Conditional Speculation, GhostMinion), once Anna has decided why each is excluded.]

- **InvisiSpec**: in the harness, but its findings are out of the defense's guarantee (collateral channels). Source: `specs/defense_units.json:29`, `wiki/findings/mdsToRead/PROTECTION_SCOPE_TABLE.md`.
- **CleanupSpec**: in the harness, but its findings are out of the defense's guarantee (post-squash residue, unXpec). Source: `specs/defense_units.json:33`.
- **SDO**: an implementation exists (`/work/sdo`, cwfletcher/sdo @ 5d058fd) but was never built or hooked. This is closest to "implementation exists but not integrated"; the repo does not record that it is incompatible with the harness. Source: `wiki/design/RESOLUTION_HOOKS_SURVEY.md:29`.
- **DOLMA**: the repo mentions it only as the origin of SpecLFB's branch-resolution rule (`wiki/design/RESOLUTION_HOOKS_SURVEY.md:73`). There is no recorded reason for leaving it out: unknown, needs Anna.
- **NDA, SafeSpec, MuonTrap, SpecShield, ConTExT, Conditional Speculation, GhostMinion**: none is mentioned in wiki/, specs/, STATUS.md, claudelog.md, or paper_figures/: unknown, needs Anna.
- **AMuLeT artifact builds**: these are the source of the InvisiSpec, CleanupSpec, SpecLFB, and amulet-STT builds we use (in scope, not excluded). Source: `wiki/design/RESOLUTION_HOOKS_SURVEY.md:25-28`.

## Glossary (2026-11-02)

Source: fresh clone of `test-paper` (HEAD `608b82d`, 2026-11-02 15:04), `sections/*.tex`; other names from captions in this file, `CLAUDE.md`, `.als` predicates, `specs/`. Refs are `file.tex:line`. "Rec." = recommendation for Anna, not a decision.

| Term | Paper's definition | Other names in use | Rec. single term |
|---|---|---|---|
| Execution graph / abstract execution | Executions modeled as directed happens-before graphs of Instruction nodes, Operands, State, with data-dependence edges (`pipeline.tex:10-11`) | "abstract execution" (`pipeline.tex:7,46`), "happens-before graph"; code: Alloy instance, `inst-*.xml` | execution graph (use "instance" only for one Alloy solution) |
| Leakage backbone | Abstract fundamental form of Spectre leakage the defense blocks, concretized into tests (`pipeline.tex:8`, `:22`) | "leakage path skeletons" (`intro.tex:27`), "forms of leakage", "LILT" (`discussion.tex:15`, old text), "leak shape" (OTB docs) | leakage backbone |
| Transmitter | Instruction that leaks one or more operands via a side channel (`model.tex:6`); typed Load, Store, Branchx, Otherx (`pipeline.tex:11`) | xmit (code `ann["xmit"]`), kinds `ld`/`br_x`/`other_x` | transmitter (xmit only in code and figure labels) |
| Speculation primitive | Instruction that initiates speculative execution, e.g. a conditional branch (`model.tex:8`) | "unresolved branch/store", BTB-forced branch | speculation primitive |
| Execution contract | What speculative control and data flow the defense considers, via its speculation primitives (`model.tex:8`) | "speculation contract" (`discussion.tex:5`, FIGURES.md, `.als speculation_contract_p`) | see Consolidate (a1) |
| Protection set | Architectural state the defense promises not to leak, plus an update rule (`model.tex:10`) | `hardware_protection_policy` + `prot_set_propagation_p` (.als), "taint" (STT) | protection set (+ "protection-set update rule") |
| Leakage contract | Set of (transmitter, unsafe operand) pairs the defense recognizes (`model.tex:6`) | "leakage function" (`discussion.tex:5`, `model.tex:31` comment, `.als leakage_function`), "leakage predicate" (`pipeline.tex:10`, `related.tex:31`) | see Consolidate (a2) |
| Violation | Data-dependence path from a protection-set element (as updated by the most recently committed instruction) to a leaked operand of a transmitter that is in the leakage contract and speculative per the execution contract (`pipeline.tex:15`) | "hit" (gem5), "leak" | violation (model); hit (gem5 result before validation); leak (validated) |
| Minimality criterion | Restricts synthesis to the smallest example of each leakage backbone (`pipeline.tex:22-23`) | `gen_useful_litmus` (.als; minimizes via RR/RS only per CLAUDE.md) | minimality criterion. Check: paper lists 5 relaxations, code uses 2 |
| Relaxations RI/RO/RS/RC/RR | RI remove instruction, RO remove operand, RS remove state, RC flip last-uncommitted to committed, RR mark unresolved as resolved (`pipeline.tex:29-33`) | none | as is |
| Interleaving | Stage-1.5 "overlapping interleaving" in Alloy by dropping relaxations (`pipeline.tex:36`) and a second round during concretization (`pipeline.tex:48`) | `pass_interleave`, `_v<k>` variants, "chain interleaving" (CLAUDE.md) | see Consolidate (a5) |
| Concretization | Turning abstract executions into programs plus simulator directives (`pipeline.tex:45-46`) | parsexml passes, "Stage 2", `STAGE2_compilation` | concretization |
| Annotation | Per-test `.ann.json`: BTB target per forced branch, resolve time of each speculation primitive, stalls, aliasing (load, store) PC pairs (`pipeline.tex:94`) | "committed annotations", "speculation annotations" (old text), "metadata" | annotation (the file) |
| Speculation and timing directives | What the simulator is told so the modeled scenario actually happens (`pipeline.tex:90`, `discussion.tex:7`) | "simulator directives", "timing directive" (FIGURES.md), hooks (`pipeline.tex:96-97`), "stall knobs" (`results.tex:168`) | speculation directive (prediction) + timing directive (stalls); "hook" = the gem5 code site |
| Harness | Probes plus directives around gem5; probes never change defense logic (`discussion.tex:7`, `pipeline.tex:63`) | "gem5 harness", Stage 3, checkers | harness |
| lc / fnc | Last committed / first non-committed instruction (`pipeline.tex:65`) | `lc_retire`, `fnc_retire`, `fnc_commit_stall_cycles` | lc, fnc |
| Resolved / committed | μarch flags carried by each instruction, enforced in simulation (`pipeline.tex:11`, `model.tex:27`) | "retired" (`*_retire` ticks) | resolved, committed ("retire tick" only for the gem5 timestamp) |
| Committed window | (lc_retire, fnc_retire) with all guarding branches still unresolved at the transmission tick (`pipeline.tex:65`) | "speculative window" (`results.tex:114,129,243`, `pipeline.tex:97`, `discussion.tex:13`), "commit window" (`discussion.tex:8`), "unresolved window" (FIGURES.md) | see Consolidate (a4) |
| Transmission mechanism | (Decided by Anna) the per-transmitter pipeline event that counts as transmission (`pipeline.tex:63`, `discussion.tex:6`) | "per-transmitter pipeline predicate" (`pipeline.tex:63`), "signal", "JSON criteria" / `specs/transmitter_criteria` | transmission mechanism |
| HSCA / HSCD | Hardware side-channel attack: an unsafe instruction makes operand-dependent resource usage an attacker observes (`intro.tex:3`); HSCD = defense (`intro.tex:5`, `background.tex:3`) | "Spectre attack/defense" | HSCA, HSCD |

Already decided by Anna: "transmission mechanism"; "Inspector"; "Kodkod model finder"; "bounded exhaustive" (Stage 1) / "non-exhaustive" (Stage 1.5) (now in `discussion.tex:4`); lowercase i0; DSL is not used.

### Consolidate or define

(a) Groups that should be merged into one name:

- (a1) **execution contract** (`model.tex:8`, `discussion.tex:16`) vs **speculation contract** (`discussion.tex:5`, the .als). Rec.: "speculation contract", which matches the code and the defense block, and avoids clashing with Guarnieri-style "execution contracts".
- (a2) **leakage contract** (`model.tex:6`) vs **leakage function** (`discussion.tex:5`, .als) vs **leakage predicate** (`pipeline.tex:10`). Rec.: "leakage function" for the spec component (the .als name) and "violation predicate" for the whole formula at `pipeline.tex:15`. Drop "leakage contract", or keep it and rename the .als references in prose only.
- (a3) **leakage backbone** / leakage path skeletons / forms of leakage / LILT. Rec.: "leakage backbone"; remove LILT from `discussion.tex:15`.
- (a4) **Window**: committed window (`pipeline.tex:65`) / commit window (`discussion.tex:8`) / speculative window (`results.tex:114,129,243`, `pipeline.tex:97`) / unresolved window (figures). Options: (A) "committed window" for the lc/fnc interval only, with "branches unresolved" stated as a separate gate. This is accurate to the construction but hides the branch condition. (B) "speculative window": familiar and already used in results, but readers will take it to mean the hardware's whole speculation span, not the lc/fnc interval. (C) "violation window": a new term, defined once at `pipeline.tex:65` as the committed interval AND the unresolved gate. It is unambiguous and ties to "violation" (`pipeline.tex:15`), at the cost of one new term. **Rec.: (C)**, then use it in results.tex, discussion.tex and all captions. If no new term, use (B) with a one-line definition. Note that `discussion.tex:8` treats "commit window vs branch resolution" as an open semantic issue, so the name should follow Anna's call on that.
- (a5) **Interleaving**: overlapping interleaving / second-round interleaving / chain interleaving. Rec.: "Stage-1.5 interleaving" and "concretization interleaving".
- (a6) **directives / hooks / knobs / annotations**. Rec.: annotation = the file, directive = what it asks for, hook = the gem5 source site, knob = a swept stall parameter.
- (a7) **violation / hit / leak**. Rec.: use them as three stages (model, then raw gem5 result, then validated).

(b) Terms the paper uses but never defines:

- **ddi / rf / spo** edge names, if used beyond `pipeline.tex:11` (only "data-dependence edges" is defined there).
- **defense unit** (only in `specs/defense_units.json`; not in the paper). Define it or keep it out.
- **visibility point (VP)** (`results.tex:86`): used as a section title with no definition.
- **window-valid** (`results.tex` AMuLeT comparison): needs a one-line tie to the window definition.
- **fnc stall, resolved-branch stall, unresolved-branch stall $s_U$** (`results.tex:168-194`): name and define them once next to the timing directives.
- **store set / store-to-load forwarding misprediction** (`pipeline.tex` instrumentation): assumes gem5 knowledge.
- **HSCD**: used in `intro.tex:5` before or without expansion; check first use.
- **taint** (STT, `results.tex`): explain as STT's own protection-set mechanism.


### Reviewer terminology feedback (YArch'26, real reviews: `~/Downloads/#71 - YArch'26.pdf`)

- **Review #71B (Accept, expert):** "The terms 'leakage contract' and 'execution contract' used in this paper is different from the common definitions for these terms from prior works: HW/SW Contracts [SP'21], Revizor [ASPLOS'23] and Amulet [ASPLOS'25]. Leakage contract consists of an observation clause (which side-channels can leak) and execution clause (what speculations can leak). It would be better to update the usage of 'leakage contract' and 'execution contract' in your paper with observation clause and execution clause respectively ... to be consistent with the literature in this space."
- **Review #71A (Weak accept):** "please define acronyms before use---for example, what do 'rf' and 'ddi' stand for?"; avoid long, winding sentences.
- **Review #71C (Weak accept):** summarizes the spec as "leakage contract, speculation primitives and architecture state to protect".
- **Anna's view (2026-11-02), supersedes my earlier mapping:** the *observation clause* is a separate concept (what the attacker can observe in µarch state, not what is fundamentally leaked), so it does not map onto our leakage/transmitter function; **"execution contract" is right** (the term other work uses to characterize the allowed execution); "leakage contract" for the transmitter part makes sense but is the least certain.
- **Origin of the observation/execution split (from a search summary, not yet read in full):** contracts were introduced by Guarnieri, Köpf, Reineke, Vila, "Hardware-Software Contracts for Secure Speculation", IEEE S&P 2021 (https://mguarnieri.github.io/publication/sp2021/sp2021.pdf); the clause names "observation clause" / "execution clause" are used by Revizor (Oleksenko, Fetzer, Köpf, Silberstein, ASPLOS 2022, https://arxiv.org/pdf/2105.06872), e.g. CT-SEQ (observe load/store addresses and control flow; empty execution clause) and MEM-COND (allows branch misprediction). The reviewer's "Revizor [ASPLOS'23]" is probably the follow-up "Hide and Seek with Spectres" (ASPLOS 2023, https://arxiv.org/pdf/2301.07642). AMuLeT (ASPLOS 2025) uses the same contracts.
- **LCM (Mosier, Lachnitt, Nemati, Trippel, ISCA 2022; read this session, `reference_papers/lcm_clou_isca22/`):** calls its contracts *leakage containment models*, "axiomatic hardware-software contracts for security"; its vocabulary is transmitters (with a severity taxonomy), access instructions, xstate, and the rfx/cox/frx/comx relations, and it distinguishes transient vs non-transient leakage (abstract, §1, §3). It does not use "observation/execution clause"; it describes Guarnieri et al.'s contracts as exposing "which aspects of microarchitectural state are observable to an adversary" (§ related work).

## Basic execution-graph example (2026-11-02)

`drafts/dataflow_8pt.tex` (preview `_standalone_dataflow_8pt.tex`, color preview `_standalone_dataflow_8pt_color3.tex`) redraws the paper's old `tikz/alloyviolation.tex` (fig:ddi-rf) in the shared row notation with the same program, edges and flags. It is in the paper as `tikz/dataflow_8pt.tex` (same label `fig:ddi-rf`) in the Execution Syntax section; the old file is kept. Caption: `captions/dataflow_8pt.tex`. Colors are named (`ssprot*`, `ssspec*`, `ssxmit*`) with B&W defaults via `\providecolor`, so a palette in the preamble switches it to color.

**2026-11-03 relaxation v5 (in the paper, not yet pushed):** `drafts/relaxation_v5_8pt.tex`, preview `drafts/_standalone_relaxation_v5_8pt-1.png`, caption `drafts/captions/relaxation_v5_8pt.tex`: Anna's original four panes ((a)–(c) relax to backbone (d) by RO, RI, RR) in the shared notation. Dataflow caption rewritten to explain the STT violation (`drafts/captions/dataflow_8pt.tex`). Both marked with red TODOs in the paper. Details: `plans/fig_b_relaxation.md`.

**2026-11-03 paper pass (ready, not yet pushed):** the relaxation figure is now one file, paper `tikz/relaxation.tex` (body = `drafts/relaxation_v5_8pt.tex`; the old `relaxation.tex` original and `relaxation_v4*.tex` removed, in git history). Table II (`instrtable_v2_8pt`) Stage 2 column now says each element's (mis)prediction and (not-)taken direction (from `plans/fig_d_instrtable.md` fact rows 1-5). Syntax-table refs fixed in the interleave, instrtable and recon_otb captions. Transmission-criteria table hidden (commented out). Fig. 6 (checker window) cited at its first use. 33 red `\claudenote{}` suggestions (cut / reword / proposed text) in the Concretization and gem5 subsections and one in results; `\renewcommand{\claudenote}[1]{}` in the preamble hides them.

**2026-11-03 later (in the local paper copy, not yet pushed):** Fig. 4 shows *unresolved* on branch i0 in every pane (pane notes moved to header lines; `drafts/relaxation_v5_8pt.tex`). Resolution-timing figure remade from Anna's original in the shared notation (`drafts/resolutiontiming_v3_8pt.tex`; paper `tikz/resolutiontiming.tex`, back in at its citation; `resolutiontiming_v2*` removed). Race and ReCon STLF figures now have an execution graph on top of the pipeline trace (`drafts/squashrace_v3_8pt.tex`, `drafts/reconstl_v3_8pt.tex`, captions in `drafts/captions/`; bodies replace the paper's `squashrace_v2_8pt` / `reconstl_v2_8pt`). The STLF graph draws only the XML's edges: no store-to-load memory edge exists in the model (store i4 has no outmem, xmit i5 no inmem); both address operands name r0. `wiki/findings/bug/recon_SLF_stlf_bypass/NOTE.md` corrected: pc2, not pc1, is the mispredicted branch (XML, ann.json).

## How related papers present their bugs (2026-11-11)

Read from the real PDFs. AMuLeT: `~/Documents/quail/sources/papers/fu-2025-amulet.pdf`. The rest are saved under `paper_figures/reference_papers/<name>/` (revizor, hideandseek, specfault, phantomtrails, cheng, specdoctor_ccs22, introspectre_isca21, dejavuzz_asplos25, specure_dac24, cascade_sec24), plus the local Contract Shadow Logic, Pensieve, TriCheck and CheckMate copies. Page numbers are PDF pages.

| Paper | All-bugs table? | Per-bug visuals | Space per bug | Abstract claim |
|---|---|---|---|---|
| AMuLeT (ASPLOS'25) | No. Table 4 (p9) is per defense: contract, detected?, detection time, #violations, throughput | Almost every bug, about 12 small single-column items for 9 bugs: test asm + input pair + trace diff (Fig 4, 6, 8, 9), buggy gem5 code + patch (Listings 1–2, Fig 7), op-sequence tables (Tables 7, 9, 10), violation types before/after patch (Table 8) | §4.5–4.8, one subsection per defense, about 4 of 16 pages. Each bug is a bold run-in "UV1. …" paragraph, then "Root Cause:" and "Fix:" (implementation bug vs design issue) | "3 known and 6 unknown bugs and vulnerabilities, within 3 hours" (p1) |
| Revizor (ASPLOS'22) | Matrix Table 3 (table*, p9): targets × contracts, ✓/× cells naming the vulnerability, ** marks novel | Short listings for the new variants only (Fig 5, 3 lines) | Known: 2–6 lines per target; new: about half a column (§6.3) | "several previously unknown variants" |
| Hide and Seek (S&P'23) | Matrix Fig 1 (p2): ISA subset × CPU | Only the 2 new leaks: one full-width cache-line diagram (Fig 2) + 2–4-line listings | Own early section §II, about 1.3 columns, for the 2 new leaks | "two new classes of leaks" + vendor disclosure |
| Speculation at Fault (Sec'23) | Matrix Table 1 (table*, p12): fault × contract × CPU | 3–6-line inline asm per new leak, no diagrams | 15–25 lines per new leak (bold run-in), 1–3 lines per known one | "three novel transient leaks", CVE |
| Phantom Trails (Sec'25) | Time-to-exposure Table 1 for the known bugs only | One 9-line listing for the one new bug | Whole §8 (about 1.3 columns) for the one new bug | "all known … as well as a new Spectre variant" |
| Cheng (Sec'26; bypasses STT/SPT/DOLMA in gem5) | Defense × limitation matrix Table 1 (table*, about 40% of a page; blue = new) + 3-row Table 3 | Listing + pipeline timeline per gadget (Fig 5 figure*, Figs 6–8) | 15–30 lines per limitation/gadget, grouped by violated design assumption | "three limitations"; disclosure in Ethics |
| SpecDoctor (CCS'22) | Small single-column variants table (Table 5) + tool-comparison table (Table 4) | 2 new bugs: mechanism block diagram + code (about half a column each) | §7 Findings: 1–1.5 columns per new bug; known ones get one sentence | names the 2 new bugs, developer-confirmed, CVE |
| IntroSpectre (ISCA'21) | Yes, Table IV (table*, about 1/3 page, 16 rows): ID (R1–R8, L1–L3, X1–X2) / leak / gadget | 4 of 16 cases get figures | §VIII case studies: 3–10 lines per case; same-mechanism cases share a paragraph | "13 distinct, not previously documented" |
| DejaVuzz (ASPLOS'25) | Single-column classification Table 5 (6 rows) | Listings for 2 of 5 bugs | Bold "B3. Name (CVE)" paragraph, 6–12 lines each | "5 previously undiscovered (6 CVEs)" |
| Cascade (Sec'24) | Yes, but in an appendix (38 rows, ID/description/CWE/CVE) | Aggregate charts only (bugs by class, time-to-reveal per ID) | One paragraph per symptom class citing IDs, no deep dives | "37 new bugs (28 new CVEs)" |
| CheckMate (MICRO'18) | Single-column Table I (pattern / bound / time / #tests) | One full-page 4-panel µhb-graph figure, transmit path in red | About 1 column per new exploit | new exploits named |
| TriCheck (ASPLOS'17) | No; aggregate bar Fig 15 | Small litmus figure per bug class (Figs 8–14) | One subsection per bug class + recommended fix | count of forbidden outcomes over N tests |
| Pensieve, CSL, Specure | No / small tool × target matrix | One counterexample figure (Pensieve) or a 3-line listing (CSL) | One case study (Pensieve §6) or one paragraph | "a new … variant" |

**The common pattern.**

- **Space follows the number of bugs.** Papers with 2–5 new bugs give each its own bold paragraph or subsection and keep no master list. Papers with 13+ use an ID'd table and write one paragraph per group of same-mechanism bugs (IntroSpectre, Cascade).
- **Known or replicated bugs get one sentence, a table cell, or a time-to-detect comparison.** They never get figures.
- **Only 1–4 bugs get a visual,** and those are the most novel ones. The visual is usually a 3–9-line listing; a mechanism or timeline diagram goes only to the flagship bug. AMuLeT is the outlier, with a concrete figure for nearly every bug.
- **The abstract gives an exact "N new" count plus outside validation** (developer-confirmed, CVE, patch), and every paper has a disclosure sentence. Time-to-detect sits in its own table or chart, not in the bug table.
- **Only bugs the tool found are listed.**

**What this means for SimSpect (Anna decides).**

- **Our bug IDs:** the paper's new-bug labels UV1–UV6 (`results.tex` §Unknown bugs) collide with AMuLeT's UV1–UV6, which the same section uses for the replicated bugs. Use a distinct prefix for ours.
- **Our table:** the 23-row two-column `bugtable_v4_wide_8pt` is larger than any comparable main-text bug table. It also includes source-audit bugs that our tests do not reach, which no comparable paper does.
- **Our visuals:** with about 11 new bugs, the norm is one compact single-column table plus a paragraph per bug (or per same-mechanism group), and figures for only 2–4 flagship bugs. We have 3 bug figures in the paper and 7 more proposed (`tikz/prop_*`); using all 10 would be far above the norm.
- **One option that fits our method:** a single CheckMate-style multi-panel figure of minimal violating execution graphs, one panel per flagship bug, in the same notation as the model section.

## Inspector figure v6 (2026-11-16)

New files in ISCA-27 `tikz/` (v5 and the paper text untouched): `checkerwindow_v6_8pt.tex` (recommended) and the alternative `checkerwindow_v6b_8pt.tex`, each with its `_standalone_*.tex` and 200 dpi `-1.png` preview. Both carry the full figure environment, the same label `fig:checkerwindow`, and a proposed 69-word plain caption ending in a red `\reviewtag`. To switch, in `sections/pipeline.tex` change `\input{tikz/checkerwindow_v5_8pt}` to `\input{tikz/checkerwindow_v6_8pt}` (or `_v6b_`).

Why: Anna found Fig. 5 (v5) confusing. The redesign follows the Executor review (`caroline/REVIEW_ACTION_ITEMS_EXECUTOR.md` F1–F4, W-5 rec. (b), W-8 rec. (a)), so the figure says one thing: the window's two edges plus the in-window event make the hit.

What changed from v5: the speculation-window bar is gone (one window only); the "Role labels" header row, icon and bus line are gone; the five-line criterion box and its icon column became one blue line ("Criterion: a cache or D-TLB change by a squashed load younger than lc"); issue is I, not E; rows are 19pt apart (v5: 26 and 36pt); "5000-cycle resolve stall" became "5,000-cycle hold"; the long branch note became "(branch)" in the row label; the star's label is "L1D eviction: hit". In v6 the violation window is a tan band behind the rows: its left edge runs through lc's retirement dot and its right edge through the squash cross on xmit, so the star visibly sits inside it. v6b instead draws one tan bar under the rows, tied to the same two events by dashed drop lines, which matches the squash-race figure (`squashrace_v3_8pt.tex`); it is 8.3pt taller.

Height, measured on the standalone PDFs (2pt border included, width unchanged at 244.1pt): v5 217.7pt, v6 94.7pt (56% shorter), v6b 103.1pt (53% shorter). Every label renders at 8pt (one text height in `pdftotext -bbox`). A copy of the paper built with v6 compiles with no errors and puts the figure on p. 7 as Fig. 5.

Data are unchanged: every cycle comes from the v5 trace (InvisiSpec, Spectre model, STT_6 mispredict_not_taken inst-002014; fixture `STAGE3_gem5/tests/fixtures/inv_uv1.pipeview.txt.gz`), re-read on 2026-11-16: i0 F 0, D 1, I 4, retires 8; i1 F 1, D 2, I 6, resolves 5007 (the checker's estimate, complete + 5,000), retires 5013; i2 F 2, D 3, I 40, L1D eviction 70, squash lands 5008.

Still open: DECIDE W-1 (whether the window ends at the squash, as the text and figure say, or at resolution, as the checker does); under (b), move the band's or bar's right edge from 5008 to 5007, as the file header explains. The figure does not show the separate resolution-to-squash scan; §5.2 explains it in prose. Band (v6) or bar (v6b) is Anna's call; if she picks the band, the squash-race figure could later get the same treatment.

### Inspector figure v7 requirements (Anna, 2026-11-16)

Anna likes v6's layout. The next version must: (1) use an STT trace of the clean running-example test (the same test as Fig. 4, no xmm route, found by the clean-example agent; trace from Anna's experimentalist with the gem5 command in `paper_figures/fig2_concretization_example.md` §7), (2) show the real cycle numbers where each event happened, (3) put a dot (or other mark) on the instruction's timeline for EVERY event it mentions; no event may be only written as text, and (4) label the box "Transmission criterion" (confirmed by Anna 2026-11-16).

## Inspector figure v7 and v7b (2026-11-16, inspector-v7-agent)

New ISCA-27 files (paper text, v5/v6 and the `\input` untouched; no git writes): `tikz/checkerwindow_v7_8pt.tex` (STT, no hit) and `tikz/checkerwindow_v7b_8pt.tex` (same test on the undefended Unsafe build, hit), each with `_standalone_*.tex` and a 200 dpi `-1.png`. Both carry `\label{fig:checkerwindow}` and a plain proposed caption ending in a red `\reviewtag`. To switch, change `\input{tikz/checkerwindow_v6_8pt}` in `sections/pipeline.tex` to `_v7_` or `_v7b_`. Data, commands and sha256s: `paper_figures/inspector_v7/README.md`.

Test: `STT_6_u_core_lpP_fv3` inst-023734, mispredict_not_taken (§7 of `fig2_concretization_example.md`), rerun once on cafe3 with the E3 campaign config and the campaign's timing draw (branch held 2,500 cycles), and once with E1's gem5 block (`gem5-recon-modded`, `--scheme=0`). The STT rerun reproduces the campaign record tick for tick. Key cycles (0 = lc's fetch): v7 lc retires 20, branch held from 124 and resolves 2625, xmit's address ready 238 and held by STT, squash lands on xmit 2626, fnc retires 2639. v7b lc retires 19, branch resolves 2612, xmit issues 213 and reads the cache 214, squash lands and fnc retires 2613.

Meets the v7 requirements: every drawn event has its trace cycle on the axis (two tiers of numbers, so cycles one apart stay readable); every event is a mark on its instruction's bar (ticks for F/D/I, dots for retire, hold, ready and resolve, a cross for the squash, the red star for the transmission), with a thin leader line from each label that is not right next to its mark; the box reads "Transmission criterion:" with STT's criterion; the tan window runs from lc's retirement to the squash landing on xmit; STT's hold on xmit is blue. Standalone height 112.0pt each (v6 as built now: 104.2pt; its 2026-11-16 preview: 94.7pt): the second line of the criterion box and the second tier of numbers add the height.

Notes: (1) check_ld labels the E1 transmitter `store_forward`, but the trace shows a cache read with an empty store queue; this is the known Recon-build gate mislabel (`wiki/findings/bug/recon_cache_reach_gate/README.md`) and does not change the verdict; v7b draws a cache access. (2) The rows use Fig. 2's names (i0 = fnc, the branch; i3 = xmit) and lc = the committed load pc0; the captions describe the test as Fig. 2's graph plus a committed load, because Fig. 4 still shows inst-024552 (DECIDE CLEAN-EX). If Fig. 4 moves to inst-023734, the captions can say "the test of Fig. 4".

## Squash-race figure v4 (2026-11-16, inspector-v7-agent)

New ISCA-27 files: `tikz/squashrace_v4_8pt.tex`, `_standalone_squashrace_v4_8pt.tex`, `-1.png` (112.2pt; v3 untouched; labels `fig:racev2`, `fig:race`). Same visual language as Inspector v7, no execution graph on top. Data: `paper_figures/race_v4/README.md`.

Why the test changed: v3's STT trace (inst-047231) came from the old slowed pipeline (commitToIEWDelay 4, iewToCommitDelay 30, squashWidth 1). At the final settings its fnc retires before the packet (DECIDE PT-1), and the final STT race rows were stopped before producing traces. v4 uses SPT test inst-000125, one of the 40 confirmed UV6 tests (SPT-Fence, only commitToIEWDelay raised to 4), re-run once with the trace kept exactly as `confirm_uv6.sh` ran it; the rerun matches its confirmation record. Key cycles (0 = lc's fetch): lc retires 14; branch held from 125, resolves 2626; xmit ready 124, held by SPT (blue), released 2626 (the resolution's visible tick; the release itself is not printed), cache access 2628, squash lands 2630; fnc retires 2640.

Text to pair with it (Anna places it; `sections/results.tex` line 70). Old: "In test inst-047231 (Fig.~\ref{fig:race}), the mispredicted branch i2 resolves at cycle~77, transmitter i5 sends a cache packet at cycle~79, and the squash arrives at cycle~81." New, placed after the SPT-Fence sentence: "In SPT test inst-000125 (Fig.~\ref{fig:race}), the mispredicted branch resolves at cycle~2626, SPT releases the transmitter, the transmitter sends a cache packet at cycle~2628, and the squash arrives at cycle~2630." The STT claim at commitToIEWDelay 3 still rests on inst-047231, which is DECIDE PT-1.

## Figs. 11 and 12 sanity check (2026-11-16, inspector-v7-agent, ISCA-27 1fb5771)

Compiled the paper (scratch copy, latexmk) and read p. 11 at 450 dpi; checked every plotted value against `experiments/2026-11-10_footprint_vs_amulet/code/figvalues_20261116d.py` (re-run) and cafe3 `/tests/timing_20261115/clean_summary.json` / `retime_fast/summary.json`. All plotted values, intervals and multipliers in both bodies equal the script output. AMuLeT's A-UV4 and A-UV5 points are both 179k (4.2k s) because AMuLeT's own one-cause classifier (priority UV3 > UV4 > UV5) gives exactly 4 violations each (6 and 5 without the priority; EVAL_MANIFEST AMuLeT per-bug table). The A-UV5 points use (N+1)/(K+1), which the captions now state (a757ba3). Fig. 12's "1.3–1.7 CPU-seconds" holds: CleanupSpec execution is 1.738 s per test (the 1.75 from 70/40 comes from rounded labels).

Found: (1) Fig. 12's two legend rows were 6.8pt apart at 8pt text, so row 1's descenders touched row 2. New body `tikz/timedet_dots3_v3_body.tex` moves only row 2 down (9.6pt apart); to use it, change `\input{tikz/timedet_dots3_v2_body}` to `\input{tikz/timedet_dots3_v3_body}` in `tikz/timedet_bars_v8_8pt.tex` (line 7); verified in the compiled paper, no reflow. (2) Fig. 12 caption: "0.93 CPU-seconds (about 0.56 to run the Alloy model and 0.38 to concretize and compile the test)" adds up to 0.94, and the Alloy part is a scaled re-time (the results text says "estimated"); exact parts 0.555 + 0.377 (EVAL_MANIFEST "Generation CPU (big corpus, re-timed)"). Proposed: "an estimated 0.93 CPU-seconds (0.555 to run the Alloy model and 0.377 to concretize and compile the test)". (3) Fig. 11: no overlaps or clipping; the 1,655× and 94× multipliers sit on the faint 1M gridline (cosmetic). (4) Comment only: `timedet_bars_v8_8pt.tex`'s header still names figvalues_20261116c.py; the rows are d.py's.

## Timeline figure style (2026-11-16, figs-stl-race-v3; applies to Figs. 5, 7, 8, 10)

Anna's rules (2026-11-16, strict) for every timeline figure, and how the v3/v5/v7c figures meet them. Reference implementations: ISCA-27 `tikz/squashrace_v5_8pt.tex` (simplest), `tikz/reconstl_v3_8pt.tex` (graph on top, four rows), `tikz/checkerwindow_v7c_8pt.tex`; copy their macro block (`\cwflag`, `\cwnum`, `\cwbar`, `\cwgap`, `\cwend`, `\cwdotat`, `\cwcross`, `\cwstarat`) rather than re-deriving it.

1. **Every labeled event is a mark on its instruction's bar at its exact trace cycle.** A filled dot (radius 1.9pt, white rim), the red star (transmission: a cache access or a completed forward), or the cross (squash). A label sits either beside its mark on the bar's centre line (only where the bar has ended there: lc's "Retires", "Squashed") or on a thin vertical leader (0.4pt, black!80) from the mark to the label's bottom or top corner (`\cwflag`, sides e/w/c, two lanes 3.2pt and 3.2+8.6pt from the bar). A stretch (blue hold) gets one label with a leader to each end's mark, or a label at its start mark when its end is already labeled (e.g. the squash cross). No floating labels, and no F/D/I letter ticks: a bar runs from the instruction's fetch (a short closing tick, the cycle on the axis) to its retirement or squash.
2. **No touching text.** No label crosses the violation window's edge lines (a label's fill would hide the edge): keep each label entirely inside or outside the band, using the leader side (e/w/c) and the lane to fit. Labels on the band use a tan fill (`cwband`), outside it white (`cwwhite`), so dotted cycle lines never run through text. Labels of one row stay in that row's lanes; if two rows would share the space between them, move one row's labels to its other side.
3. **One row of cycle numbers.** Uniform scale inside each axis segment, 12–14pt per cycle (14 when four-digit labels must sit two cycles apart near the window edge); elided stretches 7–12pt wide. Two numbers one cycle apart spread away from each other (the earlier anchored north east, ending 1.2pt right of its tick; the later north west, starting 1.2pt left of its tick); three consecutive cycles: outer two spread, middle centred. Widen the elided stretch before a segment until no two numbers touch (check at 300 dpi). Number every bar start and every mark, nothing else.
4. **8pt everywhere, single column (≤ 237.5pt), light semantic fills:** tan = violation window, blue fill = the defense's hold on an instruction (blue ink = defense state, e.g. ReCon's taint), lavender = protected state in the graph, red = transmitter and transmission. Row labels: name on the bar's line (`i<k>: lc`), italic role gloss under it; time origin at x = 57pt.
5. **Real data only:** every drawn cycle is listed with its tick and trace line in the `.tex` header; if an event is not printed (e.g. SPT's release in the v4 trace), rerun with print-only debug flags (IEW, IQ, Commit, DelayUnit) and show that the original trace lines are unchanged, instead of inferring the cycle.
6. **Check in the compiled paper,** not only the standalone: scratch copy of ISCA-27 with the `\input` swapped, `pdftoppm -r 150` and `-r 300`, compare page count and the page where the next section starts.

Captions then say "(notation of Fig.~\ref{fig:checkerwindow})" and Fig. 5's caption defines the marks once: "Each bar runs from an instruction's fetch to its retirement or squash; dots and the cross mark events at their trace cycles, and dotted stretches are elided cycles."

**Fig. 8 v6 (fig8-otb-v5 agent, 2026-11-16):** `tikz/recon_otb_v6_8pt.tex` (+ standalone, 200 dpi png) applies these rules to Fig. 8 v5 (generated test inst-003908). Two departures, both forced by one column at 12 pt per cycle: 507 and 2511 have marks and ticks but no numbers (one of each adjacent pair, as agreed), and v5's "Reads cache" mark on i6 (cycle 126) is dropped. Data and checks: `paper_figures/otb_v5/README.md`.

## ReCon STL figure v3, squash-race figure v5, Inspector figure v7c (2026-11-16, figs-stl-race-v3)

New ISCA-27 files only (paper text and every existing figure untouched; no git writes): `tikz/reconstl_v3_8pt.tex` (Fig. 7, 248.3pt standalone; v2_short 249.4pt), `tikz/squashrace_v5_8pt.tex` (Fig. 10, 119.1pt; v4 112.2pt), `tikz/checkerwindow_v7c_8pt.tex` (Fig. 5, 108.9pt; v7 112.0pt), each with `_standalone_*.tex` and a 200 dpi `-1.png`. A scratch paper build with all three swapped in has 18 pages, the same two pre-existing overfull hboxes as the current paper, and Related Work starting at the same place (p. 13). Data, commands, sha256s and every cycle: `paper_figures/stl_v3/README.md`.

- **Fig. 7 v3:** counted UV2 test of row E2w, `STT_6_u_core_lpP_s2A` inst-014536 (not_taken; inst-014912 is from the June Recon_6 campaign and is not one of the 1,690), rerun on cafe3 exactly as the campaign ran it (hit reproduced, `store_forward`). Graph = the Alloy instance, which has a store-to-load rf edge (drawn). At cycle 114 the store executes, the store queue forwards its value to xmit, `STL_CHECK` reports xmit tainted and speculative, and xmit completes; the branch, held 5,000 cycles, resolves at 5111 and the squash lands at 5112. `STL_CHECK` is SimSpect's debug print of ReCon's taint tracker (`gem5-hooks/gem5-recon-modded/recon-modded_src.diff:339`), not ReCon's own check, so the caption says "ReCon's taint tracker marks i4 tainted".
- **Fig. 10 v5:** same test and trace as v4 plus one rerun with print-only IEW and IQ flags (all 32,510 v4 trace lines unchanged and in order; sim_ticks equal). The new lines show SPT's hold directly ("Deferring load due to virtual fence" at 125) and the release at 2627 (back on the ready list and issued), one cycle after the branch resolves at 2626; v4 drew the release at 2626 by inference. (gem5-spt's own `--trackInstsFile` tracking aborts on this test: `regfile.hh:280` assertion.)
- **Fig. 5 v7c:** v7's data in the style above; fixes v7's two tiers of numbers and the nearly touching "Resolves"/"2,500-cycle hold" labels. Superseded in the paper by `checkerwindow_v8_8pt` (integer version, agent stt-int-fig; ISCA-27 59cd83e), which already has one row of numbers but keeps "F" letter ticks and places "2,500-cycle hold" about 2pt under "Resolves"; to match Figs. 7 and 10, v8 would drop the F letters (a bare closing tick at fetch) and put the hold label under the fnc bar, as v7c does.

## Figs. 4 and 5 in integer form: concretization v2, Inspector v8/v8b and v9/v9b (2026-11-16, stt-int-fig)

Fig. 4 `tikz/concretization_example_v2_8pt.tex` and Fig. 5 `tikz/checkerwindow_v8_8pt.tex` (with `v8b`, Unsafe) show the integer version of `STT_6_u_core_lpP_fv3` inst-023734 (built for the figure with the corpus's own Stage-2 code, only fpr off; no xmm register); the coordinator committed and wired them in (ISCA-27 59cd83e). `tikz/checkerwindow_v9_8pt.tex` / `v9b` redraw v8/v8b's data in the "Timeline figure style" above (v8 has F letter ticks and a hold label under "Resolves"); not wired in: change `\input{tikz/checkerwindow_v8_8pt}` (sections/pipeline.tex:111) to `_v9_` (or `_v9b_`). Scratch paper build with v9 or v9b: 19 pages, same overfull warnings, Related Work still on p. 13. Data, verdicts, every cycle, sha256s: `paper_figures/inspector_v8/README.md`; DECIDE CLEAN-EX-2 in `URGENT_TODO.md`.

## Relaxation figure v3 (Fig. 3, 2026-11-16, fig3-relax-v3)

Anna: "the relaxation graph is messed up and missing labels. too squished maybe". New ISCA-27 files only (paper text and `relaxation_v2_short.tex` untouched, no git writes): `tikz/relaxation_v3_short.tex`, `tikz/_standalone_relaxation_v3_short.tex`, preview `tikz/_standalone_relaxation_v3_short-1.png` (220 dpi). Same panes, notation, colors and caption as v2. Changes: every ddi and rf arrow is labeled in every pane (v2 labeled them only in (d)); "leakage backbone" is now the title on the top border of (d)'s box (in v2 it sat on (d)'s i1 row, against the RI arrowhead and past the tan band); row pitch 21pt in every pane (was 16pt in (a)–(c), 22pt in (d)), 18pt between panes (was 16pt), 26pt from (c) to (d); (b)'s removed rf edge runs in a gutter 6pt further right so it clears the new rf label. All row positions follow from three knobs (`\rlP`, `\rlG`, `\rlGD`). Height 235.8 → 279.9pt (+44pt). Scratch build of the whole paper (ISCA-27 cad0a5b, rechecked at 3363b42; `\input` swapped in a copy): 18 pages and References at the same spot on p.14 in both builds; only p.5's text changes, because the taller figure fills slack that was already below Fig. 3 in the right column (the caption moves down 44pt, the column's text keeps the same lines). Checked at 150, 300 and 900 dpi: no touching text, no arrow through a label (closest gaps about 2.5–3pt: each rf label to the `]` below it, and (b)'s rf label to the dashed removed edge). To use it: `sections/pipeline.tex:49` `\input{tikz/relaxation_v2_short}` → `\input{tikz/relaxation_v3_short}`.

## Whitespace pass (2026-11-16)

Agent fig-whitespace. Base: ISCA-27 `5ebab78` (the brief named `fe179e1`; HEAD moved during the run, and every number below was re-measured at `5ebab78`; tikz files are identical at both). Built in a scratch copy with every note group hidden (switches (1)–(5), the submission view, as in the cut plan `caroline/reviews/2026-11-16_cut_plan.md`), measured in ISCA `review` grid rows (58 per column, 116 per page; the 11-page limit is row 1276). Paper untouched, no git writes. Candidates, standalones and previews: `paper_figures/whitespace_20261116/tikz/`; old/new page crops and both full builds: `paper_figures/whitespace_20261116/pairs/` (open with `paper_figures/whitespace_20261116/open_pairs.sh`). Only spacing changed: every label, mark, number, color and caption is the same.

Method: each figure's height and its gaps were read from the PDF (float positions from `\pdfsavepos` markers, ink extents from 4x renders); then each figure was shrunk alone by 3–44pt (a trailing negative `\vspace` in a scratch copy) to find how much it must shrink before the body end moves. All 13 floats sit at a column top. Below a threshold the freed space only stretches the float gap; above it the body end jumps 6 rows at once (a paragraph boundary on pp. 11–12 re-breaks). Thresholds on the base: Fig. 5 6pt; Figs. 7, 10 15pt; Figs. 6, 8, 9, 11 20pt; Fig. 3, Fig. 4, Table 2 44pt; Fig. 1, Table 1, Fig. 2 more than 44pt. On top of the new build, no unchanged figure moves the body end until it shrinks by 30pt (Figs. 3, 4, Table 2), and Figs. 1, 2, 6, 10, 11, Table 1 not even at 30pt, so further trimming of those buys nothing at this point.

| # | Figure | Old → new | Height saved (measured) | Body end, this figure alone | What changed | Check |
|---|---|---|---|---|---|---|
| 01 | Fig. 1 | `intro_threelayer_v9` (unchanged) | 0 | 0 even at −44pt | none: spacing tuned by Anna 2026-11-14..16, already a −3pt caption skip; L2/L29 are cut-plan text items | |
| 02 | Table 1 | `execvocab_v3_8pt` (unchanged) | 0 | 0 even at −44pt | none: rows at `\arraystretch` 1, already −4pt | |
| 03 | Fig. 2 | `dataflow_v2_8pt` (unchanged) | 0 | 0 even at −44pt | none: only 3.5pt above and 3pt below the drawing | |
| 04 | Fig. 3 | `relaxation_v3_short` (unchanged) | 0 | 0 until −44pt | none: v3 loosened the rows and pane gaps on purpose today ("too squished"); D7 (one pane) stays a cut-plan decision | |
| 05 | Fig. 4 | `concretization_example_v2_8pt` (unchanged) | 0 | 0 until −44pt | none: verbatim listing, no padding, already −6pt | |
| 06 | Table 2 | `instrtable_v2_short` (unchanged) | 0 | 0 until −44pt | none: rule gaps 1.5pt, rows set by text wrap; F3 is a cut-plan text item | |
| 07 | Fig. 5 | `checkerwindow_v9_8pt` → `checkerwindow_v10_8pt` | 11.0pt (104.8 → 93.8pt body) | −6 rows (1401 → 1395) | "Violation window" moves from its own line above the band into the band on lc's row, right-aligned; band starts 5.5pt above lc's bar (was 14.5pt); 9.5pt (was 11.5pt) from the cycle numbers to the criterion box | title is now inside the band, 3.9pt above "Resolves" |
| 08 | Fig. 6 | `stt_xmm4_code_8pt` (unchanged) | 0 | 0 until −20pt (base); 0 at −30pt on the new build | none: 12 code lines at 8/9.5pt in a 2pt-padded box | |
| 09 | Fig. 7 | `reconstl_v3_8pt` → `reconstl_v4_8pt` | 15.7pt (244.2 → 228.5pt) | −6 rows | same title move (centred 2pt above lc's bar, clear of "5,000-cycle hold"); timeline starts 20pt below the graph's last row (was 32pt; 8pt between the two tan bands); store and xmit rows 22pt apart (was 24pt); box gap 9.5pt | graph and timeline are closer; "Forwarded" still clears both bars |
| 10 | Fig. 8 | `recon_otb_v6_8pt` → `recon_otb_v7_8pt` | 19.0pt (251.8 → 232.8pt) | −6 rows | the two-line "Violation window" moves down into the band on i2's row (empty there, tan fill over the dotted lines); band starts 8pt above i2's bar (was 24pt); listing 15pt above i2 (was 28pt), clear of i2's "Resolves"; rows 21pt apart (was 22pt); box gap 9.5pt | listing now sits closer to the timeline |
| 11 | Fig. 9 | `squashrace_v5_8pt` → `squashrace_v6_8pt` | 8.0pt (115.0 → 107.0pt) | 0 alone (it counts in the total) | same title move (centred 4pt above lc's bar); "2,500-cycle hold" uses the style's second lane, 3.2+8.6pt (was 3.2+9.2pt), so it clears the title; box gap 9.5pt | title vs hold label about 3pt apart |
| 12 | Fig. 10 | `firstdet_bars_v9_8pt` (unchanged) | 0 | 0 until −15pt (base); 0 at −30pt on the new build | none (see DECIDE WS-3) | |
| 13 | Fig. 11 | `timedet_bars_v8_8pt` (unchanged) | 0 | 0 until −20pt (base); 0 at −30pt on the new build | none (see DECIDE WS-3) | |

**Total:** 53.7pt of figure height (about 4.9 grid rows of height). Measured body end: page 13, row 1401 → page 12, row 1391 (−10 rows; the Acknowledgments heading moves from row 1404 to the top of page 13, row 1393). Still 115 rows over the row-1276 limit. These are on `5ebab78` without the cut plan's text cuts: once the Free and Low tiers land, the floats re-settle and the per-figure body-end numbers will change; the heights saved do not. All new text measures 7.97bp (8pt) in `figfont_audit.py`; checked at 250 dpi for overlaps (one overlap in a first draft of Fig. 9, title vs hold label, fixed).

**DECIDE items (measured, not applied in the "new" build):**

- [ ] DECIDE WS-1: caption skip 12pt → 6pt for every float (`\captionsetup{skip=6pt}` after `\begin{document}`): −10 rows on the base (1401 → 1391), −12 more on top of the four new figures (1391 → 1379). It changes the template's float spacing, which the ISCA rules ("do not modify margins, fonts, or line spacing") arguably cover. *Recommendation: no.*
- [ ] DECIDE WS-2: `\textfloatsep` 15pt (+8/−5) → 10pt (+4/−3) and `\floatsep` 12pt → 8pt (+4/−2): −10 rows on the base, −8 more on top of the new figures (1391 → 1383). Same template concern. *Recommendation: no.*
- [ ] DECIDE WS-3: Figs. 10 and 11, move the legend into the empty lower-middle plot area (below A-UV4/A-UV5, white backing) and compress the y axis 10%: about 7pt each (the top is set by the multipliers as well as the legend). Not built; on the new build neither figure moves the body end even at −30pt. *Recommendation: no, revisit only after the text cuts.*
- [ ] DECIDE WS-4: Fig. 3, pane gaps 18/26pt → 15/22pt (−10pt), undoing part of today's v3 loosening. Not built; 0 rows unless Fig. 3 shrinks by 30pt or more. *Recommendation: no.*
- No float moves are proposed (not tested in this pass).

**To use an approved figure** (new files only, `cp -n` never overwrites), then change one `\input` line:

- Fig. 5: `cp -n ~/trippel/simspect/paper_figures/whitespace_20261116/tikz/{checkerwindow_v10_8pt.tex,_standalone_checkerwindow_v10_8pt.tex,_standalone_checkerwindow_v10_8pt-1.png} ~/trippel/ISCA-27/tikz/`; in `sections/pipeline.tex:111` change `\input{tikz/checkerwindow_v9_8pt}% moved up to where it is first cited, 2026-11-03` → `\input{tikz/checkerwindow_v10_8pt}% moved up to where it is first cited, 2026-11-03`.
- Fig. 7: `cp -n ~/trippel/simspect/paper_figures/whitespace_20261116/tikz/{reconstl_v4_8pt.tex,_standalone_reconstl_v4_8pt.tex,_standalone_reconstl_v4_8pt-1.png} ~/trippel/ISCA-27/tikz/`; in `sections/results.tex:56` change `\input{tikz/reconstl_v3_8pt}` → `\input{tikz/reconstl_v4_8pt}`.
- Fig. 8: `cp -n ~/trippel/simspect/paper_figures/whitespace_20261116/tikz/{recon_otb_v7_8pt.tex,_standalone_recon_otb_v7_8pt.tex,_standalone_recon_otb_v7_8pt-1.png} ~/trippel/ISCA-27/tikz/`; in `sections/results.tex:64` change `\input{tikz/recon_otb_v6_8pt}` → `\input{tikz/recon_otb_v7_8pt}`.
- Fig. 9: `cp -n ~/trippel/simspect/paper_figures/whitespace_20261116/tikz/{squashrace_v6_8pt.tex,_standalone_squashrace_v6_8pt.tex,_standalone_squashrace_v6_8pt-1.png} ~/trippel/ISCA-27/tikz/`; in `sections/results.tex:76` change `\input{tikz/squashrace_v5_8pt}` → `\input{tikz/squashrace_v6_8pt}`.
- Line numbers are at `5ebab78`; if the F1 patch below is applied first, the `results.tex` lines move down (the `\input` lines themselves are unique).

**Cut-plan items Anna asked for mid-run (2026-11-16):** the agent's edit of `sections/results.tex` was refused by the permission system (the paper is read-only for it), so each is a patch in `paper_figures/whitespace_20261116/cutplan_patches/`, dry-run clean against `5ebab78`: `F1_runin_heads.patch` (six bold run-in heads; also joins UV2's head to its paragraph and adds the paragraph break UV4 needs, without which its head would run into the UV3 paragraph; old heads kept as `%` lines), `F7_tuning_point.patch` (old sentence kept as a `%` line), `F8_fig10_caption.patch` (the A-UV$n$ gloss kept as a `%` line). Apply with `cd ~/trippel/ISCA-27 && patch -p1 < ~/trippel/simspect/paper_figures/whitespace_20261116/cutplan_patches/<name>.patch`. Measured together on `5ebab78` (scratch build): body end 1401 → 1391 (−10 rows).
- Discussion orphans (Anna, mid-run: "fix the orphan words on the coverage and the soundness paragraphs"): "Soundness of the harness" ends on "misprediction." alone (row 1190) and "Coverage limits" on "line." alone (row 1262). Two tested options, each removes both orphans and measures 1401 → 1397 (−4 rows) on `5ebab78`: (a) `discussion_orphans_option_a.patch`, shortest: `UV5 also reproduces on an unmodified build with a natural misprediction.` → `UV5 also reproduces on an unmodified build.` and `an InvisiSpec request that downgrades another core's copy` → `an InvisiSpec request downgrading another core's copy`; (b) `discussion_orphans_option_b.patch`, keeps every fact: `easier to hit than natural timing would, and could break a timing assumption of a defense, though` → `easier to hit than natural timing and could break a defense's timing assumption, though` and `speculation types that would be useful to add:` → `speculation types worth adding:`. Recommendation: (b). Both patches touch only the live (uncommented) lines.
- **In the paper (Anna, 2026-11-16: "the timing figures are good … bold where it says violation window … dark yellow … put the figures and all this in and then push it", then "merge the new branch"):** the four timeline figures went in as new files with the title in bold dark saturated yellow `#8C6400` (4.7:1 contrast on the tan band, dark gray in grayscale; defined inside each figure as `sswintitle`): `checkerwindow_v11_8pt`, `reconstl_v5_8pt`, `recon_otb_v8_8pt`, `squashrace_v7_8pt` (each = the v10/v4/v7/v6 candidate above plus the bold title; copies with standalones and previews in `whitespace_20261116/tikz/`). ISCA-27 `3a5b07d`: the four figures, F1, F7, F8. ISCA-27 `3ebf931`: merge of Overleaf branch `overleaf-2026-11-17-0449` (Anna's new Discussion, keywords, AI-use acknowledgment; the one conflict resolved to the Overleaf version), a stray ``` from the Overleaf paste removed, the Soundness and Coverage orphan words fixed on the new Discussion (`than natural timing would,` → `than natural timing,`; `such as \texttt{xchg}` → `(\texttt{xchg})`; `that downgrades` → `downgrading`), and `{\emergencystretch=2em\par}` after the UV2, UV3 and UV4 paragraphs, whose lines stuck into the margin (up to 34.7pt) after the F1 run-in heads. Pushed to origin/main. Notes-hidden build at `3ebf931`: 17 pages, 0 errors, 0 overfull boxes, body ends page 12, row 1361 (limit 1276).

## Table 1 v4, Fig. 6 v2, Table 2 v3 (2026-11-16)

Candidates in `paper_figures/table2_stt_20261116/` (`tikz/` new files, `pairs/` old/new crops, `open_pairs.sh`), measured on notes-hidden scratch builds of ISCA-27 `6f492f7`. Nothing is in the paper until Anna OKs it.

- **Table 1 → `execvocab_v4_8pt`:** name column 46pt → 39pt (the widest name, "Instructions", is 37pt) and the Flags row drops "(implies resolved)", which §3 states (`model.tex:37`, "committed, which implies resolved"), so Flags fits on one line. Height 108.4pt → 98.9pt.
- **Fig. 6 → `stt_xmm4_code_v2_8pt`:** the two "..." rows move onto code rows (226–227 after line 225's brace; 231–232 before line 233's code, so the line-number gap shows them) and the trailing "..." row is dropped: 12 rows → 7, height 163.0pt → 115.5pt. Code is 8pt typewriter on a 9.5pt pitch (the 8pt minimum). Fig. 6 has no `\ref` in the text (`fig:sttxmm4` is only labeled).
- **Table 1 v4 + Fig. 6 v2 together:** References start below row 1335 → 1331 with the green cuts kept, 1304 → 1298 with switch (7).
- **Table 2 → `instrtable_v3_short` (not recommended):** flags "unresolved"/"resolved" under the kind and the left column 83pt → 65pt. Narrowing alone (83 → 77pt) changed no row. v3 is 11.6pt shorter with the green cuts kept, but 14.2pt taller with switch (7), because once the cycle counts are cut the left cells are the tallest.
- To use: `cp -n ~/trippel/simspect/paper_figures/table2_stt_20261116/tikz/{execvocab_v4_8pt,stt_xmm4_code_v2_8pt}.tex ~/trippel/ISCA-27/tikz/`; in `sections/model.tex` change `\input{tikz/execvocab_v3_8pt}` → `\input{tikz/execvocab_v4_8pt}`; in `sections/results.tex` change `\input{tikz/stt_xmm4_code_8pt}` → `\input{tikz/stt_xmm4_code_v2_8pt}`.

## Relaxation 2×2 grid (2026-11-16)

Agent fig3-grid. Anna: "is there any way to redesign the relaxation figure so that we can put it in a grid of 4." New candidate files only (paper untouched, no git writes): `paper_figures/relaxation_grid_20261116/relaxation_v4_grid.tex`, `_standalone_relaxation_v4_grid.tex` and the preview `_standalone_relaxation_v4_grid-1.png` (300 dpi). Old and new standalone renders and page crops, all at one scale, are in `relaxation_grid_20261116/pairs/`; open them with `relaxation_grid_20261116/pairs/open_pairs.sh`. A true 2×2 works at 8pt in one column (`figure`, not `figure*`): (a) and (b) on top, (c) and (d) below. Each pane is about half the column: tan bands 113pt wide, (d)'s box 119pt, 241pt in all.

- **Same content:** every word v3 prints appears in the grid the same number of times (pdftotext word counts are identical). Every ddi and rf arrow is still labeled in every pane, and the row pitch is still 21pt. Colors, the gray and dashed removed parts, the purple highlighter, the red xmit flag and the caption are unchanged (caption verbatim, checked by diff).
- **What moved:** (1) the pane letters sit on a header line above each pane, because a letter left of i0 no longer fits at half width. (d)'s letter joins its border title, "(d) leakage backbone", and (c)'s header shares that baseline. (2) Each relaxation label is one line ("RS: unneeded r1", "RI: extra load i3", "RR: resolve i1") directly under its source pane, at the tail of its arrow: a→d runs diagonally, b→d straight down and c→d straight across under (c), all into (d)'s box. (3) The operand columns are packed to a word space or more and the flag words share one column; Branch_n still ends left of the ddi label above i1. (4) (b)'s removed rf edge runs in a gutter to the right of i2's xmit. (5) (d)'s box has sharp corners, because properties are sharp (rule of 2026-11-15); v3's box was rounded.
- **Why this layout:** putting each label under its own pane keeps it next to its source. RS uses the empty fourth row under (a) for free, since (b) has four rows, and RI fits between (b) and (d)'s title. The c→d arrow can't carry its label in the gap between (c) and (d): the gap is 9pt and "resolve i1" alone is 29pt. So RR sits under (c), which costs about 6pt. Two alternatives were checked and rejected. Column-major, (a) (c) over (b) (d), saves nothing once the RI label has to sit under (b). (d) wide on top with (a) (b) (c) in one row needs at least 110pt per pane, but three across gives 80pt.
- **Checks:** all 103 text spans measure 7.97bp (8pt), both in the paper build (`scripts/figfont_audit.py`) and in the standalone. The body has no `\scriptsize`, `\tiny` or scaling. No two text spans overlap (`relaxation_grid_20261116/tools/textgap.py`). The closest gaps: each rf label sits 0.85pt (between font boxes) from the `]` below it, the same as in v3. It also sits 1.4pt across and about 3pt up from the xmit below and to its right, which is new, so check it visually. The figure reads in grayscale: xmit is dark gray, removed parts light gray, and the leak path black on its highlighter. The build has 0 overfull boxes and 0 errors.
- **Measured** on a scratch copy of ISCA-27 `6f492f7` with every note group hidden (switches (1)–(5)) and the `\input` swapped in the copy; the grid has 58 rows per column, and row 1276 is the end of page 11. The height drops from 279.9pt to 189.7pt standalone, and the float with its caption from 364.9pt to 274.4pt (33.3 → 25.0 grid rows, −90.5pt). The body end (last line of the Acknowledgments) moves from row 1333 to 1323 (−10 rows; References heading 1335 → 1325; 16 → 15 pages). With switch (7) also on (the green cuts applied), it moves from row 1302 to 1293 (−9 rows; References 1304 → 1296): 26 → 17 rows over the limit. Both results hold with the figure 10pt taller or shorter. Fig. 3 moves from the top of p.6, left column (above Fig. 4), to the top of p.5, right column.
- **Layout-dependent:** at the brief's base `ead06d8`, before Anna's orphan commit `6f492f7`, the same figure gave −10 rows with notes hidden but only −1 row with switch (7). There the freed space fell into stretched columns on pp. 6–7 (two new badness-10000 underfull columns) until Fig. 3 shrank about 14pt more. Re-measure after further cuts.
- **With Table 1 v4 and Fig. 6 v2** (section above, same base): the body end moves from row 1333 to 1314 (−19) with notes hidden, and from 1302 to 1280 (−22) with switch (7), which is 4 rows over row 1276.
- **Caption:** no change proposed. "Each relaxes to (d) by the relaxation on its arrow" still holds, because each label sits at the tail of its arrow, as in v3 (where it sat above the arrow's first segment).
- **To use** (new files only; `cp -n` never overwrites): `cp -n ~/trippel/simspect/paper_figures/relaxation_grid_20261116/{relaxation_v4_grid.tex,_standalone_relaxation_v4_grid.tex,_standalone_relaxation_v4_grid-1.png} ~/trippel/ISCA-27/tikz/`. Then, in `sections/pipeline.tex:54` (line number at `6f492f7`; the line itself is unique), change `\input{tikz/relaxation_v3_short}% the one relaxation figure (your four panes, redrawn), 2026-11-03` → `\input{tikz/relaxation_v4_grid}% the one relaxation figure (your four panes, redrawn), 2026-11-03`. Like v3's, the standalone compiles from the paper root (`\input{tikz/relaxation_v4_grid}`).

- 2026-11-16 later: **v5 grid (`relaxation_v5_grid`, in the paper at ISCA-27 `37d287c`)**, Anna: "make sure that all the arrows point from the box not from the text, to the other box". Each relaxation arrow now starts on its pane's band edge ((a) and (c) from the bottom edge near the right corner, (b) exactly at its band bottom) and ends on (d)'s box; the RS and RR labels are right-aligned beside their arrow starts (RI already was). v4 kept.

## Figs. 10–11 merged (2026-11-16)

Agent fig10-11-merge. Anna: "we could put figure 11 in the same figure as the other one. could you try that". New candidate files only (paper untouched, no git writes), in `paper_figures/detection_merge_20261116/`: `tikz/detection_v1_8pt.tex` (the figure: body, combined caption, both labels), `tikz/detection_v1_body.tex` (one tikzpicture holding both panels), `tikz/_standalone_detection_v1_8pt.tex` and its preview `-1.png` (250 dpi); variant **v1b** (`detection_v1b_8pt.tex`, `detection_v1b_body.tex`, standalone and preview) is v1 with 10% shorter log axes (`\fdu` 0.40 → 0.36 cm per decade), nothing else changed. Old Fig. 10, old Fig. 11, v1 and v1b standalone at one scale (250 dpi), plus page 10 before and after, are in `pairs/`; open them with `pairs/open_pairs.sh`. Measuring tools in `tools/` (`bodyend.py`, `floats.py`, `phr.py` = row of a phrase, `rotgap.py` = overlap check that handles rotated labels, `hook.tex`).

- **What changed:** one single-column `figure`: (a) tests per detection on top, (b) CPU time to detect below, with panel letters (a)/(b) at each panel's top left. Shared: the bug-label row and the defense row (InvisiSpec / CleanupSpec / SpecLFB) print once, under (b), since the six groups sit at the same x in both panels; one legend, in (a)'s top whitespace (● SimSpect light blue, ● with generation dark blue, ■ AMuLeT gray); one caption. Kept per panel: each y axis and its label, gridlines, the dashed separator before jmp*, every value label, error bar and multiplier. (a) is placed automatically 0.14 cm above (b)'s tallest multiplier (A-UV5's 0.050×/0.032×).
- **Same numbers:** every data row of both loops is identical to `firstdet_dots_v2_body.tex` (minus its bug-label field, now printed under (b)) and `timedet_dots3_v3_body.tex` (checked by script, v1 and v1b). The dagger on A-UV5 and the asterisk on jmp print once, under (b); the caption's dagger note covers both panels.
- **Legend:** colors unchanged (the same three RGB definitions in both old bodies): light blue = SimSpect without generation in both panels, dark blue = SimSpect with generation (only in (b)), gray = AMuLeT. Labels changed: (a)'s "SimSpect tests" → "SimSpect" and "AMuLeT test cases" → "AMuLeT"; (b)'s "SimSpect:" / "execution only" / "with generation" → "SimSpect" / "with generation". The caption still says "execution only (light blue)" and "896,000 test cases". Legend rows are 0.34 cm (9.6pt) apart, as in timedet v3.
- **Heights:** the float with its caption goes from 203.4pt + 231.1pt = 434.5pt (two floats, each with a 15pt `\textfloatsep`) to 383.7pt (one float): −50.8pt, or −65.8pt counting the float gap, about 6.1 grid rows (626pt / 58 rows = 10.8pt). Standalone bodies: 128.9pt + 134.6pt → 242.8pt (borders included). v1b: 366.6pt float, −82.9pt with the gap, about 7.7 rows. The caption is 12 lines, against 6 + 8 = 14 for the two old ones; the rest of the saving is the bug-label row, one caption skip and one float gap.
- **Rows** (References heading row; scratch copy of ISCA-27 `37d287c` with switches (1)–(5) on and the `\input` swapped in the copy; 58 rows per column): green cuts kept: 1317 → 1311 (−6) with v1, 1311 (−6) with v1b. Switch (7) on: 1298 → 1296 (−2) with v1, 1293 (−5) with v1b. Both builds: 15 pages, 0 overfull boxes, 0 undefined references.
- **Why only −2 with switch (7):** the merged figure takes the top of p.10's left column, and that column now ends just before the §7 heading (Discussion moves to the top of the right column), so about 3 rows of the freed space become stretch. Markers: Related Work 1193 → 1189 (−4), Conclusion 1280 → 1277 (−3), References 1298 → 1296. v1b's extra 17pt recovers it. This is layout-dependent; re-measure after further cuts.
- **Checks:** all 98 text spans are 7.97bp (8pt) in the paper build (`scripts/figfont_audit.py`) and in the standalone; no `\scriptsize`, `\tiny` or scaling. `tools/rotgap.py` finds no overlap that old Fig. 11 did not already have: the 7 rotated value-label pairs in (b) (e.g. 2.7/4.5, 70/107/88) touch only at font-box level, as in `timedet_dots3_v3`, and their digits are clear at 600 dpi. Grayscale: light circle, dark circle and gray square stay distinct. No bold title sentence starts the caption.
- **Caption old → new** (everything else verbatim): (1) Fig. 10's "Expected tests per detection …" → "(a) Expected tests per detection …"; (2) Fig. 11's "CPU time to detect each bug: …" → "(b) CPU time to detect each bug: …"; (3) "times tests per detection (Fig.~\ref{fig:firstdetv2})." → "times tests per detection in (a)."; (4) the two dagger notes, Fig. 10's "(95\% interval: 0.8--19$\times$)." and Fig. 11's "$^{\dagger}$95\% interval for A-UV5's ratio with generation: 0.007--0.17$\times$.", → one note ending "(95\% intervals: 0.8--19$\times$; with generation, 0.007--0.17$\times$)." (the longer "95\% interval for its ratio with generation: …" left a one-word 13th caption line).
- **Proposed text tweaks (not applied; quote current text → new):** (T1, needed: with both labels on one figure it prints "Figs. 10 and 10") `results.tex:100` "error bars in Figs.~\ref{fig:firstdetv2} and~\ref{fig:timedet} are 95\% Clopper-Pearson intervals on each side's detection rate." → "error bars in Fig.~\ref{fig:firstdetv2} are 95\% Clopper-Pearson intervals on each side's detection rate." (T2) `results.tex:100` "for which it needs about $3.7\times$ fewer (Fig.~\ref{fig:firstdetv2})." → "for which it needs about $3.7\times$ fewer (Fig.~\ref{fig:firstdetv2}a)." (T3) `results.tex:103` "and the rare A-UV5 about $31\times$ faster (Fig.~\ref{fig:timedet})." → "and the rare A-UV5 about $31\times$ faster (Fig.~\ref{fig:timedet}b)." (T4) `intro.tex:335` "which we miss} (Fig.~\ref{fig:firstdetv2})." → "which we miss} (Fig.~\ref{fig:firstdetv2}a)." and "the rare cleaning-too-much bug by about $31\times$ (Fig.~\ref{fig:timedet})." → "the rare cleaning-too-much bug by about $31\times$ (Fig.~\ref{fig:timedet}b)." Style precedent for "Fig. Na": `results.tex:196`/`:204` (`Fig.~\ref{fig:timing}a`, inside an `\iffalse` block).
- **To use** (new files only; `cp -n` never overwrites): `cp -n ~/trippel/simspect/paper_figures/detection_merge_20261116/tikz/{detection_v1_8pt.tex,detection_v1_body.tex,_standalone_detection_v1_8pt.tex,_standalone_detection_v1_8pt-1.png} ~/trippel/ISCA-27/tikz/`. Then in `sections/results.tex:97` change `\input{tikz/firstdet_bars_v9_8pt}` → `\input{tikz/detection_v1_8pt}`, and at `sections/results.tex:104` comment out `\input{tikz/timedet_bars_v8_8pt}` → `% \input{tikz/timedet_bars_v8_8pt}% merged into detection_v1_8pt (2026-11-16)`. For v1b, copy the four `detection_v1b` files instead and use `\input{tikz/detection_v1b_8pt}`. Apply T1 in the same commit.
- **DECIDE (Anna):** (1) v1 or v1b (v1b: 10% shorter axes, decades 10.2pt apart instead of 11.3pt; same rows with the cuts kept, 3 more rows with switch (7)); recommendation v1b if the denser axis reads well in `pairs/new_v1b.png`. (2) the shared legend's wording (loses "tests"/"test cases" in (a) and "execution only" in (b); the caption still carries both); alternative: two compact legends as before, which costs no height because both sit in whitespace.

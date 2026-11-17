## 2026-11-17 01:25 — whole paper, final pass on the OLD criteria (ISCA-27 ef1784e)

Scope: abstract, §1–§9 and every caption of the figures and tables the paper inputs (Figs. 1–10, Tables 1–2). Criteria: Caroline's D1–D5, Anna's D6, machine-sounding prose, the e.g./i.e. comma rule, `PAPER_AUDIT_GUIDELINES.md` §9/§9b, "Canonical terms" and "Front-of-paper terms", `CAROLINE.md`. Built from the working tree at 01:02 (`latexmk` into /tmp/finalold, 15 pages: body plus acknowledgments end at the bottom of page 11, references pp. 12–15). Settled items not re-flagged: Fig. 1, "three components", labels = microarchitectural state, `\S\ref` without tilde, single hyphens, the locked abstract (factual errors only), Protean's timing leak. Every quoted old text was re-checked with `grep -F` against ISCA-27 ef1784e (01:22): each occurs exactly once in live text; where grep finds two hits, the second is a commented-out (%) copy, so edit the uncommented one. Line numbers are hints only.

Mechanical checks, all clean: no `e.g.`/`i.e.` without a following comma in any live section or caption; no `\S~\ref`, `Sec.~`, `Section~\ref`, `Figure~\ref`, `Fig.\ref` or `Table\ref`; no word--word double hyphen; no undefined references in the log. One rendered note remains (🔴 F1 below).

Line model for the estimates: an ACM two-column page holds about 58 lines per column (≈116 per page) at about 60 characters per line; a cut saves its characters ÷ 60, rounded down unless it ends a paragraph or removes a paragraph break.

## (1) Structural pass

**Abstract (locked).** Job: problem, three parts, results. Does it. One factual error: "per detection of each known bug" (F2); the paper's "known bugs" are seven and include Protean's two, which SimSpect misses (intro "Prior work found seven such bugs", §7 "Known bugs we miss").

**§1 Introduction.** Job: problem (simulated defenses have no security check) → why prior testing falls short (AMuLeT: random programs, contract/adversary-model granularity) → SimSpect's three parts → results. Order is right and each paragraph has one goal. Problems: (a) the novelty sentence claims "first" (F3, D6); (b) the AMuLeT-granularity paragraph's conclusion "No pairing of contract and adversary model can match such a guarantee exactly" is stronger than the support §2.2 gives ("matches no contract built from these modes") (F4); (c) the "requires targeted tests" claim conflicts with AMuLeT finding bugs with random tests (D-1); (d) the executor paragraph defines "speculation conditions" in parentheses and uses "transmission criterion" undefined (M-items); (e) the last paragraph's \anna note renders in the PDF (F1). Redundancy with later sections: the "no attacker, probe program, or second run" sentence is repeated verbatim in §5 (cut it there, C19); the bug list is fine as a close paraphrase of §6.2.

**§2 Background.** Job: give the reader the defenses tested (§2.1), the contract vocabulary SimSpect is positioned against (§2.2), and the axiomatic/litmus lineage (§2.3). §2.1 and §2.3 do their job. §2.2 carries one off-narrative sentence (SNI/weak SNI, used nowhere else: C3) and a disambiguating parenthetical about AMuLeT's use of "leakage contract" (C11). The adversary-model paragraph restates the intro's granularity argument with the STT-store example that §6.1 gives a third time (A-KV3); keep one concrete copy (C33, optional).

**§3 Defense Specification.** Job: define execution graphs, the three components, the predicate, and STT as the running example. Does it, but ¶1 ends with a prefetching sentence about the synthesizer and Inspector (C6, Anna's STRICT no-prefetching rule), §3.2 defines the transmission criterion only to say it is not part of the section's object (C8), and the section still says "candidate execution graphs", "Candidate Executions" and "microarchitectural status" against the decided terms (M-items).

**§4 Synthesizer.** Job: specification → backbones → extended graphs → tests. The roadmap paragraph restates each subsection's opening (Alloy, the backbone definition, "grows", the exhaustive/sampled split) and ends with a prefetch to §5; compress it to a roadmap and move the two definitions into §4.1/§4.2 (C2). The per-subsection Input/Output lines repeat the subsection headings and the previous subsection's output (C5, DECIDE). Each design choice has an independent reason (six-instruction bound: enumeration finishes; eight: tractable solves; committed instruction: SPT/ReCon update through commits; vector version: x86 register classes; random cache state: no specification fixes it), so no "bug-only" justification remains.

**§5 Executor.** Job: run, steer, check; define violation → hit → leak → bug. Does it. Redundancies: the §5 intro repeats the intro's "no attacker" clause (C19); §5.2's "two passes" sentence is an implementation detail with no stated content (C18); Fig. 5's transmission-criterion box repeats §5.2's STT example word for word (C4).

**§6 Results.** Job: replicate known bugs, present six new bugs, compare with AMuLeT on tests and time. Order is right. Problems: "every previously known bug" in §6.3 includes Protean's two (F2); UV4's "its patch for A-UV6 would also close this bug" rests on a code reading of a patch that is not in AMuLeT's paper (F5); UV5's "which AMuLeT's analysis would attribute to A-UV6" asserts what another tool's authors would conclude (F6); UV5's "always" is ambiguous (M-item); UV3 calls the 500-cycle resolved-branch delay a "hold" (M-item). The out-of-scope paragraph in §6.1 justifies A-KV2 twice (instruction cache, and CleanupSpec's constant-time future work: C12).

**§7 Discussion.** Job: threats (harness soundness, the non-default delay, what we count, specifications, completeness, coverage, misses, generality). Each paragraph has one goal. Redundancy: "What we count" re-defines a hit verbatim from §5 (C15); "Completeness" repeats §4.1's UNSAT/three-instruction sentence and §4.3.3's Pass 4 sentence (C13); "Coverage" repeats §4.3.2's store-bypass sentence (C14).

**§8 Related Work.** Job: position against testing tools (AMuLeT closest), formal foundations, litmus synthesis, defenses and their known leaks. The AMuLeT paragraph ends with an overclaim, "so only locating the responsible code in the defense is manual", which contradicts §5's manual confirmation that a hit is not an artifact (F7). The "Spectre Defenses" first paragraph lists defenses SimSpect does not test (C29, optional for space).

**§9 Conclusion.** Job: one-paragraph restatement. Its second sentence repeats the intro's "requires targeted tests" claim (D-1) and can go (C34).

**Cross-section consistency.** "500-cycle hold" (UV3, Fig. 8) vs §5.1's hold/delay split; "SPT-Fence" (UV6, Fig. 9) never defined; "jmp*" (Fig. 10) is a banned label; "our STT model", "store shadows", "corpus", "re-concretizations", "branch-stall", "wrong path", "squash lands", "ReCon's underlying implementation", "Protean's extension of AMuLeT" are all on the canonical-terms "Not" list.

## (2) Space-saving cuts, ranked (total ≈ 120 lines ≈ 1.03 pages; "safe" items alone ≈ 66 lines, "safe" + "trim" ≈ 92)

Ranked by lines saved per unit of risk. Each loses no claim the paper needs. "safe" = no content lost; "trim" = loses a detail stated elsewhere; "DECIDE" = Anna's design choice.

- [ ] C1 (≈2 lines, safe, also 🔴 F1) main.tex: `% % \renewcommand{\anna}[1]{\unskip}\renewcommand{\todo}[1]{\unskip}\renewcommand{\figtodo}[1]{\unskip}% (1) hides your notes` → `\renewcommand{\anna}[1]{\unskip}\renewcommand{\todo}[1]{\unskip}\renewcommand{\figtodo}[1]{\unskip}% (1) hides your notes`. The \anna note after "per detection of each of AMuLeT's bugs" renders on p. 3 (two lines). Also uncomment switches (2) and (3) for the submission build so no \reviewnote/\caroline can render.
- [ ] C2 (≈5 lines, safe) pipeline.tex:10, replace the whole §4 opening paragraph. Old (first and last words): `The synthesizer turns a defense's specification (\S\ref{formalmodel}) into security litmus tests in three stages:` … `every test keeps its backbone's forbidden transmission. The executor then runs each test (\S\ref{sec:executor}).` → `The synthesizer turns a defense specification (\S\ref{formalmodel}) into security litmus tests in three stages: Stage~1a enumerates leakage backbones (\S\ref{sec:test-generation-alloy}), Stage~1b extends each into larger violating graphs (\S\ref{sec:stage1b}), and Stage~2 concretizes each graph into tests (\S\ref{sec:concretization-phase}). Only Stage~1a is exhaustive; Stages~1b and~2 sample.` Then move the two definitions: pipeline.tex:26 `Stage~1a enumerates the leakage backbones.` → `Stage~1a enumerates every \emph{leakage backbone}: a minimal graph that violates the leakage predicate.`; pipeline.tex:60 `Stage~1b adds instructions to each backbone to test how` → `Stage~1b adds instructions to each backbone, forming \emph{extended execution graphs}, to test how`. Removes the Alloy repeat, "grows" (banned), the undefined "forbidden transmission" and the prefetch to §5.
- [ ] C3 (≈5 lines, safe) background.tex:54, delete the sentence that starts `Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant weak SNI` and ends `makes every program weakly SNI.` SNI and weak SNI appear nowhere else in the paper (D4).
- [ ] C4 (≈9 lines of figure height, trim) delete the four "rule" boxes, each of which restates the paragraph beside it: comment out the two lines `\node[draw=sssrcink, fill=sssrcbg, line width=0.4pt, anchor=north west, inner xsep=1.8pt, inner ysep=2.2pt] at (0,\cwyK)%` + `{\parbox{\cwtw pt}{\raggedright\textit{Transmission criterion:} …` in tikz/checkerwindow_v12_8pt.tex:153–154 (≈2), the same pair ending `\textit{ReCon-STT rule:} …` in tikz/reconstl_v6_8pt.tex:218–219 (≈3; also removes the banned "ReCon-STT"), `\textit{ReCon rule:} …` in tikz/recon_otb_v9_8pt.tex:201–202 (≈2), and `\textit{SPT rule:} …` in tikz/squashrace_v8_8pt.tex:166–167 (≈2). Check each preview: if `\cwyK`/`\ovyK` is also used by an invisible bounding node, that node must go too.
- [ ] C5 (≈6 lines, DECIDE) comment out the three subsection Input/Output lines, which repeat the subsection heading and the previous output; keep the section-level ones (§3, §4, §5): pipeline.tex:24 `\stageio{a defense specification: (leakage contract, execution contract, protection set)}{leakage backbones of at most six instructions}`, pipeline.tex:57 `\stageio{leakage backbones of at most six instructions}{extended execution graphs of at most eight instructions}`, pipeline.tex:71 `\stageio{extended execution graphs of at most eight instructions\newline}{security litmus tests: (program, target execution)}`.
- [ ] C6 (≈2.5 lines, safe, also 🟠 prefetching) model.tex:18, delete `The leakage predicate is the synthesizer's defense-specific input (\S\ref{sec:synthesizer}), and the defense's transmission criterion is the Inspector's (\S\ref{sec:transmission-requirement}).` (Anna's STRICT no-prefetching rule: the model section discusses only the model.)
- [ ] C7 (≈2 lines, safe) model.tex:16, delete the roadmap `We first define candidate execution graphs (\S\ref{sec:execution-syntax}), then the three components and the predicate they form (\S\ref{sec:leakage-predicate}), and then specify STT as an example (\S\ref{sec:example-contract}). ` (the three subsection headings carry it; also removes the banned "candidate execution graphs"). If kept, at least `candidate execution graphs` → `execution graphs`.
- [ ] C8 (≈2 lines, safe) model.tex:51, delete `The events that count as a transmission, the defense's \emph{transmission criterion}, are not part of the leakage predicate (\S\ref{sec:transmission-requirement}).` and define it where it is used, pipeline.tex:152 `What counts as a transmission is the defense's transmission criterion (\S\ref{sec:leakage-predicate}), which we write from the defense's paper.` → `What counts as a transmission is the defense's \emph{transmission criterion}, which we write from the defense's paper and which is not part of the leakage predicate.`
- [ ] C9 (≈3 lines, safe) intro.tex:312, `\toolname{} replicates every bug found by AMuLeT in that scope: InvisiSpec's speculative L1D eviction, CleanupSpec's three cleanup bugs (an uncleaned speculative read-modify-write, an uncleaned line-crossing access, and cleaning too much), and SpecLFB's unprotected first load (\S\ref{sec:known-bugs}).` → `\toolname{} replicates all five bugs AMuLeT found within the affected defenses' security guarantees (\S\ref{sec:known-bugs}).` (also fixes the vague "in that scope"; §6.1 names them).
- [ ] C10 (≈2 lines, safe) intro.tex:335, `Each of its tests costs more CPU time to run, but, counting test generation, it detects three of these bugs $4.9\times$ to $53\times$ faster than AMuLeT on the same number of cores, while AMuLeT detects two CleanupSpec bugs faster: the uncleaned read-modify-write by about $1.2\times$, and the rare cleaning-too-much bug by about $31\times$ (Fig.~\ref{fig:timedet}).` → `Its tests cost more CPU time each, but, counting test generation, on the same number of cores it detects three of these bugs $4.9\times$ to $53\times$ faster than AMuLeT, and two CleanupSpec bugs about $1.2\times$ and $31\times$ slower (Fig.~\ref{fig:timedet}).`
- [ ] C11 (≈2 lines, trim) background.tex:69, delete ` (AMuLeT instead uses ``leakage contract'' for a whole hardware-software contract~\cite[\S 2.1]{amulet})`. Keep it if you expect AMuLeT's authors as reviewers.
- [ ] C12 (≈2.5 lines, safe) results.tex:41, delete `CleanupSpec also leaves a constant-time cleanup to future work~\cite[\S 4(b)]{saileshwar2019cleanupspec}, so the timing difference behind unXpec is a stated limit of the design rather than a departure from it. ` (A-KV2 is already excluded by the preceding instruction-cache sentence).
- [ ] C13 (≈3 lines, safe) discussion.tex:21, `For every specification except SPT's, it reaches UNSAT and no leakage backbone has more than three instructions (\S\ref{sec:test-generation-alloy}); SPT's enumeration stops` → `SPT's enumeration stops` (repeats §4.1), and delete `Pass~4, which interleaves additional chains of dependent instructions (\S\ref{sec:conc-interleave}), is off in our evaluation.` (stated in §4.3.3); then in pipeline.tex:103 `is off in our evaluation (\S\ref{sec:discussion}).` → `is off in our evaluation.`
- [ ] C14 (≈1.5 lines, safe) discussion.tex:26, delete `Under store bypass, it builds only a load that aliases the older store but is predicted not to (\S\ref{sec:speculation-primitive-instrumentation}).` (§4.3.2 says it: "we do not realize the reverse case").
- [ ] C15 (≈2 lines, safe) discussion.tex:12, `We check each simulated Spectre defense only against the security guarantee its own paper states, with no adversary model: a hit is a run in which the target transmitter meets the defense's transmission criterion inside the violation window, even if no particular attacker could measure it.` → `We check each simulated Spectre defense only against its own paper's security guarantee, with no adversary model, so a hit need not be measurable by any particular attacker.` and `, so we cannot tell whether it is intended, but we note that ReCon as implemented does not taint floating-point loads.` → `, so we cannot tell whether it is intended.`
- [ ] C16 (≈1.5 lines, safe, also 🟠 D6) results.tex:103, `Generation is a one-time cost, and the generated tests are reused when a defense is patched; AMuLeT generates programs inside its fuzzing loop, so its time per detection already includes generation.` → `AMuLeT generates programs inside its fuzzing loop, so its time per detection includes generation.` (reuse after a patch is never shown).
- [ ] C17 (≈2 lines, safe) tikz/relaxation_v5_grid.tex:117 caption, delete `(a) also specifies i2's destination $r1$; (b) adds a second load i3 from $[r0]$; (c) also marks i1 unresolved. ` (each arrow already says it: "RS: unneeded r1", "RI: extra load i3", "RR: resolve i1").
- [ ] C18 (≈1.5 lines, safe) pipeline.tex:150, delete `The Inspector checks this window in two passes: up to each such branch's resolution, and from the resolution to the squash.` (implementation detail; the reader cannot say what each pass checks).
- [ ] C19 (≈1 line, safe) pipeline.tex:115, `, so detection needs no attacker, probe program, or second run (\S\ref{sec:transmission-requirement})` → ` (\S\ref{sec:transmission-requirement})` (verbatim in the intro; Caroline: "close paraphrase of the abstract is fine; verbatim repetition is not").
- [ ] C20 (≈1 line, safe) pipeline.tex:33, delete `The well-formedness axioms and the leakage predicate are those of \S\ref{formalmodel}. ` (constraints (1) and (3) one sentence earlier already point to §3.1 and §3.2).
- [ ] C21 (≈1 line, safe) pipeline.tex:60, `Minimality drops RI, so the graph may hold instructions the leak does not need, while RR, RC, and RS still apply.` → `Minimality drops RI but keeps RR, RC, and RS.` (the paragraph's first sentence says why).
- [ ] C22 (≈2 lines, safe) results.tex:94, `We claim the race only for squashes slower than gem5's default (\S\ref{sec:discussion}): \texttt{commitToIEWDelay}~$=3$ triggers it on STT, and at the default of~1 the squash arrives first.` → `It needs \texttt{commitToIEWDelay}~$=3$ on STT; at gem5's default of~1 the squash arrives first (\S\ref{sec:discussion}).` and `re-running 40 of them with the campaign's timing confirms the full signature in all 40, as in Fig.~\ref{fig:race}` → `re-running 40 of them confirms the sequence of Fig.~\ref{fig:race} in all 40` ("campaign" and "full signature" are undefined).
- [ ] C23 (≈1 line, safe, also 🔴 F6) results.tex:87, `When we run AMuLeT's fuzzer on SpecLFB, it also triggers this bug, in 47 of 248 violations, which AMuLeT's analysis would attribute to A-UV6 (\S\ref{sec:discussion}).` → `AMuLeT's fuzzer also triggers this bug on SpecLFB, in 47 of 248 contract violations (\S\ref{sec:discussion}).`
- [ ] C24 (≈1 line, safe) model.tex:38, delete ` (an MCM's rf relates only memory events, \S\ref{sec:bg-axiomatic})`.
- [ ] C25 (≈1 line, safe) intro.tex:301, `Each graph yields several tests, with different instructions and both branch directions, so the defense is tested on more than one realization of each leak (\S\ref{sec:concretization-phase}).` → `Each graph yields several tests, with different instructions and both branch directions (\S\ref{sec:concretization-phase}).`
- [ ] C26 (≈1 line, safe) intro.tex:326, `The race appears when gem5's \texttt{commitToIEWDelay}, a stock, core-wide gem5 parameter, is raised from its one-cycle default to 3 or 4 cycles (\S\ref{sec:discussion}).` → `The race appears when gem5's stock, core-wide \texttt{commitToIEWDelay} parameter is raised from its one-cycle default to 3 or 4 cycles (\S\ref{sec:discussion}).`
- [ ] C27 (≈1 line, safe) results.tex:35, `(A-UV5, 5 tests from 3 programs)` → `(A-UV5)` (the Fig. 10 caption gives the 5 detections, and "programs" vs "tests" is never explained here). Also results.tex:41 `A-KV2 (unXpec~\cite{li2022unxpec}: a squashed load that missed takes longer to clean up, visible in later instruction fetches~\cite[\S 4.6]{amulet})` → `A-KV2 (unXpec~\cite{li2022unxpec}, \cite[\S 4.6]{amulet})` (≈1 more line; the sentence goes on to say it is seen only through the instruction cache).
- [ ] C28 (≈1 line, safe) background.tex:79, delete `MCMs define the values that loads in a parallel program may return~\cite{lcms}. ` and background.tex:49 delete `A contract is named by its pair, e.g., \contract{CT-SEQ}. ` (≈1 more line; "CT-SEQ" reads as the pair of CT and SEQ two sentences later).
- [ ] C29 (≈7 lines, DECIDE: loses citations, no claim) related.tex:14, delete the paragraph that starts `Spectre defenses vary in the side channels and kinds of speculation they address` and ends `\cite{tran2020clearing,zhao2020invarspec,hajiabadi2024levioso}.` Its defenses are never tested or discussed. Keep it if the cited authors are likely PC members.
- [ ] C30 (≈3 lines, trim) related.tex:8, delete `Pomset~\cite{disselkoen2019code}, axiomatic~\cite{ponce2022cats}, and out-of-order operational~\cite{guanciale2020inspectre} semantics model speculative execution, and STT comes with a pen-and-paper proof over a formal processor model~\cite{yu2019sttformal}. ` and related.tex:3 `Scam-V~\cite{nemati2020scamv} validates side-channel models against hardware, and software tools test programs for Spectre gadgets~\cite{oleksenko2020specfuzz} or against leakage models~\cite{barthe2024lmtest}. ` (≈2.5 more lines).
- [ ] C31 (≈11 lines, DECIDE) delete Fig. 6 (`\input{tikz/stt_xmm4_code_v2_8pt}` in results.tex:54). UV1's text already gives `rob_impl.hh:229`, the index-16 check, the register class and both commits; the figure adds the code lines only.
- [ ] C32 (≈3 lines, safe) Fig. 10: the two stacked panels leave ≈1 line of white space above (a) and between (a) and (b) (p. 10, left column); reduce each axis' `height` in tikz/detection_v1b_body.tex by ≈10% and delete `, on a log scale` from the caption (both axes say "(log)").
- [ ] C33 (≈5 lines, trim) background.tex:66, delete the paragraph `An adversary model observes only microarchitectural state, so it cannot tell which instruction changed it: …` through `report leaks outside the guarantee (\S\ref{sec:known-bugs}).` The intro states the argument and §6.1 gives the STT-store example (A-KV3). If cut, apply F4's scoped wording in the intro.
- [ ] C34 (≈2.5 lines, safe, also D-1) conclusion.tex:5, delete `Security bugs leave no trace in architectural outputs, so exposing them requires targeted tests, each attempting a leakage the defense forbids. `
- [ ] C35 (≈1.5 lines, trim) tikz/recon_otb_v9_8pt.tex:207 caption, delete `i3 is speculative under branch i2, and i6 under the mispredicted branch i4. ` (the trace labels say "Older branch", "Mispredicted", "Older source", "Younger source").
- [ ] C36 (≈1 line, safe) results.tex:53, `The check is also at line 229 of STT's master branch, commit 5bf4110~\cite{sttmaster}.` → `It is unchanged on STT's master branch~\cite{sttmaster}.`
- [ ] C37 (≈1 line, safe) pipeline.tex:105, `(e.g., integer and SSE arithmetic, shifts, bit operations, conditional moves, \texttt{nop}s, and a direct \texttt{jmp} to the next instruction)` → `(e.g., SSE arithmetic, conditional moves, \texttt{nop}s, and a direct \texttt{jmp} to the next instruction)`.

- [ ] C38 (≈1.5 lines, safe) results.tex:75, delete `Any instruction that reads two tainted registers, such as an \texttt{add}, loses the younger source the same way.` (the mechanism sentence already says "an instruction with several tainted operands passes on only the oldest one's taint"; no test shows the add case).
- [ ] C39 (≈1 line, safe, also 🟠 D6) related.tex:16, delete ` \toolname{} finds such bugs with one method for every specified defense.` ("such bugs" follows a list of design-level leaks that SimSpect does not find, so it reads as an overclaim).
- [ ] C40 (≈1 line, safe) results.tex:61 `Fig.~\ref{fig:reconstl} shows this in generated test inst-014536. ` → delete and end the previous sentence `(\texttt{lsq\_unit.cc:2019}, Fig.~\ref{fig:reconstl})`; results.tex:71 `: Fig.~\ref{fig:otb} shows this in generated test inst-003908.` → ` (Fig.~\ref{fig:otb}).` (both captions name the test).
- [ ] C41 (≈1 line, safe) discussion.tex:8, `This stock gem5 parameter is set once per run and changes no defense logic, but it changes the simulated microarchitecture, so we report UV6 with it.` → `It changes no defense logic but changes the simulated microarchitecture, so we report UV6 with it.`
- [ ] C42 (≈1 line, safe) pipeline.tex:152, `Throughout this window the run matches the graph's commit boundary, and the instructions` → `Throughout this window the instructions` (the window's definition already fixes lc and fnc).
- [ ] C43 (≈1 line, safe) drop repeated defense citations in §6 (each defense is cited in §2.1): results.tex:27 `InvisiSpec~\cite{yan2018invisispec}, CleanupSpec~\cite{saileshwar2019cleanupspec}, and SpecLFB~\cite{cheng2024speclfb}` → `InvisiSpec, CleanupSpec, and SpecLFB`; results.tex:34–35 `On InvisiSpec~\cite{yan2018invisispec},` → `On InvisiSpec,`, `On CleanupSpec~\cite{saileshwar2019cleanupspec},` → `On CleanupSpec,`, `On SpecLFB~\cite{cheng2024speclfb},` → `On SpecLFB,`.
- [ ] C44 (≈1.5 lines, trim) intro.tex:138–140, delete `Since AMuLeT's contracts capture` / `architectural leakage only, such violations stem from` / `speculative execution.` (three source lines).
- [ ] C45 (≈1 line, trim) background.tex:16, delete `, which a receiver observes to infer that operand`.
- [ ] C46 (≈2 lines, trim) background.tex:6, delete `An out-of-order core makes program control-flow and data-flow predictions and executes younger instructions speculatively before each prediction is checked.` (standard for ISCA readers; the next sentence defines speculation primitives).
- [ ] C47 (≈4 lines, DECIDE) the Acknowledgments block (main.tex `\begin{acks}` … `\end{acks}`). Caroline's comment asks whether the AI-use statement counts against the page limit; if the ISCA 2027 CFP allows it on the submission form or outside the limit, move it there. Unverified: I did not open the CFP.

Tally: C1 2, C2 5, C3 5, C4 9, C5 6, C6 2.5, C7 2, C8 2, C9 3, C10 2, C11 2, C12 2.5, C13 3, C14 1.5, C15 2, C16 1.5, C17 2, C18 1.5, C19 1, C20 1, C21 1, C22 2, C23 1, C24 1, C25 1, C26 1, C27 2, C28 2, C29 7, C30 5.5, C31 11, C32 3, C33 5, C34 2.5, C35 1.5, C36 1, C37 1, C38 1.5, C39 1, C40 1, C41 1, C42 1, C43 1, C44 1.5, C45 1, C46 2, C47 4 = ≈120 lines (≈1.03 pages). Safe ≈ 66, trim ≈ 26 (C4, C11, C30, C33, C35, C44, C45, C46), DECIDE ≈ 28 (C5, C29, C31, C47). The 0.7-page target (≈81 lines) needs every safe item plus about half of the trim items, or the safe items plus C5 and C31. Line estimates are ±30%: rebuild after each block.


## (3) Findings by section, in paper order (🔴 blocker / 🟠 major / 🟡 minor)

Items already covered by a cut above point to it ("→ Cn") and are not repeated.

### Abstract (locked: factual errors only)

- 🔴 F2a [D3/D6 factual] abstract.tex:24 `per detection of each known bug.` → `per detection of each of these bugs.` The paper's "known bugs" are seven (intro "Prior work found seven such bugs in five simulated Spectre defenses"), including Protean's two, which SimSpect misses (§7 "Known bugs we miss"); the 3.7×–1,655× range covers only AMuLeT's five.

### §1 Introduction

- 🔴 F1 [FORMAT] intro.tex:335 the note `\anna{changed from ``to first detect the previously known bugs'': …}` renders on p. 3 (two violet lines in the submission PDF). → C1 (hide switch (1) in main.tex), or delete the note.
- 🔴 F3 [D6 overclaim] intro.tex:247–248 `the` (end of line 247) + `first targeted and automated approach` → `a` + `targeted and automated approach`. "First" is an absolute novelty claim; CheckMate (§2.3) already synthesizes targeted security litmus tests automatically, so a reviewer only needs one counterexample in scope; `PAPER_AUDIT_GUIDELINES.md` §7b bans "first" without the closest prior work named next to it. The three parts state what is new.
- 🔴 F4 [D6 overclaim] intro.tex:163 `No pairing of contract and adversary model` → `No pairing of these contracts and adversary models`. The only support, background.tex:66, is scoped: the guarantee "matches no contract built from these modes".
- 🟠 O7 [§9b rules 1–2] intro.tex:310 `transmits, by the defense's transmission criterion, while the target execution's speculation conditions still hold (which branches are unresolved and which instructions are uncommitted).` → `transmits, as the defense's paper defines transmission, while the target execution's unresolved branches are still unresolved and its uncommitted instructions uncommitted.` "Transmission criterion" is undefined in the intro, "speculation conditions" is used nowhere else and is defined in parentheses.
- 🟠 D-1 [D6 overclaim vs Caroline] intro.tex:90–91 `exposing them requires targeted tests that` (and conclusion C34). AMuLeT exposes five of these bugs with random tests, so "requires" is contradicted by §6. DECIDE below.
- 🟠 D-2 [D6 put-down vs Caroline] intro.tex:143 `AMuLeT relies heavily on luck to find violations.` DECIDE below.
- 🟡 [TERM] intro.tex:321 `In ReCon's underlying implementation of STT,` → `In ReCon's implementation of STT,`.
- 🟡 [TERM] intro.tex:321 `releases a younger wrong-path transmitter` → `releases a younger transient transmitter` ("wrong-path" is not a paper term; the intro defines "transient").
- 🟡 [TERM] intro.tex:335 `In part because its tests target leaks,` → `In part because its tests are targeted,` (canonical: not "its tests target leaks").
- 🟡 [§9b rule 9, paraphrase test] intro.tex:321 `SpecLFB (4) misimplements its ROB walk order, so` → `SpecLFB (4) checks loads in the wrong order, so`. A reader who has not seen §6.2 cannot say what a "ROB walk order" is.
- 🟡 [D2] intro.tex:312 `in that scope` is vague → fixed by C9.
- 🟡 [TERM, pending T-2; apply only if decided] intro.tex:310 `The executor runs each test on the defense's gem5 prototype` → `The executor runs each test on the simulated defense`.
- Cuts here: C9, C10, C25, C26, C44.

### §2 Background

- 🟠 [D4] background.tex:54 SNI/weak SNI sentence, used nowhere else → C3.
- 🟡 [D1] background.tex:69 AMuLeT parenthetical → C11; background.tex:66 adversary-model paragraph duplicates the intro and §6.1 → C33 (optional).
- Checked: background.tex:69 "the most widely used, the constant-time contract" is supported, RTL2MµPATH §II-B (`papers/rtl2mupath_micro24.txt:245`): "The most widely adopted leakage contract, the constant-time (CT) contract".
- Cuts here: C3, C11, C28, C33, C45, C46.

### §3 Defense Specification

- 🟠 O1 [prefetching, Anna STRICT] model.tex:18 → C6.
- 🟠 O2 [TERM, decided 2026-11-17] model.tex:34 `annotated with their microarchitectural status.` → `labeled with their microarchitectural state.` (the intro says "labeled with their microarchitectural state").
- 🟠 O3 [TERM, T-4] model.tex:30 `\subsection{Candidate Executions}` → `\subsection{Execution Graphs}`; model.tex:16 `candidate execution graphs` → `execution graphs` (or delete the roadmap, C7). "Candidate execution" is the MCM term §2.3 defines; using it for SimSpect's graphs merges the two.
- 🟡 [TERM] model.tex:48 `that the defense promises to not leak transiently.` → `that the defense protects at each program point.` (canonical: not "promises to not leak"; matches the intro's definition).
- 🟡 [prefetching] model.tex:51 transmission-criterion sentence → C8.
- Cuts here: C6, C7, C8, C24.

### §4 Synthesizer

- 🟠 [D1/D5, prefetch, TERM "grows"] pipeline.tex:10 roadmap restates §4.1–§4.3 and ends with a pointer to §5 → C2.
- 🟡 [D2] pipeline.tex:60 `draws a capped number of graphs per backbone` gives no number; state the cap (e.g., `draws at most N graphs per backbone`) from the run configuration. Unverified: I did not look up N.
- 🟡 [D1] pipeline.tex:103 `is off in our evaluation (\S\ref{sec:discussion}).` → `is off in our evaluation.` once C13 removes the §7 copy. The two descriptions of Pass 4 also differ ("can add a second, independent speculative source" vs §7's "interleaves additional chains of dependent instructions"); C13 keeps only the first.
- Cuts here: C2, C5, C17, C20, C21, C37.

### §5 Executor

- 🟠 [FORMAT] pipeline.tex:146–148 the manual hyphenation `after the last committed instru-` + `\noindent ction (lc) retires` will print "instru- ction" mid-line as soon as any cut above moves the column break. After the cuts, restore `after the last committed instruction (lc) retires` on one line.
- 🟡 [TERM] pipeline.tex:152 `a resolved branch on the wrong path is not checked` → `a resolved branch that is itself transient is not checked`.
- 🟡 [TERM] pipeline.tex:152 `stay transient until its squash lands` → `stay transient until the branch's squash reaches them` (canonical: no undefined "squash lands").
- Cuts here: C18, C19, C42 (and C8's §5.2 replacement).

### §6 Results

- 🔴 F2b [D3/D6] results.tex:100 `We compare how many tests each tool needs to detect each previously known bug.` → `We compare how many tests each tool needs to detect each of AMuLeT's bugs.`; results.tex:100 `fewer tests for every previously known bug except A-UV5` → `fewer tests for each of AMuLeT's bugs except A-UV5`; tikz/detection_v1b_8pt.tex:11 `(a) Expected tests per detection of each previously known bug and of` → `(a) Expected tests per detection of each of AMuLeT's bugs and of`. "Previously known bugs" include Protean's two, which have no bar.
- 🔴 F5 [D3 unsupported] results.tex:81 `and its patch for A-UV6 would also close this bug.` → `and, by our reading of the code, a patch for A-UV6 in AMuLeT's repository would also close it.` The AMuLeT paper has no gem5 patch for A-UV6; the repository patch was committed by accident and reverted (amulet-gem5 commit 5f9ac78), and "would close" is a prediction from recorded flags plus code reading, not a run (simspect `wiki/findings/audits/2026-10-28/hooks_speclfb_and_uv6.md:7–19`). If you have since run the patched build, cite that run instead.
- 🔴 F6 [D3/D6 put-down] results.tex:87 `which AMuLeT's analysis would attribute to A-UV6` asserts what another tool's authors would conclude → C23.
- 🟠 O4 [TERM, consistency] results.tex:71 `without the swept 500-cycle hold, i2 would resolve` → `without the swept 500-cycle delay, i2 would resolve`, and tikz/recon_otb_v9_8pt.tex:207 `after a 500-cycle hold` → `after a 500-cycle delay`. §5.1 holds unresolved branches for 2,500/5,000/10,000 cycles and delays resolved ones by 0/500/2,500; the sentence itself cites Table 2 row 2 (resolved branch). Check i2's flag in inst-003908 before changing.
- 🟠 O5 [D2/D6 "always"] results.tex:87 `A test reaches it when a direct jump lies between the mispredicted branch and a later load: always with a flushed or filled cache.` → `Every test that triggers it has a direct jump between the mispredicted branch and a later load, and a flushed or filled cache.` The current sentence can be read as "every such test triggers it" (sufficient) or "every trigger had a flushed or filled cache" (necessary); keep only what the data shows.
- 🟠 O6 [D6 promise] results.tex:103 "the generated tests are reused when a defense is patched" is never shown → C16.
- 🟡 [TERM] results.tex:34 `AMuLeT~\cite{amulet} reports nine bugs in these defenses;` → `AMuLeT~\cite{amulet} reports nine vulnerabilities in these defenses;` (four are out of scope, so not bugs by §5's definition; the next sentence's "its four other reports" already uses the neutral word).
- 🟡 [TERM] results.tex:63 `tests from our STT model reach the bug` → `tests from STT's specification reach the bug`; results.tex:63 `whose execution contract adds store shadows` → `whose execution contract adds store bypass`; results.tex:75 `tests from our STT model show this bug` → `tests from STT's specification show this bug`.
- 🟡 [TERM] results.tex:94 `even on the wrong path: a wrong-path load's result stops being tainted` → `even when it is transient: a transient load's result stops being tainted`.
- 🟡 [TERM, T-6] results.tex:94 `SPT-Fence~\cite{spt} lifts its fence` and tikz/squashrace_v8_8pt.tex caption `on a gem5 trace of SPT-Fence running` use an undefined variant name. Either `SPT-Fence` → `SPT` in both, or define it once in §6's first paragraph (DECIDE D-7).
- 🟡 [TERM] results.tex:100 `drawing the cache state and the branch-stall timing at random for each test` → `drawing the cache state and the timing setting at random for each test`; results.tex:100 `run the first 4{,}000 tests of one corpus, and CleanupSpec all 291{,}860 tests of two corpora and three random re-concretizations of the first.` → `run the first 4{,}000 tests of one suite, and CleanupSpec all 291{,}860 tests of two suites and three further random concretizations of the first.`
- 🟡 [TERM] tikz/squashrace_v8_8pt.tex caption `which closes when the squash lands at 2630.` → `which closes when the squash reaches xmit at 2630.`
- 🟡 [TERM] Fig. 10: caption `(jmp$^{*}$, UV5)` → `(UV5)` and the x-axis tick `{jmp$^{\textstyle *}$}` → `{UV5}` in tikz/detection_v1b_body.tex:36 (canonical: not "jmp*").
- 🟡 [D3] results.tex:103 `Generating a test takes an estimated 0.93 CPU-seconds` does not say how it was estimated; add the basis (e.g., `0.93 CPU-seconds, averaged over N tests,`) or drop `an estimated`. Unverified: N not looked up.
- 🟡 [TERM] tikz/reconstl_v6_8pt.tex:219 box `\textit{ReCon-STT rule:}` uses the banned "ReCon-STT"; C4 deletes the box, otherwise → `\textit{ReCon's STT:}`.
- Cuts here: C12, C16, C22, C23, C27, C31, C32, C35, C36, C38, C40, C43.

### §7 Discussion

- 🟡 [TERM] discussion.tex:30 `Protean's extension of AMuLeT found` → `Protean's fuzzer found` (canonical; §8 already says "Protean's fuzzer").
- 🟡 [machine-sounding/defensive] discussion.tex:12 `but we note that` → C15.
- Cuts here: C13, C14, C15, C41.

### §8 Related Work

- 🔴 F7 [D6 overclaim] related.tex:5 `so only locating the responsible code in the defense is manual.` → `so manual work reduces to confirming each hit on its trace and locating the responsible code.` §5 (pipeline.tex:115) defines a leak as a hit "that we confirm, on its trace, is not a harness or Inspector artifact", which is manual.
- 🟠 [D6 overclaim] related.tex:16 `\toolname{} finds such bugs with one method for every specified defense.` follows a list of design-level leaks SimSpect does not find → C39.
- Cuts here: C29, C30, C39.

### §9 Conclusion

- 🟠 [D6, D1] conclusion.tex:5 the "requires targeted tests" sentence repeats the intro → C34 (and D-1).

### Captions not covered above

- Fig. 1: settled, not reviewed. Table 1, Table 2, Fig. 4, Fig. 6: no finding beyond C31. Fig. 2: no finding. Fig. 5: C4. Fig. 3: C17. Fig. 7: C4. Fig. 8: O4, C35. Fig. 9: SPT-Fence, "squash lands". Fig. 10: F2b, jmp*, C32. No caption opens with a bold title.

### First-time-reader pass (intro terms used before definition)

| term | first use | defined? | action |
|---|---|---|---|
| transmission criterion | intro.tex:310 | no (defined in §3.2/§5.2) | O7 |
| speculation conditions | intro.tex:310 | parenthetical only, never used again | O7 |
| ROB walk order | intro.tex:321 | no | 🟡 above |
| visibility point | intro.tex:321 | no (§2.1); named only, the clause after it explains the race | none |
| taint | intro.tex:321 | intro ¶2 has "taint-track" as a verb only | none (standard) |
| contract observations | intro.tex:131 | pointer to §2.2 | none |

### DECIDE

- D-1 "requires targeted tests" (intro.tex:90–91, conclusion.tex:5). (A) Keep: Caroline asked for it (intro.tex:68 comment: "I would say that the targeted is required, and they ``get lucky'' … we should make sure this sentiment is articulated explicitly"); delete only the conclusion copy (C34). (B) Scope it to the evidence: `exposing them requires targeted tests that` → `exposing them efficiently requires targeted tests that` (Fig. 10 supports "efficiently"; AMuLeT's random tests do expose five bugs). Recommendation: B plus C34.
- D-2 intro.tex:143 `AMuLeT relies heavily on luck to find violations.` (A) Keep (Caroline's "get lucky" sentiment). (B) `AMuLeT finds violations by chance.` (shorter, states the same fact without "relies heavily on luck"). Recommendation: B.
- D-3 C5, subsection Input/Output lines (your 2026-11-16 design) vs ≈6 lines.
- D-4 C29, related-work defenses paragraph (citations, PC politics) vs ≈7 lines.
- D-5 C31, Fig. 6 (code evidence for UV1) vs ≈11 lines.
- D-6 C47, acknowledgments inside or outside the page limit (check the ISCA 2027 CFP).
- D-7 "SPT-Fence": define it once or replace it with "SPT" (canonical terms, pending T-6).
- D-8 "gem5 prototype" in intro.tex:310 (pending T-2).

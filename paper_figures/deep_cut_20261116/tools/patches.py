# Deep-cut patch definitions against ISCA-27 8587638. Each patch: (id, name, tier, [edits]).
# Edit forms: ('r', file, old, new) replaces text on one live line (old line kept as a % comment);
#             ('block', file, start, end, new) comments out live lines start..end and inserts new.
I = 'sections/intro.tex'; B = 'sections/background.tex'; M = 'sections/model.tex'; P = 'sections/pipeline.tex'
R = 'sections/results.tex'; D = 'sections/discussion.tex'; W = 'sections/related.tex'
T = lambda n: 'tikz/' + n + '.tex'

PATCHES = [
# ---------------- FREE ----------------
('01', 'related_widows', 'Free', [
  ('r', W, r'In gem5, SpecCheck~\cite{mckevitt2023speccheck} identifies vulnerable transient execution in a running program.',
           r'In gem5, SpecCheck~\cite{mckevitt2023speccheck} identifies vulnerable transient execution at run time.'),
  ('r', W, r'or require programmers to change memory layout~\cite{green2023safebet,kim2024perspective}',
           r'or require memory-layout changes~\cite{green2023safebet,kim2024perspective}'),
]),
('02', 'spec_repeats', 'Free', [
  ('r', M, r"and the defense's transmission criterion is the Inspector's (\S\ref{sec:transmission-requirement}).",
           r"and the transmission criterion the Inspector's (\S\ref{sec:transmission-requirement})."),
  ('r', M, r'A leakage predicate combines three components, each adapted from prior work (\S\ref{sec:bg-contracts}):',
           r'A leakage predicate combines three components (\S\ref{sec:bg-contracts}):'),
  ('r', M, r"A defense's guarantee needs this detail: whether the defense lets an instruction transmit depends on which older branches are still unresolved",
           r'Whether a defense lets an instruction transmit depends on which older branches are unresolved'),
  ('r', M, r" (an MCM's rf relates only memory events, \S\ref{sec:bg-axiomatic})", ''),
]),
('03', 'synth_repeats', 'Free', [
  ('r', P, r', running the solver until no graph is left (UNSAT) for every defense except SPT, whose enumeration we cap (\S\ref{sec:discussion})', ''),
  ('r', P, r' The executor then runs each test (\S\ref{sec:executor}).', ''),
  ('r', P, r'Stage~2 writes it as an annotation beside the program. Fig.~\ref{fig:concretization} shows an excerpt of one test.',
           r'Stage~2 writes it as an annotation beside the program (Fig.~\ref{fig:concretization}).'),
  ('r', P, r'\subsubsection{Instruction Choice}\label{sec:instruction-choice}', r'\noindent\textbf{Instruction Choice.}\label{sec:instruction-choice}'),
  ('r', P, r'\subsubsection{Speculation Primitives}\label{sec:speculation-primitive-instrumentation}', r'\noindent\textbf{Speculation Primitives.}\label{sec:speculation-primitive-instrumentation}'),
  ('r', P, r'\subsubsection{State Assignment And Compilation}\label{sec:conc-interleave}', r'\noindent\textbf{State Assignment And Compilation.}\label{sec:conc-interleave}'),
]),
('04', 'circular_pointers', 'Free', [
  ('r', P, r'is off in our evaluation (\S\ref{sec:discussion}).', r'is off in our evaluation.'),
  ('r', D, r' Pass~4, which interleaves additional chains of dependent instructions(\S\ref{sec:conc-interleave}), is off in our evaluation.', ''),
  ('r', P, r'a load that mispredicts an alias (\S\ref{sec:discussion}).', r'a load that mispredicts an alias.'),
  ('r', D, r' Under store bypass, it builds only a load that aliases the older store but is predicted not to (\S\ref{sec:speculation-primitive-instrumentation}).', ''),
]),
('05', 'background_roadmap_widow', 'Free', [
  ('r', B, r'This section covers the Spectre defenses we test', r'We cover the Spectre defenses we test'),
]),
('06', 'results_repeats', 'Free', [
  ('r', R, r', whose execution contract adds store shadows (\S\ref{sec:example-contract})', ''),
  ('r', R, r', drawing the cache state and the branch-stall timing at random for each test (\S\ref{sec:speculation-directives})', ''),
  ('r', R, r'Finally, STT assumes that stores are performed only at retirement', r'STT assumes that stores are performed only at retirement'),
]),
('07', 'discussion_repeats', 'Free', [
  ('r', D, r', so we cannot tell whether it is intended, but we note that ReCon as implemented does not taint floating-point loads.', r', so we cannot tell whether it is intended.'),
  ('r', D, r"so SPT's specification untaints less than SPT does and can forbid executions that SPT permits.", r"so SPT's specification untaints less than SPT and can forbid executions SPT permits."),
]),
('08', 'caption_table_repeats', 'Free', [
  ('r', T('relaxation_v3_short'), r" (a) also specifies i2's destination $r1$; (b) adds a second load i3 from $[r0]$; (c) also marks i1 unresolved.", ''),
  ('r', T('timedet_bars_v8_8pt'), r'\toolname{} execution only (light blue), with test generation (dark blue), and AMuLeT (gray)', r'\toolname{} execution only, with test generation, and AMuLeT'),
  ('r', T('instrtable_v2_short'), r'(notation of Table~\ref{tab:execvocab}; lc, fnc: last committed, first uncommitted)', r'(notation of Table~\ref{tab:execvocab})'),
  ('r', T('instrtable_v2_short'), r'; one test per misprediction direction. \textbf{Executor:} forced to mispredict; resolution held 2{,}500, 5{,}000, or 10{,}000 cycles.', r'. \textbf{Executor:} forced to mispredict; resolution held.'),
  ('r', T('instrtable_v2_short'), r'\textbf{Executor:} forced correct; resolution delayed 0, 500, or 2{,}500 cycles.', r'\textbf{Executor:} forced correct; resolution delayed.'),
  ('r', T('instrtable_v2_short'), r'i0 and i1 share an address, in inline asm so the compiler cannot forward.', r'i0 and i1 share an address.'),
]),
]
FIG1_NEW = r"\caption{\toolname{} tests a simulated Spectre defense against a specification of its own security guarantee; AMuLeT~\cite{amulet} tests it against a hardware-software contract~\cite{guarnieri2021contracts}, which can be weaker than the guarantee, so testing can miss bugs, or stronger, so it can report leaks the guarantee excludes."
PATCHES += [
# ---------------- LOW ----------------
('09', 'fig1_caption_optionB', 'Low', [
  ('block', T('intro_threelayer_v9'), r'\caption{\toolname{} has three parts:', 'leaks.', FIG1_NEW),
]),
('10', 'intro_targeted', 'Low', [
  ('r', I, r' Each graph yields several tests, with different instructions and both branch directions, so the defense is tested on more than one realization of each leak (\S\ref{sec:concretization-phase}).', r' (\S\ref{sec:concretization-phase}).'),
  ('r', I, r"\toolname{} replicates every bug found by AMuLeT in that scope: InvisiSpec's speculative L1D eviction, CleanupSpec's three cleanup bugs (an uncleaned speculative read-modify-write, an uncleaned line-crossing access, and cleaning too much), and SpecLFB's unprotected first load (\S\ref{sec:known-bugs}).",
           r"\toolname{} replicates all five of AMuLeT's bugs in that scope (\S\ref{sec:known-bugs})."),
  ('r', I, r'(1) STT fails to taint one register: a check that skips register index 16 ignores the register class, so a secret copied through the low half of \texttt{xmm4} loses its taint.',
           r'(1) STT fails to taint a secret copied through the low half of \texttt{xmm4}.'),
  ('r', I, r"In ReCon's underlying implementation of STT,", r"In ReCon's implementation of STT,"),
  ('r', I, r"The race appears when gem5's \texttt{commitToIEWDelay}, a stock, core-wide gem5 parameter, is raised", r"The race appears when gem5's \texttt{commitToIEWDelay} is raised"),
  ('block', I, "Since AMuLeT's contracts capture", 'speculative execution.', ''),
  ('r', I, r'cryptographic libraries (secret keys)~\cite{cauligi2020constanttime}, operating system kernels (kernel memory)~\cite{inspectre}, and web browsers (cross-origin secrets)~\cite{spook}.',
           r'cryptographic libraries~\cite{cauligi2020constanttime}, operating system kernels~\cite{inspectre}, and web browsers~\cite{spook}.'),
  ('r', I, r'In part because its tests target leaks,', r'In part because its tests are targeted,'),
  ('r', I, r'while AMuLeT detects two CleanupSpec bugs faster: the uncleaned read-modify-write by about $1.2\times$, and the rare cleaning-too-much bug by about $31\times$ (Fig.~\ref{fig:timedet}).',
           r'while AMuLeT detects two CleanupSpec bugs $1.2\times$ and $31\times$ faster (Fig.~\ref{fig:timedet}).'),
]),
('11', 'stage1a_list_to_sentence', 'Low', [
  ('r', P, r'A solution graph must satisfy three kinds of constraint:', r'A solution graph satisfies the defense-agnostic well-formedness axioms (\S\ref{sec:execution-syntax}) and minimality criteria and violates the defense-specific leakage predicate (\S\ref{sec:leakage-predicate}).'),
  ('block', P, r'\begin{enumerate}', r'\end{enumerate}', ''),
  ('r', P, r'The well-formedness axioms and the leakage predicate are those of \S\ref{formalmodel}. ', ''),
]),
('12', 'spec_roadmap', 'Low', [
  ('r', M, r' We first define candidate execution graphs (\S\ref{sec:execution-syntax}), then the three components and the predicate they form (\S\ref{sec:leakage-predicate}), and then specify STT as an example (\S\ref{sec:example-contract}).', ''),
]),
('13', 'stage2_pass6_7', 'Low', [
  ('r', P, r'; the specification does not fix which register holds it, so we draw one at random', ''),
  ('r', P, r'The compiler cannot drop, reorder, or re-register an instruction the graph specifies: each non-branch one is an \texttt{asm sideeffect} block, which LLVM must assume has side effects it cannot see~\cite{llvmlangref}, and each register the graph fixes is pinned by its register constraint.',
           r'Because each non-branch instruction is an \texttt{asm sideeffect} block~\cite{llvmlangref} and each register the graph fixes is pinned by a register constraint, the compiler cannot drop, reorder, or re-register an instruction the graph specifies.'),
]),
('14', 'executor_details', 'Low', [
  ('r', P, r", so detection needs no attacker, probe program, or second run (\S\ref{sec:transmission-requirement})", r" (\S\ref{sec:transmission-requirement})"),
  ('r', P, r" The annotation gives each instruction's PC, each branch's misprediction direction and BTB target, which instruction is the transmitter, and for store bypass the (store, load) pair whose load must mispredict no alias.", ''),
  ('r', P, r" Print-only hooks log events that a build does not otherwise print, such as a branch's prediction and resolution.", ''),
  ('r', P, r"The Inspector checks this window in two passes: up to each such branch's resolution, and from the resolution to the squash.", ''),
  ('r', P, r" (InvisiSpec's include the D-TLB)", ''),
]),
('15', 'known_bugs_details', 'Low', [
  ('r', R, r' CleanupSpec also leaves a constant-time cleanup to future work~\cite[\S 4(b)]{saileshwar2019cleanupspec}, so the timing difference behind unXpec is a stated limit of the design rather than a departure from it.', ''),
  ('r', R, r'; every detection had a flushed or filled cache, none a warm one (\S\ref{sec:speculation-directives})', ''),
  ('r', R, r' (A-UV5, 5 tests from 3 programs)', r' (A-UV5)'),
]),
('16', 'new_bugs_details', 'Low', [
  ('r', R, r" The check is also at line 229 of STT's master branch, commit 5bf4110~\cite{sttmaster}.", r" The check is also in STT's master branch~\cite{sttmaster}."),
  ('r', R, r'since ReCon assigns taint at rename: without the swept 500-cycle hold, i2 would resolve at cycle~6, before the merge is renamed at cycle~121, and ReCon would hold i7 (Table~\ref{tab:instrtable}, row~2).',
           r'since ReCon assigns taint at rename; the swept resolution delay provides this (Table~\ref{tab:instrtable}, row~2).'),
  ('r', R, r': a \texttt{mov} or \texttt{cqto} reading its old destination (12 tests, as in Fig.~\ref{fig:otb}), or an arithmetic instruction reading the old flags (5)',
           r': a \texttt{mov} or \texttt{cqto} reading its old destination (as in Fig.~\ref{fig:otb}) or an arithmetic instruction reading the old flags'),
  ('r', R, r' Loads after the first speculative load can therefore go unprotected as well.', ''),
  ('r', R, r"; re-running 40 of them with the campaign's timing confirms the full signature in all 40, as in Fig.~\ref{fig:race})", r'; Fig.~\ref{fig:race})'),
]),
('17', 'timing_env', 'Low', [
  ('r', R, r"; both tools' per-test costs are measured on the same idle node, each keeping about 16 hardware threads busy", ''),
]),
('18', 'discussion_restatements', 'Low', [
  ('r', D, r"UV6 (\S\ref{sec:bug-race}) needs a squash that takes longer than gem5's default of one cycle to reach the issue stage: it appears with \texttt{commitToIEWDelay} at 3 and 4 on STT and at 4 on SPT, and in no test we ran at the default.",
           r"UV6 (\S\ref{sec:bug-race}) needs \texttt{commitToIEWDelay} above its default of one cycle."),
  ('r', D, r"delays a transient transmitter ``until the mispredicted explicit branch B squashes''~\cite[\S 6.4.2]{yu2019stt}, as our violation window does (\S\ref{sec:transmission-requirement}), whereas both implementations release the transmitter at resolution.",
           r"delays a transient transmitter until the squash~\cite[\S 6.4.2]{yu2019stt}, as our violation window does (\S\ref{sec:transmission-requirement}), whereas both implementations release it at resolution."),
  ('r', D, r", with no adversary model: a hit is a run in which the target transmitter meets the defense's transmission criterion inside the violation window, even if no particular attacker could measure it.",
           r", with no adversary model: a hit counts even if no particular attacker could measure it."),
  ('r', D, r' and no leakage backbone has more than three instructions', ''),
]),
('19', 'background_micro', 'Low', [
  ('r', B, r'A contract is named by its pair, e.g., \contract{CT-SEQ}. ', ''),
  ('r', B, r" (AMuLeT instead uses ``leakage contract'' for a whole hardware-software contract~\cite[\S 2.1]{amulet})", ''),
  ('r', B, r" (e.g., in STT's Spectre model, until all older branches resolve~\cite[\S 6.1]{yu2019stt})", ''),
  ('r', B, r', typically the acyclicity or irreflexivity of combinations of such relations,', ''),
  ('r', B, r'Such models formalize many hardware and language MCMs~\cite{owens2009x86tso,herdingcats,pulte2018simplifying,batty2011mathematizing,lahav2017repairing,simner2020ifetch,simner2022vm,simner2025exceptions}.', ''),
  ('r', B, r'is a short single-/multi-threaded program with a final outcome. The outcome is forbidden if no allowed execution of the program produces it.',
           r'is a short program with a final outcome, which is forbidden if no allowed execution of the program produces it.'),
]),
('20', 'related_dups', 'Low', [
  ('r', W, r'Isla~\cite{armstrong2021isla} evaluates litmus tests against full ISA semantics~\cite{armstrong2019sail}, and TransForm', r'TransForm'),
  ('r', W, r"; four of its nine reports fall outside the defenses' security guarantees", ''),
  ('r', W, r"Implementation bugs in simulated Spectre defenses include a pending-squash timing leak in STT and SPT, found by Protean's fuzzer~\cite[\S VII-B4b]{protean}, and an SPT bug, found by manual inspection, that untaints transient loads after a pending fault~\cite[\S VII-B4c]{protean}, both since fixed~\cite{nickscommittoSTT,mosier2025sptpr6}.",
           r"Implementation bugs in simulated Spectre defenses include Protean's two bugs in STT and SPT (\S\ref{sec:discussion})."),
  ('r', I, r'(\S\S\ref{sec:known-bugs} and~\ref{sec:related-work})', r'(\S\S\ref{sec:known-bugs} and~\ref{sec:discussion})'),
]),
('21', 'result_captions', 'Low', [
  ('r', T('reconstl_v5_8pt'), r"; i1 is the unresolved branch, so i2--i4 are speculative; i2 loads the protected $m0$ into $r0$ (\textit{ddi}), $r0$ is the address of both the store i3 and the transmitter i4, and i4 reads i3's store (\textit{rf}). Bottom: the gem5 trace", r'; bottom: its gem5 trace'),
  ('r', T('recon_otb_v8_8pt'), r' i3 is speculative under branch i2, and i6 under the mispredicted branch i4.', ''),
  ('r', T('squashrace_v7_8pt'), r" xmit's address comes from committed instructions, so SPT holds xmit (blue) while the branch is unresolved.", ''),
]),
]

# Parked review notes (2026-11-15)

Every note added to ISCA-27 on 2026-11-15 in commits `3303db2` (Background vs Protean, plus the whole-paper terminology audit against Fig. 1 and the intro) and `fe6ce0b` (adversary model, "transient", leakage contract with transmission criteria). Anna asked to bank them outside the paper and come back to them later, so they were taken out of the paper source in commit `c06acd7`. Notes Anna wrote herself, like `\anna{...}` and `% anna looking into this...`, were left in place.

Counts: 46 notes. 39 were live and 5 were commented out; all of these were removed. 2 had already been deleted by Anna and are kept here for the record.

**To put a note back:** paste its line into the file directly after the line quoted as "after", which is the body line it followed. To see the original placement, run `git show fe6ce0b:sections/<file>.tex` in `~/trippel/ISCA-27`. Line numbers quoted inside the notes refer to commit `206a6f8`, the version before any notes, so they are a few lines off.

## sections/abstract.tex

1. Status: you had commented it out; removed 2026-11-15. After: `We propose \toolname{}, a three-part framework for automated, thorough security validation of simulated Spectre defenses. First, a new speci…`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: here the language formalizes ``how a Spectre defense's hardware support enforces its security guarantee''; Fig.~1's caption and intro.tex:119,131 say it formalizes the security guarantee itself (as a leakage predicate), and the abstract never says ``defense specification''. Option A: keep ``how \ldots enforces'' (stresses mechanism-level detail); option B: ``formalizing a Spectre defense's security guarantee as a defense specification, in enough detail to expose\ldots''. Recommendation: B, which matches Fig.~1 and keeps the mechanism clause. \textit{Source:} tikz/intro\_threelayer\_v9.tex:52,86; intro.tex:119,131.}
```

## sections/intro.tex

1. Status: was live in the paper; removed 2026-11-15. After: `at different performance and complexity costs~\cite{hu2021sok}.`

```latex
\urgentbr\urgentnote{Broken reference: \texttt{sec:specificationlangauge} (line 18) is not defined anywhere, so it prints ``??''; the specification-language section's label is \texttt{formalmodel}, and the sentence also lacks ``Sec.~''. \textit{Source:} model.tex:1; \texttt{grep} over sections/ and main.tex.}
```

2. Status: you had commented it out; removed 2026-11-15. After: `Validation targets for many of these methods including AMuLeT are \textit{hardware-software (HW-SW) security contracts}\cite{guarnieri2021co…`

```latex
\urgentbr\urgentnote{Possible factual error, here and in Fig.~1's contract box: \contract{ARCH-SEQ} is not ``also known as'' speculative non-interference. Guarnieri et al.\ define SNI (their Def.~5, from Spectector) as a property of a program, and describe \contract{ARCH-SEQ} as ``a simple and clean formulation of the idea behind transient noninterference''; Background (background.tex:20) already treats SNI as the software property. Suggest ``e.g., \contract{ARCH-SEQ}, which formalizes transient non-interference~\cite{guarnieri2021contracts}'' here and in the figure. \textit{Source:} guarnieri-2021-hw-sw-contracts.pdf \S III (\contract{ARCH-SEQ}) and \S IV Def.~5 (SNI).}
```

3. Status: you had commented it out; removed 2026-11-15. After: `Validation targets for many of these methods including AMuLeT are \textit{hardware-software (HW-SW) security contracts}\cite{guarnieri2021co…`

```latex
\notebr\auditnote{term}{VOCAB}{``advertised security guarantees'' (here and at :96) vs.\ plain ``security guarantee(s)'' in Fig.~1's caption and the rest of the intro (:119, :131); guidelines \S5 also says ``security guarantee'' everywhere, not advertised/promised/stated. Suggest dropping ``advertised'' (or ``its own security guarantee'' where it contrasts with a contract). \textit{Source:} Fig.~1 caption (tikz/intro\_threelayer\_v9.tex:86), intro.tex:119,131.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `There exists no principled way to validate a defense's simulator prototype directly against its advertised security guarantee (Fig.~\ref{fig…`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: this line says ``spurious bugs'' (as does Fig.~1's AMuLeT box), but Fig.~1's caption says ``report false leaks''. Option A: ``spurious bugs'' in all three places; option B: ``false leaks'' in all three. Recommendation: A (or ``spurious reports''), because pipeline.tex:96 defines a leak as a hit confirmed to be real, so ``false leak'' contradicts the paper's own definition. \textit{Source:} tikz/intro\_threelayer\_v9.tex:45,87; pipeline.tex:96.}
```

5. Status: was live in the paper; removed 2026-11-15. After: `\input{tikz/intro_threelayer_v9}% v9: second overview mockup (2026-11-14), replaces v8`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: three definitions of a security litmus test. Fig.~1: (Execution, Directive); intro.tex:136: an x86 program paired with directives that describe its target execution; abstract.tex:10: a program paired with a target execution. Option A: change the figure's line to (Program, Directives); option B: keep (Execution, Directive) and reword :136 and the abstract around it. Recommendation: A, since the text (and pipeline.tex:60) always pairs a \emph{program} with something and says ``directives'' in the plural. \textit{Source:} tikz/intro\_threelayer\_v9.tex:56, intro.tex:136, abstract.tex:10.}
```

6. Status: you had commented it out; removed 2026-11-15. After: `\emph{security litmus tests}, and (3) an \textbf{executor} for running and steering these tests on gem5 implementations of the defense to de…`

```latex
\notebr\auditnote{term}{VOCAB}{Low priority: ``early-stage prototypes of hardware support for Spectre defenses'' (:119) and ``gem5 implementations of the defense'' (:121) vs.\ Fig.~1's ``simulated defenses'' (and the abstract's ``simulated Spectre defenses''). Suggest ``simulated Spectre defenses'' at :119. \textit{Source:} tikz/intro\_threelayer\_v9.tex:44,51,75; abstract.tex:7.}
```

7. Status: you had already deleted it (the [Proposed] paragraph was accepted into the text; the clause-order note became your own \anna todo). After: `The predicate combines three clauses: an \emph{execution contract} (which instructions are speculative when), a \emph{protection set} (which…`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: clause order. Here, model.tex:3, conclusion.tex:2 and the pipeline figure's slabs 3a--3c use (execution contract, protection set, leakage contract); Fig.~1 and model.tex:28--33 use (leakage contract, execution contract, protection set). Option A: Fig.~1's order everywhere, which keeps the visual pairing of leakage contract with observer mode and execution contract with execution mode; option B: this order everywhere, including Fig.~1. Recommendation: A, since Fig.~1 is the newest reference and the pairing is deliberate. \textit{Source:} tikz/intro\_threelayer\_v9.tex:43,52; model.tex:3,28--33; tikz/pipeline\_full\_8pt1col\_v3.tex:145--147.}
```

8. Status: was live in the paper; removed 2026-11-15. After: `\ts{Due to its leakage-targeting nature, \toolname{} is more efficient}. Compared to AMuLeT, a fuzzer, \toolname{} needs at least $18\times$…`

```latex
\notebr\auditnote{term}{VOCAB}{``AMuLeT's randomly synthesized STT tests'' reuses ``synthesize'', which Fig.~1 and :136 reserve for \toolname{}'s synthesizer; Fig.~1 calls AMuLeT ``random testing''. Suggest ``randomly generated''; same at results.tex:74, which also words the 17\% differently (``contain a speculative gadget inside the window''). \textit{Source:} tikz/intro\_threelayer\_v9.tex:44, intro.tex:136.}
```

## sections/background.tex

1. Status: you had already deleted it (the [Proposed] paragraph was accepted into the text; the clause-order note became your own \anna todo). After: `An out-of-order core predicts control and data flow of a program to maximize hardware resource utilization. \textit{Speculation primitives} …`

```latex
\proposed[``An out-of-order core predicts control and data flow\ldots'' (same facts; adds transient, sequential and transmitter, which Background never defines)]{An out-of-order core predicts the control and data flow of a program to maximize hardware resource utilization. \textit{Speculation primitives} originate this speculation, such as a conditional branch (control flow) or store bypass~\cite{horn2018ssb}, in which a load executes before an older store whose address is still unknown (data flow). When a speculation primitive \textit{resolves} as mispredicted, the core \emph{squashes} all younger instructions; instructions that are not squashed \emph{commit} in program order from the head of the reorder buffer (ROB). An instruction bound to squash is \emph{transient}, and one bound to commit is \emph{sequential}~\cite{canella2019systematic}. A \emph{transmitter} is an instruction that modulates a hardware resource (a \emph{channel}, such as the data cache) as a function of one of its operands, which a receiver observes to infer that operand~\cite{kiriansky2018dawg}; e.g., a load transmits its address.}
```

2. Status: you had commented it out; removed 2026-11-15. After: `An out-of-order core predicts control and data flow of a program to maximize hardware resource utilization. \textit{Speculation primitives} …`

```latex
\notebr\reviewnote{Why: (1) ``instructions \ldots such as \ldots a store bypass mechanism'' calls a mechanism an instruction; (2) ``otherwise they commit'' reads as if the primitives commit; (3) Background uses ``transmitter'' (next paragraph) and the intro uses ``transiently'' without defining either, while Protean's Background defines both first. The store-bypass wording is from your commented line below. \textit{Source:} protean\_hpca26.pdf \S II-A (transmitter, channel and receiver, citing Kiriansky et al.\ [DAWG]; transient and sequential, citing Canella et al.).}
```

3. Status: was live in the paper; removed 2026-11-15. After: `An out-of-order core predicts control and data flow of a program to maximize hardware resource utilization. \textit{Speculation primitives} …`

```latex
\notebr\reviewnote{Check ``transient'' throughout the paper. Protean, citing Canella et al., defines a \emph{transient} instruction as one bound to squash and a \emph{sequential} one as bound to commit; a speculative instruction becomes one or the other. The abstract (abstract.tex:1, ``transient (i.e., uncommitted) instructions'') and the intro (intro.tex:10, ``transiently (via uncommitted instructions)'') gloss transient as uncommitted, but an uncommitted instruction may still commit, and ``uncommitted'' is also an execution-graph status in the model (model.tex:48). Suggest ``transient (i.e., later squashed)'' or ``bound to squash''. Background itself never says ``transient'' except ``leaking transiently'' in the protection-set sentence (Protean's words), and never defines it; the proposed paragraph above adds the definition. The other uses look consistent: intro.tex:64 ``transient leakage''; related.tex:6 ``transient leaks'' and ``transient-execution bugs''. Also check for ``speculative'' where ``transient'' is meant, or the reverse: a defense protects data in speculative instructions, which may turn out to be sequential. \textit{Source:} protean\_hpca26.pdf \S II-A; search of the live text on 2026-11-15.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `Spectre defenses aim to protect some set of architectural state from being leaked through a side channel formed by a data-dependent optimiza…`

```latex
\notebr\reviewnote{Wording: ``aim to protect some set of architectural state from being leaked through a side channel formed by a data-dependent optimization, while under such speculation'' is hard to parse. Protean's phrasing is cleaner and sets up the protection set: ``Each defense promises to keep some architectural state from leaking transiently~\cite{protean}.'' The next sentence has two e.g.'s; suggested: ``Defenses differ in when an instruction stops being speculative, a point STT calls its \textit{visibility point}~\cite{yu2019stt}: once all older control-flow instructions have resolved (STT's Spectre model), or once the instruction can no longer be squashed (its Futuristic model).'' \textit{Source:} protean\_hpca26.pdf \S III-B; your commented line above (STT \S 6.1).}
```

5. Status: was live in the paper; removed 2026-11-15. After: `Spectre defenses aim to protect some set of architectural state from being leaked through a side channel formed by a data-dependent optimiza…`

```latex
\urgentbr\urgentnote{Check: ``or once the instruction has reached the head of the ROB'' is Protean's \textsc{AtCommit} model. Protean says it matches the formal definition of STT's Futuristic model but not its implementations, which treat an instruction as speculative only until all older instructions have executed without faulting or mispredicting. Since STT is the example here, either say ``can no longer be squashed'' (STT's words, your commented line above) or attribute the head-of-ROB rule to Protean. Related, for Fig.~1: STT's execution contract there is ``SpectreCtrl'', a name Background never introduces; Protean calls this model \textsc{Control} (speculative until all older branches resolve) and STT calls it the Spectre model. DECIDE: (a) define ``SpectreCtrl'' here, where the two speculation models are introduced; or (b) use Protean's \textsc{Control} and \textsc{AtCommit} in Fig.~1 and the body. Recommendation: (b), since Background already borrows Protean's contract vocabulary. \textit{Source:} protean\_hpca26.pdf \S II-B2 and footnote 1.}
```

6. Status: was live in the paper; removed 2026-11-15. After: `Spectre defenses aim to protect some set of architectural state from being leaked through a side channel formed by a data-dependent optimiza…`

```latex
\notebr\reviewnote{Optional extra, to match Fig.~1's third element: give each defense's protection set in Protean's words as you describe it. STT (like NDA and SpecShield) protects all memory but no registers (Fig.~1: ``unaccessed memory''); SPT protects every register and memory byte that has not been architecturally transmitted, directly or through invertible arithmetic. Protean also names each defense's mechanism (NDA and SpecShield delay access, STT tracks access, SPT's secure baseline delays transmitters), which maps onto the intro's ``delay or taint-track''. Skip if space is tight. \textit{Source:} protean\_hpca26.pdf \S III-C, Fig.~2, Tab.~I.}
```

7. Status: was live in the paper; removed 2026-11-15. After: `Three other defenses let speculative loads execute and instead control their effect on the memory system. InvisiSpec~\cite{yan2018invisispec…`

```latex
\notebr\reviewnote{Typo and cite: the paragraph ends with a stray ``)'' after the cite, and its only cite (InvisiSpec \S IV) supports the claim for one of the three defenses; add CleanupSpec's and SpecLFB's sections, as intro.tex:92 cites all three. To match the intro, say ``cover only (load, address) transmitters'' rather than ``cover only loads''. \textit{Source:} intro.tex:92.}
```

8. Status: was live in the paper; removed 2026-11-15. After: `Three other defenses let speculative loads execute and instead control their effect on the memory system. InvisiSpec~\cite{yan2018invisispec…`

```latex
\notebr\reviewnote{Optional consistency: the intro lists ten defenses expressed in the \toolname{} language (intro.tex:134), but Background never describes DoM or SDO (NDA and SpecShield appear only in the contracts subsection). That is fine if Background covers only the defenses you test; just make sure DoM and SDO are defined before any later section relies on them. \textit{Source:} intro.tex:134.}
```

9. Status: was live in the paper; removed 2026-11-15. After: `Hardware--software security contracts~\cite{guarnieri2021contracts} specify which executions of a victim program an attacker may distinguish…`

```latex
\urgentbr\urgentnote{Conflict with the intro and Fig.~1: this paragraph treats speculative non-interference as a software property, which is correct (Guarnieri et al.\ Def.~5, from Spectector), but intro.tex:92 and Fig.~1's contract box say \contract{ARCH-SEQ} is ``also known as speculative non-interference''. Guarnieri et al.\ instead call \contract{ARCH-SEQ} ``a simple and clean formulation of the idea behind transient noninterference''. Keep this paragraph and fix the intro and the figure (see the note at the intro's contracts paragraph); optionally add here: ``\contract{ARCH-SEQ} formalizes transient non-interference~\cite{guarnieri2021contracts}.'' \textit{Source:} guarnieri-2021-hw-sw-contracts.pdf \S III and \S IV Def.~5.}
```

10. Status: was live in the paper; removed 2026-11-15. After: `Hardware--software security contracts~\cite{guarnieri2021contracts} specify which executions of a victim program an attacker may distinguish…`

```latex
\notebr\reviewnote{Wording vs Protean: Protean defines \contract{CT} as exposing ``all unsafe transmitter operands''; you give Guarnieri et al.'s concrete version (the program counter and load/store addresses). Protean's version ties \contract{CT} to transmitters, which is what makes Fig.~1's STT leakage contract (``\contract{CT} with conditions'') readable, so consider: ``\contract{CT} exposes the unsafe operands of every transmitter (the program counter and the addresses of loads and stores)''. Also use ``resp.'' as Protean does: ``A defense that upholds \contract{ARCH-SEQ} (resp.\ \contract{CT-SEQ}) leaks no data beyond what the program accesses (resp.\ transmits) sequentially''; the bare parentheses read as a gloss. \textit{Source:} protean\_hpca26.pdf \S II-C.}
```

11. Status: was live in the paper; removed 2026-11-15. After: `Hardware--software security contracts~\cite{guarnieri2021contracts} specify which executions of a victim program an attacker may distinguish…`

```latex
\notebr\reviewnote{Adversary model: it is here, but only as one clause (``A separate adversary model defines which microarchitectural state the attacker observes\ldots''), and Fig.~1's contract box leaves it out. If the leakage contract carries a transmission criterion per transmitter (DECIDE note below), the adversary model is half of what the leakage contract corresponds to, so it deserves its own sentence here and a place in Fig.~1. Suggested: ``A contract is evaluated under an \emph{adversary model}, which defines how an attacker observes the microarchitecture to tell two executions apart~\cite{guarnieri2021contracts}. AMuLeT applies one adversary model to every defense it tests: a snapshot of the L1 data cache and D-TLB at the end of each test~\cite{amulet}.'' This also sets up why some AMuLeT reports fall outside a defense's guarantee: its D-TLB snapshot flagged STT's speculative stores (KV3), which STT's guarantee excludes. \textit{Source:} fu-2025-amulet.pdf ($\mu$arch trace = ``the final state of the L1D-cache and D-TLB extracted from the simulator at the end of a test case''; KV3, speculative store installing a D-TLB entry); protean\_hpca26.pdf \S II-C; the intro's commented AMuLeT accounting note (KV3 out of scope, STT \S5).}
```

12. Status: was live in the paper; removed 2026-11-15. After: `\toolname{}'s specification language borrows two of these names in narrower senses. \toolname{}'s \emph{execution contract} plays the role o…`

```latex
\urgentbr\urgentnote{DECIDE (mismatch with Fig.~1; updated 2026-11-15 with your definition: the leakage contract is a set of (transmitter, operand) pairs plus a transmission criterion for each pair). In Guarnieri et al.'s terms that definition spans two pieces. The pair set plays the role of the observer mode: Protean's \contract{CT} ``exposes all unsafe transmitter operands'', so \contract{CT} is the coarse case of a pair set. The criteria play the role of the adversary model: how and when the attacker sees each transmission (a load once it obtains its data, a branch when it resolves). Protean states its transmitter assumptions the same way, as pairs with a time (load and store micro-ops ``fully transmit their address operands when they execute'', branches ``when they resolve''), but puts them in its threat model, not its contract. Consequences either way: (1) this paragraph's ``neither an observation clause nor\ldots'' must go, and so must ``execution clause'' and ``observation clause'', which the paragraph above no longer defines; (2) the model section's definition (model.tex:31) lists only the pairs, and the criteria appear only in the Inspector section as the ``transmission mechanism'' (pipeline.tex:129), so the definition would gain the criteria; (3) ``The attacker model is orthogonal to the specification'' (pipeline.tex:131) becomes false, since the criteria are the specification's adversary model; what is true is that no attacker program is needed; (4) Fig.~1's contract box shows (observer mode, execution mode) without the adversary model, so the parallel is exact only if the box adds it, and ``\contract{CT} with conditions'' then reads as pairs (\contract{CT}) plus criteria (conditions), if that is what ``conditions'' means. Options: (a) the leakage contract is a per-transmitter observer mode plus adversary model, the execution contract is the execution mode, and the protection set is Protean's, which a contract leaves implicit; (b) keep SynthLC's sense (pairs only), say the criteria extend it, and change Fig.~1's STT example to its pairs and criteria. Recommendation: (a). It matches Fig.~1, gives the adversary model the weight it needs, and explains AMuLeT's out-of-scope reports as an adversary-model mismatch: AMuLeT applies one adversary model (L1D and D-TLB) to every defense, while each defense's criteria come from its own paper. Either way, update the audit guidelines' rule (``leakage contract is SynthLC's sense, not AMuLeT's''). \textit{Source:} protean\_hpca26.pdf \S II-B1 and \S II-C; fu-2025-amulet.pdf ($\mu$arch trace); model.tex:31; pipeline.tex:129,131; tikz/intro\_threelayer\_v9.tex.}
```

13. Status: was live in the paper; removed 2026-11-15. After: `\toolname{}'s specification language borrows two of these names in narrower senses. \toolname{}'s \emph{execution contract} plays the role o…`

```latex
\notebr\reviewnote{Optional extra from Protean: (1) its protection set ``may evolve as a program executes'', worth saying since SPT's shrinks as data is transmitted; (2) its threat model lists the transmitters it assumes on gem5's O3 core: loads and stores transmit their address when they execute, conditional and indirect branches transmit their condition or target when they resolve, and divisions partially transmit both inputs (first flagged by Protean). One sentence citing this would ground the leakage contract's transmitter list, here or in the model section. \textit{Source:} protean\_hpca26.pdf \S III-B and \S II-B1.}
```

14. Status: was live in the paper; removed 2026-11-15. After: `Prior work uses axiomatic models to specify which executions a memory consistency model (MCM) allows. A \emph{candidate execution} of a prog…`

```latex
\notebr\reviewnote{Typo: ``the model's axioms'' starts a sentence in lowercase.}
```

15. Status: was live in the paper; removed 2026-11-15. After: ``

```latex
\notebr\reviewnote{Prefetching: ``(Stage~1a)'' names a pipeline stage that is defined only in the synthesizer section; drop the parenthetical (audit guidelines, NO PREFETCHING). This is separate from the last sentence. \textit{Source:} PAPER\_AUDIT\_GUIDELINES.md (NO PREFETCHING).}
```

## sections/model.tex

1. Status: was live in the paper; removed 2026-11-15. After: `(which instruction operands transmit). We write each clause by hand from the defense's paper. We first define the execution graphs that the …`

```latex
\notebr\auditnote{term}{VOCAB}{The section says ``a \toolname{} specification'' and is titled ``\toolname{} Specification Language'', while Fig.~1 and intro.tex:119 say \emph{defense specification} and \emph{defense specification language}; ``defense specification'' never appears in this section. Suggest ``A \emph{defense specification} states\ldots'' at :2 and a title matching intro.tex:119. \textit{Source:} tikz/intro\_threelayer\_v9.tex:52, intro.tex:119.}
```

2. Status: was live in the paper; removed 2026-11-15. After: `We define a SimSpect leakage predicate to have the following three components:`

```latex
\notebr\auditnote{term}{VOCAB}{Here the three clauses are ``components'' of the leakage predicate; in Fig.~1 they make up the \emph{defense specification}, and :2 and intro.tex:134 say the predicate \emph{combines} three \emph{clauses}. Suggest ``A defense specification has three clauses, which the leakage predicate combines:''. \textit{Source:} tikz/intro\_threelayer\_v9.tex:52, intro.tex:134.}
```

3. Status: was live in the paper; removed 2026-11-15. After: `A leakage contract is the set of pairs of \textit{transmitters} (instructions that leak one or more operands via a hardware side channel) an…`

```latex
\notebr\reviewnote{If the leakage contract includes a transmission criterion per pair (DECIDE note in Background, at the paragraph on \toolname{}'s borrowed names), this definition needs the criteria too, e.g., ``\ldots and their unsafe operand(s), each with a \emph{transmission criterion}: the event by which that operand is observed, such as a load obtaining its data or a branch resolving''. The criteria are now introduced only in the Inspector section, as the ``transmission mechanism'' (pipeline.tex:129). \textit{Source:} your definition, 2026-11-15; pipeline.tex:129.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `STT~\cite{yu2019stt} delays a transmitter until the speculative loads its operands depend on reach their visibility point (Sec.~\ref{sec:bg-…`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: this STT example does not use Fig.~1's values (\contract{CT} with conditions, SpectreCtrl, unaccessed memory). Here the leakage contract is (load, address) and (branch, condition), the execution contract is unnamed, and the protection set is ``memory'' with the identity update (Fig.~\ref{fig:relaxation}'s caption says ``the value read by every speculative load''); ``SpectreCtrl'' is defined nowhere in the body (Protean calls this speculation model \contract{CONTROL}; STT calls it the Spectre model). Option A: reword Fig.~1's example to this text's values; option B: use Fig.~1's names here, define SpectreCtrl (citing Protean's \contract{CONTROL}) and say what ``with conditions'' and ``unaccessed'' mean. Recommendation: B for the names, after settling ``memory'' vs.\ ``unaccessed memory'', which are different protection sets. \textit{Source:} tikz/intro\_threelayer\_v9.tex:54; tikz/relaxation\_v2\_short.tex caption; protean\_hpca26.pdf \S II-B (``The weakest speculation model studied in prior work is CONTROL'').}
```

## sections/pipeline.tex

1. Status: was live in the paper; removed 2026-11-15. After: `\section{The \toolname{} Pipeline}\label{sec:pipeline}`

```latex
\notebr\auditnote{term}{VOCAB}{The title, :7 and Fig.~\ref{fig:pipeline}'s caption lead call the tool ``the \toolname{} pipeline'' (also discussion.tex:37, ``The pipeline also supports''), while Fig.~1 and the abstract present \toolname{} as three parts: defense specification, synthesizer, executor. Suggest a title such as ``Synthesizer And Executor'' and ``\toolname{}'' for the tool, keeping ``pipeline'' for the CPU pipeline. \textit{Source:} tikz/intro\_threelayer\_v9.tex:86, abstract.tex:7--14.}
```

2. Status: was live in the paper; removed 2026-11-15. After: `\toolname{} turns a defense's leakage predicate into a suite of violating security litmus tests and runs each one on the defense implementat…`

```latex
\notebr\auditnote{term}{VOCAB}{``an x86 program paired with an annotation that describes its target execution'' (also :60, and Fig.~\ref{fig:pipeline}'s caption ``x86 programs with annotations''): Fig.~1 and intro.tex:136 pair the program with \emph{directives}, and the decided glossary keeps ``annotation'' for the \texttt{.ann.json} file. Suggest ``paired with directives that describe its target execution'' here and at :60. \textit{Source:} intro.tex:136, tikz/intro\_threelayer\_v9.tex:56; guidelines \S5 glossary.}
```

3. Status: was live in the paper; removed 2026-11-15. After: `\subsection{Synthesizer: Abstract Test Generation (Stages 1a and 1b)}\label{sec:abstract-test-generation}`

```latex
\notebr\auditnote{term}{VOCAB}{The heading ``Abstract Test Generation'' and :12 (``enumerates tests as execution graphs''): Fig.~1 and intro.tex:136 say the synthesizer enumerates \emph{leakage backbones} (execution graphs) and only Stage~2 turns graphs into \emph{tests}. Suggest ``Synthesizer: Execution-Graph Enumeration (Stages 1a and 1b)''; the label can stay, since Fig.~1 cites it. \textit{Source:} intro.tex:136, tikz/intro\_threelayer\_v9.tex:55.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `\subsubsection{Speculation Primitive Instrumentation}\label{sec:speculation-primitive-instrumentation}`

```latex
\notebr\auditnote{term}{VOCAB}{``Instrumentation'' (this heading, :73 ``we instrument store bypass'', Table~\ref{tab:instrtable}'s caption ``How concretization instruments'') names what intro.tex:136 calls writing \emph{directives}: Stage~2 only emits code plus directives, and the executor steers. Suggest e.g.\ ``Speculation Primitives And Their Directives'' and ``we realize store bypass''. \textit{Source:} intro.tex:136,138.}
```

5. Status: was live in the paper; removed 2026-11-15. After: `The executor runs each test on the defense's gem5 prototype and checks the run against the test's target execution. Running the binary is no…`

```latex
\notebr\auditnote{term}{VOCAB}{DECIDE: ``harness'' (here, the :98 heading, :100, Table~\ref{tab:instrtable}'s ``gem5 harness'' column, Fig.~\ref{fig:pipeline}'s ``Minimal harness'') is a component that Fig.~1 and intro.tex:138 do not name: there the executor itself \emph{steers} the test and its Inspector observes. Option A: drop ``harness'' and say the executor steers (heading e.g.\ ``Executor: Steering With Speculation And Timing Directives''); option B: keep ``harness'' and introduce it at intro.tex:138 as the steering counterpart of the Inspector. Recommendation: A, matching Fig.~1's steers/observes arrows. \textit{Source:} tikz/intro\_threelayer\_v9.tex:79--80, intro.tex:138.}
```

6. Status: was live in the paper; removed 2026-11-15. After: `Because we take advantage of its whitebox nature to read the simulator's trace directly, detection needs no attacker: we neither time a prob…`

```latex
\notebr\auditnote{term}{VOCAB}{``The attacker model is orthogonal to the specification'' reads as contradicting Fig.~1, which pairs the leakage contract with the security contract's observer mode (what the attacker observes) and the execution contract with its execution mode; the next sentence in fact gives the leakage contract that observer role. Suggest e.g.\ ``Detection needs no attacker program: the leakage contract's transmission criteria play the role of an adversary model, and the Inspector checks them directly in the trace.'' (Updated 2026-11-15: if the leakage contract includes transmission criteria, they correspond to the adversary model rather than the observer mode; see the DECIDE note in Background.); same tension at discussion.tex:23. Guidelines \S5 decided the opposite (the observation clause does not map onto our leakage contract), before Fig.~1 v9. \textit{Source:} tikz/intro\_threelayer\_v9.tex:43,52.}
```

7. Status: was live in the paper; removed 2026-11-15. After: `\input{tikz/checkerwindow_v5_8pt}% moved up to where it is first cited, 2026-11-03`

```latex
\notebr\auditnote{term}{VOCAB}{Fig.~\ref{fig:checkerwindow} says the roles are ``labels carried from the Alloy instance'' (caption, and the node ``Role labels from the Alloy instance''); Fig.~1 and intro.tex:136 call this object an \emph{execution graph}. Suggest ``from the execution graph''. \textit{Source:} intro.tex:136; guidelines \S5 glossary (``execution graph'' for the Alloy object).}
```

## sections/results.tex

1. Status: was live in the paper; removed 2026-11-15. After: `We check each defense only against the leakage its own paper claims to prevent (see the Discussion). AMuLeT~\cite{amulet} reports nine bugs …`

```latex
\notebr\auditnote{term}{VOCAB}{``AMuLeT reports nine bugs'' clashes with the paper's own definition (pipeline.tex:96: a bug is a leak the defense should have blocked) and with :35, which argues four of the nine are not bugs; the same nine are ``vulnerabilities'' at :28 and intro.tex:96, ``reports'' at :35 and ``problems'' at :38. Suggest ``reports'' for AMuLeT's nine throughout, and ``bugs'' only for the five in scope. \textit{Source:} pipeline.tex:96; guidelines \S5 (violation/hit/leak/bug).}
```

2. Status: was live in the paper; removed 2026-11-15. After: `AMuLeT tests each defense against a high-level contract that it pairs with the defense's security guarantee, \contract{CT-SEQ} for InvisiSpe…`

```latex
\notebr\auditnote{term}{VOCAB}{``a high-level contract'' vs.\ Fig.~1's ``security contract'' (intro.tex:92: ``HW-SW security contracts''). Suggest ``a HW-SW security contract''. Guidelines \S5 used ``high-level contract'' for this contrast; Fig.~1 v9 postdates it. \textit{Source:} tikz/intro\_threelayer\_v9.tex:43,87; intro.tex:92.}
```

3. Status: was live in the paper; removed 2026-11-15. After: `STT treats store-to-load forwarding as an implicit branch on the load's address and delays resolving it until that address is untainted~\cit…`

```latex
\notebr\auditnote{term}{VOCAB}{``tests from our STT model'' (also :58, and ``one corpus from the footprint model'' at :74): Fig.~1 and :35 call this a \emph{specification} (``our STT specification''), as does discussion.tex:32 (``the footprint specification''). Suggest ``from our STT specification'' and ``the footprint specification''. \textit{Source:} tikz/intro\_threelayer\_v9.tex:52, results.tex:35, discussion.tex:32.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `\input{tikz/resolutiontiming_v2}% moved from the pipeline section, 2026-11-13`

```latex
\notebr\auditnote{term}{VOCAB}{Fig.~\ref{fig:resolutiontiming}'s caption says ``An abstract execution of the bug'' and ``The model fixes only that i0 has committed''; elsewhere this object is an \emph{execution graph}. Suggest ``An execution graph of the bug'' and ``The graph fixes only\ldots''. \textit{Source:} intro.tex:136, model.tex:20.}
```

5. Status: was live in the paper; removed 2026-11-15. After: `SpecLFB treats a load as safe only if no older control instruction is unresolved~\cite[\S 6.2.2]{cheng2024speclfb}, and its ROB walk tracks …`

```latex
\notebr\auditnote{term}{VOCAB}{``47 of their 248 violations'': in this paper a \emph{violation} is an execution graph that breaks the leakage predicate (pipeline.tex:96). Suggest AMuLeT's own term, ``contract violations'', as related.tex:6 says. \textit{Source:} pipeline.tex:96, related.tex:6.}
```

## sections/related.tex

1. Status: was live in the paper; removed 2026-11-15. After: `Most leakage testing runs random programs and compares executions. On commercial CPUs, Revizor~\cite{revizor} and its follow-ups~\cite{oleks…`

```latex
\notebr\auditnote{term}{VOCAB}{Two small mismatches with Fig.~1's taglines: AMuLeT tests ``against contracts'' (Fig.~1: ``security contracts''), and \toolname{} ``checks one run against the defense's security guarantee'' (Fig.~1: ``against defense specifications''). Suggest ``against security contracts'' and ``against the defense's specification''. \textit{Source:} tikz/intro\_threelayer\_v9.tex:44,51.}
```

## sections/discussion.tex

1. Status: was live in the paper; removed 2026-11-15. After: `\paragraph{What we check.} \toolname{} judges each prototype against the security guarantee its own paper states, so a reported bug breaks a…`

```latex
\notebr\auditnote{term}{VOCAB}{``the security guarantee its own paper states'' and ``breaks a promise the authors made'': guidelines \S5 asks for plain ``security guarantee'' (not stated/promised), as in Fig.~1's caption; and ``A high-level contract'' later in this paragraph is Fig.~1's ``security contract''. \textit{Source:} tikz/intro\_threelayer\_v9.tex:86--87; guidelines \S5.}
```

2. Status: was live in the paper; removed 2026-11-15. After: `\paragraph{What we check.} \toolname{} judges each prototype against the security guarantee its own paper states, so a reported bug breaks a…`

```latex
\notebr\auditnote{term}{VOCAB}{``Each footprint criterion'': the decided term is \emph{transmission mechanism} (pipeline.tex:124, Fig.~\ref{fig:checkerwindow}), not ``criterion''. Suggest ``Each footprint defense's transmission mechanism lists only\ldots''. \textit{Source:} pipeline.tex:124; guidelines \S5 (``transmission mechanism'', not ``criterion'').}
```

3. Status: was live in the paper; removed 2026-11-15. After: `\paragraph{Soundness of the harness.} The harness changes only where the predictors send execution, by forcing each annotated branch to misp…`

```latex
\notebr\auditnote{term}{VOCAB}{``Soundness of the harness'' (also ``harness'' at :35, :42, :43): see the DECIDE on ``harness'' at pipeline.tex:96; under its option A this becomes e.g.\ ``Soundness of steering''. \textit{Source:} tikz/intro\_threelayer\_v9.tex:79, intro.tex:138.}
```

4. Status: was live in the paper; removed 2026-11-15. After: `\paragraph{Execution contracts.} An execution contract conservatively specifies which instructions are speculative, and therefore protected,…`

```latex
\notebr\auditnote{term}{VOCAB}{``which instructions are speculative, and therefore protected'' merges two clauses: in Fig.~1, model.tex:31--33 and intro.tex:134 the execution contract says what is speculative and the \emph{protection set} says what is protected. Suggest ``which instructions are speculative, and therefore may not transmit protected values''. \textit{Source:} model.tex:31--33, intro.tex:134.}
```

## sections/conclusion.tex

1. Status: was live in the paper; removed 2026-11-15. After: `Hardware Spectre defenses are prototyped in simulators that can measure their performance but not their security guarantee. \toolname{} clos…`

```latex
\notebr\auditnote{term}{VOCAB}{``only for the STT and ReCon models'': elsewhere these are \emph{specifications} (Fig.~1; discussion.tex:32), and discussion.tex:32 also lists the footprint specification as exhaustive to six instructions, so the two sentences disagree on which reached UNSAT. Suggest ``for the STT, ReCon and footprint specifications'' if discussion.tex:32 is right. \textit{Source:} discussion.tex:32.}
```

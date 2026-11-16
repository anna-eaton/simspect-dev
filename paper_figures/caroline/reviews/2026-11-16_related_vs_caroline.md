# Related Work vs Caroline's last-author papers (2026-11-16)

Checked against ISCA-27 `027bcf8` (pulled 2026-11-16, includes today's Check-tools rewording). Paper untouched, no git writes. Every "old" string below was checked with `grep -F -c` and occurs exactly once in its file.

## Summary

**Her recent last-author papers (Stanford era, confirmed from the PDF author lists):** Helium (ISCA'26), Protean (HPCA'26), ITHICA (MICRO'26), µSpectre (arXiv'25), RTL2MµPATH/SynthLC (MICRO'24), MemGlue (FMCAD'24), Serberus (S&P'24), Design for HW MCM Verification and HW-SW Codesign for Spectre (PLARCH'23 abstracts), LCMs (ISCA'22), rtl2µspec (MICRO'21), plus out-of-area ones (ICSE'26, FMCAD'24 NL2LTL, CAV'23, EuroSys'24). CounterPoint is middle-author (Lindsay is first, Bhattacharjee last), so it was not used. µSpectre and the two PLARCH abstracts have no Related Work section; their intros were used. All files are in `paper_figures/caroline/papers/`.

**Overall verdict:** the section mostly agrees with her. It uses the same run-in-head format as Helium and Protean, puts the closest group first, and ends most paragraphs with a positioning sentence. Where it disagrees, the cause is mostly a grouping in which a work sits under a label she would not give it (LEAVE, OISA, InvarSpec/Clearing Shadows/Levioso, the Check tools' scope). There are also two descriptions of her own group's work that her papers state differently: the AMuLeT description in the intro, and the SynthLC leakage-contract description in Background. The biggest omissions are works her papers treat as close relatives of exactly what we do: LMSPEC/LmTest (Helium compares against it directly), Protean's AMuLeT extension (AMuLeT\*, her own fuzzer extension, which has a pipeline-timing adversary), and McVerSi (rtl2µspec's example of litmus-test generation in simulation).

**Counts:** 7 🔴 (disagrees with her characterization), 7 🟠 (omission she consistently includes), 8 🟡 (structure/wording). 3 of these are DECIDEs for Anna (marked).

**Her Related Work structure (what "agrees with Caroline" means here):**

- **Placement:** Related Work comes right before the Conclusion, after any Discussion or Limitations section, in every recent last-author paper: Helium (VIII Limitations and Future Directions → IX Related Work → X Conclusion), Protean (X → XI Conclusion), RTL2MµPATH (VII Results & Discussion → VIII → IX), ITHICA (IX → X Related Work → XI), MemGlue (VII → VIII). This answers the `\anna{ask: should Discussion come before Related Work...}` note at `related.tex:2`: Discussion goes first.
- **Length and grouping:** 2–4 groups, about 230–600 words (Serberus ~230, Protean ~330, MemGlue ~330, Helium ~520, LCM ~520, ITHICA ~600). Our section has about 650 words of prose, which fits, but roughly 130 citations, far more than any of hers.
- **Heads:** run-in heads. Helium, MemGlue, and LCM use "Leakage quantification:" (colon, sentence case). Protean numbers them ("1) Noncomprehensive Defenses:"). Serberus and ITHICA use periods ("Software Detection."). Ours ("\textbf{Testing for speculative leakage:}") matches Helium.
- **Order:** the group closest to the paper's own problem comes first (Helium: leakage quantification; Protean: other defenses; rtl2µspec: litmus testing, then "the most relevant prior work", the Check tools). Ours (testing first) matches.
- **Opening roadmap (optional):** ITHICA opens with "Prior works most relevant to ITHICA fall into four categories: soft error detection, post-silicon validation, fuzzing, and hyperscaler fleet studies" (§X). Serberus opens with "Several works study detection, formal foundations, and mitigation of Spectre attacks [25], [113]" (§8).
- **She names the closest work outright:** "The Check tools ... are the most relevant prior work, especially RTLCheck" (rtl2µspec §8); "Closest in motivation to ITHICA is PathFuzz [92], which ... but, unlike ITHICA, requires deterministic seeds" (ITHICA §X); "Most similar to TracerSym, Bao et al. ..." (Helium §IX); "The closest prior work verifies hardware adherence to CT contracts" (RTL2MµPATH §VIII).
- **Her contrasts are about goals and stay generous:** "It also accomplishes a different goal—µspec model synthesis" (rtl2µspec §8); "LMTEST is optimized to find counterexamples to a non-interference property, whereas TracerSim is designed for leakage quantification" and "This does not reflect a fundamental limitation of LMSPEC's leakage clauses compared to µobs functions, but rather the fact that they support distinct use cases" (Helium §IX); "Like ProtISA, these defenses expose programmable ProtSets. Unlike ProtISA, they cannot be automatically programmed" (Protean §X-2). Each group ends with, or contains, one explicit contrast. Our litmus-test paragraph has none.
- **Tone:** neutral and factual. She states a limitation as a scope fact, not as a failing (e.g., "These methodologies are all theoretically incomplete due to their use of symbolic initial states ... at the cost of false counterexamples", RTL2MµPATH §VIII).

## 🔴 Disagrees with her characterization

### 1. Intro: AMuLeT tests against contracts, not against the "advertised security guarantees"

- **Hers:** "AMuLeT [41], a fuzzing framework for testing gem5 implementations of Spectre defenses against §II-C-style security contracts" (Protean §VII-B1); "an enhanced version of the AMuLeT fuzzer [41]" (Protean §I). Protean also notes that "such contracts assume sequentially-leaked data is always public" (§VII-B), so a contract is not the same thing as a defense's own guarantee.
- **Ours (intro.tex:108–109):** "is the current state-of-the-art / approach for testing whether simulated Spectre / defenses uphold their advertised security guarantees." This says AMuLeT tests the defenses' own guarantees. Our whole positioning rests on AMuLeT testing a different property, and Anna's `\anna` note on that line raises the same point.
- **Fix:** two lines, both unique in `intro.tex`. Old `approach for testing whether simulated Spectre` → new `fuzzer for testing the security of simulated Spectre`. Old `defenses uphold their advertised security guarantees.` → new `defenses.` (keep the `\anna` note or delete it once decided). Result: "AMuLeT (§…) is the current state-of-the-art fuzzer for testing the security of simulated Spectre defenses." The next sentence already says it uses a hardware–software security contract.

### 2. Related: Check tools sentence (today's version)

- **Hers:** "The Check tools automate formal memory consistency model and security verification of processors by analyzing abstract models of microarchitectures, called µSPEC models" (RTL2MµPATH abstract). "A µSPEC model is a set of first-order logic axioms (rules) that describe how to construct µHB graphs" (RTL2MµPATH §I). "The Check tools provide an efficient mechanism for proving that a microarchitecture's MCM implementation is correct with respect to a suite of litmus test programs. Remarkably, recent work has shown that this approach can even be extended to prove correctness over the space of all programs [30 = PipeProof]" (rtl2µspec §1). "Checkmate ... searches for security vulnerabilities in hardware designs using µhb analysis" (rtl2µspec §8). Her Check list is PipeCheck, CCICheck, COATCheck, TriCheck, RTLCheck, PipeProof, and CheckMate (security). RealityCheck is not in it, but it is a Check tool, so keeping it is fine.
- **Ours:** the sentence says every cited tool checks "with respect to a suite of litmus tests", but PipeProof (cited in the same list) proves correctness for all programs. "Given as axioms over microarchitectural happens-before graphs" is also slightly off: in her description, the axioms describe how to construct the graphs.
- **Old (related.tex):** `The Check tools formally check that a microarchitecture, given as axioms over microarchitectural happens-before graphs, implements a memory consistency model with respect to a suite of litmus tests, from pipelines to RTL~\cite{lustig2014pipecheck,manerkar2015ccicheck,lustig2016coatcheck,trippel2017tricheck,manerkar2017rtlcheck,manerkar2018pipeproof,manerkar2020realitycheck}, and CheckMate applies them to hardware security by synthesizing security litmus tests~\cite{checkmate};`
- **New:** `The Check tools automate formal verification of memory consistency model implementations, from pipelines to RTL, by analyzing axiomatic models whose axioms describe how to construct microarchitectural happens-before graphs, for a suite of litmus tests or, with PipeProof, for all programs~\cite{lustig2014pipecheck,manerkar2015ccicheck,lustig2016coatcheck,trippel2017tricheck,manerkar2017rtlcheck,manerkar2018pipeproof,manerkar2020realitycheck}, and CheckMate applies this analysis to hardware security by synthesizing security litmus tests~\cite{checkmate};`

### 3. Related: LEAVE is a constant-time contract verifier, not an RTL secure-speculation checker

- **Hers:** "The closest prior work verifies hardware adherence to CT contracts [32], [36], [38], [91] ... using a product circuit formulation" and "LEAVE [91] and UPEC-DIT-23 [31] are CT contract satisfaction approaches. CONJUNCT [36] is both [synthesis and satisfaction]" (RTL2MµPATH §VIII).
- **Ours:** `leave` sits in "checks secure speculation in RTL", and ConjunCT/H-Houdini "prove which instructions are safe".
- **Fix (two strings in related.tex):** Old `checks secure speculation in RTL~\cite{fadiheh2019upec,fadiheh2020formal,fadiheh2023exhaustive,zagieboylo2023specverilog,leave,contractshadow,yang2026compass,dong2026interplay}` → new `checks secure speculation in RTL~\cite{fadiheh2019upec,fadiheh2020formal,fadiheh2023exhaustive,zagieboylo2023specverilog,contractshadow,yang2026compass,dong2026interplay}`. Old `and proves which instructions are safe~\cite{dinesh2024conjunct,dinesh2025hhoudini}` → new `and verifies hardware adherence to constant-time contracts~\cite{leave,dinesh2024conjunct,dinesh2025hhoudini}` (add UPEC-DIT here if item 11 is taken).

### 4. Related: OISA is a defense with secrecy labels, not a "formal definition of what may leak"

- **Hers:** "OISA [146], ProSpeCT [35], ConTExT [118], and SpectreGuard [42] rely on explicit source-level secrecy annotations to label memory as secret/public and prevent transient leaks of secret memory" (Protean §X-2). "OISA [97] attaches secrecy labels to architectural state and detects if a transmitter's unsafe operand, as defined in a CT contract, is ever passed secret data at runtime" (RTL2MµPATH §II-B).
- **Ours:** OISA opens the formal-definitions paragraph, ProSpeCT is buried in "many others", and only ConTExT and SpectreGuard appear under "secret annotation".
- **Fix (three strings in related.tex):** (a) Old `Formal definitions of what may leak include the safe and unsafe operands of a data-oblivious ISA~\cite{yu2019oisa}, information-flow properties` → new `Formal definitions of what may leak include information-flow properties`. (b) Old `secret annotation~\cite{schwarz2020context,fustos2019spectreguard}` → new `source-level secrecy annotations~\cite{yu2019oisa,daniel2023prospect,schwarz2020context,fustos2019spectreguard}`. (c) In the `and many others~\cite{...}` list, delete `daniel2023prospect,` (and `hajiabadi2024levioso,`, see item 5).

### 5. Related: "relaxations that recover performance" → security-preserving optimizations

- **Hers:** "Prior work proposes security-preserving optimizations for layering on top of Spectre defenses (like PROTEAN). ... InvarSpec [150], Clearing Shadows [128], and Levioso [51] enable earlier, safe execution through compile-time transformations [128] or by communicating static analyses to hardware [51], [150]" (Protean §X-3). "Relaxation" suggests the security guarantee is weakened, which she says it is not.
- **Old:** `relaxations that recover performance~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned}`
- **New:** `security-preserving optimizations layered on top of defenses~\cite{tran2020clearing,zhao2020invarspec,hajiabadi2024levioso,zhao2022pinned}`. Also remove `hajiabadi2024levioso,` from "many others". Pinned Loads is not in her list, so check that its own paper calls it security-preserving before keeping it here.

### 6. Background: SynthLC's leakage contracts in general vs the CT contract

- **Hers:** "state-of-the-art defenses assume the availability of microarchitectural leakage contracts, which characterize implementations' transmitters. ... The most widely-adopted leakage contract, the constant-time (CT) contract, enumerates a microarchitecture's transmitters and their unsafe ('leaky') operands. ... these defenses adopt bespoke leakage contracts that are much finer grained" (RTL2MµPATH §II-B).
- **Ours:** "SynthLC's leakage contracts list a microarchitecture's transmitters and their unsafe operands" gives the CT contract's definition for leakage contracts in general. Her next sentence, which we quote, is about the finer-grained STT/SPT contract.
- **Old (background.tex):** `SynthLC's leakage contracts list a microarchitecture's transmitters and their unsafe operands`
- **New:** `SynthLC's leakage contracts characterize a microarchitecture's transmitters (the canonical constant-time contract lists the transmitters and their unsafe operands)`. Keep the rest of the sentence ("and SynthLC notes that STT and SPT …"). The intro's own clause (`a \emph{leakage contract} (the instruction--operand pairs that transmit~\cite{rtl2upath})`) is our adaptation and can stay.

### 7. Background: SPT's declassification rule (DECIDE: check SPT §6 first)

- **Hers:** "SPT declassifies data once it is inevitable that it will be, or has been, transmitted architecturally" (RTL2MµPATH §II-B). Protean phrases the protection set as all state "that [has] not been architecturally transmitted in the past ... directly or indirectly via invertible arithmetic dependencies" (Protean §III-C). Her two papers stress different halves of the rule.
- **Ours:** "SPT delays a transmitter until it can prove that the transmitter's operands were already leaked by the program's non-speculative execution." The "will be" half is missing.
- **Old (background.tex):** `SPT~\cite[\S 6]{spt} delays a transmitter until it can prove that the transmitter's operands were already leaked by the program's non-speculative execution.`
- **New (if SPT §6 agrees with RTL2MµPATH):** `SPT~\cite[\S 6]{spt} delays a transmitter until its operands have been, or are certain to be, transmitted by the program's non-speculative execution.` The SPT paper is not saved locally, so I could not check it against §6. DECIDE.

## 🟠 Omissions she consistently includes

### 8. LMSPEC / LmTest: the closest prior "leakage + speculation clauses" specification

- **Hers:** "LMSPEC specifies leakage clauses (identifying transmitters) and prediction clauses (identifying instructions that introduce speculation) [14]. ... LMSPEC is coupled with a sampling-based testing framework, LMTEST, to detect leakage. ... LMTEST is optimized to find counterexamples to a non-interference property" (Helium §IX, "Side-channel models"). Those two clauses parallel our leakage contract and execution contract. A reviewer from her group would expect the comparison, and today we cite `barthe2024lmtest` only inside a list of software gadget testers.
- **Old (related.tex):** `software tools test programs for Spectre gadgets or against leakage models~\cite{oleksenko2020specfuzz,wang2021oo7,lin2025teapot,barthe2024lmtest}.`
- **New:** `software tools test programs for Spectre gadgets~\cite{oleksenko2020specfuzz,wang2021oo7,lin2025teapot}. LmTest tests cryptographic code against LMSPEC leakage models, whose leakage clauses identify transmitters and whose prediction clauses identify instructions that introduce speculation~\cite{barthe2024lmtest}; \toolname{}'s leakage and execution contracts play similar roles, but it tests a defense's implementation rather than a program.` This adds about 35 words; item 19 frees some.

### 9. AMuLeT\* (Protean's AMuLeT extension), and name AMuLeT as the closest work

- **Hers:** AMuLeT\* "extends AMuLeT [41] ... with ... a new LLVM-IR test generator ..., Enhanced CT observer mode ..., New observer modes ..., a new adversary model ... that exposes to an attacker the cycle at which each instruction reaches each pipeline stage. This adversary model surfaces contract violations in STT/SPT/SPT-SB that AMuLeT's default cache+TLB adversary model does not" (Protean §VII-B1). She names the closest work outright in every Related Work (see Summary). Today the testing paragraph never mentions AMuLeT\*: Protean shows up only as the source of two bugs. AMuLeT\* is her own tool, and its pipeline-timing adversary is close to what our Inspector observes.
- **Old (related.tex):** `In gem5, SpecCheck~\cite{mckevitt2023speccheck} monitors any running program for a generic transient-execution pattern, and AMuLeT~\cite{amulet} tests simulated Spectre defenses against contracts (\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}).`
- **New:** `In gem5, SpecCheck~\cite{mckevitt2023speccheck} monitors any running program for a generic transient-execution pattern. Closest to \toolname{} is AMuLeT~\cite{amulet}, a fuzzer that tests simulated Spectre defenses against contracts (\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}); Protean extends it with an LLVM-IR test generator and an adversary model that observes the cycle at which each instruction reaches each pipeline stage~\cite[\S VII-B1]{protean}.`

### 10. Intro: count Protean's bugs alongside AMuLeT's (DECIDE: wording and count)

- **Hers:** AMuLeT\* "found a previously unknown corner-case bug in PROTEAN's implementation of delayed branch resolution, which it borrows directly from STT/SPT/SPT-SB", and "We manually discover a corner-case implementation bug in SPT that AMuLeT\* misses" (Protean §VII-B4b–c).
- **Ours (intro.tex):** `Prior work found five such bugs in three simulated Spectre defenses~\cite{amulet} (\S~\ref{sec:known-bugs}).` This credits only AMuLeT, although her group found two more bugs in simulated defenses. The commented-out line just above it (`AMuLeT~\cite{amulet} and its extension in Protean~\cite{protean} are the only prior tools …`) shows the same intent.
- **New:** `Prior work found five such bugs in three simulated Spectre defenses~\cite{amulet} and two more in STT and SPT~\cite[\S VII-B4]{protean} (\S~\ref{sec:known-bugs}).` DECIDE: whether to count bugs across both papers or keep the AMuLeT-only number that the abstract and Results mirror.

### 11. UPEC-DIT (RTL2MµPATH's contract-verification baseline)

- **Hers:** "UPEC-DIT [32] is a CT contract synthesis approach" (RTL2MµPATH §VIII), cited as [32] Deutschmann et al., "Towards a formally verified hardware root-of-trust for data-oblivious computing", DAC 2022 (and [31], the arXiv 2023 follow-up).
- **Ours:** not cited (no `deutschmann` entry in `references.bib`).
- **Fix:** add `deutschmann2022upecdit` to the constant-time-contract cite in item 3 (`\cite{deutschmann2022upecdit,leave,dinesh2024conjunct,dinesh2025hhoudini}`), with a new bib entry taken from RTL2MµPATH ref [32].

### 12. McVerSi (litmus-test generation in simulation)

- **Hers:** "Several tools are available for systematic litmus-based post-silicon testing of hardware, including litmus [3], mcversi [16], and PerpLE [34], and dedicated tools for GPU testing [40]" (rtl2µspec §8). [16] is Elver and Nagarajan, "McVerSi: A test generation framework for fast memory consistency verification in simulation", HPCA 2016. It is the closest MCM analogue of what we do (generated tests run in a simulator).
- **Old (related.tex):** `run on hardware~\cite{sarkar2011power,flur2016modelling,alglave2011litmus,perple}`
- **New:** `run on hardware~\cite{sarkar2011power,flur2016modelling,alglave2011litmus,perple} and generated for simulators~\cite{elver2016mcversi}` (new bib entry from rtl2µspec ref [16]).

### 13. Canella et al. as the survey

- **Hers:** Protean classifies attacks with "Prior work [25 = Canella et al., A Systematic Evaluation of Transient Execution Attacks and Defenses]" (§II-A), and Serberus opens its Related Work with "Several works study detection, formal foundations, and mitigation of Spectre attacks [25], [113]" (§8). We already cite `canella2019systematic` in Background.
- **Old (related.tex):** `Hu et al.\ survey hardware Spectre defenses~\cite{hu2021sok}.`
- **New:** `Canella et al.\ and Hu et al.\ survey transient-execution attacks and hardware defenses~\cite{canella2019systematic,hu2021sok}.`

### 14. Okapi with the memory-layout defenses (low priority)

- **Hers:** "SafeBet [46], Okapi [116], and Perspective [65] require programmers to modify memory layout, ensuring secrets are not placed in architecturally accessed cache lines or pages" (Protean §X-2). We cite SafeBet and Perspective only inside "many others", and Okapi not at all. It fits the regrouping in item 15; add it only if that regrouping is taken.

## 🟡 Structure and wording

### 15. Group the defenses paragraph by what each defense covers, as Protean does (outline)

Protean groups defenses by threat-model scope, not by mechanism: "1) Noncomprehensive Defenses: Many Spectre defenses are noncomprehensive, assuming a restricted set of channels or speculation types and thus still allowing secrets to transiently leak. Some defend against cache-based channels only [SafeSpec, Conditional Speculation, HidFix, DoM, context-sensitive fencing, GhostMinion, MuonTrap, CleanupSpec, InvisiSpec, DAWG]... 2) Non-programmer-transparent Defenses ... 3) Defense Optimizations" (Protean §X). This axis suits our paper, because what we test is each defense's stated guarantee. Proposed order for the paragraph (same citations, about the same length):

1. Survey sentence (item 13).
2. "Many defenses protect only some channels, e.g., the cache hierarchy~\cite{taram2019csf,li2019conditional,kiriansky2018dawg,…}" (conditional speculation, CSF, and DAWG move here from the mechanism list, following Protean's cache-only list); then secrecy annotations (item 4); then memory-layout requirements (SafeBet, Perspective, Okapi, item 14); then security-preserving optimizations (item 5); then "and many others" with the remainder (SpecCFI stays there).
3. Design-level leaks. Change the heading too: old `\textbf{Spectre defenses and their flaws:}` → new `\textbf{Spectre defenses and their leaks:}`. Her term for leaks through excluded channels is "noncomprehensive", not "flawed", and Anna's rule says out-of-scope leaks are not bugs. Keep the existing "some through channels the defenses' papers exclude".
4. Implementation bugs (item 16), Pensieve/GhostMinion, Kvalsvik/UV3, then the closing contrast sentence (already good).

### 16. Pending-squash sentence: use her description of the mechanism

- **Hers:** "a previously unknown corner-case bug in PROTEAN's implementation of delayed branch resolution, which it borrows directly from STT/SPT/SPT-SB ... This creates a secret-dependent squash signal that leaks the tainted/protected branch predicate" (Protean §VII-B4b).
- **Old (related.tex):** `Implementation bugs in the simulated defenses include a pending-squash timing leak in STT and SPT, found by Protean's extended fuzzer~\cite[\S VII-B4b]{protean}, and an SPT untaint bug found by manual inspection~\cite[\S VII-B4c]{protean}`
- **New:** `Implementation bugs in the simulated defenses include a pending-squash timing leak in the delayed branch resolution that SPT inherits from STT's implementation, found by Protean's extended fuzzer~\cite[\S VII-B4b]{protean}, and an SPT untaint bug found by manual inspection~\cite[\S VII-B4c]{protean}` ("timing leak" kept; never "race").

### 17. "Random programs" → fuzzing, her word for this class

- **Hers:** "Other approaches include fuzzing [SpecFuzz, Revizor, Scam-V]" (Serberus §8); "the AMuLeT fuzzer" (Protean §I); "A large number of fuzzing works exist, targeting defects, design bugs, or security bugs" (ITHICA §X).
- **Old:** `Most leakage testing runs random programs and compares executions.`
- **New:** `Most leakage testing is fuzzing: it runs random programs and compares their executions.`

### 18. The litmus-test paragraph has no positioning sentence

Every group in her Related Work sections states how the paper differs (e.g., "rtl2µspec, on the other hand, can be used to verify hardware before tape out", rtl2µspec §8). Ours ends after Isla. Add one pointer-sized contrast instead of repeating Background. Old ` and Isla~\cite{armstrong2021isla} evaluates litmus tests against full ISA semantics~\cite{armstrong2019sail}. ` → new ` and Isla~\cite{armstrong2021isla} evaluates litmus tests against full ISA semantics~\cite{armstrong2019sail}. These tests check memory-ordering or transistency outcomes; \toolname{}'s tests encode leaks a defense forbids (\S~\ref{sec:bg-axiomatic}).`

### 19. Synthesized models: say what is synthesized from what

- **Hers:** "rtl2µspec ... synthesizes ... µspec model ... from a Verilog design" (rtl2µspec §8); LCM cites Bornholt and Torlak as MCM-analysis literature.
- **Old:** `models have also been synthesized automatically~\cite{memsynth,norman2023pipesynth,hsiao2021rtl2uspec}`
- **New:** `memory models~\cite{memsynth} and microarchitectural axioms~\cite{norman2023pipesynth} have also been synthesized, the latter also from RTL~\cite{hsiao2021rtl2uspec}` (check PipeSynth's inputs before applying).

### 20. TransForm: use its own term

TransForm's title and abstract say "Synthesizing Enhanced Litmus Tests" ("enhanced litmus tests, or ELTs", transform_isca20 abstract). Old `TransForm~\cite{hossain2020transform} synthesizes litmus tests from axiomatic transistency models` → new `TransForm~\cite{hossain2020transform} synthesizes enhanced litmus tests from axiomatic transistency models`.

### 21. Placement: Discussion before Related Work (answers the `\anna` note)

All five of her recent full papers put Related Work immediately before the Conclusion, after Discussion or Limitations (see Summary). Recommendation: move Discussion ahead of Related Work in `main.tex`, then delete the `\anna{ask: should Discussion come before Related Work…}` note.

### 22. The pending `\reviewnote{Add: Existing validation work…}` and an optional roadmap sentence

Her advisor comment in CAROLINE.md says "the RTL work is not testing", but the pending reviewnote groups RTL verification with testing ("verifies or fuzzes RTL"). If Anna wants an opener, use the ITHICA form, which lists categories without merging them: `Prior work most relevant to \toolname{} falls into four categories: leakage testing, formal models and verification, axiomatic models and litmus tests, and Spectre defenses.` Otherwise drop the reviewnote. DECIDE (optional; adds about 20 words).

## Checked and consistent (no change)

- Contracts in Background match Protean §II-C almost word for word (observer mode / execution mode / adversary model; ARCH and CT; "leaks no data beyond that which is accessed (transmitted) sequentially"). Our "STT aims to uphold ARCH-SEQ" is a deliberate hedge where Protean says "uphold"; keep it, since we report STT bugs.
- Transmitter definition and the Kiriansky citation match Protean §II-A and RTL2MµPATH §II-A. Speculative/transient/sequential follows Protean §II-A.
- ReCon in Background agrees with Protean §X-3 ("marks memory words unprotected if they were previously leaked via load-load dependencies").
- The SynthLC quote on STT and SPT sharing a leakage contract is exact (RTL2MµPATH §II-B).
- The LCM description matches the LCM abstract ("axiomatic vocabulary ... derived from the established axiomatic vocabulary for formalizing processor memory consistency models").
- CheckMate in Background matches rtl2µspec §8 and RTL2MµPATH §II ("Check-based hardware security verification").
- The SPT untaint bug and "both since fixed" match Protean §VII-B4c ("we upstream and locally apply a patch").
- Ponce de León and Kinder as the axiomatic speculation semantics matches Serberus §8 ("take an axiomatic approach inspired by memory consistency models").
- Scam-V and Revizor: Serberus §8 files them under fuzzing, which is consistent with our testing paragraph.
- Pensieve, SpecDoctor, SpecCheck, Revizor follow-ups, and the design-level leak papers do not appear in her recent last-author papers, so there is no wording of hers to match.

b# Review action items: Related Work

Coverage check (2026-11-16): every weakness, question, numbered item, audit verdict, missing-work entry, DECIDE and open §12 item of the review was rechecked against ISCA-27 `748779e` (since `9006a33` only `discussion.tex`, `pipeline.tex` and `results.tex` changed; `related.tex` is unchanged); 7 added, 17 fixes added, 10 not carried over (list at the end, after the review → item map).

Targeted fixes only. Checked against ISCA-27 `9006a33` (`related.tex` unchanged since `6388130`). Line numbers are `sections/related.tex` unless marked. Rendered prose: 557 words now, about 547 after the items below (several correct facts and so don't shrink), about 520 with Decision R-7(c) and the software-clause merge (Helium §IX ≈ 450, Protean §X ≈ 320). Full review with the per-sentence audit: [reviews/2026-11-15_2356_related.md](reviews/2026-11-15_2356_related.md). This restates the open items of the 2026-11-15 wording audit (`paper_figures/related_work/RELATED_WORK_INVENTORY.md` §12) by their IDs (F1…, T1…). Fixed since then, so dropped: the misnamed `synthlc` key (now `wang2025synthesis`). Every quote below was checked this session against the local PDF named; Ayoub and Maurice (EuroSec 2021) could not be opened, so it is marked unverified.

## 🔴 Wrong, contradicts another section, or a reviewer will use it

- [ ] **`:16` "a pending-squash race in STT and SPT" (F1).** Protean calls it a "corner-case bug" that "creates a secret-dependent squash signal" (Protean p11 §VII-B4b), and the fix commit says "pending squash bug". Calling it a race makes it read as our UV6, the "visibility-point/squash race" in the same two defenses. "The gem5 prototypes" has no referent. → `Protean's extended fuzzer found a pending-squash bug in STT's and SPT's gem5 implementations that makes the squash signal secret-dependent, and manual inspection an SPT untaint bug, both since fixed~\cite{protean,nickscommittoSTT,mosier2025sptpr6}.` Also at `discussion.tex:38`: "a pending-squash race" → "the pending-squash bug".
- [ ] **`:13` "The Check tools verify microarchitectures against $\mu$hb models" (F2)** has it backwards. In the Check tools the µspec model *is* the microarchitecture, and it is checked against an MCM (rtl2µspec p1: "formally check that a specific microarchitecture correctly implements an MCM with respect to a suite of litmus test programs"). → `The Check tools verify that microarchitectures implement memory models, from pipelines to RTL~\cite{…same keys…};`
- [ ] **`:16` "Many were later broken at the design level … breaks … defeat … bypasses" (F3)** contradicts `results.tex:35`. Results places unXpec ("a stated limit of the design"), InvisiSpec's contention and STT's stores outside those defenses' guarantees. Three more problems:
  - Hacky Racers builds timers, not a channel (its title).
  - Cheng et al. bypass STT *and* DOLMA through a design assumption (Cheng p2).
  - DOLMA's store channel in STT is confirmed (AMuLeT p3); its "memory-ordering" channel is not (no local DOLMA copy).

  → `Design-level leaks, some through channels the defenses' papers exclude, include speculative interference in invisible speculation~\cite{behnia2021interference}, rollback timing in CleanupSpec~\cite{li2022unxpec}, inclusive caches and store-to-load forwarding in delay and cache-based schemes~\cite{aimoniotis2022doin,chakraborty2022timed}, store channels in STT~\cite{loughlin2021dolma}, timing channels and timers that sidestep many defenses~\cite{fustos2020spectrerewind,xiao2023hackyracers}, and reservation-station contention that STT's and DOLMA's designs overlook~\cite{cheng2026contention}.`
  - This also answers Q5 (UV2 vs. Chakraborty et al.): their attacks use store-to-load forwarding against cache-based countermeasures by design (title-level; no local copy), while UV2 is ReCon's implementation of STT skipping the check STT's paper prescribes for forwarding (`results.tex:52`, STT §6.4.2). "Design-level" here and "Implementation bugs" in the next sentence carry the distinction, so no further text is needed. To add the ROB-contention paper, see Missing related work.
- [ ] **`:7` "Because its contract violations compare two whole runs, … so each is root-caused by hand" (F6).** Three problems:
  - A violation is a program and two inputs whose final D-cache or TLB states differ (AMuLeT p6 §3.3); nothing compares whole runs.
  - "Each" overstates: duplicates are filtered by patches, contracts and regex signatures (p7 §3.3b). What is manual is root-causing: "a few hours to few days" (p7).
  - "The rule of the defense" is undefined.

  → `Each AMuLeT violation is a program and two inputs whose final cache or TLB states differ, so finding the leaking instruction is manual and takes hours to days~\cite[\S 3.3]{amulet}.`
  - Since `748779e`, `results.tex:65` points here (`\S~\ref{sec:related-work}`) for "a contract violation does not say which load leaked", so this sentence is now the paper's only statement of it: keep the leaking-instruction clause.
- [ ] **`:10` "Pensieve brings bounded model checking to early-stage defense designs" (T10).** Pensieve also checks early-stage defenses "against formal guarantees" (Pensieve p2). So the intro's "first … approach for validating early-stage prototypes … against their security guarantees" (`intro.tex:203`) holds only if this sentence says Pensieve checks a hand-written model, not the prototype. AMuLeT p7 §5.3 says it does: Pensieve "requires manual modeling of defenses in domain-specific languages". → `Pensieve~\cite{pensieve} model-checks hand-written models of early-stage defense designs.` This is also the paper's answer to W4/Q1 (what SimSpect finds that Pensieve cannot): bugs in the simulated defense's code, which a hand-written model leaves out by construction; ¶4's GhostMinion sentence is the example.
- [ ] **`:10` LEAVE is filed under secure speculation (F4).** RTL2MµPATH p14: "LEAVE [91] and UPEC-DIT-23 [31] are CT contract satisfaction approaches. CONJUNCT [36] is both." → delete `leave,` from the RTL list. Change the end of the sentence to `synthesizes leakage contracts and leakage signatures from RTL~\cite{mohr2024synthesizing,wang2025synthesis,rtl2upath}, and verifies which instructions are safe~\cite{leave,dinesh2024conjunct,dinesh2025hhoudini};`
- [ ] **`:13` TransForm, Isla and CheckMate (F5).** Four problems:
  - "them" makes Isla evaluate TransForm's tests.
  - "for transistency" is undefined.
  - CheckMate synthesized its attacks (CheckMate p3: "generated new attacks—MeltdownPrime and SpectrePrime"); it did not "find" them.
  - CheckMate's own cite is missing.

  → `TransForm~\cite{hossain2020transform} synthesizes litmus tests from axiomatic transistency models, Isla~\cite{armstrong2021isla} evaluates litmus tests against full ISA semantics~\cite{armstrong2019sail}, and CheckMate~\cite{checkmate} synthesized new attacks~\cite{trippel2018meltdownprime}.`
- [ ] **`:7` SpecCheck sits next to AMuLeT under "In gem5", as if both tested defenses.**
  - SpecCheck flags one FSM pattern "during an arbitrary program's simulation" (p1). It was evaluated only on an `lfence`-mitigated gadget (p9), never on a hardware defense.
  - "generic" is the word you banned paper-wide (Caroline, Fig. 1 v7 `:57`).
  - "Spectre defense prototypes" and bare "contracts" don't match Fig. 1 (T4).

  → `In gem5, SpecCheck~\cite{mckevitt2023speccheck} flags one fixed transient-execution pattern, and AMuLeT~\cite{amulet} randomly tests simulated defenses against security contracts (\S\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}).` Whether to add that AMuLeT is the only such tool: R-6. Together these answer Q6 (why SpecCheck is not a baseline).
- [ ] **`:16` closer: "complements these case-by-case findings: instead of designing an attack against one defense".**
  - Protean's bug came from a fuzzer and Pensieve's from model checking; nobody designed an attack.
  - It frames our work by what others lack.
  - It leaves a one-word last line ("specification.").

  → `\toolname{} instead derives security litmus tests from each defense's specification, so every specified defense is tested the same way.`
- [ ] **`intro.tex:68` "Prior work found five such bugs in three simulated Spectre defenses~\cite{amulet}"** contradicts `:16`, which adds Protean's two STT/SPT bugs and Pensieve's GhostMinion omission. → R-8.
- [x] **Done in ISCA-27 `748779e` (2026-11-16): the `discussion.tex:18` sentence is gone and `results.tex:65` now points to `sec:related-work`.** **The AMuLeT root-cause contrast appears three times:**
  - `:7` (this section);
  - `discussion.tex:18`: "A contract violation also does not localize a bug … root-caused by hand~\cite[\S 3.3]{amulet}; a \toolname{} hit names …" (new in `9006a33`);
  - `results.tex:65`: "a contract violation does not say which load leaked".

  Your guideline puts the full AMuLeT contrast in Related Work. → In `discussion.tex:18`, delete from "A contract violation also" through "let it transmit." At `results.tex:65`, change `(\S~\ref{sec:discussion})` to `(\S~\ref{sec:related-work})`.
- [ ] **`:7` "rather than relying on the simulated predictor's configuration~\cite{ayoub2021gem5spectre}".** Ayoub is unverified: it could not be opened, and its only description is an earlier agent summary. The verified contrast is AMuLeT's: it "preserves the µarch state of the predictors … between test cases" (AMuLeT p6 §3.2). → the `:7` closer below cites `\cite[\S 3.2]{amulet}`. Re-add Ayoub only after reading it.
- [ ] **`:16` "two of ReCon's authors report that ReCon leaks when an instruction has multiple secret sources" (C1).**
  - The source is an IEEE DataPort dataset that nobody has read; the bib note still says "TODO: replace with the ReConnaissance paper".
  - The clause does not say whether the leak is in ReCon's design or its implementation, and it sits next to our UV3.

  → R-4.

## 🟠 Terms (one name per concept; match Fig. 1, the intro, Background and the model section)

- [ ] **`:6` "Testing for speculative leakage" (T1)** → `Testing for transient leakage`. The intro says "attempt transient leakage" (`intro.tex:77`), and LCM's headings are "Detecting Transient Leakage" and "Formalizing Transient Leakage" (LCM p13).
- [ ] **`:7` closer (T2).** Four term problems, plus a one-word last line in the working PDF:
  - "one run": the paper's term is "a single execution" (`model.tex:9`).
  - "security guarantee": Fig. 1 contrasts AMuLeT's "security contracts" with our "defense specifications".
  - "protected operand": `model.tex:50` and `discussion.tex:18` say "protected value", and an operand is unsafe, not protected.
  - "each modeled misprediction" is vague.

  → `\toolname{} instead checks one execution against the defense's specification, so each hit names its transmitter and protected value, and it forces each test's mispredictions rather than relying on predictor state carried across tests~\cite[\S 3.2]{amulet}.`
- [ ] **`:7` "pre-silicon tools search for transient-execution bugs … or contract coverage" (T3).**
  - gem5 prototypes are pre-silicon too.
  - "Bug" is reserved for a leak the defense should block.
  - DejaVuzz's mechanism is "differential information flow tracking" (its abstract), so it belongs with information-flow tracking.
  - Geier et al. do coverage "based on Leakage Contracts" (their title).

  → `RTL tools search for transient-execution vulnerabilities through differential execution~\cite{hur2022specdoctor}, gadget-driven simulation~\cite{ghaniyoun2021introspectre,ghaniyoun2023teesec}, information-flow tracking~\cite{xu2025dejavuzz,rostami2024specure,defaveritron2025phantomtrails} or leakage-contract coverage~\cite{geier2025coverage}.`
- [ ] **`:7` "measure, synthesize or detect transient leaks" (T5).** Nobody synthesizes leaks; Medusa synthesizes attacks (its title). → `and other tools measure or detect transient leaks or synthesize attacks~\cite{xiao2020speechminer,weber2026trevex,moghimi2020medusa}`
- [ ] **`:7` "Most leakage testing runs random programs and compares executions" (T6).** "Most" is not true even of this paragraph's own list: SpecCheck, SpecFuzz, Teapot, oo7, Phantom Trails and SpeechMiner do not compare executions. → `Many leakage testers run random programs and compare pairs of executions.`
- [ ] **`:7` "software tools test programs for Spectre gadgets".** oo7 doesn't test; it is a static analysis that patches gadgets (its title: "…via Program Analysis"). → `and software tools find Spectre gadgets or test programs against leakage models~\cite{…same keys…}.`
- [ ] **`:10` "SNI and contracts (§2.2), which Reineke surveys; … build on them" (T7).** "contracts" is bare, and "which" and "them" each have three possible referents. → `…, SNI, and security contracts surveyed by Reineke~\cite{reineke2026foundations} (\S~\ref{sec:bg-contracts}); software analyses and secure compilers build on these~\cite{…same keys…}.`
- [ ] **`:10` the axiomatic semantics list omits LCMs (T8).** Serberus p14: "Mosier et al. [120] and Ponce-de-León and Kinder [27] take an axiomatic approach inspired by memory consistency models…". → `axiomatic~\cite{ponce2022cats,lcms}`
- [ ] **`:10` closer (T9).** The cited tools verify or synthesize contracts, not "guarantees". "generatively" is jargon, and "the implementation" has no referent. → `\toolname{} neither verifies nor synthesizes a contract: it formalizes the defense's own security guarantee over only the state that guarantee depends on, and generates tests from it.`
- [ ] **`:13` "Beyond the synthesis SimSpect builds on" and "models have also been synthesized automatically" (T11).** Which synthesis? Which models? Our "model" is the Alloy model. → `Beyond the minimal litmus-test synthesis \toolname{} builds on` (the term at `background.tex:2`) and `memory and $\mu$spec models have also been synthesized~\cite{memsynth,norman2023pipesynth,hsiao2021rtl2uspec}.`
- [ ] **`:16` "secret annotation" and "relaxations that recover performance" (T12).** "Relaxation" collides with Background's minimality relaxations (`background.tex:45`) and suggests weakened security. Protean p14 calls these "security-preserving optimizations". It also groups ProSpeCT with ConTExT and SpectreGuard ("explicit source-level secrecy annotations"), and Levioso with InvarSpec and Clearing Shadows. → `secrecy annotations~\cite{schwarz2020context,fustos2019spectreguard,daniel2023prospect}` and `security-preserving optimizations~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned,hajiabadi2024levioso}`; drop `daniel2023prospect` and `hajiabadi2024levioso` from "many others".
- [ ] **`:16` "GhostMinion's gem5 model" (T13).** Here "model" means the formal model. Pensieve p10: "the simulator open-sourced by the authors [2] does not implement the leapfrogging operations". → `GhostMinion's gem5 implementation` (or your R-1 term).
- [ ] **Six names for the system under test:**
  - `:7` "Spectre defense prototypes";
  - `:10` "the implementation";
  - `:13` "the defense's gem5 implementation";
  - `:16` "the gem5 prototypes", "GhostMinion's gem5 model" and "STT in gem5".

  → R-1. Your own `\anna` notes at `:7`, `:13` and `:16` already point to "simulated Spectre defense".

## 🟡 Density, paragraph goals, missing evidence

- [ ] **`:16` "Hu et al.\ survey hardware Spectre defenses~\cite{hu2021sok}."** The intro already cites this survey for the same point (`intro.tex:26`). → delete.
- [ ] **`:16` "Beyond those cited in the introduction, proposals include"** → `Other proposals include`
- [ ] **`:12` the heading "Axiomatic models and litmus tests"** doesn't cover the paragraph's first sentence (directed functional test generation). → `\textbf{Litmus tests and test generation:}` (matches the label `sec:litmus-testing-test-generation`). The opener itself, "Directed test generation has long served functional verification" (item 36, machine-sounding), → `Functional verification uses coverage-directed~\cite{fine2003cdg} and graph-based~\cite{mishra2004graph} test generation.` (both adjectives are the cited titles' own words: "Coverage Directed Test Generation …", "Graph-Based Functional Test Program Generation …").
- [ ] **`:10` "Speculation has been given pomset … semantics"** → `Speculation has pomset~\cite{…}, axiomatic~\cite{…}, abstract~\cite{…} and out-of-order operational semantics~\cite{…}`
- [ ] **`:16` Protean's other gem5 finding is missing.** Protean p10: "No prior work has found that division micro-ops are transmitters on gem5". Discussion says no evaluated leakage contract lists division, so a reviewer will connect the two. → after the bug sentence, add `Protean's fuzzer also showed that division micro-ops transmit on gem5~\cite[\S VII-B4]{protean}.` Adding it makes Q4 (why is a division leak in STT not a missed bug?) sharper, and Protean counts it as a security issue in STT and SPT: decide how to answer in R-10.
- [ ] **`intro.tex:47` "typically prototyped in pre-RTL microarchitectural simulators, especially gem5~\cite{gem5}"**: nothing supports "typically". Pensieve p1: "In most defense papers, the authors first implement their proposed defense mechanism in a concrete Gem5 model". → `typically prototyped~\cite{pensieve} in pre-RTL microarchitectural simulators` (adds a cite only; no rewrite). Optional second cite for `intro.tex:52-53` ("bugs that void the defense's security guarantee are much harder to detect"): `much harder to detect~\cite[\S 6.2]{pensieve}`. Pensieve §6.2 says GhostMinion's simulator "does not implement the leapfrogging operations", modeling that "is roughly sufficient for estimating the performance overhead … but leaves the GhostMinion implementation vulnerable", and that "microarchitectural simulators designed for performance evaluation are not trustworthy for security evaluation". Use it only if you read that as support for "harder to detect".
- [ ] **Software tools sit in ¶1, software analyses in ¶2 (W5; restructuring of ¶1).** `:7` "Scam-V~\cite{…} validates side-channel models against hardware, and software tools test programs for Spectre gadgets or against leakage models~\cite{…}." → end that sentence at `…against hardware.`, and append the software tools to ¶2's software clause (after T7): `…; software analyses and secure compilers build on these~\cite{…same 12 keys…}, and other software tools find Spectre gadgets or test programs against leakage models~\cite{oleksenko2020specfuzz,wang2021oo7,lin2025teapot,barthe2024lmtest}.` This absorbs the oo7 fix in 🟠. About the same length; it puts all software work in one place, so ¶1 is only hardware and simulator testing.
- [ ] **`:7` TEESec under "gadget-driven simulation" is unverified.** No local copy, and the ACM page returns 403. Its abstract (DOI 10.1145/3579371.3589070) confirms a pre-silicon tester built in Chipyard and run on two RISC-V out-of-order cores against "data and metadata leakage across isolation boundaries" of a TEE, so it belongs with the RTL tools, but the abstract does not say gadget-driven. → First read TEESec's method section. If it is not gadget-driven, use `gadget-driven simulation~\cite{ghaniyoun2021introspectre}` and end the sentence with `; TEESec extends pre-silicon testing to trusted execution environments~\cite{ghaniyoun2023teesec}.` (+8 words; wording from its title and abstract).
- [ ] **`references.bib` `perple` has no venue**, so it prints without one. Its DOI `10.1109/MICRO50266.2020.00037` is MICRO 2020. → add `booktitle = {Proceedings of the 53rd Annual IEEE/ACM International Symposium on Microarchitecture (MICRO)},`

## ⚪ Nitpicks

- [ ] **`:7` `(\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work})`** → `(\S\S~\ref{…} and~\ref{…})`. The SpecCheck fix above already does this.
- [ ] **`:4` the [Note] "Add: Existing validation work tests fabricated CPUs …"** is done: ¶1 and ¶2 now carry every cite in it. → delete the note.
- [ ] **`:13` "generated from relaxation cycles"** is a second collision with Background's "relaxation". → `generated from cycles of relaxed orderings~\cite{alglave2010fences}`
- [ ] **Serial comma.** The intro uses it (`intro.tex:232`, "STT, SPT, and ReCon"). Correction: this section does not "never" use it. It is mixed: serial at `:10` "…~\cite{cheang2019formal}, and SNI", `:13` ", and CheckMate's synthesis" and `:16` ", and many others"; not serial at `:7` "measure, synthesize or detect", "…, information-flow tracking~\cite{…} or contract coverage", `:10` "…, abstract~\cite{…} and out-of-order" and `:13` "…, run on hardware~\cite{…} and mutated". Results and Discussion mostly omit it. Pick one rule for the whole paper. **Recommended: serial**, since the intro uses it throughout and T7's "…, SNI, and security contracts surveyed by Reineke" is ambiguous without it. On top of the fixes above, that means `information-flow tracking~\cite{…}, or leakage-contract coverage~\cite{geier2025coverage}` (T3), `abstract~\cite{colvin2020abstractsemantics}, and out-of-order operational semantics` (`:10`) and `run on hardware~\cite{…}, and mutated to evaluate testing~\cite{mcmutants}` (`:13`); F3's fix and R-7(b) are already serial. Without the serial comma, delete the comma before the last "and" at `:13` "CheckMate", in F3's "reservation-station" and in R-7(b)'s "security-preserving optimizations", and rephrase T7 as `…, SNI and Reineke's survey of security contracts~\cite{reineke2026foundations}`.
- [ ] **One-word last lines in the PDF with notes hidden (p12).** ¶3 ends on "model." and ¶4 on "specification.". Both go away with R-2 and the `:16` closer above.
- [ ] **`discussion.tex:16–18`**: "Our transmission criteria", then a blank line, then "so a reported bug …". This prints a half sentence and a paragraph break on the Related Work page. → delete "Our transmission criteria" and the blank line.
- [ ] **Fig. 11's caption repeats Fig. 10's.** The two share Related Work's page (p11). Fig. 11 repeats Fig. 10's estimator, error-bar and A-UV5 text, about 7 lines. → in `tikz/timedet_bars_v7_8pt.tex:8`, replace everything from "Per-test costs are measured" through the A-UV5 sentence with `Estimator, error bars and A-UV5 as in Fig.~\ref{fig:firstdetv2}, with the time per test held fixed (A-UV5 ratio with generation: 0.007--0.16$\times$).` Revised 2026-11-16: the original fix dropped "with the time per test held fixed", the one error-bar detail Fig. 10 lacks. It also drops "Per-test costs are measured on dedicated nodes with the same CPU", which `REVIEW_ACTION_ITEMS_RESULTS.md` flags as false for AMuLeT, so the two fixes agree.

- [ ] **Pin cites where the section is known (item 48).** In F1's fix, `…an SPT untaint bug, both since fixed~\cite{protean,nickscommittoSTT,mosier2025sptpr6}.` becomes `…an SPT untaint bug~\cite[\S VII-B4]{protean}, both since fixed~\cite{nickscommittoSTT,mosier2025sptpr6}.` A note in `\cite[…]` attaches to the whole key list, so Protean needs its own `\cite`. The pending-squash bug is in Protean §VII-B4b and the untaint bug in §VII-B4c. Optional: `\cite[\S 6.2]{pensieve}` on the GhostMinion sentence (that is where Pensieve says the simulator "does not implement the leapfrogging operations") and `\cite[\S IV]{mckevitt2023speccheck}` on SpecCheck (its evaluation, where the only defense is an `lfence`).
- [ ] **Guideline length target for Related Work is off (§12 structural note).** `PAPER_AUDIT_GUIDELINES.md` line 23 says "Related Work about 250 words", but Helium's Related Work is about 450 words (§IX plus the part of it above the heading on p13, inventory §12). That is the figure the review's word counts use. → change it to `Related Work about 450 words (ours: about 450-650, since it carries more prior work)`. This is your guideline, so it is your edit.

## Missing related work

- [ ] **McVerSi** (Elver and Nagarajan, "McVerSi: A test generation framework for fast memory consistency verification in simulation", HPCA 2016, pp. 618–630). It is reference [16] in Caroline's rtl2µspec (p16), listed on p13 alongside litmus and PerpLE.
  - Why: it generates tests that find memory-consistency bugs in a simulated design, so it is the litmus line's closest analogue to testing a simulated defense. It was never considered. That it ran on gem5 is from memory and unverified.
  - Where: `:13` "run on hardware~\cite{…}" → "run on hardware or in simulation~\cite{…,elver2016mcversi}". Better, with the cite right after the thing it supports (guideline §6): `run on hardware~\cite{sarkar2011power,flur2016modelling,alglave2011litmus,perple} or in simulation~\cite{elver2016mcversi}`. "In simulation" is the title's own phrase.
  - Bib: not in `references.bib` or `ALL_NEW_ENTRIES.bib`. Draft, from Crossref (DOI 10.1109/HPCA.2016.7446099) and rtl2µspec's reference [16], both opened 2026-11-16: `@inproceedings{elver2016mcversi, author = {Elver, Marco and Nagarajan, Vijay}, title = {{McVerSi}: A Test Generation Framework for Fast Memory Consistency Verification in Simulation}, booktitle = {2016 IEEE International Symposium on High Performance Computer Architecture (HPCA)}, pages = {618--630}, year = {2016}, doi = {10.1109/HPCA.2016.7446099}}`
- [ ] **UPEC-DIT** (Deutschmann et al., DAC 2022) **and UPEC-DIT-23** (arXiv 2308.07757, since published in IEEE TCAD 2024).
  - Why: Caroline groups them with LEAVE and ConjunCT (RTL2MµPATH p14, refs [31] and [32]).
  - Where: `:10`. Corrected 2026-11-16: the two go in different lists. RTL2MµPATH p14 says "UPEC-DIT [32] is a CT contract synthesis approach. LEAVE [91] and UPEC-DIT-23 [31] are CT contract satisfaction approaches. CONJUNCT [36] is both." So F4's fixed sentence becomes `synthesizes leakage contracts and leakage signatures from RTL~\cite{mohr2024synthesizing,wang2025synthesis,rtl2upath,deutschmann2022upecdit}, and verifies which instructions are safe~\cite{leave,deutschmann2024scalable,dinesh2024conjunct,dinesh2025hhoudini};`
  - Bib: absent. Drafts from Crossref (DOIs below) and RTL2MµPATH refs [31]–[32], opened 2026-11-16. Cite the TCAD version, not the arXiv (guideline §6, bib hygiene): `@inproceedings{deutschmann2022upecdit, author = {Deutschmann, Lucas and M{\"u}ller, Johannes and Fadiheh, Mohammad R. and Stoffel, Dominik and Kunz, Wolfgang}, title = {Towards a Formally Verified Hardware Root-of-Trust for Data-Oblivious Computing}, booktitle = {Proceedings of the 59th ACM/IEEE Design Automation Conference (DAC)}, pages = {727--732}, year = {2022}, doi = {10.1145/3489517.3530981}}` and `@article{deutschmann2024scalable, author = {Deutschmann, Lucas and M{\"u}ller, Johannes and Rahmani Fadiheh, Mohammad and Stoffel, Dominik and Kunz, Wolfgang}, title = {A Scalable Formal Verification Methodology for Data-Oblivious Hardware}, journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems}, volume = {43}, number = {9}, pages = {2551--2564}, year = {2024}, doi = {10.1109/TCAD.2024.3374249}}`
- [ ] **LCMs / Clou** (`lcms`): `:10`, the T8 item above. Bib: present.
- [ ] **CheckMate** (`checkmate`), cited next to its name: `:13`, the F5 item above. Bib: present.
- [ ] **Protean's division-transmitter finding:** `:16`, the 🟡 item above. Bib: present.
- [ ] **Witharana and Mishra, "Speculative Load Forwarding Attack"** (ICCAD 2022). The title comes from inventory §8; the paper was not read.
  - Why: a store-to-load forwarding attack that a reviewer may tie to UV2.
  - Where: `:16`, beside `chakraborty2022timed`.
  - Bib: absent; it was dropped earlier only because it had no bib entry.
  - **Verdict 2026-11-16: do not add.** Its abstract (DOI 10.1145/3508352.3549417; the ACM page returned 403, so it was read in Semantic Scholar's copy) presents "a Meltdown/MDS type of attack to leak data from the load queue in AMD Zen family architectures". That attack is on commercial hardware, not on a Spectre defense, and goes through load-queue forwarding, not store-to-load forwarding. It fits neither ¶4's list of defense flaws nor a UV2 comparison.
- [ ] **Aimoniotis et al., ROB contention as speculative interference** (IEEE CAL 2021).
  - Where: `:16`, beside `behnia2021interference`.
  - Bib: `ALL_NEW_ENTRIES.bib` L599 has an entry, but its year is marked TODO; unverified.
  - Checked 2026-11-16. Crossref (DOI 10.1109/LCA.2021.3123408) gives IEEE CAL 20(2):162–165, 2021. The abstract (Semantic Scholar) says defenses that "selectively lift defenses for speculation invariant instructions" are broken by "forward speculative interference" through ROB occupancy. Clause for F3's fixed sentence (+9 words): `speculative interference in invisible speculation~\cite{behnia2021interference} and in defenses that lift protection for speculation-invariant instructions~\cite{aimoniotis2021robcontention}`. Bib: copy `aimoniotis2021robcontention` from `ALL_NEW_ENTRIES.bib` and replace its TODO note with `volume = {20}, number = {2}, pages = {162--165}, doi = {10.1109/LCA.2021.3123408}`.
- **Optional, low relevance:**
  - CounterPoint (ASPLOS 2026; Caroline is a co-author) refines microarchitectural models with event counters. It could go after Scam-V at `:7`. Not in the bib; the PDF is local. Recommendation: skip unless there is space. If added: `Scam-V~\cite{nemati2020scamv,buiras2021observation} validates side-channel models against hardware, and CounterPoint~\cite{lindsay2026counterpoint} uses hardware event counters to refute and refine microarchitectural assumptions.` (the title's wording). Bib from Crossref (DOI 10.1145/3779212.3790145): `@inproceedings{lindsay2026counterpoint, author = {Lindsay, Nick and Trippel, Caroline and Khandelwal, Anurag and Bhattacharjee, Abhishek}, title = {{CounterPoint}: Using Hardware Event Counters to Refute and Refine Microarchitectural Assumptions}, booktitle = {Proceedings of the 31st ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2 (ASPLOS)}, pages = {459--475}, year = {2026}, doi = {10.1145/3779212.3790145}}`
  - Simner et al. "Abstract Architecture Catches Concrete Bugs", Alglave et al. "Armed Cats" and ArchSem could go in `:13`. Not read; unverified. Bib entries exist only in `~/trippel/JS-fellowship-app/references.bib` (`simner2027abstract`, EuroSys '27, "to appear"; `alglave2021armed`, TOPLAS 43(2); `perami2026archsem`, PACMPL 10(POPL)), all with "and others" author lists (unverified). Title-level clause if wanted, at the end of the `:13` litmus sentence: `; an abstract architecture model has also caught concrete page-table synchronisation bugs~\cite{simner2027abstract}`. Recommendation: skip; none is about test generation for a simulated design.
  - SPT PR #4 (`mosier2025sptpr4`, `ALL_NEW_ENTRIES.bib` L553) could join the `:16` cite list. Protean already covers it. Exact text: in F1's fix, `both since fixed~\cite{protean,nickscommittoSTT,mosier2025sptpr4,mosier2025sptpr6}` (or, with the pin item, `~\cite{nickscommittoSTT,mosier2025sptpr4,mosier2025sptpr6}`). Bib: copy from `ALL_NEW_ENTRIES.bib` L553; its title matches Protean's ref [93] ("SPT: Fix pending squash bug," GitHub Pull Request #4). It is SPT's own fix, which R-9 also needs.
- **Do not add:**
  - Helium: it quantifies non-speculative leakage ("As we do not consider speculative leakage", Helium p13).
  - µSpectre: it belongs in Discussion "Generality", as another speculation source.

## Decisions (recommendation first)

- [ ] **R-1. One name for the system under test.**
  - **Recommended: "simulated (Spectre) defense"** (Fig. 1; `intro.tex:205` and `:232`; your `\anna` notes).
  - Alternative: "gem5 implementation", Caroline's own usage (Protean p2–3, p11).
  - Either way, never call gem5 code a "model" or "prototype".
  - Text under the recommended option (after the fixes above): `:7` "randomly tests simulated defenses against security contracts" (SpecCheck item); `:13` "its tests run on the simulated defense" (R-2); `:16` F1 `…found a pending-squash bug in simulated STT and SPT that makes the squash signal secret-dependent, …`; T13 `Pensieve's authors found that the simulated GhostMinion omits the leapfrogging the defense relies on~\cite{pensieve}`. T9's fixed closer needs no noun, and F3 removes "bypasses STT in gem5".
  - Text under the alternative: `:7` "randomly tests gem5 implementations of defenses against security contracts"; `:13` "its tests run on the defense's gem5 implementation"; F1 and T13 as written ("STT's and SPT's gem5 implementations", "GhostMinion's gem5 implementation").
- [ ] **R-2. ¶3's closer (`:13`).**
  - **Recommended (b):** `Unlike CheckMate's exploit patterns, \toolname{}'s leakage predicate states what a defense forbids, and its tests run on the simulated defense.` It answers Caroline's "What is different about this?" (`oldtechnicaldetails.tex:164`).
  - (a): `\toolname{} applies minimal litmus-test synthesis to Spectre defenses and runs the tests on the simulated defense instead of analyzing a model.` This doesn't distinguish SimSpect from litmus tests run on hardware.
- [ ] **R-3. "Security litmus test" means something different from CheckMate's.** CheckMate: "the most compact representation of an exploit program" (CheckMate p5).
  - **Recommended:** leave the term as is; Background credits CheckMate.
  - Alternative: add ", which need no receiver," after "security litmus tests" in the `:16` closer.
- [ ] **R-4. Kvalsvik and Själander vs. UV3.**
  - (a) Keep UV3 as new and cite them neutrally (the current text).
  - (b) Relabel UV3 as a known bug.
  - (c) Drop the cite.
  - Whichever you pick, the clause should say "design" or "gem5 implementation", and the dataset should be replaced by their paper once it is found.
  - New evidence (2026-11-16). The dataset's DataCite record (DOI 10.21227/dkjt-k008) carries their paper's abstract: "We show that ReCon leaks potential secrets in cases where an instruction has multiple secret sources. We present insights into the interaction of Speculative Taint Tracking (STT) and ReCon, and show how their combination undermines STT's security guarantee. We present ReConnaissance, which fixes this oversight, and show that it lowers the performance overhead-reduction of ReCon from 23.5% to 18.3%."
    - So it is a design oversight, fixed at a performance cost, and C1's reading is "design".
    - The abstract does not name the mechanism, so whether it is UV3's "only the oldest taint source" (`results.tex:58`, `taint_tracker.cc:108–131` in ReCon's implementation of STT) stays open. That is Q2, and the same trigger ("an instruction with several tainted operands") makes it a real risk.
  - Text for (a): `…~\cite{pensieve}, and two of ReCon's authors report that ReCon's design leaks when an instruction has multiple secret sources~\cite{kvalsvik2025reconnaissance}.`
  - Text for (b): `…multiple secret sources~\cite{kvalsvik2025reconnaissance}, which \toolname{} also finds (\S~\ref{sec:bug-otb}).` Also `intro.tex:240` "six previously unknown bugs" → "five previously unknown bugs", and UV3 moves into Known Bugs Replicated (`results.tex:56–58`).
  - Text for (c): end the sentence at `…the defense relies on~\cite{pensieve}.` and delete the Kvalsvik clause.
  - Recommendation: (a) with "design", and get their paper before submission (inventory §10). Switch to (b) if the paper describes the oldest-source mechanism.
- [ ] **R-5. AMuLeT's high-level contract (CT-SEQ/ARCH-SEQ, coarser than the guarantee).** This contrast is already stated in the intro, Background, Results and Discussion; Related Work only points to Results.
  - **Recommended:** keep the pointer and change guideline §5 to match.
  - Alternative: add `against \contract{CT-SEQ} or \contract{ARCH-SEQ}, which are coarser than the defenses' guarantees` to the `:7` AMuLeT clause, and cut Discussion's "A high-level contract that approximates the guarantee …" sentence.
  - The alternative should also carry W1's "four of nine" point, which guideline §5's "full version" lists. Full clause: `AMuLeT~\cite{amulet} randomly tests simulated defenses against \contract{CT-SEQ} or \contract{ARCH-SEQ}, which are coarser than the defenses' security guarantees, so four of its nine reports fall outside them (\S~\ref{sec:known-bugs})`. The facts are at `results.tex:31` ("nine bugs …; five fall in that scope") and `:38`.
  - Text for the recommended guideline change:
    - `PAPER_AUDIT_GUIDELINES.md` §5 (line 129) → `AMuLeT contrast: stated in full once, in Results (high-level contract; four of nine reports out of scope); Related Work points there and adds only root-causing and predictor state; the intro keeps at most one neutral sentence.`
    - §2 (line 78), "State the contrast once each in the intro, Related Work and Results' comparison" → `State it in full once, in Results, with one neutral sentence in the intro and a pointer from Related Work`.
  - Either way, `discussion.tex:18` still makes a fourth statement ("A high-level contract that approximates the guarantee, as in AMuLeT…"). You kept it in `748779e`; guideline §2's "nowhere else" would cut it.
- [ ] **R-6. Say that AMuLeT is the only prior tool that tests simulated defenses.**
  - **Recommended: say it.** It is Caroline's own claim (Fig. 1 v7 `:58`), and it now checks out: SpecCheck never tested a hardware defense (p9), and Pensieve checks models (p2). Cheng et al. hand-built gadgets on gem5 STT, but that is not a tool.
  - Proposed sentence: `In gem5, SpecCheck~\cite{mckevitt2023speccheck} flags one fixed transient-execution pattern, and only AMuLeT and its extension in Protean~\cite{amulet,protean} test simulated defenses, randomly and against security contracts (\S\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}).`
  - Variant that also names the closest prior work (review restructuring of ¶1; Caroline does this in her own Related Work sections, rtl2µspec p13 and RTL2MµPATH p14): `In gem5, SpecCheck~\cite{mckevitt2023speccheck} flags one fixed transient-execution pattern; the closest prior work, AMuLeT~\cite{amulet} and its extension in Protean~\cite{protean}, are the only tools that test simulated defenses, randomly and against security contracts (\S\S~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}).`
  - Context checked 2026-11-16:
    - The intro's own "only prior tools" sentence is commented out (`intro.tex:105`). The live intro calls AMuLeT "the current state-of-the-art approach" (`intro.tex:107`), so this would be the paper's only "only" claim.
    - The one gem5 paper still unread, Ayoub and Maurice, is titled "Reproducing Spectre Attack with gem5: How To Do It Right?": it reproduces attacks rather than testing defenses (title-level only). So it does not undercut "only".
- [ ] **R-7. The defense catalogue (`:16`, "and many others" with 14 keys after the T12 move).**
  - (a) Keep it, per your 2026-11-11 directive to "cite as many papers as possible".
  - **Recommended (b):** cut "and many others~\cite{…}" and keep the groups that have a description. Caroline's own long cite lists always sit under a stated property (Protean p14).
  - (c) Delete the whole sentence (about −20 words), since the paragraph's goal is flaws and bugs.
  - Text for (b), with T12 applied: `Other proposals include context-sensitive fencing~\cite{taram2019csf}, conditional speculation~\cite{li2019conditional}, secrecy annotations~\cite{schwarz2020context,fustos2019spectreguard,daniel2023prospect}, CFI-informed speculation~\cite{koruyeh2020speccfi}, cache partitioning~\cite{kiriansky2018dawg}, and security-preserving optimizations~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned,hajiabadi2024levioso}.`
  - Text for (c): delete that sentence as well as the Hu et al. sentence, so ¶4 opens with F3's `Design-level leaks, …`.
- [ ] **R-8. The intro's count of prior bugs (`intro.tex:68`).**
  - **Recommended (a):** `Prior work found eight such bugs in six simulated Spectre defenses~\cite{amulet,protean,pensieve} (\S\S~\ref{sec:known-bugs} and~\ref{sec:related-work}).` The eight are AMuLeT's five in-scope bugs, Protean's pending-squash and SPT untaint bugs, and Pensieve's GhostMinion omission; you decide what counts.
  - (b) Keep "five" and name AMuLeT. This introduces AMuLeT before `:107` and breaks "introduce once".
  - Context found 2026-11-16: Caroline set "five" herself, in the commented note at `intro.tex:69`: "I changed to 5 and then you can fwd ref to the section where you justify that number".
  - (c) Keep her number and drop the implication that five is the total: `Prior work found such bugs, five of them in three simulated Spectre defenses~\cite{amulet} (\S~\ref{sec:known-bugs}).` This no longer contradicts `:16`, names no tool before `:107`, and keeps her forward reference.
  - Recommendation update: (c), because it respects Caroline's edit. (a) was the review's pick, made without knowing she had set the number.
- [ ] **R-9. Our SPT build predates Mosier's SPT fixes (Q3).**
  - Background: `/work/gem5-spt` is at `0d2be0f` (May 2022) and lacks FPSG-UIUC/SPT PRs #4–#6 (`URGENT_TODO.md:115`, `claudelog.md:289`). Related Work `:16` says both bugs are "since fixed", and UV6 is reported on SPT-Fence (`discussion.tex:24`), so a reviewer will ask whether our SPT hits are the known bugs.
  - (a) Keep the build and say so after a trace check. Append to `discussion.tex:38`: `Our SPT build predates Mosier's SPT fixes~\cite{mosier2025sptpr4,mosier2025sptpr6}; our runs raise no faults, which the untaint bug needs~\cite[\S VII-B4]{protean}, and [none / N] of our SPT hits have two mispredicted branches resolving in one cycle, which the pending-squash bug needs.` Fill the bracket from the traces. "No faults" rests on `wiki/design/MODELS_AND_BUILDS.md:333` ("single-core, fault-free gem5 runs squash only on a branch misprediction or a store-load memory-order violation") and on the untaint bug needing loads "following a pending fault" (Protean §VII-B4c).
  - (b) Rebuild SPT at upstream master and rerun the SPT rows; then `We test SPT at upstream commit [hash], which includes both fixes~\cite{mosier2025sptpr4,mosier2025sptpr6}.`
  - Recommendation (from `URGENT_TODO.md:115`): (a) now, (b) after the deadline.
- [ ] **R-10. Protean's division transmitter vs. our leakage contracts (Q4).**
  - Evidence:
    - Protean §VII-B4b: division micro-ops "leak a function of their n-bit divisor and 2n-bit dividend on the gem5 O3 CPU by conditionally faulting". It is one of "two security issues that also impact all three secure baselines (STT/SPT/SPT-SB)".
    - STT §6.1.1: "An instruction should be a transmit instruction if its execution creates operand-dependent resource usage that can reveal the operand". STT's Table 1 lists "Execution unit timing" as an explicit channel.
    - Our STT specification's transmitters are load addresses and branch predicates (`results.tex:35`). Discussion says no evaluated leakage contract lists a divide (`discussion.tex:40`), and our instruction vocabulary excludes `div`/`idiv` (`URGENT_TODO.md` ILV-3).
  - (a) Disclose it as a limitation. Add the Protean clause (🟡 item), and in `discussion.tex:40` change "faulting transmitters such as a divide, which no evaluated leakage contract lists" → `faulting transmitters such as a divide, which Protean found leaks on gem5~\cite[\S VII-B4]{protean} but no evaluated leakage contract lists`. This follows guideline §2b: every known bug we do not find gets a limitation with its reason.
  - (b) Add division to the STT and SPT leakage contracts and to the vocabulary. This changes the model, so it is future work and needs your sign-off.
  - (c) Leave Protean's division finding out of Related Work, which leaves Q4 for the rebuttal.
  - Recommendation: (a). Whether STT's general definition obliges our STT specification to list division is the underlying question about what the model should mean, and it is yours.
- [ ] **R-11. Section order (your `\anna{ask: should Discussion come before Related Work or after?}` at `:2`; the review noted it but did not answer it).**
  - (a) Keep Related Work before Discussion (now, `main.tex:87–88`). Protean, RTL2MµPATH and TransForm have no Discussion section: Related Work comes right before the Conclusion.
  - (b) Put Discussion first, as Helium does (§VIII Limitations and Future Directions, then §IX Related Work). Helium is your model paper for section structure (guideline §2). → swap `\input{sections/related}` and `\input{sections/discussion}` in `main.tex:87–88`.
  - Recommendation: (b). It matches the model paper, and Discussion's limitations follow straight from Results. Nothing in Related Work depends on coming before Discussion. Once decided, delete the `:2` note.

## Review → item map (coverage check 2026-11-16)

- Weaknesses: W1 → R-5 (contract, four of nine), R-6 (only tool, closest), `:7` SpecCheck item; W2 → F2, F4, F1, F6, F3 (Hacky Racers), `:7` software-tools item (oo7); W3 → F3; W4 → T10, R-2; W5 → R-7, software-clause merge; W6 → McVerSi, UPEC-DIT, LCMs.
- Questions: Q1 → T10; Q2 → R-4; Q3 → R-9; Q4 → division item, R-10; Q5 → F3 note; Q6 → SpecCheck item, R-6.
- Restructuring: ¶1 → T6, software-clause merge, R-6 variant; ¶2 → F4, T10, T9; ¶3 → heading item, R-2; ¶4 → Hu et al. item, R-7; cross-section → done (`748779e`).
- Numbered items: 1 F1, 2 F2, 3 F3, 4 F4, 5 F5, 6 F6, 7 T10, 8 SpecCheck, 9 `:16` closer, 10 R-8, 11 done, 12 Ayoub, 13 R-4, 14 R-7, 15 heading + R-2, 16–27 T1–T13 + oo7, 28 R-1, 29 R-2, 30 R-3, 31 R-5, 32 R-6, 33 division, 34 "typically", 35 Hu et al., 36 heading item + T10 + closer + R-2, 37–46 nitpicks, 47 not carried over, 48 pin cites.
- Audit-table verdicts beyond the numbered items: TEESec (🟡 item), SIGFuzz and `dong2026interplay` (verified, not carried over).
- Missing related work: every row of the review's §6b is an entry above. §12: F1–F6 and T1–T13 by ID; D1 → R-1, D2 → R-2, D3 → R-3, C1 → R-4; structural notes → R-6 variant (closest prior work), F6 and `:16` closer (deficiency framing), guideline length item.

## Not carried over

- AMuLeT root-cause contrast stated three times: done in ISCA-27 `748779e` (ticked above).
- Misnamed `synthlc` key (half of F4): renamed `wang2025synthesis` before the review.
- §12's intro "a recent squash race in STT~\cite{protean}": commented out at `intro.tex:70` and `:84`, so it does not print.
- SIGFuzz "in RTL" (review: unverified): its abstract (DOI 10.23919/DATE56975.2023.10136966) evaluates the Rocket and BOOM designs, so the claim holds.
- `dong2026interplay` RTL vs. model (review: unverified): its abstract (DOI 10.1109/SP63933.2026.00203) reports case studies on BOOM processors, so it stays in the RTL list.
- "Invisible speculation" (item 47): Behnia et al.'s class name; the review says keep it.
- Timing-channel discovery clause and the one-clause software-compiler list (audit rows): kept for breadth per your 2026-11-11 directive; no defect.
- 3-line gap under Fig. 11: template float separation, which guideline §0 says not to touch.
- Already addressed or already true: the review's §8 comments (`intro.tex:102` move, Fig. 1 v7 `:58` RTL placement, `:48` Guarnieri ref; no e.g. or i.e. here), "¶2 fine in shape", and "silicon and RTL lists in one clause each".
- §12 alternative wordings (F2 long form, F3/F6 first drafts, T2 "the unsafe operand a protected value reached", T7 OISA "leakage contract", T9 ending in "gem5 implementation"): superseded by the review's fixes above.

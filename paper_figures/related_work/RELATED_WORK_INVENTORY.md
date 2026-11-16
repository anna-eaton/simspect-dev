# Related Work inventory (ISCA-27, 2026-11-11)

Every paper or bullet that was ever a candidate for the paper's Related Work section, with its status after the 2026-11-11 rewrite of `ISCA-27/sections/related.tex` (Anna: "the related work is way too long ... make a list somewhere of all the bullets/papers you ever had that could go in this area ... we should really cite as many papers as possible while not going into any detail about them unless it's a direct comparison like AMuLeT"; format modeled on Helium §IX). Sources combed: the live `related.tex` before the rewrite (bullets, notes, CUT LIST comments, [Proposed] paragraphs), all nine git revisions of it (`1c5c53d` to `ae391d0`), `RELATED_WORK_DRAFT.md`, `rw1_validators.md` to `rw8_defense_bugs_recent.md`, `ALL_NEW_ENTRIES.bib`, `rw6_attacks.bib`, and the area-relevant entries already in `sections/references.bib`.

Line format: `key` (or where its bib entry is) · venue and year · what it is · relation to SimSpect · **status**. "cited" = cited in the new Related Work; "cited elsewhere" = not in Related Work but cited live in the named section; "dropped" = not cited, with the reason. "Appended" = entry copied verbatim into `references.bib` on 2026-11-11 from `ALL_NEW_ENTRIES.bib` at the given line. The rewritten section has 561 prose words (citations stripped) and 126 distinct citation keys.

## 1. Testing CPUs, simulators and software for speculative leakage

- `amulet` · ASPLOS 2025 · random contract-based relational testing of gem5 Spectre defense prototypes · closest prior work and our baseline · **cited** (two sentences: root-causing by hand, §3.3; points back to Results for scope and efficiency); also intro, pipeline, results, discussion
- `revizor` · ASPLOS 2022 · black-box CPU testing against speculation contracts · origin of the contract-testing method AMuLeT reuses · **cited**; also intro, background
- `oleksenko2023hideseekspectresefficient` · S&P 2023 · makes Revizor-style random testing efficient · efficiency by better random search, not targeting · **cited**; also intro
- `hofmann2023speculationatfault` · USENIX Security 2023 · speculation contracts extended to CPU exceptions, tested with Revizor · Revizor line; refines a model by testing CPUs · **cited**
- not in bib; ALL_NEW_ENTRIES.bib L618 (`hofmann2023specfault`) · USENIX Security 2023 · same paper as above · duplicate entry · **dropped**: duplicate of `hofmann2023speculationatfault`
- `oleksenko2026enterexit` (appended, ALL_NEW_ENTRIES.bib L609) · S&P 2026 · Revizor extended to isolation boundaries; new AMD leaks · Revizor follow-up on commercial CPUs · **cited**
- `weber2026trevex` · S&P 2026 · black-box detection of data-flow transient-execution vulnerabilities · silicon testing with no defense model · **cited**
- `xiao2020speechminer` · NDSS 2020 · framework measuring speculative-execution vulnerabilities on real CPUs · measurement on silicon, not defense validation · **cited**
- `moghimi2020medusa` · USENIX Security 2020 · automated synthesis of data-sampling attacks (Transynther) · synthesizes attacks on CPUs, not defense tests · **cited**
- `weber2021osiris` · USENIX Security 2021 · automated discovery of microarchitectural timing side channels · transmitter discovery, not defense validation · **cited**
- `rajapaksha2023sigfuzz` · DATE 2023 · fuzzing framework for microarchitectural timing side channels · transmitter discovery · **cited**
- `borkar2024whisperfuzz` (appended, ALL_NEW_ENTRIES.bib L71) · USENIX Security 2024 · white-box RTL fuzzing for processor timing vulnerabilities · white-box like our hooks, but timing channels · **cited**
- `mckevitt2023speccheck` · PACT 2023 · gem5 commit-stage monitor flagging a generic transient pattern · closest gem5 tool; no tests, no defense guarantee · **cited** (one clause)
- `nemati2020scamv` · CAV 2020 · generates programs validating abstract side-channel models against hardware · model-vs-implementation testing, for side-channel models · **cited**
- `buiras2021observation` · MICRO 2021 · Scam-V follow-up: validation by observation refinement · same line as Scam-V · **cited**
- `oleksenko2020specfuzz` · USENIX Security 2020 · fuzzing software to expose Spectre gadgets · software-side gadget finding · **cited**
- `wang2021oo7` · IEEE TSE 2021 · binary analysis that detects and patches Spectre gadgets · software-side · **cited**
- `lin2025teapot` (appended, ALL_NEW_ENTRIES.bib L81) · CGO 2025 · finds Spectre gadgets in COTS binaries · software-side · **cited**
- `barthe2024lmtest` (appended, ALL_NEW_ENTRIES.bib L61) · CCS 2024 · LmSpec leakage models plus LmTest testing of crypto code · tests software against leakage models (Helium's main comparison) · **cited**
- `ayoub2021gem5spectre` (appended, ALL_NEW_ENTRIES.bib L505) · EuroSec 2021 · how to reproduce Spectre in gem5 (configuration, predictor) · supports forcing mispredictions over relying on predictors · **cited**
- no entry (InvisiSpec GitHub issue #11) · GitHub 2024 · public report of speculative evictions (A-UV1) and MSHR interference · A-UV1 reported publicly before AMuLeT · **dropped**: issue, not a paper; A-UV1 provenance belongs in Results if anywhere
- no entry (μRL, arXiv 2502.14307) · arXiv 2025 · RL with LLM embeddings for transient bugs · not read · **dropped**: unverified, no entry
- no entry (ABSynthe NDSS 2020 / Absynthe PLDI 2023) · — · contention-channel synthesis / program synthesis · not transient-execution testing (rw1) · **dropped**

## 2. RTL (pre-silicon) fuzzing and testing

- `hur2021difuzzrtl` · S&P 2021 · differential RTL fuzzing for functional CPU bugs · functional RTL fuzzing baseline · **cited**
- `solt2024cascade` · USENIX Security 2024 · CPU fuzzing via intricate program generation · functional RTL fuzzing · **cited**
- `hur2022specdoctor` · CCS 2022 · differential RTL fuzzing for transient-execution vulnerabilities · undefended RTL, random generation · **cited**; also intro
- `xu2025dejavuzz` · ASPLOS 2025 · RTL fuzzer with swappable memory and differential IFT · random/coverage-guided on baseline cores · **cited**
- `ghaniyoun2021introspectre` · ISCA 2021 · gadget fuzzing plus RTL simulation log analysis · simulation-based, generic gadgets on undefended RTL · **cited**; also intro
- `ghaniyoun2023teesec` (appended, ALL_NEW_ENTRIES.bib L42) · ISCA 2023 · pre-silicon vulnerability discovery for trusted execution environments · tests a protection pre-silicon, at RTL · **cited**
- `rostami2024specure` · DAC 2024 · static RTL information flow guides speculative-vulnerability fuzzing · guidance from the netlist, not a defense model · **cited**
- `defaveritron2025phantomtrails` · USENIX Security 2025 · template-free pre-silicon discovery of transient data leaks · channel-independent, but undefended RTL · **cited**
- `geier2025coverage` · arXiv 2025 · contract-based coverage-guided fuzzing of Rocket/BOOM · random generation against a sequential contract · **cited**

## 3. Formal verification of secure speculation in hardware (and IFT context)

- `fadiheh2019upec` · DATE 2019 · UPEC: formal RTL detection of transient-execution vulnerabilities · formal counterpart; needs RTL · **cited**
- `fadiheh2020formal` · DAC 2020 · UPEC for out-of-order processors · same · **cited**
- `fadiheh2023exhaustive` · IEEE TC 2023 · exhaustive detection of transient side channels in RTL · same · **cited**; also intro
- `contractshadow` · ASPLOS 2025 · RTL verification of secure speculation with contract shadow logic · same · **cited**; also intro
- `leave` · CCS 2023 · verifies open-source cores against leakage contracts · RTL proof vs our simulator testing · **cited**
- `dong2026interplay` · S&P 2026 · model checking secure-speculation processor designs (case study) · formal defense verification, concurrent · **cited**
- `zagieboylo2023specverilog` · CCS 2023 · information-flow type system for secure speculation in HDL · design-time verification · **cited**
- `yang2026compass` (appended, ALL_NEW_ENTRIES.bib L463) · ASPLOS 2026 · picks the lightest taint scheme for RTL security proofs · formal RTL, same community · **cited**
- `cabodi2019speculationmc` (appended, ALL_NEW_ENTRIES.bib L308) · C2SI 2019 · model checking abstracted processor models for speculation properties · abstract processor model, verified not tested · **cited**
- `mohr2024synthesizing` · DATE 2024 · synthesizes leakage contracts for RISC-V cores from tests · synthesizes a contract; we take the guarantee · **cited**
- `synthlc` (really LeaSyn, Wang et al.) · CCS 2025 · synthesis of sound and precise leakage contracts for RISC-V · same; key is misnamed (SynthLC is `rtl2upath`) · **cited**
- `rtl2upath` · MICRO 2024 · µPATH synthesis from RTL, incl. SynthLC leakage signatures · bottom-up; source of our "leakage contract" term · **cited**; also intro, background
- `dinesh2024conjunct` · S&P 2024 · proves unbounded instruction safety by invariant learning · proves the transmitter set; we take it as input · **cited**
- `dinesh2025hhoudini` · ASPLOS 2025 · scalable invariant learning for safe-instruction sets (BOOM) · same · **cited**
- `pensieve` · ISCA 2023 · bounded model checking of hand-written early-stage defense models for SNI · closest early-stage work; checks a model, not the prototype · **cited** (one clause); also intro
- `blackbox` · IEEE Computer 2024 · guide to formal verification of secure processors for architects · survey anchor · **cited**
- not in bib; ALL_NEW_ENTRIES.bib L431 (`tiwari2009glift`) · ASPLOS 2009 · gate-level information flow tracking · IFT context only · **dropped**: no contrast needed
- not in bib; ALL_NEW_ENTRIES.bib L441 (`solt2022cellift`) · USENIX Security 2022 · cell-level dynamic IFT for RTL · IFT context only · **dropped**: no contrast needed
- not in bib; ALL_NEW_ENTRIES.bib L451 (`hu2021hwift`) · ACM CSUR 2021 · survey of hardware IFT · IFT context only · **dropped**: no contrast needed

## 4. Security definitions, contracts and speculation semantics (incl. software side)

- `guarnieri2021contracts` · S&P 2021 · hardware-software contracts (observation and execution clauses) · vocabulary our specification language borrows · **cited elsewhere** (background, discussion); Related Work points back to Sec. bg-contracts
- `guarnieri2020spectector` · S&P 2020 · defines speculative non-interference; symbolic execution of software · the relational property we contrast with · **cited elsewhere** (background)
- `cheang2019formal` · CSF 2019 · secure speculation as an information-flow property (TPOD) · early formal definition · **cited**
- `yu2019oisa` (appended, ALL_NEW_ENTRIES.bib L132) · NDSS 2019 · data-oblivious ISA labeling operands safe or unsafe · origin of the unsafe-operand (transmitter) vocabulary · **cited**
- `reineke2026foundations` (appended, ALL_NEW_ENTRIES.bib L152) · LNCS 2026 · survey of hardware-software leakage contracts · survey anchor for contracts · **cited**
- `cauligi2022sok` · S&P 2022 · SoK of formal foundations for software Spectre defenses · survey anchor for the software side · **cited**
- `cauligi2020constanttime` · PLDI 2020 · speculative constant-time semantics (Pitchfork) · software-side semantics · **cited**
- `vassena2021blade` · POPL 2021 · type-based automatic elimination of speculative leaks · software-side · **cited**
- `patrignani2021exorcising` · CCS 2021 · secure-compilation view of speculative non-interference · software-side · **cited**
- `barthe2021highassurance` · S&P 2021 · speculative constant-time for verified crypto (Jasmin) · software-side · **cited**
- `daniel2021haunter` · NDSS 2021 · relational symbolic execution for Spectre-PHT and store bypass · software-side, includes store bypass · **cited**
- `fabian2022combinations` · CCS 2022 · detects combinations of speculation sources · software-side; multiple primitives · **cited**
- `fabian2025lift` (appended, ALL_NEW_ENTRIES.bib L110) · POPL 2025 · lifts compiler guarantees to stronger speculative semantics · guarantees depend on which speculation is modeled · **cited**
- `shivakumar2023typing` · S&P 2023 · type system for Spectre v1 in crypto code · software-side · **cited**
- `shivakumar2023declassified` · S&P 2023 · declassification interacts with speculation · software-side · **cited**
- `mosier2024serberus` · S&P 2024 · compile-time Spectre protection for crypto code · software-side, same group as LCM · **cited**
- `arranzolmos2025rsb` (appended, ALL_NEW_ENTRIES.bib L122) · ASPLOS 2025 · speculative constant-time protection for all known Spectre variants · software-side · **cited**
- `disselkoen2019code` · S&P 2019 · pomset-style semantics of speculative evaluation · full semantics vs our state snapshot · **cited**
- `ponce2022cats` · S&P 2022 · axiomatic (cat) model of speculation finding software gadgets · closest axiomatic analogue; models attacks, not defenses · **cited**
- `colvin2020abstractsemantics` (appended, ALL_NEW_ENTRIES.bib L263) · FM 2019 workshops, LNCS 2020 · abstract semantics of speculative execution · language-level abstraction · **cited**
- `guanciale2020inspectre` · CCS 2020 · operational out-of-order semantics; analyzes countermeasures · complete model, proved rather than tested · **cited**
- `yu2019sttformal` · tech report 2019 · STT's pen-and-paper non-interference proof over an abstract machine · the guarantee our STT model encodes · **cited**
- `lcms` · ISCA 2022 · leakage containment models: axiomatic contracts in µhb style · conceptual parent · **cited elsewhere** (background)
- `mcilroy2019spectre` · arXiv 2019 · formal model arguing software cannot fully mitigate Spectre · motivation for hardware defenses · **dropped**: motivation is the intro's job
- not in bib; ALL_NEW_ENTRIES.bib L141 (`guarnieri2020casco`) · arXiv 2020 · contract-aware secure compilation · software consumer of contracts · **dropped**: software, low relevance
- not in bib; ALL_NEW_ENTRIES.bib L166 (`fabian2026compositional`) · arXiv 2026 · compositional speculative semantics in Spectector · software · **dropped**: preprint, no venue
- not in bib; ALL_NEW_ENTRIES.bib L330 (`almeida2017jasmin`) · CCS 2017 · Jasmin verified crypto language and compiler · background only · **dropped**: not speculation
- not in bib; ALL_NEW_ENTRIES.bib L340 (`arranzolmos2025sctpreservation`) · POPL 2025 · compilation preserving speculative constant-time · software · **dropped**: covered by the software group
- not in bib; ALL_NEW_ENTRIES.bib L352 (`vanderwall2025snip`) · POPL 2025 · SNI preservation for compiler transformations · software · **dropped**: covered by the software group
- not in bib; ALL_NEW_ENTRIES.bib L364 (`arranzolmos2026sps`) · PACMPL 2026 (OOPSLA) · speculation-passing style for Spectre proofs · software · **dropped**: low relevance
- not in bib; ALL_NEW_ENTRIES.bib L288 (`wu2019abstractinterp`) · PLDI 2019 · abstract interpretation under speculative execution · software · **dropped**: low relevance
- not in bib; ALL_NEW_ENTRIES.bib L298 (`pescosta2021bmcsni`) · ICCAD 2021 · bounded model checking of SNI for programs · software program checking · **dropped**: low relevance
- not in bib; ALL_NEW_ENTRIES.bib L275 (`coughlin2024weakmemory`) · FM 2024 · speculation semantics combined with weak memory · low · **dropped**: LNCS volume unverified, low relevance
- not in bib; ALL_NEW_ENTRIES.bib L243 (`smith2025wpspeculative`) · arXiv 2025 · weakest-precondition detection of speculative data-flow leaks · software · **dropped**: rw3 recommends not citing
- not in bib; ALL_NEW_ENTRIES.bib L320 (`zhang2023ultimateslh`) · USENIX Security 2023 · variable-time arithmetic leaks speculatively; Ultimate SLH · supports non-memory transmitters · **dropped**: only if `other_x` transmitters are discussed

## 5. Axiomatic models, litmus tests and test generation

- `herdingcats` · TOPLAS 2014 · cat language for axiomatic memory models · modeling style we follow · **cited elsewhere** (background)
- `memalloy` · POPL 2017 · Alloy comparison of memory models via minimal distinguishing tests · Alloy precedent · **cited elsewhere** (background); Related Work points back
- `lustig` · ASPLOS 2017 · Alloy synthesis of minimal litmus-test suites · our minimality comes from it · **cited elsewhere** (background)
- `checkmate` · MICRO 2018 · µhb exploit patterns; Alloy synthesizes security litmus tests · direct precursor · **cited elsewhere** (background)
- not in bib; ALL_NEW_ENTRIES.bib L231 (`trippel2019checkmatemicro`) · IEEE Micro 2019 · Top Picks summary of CheckMate · duplicate of CheckMate · **dropped**: one CheckMate cite suffices
- `trippel2018meltdownprime` · arXiv 2018 · MeltdownPrime/SpectrePrime, synthesized by CheckMate · model-driven synthesis finds new attacks · **cited**
- `hossain2020transform` · ISCA 2020 · Alloy transistency models; synthesized enhanced litmus tests · methodological precedent · **cited**
- `alglave2010fences` · CAV 2010 · axiomatic framework with fences; diy cycle-based generator · tests from relaxation cycles · **cited**
- `alglave2011litmus` · TACAS 2011 · litmus tool running tests on hardware · analogue of our harness · **cited**
- `maradhaim2010generating` · CAV 2010 · generating litmus tests that contrast memory models · model-driven test generation · **cited**
- `maradhaim2011litmus` · DAC 2011 · how long distinguishing litmus tests must be · same · **cited**
- `perple` · 2020 (bib has no venue) · faster, more effective memory-consistency testing · running tests on hardware · **cited**
- `mcmutants` · ASPLOS 2023 · mutation testing of memory-consistency testing · grading test suites · **cited**
- `memsynth` · PLDI 2017 · synthesizes memory models from sketches and litmus tests · inverse direction (tests to model) · **cited**
- `norman2023pipesynth` · ASPLOS 2023 · synthesizes microarchitectural µhb axioms · automatic model synthesis · **cited**
- `hsiao2021rtl2uspec` · MICRO 2021 · synthesizes µspec models from RTL · implementation-to-model direction · **cited**
- `lustig2014pipecheck` · MICRO 2014 · µhb graphs for pipeline memory ordering · root of the Check tools · **cited**
- `manerkar2015ccicheck` · MICRO 2015 · µhb for the coherence-consistency interface · Check tools · **cited**
- `lustig2016coatcheck` · ASPLOS 2016 · µhb at the hardware-OS interface · Check tools · **cited**
- `trippel2017tricheck` · ASPLOS 2017 · full-stack (language, ISA, microarchitecture) litmus verification · Check tools · **cited**
- `manerkar2017rtlcheck` · MICRO 2017 · µhb axioms and litmus tests as RTL assertions · checking an implementation against an axiomatic model · **cited**
- `manerkar2018pipeproof` · MICRO 2018 · unbounded proofs for µhb microarchitectural models · proof vs bounded tests · **cited**
- `manerkar2020realitycheck` · arXiv 2020 · modular, hierarchical axiomatic memory-model verification · Check tools · **cited**
- `armstrong2021isla` · CAV 2021 · full ISA semantics with axiomatic concurrency for litmus tests · tool-level analogue of concretization · **cited**
- `armstrong2019sail` · POPL 2019 · Sail ISA semantics for ARMv8-A, RISC-V, CHERI · ISA substrate for Isla · **cited**
- `sarkar2011power` · PLDI 2011 · operational POWER model validated with litmus tests on hardware · model-vs-hardware testing · **cited**
- `flur2016modelling` · POPL 2016 · operational ARMv8 model tested against hardware · model-vs-hardware testing · **cited**
- `owens2009x86tso` · TPHOLs 2009 · x86-TSO memory model · axiomatic model of our ISA · **cited elsewhere** (background)
- `pulte2018simplifying` · POPL 2018 · axiomatic and operational ARMv8 models · canonical MCM work · **cited elsewhere** (background)
- `batty2011mathematizing` · POPL 2011 · axiomatic C++11 memory model · canonical MCM work · **cited elsewhere** (background)
- `lahav2017repairing` · PLDI 2017 · RC11 repair of the C11 model · canonical MCM work · **cited elsewhere** (background)
- `simner2020ifetch` · ESOP 2020 · relaxed instruction-fetch semantics for Armv8-A · beyond plain loads/stores · **cited elsewhere** (background)
- `simner2022vm` · ESOP 2022 · relaxed virtual-memory semantics for Armv8-A · same · **cited elsewhere** (background)
- `simner2025exceptions` · ISCA 2025 · precise exceptions in relaxed architectures · same · **cited elsewhere** (background)
- `alglave2018linux` · ASPLOS 2018 · Linux-kernel memory model in cat · MCM of a real specification · **dropped**: memory-model only, no contrast with SimSpect
- `lustig2015armor` · ISCA 2015 · ordering specifications for translating between memory models · not test generation · **dropped**: off topic
- not in bib; ALL_NEW_ENTRIES.bib L221 (`lustig2019ptx`) · ASPLOS 2019 · PTX memory model with Alloy bounded checking · marginal · **dropped**: marginal
- not in bib; ALL_NEW_ENTRIES.bib L212 (`chong2018transactions`) · PLDI 2018 · transactions plus weak memory; tests run on TSX · model-to-tests-to-implementation loop · **dropped**: marginal, for space
- `jackson2002alloy` · TOSEM 2002 · the Alloy language · tool we use · **cited elsewhere** (intro, background, pipeline)
- `kodkod` · TACAS 2007 · Kodkod relational model finder · solver under Alloy · **cited elsewhere** (background, pipeline)
- not in bib; ALL_NEW_ENTRIES.bib L177 (`torlak2007kodkod`) · TACAS 2007 · same paper as `kodkod` · duplicate · **dropped**: duplicate of `kodkod`
- not in bib; ALL_NEW_ENTRIES.bib L190 (`jackson2012softwareabstractions`) · MIT Press 2012 · standard Alloy book · alternative Alloy cite · **dropped**: one Alloy cite suffices
- not in bib; ALL_NEW_ENTRIES.bib L200 (`jackson2019alloycacm`) · CACM 2019 · Alloy overview · alternative Alloy cite · **dropped**: one Alloy cite suffices
- `sat4j` · JSAT 2010 · SAT4J solver · solver under Kodkod · **cited elsewhere** (pipeline)
- `fine2003cdg` (appended, ALL_NEW_ENTRIES.bib L524) · DAC 2003 · coverage-directed test generation for functional verification · directed vs random generation · **cited**
- `mishra2004graph` (appended, ALL_NEW_ENTRIES.bib L534) · DATE 2004 · test programs from a specification graph of the pipeline · classical model-driven test generation · **cited**

## 6. Spectre hardware defenses

- `yu2019stt`, `spt`, `recon`, `yan2018invisispec`, `saileshwar2019cleanupspec`, `cheng2024speclfb` · MICRO 2019, MICRO 2021, MICRO 2023, MICRO 2018, MICRO 2019, USENIX Security 2024 · the six defenses we test · the objects under test · **cited elsewhere** (intro class list, background, results); old bullet list and [Proposed] paragraph listed them again; dropped from Related Work as duplicates
- `nda`, `specshield`, `sakalis2019delay` (DoM), `doppelganger`, `protean`, `loughlin2021dolma`, `sdo` · MICRO 2019, PACT 2019, ISCA 2019, ISCA 2023, HPCA 2026, USENIX Security 2021, ISCA 2020 · delay/taint, relaxation and data-oblivious defenses · intro's class list · **cited elsewhere** (intro); `protean` and `loughlin2021dolma` also cited in Related Work for their findings (sec. 7)
- `khasawneh2019safespec`, `ainsworth2020muontrap`, `ainsworth2021ghostminion` · DAC 2019, ISCA 2020, MICRO 2021 · invisible-speculation defenses · intro's class list · **cited elsewhere** (intro)
- `hu2021sok` · SEED 2021 · SoK of hardware defenses against speculative execution · survey anchor · **cited**
- `taram2019csf` · ASPLOS 2019 · context-sensitive fencing via microcode customization · extra defense · **cited**
- `li2019conditional` · HPCA 2019 · conditional speculation: blocks security-dependent speculative loads · extra defense · **cited**
- `schwarz2020context` · NDSS 2020 · ConTExT: memory marked secret never used speculatively · extra defense · **cited**
- `fustos2019spectreguard` · DAC 2019 · SpectreGuard: software-marked secret regions · extra defense · **cited**
- `koruyeh2020speccfi` (appended, ALL_NEW_ENTRIES.bib L375) · S&P 2020 · CFI-informed speculation · extra defense (control-flow predictors) · **cited**
- `kiriansky2018dawg` · MICRO 2018 · DAWG: way-partitioned caches · extra defense · **cited**
- `tran2020clearing` · PACT 2020 · HW/SW co-design recovering invisible-speculation performance · relaxation · **cited**
- `zhao2020invarspec` · MICRO 2020 · program analysis finds speculation-invariant instructions · relaxation · **cited**
- `zhao2022pinned` · ASPLOS 2022 · Pinned Loads: makes loads non-speculative sooner · relaxation · **cited**
- `jin2023specterminator` · TACO 2023 · blocks speculative channels by instruction class on RISC-V · extra defense · **cited** (in "many others")
- `daniel2023prospect` · USENIX Security 2023 · provably secure speculation for the constant-time policy · extra defense · **cited** (many others)
- `ganjisaffar2025specasan` · ISCA 2025 · speculative address sanitization · extra defense · **cited** (many others)
- `hajiabadi2024levioso` · DAC 2024 · compiler-informed secure speculation · extra defense · **cited** (many others)
- `hajiabadi2025cassandra` · ISCA 2025 · enforces sequential execution for crypto programs · extra defense · **cited** (many others)
- `aimoniotis2024janus` · SBAC-PAD 2024 · RL-guided speculative defense · extra defense · **cited** (many others)
- `chen2025mustt` · ICCD 2025 · microarchitecture design for STT · extra defense · **cited** (many others)
- `cui2023ssft` · JCST 2023 · speculative secret-flow tracking · extra defense · **cited** (many others)
- `kvalsvik2025shadowbinding` · MICRO 2025 · realizable in-core microarchitectures for secure speculation · extra defense · **cited** (many others)
- `green2023safebet` · arXiv 2023 · SafeBet: secure, simple, fast speculation · extra defense · **cited** (many others)
- `kim2024perspective` · ISCA 2024 · OS framework for secure speculation · extra defense · **cited** (many others)
- `castes2024sharing` · ASPLOS 2024 · core-gapped confidential VMs block transient attacks · system-level defense · **cited** (many others)
- `trujillo2026register` · S&P 2026 · register hiding limits secret reachability · extra defense · **cited** (many others)
- `wu2025rcp` · IEEE TDSC 2025 · low-overhead reversible coherence protocol · undo-style defense · **cited** (many others)
- `sakalis2023delayonsquash` (appended, ALL_NEW_ENTRIES.bib L408) · TACO 2023 · Delay-on-Squash against replay attacks · extra defense · **cited** (many others)
- `choudhary2023declassiflow` · CCS 2023 · static analysis relaxing speculative defenses · software side of the defense space · **cited** (many others)
- not in bib; ALL_NEW_ENTRIES.bib L420 (`skarlatos2019microscope`) · ISCA 2019 · microarchitectural replay attacks · attack enabler, not a defense break · **dropped**: off topic

## 7. Design-level breaks of defenses and bugs in defense implementations

- `behnia2021interference` · ASPLOS 2021 · speculative interference breaks invisible speculation · design flaw vs our implementation bugs · **cited**
- `li2022unxpec` · HPCA 2022 · rollback timing breaks undo-based CleanupSpec · design flaw; A-KV2 · **cited**; also results, discussion
- `aimoniotis2022doin` · SEED 2022 · inclusive caches attack speculative delay schemes · design flaw · **cited** (restored from the 2026-11-03 cut list)
- `chakraborty2022timed` · DAC 2022 · store-to-load forwarding bypasses cache-based countermeasures · design flaw; STLF relevance · **cited**
- `loughlin2021dolma` · USENIX Security 2021 · DOLMA: store and memory-ordering channels in STT · design flaw; A-KV3 · **cited**; also intro, results, discussion
- `fustos2020spectrerewind` (appended, ALL_NEW_ENTRIES.bib L386) · ASHES 2020 · leaks secrets to past instructions via contention · channel outside cache-centric defenses · **cited**
- `xiao2023hackyracers` (appended, ALL_NEW_ENTRIES.bib L397) · ASPLOS 2023 · ILP-based timers that break many countermeasures · new timing channel · **cited**
- `cheng2026contention` · USENIX Security 2026 · CMOV/REP reservation-station contention bypasses STT and DOLMA in gem5 · novelty risk; design-level, not our UV1 · **cited** (one clause)
- not in bib; ALL_NEW_ENTRIES.bib L599 (`aimoniotis2021robcontention`) · IEEE CAL 2021 · ROB contention as a speculative interference attack · design flaw · **dropped**: year marked TODO in rw8, unverified
- `protean` · HPCA 2026 · programmable Spectre defense; its extended AMuLeT found the STT/SPT pending-squash bug, manual inspection an SPT untaint bug (p11 §VII-B4) · prior implementation bugs in our builds · **cited**; also intro, background
- `nickscommittoSTT` · GitHub 2025 · STT commit 18e304f fixing the pending-squash bug · prior fix · **cited**; also intro, discussion
- `mosier2025sptpr6` · GitHub 2025 · SPT PR #6: taint all registers at rename (pending-fault untaint fix) · prior fix · **cited**
- not in bib; ALL_NEW_ENTRIES.bib L544 (`mosier2025sttpr10`) · GitHub 2025 · STT PR #10, pending-squash fix · same fix as `nickscommittoSTT` · **dropped**: duplicate
- not in bib; ALL_NEW_ENTRIES.bib L553 (`mosier2025sptpr4`) · GitHub 2025 · SPT PR #4, pending-squash fix · covered by `protean` · **dropped**: for space
- not in bib; ALL_NEW_ENTRIES.bib L562 (`mosier2025sptpr5`) · GitHub 2025 · SPT PR #5, untaint upper 32 bits (precision change) · same code as SPT partial-write candidates · **dropped**: not a security fix; see DECIDE (SPT build) in sec. 10
- `kvalsvik2025reconnaissance` · IEEE DataPort 2025 · ReCon leaks when an instruction has multiple secret sources · novelty risk for UV3 · **cited** (one neutral clause)

## 8. Transient-execution attacks and store-bypass literature

The 31 `rw6_attacks.bib` entries are not in `ALL_NEW_ENTRIES.bib`, so this rewrite could not append them; they are attack background rather than related work. If any is wanted (e.g. for the Background's speculation primitives), copy it from `rw6_attacks.bib` after checking it (rw6 notes caveats on `lipp2018meltdown` authors and `liu2026pitfall` venue).

- `spectre` · S&P 2019 · Spectre attacks · the attack class · **cited elsewhere** (intro, discussion)
- `horn2018ssb` · Project Zero 2018 · Spectre v4, speculative store bypass · our store-bypass primitive · **cited elsewhere** (background, pipeline, discussion)
- `canella2019systematic` · USENIX Security 2019 · systematic evaluation of transient attacks and defenses · gadget benchmarks · **cited elsewhere** (intro)
- `kocher2018msvc` · blog 2018 · 15 Spectre v1 example functions · gadget benchmarks · **cited elsewhere** (intro)
- `primeandprobe` · CT-RSA 2006 · Prime+Probe cache attacks on AES · side-channel background · **dropped**: not related work
- not in bib; rw6_attacks.bib L2 (`lipp2018meltdown`) · USENIX Security 2018 · Meltdown · Meltdown-type counterpart · **dropped**: attack background; not in ALL_NEW_ENTRIES
- not in bib; rw6_attacks.bib L7 (`vanbulck2018foreshadow`) · USENIX Security 2018 · Foreshadow (L1TF) · Meltdown-type · **dropped**: same
- not in bib; rw6_attacks.bib L12 (`vanschaik2019ridl`) · S&P 2019 · RIDL, line-fill-buffer data sampling · SpecLFB motivation · **dropped**: same
- not in bib; rw6_attacks.bib L17 (`schwarz2019zombieload`) · CCS 2019 · ZombieLoad data sampling · MDS · **dropped**: same
- not in bib; rw6_attacks.bib L22 (`canella2019fallout`) · CCS 2019 · Fallout, store-buffer leakage · near our store-bypass work · **dropped**: same
- not in bib; rw6_attacks.bib L27 (`maisuradze2018ret2spec`) · CCS 2018 · ret2spec, return-stack-buffer Spectre · control-flow predictors · **dropped**: same
- not in bib; rw6_attacks.bib L32 (`koruyeh2018spectrersb`) · WOOT 2018 · SpectreRSB · control-flow predictors · **dropped**: same
- not in bib; rw6_attacks.bib L37 (`barberis2022bhi`) · USENIX Security 2022 · Branch History Injection · mitigation bypass · **dropped**: same
- not in bib; rw6_attacks.bib L42 (`vanbulck2020lvi`) · S&P 2020 · Load Value Injection · value injection · **dropped**: same
- not in bib; rw6_attacks.bib L47 (`wikner2022retbleed`) · USENIX Security 2022 · RETBLEED · mitigation bypass · **dropped**: same
- not in bib; rw6_attacks.bib L52 (`trujillo2023inception`) · USENIX Security 2023 · Inception, training in transient execution · predictor attack · **dropped**: same
- not in bib; rw6_attacks.bib L57 (`wikner2023phantom`) · MICRO 2023 · Phantom, decoder-detectable mispredictions · predictor attack · **dropped**: same
- not in bib; rw6_attacks.bib L62 (`moghimi2023downfall`) · USENIX Security 2023 · Downfall, gather data sampling · MDS-type · **dropped**: same
- not in bib; rw6_attacks.bib L67 (`ormandy2023zenbleed`) · blog 2023 · Zenbleed, mis-rolled-back vzeroupper · squash/rollback bug analogy · **dropped**: same
- not in bib; rw6_attacks.bib L72 (`ragab2024ghostrace`) · USENIX Security 2024 · speculative race conditions · Spectre v1 generalization · **dropped**: same
- not in bib; rw6_attacks.bib L77 (`li2024indirector`) · USENIX Security 2024 · indirect branch predictor injection · predictor attack · **dropped**: same
- not in bib; rw6_attacks.bib L82 (`kim2025slap`) · S&P 2025 · load address prediction attacks (Apple) · data speculation · **dropped**: same
- not in bib; rw6_attacks.bib L87 (`kim2025flop`) · USENIX Security 2025 · load value prediction attacks (Apple M3) · data speculation · **dropped**: same
- not in bib; rw6_attacks.bib L92 (`kim2025tiktag`) · S&P 2025 · speculative MTE tag leak · Spectre gadget · **dropped**: same
- not in bib; rw6_attacks.bib L97 (`xiong2021survey`) · ACM CSUR 2021 · survey of transient attacks and mitigations · taxonomy · **dropped**: same
- not in bib; rw6_attacks.bib L101 (`fiolhais2023transient`) · ACM CSUR 2023 · architect's view of transient attacks · taxonomy · **dropped**: same
- not in bib; rw6_attacks.bib L105 (`sanchezvicarte2021pandora`) · ISCA 2021 · systematic study of optimization-based leaks · transmitter taxonomy · **dropped**: same (a Background candidate)
- not in bib; rw6_attacks.bib L110 (`moshovos1997dynamic`) · ISCA 1997 · memory dependence prediction · origin of store-bypass speculation · **dropped**: same
- not in bib; rw6_attacks.bib L115 (`chrysos1998storesets`) · ISCA 1998 · store-set dependence prediction (used by gem5 O3) · store-bypass speculation · **dropped**: same
- not in bib; rw6_attacks.bib L120 (`islam2019spoiler`) · USENIX Security 2019 · leak via load-store dependency resolution · not Spectre · **dropped**: same
- not in bib; rw6_attacks.bib L125 (`amd2021psf`) · AMD white paper 2021 · predictive store forwarding risk · vendor store predictor · **dropped**: same
- not in bib; rw6_attacks.bib L130 (`liu2024amdpredictors`) · HPCA 2024 · reverse-engineers AMD memory-access predictors · store-bypass family · **dropped**: same
- not in bib; rw6_attacks.bib L135 (`liu2025mdpeek`) · ASPLOS 2025 · memory-disambiguation side channel in SGX · store-bypass family · **dropped**: same
- not in bib; rw6_attacks.bib L140 (`liu2026ssbleed`) · HPCA 2026 · store-bypass attacks on Armv9 · store-bypass family · **dropped**: same
- not in bib; rw6_attacks.bib L145 (`liu2026ssbench`) · ISCA 2026 · automated characterization of dependence predictors · automation, but of predictors not defenses · **dropped**: same
- not in bib; rw6_attacks.bib L150 (`liu2026pitfall`) · LNCS 2026 (venue TODO) · Intel store-forwarding predictor attack · store-bypass family · **dropped**: same; venue unverified
- no entry (Witharana & Mishra, "Speculative Load Forwarding Attack", ICCAD 2022) · ICCAD 2022 · load-forwarding attack · store-bypass family · **dropped**: no bib entry

## 9. Simulator methodology, tools and benchmarks

- `gem5` · SIGARCH CAN 2011 · the gem5 simulator · simulator substrate · **cited elsewhere** (intro)
- `spec2017` · ICPE 2018 · SPEC CPU2017 · functional-correctness benchmarks · **cited elsewhere** (intro)
- `sttrepo` · GitHub 2020 · STT gem5 code at commit e3283b9 · code we cite · **cited elsewhere** (results)
- not in bib; ALL_NEW_ENTRIES.bib L473 (`lowepower2020gem5`) · arXiv 2020 · gem5 20.0+ overview · second gem5 cite · **dropped**: the defense builds use older gem5 bases
- not in bib; ALL_NEW_ENTRIES.bib L483 (`nowatzki2015harmful`) · IEEE Micro 2015 · critique of black-box simulator use · simulator fidelity · **dropped**: fidelity is not our claim (a Discussion candidate)
- not in bib; ALL_NEW_ENTRIES.bib L495 (`gutierrez2014sources`) · ISPASS 2014 · gem5 error against an ARM board · simulator fidelity · **dropped**: same
- not in bib; ALL_NEW_ENTRIES.bib L515 (`gonzalez2019boomspectre`) · CARRV 2019 · Spectre replicated on BOOM · BOOM background · **dropped**: the paper does not discuss BOOM

## 10. Non-paper bullets, notes and decisions from the old section

AMuLeT statements removed as redundant, and where each already lives:

- "AMuLeT, the closest prior work" · lives in intro.tex:17 · removed from Related Work.
- AMuLeT checks a hardware-software contract: two runs with matching contract traces must leave the same final L1D and D-TLB state (§3.2) · contract definition in background.tex:17; pairs of inputs in intro.tex:17 and the pipeline.tex:264 [Proposed] paragraph · removed.
- AMuLeT tests each defense against a high-level contract (CT-SEQ or ARCH-SEQ), much coarser than and different from the security guarantee (what a whole program may expose on its sequential path, not which instructions the defense must hold back or which state it protects) · full version in results.tex:38 (Known Bugs Replicated), short version in intro.tex:17, CT-SEQ's meaning in background.tex:19 · removed; Related Work points to Sec. known-bugs.
- AMuLeT's programs are random, up to five basic blocks (§3.1), not biased toward leaking programs; its authors say leaking programs "can be fundamentally hard to find with random testing" (§3.4) · randomness in intro.tex:17; the targeting gap (17% of AMuLeT tests) in results.tex:79 and :81 · removed, quote dropped.
- Anna's text: "Security testing is sensitive to this, because one leaky edge case that random generation rarely produces can be a potent attack vector, so a test suite needs a wide breadth of leaky instances" · kept verbatim in the commented intro.tex:24 · removed from Related Work for length.
- AMuLeT reports three known and six unknown bugs "within three hours of testing"; four of the nine fall outside the defenses' security guarantees · results.tex:31, :35, :38 · removed ("within three hours" not carried anywhere).
- AMuLeT leaves speculation to the simulated predictors, whose state it carries across test cases (§3.2, verified 2026-11-11 in fu-2025-amulet.pdf) · not elsewhere · removed for length; the contrast survives as "forces each modeled misprediction" with `ayoub2021gem5spectre`.
- "Implementation bugs ... surfaced through AMuLeT (Sec. VI-A)" and "Protean's extended AMuLeT" · AMuLeT's bug count is in Results · now "Protean's extended fuzzer", so AMuLeT is named only in the testing paragraph.
- Kept in Related Work (not stated live elsewhere): contract violations compare two whole runs, so they name neither the leaking instruction nor the broken rule and are root-caused by hand (AMuLeT §3.3, verified 2026-11-11 in fu-2025-amulet.pdf).

The original AMuLeT bullet list (live in every revision from `1c5c53d` to `ae391d0`):

- "the only prior automated validator of Spectre-defense simulator prototypes; randomized differential testing ... flagging a contract violation when speculative execution leaks more than architectural execution" · "only" dropped (SpecCheck and Pensieve also target this stage); description now intro.tex:17.
- "generation is random, so it is agnostic to whether a test even contains the ingredients for Spectre leakage, wasting runs and requiring manual root-causing" · root-causing kept in Related Work; randomness intro.tex:17; wasted runs results.tex:79/81.
- "it is not specialized to common defense techniques or the bug classes implementing them invites" · dropped; covered by "checks one run against the defense's security guarantee".
- "it does not exploit the white-box simulator to bias scheduling toward likely-buggy windows" · now the "forces each modeled misprediction" contrast; white-box claim is in the intro.
- "it conflates verifying that a defense prevents speculative leakage with discovering new unsafe instruction operands" · dropped; ConjunCT and H-Houdini are cited for transmitter discovery.
- "it tests against a sequential model, so it cannot test defenses that protect data speculatively even after it has leaked architecturally (Protean)" · dropped for length.

Other old bullets:

- "Hardware-software contracts and speculative non-interference: the security properties SimSpect's contracts target" · now Background II-B; Related Work points back.
- "Axiomatic, happens-before microarchitectural execution models (herdingcats, lustig): the modeling style SimSpect adapts" · Background II-C.
- "Memory-consistency litmus-test methodology (herdingcats) that SimSpect's enumeration of minimal execution graphs builds on" · Background II-C; the rest of the lineage is in the litmus paragraph.
- "The hardware defenses SimSpect expresses and tests: STT, SpecShield, NDA, DoM, SDO, SPT, and related schemes (doppelganger, sdo, protean)" with the "SPO was a typo for SDO" TODO · out of date; the six tested defenses are in the intro and background; whether SpecShield, NDA, DoM and SDO count as "expressed" is the intro's open "ten defenses" claim.

Notes moved into the old section from other sections (all now resolved by the rewrite; full text in git at `ae391d0:sections/related.tex` lines 12-15, 85-86, 217):

- From background (old II-B), prior validation: "Prior work that validates advertised security guarantees against hardware support for hardware SCDs analyzes fabricated designs (revizor) or RTL (rtl2upath), due to the wide availability" · Revizor in the testing paragraph, RTL tools in the testing and formal paragraphs, one sentence in intro.tex:17.
- From background (old II-B), AMuLeT: "Only AMuLeT analyzes simulator implementations ... attempts to validate high-level security properties, and has no ability to do directed testing" · testing paragraph and intro.tex:17; "Only AMuLeT" dropped.
- From intro (2026-11-11 notes "pick that up in related work"): relational-property passage, fuzzing-vs-targeting passage, bug count, high-level-contract passage · see the AMuLeT list above. Not carried: "Such contracts generalize SNI ..." (unchecked against Guarnieri et al. 2021); "There exists no existing work that can generate targeted test sets ..." (carried by the intro's proposal sentence).
- From background (II-B contracts paragraph): "Revizor and AMuLeT test CPUs and simulators against such contracts" · testing paragraph; naming stays in Background II-B.
- From background (II-B stub): "cite Spectector for SNI, LCM, and the RISC-V follow-ups (mohr2024synthesizing, synthlc, leave)" · Spectector and LCM in Background; the follow-ups in the formal paragraph.
- From background (II-C), speculation formalization: "cite checkmate, all of the speculation formalization, LCM" · formal paragraph (Cheang, contracts pointer, Cats vs. Spectre, The Code That Never Ran, InSpectre, STT formal analysis); CheckMate and LCM stay in Background II-C.
- From background (II-C), MCM lineage: "cite a bunch of other stuff, arm + simner stuff" · placed as in sec. 5; `sarkar2011power` is now cited (it was "not placed"); `lustig2015armor` dropped; `mcmutants` cited.
- Audit note "Structure (updated 2026-11-11)" · resolved: Related Work is prose, AMuLeT described briefly once here.

Decisions still open (the DECIDE notes deleted from related.tex; each needs Anna):

- DECIDE (novelty risk, UV3 vs Kvalsvik and Själander's ReConnaissance dataset): options (a) keep UV3 new and cite them (what the new text does, neutrally, without linking to UV3); (b) relabel UV3 as known; (c) leave uncited. Earlier recommendation: (a) now, try to obtain their paper; switch to (b) if it describes the same oldest-source mechanism. Source: IEEE DataPort 10.21227/dkjt-k008.
- DECIDE (our SPT build `0d2be0f` predates Mosier's SPT PRs #4-#6): (a) rebuild with the fixes and rerun SPT rows; (b) keep the build and show each SPT hit is not one of the two known bugs; (c) drop SPT results. Earlier recommendation: (b) for this deadline, (a) next. Source: github.com/FPSG-UIUC/SPT commits; Protean p11 §VII-B4.
- DECIDE (Cheng et al. USENIX Security 2026): (a) cite as a design-level break (done); (b) also list it in Discussion as a channel outside our leakage contract. Earlier recommendation: (a), plus (b) in one clause if space allows.
- DECIDE (CheckMate contrast): the litmus paragraph keeps "what it tests is the defense's gem5 implementation, not the model" (option a). Options (b) contrast on content ("CheckMate's patterns describe attacks; SimSpect's model describes what a defense forbids"), (c) both. Earlier recommendation: (c).
- Guideline tension: PAPER_AUDIT_GUIDELINES §2 says to state the AMuLeT high-level-contract contrast once each in intro, Related Work and Results; Anna's 2026-11-11 ask was to stop repeating AMuLeT, so Related Work now points to Results instead. Confirm, or move results.tex:38 here.
- The `synthlc` key is LeaSyn (Wang et al., CCS 2025), not SynthLC; renaming it is Anna's call.
- VOCAB notes in the old section ("contract violation" for AMuLeT's detections; "Hardware-software contracts" as Guarnieri's name) · both applied; the new text says "contract violations" and "contracts".

## 11. 2026-11-15 sweep of Anna's other sources (Zotero, quail reading library, reference_papers, old drafts, theses, JS fellowship bib)

Everything relevant that this sweep found missing from `references.bib` is already in §§1–10 above with a drop reason, except the items below, which were never considered. Status: none added; Anna to decide.

- `counterpoint_asplos26` (Lindsay et al., Trippel co-author, ASPLOS 2026; PDF in `paper_figures/reference_papers/counterpoint_asplos26/`) · refutes and refines user-written microarchitectural models with hardware event counters · same model-vs-implementation idea as SimSpect · candidate for Related Work (formal / microarchitectural models).
- `helium_isca26` (Archer et al., Trippel co-author, ISCA 2026; PDF in `paper_figures/reference_papers/helium_isca26/`) · quantifies side-channel leakage with probabilistic guarantees, simulation-based · used so far only as the §IX format model, never cited · candidate for Related Work.
- μSpectre (Mosier et al., Trippel co-author; venue unverified; `~/Documents/quail/sources/papers/mosier-2024-uspectre.*`) · microcode branch mispredictions as a speculation source · relevant to speculation-contract scope · candidate for Background or Related Work.
- From `~/trippel/JS-fellowship-app/references.bib` (never considered): Simner et al., "Abstract Architecture Catches Concrete Bugs"; Alglave et al., "Armed Cats" (2021); ArchSem · formal architecture models that catch real implementation bugs · candidates for the memory-model-tooling paragraph.
- Do NOT cite: `isca2025-35-taint-primitive-tracking` and `micro2024-811-taint-primitive-elimination` in the quail library are confidential unpublished submissions (`confidential: true` in their md front matter).
- Zotero (`~/Zotero/zotero.sqlite`) holds 59 unrelated items, so there is nothing to mine there. The thesis bibs (website fingerprinting) and `~/fitd-simulator` (memory tiering) are unrelated.

## 12. 2026-11-15 wording audit of Related Work against Caroline Trippel's papers

Adversarial read of every sentence in `ISCA-27/sections/related.tex` (live text as of 2026-11-15; lines 5–15) against how Caroline Trippel's own papers phrase the same things, weighted toward imprecision (loose terms, unclear referents, untrue quantifiers, blurred model / implementation / RTL / simulator distinctions, conflated concepts). The paper was not edited. Page numbers are PDF pages as extracted with pdftotext (checked against `-layout` where hyphenation broke a quote). Reference vocabulary: `tikz/intro_threelayer_v9.tex` (Fig. 1) and the live intro. Agrees with and folds in the one banked related.tex note (`NOTES_BACKUP_2026-11-15.md`, "sections/related.tex" item 1: AMuLeT "against security contracts", SimSpect "against the defense's specification"); see T2 and T4.

**How the paper list was built.** DBLP is behind a bot check (blocked for curl and WebFetch) and Google Scholar needs a login, so the 2020–2026 list comes from the Crossref API (author query "Caroline Trippel", filtered to her CS works), her Stanford profile (profiles.stanford.edu/caroline-trippel, publications tab), her researchr profile, and local copies. The arXiv API was rate-limited, so an arXiv-only preprint could be missing.

**Read (intro/abstract, background and related work at minimum):**

- Protean (Mosier, Nemati, Mitchell, Trippel; HPCA 2026): `paper_figures/reference_papers/protean_hpca26/protean_hpca26.pdf` (also §VII-B security evaluation).
- CounterPoint (Lindsay, Trippel, Khandelwal, Bhattacharjee; ASPLOS 2026): `paper_figures/reference_papers/counterpoint_asplos26/counterpoint_asplos26.pdf`.
- Helium (Archer, Fadiheh, Trippel; ISCA 2026, DOI 10.1109/ISCA66397.2026.00045): `paper_figures/reference_papers/helium_isca26/helium_isca26.pdf`.
- RTL2MµPATH / SynthLC (Hsiao et al.; MICRO 2024): `paper_figures/reference_papers/rtl2mupath_synthlc_micro24/rtl2mupath_synthlc_micro24.pdf`.
- Serberus (Mosier, Nemati, Mitchell, Trippel; S&P 2024): `paper_figures/reference_papers/serberus_sp24/serberus_sp24.pdf`.
- µSpectre (Mosier, Nemati, Mitchell, Trippel; venue unverified, not in Crossref): `~/Documents/quail/sources/papers/mosier-2024-uspectre.pdf` (abstract and background only, for terminology).
- LCM / Clou, "Axiomatic Hardware-Software Contracts for Security" (Mosier, Lachnitt, Nemati, Trippel; ISCA 2022): `paper_figures/reference_papers/lcm_clou_isca22/lcm_clou_isca22.pdf`.
- rtl2µspec (Hsiao, Mulligan, Nikoleris, Petri, Trippel; MICRO 2021): `paper_figures/reference_papers/rtl2uspec_micro21/rtl2uspec_micro21.pdf`.
- Pandora (Sanchez Vicarte et al.; ISCA 2021): `~/trippel/trippel-lab/website/pubs/pandora-isca-21.pdf` (abstract and terminology only; it is not cited in related.tex).
- TransForm (Hossain, Trippel, Martonosi; ISCA 2020): `paper_figures/reference_papers/transform_isca20/transform_isca20.pdf`.
- Older, read because related.tex characterizes them: CheckMate (MICRO 2018), `paper_figures/reference_papers/checkmate_micro18/checkmate_micro18.pdf`; TriCheck (ASPLOS 2017) for terminology counts only.
- Trippel's own talk material: FAVA tutorial slides (Hsiao, Archer, Trippel; ISCA 2026 tutorial), https://fava.stanford.edu/01-introduction.pdf (PDF author field: Caroline Trippel); POPL 2026 keynote abstract, https://popl26.sigplan.org/details/POPL-2026-popl-research-papers/2/ (summary only).
- Non-Trippel sources checked where related.tex characterizes them: AMuLeT (`~/Documents/quail/sources/papers/fu-2025-amulet.pdf`), Pensieve (`yang-2023-pensieve.pdf`), SpecCheck (`mckevitt-2023-speccheck.pdf`), Cheng et al. USENIX Security 2026 (`paper_figures/reference_papers/cheng/cheng.pdf`), STT commit 18e304f message (github.com/cwfletcher/stt/commit/18e304f), and the ISCA-27 bib titles of LEAVE, PipeSynth, MemSynth, Geier et al.

**Could not obtain:** Trippel, "Specification and Formal Verification of Hardware–Software Contracts for High-Assurance Computer Architectures," IEEE Computer 58(8):86–91, 2025, DOI 10.1109/MC.2025.3573841 (paywalled at IEEE Xplore; no open copy found; the download was refused by the session's permission check). This is the paper most likely to contain her current contract vocabulary, so it is worth Anna getting it through the Stanford library. **Excluded as off-topic** (Trippel co-author, 2020–2026, nothing on speculation, contracts, litmus tests or verification): Porcupine (PLDI 2021), RecSSD (ASPLOS 2021), RecShard (ASPLOS 2022), BMVC 2021 feature descriptors, G-QED (DAC 2023), nl2spec (CAV 2023), latency-critical model selection (EuroSys 2024), IEDM 2024 memory, long/short-term RAM (2025 workshop), ICSE 2026 requirements formalization, SoK software-hardware-security codesign (HASP 2020).

**Findings: 23 total.** 6 factual mischaracterizations (F1–F6), 16 term mismatches or imprecisions (T1–T13 plus the three DECIDE items D1–D3), 1 clarity item (C1).

### F1. The pending-squash bug is not a race (and the word collides with our own race bug)

- Location: `related.tex:15`, "Implementation bugs in the gem5 prototypes include a pending-squash race in STT and SPT, found by Protean's extended fuzzer".
- Problem: Neither Protean nor the fix calls this a race. It is a same-cycle notification bug: the execute stage reports only the youngest mispredicted branch per cycle, so an older tainted branch can block a younger untainted branch's squash, making the squash signal secret-dependent. The fix commit is titled "fix pending squash bug" and never says "race" (github.com/cwfletcher/stt/commit/18e304f). Calling it a race invites a reviewer to read it as our new bug (6), which the intro calls "a visibility-point/squash timing race" in the same two defenses (STT and SPT); that undercuts the novelty claim. "the gem5 prototypes" also has no clear referent. The intro has the same problem ("a recent squash race in STT~\cite{protean}", intro.tex), outside this audit's scope but worth the same change.
- Caroline's wording: "a previously unknown corner-case bug in PROTEAN's implementation of delayed branch resolution, which it borrows directly from STT/SPT/SPT-SB" and "This creates a secret-dependent squash signal that leaks the tainted/protected branch predicate" (Protean, p11, §VII-B4b).
- Proposed replacement (same length):

```latex
Bugs in STT's and SPT's gem5 implementations include the pending-squash bug, a secret-dependent squash signal found by Protean's extended fuzzer, and an SPT untaint bug found by manual inspection, both since fixed~\cite{protean,nickscommittoSTT,mosier2025sptpr6}.
```

### F2. "The Check tools verify microarchitectures against µhb models" inverts what they do

- Location: `related.tex:12`, "The Check tools verify microarchitectures against $\mu$hb models, from pipelines to RTL".
- Problem: In the Check tools the axiomatic (µspec) model *is* the microarchitecture under verification; it is checked against a memory consistency model, for suites of litmus tests, using µhb analysis. The sentence makes the µhb model the specification. "µhb models" is also not a term her papers use (they say µhb graphs, µhb analysis, µspec models).
- Caroline's wording: "the Check tools, which formally check that a specific microarchitecture correctly implements an MCM with respect to a suite of litmus test programs ... must be supplied a microarchitecture in the guise of a manually constructed axiomatic specification, called a µspec model" (rtl2µspec, p1, abstract); "The Check tools automate formal memory consistency model and security verification of processors by analyzing abstract models of microarchitectures, called µSPEC models" and "conduct microarchitectural happens-before (µHB) analysis" (RTL2MµPATH, p1).
- Proposed replacement (longer; corrects a factual error):

```latex
The Check tools use $\mu$hb analysis to verify that microarchitectures, given as axiomatic models, implement memory models, from pipelines to RTL~\cite{lustig2014pipecheck,manerkar2015ccicheck,lustig2016coatcheck,trippel2017tricheck,manerkar2017rtlcheck,manerkar2018pipeproof,manerkar2020realitycheck};
```

### F3. "Many were later broken at the design level" contradicts our own Results on scope

- Location: `related.tex:15`, "Many were later broken at the design level: speculative interference breaks invisible speculation~\cite{behnia2021interference}, rollback timing breaks CleanupSpec~\cite{li2022unxpec}, ... DOLMA identifies store and memory-ordering channels in STT~\cite{loughlin2021dolma}, ... and reservation-station contention bypasses STT in gem5".
- Problem: "Broken" asserts an in-scope failure. Results says the opposite for three of these: unXpec's timing difference "is a stated limit of the design rather than a departure from it", STT "assumes that stores are performed only at retirement" so store channels "are therefore out of scope", and InvisiSpec places MSHR/execution-unit contention "out of scope" (results.tex:35). A reviewer who reads both sections sees a contradiction. Caroline's framing for this class is "noncomprehensive": defenses that leak through channels or speculation types they never claimed. Also "bypasses STT in gem5" blurs design and implementation: Cheng et al. describe a design-level assumption ("several state-of-the-art selective-speculation defenses rest on shared assumptions that overlook important microarchitectural behaviors", cheng.pdf p1, abstract), demonstrated in gem5.
- Caroline's wording: "Many Spectre defenses are noncomprehensive, assuming a restricted set of channels or speculation types and thus still allowing secrets to transiently leak" (Protean, p14, §X-1).
- Proposed replacement (same length; keeps every attack and citation, drops the in-scope verbs):

```latex
Later work found design-level leaks in many, some through channels their papers exclude: speculative interference in invisible speculation~\cite{behnia2021interference}, rollback timing in CleanupSpec~\cite{li2022unxpec}, inclusive caches and store-to-load forwarding in delay and cache-based schemes~\cite{aimoniotis2022doin,chakraborty2022timed}, store and memory-ordering channels in STT (DOLMA)~\cite{loughlin2021dolma}, new timing channels that sidestep many defenses~\cite{fustos2020spectrerewind,xiao2023hackyracers}, and reservation-station contention that STT's design overlooks~\cite{cheng2026contention}.
```

### F4. LEAVE is filed under "secure speculation", and "contracts" is bare

- Location: `related.tex:9`, "checks secure speculation in RTL~\cite{...,leave,...} ..., synthesizes contracts and leakage signatures from RTL~\cite{mohr2024synthesizing,synthlc,rtl2upath}, and proves which instructions are safe~\cite{dinesh2024conjunct,dinesh2025hhoudini}".
- Problem: Caroline classifies LEAVE with ConjunCT as verifying hardware against constant-time (CT) leakage contracts, i.e., which instructions and operands are safe, not as secure-speculation verification (LEAVE's own title: "... via Leakage Contracts"). "contracts" alone is ambiguous here, because two sentences earlier "contracts" meant hardware–software security contracts, and the paper uses "leakage contract" in SynthLC's sense. H-Houdini's placement follows the inventory's description (§3), not a reading of the paper.
- Caroline's wording: "LEAVE [91] and UPEC-DIT-23 [31] are CT contract satisfaction approaches. CONJUNCT [36] is both" (RTL2MµPATH, p14, §VIII); SynthLC synthesizes "a variety of formally verified leakage contracts from SystemVerilog processor designs" and "is the first automated methodology for formally verifying hardware adherence to them" (RTL2MµPATH, p1); the CT contract "enumerates a microarchitecture's transmitters and their unsafe ('leaky') operands" (p2–3).
- Proposed replacement (two words longer; fixes a misgrouping):

```latex
Formal verification of secure processors~\cite{blackbox} checks secure speculation in RTL~\cite{fadiheh2019upec,fadiheh2020formal,fadiheh2023exhaustive,zagieboylo2023specverilog,contractshadow,yang2026compass,dong2026interplay} or in abstracted processor models~\cite{cabodi2019speculationmc}, synthesizes leakage contracts and leakage signatures from RTL~\cite{mohr2024synthesizing,synthlc,rtl2upath}, and verifies which instructions are safe against constant-time contracts~\cite{leave,dinesh2024conjunct,dinesh2025hhoudini};
```

### F5. TransForm "litmus tests for transistency", and Isla "evaluates them"

- Location: `related.tex:12`, "TransForm~\cite{hossain2020transform} synthesizes litmus tests for transistency, Isla~\cite{armstrong2021isla} evaluates them against full ISA semantics~\cite{armstrong2019sail}, and CheckMate's synthesis found new attacks~\cite{trippel2018meltdownprime}".
- Problem: "them" makes Isla evaluate TransForm's tests, which it does not; Isla evaluates litmus tests in general. "Transistency" alone is undefined jargon; TransForm specifies memory transistency models axiomatically and synthesizes enhanced litmus tests from them. CheckMate did not "find" attacks; it synthesized them.
- Caroline's wording: "TransForm features an axiomatic vocabulary for formally specifying MTMs. Second, TransForm includes a synthesis engine to support the automated generation of litmus tests enhanced with MTM features (i.e., enhanced litmus tests, or ELTs)" (TransForm, p1); "CheckMate synthesized new exploits that are similar to Meltdown and Spectre" (CheckMate, p1) and "CheckMate generated new attacks—MeltdownPrime and SpectrePrime" (p3).
- Proposed replacement (same length):

```latex
TransForm~\cite{hossain2020transform} synthesizes litmus tests from axiomatic memory transistency models, Isla~\cite{armstrong2021isla} evaluates litmus tests against full ISA semantics~\cite{armstrong2019sail}, and CheckMate synthesized new attacks~\cite{trippel2018meltdownprime}.
```

### F6. AMuLeT's contract violations do not "compare two whole runs"

- Location: `related.tex:6`, "Because its contract violations compare two whole runs, they name neither the instruction that leaked nor the rule of the defense it broke, so each is root-caused by hand~\cite[\S 3.3]{amulet}".
- Problem: A violation does not compare anything; it is a program and a pair of inputs with equal contract traces whose final cache or TLB states differ. "Whole runs" suggests full-trace comparison, which AMuLeT does not do. "The rule of the defense" is not a term the paper defines.
- Source wording: "Violations are detected by AMuLeT when there is a difference in the µarch traces (final D-cache or TLB state) for two inputs to a program with the same contract trace" and "AMuLeT outputs the program and the pair of inputs causing the violation" (AMuLeT, p6, §3.3). Caroline's definition: "A microarchitecture upholds (resp. violates) a security contract if for all (resp. some) programs whose contract executions are indistinguishable, their microarchitectural executions are indistinguishable (resp. distinguishable) per the adversary model" (Protean, p3, §II-C).
- Proposed replacement (same length):

```latex
AMuLeT reports each contract violation as a program and two inputs whose final cache or TLB states differ, naming neither the leaking instruction nor its cause, so each is root-caused by hand~\cite[\S 3.3]{amulet}.
```

### T1. "Speculative leakage" vs "transient leakage" (heading plus three synonyms in one paragraph)

- Location: `related.tex:5`, "\textbf{Testing for speculative leakage:}"; the paragraph also says "transient leaks", "transient-execution bugs" and "transient-execution pattern".
- Problem: The background defines transient (bound to squash) and sequential (bound to commit), and the intro says secrets leak "transiently (via uncommitted instructions)". "Speculative leakage" is a different, broader notion (a speculative instruction may still commit), and four names for one concept in one paragraph read as four concepts. Caroline's related-work headings use exactly "transient leakage".
- Caroline's wording: headings "Detecting Transient Leakage" and "Formalizing Transient Leakage" (LCM, p13, §7); "A transient instruction is bound to squash [25]; a sequential instruction is bound to commit. Speculative instructions eventually become transient or sequential" (Protean, p3, §II-A).
- Proposed replacement (same length; T3 and T5 align the rest of the paragraph):

```latex
\textbf{Testing for transient leakage:}\label{sec:validating-speculative-execution-defenses}
```

### T2. "protected operand", "security guarantee", "one run", "each modeled misprediction"

- Location: `related.tex:6`, "\toolname{} instead checks one run against the defense's security guarantee, so each hit names its transmitter and protected operand, and it forces each modeled misprediction rather than relying on the simulated predictor's configuration".
- Problem: (1) An operand is not protected; protected *data* reaches an *unsafe* operand. model.tex uses "transmitters ... and their unsafe operands", as do SynthLC and Caroline's FAVA slides; "protected operand" appears nowhere else in the live paper. (2) Fig. 1's tagline is "against defense specifications" (agrees with the banked note). (3) The intro says "a condition on a single execution", not "run". (4) "Modeled" leaves unclear what is modeled; the tests carry the mispredictions as directives.
- Caroline's wording: the CT contract "enumerates a microarchitecture's transmitters and their unsafe ('leaky') operands" (RTL2MµPATH, p3, §II-B); "Side-Channel Leakage Contracts - defining unsafe instruction-operand pairs" (FAVA slides, p4).
- Proposed replacement (same length):

```latex
\toolname{} instead checks one execution against the defense's specification, so each hit names its transmitter and the unsafe operand a protected value reached, and it forces each test's mispredictions rather than relying on the simulated predictor~\cite{ayoub2021gem5spectre}.
```

### T3. "pre-silicon tools search for transient-execution bugs"; "contract coverage"

- Location: `related.tex:6`, "pre-silicon tools search for transient-execution bugs through differential execution~\cite{...}, gadget-driven simulation~\cite{...}, information-flow tracking~\cite{...} or contract coverage~\cite{geier2025coverage}".
- Problem: (1) gem5 prototypes are also pre-silicon, so "pre-silicon tools" does not separate these RTL tools from SimSpect's setting (the intro says "pre-RTL microarchitectural simulators"). Every cited tool works on RTL. (2) "Bug" is reserved in this paper for a leak the defense should have blocked (guidelines §5, four stages); these tools find vulnerabilities in mostly undefended cores. (3) "Contract coverage" is opaque: Geier et al. do coverage-guided fuzzing "based on Leakage Contracts" (their title).
- Caroline's wording: she separates "systematic litmus-based post-silicon testing of hardware" from a tool that "can be used to verify hardware before tape out" from RTL (rtl2µspec, p13); vulnerabilities, not bugs, for attack surfaces: "automatically identifies Spectre vulnerabilities in programs" (LCM, p1).
- Proposed replacement (same length):

```latex
Beyond functional RTL fuzzing~\cite{hur2021difuzzrtl,solt2024cascade}, RTL tools search for transient-execution vulnerabilities through differential execution~\cite{hur2022specdoctor,xu2025dejavuzz}, gadget-driven simulation~\cite{ghaniyoun2021introspectre,ghaniyoun2023teesec}, information-flow tracking~\cite{rostami2024specure,defaveritron2025phantomtrails} or leakage-contract coverage~\cite{geier2025coverage}.
```

### T4. AMuLeT "tests Spectre defense prototypes against contracts"

- Location: `related.tex:6`, "AMuLeT~\cite{amulet} tests Spectre defense prototypes against contracts".
- Problem: Fig. 1's tagline is "random testing of simulated defenses against security contracts"; the background and Protean name these "hardware–software security contracts". Bare "contracts" in a paragraph that also says "speculation contracts" (Revizor's own term) blurs which contract is meant, and "prototypes" is one of six names for the system under test (see D1). The banked note proposed "against security contracts"; agreed.
- Caroline's wording: "formal hardware-software security contracts, comprising an observer mode and an execution mode" (Protean, p3, §II-C).
- Proposed replacement (one word longer, adds Fig. 1's "random"; uses D1 option A, swap in option B if chosen):

```latex
In gem5, SpecCheck~\cite{mckevitt2023speccheck} monitors any running program for a generic transient-execution pattern, and AMuLeT~\cite{amulet} randomly tests simulated defenses against security contracts (Sec.~\ref{sec:known-bugs} and~\ref{sec:comparison-prior-work}).
```

### T5. "measure, synthesize or detect transient leaks"

- Location: `related.tex:6`, "other tools measure, synthesize or detect transient leaks~\cite{xiao2020speechminer,moghimi2020medusa,weber2026trevex}".
- Problem: Nobody synthesizes leaks. Medusa synthesizes attacks; SpeechMiner measures; TREVEX detects.
- Caroline's wording: "exploit synthesis" and "automated exploit program synthesis from microarchitecture and exploit pattern specifications" (CheckMate, p1).
- Proposed replacement (one word longer):

```latex
and other tools measure or detect transient leaks or synthesize attacks~\cite{xiao2020speechminer,weber2026trevex,moghimi2020medusa};
```

### T6. "Most leakage testing runs random programs and compares executions"

- Location: `related.tex:6`, opening sentence.
- Problem: "Most" is not shown, and the paragraph's own list includes tools that do not compare executions (SpecCheck checks "an arbitrary program's simulation" for one pattern, SpecCheck p1). "Compares executions" leaves out what is compared: pairs of executions.
- Caroline's wording: contracts "describe which victim executions an attacker is permitted to distinguish" (Protean, p3, §II-C).
- Proposed replacement (one word longer):

```latex
Many leakage testers run random programs and compare pairs of executions.
```

### T7. Formal-definitions sentence: "contracts", "which", "them", OISA

- Location: `related.tex:9`, "the safe and unsafe operands of a data-oblivious ISA~\cite{yu2019oisa}, ... and SNI and contracts (Sec.~\ref{sec:bg-contracts}), which Reineke surveys~\cite{reineke2026foundations}; software analyses and secure compilers build on them".
- Problem: "contracts" is bare (the background calls them hardware–software security contracts). "Which" can attach to SNI, contracts or all three; Reineke surveys leakage contracts. "Them" has three candidate referents. Caroline counts OISA among defenses with their own fine-grained leakage contract, which is exactly the paper's sense of "leakage contract", so naming it ties this sentence to our vocabulary.
- Caroline's wording: "these defenses adopt bespoke leakage contracts that are much finer grained", with OISA [97] among them (RTL2MµPATH, p3, §II-B); "formal hardware-software security contracts" (Protean, p3).
- Proposed replacement (three words longer):

```latex
Formal definitions of what may leak include a data-oblivious ISA's leakage contract of safe and unsafe operands~\cite{yu2019oisa}, information-flow properties of speculative executions~\cite{cheang2019formal}, and SNI and security contracts (Sec.~\ref{sec:bg-contracts}), the latter surveyed by Reineke~\cite{reineke2026foundations}; software analyses and secure compilers build on these definitions~\cite{cauligi2022sok,cauligi2020constanttime,vassena2021blade,patrignani2021exorcising,barthe2021highassurance,daniel2021haunter,fabian2022combinations,fabian2025lift,shivakumar2023typing,shivakumar2023declassified,mosier2024serberus,arranzolmos2025rsb}.
```

### T8. The axiomatic entry omits LCMs, which Caroline pairs with Cats vs. Spectre

- Location: `related.tex:9`, "Speculation has been given pomset~\cite{disselkoen2019code}, axiomatic~\cite{ponce2022cats}, ...".
- Problem: Caroline describes her own LCMs and Ponce-de-León and Kinder as the same approach. LCMs are cited only in Background, so Related Work lists the axiomatic line of speculation modeling without her group's paper (guidelines §6, "Cite originals ... Mosier's LCM"). Adding the key adds no words and duplicates no description.
- Caroline's wording: "Mosier et al. [120] and Ponce-de-León and Kinder [27] take an axiomatic approach inspired by memory consistency models to model and detect program instructions that may transiently access or leak secrets" (Serberus, p14, §8; [120] is the LCM paper); LCMs are "novel axiomatic security contracts" (LCM, p1).
- Proposed replacement (same length):

```latex
Speculation has been given pomset~\cite{disselkoen2019code}, axiomatic~\cite{ponce2022cats,lcms}, abstract~\cite{colvin2020abstractsemantics} and out-of-order operational semantics~\cite{guanciale2020inspectre}, and STT comes with a pen-and-paper proof over an abstract machine~\cite{yu2019sttformal}.
```

### T9. Formal paragraph closer: "neither proves nor synthesizes a guarantee"

- Location: `related.tex:9`, "\toolname{} neither proves nor synthesizes a guarantee: it takes the defense's own, models only the state that guarantee depends on, and uses the leakage predicate generatively, to test the implementation."
- Problem: The cited tools do not prove or synthesize "guarantees"; they verify RTL against, or synthesize, leakage contracts and secure-speculation properties. "the defense's own" is elliptical, "generatively" is jargon, and "the implementation" has no referent in this paragraph.
- Caroline's wording: "verifying hardware adherence to [leakage contracts]" and "synthesizing ... leakage contracts" (RTL2MµPATH, p1); she frames such contrasts as a different goal: "It also accomplishes a different goal—µspec model synthesis" (rtl2µspec, p13).
- Proposed replacement (two words longer; "gem5 implementation" per D1):

```latex
\toolname{} neither verifies nor synthesizes a contract: it takes the defense's own security guarantee, models only the state that guarantee depends on, and generates tests from it for the defense's gem5 implementation.
```

### T10. Pensieve "brings bounded model checking to early-stage defense designs"

- Location: `related.tex:9`, "Pensieve~\cite{pensieve} brings bounded model checking to early-stage defense designs."
- Problem: This blurs model and implementation, which is exactly the line SimSpect draws. Pensieve model-checks a hand-written model of a design in its own modeling discipline; it does not check the design's gem5 prototype.
- Source wording: "Our modeling discipline describes a microarchitectural design as a modular composition" and "leverages symbolic execution and bounded model checking to help architects automatically check defense schemes against formal guarantees" (Pensieve, p2).
- Proposed replacement (same length):

```latex
Pensieve~\cite{pensieve} model-checks hand-written models of early-stage defense designs.
```

### T11. "Beyond the synthesis" and "models have also been synthesized"

- Location: `related.tex:12`, "Beyond the synthesis \toolname{} builds on (Sec.~\ref{sec:bg-axiomatic}), ...; models have also been synthesized automatically~\cite{memsynth,norman2023pipesynth,hsiao2021rtl2uspec}."
- Problem: "the synthesis" does not say which synthesis (Background's roadmap says "minimal litmus-test synthesis"). "Models" is ambiguous in a paper whose "model" is the Alloy model: MemSynth synthesizes memory models, PipeSynth microarchitectural axioms, rtl2µspec µspec models.
- Caroline's wording: rtl2µspec is "a methodology and associated tool ... for automatically synthesizing µspec models" from RTL (rtl2µspec, p1); "CheckSuite and related tools ... describe microarchitectural executions using µspec models" (CounterPoint, p13).
- Proposed replacement (five words longer; removes an ambiguity with our own "model"):

```latex
Beyond the minimal litmus-test synthesis \toolname{} builds on (Sec.~\ref{sec:bg-axiomatic}), litmus tests have been generated from relaxation cycles~\cite{alglave2010fences} and to contrast memory models~\cite{maradhaim2010generating,maradhaim2011litmus}, run on hardware~\cite{sarkar2011power,flur2016modelling,alglave2011litmus,perple} and mutated to evaluate testing~\cite{mcmutants}; memory models and microarchitectural axioms have also been synthesized~\cite{memsynth,norman2023pipesynth,hsiao2021rtl2uspec}.
```

### T12. "secret annotation" and "relaxations that recover performance"

- Location: `related.tex:15`, "secret annotation~\cite{schwarz2020context,fustos2019spectreguard}" and "relaxations that recover performance~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned}".
- Problem: "Relaxations" suggests weakened security, and it collides with Background's "relaxation" (Lustig's minimality relaxations, background.tex). Protean calls these security-preserving optimizations. "Secret annotation" undersells source-level secrecy labels.
- Caroline's wording: "Prior work proposes security-preserving optimizations for layering on top of Spectre defenses" and "InvarSpec [150], Clearing Shadows [128], and Levioso [51] enable earlier, safe execution"; ConTExT and SpectreGuard "rely on explicit source-level secrecy annotations to label memory as secret/public" (Protean, p14, §X-2 and §X-3).
- Proposed replacement (same length):

```latex
Beyond those cited in the introduction, proposals include context-sensitive fencing~\cite{taram2019csf}, conditional speculation~\cite{li2019conditional}, secrecy annotations~\cite{schwarz2020context,fustos2019spectreguard}, CFI-informed speculation~\cite{koruyeh2020speccfi}, cache partitioning~\cite{kiriansky2018dawg}, security-preserving optimizations~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned}, and many others~\cite{jin2023specterminator,daniel2023prospect,ganjisaffar2025specasan,hajiabadi2024levioso,hajiabadi2025cassandra,aimoniotis2024janus,chen2025mustt,cui2023ssft,kvalsvik2025shadowbinding,green2023safebet,kim2024perspective,castes2024sharing,trujillo2026register,wu2025rcp,sakalis2023delayonsquash,choudhary2023declassiflow}.
```

### T13. "GhostMinion's gem5 model"

- Location: `related.tex:15`, "Pensieve's authors found that GhostMinion's gem5 model omits the leapfrogging the defense relies on".
- Problem: In this paper "model" means the formal model; gem5 code is the implementation. Pensieve itself says the open-sourced simulator "does not implement" leapfrogging.
- Wording: "the simulator open-sourced by the authors [2] does not implement the leapfrogging operations" (Pensieve, p10); Caroline: "STT's gem5 implementation" (Protean, p2–3).
- Proposed replacement (same length; per D1):

```latex
Pensieve's authors found that GhostMinion's gem5 implementation omits the leapfrogging the defense relies on~\cite{pensieve},
```

### D1. DECIDE: one name for the system under test

- Location: six names in one section: "Spectre defense prototypes" (`:6`), "the implementation" (`:9`), "the defense's gem5 implementation" (`:12`), "the gem5 prototypes" (`:15`), "GhostMinion's gem5 model" (`:15`), "bypasses STT in gem5" (`:15`).
- Problem: Six names read as six objects, and "model" collides with the formal model. The intro carries an open `\anna{standardize 'simulated spectre defense'}`.
- Option A (Fig. 1 v9 and its caption): "simulated defense" ("random testing of simulated defenses", "runs these tests on a simulated Spectre defense"). Implication: matches the figure; reads as one object; a little less concrete about gem5.
- Option B (Caroline's usage): "gem5 implementation" ("STT's gem5 implementation", Protean p2–3; "our final, fixed gem5 implementation of PROTEAN", p11). Implication: concrete, contrasts directly with "RTL" and "model"; Fig. 1 would need "Simulated Defense" changed or glossed once.
- Either way, never "model" or "prototype" for gem5 code in Related Work. Not chosen here; T4 shows option A, T9 and T13 show option B, so whichever Anna picks, swap in that phrase.

```latex
% Option A: simulated defense(s)   e.g. "AMuLeT~\cite{amulet} randomly tests simulated defenses ..."
% Option B: gem5 implementation(s) e.g. "AMuLeT~\cite{amulet} randomly tests gem5 implementations of defenses ..."
```

### D2. DECIDE: the litmus paragraph's closing contrast (open since §10, "CheckMate contrast")

- Location: `related.tex:12`, "\toolname{} applies minimal-test enumeration to Spectre defenses, and what it tests is the defense's gem5 implementation, not the model."
- Problem: (1) "minimal-test enumeration" contradicts Background, which says SimSpect takes "the enumeration of executions rather than programs"; the lineage term is minimal litmus-test synthesis. (2) "not the model" has no referent (the Alloy model? the Check tools' µspec models?), and the paragraph itself cites litmus tests "run on hardware", so "tests an implementation" does not distinguish SimSpect from that line. The precise contrast is with the Check tools and CheckMate, which analyze µspec models (RTL2MµPATH, p1: "analyzing abstract models of microarchitectures, called µSPEC models").
- Option (a), keep the implementation-vs-model contrast, made precise:

```latex
\toolname{} applies minimal litmus-test synthesis to Spectre defenses and, unlike the Check tools, runs its tests on an implementation instead of analyzing a $\mu$spec model.
```

- Option (b), contrast on content (what the model describes):

```latex
CheckMate's exploit patterns describe attacks on a modeled microarchitecture; \toolname{} applies minimal litmus-test synthesis to what a defense forbids and runs the tests on its gem5 implementation.
```

- Earlier recommendation in §10 was (c), both; that was a recommendation, not a decision.

### D3. DECIDE: "security litmus test" means something different from CheckMate's

- Location: `related.tex:15`, "it derives security litmus tests from each defense's specification" (term from Fig. 1 and the intro).
- Problem: CheckMate coined the term for minimal *exploit programs*; SimSpect's security litmus tests are programs plus directives that attempt leakage a defense forbids, with "no attacker or probe program" (intro). A reader who knows CheckMate (Caroline's paper, which Background cites for the term's origin) will read SimSpect's tests as exploits.
- Caroline's wording: "Security litmus tests are the most compact representation of an exploit program, meaning they contain the minimal number of micro-ops necessary to produce the exploit pattern of interest" (CheckMate, p5, §III).
- Option A: keep the term and mark the difference once, here (three words longer):

```latex
\toolname{} complements these case-by-case findings: instead of designing an attack against one defense, it derives security litmus tests, which need no receiver, from each defense's specification.
```

- Option B: keep the sentence as is; the shared lineage (minimal, Alloy-synthesized) is the point, and Background already credits CheckMate.

### C1. "ReCon leaks": design or implementation?

- Location: `related.tex:15`, "two of ReCon's authors report that ReCon leaks when an instruction has multiple secret sources~\cite{kvalsvik2025reconnaissance}".
- Problem: Every other item in the paragraph says whether a flaw is in a design or in a gem5 implementation; this one does not, and it sits next to our UV3 (an implementation bug in ReCon's STT, intro bug (3)). The source is an IEEE DataPort dataset this audit could not read, so the right reading is unverified; it ties to the open §10 DECIDE (UV3 novelty).
- Proposed replacement (pick the reading the source supports):

```latex
% if the dataset concerns ReCon's design:
two of ReCon's authors report that ReCon's design leaks when an instruction has multiple secret sources~\cite{kvalsvik2025reconnaissance}.
% if it concerns ReCon's gem5 implementation:
two of ReCon's authors report that ReCon's gem5 implementation leaks when an instruction has multiple secret sources~\cite{kvalsvik2025reconnaissance}.
```

### Structural and convention observations

- **Helium's Related Work is about 450 words, not 250.** pdftotext puts 221 prose words under the "IX. Related Work" heading and another 230 in the column that overflows above it on p13 ("channels. Others use symbolic analysis..." through the LmSpec/LmTest contrast). The 250 target in `PAPER_AUDIT_GUIDELINES.md` §1 counted only the first part. Ours is 561 prose words (citations, labels and `\anna` stripped), about 25% over Helium; correcting the target is Anna's call.
- **She names the closest prior work inside Related Work:** "The Check tools ... are the most relevant prior work, especially RTLCheck" (rtl2µspec, p13); "The closest prior work verifies hardware adherence to CT contracts" (RTL2MµPATH, p14); "Most similar to TracerSym, Bao et al. ..." (Helium, p13). Ours never says which cited tool is closest; AMuLeT's "closest" status lives only in the intro, by the §10 decision.
- **She frames differences as different goals, not shortcomings:** "It also accomplishes a different goal—µspec model synthesis" (rtl2µspec, p13); "This does not reflect a fundamental limitation of LMSPEC's leakage clauses ..., but rather the fact that they support distinct use cases: leakage detection vs. quantification" (Helium, p13). Our formal-paragraph closer does this; the AMuLeT sentence (F6) and the defenses closer ("case-by-case findings") are framed as deficiencies.
- **Where the "this work" sentence goes:** she places it right after the closest work, often mid-paragraph ("Clou is not based on symbolic execution; it uses axiomatic LCM definitions", LCM p13; "Like ProtISA ... Unlike ProtISA", Protean p14), or closes with "In contrast, TransForm can be used to generate ELTs" (TransForm, p13). Ours always closes the paragraph, which matches TransForm.
- **Run-in headings:** Helium and LCM use bold run-in headings ending in a colon, as ours do; LCM's wording is "Detecting Transient Leakage" / "Formalizing Transient Leakage" (p13), which supports T1.
- **Long citation lists are her style too:** Protean's Related Work cites 11 papers for one clause ("Some defend against cache-based channels only [6], [7], [61], [66], [75], [99], [107], [112], [113], [126], [142]", p14).
- **One name per object:** her papers keep "gem5 implementation", "transient leakage", and "transmitters and their unsafe operands" fixed throughout. Ours uses six names for the system under test (D1) and four for leakage (T1).
- **Her papers not in Related Work:** LCM/Clou appears only in Background, though Clou also fits the "software tools test programs for Spectre gadgets" list ("a static analysis tool based on LCMs which automatically identifies Spectre vulnerabilities in programs", LCM p1). Pandora, Helium, CounterPoint and µSpectre are already listed in §8 and §11 with their status; not repeated here.
- **Cross-section:** the intro's "a recent squash race in STT~\cite{protean}" needs the same change as F1.

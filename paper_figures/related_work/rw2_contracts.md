# RW2: Leakage contracts and speculation security definitions (related-work part 2)

Search agent RW2, 2026-11-10. Scope: part (2) of the `\auditnote` plan in `~/trippel/ISCA-27/sections/related.tex:9`. Every NEW entry was verified against crossref metadata (DOI lookup), the arXiv abstract page, or the publisher page in this session; verified BibTeX is in `rw2_contracts.bib` (same folder). Entries marked "in bib" already exist in `ISCA-27/sections/references.bib` and were not duplicated. Nothing was found that had to be marked UNVERIFIED, but two items are preprints with no venue listed (noted in the table).

## Already in references.bib (core of part 2; do not re-add)

Core: `guarnieri2021contracts`, `guarnieri2020spectector`, `cheang2019formal` (CSF 2019, DOI 10.1109/CSF.2019.00027; authors Cheang, Rasmussen, Seshia, Subramanyan), `cauligi2022sok`, `lcms` (Mosier et al., ISCA 2022, the axiomatic contracts paper), `leave` (CCS 2023), `synthlc` (actually LeaSyn: Wang, Mohr, von Gleissenthall, Reineke, Guarnieri, CCS 2025, arXiv 2509.06509; confirmed the key is misleading, SynthLC is in `rtl2upath`), `mohr2024synthesizing` (DATE 2024). Cut-list / defense-side entries also already present: `cauligi2020constanttime`, `mosier2024serberus`, `vassena2021blade`, `daniel2023prospect`, `shivakumar2023declassified`, `shivakumar2023typing`, `choudhary2023declassiflow`, `patrignani2021exorcising`, `fabian2022combinations`, `barthe2021highassurance`, `ponce2022cats`, `guanciale2020inspectre`, `daniel2021haunter`, `buiras2021observation`, `contractshadow`, `pensieve`, `dong2026interplay`, `yu2019stt`.

## New candidates (verified BibTeX in rw2_contracts.bib)

| key | title | authors | venue/year | URL/DOI | what it does | how SimSpect differs / why cite | relevance |
|---|---|---|---|---|---|---|---|
| `yu2019oisa` | Data Oblivious ISA Extensions for Side Channel-Resistant and High Performance Computing | Jiyong Yu, Lucas Hsiung, Mohamad El'Hajj, Christopher W. Fletcher | NDSS 2019 | 10.14722/ndss.2019.23061 | ISA-level contract: data labeled Public/Confidential, each instruction operand Safe/Unsafe; hardware must hide or trap data-dependent behavior; prototyped on BOOM. | Origin of the "unsafe operand = transmitter" vocabulary that STT and our leakage-function clause use; cite where we define transmitters. | HIGH |
| `dinesh2024conjunct` | ConjunCT: Learning Inductive Invariants to Prove Unbounded Instruction Safety Against Microarchitectural Timing Attacks | Sushant Dinesh, Madhusudan Parthasarathy, Christopher W. Fletcher | IEEE S&P 2024, pp. 3735-3753 | 10.1109/SP54263.2024.00180 | Proves, on RTL, which ISA instructions are safe (non-transmitters) for unbounded cycles via learned inductive invariants (Ibex, Rocket). | Synthesizes/proves the transmitter set from RTL; SimSpect takes the defense's transmitter set as a model input and tests a simulator. Pairs with `rtl2upath`/SynthLC. | MEDIUM-HIGH |
| `dinesh2025hhoudini` | H-Houdini: Scalable Invariant Learning | Sushant Dinesh, Yongye Zhu, Christopher W. Fletcher | ASPLOS 2025, pp. 603-618 (Best Paper per ASPLOS awards page) | 10.1145/3669940.3707263 | Hierarchical invariant learning (tool VeloCT) for safe-instruction-set synthesis; first to scale to BOOM. | Same contrast as ConjunCT; one cite for "RTL proofs of the transmitter contract" (cite both or just this one). | MEDIUM |
| `barthe2024lmtest` | Testing Side-channel Security of Cryptographic Implementations against Future Microarchitectures | Barthe, Böhme, Cauligi, Chuengsatiansup, Genkin, Guarnieri, Mateos Romero, Schwabe, Wu, Yarom | CCS 2024, pp. 1076-1090 | 10.1145/3658644.3670319 | LmSpec DSL for leakage models of proposed optimizations + LmTest to test crypto code against them (18 optimizations, 25 implementations). | Also takes a leakage model as an explicit spec and tests against it, but tests software against a hypothetical model; SimSpect tests a hardware implementation against its defense model. | MEDIUM |
| `reineke2026foundations` | Foundations of Hardware-Software Leakage Contracts | Jan Reineke | Engineering Trustworthy Software Systems, LNCS 16481, Springer 2026, pp. 89-112 (arXiv 2610.20754) | 10.1007/978-981-95-8617-2_4 | Tutorial/survey of the leakage-contract framework, recent contributions, open challenges. | Recent survey anchor for contracts (the hardware-side counterpart of `cauligi2022sok`); lets us cite one paper for "the contract line of work". | MEDIUM |
| `fabian2025lift` | Do You Even Lift? Strengthening Compiler Security Guarantees against Spectre Attacks | Xaver Fabian, Marco Patrignani, Marco Guarnieri, Michael Backes | PACMPL 9 (POPL 2025), pp. 893-922 | 10.1145/3704867 | Lifts secure-compilation guarantees of 9 countermeasures from weaker to stronger speculative semantics; SLH does not lift to indirect-jump speculation. | Shows a guarantee depends on which speculation sources the semantics includes, the same issue as our speculation-contract clause; software-side. | LOW-MEDIUM |
| `guarnieri2020casco` | Contract-Aware Secure Compilation | Marco Guarnieri, Marco Patrignani | arXiv 2012.14205 (PriSC 2021 short talk) | arXiv:2012.14205 | Compilers parametric in the hardware-software contract. | Software consumer of contracts; cite only if the paragraph covers the software side. | LOW |
| `arranzolmos2025rsb` | Protecting Cryptographic Code Against Spectre-RSB (and, in Fact, All Known Spectre Variants) | Arranz Olmos, Barthe, Chuengsatiansup, Grégoire, Laporte, Oliveira, Schwabe, Yarom, Zhang | ASPLOS 2025, pp. 933-948 | 10.1145/3676641.3716015 | Speculative-constant-time type system + compiler pass in Jasmin, Coq-verified, all known Spectre variants. | Software SCT, already represented by `cauligi2022sok`; cut-list candidate. | LOW |
| `geier2025coverage` | Coverage-Guided Pre-Silicon Fuzzing of Open-Source Processors based on Leakage Contracts | Gideon Geier, Pariya Hajipour, Jan Reineke | arXiv 2511.08443 (2025; no venue listed) | arXiv:2511.08443 | Contract-based RTL fuzzing of Rocket/BOOM with a Self-Composition Deviation coverage metric. | Contract testing of RTL with random programs + coverage; SimSpect uses model-directed enumeration on a simulator. Fits part (1) better; hand to RW1. | LOW-MEDIUM (preprint) |
| `fabian2026compositional` | Detecting Speculative Leaks with Compositional Semantics | Fabian, Guarnieri, Köpf, Morales, Patrignani, Reineke, Sanchez | arXiv 2603.29800 (2026; no venue listed) | arXiv:2603.29800 | Consolidated SNI + compositional speculative semantics, implemented in Spectector. | Possible replacement for or addition to `guarnieri2020spectector` + `fabian2022combinations`; check for a venue before citing. | LOW (preprint) |

Searched with nothing new found: a mechanized/relational STT proof newer than STT's own MICRO 2019 formal analysis, and 2025-2026 ISCA/MICRO/HPCA contract papers specific to STT/SPT-style defenses (none surfaced; AMuLeT, `contractshadow` and `dong2026interplay`, all in bib, are the closest).

## Proposed LaTeX paragraph (~185 words)

```latex
\para{Leakage contracts and speculation security definitions.}
Formal definitions of secure speculation began with information-flow
properties over speculative executions~\cite{cheang2019formal} and
speculative non-interference~\cite{guarnieri2020spectector}, which
Guarnieri et al.\ generalized into hardware--software
contracts~\cite{guarnieri2021contracts}: an observation clause (what an
instruction leaks) and an execution clause (what may execute
speculatively). The OISA proposal~\cite{yu2019oisa} introduced the
safe/unsafe operand split that later defenses call transmitters, and
LCMs~\cite{lcms} recast contracts axiomatically, in the style of memory
models, which is the formalism \toolname{} builds on. Software-side work
uses such contracts to verify or compile code (surveyed
in~\cite{cauligi2022sok}). Hardware-side work checks or synthesizes
contracts for RTL designs: LeaVe verifies them~\cite{leave}, Mohr et al.\
and Wang et al.\ synthesize them~\cite{mohr2024synthesizing,synthlc},
SynthLC derives leakage signatures~\cite{rtl2upath}, and
ConjunCT/H-Houdini prove which instructions are safe for unbounded
executions~\cite{dinesh2024conjunct,dinesh2025hhoudini}; Reineke surveys
the line~\cite{reineke2026foundations}. \toolname{} instead treats a
defense's own guarantee as the contract, split into a speculation
contract, a protection set (which has no counterpart in a contract) and a
transmitter-based leakage function, and uses it generatively, to
enumerate tests that a correct implementation of that defense must not
leak on.
```

Notes for Anna: (a) the paragraph maps our three clauses onto Guarnieri's two clauses, which the related.tex note says should happen once, in background; if it already appears there, cut the last sentence down to a back-reference. (b) Whether to include ConjunCT/H-Houdini (transmitter-set proofs) is a framing call: they support our "leakage function = transmitter set" clause but add two cites. (c) The `synthlc` key really is LeaSyn (CCS 2025, arXiv 2509.06509), so the existing audit note is right; renaming it to e.g. `wang2025leasyn` would avoid confusion (paper-repo edit, Anna's call).

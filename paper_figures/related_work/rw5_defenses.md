# RW5: Spectre hardware defenses by class (related-work part 5)

Compiled 2026-11-10 for ISCA-27 `sections/related.tex` part (5). Almost every defense in scope is **already in `references.bib`**; only 5 new entries are proposed (in `rw5_defenses.bib`, metadata from Crossref/doi.org, resolved this session). Existing entries were checked by reading their bib fields, not re-fetched. Gap that was not filled: no separate "data-oblivious" defense beyond SDO.

## Bib issues found in existing references.bib (fix by hand; paper is read-only for Claude)

- `sdo`: the `title` field holds the booktitle ("2020 ACM/IEEE 47th Annual International Symposium on Computer Architecture (ISCA)") instead of the paper title "Speculative Data-Oblivious Execution: Mobilizing Safe Prediction For Safe and Efficient Speculative Execution" (from memory, UNVERIFIED in this session; check DOI 10.1109/ISCA45697.2020.00064). It will render wrong.
- `yu2019stt`: no `year` field was parsed (check it renders 2019).
- DoM has no separate key: `sakalis2019delay` ("Efficient invisible speculative execution through selective delay and value prediction", ISCA 2019) is the Delay-on-Miss paper, so cite DoM as `\cite{sakalis2019delay}`.

## Table

| key | title | authors | venue/year | DOI/URL | class | in bib? | why cite | relevance |
|---|---|---|---|---|---|---|---|---|
| yu2019stt | Speculative Taint Tracking (STT) | Yu, Yan, Khyzha, Morrison, Torrellas, Fletcher | MICRO 2019 | bib | delay/taint | y | tested; has Alloy model | high |
| nda | NDA: Preventing Speculative Execution Attacks at Their Source | Weisse et al. | MICRO 2019 | 10.1145/3352460.3358306 | delay/taint | y | class exemplar (not tested) | med |
| sakalis2019delay | Efficient invisible speculative execution through selective delay and value prediction (DoM) | Sakalis, Kaxiras, Ros, Jimborean, Själander | ISCA 2019 | bib | delay | y | DoM; recon/gem5 scheme 3 | med |
| recon | ReCon: Efficient Detection, Management, and Use of Non-Speculative Information Leakage | Aimoniotis, Kvalsvik, Chen, Själander, Kaxiras | MICRO 2023 | 10.1145/3613424.3623770 | delay/taint relax | y | tested; has Alloy model | high |
| doppelganger | Doppelganger Loads | Kvalsvik, Aimoniotis, Kaxiras, Själander | ISCA 2023 | 10.1145/3579371.3589088 | delay optimization | y | optimization on delay schemes | med |
| spt | Speculative Privacy Tracking (SPT) | Choudhary, Yu, Fletcher, Morrison | MICRO 2021 | 10.1145/3466752.3480068 | taint (non-spec secrets) | y | tested; has Alloy model | high |
| sdo | Speculative Data-Oblivious Execution | Yu, Mantri, Torrellas, Morrison, Fletcher | ISCA 2020 | 10.1109/ISCA45697.2020.00064 | data-oblivious | y (title broken) | only data-oblivious class member | med |
| specshield | SpecShield | Barber, Bacha, Zhou, Zhang, Teodorescu | PACT 2019 | 10.1109/PACT.2019.00020 | delay | y | class list | low |
| li2019conditional | Conditional Speculation | Li, Zhao, Hou, Zhang, Meng | HPCA 2019 | bib | delay (filtered) | y | class list | low |
| loughlin2021dolma | DOLMA: Securing Speculation with the Principle of Transient Non-Observability | Loughlin et al. | USENIX Sec 2021 | bib | delay | y | class list | low |
| schwarz2020context | ConTExT: A Generic Approach for Mitigating Spectre | Schwarz et al. | NDSS 2020 | bib | secret-annotation delay | y | class list | low |
| fustos2019spectreguard | SpectreGuard | Fustos, Farshchi, Yun | DAC 2019 | bib | secret-annotation delay | y | class list | low |
| yan2018invisispec | InvisiSpec | Yan, Choi, Skarlatos, Morrison, Fletcher, Torrellas | MICRO 2018 | bib | invisible | y | tested with STT testset | high |
| khasawneh2019safespec | SafeSpec | Khasawneh et al. | DAC 2019 | bib | invisible | y | class list | low |
| ainsworth2020muontrap | MuonTrap | Ainsworth, Jones | ISCA 2020 | bib | invisible | y | class list | low |
| ainsworth2021ghostminion | GhostMinion | Ainsworth | MICRO 2021 | bib | invisible | y | class list | low |
| cheng2024speclfb | SpecLFB | Cheng, Tong, Wang, Zhou, Jiang, Zhang | USENIX Sec 2024 | bib | invisible (LFB) | y | tested with STT testset | high |
| saileshwar2019cleanupspec | CleanupSpec: An "Undo" Approach to Safe Speculation | Saileshwar, Qureshi | MICRO 2019 | bib | undo | y | tested with STT testset | high |
| wu2025rcp | Reversible Coherence Protocol (ReversiSpec successor) | Wu, Qian | TDSC 2025 | bib | undo | y | CleanupSpec successor | low |
| taram2019csf | Context-Sensitive Fencing | Taram, Venkat, Tullsen | ASPLOS 2019 | bib | fence co-design | y | fence class | low |
| koruyeh2020speccfi | SpecCFI: Mitigating Spectre Attacks using CFI Informed Speculation | Koruyeh, Haji Amin Shirazi, Khasawneh, Song, Abu-Ghazaleh | IEEE S&P 2020 | 10.1109/SP40000.2020.00033 | control-flow restriction (BTB/RSB) | **n (new)** | named in brief; scope contrast (SimSpect targets PHT-style data leaks) | low-med |
| zhao2022pinned | Pinned Loads | Zhao, Ji, Morrison, Marinov, Torrellas | ASPLOS 2022 | bib | delay relaxation | y | co-design | low |
| sakalis2023delayonsquash | Delay-on-Squash: Stopping Microarchitectural Replay Attacks in Their Tracks | Sakalis, Kaxiras, Själander | ACM TACO 20(1) 2023 | 10.1145/3563695 | delay (replay) | **n (new)** | DoM lineage; replay threat model | low |
| hu2021sok | SoK: Hardware Defenses Against Speculative Execution Attacks | Hu, He, Lee | SEED 2021 | bib | survey | y | taxonomy anchor | high |
| behnia2021interference | Speculative interference attacks: breaking invisible speculation schemes | Behnia et al. | ASPLOS 2021 | bib | attack on invisible | y | defense broken post-publication | high |
| li2022unxpec | unXpec: Breaking Undo-based Safe Speculation | Li, Miao, Yang, Bu | HPCA 2022 | bib | attack on undo | y | breaks CleanupSpec (which SimSpect tests) | high |
| aimoniotis2022doin | Data-Out Instruction-In (DOIN!) | Aimoniotis, Kvalsvik, Själander, Kaxiras | SEED 2022 | bib | attack on delay | y (cut) | breaks delay schemes; consider restoring | med |
| chakraborty2022timed | Timed speculative attacks (STLF) | Chakraborty et al. | (see bib) | bib | attack | y | STLF relevance | med |
| fustos2020spectrerewind | SpectreRewind: Leaking Secrets to Past Instructions | Fustos, Bechtel, Yun | ASHES 2020 (CCS workshop) | 10.1145/3411504.3421216 | attack (backwards-in-time contention channel) | **n (new)** | channel outside cache-centric defenses' threat model | med |
| xiao2023hackyracers | Hacky Racers: Exploiting Instruction-Level Parallelism to Generate Stealthy Fine-Grained Timers | Xiao, Ainsworth | ASPLOS 2023 | 10.1145/3575693.3575700 | attack (ILP timers, backwards-in-time gadgets) | **n (new)** | abstract says its gadgets "break many hardware countermeasures in the literature" | med |
| skarlatos2019microscope | MicroScope: Enabling Microarchitectural Replay Attacks | Skarlatos, Yan, Gopireddy, Sprabery, Torrellas, Fletcher | ISCA 2019 | 10.1145/3307650.3322228 | attack (replay) | **n (new)** | motivates Delay-on-Squash; optional | low |

## Proposed LaTeX paragraph (~180 words)

```latex
\paragraph{Spectre hardware defenses}
Hardware defenses fall into a few classes~\cite{hu2021sok}. \emph{Delay and taint-tracking} schemes stop speculative data from reaching a transmitter: NDA~\cite{nda}, STT~\cite{yu2019stt}, Delay-on-Miss~\cite{sakalis2019delay}, SpecShield~\cite{specshield}, Conditional Speculation~\cite{li2019conditional}, DOLMA~\cite{loughlin2021dolma}, and the secret-annotation designs ConTExT~\cite{schwarz2020context} and SpectreGuard~\cite{fustos2019spectreguard}; SPT~\cite{spt}, ReCon~\cite{recon} and Doppelganger loads~\cite{doppelganger} relax them by declassifying data, and SDO~\cite{sdo} replaces delay with data-oblivious execution. \emph{Invisible-speculation} schemes hide speculative cache state: InvisiSpec~\cite{yan2018invisispec}, SafeSpec~\cite{khasawneh2019safespec}, MuonTrap~\cite{ainsworth2020muontrap}, GhostMinion~\cite{ainsworth2021ghostminion} and SpecLFB~\cite{cheng2024speclfb}. \emph{Undo} schemes roll back that state on a squash: CleanupSpec~\cite{saileshwar2019cleanupspec}. Fence and co-design schemes include context-sensitive fencing~\cite{taram2019csf}, SpecCFI~\cite{koruyeh2020speccfi} and Pinned Loads~\cite{zhao2022pinned}. Several of these defenses were later broken by attacks outside their designers' analysis~\cite{behnia2021interference,li2022unxpec,aimoniotis2022doin,fustos2020spectrerewind,xiao2023hackyracers}. \toolname{} expresses STT, ReCon and SPT as models and tests these three plus InvisiSpec, CleanupSpec and SpecLFB in gem5. Instead of designing a new attack, it checks whether each simulated implementation keeps the defense's own guarantee.
```

Wording caveats for Anna: "relax them by declassifying data" for Doppelganger is a loose grouping (it is a load-address-prediction optimization for delay schemes); and the "broken by" sentence lumps SpectreRewind/Hacky Racers (new channels) with direct defense breaks. Tighten both if you want precision.

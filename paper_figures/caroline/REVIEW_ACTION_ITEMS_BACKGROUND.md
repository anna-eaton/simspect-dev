# Review action items: Background

Coverage check (2026-11-16): every live problem in reviews/2026-11-15_2313_background.md has an item; 5 added, 14 fixes added, 5 not carried over.

Re-checked against ISCA-27 `748779e` (2026-11-16): `background.tex`, intro.tex, related.tex, Fig. 1 (`tikz/intro_threelayer_v9.tex`) and Table 1 (`tikz/execvocab_v3_8pt.tex`) are unchanged since the review, so every `background.tex` line below still holds. Lines shifted in two other files: model.tex :20→:23, :24→:28, :30→:36, :32→:38, :34→:40, :44→:50, :52→:55, and the old :3–5 opening is now :9 (model §3.1 is now titled "Candidate Executions"); pipeline.tex :27→:31, :83→:88, :112→:120, :134→:142, :142→:150.

Full review behind this list: [reviews/2026-11-15_2313_background.md](reviews/2026-11-15_2313_background.md). Index of all reviews and action items: [REVIEWS.md](REVIEWS.md).

Targeted fixes only. Checked against ISCA-27 `5f00495` (2026-11-15 23:13; `background.tex` is unchanged since `deaf190`). Line numbers are `sections/background.tex` unless marked. Rendered Background: about 1,200 words now, about 880 after every item below; Protean §II is about 790 words and Helium §II about 700. Full review with per-sentence audit: `REVIEWS.md`, entry "2026-11-15 23:13 — background". This pass focuses on ambiguity across paragraphs, uncited claims and missing section refs, and adds a "Missing from Background" list.

Fixed since the 805e684 review, so dropped: the "borrows two of these names" paragraph and its undefined execution/observation clauses; SynthLC's "fine-grained statement" (B-2); the visibility-point origin; the ROB-head clause; "e.g. once"; NDA and SpecShield (B-9); ". the model's"; "it detects it"; "a defense such as STT"; CheckMate credited for "security litmus test"; "transient" is now bound-to-squash in the abstract, the intro and here. Withdrawn: SPT "already leaked" is SPT's own key-idea wording (SPT abstract).

## 🔴 Wrong, uncited, or contradicts another section

- [x] **`:35` "their adversary model cannot differentiate between different transmitters that touch the same microarchitectural state".** It is uncited, it contradicts `:22` ("A *separate* adversary model"), and it is a fourth statement of the AMuLeT contrast, which your guideline (PAPER_AUDIT_GUIDELINES.md:78) limits to the intro, Related Work and Results. → Decision B-5. Rec.: delete the sentence, drop "instead" from the next one, and repoint intro.tex:136 from `(\S~\ref{sec:bg-contracts})` to `(\S~\ref{sec:known-bugs})`. *(done 2026-11-16: Anna took option A, justifying it in Background: the adversary model is a projection of state, so it cannot tell which instruction changed it; STT's stores and A-KV3 as the example; intro sentence rewritten to match)*
- [x] **`:35` "Two lines of work describe a single defense instead."** SynthLC's leakage contracts describe a microarchitecture, which defenses then assume (RTL2MµPATH §II-B, p.4: defenses "assume the availability of microarchitectural leakage contracts, which characterize implementations' transmitters"). → `Two lines of work describe one design at a time.` *(2026-11-16: already applied in a0ae7e4 (`:55`); tick.)*
- [ ] **Fig. 1 (`tikz/intro_threelayer_v9.tex:47`) "(ARCH, SEQ), which guarantees weak speculative non-interference".** This contradicts `:43`. ARCH-SEQ is a hardware contract, while wSNI is a program property defined against ARCH-SEQ observations (Guarnieri Def. 4, p.6). Guarnieri p.4 calls ARCH-SEQ "a simple and clean formulation of the idea behind transient noninterference". The "(ARCH, SEQ)" pair notation also breaks your 2026-11-14 rule. → `\textit{e.g., (\contract{ARCH}, \contract{SEQ}), which guarantees weak speculative non-interference}~\cite{guarnieri2021contracts}` → `\textit{e.g., \contract{ARCH-SEQ}}~\cite{guarnieri2021contracts}` (B-4).
- [x] **`:43` "MCMs define ordering restrictions on memory events in an ISA."** This is vague, and "in an ISA" is false for the C++11 models cited three sentences later. → `MCMs define the values that loads in a parallel program may return~\cite{lcms}.` (LCM §2.1, p.3: "MCMs define the value(s) that can be legally returned by shared-memory loads in a parallel program.")
- [x] **`:43` "Acyclicity is used because if you have a cycle of protected ordering edge-connected events, …".** It is uncited, written in second person, and serves no later section. → Delete it.
- [x] **`:45` "every execution graph specified by an axiomatic model … representing a forbidden execution".** "Specified by" reads as *allowed*, which contradicts "forbidden". → Change "specified by an axiomatic model" to "that violates the model's axioms", and delete ": a short (program, outcome) pair representing a forbidden execution" (it repeats `:45` S1).
- [x] **`:47` last sentence (your \anna).** Four problems:
  - "po" is wrong: the model uses spo (model.tex:24);
  - "(Stage~1a)" is not a ref;
  - CheckMate already modeled speculation (CheckMate p.2: "supplying CheckMate with a speculative out-of-order (OoO) processor");
  - the real difference from CheckMate is never stated.

  → `\toolname{} reuses execution graphs, bounded enumeration and relaxation-based minimality (\S~\ref{sec:test-generation-alloy}), but its graphs encode a leak that a defense's guarantee forbids (\S~\ref{sec:leakage-predicate}), and its tests run on the defense's implementation.`
- [x] **`:47` "minimal exploit programs that induce them".** Two problems:
  - CheckMate's "minimal" means the fewest micro-ops (§III-B2: "contain the minimal number of micro-ops necessary to produce the exploit pattern"). That collides with Lustig's relaxation minimality one paragraph earlier and with ours.
  - "them" has two possible antecedents (the patterns or the graphs).

  → `the smallest programs that induce each pattern~\cite[\S III-B2]{checkmate}`
- [x] **`:8` S1 "Spectre defenses aim to protect some set of architectural state … data-dependent optimization while under speculation."** It is vague, and it is Protean's protection-set idea without a cite, which `:35` now states with the cite. It is also wrong for the three cache defenses. → Delete it; S2 is the topic sentence.
- [x] **`:10` GLIFT.** SPT calls its analysis "novel" (abstract) and borrows only "GLIFT-like ideas" (§1). No later section uses the mechanism. → Delete ", using a dynamic information-flow analysis~\cite{tiwari2009glift} to declassify data as it leaks". To keep "declassify" defined, restore SynthLC's own gloss in the `:35` quote: `safe to declassify (mark public)'' data`.
- [x] **`:12` "InvisiSpec and SpecLFB protect only against speculative loads".** It names no channel, but CleanupSpec's clause does, so it reads as if those two cover every channel. The cites have no pinpoints, and the sentence leaves a widow, "§2.1].". → `All three protect only the data-cache hierarchy: InvisiSpec and SpecLFB from speculative loads~\cite[\S III-B]{yan2018invisispec}, \cite[\S 4]{cheng2024speclfb}, and CleanupSpec from any transient instruction~\cite[\S 2.1]{saileshwar2019cleanupspec}.`

## 🟠 Cut (off-narrative or duplicated)

- [x] **`:22` COND** (never used again; Revizor tests CPUs). → Delete ", while \contract{COND} also follows mispredicted branches~\cite{revizor}".
- [x] **`:24` "Revizor~\cite{revizor} and AMuLeT~\cite{amulet} test hardware … STT against \contract{ARCH-SEQ}."** It repeats intro.tex:110–120 and results.tex:38 (guideline line 78), and Revizor is not simulator work (Caroline v7_8pt:58). → Delete.
- [x] **`:25` SNI and wSNI (2 sentences, about 50 words).** No later section uses them; Caroline v7_8pt:48 says use ARCH-SEQ instead of SNI. → Delete them, and change related.tex:10 "SNI and contracts" → "contracts" (B-4).
- [x] **`:43` the seven-citation MCM list.** → Compress it to one clause, as LCM §2.1 (p.3) does ("a large body of work is devoted to formalizing them [4, 9, 10, …]"): `Such models exist for many hardware and language MCMs~\cite{owens2009x86tso,herdingcats,pulte2018simplifying,batty2011mathematizing,lahav2017repairing,simner2020ifetch,simner2022vm,simner2025exceptions}.` Moving it to Related Work is the alternative. **Fix added (2026-11-16):** if you keep the list as it is, "such as instruction fetch, virtual memory and exceptions" → "i.e., instruction fetch, virtual memory and exceptions" (the list is exactly the three Simner papers, so "such as" is wrong).
- [x] **`:45` the Kodkod cite** duplicates pipeline.tex:27. → "A relational model finder, the Alloy Analyzer~\cite{jackson2002alloy} built on Kodkod~\cite{kodkod}," → "The Alloy Analyzer~\cite{jackson2002alloy}".
- [x] **`:5` S1 "An out-of-order core predicts … to maximize hardware resource utilization."** Nothing later uses it, and "maximize" is not exact. → Delete it.
- [x] **`:47` "Axiomatic models have since been applied to security."** It announces rather than states. → Delete it.
- [x] **`:45`** → "To keep the suite small and every test meaningful" → "To keep suites small"; delete ", so every element is load-bearing to the violation".

## 🟡 Ambiguity and terms

- [x] **"speculative" is never defined but is used about 15 times in three senses:**
  - STT's before the visibility point (`:8`);
  - CleanupSpec's transient (`:12`);
  - "speculative executions" (`:25`).

  At `:5`, replace the transient/sequential sentence with `A \emph{speculative} instruction turns out \emph{transient} (bound to squash) or \emph{sequential} (bound to commit)~\cite{canella2019systematic}.` Protean §II-A (p.3) says "Speculative instructions eventually become transient or sequential".
- [x] **`:5` "speculation primitive": instruction or mechanism?**
  - The paper treats it as an instruction: it "resolves" (`:5`, model.tex:32).
  - "store bypass" is a mechanism.
  - Serberus §2.2.1 defines primitives as prediction sources and cites Canella and Miller.
  - The term is uncited here.

  → `\emph{Speculation primitives} are instructions whose outcome the core predicts~\cite{canella2019systematic}, e.g., a conditional branch, or an older store whose unknown address a younger load bypasses (store bypass~\cite{horn2018ssb}).` This also removes "originate this speculation", the two misprediction parentheticals and "still". (Source note, 2026-11-16: Serberus §2.2.1 credits the term to Canella [20] and Miller's MSRC blog [21], checked in `papers/serberus_sp24.txt`; Canella itself was not opened, so the Canella cite is unverified, and Miller has no bib entry.)
- [x] **"safe" has three meanings:**
  - STT's untainted (`:8`);
  - a load at its visibility point (`:12`, twice);
  - leaked data (`:10`).

  At `:12`: "exposes the load only once it is safe" → "exposes the load at its visibility point"; "installs the line only once the load is safe" → "installs the line once the load reaches its visibility point". SpecLFB uses the term too.
  - **Fix (revised 2026-11-16):** "visibility point" is defined at `:17–18` (InvisiSpec coined it, §V-A; STT §6.1 gives the Spectre-model condition), so the InvisiSpec change stands. SpecLFB never uses the term for its own rule; its LFB refills a line "only when the security check mechanism determines that it is safe" (§6.1, p.637), i.e., once the load is no longer speculative under any of the sources §5 lists (control flow, address speculation, value prediction, other exceptions; p.635). So at `:24` write `installs the line only once the load is no longer speculative~\cite[\S 5]{cheng2024speclfb}`. Optional, for the last "safe": `:20` `lets STT treat that data as safe` → `lets STT untaint that data`.
- [x] **One speculation model, four names:**
  - `:9` "the Spectre model";
  - `:35` "e.g., until all older branches resolve";
  - Fig. 1 "SpectreCtrl";
  - model.tex:52 "the Spectre configuration".

  At `:35` → `(e.g., STT's Spectre model: until all older branches resolve~\cite[\S 6.1]{yu2019stt})`. Then make Fig. 1 and model.tex:52 use the same name (B-6 in the intro list). **Fix added (2026-11-16):** model.tex:55 (was :52) "for the Spectre configuration we test" → "for its Spectre model, which we test".
- [x] **`:55` "combines these ideas" never maps the three clauses.** "Execution contract" echoes Guarnieri's execution mode, but intro.tex:227 glosses it as Protean's speculation model, and nothing here connects them. → `\toolname{}'s specification language (\S~\ref{formalmodel}) combines these ideas.` → `\toolname{}'s leakage contract, execution contract (a speculation model) and protection set adapt these ideas (\S~\ref{sec:leakage-predicate}).`
- [x] **`:55` "Protean states its threat model through speculation models".** The speculation model is only half of Protean's threat model (§II-B1 covers transmitters, §II-B2 speculation), and the term predates Protean (Protean fn. 1 credits SPT, InvisiSpec and STT). → `Protean states its threat model through speculation models, which say when an instruction is speculative` → `Protean's threat model fixes a \emph{speculation model}, which says when an instruction is speculative …~\cite[\S II-B2]{protean}`.
  - **Fix added (2026-11-16): the full sentence, and all of ¶6 with the `:35` items applied** (B-5 rec. B, plus the items on "a single defense", GLIFT's gloss, "unsafe operands", "to refer to", speculation-model names, "may evolve" and the clause mapping; sources as in those items, Protean §II-B2 and §III-B re-read in `papers/protean_hpca26.txt`). Replace all of `:55`, from `Two lines of work describe one design at a time.` through `(\S~\ref{formalmodel}) combines these ideas.`, with (`:54`, B-5's option-A text, stays): `Two lines of work describe one design at a time. SynthLC's leakage contracts list a microarchitecture's transmitters and their unsafe operands, and SynthLC notes that STT and SPT ``have the same fine-grained leakage contract and differ only in their policy for when it [is] safe to declassify (mark public)'' data~\cite[\S II-B]{rtl2upath} (AMuLeT instead uses ``leakage contract'' for a hardware--software security contract~\cite[\S 2.1]{amulet}). Protean's threat model fixes a \emph{speculation model}, which says when an instruction is speculative (e.g., STT's Spectre model: until all older branches resolve~\cite[\S 6.1]{yu2019stt})~\cite[\S II-B2]{protean}. Protean also observes that every Spectre defense implicitly defines, at each program point, a \emph{protection set} of architectural state it promises to keep from leaking transiently, which may evolve as the program executes~\cite[\S III-B]{protean}. \toolname{}'s leakage contract, execution contract (a speculation model) and protection set adapt these ideas (\S~\ref{sec:leakage-predicate}).` Append the threat-model sentence (Missing list) and the speculation-model clause (Missing list) only if you take those items.
- [x] **`:35` the SynthLC quote dangles.** Why does it matter that STT and SPT differ only in declassification? Make the argument explicit by adding Protean's wording after "a \emph{protection set} of architectural state …": `, which may evolve as the program executes~\cite[\S III-B]{protean}` (Protean §III-B, p.4).
- [x] **`:35` "the operands each transmits"** → "their unsafe operands". That is SynthLC's word (§II-B, p.4) and the model's (model.tex:30).
- [ ] **Defense classes: one is named, one isn't.** `:24` now names \emph{invisible-speculation defenses}~\cite[\S 10]{cheng2024speclfb}, and `a8187e4` swapped "footprint" for it everywhere. STT, SPT and ReCon are still unnamed here, though §5 and the Discussion call them "taint-tracking defenses" (pipeline.tex:120, :142, :146; discussion.tex:42). The name is grounded: it is STT's own (Speculative Taint Tracking).
  - `:17` `STT, SPT, and ReCon are Spectre defenses that delay transmitters until their operands are deemed safe.` → `STT, SPT, and ReCon, the \emph{taint-tracking} defenses, delay transmitters until their operands are deemed safe.`
  - `:24` (better suggestion, 2026-11-16; also covers the "memory system" item under *One word per concept*): `let speculative loads execute and instead control their effect on the memory system.` → `let speculative loads execute but hide or undo their effect on the data-cache hierarchy.` "Hide or undo" makes the two mechanisms visibly parallel (Caroline intro:39): InvisiSpec and SpecLFB hide it (speculative buffer, line-fill buffer), CleanupSpec undoes it. "Data-cache hierarchy" is narrower than "memory system" and exact: InvisiSpec §III-B ("any level of a multiprocessor data cache hierarchy … It also includes data TLB state"), CleanupSpec §2.1 (L1-D and L2/LLC; I-cache and TLB excluded), SpecLFB ("We do not consider other speculative side channels, such as TLB"). Then `All three protect only the data-cache hierarchy: InvisiSpec and SpecLFB from speculative loads` → `InvisiSpec and SpecLFB protect it only from speculative loads`, so the hierarchy is not named twice in a row.
- [x] **One word per concept:**
  - "valid" (`:63`), "legal" (`:67`) and "allowed" → "allowed" (LCM §2.1: "allowed (resp. disallowed)"): `decide which candidates are valid` → `decide which candidates are allowed`; `no legal execution of the program` → `no allowed execution of the program`;
  - "memory system" (`:24`): see the better suggestion under *Defense classes* above ("hide or undo their effect on the data-cache hierarchy");
  - "mis-speculation" (`:24`) → "squash": `undoes the changes on a mis-speculation` → `undoes the changes on a squash`;
  - `:17` `every speculative \emph{access} instruction (a load)` → `every speculative load`, and `an access instruction's output once it reaches its` → `a load's output once the load reaches its` (this also removes the ambiguous "it").
- [x] **"adversary model"** (`:38`, `:54`) vs "attacker model" (pipeline.tex:150) vs "observation model" (discussion.tex:26). → Use "adversary model" everywhere (Guarnieri §II-D; Protean §II-C). **Fix added (2026-11-16):** pipeline.tex:150 (was :142) `The attacker model is orthogonal to the specification.` → `The adversary model is orthogonal to the specification.`; discussion.tex:26 `does not filter hits by an attacker's observation model` → `does not filter hits by an adversary model`.
- [x] **Dash in "hardware–software":** `:2` and `:55` use a hyphen; `:35`, `:36`, `:54` and intro.tex:111 use an en dash. → `hardware--software` everywhere: `:2` `the hardware-software security contract vocabulary` → `the hardware--software security contract vocabulary`; `:55` `to refer to a hardware-software security contract` → `to refer to a hardware--software security contract`.
- [x] **`:24` "invisible to the data-cache hierarchy"** → `invisible to the data-cache hierarchy` → `without modifying the cache hierarchy` (InvisiSpec abstract). Caroline intro:39: "what is meant by ``invisible''".
- [x] **Definitions that conflict with model.tex:**
  - transmitter (`:13` vs model.tex:36, "leak one or more operands via a hardware side channel");
  - speculation primitive (`:9` vs model.tex:38, "initiate speculative executions");
  - protection set (`:55`, "keep from leaking transiently", vs model.tex:40, "not leak architecturally and/or speculatively"; this one is a contradiction).

  → Keep the Background definitions, cut the parentheticals: model.tex:36 delete ` (instructions that leak one or more operands via a hardware side channel)`; model.tex:38 delete ` (instructions that initiate speculative executions, e.g., a conditional branch)`; model.tex:40 `not leak architecturally and/or speculatively` → `not leak transiently`.
- [x] **Contract granularity contradicts itself** (rewritten 2026-11-16). The intro (`intro.tex:129–131`, live) says AMuLeT's contracts characterize leakage "at the instruction level (e.g., certain instructions expose certain operands)", while Background `:60` and results.tex:38 say a contract covers "what a whole program may expose". Both are half right: the observer mode is per instruction (`:36` already says "what architectural state each execution step exposes"), and the upholds condition compares two whole executions (`:44` already says so). So only the two "whole program" phrases need to change; the intro stays. → (1) `:60` `Hardware--software security contracts constrain what state a whole program may expose, compared across two executions, and their adversary model is a projection of microarchitectural state` → `A contract's adversary model is a projection of microarchitectural state` (the cut clause repeats `:44`; the paragraph's point is the projection). (2) results.tex:38 `Such a contract states what a whole program may expose along its sequential execution, which is coarser` → `Such a contract states what each instruction on the program's sequential path may expose, which is coarser` (SEQ observes only the sequential path, as `:36` says; the rest of the sentence, "neither which instructions the defense must hold back nor which state the defense claims to protect", still holds).
- [x] **`:45` Lustig defines minimality on tests, not graphs** (§3.1, p.3: "at least one forbidden outcome that becomes observable under every instruction relaxation"). → `generate only \emph{minimal} tests: every \emph{relaxation}, such as removing an instruction or a dependency or weakening a fence, makes the forbidden outcome observable~\cite[\S 3.1]{lustig}`. *(2026-11-16: already applied in a0ae7e4 (`:74`); tick.)*
- [x] **`:38` "(\contract{CT-SEQ})" and "(transmits)"** → `\contract{ARCH-SEQ} (\contract{CT-SEQ})` → `\contract{ARCH-SEQ} (resp.\ \contract{CT-SEQ})` and `accesses (transmits)` → `accesses (resp.\ transmits)` (Protean §II-C, p.3).
- [x] **Merge ¶7 and ¶8** (same goal: synthesis lineage). Delete the blank line at `:66`, between the commented `% Such models exist for hardware MCMs` line and `A memory consistency \emph{litmus test}`. ¶2 gets a topic sentence once its S1 is cut (🟠) and the primitive sentence leads.
- [x] **rf means two things (added 2026-11-16).** `:63` gives the MCM meaning, "reads-from (rf), which relates a write to each read that sees its value" (same-address memory events only, LCM §2.1.2, p.3), but model.tex:28 uses rf for "an output operand to an input operand of a later instruction on the same location", register or memory. A reader fresh from Background will assume the MCM meaning; the [Note] at model.tex:29 asks for the same fix. → model.tex:28 `an input operand of a later instruction on the same location` → `an input operand of a later instruction on the same register or memory location (an MCM's rf relates only memory events, \S~\ref{sec:bg-axiomatic})`.

## ⚪ Nitpicks

- [x] `:2` roadmap: "protocols" is the wrong noun, and "borrows" appears twice. → `This section introduces the Spectre defenses we test (\S~\ref{sec:bg-defenses}), the hardware-software security contract vocabulary our specification language borrows (\S~\ref{sec:bg-contracts}), and the axiomatic models and minimal litmus-test synthesis protocols our synthesizer borrows from memory consistency research (\S~\ref{sec:bg-axiomatic}).` → `This section covers the Spectre defenses we test (\S~\ref{sec:bg-defenses}), the contract vocabulary our specification language reuses (\S~\ref{sec:bg-contracts}), and the axiomatic models and minimal litmus tests our synthesizer builds on (\S~\ref{sec:bg-axiomatic}).`
- [ ] `:10` `instructions that are not squashed \emph{commit}` → `the rest \emph{commit}`.NO
- [x] `:10` (added 2026-11-16) `When a speculation primitive \textit{resolves} as mispredicted` → `When a primitive \textit{resolves} as mispredicted` (the term was defined one sentence earlier).
- [ ] `:13` (added 2026-11-16, optional) `A \emph{transmitter} is an instruction that modulates` → `A \emph{transmitter} modulates`. Skip it if you want the definition to name its genus (instruction).
- [ ] `:17` `STT, SPT, and ReCon are Spectre defenses that delay` → `STT, SPT, and ReCon delay` (if you skip the class-name item).
- [x] `:19` `delays a transmitter only until` → `delays a transmitter until`.
- [x] `:38` `A separate \emph{adversary model}` → `An \emph{adversary model}~\cite[\S II-D]{guarnieri2021contracts}`. Also `the tags of the data cache and TLB~\cite{amulet}` → `L1D and D-TLB tags~\cite[\S 3.2]{amulet}`, which is AMuLeT's exact trace.
- [ ] `:38` delete `A contract is named by its pair, e.g., \contract{CT-SEQ}.`
- [x] `:36` (added 2026-11-16) `\contract{ARCH} additionally exposes every value loaded from memory` → `\contract{ARCH} also exposes every loaded value`.
- [x] `:40` cut the second "aims to uphold" and add the pinpoint: `and SPT~\cite{spt} aims to uphold \contract{CT-SEQ}~\cite{protean}` → `and SPT~\cite{spt} \contract{CT-SEQ}~\cite[\S II-C]{protean}`.
- [ ] `:43`, only if B-4 goes B:
  - SNI's CT-SEQ form is Guarnieri Def. 5 (p.6), not Spectector → `Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant` → `Speculative non-interference (SNI)~\cite[Def.~5]{guarnieri2021contracts} and its variant`;
  - ~~"under the contract" has no antecedent → "under a contract"; *(2026-11-16: already applied in a0ae7e4 (`:43` reads `its observations under a contract`); tick this sub-bullet.)*~~ (done)
  - `are the matching program properties` → `are the corresponding program properties`.
- [x] `:55` `to refer to a hardware-software security contract` → `for a hardware-software security contract`.
- [x] `:63` (added 2026-11-16) `Prior work uses axiomatic models to specify which executions a memory consistency model (MCM) allows.` → `Axiomatic models specify which executions a memory consistency model (MCM) allows.` ("Prior work" is a vague subject.)
- [ ] `:67` `A memory consistency \emph{litmus test} is a short single-/multi-threaded program with a final outcome, the test being forbidden if no legal execution of the program produces the outcome.` → `A \emph{litmus test} is a short program with an outcome, forbidden if no allowed execution of the program produces it.` (This cuts "memory consistency", "single-/multi-threaded", "final" and "the test being".)
- [x] `:82` split the 50-word sentence: `pipeline, and leakage containment models (LCMs)~\cite{lcms} formalize` → `pipeline. Leakage containment models (LCMs)~\cite[\S 2]{lcms} formalize`.
- [x] Pinpoints still missing (`:36`–`:38`): after `the paths along which the program exposes it` add `~\cite[\S III-B]{guarnieri2021contracts}` (modes); after `\emph{violates} it otherwise` add `~\cite[Def.~1]{guarnieri2021contracts}` (upholds).
- [x] `:62` `\subsection{Axiomatic Execution Models}` → `\subsection{Axiomatic Models and Litmus Tests}` (matches related.tex:12).
- [ ] Dead comments: delete the `%` lines, now at `:6–8`, `:11`, `:14`, `:16`, `:20–21`, `:26`, `:28–29`, `:31–32`, `:37`, `:39`, `:41–42`, `:44`, `:46`, `:48`, `:50`, `:52`, `:65`, `:68`, `:71`, `:73`, `:75`, `:77`, `:79–80` and `:83` (no PDF effect). Keep `:58` (`% Justify here (decision B-5)`) until B-5 is decided.
- [ ] Widows on pp.3–4. The items above remove all five:
  - "ory consistency research (§ 2.3)." (roadmap);
  - "§2.1]." (`:12`);
  - "beyond its ARCH-SEQ observations." (`:25`);
  - "combines these ideas." (`:35`);
  - "is load-bearing to the violation." (`:45`).
- [ ] Table 1 on p.4 (`tikz/execvocab_v3_8pt.tex`), about 3 lines:
  - `:22` `\renewcommand{\arraystretch}{1.2}%` → `\renewcommand{\arraystretch}{1.0}%`;
  - `:5` delete the caption's second sentence, ` Only the three clauses (execution contract, protection set, leakage contract) differ between defenses.` (model.tex:9 says it), which takes the bold caption from 4 lines to 2.
  - (added 2026-11-16) The opening that says it is now model.tex:9 ("It has three clauses …"). Optional, only if you accept touching float spacing: after `\end{tabular}%` (`tikz/execvocab_v3_8pt.tex:32`) add `\vspace{-4pt}`, which removes part of the 2.5 blank lines under the table.

## Missing from Background (only gaps a later section needs)

- [x] **Speculation models, and which one each tested build uses.** *Done 2026-11-16 (`1f76d11`): `:22` defines both models (STT §6.1); results.tex:26 says the STT and SPT implementations run in their Spectre models and AMuLeT's STT and InvisiSpec builds in their Futuristic models (AMuLeT §4.1). SPT: `SpectreSafeFence`, and SPT's paper defines Spectre and Futuristic models. ReCon is left out: its build (`--scheme=2`) uses control and store shadows (EVAL_MANIFEST E2/E6), which is neither model.*
  - Where: the `:55` Protean sentence (item above).
  - Why: model.tex:54 says "the Spectre configuration we test"; discussion.tex:10 says "Threat models differ"; and Results compares against AMuLeT, which ran InvisiSpec and STT in Futuristic mode (AMuLeT §3.1, p.5; §4.1: "For InvisiSpec and STT, we run them in their Futuristic mode").
  - Cite: STT §6.1, p.5: Spectre = "all older control-flow instructions have resolved"; Futuristic = "cannot be squashed".
  - Text: `(e.g., until all older branches resolve)` → `(e.g., in STT's Spectre model, until all older branches resolve; in its Futuristic model, until it can no longer squash~\cite[\S 6.1]{yu2019stt})`, plus one clause naming the model of each tested build. You supply those facts; only STT's is stated anywhere (model.tex:54).
  - **Fix added (2026-11-16): the facts, from the run configs and simspect docs (confirm before pasting).** InvisiSpec runs in its Futuristic model, as in AMuLeT (`runconfigs/firstdet_final_20261110/T1g_*.jsonc`: `--scheme=FuturisticSafeInvisibleSpec`, `threat_model=Futuristic`). STT runs in its Spectre model (`wiki/state/EVAL_MANIFEST.md` row E3: "our glue sets Spectre"). SPT runs as `SpectreSafeFence` (`runconfigs/fixed_20261030/SPT_6_oneLP_fence_fixed_latest.jsonc`); that this is SPT's Spectre model is read from the scheme name (unverified). CleanupSpec and SpecLFB take no mode flag (`T2g_*`, `T3g_*`): CleanupSpec undoes any transient instruction's changes (§2.1, p.3), and SpecLFB protects loads behind unresolved branches, store addresses and possible exceptions (§5, pp.635–636). ReCon: unverified (EVAL_MANIFEST row E2 says scheme 2 of that tree uses control and store shadows). Text: `We test STT and SPT in their Spectre models, and InvisiSpec, as AMuLeT does~\cite[\S 4.1]{amulet}, in its Futuristic model.` This also answers reviewer Q1: the AMuLeT comparison (results.tex:74) runs only InvisiSpec, CleanupSpec and SpecLFB, and InvisiSpec's mode matches AMuLeT's.
- [x] **A threat-model sentence.**
  - Where: the end of ¶6, after `(\S~\ref{formalmodel}) combines these ideas.` (`:55`).
  - Why: pipeline.tex:150 says "detection needs no attacker … The attacker model is orthogonal"; discussion.tex:26 says there is no observation-model filtering; the intro claims "no attacker or probe".
  - Precedent: Protean §II-B (p.3), Helium §III-A (p.3), Serberus §2.3.
  - Text: `\toolname{} adopts each defense's own threat model: its leakage contract fixes the transmitters, and its execution contract the speculation.`
- [x] **Transmitter assumptions: what transmits, and when.**
  - Where: the `:13` transmitter example.
  - Why: model.tex:54 gives STT's leakage contract as "(load, address) and (branch, condition)"; pipeline.tex:142 has per-kind transmission criteria; the Results bugs use branch transmitters.
  - Cite: Protean §II-B1, p.3.
  - Text: `e.g., a load transmits its address by changing cache timing` → `e.g., a load transmits its address when it executes, and a branch its condition when it resolves~\cite[\S II-B1]{protean}`.
- [x] **Candidate-execution structure (event structure plus execution witness, LCM §2.1.1–2.1.2, p.3).** Needed only if B-10 goes B.
- Checked and not needed:
  - upholds/violates vs our "violates": model.tex:44 already contrasts them and points to §2.2;
  - store-to-load forwarding: results.tex:52 explains it and cites STT §6.4.2;
  - MSHR, RMW, `commitToIEWDelay` and squash propagation to issue: explained where Results and Discussion use them;
  - line-fill buffer and visibility point: already in ¶3–¶4;
  - Spectre-vs-Meltdown scope: the title and intro fix it.

## Decisions (recommendation first)

- [ ] **B-1 (unchanged): the names of a contract's two components.**
  - Rec.: observer mode and execution mode, as Fig. 1 v9 and the current text use.
  - Alternative: Caroline's visible v7_8pt:48, "leakage contract + execution contract".

  "Leakage contract" already has two senses in `:55` (SynthLC's and AMuLeT's).

  Text change per option (added 2026-11-16). Rec.: none beyond the pinpoint: after `the paths along which the program exposes it` (`:36`) add `~\cite[\S III-B]{guarnieri2021contracts}`. Alternative: at `:36`, `an \emph{observer mode}` → `a \emph{leakage contract}`, `an \emph{execution mode}` → `an \emph{execution contract}`, `Two observer modes` → `Two leakage contracts`, `The \contract{SEQ} execution mode` → `The \contract{SEQ} execution contract`; and Fig. 1 (`tikz/intro_threelayer_v9.tex:47`) `(Observer Mode, Execution Mode)` → `(Leakage Contract, Execution Contract)`, which then repeats two of the three names in the Defense Specification box (`:58`).
- [ ] **B-3 (unchanged): the CT definition.**
  - Rec.: Protean's "CT exposes all unsafe transmitter operands" (§II-C, p.3), which matches the "unsafe operands" proposed for `:55`.
  - Alternative: Guarnieri's PC + load/store addresses (current).
  - Text change per option (added 2026-11-16). Rec.: `:36` `\contract{CT} exposes the program counter and the addresses of loads and stores, modeling constant-time code` → `\contract{CT} exposes all unsafe transmitter operands~\cite[\S II-C]{protean}, modeling constant-time code` (Protean §II-C, p.3, re-read: "CT exposes all unsafe transmitter operands and thus models the assumption of constant-time code"). Alternative: keep the text and add `\cite[\S III-B]{guarnieri2021contracts}` after `the addresses of loads and stores`.
- [ ] **B-4 (updated): SNI and wSNI.**
  - Rec. A: delete `:43` and Fig. 1's gloss, and change related.tex:10 "SNI and contracts" → "contracts" (Caroline v7_8pt:48).
  - B: keep them, since your guideline line 119 says to cite SNI to Spectector. Then fix Fig. 1 to "formalizes transient non-interference" (Guarnieri p.4) and apply the `:43` nits.
  - Text change per option (added 2026-11-16). A: delete all of `:43`, from `Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant` through `makes every program weakly SNI.` (now one sentence); Fig. 1 (`tikz/intro_threelayer_v9.tex:47`) `\textit{e.g., (\contract{ARCH}, \contract{SEQ}), which guarantees weak speculative non-interference}~\cite{guarnieri2021contracts}` → `\textit{e.g., \contract{ARCH-SEQ}}~\cite{guarnieri2021contracts}`; related.tex:10 `and SNI and contracts (\S~\ref{sec:bg-contracts})` → `and contracts (\S~\ref{sec:bg-contracts})`. B: keep `:43` with the `:43` nitpick fixes; Fig. 1:47 `\textit{e.g., (\contract{ARCH}, \contract{SEQ}), which guarantees weak speculative non-interference}~\cite{guarnieri2021contracts}` → `\textit{e.g., \contract{ARCH-SEQ}, which formalizes transient non-interference}~\cite{guarnieri2021contracts}` (Guarnieri p.4, re-read: ARCH-SEQ "is a simple and clean formulation of the idea behind transient noninterference").
- [x] **B-5 (updated): where intro.tex:136's "No instruction-level contract can capture such a guarantee exactly" is justified.** *(done 2026-11-16: Anna took option A, justifying it in Background: the adversary model is a projection of state, so it cannot tell which instruction changed it; STT's stores and A-KV3 as the example; intro sentence rewritten to match)*
  - Rec. B: delete `:35` S1 and repoint intro.tex:136 to `\S~\ref{sec:known-bugs}`, where results.tex:35–38 already argue it. This also keeps the AMuLeT contrast to three places (guideline line 78).
  - A: keep `:35` S1 but make it cited: `A contract compares two whole executions, and its adversary model observes microarchitectural state, not which transmitter changed it~\cite[\S II-D]{guarnieri2021contracts}.`

  Either way, "No" is a universal claim. Guarnieri §II-D lets an adversary model project onto one structure, so consider "No standard contract". Text change for that (added 2026-11-16, either option): intro.tex:135 "No instruction-level contract can capture such a guarantee exactly" → "No standard instruction-level contract can capture such a guarantee exactly".
- [x] **B-10 (new): "candidate execution" at `:63`.** *Resolved 2026-11-16 (`1f76d11`) with a third option: keep `:76`'s one-sentence definition and the §3.1 title, and tie them in §3.1 ("Like an MCM's candidate execution (§2.3), an execution graph …"); no event structure or witness. The LCM-framing [Note] in model.tex is deleted.*
  - Rec. A: drop the term ("An execution graph of a program connects its memory events …") and retitle model §3.1 "Execution Graphs". This introduces the fewest concepts, and it answers your \anna at model.tex:20.
  - B: follow the deaf190 [Note] in model.tex. Define a candidate execution LCM's way here (event structure + execution witness, LCM §2.1; about 30 more words), and present §3.1's execution graph as SimSpect's candidate execution.
  - Changed since the review (added 2026-11-16): model §3.1 is now titled "Candidate Executions" (model.tex:21), so B matches the current title, A would undo that retitle, and the term is no longer unused after `:63`.
  - Text change per option (added 2026-11-16). A: `:63` S3 `A \emph{candidate execution} of a program is an execution graph of its memory events connected by relations such as program order (po) and reads-from (rf), which relates a write to each read that sees its value.` → `An \emph{execution graph} of a program connects its memory events by relations such as program order (po) and reads-from (rf), which relates a write to each read that sees its value.`; S4 `decide which candidates are valid` → `decide which execution graphs are allowed`; model.tex:21 `\subsection{Candidate Executions}` → `\subsection{Execution Graphs}`. B: `:63` S3 (same old text) → `A \emph{candidate execution} of a program combines an \emph{event structure}, the memory events of one control-flow path with every branch resolved, ordered by program order (po), with an \emph{execution witness} of relations such as reads-from (rf), which relates each write to the same-address reads that read from it~\cite[\S 2.1]{lcms}.` (LCM §2.1.1–2.1.2, p.3, re-read; about 13 words more than now); S4 `decide which candidates are valid` → `decide which candidate executions are allowed`; keep model.tex:21's title.
- B-2 is resolved by `:35`'s current wording, but PAPER_AUDIT_GUIDELINES.md:118 still prescribes "a defense's own fine-grained statement". Update the guideline so later audits don't push the old wording back. B-6 (Fig. 1's STT example) stays in the intro list; B-9 and DECIDE 8 are resolved. Concrete guideline edit (added 2026-11-16): in PAPER_AUDIT_GUIDELINES.md:118, "a defense's own fine-grained statement of which instructions transmit which operands" → "SynthLC's leakage contracts list a microarchitecture's transmitters and their unsafe operands (RTL2MµPATH §II-B, p.4); ours lists the (transmitter, unsafe operand) pairs a defense recognizes (model.tex:36)".

## Not carried over (2026-11-16)

- Review item 58 (cross-reference format, e.g./i.e. commas): already conform in `background.tex`; its two vague ref targets are fixed by the `:35` clause-mapping item and the `:47` CheckMate item.
- Section and subsection skips on p.3 (review §7): acmart defaults, and the review says to leave them.
- `:22` "violates" vs §3.2's "violates the leakage predicate": the review marks it handled, since model.tex:50 (was :44) states the difference.
- B-6 (Fig. 1's STT example and "SpectreCtrl"): tracked in REVIEW_ACTION_ITEMS_INTRO.md (Fig. 1 line-60 item).
- B-9 (NDA, SpecShield) and DECIDE 8 ("transient" = bound to squash): resolved before this review; `background.tex:23` keeps them commented out and `:5` uses bound-to-squash.

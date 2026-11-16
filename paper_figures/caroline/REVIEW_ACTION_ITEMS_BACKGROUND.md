# Review action items: Background (§2)

Coverage (2026-11-16 08:25, ISCA-27 `9e48df1`; background.tex unchanged since `d6b0d78`): the previous list had 14 open items; 10 are still live and folded in below, 4 are dropped (end of file). This pass adds 17 problems (marked *new*). Every problem in [reviews/2026-11-16_0825_background.md](reviews/2026-11-16_0825_background.md) (W1–W5, Q1–Q3, items 1–14, B-4 update) has an item here: 16 items (🔴 2, 🟠 5, 🟡 4, ⚪ 5), 7 possible cuts (about 7 lines, about 10 with B-4 A), 3 decisions.

Targeted fixes only. Each fix quotes the current text (`old` → `new`); line numbers are `sections/background.tex` hints. Rendered Background: about 1,229 words now, about 1,150 after every item (Protean §II about 790, Helium §II about 700). Index: [REVIEWS.md](REVIEWS.md).

## 🔴 Unsupported or overclaimed

- [ ] *new* `:49` the corollary is not in Guarnieri et al.: Def. 4 (p.6) defines wSNI of a program relative to a contract, and nothing says an ARCH-SEQ CPU "makes every program weakly SNI". Delete `, so a CPU that upholds \contract{ARCH-SEQ} makes every program weakly SNI` (under either B-4 option), so the sentence ends at `…beyond its \contract{ARCH-SEQ} observations.`
- [ ] *new* `:60` three problems in one sentence: STT's store exclusion is uncited (STT §7.3: "we assume stores are performed at retirement"); "standard contracts" is never defined, and intro.tex:140 relies on it; "reports" claims it always happens, and "never claimed to block" is pointed. `such as STT's, whose transmitters exclude stores,` → `such as STT's, whose transmitters exclude stores~\cite[\S 7.3]{yu2019stt},`; `therefore has no exact counterpart among the standard contracts,` → `therefore matches no contract built from these modes,`; `and testing against one reports leaks the defense never claimed to block` → `and testing against one can report leaks outside the guarantee`.

## 🟠 Structure and terms

- [ ] *new* `:10` "speculation primitive" now has two senses. `:9` defines primitives as "sources of control- and data-flow prediction" (Serberus), which do not "resolve"; §3.1's resolved flag and pipeline.tex:45 ("realizes the graph's speculation primitives") use the instruction sense. Re-raised although you declined "a primitive" last pass, because `:9`'s definition changed since. `When a speculation primitive \textit{resolves} as mispredicted` → `When a predicted instruction \textit{resolves} as mispredicted`.
- [ ] *new* ¶5 has two goals: the projection argument (`:60`) belongs to the contracts paragraph, and "Two lines of work" is a topic sentence stuck mid-paragraph. Delete the blank lines between `makes every program weakly SNI.` and `A contract's adversary model is a projection` (lines 50–59 hold only comments), and put a blank line before `Two lines of work describe one design at a time.` No line cost.
- [ ] *new* The adversary model is defined twice, at `:44` and `:60` (see cut C1). `An \emph{adversary model}~\cite[\S II-D]{guarnieri2021contracts} defines which microarchitectural state the attacker observes, e.g., L1D and D-TLB tags~\cite[\S 3.2]{amulet}.` → `An \emph{adversary model}~\cite[\S II-D]{guarnieri2021contracts} is the projection of microarchitectural state the attacker observes, e.g., L1D and D-TLB tags~\cite[\S 3.2]{amulet}.`; delete `A contract's adversary model is a projection of microarchitectural state, e.g., the cache tags~\cite[\S II-D]{guarnieri2021contracts}. `; `A projection of state cannot tell which instruction changed it:` → `Such a projection cannot tell which instruction changed the state:` (Guarnieri §II-D: "We model hardware observations as projections to parts of the microarchitectural state").
- [ ] *new* `:63–66` one 70-word sentence with two claims. `~\cite[\S II-B]{protean},` followed on `:66` by `and observes that every Spectre defense implicitly defines` → `~\cite[\S II-B]{protean}. Protean also observes that every Spectre defense implicitly defines`.
- [ ] *new* Oxford commas. `:68` `execution contract (a speculation model) and protection set` → `execution contract (a speculation model), and protection set`; `:94` `bounded enumeration and relaxation-based minimality` → `bounded enumeration, and relaxation-based minimality`.

## 🟡 Pinpoints and wording

- [ ] *new* `:9` pinpoint (Serberus §2.2.1, p.3: "distinct sources of control- and data-flow (mis)prediction … called speculation primitives"). `~\cite{miller2018mitigating,mosier2024serberus}` → `~\cite{miller2018mitigating}, \cite[\S 2.2.1]{mosier2024serberus}`.
- [ ] *new* `:76` pinpoint (LCM §2.1, p.3: "MCMs define the value(s) that can be legally returned by shared-memory loads in a parallel program"). `may return~\cite{lcms}` → `may return~\cite[\S 2.1]{lcms}`.
- [ ] *new* `:22` vs `:64`: STT's Spectre model is "all older control-flow instructions have resolved" (STT §6.1) at `:22` and "until all older branches resolve" at `:64`. Cut C6 removes the second; otherwise `(e.g., STT's Spectre model: until all older branches resolve` → `(e.g., STT's Spectre model: until all older control-flow instructions resolve`.
- [ ] *new* `:5` uses "checked", `:10` "resolves" for the same event. `before each prediction is checked` → `before each prediction resolves`.

## ⚪ Layout, cross-section and housekeeping

- [ ] Widows on p.3 (updated). "on (§ 2.3)." (roadmap): `and the axiomatic models and minimal litmus tests` → `and the axiomatic models and litmus tests` (§2.3 defines minimality itself); "model." (end of `:68`): the `:63–66` split and cut C1 reflow it; "instruction [125, §2.1]." (`:31`): no fix proposed.
- [ ] `:13` optional: `A \emph{transmitter} is an instruction that modulates` → `A \emph{transmitter} modulates` (skip if you want the definition to name its genus).
- [ ] Dead comments: delete the `%` lines (now `:6–8`, `:11`, `:14`, `:16`, `:18`, `:20`, `:24–25`, `:30`, `:32`, `:34–35`, `:37–38`, `:43`, `:45`, `:47–48`, `:50`, `:52`, `:54`, `:56`, `:58`, `:62`, `:65`, `:67`, `:71`, `:78`, `:80`, `:83`, `:85`, `:87`, `:89`, `:91–92`, `:95`). No PDF effect. `:71` (`% Justify here (decision B-5)`) can go too: B-5 is decided.
- [ ] *new* Cross-section, for the Synthesizer items: pipeline.tex:45 `Pass~3 realizes the graph's speculation primitives` uses the instruction sense of the term (see the `:10` item); `the graph's speculation primitives` → `the graph's unresolved branches and stores`, or leave it if you take the `:10` fix and accept both senses.
- [ ] Guideline, not paper: PAPER_AUDIT_GUIDELINES.md:118 still prescribes "a defense's own fine-grained statement of which instructions transmit which operands", which the text no longer uses. "a defense's own fine-grained statement of which instructions transmit which operands" → "SynthLC's leakage contracts list a microarchitecture's transmitters and their unsafe operands (RTL2MµPATH §II-B, p.3); ours lists the (transmitter, unsafe operand) pairs a defense recognizes (model.tex:37)".

## 🟢 Possible cuts (about 7 lines; about 10 with B-4 A)

- [ ] C1, adversary model defined once, about 1.5 lines: the `:44`/`:60` item above.
- [ ] C2, `:44`, about 0.7 line. Delete `A contract is named by its pair, e.g., \contract{CT-SEQ}.` (the names are self-explanatory at first use, `:44` "ARCH-SEQ (resp. CT-SEQ)").
- [ ] C3, `:76`, about 1 line. Delete `, typically the acyclicity or irreflexivity of combinations of such relations,` (no later section uses acyclicity; model.tex:49 needs only "consistency predicate").
- [ ] C4, `:77`, about 1.5 lines. Delete `Such models formalize many hardware and language MCMs~\cite{owens2009x86tso,herdingcats,pulte2018simplifying,batty2011mathematizing,lahav2017repairing,simner2020ifetch,simner2022vm,simner2025exceptions}.` and add the eight cites to related.tex's "Axiomatic models and litmus tests" paragraph (no later section uses the sentence; you compressed it last pass, so this is optional).
- [ ] C5, `:79`, about 1 line. `A memory consistency \emph{litmus test} is a short single-/multi-threaded program with a final outcome, the test being forbidden if no allowed execution of the program produces the outcome.` → `A \emph{litmus test} is a short program with an outcome, forbidden if no allowed execution of the program produces it.`
- [ ] C6, `:64`, about 0.5 line: the Spectre model is defined at `:22`. `(e.g., STT's Spectre model: until all older branches resolve~\cite[\S 6.1]{yu2019stt})` → `(e.g., STT's Spectre model, \S~\ref{sec:bg-defenses})`.
- [ ] C7, B-4 A: delete all of `:49`, about 3 more lines (see Decisions).

## Decisions (recommendation first)

- [ ] **B-1: the names of a contract's two components.** Rec.: observer mode and execution mode, as now (Fig. 1 v9 uses them). Alternative (Caroline's visible v7_8pt:48): leakage contract + execution contract, i.e., `:42` `an \emph{observer mode}` → `a \emph{leakage contract}`, `an \emph{execution mode}` → `an \emph{execution contract}`, `Two observer modes` → `Two leakage contracts`, `The \contract{SEQ} execution mode` → `The \contract{SEQ} execution contract`, and Fig. 1 line 47 `(Observer Mode, Execution Mode)` → `(Leakage Contract, Execution Contract)`; this repeats two of the Defense Specification box's three names and gives "leakage contract" a third sense next to `:61`'s two.
- [ ] **B-3: the CT definition.** Rec.: Protean's, `:42` `\contract{CT} exposes the program counter and the addresses of loads and stores, modeling constant-time code` → `\contract{CT} exposes all unsafe transmitter operands~\cite[\S II-C]{protean}, modeling constant-time code` (Protean §II-C p.3: "CT exposes all unsafe transmitter operands and thus models the assumption of constant-time code"). Alternative: keep Guarnieri's and add `\cite[\S III-B]{guarnieri2021contracts}` after `the addresses of loads and stores`. Interacts with INTRO F-1: if Fig. 1 keeps "CT with conditions", the current CT definition (which names stores) contradicts STT's leakage contract.
- [ ] **B-4 (updated): SNI and wSNI.** The 🔴 `:49` item removes the unsupported corollary under either option. A (rec.; Caroline v7_8pt:48, fewest concepts): delete all of `:49` from `Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant weak SNI` through `observations.`, use INTRO's Fig. 1 line 47 second form (`\textit{e.g., \contract{ARCH-SEQ}}`), and related.tex:10 `and SNI and contracts (\S~\ref{sec:bg-contracts})` → `and contracts (\S~\ref{sec:bg-contracts})`. B: keep `:49` without the corollary and `are the matching program properties` → `are the corresponding program properties`.

## Not carried over

- `:10` `instructions that are not squashed \emph{commit}` → `the rest \emph{commit}`: you marked it NO.
- `:17` "STT, SPT, and ReCon are Spectre defenses that delay" → "…delay": moot, the class name is applied ("the \emph{taint-tracking} defenses").
- B-4 B's sub-nit "cite SNI as Guarnieri Def. 5": conflicts with your guideline §5 (SNI cites Spectector, the original), and Guarnieri's Def. 5 itself credits Spectector [11].
- Table 1 whitespace (three items): done (`\arraystretch` 1.0, one-sentence caption, `\vspace{-4pt}`).
- Wordings ticked last pass but not applied ("Prior work uses axiomatic models", "hide or undo", "InvisiSpec and SpecLFB protect it only"): treated as declined and not re-raised.
- Fig. 1 line 47 ("(ARCH, SEQ) … weak speculative non-interference"): tracked once, in REVIEW_ACTION_ITEMS_INTRO.md 🔴.
- Checked and clean: every e.g./i.e. has its comma and the right word; cross-references and cite ties conform; no `\caroline{}` in background.tex.

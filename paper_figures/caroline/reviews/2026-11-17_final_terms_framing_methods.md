## 2026-11-17 02:10 — whole paper: terminology, framing, clean methods (ISCA-27 ef1784e)

Scope: three checks (A terminology, B framing, C clean methods/results), on ISCA-27 HEAD `ef1784e` with a clean working tree. Old text is quoted verbatim from live (uncommented) lines. Each quoted string was grep-checked: it is unique among live lines, but several also appear in the commented-out copy directly above the live line (pipeline.tex :31/:33, :59/:60, :72/:73, :81/:82, :114/:115, :119/:120, :151/:152 (copy below :120); model.tex :64/:66; results.tex :73/:75); edit the live line. Not re-flagged (settled): Fig. 1, "three components", microarchitectural state, `\S\ref` without tilde, the abstract, Protean's bug = timing leak, page fit.

**Status of tonight's earlier findings: none is fixed.** HEAD is still `ef1784e` (the commit all three earlier passes reviewed) and `git status` is clean, so every define-before-use item (new-criteria R1–R13, S1, S3–S5, S7, S16) and every banned-term item (S6, S11, G3–G5, G9–G12, G16; old-criteria O4, F2b, the §5/§6 TERM lines) is still live, verbatim. A re-scan of live lines confirms it: "prototype" noun at intro.tex:55 and :310; "candidate execution" for ours at model.tex:16 and :30; "status" and "annotated" at model.tex:34; "Flags" at model.tex:38 and execvocab; "speculation conditions" and undefined "transmission criterion" at intro.tex:310; "minimal violating" at intro.tex:279; "store shadows" and "our STT model" at results.tex:63 and :75; "corpus", "corpora", "re-concretizations" and "branch-stall" at results.tex:100; "wrong-path"/"wrong path" at intro.tex:324, pipeline.tex:152, results.tex:94; "squash lands" at pipeline.tex:152 and the Fig. 9 caption; "ReCon-STT" at tikz/reconstl_v6_8pt.tex:219; "grows" at pipeline.tex:10; "previously known bug" at results.tex:100 (twice) and the Fig. 10 caption; "Unknown Bugs" heading at results.tex:48; "underlying implementation" at intro.tex:321. Clean: no live "clause", "security contract" in body prose outside Background's heading and first sentence (D-4 still open), "checker" in prose, "speculative window", "model for specification", "stall" in prose other than results.tex:100. This file does not repeat those fixes; it gives only new ones.

### A. Terminology

Define-before-use table, in reading order (intro first; abstract excluded because it is locked). "Def" = the first defining clause. Verdicts: ok / **use before def** / **parenthetical** / **variant** / **undefined**.

| term | first use | def | verdict |
|---|---|---|---|
| Spectre attack, misprediction, hardware side channel | intro:10–11 | cite spectre | ok |
| transient / architecturally / committed | intro:11 | intro:11, in parentheses | **parenthetical** (R3, live) |
| architectural state | intro:12 | standard | ok |
| security guarantee | intro:20 | "natural-language", §3.2 pointer | ok |
| delay / taint-track "until they are safe" | intro:40–42 | cites; "safe" never defined in the intro | ok (low) |
| speculative updates to microarchitectural structures | intro:45 | by context | ok |
| prototyped (verb) | intro:52 | allowed | ok |
| undefended baseline microarchitecture | intro:54 | Caroline's term | ok |
| prototypes (noun) | intro:55, :310 | — | **variant** (S5, live) |
| simulated Spectre defense | intro:77 | never stated | **undefined** (S5, live) |
| targeted tests | intro:91 | "that attempt transient leakage" | ok (see B2) |
| hardware-software security contract | intro:128 | cite + §2.2 | ok |
| contract observations | intro:131 | Background :47 (observer mode) | ok (cited) |
| adversary model, contract violation | intro:136–137 | in-sentence | ok |
| violations (contract sense) | intro:143 | intro:137 | variant of "contract violation" (S4, live) |
| transmitter | intro:157 | appositive + cite DAWG | ok; Background :16 defines it again |
| out-of-scope bug reports | intro:167 | by context (outside the guarantee) | ok |
| security litmus test | intro:255 | in-sentence + cite CheckMate | ok |
| target execution | intro:255 | contents at intro:301, full def pipeline:73 | ok (contents follow in the intro) |
| leakage predicate | intro:274 | intro:274 | ok |
| execution graph, happens-before | intro:274 | intro:274 + cite lamport-hb | ok |
| in-flight, unresolved, microarchitectural state (labels) | intro:276–278 | standard / intro:276 | ok |
| solver (Alloy) | intro:279 | "our implementation uses Alloy" | ok |
| violating (predicate sense) | intro:279 | never tied to "forbidden" | **undefined** (S4, live) |
| leakage contract / execution contract / protection set | intro:282 | defining clauses | ok |
| transmit (verb) | intro:157 (via transmitter), :282 | twice | redundant (R9, live) |
| our case study | intro:283 | intro:283 | ok |
| defense specification (object) | intro:300 | model:16 | **use before def** in the intro (S3, live) |
| instruction bound, leakage backbone, label | intro:300 | intro:300 | ok |
| concretize | intro:301 | by its object | ok |
| directives | intro:310 | colon clause | ok |
| Inspector, hit | intro:310 | intro:310 | ok |
| transmission criterion | intro:310 | model:51 | **use before def** (R1, live) |
| speculation conditions | intro:310 | in parentheses; never reused | **parenthetical**, coined (R2, live) |
| gem5 build | intro:312 | by context | ok |
| taint source, ROB walk | intro:324 | never in the intro | **undefined** (R7, live) |
| visibility-point/squash race | intro:324 | colon clause; "visibility point" at Background :26 | ok |
| tests per detection | intro:335 | results:100 | ok |
| speculation primitive, store bypass | background:10 | background:10 | ok |
| resolve, squash, commit, ROB | background:11 | background:11 | ok |
| speculative / transient / sequential | background:14 | background:14 | ok |
| channel | background:16 | background:16 | ok |
| taint-tracking defenses, taint/untaint | background:20 | background:20–24 | ok |
| visibility point; Spectre model; Futuristic model | background:26 | background:26 | ok |
| invisible-speculation defenses; D-TLB | background:32, :36 | in-sentence | ok |
| observer mode, execution mode, CT, ARCH, SEQ | background:47 | background:47 | ok |
| upholds / violates (a contract) | background:49 | background:49 | ok |
| SNI, weak SNI | background:54 | background:54 | ok, but never used again (C3, live) |
| unsafe operand; speculation model | background:69 | background:69 | ok |
| threat model | background:71 | never | **undefined** (R12, live) |
| candidate execution (MCM), po, rf, consistency predicate | background:79 | background:79 | ok |
| litmus test, minimal, relaxation | background:82–89 | in-sentence | ok |
| µhb graph, LCM | background:93, :97 | cites | ok |
| candidate execution (ours) | model:16, :30 heading | — | **variant** (S7, live) |
| snapshot | model:34 | — | **variant** of the intro's execution graph (A1) |
| spo, resolved, committed, xmit | model:38 | model:38 | ok ("flags" variant, S6 live) |
| rf (ours), ddi, dataflow path, well-formedness axioms | model:38 | model:38 | ok |
| update rule | model:48 | model:48 | ok |
| violates (predicate) | model:58 | box | ok here; tie to "forbidden" (R10, live) |
| direct load pair | model:66 | Background :30 says "pairs of directly dependent loads" | variant (A8) |
| Stage 1a / 1b / 2; extended execution graph | pipeline:10 | pipeline:10 | ok ("grows", G3 live) |
| forbidden transmission | pipeline:10 | — | **undefined** (C2, live) |
| minimality criteria | pipeline:29 | "every part of the graph" | vague (S14, live) |
| RI, RR, RC | pipeline:33 | pipeline:33 | ok |
| state element (RS) | pipeline:33 | — | **undefined** (A2) |
| UNSAT | pipeline:33 | parenthetical gloss | ok (standard) |
| commit boundary, lc, fnc, annotation | pipeline:73 | pipeline:73 | ok |
| instruction table | pipeline:82 | — | **undefined**, collides with Table 2 (A3) |
| misprediction direction | pipeline:90 | pipeline:90 | ok |
| free pool | pipeline:105 | — | ok (plain English) |
| value-neutral additions, filler instructions | pipeline:105 | pipeline:105 | ok ("spliced", A6) |
| integer version / vector version | pipeline:105 | pipeline:105 | ok |
| timing draw | pipeline:105 | timing settings at pipeline:120 | **use before def**, prefetch (A4) |
| run configuration | pipeline:108 | — | ok (implementation artifact) |
| harness, speculation directives, timing directives | pipeline:115 | pipeline:115 | ok |
| violation / hit / leak / bug | pipeline:115 | pipeline:115 | ok (S10 and B3 live) |
| violation window | pipeline:115 | pipeline:146 | ok (same section, with ref) |
| hook | pipeline:120 | pipeline:120 | ok |
| grid, timing setting, sweep | pipeline:120 | pipeline:120 | two modes, see C5 |
| warm / flushed / filled | pipeline:123 | pipeline:123 | ok |
| invalid run | pipeline:152 | pipeline:152 | ok |
| A-KV / A-UV / UV labels | results:29 | results:29 | "(unknown)" contradicts "Known Bugs" (B4) |
| load-to-load test | results:53 | — | **undefined** (A5) |
| taint source (§6) | results:69 heading | results:71 | ok in §6 |
| merge (noun) | results:71 | — | **undefined** (A7) |
| ROB walk, LSQ walk | results:81 | results:81 | ok |
| shadow | results:63, :81 | — | **undefined** (R11, live) |
| SPT-Fence | results:94 | — | **undefined** (T-6, pending) |
| campaign, full signature | results:94 | — | **undefined** (C22, live) |
| Clopper-Pearson, test case (AMuLeT) | results:100 | standard / AMuLeT's term | ok |
| divide transmitter (Other\_x) | Table 2 last row | no specification lists one | **undefined in §3** (C10) |
| backward untaint rules | discussion:17 | cite SPT §6.6 | ok |
| pending-squash timing leak | discussion:31 | discussion:31 | ok |
| leapfrogging | related:16 | cite Pensieve | ok |

New violations (not in the earlier passes):

- **A1 🟡 model.tex:34 adds a third description of the execution graph ("snapshot"), and the snapshot's moment is never named.** The intro defines the graph by its nodes and labels; pipeline.tex:90 fixes the moment ("when the transmitter acts"). Supersedes S6's model:34 fix: `a snapshot of a core's committed and in-flight instructions, annotated with their microarchitectural status` → `the core's committed and in-flight instructions when the transmitter acts, labeled with their microarchitectural state` (0 words).
- **A2 🟡 pipeline.tex:33: "state element" is never defined; RS actually leaves an operand's register or memory location unspecified** (Fig. 4: "RS: unneeded r1"; caption "(a) also specifies i2's destination r1"). `removing a state element (RS)` → `unspecifying an operand's register or memory location (RS)` (+4 words; clarity exception).
- **A3 🟡 pipeline.tex:82: "its instruction table" is undefined and reads as Table 2 (`tab:instrtable`, "How each execution-graph element is realized"), which is a different table.** `uniformly at random among the candidates in its instruction table that have enough operand slots for the graph` → `uniformly at random among its x86 candidates that have enough operand slots for the graph` (−3).
- **A4 🟡 pipeline.tex:105 (§4) uses "timing draw" before §5.1 defines timing settings (prefetch).** `The two versions share every other instruction, memory access, branch direction, and timing draw.` → `The two versions share every other instruction, memory access, and branch direction.` (−2).
- **A5 🟡 results.tex:53: "load-to-load tests" is undefined.** `Of 100 load-to-load tests that STT blocks when every value stays in an integer register,` → `Of 100 tests in which a load feeds a transmitting load, which STT blocks when every value stays in an integer register,` (+5).
- **A6 🟡 pipeline.tex:105: "spliced" is a metaphor, and "data path" is not the defined "dataflow path" (model.tex:38).** `ALU operations spliced into the transmitter's data path and elsewhere` → `ALU operations inserted on the transmitter's dataflow path and elsewhere` (0).
- **A7 🟡 results.tex:71: "the merge" is an undefined noun.** Folded into C8's fix ("the merging instruction").
- **A8 🟡 model.tex:66 says "a committed direct load pair"; Background :30 says "pairs of directly dependent loads that dereference a pointer".** `any later read of a word that a committed direct load pair has revealed` → `any later read of a word that a committed pair of directly dependent loads has revealed` (+3).

### B. High-level framing

- **B-para 1, what SimSpect is.** Abstract: "a three-part framework for automated, thorough security validation of simulated Spectre defenses"; intro :247–258: "the first targeted and automated approach for validating simulated Spectre defenses against their security guarantees" with three parts; §3–§5 open with matching Input/Output lines; conclusion: "tests whether a simulated Spectre defense upholds its own security guarantee". The identity is consistent. Two shifts remain: "first" (old-criteria F3, live), and "simulated Spectre defense" is never defined although it is the object of every claim (S5, live). No new fix.
- **B-para 2, what "targeted" means.** Intro :91 "targeted tests that attempt transient leakage"; :255 "a target execution that exhibits leakage the defense forbids"; :335 "its tests target leaks" (G7, live); §4 :10 "every test keeps its backbone's forbidden transmission"; Results :100 "every SimSpect test contains a transmitter whose operand is in the protection set"; conclusion "each attempting a leakage the defense forbids". Results narrows the definition: a protected operand alone does not violate the predicate, which also needs the transmitter to be speculative under the execution contract and the operand to be in the leakage contract. Fix B2 below.
- **B-para 3, what a hit, leak and bug are.** §5 :115 defines the four stages, but a "leak" is "a hit that we confirm, on its trace", which implies a person checks every hit. Results then reports thousands of tests ("1,690 of the 30,368", "2,848 of the 60,342", "1,674 of 2,000", "398 of the first 4,000") with no word on who confirms them, and Related Work says "only locating the responsible code in the defense is manual" (T2/F7, live). The intro's hit definition also omits the post-resolution part of the window (S1, live), and §5's "bug" wording differs from the intro's (S10, live). Fix B3 makes the leak definition neutral on who checks, which also removes the T2 contradiction without promising automation.
- **B-para 4, which bugs are "known" and which are "new".** The intro counts seven known bugs (AMuLeT's five in scope plus Protean's two) and six "previously unknown" ones; Results :29 labels AMuLeT's A-UV1–A-UV6 "(unknown)" and then lists them under "Known Bugs Replicated"; the heading :48 says "Unknown Bugs" for ours; abstract, Results :29 and the conclusion say "new bugs"; §6.4 and Fig. 10 still say "previously known bug" (S2/T3, live; false now that Protean's two count). Fix B4 removes the visible contradiction at :29; D-5 (new vs previously unknown) stays open.
- **B-para 5, what is claimed vs. shown.** The intro's "we specify six defenses in this language" becomes four specifications in §3 (InvisiSpec, CleanupSpec and SpecLFB share one), which a reviewer reads as inflation (teardown, rebuttal-only). Fix B5. The test-count claim is consistent in scope ("each of AMuLeT's bugs") everywhere except §6.4/Fig. 10 (S2). The timing claim (three faster, two slower) is stated in the intro and §6.5 only; abstract and conclusion stay silent on it (teardown W3, no new fix). The six-instruction completeness claim is scoped the same way in the intro (:312), §4.1 and Discussion.
- **B1 🟠 Table 2 vs Discussion: faults.** Table 2's last row builds a divide "unguarded, so a zero divisor faults" and counts "a divide's fault" as a transmission, while discussion.tex:31 says "our tests are not built to fault". Both are true only if the divide's fault is always transient. State the true property: `our tests are not built to fault (\S\ref{sec:conc-interleave})` → `no fault in our tests reaches commit (\S\ref{sec:conc-interleave})` (0). Also see C10.
- **B2 🟡 results.tex:100 narrows "targeted".** `every \toolname{} test contains a transmitter whose operand is in the protection set` → `every \toolname{} test's target execution violates the leakage predicate` (−4).
- **B3 🟠 pipeline.tex:115: the leak definition implies a person confirms every hit, which Results' counts and Related Work's "only ... is manual" contradict.** `a \emph{leak} is a hit that we confirm, on its trace, is not a harness or Inspector artifact;` → `a \emph{leak} is a hit whose trace shows no harness or Inspector artifact;` (−5). DECIDE against old-criteria F7: if every hit really is confirmed by hand, keep §5 as is and take F7's Related Work fix instead; if the checks are scripted (the `STAGE3_gem5/bugs/` disqualifiers), take B3 and F7 is no longer needed.
- **B4 🟠 results.tex:29 calls AMuLeT's bugs "unknown" one line above "Known Bugs Replicated".** `as A-KV1--A-KV3 (known) and A-UV1--A-UV6 (unknown),` → `as A-KV1--A-KV3 (known before AMuLeT) and A-UV1--A-UV6 (found by AMuLeT),` (+3).
- **B5 🟡 intro.tex:283: six defenses, four specifications.** `In our case study, we specify six defenses in this language:` → `In our case study, we specify six defenses in this language, three of which share one specification:` (+6; skip if space is tight, since §3 states it).

### C. Clean, principled methods and results (§4–§6)

- **C1 🟠 pipeline.tex:33: the bound reads as tuned to make the solver finish ("so that ... finishes ... except SPT's").** State the bound and the result, not a convenience reason. `We bound backbones at six instructions so that this enumeration finishes for every specification except SPT's (\S\ref{sec:discussion}); no backbone of those specifications has more than three instructions.` → `We bound backbones at six instructions; within this bound, every specification except SPT's reaches UNSAT with no backbone above three instructions (\S\ref{sec:discussion}).` (−6).
- **C2 🟡 pipeline.tex:60: informal second reason.** The first reason (SPT and ReCon update protection through committed instructions) already justifies the rule. `(\S\ref{sec:example-contract}), and we want every test to exercise that tracking.` → `(\S\ref{sec:example-contract}).` (−9).
- **C3 🟡 pipeline.tex:60: an internal mechanism and a vague cap.** `Stage~1b draws a capped number of graphs per backbone in a seeded random solver order.` → `Stage~1b samples a fixed number of graphs per backbone, with a seeded solver for reproducibility.` (+1; state the number if it fits, or leave it to the artifact).
- **C4 🟡 pipeline.tex:82: a counterfactual where a principle fits.** `Exhausting the cross product of candidates instead of sampling it is possible but would multiply the number of tests.` → `Sampling, rather than exhausting the candidates' cross product, keeps the suite compact.` (−7).
- **C5 🟠 pipeline.tex:120: two run modes (one draw per test vs a sweep over every setting) with no rule for which runs use which.** §6.4 uses draws; UV3 says "the swept 500-cycle hold". Two modes with no rule looks ad hoc. Say which runs use which, or keep one. Option 1, if the bug-finding campaigns swept and the comparison drew: `each test draws one setting, and a sweep runs every setting and reports a hit if any setting triggers one.` → `the comparison with AMuLeT draws one setting per test (\S\ref{sec:comparison-prior-work}), and bug-finding runs sweep every setting, reporting a hit if any setting triggers one.` (+5). Option 2, if all reported runs drew: `each test draws one setting, and a sweep runs every setting and reports a hit if any setting triggers one.` → `each test draws one setting.` (−14), and in results.tex:71 drop "swept" (C8 does). Unverified which runs swept: check the run configs before choosing.
- **C6 🟡 pipeline.tex:120: the cycle counts repeat Table 2 rows 1–2 verbatim.** Keep the principle in prose and the numbers in the table. `The harness holds each unresolved branch's resolution for 2{,}500, 5{,}000, or 10{,}000 cycles, so that the branch is still unresolved when the transmitter acts, and delays each resolved branch's resolution by 0, 500, or 2{,}500 cycles after its direction and target are known (Table~\ref{tab:instrtable}, rows~1--2), so that tests vary when resolved branches resolve, as they would if their conditions arrived late.` → `The harness holds each unresolved branch's resolution so that the branch is still unresolved when the transmitter acts, and delays each resolved branch's resolution, as if its condition arrived late (cycle counts in Table~\ref{tab:instrtable}, rows~1--2).` (−29, about −2.5 lines).
- **C7 🟡 pipeline.tex:120: print-only hooks are an implementation detail, and Discussion :4 already mentions them ("besides these overrides and print-only logging").** Delete `Print-only hooks log events that a build does not otherwise print, such as a branch's prediction and resolution. ` (−17, about −1.5 lines).
- **C8 🟠 results.tex:71: a counterfactual with cycle numbers that makes UV3 look like an artifact of harness timing, plus "hold" for a resolved branch (G10) and the undefined "merge" (A7).** Supersedes G10's results.tex fix. `The release needs the older load's branch to resolve after the merge is renamed, since ReCon assigns taint at rename: without the swept 500-cycle hold, i2 would resolve at cycle~6, before the merge is renamed at cycle~121, and ReCon would hold i7 (Table~\ref{tab:instrtable}, row~2).` → `Because ReCon assigns taint at rename, the release needs the older load's branch to resolve after the merging instruction is renamed, here because of a 500-cycle resolution delay (Table~\ref{tab:instrtable}, row~2).` (−13). Keep the old sentence in the rebuttal notes, since it answers "is the delay needed?".
- **C9 🟡 results.tex:75: per-instruction bookkeeping.** The two classes are exhaustive, so "i.e.". `a \texttt{mov} or \texttt{cqto} reading its old destination (12 tests, as in Fig.~\ref{fig:otb}), or an arithmetic instruction reading the old flags (5)` → `i.e., a \texttt{mov} or \texttt{cqto} reading its old destination (Fig.~\ref{fig:otb}) or an arithmetic instruction reading the old flags` (−3). Old-criteria C38 (delete the unshown `add` sentence) still applies.
- **C10 🟡 Table 2 (tikz/instrtable_v2_short.tex, last row): a divide transmitter that no specification in §3 lists.** No §3 leakage contract contains an `Other` transmitter (STT: load, branch; SPT adds store; the shared one: load), so the divide reads as a leftover special case and conflicts with Discussion's fault sentence (B1). If no evaluated specification has an `Other\_x` transmitter: `; divide: unguarded, so a zero divisor faults.` → `.` and `; a divide's fault counts as a transmission.` → `.`, and drop `{\itshape or}{\texttt{Other\_x}}` from the row label. Unverified: check the `.als` leakage contracts first.
- **C11 🟡 pipeline.tex:123: two special cases with no common rule.** `On InvisiSpec, where \texttt{clflush} is a no-op, tests draw only warm or filled. Runs on ReCon's implementation of STT start warm, because STT's transmission criterion does not depend on the cache state.` → `Each build draws only states it can reach and its transmission criterion distinguishes: InvisiSpec, where \texttt{clflush} is a no-op, draws warm or filled, and ReCon's implementation of STT starts warm.` (−2). If the STT and SPT builds also start warm, write `the taint-tracking builds start warm` (unverified).
- **C12 🟡 pipeline.tex:152: a stacked exception that follows from the first clause** (only branches between the commit boundary and the oldest unresolved branch are checked). Delete `; a resolved branch on the wrong path is not checked, because the older unresolved branch already makes the transmitter speculative` (−21, about −2 lines; also removes a banned "wrong path").
- **C13 🟡 results.tex:63: per-suite bookkeeping and an aside on why ReCon's suite is larger.** Supersedes S11's :63 fix. `1{,}690 of the 30{,}368 tests from our STT model reach the bug on ReCon's implementation of STT, and so do 2{,}848 of the 60{,}342 tests of ReCon's own specification, whose execution contract adds store shadows (\S\ref{sec:example-contract}).` → `On ReCon's implementation of STT, 2{,}848 of the 60{,}342 tests of ReCon's specification reach the bug, as do 1{,}690 of the 30{,}368 tests of STT's.` (−13).
- **C14 🟠 results.tex:100: uneven, corpus-by-corpus test counts read as ad hoc.** Keep the totals the estimate uses and move the composition to the artifact (also supersedes G9 for this sentence). `InvisiSpec and SpecLFB run the first 4{,}000 tests of one corpus, and CleanupSpec all 291{,}860 tests of two corpora and three random re-concretizations of the first.` → `InvisiSpec and SpecLFB run 4{,}000 tests each, and CleanupSpec 291{,}860 (suite composition in the artifact).` (−11). If the reason for the larger CleanupSpec run is A-UV5's rarity, say it instead of the artifact pointer: `and CleanupSpec, for the rare A-UV5, 291{,}860.`
- **C15 🟡 results.tex:81: "first" is bookkeeping here.** `In 398 of the first 4{,}000 tests, only a later load leaks.` → `In 398 of 4{,}000 tests, only a later load leaks.` (−2).
- **C16 🟠 pipeline.tex:103: describing a pass that the evaluation never runs makes the pipeline look unfinished, and no reason is given (S18/D-6).** Option 1 (recommended, cleanest): remove Pass 4 and renumber: `Stage~2 builds each test in seven passes.` → `Stage~2 builds each test in six passes.`; `Passes~4--7 assign state, vary the program, and compile it. Pass~4, which can add a second, independent speculative source, is off in our evaluation (\S\ref{sec:discussion}).` → `Passes~4--6 assign state, vary the program, and compile it.`; `Pass~5 assigns state:` → `Pass~4 assigns state:`; `Pass~6 emits LLVM IR` → `Pass~5 emits LLVM IR`; `Pass~7 compiles the IR` → `Pass~6 compiles the IR`; discussion.tex:21 delete ` Pass~4, which interleaves additional chains of dependent instructions (\S\ref{sec:conc-interleave}), is off in our evaluation.` (about −3 lines in total). Option 2: keep Pass 4 and give one independent reason in §4.
- **Still-live C-type items from the earlier passes (not repeated here):** old-criteria C18 (Inspector's "two passes"), C21 (Stage 1b minimality sentence), C22 (UV6 "We claim the race only", "campaign's timing"), C23/F6 (AMuLeT's analysis "would attribute"), C27 (A-UV5 "5 tests from 3 programs"), C36 (master-branch line number), C37 (filler list), C38 (`add` sentence), C40 (test-id sentences), C42 ("Throughout this window"), C16/O6 (tests "reused when a defense is patched"), O5 (UV5 "always"), F5 (A-UV6 patch "would also close"), T4 (UV6 STT count).

### Counts

A: 94-row term table; 8 new violations (A1–A8, all 🟡) plus 30 earlier define-before-use and banned-term items confirmed still live. B: 5 framing paragraphs; 5 fixes (B1, B3, B4 🟠; B2, B5 🟡). C: 16 items (C1, C5, C8, C14, C16 🟠; 11 🟡), net about −10 lines if all are taken (C6, C7, C12, C16 give most of it).

### Top 12 fixes, in priority order

1. B3 🟠 pipeline.tex:115: `a \emph{leak} is a hit that we confirm, on its trace, is not a harness or Inspector artifact;` → `a \emph{leak} is a hit whose trace shows no harness or Inspector artifact;` (DECIDE against F7).
2. B4 🟠 results.tex:29: `as A-KV1--A-KV3 (known) and A-UV1--A-UV6 (unknown),` → `as A-KV1--A-KV3 (known before AMuLeT) and A-UV1--A-UV6 (found by AMuLeT),`.
3. B1 🟠 discussion.tex:31: `our tests are not built to fault (\S\ref{sec:conc-interleave})` → `no fault in our tests reaches commit (\S\ref{sec:conc-interleave})`.
4. C16 🟠 remove the unused Pass 4 and renumber Passes 5–7 to 4–6 (or give one reason).
5. C5 🟠 pipeline.tex:120: say which runs draw one timing setting and which sweep (verify first).
6. C8 🟠 results.tex:71: replace the UV3 counterfactual with the principle (also fixes "hold" and "merge").
7. C14 🟠 results.tex:100: `InvisiSpec and SpecLFB run the first 4{,}000 tests of one corpus, and CleanupSpec all 291{,}860 tests of two corpora and three random re-concretizations of the first.` → `InvisiSpec and SpecLFB run 4{,}000 tests each, and CleanupSpec 291{,}860 (suite composition in the artifact).`
8. C1 🟠 pipeline.tex:33: state the six-instruction bound and the UNSAT result without the "so that this enumeration finishes" reason.
9. C6 🟡 pipeline.tex:120: move the hold/delay cycle counts to Table 2 only (−2.5 lines).
10. B2 🟡 results.tex:100: `every \toolname{} test contains a transmitter whose operand is in the protection set` → `every \toolname{} test's target execution violates the leakage predicate`.
11. A3 🟡 pipeline.tex:82: `among the candidates in its instruction table that have enough operand slots` → `among its x86 candidates that have enough operand slots`.
12. A2 🟡 pipeline.tex:33: `removing a state element (RS)` → `unspecifying an operand's register or memory location (RS)`.

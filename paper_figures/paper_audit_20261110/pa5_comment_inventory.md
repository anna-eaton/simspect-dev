# PA5: comment inventory and triage (ISCA-27, 2026-11-10)

Source: `~/trippel/ISCA-27` working tree on top of c376706 (2026-11-10 17:20, with uncommitted edits to six sections). Read-only; nothing in the paper repo was edited. This is a PARTIAL inventory because the deadline was moved up: the blockers and the per-section tables for main/abstract/intro/background/model/pipeline/results/discussion/conclusion are complete; the related.tex rows are grouped; anything marked TODO was not re-verified line by line.

Root-file change since the 11-09 audit: `main.tex` is now the live ISCA 2027 acmart root. It `\input`s every section plus `sections/conclusion.tex` and uses `sections/references.bib`. `bare_conf_compsoc.tex` does not input conclusion.tex. So the 11-09 audit's "main.tex is dead" no longer holds, and the CLAUDE.md line "root bare_conf_compsoc.tex" is stale. DECIDE: which root Overleaf compiles. Recommendation: main.tex, retiring bare_conf_compsoc.tex.

No `\claudenote` or `\claudetag` exists anywhere. The word "claude" appears only in `sections/oldtechnicaldetails.tex:1` and `:113`, two `\anna` notes in a file nothing inputs. Recommendation: delete that file, or those two words, before the advisor reads the source.

## Counts (approximate; live notes plus review-type % comments)

| status | count |
|---|---|
| OPEN (action known, proposed text exists or given) | ~120 |
| BLOCKED on a decision | ~14 |
| RESOLVED by later text (delete the note) | ~16 |
| OBSOLETE / dead (% fragments, \iffalse blocks, superseded notes) | ~35 |

## Top blockers (fix before anyone else reads it)

1. **The speed-up numbers disagree.** The abstract (abstract.tex:3) says "at least 23x fewer tests". The intro (intro.tex:77), the results prose (results.tex:75) and the conclusion note (conclusion.tex:2) say "[N]x". The comparison note (results.tex:77) says "at least 18x" (140x-2,100x for all but A-UV5). The timing note (results.tex:80) says "[19-37]x" in CPU time. A-UV5 is "[1] test" at results.tex:39 but "four times in 50,232 tests" in the :77 note. Action: pick one source (EVAL_MANIFEST T rows / the f8890bb first-detection figure) and use one number everywhere.
2. **Scope and completeness are overclaimed.**
   - intro.tex:60 claims "10 hardware defenses" are expressed, and related.tex:182 lists SpecShield/NDA/DoM/SDO. Only STT, ReCon and SPT are Alloy models. Urgent notes intro:62 and related:187 carry the proposed text.
   - intro.tex:52, :58 ("all possible"), pipeline.tex:8, :42 and :272 ("coverage is complete") and the Fig. 3 "Bounded-exhaustive" label are only true for STT/ReCon Stage 1a; SPT is capped. Notes: intro:54, pipeline:44, pipeline_full caption urgentnote. This is BLOCKED on H3 (the SPT testset).
3. **The UV6 race is not reportable as written.**
   - results.tex:70 still has the placeholders [2--3], [N] and [pending].
   - intro.tex:72 says "STT and SPT share" with no latency condition (note intro:74).
   - The 11-08 window rule (unresolved until the squash lands) is not in pipeline.tex:225 or in the checker.
   - The only count (23,966) predates the fix.
   - BLOCKED on D1 (window rule), D2 (count source) and D8 (SPT re-run).
4. **Pipeline/harness factual errors are visible in the prose.**
   - pipeline.tex:10 has an undefined `\ref{stage1}` (prints ??).
   - pipeline.tex:185 gives pre-fix stall values (note :187).
   - pipeline.tex:181 says the stall sweep shows "not hinge on any single setting", but the code ORs over the grid (note :183).
   - pipeline.tex:197 says "No cache or defense code is instrumented to see a leak", which is false (note :199). The "non-invasive" wording repeats at pipeline:24 and in the Fig. 3 caption.
   - pipeline.tex:163 claims every hook is paired with a control run, but only the Unsafe baseline ran (note :165).
   - intro.tex:31 misdescribes AMuLeT as "two randomly generated architecturally identical tests" (note :33). background:23 and related:26 repeat the misdescription.
5. **The paper's structure is not submittable.**
   - Related Work is still bullets plus ~45 notes (related:5).
   - The Conclusion section is only an urgentnote (conclusion.tex:2), so it is empty when notes are hidden.
   - main.tex:86-88 still has the template acks ("derived from previous conferences"); this breaks double-blind.
   - discussion.tex:17 has a stray prose fragment, "- Sentence about".
   - results.tex:181 has a stale labnote ("InvisiSpec, SpecLFB and CleanupSpec results still to be inserted"); those results are now in Known Bugs Replicated.
   - results.tex:39 says "(A-UV3, next paragraph)", but that paragraph is commented out (note :41).
   - results.tex:253-260 says "Every count ... is a confirmed real leak", which is an overclaim (note :267).

## Pending decisions (Anna's)

| id | question | evidence | recommendation |
|---|---|---|---|
| D1/H4 | Does the violation window end at the squash (11-08 rule) in the text, both trace figures and the checker? | pipeline.tex:225, results:73, gem5_common resolve_visible | Adopt everywhere and re-score. |
| D2 | Where does the race count come from? | results:71 (23,966 is pre-fix) | Run a slowed-squash eval row; otherwise give one traced example with no count. |
| D6/H1 | Fig. 5 / interleave as the OTB route | pipeline:82, :137; results:60 | Redraw around the fanout-v2 OTB merge. |
| D7 | "ReCon" vs "ReCon's implementation of STT" in headings (results:51, :57) and in the abstract's "six defenses" | results:32 | Use "ReCon's STT". |
| D8 | The SPT race claim | results:70-71 | Say "SPT-Fence lifts its fence on the same signal" as a code-level statement, or re-run. |
| H2 | How minimality is stated; RO is listed but never enforced | pipeline:61-73, :90 | Two-stage wording; relabel pane (a) as RS. |
| H3 | Exhaustiveness claim for SPT | intro:54, pipeline:44 | Claim STT/ReCon only. |
| H5 | Violation definition: STT_6 location-based vs STT_6_u values | model.tex:60-61, :101 | Follow STT_6_u if it produces the results. |
| VOCAB | Contract terminology; see also NEW-1 | background:15 | Keep our terms plus the bg:15 paragraph. |
| FP | Count footprints of any squashed load, or only the transmitter's? | results:41(4), pipeline:220 | Report the transmitter's footprints, with all-load counts as secondary. |
| UV4 | Is the walk order really separate from A-UV6? | results:63 | Check AMuLeT's fix first. Until then, a "new bug" claim is at risk. |
| UV5 | Do the 274 replay-tagged hits count? | results:67 | Leave them out until traced. |
| ROOT | main.tex vs bare_conf_compsoc.tex | above | main.tex |

## main.tex / bare_conf_compsoc.tex / abstract.tex

| file:line | gist | status | proposed resolution |
|---|---|---|---|
| main.tex:86-88 | template acks body | OPEN, blocker | Delete the `acks` block for submission. |
| main.tex:54 | switch (1) comment says it hides [Anna:], but the code hides only todo/figtodo | OPEN, low | Fix the comment or the code. |
| main.tex:65 | double space in "of  Simulated" | OPEN, trivial | Delete one space. |
| bare_conf_compsoc.tex (whole) | 11-09 Part 1 preamble/template rows | OBSOLETE if main.tex is the root | Retire the file (see ROOT). |
| abstract.tex:3 | "uncovers all bugs that were found by ... AMuLeT, and are in-scope for the defense, plus six new bugs" | OPEN (grammar; no note) | "...uncovers all five bugs reported by AMuLeT, the prior state-of-the-art simulator tester, that fall within each defense's own guarantee, plus six new bugs." |
| abstract.tex:3 | "at least 23x" | OPEN, blocker 1 | Unify with results. |
| abstract.tex:3 | "five publicly available ... and one obtained from its authors" | OPEN (D7) | The ReCon runs test ReCon's STT; say so. |
| abstract.tex:5-14, :18-19 | commented old abstracts | OBSOLETE | Delete. |
| abstract.tex:22-25 | commented urgentnote (walk order vs "six new") | RESOLVED (Anna counts six) | Delete. |

## intro.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| :2, :5, :24-28, :44, :65, :81 | outline / commented prose | OBSOLETE | Delete. |
| :8 | `\anna{should we use}` (dangling) | OPEN | Ask Anna what term she meant; likely "advertised". Then delete the note. |
| :11 | `% not cycle accurate` | OBSOLETE | Delete, or make it a Discussion point. |
| :14, :16, :18 | `% \todo` cite benchmarks; old `\anna` | RESOLVED | Delete. |
| :22 | reviewnote citation check | OPEN (3 sub-items) | (1) Add Pensieve at :20: "...against a sequential baseline~\cite{amulet}; early-stage designs have been model-checked against speculative non-interference~\cite{pensieve}, but none checks a prototype against the defense's own security guarantee." (2) Move `\cite{spec2017}` to after "checking their architectural outputs". (3) Drop `\cite{nickscommittoSTT}` at :9, or give it its own clause. |
| :33 | urgentnote: AMuLeT misdescription | OPEN, blocker 4 | Paste the note's PROPOSED TEXT. |
| :35 | `\anna` move SNI discussion to related work | RESOLVED (:36 commented) | Delete. Make sure related:101 carries SNI. |
| :37 | `\anna` fuzzing vs targeting paragraph | OPEN | Keep one sentence ("AMuLeT's generation is random, so most of its tests cannot leak"); move the rest to related VI-A. |
| :41 | `\anna` STT running mini example | OPEN | Add it as its own figure or drop the idea (Fig. 1 already sits here). |
| :46 | reviewnote: add Fig. 1 reference | OPEN, trivial | Append "(Fig.~\ref{fig:intro})" to the :41 sentence. |
| :54 | urgentnote: completeness | BLOCKED (H3) | Paste the note's text. |
| :58 | "target all possible types of violations" (no note) | OPEN | "...targets every minimal form of violation up to the instruction bound..." |
| :62 | urgentnote: "10 defenses" | OPEN, blocker 2 | Paste the note's text. |
| :69 | reviewnote: known-bug evidence | OPEN | Rename UV1 to A-UV1, etc. Update A-UV5 to the comparison note's 4/50,232. |
| :74 | urgentnote: race condition | BLOCKED (D1/D2) | Paste once decided. |
| :77 | "[N]x", plus the 17% claim (no note) | OPEN, blocker 1 | Unify N. The 17% is supported only by the hidden "Test targeting" paragraph (results:206-213); unhide it or cite its source. |
| :79 | `% NO` | RESOLVED (Anna rejected the future-work paragraph) | Delete together with :81. |

## background.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| :5 | auditnote: add an SPT sentence; reword the STT one | OPEN | Paste both. |
| :9 | reviewnote: check the ReCon sentence | OPEN | Anna reads it, then delete. |
| :13 | auditnote: add InvisiSpec/CleanupSpec/SpecLFB | OPEN, important | Paste with its two caveats. Three of the six evaluated defenses are never introduced otherwise. |
| :15 | urgentnote VOCAB: leakage-contracts paragraph | BLOCKED (VOCAB) | Paste after the decision. |
| :21 | auditnote: unfinished clause at :19 | OPEN | Paste the note's text. |
| :23 | AMuLeT "indistinguishable in their architectural side-channel leakage" (no note) | OPEN | Reuse the intro:33 wording. |
| :25 | `\anna` talk about uarch state | OPEN | TODO: write from AMuLeT §3 (which state it observes). |
| :28, :34, :36 | `\anna` cite Arm/Simner; CheckMate/LCM; more on modeling | OPEN | Cite keys from the :39 note (checkmate, lcms, ponce2022cats, simner*; all in the bib). |
| :30 | auditnote: missing period; Kodkod | OPEN | `kodkod` is still not in references.bib. Add it, then paste. |
| :32 | `\anna` replace sentence, cite Wickerson | OPEN | "Wickerson et al.\ use Alloy to compare memory models and synthesize distinguishing litmus tests~\cite{memalloy}." |
| :37 | commented bridge sentence | OBSOLETE | Delete. |
| :39 | auditnote: write more (axiomatic) | OPEN | Write it as planned in the note. |
| :3, :11, :18, :19 | "HSCD", "hardware SCDs": undefined acronyms (no note) | OPEN | Use "Spectre defenses" as in the intro. |

## model.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| :2 | `\anna{comprehensive??}` | OPEN | "We adopt a formal language for specifying the security guarantee of a Spectre defense." |
| :4 | fragment "We take inspiration from prior work to" (no note) | OPEN | Delete it, or finish it: "...prior work on axiomatic memory models~\cite{herdingcats,lustig}." |
| :16-22, :93, :103-121 | commented duplicates, todo, figures | OBSOLETE | Delete. |
| :27, :39, :60, :71, :75, :79 | older notes, each superseded by the note after it | OBSOLETE | Delete. |
| :29 | auditnote: shared skeleton except SPT per-operand | OPEN | Paste. |
| :31 | `\anna{add citations}`; "as in \ref{formalmodel}" refers to its own section | OPEN | Drop the self-reference; cite lustig/herdingcats (already present) plus checkmate. |
| :35, :41, :49 | VOCAB: define spo, resolved/committed, rf/ddi | OPEN | Paste (:41 replaces :39). |
| :45 | auditnote: commit is measured, not enforced | OPEN | Paste. |
| :53, :64 | "Figure" for a table; I1 vs i1 | OPEN, trivial | Paste. |
| :61 | violation definition under STT_6_u | BLOCKED (H5) | — |
| :73, :77, :81, :83, :85, :87 | Fig. 3 caption: non-invasive, bounded-exhaustive, Stage 1b "minimal", Inspector vs checker, colors | OPEN | The caption still has all of these (tikz/pipeline_full_8pt1col.tex:231, :244, :261, :268-271). Paste the notes. |
| :92 | urgentnote: rename to Stage 1a/1b | OPEN (figure done; prose pending at pipeline:12, :29, :80; results:17, :24; discussion:6) | Delete once the prose is renamed. |
| :101 | STT protection set is location-based | BLOCKED (H5) | — |

## pipeline.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| :3 | `\anna{hardware under test??}` | OPEN | "...on the defense's simulated implementation (the design under test)". |
| :4-5 | `\anna` delete commented | RESOLVED | Delete :4-5. |
| :12 | stage names; `\ref{stage1}` ?? | OPEN, blocker 4 | Paste the note's text. |
| :16, :20, :41, :48-50, :93, :168, :249, :257, :269, :274 | commented prose | OBSOLETE | Delete. |
| :17 | `\anna{define leakage backbones}` | RESOLVED by :24 | The intro (:52) uses the term first; add a forward reference there. |
| :29, :80 | Stage 1a naming in text and the interleave caption | OPEN, trivial | Paste. |
| :36, :90 | minimality per stage | OPEN (H2) | Paste. |
| :44 | UNSAT claim | BLOCKED (H3) | — |
| :53 | backbone-bound proof TODO | BLOCKED (research) | A k=7 Stage 1a run, or the proof; meanwhile say "up to the instruction bound". |
| :59, :61, :84, :86, :119, :123, :129 | figure fixes (relaxation, interleave, Table II, Fig. 6 vs Fig. 10) | OPEN | Paste. At :123/:127, pick "ReCon holds i5" / "ReCon releases i5 (bug)" and delete the commented :125. |
| :70, :102, :111, :142, :246 | fact fixes (RC, branch asm, xmit-branch exception, free pool, load signal) | OPEN | Paste. |
| :82, :137 | interleave is not the OTB route | BLOCKED (D6) | — |
| :99, :134, :151, :193, :256 | reviewtags "check it" | OPEN | Anna reads them, then delete. |
| :117, :255 | Other_x never ran | OPEN | Add the caption sentence; cut or qualify the :255 bullet. |
| :147, :159, :207 | proposed paragraphs (compilation, white-box, no attacker) | OPEN | Paste. |
| :156, :231, :216, :240 | VOCAB: violation/hit/leak; window label | OPEN (D1) | Paste. :240 is the key definition. |
| :165, :172, :178, :195 | controls, annotation contents, BTB, hook sets | OPEN | Paste. |
| :183, :187, :199 | sweep OR; stall values; observation hooks | OPEN, blocker 4 | Paste. |
| :211, :227 | window name; "guarding branches" | BLOCKED (D1) | — |
| :218 | checker figure out of scope | RESOLVED (results now treats A-UV1 as in scope) | Re-caption it as InvisiSpec's footprint criterion. |
| :220 | footprint attributed to any squashed load | BLOCKED (FP) | — |
| :236-237 | hidden xmitcriteria table | OBSOLETE | Drop. |
| :261 | store-transmitter bullet | OPEN | Cut it. |
| :266 | quote typo | OPEN, trivial | Change to ``branches still unresolved''. |
| :272/:275 | knobs "complete"; `\anna{idk}` | OPEN | Replace :272 with: "Enumeration is exhaustive over minimal violating graphs up to six instructions where Stage~1a reaches UNSAT (STT and ReCon); Stage~1b and every concretization choice (instruction templates, register naming, misprediction direction, resolution timing, fanout merges) are sampled; the leakage predicate is fixed per campaign." Or cut the subsection. |

## results.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| :1-5, :52, :58, :65, :69 | reorganization breadcrumbs | OBSOLETE once accepted | Delete. |
| :8 | labnote "results are not finalized" | OPEN (lab only) | Remove at submission. |
| :10-27, :84-122, :184-187, :218-248 | \iffalse lists, old bug table, cut sections | OBSOLETE | Delete. |
| :32 | run list (ReCon's STT; cite at first mention) | OPEN (D7) | Paste. |
| :34 | stray `\urgentbr` with no note | OPEN | Delete. |
| :36 | "UVn" for new bugs collides with A-UVn; :39 says "KV3" | OPEN (no note) | Rename the new bugs N1-N6 (or similar); write "A-KV3". |
| :39 | "[1] test" for A-UV5; "next paragraph" | OPEN, blocker 1/5 | Paste the :41 note item (1); A-UV5 = 4 of 50,232. |
| :41(4) | footprint by any squashed load | BLOCKED (FP) | — |
| :43, :124-178, :189-204, :261-266 | commented detail / scope / closing list | RESOLVED (merged into the notes) | Delete after the notes are pasted. |
| :47 | "how this section is organized" note | RESOLVED | Delete. |
| :50, :54, :56, :60, :67 | per-bug proposed text and figure notes | OPEN | Paste. Also fix the recon_otb caption ("enumeration does not reach this shape") and the "speculative window" → "violation window" wording. |
| :62-63 | UV4 bracket "[157 and 162]"; separate-bug check | BLOCKED (UV4) | — |
| :70-73 | UV6 placeholders; figure | BLOCKED (D1/D2/D8) | — |
| :75-77 | comparison; 18x vs 23x | OPEN, blocker 1 | — |
| :80, :82 | timing note "[19-37]x"; CPU-usage labnote | OPEN | Needs final data. |
| :181 | stale labnote (prints) | OBSOLETE, blocker 5 | Delete. |
| :206-213 | hidden targeting paragraph + `\anna{fixing}` | OPEN | This is the only support for "17%"; finish it or drop the claim. |
| :253-260/:267 | "confirmed real leak" overclaim | OPEN, blocker 5 | Paste :267. |

## discussion.tex and conclusion.tex

| line | gist | status | proposed resolution |
|---|---|---|---|
| discussion:2-16 | hidden to-do list (+ :14 auditnote) | OPEN (planning) | Rename the stages at :6. |
| discussion:17 | stray "- Sentence about" | OPEN, blocker 5 | Delete. |
| :21, :25 | VOCAB "still-speculative windows"; raw+intersected contract unsupported | OPEN | Paste. |
| :29 | `\anna` running-example figure list | OPEN | Anna's figure plan; TODO. |
| :31, :33, :35, :37, :39, :41, :43, :45 | proposed Discussion paragraphs | OPEN | Paste. Discussion has one prose paragraph otherwise. :38 cites `\cite{yu2019stt}` for the December 2025 upstream fix; cite `nickscommittoSTT` instead. :43 still contains "[cite each threat model]". :39 has a pending ReCon store-channel decision. |
| conclusion.tex:2 | proposed Conclusion (note only) | OPEN, blocker 5 | Paste it as prose. Its wording drifts: it says "speculation contract ... leakage function" where model.tex says "execution contract ... leakage contract", and "[N]x" where the abstract says 23x. Fix both. |

## related.tex (grouped; per-line re-check TODO)

| lines | gist | status | proposed resolution |
|---|---|---|---|
| :5, :21 | still bullets; structure problems | OPEN, blocker 5 | Write VI as prose (~0.75 pp). In the :21 note, the "Results split V-B/V-C/V-E" item is RESOLVED by the 11-10 reorg; AMuLeT ×4, the conclusion and the acks remain. |
| :3, :7, :9, :11, :13, :15 | part plan + SpecCheck must-cite + `synthlc` cite trap | OPEN | Follow the plan. Rename the `synthlc` key. |
| :26-29 | AMuLeT bullet misdescription; VOCAB "contract violation" | OPEN | Paste. |
| :43-44 | "tests against a sequential model, so it cannot test [Protean-style] defenses" | OPEN (no note) | Verify against AMuLeT §2-3 before keeping. |
| :48-66, :99-117, :135-139, :169-171, :194-200, :214-220 | ~33 CITE notes | OPEN | Fold them into the prose. |
| :68, :119, :141, :173, :202, :222, :231 + commented blocks | CUT LIST | OPEN | Delete once VI is prose. |
| :91 | VOCAB "Hardware-software contracts" + Spectector | OPEN | Paste. |
| :94, :211 | % \todo add cites | RESOLVED | Delete. |
| :182-187 | stale defense list; SPO→SDO reviewtag; sdo cited twice | OPEN, blocker 2 | Paste the :187 text. |

## Earlier audit (wiki/findings/audits/2026-11-09/PAPER_COMMENT_AUDIT.md): what is resolved now

- **RESOLVED:**
  - P1: the stale abstract labnote; the 6.5x/"less time" claim (now 23x, but see blocker 1); "replicate all in-scope" (now 5/5); xmm4 and jmp-shadow missing; "proving"/"comprehensive" in the abstract; the title; decisions 1, 2, 5 and 6.
  - P2: intro:25 "claude" comment; the findings list (now six-bug prose); intro labnotes :70/:74; "CUT ONE"/"REWORD Unlike AMuLeT"/"MOVE future work" (gone or rejected).
  - P3: the pipeline "@claude" line.
  - P4: D3 (Anna counts six new bugs); D4 (scope rewritten as Known Bugs Replicated); D5 (KV3 scoped out); bug claims; the AMuLeT scope paragraph; pre-fix 23,966 and 68/300 removed from prose; un-hide/delete pass.
  - P5: Notes A, C and D (one home per bug, scope cut, closing list cut); Note E mostly done.
- **OBSOLETE:**
  - P1: "main.tex is dead" (it is now the root); bare_conf_compsoc preamble/template rows, if it is retired.
  - P5 Note B: walk order "not separate" was overridden; Anna counts it as new.
- **STILL OPEN:**
  - P1: decisions 3 (race) and 4 (number, now inconsistent); acks placeholder; Conclusion not pasted.
  - P2: defense count (now "10"); related defense list; protection-set semantics (H5); `synthlc` key; Kodkod bib entry; background:19/:28; AMuLeT misdescription; Fig. 1 reference; all bg `\anna` items; related prose.
  - P3: H1-H5; stall values; minimality, exhaustiveness and OTB body text; `\ref{stage1}`; oldtechnicaldetails "claude" ×2.
  - P4: D1, D2, D6, D7, D8; window rule; Fig. 3/5/OTB captions.
  - P5: conclusion paste.

## New suggestions a careful ISCA reviewer would raise (no existing comment)

1. **Terminology drift.** model.tex says execution/leakage *contract*; the conclusion, discussion:7 and the repo docs say speculation contract / leakage *function*; the intro says "speculation contracts" for Revizor. Pick one set and define it once.
2. **Acronym drift.** HSCA (intro) vs HSCD/SCD (background). Neither HSCD nor SCD is defined.
3. **New-bug naming.** "UV1-UV6" for new bugs next to AMuLeT's "A-UV1-6" invites confusion; rename them.
4. **Unsupported numbers in visible text.** The "17% of AMuLeT's tests" and every [N] placeholder rely on hidden or uncomputed sections.
5. **Missing coverage table.** The paper never states how many graphs/tests per defense were run in the eval (the hidden Coverage item at results:23). Reviewers will ask.
6. **Store bypass presented without a result.** pipeline:131 and :189 describe store-bypass instrumentation, but no STL result is reported. Mark it as a capability or cut it.
7. **"First rigorous ... approach"** (intro:41) needs the Pensieve/SpecCheck contrast (related:56, :171) or narrower wording.
8. **Self-reference.** model.tex:31 references its own section. Results/Discussion have no `\label`, so the conclusion cannot `\ref` them.
9. **Caption reviewtags print.** pipeline_full_8pt1col:267, recon_otb_v2_8pt:134, checkerwindow_v4_8pt:172 and resolutiontiming:109 carry red reviewtags in captions (hidden only by switch 2).

# Paper audit guidelines (ISCA-27)

The checklist every paper audit runs against, from grammar up to storyline. It collects Anna's standing directives, each tagged with where it came from. When Anna asks for a re-audit after she edits, give each agent this file plus its slice of the paper. Add every new general directive here the day she gives it, with its date. Paper repo: `~/trippel/ISCA-27` (root `main.tex`, ACM template since 2026-11-10; sections in `sections/*.tex`, bib `sections/references.bib`, figures in `tikz/`).

Tags: "(Anna, date, session transcript)" = her words in a Claude Code session; "(Anna, date, paper note)" = her `\anna{}` or a decided VOCAB note in the paper; a file name = the repo doc that records it; "(suggested)" = an inference, not her words, for her to confirm or edit.

## ⛔ NO PREFETCHING (Anna, 2026-11-11, STRICT, applies to every section)

**Never mention a concept before the section that introduces it.** Each section is self-contained and talks only about its own subject: the model section discusses only the model (execution graphs, the three clauses, the leakage predicate, the STT example), with no synthesizer, Alloy, enumeration, stages, figure stages or tests; the synthesizer section is where the model is encoded in Alloy and solved; the executor section is where tests are run and checked. A sentence that says what a later section will do with this section's content ("which form the synthesizer's input", "Stage 1a enumerates these") is prefetching: cut it. A forward pointer is acceptable only as a bare roadmap in the intro or a section's own roadmap sentence. (Anna: "lets not talk about the synthesizer yet. thats prefetching. we are just discussing the model. i dont want anything to be prefetched")

**Exception for Background (Anna, 2026-11-16, following Caroline's papers):** Background may point forward briefly to where this paper uses or extends a prior concept, e.g., "…which \toolname{} adapts (\S~\ref{formalmodel})". It must not define the paper's own concepts; their full definitions stay in their own section. Precedent:
- TransForm §II: "§III extends the vocabulary in §II-A to incorporate transistency operations";
- Protean §II: "…security contracts (§II-C), which we use to validate our PROTEAN prototypes (§VII-B)";
- RTL2MµPATH §II: "formal definitions that we introduce (§IV-C)";
- Helium §II: "(our focus, §III-A)".

The rest of the rule is unchanged: the model, synthesizer and executor sections still never prefetch later sections.

## ⛔ CONCISE AND ACCESSIBLE (Anna, 2026-11-11, STRICT)

**A normal amount of information, never bloat.** The paper must reach the 11-page limit, and more technical is not better: write for an architecture reader, not a gem5 developer. One proposal per paragraph (never two competing versions of the same text). A bug paragraph is about 100-150 words: what the defense promises, what goes wrong in plain words (at most one file:line), how the tests reach it and under what condition, one headline count. Leave out control experiments, history, alternative counts, internal run names (E2, RL-9, TA-1, fv3), multiple code citations and stacked caveats; if a detail must be kept somewhere, it goes in the simspect docs, with at most a one-line pointer note. (Anna: "dont bloat things with too many details we eventually have to get to this 11 page limit. more technical is not always better we want things accessible.")

**Match section lengths to the model paper (Helium) (Anna, 2026-11-11: "match for length. you can go a bit over on all targets rn but not sooo over").** Targets measured from Helium with pdftotext: Related Work about 250 words (ours: about 450-650, since it carries more prior work), Limitations/Discussion about 1,290 words (ours: about 1,100-1,300). Going a little over is fine for now; not far over. Optional material goes in `\proposed[optional: could be omitted]{...}` and does not count.

## 0. Permissions (hard rules)

- **Paper text is read-only.** Propose prose in a note; Anna pastes. The exceptions are listed below, and outside them a change is a proposal, not an edit. (CLAUDE.md "Paper text is read-only", 2026-10-28)
- **Allowed direct edits:**
  - moving a citation within its own sentence, without a note (2026-11-11);
  - tying citations with `~` (2026-11-11);
  - Title Case in `\section`/`\subsection`/`\subsubsection` titles (2026-11-11);
  - the Stage 1 → 1a and Stage 1.5 → 1b rename (2026-11-11);
  - adding bib entries she names (2026-11-11: `kodkod`);
  - deleting notes that are no longer relevant (2026-11-10);
  - new figure files in `tikz/` (never overwrite an existing figure without her OK).
  - figure edits she names in a decided VOCAB note, e.g. relabeling the pipeline figure's slabs (Anna, 2026-11-03, session transcript: "make the figure edits to the big pipeline figure").
- **Her own asks are not to be deleted.** Leave Anna's `%claude` / `@claude` comments and `\anna{}` notes in place, but find every one on each audit pass and answer it; she noticed when one was skipped ("what happened to my @claude there?"). (Anna, 2026-11-03, session transcript; memory `paper-no-claude-references`)
- **Never write "Claude" anywhere in the paper repo.** Her advisor reads it. That covers notes, comments and commit messages (no Co-Authored-By trailer). Notes render as [Note] through `\reviewnote`; say "project log" instead of `claudelog.md`. (memory `paper-no-claude-references`, 2026-11-04)
- **That includes file names in comments:** cite the project log as "simspect project log <date>", never by its file name `claudelog.md` (three figure comments had it; fixed 2026-11-11). Check with `grep -rni claude sections/ tikz/ main.tex` before every push; Anna's own notes in `oldtechnicaldetails.tex` are hers.
- **Git:** no git writes unless she asks for that action in the current message. A "pull" authorizes committing local work and merging in place; never re-clone (memory `paper-one-clone`). Never push unasked.
- **Never overwrite template settings.** When the class or template changes (IEEEtran → acmart, 2026-11-10), her macros and note switches move over without touching the template's own settings. (Anna, 2026-11-11, session transcript: "i dont want to overwrite any overleaf template settings")
- **Hard calls are hers:** what a claim says, how to frame a bug, what counts as a result. Surface each as a DECIDE note with the options and a labeled recommendation; never bury it in an edit. (CLAUDE.md "Surface the hardest decisions", 2026-10-30)
- **Don't invent names.** No new labels, IDs or naming schemes for bugs, notes or concepts unless she asks; reuse the ones she has. (Anna, 2026-11-09, session transcript: "dont make up naming convetions too eagerly")

## 1. Notes: how to leave a comment

- **Leave `\anna{...}` comments alone.** They are usually notes Anna leaves for herself or for Caroline, not questions for us: do not add notes answering or responding to them unless she explicitly asks us something. (Anna, 2026-11-11; this overrides any earlier "answer each \anna note" instruction)
- Macros (defined in `main.tex`):
  - `\urgentbr\urgentnote{…}` for anything she must act on;
  - `\notebr\reviewnote{…}` for ordinary review notes ([Note]);
  - `\auditnote{cat}{tag}{…}` for audit findings, one color per audit category (fact, claim, figure, writing, cite), so different audits are told apart at a glance (Anna, 2026-11-03, session transcript: "make the different audits different colors of comments");
  - `\labbr\labnote{…}` for notes to lab readers;
  - `\anna{…}` is hers alone.
- **Proposed prose goes in its own paragraph:** `\proposed[what it replaces]{...}` (dark-cyan "[Proposed, replaces: ...]"; the optional argument names the replaced paragraph(s) by their opening words, or says "nothing; new paragraph inserted here"; Anna 2026-11-11: "for all instances", defined in `main.tex`, hidden by switch (5)), placed where the text would go and holding the full text as it would read after acceptance, so Anna accepts by deleting the wrapper. The note next to it keeps only the why, the Source, and what to delete. (Anna, 2026-11-11; replaces the older `\textbf{PROPOSED TEXT}` inside notes)
- **Every factual note ends with `\textit{Source:}`**: the file, doc section or paper page it came from.
- **A note is its own source line, not its own paragraph.** Put each note on a separate line in the `.tex`, but don't open a new paragraph in the PDF (use the `*br` macro, no blank line). (Anna, 2026-11-03, session transcript)
- **Notes she must read go in `\urgentnote`**, so they show with her current switches and she never has to uncomment them. (Anna, 2026-11-09, session transcript: "change those notes to urgent so that i dont have to uncomment them all")
- **Check that notes render as notes.** After a pass, compile and look at the PDF: no note may print inline as if it were body text, and the build has no new errors. (Anna, 2026-11-09, session transcript: "some places where the notes seem to just get inlined and dont look like notes"; `paper_audit_20261110/comment_cleanup_log.md` compile-and-diff check)
- **Moving text between sections:** leave a note in BOTH places, so nothing is lost. The note at the destination carries the moved text, and the note at the origin says where it went. (Anna, 2026-11-11)
- **One topic per note.** Before adding a note, check for an existing note on the same topic and update it instead of duplicating it.
- **Every vocabulary decision gets a VOCAB note** at each place the wording must change, so she can apply it herself. (Anna, 2026-11-03, session transcript: "for all these decisions i tell you make a note where i need to change the vocab")
- **Never lose her text.** A shorter or cleaner proposal keeps every fact of the original, or says where each one went. (Anna, 2026-11-02, session transcript: "DONT lose info"; 2026-11-11 "as long as info gets moved to related work and not lost")

## 2. Storyline and structure

- **No duplication (principle).** Each fact lives in one place: intro, background, body or related work. If it appears twice, pick the home and cut or point to it from the other. (Anna, 2026-11-11)
- **Each bug is described once,** in one spot (Known Bugs Replicated or Unknown Bugs Found), never repeated later in Results. (Anna, 2026-11-10, session transcript: "the bug reports are all in one spot ... and not repeated again"; `results.tex:1`)
- **The intro carries every claim the paper makes later.** That includes: directed/targeted generation; every test contains a protected transmitter; complete up to the instruction bound; uses the simulator's white-box access; no attacker or probe program is needed; narrows the space of tests; checks a defense against its own guarantee; replicates known bugs and finds new ones. Any later claim missing from the intro gets a note. (Anna, 2026-11-11; "no attacker or probe needed" and "whitebox": Anna, 2026-11-11 00:13, session transcript)
- **The intro follows the abstract's last part**, the three components of SimSpect: (1) a formal language for a defense's guarantee, (2) a test generator, (3) a test validator/harness on gem5. Note where it does not. (Anna, 2026-11-11)
- **The end of the intro and the Results section mirror the abstract's order exactly**: known bugs replicated, then each new bug in the abstract's order, then the comparison with prior work. When she rewrites the abstract, re-check both. (Anna, 2026-11-09, session transcript: "i want the structure of the abstract mirrored exacrlyt")
- **Headline results reach the abstract and intro.** Each audit checks that the main Results findings (bugs, the AMuLeT comparison) appear in the abstract and the intro, and notes what is missing. (Anna, 2026-11-03, session transcript: "add comments for stuff im missing in the intro and abstract from the results")
- **Introduce before use.** SimSpect is not described before the sentence that proposes it, and a system (e.g. AMuLeT) is introduced once, not again two sentences later. (Anna, 2026-11-03, session transcript: "before we say we propose simspect we are talking abotu simspect"; 2026-11-11: "amulet then being introed there and then again two sentences later")
- **Validation, not verification.** The paper tests a prototype against its guarantee; it never claims to prove it secure. (Anna, paper note at old `intro.tex:18`, resolved per `paper_audit_20261110/comment_cleanup_log.md`)
- **Background is lean.** It holds only what a reader needs to follow the pipeline and the results: where our contract terms come from, and where the pipeline's ideas come from (axiomatic models, minimal litmus synthesis). Everything else goes to Related Work, with a note at the destination. Audit each background item for necessity, and also for things the results need that it does not explain. (Anna, 2026-11-11, session transcript: "i really cant ge tinto infinite detail"; commit 2d427c5 message)
- **Model paper for flow:** Helium (Archer, Rahmani Fadiheh, Trippel). Anna calls it ASPLOS'26; the local copy is filed as `paper_figures/reference_papers/helium_isca26/` and the PDF shows no venue. It is a good model for intro and background flow and for section structure. Its intro has an "A. This Paper" subsection. Its background opens with a one-sentence roadmap of its subsections. It has a Threat Model and Overview section before the technical sections, and a Limitations and Future Directions section before Related Work. (Anna, 2026-11-11)
- **Prose order matches figure order.** Where a figure lists steps (e.g. the concretization passes), the text explains them in the same order. (Anna, 2026-11-03, session transcript: "make sure the conc thing is clear and in the same order as the figure")
- **Precise "at this stage" claims.** Pensieve model-checks early-stage designs, so a claim of "no principled way" must be scoped to the simulator prototype checked against its own guarantee. (2026-11-11)
- **AMuLeT is checked against a high-level contract, not the defense's guarantee.** Wherever AMuLeT is introduced, say that it tests each defense against one of a few high-level contracts it pairs with the guarantee (CT-SEQ or ARCH-SEQ, AMuLeT p5), which is much coarser than the guarantee and different from it (what a whole program may expose on its sequential path, not which instructions the defense must hold back or which state it claims to protect). State the contrast once each in the intro, Related Work and Results' comparison, and nowhere else. (Anna, 2026-11-11)

## 2b. Discussion and limitations

- **Out-of-scope reports get their own paragraph**, framed as why judging each defense against its own paper is more accurate, e.g. InvisiSpec's MSHR contention (UV2) and STT's stores: these are limits of the defense's scoped mechanism, not implementation bugs, so we mention them but do not count them. (Anna, 2026-10-28 and 2026-11-09, session transcripts; 2026-11-11 "a paragraph on why all th ebugs that are out of scope from amulet are out of scope")
- **A paper's judgment is not a guarantee.** If the defense paper calls a channel "hard to exploit" and promises nothing, a break of that channel (KV2/unXpec on CleanupSpec) stays out of scope. (Anna, 2026-11-09, claudelog 16:40 correction)
- **Every known bug we don't find gets a limitation with its reason,** e.g. Mosier's pending-squash bug on AMuLeT's STT build ("the timing is too precise to show up"). Check first that the bug is present in the build we ran. (Anna, 2026-11-11, session transcript)
- **Coverage limits are separate from scope:** a report inside a paper's claim that our generator cannot yet reach is a coverage limit, not out of scope. (`discussion.tex:41` proposed text; suggested split, confirm)
- **The harness is disclosed and justified:** a Discussion paragraph explains why forcing predictions and stretching timing neither changes the defense nor creates leaks a regular predictor could not produce, and that it is a global setting, not a disallowed modification. (Anna, 2026-11-09, session transcript; `intro.tex:52` paper note; 2026-11-10 "the harness stuff we will disclose")
- **Non-default configurations are explained:** the shrunk caches used for footprint runs get a sentence or two in the Discussion. (Anna, 2026-11-08/09, session transcript, `URGENT_TODO.md` P-1)
- **A Timing and CPU Usage section exists** (timing paragraph plus CPU cost, filled when numbers land). (Anna, 2026-11-10, session transcript)

## 3. Results: how to present bugs

- Full survey: `paper_figures/FIGURES.md` "How related papers present their bugs (2026-11-11)".
- **New bugs** each get a bold-headed paragraph: what the defense claims, the root cause (gem5 file:line), how a test reaches it, and whether it is an implementation bug or a design flaw. Only 2–4 flagship bugs get a figure.
- **Known bugs** get one paragraph, table rows and the first-detection chart. No figures.
- **List only bugs our tests found** in the bug table. Bugs found only by source audit go in Discussion. An audit finding is reported only if SimSpect's own pipeline finds it; no hand-written gadgets count. (Anna, 2026-11-08, `URGENT_TODO.md` DECIDED; 2026-11-09, session transcript: "only if we can find it with our thing otherwise we shouldnt report")
- **Our bug IDs must not collide with AMuLeT's UV1–UV6.** AMuLeT's bugs carry an `A-` prefix (A-UV1…). A prefix for ours is still Anna's decision.
- **Every bug claim states its condition.** Examples: opt-in timing (the visibility-point/squash race needs a longer commit-to-IEW delay); a cold cache (A-UV3); an opt-in corpus (RMW, generated `jmp`s). A hit that shows the mechanism on a non-secret value (UV5's constant stack slot) says so. (claudelog 2026-11-10 15:20 "disclose")
- **Scope:** each defense is judged against its own paper's guarantee, and each checker checks only the structures that paper claims to protect. Every "out of scope" claim cites the defense paper's page and section. (Anna, 2026-10-28 and 2026-11-08, session transcripts: "only check the structures that the paper actually says")
- **Defenses in the paper are the authors' official prototypes** (e.g. NDA/DoM/Doppelganger only if they come from the ReCon authors' tree), run with the authors' prescribed flags. (Anna, 2026-11-09, session transcript)
- **Results text is certain or absent.** In a draft for readers, uncertain wording in Results is removed (and the removal reported to Anna), not hedged. (Anna, 2026-11-03, session transcript, lab-review draft; suggested as standing)

## 4. Numbers

- **Every number traces to a doc:** `simspect/wiki/state/EVAL_MANIFEST.md` (footprint part 7 complete run, part 9 same-estimator table) or `claudelog.md`. Cite the doc in the note.
- **Every reported number has a replication snapshot**: the exact settings and pipeline files used are saved, so the experiment can be rerun after the code changes. (Anna, 2026-11-10, session transcript: "save these results somewhere and the exact settings in some kind of snapshot")
- **Comparisons use one estimator on both sides.** The first-detection figure uses (N+1)/(K+1) for SimSpect and AMuLeT: UV5 about 18×. The intro's 23× uses the older mixed estimator. One number throughout, everywhere.
- **Report time, not CPU (Anna, 2026-11-11):** wall-clock time to detection at equal core counts, using per-test run time (build, gem5, Inspector; single-threaded, so wall = CPU per test), with generation stated separately as a one-time cost per corpus, shared by every defense build and reusable after a patch. Say that AMuLeT's time already includes its own generation. Source: EVAL_MANIFEST footprint part 8, check 6.
- **Report tests per detection,** the (N+1)/(K+1) rate estimate, not the literal first-detection index in seed order, which is noisy (A-UV5: test #7,430 on one corpus, #2,339 on the other). (Anna leaning, 2026-11-11: "the latter seems less noisy"; the figure already plots it; renaming its caption from "first detection" is still her call)
- **The comparison unit is tests,** counted for both tools (AMuLeT's per-input test cases stated alongside), and the abstract's single number is the **minimum** multiple across bugs. (Anna, 2026-11-10, session transcript: "im inclined to do #tests ... ill do the minimum for the abstract number")
- **Comparisons run one fanout version per defense** with every fanout extension on, and random cache setups per test rather than the best-case setup. (Anna, 2026-11-10, session transcripts)
- **No `[N]` placeholder survives** a pass without a note saying where its number will come from.

## 5. Terminology

- **Stage names:** Stage 1a (minimal violating graphs), Stage 1b (graphs grown under loosened minimality), Stage 2 (concretization), Stage 3 (gem5 run and check). Never "Stage 1" or "Stage 1.5" for those. Stage 1a is "bounded exhaustive enumeration" and Stage 1b "non-exhaustive enumeration". (Anna, 2026-11-02, 2026-11-09, 2026-11-11; `URGENT_TODO.md` DECIDED 2026-11-02)
- **Defense specification = three parts with decided names:** the **execution contract** (what speculation the defense considers; Anna: "the term that other work uses to broadly characterize the allowed execution"), the **protection set**, and the **leakage contract** (transmitters and their unsafe operands, as SynthLC uses the term; her least certain choice). Together they form the **leakage predicate**. The pipeline figure's slabs were relabeled to these names. Older text still says "speculation contract" and "leakage function" (the `.als` names); flag each in prose. (Anna, 2026-11-02 and 2026-11-03, session transcripts; `FIGURES.md` "Reviewer terminology feedback")
- **Applied 2026-11-11 (Anna: "please change to execution contract and leakage contract directly, you have permission"):** our "speculation contract" became "execution contract" and our "leakage function" became "leakage contract" in prose and notes. Exceptions kept on purpose: Revizor's own term "speculation contracts" when describing Revizor, and the Alloy predicate name `leakage_function` when naming code.
- **"Leakage contract" is SynthLC's sense, not AMuLeT's.** Say so where the term is defined: a defense's own fine-grained statement of which instructions transmit which operands (SynthLC~\cite{rtl2upath} p4: STT and SPT "have the same fine-grained leakage contract"), unlike AMuLeT's sequential contracts (CT-SEQ, ARCH-SEQ). (Anna, 2026-11-11)
- **Separate our vocabulary from prior work's.** Guarnieri et al.'s are "hardware–software contracts" (their own name), with speculative non-interference cited to Spectector; AMuLeT's detections are "contract violations" (its Def. 2.1); the observation clause is a different concept (what the attacker observes in µarch state), so it does not map onto our leakage contract. Note where the paper should state the difference, ideally in Background. (Anna, 2026-11-02/03, session transcripts; VOCAB notes `related.tex:29`, `:91`)
- **violation / hit / leak / bug are four stages:** a violation is an abstract graph that breaks the leakage predicate; a hit is a test the checker sees transmit inside the violation window; a leak is a confirmed hit; a bug is a leak the defense should have blocked. Alloy outputs "violating execution graphs", never "leaking". (Anna, VOCAB notes `pipeline.tex:137,196,211,220`; 2026-11-03 pasted URGENT VOCAB)
- **Two windows, two names (Anna, 2026-11-11, replaces the 2026-11-03 "one window" rule):** the **speculation window** is when speculation is open, in the abstract sense (e.g. a resolve-stall slides it; defenses aim to be secure for any speculation window); the **violation window** is when every condition the checker enforces holds (committed instructions, unresolved branches; ends when fnc retires or a guarding branch's squash lands), i.e. everything in the enforcement realm. "Speculative window" is not used. Whether the paper should keep both names is still an open question for Anna (an `\anna{}` note at the violation-window definition, `pipeline.tex`). Terms consolidated in body sections 2026-11-11.
- **Define every relation and acronym before use:** spo (speculative program order), rf (reads-from), ddi ("data dependence internal" everywhere), resolved, committed, HSCD. YArch'26 reviewer #71A asked exactly this for rf/ddi. (Anna, 2026-11-03, session transcript; VOCAB notes `model.tex:25,29,37`; `FIGURES.md` "Reviewer terminology feedback")
- **Resolved** means the defense knows the outcome; a branch that has executed but not yet squashed its wrong path is still unresolved. (Anna, 2026-11-08, VOCAB note `model.tex:29`)
- **Other decided terms:** "transmission criterion" (not "mechanism"; W-9, Anna 2026-11-16); "Kodkod model finder"; "Inspector"; "store bypass" for the STL speculation primitive; "a load mispredicts no-alias", and "mispredict" rather than "predict" wherever that is what happens; "speculation directives" and "timing directives"; "defense implementation under test"; "validating the security guarantee"; scheme 1 on the ReCon builds is "NDA"; lowercase instruction ids `i0`. (Anna, 2026-11-02 / 2026-11-03 / 2026-11-08, session transcripts; `URGENT_TODO.md` DECIDED; `FIGURES.md` Glossary "Already decided by Anna")
- **Do not use "DSL".** (Anna, 2026-11-11; resolves the 11-02 vs Glossary conflict.) Say "the \toolname{} language" or "specification language".
- **Component names follow the abstract:** specification language, synthesizer, executor; tests are security litmus tests paired with a target execution. (Anna, 2026-11-11: "the abstract is good. lets try to put those terms more and consolidate. use the glossary.")
- **Side channels only in the opening, then Spectre:** "HSCA/HSCD" appear only where the intro sets up hardware side channels in general; everywhere after, say Spectre attack(s)/defense(s). (Anna, 2026-11-11)
- **"Security guarantee" everywhere** (not advertised/promised/stated guarantee); "its own" only where it contrasts with a generic property. (Anna, 2026-11-11)
- **AMuLeT contrast, full version only in Related Work (and once in Results):** high-level contract (CT-SEQ/ARCH-SEQ) coarser than and different from the guarantee; random tests; four of its nine reports fall outside the defenses' security guarantees. The intro keeps at most one neutral sentence (Anna: the rest "seems too mean" for the intro). (Anna, 2026-11-11)
- **The component that judges a run is the Inspector** (the pipeline figure's name; Anna 2026-11-02, confirmed 2026-11-11): say "the Inspector" in prose, not "the checker"; code names (`check_ld.py`) stay. A detected event is a **hit**; a confirmed real defect is a **bug** (the figure's bug icon says "Bug?", since a hit can turn out to be something else). (Anna, 2026-11-11)
- **Glossary decisions (Anna, 2026-11-11, "sounds good for the terminology"):** annotation = the `.ann.json` file, directive = what it tells the simulator, hook = the gem5 source site, no "knob"; "leakage backbone" everywhere, glossed at first use; "execution graph" for the Alloy object, "target execution" only for what a test is steered toward; Synthesizer/Executor prefixes on the pipeline section's headings; keep both window names. Recorded as DECIDED notes in the paper, to apply when editing.
- **Timeline figures share one treatment** (Anna, 2026-11-11): a cycle axis with ticks at each event and faint dotted lines rising through every row; each window bar's opening and closing are tied to the events that cause them, labeled with the cause (e.g. "speculation primitive, forced by its annotation, opens it"; "lc retires"; "squash lands"). Applies to the race, checker-window and trace figures.
- **One name per concept everywhere** (consolidation groups in `FIGURES.md` "Glossary" → "Consolidate or define": leakage backbone, interleaving, directives/hooks/knobs/annotations). Flag synonyms; the recommendations there are not yet her decisions. (`FIGURES.md` "Glossary", 2026-11-02)
- **Defense names:** use each paper's spelling (InvisiSpec, CleanupSpec, SpecLFB, ReCon, STT, SPT, NDA, DoM, SDO); `\toolname{}` for SimSpect; gem5 in lowercase.
- Previous terminology feedback from YArch'26 reviewers: `paper_figures/FIGURES.md` "Reviewer terminology feedback".

## 6. Citations

- **Tie every citation with `~`** (`word~\cite{x}`) so a line break never strands it. Never glue `\cite` straight onto a word. Merge adjacent `\cite{a}\cite{b}` into `\cite{a,b}`. (Anna, 2026-11-11)
- **Cross-reference format is fixed: `Fig.~\ref{}` for figures, `\S~\ref{}` for sections, `Table~\ref{}` for tables.** Never write `Sec.~\ref`, `Section~\ref` or `Figure~\ref`, and always put the tie `~` before `\ref`. (Anna, 2026-11-16, pasted directive "You need to do: Fig.~\ref{todo} for figures, \S\~\ref{todo} for sections, Table~\ref{todo} for tables". The `\~` in the paste is read as a stray escape for `~`, since `\~` in LaTeX is a tilde accent.) As of ISCA-27 `d1e84bb`, outside comments: 25 `Sec.~\ref` to convert, 3 `\S\ref` missing the tie, while the 25 `Fig.~\ref` and 5 `Table~\ref` already conform.
- **Cite right after the thing it supports** when that is mid-sentence, e.g. "AMuLeT~\cite{amulet} runs …" or "STT~\cite{yu2019stt} and SPT~\cite{spt}". Trippel-lab papers do this for 38–88% of their citations. Moving a citation within its sentence needs no note. (Anna, 2026-11-11)
- **Cite the tools we build on:** Alloy (`jackson2002alloy`), Kodkod (`kodkod`) and SAT4J (`sat4j`, its requested citation: Le Berre & Parrain, JSAT 7, 2010) together where the paper says what solves our models (`pipeline.tex` Test Generation, done 2026-11-11); gem5 (`gem5`). We use Alloy 6.2 with Kodkod and SAT4J, not AlloyStar (memalloy uses AlloyStar); whether to use AlloyStar is an `URGENT_TODO.md` item.
- **Citing code:** cite the repository as a `@misc` bib entry pinned to the exact commit (author = the code's author from `git log`, title naming the repo and commit, `howpublished` = the commit-pinned URL), and give the file and line in the text, e.g. "(`rob_impl.hh:229` at commit e3283b9 of the STT repository~\cite{sttrepo})". A fix or bug report that lives in one commit gets its own entry (`nickscommittoSTT`). Never cite the defense paper for an implementation detail it does not contain. (Anna, 2026-11-11)
- **Cite originals.** The original Spectre paper, the original Guarnieri contracts paper, SynthLC, and Mosier's LCM, not only later work that uses them. (Anna, 2026-11-03, session transcript)
- **Bib hygiene:** no duplicate entries; replace an arXiv entry with its published version when one exists; flag any broken entry whose fix is not obvious. (Anna, 2026-11-03, session transcript)
- **Related Work proposes generously.** Suggest more papers than needed (MCM and axiomatic formalization: Wickerson, Lustig, Simner; speculation execution modeling; the HW Spectre defenses), each as a note she can accept, and prompt her about every paper we could cite and have a bib entry for. The intro's list of HW defenses stays lean. (Anna, 2026-11-03, session transcript)
- **Real sources only.** A claim about a paper cites the page and section actually read. Never cite from memory. (CLAUDE.md "Real sources over memory")
- A deep citation pass (every citation relevant, none missing or wrong) is an `URGENT_TODO.md` item (Anna, 2026-11-11).

## 7. Headings and formatting

- **Title Case for every word** in section, subsection and subsubsection titles: "Known Bugs Replicated", "Comparison With Prior Work". The only exceptions are lowercase names (gem5, x86), "vs.", and code in `\texttt{}`. (Anna, 2026-11-11)
- **Every section, subsection and subsubsection carries a `\label{sec:...}`** so it can be cited; new headings get one when added. (Anna, 2026-11-11)
- `Fig.~\ref{…}` and `Table~\ref{…}`, with a tie, and the right word for the target (a table is not "Figure"). (`model.tex:41` audit note)
- Spell out numbers under ten in prose ("three types", not "3 types"). (suggested; confirm)

## 7b. General writing vibes (suggested house style; Anna confirms or edits)

- **One term per concept, defined before first use.** A new word for an old thing reads as a new thing (the YArch reviewers flagged this).
- **Lead with the claim, then the evidence.** Every paragraph opens with its point, and every claim in Results carries a number and its condition.
- **Short, concrete sentences in active voice:** "SimSpect forces each branch's prediction", not "predictions are forced". YArch reviewer #71A asked us to avoid long, winding sentences. (`FIGURES.md` "Reviewer terminology feedback")
- **Name the thing, then cite it.** No sentence starts with a bare citation.
- **No stacked hedges** ("may potentially"), no "we believe" for things we measured, no "novel" or "first" without the closest prior work named next to it.
- **No forward references to undefined terms.** If the intro needs a term the background defines, give a one-clause gloss in the intro.
- **Every figure and table earns its space.** It is referenced, and it says something the text does not.
- **Say what a figure abstracts.** If a figure shows a step in a different stage than before (e.g. interleaving in Stage 2), the text says so. (Anna, 2026-11-02, session transcript: "its fine id the interleaving is in stage 2 as long as we say that"; suggested as general)

## 8. Figures

- **Text size and layout:** 8pt minimum for all text, including arc and edge labels (rf, ddi, arrow labels), multiplicities, icon glyphs and subscripts (write `r0`, not `$r_0$`). Single column, full column width; she rejected a double-wide pipeline. Dense, but nothing overlaps; squeeze spacing rather than cut words, and never `\resizebox`. (Anna, 2026-11-02, session transcript; memory `paper-figure-style`; `plans/VISUAL_LANGUAGE.md` CURRENT RULES, which supersede its older 7pt and gray-only sections) Check it on the built PDF, not the source: `paper_figures/scripts/figfont_audit.py main.pdf` (needs PyMuPDF) prints the rendered sizes inside every figure; 8pt is 7.97 bp, and the 6pt review-mode margin numbers and 7pt running header are not figure text. Math superscripts (`$10^2$`, `$^{\dagger}$`) render at 6pt, so write tick labels as 100, 1k, ... and marks as `$^{\textstyle\dagger}$` (Anna, 2026-11-14: "make sure the figure text even in figure 1 is never too small").
- **Professional and minimal:** TikZ defaults where possible, minimal fonts, one arrow type, no random accent colors; list items sit inside one box, not one box each. (Anna, 2026-11-02 and 2026-11-03, session transcripts: "want minimal colors not stupid colors", "make the first figure not be random arrows just make one type of arrow")
- **Colors:** light semantic fills, with text in black:
  - blue = defense-specific;
  - tan = speculative;
  - lavender = protection set;
  - red = transmitter or bug.

  Figures must read in grayscale. Palette: `tikz/sscolors.tex`. (memory `paper-figure-style`; `paper_figures/plans/VISUAL_LANGUAGE.md`)
- **Speculative rows get a tan background band**, not a different text color. (Anna, 2026-11-03, session transcript)
- **Flags only where they mean something:** resolved/unresolved annotations appear only on instructions where they matter (branches, and stores under store bypass), but an unresolved speculation primitive is always labeled *unresolved*. (Anna, 2026-11-03, session transcript)
- **Shape = type:** stages are distinct rounded blobs, not lines across the figure; outputs between stages share one visual treatment and show their multiplicity; gem5 is a container with the logo, the defense build under test inside and a thin harness ring, so the harness reads as a small addition to the defense build; bugs are one bold bug icon. Don't spread content horizontally or squash it for no reason. (Anna, 2026-11-02, session transcript; `plans/VISUAL_LANGUAGE.md`)
- **Corners = kind of box (Anna, 2026-11-15):** properties (security contracts, defense specifications, litmus tests) get sharp corners; tools (AMuLeT, the synthesizer, the executor) get rounded corners with one shared outline (black, 0.6pt). The defense implementation is sharp too (Anna, 2026-11-15, ISCA-27 commit c9f8550), so only tools are rounded. The shape carries the distinction in grayscale, where the green and blue fills look nearly the same. First applied in Fig. 1 (`tikz/intro_threelayer_v9.tex`, ISCA-27 commit 33d0eea).
- **No legend box;** the caption explains colors and notation. (Anna, 2026-11-02, session transcript: "i dopnt like the legend at the top of the figure"; `plans/VISUAL_LANGUAGE.md`)
- **Breathing room:** margins inside every figure, and space between the figure and the text around it. (Anna, 2026-11-02 and 2026-11-03, session transcripts: "these generally need more margins", "why is the text so close to figure")
- **The intro figure gets across the problem only:** concise, clear, well designed, and says "prior work" rather than naming AMuLeT. (Anna, 2026-11-02, session transcript)
- **Flagship bug figures pair an execution graph with the pipeline trace** in the shared notation. (Anna, 2026-11-03, session transcript: "the race needs a pipeline and the forwarding one also needs a graph")
- **Fit the page:** every live figure fits the 241pt column and the page height with its caption.
- **Each figure is referenced in the text**, and every caption number matches the current data.
- **Every figure worth keeping is visible in the paper;** figures not yet redesigned or still uncertain go at the end of the paper until placed. (Anna, 2026-11-02 and 2026-11-03, session transcripts)
- **One copy per figure in the repo:** once the current version is in, superseded versions that will definitely not be needed are deleted from `tikz/`, so no redundant copies remain. (Anna, 2026-11-11, session transcript)
- **Every label in a figure has a source** (code, md or paper), recorded in the figure's plan file. (`plans/VISUAL_LANGUAGE.md` "Provenance")

## 8b. Captions

- **Caption layout = the ACM template default.** No `\captionsetup`, no manual centering or alignment overrides. (Anna, 2026-11-11, resolves "why is the caption centered")
- **Captions** state what the figure shows. Long explanations go in the text.
- **Start from her caption.** When a figure is redone, pull her existing caption first and keep its content. (Anna, 2026-11-03, session transcript: "pull my caption first")
- **A changed caption or text is marked** with a red TODO so she sees it. (Anna, 2026-11-03, session transcript: "if you cnage a captoin or text be sure to mark it wiht a red todo")
- **The caption explains the example**, e.g. a graph shown for STT says why it is an STT violation. (Anna, 2026-11-03, session transcript; suggested as general)
- **Proposed captions live in `FIGURES.md`** and `drafts/captions/<name>.tex`; previews leave space for the caption instead of rendering it. (Anna, 2026-11-02, session transcript; `plans/VISUAL_LANGUAGE.md`)

## 9. Reviewer-level checks (run on every full audit)

- Substance: does the evaluation support each claim, and is the novelty stated against the closest work (AMuLeT, Pensieve, CheckMate, Revizor)?
- Storyline: does every section serve the thesis, in order?
- Threats: bounded completeness, the hand-written specifications, harness interventions, timing-dependent bugs, the estimator for the AMuLeT comparison, CPU cost per test vs AMuLeT's (`URGENT_TODO.md` DG-1).
- Pre-emption risks to check: the Kvalsvik DataPort abstract (ReCon multi-source), Cheng'26 (STT/SPT bypass), SPT PRs #4–#6.
- Glossary pass: every term defined once, before use, and used one way (Anna, 2026-11-03, session transcript: "audit for glossary pass ... if stuff is not defined well or messy").
- Treat incomplete parts by extrapolating them as best as possible rather than flagging that they are incomplete. (Anna, 2026-11-11, session transcript)

## 10. Directive log

- 2026-11-16: Protean's pending-squash bug is never called a "race" (Anna: "the protean bug should NEVER be called a race that is not what it is. fix this every time!!"); it is the pending-squash timing leak; "race" is only UV6.

- 2026-11-16: not harsh on prior work; not defensive; do not pre-empt reviewer criticism; state obvious truths plainly.

- 2026-11-16: every pipeline design decision has at least one independent justification (not the bug it found); no targeting framing; no back-references from bugs to the mechanism that found them.

- 2026-11-16: "targeted" means a test contains a leakage (its graph violates the leakage predicate), never that a test chases a bug (Anna: "targeted testing means there is some leakage in the test ... not like we are chasing down a bug"). RMWs, `jmp`s and other instruction forms are justified as part of the general concretization vocabulary, not one by one ("just include them in the general explanation of concretizations").

- 2026-11-16: every claim resting on another section gets a \S~\ref; every claim from a paper gets a pinpointed \cite[\S X]; never add `\anna{new sec reference}` marker notes (all removed 2026-11-16).

- 2026-11-16: never overclaim: every statement must be scoped to its evidence; flag absolutes (always/every/never/only/first/guarantees) and general-sounding rates; overclaiming puts reviewers off.

- 2026-11-16: never start a figure or table caption with a bold title sentence (Caroline hates it); plain sentences only. Applies to every proposed caption.

- 2026-11-16: every action-item fix quotes the exact current text it replaces (verbatim, unique in the file), then the new text (`old` → `new`); Anna finds items by searching, since line numbers go stale immediately. Line numbers are only a secondary hint.

- 2026-11-16: every problem a review raises must have a matching action item with a concrete fix, big or small, unless it is no longer relevant; reviews list what they don't carry over, with a reason (Anna: "make sure theres a corresponding action item that will fix each problem").

- 2026-11-16: Reviews and action items are organized per section (Anna, 2026-11-16): each full review goes in its own file `paper_figures/caroline/reviews/<YYYY-MM-DD_HHMM>_<section>.md`, linked from the index `paper_figures/caroline/REVIEWS.md` under the section's heading (several reviews per section allowed, newest first; mark older ones superseded). Action items go in `paper_figures/caroline/REVIEW_ACTION_ITEMS_<SECTION>.md` (e.g., INTRO, BACKGROUND, MODEL, PIPELINE, RESULTS, DISCUSSION, RELATED), also linked from the index.

- 2026-11-16: NO PREFETCHING loosened for Background only. Short forward pointers to where the paper adapts a prior concept are fine, as in Caroline's papers (TransForm, Protean, RTL2MµPATH, Helium); own concepts are still defined only in their own section. (Anna: "update it the rule", after "just generally i want you to look at other papers carolines on".)

- 2026-11-16: no rewrites for the intro (Anna: "im not doing any rewrites for intro"). Review feedback reaches Anna as targeted action items in per-section `paper_figures/caroline/REVIEW_ACTION_ITEMS_<SECTION>.md` files ("give me feedback via the action items"), not as paragraph rewrites or dense per-sentence tables.

- 2026-11-16: FP registers and direct `jmp`/`call` are part of the general pipeline, not special conditions. Stage 2 draws FP (xmm) registers from the same concretization vocabulary as GPRs, and `jmp`/`call` are ordinary random-instruction vocabulary. So bugs (1) STT xmm4 taint and (5) SpecLFB jmp shadow need no disclosed non-default condition, and reviews must not flag them as such (Anna, on be-caroline intro review W4). Conditions that still need stating: (6)'s `commitToIEWDelay` > 1; (3)'s swept resolution delay, not yet ruled on.

- 2026-11-16: cross-reference format `Fig.~\ref{}` / `\S~\ref{}` / `Table~\ref{}` (rule under citations above). The same day Anna queued a comprehensive citation sweep (`URGENT_TODO.md` "deep citation pass"): section refs to where things are defined, regular cites, and pinned sections in cited papers wherever possible.

- 2026-11-15: Fig. 1 v9 (`tikz/intro_threelayer_v9.tex`) plus the intro are the reference vocabulary for terminology audits (Anna: "audit the whole paper for places where my language no longer matches the language that we have in the figure 1 and intro"). Where they conflict with §5 (e.g. Fig. 1 gives STT's leakage contract as "CT with conditions", parallel to an observer mode, while §5 says the leakage contract is SynthLC's sense), flag it as a DECIDE note rather than picking a side. Background was also audited against Protean's Background that day (notes in `background.tex`).
- 2026-11-11 (later): execution contract / leakage contract applied directly; no "DSL"; speculation window vs violation window are two things (open question kept as an \anna note); cite Kodkod with SAT4J; code citations pin a commit and give file:line; captions follow the ACM default; discussion uses bold run-in paragraphs (Helium style); new discussion points on predictor-specific protection and no observation-model filtering.
- 2026-11-11 (latest): AMuLeT = high-level contract, coarser and different, hammered at first mention; leakage contract in SynthLC's sense; abstract's component names everywhere; CPU multiples on run time only; tests per detection over first detection; labels on every heading; name Alloy with Kodkod and SAT4J and leave AlloyStar out of the paper.
- 2026-11-15: sharp corners for properties, rounded corners for tools, in every figure (Fig. 1 first).
- 2026-11-14: contract and mode names (ARCH-SEQ, CT-SEQ, CT, ARCH, SEQ, COND) always through `\contract{}` (typewriter, as AMuLeT and Protean set them), in text and figures; never "(ARCH, SEQ)" pairs.
- 2026-11-14: ISCA 2027 rules (iscaconf.org/isca2027/submit/guidelines.php and the template ISCA2027_ACM_template/main.tex, read 2026-11-14) give no numeric figure-text minimum: "Ensure that the figures and tables are legible", colors distinguishable in grayscale, ACM sigconf, "Do not modify margins, fonts, or line spacing", 11 pages plus references. Anna asked for a 7pt trial of Fig. 1 v8.
- 2026-11-14: figure text never too small, Fig. 1 included; audit the rendered PDF (superscripts count); background explains CT-SEQ-type security properties (proposed).
- 2026-11-11: tilde ties; mid-sentence citations; Title Case headings; Stage 1a/1b everywhere; intro carries all later claims (incl. no attacker or probe, white-box use); intro follows the abstract's three components; background lean with moves to Related Work noted at both ends, audited for necessity; no duplication; AMuLeT introduced once; Helium as the structure model; a deep citation pass later; out-of-scope paragraph for AMuLeT's bugs; limitation for Mosier's pending-squash bug (timing too precise); delete superseded figure versions; don't overwrite template settings; reviewers extrapolate incomplete parts.
- 2026-11-10: delete notes that are no longer relevant; each bug described once; Timing and CPU Usage section; comparison unit = tests, abstract number = minimum multiple; one fanout version per defense, random cache setups; replication snapshot for every reported number; disclose the harness.
- 2026-11-09: end of intro and Results mirror the abstract's order exactly; Discussion paragraphs on out-of-scope bugs (more accurate to the papers), predictor/timing forcing soundness and cache sizes; urgent notes for anything she must read; check notes render as notes; don't invent naming conventions; report only findings our pipeline finds; official author prototypes and flags only; KV2 out of scope (a paper's judgment is not a guarantee).
- 2026-11-08: NDA name for scheme 1; resolved excludes executed-but-unsquashed branches; check only structures the paper claims; shrunk caches explained in the paper.
- 2026-11-04: no "Claude" in the paper repo (incl. commit trailers); one clone.
- 2026-11-03: figure palette (light semantic fills); speculative tan band; flags only where relevant; one arrow type; margins and space around figures; flagship bug figures = graph + trace; pull her caption first; red TODO on changed captions/text; proposals labeled with what they replace; notes on their own line, not paragraph; different audit colors; glossary pass; VOCAB note per decision; execution contract / leakage contract / leakage predicate; violation window; violation vs hit; ddi = data dependence internal; mispredict wording; store bypass; cite originals; bib hygiene; generous Related Work proposals, lean HW defense list; introduce SimSpect before describing it; headline results in abstract and intro; answer her @claude asks.
- 2026-11-02: 8pt minimum for all figure text incl. arc labels; single-column, full-width figures; minimal professional style; no legend box; shape language; intro figure shows the problem and says "prior work"; say where a figure's step happens (Stage 2 interleaving); never lose her text; proposed captions in FIGURES.md; transmission criterion, Kodkod model finder, Inspector, bounded exhaustive / non-exhaustive; speculation and timing directives; observation clause is separate; execution contract is the right term.
- 2026-10-30: hard calls go to Anna as DECIDE notes.
- 2026-10-28: paper text read-only; new figure files OK; out-of-scope = limits of the defense's scoped mechanism, not bugs.

# Citation audit, ISCA-27 (2026-11-16)

Checked against ISCA-27 `04e7347` (compiled into a scratch dir; cited keys from `main.aux`, live `\cite`s located by a script that skips `%` comments and `\iffalse` blocks, recursing into `methodology.tex` → `model.tex`, `pipeline.tex` and the figure files). Paper untouched, no git writes. Every "old" string below occurs exactly once in its file (`grep -c -F`). Comparison set: Caroline's recent full papers cite 56–152 works (Protean 152, Serberus 125, Pandora 122, Counterpoint 120, RTL2MµPATH 102, Helium 101, ITHICA 100, LCM 83, CheckMate 66, TransForm 56).

## (a) Summary

**170 distinct works are cited; 124 of them in Related Work, and 112 only there.** The overrun is almost entirely Related Work: outside it the paper cites 58 works, all of them used for a specific claim.

**Counts per class (170 keys):** 43 KEEP-ESSENTIAL, 77 KEEP-SUPPORTING, 48 PADDING, 2 WRONG metadata (`blackbox`, `perple`; both claims are fine). One more citation is incomplete rather than wrong (W1, the SPT pending-squash fix). No citation was found that does not support the claim it is attached to.

**Projected total after the cut list (C1–C10): 170 − 48 = 122**, or 123 if the missing SPT fix (W1) is added. With the two optional cuts O1–O2, 120–121. That sits between RTL2MµPATH (102) and Counterpoint/Pandora (120–122), and below Protean (152) and Serberus (125). Related Work would go from 124 to 77 distinct works (still the most-cited section, as it is in Protean and Serberus).

**Where the 48 cuts come from:** "many others" defenses list −13 (C10), the testing paragraph −13 (C2–C4), software analyses and secure compilers −8 (C5), RTL verification −4 (C7), MCM formalizations in Background −4 (C1), litmus-test paragraph −5 (C8–C9), semantics −1 (C6). No essential citation is cut: the six defenses, their code and fix commits, AMuLeT, Protean, CheckMate, LCMs, Guarnieri et al., Alloy/Kodkod/SAT4J, gem5, LLVM, Spectre, Half&Half, the Intel SDM, DOLMA, NDA and every pinpointed citation all stay.

**Related Work verification (Anna's scope extension):** all 124 Related Work keys were checked against the cited work (local PDFs/texts, Crossref DOI records, arXiv, USENIX/NDSS/GitHub pages; dblp refused automated access). Every claim is supported and every pinpoint (AMuLeT §3.2, §3.3; Protean §VII-B4b, §VII-B4c; Kvalsvik thesis §4.3) points at the right section. Findings: W1–W3 below plus five weak fits, three of which are already in the cut list. Full per-citation verdicts are in section (e).

**How to apply the cuts (Anna's comment-out rule):** each Related Work paragraph is one physical line, so a `%` mid-line would comment out the rest of the paragraph. For a pure citation trim, put one comment line directly above the paragraph listing the removed keys, e.g. `% [citation trim 2026-11-16] removed: oleksenko2026enterexit, ...` (the same style as `related.tex:6–7`). Where a clause is cut (C2, C8), the new text below already comments it out on its own line.

**DECIDE (for Anna):**

- **CITE-1, how far to cut:** (a) C1–C10 → 122–123 (recommended: lands at Caroline's 100–125 band and touches no claim); (b) C1–C10 plus O1–O2 → 120–121; (c) keep the long lists but drop only "many others" and the compiler dump (C5 + C10) → 149, still near Protean's 152, her highest.
- **CITE-2, W1 SPT fix:** (a) add `mosier2025sptpr4` so "both since fixed" cites both SPT fixes (recommended; +1 reference); (b) credit the SPT pending-squash fix through `\cite[\S VII-B4b]{protean}` instead.
- **CITE-3, C10 representatives:** which four defenses stand for "many others". Recommended: the four that Protean's own Related Work names (ProSpeCT, Levioso, SafeBet, Perspective); alternatives with more recent venues are Cassandra (ISCA'25) and SpecASan (ISCA'25).

## (b) WRONG / incomplete findings

### W1. "both since fixed" cites only one of SPT's two fixes (related.tex:19), incomplete

The sentence names two bugs found by Protean, a pending-squash timing leak in STT **and SPT** and an SPT untaint bug, then says "both since fixed~\cite{nickscommittoSTT,mosier2025sptpr6}". `nickscommittoSTT` is the STT pending-squash fix (github.com/cwfletcher/stt/commit/18e304f, "fix pending squash bug", exists) and `mosier2025sptpr6` is the SPT untaint fix (FPSG-UIUC/SPT PR #6, "taint all registers at rename", merged 2025-12-14). The SPT pending-squash fix is a separate pull request, FPSG-UIUC/SPT PR #4 ("fix pending squash bug", merged 2025-12-14; Protean cites it as ref [93]), and it has no bib entry. Checked on the GitHub pages (read-only) and in `protean_hpca26.txt`.

Fix (option (a) of CITE-2). New bib entry:

```bibtex
@misc{mosier2025sptpr4,
  author = {Nicholas Mosier},
  title = {{SPT}: Fix pending squash bug},
  howpublished = {GitHub Pull Request \#4, FPSG-UIUC/SPT, merged December 2025},
  url = {https://github.com/FPSG-UIUC/SPT/pull/4},
  year = {2025}
}
```

Old (related.tex): `both since fixed~\cite{nickscommittoSTT,mosier2025sptpr6}` → New: `both since fixed~\cite{nickscommittoSTT,mosier2025sptpr4,mosier2025sptpr6}`

Related check: `discussion.tex:50` says "our SPT build ... predate[s] the fix" but cites only the STT commit for "the fix"; with PR #4 in the bib, that sentence can cite it too (proposal only; the sentence is otherwise correct).

### W2. `perple` has no venue (bib only)

The entry is `@inproceedings` with no `booktitle`, so it prints with no venue (BibTeX warning "empty booktitle in perple"). Crossref: MICRO 2020 (53rd), pp. 329–341, DOI 10.1109/MICRO50266.2020.00037. Fix in `references.bib`: after the `title = {{PerpLE}: ...},` line add `booktitle = {2020 53rd Annual IEEE/ACM International Symposium on Microarchitecture (MICRO)},`.

### W3. `blackbox` lists two non-authors (bib only)

The Computer article "Formal Verification for Secure Processors: A Guide for Computer Architects" (Computer 57(10):138–143, 2024, DOI 10.1109/MC.2024.3434848) is by Mengjia Yan, Thomas Bourgeat and Sharad Malik only (Crossref record and Princeton portal). The bib adds "Jones, Timothy and Mullins, Robert", most likely the column editors. Fix in `references.bib`: `author = {Yan, Mengjia and Bourgeat, Thomas and Malik, Sharad and Jones, Timothy and Mullins, Robert},` → `author = {Yan, Mengjia and Bourgeat, Thomas and Malik, Sharad},` and add `pages = {138--143},`. The citation itself is fine.

### Other bib metadata noticed in passing (no claim affected)

- `intelsdm` and `llvmlangref` have no year, so they print "n.d." Give the SDM the version/date actually consulted (Intel order number 325383 and its revision) and the LangRef an access year (`note = {Accessed 2026}`). The exact SDM revision used for UV3 should come from whoever read it, not be guessed.
- `protean` carries a stray `issue_date = {February 2020}` and no pages (Crossref gives 1–20).
- `mishra2004graph` has no DOI (10.1109/date.2004.1268846). Moot if C8 is applied.
- arXiv-only entries checked: `green2023safebet`, `manerkar2020realitycheck`, `geier2025coverage`, `mosier2025uspectre`, `trippel2018meltdownprime` have no published version found, so `@misc` is right. `xu2025dejavuzz`, `rostami2024specure` and `oleksenko2026enterexit` already give the published venue.
- No duplicate works under two keys among the 170 cited keys.

### Weak fits (not wrong)

- `wang2021oo7` (related.tex:8): oo7 is a static-analysis defense that finds and patches gadgets, not a testing tool. Cut in C4.
- `castes2024sharing` (related.tex:19): software-only core-gapping for confidential VMs, in a list of hardware Spectre defenses. Cut in C10.
- `choudhary2023declassiflow` (related.tex:19): a static LLVM analysis that relaxes protections; fits "relaxations" better than "many others". Cut in C10.
- `flur2016modelling` (related.tex:16): an ARM modelling paper whose hardware runs are validation. Cut in C9.
- `moghimi2020medusa` (related.tex:8): mainly an attack paper; fits "synthesize" only through its Transynther fuzzer. Cut in C2.
- `dinesh2024conjunct`, `dinesh2025hhoudini` (related.tex:12): they prove per-instruction safety against timing leakage; "adherence to constant-time contracts" is a fair paraphrase (RTL2MµPATH §VIII groups ConjunCT the same way). Keep.
- `yu2019sttformal` (related.tex:12): "an abstract machine" for what the TR calls a detailed formal model of an OoO processor; defensible. Optional: `over an abstract machine` → `over a formal processor model`.
- Outside Related Work, `intro.tex:39` cites `sakalis2019delay` and `doppelganger` under "delay or taint-track"; both are delay schemes, so the "delay" half covers them. No change.

## (c) Cut list (paper order)

Each item gives the reference-count saving; the running total is out of 48. Removed keys were checked to have no other live citation, so each removal drops the entry from the reference list.

### C1. background.tex:73 (MCM list): removes 4 (running total 4)

Eight MCM formalizations back one background sentence; four (x86-TSO, Herding Cats, ARMv8, C++11) make the point. Keep a Simner paper instead of ARMv8 if Anna prefers the Simner line.

Removed keys: `lahav2017repairing`, `simner2020ifetch`, `simner2022vm`, `simner2025exceptions`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `background.tex`):

```latex
~\cite{owens2009x86tso,herdingcats,pulte2018simplifying,batty2011mathematizing,lahav2017repairing,simner2020ifetch,simner2022vm,simner2025exceptions}
```

New:

```latex
~\cite{owens2009x86tso,herdingcats,pulte2018simplifying,batty2011mathematizing}
```

### C2. related.tex:8 (testing paragraph, CPU and timing tools): removes 8 (running total 12)

Third Revizor follow-up, silicon measurement/attack-synthesis tools, timing-side-channel discovery and functional RTL fuzzing are not transient-execution defense testing. Trevex stays as the one detection tool. The cut clauses are commented out, not deleted.

Removed keys: `oleksenko2026enterexit`, `xiao2020speechminer`, `moghimi2020medusa`, `weber2021osiris`, `rajapaksha2023sigfuzz`, `borkar2024whisperfuzz`, `hur2021difuzzrtl`, `solt2024cascade`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
Revizor~\cite{revizor} and its follow-ups~\cite{oleksenko2023hideseekspectresefficient,hofmann2023speculationatfault,oleksenko2026enterexit} test against speculation contracts, and other tools measure, synthesize or detect transient leaks~\cite{xiao2020speechminer,moghimi2020medusa,weber2026trevex}; timing side channels are discovered automatically on CPUs and in RTL~\cite{weber2021osiris,rajapaksha2023sigfuzz,borkar2024whisperfuzz}. Beyond functional RTL fuzzing~\cite{hur2021difuzzrtl,solt2024cascade}, pre-silicon tools
```

New:

```latex
Revizor~\cite{revizor} and its follow-ups~\cite{oleksenko2023hideseekspectresefficient,hofmann2023speculationatfault} test against speculation contracts, and other tools detect transient leaks~\cite{weber2026trevex}. % [cut 2026-11-16, citation trim] ; timing side channels are discovered automatically on CPUs and in RTL~\cite{weber2021osiris,rajapaksha2023sigfuzz,borkar2024whisperfuzz}. Beyond functional RTL fuzzing~\cite{hur2021difuzzrtl,solt2024cascade},
Pre-silicon tools
```

### C3. related.tex:8 (pre-silicon tools): removes 2 (running total 14)

One representative per technique (IntroSpectre already appears in the paragraph's first sentence; SpecDoctor stays with DejaVuzz).

Removed keys: `ghaniyoun2023teesec`, `defaveritron2025phantomtrails`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
gadget-driven simulation~\cite{ghaniyoun2021introspectre,ghaniyoun2023teesec}, information-flow tracking~\cite{rostami2024specure,defaveritron2025phantomtrails} or
```

New:

```latex
gadget-driven simulation~\cite{ghaniyoun2021introspectre}, information-flow tracking~\cite{rostami2024specure} or
```

### C4. related.tex:8 (Scam-V and software tools): removes 3 (running total 17)

Scam-V's follow-up and two of three gadget tools are padding; oo7 is a static-analysis defense, a weak fit for "test" (agent check). Splitting the cite also puts LmTest next to "leakage models", which the Related-vs-Caroline review (item 8) wants.

Removed keys: `buiras2021observation`, `wang2021oo7`, `lin2025teapot`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
Scam-V~\cite{nemati2020scamv,buiras2021observation} validates side-channel models against hardware, and software tools test programs for Spectre gadgets or against leakage models~\cite{oleksenko2020specfuzz,wang2021oo7,lin2025teapot,barthe2024lmtest}.
```

New:

```latex
Scam-V~\cite{nemati2020scamv} validates side-channel models against hardware, and software tools test programs for Spectre gadgets~\cite{oleksenko2020specfuzz} or against leakage models~\cite{barthe2024lmtest}.
```

### C5. related.tex:12 (software analyses and secure compilers): removes 8 (running total 25)

Twelve-reference dump behind "build on them". Keep the SoK (also Background), Cauligi PLDI'20 (also intro), Blade, and Serberus (Caroline's).

Removed keys: `patrignani2021exorcising`, `barthe2021highassurance`, `daniel2021haunter`, `fabian2022combinations`, `fabian2025lift`, `shivakumar2023typing`, `shivakumar2023declassified`, `arranzolmos2025rsb`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
software analyses and secure compilers build on them~\cite{cauligi2022sok,cauligi2020constanttime,vassena2021blade,patrignani2021exorcising,barthe2021highassurance,daniel2021haunter,fabian2022combinations,fabian2025lift,shivakumar2023typing,shivakumar2023declassified,mosier2024serberus,arranzolmos2025rsb}.
```

New:

```latex
software analyses and secure compilers build on them~\cite{cauligi2022sok,cauligi2020constanttime,vassena2021blade,mosier2024serberus}.
```

### C6. related.tex:12 (speculation semantics): removes 1 (running total 26)

Colvin et al. is a workshop paper; three semantics make the point.

Removed keys: `colvin2020abstractsemantics`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
Speculation has been given pomset~\cite{disselkoen2019code}, axiomatic~\cite{ponce2022cats}, abstract~\cite{colvin2020abstractsemantics} and out-of-order operational semantics~\cite{guanciale2020inspectre},
```

New:

```latex
Speculation has been given pomset~\cite{disselkoen2019code}, axiomatic~\cite{ponce2022cats} and out-of-order operational semantics~\cite{guanciale2020inspectre},
```

### C7. related.tex:12 (RTL verification): removes 4 (running total 30)

Seven RTL verifiers; keep UPEC, its exhaustive follow-up, and Contract Shadow Logic.

Removed keys: `fadiheh2020formal`, `zagieboylo2023specverilog`, `yang2026compass`, `dong2026interplay`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
checks secure speculation in RTL~\cite{fadiheh2019upec,fadiheh2020formal,fadiheh2023exhaustive,zagieboylo2023specverilog,contractshadow,yang2026compass,dong2026interplay}
```

New:

```latex
checks secure speculation in RTL~\cite{fadiheh2019upec,fadiheh2023exhaustive,contractshadow}
```

### C8. related.tex:16 (directed test generation): removes 2 (running total 32)

Generic functional-verification test generation is tangential to the paragraph's subject (litmus tests).

Removed keys: `fine2003cdg`, `mishra2004graph`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
Directed test generation has long served functional verification~\cite{fine2003cdg,mishra2004graph}. Beyond
```

New:

```latex
% [cut 2026-11-16, citation trim] Directed test generation has long served functional verification~\cite{fine2003cdg,mishra2004graph}.
Beyond
```

### C9. related.tex:16 (litmus generation and hardware runs): removes 3 (running total 35)

Keep one Mador-Haim paper and two hardware runners (litmus, PerpLE). Flur et al. is mainly a modelling paper (weak fit, agent check).

Removed keys: `maradhaim2010generating`, `sarkar2011power`, `flur2016modelling`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
to contrast memory models~\cite{maradhaim2010generating,maradhaim2011litmus}, run on hardware~\cite{sarkar2011power,flur2016modelling,alglave2011litmus,perple}
```

New:

```latex
to contrast memory models~\cite{maradhaim2011litmus}, run on hardware~\cite{alglave2011litmus,perple}
```

### C10. related.tex:19 (defenses, relaxations and "many others"): removes 13 (running total 48)

The 16-reference "many others" is the largest dump. Keep four that Protean's Related Work also names (ProSpeCT, Levioso, SafeBet, Perspective). Drops Pinned Loads from the optimization list (its own claim of being security-preserving is unverified, per the Related-vs-Caroline review item 5). castes2024sharing (software-only, hypervisor) and choudhary2023declassiflow (software analysis) are weak fits here anyway (agent check).

Removed keys: `zhao2022pinned`, `jin2023specterminator`, `ganjisaffar2025specasan`, `hajiabadi2025cassandra`, `aimoniotis2024janus`, `chen2025mustt`, `cui2023ssft`, `kvalsvik2025shadowbinding`, `castes2024sharing`, `trujillo2026register`, `wu2025rcp`, `sakalis2023delayonsquash`, `choudhary2023declassiflow`. None of them is cited anywhere else in the live text (checked against the compiled citation list).

Old (occurs once in `related.tex`):

```latex
relaxations that recover performance~\cite{tran2020clearing,zhao2020invarspec,zhao2022pinned}, and many others~\cite{jin2023specterminator,daniel2023prospect,ganjisaffar2025specasan,hajiabadi2024levioso,hajiabadi2025cassandra,aimoniotis2024janus,chen2025mustt,cui2023ssft,kvalsvik2025shadowbinding,green2023safebet,kim2024perspective,castes2024sharing,trujillo2026register,wu2025rcp,sakalis2023delayonsquash,choudhary2023declassiflow}.
```

New:

```latex
relaxations that recover performance~\cite{tran2020clearing,zhao2020invarspec}, and many others~\cite{daniel2023prospect,hajiabadi2024levioso,green2023safebet,kim2024perspective}.
```
### Optional cuts (O1–O2, −2 more)

- **O1** (related.tex:12, −1): `constant-time contracts~\cite{leave,dinesh2024conjunct,dinesh2025hhoudini}` → `constant-time contracts~\cite{leave,dinesh2024conjunct}`. H-Houdini is the invariant-learning engine behind ConjunCT's line of work; ConjunCT carries the claim.
- **O2** (related.tex:16, −1): `manerkar2018pipeproof,manerkar2020realitycheck}` → `manerkar2018pipeproof}`. RealityCheck is arXiv-only and not in Caroline's own list of Check tools (Related-vs-Caroline review, item 2). Keep it if Anna wants the full Check family.

### Not cut on purpose

- The seven Check tools, TransForm, MemSynth, PipeSynth, rtl2µspec, McMutants: Caroline's group's work and the lineage a reviewer from her group expects.
- The intro defense lists (`intro.tex:39–44`, 16 works): every one is a hardware defense in the class the paper tests; trimming them is possible (e.g. SpecShield, SafeSpec) but the Background/Results narrative uses the class, so they stay.
- The design-level leak list (related.tex:19): each backs a specific "this defense leaks via X" claim, and all were verified.
- The Related-vs-Caroline review proposes adding LMSPEC discussion, AMuLeT\*, UPEC-DIT, McVerSi, Okapi and Canella et al. in Related Work. If all are taken, add about +3 new bib entries (UPEC-DIT, McVerSi, Okapi); the projected total becomes about 125–126.

## (d) Per-key table

Class legend: KEEP-ESSENTIAL (defense we evaluate, source of a reported bug/claim, tool compared or built on, or pinpointed factual claim), KEEP-SUPPORTING (expected prior work), PADDING (cite-dump member the narrative does not need; the "cut" column names the edit that removes it), WRONG (here: bib metadata only). Locations are `file:line` in ISCA-27 `04e7347` (`intro_threelayer_v9` = Fig. 1 source, `stt_xmm4_code_8pt` = UV1 code figure).

| key | where cited (file:line) | class | reason | cut |
|---|---|---|---|---|
| `aimoniotis2022doin` | related:19 | KEEP-SUPPORTING | design-level leak |  |
| `aimoniotis2024janus` | related:19 | PADDING | "many others" | C10 |
| `ainsworth2020muontrap` | intro:41 | KEEP-SUPPORTING | intro defense list |  |
| `ainsworth2021ghostminion` | intro:41 | KEEP-SUPPORTING | intro defense list; Pensieve claim |  |
| `alglave2010fences` | background:72, related:16 | KEEP-ESSENTIAL | axiomatic models, diy test generation (verified) |  |
| `alglave2011litmus` | related:16 | KEEP-SUPPORTING | litmus tool |  |
| `amulet` | intro:70, intro:115, intro:155, intro_threelayer_v9:48, intro_threelayer_v9:93, intro:266, background:44, background:62, results:26, results:28, results:32, results:35, results:46, results:66, related:8 | KEEP-ESSENTIAL | closest prior work and baseline; source of A-KV/A-UV bugs; pinpoints §2.1, §3.2, §3.3, §4.1, §4.4-4.8 (§3.2, §3.3 verified) |  |
| `armstrong2019sail` | related:16 | KEEP-SUPPORTING | Sail ISA semantics |  |
| `armstrong2021isla` | related:16 | KEEP-SUPPORTING | litmus vs ISA semantics |  |
| `arranzolmos2025rsb` | related:12 | PADDING | compiler list | C5 |
| `barthe2021highassurance` | related:12 | PADDING | compiler list | C5 |
| `barthe2024lmtest` | related:8 | KEEP-SUPPORTING | leakage-model testing (Helium compares against it) |  |
| `batty2011mathematizing` | background:73 | KEEP-SUPPORTING | MCM example (C++) |  |
| `behnia2021interference` | related:19 | KEEP-SUPPORTING | design-level leak (verified) |  |
| `blackbox` | related:12 | WRONG | claim OK; bib lists two non-authors (W3) |  |
| `borkar2024whisperfuzz` | related:8 | PADDING | timing channels | C2 |
| `buiras2021observation` | related:8 | PADDING | second Scam-V cite | C4 |
| `cabodi2019speculationmc` | related:12 | KEEP-SUPPORTING | abstract-model checking |  |
| `canella2019systematic` | background:12 | KEEP-ESSENTIAL | transient/sequential terminology |  |
| `castes2024sharing` | related:19 | PADDING | software-only (weak fit) in "many others" | C10 |
| `cauligi2020constanttime` | intro:14, related:12 | KEEP-SUPPORTING | intro example (crypto) + RW |  |
| `cauligi2022sok` | background:42, related:12 | KEEP-SUPPORTING | contracts observer modes (Background) + RW |  |
| `chakraborty2022timed` | related:19 | KEEP-SUPPORTING | design-level leak |  |
| `cheang2019formal` | related:12 | KEEP-SUPPORTING | formal leak definition |  |
| `checkmate` | intro:228, background:86, background:89, pipeline:14 | KEEP-ESSENTIAL | security litmus test synthesis we build on |  |
| `chen2025mustt` | related:19 | PADDING | "many others" | C10 |
| `cheng2024speclfb` | intro:41, background:28, background:29, background:31, pipeline:116, results:26, results:33, results:66, results:70 | KEEP-ESSENTIAL | defense evaluated; "invisible" grouping matches its §10 related work |  |
| `cheng2026contention` | related:19 | KEEP-SUPPORTING | design-level leak (verified) |  |
| `choudhary2023declassiflow` | related:19 | PADDING | software analysis (weak fit) in "many others" | C10 |
| `colvin2020abstractsemantics` | related:12 | PADDING | fourth semantics, workshop paper | C6 |
| `contractshadow` | related:8, related:12 | KEEP-SUPPORTING | RTL contract verification |  |
| `cui2023ssft` | related:19 | PADDING | "many others" | C10 |
| `daniel2021haunter` | related:12 | PADDING | compiler list | C5 |
| `daniel2023prospect` | related:19 | KEEP-SUPPORTING | kept representative (Protean lists it) |  |
| `defaveritron2025phantomtrails` | related:8 | PADDING | second IFT cite | C3 |
| `dinesh2024conjunct` | related:12 | KEEP-SUPPORTING | CT verification (weak fit wording) |  |
| `dinesh2025hhoudini` | related:12 | KEEP-SUPPORTING | CT verification; optional cut O1 |  |
| `disselkoen2019code` | related:12 | KEEP-SUPPORTING | speculation semantics |  |
| `dong2026interplay` | related:12 | PADDING | RTL list | C7 |
| `doppelganger` | intro:39 | KEEP-SUPPORTING | intro defense list (delay) |  |
| `fabian2022combinations` | related:12 | PADDING | compiler list | C5 |
| `fabian2025lift` | related:12 | PADDING | compiler list | C5 |
| `fadiheh2019upec` | related:12 | KEEP-SUPPORTING | UPEC |  |
| `fadiheh2020formal` | related:12 | PADDING | third UPEC paper | C7 |
| `fadiheh2023exhaustive` | related:8, related:12 | KEEP-SUPPORTING | RTL verification |  |
| `fine2003cdg` | related:16 | PADDING | functional verification, tangential | C8 |
| `flur2016modelling` | related:16 | PADDING | model paper, weak fit for "run on hardware" | C9 |
| `fustos2019spectreguard` | related:19 | KEEP-SUPPORTING | secret annotation |  |
| `fustos2020spectrerewind` | related:19 | KEEP-SUPPORTING | design-level leak |  |
| `ganjisaffar2025specasan` | related:19 | PADDING | "many others" | C10 |
| `geier2025coverage` | related:8 | KEEP-SUPPORTING | contract-coverage fuzzing (arXiv only, correct) |  |
| `gem5` | intro:48, intro_threelayer_v9:81, pipeline:110 | KEEP-ESSENTIAL | simulator |  |
| `ghaniyoun2021introspectre` | related:8 | KEEP-SUPPORTING | pre-silicon gadget fuzzing |  |
| `ghaniyoun2023teesec` | related:8 | PADDING | TEE testing, second IntroSpectre-line cite | C3 |
| `green2023safebet` | related:19 | KEEP-SUPPORTING | kept representative (Protean lists it); arXiv only |  |
| `guanciale2020inspectre` | related:12 | KEEP-SUPPORTING | OoO speculation semantics |  |
| `guarnieri2020spectector` | background:49 | KEEP-ESSENTIAL | SNI original |  |
| `guarnieri2021contracts` | intro:121, intro_threelayer_v9:47, intro_threelayer_v9:93, background:42, background:44, background:49 | KEEP-ESSENTIAL | contracts foundation; pinpoints |  |
| `hajiabadi2024levioso` | related:19 | KEEP-SUPPORTING | kept representative (Protean lists it) |  |
| `hajiabadi2025cassandra` | related:19 | PADDING | "many others" | C10 |
| `herdingcats` | background:72, background:73 | KEEP-ESSENTIAL | axiomatic MCM foundation |  |
| `hofmann2023speculationatfault` | related:8 | KEEP-SUPPORTING | Revizor follow-up |  |
| `horn2018ssb` | background:9 | KEEP-ESSENTIAL | store bypass |  |
| `hossain2020transform` | related:16 | KEEP-SUPPORTING | litmus synthesis from transistency models |  |
| `hsiao2021rtl2uspec` | related:16 | KEEP-SUPPORTING | synthesis from RTL |  |
| `hu2021sok` | intro:27, related:19 | KEEP-ESSENTIAL | survey of HW defenses (intro cost claim and RW) |  |
| `hur2021difuzzrtl` | related:8 | PADDING | functional RTL fuzzing | C2 |
| `hur2022specdoctor` | related:8 | KEEP-SUPPORTING | pre-silicon differential fuzzing |  |
| `inspectre` | intro:14 | KEEP-SUPPORTING | intro example (kernels): InSpectre Gadget, cross-privilege Spectre v2 |  |
| `intelsdm` | results:63 | KEEP-ESSENTIAL | supports x86 register-read claim (UV3); bib has no year/version |  |
| `jackson2002alloy` | intro:250, background:75, pipeline:14, pipeline:30 | KEEP-ESSENTIAL | tool we build on |  |
| `jin2023specterminator` | related:19 | PADDING | "many others" | C10 |
| `khasawneh2019safespec` | intro:41 | KEEP-SUPPORTING | intro defense list |  |
| `kim2024perspective` | related:19 | KEEP-SUPPORTING | kept representative (Protean lists it) |  |
| `kiriansky2018dawg` | background:13, related:19 | KEEP-ESSENTIAL | transmitter definition (Background); also in RW (verified) |  |
| `kodkod` | pipeline:30 | KEEP-ESSENTIAL | solver we use |  |
| `koruyeh2020speccfi` | related:19 | KEEP-SUPPORTING | defense |  |
| `kvalsvik2025shadowbinding` | related:19 | PADDING | "many others" | C10 |
| `kvalsvik2025thesis` | related:19 | KEEP-ESSENTIAL | UV3 contrast; §4.3 verified |  |
| `lahav2017repairing` | background:73 | PADDING | fifth of eight MCM examples | C1 |
| `lattner2004llvm` | pipeline:101 | KEEP-ESSENTIAL | IR we emit |  |
| `lcms` | background:72, background:90, model:29, model:50 | KEEP-ESSENTIAL | LCMs, axiomatic leakage vocabulary |  |
| `leave` | related:12 | KEEP-SUPPORTING | CT-contract verification |  |
| `li2019conditional` | related:19 | KEEP-SUPPORTING | defense |  |
| `li2022unxpec` | results:35, related:19 | KEEP-ESSENTIAL | A-KV2 = unXpec (verified) |  |
| `lin2025teapot` | related:8 | PADDING | third gadget tool | C4 |
| `llvmlangref` | pipeline:101 | KEEP-ESSENTIAL | supports asm sideeffect claim; bib has no year |  |
| `loughlin2021dolma` | intro:39, related:19 | KEEP-ESSENTIAL | defense in intro list; source of STT store-channel claim (verified) |  |
| `lustig` | background:75, background:82 | KEEP-ESSENTIAL | minimal litmus synthesis we build on; §3.1 |  |
| `lustig2014pipecheck` | related:16 | KEEP-SUPPORTING | Check tools |  |
| `lustig2016coatcheck` | related:16 | KEEP-SUPPORTING | Check tools |  |
| `manerkar2015ccicheck` | related:16 | KEEP-SUPPORTING | Check tools |  |
| `manerkar2017rtlcheck` | related:16 | KEEP-SUPPORTING | Check tools |  |
| `manerkar2018pipeproof` | related:16 | KEEP-SUPPORTING | Check tools; all-programs proof |  |
| `manerkar2020realitycheck` | related:16 | KEEP-SUPPORTING | Check tools; arXiv only, not in Caroline list; optional cut O2 |  |
| `maradhaim2010generating` | related:16 | PADDING | second Mador-Haim cite | C9 |
| `maradhaim2011litmus` | related:16 | KEEP-SUPPORTING | tests to contrast MCMs |  |
| `mckevitt2023speccheck` | related:8 | KEEP-SUPPORTING | only other gem5 tool |  |
| `mcmutants` | related:16 | KEEP-SUPPORTING | mutation testing of MCM tests |  |
| `memalloy` | background:75 | KEEP-ESSENTIAL | axiomatic spec to test generator |  |
| `memsynth` | related:16 | KEEP-SUPPORTING | model synthesis |  |
| `miller2018mitigating` | background:9 | KEEP-ESSENTIAL | speculation primitives |  |
| `mishra2004graph` | related:16 | PADDING | functional verification, tangential | C8 |
| `moghimi2020medusa` | related:8 | PADDING | attack paper (weak fit) | C2 |
| `mohr2024synthesizing` | related:12 | KEEP-SUPPORTING | contract synthesis |  |
| `mosier2024serberus` | background:9, related:12 | KEEP-ESSENTIAL | speculation primitives (Background); kept in RW trim |  |
| `mosier2025sptpr6` | related:19 | KEEP-ESSENTIAL | SPT untaint fix (PR #6, verified); the SPT pending-squash fix (PR #4) is missing, see W1 |  |
| `mosier2025uspectre` | discussion:52 | KEEP-ESSENTIAL | microcode mispredictions (future work) |  |
| `nda` | intro:39 | KEEP-ESSENTIAL | defense list, NDA scheme |  |
| `nemati2020scamv` | related:8 | KEEP-SUPPORTING | model-vs-implementation testing |  |
| `nickscommittoSTT` | discussion:50, related:19 | KEEP-ESSENTIAL | STT pending-squash fix commit 18e304f (exists, verified) |  |
| `norman2023pipesynth` | related:16 | KEEP-SUPPORTING | µarch axiom synthesis |  |
| `oleksenko2020specfuzz` | related:8 | KEEP-SUPPORTING | software gadget testing |  |
| `oleksenko2023hideseekspectresefficient` | related:8 | KEEP-SUPPORTING | Revizor follow-up, CPU testing stage |  |
| `oleksenko2026enterexit` | related:8 | PADDING | third Revizor follow-up | C2 |
| `owens2009x86tso` | background:73 | KEEP-SUPPORTING | MCM example (x86) |  |
| `patrignani2021exorcising` | related:12 | PADDING | compiler list | C5 |
| `pensieve` | related:8, related:19 | KEEP-ESSENTIAL | GhostMinion leapfrogging claim (verified) + model-checking stage |  |
| `perple` | related:16 | WRONG | claim OK; bib has no booktitle (W2) |  |
| `ponce2022cats` | related:12 | KEEP-SUPPORTING | axiomatic speculation semantics (closest formalism) |  |
| `protean` | intro:39, intro:70, background:13, background:46, background:62, discussion:50, related:8, related:19 | KEEP-ESSENTIAL | source of the pending-squash and untaint bugs and of protection set / speculation model; §VII-B4b, §VII-B4c verified |  |
| `pulte2018simplifying` | background:73 | KEEP-SUPPORTING | MCM example (ARMv8) |  |
| `rajapaksha2023sigfuzz` | related:8 | PADDING | timing channels | C2 |
| `recon` | intro:39, background:26, model:55, results:52, results:60, discussion:31 | KEEP-ESSENTIAL | defense evaluated |  |
| `reineke2026foundations` | related:12 | KEEP-SUPPORTING | contracts survey |  |
| `revizor` | related:8 | KEEP-ESSENTIAL | origin of contract testing AMuLeT reuses |  |
| `rostami2024specure` | related:8 | KEEP-SUPPORTING | pre-silicon IFT fuzzing |  |
| `rtl2upath` | intro:243, background:62, related:8, related:12 | KEEP-ESSENTIAL | leakage contract definition (§II-B); also cited in Related Work (verified) |  |
| `saileshwar2019cleanupspec` | intro:41, background:29, background:31, pipeline:116, results:26, results:33, results:35 | KEEP-ESSENTIAL | defense evaluated |  |
| `sakalis2019delay` | intro:39 | KEEP-SUPPORTING | intro defense list (delay) |  |
| `sakalis2023delayonsquash` | related:19 | PADDING | "many others" | C10 |
| `sarkar2011power` | related:16 | PADDING | hardware-run list | C9 |
| `sat4j` | pipeline:30 | KEEP-ESSENTIAL | solver we use (requested citation) |  |
| `schwarz2020context` | related:19 | KEEP-SUPPORTING | secret annotation (Protean groups it) |  |
| `sdo` | intro:44 | KEEP-SUPPORTING | intro defense list (data-oblivious) |  |
| `shivakumar2023declassified` | related:12 | PADDING | compiler list | C5 |
| `shivakumar2023typing` | related:12 | PADDING | compiler list | C5 |
| `simner2020ifetch` | background:73 | PADDING | MCM list | C1 |
| `simner2022vm` | background:73 | PADDING | MCM list | C1 |
| `simner2025exceptions` | background:73 | PADDING | MCM list | C1 |
| `solt2024cascade` | related:8 | PADDING | functional RTL fuzzing | C2 |
| `specshield` | intro:39 | KEEP-SUPPORTING | intro defense list |  |
| `spectre` | intro:11, discussion:21 | KEEP-ESSENTIAL | Spectre original |  |
| `spook` | intro:14 | KEEP-SUPPORTING | intro example (browsers) |  |
| `spt` | intro:39, background:23, background:46, model:55, results:75, discussion:34 | KEEP-ESSENTIAL | defense evaluated |  |
| `sttmaster` | results:46 | KEEP-ESSENTIAL | code citation, check still on master |  |
| `sttrepo` | results:46, stt_xmm4_code_8pt:29, discussion:50 | KEEP-ESSENTIAL | code citation for UV1 (commit e3283b9) |  |
| `taram2019csf` | related:19 | KEEP-SUPPORTING | defense |  |
| `tran2020clearing` | related:19 | KEEP-SUPPORTING | optimization |  |
| `trippel2017tricheck` | related:16 | KEEP-SUPPORTING | Check tools |  |
| `trippel2018meltdownprime` | background:90 | KEEP-SUPPORTING | CheckMate exploits; arXiv companion (no published version) |  |
| `trujillo2026register` | related:19 | PADDING | "many others" | C10 |
| `vassena2021blade` | related:12 | KEEP-SUPPORTING | secure compiler, representative |  |
| `wang2021oo7` | related:8 | PADDING | static-analysis defense, weak fit for "test" | C4 |
| `wang2025synthesis` | related:12 | KEEP-SUPPORTING | contract synthesis |  |
| `weber2021osiris` | related:8 | PADDING | timing channels, not transient testing | C2 |
| `weber2026trevex` | related:8 | KEEP-SUPPORTING | transient-leak detection on CPUs |  |
| `wu2025rcp` | related:19 | PADDING | "many others" | C10 |
| `xiao2020speechminer` | related:8 | PADDING | measurement on silicon, tangential | C2 |
| `xiao2023hackyracers` | related:19 | KEEP-SUPPORTING | design-level leak |  |
| `xu2025dejavuzz` | related:8 | KEEP-SUPPORTING | pre-silicon differential fuzzing |  |
| `yan2018invisispec` | intro:41, intro:143, background:22, background:29, background:31, results:26, results:32, results:35 | KEEP-ESSENTIAL | defense evaluated |  |
| `yang2026compass` | related:12 | PADDING | RTL list | C7 |
| `yavarzadeh2023halfhalf` | discussion:21 | KEEP-ESSENTIAL | supports undocumented-predictor claim |  |
| `yu2019oisa` | related:12 | KEEP-SUPPORTING | formal leak definition |  |
| `yu2019stt` | intro:39, intro_threelayer_v9:60, background:17, background:22, background:44, background:60, background:62, model:55, pipeline:140, results:35, results:52, results:60, results:75, discussion:21 | KEEP-ESSENTIAL | defense evaluated; many pinpoints |  |
| `yu2019sttformal` | related:12 | KEEP-SUPPORTING | STT proof |  |
| `zagieboylo2023specverilog` | related:12 | PADDING | RTL list | C7 |
| `zhao2020invarspec` | related:19 | KEEP-SUPPORTING | optimization |  |
| `zhao2022pinned` | related:19 | PADDING | third optimization | C10 |

## (e) Related Work verification (every live citation in `related.tex`)

Method: each key was checked for (1) existence with the bib's title/authors/venue/year, (2) whether the work says or does what the sentence attributes to it, (3) the pinpoint section. Sources: local PDFs/texts (`~/Documents/quail/sources/papers/`, `paper_figures/caroline/papers/`), Crossref DOI records, arXiv abstract pages, USENIX/NDSS/MIT/Princeton pages, GitHub (read-only). dblp refused automated access, so metadata comes from Crossref. Prose style was not reviewed (separate agent). Verdicts: OK, WRONG claim, WRONG pinpoint, WRONG metadata, INCOMPLETE, WEAK FIT.

### Line 8: Testing for speculative leakage

| key | verdict | how checked / evidence |
|---|---|---|
| `revizor` | OK | Local PDF: ASPLOS'22, testing black-box CPUs against speculation contracts. |
| `oleksenko2023hideseekspectresefficient` | OK | S&P'23; efficient random testing of commercial CPUs. |
| `fadiheh2023exhaustive` | OK | Crossref: IEEE TC 72, 2023; UPEC-based formal RTL verification (fits lines 8 and 12). |
| `contractshadow` | OK | Crossref: ASPLOS'25 (Tan, Yang, Bourgeat, Malik, Yan). |
| `rtl2upath` | OK | Crossref: MICRO'24; local text: synthesizes formally verified leakage contracts and signatures. |
| `hur2022specdoctor` | OK | Crossref: CCS'22, "Differential Fuzz Testing" (= differential execution). |
| `ghaniyoun2021introspectre` | OK | Crossref: ISCA'21; gadget fuzzing in RTL simulation. |
| `pensieve` | OK | Local PDF: model-checking framework "targeting early-stage microarchitectural defenses". |
| `hofmann2023speculationatfault` | OK | USENIX Sec'23; "extends Revizor". |
| `oleksenko2026enterexit` | OK | Crossref: S&P'26; integrated into Revizor. |
| `xiao2020speechminer` | OK | NDSS'20; framework "for exploring and measuring" speculative vulnerabilities (= "measure"). |
| `moghimi2020medusa` | OK / WEAK FIT | USENIX Sec'20; attack paper whose Transynther fuzzer synthesizes variants (= "synthesize"). |
| `weber2026trevex` | OK | S&P'26; black-box detection framework (= "detect"). |
| `weber2021osiris` | OK | USENIX Sec'21; fuzzing-based timing side-channel discovery on CPUs. |
| `rajapaksha2023sigfuzz` | OK | Crossref: DATE'23; timing side channels in RTL. |
| `borkar2024whisperfuzz` | OK | USENIX Sec'24; white-box RTL fuzzing for timing vulnerabilities. |
| `hur2021difuzzrtl` | OK | Crossref: S&P'21; functional RTL fuzzing. |
| `solt2024cascade` | OK | USENIX Sec'24; functional CPU fuzzing. |
| `xu2025dejavuzz` | OK | ASPLOS'25; differential information-flow-tracking fuzzer. |
| `ghaniyoun2023teesec` | OK | Crossref: ISCA'23; pre-silicon gadget-based TEE testing. |
| `rostami2024specure` | OK | DAC'24; fuzzing plus information-flow tracking. |
| `defaveritron2025phantomtrails` | OK | USENIX Sec'25; pre-silicon taint-based discovery. |
| `geier2025coverage` | OK | arXiv 2511.08443 (no venue yet, so `@misc` is right); coverage-guided contract fuzzing. |
| `nemati2020scamv` | OK | Crossref: CAV'20; validates side-channel models against hardware. |
| `buiras2021observation` | OK | Crossref: MICRO'21; Scam-V follow-up. |
| `oleksenko2020specfuzz` | OK | USENIX Sec'20; dynamic testing for Spectre gadgets. |
| `wang2021oo7` | WEAK FIT | Crossref: TSE 47(11), 2021; static analysis that detects and patches gadgets (a defense, not a test). Cut in C4. |
| `lin2025teapot` | OK | CGO'25; binary rewriting plus fuzzing for gadgets. |
| `barthe2024lmtest` | OK | Crossref: CCS'24; tests crypto code against leakage models. |
| `mckevitt2023speccheck` | OK | Local PDF: PACT'23; FSM checks "suspicious program flows during an arbitrary program's simulation" in gem5. |
| `amulet` | OK | Crossref: ASPLOS'25; tests gem5 defenses. |
| `amulet` [§3.3] | OK pinpoint | Local PDF §3.3 "Analyzing Violations": side-by-side gem5 debug logs, trace back to the mis-speculated instruction, root-causing "took a few hours to few days". |
| `amulet` [§3.2] | OK pinpoint | Local PDF §3.2: AMuLeT-Opt "preserves the µarch state of the predictors ... between test cases". |
| `protean` | OK | Local text: extends AMuLeT (AMuLeT\*) to test its gem5 defenses. |

### Line 12: Formal models and verification

| key | verdict | how checked / evidence |
|---|---|---|
| `yu2019oisa` | OK | Crossref: NDSS'19; safe/unsafe operands are its core concept. |
| `cheang2019formal` | OK | Crossref: CSF'19; trace property for secure speculation. |
| `reineke2026foundations` | OK | arXiv 2610.20754 / LNCS 16481 (2026); introduces foundations and discusses recent work on leakage contracts (= "surveys"). |
| `cauligi2022sok` | OK | Crossref: S&P'22; SoK of software defenses and their foundations. |
| `cauligi2020constanttime`, `vassena2021blade`, `patrignani2021exorcising`, `barthe2021highassurance`, `daniel2021haunter`, `fabian2022combinations`, `fabian2025lift`, `shivakumar2023typing`, `shivakumar2023declassified`, `mosier2024serberus`, `arranzolmos2025rsb` | OK (all 11) | Crossref titles/venues match the bib (PLDI'20, POPL'21, CCS'21, S&P'21, NDSS'21, CCS'22, PACMPL'25, S&P'23 ×2, S&P'24, ASPLOS'25); each is a software analysis or secure compiler for an SCT/SNI-style definition. |
| `disselkoen2019code` | OK | Crossref: S&P'19; pomset model. |
| `ponce2022cats` | OK | Crossref: S&P'22; axiomatic approach. |
| `colvin2020abstractsemantics` | OK | Crossref: LNCS 2020 (FM'19 workshops). |
| `guanciale2020inspectre` | OK | Crossref: CCS'20; formal model of OoO and speculative features. |
| `yu2019sttformal` | OK (minor wording) | Local TR: non-interference proved for "an STT machine", a detailed formal OoO model; "abstract machine" is loose but defensible. |
| `blackbox` | WRONG metadata | Crossref + Princeton portal: authors are Yan, Bourgeat, Malik only (W3). Claim OK. |
| `fadiheh2019upec` | OK | Crossref: DATE'19. |
| `fadiheh2020formal` | OK | Crossref: DAC'20. |
| `zagieboylo2023specverilog` | OK | Crossref: CCS'23; IFC for secure speculation. |
| `yang2026compass` | OK | ASPLOS'26; taint schemes for RTL verification, evaluated on secure speculation. |
| `dong2026interplay` | OK | S&P'26 (MIT PDF); model checking secure speculation on BOOM. |
| `cabodi2019speculationmc` | OK | C2SI'19, LNCS (an extended MDPI Electronics 2019 version also exists); abstracted processor models. |
| `mohr2024synthesizing` | OK | Crossref: DATE'24; contract synthesis. |
| `wang2025synthesis` | OK | CCS'25 (DOI 10.1145/3719027.3765148). |
| `rtl2upath` | OK | Synthesizes leakage signatures from RTL. |
| `leave` | OK | Crossref: CCS'23; verifies RTL against leakage (incl. constant-time) contracts. |
| `dinesh2024conjunct` | OK / WEAK FIT | Crossref: S&P'24; proves per-instruction safety against timing leakage ("CT contract" is a fair reframing). |
| `dinesh2025hhoudini` | OK / WEAK FIT | ASPLOS'25; invariant learning applied (VeloCT) to the same safe-instruction property. |

### Line 16: Axiomatic models and litmus tests

| key | verdict | how checked / evidence |
|---|---|---|
| `fine2003cdg` | OK | Crossref: DAC'03; coverage-directed test generation. |
| `mishra2004graph` | OK | Crossref: DATE'04; functional test program generation (bib lacks DOI). |
| `alglave2010fences` | OK | Crossref: CAV'10; diy generates litmus tests from relaxation cycles. |
| `maradhaim2010generating` | OK | Crossref: CAV'10; "...Contrasting Memory Consistency Models". |
| `maradhaim2011litmus` | OK | Crossref: DAC'11. |
| `sarkar2011power` | OK | Crossref: PLDI'11; tests run on POWER hardware. |
| `flur2016modelling` | OK / WEAK FIT | Crossref: POPL'16; model paper validated against ARM hardware runs. |
| `alglave2011litmus` | OK | Crossref: TACAS'11, "Litmus: Running Tests against Hardware". |
| `perple` | WRONG metadata | Crossref: MICRO'20, pp. 329–341; bib has no booktitle (W2). Claim OK. |
| `mcmutants` | OK | Local PDF + Crossref: ASPLOS'23; mutation testing to evaluate MCM testing. |
| `memsynth` | OK | Crossref: PLDI'17. |
| `norman2023pipesynth` | OK | Crossref: ASPLOS'23; synthesizes µarch axioms. |
| `hsiao2021rtl2uspec` | OK | Crossref: MICRO'21; synthesis from RTL. |
| `lustig2014pipecheck`, `manerkar2015ccicheck`, `lustig2016coatcheck`, `trippel2017tricheck`, `manerkar2017rtlcheck`, `manerkar2018pipeproof` | OK | Crossref: MICRO'14, MICRO'15, ASPLOS'16, ASPLOS'17, MICRO'17, MICRO'18; PipeProof proves for all programs. |
| `manerkar2020realitycheck` | OK | arXiv 2003.04892; no published venue found (`@misc` right). |
| `hossain2020transform` | OK | Crossref: ISCA'20, "...Synthesizing Enhanced Litmus Tests". |
| `armstrong2021isla` | OK | Crossref: CAV'21; full-scale ISA semantics with axiomatic concurrency models. |
| `armstrong2019sail` | OK | Crossref: PACMPL 3 (POPL'19). |

### Line 19: Spectre defenses and their flaws

| key | verdict | how checked / evidence |
|---|---|---|
| `hu2021sok` | OK | Crossref: SEED'21; SoK of hardware defenses. |
| `taram2019csf`, `li2019conditional`, `koruyeh2020speccfi`, `kiriansky2018dawg` | OK | Crossref: ASPLOS'19, HPCA'19, S&P'20, MICRO'18. |
| `schwarz2020context`, `fustos2019spectreguard` | OK | Crossref: NDSS'20, DAC'19; secret-annotation defenses. |
| `tran2020clearing`, `zhao2020invarspec`, `zhao2022pinned` | OK | Crossref: PACT'20, MICRO'20, ASPLOS'22; performance-recovering optimizations. |
| `jin2023specterminator`, `daniel2023prospect`, `ganjisaffar2025specasan`, `hajiabadi2024levioso`, `hajiabadi2025cassandra`, `aimoniotis2024janus`, `chen2025mustt`, `cui2023ssft`, `kvalsvik2025shadowbinding`, `kim2024perspective`, `trujillo2026register`, `wu2025rcp`, `sakalis2023delayonsquash` | OK | Crossref/USENIX: TACO'23, USENIX Sec'23, ISCA'25, DAC'24, ISCA'25, SBAC-PAD'24, ICCD'25, JCST'23, MICRO'25, ISCA'24, S&P'26, TDSC'25, TACO'23; all hardware (or HW-SW) Spectre defenses. |
| `green2023safebet` | OK | arXiv 2306.07785 only (no published version found). |
| `castes2024sharing` | WEAK FIT | Crossref: ASPLOS'24; software-only hypervisor core-gapping, not a hardware Spectre defense. Cut in C10. |
| `choudhary2023declassiflow` | WEAK FIT | Crossref: CCS'23; static LLVM analysis that relaxes protections (software). Cut in C10. |
| `behnia2021interference` | OK | arXiv full text: attacks DoM and InvisiSpec; "CleanupSpec does not block speculative interference but makes its exploitation more challenging." |
| `li2022unxpec` | OK | Local PDF: timing channel "through the rollback operations", demonstrated on CleanupSpec. |
| `aimoniotis2022doin` | OK | Crossref: SEED'22, "Leveraging Inclusive Caches to Attack Speculative Delay Schemes". |
| `chakraborty2022timed` | OK | Crossref: DAC'22, "...exploiting store-to-load forwarding bypassing cache-based countermeasures". |
| `loughlin2021dolma` | OK | USENIX abstract: STT "fails to mitigate attacks using speculative stores". |
| `fustos2020spectrerewind` | OK | Crossref: ASHES'20; contention channel that bypasses state-reverting defenses. |
| `xiao2023hackyracers` | OK | Crossref: ASPLOS'23; gadgets break "many hardware countermeasures". |
| `cheng2026contention` | OK | USENIX Sec'26 page: secret-dependent reservation-station contention that bypasses STT/DOLMA. |
| `protean` [§VII-B4b] | OK pinpoint | `protean_hpca26.txt` "b) PROTEAN": AMuLeT\* found the delayed-branch-resolution pending-squash bug shared with STT/SPT/SPT-SB. |
| `protean` [§VII-B4c] | OK pinpoint | "c) STT, SPT, and SPT-SB": "We manually discover a corner-case implementation bug in SPT that AMuLeT\* misses". |
| `nickscommittoSTT` | OK | github.com/cwfletcher/stt/commit/18e304f exists, "fix pending squash bug". |
| `mosier2025sptpr6` | INCOMPLETE | PR #6 exists and fixes the untaint bug; the SPT pending-squash fix (PR #4) is uncited (W1). |
| `pensieve` | OK | Local PDF §6: "the simulator open-sourced by the authors does not implement the leapfrogging operations" (GhostMinion). |
| `kvalsvik2025thesis` [§4.3] | OK pinpoint | Thesis §4.3 "Reveal/Conceal for Multiple Secrets": "only information about the youngest of these is preserved"; "an older taint can be transmitted if the younger taint is revealed" (Paper C, Kvalsvik and Själander, both ReCon authors). |

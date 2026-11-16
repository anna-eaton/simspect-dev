# PA4: results.tex + discussion.tex audit against simspect sources of truth (2026-11-10, partial: stopped at coordinator deadline)

Scope: ~/trippel/ISCA-27/sections/results.tex, discussion.tex, tikz/firstdet_bars_v2_{8pt,body}.tex, bugtable_v3_8pt.tex (commented out), squashrace/reconstl/recon_otb captions. Sources: wiki/state/EVAL_MANIFEST.md (EM), wiki/findings/bug/BUGS.md, URGENT_TODO.md (UT), claudelog.md (CL), bugsynth/*.md. Paper text was not edited. Items marked TODO were not finished before the deadline.

## 1. Stale or unsupported numbers (highest priority)

| # | paper location | paper says | status | correct value / action | source |
|---|---|---|---|---|---|
| 1 | results.tex:39 A-UV1 | 2,995 of 3,000 sampled tests | stale (old STT_6 shrunk-L1D run, 2026-11-07) | final protocol: 2,002/4,000 (InvisiSpec-Fu, all under the `full` setup, so it measures the setup: TA-6/CF-1) | EM:393, EM:463 |
| 2 | results.tex:39 A-UV4 | 38 tests | stale (TBE-8 arm, 20261107) | 599/50,232, first at #1 | EM:395 |
| 3 | results.tex:39 A-UV5 | [1] test | stale | 4/50,232 (2 programs, inst-021207 and inst-007645, each in both modes, all cold); constant stack slot, so it shows the mechanism, not a secret (DG-6) | EM:396, EM:401, EM:441 |
| 4 | results.tex:39 A-UV6 | 1,143 and 1,142 of 1,500 per direction | stale | 861/4,000 (first #1) on the final corpus | EM:397 |
| 5 | results.tex:41 note (1) A-UV3 | 407/590 vs 0/590 | stale as the headline count | 1,861/50,232 (cold 1,770, full 91), first #11; keep 407/590 only as the flush control | EM:394 |
| 6 | results.tex:41 note optional CS-EM | 73 of 590 | stale | own-RMW E→M (`EM_rmw`) 472 in the complete run; real defect (BUGS:42) | EM:403 |
| 7 | results.tex:62 + note:63 UV4 walk order | [157 and 162] of 1,500; "check AMuLeT's fix does not close it" | check done, and it FAILS: AMuLeT's reverted UV6 patch (5f9ac78) would close all 4,738 walk-order loads (prediction, no patched run). Complete run: walk_order 666 of 4,000 | DECIDE still open (UT:322, recommendation (a): five new bugs, walk order inside A-UV6). Paper's "your decision 2026-11-09" conflicts with UT:322 open status and bugtable_v3:21 ("not a separate bug") | UT:321-322, BUGS:49, EM:403 |
| 8 | results.tex:66 + note:67 UV5 jmp shadow | 148 of 1,500 taken; note: 134 of 3,744 | stale | final corpus: 555/4,000 (first #19; cold 439, full 116), 2,594x same-estimator (2,650x mixed); AMuLeT's own runs: 47 of 248 SpecLFB violations. Disclose: jmps come from `jmp_direct` + uniform jmp post-pass (TA-2, audit S3/S5: added after the bug was known) | EM:398, EM:358, EM:547, EM:231-254 |
| 9 | results.tex:59 + note:60 UV3 OTB | 100/100 vs 0/100; "11 of the 24 tests per direction (2% sample)" | supported but targeted: both come from the fanout OTB merge transform, now OFF for reported numbers (TA-1). Untargeted evidence now exists: R-SA-8 in the regen-lp 100% eval via x86 `mov` false dependency (E2 26/27 candidates + inst-012910 traced; E6 125/146 + inst-022384 shape B) | replace "Stage 2 reproduces it by merging" with the untargeted eval evidence; DECIDE E2LT-2 (count as detection) and RL-12 | EM:581, EM:586-589, UT:12, UT:90, CL 2026-11-11 00:35 |
| 10 | results.tex:70 UV6 race | commitToIEWDelay >= [2-3], [N] tests | no current count; only count (23,966) is pre-fix | keep inst-047231 without a count, or run a slowed-timing row; SPT 3/14/15 of 24 is from old SPT_6_oneLP | BUGS:56, BUGS:83 |
| 11 | results.tex:77 note Comparison | "at least 18x fewer for every previously known bug" | slightly overstated: same-estimator A-UV5 = 17.8x | "about 18x" or "at least 17x"; others 140x (UV3) to 2,140x (UV4) OK; 95% 3.3-96x OK | EM:545, EM:472 |
| 12 | firstdet figure + caption | "one generated corpus ... all three defenses" | incomplete disclosure: InvisiSpec and SpecLFB use only the first 4,000 of the seed order (CleanupSpec all 50,232). An extension of T1g/T3g to the full corpus was claimed by nonmin (claudenotes 19:35) with no DONE logged: check before final | add "(InvisiSpec, SpecLFB: first 4,000 tests)"; values in body.tex:31-36 match EM:391-398 under (N+1)/(K+1) both sides | EM:389, firstdet_bars_v2_body.tex:4-5 |
| 13 | results.tex:80 timing note | 0.45-1.17 CPU-s sim, 1.6-3.7 total, 1,000-2,200 tests/h; A-UV6 at test 47 (77 CPU-s), test 1 cold (3 CPU-s), A-UV4 at 47 (130 CPU-s); [19-37]x cheaper; AMuLeT A-UV3 [1.6-2.8]x faster | stale (old STT_6_fv2 T rows, 2026-11-09) and missing UV5 | final corpus, dedicated cafe1: total 3.60/3.49/2.62 CPU-s per test (gem5 0.68/1.14/0.66) + 3.0 CPU-s generation; first detections UV1 #1, UV3 #11, UV4 #1, UV5 #7,430, UV6 #1, jmp #19; CPU multiples incl. generation UV1 20.4x, UV4 11.3x, UV6 4.4x, jmp 9.0x (exec only 37.5/21.1/9.4/19.4x); AMuLeT cheaper for UV3 (0.60x; 1.11x exec only) and UV5 (0.094x, ~10x cheaper). DG-1 must be disclosed | EM:474-479, EM:391-398, UT:24 |
| 14 | discussion.tex:38 note pending squash | "17 of 20 generated gadgets" show the younger branch held | unsupported: 17/20 is RETRACTED (taint-flip across two binaries, codegen artifact) | drop the 17/20 clause; keep only the value-flip 0/12 | bugsynth/FINDINGS_SUMMARY.md:23-25, NMOSIER_PENDING_SQUASH_BUG.md:4-7 |
| 15 | discussion.tex:41 note | ReCon FP loads never speculative "need tests our generator cannot yet produce" | wrong: R-SA-13 is reached by FP routing and dominates E2/E6 (e.g. E2 100% br_x R-SA-13 2,153/2,243 twin + 2,299/2,364 static) | move R-SA-13 to Unknown bugs found | BUGS:63, EM:581, EM:592 |
| 16 | discussion.tex:41 note | SPT cmov "outside our vocabulary" | partly stale: `cmov_rr` is in fv2/fv3 vocab; SPT A2 confirmed with a hand-edited test, not reached by generated tests (SPT not run on v2/v3 corpora) | reword | SOURCE_AUDIT_SPT.md:148-152, EM:214 |
| 17 | results.tex:32 note | AMuLeT builds "driven with tests from our STT model" | stale | they are driven by the footprint model `Footprint_6_u` (one model for all three) | EM:332-336 |
| 18 | results.tex:29-30 | runs end-to-end on SPT | unsupported for the final eval: no SPT run on the v3 recipe; SPT evidence is the old SPT_6_oneLP race reproduction | say so or drop SPT from "end-to-end" | EM:235 (SPT unchanged), BUGS:83 |
| 19 | results.tex:54 note UV2 | "giving each store its own address removes all 80 such hits in 200" | true for that sample only; No-STLF E2 still fires 2/668 where the Alloy instance itself aliases. Add: A2 reproduces on ReCon authors' Ruby setup (E6), 100% E2 A2 434/435 twin + 419/409 main | add caveat + eval counts | BUGS:60, EM:495, EM:581, EM:592 |
| 20 | results.tex:39 | "STT's ... (KV3)" | naming inconsistency | A-KV3 | — |
| 21 | results.tex:255-260 "every reported leak" | data-obtained bar | known not to hold (note at :267 correct); also add RL-11 (faulting RMW scored) and the check_ld RMW limm artifact (excluded from counts) | — | UT:89, CL 2026-11-10 17:10 |

## 2. Confirmed bugs missing from the results text

| bug | BUGS.md row | in paper? | proposal |
|---|---|---|---|
| S1 xmm4 on 3 STT builds | BUGS:55 | UV1 cites /work/stt and "latest upstream" only | add AMuLeT's STT build (E4) and the eval: at 100% every gated E3/E4 hit is S1 (ld plain 794/9,460 per mode; br_x 847/876 of 10,182; RMW 688 gated), 7 idiv stems confirmed by rename 0/28 (EM:579-585) |
| R-SA-13 ReCon FP/SSE loads never speculative | BUGS:63 | no (discussion wrongly calls it unreachable) | new UV, largest class on E2/E6 |
| R-SA-18 NDA store-forward skips delay | BUGS:75 | no | NDA (E8) is recommended DROP by authorship rule (EM:609): DECIDE include or not; 8/467 STL, 42 fv2 2% |
| R-SA-14 DoM split loads bypass L1-only | BUGS:76 | no | reached but masked (E9); DECIDE |
| SL-1 SpecLFB line-crossing unsafe load | BUGS:51 | no | reached, never sole cause (inst-055160); mention as masked |
| CS-EM CleanupSpec E→M skip after squashed RMW | BUGS:42 | only as optional note | 472 in complete run; DECIDE new vs UV3 variant (AMuLeT's UV3 patch does not cover it by reading) |
| jmp shadow incl. generated jmps | BUGS:50 | yes (UV5), stale counts | see row 8 |
| A5 SPT race | BUGS:83 | in UV6 note only | promote from note; label old testset |
| R-SA-8 in eval campaign | EM:586-589 | no (only targeted OTB) | see row 9 |
| SPT A2 cmov (hand-edited test) | SOURCE_AUDIT_SPT.md:150 | listed as candidate only | mention as confirmed by directed test, not generated |

## 3. Harness artifacts needing a caveat

- H-PAD (BUGS:46): wrong-path fetch past `.text` decodes padding as an RMW and fires UV3/CS-EM; excluded from counts (complete run: UV3_padding 47, EM 7, EM:403). Add one sentence where A-UV3 counts are given.
- H-STK (BUGS:47): stack address depends on TMPDIR length; all runs use TMPDIR=/tmp, reruns must too. Methods/footnote.
- E12a store-actor (BUGS:37, CHECKER_FIX_PROPOSALS C1-a): InvisiSpec Futuristic counts squashed-store and harness `stis` DTLB fills; raw 4,000/4,000 vs ~2,002 real UV1. Caveat where InvisiSpec saturation or raw hits appear; A-UV1 K unaffected.
- Also disclose: UV1 = share of tests drawing `full` (TA-6); oracle difference per-run vs relational (DG-6); UV5 `inconsistent` window records (DG-3 could remove all four UV5 hits); classifier asymmetries <2x (DG-5); FP routing / jmp_direct / RMW added after related bugs known (EM:254).

## 4. Existing notes: proposed resolutions (partial)

- results.tex:32: accept, but change "STT model" to "footprint model" (row 17) and drop SPT from end-to-end unless run.
- results.tex:41: accept with final-corpus counts (rows 1-6).
- results.tex:50 (UV1 window wording): accept; add E4 + eval counts.
- results.tex:54 UV2: accept with row 19 additions.
- results.tex:60 UV3: rewrite evidence around untargeted R-SA-8 (row 9); fix the Fig. otb caption sentence and the interleave-figure OTB claim as the note says.
- results.tex:63 UV4: blocked on UT:322 DECIDE; the condition in the note is now known to fail.
- results.tex:67 UV5: replace counts with row 8.
- results.tex:71/73 UV6 + figure: accept; window rule still not in checker (TODO verify `resolve_visible` in gem5_common.py).
- results.tex:77 comparison: accept with "about 18x" and the 4,000-test disclosure; add DG-1 CPU caveat.
- results.tex:80 timing: replace numbers per row 13.
- discussion.tex:25 auditnote: accept (still true: only branch-only contracts in eval). TODO verify STL row.
- discussion.tex:38: drop 17/20 (row 14).
- discussion.tex:41: remove R-SA-13 and reword cmov (rows 15-16).
- discussion.tex:31/33/35/37/39/43/45: TODO (not checked line by line before deadline).

## 5. Hard decisions surfaced (Anna)

- DECIDE walk order: five or six new bugs (UT:322).
- DECIDE whether NDA (R-SA-18) and DoM (R-SA-14) results go in the paper (E8 authorship drop, EM:609).
- DECIDE E2LT-2: count R-SA-8 via mov false dependency as SimSpect's detection (UT:12).
- DECIDE DG-1/DG-2/DG-3: headline unit, interval, and over_clean window rule.
- DECIDE CS-EM new bug vs UV3 variant.

## TODO (not done before the deadline)

Line-by-line check of squashrace/reconstl/recon_otb trace numbers against their provenance files; bugtable_v3 row-by-row; ReCon authors' setup claims; STL section claims in the paper; v3 regen-lp STT/ReCon numbers vs any paper text (none currently quoted).

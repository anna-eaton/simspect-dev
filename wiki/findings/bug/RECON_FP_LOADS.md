# ReCon never marks floating-point loads speculative (R-SA-13): intent and scope

*Agent reconfp, 2026-11-16. Read-only on gem5 source; one faithful pair of single-test reruns on cafe3 (nice 19). No paper edits, no `.als` edits, no git writes.*

## Claim

**Verdict: most likely an unintended side effect, and inside ReCon's claim. Confidence: medium-high on "in scope", medium on "unintended".**

- **What happens.** In ReCon's gem5 tree, `decode.cc:685-695` registers shadows and speculative loads through an `else if` chain. The `isFloating()` arm comes before the `isLoad() && hasShadow()` arm, and its body is commented out. Every x86 SSE/x87 load micro-op (`ldfp`, `ldfp87`, `ldifp87`) is `IsFloating`, so it takes the empty arm and is never inserted as a speculative instruction. Rename then roots taint only at `isLoad() && isSpeculative()` (`rename.cc:714-720`), so the load's result is never tainted, and a transmitter fed only by it is released inside the branch shadow.
- **Why "unintended" (medium).** The `isFloating()` arm's commented-out body is `cpu->shadowTracker.insertException(inst)`, and `insertException` carries the comment "Currently unusued, no easy way to check for possible exceptions" (`shadow_tracker.cc:57`). So the arm exists to make floating-point instructions cast *exception shadows* (E-shadows), as in the shadow framework ReCon cites for its speculation tracking (Sakalis et al., ISCA'19 §2: "E-Shadows are cast by memory operations with unknown addresses, arithmetic operations, and any other instructions that can cause an exception"). ReCon's evaluation drops exception shadows on purpose (§6.1, quoted below), which explains the commented-out call. Nothing in the code or the paper says floating-point *loads* under a *branch or store* shadow should go unprotected; that follows only from the arm's position in the `else if` chain. I found no comment, README, issue or paper sentence stating it as a choice. The confidence is not higher because we have no git history (the authors' tree has none) and no public repository to check, and because even the original design (with `insertException` active) would not have marked FP loads speculative: the arm was never written with FP loads in mind, which reads as an oversight but cannot be proven one.
- **Why "in scope" (medium-high).** ReCon is "applied on top of" STT and says the underlying mechanism "maintains its entire threat model" except for revealed values (§3.1). STT protects every speculatively loaded value ("We focus on the case where access instructions are loads", STT §6.1; "Except for loads, there are only a handful of such instructions", STT §6.1.1); neither paper excludes floating-point or vector loads, and ReCon's §6.1 exclusion is about *what casts speculation* (loads, exception-raising instructions), not about which loads under a control or store shadow are protected. In our tests the FP load sits in an ordinary branch shadow, which ReCon evaluates. One more hint that FP loads were meant to stay protected: ReCon's only way to lift protection, the load-pair table, has "as many entries as physical integer registers" (ReCon §5.1), so an FP load's value would never be revealed and should simply stay tainted.
- **Not ReCon-specific code inherited from elsewhere.** Upstream gem5 v22.0.0.0 `src/cpu/o3/decode.cc` has no shadow tracker and no scheme check (0 matches for "shadow" or "scheme"; `secure_scheme/shadow_tracker.cc` returns 404 at that tag). STT's implementations (`/work/stt`, `/work/stt-master`) have no such chain: their taint root is `isAccess() { return staticInst->isLoad(); }` (`base_dyn_inst.hh:675`) with no floating-point exception, tainted at `rob_impl.hh:812-813`. So the branch is ReCon's own (or its shared Uppsala infrastructure's, "an infrastructure that shares implementations for NDA, STT, and RECON", §6.1), and STT itself protects FP loads.

**Recommendation (labeled as such):** the evidence fits wording (b) below better than (a). Wording (a) is still accurate if it does not claim the skip is intentional and only says we do not adjudicate it; the version below is written that way. Either way, the current Discussion clause is false and must change.

## Evidence

### 1. The code (all builds we run)

Identical text in `/work/gem5-recon`, `/work/gem5-recon-modded`, `/work/gem5-recon-ruby3` (row E6) and `/work/gem5-recon-modded-stl` (row E2w-stl) on cafe2/cafe3, and in the authors' docker tree `~/Downloads/dockerrecon/gem5-recon/src/cpu/o3/decode.cc:685-696` (same line numbers):

```cpp
        if (cpu->scheme != CPU::Scheme::Unsafe) {
          if (inst->isCondCtrl()){
              inst->branchResolved(false);
              cpu->shadowTracker.insertBranch(inst);
          } else if (inst->isStore()) {
              cpu->shadowTracker.insertStore(inst);
          } else if (inst->isFloating()){
//              cpu->shadowTracker.insertException(inst);
          } else if (inst->isLoad() && cpu->shadowTracker.hasShadow()) {
              cpu->shadowTracker.insertSpecInst(inst);
          }
        }
```

- `secure_scheme/shadow_tracker.cc:57-62`: `//Currently unusued, no easy way to check for possible exceptions` above `insertException`, which only pushes onto `exceptions`. `insertSpecInst` (`:78-84`) is the only place that calls `inst->setSpeculative(true)`.
- `rename.cc:714-720` (scheme STT): `if (inst->isLoad() && inst->isSpeculative()) taintTracker.insertTaintInst(inst); else taintTracker.propagateTaints(inst);`. An FP load with an untainted address register therefore produces an untainted result.
- The chain applies to every non-Unsafe scheme, so NDA (scheme 1) and DoM (scheme 3) on this tree skip FP loads too (claudelog 2026-11-08 R-SA-13 entry; `MODELS_AND_BUILDS.md:448`). Only STT (scheme 2) is in the paper.
- FP stores are not affected (`isStore()` is tested first), and FP branches do not exist on x86.

### 2. x86 SSE loads are `IsFloating` (gem5-recon-modded ISA files)

- `src/arch/x86/isa/microops/ldstop.isa:513-514`: `defineMicroLoadOp('Ldfp', code='FpData_uqw = Mem', big=False, is_float=True)`; `Ldfp87` (`:516`) and `Ldifp87` (`:532`) likewise.
- `src/arch/x86/isa/operands.isa:86-88`: `class FloatReg(FloatRegOp): ... super().__init__('df', idx, 'IsFloating', id)`; `:169`: `'FpData': FloatReg('data', 25)`. The ISA parser collects operand flags into the instruction's flags (`src/arch/isa_parser/isa_parser.py:395`, `self.flags = self.operands.concatAttrLists('flags')`; `:425-430` names the resulting op class `FloatMemReadOp` when both `IsLoad` and `IsFloating` are set, with the comment "'IsFloating' and 'IsInteger' are usually set in FP instructions"). It also adds `checkFpEnableFault` to every `IsFloating` instruction (`:447-448`), which is the exception an E-shadow would cover.
- `src/arch/x86/isa/insts/simd128/integer/data_transfer/move.py:42-45`: `MOVQ_XMM_M` = `ldfp xmml, seg, sib, disp, dataSize=8; lfpimm xmmh, 0`. This is the `movq mem, %xmmK` form that Stage 2's vector routing emits.

### 3. Papers (local copies)

- ReCon, Aimoniotis et al., MICRO'23 (`~/Documents/quail/sources/papers/aimoniotis-2023-recon.pdf`):
  - §3.1 "STT and NDA Integration": "RECON is a performance optimization that is applied on top of secure speculation mechanisms, e.g., NDA or STT. The underlying secure mechanism maintains its entire threat model except for values that previously have been made public". Same section, "Speculative Model": "RECON can operate under any speculative model ... For evaluation, we use only speculation cast by control flow and store instructions".
  - §6.1 "Methodology": "Speculation state is tracked through shadows [38, 39]. We evaluate only speculation that is triggered by control and store instructions ... We do not consider speculation triggered by load instructions and instructions that can raise an exception for the following reasons: ... speculation caused by instructions that can raise an exception lie on a different spectrum of attacks [29]." ([38] = Ghost loads, [39] = Sakalis et al. ISCA'19.)
  - §5.1: the load-pair table has "at most, as many entries as physical integer registers".
  - No mention of floating-point, SSE, vector or SIMD loads anywhere in the text (grep of the extracted text).
- STT, Yu et al., MICRO'19 (`yu-2019-stt.pdf`): §6.1 "We focus on the case where access instructions are loads, as this will be sufficient to block universal read gadget attacks (Section 4). STT taints the output of any speculative access instruction." §6.1.1 "An instruction should be an access instruction if it has the potential to read a secret. Except for loads, there are only a handful of such instructions". No FP exclusion; the TR (`yu-2019-stt-formal-tr.pdf`) models memory as integers and has none either.
- Sakalis et al., "Efficient Invisible Speculative Execution through Selective Delay and Value Prediction", ISCA'19 §2 "Speculative Shadows" (saved to `paper_figures/caroline/papers/sakalis_isca19_selective_delay.pdf`, fetched from https://webs.um.es/aros/papers/pdfs/csakalis-isca19.pdf): E-shadows include "arithmetic operations, and any other instructions that can cause an exception"; "floating point exceptions can usually be configured through special registers ... For our evaluation, we assume that floating point exceptions are disabled." This is the design the `isFloating` → `insertException` arm implements.
- Public ReCon code: none found (web search 2026-11-16 for the ReCon gem5 repository, `shadow_tracker`, `secure_scheme`; the paper gives no artifact link). Our tree is the authors' docker image (no git), so there is no history or issue tracker to check.

### 4. One faithful trace (E2w, inst-000037, mispredict_not_taken)

Rerun with the E2w row config verbatim (`runconfigs/bigcorpus_20261115/E2w_STT_6_u_core_lpP_s2A.jsonc`: `gem5-recon-modded`, scheme 2, BTB force, warm cache, the campaign's timing-grid point; only paths, `keep_tmp`, `jobs 1`, one mode, and the print-only debug flags Commit, DelayUnit, Rename, IEW added), by `scripts/reconfp_20261116/rerun_reconfp.sh` (a copy of fig8-otb-v5's `rerun_otb_v5.sh` with only the output dir changed). Output: cafe3 `/tests/bigcorpus_20261115/e2w/reconfp/{vec,int}_not_taken_inst-000037/` (run.log, cfg.json, pipeview.txt.gz, stats.txt, sha256s.txt; gem5.opt sha256 `44e14c11…3f4154`). Both reproduce the campaign: the vector version hits, the integer version (the E2w GPR twin, testset `STT_6_u_core_lpP_s2A_gprtwin`) holds.

The two programs differ only in how pc2's value reaches rcx:

```
            vector version (corpus)                      integer version (GPR twin)
pc0 (lc)    movq 8(,%r11), %xmm13 ; movq %xmm13, %rcx    movq 8(,%r11), %rcx
pc1         ... cmpq $1, %rax ; jae .Ltmp0  (mispredicted not taken, held unresolved)
pc2         movq (%r11,%rcx), %xmm3                      movq (%r11,%rcx), %rcx
            pxor/por -> %xmm0 ; movq %xmm0, %rcx
pc3 (xmit)  movq (%r11,%rcx), %rcx                       movq (%r11,%rcx), %rcx
```

Vector version (window branch 0x401c5b sn:557: held 2,675,000, resolves visibly 3,925,500; lc retires 2,631,500):

```
2673500: lsq: Executing load PC (0x401c62=>0x401c68).(0=>1), [sn:559]          <- pc2, ldfp into xmm3
2673500: lsq: STL_CHECK: load PC 0x401c62 isTainted=0 isSpeculative=0          <- inside the shadow, not speculative
2724000: lsq: Executing load PC (0x401c82=>0x401c86).(0=>1), [sn:569]          <- transmitter
2724000: lsq: STL_CHECK: load PC 0x401c82 isTainted=0 isSpeculative=1          <- speculative, but untainted: not delayed
2724000: lsq: Memory request (pkt: ReadResp [35c0:35c7]) from inst [sn:569] was sent
3925500: commit: Squashing due to branch mispred PC:0x401c5b [sn:557]
3926000: lsq: Load Instruction PC (0x401c82=>0x401c86).(0=>1) squashed, [sn:569]
```

check_ld record: `issued_in_window true`, `xmit_signal 2724000`, `lc_retire 2631500 < signal < fnc_retire 3926000`, `branches_unresolved true`, `data_obtained true` (`cache_fate store_forward`, completion 2,725,000; the trace also shows the request sent, which the data-obtained gate does not read on this build, the known `recon_cache_reach_gate` gap). stats: `delay_unit.insertedTaintedLoads` 0.

Integer version (same timing point): pc2 `STL_CHECK: load PC 0x401c54 isTainted=0 isSpeculative=1`; transmitter `STL_CHECK: load PC 0x401c5e isTainted=1 isSpeculative=1`, then `delay_unit: Inserted tainted load [sn:559] into delay_unit`; it never executes before the squash at 3,925,000. `issued_in_window false`; stats `delay_unit.insertedTaintedLoads 1`.

### 5. Counts (reported ReCon rows; per-record labels from `classify.py bucket`)

Counted with `scripts/reconfp_20261116/count_rsa13.py` over each row's `buckets_per_stem.json`.

| row | hit records | R-SA-13, all labels | of which integer twin held (`R-SA-13`, `via FP elsewhere`, `replay`) | static only (no faithful twin; mostly RMW) | tests (program x mode) / programs |
|---|---|---|---|---|---|
| E2w (cafe3 `/tests/bigcorpus_20261115/e2w/`, 30,368 tests) | 18,029 | **12,973 (72%)** | 9,924 | 3,049 (338 plain + 2,711 RMW) | 12,973 tests over 6,522 of the 9,039 hit programs; not_taken 6,458, taken 6,515; br_x 5,483, ld plain 4,779, ld RMW 2,711 |
| E2w-stl (cafe1 `/tests/reconstlhook_20261116/triage/bucket_v2/`, 60,342 tests, one mode) | 33,671 | **23,662 (70%)** | 17,718 (17,573 + 142 + 3) | 5,944 (594 plain + 5,350 RMW) | 23,662 tests = programs; br_x 7,177, ld plain 11,132, ld RMW 5,353 |

- The EVAL_MANIFEST figure 23,659 is the original bucket; rstltriage added 3 (`bucket_v2`). After the RG-1 resolved-branch gate, E2w is unchanged and E2w-stl loses 430 R-SA-13 records (23,232 of 33,047; EVAL_MANIFEST "Resolved-branch gate").
- "Integer twin held" is the "both register versions" evidence: the same program with vector routing off (recipe A with `fpr` off) does not hit. The "static only" records have an SSE-load producer on the transmitter's slice but no faithful twin run (RMW programs and jmp-filler programs were not twinned).
- The `inttwin_20261116` classification (cafe3 `/tests/inttwin_20261116/cls/`) does not exist yet, so the paired E2w integer-twin campaign is not counted here.

## What is still open

- **Intent cannot be settled from code alone.** No git history, no public repository. Asking the ReCon authors would settle it; that is Anna's call (external contact).
- **Possible implication for ReCon's own numbers (unverified, do not state in the paper without checking):** if the evaluated tree is this one, FP loads in SPEC's floating-point benchmarks were never delayed or tainted under STT, NDA or DoM, which would make those baselines' overheads lower than the papers' designs imply. I did not check which benchmarks or how many loads.
- **inttwin row:** when cafe3's `inttwin_20261116` classification finishes, recount R-SA-13 on its E2w pairs.
- **Bucket scripts:** `STAGE3_gem5/bugs/r_sa13_recon_sse_load.py` still says "real gem5 defense behaviour ... not a paper bug" with no reason; its `VERDICT` is already `real_bug`. Once Anna decides, update the docstring (docstring only; then run `bugs/_regress.py`). I did not edit it.

## Paper wording (proposal only; paper not edited)

Current text, `~/trippel/ISCA-27/sections/discussion.tex:37` (ISCA-27 7f60698), verbatim:

> Source reading also finds candidate bugs that need tests we cannot yet produce: interactions between cores (an InvisiSpec request that downgrades another core's copy of a line), instructions outside our vocabulary (SPT's untaint rules for flags, conditional moves and 8- and 16-bit writes; ReCon's floating-point loads, which are never marked speculative), and shapes beyond our bound (a squash in the middle of the window while an older shadow is still open).

Both options first drop the ReCon item from that sentence:

old: `instructions outside our vocabulary (SPT's untaint rules for flags, conditional moves and 8- and 16-bit writes; ReCon's floating-point loads, which are never marked speculative), and shapes beyond our bound`

new: `instructions outside our vocabulary (SPT's untaint rules for flags, conditional moves, and 8- and 16-bit writes), and shapes beyond our bound`

Then add one sentence right after `while an older shadow is still open).`:

**(a) Anna's framing (property of the implementation, not counted as a bug):**

> ReCon's implementation never marks a floating-point load speculative, so its result is never tainted (\texttt{decode.cc:691--692}); \toolname{}'s vector-register tests reach this path, and it explains about 70\% of ReCon hits. ReCon's paper does not discuss floating-point loads, and the skipped code would register floating-point instructions as exception shadows, which ReCon's evaluation excludes~\cite[\S 6.1]{recon}, so we report this behavior separately and do not count it among the bugs.

**(b) If Anna decides it is an unintended defect within ReCon's claim:**

> ReCon's implementation never marks a floating-point load speculative (\texttt{decode.cc:691--692}): the code that would register floating-point instructions as exception shadows, which ReCon's evaluation excludes~\cite[\S 6.1]{recon}, is disabled but still diverts floating-point loads from the check that marks loads in a shadow speculative. Their results are never tainted, although STT protects every speculative load~\cite[\S 6.1]{yu2019stt}; \toolname{}'s vector-register tests reach this path, and it explains about 70\% of ReCon hits.

Notes for either option: (1) the paper's code-citation rule wants a pinned commit, but the authors' tree has none; cite it as the authors' artifact (e.g., "the authors' gem5 tree") or a new bib entry. (2) Under (b), the Discussion would name a defect that the intro's "six previously unknown bugs" and Results do not list; consistency would mean either adding it there (a seventh bug) or keeping it as a Discussion-only note, which is a separate decision. (3) "about 70\%" is the share of hit records in rows E2w (72%) and E2w-stl (70%); if the paper reports only one row, use that row's figure.

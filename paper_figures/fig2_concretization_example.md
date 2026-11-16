# Fig. 2 concretization example (real generated test)

Found 2026-11-16 by fig2-example-agent (read-only; nothing in the paper changed). Everything quoted below is copied verbatim from the generated files on cafe2; nothing was written by hand.

## 1. The test

**Stem `inst-024552`**, testset **`STT_6_u_core_lpP_fv3`** (the STT corpus behind the paper, EVAL_MANIFEST :765), branch mode **`mispredict_not_taken`**, Stage 1 core c006 (MANIFEST.tsv). Files (cafe2, container `gem5_dev`, root `/tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/`): XML `xml/inst-024552.xml` (text dump `xml/inst-024552.txt`), program `mispredict_not_taken/asm/inst-024552.s` (353 lines), annotation `mispredict_not_taken/ann/inst-024552.ann.json`. It is not in rmw_stems.tsv or jmp_stems.tsv. It is not in the sampled E3 results (`E3_STT_6_u_core_lpP_fv3__latest`), so I don't know whether it hits.

**How it was chosen.** I scanned all 53,908 XMLs of the corpus for this chain: an unresolved `Branchn` before an uncommitted `Load` L, with a ddi edge from L's inmem to L's outreg; an rf edge from L's outreg into an `Othern` O; an rf edge from O's outreg into the inaddr of the single xmit `Load`. 172 tests match. No test has exactly 4 instructions, because Stage 1b requires a committed instruction. The smallest have 5 instructions (42 tests), all with the Fig. 2 chain at pc1–pc4 and one committed instruction at pc0. Among those 42, `inst-024552` is the cleanest one whose ALU has the Fig. 2 form `r2 ← r1, r0`: a single fp route, one splice, one filler, no jmp insert, and a plain-load transmitter.

## 2. Mapping to Fig. 2

| Fig. 2 | test | Alloy atom | asm |
|---|---|---|---|
| (none) | pc0, committed `Store` (last_committed) | Instruction$1 | `movq %rdi, (%r13,%r11)` |
| i0 `Branch_n`, unresolved | pc1 (first_noncommitted) | Instruction$4 | `movq $1, %r14; cmpq $1, %r14; jae .Ltmp0` |
| i1 `Load` r1 ← m1 | pc2 | Instruction$2 | `movq (%r13,%r11), %r11` (+ xmm4 route) |
| i2 `Other_n` r2 ← r1, r0 | pc3 | Instruction$0 | `leaq (%r11,%rdx), %r11` |
| i3 `Load` ← [r2], xmit | pc4 | Instruction$3 | `movq (%r13,%r11), %rsi` |

Edges in the XML: `ddi = {Inmem$1->Outreg$1 (i1), Inreg$0->Outreg$0 (i2)}`, `rf = {Outreg$1->Inreg$0 (i1→i2), Outreg$0->Inaddr$1 (i2→i3), Outmem$0->Inmem$1, Outmem$0->Inmem$0}`. So m1 →ddi→ r1 →rf→ i2 →ddi→ r2 →rf→ [r2], exactly as in Fig. 2. pc1–pc4 are uncommitted, and the branch is the only unresolved instruction.

**Differences from Fig. 2.**

- **Committed store pc0.** It writes the slot that i1 and the transmitter read (the two `Outmem$0` rf edges). Fig. 2 has no store.
- **Free ALU operand.** In Alloy, i2 has only one inreg. The second operand `%rdx` (Fig. 2's r0) is a free operand filled during concretization.
- **Branch condition.** The branch has no Alloy operands. Stage 2 gives it a constant condition (`$1 ≥ 1`, so it is really taken), and the BTB forces a not-taken prediction into pc2.
- **Stage 2 additions:**
  - an xmm4 round trip after the load (`fpr.routes`: pc2, xmm 4, form `route`);
  - a no-op splice `xorq $0, %r11` between i1 and i2;
  - a dead filler `movq %rdx,%r10; imulq %rdx,%r10` before pc2.
- **Caveat on xmm4.** The xmm4 route is the S1_xmm4 shape, a known real STT gem5 bug. A reader of the gem5 results could recognize it. If that matters, the alternative is `inst-025184`: same 5-instruction chain, `leaq (%r12,%r9), %r9` routed through xmm3, but it has a jmp inserted before the transmitter.

## 3. Program excerpt (verbatim, `mispredict_not_taken/asm/inst-024552.s` lines 295–337)

```
295		.globl	__litmus_inst_024552_pc0
296	__litmus_inst_024552_pc0:
297		.globl	__litmus_inst_024552_last_committed
298	__litmus_inst_024552_last_committed:
299		movq	%rdi, (%r13,%r11)
...
302		.globl	__litmus_inst_024552_pc1
303	__litmus_inst_024552_pc1:
...
306		movq	$1, %r14
...
309		cmpq	$1, %r14
310		jae	.Ltmp0
...
314		movq	%rdx, %r10
315		imulq	%rdx, %r10
...
319		.globl	__litmus_inst_024552_pc2
320	__litmus_inst_024552_pc2:
321		movq	(%r13,%r11), %r11
322		movq	%r11, %xmm4
323		movq	$0, %r11
324		movq	%xmm4, %r11
...
327		xorq	$0, %r11
...
330		.globl	__litmus_inst_024552_pc3
331	__litmus_inst_024552_pc3:
332		leaq	(%r11,%rdx), %r11
...
335		.globl	__litmus_inst_024552_pc4
336	__litmus_inst_024552_pc4:
337		movq	(%r13,%r11), %rsi
```

The elided lines (`...`) are only `#APP` / `#NO_APP` markers, the `first_noncommitted` label (304–305), the `# %bb.1` block comment (312) and the base-pointer reload `movq %rsp, %r13` (317). The function ends at 339–341 (`.Ltmp0:` / `.LBB0_2: # %end_block`).

## 4. Annotation excerpt (verbatim, `mispredict_not_taken/ann/inst-024552.ann.json` lines 2–34)

```
  "branch_mode": "mispredict_not_taken",
  "annotations": [
    {
      "branch_pc": 1,
      "btb_forced_target_pc": 2,
      "mode": "mispredict_not_taken",
      "branch_addr": 4201522,
      "branch_addr_hex": "0x401c32",
      "btb_forced_target_addr": 4201534,
      "btb_forced_target_addr_hex": "0x401c3e"
    }
  ],
  "xmit": {
    "pc": 4,
    "kind": "ld",
    "atom": "Instruction$3",
    "addr": 4201564,
    "addr_hex": "0x401c5c"
  },
  "commit_boundary": {
    "last_committed": {
      "pc": 0,
      "atom": "Instruction$1",
      "addr": 4201506,
      "addr_hex": "0x401c22"
    },
    "first_noncommitted": {
      "pc": 1,
      "atom": "Instruction$4",
      "addr": 4201522,
      "addr_hex": "0x401c32"
    }
  },
```

## 5. PROPOSED listing for §4.3 (not applied; Anna places it)

The instruction text is verbatim from the `.s`. The `i0`–`i3` comments, the `...` elision and the `ann:` line are added labels that summarize the annotation.

```latex
\begin{figure}[t]\centering\fontsize{8pt}{9.5pt}\selectfont
\begin{verbatim}
   movq %rdi,(%r13,%r11)    # committed (last_committed)
   cmpq $1,%r14; jae .Ltmp0 # i0 Branch_n, unresolved
   movq (%r13,%r11),%r11    # i1 Load r1 <- m1
   movq %r11,%xmm4 ... movq %xmm4,%r11 # FP route
   leaq (%r11,%rdx),%r11    # i2 Other_n r2 <- r1,r0
   movq (%r13,%r11),%rsi    # i3 Load [r2] (xmit)
ann: xmit=pc4 (ld); commit boundary pc0|pc1;
     pc1 BTB-forced not-taken -> pc2
\end{verbatim}
\vspace{-6pt}
\caption{Concretization of the Fig.~\ref{fig:ddi-rf} graph: an x86 excerpt of generated STT test \texttt{inst-024552} and its annotation.}
\end{figure}
```

Notes for placing it:

- The `fig:ddi-rf` label is the one named in the tikz header comment. Check that it matches the label the paper actually uses.
- In the source, `cmpq` and `jae` are on separate lines (309–310), and `movq $1,%r14` (306) sets the condition. They are joined onto one line here only to save space.
- If the xmm4 caveat in §2 matters, either drop the route line or switch to `inst-025184`.

## 6. inst-025184 (Anna's choice)

**The test.** Stem `inst-025184`, same corpus (`STT_6_u_core_lpP_fv3`), branch mode **`mispredict_not_taken`**. Files are under the same cafe2 root as above: `xml/inst-025184.{xml,txt}`, `mispredict_not_taken/asm/inst-025184.s`, `mispredict_not_taken/ann/inst-025184.ann.json`. The mode matters. In `mispredict_taken` the jmp sits before pc3, not pc4 (`jmp_stems.tsv`: `mispredict_taken inst-025184 3 0x401c82 4 uniform 1`), so the not_taken program is the one with the jmp between the ALU and the transmitter.

**Correction to §1.** My earlier scan read the wrong column of `jmp_stems.tsv` (its first column is the mode), so every "jmp" flag it printed was wrong. The `jmp_insert` field in each annotation is the authoritative source.

**Mapping to Fig. 2.**

| Fig. 2 | test | Alloy atom | asm (`.s` line) |
|---|---|---|---|
| (none) | pc0, committed `Other_n` (last_committed) | Instruction$1 | `movq %r13, %r9` / `incq %r9` (303–304) |
| i0 `Branch_n`, unresolved | pc1 (first_noncommitted) | Instruction$4 | `movq $1, %rdx` (315), `cmpq $1, %rdx` (318), `jae .Ltmp0` (319) |
| i1 `Load` r1 ← m1 | pc2 | Instruction$3 | `movq (%r10), %r12` (326) + xmm3 route (327–331) |
| i2 `Other_n` r2 ← r1, r0 | pc3 | Instruction$0 | `leaq (%r12,%r9), %r9` (336) |
| (none) | inserted jmp | (not in Alloy) | `jmp .Lsimspect_jmpins` (342) |
| i3 `Load` ← [r2], xmit | pc4 | Instruction$2 | `movq (%r10,%r9), %r12` (348) |

**XML edges.**

- `ddi = {Inmem$0->Outreg$3 (i1), Inreg$0->Outreg$2, Inreg$1->Outreg$2 (i2)}`
- `rf = {Outreg$3->Inreg$0 (i1→i2), Outreg$2->Inaddr$0 (i2→i3), Outreg$1->Inreg$1 (pc0→i2)}`

So the chain m1 →ddi→ r1 →rf→ i2 →ddi→ r2 →rf→ [r2] matches Fig. 2. Unlike in `inst-024552`, both of the ALU's input registers are Alloy operands here: r0 is `%r9`, which the committed pc0 produces. Only the branch is unresolved, and pc1–pc4 are uncommitted.

**The inserted jmp.**

- **Source:** lines 340–343, `__litmus_inst_025184_jmpins:` / `jmp .Lsimspect_jmpins` / `.Lsimspect_jmpins:`.
- **Target:** a direct unconditional jump to the label on the very next line. It jumps to the next instruction, the transmitter's base reload `leaq 64(%rsp), %r10` is before it (338), and it changes no data.
- **Which pass inserted it:** Stage 2's jmp-insertion pass. Annotation lines 121–130: `"before_pc": 4`, `"addr_hex": "0x401c7f"`, `"p": 0.5`, `"n_candidates": 5`, `"placement": "uniform"`, `"in_window": true`.
- **Not a fanout filler:** it is not one of the `fanout_v2.fillers` entries, and it is not an Alloy instruction.
- **Position:** it sits between the ALU (i2) and the transmitter (i3), inside the speculative window, so the listing keeps it.

**Other Stage 2 additions:**

- an xmm3 round trip after the load (`fpr.routes`: pc2, xmm 3, form `route_alu`, alu_xmm 6; lines 327–331);
- two dead fillers: `movq %r15,%rdi; andq %r13,%rdi` before pc0 (295–296), and `movq %r13,%r8; xorq %r9,%r8` before pc1 (307–308);
- the base-pointer reloads `leaq 56(%rsp), %r10` (322) and `leaq 64(%rsp), %r10` (338).

**Program excerpt (verbatim, `mispredict_not_taken/asm/inst-025184.s` lines 299–348; elided lines are `#APP`/`#NO_APP`, fillers and labels as listed above):**

```
299		.globl	__litmus_inst_025184_pc0
300	__litmus_inst_025184_pc0:
301		.globl	__litmus_inst_025184_last_committed
302	__litmus_inst_025184_last_committed:
303		movq	%r13, %r9
304		incq	%r9
...
311		.globl	__litmus_inst_025184_pc1
312	__litmus_inst_025184_pc1:
...
315		movq	$1, %rdx
...
318		cmpq	$1, %rdx
319		jae	.Ltmp0
...
322		leaq	56(%rsp), %r10
...
324		.globl	__litmus_inst_025184_pc2
325	__litmus_inst_025184_pc2:
326		movq	(%r10), %r12
327		movq	%r12, %xmm3
328		pxor	%xmm6, %xmm6
329		por	%xmm3, %xmm6
330		movq	$0, %r12
331		movq	%xmm6, %r12
...
334		.globl	__litmus_inst_025184_pc3
335	__litmus_inst_025184_pc3:
336		leaq	(%r12,%r9), %r9
337		#NO_APP
338		leaq	64(%rsp), %r10
339		#APP
340		.globl	__litmus_inst_025184_jmpins
341	__litmus_inst_025184_jmpins:
342		jmp	.Lsimspect_jmpins
343	.Lsimspect_jmpins:
344		#NO_APP
345		#APP
346		.globl	__litmus_inst_025184_pc4
347	__litmus_inst_025184_pc4:
348		movq	(%r10,%r9), %r12
```

**Annotation excerpt (verbatim, `mispredict_not_taken/ann/inst-025184.ann.json` lines 2–34 and 121–130):**

```
  "branch_mode": "mispredict_not_taken",
  "annotations": [
    {
      "branch_pc": 1,
      "btb_forced_target_pc": 2,
      "mode": "mispredict_not_taken",
      "branch_addr": 4201555,
      "branch_addr_hex": "0x401c53",
      "btb_forced_target_addr": 4201562,
      "btb_forced_target_addr_hex": "0x401c5a"
    }
  ],
  "xmit": {
    "pc": 4,
    "kind": "ld",
    "atom": "Instruction$2",
    "addr": 4201601,
    "addr_hex": "0x401c81"
  },
  "commit_boundary": {
    "last_committed": {
      "pc": 0,
      "atom": "Instruction$1",
      "addr": 4201532,
      "addr_hex": "0x401c3c"
    },
    "first_noncommitted": {
      "pc": 1,
      "atom": "Instruction$4",
      "addr": 4201555,
      "addr_hex": "0x401c53"
    }
  },
...
  "jmp_insert": {
    "before_pc": 4,
    "addr": 4201599,
    "addr_hex": "0x401c7f",
    "seed": 20261109,
    "p": 0.5,
    "n_candidates": 5,
    "placement": "uniform",
    "in_window": true
  }
```

**PROPOSED listing for §4.3 (not applied; Anna places it).**

What is verbatim and what is changed:

- **Verbatim:** the instruction text, from `.s` lines 303–304, 318, 319, 326, 336, 342 and 348.
- **Whitespace:** tabs are replaced by single spaces.
- **Joined:** pc0's two instructions share one line.
- **Elided:** the xmm3 round trip (327–331) is the single `...` line.
- **Added labels:** the `#` comments and the `ann:` line.

The listing is 9 lines, with cmpq and jae on separate lines.

```latex
\begin{figure}[t]\centering\fontsize{8pt}{9.5pt}\selectfont
\begin{verbatim}
movq %r13, %r9; incq %r9  # committed (pc0)
cmpq $1, %rdx             # i0 Branch_n, unresolved
jae .Ltmp0
movq (%r10), %r12         # i1 Load r1 <- m1
...
leaq (%r12,%r9), %r9      # i2 Other_n r2 <- r1, r0
jmp .Lsimspect_jmpins     # inserted jmp (to next line)
movq (%r10,%r9), %r12     # i3 Load [r2], xmit
ann: xmit pc4 (ld); commit pc0|pc1; pc1 BTB -> pc2
\end{verbatim}
\vspace{-6pt}
\caption{An excerpt of the x86 program and annotation that SimSpect generated for an STT test with the execution graph of Fig.~\ref{fig:ddi-rf}.}
\end{figure}
```

Two checks before placing it:

- **Width:** the widest line is about 52 characters. That should fit the 241pt ACM column at 8pt monospace (about 4.2pt per character), but confirm on the compiled PDF.
- **Label:** confirm that `fig:ddi-rf` is the label the paper actually uses.

## 7. Clean running example (no xmm, no STT hit)

Found 2026-11-16 by clean-example-agent (read-only; no paper file and no git state changed; no gem5 run). Scripts and raw tables: `scripts/clean_example_20261116/` (`scan_fig2_chain.py` = the Fig. 2 chain scan over the XML text dumps, `lookup_results.py` = per-stem E3/E4 records, `scan_out.tsv`, `e3_lookup.tsv`).

**Headline: a test with no xmm on the chain does not exist in this corpus, so I picked the cleanest one whose xmm route is not xmm4.** Every program in `STT_6_u_core_lpP_fv3` was built with `fpr.loads: "consumed"` (each annotation's `fpr` block), so Stage 2 routes every load whose value is consumed through an xmm register. All 172 Fig. 2 tests (344 test×mode records) have an xmm route between i1 and the transmitter. UV1 is specific to xmm4 (`STAGE3_gem5/bugs/uv1_stt_xmm4.py`: STT skips taint on FP index 16, the low half of xmm4; renaming xmm4 to xmm3 removes the hits, BUGS.md UV1 row), so a test routed through another xmm register is not the UV1 shape. This is a decision for Anna (see the DECIDE at the end of this section).

**Recommended stem: `inst-023734`**, testset `STT_6_u_core_lpP_fv3`, mode **`mispredict_not_taken`**, Stage 1 core c050 (MANIFEST.tsv). Files on cafe2, container `gem5_dev`, root `/tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/`: `xml/inst-023734.{xml,txt}`, `mispredict_not_taken/asm/inst-023734.s` (368 lines), `mispredict_not_taken/ann/inst-023734.ann.json`. It has 5 instructions, no `jmp_insert`, no RMW (not in `rmw_stems.tsv` or `jmp_stems.tsv`), no `xmm4` anywhere in the `.s`, and its ALU has Fig. 2's form `r2 ← r1, r0` with a distinct r0 (`leaq (%r8,%rcx), %r15`).

**Why this one.** Among the 155 not_taken records with no xmm4 route, I kept the 5-instruction tests with no inserted jmp that do not hit on E3 in either mode (13 tests). Of those, only `inst-023734` has an ALU that reads two different registers. The others read r1 twice (`leaq (%r14,%r14),%r14` in inst-007787, inst-018288, inst-022563, inst-010489), use a `cmov` shape (inst-017704, inst-017495, inst-004420, inst-000350, inst-002099, inst-016043), or have a `notq` ALU (inst-024509). The closest alternative with a two-register ALU is `inst-009809` (`leaq (%r13,%r15), %r13`, xmm13 route, E3 no hit), but it has an inserted jmp.

### 7.1 Mapping to Fig. 2

| Fig. 2 | test | Alloy atom | asm (`.s` line) |
|---|---|---|---|
| (none) | pc0, committed `Load` (last_committed) | Instruction$1 | `movq (%rsi,%r8), %r15` (299) + xmm0 route (300–302) |
| i0 `Branch_n`, unresolved | pc1 (first_noncommitted) | Instruction$4 | `movq %r15, %rax; andq $0, %rax; orq $1, %rax` (316–318), `cmpq $1, %rax` (321), `jae .Ltmp0` (322) |
| i1 `Load` r1 ← m1 | pc2 | Instruction$3 | `movq (%rsi,%r15), %r8` (329) + xmm11/xmm5 route (330–334) |
| i2 `Other_n` r2 ← r1, r0 | pc3 | Instruction$0 | `leaq (%r8,%rcx), %r15` (342) |
| i3 `Load` ← [r2], xmit | pc4 | Instruction$2 | `movq (%rsi,%r15), %r8` (351) |

**XML edges (`xml/inst-023734.txt`).**

- `ddi = {Inmem$1->Outreg$2 (i1), Inreg$0->Outreg$1 (i2), Inmem$0->Outreg$0 (pc0), Inmem$2->Outreg$3 (i3)}`
- `rf = {Outreg$2->Inreg$0 (i1→i2), Outreg$1->Inaddr$2 (i2→i3), Outreg$0->Inaddr$0 (pc0→i1 address), Outreg$0->Inreg$1 (pc0→branch condition)}`
- `isresolved` covers every instruction except Instruction$4 (the branch); `iscommitted = {Instruction$1}`; `isxm = {Instruction$2}`.

So m1 →ddi→ r1 →rf→ i2 →ddi→ r2 →rf→ [r2] is exactly Fig. 2's chain, pc1–pc4 are uncommitted, and the branch is the only unresolved instruction.

**Differences from Fig. 2.**

- **Committed load pc0.** It produces i1's address register (`%r15`) and the branch's condition input. Fig. 2 has no committed instruction (Stage 1b requires one).
- **Free ALU operand.** In Alloy, i2 has one inreg (`Inreg$0`); r0 = `%rcx` is a free operand filled during concretization, as in inst-024552.
- **Branch condition.** It comes from Alloy (`branch_cond.from_alloy: true`): Stage 2 reads pc0's `%r15` and forces it to 1 (`andq $0; orq $1`), so `cmpq $1; jae` is architecturally taken, and the BTB forces a not-taken prediction into pc2.
- **Stage 2 additions:** xmm routes after both loads (`fpr.routes`: pc0 xmm0 `route`; pc2 xmm11 `route_alu`, alu_xmm 5); two splices (`leaq (%r8), %r8` at 337 between i1 and i2; `addq/subq $4097, %r15` at 345–346 between i2 and the transmitter, `xmit_edge: true`); three dead fillers (`fanout_v2.fillers`: an add before pc0, `leaq (%rcx,%r8), %r13` at 305 and `movq %r8,%r14; andq %rcx,%r14` at 308–309 before pc1); the base-pointer reload `movq %rsp, %rsi` (325).

### 7.2 Program excerpt (verbatim, `mispredict_not_taken/asm/inst-023734.s` lines 296–354)

```
296	__litmus_inst_023734_pc0:
297		.globl	__litmus_inst_023734_last_committed
298	__litmus_inst_023734_last_committed:
299		movq	(%rsi,%r8), %r15
300		movq	%r15, %xmm0
301		movq	$0, %r15
302		movq	%xmm0, %r15
303		#NO_APP
304		#APP
305		leaq	(%rcx,%r8), %r13
306		#NO_APP
307		#APP
308		movq	%r8, %r14
309		andq	%rcx, %r14
310		#NO_APP
311		#APP
312		.globl	__litmus_inst_023734_pc1
313	__litmus_inst_023734_pc1:
314		.globl	__litmus_inst_023734_first_noncommitted
315	__litmus_inst_023734_first_noncommitted:
316		movq	%r15, %rax
317		andq	$0, %rax
318		orq	$1, %rax
319		#NO_APP
320		#APP
321		cmpq	$1, %rax
322		jae	.Ltmp0
323		#NO_APP
324	# %bb.1:                                # %bb_2
325		movq	%rsp, %rsi
326		#APP
327		.globl	__litmus_inst_023734_pc2
328	__litmus_inst_023734_pc2:
329		movq	(%rsi,%r15), %r8
330		movq	%r8, %xmm11
331		pxor	%xmm5, %xmm5
332		por	%xmm11, %xmm5
333		movq	$0, %r8
334		movq	%xmm5, %r8
335		#NO_APP
336		#APP
337		leaq	(%r8), %r8
338		#NO_APP
339		#APP
340		.globl	__litmus_inst_023734_pc3
341	__litmus_inst_023734_pc3:
342		leaq	(%r8,%rcx), %r15
343		#NO_APP
344		#APP
345		addq	$4097, %r15                     # imm = 0x1001
346		subq	$4097, %r15                     # imm = 0x1001
347		#NO_APP
348		#APP
349		.globl	__litmus_inst_023734_pc4
350	__litmus_inst_023734_pc4:
351		movq	(%rsi,%r15), %r8
352		#NO_APP
353	.Ltmp0:                                 # Block address taken
354	.LBB0_2:                                # %end_block
```

### 7.3 Annotation excerpt (verbatim, `mispredict_not_taken/ann/inst-023734.ann.json` lines 2–34)

```
  "branch_mode": "mispredict_not_taken",
  "annotations": [
    {
      "branch_pc": 1,
      "btb_forced_target_pc": 2,
      "mode": "mispredict_not_taken",
      "branch_addr": 4201554,
      "branch_addr_hex": "0x401c52",
      "btb_forced_target_addr": 4201559,
      "btb_forced_target_addr_hex": "0x401c57"
    }
  ],
  "xmit": {
    "pc": 4,
    "kind": "ld",
    "atom": "Instruction$2",
    "addr": 4201610,
    "addr_hex": "0x401c8a"
  },
  "commit_boundary": {
    "last_committed": {
      "pc": 0,
      "atom": "Instruction$1",
      "addr": 4201508,
      "addr_hex": "0x401c24"
    },
    "first_noncommitted": {
      "pc": 1,
      "atom": "Instruction$4",
      "addr": 4201554,
      "addr_hex": "0x401c52"
    }
  },
```

Other fields: `func_base_addr_hex` `0x401020`; `reg_naming` random, seed 501522058, locked `Reg_s$0→r8`, `Reg_s$1→r15`; no `jmp_insert` key.

### 7.4 STT result (E3 stt-master): no hit, STT holds the transmitter

E3 covers every one of the 172 Fig. 2 tests in both modes (the `sh100_*` shards complete the 100% run). `inst-023734` is in shard `E3_STT_6_u_core_lpP_fv3_sh100_1__20261110_185333` (cafe3, container `gem5_dev`, `/tests/simspect_alloy_20261108/loosepin_regen/code_eval/results/`). `window-results.json` gives `issued_in_window: false, status: ok` in both modes (`mispredict_not_taken/ld`, `mispredict_taken/ld`), and E4 amulet-STT agrees (`E4_..._sh100_1__20261110_185340`, false in both modes).

The not_taken raw record (`mispredict_not_taken/_sweep_raw/20261110194537_20261110193844_grid0000_batch0005_check_ld.py.json`), excerpted verbatim:

```
"name": "inst-023734", "status": "ok", "xmit_pc": "0x401c8a", "last_committed_pc": "0x401c24", "first_noncommitted_pc": "0x401c52", "xmit_kind": "ld", "issued_in_window": false, "xmit_issue": 0, "xmit_complete": 0, "lc_retire": 2898500, "fnc_retire": 4208000, "fnc_complete": 2950500, "cache_setup": "warm",
"force_plan": [{"branch_pc": 1, "addr": 4201554, "mode": "mispredict_not_taken", ..., "force": "not_taken"}],
"0x401c52": {"575": {"predict_force": 2946500, "predict_force_taken": 0, "predict_force_target": 4201556, "resolve_hold": 2950500, "resolve_hold_stall": 2500, "resolve_hold_fire": 4200500, ..., "resolve_visible": 4201000, ...}},
"criteria": {"lc_retired": true, "signal_seen": false, "after_lc": false, "before_fnc": true, "branches_unresolved": true, "data_obtained": null, "resolved_correct": null, "window_opened": true, "stall_applied": true, "force_applied": true},
"data_obtained": false, "cache_fate": "never_executed", "packet_tick": 0, "xmit_signal": 0, "xmit_execute": 0, "xmit_retire": 0
```

Reading: the window opened and was valid (lc retired at 2,898,500; the branch was forced not-taken, held from 2,950,500 for 2,500 cycles, released at 4,200,500; fnc retired at 4,208,000), and the transmitter never executed (`never_executed`, no packet, no signal). That is consistent with STT working as designed: the transmitter's address depends on a speculatively loaded value, so STT delays it, and the branch resolves and squashes it before it runs. The taken mode is also `never_executed`. The timing point is `sha256("tgrid-v1:inst-023734")` → grid point (unresolved 2500, resolved 500); the test has no resolved branch, so only the 2,500-cycle hold applies, as the record shows.

### 7.5 Unsafe (undefended) result: no run covers it

No E1 Unsafe campaign was run on `STT_6_u_core_lpP_fv3`: the only E1 results are `E1_STT_6_fv2`, `E1_STT_6_fv2fp` and `E1_STT_6_u_fv2` (cafe2 `code_20261109/results/`, cafe3 `firstdet_final/code/results/`), all other corpora. So I cannot say whether `inst-023734` hits on Unsafe. E1 on the fv2 corpora is near saturated (1926/1930 at 1%, EVAL_MANIFEST :82), so a hit is likely but unverified; one single-test run (recipe below) answers it.

### 7.6 PROPOSED listing for `tikz/concretization_example_8pt.tex` (not applied; Anna places it)

Verbatim instruction text from `.s` lines 299, 321, 322, 329, 342, 351 (tabs as single spaces). `...` marks the elided Stage 2 additions: the xmm0 route and fillers after pc0 (300–309), the condition setup (316–318), the base reload (325), the xmm11/xmm5 route and the `leaq (%r8),%r8` splice after i1 (330–337), and the `addq/subq` splice after i2 (345–346). The `#` comments and the `ann:` line are added labels.

```latex
% Concretization example (2026-11-16): excerpt of generated STT test inst-023734
% (STT_6_u_core_lpP_fv3, mispredict_not_taken; cafe2 /tests/simspect_alloy_20261108/testsets_twostage/),
% .s lines 299, 321-322, 329, 342, 351 and .ann.json lines 2-34, verbatim (tabs as spaces). "..." marks elided
% Stage 2 additions (xmm0 route + fillers 300-309, condition setup 316-318, base reload 325, xmm11/xmm5 route
% + lea splice 330-337, add/sub splice 345-346). No xmm4 anywhere; E3 stt-master: no hit (never_executed).
% Provenance: simspect paper_figures/fig2_concretization_example.md section 7
\begin{figure}[t]
\centering\fontsize{8pt}{9.5pt}\selectfont
\begin{verbatim}
movq (%rsi,%r8), %r15   # committed load (pc0)
...
cmpq $1, %rax           # i0 Branch_n, unresolved
jae .Ltmp0
...
movq (%rsi,%r15), %r8   # i1 Load r1 <- m1
...
leaq (%r8,%rcx), %r15   # i2 Other_n r2 <- r1, r0
...
movq (%rsi,%r15), %r8   # i3 Load [r2], xmit
ann: xmit pc4 (load); lc pc0, fnc pc1;
     pc1 mispredicts not taken, to pc2
\end{verbatim}
\vspace{-6pt}
\caption{An excerpt of a generated STT test whose execution graph is Fig.~\ref{fig:ddi-rf}'s plus a committed load: its x86 program, with Stage~2's additions elided (\ldots), and its annotation.}
\label{fig:concretization}
\end{figure}
```

Notes: 12 verbatim lines vs 11 in the current file (one extra `...` for the splice before the transmitter; it can be dropped if the caption's "additions elided" is read loosely, but then the excerpt implies i2 feeds i3 directly). The widest line is 42 characters, narrower than the current listing. The label `fig:ddi-rf` and `fig:concretization` are copied from the current file.

### 7.7 Producing the pipeview trace for the Inspector figure (for the experimentalist; not run)

The v6 figure needs: each instruction's fetch/decode/issue/complete/retire (O3PipeView), the transmitter's cache access or its absence (LSQUnit: "Executing load", the ReadReq packet), the squash and commit ticks (Commit; `gem5_common.run_gem5` always adds it), and the branch hold/release hook lines (`O3PipeView:simspect:` lines, emitted on these hooked builds whenever O3PipeView is on). Those are exactly the campaign's flags (`debug_flags: ["O3PipeView", "LSQUnit"]` + Commit), so a faithful rerun of the campaign gives the trace. Run it through the pipeline rather than by hand, because the gem5 inputs are derived: the binary is the `.s` linked with the harness entry (`gem5_common.build_binary`), and `--branch-ann-file` is a rewritten copy of the annotation with `resolve_stall_cycles` 2500 on pc1 and the force plan applied (`pipeline._inject_stalls`, `gem5_common._branch_ann_for_se`).

Recipe (in the cafe3 `gem5_dev` container, code root `/tests/simspect_alloy_20261108/loosepin_regen/code_eval`; `TMPDIR=/tmp` is required, since gem5 SE copies the `--cmd` path onto the stack and another TMPDIR length changes verdicts, BUGS.md H-STK):

```bash
cd /tests/simspect_alloy_20261108/loosepin_regen/code_eval
TS=/tests/simspect_alloy_20261108/testsets_twostage
M=STT_6_u_core_lpP_fv3__fig_example
mkdir -p $TS/$M/mispredict_not_taken/{asm,ann}
ln -s $TS/STT_6_u_core_lpP_fv3/mispredict_not_taken/asm/inst-023734.s       $TS/$M/mispredict_not_taken/asm/
ln -s $TS/STT_6_u_core_lpP_fv3/mispredict_not_taken/ann/inst-023734.ann.json $TS/$M/mispredict_not_taken/ann/
# E3 config verbatim except: results_name, keep_tmp, one mode, no sample_fraction, 1 job
python3 - <<'PY'
import json
src = "runconfigs/twostage_lp/eval_20261110/E3_STT_6_u_core_lpP_fv3.jsonc"
c = json.loads("\n".join(l for l in open(src).read().splitlines() if not l.lstrip().startswith("//")))
c["paths"]["results_name"] = "FIG_inst-023734_E3"
c["pipeline"]["keep_tmp"] = True
c["speculation"]["branch_modes"] = ["mispredict_not_taken"]
c["gem5"].pop("sample_fraction", None); c["gem5"]["jobs"] = 1
json.dump(c, open("/tmp/FIG_inst-023734_E3.json", "w"), indent=1)
# Unsafe twin: E1's gem5 block (runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc)
c["paths"]["results_name"] = "FIG_inst-023734_E1"
c["gem5"].update({"binary": "/work/gem5-recon-modded/build/X86/gem5.opt",
                  "config_script": "/work/gem5-recon-modded/configs/example/se.py",
                  "cpu_type": "X86O3CPU", "scheme": 0})
json.dump(c, open("/tmp/FIG_inst-023734_E1.json", "w"), indent=1)
PY
TMPDIR=/tmp python3 pipeline.py gem5 --model $M --config /tmp/FIG_inst-023734_E3.json
TMPDIR=/tmp python3 pipeline.py gem5 --model $M --config /tmp/FIG_inst-023734_E1.json
```

Each run's raw record (`<results_dir>/FIG_inst-023734_E{3,1}/mispredict_not_taken/_sweep_raw/*.json`) then carries a `workdir` field (kept because of `keep_tmp`); the trace is `<workdir>/m5out/pipeview.txt` and the exact gem5 command line is in `<workdir>/m5out/config.ini`/`config.json`. The E3 rerun should reproduce `never_executed` (check the verdict against §7.4 before using the trace). Copy the trace out of `/tmp` into the repo (e.g. `STAGE3_gem5/tests/fixtures/`, as the v6 InvisiSpec trace is) before drawing from it.

For reference, the command `gem5_common.run_gem5` assembles for the E3 run is (`<wd>` = the kept workdir):

```
/work/stt-master/build/X86/gem5.opt --outdir=<wd>/m5out --debug-flags=O3PipeView,LSQUnit,Commit --debug-file=pipeview.txt /work/stt-master/configs/example/se.py --cmd=<wd>/inst-023734 --cpu-type=DerivO3CPU --caches --scheme=2 --abs-max-tick=100000000000 --branch-ann-file=<wd>/branch_ann_se.json --branch-ann-base=0x401020
```

The Unsafe one differs only in `/work/gem5-recon-modded/build/X86/gem5.opt`, `/work/gem5-recon-modded/configs/example/se.py`, `--cpu-type=X86O3CPU`, `--scheme=0`. Neither config has `extra_args` or `fnc_commit_stall_cycles` > 0; cache setup is warm (no `cache_setup` key).

### 7.8 DECIDE (Anna)

- [ ] **DECIDE CLEAN-EX:** the paper corpus routes every consumed load through an xmm register (`fpr.loads: consumed`), so no Fig. 2 test is xmm-free. Options: (a) use `inst-023734` (xmm11/xmm5 route, not the UV1 xmm4 shape; E3 no hit in both modes) with the route elided as `...`, which is honest because the caption says Stage 2 additions are elided; (b) take the example from a GPR-only corpus instead (e.g. the E1/E3-covered `STT_6_u_fv2`, which also has Unsafe results), at the cost of the running example not coming from the evaluated corpus; (c) generate a GPR-only twin of `inst-023734` (`runconfigs/twostage_lp/eval_20261110/make_gpr_twin.sh`), which changes the program and needs its own E3/E1 run. Recommendation: (a); then run the §7.7 recipe once to get the Unsafe verdict and the traces.

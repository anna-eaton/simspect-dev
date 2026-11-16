# Alloy models & gem5 builds — reference

*Reference doc: what every Alloy model encodes, and every gem5 build + my intention with it.
Written 2026-10-21 (derived from the `.als` sources + runconfigs). Companion to the
discussion checklist [`../state/MODELS_AND_BUILDS_WALKTHROUGH.md`](../state/MODELS_AND_BUILDS_WALKTHROUGH.md)
(how-far-we've-gotten) — this one is the stable "what each thing is" reference.*

> **All ten defenses as three clauses (execution contract, protection set + update rule, leakage contract + transmission criterion): PART 9 at the end of this doc** (2026-11-15).

> **Ground truth is the `.als` itself.** Do not edit any `.als` without Anna's per-change sign-off
> (repo `CLAUDE.md`). This doc paraphrases; the model files are canonical.

---

## PART 0 — the common skeleton

Every current model (`STT_6` lineage) is the **same symbolic speculation framework** and differs
only in (a) the **defense** it encodes and (b) the **generation driver** (which leaks it enumerates).

- One concrete `sig Instruction { kind: one InstrType, ... }` (ld / str / br / other), topo-ordered by
  `spo` (program order). idx/IX atoms give in-model symmetry-breaking → zero duplicate instances.
- A **transmitter** `xm` is the instruction whose observable operand could leak.
- The research signal = **gem5 lets through a test the model says is *disallowed*** (model is
  conservative; gem5 is ground truth).

The three knobs that define a model's meaning:

| knob | what it is |
|---|---|
| `hardware_protection_policy` | **the protection set** — what the defense protects (STT: a `State` = memory; SPT: `Operand`s; Recon: a *parameterized* policy). |
| `leakage_function` | **the transmitter set** — which operands can leak (loads' `inaddr`, branches' `inreg`, sometimes stores' `inaddr`). |
| `gen_useful_litmus` (the driver) | **the minimality contract** — what counts as a genuine, non-redundant speculative leak worth emitting. |

---

## PART 1 — THE LATEST / PRODUCTION MODELS  ⭐ (what I care about most)

These are the three curated in `latestmodels/` and the primary enumeration targets. Each is
**6 instructions**, ~100,000 XML instances per last container scan (testsets are gitignored).

### ⭐ STT_6 — Speculative Taint Tracking
*File: `STAGE1_alloy/models/STT_6.als`. Symlinks `STT_6_interleave`, `STT_all` → this file.*

- **Defense:** protect at the **state (memory) level** — `hardware_protection_policy: State { Mem_s }`.
  A transmitter leaks only if its operand is provably in the speculative protection set propagated
  from protected memory.
- **Transmitters:** `leakage_function = Loads.inaddr + Branchxs.inreg` (load addresses + branch
  conditions).
- **Driver:** `not secure[no_p]` (it leaks) **+ per-branch resolution-minimality** — for *each*
  unresolved branch, resolving *that one branch alone* must secure the program
  (`all i: unresolved | secure[RR->i]`), plus state-minimality (`RS`) and a commit+resolve boundary
  clause on `first_uncommitted`.
- **Consequence to know:** the per-branch clause means STT_6 **structurally cannot emit a
  two-source merge** (in-degree ≥ 2 to the transmitter) — ~99.6% of its transmitters are
  single-source. That amputation is exactly what `STT_6_multisource` and the OTB probes exist to
  work around. See [`../findings/mdsToRead/OTB_GENERATION_GAP.md`](../findings/mdsToRead/OTB_GENERATION_GAP.md).
- **Intention:** the main STT model — the baseline "does the defense hold?" enumeration run against
  the recon/stt builds.

### ⭐ SPT_6_oneLP — Speculative Privacy Tracking, one-leak-point
*File: `STAGE1_alloy/models/SPT_6_oneLP.als`.*

- **Defense:** protect at **operand granularity** (`hardware_protection_policy: Operand`), with
  explicit **untaint flows** (`nonspeculative_xmit_p`) and STLF (store-to-load-forward)
  de-protection — an input whose rf-source left the protset is de-protected, **including `inaddr`**
  (loads transmit through their address and have no `inreg`, so an inreg-only rule missed
  load-address transmitters).
- **Transmitters:** `Loads.inaddr + Branchxs.inreg + **Stores.inaddr**` — adds **store-address**
  transmitters (a store's cache access leaks like a load's).
- **Driver:** `one_insecure_speculation_scheme_p` — requires **exactly one** insecure leak point
  (not just "≥1"), plus per-branch RR-minimality and the commit+resolve boundary clause.
- **Intention:** the main SPT model, run against `/work/gem5-spt` (fence + untaint variants). The
  store-transmitter additions produced the ~24 untriaged `str` hits that still need a store checker.

### ⭐ Recon_6 — Recon (dynamic / parameterized protection)
*File: `STAGE1_alloy/models/Recon_6.als`.*

- **Defense:** the protection set is **dynamic** — `hardware_protection_policy[p]: State` =
  `Mem_s` **minus** the state reachable *backward through data-dependence from speculative loads*.
  i.e. Recon de-protects memory that a speculative load has already (transitively) consumed.
  Also carries the `rf_from_most_recent_writer` fact (rf must read the most-recent writer).
- **Transmitters:** loads(inaddr) + branches(inreg) (same as STT).
- **Intention:** the Recon defense under test — run against `/work/gem5-recon-modded`. This is where
  the **two real recon bugs** reproduced: OTB / `getOldestTaint` and the STL/SLF bypass
  ([`../findings/bug/recon_SLF_stlf_bypass/`](../findings/bug/recon_SLF_stlf_bypass/)).

---

## PART 2 — VARIANTS OF THE PRODUCTION MODELS

### STT_6 variants (same STT defense, different generation contract)
| model | the *only* meaningful change vs STT_6 | why it exists |
|---|---|---|
| **STT_6_core** | idx/IX ordering removed; length relaxed `exactly 6` → *up to* 6; driver turns on **every** minimality clause (adds RO operand-min + RI instruction-min) → maximally-minimized "leak cores." | Base of the **staged enumeration**: emit minimal cores, then Stage 2 re-seeds each into real STT_6 and lets it grow (`mdsToRead/STAGED_ENUMERATION.md`). |
| **STT_6_stl** | speculation source switched from unresolved branches to unresolved-**address stores** (store-to-load / memory-dependence speculation); all branches resolved; a fact requires a true alias (a load at or before the xmit reads the `Mem_s` an older unresolved store writes). Added 2026-10-28. | Spectre-v4-style store-bypass tests (false-negative alias prediction). Concretize with branch mode `stl_bypass`; gem5 needs the SimSpect-STL hooks (`gem5-hooks/stl/`, not built yet). [`STL_SPECULATION.md`](STL_SPECULATION.md). |
| **STT_6_multisource** | minimality relaxed **per-branch → aggregate** (`secure[RR->unresolved]`): "resolving *all* speculation secures it" instead of "resolving *each branch alone* secures it." | **Admits the OTB / `getOldestTaint` two-source merge** (in-degree ≥ 2) that base STT_6 structurally can't emit. The dedicated OTB-enumeration model. |
| **STT_6_commitsplit** | commit boundary split into C (must be committed) / D (don't care) / U (must be uncommitted, holds every unresolved instruction); the leak must hold at every commit-head position in D, C and U are shrunk to the laxest leaking boundary; every unresolved instruction must alone sustain the leak (non-contiguous branches allowed). Replaces STT_6 clauses (b) and (c). Added 2026-10-29. | Tests whose lc/fnc are only as strict as the leak needs, so the harness enforces them instead of relying on timing. [`COMMIT_BOUNDARY.md`](COMMIT_BOUNDARY.md). |
| **STT_6_pincommit** | adds one fact: `rf_from_most_recent_writer` (rf reads the most-recent writer of a state — "Option A"). | Contract experiment on rf resolution. |
| **STT_6_modified_protset** | protection tracked at **Operand** granularity (not State) + `rf_from_most_recent_writer` + `first_uncommitted` fallback to `first_instr`. | Contract experiment: STT-at-operand-granularity. |

### SPT variants
| model | change | why |
|---|---|---|
| **SPT_6** (= **SPT_6_full**, symlink) | base operand-granularity SPT; `hardware_protection_policy = Instruction.operands`; **no** one-leak-point restriction; no store transmitters. | The full/base SPT model. |
| **SPT_6_oneLP_noSTLF** | `SPT_6_oneLP` **minus** store-to-load-forwarding paths — leakage back to loads+branches only, inreg-only de-protection. | Isolates whether STLF is the leak source (control for the oneLP STLF additions). |

---

## PART 3 — BUG-SYNTHESIS PROBES  (`bugsynth/models/`)

`bugsynth/models/STT_6.als` is **byte-identical** to the production STT_6. The rest are targeted
probes for the OTB/channel gaps (background: [`../findings/mdsToRead/OTB_GENERATION_GAP.md`](../findings/mdsToRead/OTB_GENERATION_GAP.md)):

| probe | what it forces |
|---|---|
| **STT_6_alupath** | *general* "ALU-on-address-path" steering (`some ALU.outreg feeds xmit.inaddr`) + relaxed driver (no per-branch RR) — tests whether the OTB 2-load merge appears **naturally** in that stratum. Not a pinned shape. |
| **STT_6_otb** | `otb_class` predicate: forces an ALU to feed the xmit load address so the capped enumeration spends budget there; the 2nd tainted load is hooked on by `parsexml:pass_interleave` (merge manufactured by interleave, not asserted). |
| **STT_6_otb2** | expresses the **full 2-load → 2-input-ALU → xmit** merge **directly in Alloy** (both ALU inputs rf-fed by distinct loads) — no interleave needed. |
| **STT_6_pendsquash** | the **pending-squash channel** (nmosier two-branch coincidence): explicit tainted-operand dataflow (`tainted_operands_p` / `tainted_states_p`) + tainted vs untainted branch-condition predicates. |

---

## PART 4 — LEGACY / DEVELOPMENT LINEAGE (park / reference only)

- `STT_2`, `STT_3`, `STT_4`, `STT_4_new`, `STT_5`, `STT_5_ld_xmit_only` (loads-only transmitters),
  `LP-only-STT_3` — the STT model development history, superseded by STT_6.
- `STAGE1_alloy/models/old_models/` — 22 archived `.als` (MCMtso, STTcommitted*, model*,
  test_ordering*, …). Archive.

---

## PART 5 — gem5 BUILDS  (`/work/*` in the `gem5_dev` container)

Each build = a different defense **implementation** the same testset is run against; gem5 is ground
truth. Defense/variant selected via `run_config.jsonc` → `SIMSPECT_*` env (see
[`METHODS_INSTRUMENTATION.md`](METHODS_INSTRUMENTATION.md)). `branch_ann_enable: true` (BTB force +
per-branch resolve-stall) works **only on `-modded`/SPT builds** — vanilla rejects `--branch-ann-file`.

| build | repo / git | CPU / config | defense selector | **my intention** |
|---|---|---|---|---|
| **`/work/gem5-recon-modded`** ⭐ | 4.5G, **NO git** (hooks → `gem5-hooks/gem5-recon-modded/`) | X86 `X86O3CPU`, `configs/example/se.py` | `--scheme` **0**=Unsafe **1**=NDA (code enum `Delay`) **2**=STT **3**=DoM; adds `--branch-ann-file` BTB override | **Primary build.** Runs STT_6 / STT_all / Recon_6. Where recon OTB + STL/SLF bugs reproduced. The `-modded` BTB override is what realizes the modeled mispredict (taken mode) + branch-resolve stalls. |
| **`/work/gem5-recon`** | 4.5G, **NO git** — the BASE of `-modded` | X86 `X86O3CPU` | same schemes, **no** branch-ann | Baseline control: the un-modded recon, to confirm a hit isn't an artifact of the BTB hook. |
| **`/work/stt`** | 7.0G, git cwfletcher/stt @e3283b9 (hooks → `gem5-hooks/stt/`) | X86 `X86O3CPU`, `configs/example/se.py` | `--scheme` 0–3 | The **upstream STT** build — cross-check STT_6 results against recon-scheme2. `STT_6_sttbuild` → 0 ld leaks (model holds). |
| **`/work/stt-dbg`** | 7.0G, debug build of `/work/stt` (hooks → `gem5-hooks/stt-dbg/`) | same | same | Debug/trace variant of `/work/stt` for diagnosing specific records (slower, fuller logging). |
| **`/work/gem5-spt`** ⭐ | 7.1G, git FPSG-UIUC/SPT @0d2be0f (hooks → `gem5-hooks/gem5-spt/`) | `DerivO3CPU`, `X86_MESI_Two_Level` | `--scheme=2`→`SpectreSafeFence`; `extra_args` pick variant: `SpectreSafeInvisibleSpec`, `Futuristic*`, `--configImpFlow=Lazy`, `--applyDDIFT`/`--fwdUntaint`/`--bwdUntaint`/`--disableUntaint` | The **SPT** build. Runs SPT_6 / SPT_6_oneLP across fence & invisible-spec & untaint variants. Where the **freeParam=0 untaint-inert** config bug was found. |
| **`/work/amulet/` — four AE builds** | 27G total, **NO git** | each a full separate gem5 tree (not scheme flags of one build) | see sub-table below | AMuLeT **load-defense** campaigns. Confirmed: InvisiSpec UV1, SpecLFB UV6, CleanupSpec unXpec, KV1/UV2. Compound hardware-structure checkers built. Scope vs us: [`docs/AMULET_VS_SIMSPECT_SCOPE.md`](docs/AMULET_VS_SIMSPECT_SCOPE.md). |
| **`/work/amulet-repo`** | 289M, git sith-lab/amulet @c871bdf | the AMuLeT **framework** source | — | Git-backed AMuLeT framework (fuzzer/analysis); the four prebuilt AE gem5 artifacts live in the 27G `/work/amulet`. |

**The four `/work/amulet/amulet-gem5-*_AE-v1.1` builds** (each a distinct gem5 defense implementation):

| defense | build dir | gem5 build / cache | scheme selector | checker |
|---|---|---|---|---|
| **InvisiSpec** | `amulet-gem5-InvisiSpec_AE-v1.1` | `build/X86_MESI_Two_Level` — Ruby MESI (`--ruby`) | `SpectreSafeInvisibleSpec` | `check_ld_invisispec_compound.py` (`bug/kv1_demo/`, `uv2_demo/`) |
| **SpecLFB** | `amulet-gem5-SpecLFB_AE-v1.1` | `build/X86` — **classic cache** | scheme `"2"`→`Speclfb` | `check_ld_speclfb.py` |
| **CleanupSpec** | `amulet-gem5-CleanupSpec_AE-v1.1` | `build/X86_MESI_Two_Level` — Ruby MESI (`--ruby`) | passthrough `--scheme` | `check_ld_cleanupspec.py` (`uv4_demo/`, `unxpec_demo/`) |
| **STT (AMuLeT's)** | `amulet-gem5-STT_AE-v1.1` | `build/X86_MESI_Two_Level` — Ruby MESI | `--scheme` | — (cross-build `l1d_assoc` comparison vs `/work/stt`) |

> ⚠️ The Ruby builds (all but SpecLFB) are **Ruby-only** — passing `caches: true` is fatal (AUDIT #1 / BUG_TAXONOMY D4).
| **`/work/sdo`** | 194M, git cwfletcher/sdo @5d058fd, **clean (no hooks)** | Speculative Data-Oblivious | — | Present but **little/no runs** — scope decision open (whether SDO is in scope for this paper). |

**Durability ⚠️:** `gem5-recon`, `gem5-recon-modded`, `amulet` are **not git-tracked**. Their hooks
are backed up under `gem5-hooks/`, but the full trees are undiffable — see
[`../state/SYNC_DIVERGENCE.md`](../state/SYNC_DIVERGENCE.md).

---

## PART 6 — which models have run against which builds (as last logged)

Recon_6 → recon-modded · STT_6 & STT_6_interleave → recon-scheme2 + sttbuild · SPT_6_oneLP →
gem5-spt fence/untaint · AMuLeT campaigns (STT_6_invisispec/_compound/_speclfb,
STT_6_cleanupspec_residue, STT_all_amulet/_recon). Verify live before trusting — see
[`../state/RUNNING.md`](../state/RUNNING.md).

---

## PART 7 — Defense-model fit per build: does each build get the right model and load criterion? (2026-11-03, defense-fit session)

*Anna's question (2026-11-03): "for each gem5, investigate if the STT load ones need to be different than the AMuLeT load ones." Investigation only: no code, config, spec or model was changed. Sources read this session: `specs/defense_units.json`, `specs/gem5_builds.json`, `specs/leakage/{stt,recon,spt,invisispec,speclfb,cleanupspec}.json`, `specs/transmitter_criteria.json`, the defense blocks of `STT_6.als:320-332`, `Recon_6.als:311-324`, `SPT_6_oneLP.als:333-361`, `STT_6_stl.als:280-370`, `STAGE3_gem5/check_ld.py:28-150`, `check_ld_speclfb.py:1-145`, `check_footprint.py:185-235,473-482`, the run configs in `runconfigs/` and `results/*_full*/`, `gem5-hooks/stt/stt.patch:120-145`, and the papers in `~/Documents/quail/sources/papers/` via `pdftotext` (PDF pages unless noted; SpecLFB = printed pages; the ReCon copy is a 3-page web capture, so it is cited by section). Builds live on cafe2, which was not accessed; build-side claims cite earlier sessions' code reads.*

**Short answer.** Yes, they must differ, and mostly they already do. There are two kinds of load criterion, because the defenses hide different things. (1) **Delay defenses** (STT-Spectre, Recon-STT, ReCon, SPT-Fence) promise that a *tainted transmitter does not execute*: "STT considers the execution of a transmit instruction as an explicit covert channel that leaks its argument" (STT §6.1 p5), and STT deliberately lets untainted speculative loads (the access load) execute and change the cache (STT §1 p2: "executing and selectively forwarding the results of speculative access instructions"). Their criterion must be keyed on the model's transmitter and count *any* execution that obtains data, cache hits included: that is `check_ld`. (2) **Hide/undo defenses** (InvisiSpec, SpecLFB, CleanupSpec) promise that *no unsafe speculative load leaves a visible footprint*, whatever its address depends on, while the load may obtain data (into the SB, the LFB, or an install that is later cleaned). Their criterion is a footprint of any unsafe speculative load in the protected structures: that is `check_footprint` + `specs/leakage/<defense>.json`. Swapping them is wrong both ways: a footprint criterion on STT flags the access load's legal footprint, and an "obtained data / reached the cache" criterion on SpecLFB counts speculative hits, which SpecLFB puts out of scope ("Leakage through speculative loads under cache hits is out of the current defense scope of SpecLFB", §9 p643).

**The protection set differs too, and AMuLeT itself says so.** AMuLeT tests "the CT-SEQ contract for testing InvisiSpec [37] (Futuristic), CleanupSpec [29], and SpecLFB [8], and the ARCH-SEQ contract for testing STT [41] (Futuristic)" (AMuLeT §3.1 p5). ARCH-SEQ also exposes "the values of all data loaded from memory on architectural program paths" (§2.1 p3), i.e. STT protects only speculatively accessed data, matching STT's own scope (non-transient access attacks are "out of scope", STT §3 Fig. 3 p3) and SPT's description ("STT does not protect non-speculatively-accessed data", SPT §2.2 p2). CT-SEQ treats every value as secret unless an architectural load/store address or the PC exposes it, and CleanupSpec says it directly: "The secret may be accessed from the memory or from a register, or computed, transiently" (§2.1 p3). `STT_6`'s protection set (`Mem_s`, untainted when a load has no older unresolved branch, `STT_6.als:326-332`) is the ARCH-SEQ one, so it is right for STT and narrower than what the three AMuLeT defenses protect.

**But for the three AMuLeT builds the model does not decide the verdict.** `check_footprint.check_footprint` never reads `xmit_pc` (`check_footprint.py:473-482`); its actor is any squashed instruction younger than lc (`squashed_after_lc`, `:216-221`). So for these builds `STT_6` is only a *stimulus generator*: its protection set and leakage function choose which programs run, never which run is a hit. Every `STT_6` test contains at least one speculative load whose own address is not tainted (the access load), which is exactly the single-load, register-address shape of AMuLeT's UV6 gadget (AMuLeT p3: "leaking secret registers with a single speculative load"). So the narrower STT protection set costs little stimulus for footprint checks. The speculation contract costs more: `STT_6` only realizes control-flow squashes, while InvisiSpec-Futuristic (AMuLeT's setting, p8), CleanupSpec ("We deem all transient instructions potentially 'unsafe' until they retire", §2.1 p3) and SpecLFB (memory-order MUSLs, §5 p637-638; the gem5 build sets `setmUSL` for unresolved older stores, `lsq_unit.cc:893` per `PROTECTION_SCOPE_TABLE.md`) also protect loads behind other squash sources, which no `STT_6` test exercises. The leakage function also includes branches (`Branchxs.inreg`), which none of the three defenses protect (InvisiSpec: "we limit ourselves to load instructions", §IV p4), so `br_x` tests can only produce incidental load footprints (APPROVALS F-1 already proposes loads-only footprint runs).

**Where the mismatch already changed a result: the SpecLFB UV6 numbers.** The paper's "68/300" and "first detection at test #6" (`results.tex:83,155-156,170`; source `wiki/results/PAPER_RESULTS.md` §4, claudelog 2026-06-03 "results") were scored by the older, STT-shaped `check_ld_speclfb` signal (the transmitter's in-window "Doing memory access"). Every one of the 68 transmitters read the pre-warmed line `0x3580` and the dcache reported a hit (`PAPER_RESULTS.md:302-304`). Later the same day the checker was re-keyed on the L1 install (claudelog 2026-06-03 "CHECKER CHANGE", `check_ld_speclfb.py:20-34`), and on the four hits it re-checked, every one flipped to `access_hit_in_window_no_install` (not a leak). The current criterion (`specs/leakage/speclfb.json`: fill/evict in L1D/L2) would not count hits either. On SpecLFB's own terms, a speculative hit is out of scope, so the 68/300 measure the mechanism (`isUnsafe=0` on a conditional USL), not a leak. The install-keyed result that does count is 11/12 on a 12-test demo with a 1kB L1D (claudelog 2026-06-08). Separately, those transmitters are the *second* speculative load; the 2026-10-28 code read (`wiki/findings/audits/2026-10-28/hooks_speclfb_and_uv6.md`) attributes second-load exemptions to a head-skip artifact (`lsq_unit.cc:817`, sticky `PrevNoUnsafe` `rob.cc:464`), not to the published first-load rule. The published UV6 leaks via the first speculative load, which `STT_6` never marks as the transmitter.

### Fit table

| gem5 build | defense | Alloy model used | load criterion used | speculation contract matches paper? | protection set matches? | leakage function matches? | proposed change | confidence |
|---|---|---|---|---|---|---|---|---|
| `/work/stt`, `/work/stt-dbg` | STT-Spectre | `STT_6` (also `STT_6_commitsplit`) | `stt.json` = `check_ld` (transmitter-keyed; data obtained = packet or store-forward) | **yes**: STT §6.1 p5 Spectre visibility point; `--scheme=2` sets `threatModel='Spectre'`, `implicitChannel` on (`gem5-hooks/stt/stt.patch:133-137`) | **yes**: `Mem_s` + untaint at the visibility point = "STT taints the output of any speculative access instruction … untaints the output of an access instruction once it becomes safe" (§6.1 p5) | **mostly**: loads + explicit branches; the store-to-load-forwarding implicit branch (§6.4.2 p8) is missing (APPROVALS STT-1) | keep `check_ld`; never move STT to a footprint criterion. Open refinements: window the data-obtained fate (existing DECIDE); check whether `spec_read_only` can occur here (D4) | high |
| `gem5-recon-modded` `--scheme=2` | Recon-STT | `STT_6`, `STT_6_interleave` | `stt.json` = `check_ld` | **subset**: the build casts shadows from branches and stores (ReCon §3.1: "we use only speculation cast by control flow and store instructions"; `decode.cc:686-695`, `STT_VS_RECON_STT.md`). Sound, misses store shadows | yes (STT's) | as STT; this build's tainted-branch handling was never read | `STT_6_shadows` (existing DECIDE, URGENT_TODO) ; packet-line fix in `parse_lsq` (existing DECIDE, `recon_cache_reach_gate`) | high |
| `gem5-recon-modded` (ReCon) | ReCon | `Recon_6` | `recon.json` = `check_ld` | subset, as above (APPROVALS R-5) | STT's set minus a reveal that is a no-op (APPROVALS R-1); paper: "values that reside in registers before the point of speculation are not considered to be potential secrets" (§3.1), same as STT | as STT | existing R-1/R-2; no local run config, so how ReCon mode is enabled was not verified | medium |
| `gem5-recon-stl` | Recon-STT, store half | `STT_6_stl` | `stt.json`/`check_ld` (STL window checker not written) | matches the store-shadow half | yes | yes | none new | medium |
| `gem5-spt` (SpectreSafeFence / SpectreSafeInvisibleSpec) | SPT | `SPT_6_oneLP` | `spt.json` = `check_ld`; `str` falls back to `check_ld` | Spectre variants yes; the `FuturisticSafe*` configs would be a subset | direction right (SPT protects non-speculative secrets, §3 p3-4) but the seed is over-broad (A1, `PROTECTION_SET_REEVAL.md`) | loads + branches + store addresses: paper-supported (SPT §2.1 p2: memory, control-flow and variable-time instructions transmit) | existing A1 / SPT-1..3 and the store checker; `spec_read_only` = not a leak is right for the InvisibleSpec variant | high |
| `amulet-InvisiSpec` | InvisiSpec | `STT_6` | reported numbers: `check_ld_invisispec_compound`; current: `invisispec.json` via `check_footprint` (any squashed instruction after lc; `*_full_*` configs never run) | Spectre mode **yes** (§IV-A1 p4 = STT's Spectre VP); Futuristic mode (AMuLeT's, p8) **no**: control-only stimulus | **no**: hides every USL (§V-A p4); CT-SEQ (AMuLeT §3.1 p5). Verdict does not use it | **no**: includes branches; InvisiSpec covers loads only (§IV p4) | loads-only runs (F-1); Futuristic stimulus (D1); attribution field (D2) | high (mismatch), medium (impact) |
| `amulet-SpecLFB` | SpecLFB | `STT_6` | reported 68/300: older access-keyed `check_ld_speclfb` (counted hits); current: install-keyed `check_ld_speclfb` and `speclfb.json` via `check_footprint` (full config never run) | control-flow part **yes** (p638); memory-order MUSLs (§5 p637, built via `setmUSL`) **not generated** | **no**: every MUSL, no taint (§4-5 p635); CT-SEQ | loads (misses) only; branches unprotected | re-score UV6 under the install/fill criterion (D3); `STT_6_stl`/shadows stimulus (D1) | high |
| `amulet-CleanupSpec` | CleanupSpec | `STT_6` | reported: `check_ld_cleanupspec` (gates on squash timing); current: `cleanupspec.json` per-line balance (full config never run) | **no**: "all transient instructions … 'unsafe' until they retire" (§2.1 p3), any squash source | **no**: register and computed secrets included (§2.1 p3) | loads only ("prevent any transient load from leaking", §2.1 p3) | Futuristic/shadow stimulus (D1) | high |
| `amulet-STT` | STT (AMuLeT) | `STT_6` (`STT_all_amulet`, 100% errors, `AUDIT.md` #1) | `stt.json` | **unknown**: AMuLeT ran it Futuristic (p8; `gem5-hooks/amulet-repo/gen_stt_tests.py:43` `STT_FuturisticSpec`); which threat model its `se.py` picks for `--scheme=2` was never read | STT's if STT | as STT | TODO: read its `se.py` before any campaign; if Futuristic, judge against `STT_6_futuristic` | low |

### Proposed defense-block clauses (proposals only; no `.als` touched; none run through Alloy)

**P1, branch + store shadows** (Recon-STT, SpecLFB's control + memory-order MUSLs). Built from `STT_6`'s and `STT_6_stl`'s own clauses (`STT_6.als:245-256,327-332`, `STT_6_stl.als:283-287,365-370`); same as the pending `STT_6_shadows` idea:

```
fun has_unresolved_brs_strs_p[p: PTag->univ] : Instruction {
	((unresolved_p[p] & (Branchxs+Branchns+Stores)).(^(spo_p[p])))   // after an unresolved branch or an unresolved-address store
}
fun speculation_contract_p[p: PTag->univ] : Instruction {uncommitted_p[p] & has_unresolved_brs_strs_p[p]}
fun prot_set_propagation_p[p:PTag->univ,i:Instruction,s:State] : State {
	s - (Loads & (i_p[p] - has_unresolved_brs_strs_p[p]) & i).inmem.opstate
}
// hardware_protection_policy, leakage_function unchanged from STT_6
```

**P2, CT-SEQ footprint model** (InvisiSpec, SpecLFB, CleanupSpec), only worth it if D2 makes the footprint verdict transmitter-keyed. Seed in `Recon_6`'s parameterized form (`Recon_6.als:316-318`), generalized from "flows into a non-speculative load address" to every CT-SEQ observation (AMuLeT Table 1: PC and load/store addresses on the architectural path):

```
fun speculation_contract_p[p: PTag->univ] : Instruction {uncommitted_p[p] & has_unresolved_brs_p[p]}   // Spectre USL; Futuristic: has_unresolved_any_p (STT_6_futuristic)
fun exposed_ops_p[p: PTag->univ] : Operand {
	((Loads + Stores) - speculation_contract_p[p]).inaddr + ((Branchxs + Branchns) - speculation_contract_p[p]).inreg
}
fun hardware_protection_policy[p: PTag->univ] : State {Mem_s - (~opstate).(*(op_edges_p[p]).(exposed_ops_p[p]))}   // secret unless it reaches an architectural observation
fun leakage_function : Operand {Loads.inaddr}   // loads only (InvisiSpec §IV p4; CleanupSpec §2.1 p3)
fun prot_set_propagation_p[p:PTag->univ,i:Instruction,s:State] : State { s }   // no visibility-point untaint
```

Caveats: the backward closure declassifies a whole source when any function of it is exposed (over-declassifies, so it under-generates rather than producing invalid tests); the `[p]` seed needs the `a[p,f[p],hardware_protection_policy[p]]` call form `Recon_6` uses; minimality (`all s: State | secure[RS->s]`) at exactly 6 instructions was not checked for SAT.

### Decisions for Anna

- [ ] DECIDE (defense-fit D1, model for the AMuLeT builds): (a) keep `STT_6` as their stimulus and say in the paper that it is a sound but incomplete generator whose protection set does not enter the footprint verdict; (b) add speculation-contract variants on the same skeleton so the stimulus covers the squash sources these defenses claim: P1 (branch + store shadows) for SpecLFB and Recon-STT, `STT_6_futuristic` for InvisiSpec-Futuristic and CleanupSpec; (c) also change the protection set to CT-SEQ (P2). Recommendation: (a) for this paper, (b) next; (c) only if D2 picks a transmitter-keyed verdict, since otherwise it changes no verdict.
- [ ] DECIDE (defense-fit D2, extends the existing InvisiSpec actor DECIDE to all three footprint defenses): who must leave the footprint? (a) any squashed load younger than lc (today; matches each paper's claim); (b) only the model's transmitter, with `STT_6` (would miss published UV6, whose leaking load is not `STT_6`'s transmitter); (c) only the transmitter, with P2; (d) keep (a) as the verdict and record per hit whether the footprint's seq is the model's transmitter. Recommendation: (d).
- [ ] DECIDE (defense-fit D3, SpecLFB UV6 numbers in the paper): the 68/300, test #6 and 23% figures counted speculative cache hits, which SpecLFB scopes out and which the current install/fill criteria do not count. (a) Re-run `results/STT_6_speclfb_full` under `speclfb.json` (likely needs the B-1 cold-line stimulus to get any misses); (b) report the install-keyed 12-test demo (11/12) instead; (c) keep 68/300 but call it a mechanism signal (`isUnsafe=0` on a conditional USL, in-window hit), not a leak. Recommendation: (a) if there is time, else (c); in all cases say the transmitter is the second speculative load.
- [ ] DECIDE (defense-fit D4, delay-defense load criterion): keep `check_ld` (transmitter-keyed, any data-obtaining execution) for STT-Spectre, Recon-STT, ReCon and SPT (recommended), and decide whether `spec_read_only` should stay "not a leak" on delay builds. It is right only where the defense makes loads invisible (InvisiSpec, SPT-InvisibleSpec); on STT/Recon/SPT-Fence a spec read by a tainted transmitter would still be an execution. Recommendation: first grep existing `/work/stt`, `gem5-recon-modded` and SPT-Fence traces for `send a spec read` (read-only); if none occur, record that in `stt.json` and change nothing.

## PART 8 — Targeted models for the three load defenses (2026-11-09, proposal only; no `.als` created or edited)

*Anna's question (2026-11-09): is the STT testset really applicable to the three AMuLeT load defenses (InvisiSpec, CleanupSpec, SpecLFB)? Her proposal: a testset built from (1) each defense's speculation primitives, (2) loads as the transmitters, (3) all memory protected. This part answers the question and specs the models. It builds on PART 7 and on `wiki/findings/mdsToRead/FOOTPRINT_DEFENSES_PAPER_AUDIT.md` §5-6. Read this session: `STT_6.als`, `STT_6_stl.als`, `STT_6_futuristic.als`, `proposed/STT_6_shadows.als`, `proposed/STT_6_rmwjmp.als` (defense blocks and helpers), the SpecLFB source in `~/trippel/defense_src/amulet-SpecLFB_AE-v1.1/src/cpu/o3/`, and the three papers in `~/Documents/quail/sources/papers/` (PDF pages). The probes below ran on scratch copies; nothing under `STAGE1_alloy/models/` was touched.*

**Answer.** The STT_6 testset is valid for these three builds but not targeted at them. The proposal makes sense, and it fits in the defense block: clause (2) becomes "all memory, never untainted", clause (3) becomes "load addresses only", and clause (1) is set per defense.

### Why STT_6 is valid but not targeted

- **Valid:** every STT_6 load-transmitter test contains a squashed speculative load, which is unsafe under all three papers' definitions, so no test is invalid (`FOOTPRINT_DEFENSES_PAPER_AUDIT.md` §5). On these builds it has found UV1, UV4, UV5 (one test), UV6, the walk order and the jmp shadow (`AMULET_BUGS_DETECTION_ACCOUNTING.md` §2).
- **The verdict does not use the model.** `check_footprint` flags a footprint of any squashed instruction younger than the last committed one and never reads the transmitter (PART 7). In the SpecLFB hooks-v2 campaign the model's transmitter is among the offending loads in 911 of 1,300 and 937 of 1,452 hits; the other hits come only from other loads.
- **Protection set too narrow.** STT protects only speculatively accessed data, so every STT_6 test is an access-to-transmit chain with at least two speculative loads. The single speculative load whose address was read before the branch (the shape of AMuLeT's UV1 and UV6 examples) cannot be generated. All three papers protect it: InvisiSpec hides every unsafe speculative load (p4), CleanupSpec says "The secret may be accessed from the memory or from a register, or computed, transiently" (p3).
- **Speculation contract too narrow.** STT_6 has branch shadows only. SpecLFB also marks loads behind an older store with an unresolved address (paper "MUSLs in an Unresolved Memory Access Order", PDF p7; build `lsq_unit.cc:942-952` `setmUSL`, fed by `rob.cc:574-578`, `preStoreResolved = false` when `!inst->effAddrValid()`). CleanupSpec deems "all transient instructions potentially 'unsafe' until they retire" (p3). InvisiSpec-Futuristic covers "loads that can be squashed by an earlier instruction" (p4).
- **Leakage function too wide.** STT_6 also makes branches transmitters. None of the three protects them (InvisiSpec p4: "we limit ourselves to load instructions"), so the branch-transmitter half of the corpus can only produce incidental load footprints on these builds.
- **The bugs that needed extra work came from outside the model.** UV3 needed the read-modify-write fanout and a cold cache, UV4 needs a split access, UV5 an older committed access to the same line. Those are Stage 2 and Stage 3 levers (fanout, cache setup), not taint-chain shapes, and a targeted model does not replace them.

### What the proposal becomes in the defense block

Diff against `STT_6.als` (two lines; the same two lines apply to `STT_6_stl.als`):

```
-fun leakage_function : Operand {Loads.inaddr+(Branchxs).inreg}
+fun leakage_function : Operand {Loads.inaddr}
 fun prot_set_propagation_p[p:PTag->univ,i:Instruction,s:State] : State {
-	s - (Loads & no_unresolved_brs_bf_or_is_p[p] & i).inmem.opstate
+	s // all memory stays protected: no visibility-point untaint
 }
```

`hardware_protection_policy` stays `Mem_s`. With the untaint gone, memory is protected whether it was read before or after the speculation source. A test then exists when a speculative load's address derives, through `rf`/`ddi`, from any memory value. That keeps every STT_6 load-transmitter shape and adds the ones where the source load is committed.

| defense (eval row) | clause 1, speculation contract | base skeleton | clause 2, protection | clause 3, leakage | runnable today |
|---|---|---|---|---|---|
| InvisiSpec Spectre (E12b) | after an unresolved branch: `uncommitted_p[p] & has_unresolved_brs_p[p]`, unchanged from STT_6 (InvisiSpec p4) | `STT_6` | `Mem_s`, propagation = identity | `Loads.inaddr` | yes |
| InvisiSpec Futuristic (E12a, AMuLeT's mode) | any squash source (p4). Realizable today: branch misprediction, and a store bypass with a true alias | `STT_6` and `STT_6_stl` | same | same | branch part yes; store part needs store-bypass hooks on the build |
| SpecLFB (E14) | unresolved branch (CUSL) or older store with unresolved address (mUSL) | `STT_6` and `STT_6_stl` | same | `Loads.inaddr`. "Misses only" is a cache-setup matter (cold line), not a model clause | branch part yes; store part needs hooks |
| CleanupSpec (E13) | every transient instruction until retire (p3). Realizable today: branch, store bypass | `STT_6` and `STT_6_stl` | same | `Loads.inaddr`; RMW transmitters stay a Stage 2 fanout (UV3), or `(Loads+Rmws).inaddr` on the `STT_6_rmwjmp` vocabulary | branch part yes; store part needs hooks |

- **So two shared models cover all three defenses:** a branch-shadow footprint model (STT_6 skeleton) and a store-shadow footprint model (STT_6_stl skeleton, which carries the true-alias fact). The defenses differ in which of the two apply and in Stage 2 and 3 options, not in clauses (2) and (3).
- **Why the store part uses the STT_6_stl skeleton and not a union contract:** the footprint verdict needs the load to be squashed. A load behind an unresolved store is squashed only when it truly aliases, which is the fact `stl_alias_pair` in `STT_6_stl.als`. A plain union of branch and store shadows (`proposed/STT_6_shadows.als`) would also generate bypass loads that are never squashed.
- **Store-bypass tests cannot run on the three AMuLeT builds yet:** they have no store-bypass hooks (`wiki/design/STL_SPECULATION.md` "Which defenses have STL in their threat model", units 4, 6, 7).

### Probes (scratch copies, `a6CountOnly`, Mac, 2026-11-09 19:31-19:38)

| scratch model | change | result |
|---|---|---|
| branch footprint model | STT_6 + the two-line diff | 3,000 instances (the cap) in 32 s |
| same, single-load query | adds `xm in Loads` and `one (Loads & speculation_contract_p[no_p])` to `gen_lit` | 3,000 (cap) in 32 s |
| STT_6, same single-load query | STT_6 unchanged + the query | no instance in 420 s (timeout, so not a proof; by the argument above there is none) |
| STT_6, load transmitters only | adds `xm in Loads` | 3,000 (cap) in 47 s |
| store footprint model | STT_6_stl + the two-line diff | 3,000 (cap) in 34 s |
| STT_6_stl, load transmitters only | adds `xm in Loads` | 3,000 (cap) in 36 s |

First 12 single-load instances, in program order (plain = committed, `~` = uncommitted and resolved, `?` = unresolved, `*` = transmitter): `Load Branchn? Load~* Branchn~ Branchn~ Branchn~`, `Branchn Load Branchn? Load~* Branchn~ Branchn~`, `Load Load Branchn? Load~* Branchn~ Branchn~`, `Othern Load Branchn? Load~* Branchn~ Branchn~`, `Load Load Load Load Branchn? Load~*`. The core is three instructions (committed load, unresolved branch, speculative load) and the rest is padding to reach six. Total instance counts and distinct-core counts were not measured.

### Notes and limits

- **"All memory" vs "all state".** Keeping `Mem_s` means every test's speculative load has an address that depends on a memory value, so each hit is a secret-dependent leak under CT-SEQ, and a register-held secret is covered as "loaded before the branch". Adding `Reg_s` would make any speculative load a violation by itself; the state-minimality rule (`all s: State | secure…[RS->s]`) would then strip everything except the one load, leaving almost no shapes. This reasoning was not run through Alloy.
- **The model remains a stimulus generator** unless decision D2 in PART 7 changes the verdict. What the targeted models buy is the single-load and store-bypass shapes, no wasted branch-transmitter tests, and a paper statement that each defense was tested against its own contract.
- **Size.** At exactly six instructions the new shapes are a three-instruction core plus padding, so many instances share a core. The two-phase tooling (`wiki/design/TWO_PHASE_MODELS.md`) can count distinct cores before a size is chosen.
- **Futuristic sources other than branches and stores** (faults, load-load order) have no concretization; Futuristic is parked (`wiki/design/FUTURISTIC_MODEL.md`).
- **The jmp shadow** needs a direct jump between the branch and the load. That is a vocabulary option (`proposed/STT_6_rmwjmp.als`, generated jumps), separate from these clauses.

### Decisions for Anna

- [ ] DECIDE (footprint models FP-1, protection set): (a) `Mem_s` with no untaint, as specced (recommended); (b) all state, `Mem_s + Reg_s`, which matches CT-SEQ literally but collapses the shapes to one load.
- [ ] DECIDE (FP-2, how many models): (a) two shared drafts, branch and store, used for all three defenses (recommended); (b) one named copy per defense so the paper can cite a model per defense, identical in clauses (2) and (3).
- [ ] DECIDE (FP-3, use): (a) run the branch footprint model alongside STT_6 on E12-E14 at the same sample size and compare hit classes before replacing anything (recommended); (b) replace STT_6 on these three rows; (c) keep STT_6 and only state the limitation in the paper (D1 option (a)).
- [ ] DECIDE (FP-4, store bypass): port the store-bypass hooks to the three AMuLeT builds so the store footprint model can run (a hooks change), or leave store shadows out of scope for these defenses in this paper. No recommendation; it depends on the time left.
- [ ] DECIDE (FP-5, transmitters for CleanupSpec): keep RMW as the Stage 2 fanout (recommended, already decided for the shared corpus on 2026-11-09), or put `Rmws` in the leakage function on the `STT_6_rmwjmp` vocabulary.

### 2026-11-10 — Paper check of the footprint models (footprint-check)

*Anna's doubt (2026-11-10): "they should have their specific speculation contracts and it should be reg and memory both right??" This section checks the six files `STAGE1_alloy/models/{InvisiSpec,CleanupSpec,SpecLFB}_6.als` and their `_stl` variants against the papers. Sources read this session: the papers in `~/Documents/quail/sources/papers/` via `pdftotext` (PDF page numbers; SpecLFB's printed page = PDF page + 629): `yan-2018-invisispec` pp3-5, `saileshwar-2019-cleanupspec` pp3, 7-8, `cheng-2024-speclfb` pp5-9, 13-14, `fu-2025-amulet` pp3, 12-13. Code read: the InvisiSpec visibility point in `~/trippel/defense_src/amulet-InvisiSpec_AE-v1.1/src/cpu/o3/{lsq_unit_impl.hh:255-283,1065-1130, rob_impl.hh:417-490}`, and the register/memory init in `STAGE2_compilation/parsexml.py:1106-1122,2105-2108`. The existing `.als` files were not edited.*

**Answer.** One of the three defense clauses has to change, and only in the three branch models: the protection set should cover registers as well as memory. Anna is right about registers. Protecting all of `Reg_s` breaks the model, though (shown below), so the draft protects memory plus every register the test never writes, i.e. the initial register values. The speculation contracts are each defense's own, within what the harness can squash, and they are right as they are. The leakage clause (load addresses only) and "never untainted" are right for all three. The `_stl` variants need no change.

#### Per defense

| defense | clause | current | what the paper says | verdict |
|---|---|---|---|---|
| InvisiSpec | contract | branch (`InvisiSpec_6`); unresolved-address store with a true alias (`InvisiSpec_6_stl`) | p4: "In the Spectre attack model, USLs are the speculative loads that follow an unresolved control-flow instruction." "In our Futuristic attack model, USLs are all the speculative loads that can be squashed by an earlier instruction" (Table I, p3: exceptions, control-flow misprediction, store-load alias, load-load alias, consistency violations, interrupts). The build's Futuristic visibility point: every older instruction `readyToCommit && isLoadSafeToCommit` with no fault (`rob_impl.hh:476-487`, used at `lsq_unit_impl.hh:1110`) | correct (see "Two InvisiSpec models?") |
| InvisiSpec | protection | `Mem_s`, never untainted | p3: transient access instructions "can write secrets into general purpose registers or the store queue". p4: a USL stays invisible until its Visibility Point whatever its address depends on. AMuLeT tests InvisiSpec against CT-SEQ (p5), where every register and memory value is secret | under-generates: register secrets are missing |
| InvisiSpec | leakage | `Loads.inaddr` | p4: "Since we focus on cache-based covert and side channel attacks, we limit ourselves to load instructions." p3 §III-B: the whole data cache hierarchy, including coherence state and the data TLB; fn. 2: instruction cache and instruction TLB not described | correct (an address-keyed load transmitter covers the D-TLB too) |
| InvisiSpec | untaint | none | No data is ever declassified. A load stops being a USL at its Visibility Point (p4-5), which is a contract event that the model expresses with resolution flags | correct |
| CleanupSpec | contract | branch / store with alias | p3 §2.1: "We deem all transient instructions potentially 'unsafe' until they retire". It is an undo on squash: "a threat model where any mis-speculated load could leak information" (p3) | correct: the undo triggers on any squash, and the harness squashes only on a branch or a store alias |
| CleanupSpec | protection | `Mem_s` | p3 §2.1: "The secret may be accessed from the memory or from a register, or computed, transiently." p3 §2.2: "Future attacks could use this recipe to leak secrets stored in registers, or results of malicious computations performed transiently", and STT-like defenses "fail against attacks without such patterns (e.g. leaking secrets from registers or computations)" | under-generates: the paper names registers explicitly |
| CleanupSpec | leakage | `Loads.inaddr` | p3 §2.1: "We only consider attacks exploiting the data-cache hierarchy"; instruction caches and TLB excluded. p8 §4: "the transient change is initiated with a speculative read"; "RFOs are issued non-speculatively". p7: a transient `clflush` is delayed (not in our vocabulary) | correct. RMW stays a Stage 2 fanout (FP-5) |
| CleanupSpec | untaint | none | Correct-path loads simply keep their changes. Nothing is released per value | correct |
| SpecLFB | contract | branch / store with alias | p7-8 §5 lists four MUSL sources: unresolved control flow, unresolved memory access order (memory dependence and consistency), value prediction, other exceptions. p8: "we have no practical implementation of SpecLFB which considers VP". The build uses only `isCUSL() \|\| isMUSL()` (AMuLeT Fig. 8c, p13) | correct for the build |
| SpecLFB | protection | `Mem_s` | §5-6: every MUSL is delayed whatever its address depends on. AMuLeT p12: CT-SEQ is "the most intuitive contract based on the security guarantees described in the SpecLFB paper", and its UV6 tests have "the secret ... in a register" (Fig. 8b: `MOV RAX, ptr [R14 + RBX]`, both initial registers) | under-generates: register secrets are missing |
| SpecLFB | leakage | `Loads.inaddr` | p6 §4: TLB and port contention out of scope. p14 §9: "Leakage through speculative loads under cache hits is out of the current defense scope" | correct. "Misses only" comes from the cache setup at Stage 3, not from this clause |
| SpecLFB | untaint | none | p9 §6.2.2: a MUSL's bit clears when its older branches resolve, or when no older store aliases it. These are contract events, not data release | correct |

#### Speculation contract: why not "uncommitted" or branch + store in one model

- **Every source the harness can squash is already covered.** The single-core, fault-free gem5 runs squash only on a branch misprediction or a store-load memory-order violation. A test whose window comes from an older incomplete load or ALU op (InvisiSpec-Futuristic's literal visibility point, or an `STT_6_futuristic`-style `has_unresolved_any_p` contract) commits every load, so it leaves no transient-only footprint and cannot violate CT-SEQ. Generating such tests would be waste. Exceptions, load-load consistency squashes and value prediction have no concretization; SpecLFB's build and gem5 have no value prediction either.
- **Branch and store in one model adds nothing.** Resolution-minimality (`all i: unresolved - first_uncommitted | secure…[RR->i]`) forces every unresolved instruction to be necessary. `STT_6` therefore never has an unresolved store and `STT_6_stl` has no unresolved branch (fact `stl_no_unresolved_branches`). With no untaint, a test with both sources only survives if both are needed, and the transmitter (younger than the store) is already covered by the store alone. So a union model would be, in effect, the disjoint union of the two files.

#### Two InvisiSpec models (Spectre vs Futuristic)?

**No new model, but a different set of models per mode.** A load after an unresolved branch is a USL in both modes, so the branch model (`InvisiSpec_6` or the v2 draft) is valid for E12b (Spectre) and E12a (Futuristic) alike. Under Futuristic, a load behind an unresolved-address store is also a USL (the store is not `readyToCommit`, `rob_impl.hh:484`), so E12a also takes `InvisiSpec_6_stl`. Under Spectre, the `_stl` tests are a control: those loads are safe once every branch has resolved. So E12b uses {branch model} and E12a uses {branch model, `_stl` model}. The `_stl` runs need the store-bypass hooks, which exist in copies (stl-port, `STL_SPECULATION.md` "Port to the AMuLeT builds").

#### Protection set: why initial registers only, not all `Reg_s`

- **The papers protect everything, but the model needs a source.** None of the three defenses tracks data: each one hides, delays or undoes an unsafe load whatever its address depends on. So under CT-SEQ every input is a secret: initial registers, memory, and anything computed from them. In this skeleton the protection set is a set of `State` atoms, and an atom is an architectural location, shared by every operand that names it.
- **All of `Reg_s` collapses the model (probed).** Every operand of the transmitter becomes a protected source by itself, so state-minimality (`all s: State | secure…[RS->s]`) removes every other state. In a 600-instance seeded random sample, 600/600 instances have exactly one state (one register, no `Mem_s`). No memory-sourced chain survives, which is worse than today.
- **Draft rule: `Mem_s + (Reg_s - Instruction.outreg.opstate)`.** Registers the test never writes hold their initial value, so they are secrets. Written registers are protected only through `rf`/`ddi` from a protected source, as before. The loss is cosmetic: a test that reads a register's initial value and overwrites it later can always use another register atom.
- **Concretization treats both kinds of secret the same way.** Stage 2 zero-initializes unwritten registers and memory (`parsexml.py:1122,2105-2108`), and `check_footprint` never reads the transmitter (PART 7). So the new shapes are stimuli of the same kind as the existing ones: the register-only form of AMuLeT's UV6 gadget, with no load needed to bring the secret in.

#### `_stl` variants: why no change

- **Under store bypass the squashed code re-executes on the same path.** The only value that differs between the transient run and the architectural run is the stale value the bypassing load read. A transmitter whose address comes from an initial register, or from a load before the store, touches the same line again after the squash. Adding registers would only add tests with no transient-only footprint.
- **The kept STT-style untaint (a load with no older unresolved store declassifies its location) is a stimulus-efficiency choice, not a paper rule.** None of the papers untaints anything. It drops one shape: a committed read of the same location before the store, i.e. the classic SSB plus a warm-up read. That shape is a cache-setup variant of tests that are already generated. I am raising it rather than changing it (DECIDE FP-7).

#### Drafts and Alloy runs (Mac, 2026-11-10 01:2x)

Drafts (NEW files, unapproved, no config uses them): `STAGE1_alloy/models/proposed/footprint_v2/{InvisiSpec,CleanupSpec,SpecLFB}_6_v2.als`, each with a `.diff` against its current model. The diff is the header plus one clause line, `fun hardware_protection_policy: State {Mem_s + (Reg_s - Instruction.outreg.opstate)}`, with the paper quote as a comment. Everything between `CLEAN MODEL WITH KIND-FIELD REFACTORING` and the defense-block banner is byte-identical to `STT_6.als` (checked with `diff`). The three drafts differ only in their header and comments.

| model (scratch copies of InvisiSpec; the 3 defenses share the block) | `a6CountOnly` cap 3,000 | 600 seeded random (`a6RandomModels`, seed 20261110) |
|---|---|---|
| current `InvisiSpec_6` | SAT, 3,000 (cap) in 36 s | 0% register-only; 219 distinct cores; top cores `Load Store Branchn? Load~*`, `Load Branchn? Load~*` |
| v2 draft | SAT, 3,000 (cap) in 38 s | 48% register-only (no `Mem_s`), 52% memory-sourced; 217 distinct cores; new cores `Othern Otherx Branchn? Load~*`, `Otherx Branchn? Load~*`, `Branchn? Load~*` (UV6 shape) |
| v2 + `no Mem_s` (register-only query) | SAT, 3,000 (cap) in 35 s | first 30: every one is `… Branchn? … Load~*` with an initial-register or ALU-on-register address |
| current + `no Mem_s` | UNSAT (0 in 1 s): today no register-only test exists | n/a |
| all `Reg_s` (rejected) | SAT, 3,000 (cap) in 33 s | 100% have exactly one state; 171 cores |

Total instance counts were not measured: every run hit its cap, as the 2026-11-09 probes did. Cores are the instructions left after dropping operand-free padding, keeping the unresolved branch. Scratch copies and XMLs were in the session scratchpad and are throwaway.

#### Decisions for Anna (also in `URGENT_TODO.md`)

- [ ] DECIDE FP-6 (protection set, supersedes FP-1's recommendation): (a) adopt v2 for the three branch models: memory + initial registers, never untainted (recommended; matches CleanupSpec p3, CT-SEQ, and AMuLeT's UV6); (b) keep `Mem_s` only and state in the paper that register secrets are reached only through a committed load; (c) all `Reg_s` (rejected: collapses to one state). Note for (a): in a capped corpus about half the instances become register-only, so the memory-sourced share halves. If that matters, generate the two halves separately (v2 + `no Mem_s`, and the current model) and fix the split.
- [ ] DECIDE FP-7 (`_stl` untaint): (a) keep the STT-style untaint in the `_stl` variants (recommended: it keeps only stale-value transmitters, and the dropped shape is a warm-up read); (b) never untaint there too, for uniformity with the branch models (adds transmitters that re-execute on the same line).
- InvisiSpec Spectre vs Futuristic: no separate model. E12b runs the branch model; E12a runs the branch model plus `InvisiSpec_6_stl`. Not a decision unless Anna wants a literal Futuristic-VP model, which I recommend against (above).

---

## PART 9 — The ten defenses in the specification language (formalization table, 2026-11-15, defense-table)

*Anna's ask (2026-11-15): find the formalizations of the ten defenses the intro says SimSpect expresses (STT, SpecShield, NDA, DoM, SDO, SPT, ReCon, InvisiSpec, SpecLFB, CleanupSpec), or make a table that gives each one precisely as execution contract, protection set + update rule, and leakage contract + transmission criterion. This answers the 🚨 URGENT_TODO item "find where the other four defenses' specifications went". Sources read this session: the defense blocks of `STAGE1_alloy/models/{STT_6_u_lpP,Recon_6_u_lpP,SPT_6_oneLP_v2,Footprint_6_u_lpP,STT_6,InvisiSpec_6_stl}.als` and `proposed/ultimate/{STT_6_u_stl,Recon_6_u_stl}.als`, the old sketches in `old_models/stt_final.als:378-425`, `specs/transmitter_criteria.json`, `specs/leakage/*.json`, `specs/gem5_builds.json`, `wiki/state/EVAL_MANIFEST.md`, and (for the four paper-only rows) the papers listed in each row. No `.als` was touched.*

**Where the ten formalizations are.** Six of the ten have a real, evaluated three-clause specification: STT (`STT_6_u_lpP.als`), ReCon (`Recon_6_u_lpP.als`), SPT (`SPT_6_oneLP_v2.als`), and InvisiSpec, CleanupSpec and SpecLFB, which share one footprint block (`Footprint_6_u_lpP.als`, identical clause lines in `InvisiSpec_6.als`, `CleanupSpec_6.als`, `SpecLFB_6.als`). NDA and SpecShield exist only as commented-out sketches in the old syntax (`old_models/stt_final.als:378-425`: SpecShield-ERP, SpecShield-ERP+, NDA-S, NDA-P; the same block is copied in the other `old_models/` files); they predate the current skeleton and were never enumerated. DoM and SDO have no specification anywhere in the repo or its git history (`git log --all -S` on `.als` files finds nothing). NDA and DoM are nevertheless *run*: the ReCon group's gem5 implements them as `--scheme=1` (code enum `Delay`) and `--scheme=3` (`specs/gem5_builds.json`), and rows E8 (NDA) and E9 (DoM) run them on STT's test set with `check_ld` (`EVAL_MANIFEST.md:31-32,65-67`). The rows below for NDA, DoM, SpecShield and SDO are new, written from the papers.

### Notation (shared by every row)

- **Program.** Instructions totally ordered by `spo`. Kinds: `Load`, `Store`, `Branchn` (non-transmitting branch), `Branchx` (transmitting branch), `Othern` (ALU), `Otherx` (variable-latency ALU that transmits). Flags `committed ⊆ resolved`; the committed instructions are a program-order prefix (`STT_6_u_lpP.als:169-172`). `U` = uncommitted.
- **Operands.** `inreg` (≤2), `inaddr`, `inmem`, `outreg`, `outmem`; each names one architectural location (`Reg_s` or `Mem_s`). A load is `inaddr, inmem → outreg`; a store is `inreg, inaddr → outmem`; an ALU is `inreg* → outreg`; a branch reads `inreg`. Edges: `rf` (an output to the input that reads it, same location), `ddi` (input to output inside one instruction). `op_edges = rf ∪ ddi`.
- **Speculation sources.** `Br↑` = instructions after an unresolved branch (`has_unresolved_brs_p`, `STT_6_u_lpP.als:279`). `St↑` = after a store whose address is unresolved (`u_store_shadow_p`, `:398`; `has_unresolved_strs_p` in the older `_stl` files). `Any↑` = after any unresolved instruction (the Futuristic flavor, parked).
- **Violation (shared skeleton, identical in every model).** Let `P` = the protection set: the seed `P₀` folded through the update rule once per instruction in `spo` order (`last_committed_protset_p`, `:267`). Let `X` = the leakage-function operands of instructions inside the execution contract (`speculative_xmit_p`). The program leaks iff `X ∩ (P ∪ P.^op_edges) ≠ ∅` (`secure_speculation_scheme_p`, `:296-299`). So forward taint along register and memory dataflow is part of the shared check, and a defense's update rule only says what each instruction adds to or removes from `P`.
- **NSX** = leakage-function operands of instructions *outside* the contract (non-speculative transmitters; `nonspeculative_xmit_p`, `SPT_6_oneLP_v2.als:251`). Used for declassification.
- **Leakage contract vs transmission criterion.** The leakage contract is the Alloy leakage function: *which* instruction-operand pairs transmit. The transmission criterion is the Stage 3 rule: *what microarchitectural action* of that transmitter, observed in gem5, counts as transmitting. The shared window for the delay defenses is `lc_retire < t < fnc_retire` with every annotated unresolved branch still unresolved at `t` (`specs/transmitter_criteria.json` `window`).

### Summary table

| Defense (variant) | Specification in SimSpect | Execution contract | Protection set: seed `P₀` | Update rule (per instruction, along `spo`) | Leakage contract | Transmission criterion (Stage 3) |
|---|---|---|---|---|---|---|
| **STT** (Spectre) | `STT_6_u_lpP.als:389-435` (evaluated, v3 pipeline) | `U ∩ Br↑` | the memory value read by every speculative load: `(Load ∩ contract).inmem` | none (identity). Taint flows forward through the shared closure; untaint is implicit (a value is tainted iff an unsafe load is in its backward data cone); no declassification | `Load.inaddr + Branchx.inreg` | `ld`: `check_ld` data-obtained gate: a read packet reached the cache, or the value was store-forwarded and the load completed, inside the window. `br_x`: `check_br` redirect (does not enforce the window; weak) |
| STT (STL flavor) | `proposed/ultimate/STT_6_u_stl.als:362-416`; evaluated STL corpora used `STT_6_stl.als` | `U ∩ St↑`, plus facts: no unresolved branch, and every unresolved store truly aliases a younger speculative load | as STT (`STT_6_stl`: all `Mem_s`) | identity (`STT_6_stl`: a load with no older unresolved store removes the location it read) | as STT | as STT, STL window checker not written |
| **ReCon** | `Recon_6_u_lpP.als:408-507` | `U ∩ Br↑` (STL flavor: `Recon_6_u_stl.als`) | STT's seed minus the *revealed* reads (defined below) | identity | `Load.inaddr + Branchx.inreg` | as STT (`specs/leakage/recon.json`) |
| **SPT** | `SPT_6_oneLP_v2.als:369-397` (evaluated; v3 and `SPT_6_u` are drafts) | `U ∩ Br↑` | every operand except a register or address input with no producer in the program: all memory and every produced value are protected, initial register values are public | remove (a) the non-speculatively transmitted operand and its `rf` producer; (b) an ALU's output if it has no inputs; (c) an ALU's output if none of its inputs is in `P`; (d) an input whose `rf` source is not in `P`; (e) a load's output and memory read if the value was forwarded from a store whose data is not in `P` | `Load.inaddr + Branchx.inreg + Store.inaddr` | `ld`, `br_x` as STT; `str`: no store checker yet (falls back to `check_ld`) |
| **InvisiSpec** (Spectre; Futuristic) | `Footprint_6_u_lpP.als:376-397`; Futuristic also runs `InvisiSpec_6_stl.als` | Spectre: `U ∩ Br↑`. Futuristic: the branch model plus `U ∩ St↑` (`InvisiSpec_6_stl`) | all memory plus every register the program never writes (the initial register values): `(Mem_s + (Reg_s − outreg.opstate)).~opstate` | identity: never untainted (`_stl`: a load with no older unresolved store removes its location, DECIDE FP-7) | `Load.inaddr` | footprint: any `fill`/`evict`/`inv`/`coh`/`repl_touch` event in L1D, L2, directory or DTLB by a squashed instruction younger than lc, inside the window; InvisiSpec's own SB/LLCSB buffers allowed. Futuristic actor: any footprint before that instruction's visibility point (`specs/leakage/invisispec.json`) |
| **CleanupSpec** | same footprint block | `U ∩ Br↑` (`CleanupSpec_6_stl`: `U ∩ St↑`) | as InvisiSpec | identity | `Load.inaddr` | per-line balance: in L1D (installs and victims) and L2 (installs), the net speculative change minus what cleanup undid must be zero; too little cleanup (UV3, UV4) or too much (UV5) is a leak (`specs/leakage/cleanupspec.json`) |
| **SpecLFB** | same footprint block | `U ∩ Br↑` (`SpecLFB_6_stl`: `U ∩ St↑`) | as InvisiSpec | identity | `Load.inaddr` | a `fill` or `evict` in L1D or L2 by a squashed instruction younger than lc, inside the window; parking in the LFB allowed; speculative hits out of scope (`specs/leakage/speclfb.json`) |
| **NDA-Strict** (+BR) | none (paper only; old sketch `NDA-S` is wrong, below). Run as gem5-recon `--scheme=1` on STT's test set (E8) | `U ∩ Br↑` (§5.1 says "after an unresolved branch or store", open Q1); +BR adds `Loads ∩ U ∩ St↑` | the output of every speculative instruction: `contract.outreg` | identity. A value becomes safe when its producer leaves the contract, i.e. when the older branch or store resolves (p7), not at commit | every consumer: `Load.inaddr + Store.(inaddr + inreg) + (Branchx + Branchn).inreg + (Otherx + Othern).inreg` | a consumer receives the unsafe value (wakes up on its tag or takes it off the bypass) while the producer is still unsafe; the E8 proxy is `check_ld` on the first dependent load |
| **NDA-Permissive** (+BR) | none (sketch `NDA-P` is wrong). gem5-recon's `Delay` scheme is this variant restricted to branch and store shadows | `U ∩ Br↑` (+BR: `∪ St↑`) | the output of every speculative *load*: `(Loads ∩ contract).outreg`. GPRs are not secret | identity | every consumer, as Strict | as Strict |
| NDA load restriction (and full = Strict+BR ∪ load restriction) | none | every instruction that is not the ROB head: `U − first_uncommitted` (all sources: faults, TSX aborts, interrupts, memory-order replay) | `(Loads ∩ contract).outreg` | identity | every consumer | as Strict |
| **DoM** (delay-on-miss) | none. Run as gem5-recon `--scheme=3` on STT's test set with `check_ld` (E9) | a load is shadowed: `U ∩ (Br↑ ∪ St↑ ∪ E↑ ∪ M↑)`. E = after a memory op with an unknown address or an op that can fault (evaluated: memory ops and integer divide); M = after an older load that has not finished (TSO only) | all data (p12: "all data are equally important and need to be kept secret"); in our vocabulary the footprint block's `Mem_s` + initial registers | identity (no taint: the load is hidden, not its data) | `Load.inaddr` | footprint: a shadowed load may not change any cache state; an L1 hit may return its value but may not update replacement state, and an L1 miss is dropped (p4 §3.3); TLB misses likewise. So a `fill`/`evict` beyond L1, an L1 `repl_touch`, or a TLB fill by a shadowed load is a leak. Variants: naive (any execution before the ROB head), eager (any execution while shadowed) |
| **SpecShield-ERP** | none (sketch `SpecShield-ERP` is wrong) | younger than the Early Resolution Point: `U ∩ (Br↑ ∪ after a load or store whose address is not yet computed and translated)` (p5 §IV-B) | the output of every load in the contract: `(Loads ∩ contract).outreg` (memory-resident secrets only, p3-4) | identity ("No load forwards until it reaches ERP", Table III) | every consumer, as NDA | a consumer receives the load's value before the load passes ERP; the load's own cache fill is allowed (p4) |
| **SpecShield-ERP+** | none (sketch `SpecShield-ERP+` misses `Store.inreg`) | as ERP | as ERP | identity: forward taint through low-risk ops is the shared closure; a value is untainted once its tainted producer passes ERP (p7 §IV-C) | the high-risk consumers: `Load.inaddr + Store.(inaddr + inreg) + (Branchx + Branchn).inreg` (p6: "Loads, Stores and Branches"); ALU ops are not transmitters | a high-risk consumer receives tainted data before ERP |
| **SDO** | none; no gem5 build | STT's: `U ∩ Br↑` (Spectre) or Futuristic (p2 §II: "We adopt STT's scope of protecting speculatively-accessed data") | STT's: `(Loads ∩ contract).inmem` | STT's (identity) | STT{ld+fp}: `Load.inaddr` + FP operands (`Otherx.inreg`, subnormal inputs) (p11 §VIII) | a tainted transmitter may execute, but only data-obliviously: it leaks iff its execution creates operand-dependent "hardware resource interference" (Def. 2, p4). For a load: any address-dependent state change, a lookup beyond the predicted cache level, or consulting the L2 TLB before untaint (p5-6); the prediction may depend only on non-sensitive information (p4) |

### Precise clauses, per defense (the Alloy lines, with their sources)

**STT** (Yu et al., MICRO'19; quotes as cited in the model file, `yu-2019-stt.pdf`).
- Execution contract: `speculation_contract_p = uncommitted_p & has_unresolved_brs_p` (`STT_6_u_lpP.als:389`). Paper p5 §6.1: "In the Spectre model, an instruction has reached the visibility point if all older control-flow instructions have resolved." A branch that has executed but whose squash is still pending counts as unresolved (Anna, 2026-11-08). Other flavors change only this line: `stl` = `uncommitted_p & u_store_shadow_p`; `futuristic` = `uncommitted_p & unresolved_p.^spo_p` (parked 2026-11-07).
- Protection set: `hardware_protection_policy = (Loads & speculation_contract_p).inmem & o_p` (`:413`). Paper p5: "STT taints the output of any speculative access instruction"; p6 §6.2: "If a load is unsafe, its output is always tainted" (so a store-forwarded value is tainted too).
- Update rule: `prot_set_propagation_p = o` (`:422`). Forward taint (p6 §6.2: "an instruction's output register is tainted if any of its input registers are tainted") is the shared `^op_edges` closure. Untaint (p6: "when all the data dependencies of an instruction become untainted, the instruction's output is untainted") needs no step: a value is tainted iff some load in its backward cone is unsafe. No declassification.
- Leakage contract: `Loads.inaddr + Branchxs.inreg` (`:435`). Not included on purpose: `Stores.inaddr` (store-address leaks do not count, Anna 2026-11-08; paper alternative §6.4.2) and `Otherxs.inreg` (our configs run `moreTransmitInsts=0`).
- Older canonical `STT_6.als:325-332` (the fv2 corpora): seed `Mem_s` (every memory location), update `s − (Loads & no_unresolved_brs_bf_or_is_p & i).inmem.opstate` (a load with no older unresolved branch declassifies the location it read).

**ReCon** (Aimoniotis et al., MICRO'23) = the STT block plus a reveal delta in clause 2 only (`Recon_6_u_lpP.als:451-485`).
- Execution contract, update rule, leakage contract: identical to STT.
- Protection set: `((Loads & speculation_contract_p).inmem & o_p) − revealed_p` (`:485`). A memory read `m` of load `L3` is revealed iff there is a committed direct load pair `LD1 → LD2` (`LD1.outreg` is `rf`-read by `LD2.inaddr` with nothing in between, and `LD2` is committed: `recon_ld1_p`, `:451`), `LD1` read the same word before `L3`, and no concealer writes that word between `LD1` and `L3` (`revealed_p`, `:475`). A concealer is a store whose address is resolved or that has committed (`recon_concealer_p`, `:465`); a store with an unresolved address does not conceal, because the re-load may bypass it (§4.5.2). Paper: ReCon's only change is that "values that previously have been made public" are not potential secrets (§3.1), made public by a committed load pair (§4.1-4.3, 5.1); "for STT, any load that receives a revealed value untaints its destination register" (§5.4).
- Open: reveal at commit (what ReCon implements) vs at LD2's visibility point (§5.1), DECIDE B1 in the model comment.

**SPT** (Choudhary et al., MICRO'21), evaluated model `SPT_6_oneLP_v2.als`.
- Execution contract: `uncommitted_p & has_unresolved_brs_p` (`:369`), the Spectre model.
- Protection set: `o_p − ((Inreg + Inaddr) − i_p.outreg.rf_p)` (`:375`): every operand except register or address inputs that no instruction in the program produced.
- Update rule (`:379-397`), applied at each instruction `i`: `− (i.operands & nonspeculative_xmit_p).*~rf_p` (declassify the non-speculatively transmitted operand and its producer); `− (i & Other − inreg.Inreg).outreg` (constant producer); `− (i & Other − inreg.o).outreg` (forward untaint: no input protected); `− ((i.inreg + i.inaddr) & (Operand − o).rf_p)` (an input whose source left `P`); `− (i & Loads & inmem.(((Stores − inreg.o) & inreg.Inreg).outmem.rf_p)).(outreg + inmem)` (store-to-load forwarding of unprotected data).
- Leakage contract: `Loads.inaddr + Branchxs.inreg + Stores.inaddr` (`:378`); SPT §2.1 p2 lists memory, control-flow and variable-time instructions as transmitters (`MODELS_AND_BUILDS.md` PART 7).
- Known defect, already found and fixed in drafts: declassification (a) is dead under the shared `^op_edges` closure, because the producer load's `inmem` stays protected and re-flags every other reader of the declassified value (audit S-1, `wiki/state/ALLOY_MODEL_CHANGES.md:366`). `SPT_6_oneLP_v3.als` (Option A, recommended for clean runs) and `SPT_6_u.als` (fixpoint seed, not run) fix it. SPT's paper also defines backward untaint through invertible ops (MOV, ADD; p7), which v2 does not model and `SPT_6_u` does (`InvOp`).

**InvisiSpec, CleanupSpec, SpecLFB** (one footprint block, `Footprint_6_u_lpP.als:376-397`; paper check in "2026-11-10 — Paper check of the footprint models" above).
- Execution contract: `uncommitted_p & has_unresolved_brs_p`. InvisiSpec p4: "In the Spectre attack model, USLs are the speculative loads that follow an unresolved control-flow instruction"; the Futuristic model ("all the speculative loads that can be squashed by an earlier instruction") contains it, and E12a adds the `_stl` model. CleanupSpec deems "all transient instructions potentially 'unsafe' until they retire" (§2.1 p3), and SpecLFB lists four MUSL sources (§5 pp7-8); the harness can squash only on a branch or a store alias, so the branch and `_stl` models cover what can be realized.
- Protection set: `(Mem_s + (Reg_s − Instruction.outreg.opstate)).~opstate` (`:386`): all memory plus the initial value of every register the program never writes (DECIDE FP-6). CleanupSpec §2.1 p3: "The secret may be accessed from the memory or from a register, or computed, transiently." All of `Reg_s` collapses the model (600/600 instances have one state).
- Update rule: identity, never untainted (`:393-397`). None of the three tracks data; each hides, undoes or delays every unsafe load whatever its address depends on.
- Leakage contract: `Loads.inaddr` (`:392`). InvisiSpec p4: "Since we focus on cache-based covert and side channel attacks, we limit ourselves to load instructions."
- Transmission criteria differ per defense (summary table). For all three the footprint checker's actor is *any* squashed instruction younger than lc, not the model's transmitter (`check_footprint.py` never reads `xmit_pc`; DECIDE D2 in PART 7), so for these builds the model chooses which programs run, not which run is a hit.

**NDA** (Weisse et al., MICRO'19, `~/Documents/quail/sources/papers/weisse-2019-nda.pdf`, PDF pages; read via `pdftotext` 2026-11-15).
- Mechanism: an unsafe micro-op "writes back to its destination physical register, but does not broadcast its destination tag to dependent instructions, does not mark its destination register ready, and does not forward its output value on the bypass network" (p7 §5.1). So NDA blocks the *producer's* value from *every* consumer, rather than tainting data and holding a transmitter.
- Strict: "NDA marks all micro-ops dispatched after an unresolved branch or store as unsafe" (p7 §5.1). Permissive: "marks only load instructions after an unresolved branch/store as unsafe. Arithmetic and control instructions are unconditionally marked safe at dispatch" (p8 §5.2). Safe point: "When the eldest outstanding micro-op resolves, it marks instructions in the ROB safe until the next eldest unresolved branch/store" (p7), i.e. at resolution, which is exactly what the contract `U ∩ Br↑` expresses. Load restriction: "loads all are considered unsafe until they are the eldest unretired instruction (i.e., at the head of the ROB)" (p9); its threat model does "not consider the contents of any GPR to be secret".
- Scope limit that the seed must respect: "We do not prevent an attack that leaks a secret using only a single speculative micro-op" (p6 §4.2). A seed of "outputs of unsafe instructions" respects this automatically; a seed of all `Reg_s` (the old `NDA-S` sketch) does not.
- In the skeleton, NDA-Permissive is `STT_6_u` with the leakage function widened to every consumer (the seed `(Loads ∩ contract).outreg` and STT's `.inmem` are equivalent through the load's `ddi` edge). NDA-Strict widens the seed to every speculative output as well. The `_u` skeleton is already Operand-typed, so both are expressible today with no skeleton change; listing `Branchn`/`Othern` inputs as transmitters means the x/n kind split carries no meaning for NDA.
- gem5-recon `--scheme=1` (`Delay`): a speculative load does access the cache, and only its writeback to dependents is held until it is non-speculative (`~/Downloads/dockerrecon/gem5-recon/src/cpu/o3/lsq_unit.cc:194-210`, re-read 2026-11-15), and shadows are cast only by conditional branches and stores (`decode.cc:685-694`). That is NDA-Permissive+BR. E8 scores it with `check_ld` on the dependent transmitter, which is the right *kind* of criterion for NDA (a dependent obtained the value).

**DoM** (Sakalis et al., ISCA'19, `sakalis-2019-dom.pdf`).
- Shadows (p3 §2): E-shadow (memory ops with unknown addresses, arithmetic and other ops that can fault; evaluated: memory ops and integer divide), C-shadow (unresolved branch condition or target), D-shadow (store with an unresolved address), M-shadow (TSO: an older load not yet finished). Only loads are delayed: "Since we do not delay computational instructions, only loads, that side-channel is left exposed" (p11 §6).
- Delay-on-miss (p4 §3.3): an L1 hit returns data but delays replacement-state updates; "In the case of an L1 miss, the request will simply be dropped." Eager: "loads are only executed when they are no longer shadowed by another instruction." DoM+VP gives a shadowed L1 miss a predicted value.
- Fit: DoM is a hide defense, like InvisiSpec and SpecLFB, so it fits the **footprint block** (all data protected, identity, `Load.inaddr`) with a broader contract and a criterion of "no cache-state change beyond an L1 hit". Value prediction has no counterpart in the language.
- Consequence for E9: `check_ld` counts any in-window data-obtaining load, L1 hits included, which DoM allows by design. That is why every E9 load test hits (2,602/2,602, `EVAL_MANIFEST.md:67,87`; the existing "warm-L1 criterion" DECIDE). Under this formalization E9 should be scored with a footprint criterion.
- gem5-recon `--scheme=3`: shadows only from conditional branches and stores (`decode.cc:685-694`; the FP exception shadow is commented out), speculative packets marked L1-only (`lsq.cc:1443-1446`), and, not in the paper, a conditional branch that is not the oldest branch shadow is held (`inst_queue.cc:1459-1465`). All re-read 2026-11-15. The realizable contract on this build is `U ∩ (Br↑ ∪ St↑)`, which the branch and `_stl` models already produce.

**SpecShield** (Barber et al., PACT'19, `barber-2019-specshield.pdf`, downloaded 2026-11-15 from the PACT'19 proceedings; proceedings page = PDF page + 150).
- Scope: "SpecShield does not consider register-resident secrets" (p3-4); "by design, SpecShield allows for speculative data to be loaded into the cache" (p4). So the speculative load's own cache access is not a transmission; its value reaching a consumer is.
- Base variant (not in the intro list): "delays the forwarding of data returned by a speculative load instruction until the instruction reaches the head of the reorder buffer (ROB) and is ready to commit" (p4 §IV-A); contract `Loads ∩ U − first_uncommitted`, otherwise as ERP.
- ERP conditions (p5 §IV-B): "1) All older branch instructions … have been resolved … 2) All older load and store instructions have had their address computed, and a TLB translation has been performed. 3) No branch misprediction or memory access exception".
- ERP+: "Data produced by a speculative load is considered tainted. An instruction that has at least one tainted operand also becomes tainted" (p7 §IV-C); the evaluated high-CCR list "includes Loads, Stores and Branches – effectively restricting the forwarding of data to these instruction classes" (p6), and the list is programmable. ERP+ is therefore STT's structure with an ERP contract and `Stores.(inaddr + inreg)` added to the leakage function.
- Store-to-load forwarding of speculative data is not discussed in the paper.

**SDO** (Yu et al., ISCA'20, `yu-2020-sdo.pdf`, NSF PAR author copy, downloaded 2026-11-15).
- Clauses 1 and 2 are STT's: "We adopt STT's scope of protecting speculatively-accessed data, i.e., blocking attacks involving doomed-to-squash access instructions" (p2 §II).
- What changes is the transmission criterion. Def. 2 (p4): "For any two operand assignments args and args′: the execution of Obl-fi(args) and Obl-fi(args′) must create the same hardware resource interference"; predictions and predictor updates "must be a function of non-sensitive information" (p4). For loads, Obl-Ld "does not create observable address-dependent hardware resource interference" at the predicted level, and on an L1 TLB miss "we do not consult the L2 TLB until the address becomes untainted" (p5-6). Variants (Table II, p11): static L1/L2/L3 prediction, the hybrid PC-keyed location predictor, and a perfect oracle used only as a performance bound.
- Fit: SDO's distinguishing property is a *differential* criterion (same interference for any two operand values), which a single-trace checker cannot decide, and its location predictor and success/fail implicit branch have no counterpart in the language. No SDO gem5 build exists here.

**Old sketches** (`old_models/stt_final.als:378-425`, also copied in the other `old_models/` files). All four use the contract `Instruction − committed − no_unresolved_brs − no_unresolved_mem`. In that file `unresolved = Instruction − committed` (`:140`), so this means "uncommitted, after an uncommitted branch, *and* after an uncommitted load or store" (`:155-160`), which matches no paper. Every sketch declassifies at commit and removes the committed load's *address* state (`i.inaddr.opstate`), not the loaded value. In addition: `NDA-S` protects all of `Reg_s` (flags the single-micro-op GPR case the paper excludes); `NDA-P` protects all of `Mem_s` (including values loaded before the branch); `SpecShield-ERP+` omits `Store.inreg`. Treat them as history, not as specifications.

### What the three-clause language cannot express yet

- DoM's value prediction, and SDO's location predictor, wait-buffer validation and success/fail implicit branch.
- SDO's differential transmission criterion (needs two runs with different secrets, or an oblivious-execution check), and any SDO build.
- SpecShield's ERP distinguishes "address computed" from "address translated"; our single `resolved` flag does not.
- Speculation sources the harness cannot squash on (faults, interrupts, TSX aborts, load-load ordering), which NDA's load restriction and DoM's E- and M-shadows include. Programs for those contracts can be generated but would not open a window on our builds.

### Decisions for Anna (also in `URGENT_TODO.md`)

- [ ] DECIDE DT-1 (paper claim "we have expressed 10 hardware defenses"): six of the ten are specified *and* evaluated as Alloy models (STT, ReCon, SPT, InvisiSpec, CleanupSpec, SpecLFB); NDA, DoM, SpecShield and SDO are now specified in this table from their papers but have no model or test set; NDA and DoM are run on gem5-recon with STT's test set. Options: (a) keep "10 expressed" and point to this table (as a paper table), saying six are evaluated; (b) say "six"; (c) build models for NDA-Permissive and SpecShield-ERP+ (each is STT_6_u plus a one-line leakage change, NDA also a seed change) and DoM (footprint block plus a shadow contract) before claiming them. Recommendation: (a) now, (c) for NDA and DoM next, since both already have builds and runs. SDO stays paper-only either way.
- [ ] DECIDE DT-2 (DoM criterion): score E9 with a footprint criterion ("no cache-state change beyond an L1 hit by a shadowed load") instead of `check_ld`, which counts L1 hits DoM allows. Recommendation: yes; this supersedes the open "warm-L1 criterion" question for DoM.
- [ ] DECIDE DT-3 (leakage function = every consumer, for NDA and SpecShield-ERP): allow a leakage function that names `Branchn`/`Othern` inputs too (all consumers), or keep the first-transmitter approximation (`Load.inaddr + Branchx.inreg`, which forward taint reaches on any chain that ends in a transmitter). Our checkers only observe transmitters, so the approximation covers every case they can score, but it does not state the paper's guarantee. Recommendation: state the full set in the specification, keep the approximation for generation.
- [ ] DECIDE DT-4 (paper ambiguities, for the NDA/SpecShield rows): (1) does an unresolved store make younger *non-loads* unsafe under NDA-Strict (§5.1 says "branch or store", but Table 2 separates Strict from Strict+BR)? (2) do indirect jumps, calls and returns count as unresolved branches (NDA p6: "Branch instructions include all variants of jmp, call, and ret")? (3) does a DoM TLB miss count as a transmission? (4) are SpecShield's high-risk "Branches" all control instructions or only conditional ones?

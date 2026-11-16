# AMuLeT vs. SimSpect: what each tool can and cannot find

*Written 2026-06-03 (session `6:invisispec`). Durable scope note for posterity —
not a transient finding. Companion to `claudelog.md`; lives in `docs/` so it
survives independently of the running log.*

---

## Why InvisiSpec is out of scope (the definitional argument) — advisor-facing

*(Added 2026-06-10. This is the principled scope boundary, stated as a category
distinction, not a difficulty plea. Read this section first.)*

**Slide figure:** `docs/scope_diagram.png` (regenerate with `python3 docs/make_scope_diagram.py`).

```
   secret ─▶ dataflow ─▶ [ TRANSMITTER ] ─▶ µarch channels ─▶ attacker observes
   operand    (taint)     load / branch       L1 tag · LRU · MSHR/TBE · L2 ·
                               │               dir · TLB · L1I · undo/cleanup
                               │                        │              (open-ended)
              ┌────────────────┘                        └────────────────┐
        SimSpect ORACLE  ✓ IN SCOPE                  AMuLeT ORACLE  (out of scope for us)
   "did the transmitter fire in the window?"   whole-µarch, DIFFERENTIAL across runs,
   channel-agnostic, single-run                per-channel + defense-specific

   transmitter-blocking defenses act at ▲       footprint-hiding defenses act at the channels
   STT · SPT · Recon · NDA · fence/delay         InvisiSpec · CleanupSpec · SpecLFB · MuonTrap
   (same security def as our oracle)             (let transmitter FIRE, hide/undo the footprint)
```

**Thesis.** SimSpect's leakage oracle is defined at the **transmitter level**: track secret
dataflow to a transmitter, then check whether that transmitter *performed its speculative
action inside the window*. The oracle is **channel-agnostic on purpose** — and that is exactly
correct for the class of defense we target.

**Why it's correct for our class.** The comprehensive Spectre defenses we evaluate — STT, SPT,
Recon, NDA, taint-tracking / delay / fence families — all define security at the **transmitter
gate**: *no instruction may execute on a secret-derived (speculatively-tainted) operand while it
is unsafe, regardless of which microarchitectural channel it would have used.* They kill the leak
at its source. So the matching oracle is "did the transmitter fire in the window?" — binary. Our
oracle and the defense's security definition are **the same definition**; that alignment is what
makes our detection sound and general.

**Why InvisiSpec is a different animal.** InvisiSpec does **not** stop the transmitter. By design
it *lets the speculative load execute* and instead tries to make its microarchitectural
**footprint** invisible (speculative buffer; no coherence-visible install until the visibility
point). Its security property is therefore **not** "the transmitter didn't occur" — *the
transmitter occurs, intentionally* — it is "the speculative access leaves no observable
secret-dependent state in any µarch structure." So our oracle is **type-mismatched, not merely
under-powered**: applied to InvisiSpec it would report "the transmitter occurred" on essentially
every test — which is **true and intended**, not a bug. The distinction between a *working* and a
*broken* InvisiSpec lives entirely in the channel/footprint, which our oracle deliberately
abstracts away. A transmitter-occurrence oracle structurally cannot judge a footprint-hiding
defense.

**Testing InvisiSpec is a different oracle, for three independent reasons.**
1. **The channel set is open-ended and defense-specific.** A speculative access can perturb L1
   tags, replacement/LRU metadata, MSHR/TBE occupancy, L2, the coherence directory, the TLB, the
   L1I, the prefetcher, and the defense's own undo machinery. That set is not fixed — it depends
   on the microarchitecture and the defense — so there is no single channel-independent observer;
   you hand-build one per (defense × structure). **Empirically proven here:** every AMuLeT bug we
   reproduced needed its *own* bespoke watcher — UV1 a Ruby compound-eviction watcher, UV2 a
   contention/stall watcher, KV1 an I-fetch watcher, UV4/unXpec a cleanup-event correlator. N bugs
   → N instrumentation efforts, none reusing the general pipeline.
2. **It is a final-state / differential property, not an in-window occurrence.** Eviction, residue,
   over-clean, "the cleanup footprint differs by hit/miss" — these are *state left behind* or *what
   differs between two runs*. SimSpect is single-run, in-window, occurrence-based by construction.
   (By our own methodology a final-state diff is *confirmation*, not *detection*.)
3. **Several of the bugs aren't even data transmitters.** We generate load/branch *data*
   transmitters; KV1 is an instruction fetch, KV3 a store→TLB walk — outside the transmitter
   vocabulary, independent of the oracle issue.

**There is a right tool for the other side.** Channel/footprint/invisibility violations are
exactly what AMuLeT (and Revizor-style contract differential testing) is built for: observe the
full µarch trace, compare against a leakage contract. SimSpect and AMuLeT are **complementary by
construction** — SimSpect catches transmitter-level violations in *transmitter-blocking* defenses;
AMuLeT catches footprint violations in *invisible/undo* defenses. Re-instrumenting every InvisiSpec
channel inside SimSpect would be reimplementing AMuLeT, worse.

**Pre-empting the obvious objection.** *"But you demonstrated UV1/KV1/UV4/unXpec."* That **supports**
the boundary. Each was a **forced controlled gadget + a bespoke per-channel watcher**, built to
*characterize* the defenses — not a detection produced by the SimSpect pipeline. The general oracle
never surfaced any of them; each required stepping outside the methodology with custom
instrumentation. That is the cost of going out of scope, demonstrated repeatedly.

**One-sentence version.** *SimSpect verifies that the transmitter never fires on protected data;
InvisiSpec lets the transmitter fire and promises you won't see it — so testing InvisiSpec means
auditing every microarchitectural surface that firing could mark, which is a whole-µarch,
differential, defense-specific oracle (AMuLeT's job), not the transmitter-occurrence oracle that
matches the comprehensive transmitter-blocking defenses we target.*

**Crisp scope statement.**
- **In scope** — defenses that enforce security at the *transmitter/execution gate*: "no
  transmitter executes on a secret-derived operand during the speculative window" (STT, SPT, Recon,
  NDA, delay/fence). Oracle: dataflow-to-transmitter + transmitter-occurrence-in-window.
  Channel-agnostic *because the defense is*.
- **Out of scope** — defenses that *permit* the transmitter and instead hide/undo its µarch
  footprint (InvisiSpec, CleanupSpec, SpecLFB-style invisibility, MuonTrap-style). Correctness = a
  per-channel final-state property → AMuLeT's domain.

---

## TL;DR

SimSpect and AMuLeT test secure-speculation defenses in **different leakage
models** and therefore find **different bug classes**. They are complementary,
not redundant.

- **SimSpect** asks: *does a chosen **transmitter** (a specific load / branch /
  ALU op) perform its own observable action **inside the speculative window**?*
  It enumerates **taint/speculation dataflow** gadgets with Alloy and observes
  the **transmitter's own access** through the gem5 **O3PipeView + LSQUnit**
  instruction trace.
- **AMuLeT** asks: *do two inputs to a **random** program produce **different
  µarch state** in a way a leakage **contract** forbids?* It observes the
  **full µarch trace** — cache **tags/evictions**, **MSHRs**, **L1I**, **TLB** —
  and compares against a contract (Revizor-style differential fuzzing).

The bugs AMuLeT reports in these defenses are all **collateral side-effects on
shared µarch resources** (cache *eviction*, MSHR *contention*, I-cache, TLB) —
**outside SimSpect's observation channel and test-generation scope.** SimSpect,
in turn, targets *transmitter-in-window* races (e.g. the visibility-point↔squash
race) that AMuLeT's random search does not aim at.

> The `/work/amulet/amulet-gem5-*_AE-v1.1` builds **are** the AMuLeT
> artifact-evaluation packages (e.g. InvisiSpec's README is "InvisiSpec-1.0";
> AMuLeT added a `apply_spec_eviction_patch` toggle). So the AMuLeT bugs are
> reproducible *in these exact builds* — with AMuLeT, not with SimSpect.

Reference: Fu et al., *AMuLeT: Automated Design-Time Testing of Secure
Speculation Countermeasures*, ASPLOS '25 (`amulet.pdf` in repo root). InvisiSpec:
Yan et al., MICRO '18 (`InvisiSpec_*.pdf`).

---

## The two leakage models side by side

| | **SimSpect** | **AMuLeT** |
|---|---|---|
| Test generation | Alloy enumerates taint/speculation **dataflow** gadgets; one **chosen transmitter** per test | Revizor-style **random** programs + multiple **inputs** |
| Leakage definition | Transmitter's observable action falls in `lc_retire < signal < fnc_retire` with guarding branches unresolved | µarch trace **differs across inputs** beyond what the **contract** (CT-SEQ / CT-COND) allows |
| What's observed | The **transmitter's own** access: O3PipeView + **LSQUnit** trace (load execute / packet / spec-read / expose tick; branch redirect; div fault) | **Full µarch trace**: cache **tags + evictions**, **MSHRs**, **L1I**, **TLB** |
| Comparison | Single run vs. the **model's** window prediction (discrepancy = signal) | **Differential** across inputs vs. a **contract** |
| Sweet spot | *Targeted* gadget reachability + **timing races** in the speculative window | *Emergent* leaks via shared-resource side effects; black-box coverage |
| Blind spot | Collateral state changes that aren't the transmitter's own access (evictions of **other** lines, MSHR/I-cache/TLB); needs cache **occupancy** pressure it can't generate | A specific targeted gadget random search may not hit; contract must encode the channel |

---

## The bugs AMuLeT found (and why they occur)

AMuLeT reports **3 known + 6 unknown** bugs across InvisiSpec, CleanupSpec, STT,
SpecLFB. The unifying root cause: **each defense defined "safe/invisible" too
narrowly** — it neutralized the *intended* channel (e.g. coherence state) but the
speculative operation still perturbs **another shared µarch resource** that is
observable.

### InvisiSpec

1. **Speculative L1D-cache eviction (UNKNOWN / headline).** A spec load
   (`SPEC_LD` / Spec-GetS) that **misses on a full cache set** triggers an
   `L1_Replacement` — it **evicts a conflicting line** while still speculative.
   The eviction is observable → leaks the spec load's address, breaking
   invisibility even **single-threaded**.
   - **Why:** invisibility was implemented at the **coherence-state** layer
     (Spec-GetS doesn't change directory/coherence state) but **not** at the
     **allocation/replacement** layer — the spec load still allocates an L1 line
     and evicts to make room. AMuLeT paper §4.5, Fig. 5, Listings 1–2.
   - **In this build:** `src/mem/protocol/MESI_Two_Level-L1cache.sm:514` (and
     L2 `…-L2cache.sm:386`) carry AMuLeT's fix as a toggle:
     `if (L1Dcache.cacheAvail(addr) || (in_msg.Type == SPEC_LD && apply_spec_eviction_patch))`.
     `apply_spec_eviction_patch := "True"` is the **default (patched)**; the bug
     is reproduced by setting it **False** (`configs/ruby/MESI_Two_Level.py`
     wires `options.apply_spec_eviction_patch`).
2. **Single-threaded speculative-interference variant (UNKNOWN, "UV2").** With
   few MSHRs (2 vs default 256), spec loads **contend for MSHRs**; the contention
   is observable **from the same core** — no SMT/multithread needed (a stronger
   form of the speculative-interference attack [Behnia et al.]).
   - **Why:** spec loads consume a **shared resource (MSHRs)** whose occupancy
     leaks via timing.
3. **L1I-cache speculative fetches (KNOWN limitation, "KV1").** Spec instruction
   fetches change L1I state; InvisiSpec explicitly does not protect the I-cache.

### Other defenses (for completeness)

- **STT:** tainted **speculative stores** speculatively access the **TLB** → TLB
  state leak (previously shown by DOLMA — **known**).
- **CleanupSpec:** leaks of speculatively-accessed addresses (**unXpec**, known)
  + a **lack of cleanup** on some paths (**unknown**).
- **SpecLFB:** the open-source implementation is **insecure** (**unknown**).

**Pattern:** cache **replacement/eviction**, **MSHR** contention, **L1I**,
**TLB** — all *shared µarch resources* perturbed as a *collateral* effect of the
speculative operation, distinct from the transmitter's "intended" channel.

### Per-bug scope determination (does SimSpect's model reach it?)

The deciding principle: **SimSpect can see a leak iff it is the transmitter's
*own* access occurring *inside* the speculative window**, visible in the
O3PipeView+LSQUnit instruction trace. It is blind when the leak is (i) collateral
state on another resource, (ii) post-squash residue / cleanup correctness, or
(iii) on a channel other than the D-cache line-fill the transmitter performs.

| Bug | Defense | Leak channel | Stimulus needed | SimSpect observes? | Verdict |
|---|---|---|---|---|---|
| UV1 — L1D eviction | InvisiSpec | spec load **evicts** a conflicting line | full cache set | no (Ruby cache) | **OUT** |
| UV2 — interference | InvisiSpec | **MSHR** contention (timing) | few MSHRs (2) | no (MSHR/debug-log) | **OUT** |
| KV1 — I-fetch | InvisiSpec | **L1I** state | — | no (I-cache) | **OUT** |
| UV3 — store not cleaned | CleanupSpec | **post-squash L1D residue** of a spec store | spec store | no (final cache; install is *expected*) | **OUT** |
| UV4 — split not cleaned | CleanupSpec | post-squash L1D residue (split req) | cacheline-crossing access | no | **OUT** |
| UV5 — too much cleaning | CleanupSpec | cleanup wrongly **evicts** a non-spec line | NSL+SL reordered, same line | no (final cache, differential) | **OUT** |
| KV3 — store→TLB | STT | tainted spec store installs a **D-TLB** entry | tainted spec store + multi-page | no (TLB; store transmitter) | **OUT** |
| **UV6 — first load unprotected** | **SpecLFB** | transmitter **load installs a secret-dependent line in the spec window** | Spectre-v1 single load | **YES** (LSQUnit/pipeview) | **IN SCOPE** |

**The one exception — SpecLFB UV6.** SpecLFB is *supposed to* delay/prevent the
speculative load's cache install, but an undocumented optimization clears
protection for the **first speculative load in the LSQ** (`isReallyUnsafe`
cleared), so a Spectre-v1 single load **installs a secret-dependent line into the
cache while speculative** (AMuLeT §4.7, Fig. 8). That is exactly `check_ld`'s
criterion — the transmitter load's *own* cache touch in-window — and the stimulus
(`CMP/JNE` mispredict → `MOV RAX,[R14+secret]`) is the Spectre-v1 shape the Alloy
model already enumerates. AMuLeT detects it via a cache-state diff; SimSpect would
detect the *same event* via the in-window cache reach. **Caveat:** SpecLFB is the
one amulet build **not yet hooked** for SimSpect (newer gem5 base; see
`project_amulet_hooks`), so it is in-scope *methodologically* but needs the
BTB-force / resolve-stall / LSQUnit-trace port before SimSpect can run it.

**Why CleanupSpec installs are NOT in scope even though they're cache line-fills:**
CleanupSpec *allows* the in-window install **by design** and cleans it up on
squash. So the in-window install isn't the bug (SimSpect's `check_ld` would
false-positive on every spec load); the bug is whether the **final** cache state
was correctly restored — a post-squash, end-of-test cache-snapshot question only
AMuLeT's differential answers. Contrast SpecLFB, which is supposed to *prevent*
the install — there the in-window install *is* the bug.

---

## Why SimSpect (today) cannot find them

Two independent gaps, illustrated with the InvisiSpec eviction bug:

1. **Wrong observation channel.** Evictions, MSHR occupancy, L1I and TLB state
   live in the **Ruby cache/coherence controllers** and are **invisible to
   O3PipeView + LSQUnit** (the instruction-pipeline trace SimSpect parses in
   `STAGE3_gem5/gem5_common.py`). SimSpect's load checkers key on the
   **transmitter load's own** cache touch, never on the eviction of *another*
   line. The InvisiSpec checker added this session
   (`STAGE3_gem5/check_ld_invisispec.py`) **explicitly assumes** the Spec-GetS is
   invisible — the very assumption the AMuLeT bug violates.

2. **Wrong test stimulus.** The eviction only fires on a **full cache set** + a
   conflicting spec load. SimSpect's Alloy model enumerates taint/speculation
   **dataflow**, not cache-set **occupancy** — its tiny litmus tests never fill a
   set (AMuLeT had to drop to a **2-way** L1D and **2** MSHRs to amplify it).
   SimSpect's generator cannot produce the contention gadget.

3. **No input-differential.** AMuLeT compares two inputs' µarch traces against a
   contract; SimSpect checks one program against the model's window prediction.

| AMuLeT bug | Observation needed | SimSpect today |
|---|---|---|
| L1D speculative eviction | Ruby `L1_Replacement` events, correlated to the spec load | ❌ pipeview/LSQUnit can't see evictions |
| MSHR interference (UV2) | timing/contention diff over inputs | ❌ no differential, no MSHR trace |
| L1I / TLB | L1I / TLB state in the trace | ❌ observes neither |

---

## What SimSpect *does* cover that AMuLeT doesn't

SimSpect targets **transmitter-in-the-speculative-window** questions, including
**timing races** that random fuzzing is unlikely to land:

- The **visibility-point ↔ squash race** class — e.g. STT/SPT, where a genuinely
  protected transmitter is released *at branch resolution* and a packet beats the
  squash by 1–2 cycles. SimSpect reproduces these deterministically with the
  resolve-stall / fnc-commit-stall hooks.
- For **InvisiSpec specifically**, the analogous question is whether the
  **expose/validate** (the *visibility-point* cache access, `lsq_unit_impl.hh`
  `exposeLoads()` → send at `:1280`, gated by `readyToExpose()` /
  `updateVisibleState():1042`) ever fires **before** its guarding branch resolves.
  `check_ld_invisispec.py` tests exactly this. Early observation: on STT_6 ld
  tests the wrong-path USLs are **squashed before any expose** (`never_exposed_
  squashed`, 0 hits) — the defense defers correctly. This is a legitimate,
  distinct result; it is **not** one of AMuLeT's bugs, and AMuLeT does not target
  it.

So: a transmitter's **own** observable action and its **timing** = SimSpect;
**collateral shared-resource** state (evictions/MSHR/I-cache/TLB) = AMuLeT.

---

## If we wanted SimSpect to find AMuLeT-class bugs (cost)

Reproducing AMuLeT's eviction finding inside SimSpect would require **rebuilding
AMuLeT's methodology**:

1. **Cache-event observation** — a checker keying on Ruby `L1_Replacement`
   (a new debug-flag trace), correlating an eviction to an in-flight `SPEC_LD`.
2. **Cache-pressure test generation** — programs that fill an L1 set then issue a
   conflicting spec load; outside the Alloy taint-dataflow model (a different
   generator), and/or small-cache configs (2-way, 2 MSHRs).
3. **Input-differential** — compare two inputs' cache states against a contract.

Given the artifact builds already ship with the toggle, the pragmatic path for
the **collateral-cache** bugs is **AMuLeT itself** (flip
`apply_spec_eviction_patch=False`, run its fuzzer), keeping SimSpect for the
targeted transmitter-window / timing-race questions.

---

## Hardware–software contracts explained (added 2026-11-14)

Sources read 2026-11-14: Guarnieri et al., "Hardware-Software Contracts for Secure Speculation", S&P'21 (arXiv 2006.03841; `~/Documents/quail/sources/papers/guarnieri-2021-hw-sw-contracts.pdf`); Oleksenko et al., "Revizor", ASPLOS'22 (arXiv 2105.06872v2; `oleksenko-2022-revizor.pdf`); AMuLeT ASPLOS'25 §2 and §4 (`fu-2025-amulet.pdf`).

**What a contract is.** A contract says what a CPU is allowed to leak, stated at the ISA level, with no mention of caches or predictors. For a program and an initial architectural state, the contract produces a contract trace (a list of observations). A CPU satisfies the contract if any two initial states with the same contract trace give the same hardware trace (Guarnieri Def. 1). "Exposes X" therefore means X may leak; everything else must not change what the attacker sees. Exposing more means a weaker guarantee. Software's side of the deal: its secrets must not influence the contract trace.

**The two knobs.** The observation clause says what each instruction exposes: MEM = data load/store addresses ("a data cache timing side-channel attack"); CT = MEM plus the program counter ("both data and instruction cache attacks"; named after constant-time programming); ARCH = CT plus the values loaded from memory ("a same-address-space attack, such as assumed in the Speculative Taint Tracking paper"). The execution clause says over which executions observations are collected: SEQ = architectural path only; COND (Guarnieri's "spec", always-mispredict) = also mispredicted branch paths, for a bounded window; BPAS = also store bypass; COND-BPAS = both (Revizor §2). A contract is one of each, e.g. CT-SEQ. Guarnieri writes them [[.]]^seq_ct, [[.]]^spec_ct, [[.]]^seq_arch, and adds [[.]]^seq-spec_ct-pc (PC also leaks speculatively; port-contention-vulnerable CPUs), [[.]]^spec_arch, top (nothing leaks) and bottom (all architectural state).

**Spectre v1 under each contract (Guarnieri Fig. 1).** P1: `if (y < size_A) { x = A[y]; temp &= B[x*64]; }` with y out of bounds and the branch mispredicted. CT-SEQ's trace has only the architectural path, so two secrets A[y] give the same trace; a baseline CPU speculatively touches B[A[y]*64], so the cache differs: violation. CT-COND's trace also contains the mispredicted path's addresses, including B + A[y]*64, so different secrets give different traces, the runs are never compared, and nothing is flagged: CT-COND permits Spectre v1. Guarnieri Thm 1: every instance of their out-of-order hardware model satisfies [[.]]^spec_ct. ARCH-SEQ exposes architecturally loaded values, but A[y] is never loaded architecturally, so the baseline violates it, while STT (A[y] speculatively loaded, so tainted, so the B load is delayed) satisfies it. P2: `x = A[y]; if (y < size_A) temp &= B[x*64];` loads A[y] architecturally first. Under ARCH-SEQ, x is already in the trace, so leaking it speculatively is allowed. STT lets the B load go because x is retired register state, so STT violates CT-SEQ but satisfies ARCH-SEQ (Guarnieri Thm 6: tt satisfies [[.]]^seq_arch, "a clean characterization of the transient noninterference guarantees" of STT). CT-SEQ = speculation adds no leakage beyond constant-time leakage; ARCH-SEQ = speculation leaks nothing not already in architectural state.

**Who uses the term "transient non-interference" (checked 2026-11-14).** Not STT: the MICRO'19 paper says STT "enforces a novel form of non-interference, with respect to all speculatively accessed data" (abstract; §8 "a novel notion of non-interference"), and the companion tech report (`~/Documents/quail/sources/papers/yu-2019-stt-formal-tr.pdf`, §4.2 "The Non-Interference Theorem") never says "transient". The phrase is Guarnieri et al.'s label (S&P'21 §III-B: [[.]]^seq_arch is "a simple and clean formulation of the idea behind transient noninterference [STT]"; §VI-C Thm 6: "a clean characterization of the transient noninterference [STT] guarantees"), reused by Revizor §2 ("equivalent to transient noninterference [STT]"). AMuLeT says "STT's non-interference guarantee"; Protean does not use the term. So cite Guarnieri (not only STT) for the phrase.

**What Protean calls STT's guarantee (checked 2026-11-15, `paper_figures/reference_papers/protean_hpca26/protean_hpca26.pdf`).** A contract, ARCH-SEQ, plus a program class, ARCH code; never "transient non-interference" and never wSNI. §II-C: "Existing comprehensive, programmer-transparent defenses uphold the ARCH-SEQ (NDA [138], SpecShield [13], STT [148]) or CT-SEQ (SPT [32]) security contracts. A defense that upholds ARCH-SEQ (resp. CT-SEQ) leaks no data beyond that which is accessed (transmitted) sequentially." §III-A: "Non-secret-accessing (ARCH) code does not access secrets architecturally, i.e., it never holds secrets in registers architecturally. … ARCH code does not leak secrets on hardware that upholds the ARCH-SEQ security contract (§II-C)." §III-C (ProtSet view): "STT [148], NDA [138], and SpecShield's [13] ProtSets always include all memory but no registers, so they target ARCH programs and secure no others (Fig. 2)." §VII: "Like prior work [41], we test STT and SPT against the ARCH-SEQ and CT-SEQ contracts, respectively". Two Protean wordings differ from Guarnieri: its CT observer "exposes all unsafe transmitter operands" (Guarnieri: PC + load/store addresses), and §II-A defines "A transient instruction is bound to squash [25]; a sequential instruction is bound to commit. Speculative instructions eventually become transient or sequential."

**Which protection set each contract implies, and what our models use (2026-11-15).** Protean (Fig. 2, §III-B) sets the minimum: a defense secures a class if its ProtSet always holds every place a secret may sit. ARCH code: "unaccessed mem", so the ARCH-SEQ minimum is memory not yet architecturally accessed (§V-A ProtCC-ARCH: "Securing non-secret-accessing (ARCH) programs requires protecting architecturally unaccessed memory … unprotecting only architecturally accessed memory"); STT, NDA, SpecShield over-approximate with "all memory but no registers" (§III-C). CT code: "untransmitted regs/mem", so the CT-SEQ ProtSet is every register and memory byte not yet architecturally transmitted (SPT, §III-C). UNR: all regs/mem (SPT-SB). Our models: STT_6_u_lpP seeds the memory read of every speculative load (`STT_6_u_lpP.als:413`), no registers, no untaint, so it is STT's "all memory", not the ARCH-SEQ minimum (a speculative re-load of an architecturally accessed word stays protected); Recon_6_u_lpP removes revealed words (`Recon_6_u_lpP.als:485`), so it sits between all memory and unaccessed memory and still covers the minimum; SPT_6_u protects everything outside the public set U = initial registers (Stage-2 load-immediates, SPT p612 §6.5) + declassified transmitter operands with untaint closure (`SPT_6_u.als:422-502`), i.e. CT-SEQ; Footprint_6_u_lpP protects all memory + initial registers and never untaints (`Footprint_6_u_lpP.als:386`), i.e. UNR, stronger than the CT-SEQ AMuLeT tests those defenses against. Our checkers test the defense's own promise on one trace, not a contract relationally, so a hit can break the defense's promise without breaking the contract it aims to uphold.

**Lattice.** Stronger = exposes less (Guarnieri §III-C, Fig. 4); a CPU that satisfies a contract satisfies every weaker one (Prop. 1). CT-SEQ is stronger than CT-COND (adds speculative observations) and than ARCH-SEQ (adds values). By the same definition (our derivation, not stated in the paper), CT-COND and ARCH-SEQ are incomparable: P1's out-of-bounds A[y] is distinguished by CT-COND but not ARCH-SEQ, and an architectural load whose value is never used as an address is distinguished by ARCH-SEQ but not CT-COND. Fig. 8 places mechanisms: no speculation satisfies CT-SEQ (Thm 2); delaying all loads under unresolved branches (loadDelay) satisfies [[.]]^seq-spec_ct-pc and ARCH-SEQ (Thms 3, 4) but NOT CT-SEQ, because a nested branch on a mispredicted path can still leak through the instruction cache and branch predictor (Example 2); STT-style taint tracking satisfies ARCH-SEQ (Thm 6).

**Why this matters for the InvisiSpec argument.** Guarnieri's Example 2 is the same channel as AMuLeT's KV1: even a defense that keeps every speculative data access out of the cache fails CT-SEQ through the I-cache, because CT's PC observation makes control flow part of the contract. No standard contract says "data cache only": MEM drops the PC from what may leak, which makes MEM-SEQ stronger, not weaker. The channel is set by the attacker model, i.e. which microarchitectural state the tester records (AMuLeT §3.2; default L1D + D-TLB tags; KV1 needed the L1I added). InvisiSpec's guarantee is a statement about channels, so it does not map onto a contract cleanly.

**Software side.** Constant-time code (no secret-dependent control flow, addresses, or variable-latency operands) is what [[.]]^seq_ct captures (Guarnieri §IV-C). A program satisfies weak speculative non-interference (wSNI) w.r.t. a contract if states with equal [[.]]^seq_arch traces have equal contract traces (Def. 4), "a variant of speculative non-interference, the security property checked by Spectector". SNI is a program property; contracts are hardware properties. So SNI does not belong in a hardware–software contract box. **wSNI vs transient NI (checked 2026-11-15).** Guarnieri never contrasts them in one sentence; the split is structural. Transient NI is STT's hardware guarantee, formalized as {|·|} ⊢ [[.]]^seq_arch (Def. 1 + Thm 6: for all programs, equal ARCH-SEQ traces ⇒ equal hardware traces). wSNI is a property of one program w.r.t. a contract [[.]] (Def. 4: equal ARCH-SEQ traces ⇒ equal [[.]] traces). They meet in §IV-D: "the fact that [[.]]^seq_arch and [[.]]^seq_ct are stronger than [[.]]^seq_arch (see §III-C) directly implies wSNI w.r.t. these contracts for any program", so on transient-NI hardware wSNI is free, and on weaker contracts ([[.]]^spec_ct, [[.]]^seq-spec_ct-pc) it must be checked per program with Spectector. wSNI's job is sandboxing (Prop. 3); vanilla sandboxing "is equivalent to p ⊢ NI(π, [[.]]^seq_arch)".

**SNI vs transient noninterference in Guarnieri (read 2026-11-14).** Transient noninterference (STT's guarantee) is a hardware property over all programs: Guarnieri states it as the hardware satisfying [[.]]^seq_arch (Def. 1 + Thm 6): equal ARCH-SEQ traces (sequential PCs, addresses, loaded values) imply equal hardware traces. SNI is a property of one program (Def. 5, generalizing Spectector): p is SNI w.r.t. policy pi and contract [[.]] if low-equivalent states with equal [[.]]^seq_ct traces have equal [[.]] traces; Spectector's original SNI is the instance [[.]] = [[.]]^spec_ct. wSNI (Def. 4) swaps the premise for equal [[.]]^seq_arch traces (sandboxing). They compose (Prop. 2): a program non-interferent w.r.t. a contract, on hardware that satisfies the contract, leaks nothing to the hardware adversary; Props. 3/4: vanilla sandboxing + wSNI, or vanilla constant-time + SNI, give security on any hardware satisfying the contract. On STT-like hardware every program is trivially wSNI w.r.t. [[.]]^seq_arch, but [[.]]^seq_arch "is inherently inadequate for constant-time programming: A program that is non-interferent w.r.t. [[.]]^seq_arch may not access any secret data" (§IV-C). Footnote 1: STT's property "alone does not provide an actionable basis" for software, since leaks of non-speculatively accessed data (P2) are out of STT's scope.

**How testers use contracts (model-based relational testing).** Revizor/AMuLeT: generate a random program and many inputs; compute each input's contract trace on an emulator of the contract; group inputs with equal contract traces; run them on the CPU or simulator and record a microarchitectural trace; any group whose traces differ is a violation (AMuLeT Def. 2.1). A reported leak therefore depends on two choices: the contract (what may leak) and the recorded trace (what is observed). AMuLeT pairings (§4.4): InvisiSpec, CleanupSpec, SpecLFB against CT-SEQ "as these defenses claim to protect against speculative memory-system side channels"; STT against ARCH-SEQ, "which captures STT's non-interference guarantee". On the undefended baseline (§4.2) CT-SEQ violations were Spectre v1 and CT-COND violations were Spectre v4 (store bypass, which COND does not cover).

**Why "hardware–software".** Guarnieri §III: "The purpose of a contract is to split the responsibilities for preventing side channels between software and hardware." Hardware promises to leak no more than the contract trace (the satisfaction relation, checked by Revizor and AMuLeT); software promises its secrets do not influence the contract trace (constant-time programming, sandboxing, wSNI). It is the leakage analogue of the ISA as the functional interface. The framework has three parts: an ISA language, a microarchitecture model, and "an adversary model specifying which microarchitectural components (such as caches or branch predictor state) are observable via side-channels" (§I). The channel lives in the adversary model, not in the contract. Names in use: "hardware–software contract" (Guarnieri), "speculation contract" (Revizor), "leakage contract" (AMuLeT). "Hardware-software security contracts" is Protean's term (Mosier, Nemati, Mitchell, Trippel, HPCA'26, §II-C, citing Guarnieri), where a contract comprises an observer mode and an execution mode, a separate adversary model says how the attacker observes channels, and a microarchitecture "upholds (resp. violates)" a contract; Protean says NDA, SpecShield and STT uphold ARCH-SEQ and SPT upholds CT-SEQ. (Corrected 2026-11-14; an earlier version of this line said the term was not from these papers.) Guarnieri fn. 1: STT's guarantee declares leakage of non-speculatively accessed data (P2) out of scope [STT §4].

**Adversary model: origin, and what Guarnieri says about InvisiSpec and CleanupSpec.** The term is Guarnieri's (§II-D "Adversary model": "We model hardware observations as projections to parts of the microarchitectural state. For instance, a cache adversary can be modeled as a function A projecting µ to its cache component"); their proofs use an adversary that sees the data-independent part of the ROB, the cache, the branch predictor and the scheduler (§V-C). Protean §II-C reuses it; AMuLeT §2.2 calls the same thing the μarch trace, Revizor the hardware trace. Guarnieri §VIII (not formalized, hedged): "Redo"-based defenses, citing InvisiSpec, SafeSpec and MuonTrap, "satisfy [[.]]^spec_ct, [but] they likely violate [[.]]^seq_arch as they still modify other parts of the microarchitectural state such as the reorder buffer", citing speculative interference attacks; "Undo"-based CleanupSpec gives "security against adversaries that observe the final cache state, but [...] likely [not] against the trace-based attackers we consider". So whether these defenses uphold a contract depends on the adversary model; AMuLeT's default (final L1D and D-TLB tags) is a final-state adversary.

**Why a CT-SEQ violation can be a leaked load address.** CT exposes load addresses only along the paths the execution mode runs. SEQ runs only the architectural path, so CT-SEQ lets committed loads leak their addresses but forbids a transient load's address from leaking: Spectre v1's B[A[y]*64] is on the mispredicted path, absent from the CT-SEQ trace, so a cache footprint that depends on it is a violation. CT-COND adds that address to the trace, so the same footprint is allowed.

**Relation to SimSpect's clauses.** Execution contract ≈ execution clause. SimSpect's leakage contract (SynthLC sense: which instructions transmit which operands) is closest to the observation clause but describes the defense's transmitters, not the attacker-visible trace. The protection set has no contract counterpart (a contract leaves it implicit). Term clash to avoid: if the paper defines a hardware–software contract as "leakage contract + execution contract", those are also two of SimSpect's own clause names; Guarnieri's own names (observation clause, execution clause) avoid it.

## Pointers

- Paper: `amulet.pdf` (root) — InvisiSpec eviction bug §4.5, Fig. 5, Listings 1–2.
- Build (AMuLeT artifact): `/work/amulet/amulet-gem5-InvisiSpec_AE-v1.1`
  - eviction bug + toggle: `src/mem/protocol/MESI_Two_Level-L1cache.sm:514`,
    `…-L2cache.sm:386`; default `apply_spec_eviction_patch := "True"`.
  - visibility point: `src/cpu/o3/lsq_unit_impl.hh:1042` (`updateVisibleState`),
    expose send `:1280`; spec read `src/cpu/o3/lsq_unit.hh:855`.
- SimSpect InvisiSpec support added this session:
  `STAGE3_gem5/check_ld_invisispec.py`, `parse_lsq` `expose_tick` in
  `STAGE3_gem5/gem5_common.py`, run at `results/STT_6_invisispec/`.
- Related memory: `project_invisispec`, `reference_gem5_build_hooks`,
  `project_amulet_hooks`. claudelog: 2026-06-03 InvisiSpec entries.

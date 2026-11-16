# CleanupSpec and the loads-only leakage contract (§3.3 sentence check), 2026-11-16

Question (Anna, 2026-11-16): is the §3.3 sentence precise, and does CleanupSpec need its own Alloy specification? Checked against ISCA-27 `8a8a0ab`, `sections/model.tex:53`. Paper untouched, no `.als` touched, no git writes.

## Verdict

**The sentence is correct but not fully precise.** Its conclusion holds: by CleanupSpec's design, transient instructions change the data caches only through loads. The reason it gives is incomplete in two ways. (1) Stores' ownership requests are not the only non-load route the paper closes. It also delays a transient `clflush` until it can no longer be squashed (§3.5) and assumes hardware prefetching is off (§2.1). (2) The gem5 implementation *does* send an ownership request speculatively for a read-modify-write (RMW), through the RMW's load micro-op. That is exactly A-UV3, which Results reports as a bug. So the claim has to be about the **design**, or it contradicts §6. Exact replacement below.

**CleanupSpec does not need a different Alloy specification.** In the paper, the code and our data, every transient change to L1D/L2 comes from a load micro-op: `ld`, `ldis`, `ldfp`, or `ldst`, the load half of an RMW. An RMW's address is its load's address, and Stage 2 makes an RMW from a model load, so `Loads.inaddr` already covers it. Adding store addresses would only produce tests whose transmitter the design (and the implementation) never lets touch the cache. No `.als` diff is proposed and no regeneration is needed.

## The sentence and the proposed replacement

Current text (`sections/model.tex:53`): "InvisiSpec, CleanupSpec and SpecLFB share one specification, whose leakage contract holds only load addresses and whose protection set is all memory and every register the test never writes. Load addresses suffice for CleanupSpec too, although it deems every transient instruction unsafe (\S~\ref{sec:bg-defenses}): it issues a store's ownership request only non-speculatively~\cite[\S 4]{saileshwar2019cleanupspec}, so transient instructions change the data caches only through loads. The three differ in their transmission criteria (\S~\ref{sec:transmission-requirement})."

The first sentence is correct: `Footprint_6_u_lpP.als:384` is `(Mem_s + (Reg_s - Instruction.outreg.opstate))` and `:392` is `fun leakage_function : Operand {Loads.inaddr}`. The third sentence is fine.

Option A (recommended; it names the design, adds clflush, and ties to A-UV3):

- old: `it issues a store's ownership request only non-speculatively~\cite[\S 4]{saileshwar2019cleanupspec}, so transient instructions change the data caches only through loads.`
- new: `by design it issues ownership requests only non-speculatively and delays \texttt{clflush} until it cannot be squashed~\cite[\S\S 3.5, 4]{saileshwar2019cleanupspec}, so transient instructions change the data caches only through loads, for a read-modify-write through its load half.`

Option B (shortest; it keeps the current claim and makes it a design claim only): `by design it issues ownership requests and \texttt{clflush} only non-speculatively~\cite[\S\S 3.5, 4]{saileshwar2019cleanupspec}, so transient instructions change the data caches only through loads.`

Why "by design" matters: Results (`sections/results.tex:32`) says "a speculative read-modify-write's line is not cleaned (A-UV3)". In the implementation that line is installed by a speculative ownership request (GETX), so an undecorated "issues ownership requests only non-speculatively" is false of the code §6 tests. Why the RMW clause is optional: it answers the reader who asks how a loads-only contract finds A-UV3. The commented-out RMW paragraph (`results.tex:38`) has the evidence that every RMW transmitter is a relabelled load ("all 150 minimal RMW cores of up to four instructions [are] relabelled load cores"), but that paragraph is commented out, so the paper currently never says this. Prefetching is left out of both options because CleanupSpec puts it out of scope as an assumption, not a mechanism; this paper has no prefetching anywhere.

## 1. The CleanupSpec paper: what besides loads can change the data caches transiently

Source: `~/Documents/quail/sources/papers/saileshwar-2019-cleanupspec.pdf` (MICRO'19 author copy, PDF pages), text via `pdftotext -layout`.

| route | what the paper says | where |
|---|---|---|
| loads (threat model) | "a threat model where any mis-speculated load could leak information (like prior work [58])" | §2.1, p3 |
| all transient instructions | "We deem all transient instructions potentially 'unsafe' until they retire" | §2.1, p3 |
| stores / RFOs | "the L2 copy never becomes stale transiently as RFOs are issued non-speculatively to prevent Spectre-Prime[44] attacks" | §4, p8 |
| what the security analysis assumes | "we assume the transient change is initiated with a speculative read" | §4, p8 |
| clflush | "A transiently executed clflush can also be used to leak information … We delay such instructions, until they are unsquashable on the correct path." Table 2: clflush M,E,S→I, "Delay till correct-path" | §3.5, p7 |
| coherence downgrades by loads | GetS-Safe: "the core delays the load till it is unsquashable" when an E/M→S change is needed | §3.5, p7 |
| hardware prefetch | "we also assume speculative hardware prefetching is disabled for caches (similar to [58])" (out of scope) | §2.1, p3 |
| I-cache, TLB | "We only consider attacks exploiting the data-cache hierarchy … as other structures like instruction caches, TLB, etc. can be protected with a low overhead with prior works"; p1 also "I-Cache, TLB or Branch Predictor can also be used to leak information, but delaying [40] or buffering [25, 58] transient changes to these structures can prevent this" | §2.1, p3; §1, p1 footnote |
| page walks | not mentioned (the TLB is out of scope) | n/a |
| undo mechanism | it "issues Restore or Invalidate requests only for squashed loads that install a new line on incurring a cache miss" | §6, p10 |

So by design, stores (non-speculative RFOs), clflush (delayed) and prefetching (assumed off) leave the data caches untouched transiently. Loads are the only transient route, and they are the only thing CleanupSpec undoes. The current sentence cites only the RFO part.

## 2. The gem5 implementation (AMuLeT CleanupSpec AE)

Source read: `~/trippel/defense_src/amulet-CleanupSpec_AE-v1.1` (AMuLeT AE source). The build we run is `specs/gem5_builds.json` id `amulet-CleanupSpec` = `/work/amulet/amulet-gem5-CleanupSpec_AE-v1.1`, which is this source plus print-only SimSpect hooks.

- **Plain stores write the cache only after commit.** `LSQUnit::commitStores` sets `canWB = true` only for stores at or below the committed `youngest_inst` (`src/cpu/o3/lsq_unit_impl.hh:1232-1251`), and `writebackStores` sends only `canWB` stores (`:1631-1645`). The one exception, `canWB` set at execute (`:1175-1178`), covers store-conditionals, which x86 does not use. No store prefetch or write-allocate happens before commit; a store's Ruby request is `RubyRequestType_ST` and is made only at writeback (`src/mem/ruby/system/Sequencer.cc:975-979`).
- **An RMW changes the cache speculatively through its load micro-op.** x86 `ldst` is a load micro-op with the `StoreCheck` flag (`src/arch/x86/isa/microops/ldstop.isa:483-485`). The Sequencer turns a read with `StoreCheck` into `RubyRequestType_RMW_Read` with secondary type `RubyRequestType_ST`, an exclusive (GETX) request (`Sequencer.cc:984-993`). It sits in the load queue and issues speculatively, like any load. Its cleanup finds the line in the write-request table, not the read table, and returns `Aliased` (`Sequencer.cc:269-272`), so the cleanup is skipped (`cleanup_skip why=nohitinfo` in our traces). This is AMuLeT's UV3 ("Speculative Store Not Cleaned"; the AMuLeT fix updates cleanup metadata in `Sequencer::writeCallback`, AMuLeT p11 Listing 3, EVAL_MANIFEST:1068). The RMW's `st` micro-op is an ordinary store and writes only after commit.
- **Locked RMWs are non-speculative.** `Ldstl` is defined with `nonSpec=True` (`ldstop.isa:486-489`). Our vocabulary excludes locked and `xchg` forms anyway (`STAGE2_compilation/instruction_tables/proposed/fv4_vocab.jsonc:117`).
- **No page-table walks touch the caches.** We run SE mode. On a TLB miss, `tlb.cc` calls the walker only `if (FullSystem)` (`src/arch/x86/tlb.cc:450-451`); in SE mode it reads the process page table in the simulator (`:457-478`), with no memory request.
- **No prefetching.** The Ruby prefetcher is off unless `--enable-prefetch` (`configs/ruby/Ruby.py:79`, default False; `configs/ruby/MESI_Two_Level.py:162`). None of the 30 CleanupSpec run configs in `runconfigs/` passes it (grep for `enable.prefetch` over the files with `Cleanup_FOR_L1L2`: 0).
- **Instruction fetch goes to the L1I** (`RubyRequestType_IFETCH`, `Sequencer.cc:981-982`), outside the L1D/L2 that `specs/leakage/cleanupspec.json` observes. This is AMuLeT's A-KV2 territory, out of scope by CleanupSpec §2.1.
- **clflush and software prefetch do not occur in test bodies.** Both are hard-excluded from the vocabulary (`STAGE2_compilation/instruction_tables/proposed/interleave_only.jsonc:177-178`; prefetch also `fv4_vocab.jsonc:113`). `clflush` appears only in the cache-setup prologue, before the window.

In the implementation, the only non-plain-load instruction that changes L1D/L2 transiently is the RMW, and it does so through `ldst`, a load micro-op at the RMW's single address.

## 3. Our data: are there CleanupSpec footprint events by non-load micro-ops?

**No.** Every transient L1D/L2 event in the CleanupSpec traces on disk comes from a load micro-op.

- **Trace scan.** The CleanupSpec traces in `experiments/2026-11-16_final/results/` are 35 traces: UV5 detections, `uv5verify` reruns, `uv5why` RMW vs plain-load runs, and `fp_equiv` round-1 tests incl. RMW tests. For each L1D/L2 `miss/fill/hit/repl_touch/evict/upgrade` event, the scan took the actor seq, its micro-op from the O3PipeView fetch line, and whether the event came before the actor retired (or the actor never retired). Transient events by micro-op: `ld` 3,064, `ldis` (POP) 683, `ldst` (RMW load half, `req=st`) 89, `ldfp` 24. There were **0 events by `st` or any other non-load micro-op**. Scripts: `scripts/cs_loads_only_20261116/scan_transient_uops.py` and `scan_unknown_seqs.py` (run from `experiments/2026-11-16_final/results/` as `python3 -I <script> $(find . -name '*.pipeview.txt.gz' | grep -v /race/)`).
- **Events whose seq has no pipeview record** (W-3's "unknown" class): 103. In 78, both neighbouring seqs retired before the event, so these are post-commit store writebacks (e.g. inst-061878 seq 3138, `MOV_M_I` at 0x404425, after 3137 retired at 17448000; inst-012528_c1 seq 3160). They are not squashed, so `check_footprint`'s `squashed_after_lc` actor rule never counts them. The other 25 have squashed neighbours. They are in-flight squashed **loads**, which never emit a pipeview record (`gem5_common.parse_lsq` docstring): inst-012528_c1 seq 3301 sits between `OR_M_I : limm` (3300) and `OR_M_I : st` (3303) at pc 0x404440, so it is the RMW's `ldst`; inst-023722_c2 seq 3260 at pc 0x404475 is `MOV_R_M : ld`.
- **Attribution of the main-corpus CleanupSpec run** (`experiments/2026-11-16_final/results/bigcorpus/cafe3/firstdet/T2g_Footprint_6_u_nov10_s2A/classes_rmw.jsonl`, 440 hits). Every non-load-looking cause is an RMW: UV3 261, EM_rmw 62, UV3_other_actor 39 (S = another RMW in the test), EM_other 25, UV3_padding 5 (the H-PAD `ADD_M_R` past `.text`). The rest are UV4 32, CS1 1, unattributed 25 and no_evidence 16. Each RMW footprint is the `req=st` fill or E→M upgrade of the RMW's `ldst` (e.g. EVAL_MANIFEST:1338, inst-021207: `L1D:miss … req=st msg=ST ev=Store`, `L2:miss … GETX`, then `cleanup_skip … why=nohitinfo`; the trace above shows that actor as `OR_M_I : ldst`, squashed).
- **Why W-3 split the defenses, then.** W-3 (claudelog 2026-11-16 15:45) was motivated by InvisiSpec. All 1,500 T1 hits there were "squashed `req=st` L1D/L2 fills plus DTLB touches" (EVAL_MANIFEST:953). For CleanupSpec, W-3 changed nothing in practice. Its criterion stayed "any transient instruction", and the code and traces show that set equals "load micro-ops" on this build. `is_load_micro_op` counts `ldst` as a load (`STAGE3_gem5/gem5_common.py:627-631`), so even a load-only filter on CleanupSpec would keep every UV3/EM_rmw actor. Caveat: the per-hit raw records keep no micro-op text, so this is shown on the 35 stored traces plus the code, not record by record over all 291,860 tests. Re-scoring the CleanupSpec rows with `"op_class": "load"` and checking that verdicts do not change would make it exhaustive, but that needs the traces on the nodes.

## 4. Conclusion

(a) **Sentence: correct, but tighten it.** Use Option A above (or B). The fixes: (i) say "by design", because the implementation's RMW sends its ownership request speculatively (A-UV3); (ii) cite clflush's delay (§3.5) next to the RFO (§4), since the RFO alone does not justify "only through loads"; (iii) optionally say an RMW changes the cache through its load half, which links the contract to A-UV3.

(b) **Alloy: no CleanupSpec-specific model.** By the paper, stores, clflush and prefetches do not change the data caches transiently. In the code, plain stores write after commit, there are no SE-mode walks, the prefetcher is off and fetch goes to the L1I. In the data, every transient L1D/L2 event comes from a load micro-op. The one non-load instruction class that leaks, the RMW, leaks at the address of its load half. That address is `Loads.inaddr` in the shared model, and Stage 2 concretizes a model load as `load_rmw_or0` (`fv4_vocab.jsonc:8-9`). A leakage function with `Stores.inaddr` would add tests whose store transmitter cannot touch L1D/L2 before commit. Under CleanupSpec's L1D/L2 criterion every such test is a guaranteed no-hit (its only transient footprint is a DTLB lookup, and the TLB is out of scope by §2.1), so it would cost Stage 1 time and find nothing. `CleanupSpec_6.als:345-350` already gives this reasoning (p3 threat model, p8 RFOs, RMW via the Stage-2 rewrite).

Hard decisions for Anna: **DECIDE CS-LO-1**, Option A vs B vs keep the current text (my recommendation is A). Optional: re-score the CleanupSpec rows with a load-only actor filter to confirm the "no non-load actor" result record by record, rather than on 35 traces plus the code.

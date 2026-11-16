# Checker and classifier fix proposals (2026-11-10, checker-proposals)

**Status: proposals only. No checker, classifier, diagnostic, harness, spec or `parsexml.py` code was changed.** Written for Anna to review on her return (URGENT_TODO 'fix the checkers later'). Every count below comes from read-only scans of existing results on cafe2/cafe3 (scan scripts were throwaway; the commands are described so they can be rerun). Nothing was started. One timing probe for item 3 was refused by the permission system as interfering with running workloads, so item 3 has no measured speed-up.

## Summary

| # | Item | Effect on existing results | Changes a reported SimSpect-vs-AMuLeT multiple? | Needs Anna |
|---|---|---|---|---|
| 1 | InvisiSpec `check_footprint`: D-1 as its own class; Futuristic actor = loads only; no-pipeview actors 'unknown' instead of vp=inf | T1g raw hits 4000 → about 2002 (every warm hit in a 59-test sample is artifact-only); E12a fv2 3744 → about 3384; E12b loses its 348 D-1-only hits from the raw count | No: UV1 K = 2002/4000 is unchanged (all UV1 events are spec-load evictions by loads) | Yes: criterion change (`specs/leakage/invisispec.json`) + DECIDE C1-a/b |
| 2 | `check_ld` on RMW transmitters: score the LSQ micro-op, gate whenever LSQ records exist | E3/E4 2%: 114 RMW raw hits → not hits (not_taken); E2 8+8, E6 3+3 likewise; RMW `store_forward` labels on Recon builds may flip (needs a rerun) | No (STT/ReCon are not in the comparison) | Global checker fix (existing DECIDE) |
| 3 | UV1 classification: stop rebuilding each binary per hit | None by design (byte-identical `classes.jsonl` is the acceptance test) | No | Routine; approve the harness field |
| 4 | CleanupSpec: credit an `under_clean` victim to the cause of the fill that evicted it (CF-2) | T2g: 96 `unattributed` → 0 (91 UV3, 5 UV3_padding); T2rt 54 → 0 | No: every such hit is already UV3 or UV3_padding, so K does not move | Close CF-2 |
| 5 | `diag_recon_oldest_taint`: gem5-side R-SA-8 signature (catches the x86 `mov` false dependency) | E2 fv3 br_x inst-016600 (both modes) NEW → R-SA-8; others unknown until the new evidence runs | No | DECIDE E2LT-2 first |
| 6 | Widen `diag_recon_stlf_bypass` to gem5-recon-ruby3 | E6 fv3 2%: 32 of 43 twin-hit ld keys NEW → A2; E6 `Recon_6_u_base`: 20/20 | No | RL-9 (source check now done: `src/cpu/o3` identical) |
| 7 | Slice tool: model `idiv`/`div`/`cqto`/one-operand `mul` implicit operands | Recon fv3: 70/26,506 slices change (incl. inst-001501, inst-003549 → R-SA-13); STT fv3 32/26,954 (8 gain xmm4) | No | Routine fix to a shared helper |
| 8 | Disqualifier for ReCon reveal-through-concretization; Stage-2 sketch | E6 twin inst-021056, inst-021429 NEW → disqualified; Stage-2 fix would change every regenerated corpus | Diagnostic: no. Stage-2 fix: possibly (it could lower the UV5 precondition rate in a regenerated footprint corpus) | Yes: E2LT-3 + new DECIDE CP-8 below |

Hard decisions surfaced here (also listed at the end): C1-a (what InvisiSpec's raw hit means), C1-b (loads-only Futuristic actor), CP-5 (R-SA-8 gem5 signature strictness), CP-8 (is a correct-looking reveal a disqualifier, and how far the Stage-2 fix reaches).

## 1. InvisiSpec `check_footprint`: raw hits saturate

### Problem and evidence

- **Saturation.** T1g (AMuLeT-parity InvisiSpec-Futuristic, final protocol, cafe3 `firstdet_final/T1g_Footprint_6_u_core_lpP_fv3`) has 4000 raw hits in 4000 tests. `classes.jsonl`: `UV1+UV1_transient` 2002, `other_DIR+other_DTLB+other_L1D+other_L2` 1988, `other_DTLB+other_L1D` 10. E12a fv2 (shrunk config) is 3744/3744, UV1 3384 (EVAL_MANIFEST line 68).
- **What the non-UV1 hits are (new scan, 120 T1g hits, seed 1110, each offending event re-derived from the kept trace with `check_footprint.TraceModel`).** All 59 sampled `warm` hits are artifact-only. Their offending events are exactly three kinds: (a) D-1, `DTLB:repl_touch` (36,737 events in the 120 tests); (b) events by seqs with no O3PipeView record that were never squashed, every one with `req=st` (L1D `repl_touch`/`fill`, L2 `fill`, DIR `coh`: about 1,400 events in the 59 warm tests), which get vp = ∞ (`check_footprint.py:157-168`); (c) one `DTLB:fill` per test by the harness call's `stis` micro-op (pc 0x401000 upc 2, a retired store, vp basis `rob_head`; the 'E12a NEW br_x' seq 3 of `SOURCE_AUDIT_INVISISPEC.md`). All 61 sampled `full` hits also carry real UV1 events (`L1D:evict req=specld` by squashed test loads, 84 + 13 events), plus SETUP-block load events (71,363) that only `classify_hits.py` strips.
- **So both artifacts are store actors.** The Futuristic actor accepts any instruction (`check_footprint.py:218-224`, `impl == "before_visibility_point"` returns True; `invisispec.json` futuristic text "Any instruction counts"), and tests only `tick < vp(seq)`. A store with a pipeview record is flagged until it reaches the ROB head; a store with no record is flagged forever.
- **Does InvisiSpec's guarantee cover DTLB replacement state?** Yes, explicitly. §VI-E3, PDF p9-10 (`~/Documents/quail/sources/papers/yan-2018-invisispec.pdf`): "Second, on a D-TLB hit, any observable TLB state changes such as updating D-TLB replacement state or access/dirty bits are delayed to the USL's point of visibility." §III-B p3 also lists "data TLB state (e.g., what entries live in the TLB)". (p4 itself only defines USLs and the visibility point; the DTLB sentence is on p9-10.) So D-1 is a real implementation deviation (`arch/x86/tlb.cc` bumps `lruSeq` on a speculative hit), already known and bucketed by `diag_invisispec_d1_dtlb.py`; it should not be dropped from the criterion, only kept out of the raw count.
- **Stores are not USLs.** §IV-A1 p4 defines Futuristic USLs as "all the speculative loads that can be squashed by an earlier instruction", and §VI p9 says of stores "InvisiSpec does not execute them speculatively". `invisispec.json` itself says "Futuristic USL = every squashable load" and then "Any instruction counts", which contradict each other.

### Proposed change

Three parts. Part A is a criterion (spec) change, B and C are checker changes. All keep the current verdict available as a new field so old numbers stay reproducible.

```diff
--- specs/leakage/invisispec.json
+++ specs/leakage/invisispec.json
@@ "actors": { ... "modes": { ... "futuristic": {
-        "text": "footprint e by instruction i (e.seq) with e.tick < vp(i), ... Any instruction counts (Futuristic USL = every squashable load), committed or squashed.",
+        "text": "footprint e by LOAD i (e.seq) with e.tick < vp(i), ... Only loads count (§IV-A1 p4: USLs are speculative loads; §VI p9: stores are not executed speculatively). i is a load iff some SimSpect event of seq i carries req in load_reqs; a seq with no req evidence is 'unknown'.",
         "impl": "before_visibility_point",
+        "actor_reqs": ["ld", "specld", "expose", "validate"],
+        "no_record": "unknown",
@@ top level
+  "known_deviations": [
+    {"id": "D-1", "struct": "DTLB", "kinds": ["repl_touch"],
+     "why": "tlb.cc updates lruSeq on a speculative hit; paper §VI-E3 p9-10 delays it to the visibility point. Real, known, reported as its own class (diag_invisispec_d1_dtlb.md)."}
+  ],
```

```diff
--- STAGE3_gem5/check_footprint.py
+++ STAGE3_gem5/check_footprint.py
@@ class TraceModel.__init__
+        # seq -> set of request kinds seen on any of its events (DTLB:fill has no req,
+        # but the same seq's DTLB:miss translate line does; SIMSPECT_HOOKS.md)
+        self.reqs = defaultdict(set)
+        for e in self.events:
+            if e["seq"] is not None and e.get("req") not in (None, "-"):
+                self.reqs[e["seq"]].add(e["req"])
@@ def vp(self, seq)
-        res = min(cands) if cands else (INF, "never")
+        if cands:
+            res = min(cands)
+        elif seq not in self.pv and self.squash_of(seq) is None:
+            res = (None, "unknown")    # no pipeview record and never squashed: committed
+                                       # but unrecorded (e.g. prologue stores) or in flight at end
+        else:
+            res = (INF, "never")       # squashed (transient): legitimately never visible
@@ def evaluate(...)
+    known = crit.get("known_deviations", [])
+    def known_dev(ev):
+        return next((k["id"] for k in known
+                     if ev["struct"] == k["struct"] and ev["kind"] in k["kinds"]), None)
+    actor_reqs = set(mode.get("actor_reqs", []))
     def is_actor(seq) -> bool:
         ...
         if impl == "before_visibility_point":
-            return True       # per-event test below
+            if not actor_reqs:
+                return True   # old criterion: any instruction
+            r = tm.reqs.get(seq, set())
+            return bool(r & actor_reqs)          # stores (req st/wb only) are not actors
     def actor_event_in_window(ev) -> bool:
         if impl == "before_visibility_point":
-            return ev["tick"] < tm.vp(ev["seq"])[0]
+            t, basis = tm.vp(ev["seq"])
+            if basis == "unknown":
+                return None                       # undecided, reported separately
+            return ev["tick"] < t
@@ def _eval_exists(...)
-    inw = [e for e in foot if in_window(e)]
+    dec = [(e, in_window(e)) for e in foot]
+    undecided = [e for e, w in dec if w is None]
+    inw_all = [e for e, w in dec if w]
+    inw_known = [e for e in inw_all if known_dev(e)]
+    inw = [e for e in inw_all if not known_dev(e)]
     ...
-    return dict(leak=bool(inw), in_window=bool(inw), decided=True,
+    return dict(leak=bool(inw), in_window=bool(inw_all), decided=True,
+                leak_incl_known=bool(inw_all),                 # = today's verdict (modulo actors)
+                known_deviations_fired=sorted({known_dev(e) for e in inw_known}),
+                offending_known=_group(inw_known, term.get("key")),
+                undecided_actor_events=_group(undecided, term.get("key")),
                 ...
```

`unknown` events never make a hit and never hide one: they are listed in `undecided_actor_events` with their seq so triage can see them. A record whose only in-window footprint is unknown stays `leak: false` but `n_undecided > 0` (add that counter to the summary). A known deviation is still reported (`known_deviations_fired: ["D-1"]`) and counted by `diag_invisispec_d1_dtlb` as today. Optional part D (only if Anna wants raw hits under `full` to be meaningful too): move `classify_hits.strip_setup`'s SETUP-block rule into the checker as one more 'excluded' class, because the setup sweep's committed plain loads are loads and stay actors under part A.

### Results that would change

- T1g: raw hits 4000 → about 2002 (the UV1 tests). Sample: 59/59 warm hits lose every offending event (D-1, unknown, or store actor); 61/61 full hits keep their UV1 events. Without part D the full tests stay raw hits through SETUP events, which is the same set.
- E12a fv2/fv2fp: 3744 → about 3384/3386 (the 348 'NEW br_x' stems are D-1 + store actor, `SOURCE_AUDIT_INVISISPEC.md` 'E12a NEW br_x'). E12b fv2/fv2fp: the 348 D-1-only stems leave the raw count and stay visible as `known_deviations_fired`.
- Direction: fewer raw hits, no new hits. UV1 cannot be lost: every UV1 event is an `L1D:evict req=specld` by a load (squashed test loads keep vp = ∞, the 9 sampled UV1 events by committed loads keep vp = rob_head).

### Tests to add (`STAGE3_gem5/tests/test_check_footprint.py`, TestInvisiSpec)

- `test_futuristic_store_is_not_actor`: a retired store (req=st) filling L1D before its rob_head → no leak under the new criterion, leak under a copy without `actor_reqs` (old behaviour).
- `test_futuristic_no_record_unsquashed_is_unknown`: event by a seq with no `inst()` record and no covering squash → `leak False`, appears in `undecided_actor_events`.
- `test_futuristic_no_record_squashed_still_never`: same seq but younger than a ROB:squash → vp `(inf, "never")`, a specld evict by it leaks (protects UV1_transient).
- `test_dtlb_fill_takes_req_from_miss`: `DTLB:miss req=ld` then `DTLB:fill` (no req) by the same seq → actor; with `req=st` → not.
- `test_d1_known_deviation`: only `DTLB:repl_touch` in window → `leak False`, `leak_incl_known True`, `known_deviations_fired == ["D-1"]`.
- Real-trace regression: rerun the offline mode (`--trace`) on the three E12a traces in cafe2 `bugwork/e12anew/traces/` and on 20 T1g UV1 traces; expect E12a → no leak, T1g → leak with the same offending UV1 items.

### Reported numbers

No multiple changes: A-UV1 (1,620x) uses `classify_hits` UV1, K = 2002 of 4000, which this does not touch. What changes is the 'hits' column of any table that shows InvisiSpec raw hits (4000/4000 → about 2002/4000, warm → 0), and the DECIDE (timing-amulet) item about 1500 InvisiSpec non-UV1 timing hits, which this explains: they are D-1 + store actor, not a window artifact.

## 2. `check_ld` on RMW transmitters

### Problem and evidence

- Root cause (claudelog 'audit-fanout-1109'; `ALLOY_MODEL_CHANGES.md:849`): `check_ld.py:87` falls back to `xmit_complete` from `best_record` over every micro-op at the xmit pc (`gem5_common.py:822-836`; `parse_pipeview` drops upc and seq). For an RMW (`OR_M_I`/`ADD_M_I`), the leading `limm` completes even when STT delays the `ldst`. The data-obtained gate runs only when `xmit_execute > 0` (`check_ld.py:145`), so a `never_executed` RMW is never gated.
- New scan of the 2% fv3 campaigns (cafe3 `loosepin_regen/code_eval/results/E{2,3,4}_STT_6_u_core_lpP_fv3__latest`, cafe2 `E6_Recon_6_u_core_lpP_fv3__latest`, all `_sweep_raw/*check_ld*.json`, RMW stems from the corpus `rmw_stems.tsv`):

| campaign, mode | RMW tests | RMW raw hits | of which `never_executed` (would drop) | plain-ld raw hits `never_executed` |
|---|---|---|---|---|
| E3 stt-master nt / t | 125 / 126 | 123 / 9 | 114 / 0 | 0 / 0 |
| E4 amulet-STT nt / t | 125 / 126 | 123 / 9 | 114 / 0 | 0 / 0 |
| E2 Recon-STT nt / t | 125 / 126 | 125 / 126 | 8 / 8 | 0 / 0 |
| E6 ReCon nt / t | 127 / 127 | 121 / 121 | 3 / 3 | 0 / 0 |

- The fix touches only these: every `never_executed` raw hit is an RMW test. (The '99/107' figure in the task brief was not found in any doc or result; the table above is the current 2% data.) T4 amulet-STT on the old corpus: 206/470 hits `never_executed`, 205 of them RMW (EVAL_MANIFEST line 662).
- Second effect, same root cause: for an RMW that executed but sent no packet, `store_forward` is decided by `xmit_complete > 0` from the same pc-wide record, which may be the `limm`'s or the `st`'s completion, not the `ldst`'s. On the Recon builds this is every RMW hit (E2 117/118, E6 118/118 are `store_forward`) because those builds never print the packet line, so `reached_cache` never appears (E2 2%: 452 `store_forward`, 142 `executed_no_packet`, 34 `never_executed`, 0 `reached_cache`; E6: 500/166/18/0). That is the separate, open `wiki/findings/bug/recon_cache_reach_gate/README.md`; this proposal does not fix it, but makes the completion tick at least belong to the right micro-op.

### Proposed change (option (a) of the existing DECIDE)

```diff
--- STAGE3_gem5/check_ld.py
+++ STAGE3_gem5/check_ld.py
-from gem5_common import best_record, check_branch_resolutions, run_batch
+from gem5_common import best_record, check_branch_resolutions, parse_pipeview_by_seq, run_batch
+
+
+def _mem_uop_record(trace_path, lsq_by_pc, xmit_pc):
+    """Pipeview record of the xmit's MEMORY micro-op: the record whose seq is one of the
+    LSQ sn's at xmit_pc (parse_lsq keeps sn). (rec|None, sns). For an RMW this is the ldst,
+    never the leading limm."""
+    sns = {r["sn"] for r in (lsq_by_pc or {}).get(xmit_pc, []) if r.get("sn") is not None}
+    if not sns or trace_path is None:
+        return None, sns
+    by_seq = parse_pipeview_by_seq(trace_path)
+    cands = [by_seq[s] for s in sns if s in by_seq]
+    return (best_record(cands) if cands else None), sns
 
-def check_ld(by_pc, xmit_pc, lc_pc, fnc_pc, unresolved, ticks_per_cycle, lsq_by_pc=None, squash_by_pc=None):
+def check_ld(by_pc, xmit_pc, lc_pc, fnc_pc, unresolved, ticks_per_cycle, lsq_by_pc=None,
+             squash_by_pc=None, trace_path=None):
     xmit_rec = best_record(by_pc.get(xmit_pc, []))
+    mem_rec, mem_sns = _mem_uop_record(trace_path, lsq_by_pc, xmit_pc)
@@
-    xmit_complete = xmit_rec["complete"] if xmit_rec else 0
+    # With LSQ records, the completion that matters is the memory micro-op's (RMW: ldst).
+    # No pipeview record for that sn (in-flight squashed load): unknown, not 0.
+    if mem_sns:
+        xmit_complete = mem_rec["complete"] if mem_rec else None
+    else:
+        xmit_complete = xmit_rec["complete"] if xmit_rec else 0
-    xmit_signal   = xmit_execute if xmit_execute > 0 else xmit_complete
+    xmit_signal   = xmit_execute if xmit_execute > 0 else (xmit_complete or 0)
@@
     elif cache_fate == "executed_no_packet":
-        data_obtained = xmit_complete > 0            # SLF forward-completion
+        if xmit_complete is None:
+            data_obtained = None                     # sn has no record: leave UNGATED (never hide)
+        else:
+            data_obtained = xmit_complete > 0        # SLF forward-completion of the mem uop
         if data_obtained:
             cache_fate = "store_forward"
@@
-    gated = in_window and (xmit_execute > 0) and (data_obtained is not None)
+    # Gate whenever the LSQ saw the xmit pc (fate is not None): a never_executed load is
+    # never a leak, whatever micro-op's tick put it in the window.
+    gated = in_window and (fate is not None) and (data_obtained is not None)
@@ criteria
-        data_obtained=(bool(data_obtained)
-                       if xmit_execute > 0 and data_obtained is not None else None),
+        data_obtained=(bool(data_obtained) if fate is not None and data_obtained is not None else None),
@@ return dict(
+        xmit_mem_seq=(mem_rec or {}).get("seq"), xmit_mem_upc=(mem_rec or {}).get("upc"),
+        xmit_mem_record_missing=bool(mem_sns) and mem_rec is None,
@@
+check_ld.wants_trace = True   # gem5_common.process_one then passes trace_path (additive, :1251-1255)
```

Also `pipeline.py:313-320`: add `"rmw": "check_ld.py"` (today it falls back to check_ld anyway). The `check_ld_*` variants that import `check_ld` inherit the fix; check each one's call signature.

### Results that would change

- Fewer hits, never more. 2% fv3: E3 and E4 lose 114 not_taken RMW raw hits each (already shown as `disq_not_obtained(never_executed)` by `eval_gate.py`, so the gated numbers in EVAL_MANIFEST do not move); E2 loses 8+8, E6 3+3 (same, already gated out by `eval_gate.py`). T4 amulet-STT (old corpus): 206 of 470 hits.
- Unknown direction, needs a rerun: the RMW `store_forward` hits on the Recon builds (E2 235, E6 236 keys at 2%), because the raw records do not keep per-seq completion. A record can flip to not-a-leak (ldst never completed) or to ungated (ldst has no record).
- Plain loads: identical by construction when the xmit pc has one micro-op; the acceptance test below checks it.

### Tests to add

- New `STAGE3_gem5/tests/test_check_ld.py` with synthetic `by_pc`/`lsq_by_pc` and a tiny pipeview file: (1) RMW, limm complete at T in window, ldst LSQ record with no execute → `issued_in_window False`, `cache_fate never_executed`; (2) RMW, ldst executed, no packet, ldst record complete > 0 → `store_forward` leak, and `xmit_mem_upc` is the ldst's; (3) ldst executed, no packet, no pipeview record for its sn → ungated (verdict = `in_window`), `xmit_mem_record_missing True`; (4) plain load with one micro-op → verdict identical to the old function on the same inputs.
- Acceptance: offline re-score of kept traces. `/work/stt` RMW sample: 309 → 0 artifacts (ALLOY_MODEL_CHANGES 3.4); one non-RMW campaign with traces (e.g. the e2_losttaint traces): identical verdicts.

### Reported numbers

None of the SimSpect-vs-AMuLeT multiples (STT is out of the comparison, URGENT_TODO 'DECIDED 2026-11-09'). It removes the need for `eval_gate.py`'s separate gate on STT builds and makes raw `window-results.json` hit counts equal the gated ones for RMW tests.

### Addendum (2026-11-10 17:10, recon-rmw): the RL-10 'RMW obtained data while tainted' class on ReCon is this artifact, not a defense bug

**Verdict: checker artifact (check_ld scores the RMW's leading `limm` micro-op).** The Recon-group STT delay unit holds the RMW's `ldst` micro-op correctly; it never sends a cache request and never completes. Nothing in gem5 needs fixing for this class. URGENT_TODO RL-10 is closed by this; the fix is this item's existing proposal.

**Faithful reruns.** 14 RMW tests on gem5-recon-ruby3 with the E6 config verbatim (`runconfigs/twostage_lp/eval_20261110/E6_Recon_6_u_core_lpP_fv3.jsonc`, same timing-grid point, BTB force, `TMPDIR=/tmp`), extra flags `LSQUnit,DelayUnit,Commit,O3PipeView,DelayDebug`: inst-000847, inst-000711, inst-001007, inst-011193 in both modes, and six from the 'no signature' remainder below (inst-007123, inst-008465, inst-009338 not_taken; inst-003001, inst-011170, inst-012691 taken). All 14 reproduce the hit (`issued_in_window true`, `cache_fate store_forward`) and all 14 have the same micro-op picture. Work dir cafe2 `/tests/simspect_alloy_20261108/bugwork/recon_rmw/` (`run.py`, `uop_table.py` → `uop_table.json`, `scan_e6.py`/`scan_ev.py` → `.txt`, `logs/`; gem5 workdirs under `/tmp/recon_rmw/`).

**What gem5 did (inst-000847, not_taken, xmit `orq $0, (%r10,%rdx)` at 0x401c52 = `OR_M_I`):**

| sn | upc | micro-op | issue | complete | LSQ / delay unit | cache send |
|---|---|---|---|---|---|---|
| 566 | 0 | `limm t2, 0` | 3036000 | **3036500** | (not a memory op) | n/a |
| 567 | 1 | `ldst t1, DS:[rdx + r10]` | 3037000 | 0 | `Executing load` 3037500, `STL_CHECK isTainted=1 isSpeculative=1`, `Doing memory access`, then `Inserted tainted load [sn:567] into delay_unit` 3037500; never released; squashed 7981000 | none (`Memory request ... was sent` appears 264 times in the trace, never for sn 567) |
| 568 | 2 | `or t1, t1, t2` | 0 | 0 | | |
| 569 | 3 | `st t1, DS:[rdx + r10]` | 0 | 0 | squashed 7981000 | none |

check_ld's record: `xmit_execute 3037500` (the ldst's LSQ execute), `xmit_complete 3036500` = the `limm`'s completion, which is earlier than the load's own execute. `_xmit_cache_fate` returns `executed_no_packet` (the delay-unit bounce), and `check_ld.py:139` turns it into `store_forward` because `xmit_complete > 0`. The other 13 runs are identical in shape (limm completes, ldst bounced into the delay unit at its execute tick and never completes, or/st never issue); in all 14 `xmit_complete` equals the limm's pipeview complete tick.

**Why the STT builds show `never_executed` instead.** Upstream STT (`/work/stt-master/src/cpu/o3/lsq_unit_impl.hh:1013`, `inst->fenceDelay(inst->isArgsTainted())`) blocks a tainted load at issue, so the ldst never reaches the LSQ's `Executing load` and the fate is `never_executed` (then left ungated by `check_ld.py:145`, the first half of this item). ReCon's STT issues the ldst and bounces it after `Doing memory access` (`/work/gem5-recon-ruby3/src/cpu/o3/lsq_unit.cc:2094-2105`, `isTaintedInst` → `clearIssued(); delayUnit.insertTaintedLoad(load_inst); return NoFault;`), which gives `executed_no_packet`, and the pc-wide completion of the limm relabels it. Same defense behaviour, two different checker paths.

**Not the recon_cache_reach_gate bug.** That bug hides real sends; here the ldst sent nothing, and the run positively shows it (Recon's own `was sent` print is enabled under `LSQUnit` and absent for the ldst).

**Scope (read-only scans of the raw records).** The RL-10 evidence set (regen-lp `bugwork/e6_stlf/recon_stlf_evidence.json`: RMW, `isTainted=1`, no forward, no ready-within-ROB) is 302 not_taken / 298 taken records; every one has `xmit_complete <= xmit_execute` (268 / 265 strictly less, 34 / 33 equal, the equal case traced above: limm completes in the same tick the ldst is bounced). E2 (Recon-STT on gem5-recon-modded, `STT_6_u_core_lpP_fv3`, cafe3 raw records, not rerun): 292 / 291 RMW `store_forward` hits with `xmit_complete <= xmit_execute`, same signature, same `src/cpu/o3` (RL-9 diff), so almost certainly the same artifact. Not covered by this addendum: the E6 RMW hits with a real store forward (`fwd ready`, 60 / 59, the known A2 `diag_recon_stlf_bypass` class) and the E2/E6 RMW `store_forward` hits whose `xmit_complete > xmit_execute` (not traced; the item 2 fix decides them on the ldst's own record).

**Fix.** This item's proposed `_mem_uop_record` change already handles it: the ldst's record (sn from the LSQ) has `complete 0`, so `data_obtained = False` and the hit drops. No new checker change needed. Optional interim disqualifier until item 2 lands (not written): on Recon builds, an RMW transmitter with `cache_fate == store_forward` and `0 < xmit_complete <= xmit_execute` is this artifact. I believe that signature is safe (a forwarded ldst completes at least a cycle after its execute), but by the 100%-certain rule it should be checked against per-seq records before it hides anything, so the better route is the item 2 fix plus a rerun.

## 3. UV1 classification rebuilds each binary per hit

### Problem and evidence

`classify_hits._classify_one` calls `text_end()` for every hit when `--testset` is given (`classify_hits.py:57-66`): it runs `gem5_common.build_binary` (two `as`, one `ld`) into a temp dir and `objdump -h` to find the end of `.text` for the H-PAD rule, then adds `cache_setup_info.delta`. T1g classifies 4000 hits this way (5 classify passes in its `classify.log`). Each hit also gunzips its trace and parses it two or three times (`parse_simspect_events`, and `parse_pipeview_by_seq` in both `sigs_invisispec` and `strip_setup`). I could not time it: a short probe on cafe3 was refused as interfering with running workloads.

### Proposed change

```diff
--- STAGE3_gem5/gem5_common.py   (process_one, after cache_setup.prepare and resolve_pc)
+        # 2026-11-xx: end of .text of the binary that actually ran (H-PAD rule in
+        # timing/classify_hits.py), so classifiers need not rebuild it.
+        result["text_end"] = hex(_text_end(binary))
+
+def _text_end(binary):
+    out = subprocess.check_output(["objdump", "-h", str(binary)], text=True)
+    m = re.search(r"^\s*\d+\s+\.text\s+([0-9a-f]+)\s+([0-9a-f]+)", out, re.M)
+    return int(m.group(2), 16) + int(m.group(1), 16)
```

```diff
--- STAGE3_gem5/timing/classify_hits.py
-def text_end(testset, mode, stem, raw, gc) -> int:
+_TE_CACHE = {}
+def text_end(testset, mode, stem, raw, gc) -> int:
+    if raw.get("text_end"):                       # recorded at run time: exact, no rebuild
+        return int(raw["text_end"], 16)
+    k = (str(testset), mode, stem, (raw.get("cache_setup_info") or {}).get("delta"))
+    if k in _TE_CACHE:
+        return _TE_CACHE[k]
     ... (unchanged rebuild) ...
+    _TE_CACHE[k] = end + delta
+    return _TE_CACHE[k]
@@ _classify_one
-    pv = gunzip_tmp(gz)
+    pv = gunzip_tmp(gz)
+    byseq = gc.parse_pipeview_by_seq(pv)          # parse once, pass to sigs_invisispec/strip_setup
```

For old runs (no `text_end` field) also write a sidecar `<out>/text_end.json` the first time, so incremental passes stop rebuilding. The run-time field is exact for the binary that ran (no warm-rebuild-plus-delta approximation).

### Results that would change

None intended. Acceptance test: classify T1g and T3g into copies of their output dirs with the new code and require `cmp classes.jsonl` to be byte-identical (and `first_detection.json` identical except timestamps); separately, on 50 records that have both, assert `int(raw["text_end"],16) == old text_end()`. If they differ, the delta approximation was wrong somewhere, which would itself be a finding (H-PAD exclusions are counted in `excluded_HPAD:*`).

### Tests to add

`STAGE3_gem5/tests/test_timing_driver.py` (or a new `test_classify_hits.py`): `text_end` returns the recorded field without calling `build_binary` (monkeypatch it to raise); the cache returns the same value on the second call; `_classify_one` on a fixture hit gives the same sigs with and without the field.

### Reported numbers

None.

## 4. CleanupSpec victim attribution (CF-2)

### Problem and evidence

`classify_cs_rmw.refine` (`classify_cs_rmw.py:119-139`) credits an `unattributed` `under_clean` item to UV3 only if every offending event is a `fill req=st` on the item's line. The victim item of the same UV3 install is an `evict` event (keyed by `victim`), so it stays `unattributed`. EVAL_MANIFEST diligence lines 445-446 explain it; this scan confirms it for every item.

New scan (cafe3 `firstdet_final/T2g_Footprint_6_u_core_lpP_fv3_merged`, `cs_evidence/diagnostics/cleanupspec_skip_evidence.json` + kept traces): 96 hits carry `unattributed`, all under `full`; 91 also carry `UV3`, 5 `UV3_padding`. For all 96 unattributed `under_clean` items, the item is a single `L1D:evict` whose `cause=` id (the fill that took the way, `SIMSPECT_HOOKS.md:18,56`) is a `fill req=st` by the same seq on the same line, i.e. the UV3 install itself (example nt inst-001446: `evict line=0xd5c0 victim=0x35c0 seq=1634 cause=10674`). T2rt merged: 54 hits, 51 UV3 + 3 UV3_padding, same shape.

### Proposed change

```diff
--- STAGE3_gem5/timing/classify_cs_rmw.py
@@ def main(), per hit, replace the single refine() pass by two passes
-            for v in ev[key]["variants"]:
-                for it in v["items"]:
-                    c, why = refine(it, rec, tr, is_rmw, max_ann)
-                    items.append(...)
+            for v in ev[key]["variants"]:
+                refined = [(it, *refine(it, rec, tr, is_rmw, max_ann)) for it in v["items"]]
+                # event id -> cause of the item that owns that event (fills of credited items)
+                owner = {int(i): c for it, c, _ in refined if c != "unattributed"
+                         for i in it.get("event_ids") or []}
+                for it, c, why in refined:
+                    if c == "unattributed" and it.get("term") == "under_clean":
+                        c2, why2 = victim_of(it, tr, owner)
+                        if c2:
+                            c, why = c2, why2
+                    items.append(dict(struct=it.get("struct"), line=it.get("line"),
+                                      term=it.get("term"), cause=c, why=why))
+
+def victim_of(item, tr, owner):
+    """CF-2: an under_clean victim item whose every event is an evict, each caused (evict.cause =
+    the fill's id, SIMSPECT_HOOKS.md) by a fill owned by an item already credited to cause C,
+    is C's victim: -> (C + '_victim', why). Anything else: (None, '')."""
+    by_id = tr[0]
+    es = [by_id.get(int(i)) for i in item.get("event_ids") or []]
+    if not es or any(e is None or e["kind"] != "evict" or e.get("cause") in (None, "-") for e in es):
+        return None, ""
+    causes = {owner.get(int(e["cause"])) for e in es}
+    if len(causes) != 1 or None in causes:
+        return None, ""
+    c = causes.pop()
+    return f"{c}_victim", f"victim of fill id(s) {sorted(e['cause'] for e in es)} credited to {c}"
```

Count `UV3_victim` with UV3 (and `UV3_padding_victim` with the excluded padding bucket) in `first_detection_rmw.json`: add them to the alias map rather than to `TARGETS`, so K stays a per-test count.

### Results that would change

T2g merged: `unattributed` 96 → 0 (91 `UV3_victim`, 5 `UV3_padding_victim`); T2rt merged 54 → 0; old T2f (CF-2's 14) → 0 by the same rule (EVAL_MANIFEST line 446: each unattributed line's actor equals the UV3 or padding actor). K(UV3) does not move, because every affected hit is already UV3 or UV3_padding. The 'other CleanupSpec classes' line (EVAL_MANIFEST line 403, `unattributed 96`) becomes 0.

### Tests to add

A fixture trace (3 lines: the UV3 `fill req=st` with id N, the `evict cause=N victim=V`, the `cleanup_skip why=nohitinfo`) plus an evidence JSON with the two items: expect `{"UV3", "UV3_victim"}`. Negative: an evict whose cause id belongs to no credited item stays `unattributed`; an evict whose cause is a UV4 fill becomes `UV4_victim`, not UV3.

### Reported numbers

None. CF-2 can be closed.

## 5. `diag_recon_oldest_taint` misses R-SA-8 through the x86 `Mov` micro-op

### Problem and evidence

`diag_recon_oldest_taint.is_known` requires `ann.fanout_v2.otb.applied` and `otb.xmit_pc == xmit.pc` (`diag_recon_oldest_taint.py:37-40`) and `KINDS = ("ld",)`. Recipe v3 turns OTB off, but R-SA-8 still fires: E2 fv3 br_x inst-016600 (both modes, main corpus and GPR twin). gem5's `Mov` is `DestReg = merge(SrcReg1, dest, op2, dataSize)` with `SrcReg1` = the destination (`arch/x86/isa/microops/regop.isa:702-704`), so `movq %rcx,%rax` also reads the old `rax`; `propagateTaints` keeps only the oldest source (`taint_tracker.cc:108-131`); the transmitter is released when that older load commits (`freeTaints`, `:136-141`; `delay_unit.cc:150-158`) while its real source is still under the held branch (`SOURCE_AUDIT_RECON.md` R-SA-8 'E2 fv3 br_x check'). The delay-unit release DPRINTF prints a pointer, so its `[sn:1]` is useless; the release must be matched by tick.

### Proposed change

A new evidence analyzer plus a second, gem5-side path in the diagnostic. The OTB path stays (it is the old evidence).

```diff
--- STAGE3_gem5/triage/rerun_hits_evidence.py
+def an_recon_release(stem, mode, wds, raws, rerun_hit, A):
+    """R-SA-8 gem5 signature (needs --extra-debug Commit,DelayUnit,LSQUnit).
+    xmit_seq: the xmit's dynamic seq (ld: LSQ 'Executing load PC (0x<xpc>' sn; br_x: the
+      BR resolve hook's seq at xpc).
+    inserted: 'Inserting {branch|load} [sn:xmit_seq] into delay_unit' tick.
+    released: first 'Released tainted {branch|load} ... from delay_unit' tick T_rel > inserted
+      (the sn in that line is a pointer; matched by tick, then by the xmit's next execute/
+      resolve_visible being >= T_rel).
+    freed_by: loads with 'Committing instruction with [sn:L]' at T_rel - c, c in {0, 1 cycle}
+      (freeTaints runs at commit), L < xmit_seq.
+    held: a resolve_hold branch whose resolve_visible > T_rel.
+    Output: dict(xmit_seq, inserted, released, freed_by=[{sn, pc}], held_visible, xmit_act_tick,
+      reproduced)."""
@@ ANALYZERS
-ANALYZERS = {"nda_fwd": ..., "recon_stlf": an_recon_stlf, ...}
+ANALYZERS = {..., "recon_release": an_recon_release}
```

```diff
--- STAGE3_gem5/triage/diag/diag_recon_oldest_taint.py
-KINDS = ("ld",)
+KINDS = ("ld", "br_x")
+@functools.lru_cache(maxsize=1)
+def _rel():
+    p = HERE / "recon_release_evidence.json"
+    return json.loads(p.read_text()) if p.exists() else {}
+
 def is_known(stem, xml_dir):
     ...
-    if not (otb.get("applied") and otb.get("xmit_pc") == ann.get("xmit", {}).get("pc")):
-        return False, "not an OTB-transmitter test"
+    if otb.get("applied") and otb.get("xmit_pc") == ann.get("xmit", {}).get("pc"):
+        ... (unchanged OTB path) ...
+    r = _rel().get(f"{MODE}/{stem}")
+    if not r or not r.get("reproduced") or not r.get("released") or not r.get("freed_by"):
+        return False, "not OTB and no release evidence"
+    sl = _fv2_slice.transmitter_slice(stem, md)            # data slice, with item 7's fix
+    slice_pcs = {p["pc"] for p in sl.get("producers", [])}
+    outside = [f for f in r["freed_by"] if f["pc"] not in slice_pcs]
+    ok = (outside and r["held_visible"] and r["released"] < r["held_visible"]
+          and r["xmit_act_tick"] and r["xmit_act_tick"] < r["held_visible"])
+    return (True, f"released at {r['released']} by commit of sn {outside[0]['sn']} (pc{outside[0]['pc']}, "
+                  f"not in the xmit's data slice) while branch held to {r['held_visible']}") if ok \
+           else (False, "release evidence incomplete")
```

DECIDE CP-5 (signature strictness, ties to E2LT-2): should 'outside the data slice' use the static slice (`_fv2_slice`, misses gem5-only dependencies by design, which is exactly what makes the `mov` case visible) or gem5's own taint source from the Rename trace (exact, but needs `Rename` flags and a parser)? Recommendation: static slice, because the point of the signature is 'released by a load the program's data flow does not depend on', and the Rename trace stays as the manual check.

### Results that would change

E2 fv3 2%: br_x inst-016600 (both modes) NEW → `real_bug:R-SA-8_oldest_taint`. Unknown until the analyzer runs: other E2/E6 br_x and ld hits whose release comes from a `mov`/merge micro-op false dependency (direction: fewer NEW, more R-SA-8; it never disqualifies). Ordering: `diag_recon_stlf_bypass` is ORDER 10, `diag_recon_oldest_taint` 12, `diag_recon_sse_load_producer` (R-SA-13) 15, so R-SA-8 would claim a hit before R-SA-13; check that this matches the primary label Anna picks in E2LT-1.

### Tests to add

`STAGE3_gem5/tests/test_recon_release.py`: feed `an_recon_release`'s parser the inst-016600 excerpt (cafe2 `bugwork/e2_losttaint/evidence_excerpts.txt` lines 242-254 + the commit and BR lines; copy into `tests/fixtures/`) → released 2927000, freed_by sn 569, held_visible 4178500 → known. Negative: the same excerpt with the commit of sn 569 removed → not known.

### Reported numbers

None (ReCon/Recon-STT are not in the comparison). It changes what 'OTB off' means for E2/E6 interpretation (R-SA-8 remains reachable), which E2LT-2 already covers.

## 6. Widen `diag_recon_stlf_bypass` to gem5-recon-ruby3

### Problem and evidence

The diagnostic is build-scoped to gem5-recon-modded in its docstring, `.md` ('Scope: build-specific, every gem5-recon-modded scheme-2 campaign'), `triage/diag/README.md:33,41`, and `specs/hit_categories.json` (`recon_slf` scope `builds: ["gem5-recon-modded"]`). On E6 (gem5-recon-ruby3) fv3 2%, 32 of 43 GPR-twin-hit ld keys carry its full signature, all reproduced (regen-lp; cafe2 `loosepin_regen/bugwork/e6_stlf/recon_stlf_evidence.json`; DECIDE RL-9), and on E6 `Recon_6_u_base` 20/20 hits did (`SOURCE_AUDIT_RECON.md` R-SA-9 'E6 ultimate check'). **Source check done for RL-9 (read-only, cafe2):** `diff -rq /work/gem5-recon-modded/src/cpu/o3 /work/gem5-recon-ruby3/src/cpu/o3` reports no difference; `lsq_unit.cc` sha256 `ae587dba…a5e6e7` in both; the forward (`lsq_unit.cc:1977` 'Forwarding from store') returns before the STT check as on modded.

### Proposed change

No code change in the diagnostic (its logic is build-agnostic). Scope edits plus installation:

```diff
--- STAGE3_gem5/triage/diag/diag_recon_stlf_bypass.py  (docstring)
-diag_recon_stlf_bypass.py — REAL BUG (known, A2): on /work/gem5-recon-modded
-scheme 2 (Recon-STT), ...
-ONE cause; build-specific (applies to every campaign on gem5-recon-modded, ...
+diag_recon_stlf_bypass.py — REAL BUG (known, A2/R-SA-9): on /work/gem5-recon-modded
+and /work/gem5-recon-ruby3 (src/cpu/o3 identical, checked 2026-11-10), scheme 2, ...
+ONE cause; build-specific (every campaign on either build, each with its own evidence file).
--- STAGE3_gem5/triage/diag/diag_recon_stlf_bypass.md, README.md:33,41: same scope sentence
--- specs/hit_categories.json  (needs approval: spec edit)
-      "scope": {"testsets": ["Recon_6"], "builds": ["gem5-recon-modded"]},
-      "diag": "diag_recon_slf.py",
+      "scope": {"testsets": ["Recon_6", "STT_6", "*_u_core_lpP_fv3"], "builds": ["gem5-recon-modded", "gem5-recon-ruby3"]},
+      "diag": "diag_recon_stlf_bypass.py",
```

Install: copy `diag_recon_stlf_bypass.{py,md}` and the campaign's own `recon_stlf_evidence.json` into `E6_Recon_6_u_core_lpP_fv3__latest/diagnostics/` (and `E6_Recon_6_u_base__latest`), then rerun `bucket_hits.py`. Note the registry still names the retired `diag_recon_slf.py`: a stale-source-of-truth item to clean up with this change.

### Results that would change

E6 fv3 2%: 32 ld keys NEW → `real_bug` (A2); E6 `Recon_6_u_base`: 20 (mode, stem) hits NEW → A2. Fewer NEW, no disqualifications.

### Tests to add

None for the logic. Add a scope check to the diagnostics README checklist: `bucket_hits.py` on E6 must report 0 matches for `diag_recon_stlf_bypass` when the evidence file is absent (it already returns 'no evidence').

### Reported numbers

None.

## 7. Slice tool misses `idiv`'s implicit operands

### Problem and evidence

`_fv2_slice.transmitter_slice` treats an instruction's last operand as its destination (`_fv2_slice.py:110-116`). For `idivq %rcx` that makes `rcx` (the divisor, a source) the 'destination', and it ignores the implicit `rdx:rax` inputs and the `rax`/`rdx` outputs; `cqto` has no operands and is skipped. In E6 inst-001501 (mispredict_not_taken), the xmit `movq (%rsi,%r10),%rdi` depends on `r10 ← rax ← idivq %rcx`, `rcx ← rdi ← xmm13 ← movq (%rsi,%rdi),%xmm13` (an SSE load), but the walk skips the `idivq`, so the slice reports GPR-only (`SOURCE_AUDIT_RECON.md` 'E6 fv3 isTainted=0' (3)). The task wording 'implicit divisor' is slightly off: the divisor is explicit; the bug is that the explicit source is mistaken for the destination and the implicit destinations are missed.

### Proposed change

```diff
--- STAGE3_gem5/triage/diag/_fv2_slice.py
+# x86 instructions with implicit register operands: mnemonic -> (implicit uses, implicit defs).
+# Any explicit operand is a SOURCE (a memory operand makes it a load-op producer).
+IMPLICIT = {
+    "cqto": ({"rax"}, {"rdx"}), "cqo": ({"rax"}, {"rdx"}), "cltd": ({"rax"}, {"rdx"}), "cdq": ({"rax"}, {"rdx"}),
+    "cltq": ({"rax"}, {"rax"}), "cdqe": ({"rax"}, {"rax"}),
+    "idivq": ({"rax", "rdx"}, {"rax", "rdx"}), "divq": ({"rax", "rdx"}, {"rax", "rdx"}),
+    "idivl": ({"rax", "rdx"}, {"rax", "rdx"}), "divl": ({"rax", "rdx"}, {"rax", "rdx"}),
+    "mulq": ({"rax"}, {"rax", "rdx"}),
+}
+def _implicit(mn, ops):
+    if mn in ("imulq", "imull") and len(ops) == 1:
+        return {"rax"}, {"rax", "rdx"}
+    return IMPLICIT.get(mn)
@@ def transmitter_slice, inside the backward loop, before the generic dst handling
         pc, mn, ops = body[j]
+        imp = _implicit(mn, ops)
+        if imp:
+            uses, defs = imp
+            if not (defs & need):
+                continue
+            slice_instrs.append((pc, mn, ops))
+            need -= defs; need |= uses
+            for o in ops:
+                if _is_mem(o):
+                    producers.append({"pc": pc, "mn": mn, "dst": "rax", "sse": False,
+                                      "asm": f"{mn} {', '.join(ops)}"})
+                need |= set(_regs_in(o))
+            need -= {"rsp", "rbp"}
+            continue
         if not ops or mn.startswith("j") ...
```

A list of implicit-operand instructions is the conventional fix; the list should be checked against the Stage-2 vocabulary (`STAGE2_compilation/instruction_tables/proposed/fv2_vocab.jsonc`) so every emitted mnemonic with implicit operands is covered.

### Results that would change (new scan: old vs patched slice over every not_taken test)

- `Recon_6_u_core_lpP_fv3`: 70 of 26,506 slices change: GPR → SSE producer 27 (incl. inst-001501 and inst-003549, both checked individually), xmm → SSE producer 24, GPR → xmm 13, and 8 gain `xmm4`. For E6 2%, inst-001501 (ld) and inst-003549 (br_x) move from 'other(GPR slice)' to `R-SA-13_static`, matching the manual verdict.
- `STT_6_u_core_lpP_fv3`: 32 of 26,954 change (GPR → SSE 9, xmm → SSE 9, GPR → xmm 7, 8 gain `xmm4`, i.e. would become `S1_xmm4` if they hit).
- `Footprint_6_u_core_lpP_fv3`: 267 of 25,116 (no footprint diagnostic uses the slice).
- Direction: more hits attributed to known static classes (R-SA-13, S1), fewer 'other'. The R-SA-13 diagnostic's twin-held path still requires the GPR twin to hold, so no hit is disqualified on the slice alone.

### Tests to add

`STAGE3_gem5/tests/test_fv2_slice.py`: a 6-line fixture body `movq (%rsi,%rdi),%xmm13; movq %xmm13,%rdi; movq %r10,%rax; movq %rdi,%rcx; cqto; idivq %rcx; movq %rax,%r10; movq (%rsi,%r10),%rdi` → `sse_producer True`, slice contains the `idivq`. Negative: a body where `idivq` writes `rax` but the xmit reads an unrelated register → slice unchanged from the old function.

### Reported numbers

None (STT/ReCon static classes only). The S1_xmm4 first-detection row for STT (`classify_hits --defense stt`) could gain a few tests; STT is out of the comparison.

## 8. ReCon reveal-through-concretization: disqualifier diagnostic and Stage-2 sketch

### Problem and evidence

E6 GPR twin inst-021056 and inst-021429 (`SOURCE_AUDIT_RECON.md` 'E6 fv3 isTainted=0' (2); URGENT_TODO E2LT-3). The xmit logs `isTainted=0 isSpeculative=1` with no forward; stats `system.cpu.lsq0.revealRequests` 2 / 1 and `system.cpu.taint_tracker.allowlistedTaintsFromTT` 13 / 15; with `gem5.allow_leaked: false` (only change, cafe2 `bugwork/e2_losttaint/E6_twin_noleak.json`) the xmit logs `isTainted=1` and neither test hits. Stage 2 created the committed pair or the alias: inst-021056's committed loads read blank memory that concretizes to `rsp+0` because every loaded value is 0, the word the speculative load reads; in inst-021429, pc1's address register is a blank slot that `pass3_assign_operands` filled with pc0's output (`parsexml.py:1655-1661`, inputs sample the full `free_pool`), creating a committed LD→LD pair Alloy does not have.

### Proposed diagnostic (option (a) of E2LT-3)

```text
STAGE3_gem5/triage/diag/diag_recon_concretized_reveal.py   (new; PHASE disqualifier,
  CATEGORY "artifact:recon_concretized_reveal", NEEDS_GEM5 True, ORDER 5, KINDS ("ld","br_x"))
evidence: rerun_hits_evidence.py --analyzer recon_reveal, run twice per key:
  pass 1  campaign config verbatim (+ LSQUnit): read m5out/stats.txt
          system.cpu.taint_tracker.allowlistedTaintsFromTT, system.cpu.lsq0.revealRequests,
          the xmit's STL_CHECK isTainted (ld) / its delay_unit insertion (br_x), rerun hit.
  pass 2  same, with gem5.allow_leaked=false (new flag --set gem5.allow_leaked=false):
          rerun hit, xmit STL_CHECK isTainted.
is_known(stem) <=> pass1.reproduced and pass1.allowlisted > 0 and pass1.reveal_requests > 0
                   and pass1.xmit_tainted == 0
                   and pass2.hit == False and pass2.xmit_tainted == 1
                   and reveal_is_legit(stem)              # see CP-8
```

The two-run part says 'ReCon's reveal removed this taint'. It does not say the reveal was correct: R-SA-2 (stale reveal across an overwrite), R-SA-4 (width) and R-SA-6 (wrong word) are reveal-path bugs that would show the same two-run signature. So a conservative disqualifier also needs `reveal_is_legit`: the committed load pair that revealed the word (LD2's address from LD1's value) read exactly the 8-byte word the speculative source load reads, with no store to that word between LD2's commit and the source load. The load addresses come from the rerun trace; which LSQUnit line carries the effective address in the recon build must be confirmed when implementing (not checked here).

### DECIDE CP-8 (new; extends E2LT-3)

- **Question 1: is a reveal that looks correct a disqualifier?** Options: (a) yes, with `reveal_is_legit` (conservative; a hit stays NEW if the reveal could be one of R-SA-2/4/6); (b) yes on the two-run signature alone (simpler, but could hide a reveal-path bug); (c) not a disqualifier, a separate 'reveal fired' class that still counts as a hit. Recommendation: (a), because the CLAUDE.md rule is to bucket only when 100% certain.
- **Question 2: how far should the Stage-2 fix reach?** See the sketch below. Recommendation: apply it only behind a Stage-2 option enabled for ReCon testsets first, and measure what it does to the footprint UV5 precondition before using it anywhere else.

### Stage-2 sketch (proposal only; `parsexml.py` edits need Anna's sign-off)

Two mechanisms, two guards:

```text
G1 (inst-021429, blank ADDRESS register slots): in pass3_assign_operands (parsexml.py:1652-1661),
   for a non-synthetic ld/str whose `inaddr` slot is unspecified, draw from
   free_pool minus {registers assigned to the outreg of any earlier ld in program order},
   instead of the full free_pool. ALU input slots (inreg0/inreg1) keep sampling the full pool,
   so the intentional chain collision that builds OTB merges (CLAUDE.md 'Chain interleaving')
   is unchanged.
G2 (inst-021056, blank MEMORY on a register-addressed load): when a load's inaddr is specified
   (address = probe_base + index register, parsexml.py:~2694-2711 for stores, the load path is
   the same shape) but its inmem is unspecified in Alloy, emit the access with a displacement
   into a disjoint region (as the no-STLF variant does with %probe_st, parsexml.py:2050, 2258),
   e.g. a new %probe_free array, so `index = 0` cannot land on a specified Mem_s word.
```

Effects to check before approving: (1) G2 changes runtime addresses, so it can change which loads alias in every corpus regenerated with it, including footprint corpora, where the UV5 precondition (a committed load on the line a squashed load installed; regen-lp census 'same line 43.2%') may rely on exactly this zero-index aliasing. A footprint corpus regenerated with G2 could have a lower UV5 rate, which would move the A-UV5 multiple. (2) G1 removes some committed LD→LD pairs that Stage 2 invents; on ReCon that is the point, elsewhere it slightly changes the shape mix. (3) Any adopted fix contaminates mixed testsets (CLAUDE.md gotcha): regenerate from Stage 2 with the stage output wiped.

### Results that would change

Diagnostic: E6 twin inst-021056, inst-021429 (both modes as applicable) NEW → disqualified. Main-corpus E6 records: unknown until the analyzer runs (the twin is where these two were found). Stage-2 fix: a regenerated corpus, so every E6 number would be new; none of the current results change in place.

### Tests to add

Diagnostic: unit test on two synthetic evidence rows (all conditions true → known; pass 2 still hits → not known; `allowlisted 0` → not known). Stage 2: a fixture instance with a blank load `inaddr` after a load whose outreg is in the free pool → assigned register never equals that outreg over 200 seeded draws (G1); a register-addressed load with blank inmem → emitted asm uses the disjoint base (G2); OTB regression: the OTB-forcing fixture still produces a merge (ALU blank input collides with a chain output).

### Reported numbers

Diagnostic: none. Stage-2 fix: none until a corpus is regenerated; if G2 were applied to the footprint corpus, the UV5 rate (and so the headline A-UV5 multiple) would need re-measuring.

## Scan commands (read-only, for reproduction)

- Item 1: per-event categories from the kept T1g traces with `check_footprint.TraceModel` (code `firstdet_final/code/STAGE3_gem5`), 120 hits, `random.Random(1110)` order over `classes.jsonl` keys.
- Item 2: `_sweep_raw/*check_ld*.json` of the four `__latest` 2% campaigns joined with `testsets_twostage/<corpus>/rmw_stems.tsv`; `would_drop` = `in_window and cache_fate is not None and not data_obtained`.
- Item 4: `cs_evidence/diagnostics/cleanupspec_skip_evidence.json` items with `cause == unattributed`, events looked up in the kept trace via `classify_cs_rmw.parse_trace`, `evict.cause` resolved to its fill.
- Item 6: `diff -rq /work/gem5-recon-modded/src/cpu/o3 /work/gem5-recon-ruby3/src/cpu/o3` and `sha256sum` of both `lsq_unit.cc` (cafe2 container).
- Item 7: old `transmitter_slice` (from `loosepin_regen/code_eval/STAGE3_gem5/triage/diag`) vs the patched walk on every `mispredict_not_taken` ann of the three fv3 corpora.

## Decisions for Anna

- **C1-a (item 1): what an InvisiSpec raw hit means.** Options: (a) raw hit = an in-window footprint outside the known deviations, D-1 reported beside it (recommended; the paper covers DTLB replacement, §VI-E3 p9-10, so D-1 stays in the criterion as a known class); (b) drop D-1 from the criterion entirely (hides a real deviation); (c) keep today's raw hit and rely on the bucketer (keeps saturation).
- **C1-b (item 1): Futuristic actor = loads only.** Options: (a) loads only, per §IV-A1 p4 (recommended; removes the store-actor artifact at the source and resolves the contradiction inside `invisispec.json`); (b) keep any instruction and only add the 'unknown' rule (removes the no-record stores but keeps the `stis` DTLB fill, so warm tests still hit). This changes E12a's criterion, which the 11-09 audit flagged as Anna's call.
- **Existing DECIDE (item 2): check_ld RMW fix**, option (a) as specified above; add the `xmit_mem_record_missing` ungated case so nothing is hidden.
- **CP-5 (item 5):** static data slice vs gem5 Rename-trace taint source for 'outside the slice' (recommendation: static).
- **CP-8 (item 8):** the disqualifier's certainty bar and the Stage-2 fix's reach (recommendations above), together with E2LT-3.
- **RL-9 (item 6):** the source check it asked for is done (`src/cpu/o3` identical); recommendation (a) widen.
- **CF-2 (item 4):** can be closed with the victim rule.

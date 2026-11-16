#!/usr/bin/env python3
"""
apply_stl_hooks_amulet.py — the SimSpect-STL hooks (store bypass, Spectre v4) for
the three AMuLeT gem5 trees: InvisiSpec, CleanupSpec (old gem5, templated O3
`*_impl.hh`, optparse configs, Python 2) and SpecLFB (gem5 22.1, same layout as
the tree apply_stl_hooks.py was written for).

Same hooks, flags and trace lines as apply_stl_hooks.py (read its docstring and
wiki/design/STL_SPECULATION.md "gem5 hooks"):
  --stl-ann-file <ann.json>      (store_addr, load_addr) pairs
  --stl-store-stall-cycles N     hold an annotated store's address generation
  --stl-alias-pred {no_alias,alias,off}   forced memory-dependence prediction
  O3PipeView:simspect:<tick>:STL:stl_hold|stl_release|pred_no_alias|pred_alias|mem_order_squash:...

Where this port differs from the recon-stl hooks (and why):
  1. mem_order_squash is printed only when the run was given an --stl-ann-file
     with at least one pair (IEW member stlTraceOn). recon-stl prints it in every
     run. Reason: without STL flags these binaries must give a trace that is
     byte-identical to the hooks-v2 binaries other campaigns use. In an STL run
     it still prints for every memory-order violation, annotated or not.
  2. InvisiSpec / CleanupSpec only: MemDepUnit keeps ONE producer per instruction
     (`producing_store`), where gem5 v22 keeps a list. In `alias` mode with a load
     barrier (the litmus setup mfence) in flight, the load waits on the YOUNGER of
     {barrier, paired store} instead of on both. That is equivalent: a paired
     store younger than the barrier was itself inserted behind it and waits on a
     barrier too (insertBarrier sets storeBarrier together with loadBarrier), and
     a paired store older than the barrier commits before the barrier executes.
  3. SpecLFB only: the violation site calls squashDueToMemOrder(inst, violator,
     tid) (SpecLFB added the store as first argument), so that one anchor differs.
Nothing else differs: the hold is the same issue-and-bounce through
rescheduleMemInst / replayMemInst, and no defense code is touched.

Every edit is located by an anchor string that must occur exactly once; nothing
is written unless all anchors of all files match. Every inserted block carries
the marker "SimSpect-STL"; a file that already has it is skipped (idempotent).
Originals are saved as <file>.pre-stl.

Usage (always on a COPY of the tree; never the in-place trees other campaigns run):
  apply_stl_hooks_amulet.py <gem5_root> --build {InvisiSpec,CleanupSpec,SpecLFB} --dry-run
  apply_stl_hooks_amulet.py <gem5_root> --build <Build>
  apply_stl_hooks_amulet.py <gem5_root> --build <Build> --diff > stl_hooks.diff
      (unified diff of every hooked file against its .pre-stl; re-apply with patch -p1)
Then rebuild: gem5-hooks/stl/build_stl_amulet.sh <Build>.
"""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import shutil
import sys
from pathlib import Path

MARK = "SimSpect-STL"
HERE = Path(__file__).resolve().parent


def ind(block: str, n: int) -> str:
    """Indent every non-empty line of a zero-indent block by n spaces."""
    return "".join((" " * n + l if l.strip() else l) for l in block.splitlines(True))


# --------------------------------------------------------------------------
# Shared text (old trees). C newlines inside format strings are written \\n.
# --------------------------------------------------------------------------
PARAMS_PY = '''
    # SimSpect-STL hooks (gem5-hooks/stl/, wiki/design/STL_SPECULATION.md)
    stlStallStorePCs = VectorParam.Addr([], "SimSpect-STL: store PCs whose "
        "address generation is held for stlStoreStallCycles")
    stlStoreStallCycles = Param.Unsigned(0, "SimSpect-STL: cycles to hold an "
        "annotated store before it computes its address (0 = off)")
    stlAliasLoadPCs = VectorParam.Addr([], "SimSpect-STL: annotated bypass "
        "load PCs, index-paired with stlAliasStorePCs")
    stlAliasStorePCs = VectorParam.Addr([], "SimSpect-STL: the store PC each "
        "annotated load truly aliases")
    stlAliasPred = Param.Unsigned(0, "SimSpect-STL: memory-dependence "
        "prediction for annotated loads: 0 = unmodified store sets, "
        "1 = no alias (false negative), 2 = alias (false positive control)")
'''

IEW_HH_INCLUDES = ("#include <unordered_map>  // SimSpect-STL\n"
                   "#include <unordered_set>  // SimSpect-STL\n")

IEW_HH_MEMBERS = '''
    /** SimSpect-STL: store PCs whose address generation is held. */
    std::unordered_set<Addr> stlStallStorePCs;
    /** SimSpect-STL: hold length (0 = hook off). */
    Cycles stlStoreStallCycles;
    /** SimSpect-STL: held store seqNum -> tick its hold ends. */
    std::unordered_map<InstSeqNum, Tick> stlHoldUntil;
    /** SimSpect-STL: this run has annotated stores, so mem_order_squash
     * lines are printed (never in a run without --stl-ann-file). */
    bool stlTraceOn = false;
'''

IEW_CTOR_OLD = '''    // SimSpect-STL: store address-generation hold (--stl-ann-file)
    stlStallStorePCs.insert(params->stlStallStorePCs.begin(),
                            params->stlStallStorePCs.end());
    stlStoreStallCycles = Cycles(params->stlStoreStallCycles);
    stlTraceOn = !stlStallStorePCs.empty();

'''

# Zero-indent body placed right after "} else if (inst->isStore()) {".
HOLD_OLD = '''// SimSpect-STL: hold an annotated store's address generation
// for stlStoreStallCycles after it first issues. It goes back
// to the mem-dep replay list (as the LSQ does for a load it
// can't execute yet); an event replays it when the hold ends.
// An early replay (MemDepUnit::replay replays every waiting
// mem op) just re-defers it until then.
if (stlStoreStallCycles > 0 &&
        stlStallStorePCs.count(inst->pcState().instAddr())) {
    auto held = stlHoldUntil.find(inst->seqNum);
    if (held == stlHoldUntil.end()) {
        Tick until = cpu->clockEdge(stlStoreStallCycles);
        stlHoldUntil[inst->seqNum] = until;
        DPRINTFR(O3PipeView, "O3PipeView:simspect:%llu:STL:"
            "stl_hold:line=-:seq=%llu:pc=%#x:victim=-:"
            "cause=-:sq=-:id=-\\n", curTick(), inst->seqNum,
            inst->pcState().instAddr());
        DynInstPtr stl_inst = inst;
        cpu->schedule(new EventFunctionWrapper(
            [this, stl_inst]() mutable {
                if (stl_inst->isSquashed())
                    return;
                replayMemInst(stl_inst);
                cpu->wakeCPU();
            },
            "iew.simspectStlStoreRelease",
            true),  // deleteOnFire
            until);
        rescheduleMemInst(inst);
        continue;
    } else if (curTick() < held->second) {
        rescheduleMemInst(inst);
        continue;
    }
    DPRINTFR(O3PipeView, "O3PipeView:simspect:%llu:STL:"
        "stl_release:line=-:seq=%llu:pc=%#x:victim=-:"
        "cause=-:sq=-:id=-\\n", curTick(), inst->seqNum,
        inst->pcState().instAddr());
}
'''

SQUASH_PRINT = '''// SimSpect-STL: window end for store-to-load speculation
// (printed only in a run with annotated stores, see stlTraceOn)
if (stlTraceOn) {
    DPRINTFR(O3PipeView, "O3PipeView:simspect:%llu:STL:"
        "mem_order_squash:line=-:seq=%llu:pc=%#x:victim=-:"
        "cause=%llu:sq=-:id=-\\n", curTick(), violator->seqNum,
        violator->pcState().instAddr(), inst->seqNum);
}
'''

MDU_HH_MEMBERS_OLD = '''
    /** SimSpect-STL: prediction override for annotated loads
     * (0 = off, 1 = no alias, 2 = alias). */
    unsigned stlAliasPred = 0;
    /** SimSpect-STL: annotated bypass load PCs. */
    std::unordered_set<Addr> stlAliasLoadPCs;
    /** SimSpect-STL: store PC -> the bypass load PCs it truly aliases. */
    std::unordered_multimap<Addr, Addr> stlAliasStoreToLoads;
    /** SimSpect-STL: bypass load PC -> the store PCs it truly aliases. */
    std::unordered_multimap<Addr, Addr> stlAliasLoadToStores;
    /** SimSpect-STL: annotated store PC -> its youngest inserted seqNum. */
    std::unordered_map<Addr, InstSeqNum> stlLastStoreSeq;
    /** SimSpect-STL (alias control): the in-flight paired store an annotated
     * load must wait on, or 0. */
    InstSeqNum stlAliasDep(DynInstPtr &inst);
'''

MDU_INIT_OLD = '''
    // SimSpect-STL: memory-dependence prediction override (--stl-alias-pred)
    stlAliasPred = params->stlAliasPred;
    if (params->stlAliasLoadPCs.size() != params->stlAliasStorePCs.size())
        fatal("SimSpect-STL: stlAliasLoadPCs and stlAliasStorePCs differ in "
              "length (%u vs %u)", params->stlAliasLoadPCs.size(),
              params->stlAliasStorePCs.size());
    for (size_t i = 0; i < params->stlAliasLoadPCs.size(); ++i) {
        stlAliasLoadPCs.insert(params->stlAliasLoadPCs[i]);
        stlAliasStoreToLoads.emplace(params->stlAliasStorePCs[i],
                                     params->stlAliasLoadPCs[i]);
        stlAliasLoadToStores.emplace(params->stlAliasLoadPCs[i],
                                     params->stlAliasStorePCs[i]);
    }
'''

MDU_ALIASDEP_OLD = '''// SimSpect-STL (alias control). The store-set predictor cannot be used
// for this: StoreSet::issued() drops a store from the LFST when it issues,
// and the held store issues (then waits) before a slow-to-dispatch load is
// inserted, so checkInst() would return 0. Depend on the paired store's
// seqNum directly while it is still in flight in this unit.
template <class MemDepPred, class Impl>
InstSeqNum
MemDepUnit<MemDepPred, Impl>::stlAliasDep(DynInstPtr &inst)
{
    InstSeqNum dep = 0;
    auto range = stlAliasLoadToStores.equal_range(inst->pcState().instAddr());
    for (auto it = range.first; it != range.second; ++it) {
        auto seq_it = stlLastStoreSeq.find(it->second);
        if (seq_it != stlLastStoreSeq.end() &&
                seq_it->second < inst->seqNum &&
                memDepHash.count(seq_it->second) &&
                seq_it->second > dep)
            dep = seq_it->second;
    }
    return dep;
}

'''

MDU_RECORD_OLD = '''
    // SimSpect-STL (alias control): remember each annotated store's seqNum
    if (stlAliasPred == 2 && inst->isStore() &&
            stlAliasStoreToLoads.count(inst->pcState().instAddr()))
        stlLastStoreSeq[inst->pcState().instAddr()] = inst->seqNum;
'''

MDU_BARRIER_OLD = '''        // SimSpect-STL: a load barrier (the litmus setup mfence) is in
        // flight, so gem5 makes this load wait on the barrier and never asks
        // the predictor. Apply the forced prediction here too. no_alias has
        // nothing to drop (a barrier wait is not a prediction). alias: this
        // tree keeps ONE producer per instruction (gem5 v22 keeps a list), so
        // the load waits on the younger of {barrier, paired store}. A paired
        // store younger than the barrier was inserted behind it and waits on
        // a barrier itself (insertBarrier sets storeBarrier with loadBarrier);
        // an older one commits before the barrier executes. Either way the
        // load still waits for both.
        if (stlAliasPred != 0 &&
                stlAliasLoadPCs.count(inst->pcState().instAddr())) {
            InstSeqNum dep = 0;
            if (stlAliasPred == 2) {
                dep = stlAliasDep(inst);
                if (dep > producing_store)
                    producing_store = dep;
            }
            DPRINTFR(O3PipeView, "O3PipeView:simspect:%llu:STL:%s:line=-:"
                "seq=%llu:pc=%#x:victim=-:cause=%llu:sq=-:id=-:via=barrier\\n",
                curTick(), stlAliasPred == 1 ? "pred_no_alias" : "pred_alias",
                inst->seqNum, inst->pcState().instAddr(), dep);
        }
'''

MDU_PRED_OLD = '''        // SimSpect-STL: forced prediction for an annotated bypass load
        if (stlAliasPred != 0 && inst->isLoad() &&
                stlAliasLoadPCs.count(inst->pcState().instAddr())) {
            if (stlAliasPred == 1)
                producing_store = 0;  // no alias (false negative): never wait
            else
                producing_store = stlAliasDep(inst);  // alias (control): wait on the store
            DPRINTFR(O3PipeView, "O3PipeView:simspect:%llu:STL:%s:line=-:"
                "seq=%llu:pc=%#x:victim=-:cause=%llu:sq=-:id=-\\n", curTick(),
                stlAliasPred == 1 ? "pred_no_alias" : "pred_alias",
                inst->seqNum, inst->pcState().instAddr(), producing_store);
        }
'''

OPTIONS_OLD = '''    # SimSpect-STL hooks (gem5-hooks/stl/). Inert unless --stl-ann-file is set.
    parser.add_option("--stl-ann-file", default="", action="store",
                      type="string",
                      help="SimSpect-STL: test .ann.json; its "
                           "stl_annotations give (store_addr, load_addr) pairs")
    parser.add_option("--stl-store-stall-cycles", default=0, action="store",
                      type="int",
                      help="SimSpect-STL: cycles each annotated store's "
                           "address generation is held (0 = no hold)")
    parser.add_option("--stl-alias-pred", default="no_alias", action="store",
                      type="choice", choices=["off", "no_alias", "alias"],
                      help="SimSpect-STL: memory-dependence prediction for "
                           "the annotated loads: no_alias = false negative "
                           "(the primitive), alias = false positive (control)")

'''

SE_OLD = '''    # SimSpect-STL hooks (gem5-hooks/stl/)
    if options.stl_ann_file:
        import json as _stl_json
        with open(options.stl_ann_file) as _f:
            _stl = _stl_json.load(_f).get("stl_annotations", [])
        _st = [int(e["store_addr"]) for e in _stl if "store_addr" in e and "load_addr" in e]
        _ld = [int(e["load_addr"]) for e in _stl if "store_addr" in e and "load_addr" in e]
        if len(_st) != len(_stl):
            warn("--stl-ann-file: %d stl_annotations entries lack store_addr/"
                 "load_addr (run compile_annotate.py); skipped" %
                 (len(_stl) - len(_st)))
        system.cpu[i].stlStallStorePCs = sorted(set(_st))
        system.cpu[i].stlStoreStallCycles = options.stl_store_stall_cycles
        system.cpu[i].stlAliasLoadPCs = _ld
        system.cpu[i].stlAliasStorePCs = _st
        system.cpu[i].stlAliasPred = {"off": 0, "no_alias": 1, "alias": 2}[options.stl_alias_pred]
        print("[se.py] SimSpect-STL: %d store/load pairs from %s, store hold "
              "%d cycles, alias pred %s" % (len(_st), options.stl_ann_file,
              options.stl_store_stall_cycles, options.stl_alias_pred))

'''


def old_tree_edits(store_indent: int) -> list:
    """EDITS for the InvisiSpec-vintage trees. store_indent = column of
    '} else if (inst->isStore()) {' in IEW::executeInsts (InvisiSpec 12,
    CleanupSpec 6: its iew_impl.hh is re-indented); the violation site is one
    level deeper than the store branch in both."""
    step = 4 if store_indent == 12 else 2
    body = store_indent + step
    store_anchor = (" " * store_indent + "} else if (inst->isStore()) {\n" +
                    " " * body + "fault = ldstQueue.executeStore(inst);\n")
    squash_anchor = " " * body + "squashDueToMemOrder(violator, tid);\n"
    return [
        ("src/cpu/o3/O3CPU.py",
         '    SSITSize = Param.Unsigned(1024, "Store set ID table size")\n',
         "after", PARAMS_PY),
        ("src/cpu/o3/iew.hh", "#include <set>\n", "after", IEW_HH_INCLUDES),
        ("src/cpu/o3/iew.hh", "    bool fetchRedirect[Impl::MaxThreads];\n",
         "after", IEW_HH_MEMBERS),
        ("src/cpu/o3/iew_impl.hh",
         "    // Setup wire to read instructions coming from issue.\n",
         "before", IEW_CTOR_OLD),
        ("src/cpu/o3/iew_impl.hh", store_anchor, "replace",
         " " * store_indent + "} else if (inst->isStore()) {\n" +
         ind(HOLD_OLD, body) +
         " " * body + "fault = ldstQueue.executeStore(inst);\n"),
        ("src/cpu/o3/iew_impl.hh", squash_anchor, "before",
         ind(SQUASH_PRINT, body)),
        ("src/cpu/o3/mem_dep_unit.hh", "#include <unordered_map>\n", "after",
         "#include <unordered_set>  // SimSpect-STL\n"),
        ("src/cpu/o3/mem_dep_unit.hh", "    MemDepPred depPred;\n", "after",
         MDU_HH_MEMBERS_OLD),
        ("src/cpu/o3/mem_dep_unit_impl.hh", '#include "debug/MemDepUnit.hh"\n',
         "after", '#include "debug/O3PipeView.hh"  // SimSpect-STL\n'),
        ("src/cpu/o3/mem_dep_unit_impl.hh",
         "    depPred.init(params->store_set_clear_period, params->SSITSize,\n"
         "            params->LFSTSize);\n",
         "after", MDU_INIT_OLD),
        ("src/cpu/o3/mem_dep_unit_impl.hh",
         "template <class MemDepPred, class Impl>\nvoid\n"
         "MemDepUnit<MemDepPred, Impl>::insert(DynInstPtr &inst)\n{\n",
         "before", MDU_ALIASDEP_OLD),
        ("src/cpu/o3/mem_dep_unit_impl.hh",
         "MemDepUnit<MemDepPred, Impl>::insert(DynInstPtr &inst)\n{\n"
         "    ThreadID tid = inst->threadNumber;\n",
         "after", MDU_RECORD_OLD),
        ("src/cpu/o3/mem_dep_unit_impl.hh",
         "        producing_store = loadBarrierSN;\n", "after", MDU_BARRIER_OLD),
        ("src/cpu/o3/mem_dep_unit_impl.hh",
         "        producing_store = depPred.checkInst(inst->instAddr());\n",
         "after", MDU_PRED_OLD),
        ("configs/common/Options.py", "def addSEOptions(parser):\n", "before",
         OPTIONS_OLD),
        ("configs/example/se.py", "    system.cpu[i].createThreads()\n",
         "before", SE_OLD),
    ]


def speclfb_edits() -> list:
    """The recon-stl EDITS (imported from apply_stl_hooks.py, so the text is the
    same by construction) with the two differences listed in the docstring."""
    spec = importlib.util.spec_from_file_location("apply_stl_hooks",
                                                  HERE / "apply_stl_hooks.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    out, seen = [], set()

    def sub(text, old, new, tag):
        assert text.count(old) == 1, f"speclfb_edits: {tag}: expected 1 match"
        seen.add(tag)
        return text.replace(old, new)

    for rel, anchor, mode, text in base.EDITS:
        if rel == "src/cpu/o3/iew.hh" and "stlHoldUntil;" in text:
            text = sub(text,
                "    std::unordered_map<InstSeqNum, Tick> stlHoldUntil;\n",
                "    std::unordered_map<InstSeqNum, Tick> stlHoldUntil;\n"
                "    /** SimSpect-STL: this run has annotated stores, so mem_order_squash\n"
                "     * lines are printed (never in a run without --stl-ann-file). */\n"
                "    bool stlTraceOn = false;\n", "member")
        if rel == "src/cpu/o3/iew.cc" and "stlStoreStallCycles = Cycles(" in text:
            text = sub(text,
                "    stlStoreStallCycles = Cycles(params.stlStoreStallCycles);\n",
                "    stlStoreStallCycles = Cycles(params.stlStoreStallCycles);\n"
                "    stlTraceOn = !stlStallStorePCs.empty();\n", "ctor")
        if rel == "src/cpu/o3/iew.cc" and "mem_order_squash" in text:
            assert anchor == "                squashDueToMemOrder(violator, tid);\n"
            anchor = "                squashDueToMemOrder(inst,violator, tid);\n"
            text = ind(SQUASH_PRINT, 16)
            seen.add("squash")
        out.append((rel, anchor, mode, text))
    assert seen == {"member", "ctor", "squash"}, seen
    return out


def edits_for(build: str) -> list:
    if build == "InvisiSpec":
        return old_tree_edits(12)
    if build == "CleanupSpec":
        return old_tree_edits(6)
    if build == "SpecLFB":
        return speclfb_edits()
    raise SystemExit(f"unknown build {build}")


def plan(root: Path, edits: list):
    by_file: dict = {}
    for rel, anchor, mode, text in edits:
        by_file.setdefault(rel, []).append((anchor, mode, text))
    plans, problems = {}, []
    for rel, es in by_file.items():
        path = root / rel
        if not path.exists():
            problems.append(f"missing file: {rel}")
            continue
        src = path.read_text()
        if MARK in src:
            print(f"[skip] {rel}: already has {MARK} hooks", file=sys.stderr)
            continue
        new = src
        for anchor, mode, text in es:
            n = new.count(anchor)
            if n != 1:
                problems.append(f"{rel}: anchor found {n}x (need 1): "
                                f"{anchor.strip()[:70]!r}")
                continue
            if mode == "after":
                new = new.replace(anchor, anchor + text)
            elif mode == "before":
                new = new.replace(anchor, text + anchor)
            else:
                new = new.replace(anchor, text)
        plans[path] = new
    return plans, problems, list(by_file)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gem5_root", type=Path)
    ap.add_argument("--build", required=True,
                    choices=["InvisiSpec", "CleanupSpec", "SpecLFB"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--diff", action="store_true",
                    help="print the unified diff of every hooked file against "
                         "its .pre-stl backup (patch -p1 format) and exit")
    a = ap.parse_args()
    root = a.gem5_root.resolve()
    if (not a.dry_run and not a.diff and root.name.startswith("amulet-gem5-")
            and root.parent.name == "amulet"):
        sys.exit("refusing: this is an in-place AMuLeT tree that other campaigns "
                 "run. Apply to a copy (cafe2: /work/amulet/hooks_stl_work/<Build>).")
    edits = edits_for(a.build)
    if a.diff:
        for rel in dict.fromkeys(e[0] for e in edits):
            new, old = root / rel, root / (rel + ".pre-stl")
            if not old.exists():
                sys.exit(f"no backup {old}: hooks not applied by this script?")
            sys.stdout.writelines(difflib.unified_diff(
                old.read_text().splitlines(True), new.read_text().splitlines(True),
                "a/" + rel, "b/" + rel))
        return
    plans, problems, _ = plan(root, edits)
    if problems:
        print("NOT APPLIED — fix these first:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    for path, new in plans.items():
        print(f"[{'would edit' if a.dry_run else 'edit'}] {path.relative_to(root)}")
        if not a.dry_run:
            backup = path.with_name(path.name + ".pre-stl")
            if not backup.exists():
                shutil.copy2(path, backup)
            path.write_text(new)
    print("dry run: nothing written" if a.dry_run else "done — rebuild gem5")


if __name__ == "__main__":
    main()

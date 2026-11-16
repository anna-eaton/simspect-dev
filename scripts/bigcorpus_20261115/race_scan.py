#!/usr/bin/env python3
"""race_scan.py -- count the visibility-point / squash race (paper UV6; wiki/findings/bug/stt_slowcomm_vp_squash_race/) in the RAW
per-record checker output of a testrun.py campaign (agent bigcorpus, 2026-11-15). No gem5 re-run.

Why a scan and not window-results.json: check_ld ends its window at branch resolution (check_ld.py, check_branch_resolutions), and the
race packet goes out AFTER the guarding branch resolves and BEFORE the squash lands, so a race test is NOT an issued_in_window hit.
Counting it needs its own definition (open DECIDE R1, option (c) "wrong-path transmission after resolution, before squash"). This
script applies exactly that definition to check_ld's own record fields, reusing check_ld's data-obtained gate (CLAUDE.md "Leak criteria"):

  race = ld transmitter record with status ok, and
    data obtained by check_ld's gate: cache_fate == reached_cache (access tick = packet_tick) or store_forward (access tick = xmit_complete);
    every other window criterion holds (lc_retired, signal_seen, after_lc, before_fnc) and ONLY branches_unresolved fails;
    the transmitter never retired (xmit_retire == 0: wrong path) and the LSQ saw it squashed (load_squash_tick > 0);
    some forced-unresolved branch has an observed resolve_tick (branch_resolutions[*].source == observed) with
      resolve_tick <= access tick < load_squash_tick  (the access lands in the resolution -> squash gap).
  Note: check_ld's branches_unresolved compares xmit_signal (LSQ execute tick) with resolve_tick; the scan keys on the ACCESS tick.

Second, model-independent measure (added after the SPT 24-stem rerun, where the old annotations carry no observed branch resolutions so
check_ld scores the race packet as an ordinary in-window hit): wp_obtained = ld record, status ok, data obtained by the gate, transmitter
never retired and squashed in the LSQ (a wrong-path transmitter that obtained its data, anywhere in time). With --control <campaign at
commitToIEWDelay 1> the scan reports the PAIRED difference: stems (per mode) wp_obtained here but not in the control = delay-induced.
Outputs per mode: race count, ld tests scanned, example stems, the gap (access - resolve, squash - access) in cycles. Conservative:
records missing any field are 'unknown', never race. Confirm a sample by re-running gem5 with
wiki/findings/bug/stt_slowcomm_vp_squash_race/diag_stt_vp_squash_race.py (--hits-from a json list of the race stems as issued_in_window).
Usage (from the code root): race_scan.py <results/<name>__latest> [--json out.json]
"""
import argparse, collections, glob, json, os, sys


def access_tick(r):
    cf = r.get("cache_fate")
    if cf == "reached_cache":
        return r.get("packet_tick") or 0
    if cf == "store_forward":
        return r.get("xmit_complete") or 0
    return 0


def classify(r):
    if r.get("xmit_kind") not in ("ld", None) or r.get("status") != "ok":
        return "skip"
    c = r.get("criteria") or {}
    if not c:
        return "unknown"
    if r.get("issued_in_window"):
        return "window_hit"
    if not r.get("data_obtained"):
        return "no_data"
    if not all(c.get(k) for k in ("lc_retired", "signal_seen", "after_lc", "before_fnc")) or c.get("branches_unresolved") is not False:
        return "other_miss"
    a, sq = access_tick(r), r.get("load_squash_tick") or 0
    if not a:
        return "unknown"
    if (r.get("xmit_retire") or 0) > 0:
        return "resolved_then_committed"
    if not sq:
        return "unknown"
    res = [b.get("resolve_tick") for b in (r.get("branch_resolutions") or []) if b.get("source") == "observed" and b.get("resolve_tick")]
    if any(t <= a < sq for t in res):
        return "race"
    return "other_miss"


def wp_obtained(r):
    return (r.get("xmit_kind") in ("ld", None) and r.get("status") == "ok" and bool(r.get("data_obtained"))
            and not (r.get("xmit_retire") or 0) and bool(r.get("load_squash_tick")))


def load_recs(camp, mode):
    recs = {}
    for f in sorted(glob.glob(os.path.join(camp, mode, "_sweep_raw", "*.json"))):
        try:
            x = json.load(open(f))
        except Exception as e:
            print(f"WARN unreadable {f}: {e}", file=sys.stderr); continue
        for r in (x if isinstance(x, list) else []):
            if isinstance(r, dict) and r.get("name"):
                recs[r["name"]] = r
    return recs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("campaign"); ap.add_argument("--json"); ap.add_argument("--examples", type=int, default=8)
    ap.add_argument("--control", help="campaign dir of the same rows at commitToIEWDelay 1 (paired delay-induced count)")
    a = ap.parse_args(); camp = os.path.realpath(a.campaign); out = {"campaign": camp}
    for mode in ("mispredict_not_taken", "mispredict_taken"):
        recs = load_recs(camp, mode)
        cnt = collections.Counter(); ex = []; gaps = []
        for n, r in sorted(recs.items()):
            v = classify(r); cnt[v] += 1
            if v == "race":
                acc = access_tick(r); tpc = 500
                res = min(b["resolve_tick"] for b in r["branch_resolutions"] if b.get("source") == "observed" and b.get("resolve_tick") and b["resolve_tick"] <= acc)
                gaps.append(((acc - res) // tpc, (r["load_squash_tick"] - acc) // tpc))
                if len(ex) < a.examples:
                    ex.append(dict(name=n, cache_fate=r.get("cache_fate"), access=acc, resolve=res, squash=r["load_squash_tick"],
                                   cache_setup=r.get("cache_setup"), stall_points=r.get("stall_points")))
        ld = sum(v for k, v in cnt.items() if k != "skip")
        wp = sorted(n for n, r in recs.items() if wp_obtained(r))
        paired = None
        if a.control:
            ctl = load_recs(os.path.realpath(a.control), mode)
            both = [n for n in recs if n in ctl and recs[n].get("status") == "ok" and ctl[n].get("status") == "ok"]
            ind = sorted(n for n in both if wp_obtained(recs[n]) and not wp_obtained(ctl[n]))
            gone = sorted(n for n in both if wp_obtained(ctl[n]) and not wp_obtained(recs[n]))
            paired = dict(paired_tests=len(both), delay_induced=len(ind), delay_induced_examples=ind[:a.examples],
                          control_only=len(gone), control_only_examples=gone[:a.examples])
        out[mode] = dict(records=len(recs), ld_scanned=ld, verdicts=dict(cnt), race=cnt["race"], examples=ex,
                         wp_obtained=len(wp), wp_obtained_examples=wp[:a.examples], paired_vs_control=paired,
                         gap_cycles_access_minus_resolve=collections.Counter(g[0] for g in gaps).most_common(6),
                         gap_cycles_squash_minus_access=collections.Counter(g[1] for g in gaps).most_common(6))
        print(f"{mode}: race {cnt['race']} / {ld} ld records; wp_obtained {len(wp)}; paired {paired and {k: v for k, v in paired.items() if not k.endswith('examples')}}; verdicts={dict(cnt)}")
    if a.json:
        open(a.json, "w").write(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

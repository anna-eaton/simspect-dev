"""UV6 (STT, SPT-Fence): the visibility-point / squash race. Internal `stt_vp_squash_race`, `vp_squash_race`.

Signature (one gem5 rerun per hit under the hit's own run_config, wiki/findings/bug/stt_slowcomm_vp_squash_race/
diag_stt_vp_squash_race.py): (1) the xmit load makes a real cache access (diag_ld_cache_reach fate reached_cache), (2) the
xmit load is squashed (not retired), and (3) its packet goes out at or after the controlling mispredicted branch's
resolution (Commit mispredict-squash broadcast). That script's verdict field is `stt_vp_squash_race`; every other verdict
(stt_no_hold, committed_access, not_real_access, no_mispredict_branch, error) stays NEW.
Not counted from window-results: check_ld ends its window at branch resolution, so a race test is usually not an
issued_in_window hit. A record-only count (scripts/bigcorpus_20261115/race_scan.py, strict / wp_obtained) is open as
DECIDE BC-1 and is NOT encoded here.
Evidence: rob_impl.hh:812 at STT e3283b9; claimed only for commitToIEWDelay > 1 (3 on STT, 4 on SPT-Fence).
Verdict: real gem5 defense bug, new (paper UV6).
"""
LABEL = "stt_vp_squash_race"
PAPER_LABEL = "UV6"
ALIASES = ["vp_squash_race", "race"]
DEFENSES = ["stt", "spt"]
PHASE = "real_bug"
VERDICT = "real_bug"
ORDER = 95
NEEDS_GEM5 = True
FAMILY = "race_record"


def matches(rec) -> bool:
    return rec.get("verdict") == "stt_vp_squash_race"

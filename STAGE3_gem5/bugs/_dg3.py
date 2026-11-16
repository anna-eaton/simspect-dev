"""DG-3 (Anna, 2026-11-15, option (i): "option i sounds right for strictness"): exempt over_clean lines from the
footprint checker's net-state replay outside-window filter, so the count rule and the replay agree.

check_footprint._eval_balance puts a differing (struct, line) of the net-state replay into `net_state.outside_window`
when none of the line's actor footprint events is inside W. For UV5 the actor S's fill precedes lc_retire because the
older committed access U is the lc itself, so every UV5 line landed there and the record was `inconsistent`
(count rule says over_clean, replay says outside W). Option (i): a line the count rule already charges as over_clean
(per_line d_install < 0 or d_victim < 0, and not in over_clean_outside_window = its cleanup belongs to a window squash)
is not filtered; it moves from net_state.outside_window to net_state.differing, and `inconsistent` / `decided` are
recomputed from the same set comparison check_footprint uses.

Implemented here as a pure record normalization (no checker edit): it changes only net_state.differing,
net_state.outside_window, net_state.leak, inconsistent and decided. `issued_in_window` and `leak` cannot change: a line
moves only when the count rule fired over_clean on it, so count_leak is already True. normalize() asserts this.
"""


def _over_keys(raw):
    out_w = {(r.get("struct"), r.get("line")) for r in raw.get("over_clean_outside_window") or []}
    return {(r["struct"], r["line"]) for r in raw.get("per_line") or []
            if (r.get("d_install", 0) < 0 or r.get("d_victim", 0) < 0)} - out_w


def normalize(raw):
    """-> (raw', changed: bool). raw is a check_footprint balance record (CleanupSpec); others pass through."""
    ns = raw.get("net_state")
    if not isinstance(ns, dict) or "inconsistent" not in raw or not ns.get("outside_window"):
        return raw, False
    over = _over_keys(raw)
    move = [r for r in ns["outside_window"] if (r["struct"], r["line"]) in over]
    if not move:
        return raw, False
    differing = list(ns.get("differing") or []) + move
    outside = [r for r in ns["outside_window"] if (r["struct"], r["line"]) not in over]
    count_keys = {(o["struct"], o["line"]) for o in raw.get("offending") or []}
    net_keys = {(r["struct"], r["line"]) for r in differing}
    inconsistent = net_keys != count_keys
    count_leak = bool(raw.get("offending"))
    net = bool(differing)
    new = dict(raw, net_state=dict(ns, leak=net, differing=differing, outside_window=outside),
               inconsistent=inconsistent, decided=not inconsistent)
    iiw = (count_leak or net) if inconsistent else count_leak
    assert iiw == bool(raw.get("issued_in_window")), f"DG-3 would change issued_in_window of {raw.get('name')}"
    return new, (inconsistent != raw.get("inconsistent"))

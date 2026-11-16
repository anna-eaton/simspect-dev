#!/usr/bin/env python3
"""pair_table.py (agent inttwin 2026-11-16) -- per-row, per-label counts for the FPR version, the integer version, and the pairs
(same mode + stem = same Alloy graph, same draws) where they differ. Reads the cls/<row>/ dirs written by classify_node.py
(collected from the nodes into one dir): per_stem_{fpr,int}.json (bucket label of every gated hit, incl. disqualifiers) for eval rows,
race_{fpr,int}.json (race_scan with all examples) for race rows; gate.json for test counts.
Paper bugs: UV1 = S1_xmm4 (STT rows), UV2 = labels starting 'A2 STLF bypass', UV3 = 'R-SA-8 confirmed' (store-shadow replay label, or rsa8_trace signature on a branch candidate); 'UV3 cand.' = unconfirmed candidates, UV6 = race rows
(strict race, wp_obtained, delay-induced vs delay 1).
Usage: pair_table.py <cls dir> [--json out.json] [--md out.md]
"""
import argparse, collections, json, os, sys
from pathlib import Path


def bug(label):
    if label == "S1_xmm4":
        return "UV1"
    if label.startswith("A2 STLF bypass"):
        return "UV2"
    if label.startswith("R-SA-8 confirmed"):
        return "UV3"
    if label.startswith("R-SA-8 candidate"):
        return "UV3 cand."
    return None


def per_stem(p):
    out = {}
    if not p.exists():
        return None
    for k, lab in json.load(open(p)).items():
        m, kind, rp, s = k.split("/")
        out[(m, s)] = lab
    return out


def tests(g, rn):
    e = g.get(rn, {})
    return sum(v.get("tests", 0) for k, v in e.items() if not k.endswith("_merge")), {k: v for k, v in e.items() if k.endswith("_merge")}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cls"); ap.add_argument("--json"); ap.add_argument("--md")
    ap.add_argument("--rg", help="dir with <results_name>.removed.jsonl / .score.json from rescore_resolved_gate.py score: gate ON view")
    a = ap.parse_args()
    R = {}; md = []
    for d in sorted(Path(a.cls).iterdir()):
        if not d.is_dir() or not (d / "gate.json").exists():
            continue
        row = d.name; G = json.load(open(d / "gate.json"))["campaigns"]
        rn = {v: f"{row}_{v}" for v in ("fpr", "int")}
        if (d / "campaigns.json").exists():   # inttwin2: the _ra rows are named <base>_<v>_ra, not <row>_<v>
            for c in json.load(open(d / "campaigns.json")):
                v = "int" if "_int" in c["results_name"][len(row.removesuffix("_ra")):] else "fpr"
                rn[v] = c["results_name"]
        nt = {v: tests(G, rn[v]) for v in rn}
        res = dict(tests={v: nt[v][0] for v in rn}, merge={v: nt[v][1] for v in rn})
        if (d / "race_fpr.json").exists():
            rr = {v: json.load(open(d / f"race_{v}.json")) for v in rn if (d / f"race_{v}.json").exists()}
            sets = collections.defaultdict(dict)
            for v, x in rr.items():
                for m in ("mispredict_not_taken", "mispredict_taken"):
                    e = x.get(m) or {}
                    sets["race"].setdefault(v, set()).update((m, r["name"]) for r in e.get("examples", []))
                    sets["wp_obtained"].setdefault(v, set()).update((m, n) for n in e.get("wp_obtained_examples", []))
                    p = e.get("paired_vs_control") or {}
                    if p:
                        sets["delay_induced"].setdefault(v, set()).update((m, n) for n in p.get("delay_induced_examples", []))
            res["race"] = {k: dict(fpr=len(s.get("fpr", ())), int=len(s.get("int", ())), fpr_only=len(s.get("fpr", set()) - s.get("int", set())),
                                   int_only=len(s.get("int", set()) - s.get("fpr", set()))) for k, s in sets.items()}
            md.append(f"\n### {row} (race; tests FPR {res['tests']['fpr']}, INT {res['tests']['int']})\n\n| measure | FPR | INT | FPR only | INT only |\n|---|---|---|---|---|")
            for k, c in res["race"].items():
                md.append(f"| {k} | {c['fpr']} | {c['int']} | {c['fpr_only']} | {c['int_only']} |")
        ps = {v: per_stem(d / f"per_stem_{v}.json") for v in rn}
        for v in rn:   # store-shadow rows: the oldest-taint re-bucket (stl_ot_node.sh) supersedes the plain bucket
            if (d / f"per_stem_ot_{v}.json").exists():
                ps[v] = per_stem(d / f"per_stem_ot_{v}.json")
        rgrm = {}
        for v in rn:   # resolved-branch gate (RG-1 = b): records it removes
            f = Path(a.rg or "/nonexistent") / f"{rn[v]}.removed.jsonl"
            if f.exists():
                rgrm[v] = {(x["mode"], x["name"]) for x in map(json.loads, open(f)) if x}
            sf = Path(a.rg or "/nonexistent") / f"{rn[v]}.score.json"
            if sf.exists():
                res.setdefault("rg_counts", {})[v] = json.load(open(sf))["counts"]
        for v in rn:   # rsa8_trace confirmation (rsa8_node.sh) of the branch R-SA-8 candidates, when it ran
            rp = d / f"rsa8_{v}.json"
            if ps[v] and rp.exists():
                r8 = json.load(open(rp))
                for k, lab in list(ps[v].items()):
                    if lab.startswith("R-SA-8 candidate"):
                        e = r8.get(f"{k[0]}/{k[1]}") or {}
                        ps[v][k] = ("R-SA-8 confirmed (rsa8_trace signature)" if e.get("rsa8_signature") else
                                    "R-SA-8 candidate, rerun error" if e.get("error") or not e else "R-SA-8 candidate, signature absent in rerun")
        for v in rn:
            if ps[v] is not None and v in rgrm:
                for k in list(ps[v]):
                    if k in rgrm[v]:
                        ps[v][k] = "removed by resolved-branch gate (RG-1 b)"
        if all(ps.values()):
            labs = sorted(set(ps["fpr"].values()) | set(ps["int"].values()))
            tab = {}
            for lab in labs:
                f = {k for k, l in ps["fpr"].items() if l == lab}; i = {k for k, l in ps["int"].items() if l == lab}
                tab[lab] = dict(fpr=len(f), int=len(i), fpr_only=len(f - i), int_only=len(i - f), bug=bug(lab))
            bugs = {}
            for b in ("UV1", "UV2", "UV3", "UV3 cand."):
                f = {k for k, l in ps["fpr"].items() if bug(l) == b}; i = {k for k, l in ps["int"].items() if bug(l) == b}
                if f or i:
                    bugs[b] = dict(fpr=len(f), int=len(i), both=len(f & i), fpr_only=len(f - i), int_only=len(i - f))
            hf, hi = set(ps["fpr"]), set(ps["int"])
            res.update(labels=tab, bugs=bugs, gated_records=dict(fpr=len(hf), int=len(hi), fpr_only=len(hf - hi), int_only=len(hi - hf)))
            md.append(f"\n### {row} (tests FPR {res['tests']['fpr']}, INT {res['tests']['int']}; gated-hit records FPR {len(hf)}, INT {len(hi)}, "
                      f"only-FPR {len(hf - hi)}, only-INT {len(hi - hf)})\n\n| bucket | paper bug | FPR | INT | FPR only | INT only |\n|---|---|---|---|---|---|")
            for lab, c in sorted(tab.items(), key=lambda x: -(x[1]["fpr"] + x[1]["int"])):
                md.append(f"| {lab} | {c['bug'] or ''} | {c['fpr']} | {c['int']} | {c['fpr_only']} | {c['int_only']} |")
        R[row] = res
    txt = "\n".join(md) + "\n"
    print(txt)
    if a.md:
        open(a.md, "w").write(txt)
    if a.json:
        json.dump(R, open(a.json, "w"), indent=1, default=list)


if __name__ == "__main__":
    main()

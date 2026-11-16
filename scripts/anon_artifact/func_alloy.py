#!/usr/bin/env python3
"""func_alloy.py -- check 3 (Alloy part) for the anonymous artifact: every stripped .als gives the same Stage-1
partition set and the same instance count / XML fingerprint set as the original, on small runs.

Core models: partition_stage1.py (repo copy) on original and stripped -> compare kinds; enumerate partitions k2 and k3
with a6CountModels (cap) -> compare counts and the alloy_solver_order fingerprint sets of the XMLs.
Loose-pin models: pin the first k3 core of the original enumeration with make_s15_model.pin_pred (as stage15lp.py does)
into both the original and the stripped lpP text -> a6CountModels with cap 300 -> compare counts and fingerprints.
Usage: python3 scripts/anon_artifact/func_alloy.py --work <scratch dir> [--families Footprint_6_u STT_6_u Recon_6_u]
"""
import argparse, json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANON = Path.home() / "trippel/simspect-anon"
JAVA = "/opt/homebrew/opt/openjdk@17/bin/java"
S1 = REPO / "STAGE1_alloy"


def enum(model, out, cap):
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([JAVA, "-Xmx4g", "-cp", "alloy6.jar:.", "a6CountModels", str(model), str(out), str(cap)],
                       cwd=S1, capture_output=True, text=True, timeout=3600)
    return len(list(out.glob("*.xml"))), r.returncode


def fps(d):
    sys.path.insert(0, str(REPO))
    import alloy_solver_order as aso
    fp = aso.make_fingerprinter(REPO / "STAGE2_compilation")
    return sorted(fp(p) for p in sorted(d.glob("*.xml")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--families", nargs="+", default=["Footprint_6_u", "STT_6_u", "Recon_6_u"])
    ap.add_argument("--cap", type=int, default=5000)
    a = ap.parse_args()
    w = Path(a.work)
    res = {}
    sys.path.insert(0, str(S1)); sys.path.insert(0, str(S1 / "models/proposed_twophase/stage15_bound"))
    import stage_seed, make_s15_model as m15
    for fam in a.families:
        r = res[fam] = {}
        parts = {}
        for tag, base in (("orig", REPO / "STAGE1_alloy/models"), ("anon", ANON / "STAGE1_alloy/models")):
            pd = w / fam / tag / "parts"
            subprocess.run([sys.executable, str(REPO / "STAGE1_alloy/models/proposed_twophase/partition_stage1.py"),
                            str(base / f"{fam}_core_ri.als"), str(pd)], check=True, capture_output=True)
            pj = json.loads((pd / "partitions.json").read_text())
            parts[tag] = (pj["kinds"], [p["name"] for p in pj["partitions"]], pd)
        r["partitions_equal"] = parts["orig"][:2] == parts["anon"][:2]
        for k in ("k2", "k3"):
            out = {}
            for tag in ("orig", "anon"):
                pd = parts[tag][2]
                f = next(pd.glob(f"*__{k}.als"))
                n, rc = enum(f, w / fam / tag / k, a.cap)
                out[tag] = (n, rc, fps(w / fam / tag / k))
            r[k] = dict(orig=out["orig"][0], anon=out["anon"][0], rc=[out["orig"][1], out["anon"][1]],
                        fingerprints_equal=out["orig"][2] == out["anon"][2])
        core_txt = sorted((w / fam / "orig" / "k3").glob("*.txt"))
        if core_txt:
            pin = m15.pin_pred(stage_seed.parse_txt(str(core_txt[0])), "b")
            out = {}
            for tag, base in (("orig", REPO / "STAGE1_alloy/models"), ("anon", ANON / "STAGE1_alloy/models")):
                mf = w / fam / tag / "lp_pinned.als"
                mf.write_text((base / f"{fam}_lpP.als").read_text() + "\n\n" + pin + "\n")
                n, rc = enum(mf, w / fam / tag / "lp", 300)
                out[tag] = (n, rc, fps(w / fam / tag / "lp"))
            r["lpP_pinned"] = dict(core=core_txt[0].name, orig=out["orig"][0], anon=out["anon"][0],
                                   rc=[out["orig"][1], out["anon"][1]], fingerprints_equal=out["orig"][2] == out["anon"][2])
        print(fam, json.dumps(r), flush=True)
    (w / "func_alloy.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

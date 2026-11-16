#!/usr/bin/env python3
"""make_campaigns.py (agent inttwin 2026-11-16) -- the gem5 campaign configs of brief step 3: each reported taint-tracking campaign config
copied into runconfigs/inttwin_20261116/<name>_{fpr,int}.jsonc with ONLY paths.testset_dir (-> /tests/inttwin_20261116/testsets, where
the FPR corpus is a symlink wrapper and the integer twin is built) and paths.results_name (<name>_fpr / <name>_int) changed (text edit
of those two values; every gem5 block, hook, stall grid, cache setup, sample fraction and seed is byte-identical). Also writes
runconfigs/inttwin_20261116/campaigns.json (results_name, model, node, kind, commitToIEWDelay, stt flag, pair id) for
STAGE3_gem5/bugs/classify.py gate and scripts/inttwin_20261116/prep_queue.py. Verifies the parsed diff = exactly those two keys.
Run from the repo root: python3 scripts/inttwin_20261116/make_campaigns.py
"""
import json, re
from pathlib import Path

OUT = Path("runconfigs/inttwin_20261116"); TS = "/tests/inttwin_20261116/testsets"
STT, REC, STL, SPT = "STT_6_u_core_lpP_s2A", "Recon_6_u_core_lpP_s2A", "Recon_6_u_stl_core_lpP_s2A", "SPT_6_oneLP_v2_flat_ld_s2Aspt"
BC, SP = "runconfigs/bigcorpus_20261115", "runconfigs/sptrace_20261116"
# (row name, source config, FPR corpus, node, kind, stt)
ROWS = [
    ("E3_" + STT, f"{BC}/E3_{STT}.jsonc", STT, "cafe3", "eval", True),
    ("E4_" + STT, f"{BC}/E4_{STT}.jsonc", STT, "cafe3", "eval", True),
    ("E2w_" + STT, f"{BC}/E2w_{STT}.jsonc", STT, "cafe3", "eval", False),
    ("E2_" + STT, f"{BC}/E2_{STT}.jsonc", STT, "cafe1", "eval", False),
    ("E6_" + REC, f"{BC}/E6_{REC}.jsonc", REC, "cafe2", "eval", False),
    ("E2wstl_" + STL, f"runconfigs/reconstl_20261116/E2wstl_{STL}.jsonc", STL, "cafe1", "eval", False),
] + [
    (f"race_{b}_d{d}_{STT}", f"{BC}/race_{b}_d{d}_{STT}.jsonc", STT, "cafe1", "race", b.startswith("stt"))
    for b in ("stt", "sttmaster") for d in (1, 3, 4)
] + [
    (f"race_sptfence_d{d}_{STT}", f"{BC}/race_sptfence_d{d}_{STT}.jsonc", STT, "cafe2", "race", False) for d in (1, 4)
] + [
    (f"race_sptfence_d{d}_{SPT}", f"{SP}/race_sptfence_d{d}_{SPT}.jsonc", SPT, "cafe2", "race", False) for d in (1, 3, 4)
]
TWIN = {STT: STT + "int", REC: REC + "int", STL: STL + "int", SPT: SPT + "int"}


def load(t):
    return json.loads(re.sub(r"//[^\n]*", "", t))


def flat(c, p=""):
    o = {}
    for k, v in c.items():
        if isinstance(v, dict):
            o.update(flat(v, p + k + "."))
        else:
            o[p + k] = v
    return o


camps = []
for row, src, corp, node, kind, stt in ROWS:
    t = Path(src).read_text()
    src_rn = load(t)["paths"]["results_name"]
    for ver in ("fpr", "int"):
        model = corp if ver == "fpr" else TWIN[corp]
        rn = f"{row}_{ver}"
        t2, n1 = re.subn(r'("testset_dir"\s*:\s*)"[^"]*"', rf'\1"{TS}"', t, count=1)
        t2, n2 = re.subn(r'("results_name"\s*:\s*)"[^"]*"', rf'\1"{rn}"', t2, count=1)
        assert n1 == n2 == 1, (src, n1, n2)
        body = "\n".join(l for l in t2.splitlines() if not l.lstrip().startswith("//"))
        a, b = flat(load(t)), flat(load(body))
        d = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        assert d == ["paths.results_name", "paths.testset_dir"], (src, d)
        hdr = (f"// inttwin 2026-11-16 (agent inttwin): copy of {src} (results_name {src_rn}), the {ver.upper()} version of row {row}\n"
               f"// on corpus {model} ({'FPR corpus, symlink wrapper' if ver == 'fpr' else 'integer twin of ' + corp}).\n"
               f"// Changed ONLY: paths.testset_dir -> {TS}, paths.results_name -> {rn}. (paths.results_dir is unused by testrun.py,\n"
               f"// which writes <code root>/results.) Brief scripts/inttwin_20261116/BRIEF.md; results -> wiki/state/EVAL_MANIFEST.md 'Integer twins'.\n")
        (OUT / f"{rn}.jsonc").write_text(hdr + body + "\n")
        c = load(body)
        camps.append(dict(row=row, version=ver, results_name=rn, model=model, fpr_corpus=corp, node=node, kind=kind, stt=stt,
                          config=str(OUT / f"{rn}.jsonc"), source_config=src, source_results_name=src_rn,
                          commitToIEWDelay=(c.get("race_knobs") or {}).get("commitToIEWDelay"),
                          sample_fraction=c["gem5"].get("sample_fraction"), binary=c["gem5"]["binary"]))
(OUT / "campaigns.json").write_text(json.dumps(camps, indent=1) + "\n")
for c in camps:
    print(f"{c['node']:6} {c['kind']:5} {c['results_name']:58} model {c['model']:36} d={c['commitToIEWDelay']} frac={c['sample_fraction']} stt={c['stt']}")

#!/usr/bin/env python3
"""bucket_eval.py -- bucket the gated hits of one eval row into known causes (regen-lp, 2026-11-10).

Inputs (all JSON / result dirs already produced):
  --gate   eval_gate.py --examples 100000 output (per mode/kind/rmw|plain: classes with the full stem lists)
  --twin   one or more GPR-twin campaign dirs (testrun results with <mode>/<kind>/window-results.json) and their testsets'
           TWIN_STEMS.tsv via --twin-stems (make_gpr_twin.sh: faithful only for plain tests without a jmp insert)
  --stlf   recon_stlf evidence JSON(s) from rerun_hits_evidence.py on the MAIN campaign (keys "<mode>/<stem>")
  --reveal optional reveal evidence JSON(s) from reveal_check.py run on the TWIN campaign ("<mode>/<stem>" -> {"revealRequests": n})
Rules (STT builds E3/E4: the gate + S1_xmm4 static classes are final; Recon builds E2/E6, plain tests):
  no faithful twin (incl. RMW tests)  main-run STLF evidence with the A2 signature -> A2 (no twin); SSE-producer slice ->
                             R-SA-13 (static only); main-run isTainted=0 -> untainted transmitter (R-SA-13 candidate); else unexplained
  twin held                  SSE-producer slice -> R-SA-13; xmm / GPR slice -> R-SA-13 via FP elsewhere (e2-losttaint:
                             e.g. an SSE load feeding idiv's implicit divisor, missed by the slice tool)
  twin hit, ld               main-run STL_CHECK tainted+speculative+forwarded+ready in window -> A2 STLF bypass;
                             main-run isTainted=0 -> R-SA-13 in the main run, and in the twin a reveal artifact (E2LT-3) if
                             the twin rerun has revealRequests > 0, else
                             R-SA-13 main / R-SA-9 twin (E2LT-1); not reproduced -> twin-hit(not reproduced)
  twin hit, br_x             R-SA-8 candidate (E2LT-2 shape: x86 mov false dependency; not verified per test)
Usage: bucket_eval.py --row E6_... --gate g.json --twin d1 d2 --twin-stems t1.tsv t2.tsv --stlf e1.json [e2.json]
       [--reveal r.json] [--json out] [--examples 3]"""
import argparse, collections, glob, json, os
ap = argparse.ArgumentParser(); ap.add_argument("--row", required=True); ap.add_argument("--gate", required=True)
ap.add_argument("--twin", nargs="*", default=[]); ap.add_argument("--twin-stems", nargs="*", default=[])
ap.add_argument("--stlf", nargs="*", default=[]); ap.add_argument("--reveal", nargs="*", default=[])
ap.add_argument("--json"); ap.add_argument("--examples", type=int, default=3); a = ap.parse_args()
G = json.load(open(a.gate))["campaigns"][a.row]
twin, tstems = {}, set()
for d in a.twin:
    for f in glob.glob(os.path.join(os.path.realpath(d), "mispredict_*", "*", "window-results.json")):
        m = f.split("/")[-3]; x = json.load(open(f)); recs = x if isinstance(x, list) else (x.get("results") or list(x.values()))
        for r in recs:
            if isinstance(r, dict):
                twin[(m, r["name"].split("__")[0])] = (bool(r.get("issued_in_window")), r.get("status"))
for t in a.twin_stems:
    tstems |= {tuple(l.split("\t")) for l in open(t).read().splitlines()[1:] if l}
stlf = {}
for f in a.stlf:
    stlf.update(json.load(open(f)))
rev = {}
for f in a.reveal:
    rev.update(json.load(open(f)))
stt = a.row.split("_")[0] in ("E3", "E4")
out = {}
for key, v in G.items():
    if key.endswith("/_merge") or "classes" not in v:
        continue
    mode, kind, rp = key.split("/")
    B = collections.Counter(); EX = collections.defaultdict(list)
    for cl, stems in v["examples"].items():
        for s in stems:
            if cl.startswith("disq"):
                b = cl
            elif stt:
                b = cl
            elif rp == "rmw" or (mode, s) not in tstems:
                sfx = ", RMW" if rp == "rmw" else ""
                e = stlf.get(f"{mode}/{s}") if kind == "ld" else None
                if e is not None and e.get("reproduced", True) and "isTainted=1 isSpeculative=1" in (e.get("stl") or "") \
                        and e.get("fwd") and e.get("ready_in_window"):
                    b = f"A2 STLF bypass (main-run evidence, no twin{sfx})"
                elif cl.startswith("R-SA-13"):
                    b = f"R-SA-13 (static only{sfx})"
                elif e is not None and "isTainted=0" in (e.get("stl") or ""):
                    b = f"untainted transmitter, no twin (R-SA-13 candidate{sfx})"
                elif rp == "rmw" and e is not None and "isTainted=1 isSpeculative=1" in (e.get("stl") or "") and not e.get("fwd"):
                    b = "check_ld RMW artifact (scores the RMW's leading limm micro-op; delay unit holds the load; RL-10 resolved)"
                elif e is not None and not e.get("reproduced", True):
                    b = f"no twin, not reproduced{sfx}"
                else:
                    b = f"unexplained(no twin{sfx}: {cl}{'' if e is None else ', evidence: ' + (e.get('stl') or '')[-28:]})"
            else:
                t = twin.get((mode, s))
                if t is None or t[1] != "ok":
                    b = "twin missing/error"
                elif not t[0]:
                    b = "R-SA-13" if cl.startswith("R-SA-13") else "R-SA-13 via FP elsewhere (twin held; e2-losttaint idiv-divisor case)"
                elif kind == "br_x":
                    b = "R-SA-8 candidate (br_x twin hit; E2LT-2)"
                else:
                    e = stlf.get(f"{mode}/{s}")
                    if e is None:
                        b = "twin-hit ld, no evidence"
                    elif not e.get("reproduced", True):
                        b = "twin-hit ld, not reproduced"
                    elif "isTainted=1 isSpeculative=1" in (e.get("stl") or "") and e.get("fwd") and e.get("ready_in_window"):
                        b = "A2 STLF bypass"
                    elif "isTainted=0" in (e.get("stl") or ""):
                        r = rev.get(f"{mode}/{s}")
                        b = ("R-SA-13 main / reveal artifact in twin (E2LT-3)" if r and r.get("revealRequests", 0) > 0 else
                             "R-SA-13 main / R-SA-9 twin (E2LT-1)" if r is not None else "isTainted=0 (reveal not checked)")
                    else:
                        b = "twin-hit ld, other STL signature"
            B[b] += 1
            if len(EX[b]) < a.examples:
                EX[b].append(s)
    out[key] = dict(tests=v["tests"], raw=v["raw_hits"], gated=v["gated_hits"], buckets=dict(B), examples=dict(EX))
for k, e in out.items():
    print(f"{k:40} tests {e['tests']:5} raw {e['raw']:4} gated {e['gated']:4}")
    for b, n in sorted(e["buckets"].items(), key=lambda x: -x[1]):
        print(f"      {n:5}  {b}" + (f"   e.g. {e['examples'][b]}" if not b.startswith(("disq", "R-SA-13", "S1", "A2")) else ""))
if a.json:
    json.dump(dict(row=a.row, buckets=out), open(a.json, "w"), indent=1)

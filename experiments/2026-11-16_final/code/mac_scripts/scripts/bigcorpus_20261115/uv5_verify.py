#!/usr/bin/env python3
"""uv5_verify.py -- check one A-UV5 (CleanupSpec over-cleaning) candidate the way diligence check 1 did (agent bigcorpus, 2026-11-16):
(1) from the KEPT trace (read-only): for every `L1D:cleanup_inv` line, the squashed S that owns it (seq, pc, never retires), S's L1D fill
of that line, every older instruction U that hits the line between S's fill and the cleanup and retires (seq, pc, its x86 form from
pipeview), the L2 cleanup_inv and DIR events, the forced branch(es) and their held resolve; (2) reruns the exact test --reruns times with
firstdet_stream.py --only-file on the same T2g config (same draw: cache setup and timing point are seeded from the stem), TMPDIR=/tmp,
then classify_hits.py, and reports hit / terms / cache setup / timing point / class per rerun. Writes <out>/verify.json (+ rerun dirs).
Usage (code root): uv5_verify.py --run <firstdet run dir> --config <T2g cfg> --model <corpus> --mode M --stem S --out <dir> [--reruns 2]
"""
import argparse, gzip, json, re, subprocess, sys, os
from pathlib import Path
sys.path.insert(0, "STAGE3_gem5"); import gem5_common as gc  # noqa: E402

EV = re.compile(r"^O3PipeView:simspect:(\d+):(L1D|L2|DIR|BR|ROB):([a-z_]+):line=([^:]*):seq=([^:]*):pc=([^:]*):(.*)$")


def chain(trace):
    lines = gzip.open(trace, "rt", errors="replace").read().splitlines()
    tmp = Path(f"/tmp/uv5v_{os.getpid()}.txt"); tmp.write_text("\n".join(lines))
    pv = gc.parse_pipeview_by_seq(tmp); tmp.unlink()
    ev = [m.groups() for m in (EV.match(l) for l in lines) if m]
    disasm = {}
    for l in lines:
        m = re.match(r"^O3PipeView:fetch:\d+:(0x[0-9a-f]+):\d+:(\d+):\s+(.*)$", l)
        if m:
            disasm[int(m.group(2))] = m.group(3).strip()
    out = {"branches": [dict(tick=int(t), ev=e, seq=s, pc=p, rest=r[:160]) for t, u, e, ln, s, p, r in ev if u == "BR" and e in ("predict_force", "resolve_hold")],
           "cleanups": []}
    for t, u, e, ln, s, p, r in ev:
        if not (u == "L1D" and e == "cleanup_inv"):
            continue
        S = int(s); tc = int(t)
        fill = next(((int(t2), r2) for t2, u2, e2, l2, s2, p2, r2 in ev if u2 == "L1D" and e2 == "fill" and l2 == ln and s2 == s), None)
        users = []
        if fill:
            for t2, u2, e2, l2, s2, p2, r2 in ev:
                if u2 == "L1D" and e2 == "hit" and l2 == ln and fill[0] <= int(t2) <= tc and s2.isdigit() and int(s2) < S:
                    rec = pv.get(int(s2)) or {}
                    users.append(dict(seq=int(s2), pc=p2, tick=int(t2), retire=rec.get("retire"), insn=disasm.get(int(s2)), rest=r2[:120]))
        l2c = [dict(tick=int(t2), unit=u2, ev=e2, rest=r2[:120]) for t2, u2, e2, l2, s2, p2, r2 in ev if l2 == ln and s2 == s and u2 in ("L2", "DIR") and int(t2) >= tc]
        recS = pv.get(S) or {}
        out["cleanups"].append(dict(line=ln, S=dict(seq=S, pc=p, retire=recS.get("retire"), insn=disasm.get(S)), cleanup_inv_tick=tc,
                                    S_fill=dict(tick=fill[0], rest=fill[1][:120]) if fill else None,
                                    U_hits_retired=[x for x in users if x.get("retire")], U_hits_all=len(users), after=l2c[:4]))
    out["over_clean_chains"] = [c for c in out["cleanups"] if c["U_hits_retired"] and not c["S"]["retire"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("--run", "--config", "--model", "--mode", "--stem", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--reruns", type=int, default=2); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    row = next(json.loads(l) for l in open(f"{a.run}/results.jsonl") if f'"{a.stem}"' in l and f'"{a.mode}"' in l)
    res = dict(key=f"{a.mode}/{a.stem}", campaign_row={k: row.get(k) for k in ("hit", "terms_fired", "cache_setup", "timing_point", "stall_points", "exec_path")})
    res["trace"] = chain(f"{a.run}/traces/{a.mode}/{a.stem}.pipeview.txt.gz")
    (out / "pair.tsv").write_text(f"{a.mode}\t{a.stem}\n"); res["reruns"] = []
    env = dict(os.environ, TMPDIR="/tmp", SIMSPECT_GEM5_TIMEOUT_S="900")
    for i in range(1, a.reruns + 1):
        d = out / f"rerun_{i}"
        subprocess.run([sys.executable, "STAGE3_gem5/timing/firstdet_stream.py", "--code-root", os.getcwd(), "--config", a.config, "--model", a.model,
                        "--out", str(d), "--seed", "20261109", "--parallel", "1", "--only-file", str(out / "pair.tsv"), "--poll", "5"],
                       env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3000)
        subprocess.run([sys.executable, "STAGE3_gem5/timing/classify_hits.py", str(d), "--defense", "cleanupspec", "--stage3", "STAGE3_gem5",
                        "--testset", str(Path(a.run).parents[1] / "testsets" / a.model), "--jobs", "1"], env=env,
                       stdout=open(d / "classify.stdout", "w"), stderr=subprocess.STDOUT)
        r = next((json.loads(l) for l in open(d / "results.jsonl")), {}) if (d / "results.jsonl").exists() else {}
        cl = next((json.loads(l) for l in open(d / "classes.jsonl")), {}) if (d / "classes.jsonl").exists() else {}
        res["reruns"].append(dict(dir=str(d), hit=r.get("hit"), terms=r.get("terms_fired"), cache_setup=r.get("cache_setup"),
                                  timing_point=r.get("timing_point"), sigs=cl.get("sigs")))
    res["reproduced"] = all(x.get("sigs") and "UV5" in x["sigs"] for x in res["reruns"])
    json.dump(res, open(out / "verify.json", "w"), indent=1)
    c = res["trace"]["over_clean_chains"]
    print(json.dumps(dict(key=res["key"], row=res["campaign_row"], chains=[dict(line=x["line"], S=x["S"], S_fill=(x["S_fill"] or {}).get("tick"),
          U=[(u["seq"], u["pc"], u["insn"], u["tick"], u["retire"]) for u in x["U_hits_retired"]], cleanup=x["cleanup_inv_tick"],
          after=[(y["tick"], y["unit"], y["ev"]) for y in x["after"]]) for x in c], reruns=res["reruns"], reproduced=res["reproduced"]), indent=None))


if __name__ == "__main__":
    main()

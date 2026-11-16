#!/usr/bin/env python3
"""classify_cs_rmw.py: CleanupSpec first detection on the RMW fanout corpus
STT_6_fv2fp_rmw (firstdet-cleanupspec, 2026-11-09). Runs AFTER classify_hits.py
--defense cleanupspec on a timing_driver.py output dir and refines its
per-item causes so UV3 and E->M are credited only to the test's OWN RMW
transmitter (Anna 2026-11-09: hits caused by the harness padding RMW, H-PAD,
do not count; they are reported as an excluded bucket).

    python3 classify_cs_rmw.py <timing_out_dir> --rmw-stems <corpus>/rmw_stems.tsv \
        --testset <corpus>   [--stage3 <code>/STAGE3_gem5]

Inputs (all written by timing_driver.py / classify_hits.py, read-only here):
  results.jsonl, raw/<mode>/<stem>.json (checker record: xmit_pc, offending),
  traces/<mode>/<stem>.pipeview.txt.gz, cs_evidence/diagnostics/cleanupspec_skip_evidence.json
  (per offending item: cause UV4_split / UV5_older_load / CS1_older_store_upgrade /
  EM_upgrade_squashed / unattributed), and <testset>/<mode>/ann/<stem>.ann.json.

Refinement per offending item (existing rules unchanged; only `unattributed` and
`EM_upgrade_squashed` items are looked at again):
  UV3            item is `unattributed`; every offending event is a fill with req=st
                 (L1D msg=ST or L2 msg=GETX) on the item's line by one actor seq S that
                 never retired, the trace has `L1D:cleanup_skip line=<line> seq=S
                 why=nohitinfo`, and S's pc == the record's xmit_pc and the stem is an RMW
                 stem (rmw_stems.tsv). Same event rule as triage/uv3_rmw_evidence.py judge().
  UV3_padding    the same chain but the actor is the H-PAD padding RMW: its pc lies after
                 the xmit and its fetch disassembly (by pc) is ADD_M_R (`00 00` = add
                 %al,(%rax); BUGS.md H-PAD). EXCLUDED (Anna 2026-11-09).
  UV3_other_actor  the same chain by any other actor (reported, not credited).
  EM_rmw         `EM_upgrade_squashed` whose E->M upgrader (L1D hit st=E nst=M req=st on
                 the line) is at xmit_pc of an RMW stem: CS-EM by the test's own RMW
                 (non-AMuLeT, reported separately).
  EM_padding     the upgrader is the H-PAD padding RMW (rule above). EXCLUDED.
  EM_other       any other upgrader.
UV4 / UV5 / CS1 keep classify_hits.py's attribution.

Writes <out>/classes_rmw.jsonl and <out>/first_detection_rmw.json (same metrics as
classify_hits.py: first position, K of N over the contiguous finished prefix,
(N+1)/(K+1), CPU-s), log <out>/classify_cs_rmw.log.
"""
import argparse, collections, gzip, json, sys, time, traceback
from pathlib import Path

PREFIX = "O3PipeView:simspect:"
TARGETS = ["UV3", "UV4", "UV5"]
SEPARATE = ["CS1", "EM_rmw", "EM_other", "UV3_other_actor", "unattributed"]
EXCLUDED = ["UV3_padding", "EM_padding"]


def addr_fields(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out += addr_fields(v)
            elif (k == "addr" or k.endswith("_addr")) and isinstance(v, int):
                out.append(v)
    elif isinstance(obj, list):
        for v in obj:
            out += addr_fields(v)
    return out


def parse_trace(gz: Path):
    by_id, evs, committed, fetch = {}, [], set(), {}
    dis_by_pc = {}
    cur = None
    with gzip.open(gz, "rt", errors="replace") as fh:
        for ln in fh:
            if ln.startswith(PREFIX):
                p = ln.rstrip("\n").split(":")
                kv = dict(x.split("=", 1) for x in p[5:] if "=" in x)
                kv.update(tick=int(p[2]), struct=p[3], kind=p[4])
                evs.append(kv)
                if kv.get("id", "-") not in ("-", None):
                    try:
                        by_id[int(kv["id"])] = kv
                    except ValueError:
                        pass
            elif ln.startswith("O3PipeView:fetch:"):
                q = ln.rstrip("\n").split(":")
                try:
                    cur = int(q[5])
                    fetch[cur] = (int(q[3], 16), ":".join(q[6:]))
                    dis_by_pc.setdefault(int(q[3], 16), ":".join(q[6:]).split(":")[0].strip())
                except (ValueError, IndexError):
                    cur = None
            elif ln.startswith("O3PipeView:retire:") and cur is not None:
                try:
                    if int(ln.split(":")[2]) > 0:
                        committed.add(cur)
                except ValueError:
                    pass
                cur = None
    return by_id, evs, committed, dis_by_pc


def is_padding(pc: int, xpc, dis_by_pc) -> bool:
    """H-PAD: the actor's macro-op (looked up by pc in any O3PipeView fetch record; the
    actor's own seq often has none) is ADD_M_R and lies after the transmitter. The
    source corpus has no memory-destination ALU op (grep of all STT_6_fv2fp taken .s,
    2026-11-09), so ADD_M_R after the xmit can only be the `00 00` padding past .text.
    The stored annotation cannot bound the code: cold cache_setup shifts every pc."""
    return xpc is not None and pc > xpc and dis_by_pc.get(pc) == "ADD_M_R"


def refine(item, rec, tr, rmw, max_ann):
    by_id, evs, committed, fetch = tr
    xpc = int(rec["xmit_pc"], 16) if rec.get("xmit_pc") else None
    cause = item.get("cause")
    if cause == "unattributed" and item.get("term") == "under_clean":
        es = [by_id.get(int(i)) for i in item.get("event_ids") or []]
        if es and all(e is not None for e in es):
            ok = all(e["kind"] == "fill" and e.get("req") == "st" and e.get("line") == item["line"]
                     and e.get("msg") == {"L1D": "ST", "L2": "GETX"}.get(e["struct"]) for e in es)
            seqs = {e.get("seq") for e in es}
            pcs = {e.get("pc") for e in es}
            if ok and len(seqs) == 1 and len(pcs) == 1 and None not in seqs | pcs and "-" not in seqs | pcs:
                S, pc = int(seqs.pop()), int(pcs.pop(), 16)
                skip = any(e["struct"] == "L1D" and e["kind"] == "cleanup_skip" and e.get("line") == item["line"]
                           and e.get("seq") == str(S) and e.get("why") == "nohitinfo" for e in evs)
                if skip and S not in committed:
                    if pc == xpc and rmw:
                        return "UV3", f"S={S} pc={hex(pc)} = xmit RMW; fill req=st; cleanup_skip nohitinfo"
                    if is_padding(pc, xpc, fetch):
                        return "UV3_padding", f"S={S} pc={hex(pc)} ADD_M_R after xmit {rec.get('xmit_pc')} (H-PAD)"
                    return "UV3_other_actor", f"S={S} pc={hex(pc)} xmit={rec.get('xmit_pc')} rmw={rmw}"
        return "unattributed", item.get("why", "")
    if cause == "EM_upgrade_squashed":
        ups = [e for e in evs if e["struct"] == "L1D" and e["kind"] == "hit" and e.get("st") == "E"
               and e.get("nst") == "M" and e.get("req") == "st"]
        lines = {item["line"]}
        for i in item.get("event_ids") or []:
            e = by_id.get(int(i))
            if e and e.get("line"):
                lines.add(e["line"])          # victim items: the upgraded line is S's fill line
        ups = [e for e in ups if e.get("line") in lines and e.get("seq") not in (None, "-")
               and int(e["seq"]) not in committed]
        pcs = {int(e["pc"], 16) for e in ups if e.get("pc") not in (None, "-")}
        if len(pcs) == 1:
            pc = pcs.pop()
            U = int(ups[0]["seq"])
            if pc == xpc and rmw:
                return "EM_rmw", f"U={U} pc={hex(pc)} = xmit RMW"
            if is_padding(pc, xpc, fetch):
                return "EM_padding", f"U={U} pc={hex(pc)} ADD_M_R after xmit {rec.get('xmit_pc')} (H-PAD)"
            return "EM_other", f"U={U} pc={hex(pc)}"
        return "EM_other", f"{len(pcs)} distinct squashed upgrader pcs"
    name = {"UV4_split": "UV4", "UV5_older_load": "UV5", "CS1_older_store_upgrade": "CS1"}
    return name.get(cause, cause), item.get("why", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--rmw-stems", required=True)
    ap.add_argument("--testset", required=True)
    a = ap.parse_args()
    out, ts = Path(a.out).resolve(), Path(a.testset)
    log = open(out / "classify_cs_rmw.log", "a")
    log.write(f"== start {time.strftime('%F %T')} out={out} rmw={a.rmw_stems}\n")
    rmw = {tuple(l.split("\t")[:2]) for l in Path(a.rmw_stems).read_text().splitlines()[1:] if l.strip()}
    rows = {}
    for l in (out / "results.jsonl").read_text().splitlines():
        try:
            r = json.loads(l); rows[r["idx"]] = r
        except Exception:
            pass
    ev = json.loads((out / "cs_evidence" / "diagnostics" / "cleanupspec_skip_evidence.json").read_text())
    cls = {}
    for i, r in rows.items():
        if not r.get("hit"):
            continue
        key = f"{r['mode']}/{r['stem']}"
        is_rmw = (r["mode"], r["stem"]) in rmw
        try:
            rec = json.loads((out / "raw" / r["mode"] / f"{r['stem']}.json").read_text())
            gz = out / "traces" / r["mode"] / f"{r['stem']}.pipeview.txt.gz"
            ann = json.loads((ts / r["mode"] / "ann" / f"{r['stem']}.ann.json").read_text())
            max_ann = max(addr_fields(ann) or [0])
            if key not in ev or not gz.exists():
                cls[i] = ({"no_evidence"}, [])
                continue
            tr = parse_trace(gz)
            items = []
            for v in ev[key]["variants"]:
                for it in v["items"]:
                    c, why = refine(it, rec, tr, is_rmw, max_ann)
                    items.append(dict(struct=it.get("struct"), line=it.get("line"), term=it.get("term"),
                                      cause=c, why=why))
            cls[i] = ({x["cause"] for x in items}, items)
        except Exception:
            log.write(f"ERROR idx={i} {key}\n{traceback.format_exc()}\n")
            cls[i] = ({"classify_error"}, [])
    with open(out / "classes_rmw.jsonl", "w") as f:
        for i in sorted(cls):
            r = rows[i]
            f.write(json.dumps(dict(idx=i, mode=r["mode"], stem=r["stem"], kind=r.get("kind"),
                                    rmw=(r["mode"], r["stem"]) in rmw, cache_setup=r.get("cache_setup"),
                                    sigs=sorted(cls[i][0]), items=cls[i][1])) + "\n")
    N = 0
    while N in rows:
        N += 1
    cum_g = cum_t = 0.0
    first, K = {}, collections.Counter()
    st = collections.Counter()
    n_rmw = 0
    for i in range(N):
        r = rows[i]
        cum_g += r.get("gem5_cpu_s") or 0
        cum_t += r.get("total_cpu_s") or 0
        st[r.get("status")] += 1
        n_rmw += (r["mode"], r["stem"]) in rmw
        for s in cls.get(i, (set(), []))[0]:
            K[s] += 1
            if s not in first:
                first[s] = dict(first_idx=i, tests_to_first=i + 1, stem=r["stem"], mode=r["mode"],
                                cum_gem5_cpu_s=round(cum_g, 2), cum_total_cpu_s=round(cum_t, 2))

    def sig(s):
        return dict(first.get(s, {}), K=K[s], N=N, expected_tests_to_first=round((N + 1) / (K[s] + 1), 2),
                    expected_gem5_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_g / N, 2) if N else None,
                    expected_total_cpu_s_to_first=round((N + 1) / (K[s] + 1) * cum_t / N, 2) if N else None)
    res = dict(N_prefix=N, n_rows=len(rows), n_rmw_in_prefix=n_rmw, status=dict(st),
               hits=sum(1 for i in range(N) if rows[i].get("hit")),
               gem5_cpu_s_per_test=round(cum_g / N, 3) if N else None,
               total_cpu_s_per_test=round(cum_t / N, 3) if N else None,
               targets={s: sig(s) for s in TARGETS},
               separate_non_amulet={s: sig(s) for s in SEPARATE},
               excluded_padding={s: sig(s) for s in EXCLUDED},
               other={s: sig(s) for s in sorted(set(K) - set(TARGETS) - set(SEPARATE) - set(EXCLUDED))})
    (out / "first_detection_rmw.json").write_text(json.dumps(res, indent=1))
    log.write(json.dumps(res) + f"\n== end {time.strftime('%F %T')}\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    sys.exit(main())

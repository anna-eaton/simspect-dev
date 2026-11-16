"""Shared trace / record readers for the cause modules. No verdicts here: these only extract facts.

Every function is moved verbatim from the old classifiers (reference copies stay in place until Anna switches over):
  ev_pc, text_end, gunzip_tmp                 STAGE3_gem5/timing/classify_hits.py
  cs_parse, cs_sel, cs_squash_seq, _int       STAGE3_gem5/timing/cleanupspec_skip_evidence.py (parse, _sel, _squash_seq)
  rmw_parse_trace, addr_fields                STAGE3_gem5/timing/classify_cs_rmw.py (parse_trace, addr_fields)
The two CleanupSpec trace parsers differ on purpose (cs_parse also counts gem5 Commit-trace lines as committed;
rmw_parse_trace does not) and are kept separate so each rule sees exactly the facts it saw before.
"""
import gzip
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

PREFIX = "O3PipeView:simspect:"
COMMIT_RE = re.compile(r"^\s*(\d+): .*Committing instruction with \[sn:(\d+)\]")


# ── classify_hits.py helpers ─────────────────────────────────────────────────

def text_end(testset: Path, mode: str, stem: str, raw: dict, gc) -> int:
    """End of .text of the binary that ran (H-PAD): objdump -h of the test rebuilt warm plus the record's
    cache_setup_info.delta when a cache_setup rewrote it."""
    s = testset / mode / "asm" / f"{stem}.s"
    with tempfile.TemporaryDirectory(prefix="hpad_") as td:
        b = gc.build_binary(s, Path(td), cache_setup_ok=True)
        out = subprocess.check_output(["objdump", "-h", str(b)], text=True)
    m = re.search(r"^\s*\d+\s+\.text\s+([0-9a-f]+)\s+([0-9a-f]+)", out, re.M)
    end = int(m.group(2), 16) + int(m.group(1), 16)
    return end + int((raw.get("cache_setup_info") or {}).get("delta") or 0)


def ev_pc(e, byseq):
    pc = e.get("pc")
    if isinstance(pc, int):
        return pc
    if isinstance(pc, str) and pc.startswith("0x"):
        return int(pc, 16)
    seq = e.get("seq")
    try:
        seq = int(seq) if seq is not None else None
    except (TypeError, ValueError):
        seq = None
    r = byseq.get(seq) if seq is not None else None
    return r["pc"] if r else None


def gunzip_tmp(gz: Path) -> Path:
    fd, p = tempfile.mkstemp(suffix=".pipeview.txt")
    with gzip.open(gz, "rb") as fi, os.fdopen(fd, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    return Path(p)


# ── cleanupspec_skip_evidence.py helpers ─────────────────────────────────────

def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def cs_parse(fh):
    """-> (events, by_id, committed). Verbatim cleanupspec_skip_evidence.parse."""
    evs, by_id, committed, cur = [], {}, set(), None
    for ln in fh:
        if ln.startswith(PREFIX):
            p = ln.rstrip("\n").split(":")
            kv = dict(x.split("=", 1) for x in p[5:] if "=" in x)
            kv.update(tick=int(p[2]), struct=p[3], kind=p[4], seqn=_int(kv.get("seq")))
            evs.append(kv)
            if _int(kv.get("id")) is not None:
                by_id[int(kv["id"])] = kv
        elif ln.startswith("O3PipeView:fetch:"):
            q = ln.split(":")
            cur = _int(q[5]) if len(q) > 5 else None
        elif ln.startswith("O3PipeView:retire:") and cur is not None:
            if (_int(ln.split(":")[2]) or 0) > 0:
                committed.add(cur)
            cur = None
        elif "Committing instruction with [sn:" in ln:
            m = COMMIT_RE.match(ln)
            if m:
                committed.add(int(m.group(2)))
    return evs, by_id, committed


def cs_sel(evs, struct, kind, **kw):
    return [e for e in evs if e["struct"] == struct and e["kind"] == kind
            and all(e.get(k) == v for k, v in kw.items())]


def cs_squash_seq(evs, sq):
    q = [e["seqn"] for e in evs if e["struct"] == "ROB" and e["kind"] == "squash" and e.get("sq") == sq]
    return q[0] if q else None


def cs_actor(item, tr):
    """Common precondition of every CleanupSpec item rule (verbatim head of the old judge()):
    -> (es, S, None) when every offending event id is in the trace and the actor S = first event's seq never committed,
    else (None, None, reason)."""
    evs, by_id, committed = tr
    ids = item.get("event_ids") or []
    es = [by_id[i] for i in ids if i in by_id]
    if not es or len(es) != len(ids):
        return None, None, "offending event id missing from trace"
    e0 = es[0]
    S = e0["seqn"]
    if S is None or S in committed:
        return None, None, f"actor seq {e0.get('seq')} committed or unknown"
    return es, S, None


def cs_is_victim_item(item, es, S):
    """Shape A of the old judge(): under_clean item, every event an evict of the item's line by S."""
    return item["term"] == "under_clean" and all(
        e["kind"] == "evict" and e.get("victim") == item["line"] and e["seqn"] == S for e in es)


def cs_is_install_item(item, es, S):
    """Shape B of the old judge(): under_clean item, every event a fill of the item's line by S."""
    return item["term"] == "under_clean" and all(
        e["kind"] == "fill" and e.get("line") == item["line"] and e["seqn"] == S for e in es)


def cs_split_seqs(evs):
    return {e["seqn"] for e in cs_sel(evs, "L1D", "cleanup_skip", why="split")}


def cs_victim_chain(item, es, S, tr):
    """Facts of the old judge() victim-item chain after the split test (shared by CS1 and EM_upgrade).
    -> dict(ok=True, U, Q, chain) when: V (the item's line) was not restored by S, exactly one `cleanup_skip
    line=L seq=S ev=Inv_CLEANUP st=M`, exactly one `L1D:hit line=L st=E nst=M` between S's fill and that skip with
    req=st, the skip's squash seq Q is known and S > Q; else dict(ok=False, why)."""
    evs, by_id, committed = tr
    e0 = es[0]
    line = item["line"]
    L = e0.get("line")
    if cs_sel(evs, "L1D", "cleanup_restore", line=line, seq=str(S)):
        return dict(ok=False, why="victim restored by S")
    sk = [e for e in cs_sel(evs, "L1D", "cleanup_skip", line=L, seq=str(S))
          if e.get("ev") == "Inv_CLEANUP" and e.get("st") == "M"]
    if len(sk) != 1:
        return dict(ok=False, why=f"S={S}: {len(sk)} Inv_CLEANUP st=M skips on {L}")
    t_fill, t_sk = e0["tick"], sk[0]["tick"]
    Q = cs_squash_seq(evs, sk[0].get("sq"))
    ups = [e for e in cs_sel(evs, "L1D", "hit", line=L, st="E", nst="M") if t_fill <= e["tick"] <= t_sk]
    if len(ups) != 1 or ups[0].get("req") != "st" or Q is None or not (S > Q):
        return dict(ok=False, why=f"S={S}: {len(ups)} E->M upgraders, squash seq {Q}")
    U = ups[0]["seqn"]
    chain = (f"S={S} fill {L} @{t_fill} evicts V={line}; U={U} st E->M @{ups[0]['tick']} pc={ups[0].get('pc')}; "
             f"cleanup_skip Inv_CLEANUP st=M @{t_sk} (sq={sk[0].get('sq')}, squash seq {Q}); V never restored")
    return dict(ok=True, U=U, Q=Q, chain=chain)


# ── classify_cs_rmw.py helpers ───────────────────────────────────────────────

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


def rmw_parse_trace(gz: Path):
    """-> (by_id, evs, committed, dis_by_pc). Verbatim classify_cs_rmw.parse_trace."""
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


def rmw_uv3_chain(item, tr):
    """Facts of the old classify_cs_rmw UV3 chain (shared by UV3, UV3_padding, UV3_other_actor):
    an `unattributed` under_clean item whose every offending event is a fill with req=st (L1D msg=ST / L2 msg=GETX) on
    the item's line by one actor seq S with one pc, the trace has `L1D:cleanup_skip line=<line> seq=S why=nohitinfo`,
    and S never retired. -> (S, pc) or None."""
    by_id, evs, committed, fetch = tr
    if item.get("cause") != "unattributed" or item.get("term") != "under_clean":
        return None
    es = [by_id.get(int(i)) for i in item.get("event_ids") or []]
    if not (es and all(e is not None for e in es)):
        return None
    ok = all(e["kind"] == "fill" and e.get("req") == "st" and e.get("line") == item["line"]
             and e.get("msg") == {"L1D": "ST", "L2": "GETX"}.get(e["struct"]) for e in es)
    seqs = {e.get("seq") for e in es}
    pcs = {e.get("pc") for e in es}
    if ok and len(seqs) == 1 and len(pcs) == 1 and None not in seqs | pcs and "-" not in seqs | pcs:
        S, pc = int(seqs.pop()), int(pcs.pop(), 16)
        skip = any(e["struct"] == "L1D" and e["kind"] == "cleanup_skip" and e.get("line") == item["line"]
                   and e.get("seq") == str(S) and e.get("why") == "nohitinfo" for e in evs)
        if skip and S not in committed:
            return S, pc
    return None


def rmw_em_upgraders(item, tr):
    """Facts of the old classify_cs_rmw EM chain: the squashed E->M upgraders (L1D hit st=E nst=M req=st, never
    committed) of the item's line or of the fill line of any of its events. -> (set of their pcs, [upgrader events])."""
    by_id, evs, committed, fetch = tr
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
    return pcs, ups

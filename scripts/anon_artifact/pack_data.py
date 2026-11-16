import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

SNAP = Path("/Users/annaeaton/trippel/simspect/experiments/2026-11-16_final")
OLD = Path("/Users/annaeaton/trippel/simspect/experiments/2026-11-10_footprint_vs_amulet/results/amulet_t5")
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
R = SNAP / "results"
FD3 = R / "bigcorpus/cafe3/firstdet"
FD1 = R / "bigcorpus/cafe1/firstdet"
FD2 = R / "bigcorpus/cafe2/firstdet"
TM = R / "timing/cafe3"
DROP = {"trace", "workdir", "criterion_path", "log", "pid", "dir", "testset", "host", "user", "hostname"}
BAD = re.compile(r"anna|eaton|trippel|caroline|stanford|/afs|cafe\d|macbook|/users/|/home/|/tests/|/work/|/scr/|claude|anthropic", re.I)
MTIME = 1794787200
HEX = re.compile(r"\b[0-9a-f]{8,}\b")


def bad(t):
    return BAD.search(HEX.sub("", t))


def scrub(o):
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items() if k not in DROP}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    if isinstance(o, str) and (o.startswith("/") or bad(o)):
        raise SystemExit(f"unscrubbed string: {o[:120]}")
    return o


def rd(p):
    p = Path(p)
    if not p.exists() and Path(str(p) + ".gz").exists():
        p = Path(str(p) + ".gz")
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt") as f:
        return f.read()


def wbytes(dst, data):
    dst = OUT / dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    if str(dst).endswith(".gz"):
        with open(dst, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as g:
                g.write(data)
    else:
        dst.write_bytes(data)


def wjson(dst, obj):
    wbytes(dst, (json.dumps(scrub(obj), indent=1) + "\n").encode())


def wjsonl(dst, src):
    lines = [json.dumps(scrub(json.loads(l))) for l in rd(src).splitlines() if l.strip()]
    wbytes(dst, ("\n".join(lines) + "\n").encode())


def wtext(dst, src, check=True, cols=0):
    t = rd(src)
    if cols:
        t = "".join("\t".join(l.split("\t")[:cols]) + "\n" for l in t.splitlines() if l.strip())
    if check and bad(t):
        raise SystemExit(f"identity in {src}")
    wbytes(dst, t.encode())


def tarball(name, top, members):
    dst = OUT / "corpus" / f"{name}.tar.xz"
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as fo:
        xz = subprocess.Popen(["xz", "-T0", "-9", "-c"], stdin=subprocess.PIPE, stdout=fo)
        with tarfile.open(fileobj=xz.stdin, mode="w|", format=tarfile.PAX_FORMAT) as tf:
            dirs = set()
            for arc, data in members:
                parts = Path(top, arc).parts
                for i in range(1, len(parts)):
                    d = "/".join(parts[:i])
                    if d not in dirs:
                        dirs.add(d)
                        ti = tarfile.TarInfo(d)
                        ti.type, ti.mode, ti.mtime = tarfile.DIRTYPE, 0o755, MTIME
                        tf.addfile(ti)
                ti = tarfile.TarInfo(f"{top}/{arc}")
                ti.size, ti.mode, ti.mtime = len(data), 0o644, MTIME
                tf.addfile(ti, io.BytesIO(data))
        xz.stdin.close()
        if xz.wait():
            raise SystemExit("xz failed")
    print(name, dst.stat().st_size, flush=True)


def corpus_members(src, with_xml, ready):
    src = Path(src)
    yield "READY", ready.encode()
    for f in ("MANIFEST.tsv", "rmw_stems.tsv", "jmp_stems.tsv"):
        if (src / f).exists():
            yield f, (src / f).read_bytes()
    subs = (["xml"] if with_xml else []) + [f"{m}/{k}" for m in ("mispredict_not_taken", "mispredict_taken") for k in ("asm", "ann")]
    for sd in subs:
        for p in sorted((src / sd).iterdir()):
            if p.name.startswith(".") or not p.is_file():
                raise SystemExit(f"unexpected {p}")
            yield f"{sd}/{p.name}", p.read_bytes()


def corpora():
    n_main = len(list((SRC / "Footprint_6_u_nov10_s2A/xml").glob("*.xml")))
    tarball("Footprint_6_u_main_A", "Footprint_6_u_main_A", corpus_members(SRC / "Footprint_6_u_nov10_s2A", True,
            f"READY Footprint_6_u_main_A: {n_main} programs, {2 * n_main} tests (both modes)\n"))
    n_ex = len(list((SRC / "Footprint_6_u_core_lpP_s2A/xml").glob("*.xml")))
    tarball("Footprint_6_u_extra_A", "Footprint_6_u_extra_A", corpus_members(SRC / "Footprint_6_u_core_lpP_s2A", True,
            f"READY Footprint_6_u_extra_A: {n_ex} programs, {2 * n_ex} tests (both modes)\n"))
    for r in (1, 2, 3):
        nm = f"Footprint_6_u_main_A_c{r}"
        tarball(nm, nm, corpus_members(SRC / f"Footprint_6_u_nov10_c{r}_s2A", False,
                f"READY {nm}: {n_main} programs re-concretized from Footprint_6_u_main_A/xml (stem inst-NNNNNN_c{r} = inst-NNNNNN), {2 * n_main} tests\n"))
    n_stt = len(list((SRC / "STT_6_u_core_lpP_s2A/xml").glob("*.xml")))
    tarball("STT_6_u_A", "STT_6_u_A", corpus_members(SRC / "STT_6_u_core_lpP_s2A", True,
            f"READY STT_6_u_A: {n_stt} programs, {2 * n_stt} tests (both modes)\n"))
    lines = [l for l in rd(R / "rounds_stem_mapping.tsv.gz").splitlines() if l and not l.startswith("#")]
    wbytes("corpus/rounds_stem_mapping.tsv.gz", ("\n".join(lines) + "\n").encode())


def run_records(dst, d, rmw):
    d = Path(d)
    wjsonl(f"{dst}/results.jsonl.gz", d / "results.jsonl")
    wjsonl(f"{dst}/classes.jsonl.gz", d / "classes.jsonl")
    if rmw:
        wjsonl(f"{dst}/classes_rmw.jsonl.gz", d / "classes_rmw.jsonl")
        wjson(f"{dst}/first_detection_rmw.json", json.loads(rd(d / "first_detection_rmw.json")))
    wjson(f"{dst}/first_detection.json", json.loads(rd(d / "first_detection.json")))
    for f in ("order_seed.tsv", "order_stream.tsv"):
        if (d / f).exists() or (d / (f + ".gz")).exists():
            wtext(f"{dst}/{f}.gz", d / f, cols=3)


def records():
    run_records("records/main/invisispec", FD3 / "T1g_Footprint_6_u_nov10_s2A", False)
    run_records("records/main/speclfb", FD3 / "T3g_Footprint_6_u_nov10_s2A", False)
    run_records("records/main/cleanupspec", FD3 / "T2g_Footprint_6_u_nov10_s2A_merged", True)
    run_records("records/extra_new/cleanupspec", FD3 / "T2g_Footprint_6_u_core_lpP_s2A_new", True)
    run_records("records/round1/cleanupspec", FD1 / "T2g_Footprint_6_u_nov10_c1_s2A", True)
    run_records("records/round2/cleanupspec", FD2 / "T2g_Footprint_6_u_nov10_c2_s2A", True)
    run_records("records/round3/cleanupspec", FD3 / "T2g_Footprint_6_u_nov10_c3_s2A", True)
    wtext("records/main/prefix_pairs.tsv", R / "bigcorpus/cafe3/ws_nov10/prefix_pairs.tsv")
    dd = FD3 / "report/extra_dedup"
    wtext("records/extra_new/dup_stems.txt", dd / "dup_stems.txt")
    wjson("records/extra_new/dedup_summary.json", json.loads(rd(dd / "dedup_summary.json")))
    E = R / "bigcorpus/cafe3/e2w"
    bk = json.loads(rd(E / "buckets.json"))
    sys.path.insert(0, str(Path(__file__).resolve().parent / "prune"))
    from labels import relabel as lab, FIELD_RENAMES
    e2w = {"row": "E2w_STT_6_u_A",
           "buckets": {k: {"tests": v["tests"], "raw": v["raw"], "gated": v["gated"],
                           "buckets": {lab(b): n for b, n in v["buckets"].items()}} for k, v in bk["buckets"].items()}}
    wjson("records/e2w/recon_stt/buckets.json", e2w)
    tr = json.loads(rd(E / "rsa8_trace.json"))
    fr = dict(FIELD_RENAMES)
    wjson("records/e2w/recon_stt/oldest_taint_rerun.json", {k: {fr.get(kk, kk): vv for kk, vv in v.items() if kk != "trace"} for k, v in tr.items()})
    kn = json.loads(rd(TM / "scripts/kn_final.json"))
    wjson("kn.json", {"pooled": next(iter(kn.values()))})


def timing():
    for row, dfn in (("T1g", "invisispec"), ("T2g", "cleanupspec"), ("T3g", "speclfb")):
        d = TM / "simspect" / f"{row}_p16_fast"
        wjsonl(f"timing/simspect/{dfn}/results.jsonl.gz", d / "results.jsonl")
        wjsonl(f"timing/simspect/{dfn}/fastpath_workers.jsonl", d / "fastpath_workers.jsonl")
        wtext(f"timing/simspect/{dfn}/order_stream.tsv", d / "order_stream.tsv", cols=3)
    wtext("timing/sample/sample.tsv", TM / "sample/sample.tsv")
    m = json.loads(rd(TM / "sample/sample_meta.json"))
    m["testset"] = "Footprint_6_u_extra_A"
    wjson("timing/sample/sample_meta.json", m)
    prov = json.loads(rd(SRC / "Footprint_6_u_core_lpP_s2A/PROVENANCE.json"))
    wjson("timing/generation.json", {
        "corpus": "Footprint_6_u_extra_A",
        "programs": prov["programs_merged"],
        "tests": prov["stem_mode_pairs"],
        "stage15_alloy_job_wall_s_sum_loaded": prov["cpu_s"]["stage15_alloy_job_wall_s_sum"],
        "stage2_cpu_s": prov["cpu_s"]["stage2_parsexml_llc"],
        "retime": {"jobs": 16, "seed": 20261115, "solver_wall_s_idle": 1568, "solver_wall_s_loaded": 4800,
                   "instances_per_job": 100}})
    for run in sorted((TM / "amulet/runs").iterdir()):
        D = run.name.split("_")[0]
        s = json.loads(rd(run / "t5_summary.json"))
        s["run"] = run.name
        wjson(f"amulet/timing/{D}/t5_summary.json", s)
        wjson(f"amulet/timing/{D}/t5_instances.json", json.loads(rd(run / f"benchmark-out-{D}/t5_instances.json")))
    pb = json.loads(rd(OLD / "perbug/out/perbug_summary.json"))
    for D, v in pb.items():
        v["run"] = os.path.basename(v["run"])
    wjson("amulet/hits/perbug_summary.json", pb)
    for run in sorted((OLD / "runs").iterdir()):
        D = run.name.split("_")[0]
        if (run / "t5_summary.json").exists() and D in pb:
            s = json.loads(rd(run / "t5_summary.json"))
            s["run"] = run.name
            wjson(f"amulet/hits/{D}/t5_summary.json", s)


if __name__ == "__main__":
    what = sys.argv[3:] or ["records", "timing", "corpora"]
    for w in what:
        globals()[w]()

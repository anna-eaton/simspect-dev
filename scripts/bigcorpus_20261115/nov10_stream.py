#!/usr/bin/env python3
"""nov10_stream.py -- re-concretize the 2026-11-10 Footprint corpus programs with the unified recipe A, streamed in seed order
(agent bigcorpus, 2026-11-15; Anna: "start running conc and gem5 as soon as you get the tests in so that we pipeline", option 3 (a):
the MAIN AMuLeT-comparison number = the Nov 10 programs re-concretized with recipe A).

Input (read-only, never modified): the Nov 10 Stage-1b XMLs <src>/inst-NNNNNN.{xml,txt} (cafe3
/tests/simspect_alloy_20261108/testsets_twostage/Footprint_6_u_core_lpP_fv3/xml; same stems, same lpP model body as Nov 10).
Order: the seed-20261109 order of the (mode, stem) pairs exactly as timing_driver.build_order computes it (sorted pairs over both modes,
random.Random(20261109).shuffle), so as long as every stem compiles in both modes the InvisiSpec/SpecLFB --seed-prefix 4000 is the same
4,000 pairs as Nov 10 (paired comparison). Stems are processed in order of their first pair; chunk 1 = the stems of the first 4,000 pairs.
Per chunk: copy the XMLs into <ts>/<base>/xml, stage2_sharded.py (only new stems; small shards so the chunk spreads over --jobs), then
publish atomically into <ts>/<final>: .s then .ann.json per mode, xml/txt, rmw_stems.tsv / jmp_stems.tsv rows from each ann's vocab_rj
(stream_fp.vocab_rows, unchanged), and only then MANIFEST.tsv rows (stem, chunk, modes, published_at). A stem missing a mode is retried in
the next chunk's Stage-2 pass, and published with the modes it has after 2 failed passes. READY at the end (counts, seed-prefix check).
Logs: <ws>/nov10_stream.log (every step, rc, counts, stderr of failures); state <ws>/state.json (resumable: published stems are skipped).
Usage (cafe3 gem5_dev, from the code root):
  python3 scripts/bigcorpus_20261115/nov10_stream.py --src <nov10 xml dir> --cfg runconfigs/bigcorpus_20261115/stage2_final_A.jsonc \
      --ts /tests/bigcorpus_20261115/testsets --final Footprint_6_u_nov10_s2A --ws /tests/bigcorpus_20261115/ws_nov10 --jobs 24
"""
import argparse, datetime as dt, json, os, random, re, shutil, subprocess, sys, time, traceback
from pathlib import Path

MODES = ["mispredict_not_taken", "mispredict_taken"]
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "STAGE1_alloy/models/proposed/ultimate/loosepin"))
import stream_fp  # noqa: E402  (vocab_rows only, unchanged)


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def acopy(src, dst):
    tmp = dst.parent / f".{dst.name}.tmp"; shutil.copy2(src, tmp); os.replace(tmp, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--cfg", required=True); ap.add_argument("--ts", required=True)
    ap.add_argument("--final", required=True); ap.add_argument("--ws", required=True); ap.add_argument("--jobs", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20261109); ap.add_argument("--prefix", type=int, default=4000)
    ap.add_argument("--chunk", type=int, default=1500); ap.add_argument("--shard-size", type=int, default=20)
    a = ap.parse_args()
    src, ts, ws = Path(a.src), Path(a.ts), Path(a.ws); ws.mkdir(parents=True, exist_ok=True)
    base_name = a.final + "_base"; base = ts / base_name; final = ts / a.final
    (base / "xml").mkdir(parents=True, exist_ok=True)
    for m in MODES:
        for d in ("asm", "ann"):
            (final / m / d).mkdir(parents=True, exist_ok=True)
    (final / "xml").mkdir(parents=True, exist_ok=True)
    logf = open(ws / "nov10_stream.log", "a", buffering=1)
    def log(msg):
        logf.write(f"{now()} {msg}\n"); print(msg, flush=True)
    stf = ws / "state.json"
    st = json.loads(stf.read_text()) if stf.exists() else {"published": [], "tries": {}, "chunk": 0}
    def save():
        tmp = ws / ".state.json.tmp"; tmp.write_text(json.dumps(st)); os.replace(tmp, stf)
    # stream config: recipe A with only paths.testset_dir (absolute) and gem5.jobs (asm threads) changed
    txt = Path(a.cfg).read_text()
    txt = re.sub(r'"testset_dir"\s*:\s*"[^"]*"', f'"testset_dir": "{ts}"', txt, count=1)
    txt = re.sub(r'"jobs"\s*:\s*\d+', f'"jobs": {a.jobs}', txt, count=1)
    scfg = ws / "stage2_final_A_nov10_stream.jsonc"
    scfg.write_text(f"// nov10_stream.py {now()}: copy of {a.cfg} with only paths.testset_dir and gem5.jobs changed\n" + txt)
    stems = sorted(p.stem for p in src.glob("inst-*.xml"))
    pairs = sorted((m, s) for m in MODES for s in stems)
    random.Random(a.seed).shuffle(pairs)
    order, seen = [], set()
    for m, s in pairs:
        if s not in seen:
            seen.add(s); order.append(s)
    pre = {s for _, s in pairs[:a.prefix]}
    first = [s for s in order if s in pre]
    (ws / "prefix_pairs.tsv").write_text("".join(f"{m}\t{s}\n" for m, s in pairs[:a.prefix]))   # firstdet_stream --only-file for T1g/T3g
    (ws / "order_seed_pairs.tsv").write_text("".join(f"{i}\t{m}\t{s}\n" for i, (m, s) in enumerate(pairs)))
    log(f"START src={src} stems={len(stems)} pairs={len(pairs)} seed={a.seed} prefix {a.prefix} pairs = {len(pre)} stems; cfg={scfg} "
        f"final={final} published so far {len(st['published'])}")
    man = final / "MANIFEST.tsv"
    if not man.exists():
        man.write_text("stem\tchunk\tmodes\tpublished_at\n")
    pub = set(st["published"])
    rest = [s for s in order if s not in pre]
    chunks = [first] + [rest[i:i + a.chunk] for i in range(0, len(rest), a.chunk)]
    pending = []          # stems copied into base but not yet published (failed a mode)
    for ci, ch in enumerate(chunks):
        todo = [s for s in ch if s not in pub]
        if not todo and not pending:
            continue
        t0 = time.time()
        for s in todo:
            for ext in (".xml", ".txt"):
                p = src / f"{s}{ext}"
                if p.exists() and not (base / "xml" / p.name).exists():
                    shutil.copy2(p, base / "xml" / p.name)
        r = subprocess.run([sys.executable, "STAGE1_alloy/models/proposed_twophase/stage2_sharded.py", "--config", str(scfg), "--model", base_name,
                            "--jobs", str(a.jobs), "--shard-size", str(a.shard_size), "--first-fraction", "0"], capture_output=True, text=True)
        log(f"chunk {ci}: stage2 rc={r.returncode} stems {len(todo)} (+{len(pending)} retried) secs={round(time.time() - t0)}"
            + (f"\nSTDERR {r.stderr[-3000:]}" if r.returncode else ""))
        cand = pending + todo; pending = []; ready, partial = [], {}
        for s in cand:
            have = [m for m in MODES if (base / m / "asm" / f"{s}.s").exists() and (base / m / "ann" / f"{s}.ann.json").exists()]
            if len(have) == len(MODES):
                ready.append(s)
            else:
                st["tries"][s] = st["tries"].get(s, 0) + 1
                if st["tries"][s] >= 2 or ci == len(chunks) - 1:
                    ready.append(s); partial[s] = have
                    log(f"chunk {ci}: {s} published with modes {have} after {st['tries'][s]} Stage-2 passes")
                else:
                    pending.append(s)
        try:
            bd = ws / "batches" / f"c{ci:03d}"; shutil.rmtree(bd, ignore_errors=True); bd.mkdir(parents=True)
            stream_fp.vocab_rows(base, bd, ready)
            for m in MODES:
                for s in ready:
                    if s in partial and m not in partial[s]:
                        continue
                    acopy(base / m / "asm" / f"{s}.s", final / m / "asm" / f"{s}.s")
                for s in ready:
                    if s in partial and m not in partial[s]:
                        continue
                    acopy(base / m / "ann" / f"{s}.ann.json", final / m / "ann" / f"{s}.ann.json")
            for s in ready:
                for ext in (".xml", ".txt"):
                    p = base / "xml" / f"{s}{ext}"
                    if p.exists():
                        acopy(p, final / "xml" / p.name)
            keep = set(ready)
            for t, dst in (("rmw/rmw_stems.tsv", "rmw_stems.tsv"), ("jmp_rows/jmp_stems.tsv", "jmp_stems.tsv")):
                lines = (bd / t).read_text().splitlines(); agg = final / dst
                old = agg.read_text() if agg.exists() else (lines[0] + "\n")
                body = [l for l in lines[1:] if l.split("\t")[1] in keep]
                tmp = agg.parent / f".{agg.name}.tmp"; tmp.write_text(old + "".join(l + "\n" for l in body)); os.replace(tmp, agg)
            tp = now()
            rows = "".join(f"{s}\tc{ci:03d}\t{','.join(partial.get(s, MODES))}\t{tp}\n" for s in ready)
            tmp = man.parent / ".MANIFEST.tsv.tmp"; tmp.write_text(man.read_text() + rows); os.replace(tmp, man)
            st["published"] += ready; pub |= keep; st["chunk"] = ci; save()
            log(f"chunk {ci}: published {len(ready)} stems ({len(partial)} partial), total {len(pub)}/{len(stems)}")
        except Exception:
            log(f"chunk {ci}: PUBLISH ERROR\n{traceback.format_exc()}"); raise
    n = {m: len(list((final / m / "asm").glob("*.s"))) for m in MODES}
    full = all(n[m] == len(stems) for m in MODES)
    (final / "READY").write_text(f"READY {now()} nov10_stream: {a.final} = the 2026-11-10 Footprint_6_u_core_lpP_fv3 programs ({len(stems)} stems from {src}) "
                                 f"re-concretized with {a.cfg} (recipe A, vocab_rj, no post-passes). tests {n}. seed-{a.seed} prefix {a.prefix} identical to "
                                 f"Nov 10's pair set: {full} (every stem compiled in both modes).\n")
    log(f"READY: tests {n}; full pair set {full}")


if __name__ == "__main__":
    main()

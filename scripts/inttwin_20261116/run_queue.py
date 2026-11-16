#!/usr/bin/env python3
"""run_queue.py (agent inttwin 2026-11-16) -- unattended runner for this node's inttwin shard queue (prep_queue.py). Keeps up to N testrun
processes busy (N re-read every loop from /tests/inttwin_20261116/slots_<node>, default --slots), each
`nice -n 5 python3 -u testrun.py --config <shard cfg> --model <shard testset> --once --resume --max-new 100000` with TMPDIR=/tmp,
SIMSPECT_GEM5_TIMEOUT_S=900, SIMSPECT_GEM5_MAX_TICK=2e9 (runaway net; the longest legit test ends near 2.4e7 ticks, sptrace PROVENANCE)
and, for race rows, SIMSPECT_COMMIT_IEW_DELAY=<race_knobs.commitToIEWDelay> (read by the build's se_exp.py, as gem5_row.sh did).
The queue file is re-read every loop, so items prep_queue.py appends later are picked up. Item done = logs/q/<name>.DONE (rc, start,
end, seconds); rc != 0 is logged and retried once. Keeps polling for new items until every item is DONE and logs/q/FINISH_<node> exists.
Pause launching: touch logs/PAUSE_QUEUE (running items continue). Log: /tests/inttwin_20261116/logs/queue_<node>.log; per item logs/q/<name>.log.
Run from the code root inside gem5_dev (tmux inttwin window queue): python3 scripts/inttwin_20261116/run_queue.py --node cafe3 --slots 8
"""
import argparse, json, os, subprocess, time
from pathlib import Path

O = Path("/tests/inttwin_20261116"); QD = O / "logs" / "q"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--slots", type=int, default=8); a = ap.parse_args()
    QD.mkdir(parents=True, exist_ok=True); L = open(O / "logs" / f"queue_{a.node}.log", "a", buffering=1)
    log = lambda s: L.write(f"[{time.strftime('%F %T', time.gmtime())}] {s}\n")
    run, tries = {}, {}
    log(f"START run_queue pid {os.getpid()} slots {a.slots}")
    while True:
        sf = O / f"slots_{a.node}"
        try:
            slots = int(sf.read_text().strip()) if sf.exists() else a.slots
        except Exception:
            slots = a.slots
        q = json.load(open(O / f"queue_{a.node}.json")) if (O / f"queue_{a.node}.json").exists() else []
        for n, (p, t0, it) in list(run.items()):
            rc = p.poll()
            if rc is None:
                continue
            del run[n]; dt = int(time.time() - t0)
            if rc == 0 or tries.get(n, 0) >= 2:
                (QD / f"{n}.DONE").write_text(json.dumps(dict(rc=rc, start=t0, end=time.time(), seconds=dt, tests=it["tests"])) + "\n")
            log(f"END {n} rc={rc} {dt}s tests={it['tests']}" + ("" if rc == 0 else f" (try {tries.get(n)})"))
        pend = [i for i in q if i["name"] not in run and not (QD / f"{i['name']}.DONE").exists()]
        if (O / "logs" / "PAUSE_QUEUE").exists() or (O / "logs" / "GUARD_STOPPED").exists():
            pend = []
        while pend and len(run) < slots:
            it = pend.pop(0); n = it["name"]; tries[n] = tries.get(n, 0) + 1
            env = dict(os.environ, TMPDIR="/tmp", SIMSPECT_GEM5_TIMEOUT_S="900", SIMSPECT_GEM5_MAX_TICK="2000000000")
            env.pop("SIMSPECT_COMMIT_IEW_DELAY", None)
            if it.get("delay") is not None:
                env["SIMSPECT_COMMIT_IEW_DELAY"] = str(it["delay"])
            f = open(QD / f"{n}.log", "a")
            f.write(f"=== START {time.strftime('%F %T', time.gmtime())} try {tries[n]} delay={it.get('delay')} cfg={it['cfg']} model={it['model']}\n"); f.flush()
            p = subprocess.Popen(["nice", "-n", "5", "python3", "-u", "testrun.py", "--config", it["cfg"], "--model", it["model"], "--once", "--resume",
                                  "--max-new", "100000"], stdout=f, stderr=subprocess.STDOUT, env=env)
            run[n] = (p, time.time(), it); log(f"LAUNCH {n} pid {p.pid} tests={it['tests']} delay={it.get('delay')} (running {len(run)}/{slots})")
        done = sum((QD / f"{i['name']}.DONE").exists() for i in q)
        (O / "logs" / f"queue_{a.node}.last").write_text(f"{time.strftime('%F %T', time.gmtime())} items {len(q)} done {done} running {len(run)} slots {slots}\n")
        if not run and done == len(q) and (QD / f"FINISH_{a.node}").exists():
            log("FINISH: all items done"); break
        time.sleep(20)


if __name__ == "__main__":
    main()

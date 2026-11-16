#!/usr/bin/env python3
"""fastpath_worker.py (agent fastpath, 2026-11-16): option 3 of the OPT-IN fast path (TC-1): a persistent
Python worker for the per-test drivers (timing_driver.run_one, used by firstdet_stream.py and TIME-1).

Production runs each test as `python3 pipeline.py gem5 ...` (one interpreter), which runs
`python3 check_<x>.py <tmp> ...` (a second interpreter). With run_config `gem5.fast_path: true`,
timing_driver.run_one hands the SAME pipeline command line, environment, cwd and log file to a long-lived
worker process instead, which runs pipeline.main() in-process and, inside it, runs the checker script
in-process too (runpy, as `__main__`, same argv), with fd 1/2 redirected exactly where the subprocesses'
output went. Nothing else changes: same staging, pass config, grid/stall draws, gem5 command lines,
cache setup, branch forces, checker code, output files. gem5 is still one process per test (TC-2: no
batching). Options 1 + 2 (STAGE3_gem5/gem5_fastpath.py) are active inside the worker because the checker
environment carries SIMSPECT_FAST_PATH=1 from the config.

Why a persistent process gives the same records as fresh ones (checked by fastpath_worker's guards and by
timing/fastpath_equiv.py on real tests):
  - gem5_common reads its SIMSPECT_* settings at import. A worker serves ONE checker script (the driver keeps
    one pool per checker), and the first checker run imports gem5_common under that run's checker env
    (+ the checker's own setdefault, e.g. check_footprint's debug flag), exactly as a fresh checker process.
    Every later batch must carry the same SIMSPECT_* env and the same checker path; otherwise that batch
    runs as a real subprocess (logged as path fast_partial). If gem5_common was imported before the first
    checker run, the worker never runs a checker in-process.
  - os.environ, sys.argv, sys.path and cwd are restored after every test and every checker run, so a
    checker's setdefault/sys.path.insert cannot leak into the next test.
  - Every random draw in the per-test path is seeded per call from (seed, stem) (pipeline sweep helpers,
    cache_setup.choose/choose_all); process_one makes a fresh temp dir per test; the only cross-test state is
    the resolve-hook cache, keyed on the binary's identity.
  - gem5's environment is the same as production's (the driver's env + PYTHONPATH + TIMING_GEM5_LOG, plus
    the fast-path variables, which no gem5 config reads).

CPU accounting: per test, RUSAGE_SELF + RUSAGE_CHILDREN deltas of the worker (single-threaded per test, jobs=1)
= the same quantity as production's os.wait4 on the pipeline subtree, minus the two interpreter starts.
gem5 CPU goes to the per-test TIMING_GEM5_LOG file in the sitecustomize format (same hook, re-pointed per test).
Each worker's one-time startup CPU is reported in <out>/fastpath_workers.jsonl and driver.log.

Logs (campaign dir = the driver's --out): driver.log (pool events, fallbacks with traceback),
fastpath_logs/worker_<n>.log (per worker: start, bind, every test with rc/cpu/path, every error with full
traceback, end; the gem5_fastpath per-test lines too), fastpath_workers.jsonl (spawn/exit records).

Failure handling: if a worker cannot start, dies, or answers garbage, the driver kills it and runs that test
through the production subprocess path (row exec_path=production, fastpath_fallback=<why>). After 3
consecutive spawn failures the pool disables itself for the rest of the run (logged).

    # worker side (spawned by FastPool, never by hand):
    python3 fastpath_worker.py serve --code-root <code> --log <file> --key <checker>
"""
from __future__ import annotations

import argparse
import atexit
import contextlib
import json
import os
import re
import resource
import select
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKER_PY = Path(__file__).resolve()
READY_TIMEOUT_S = 300


def _ru():
    s = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime, c.ru_utime + c.ru_stime


# ═════════════════════════════ worker side ═══════════════════════════════════

_WLOG = [None]          # worker log path
_GEM5_LOG = [None]      # per-test TIMING_GEM5_LOG target (sitecustomize format)
_EVENTS = []            # per-test notes (checker batches that ran as subprocesses, ...)
_BOUND = {}             # checker path + SIMSPECT_* env snapshot this worker serves
_STAGE3 = [None]


def wlog(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] worker pid={os.getpid()} {msg}\n"
    try:
        with open(_WLOG[0], "a") as f:
            f.write(line)
    except Exception:
        pass


def _install_gem5_rusage_hook():
    """Same record as STAGE3_gem5/timing/sitecustom/sitecustomize.py, written to the per-test log."""
    _orig_init = subprocess.Popen.__init__

    def _init(self, *a, **kw):
        self._timing_t0 = time.monotonic()
        _orig_init(self, *a, **kw)

    def _try_wait(self, wait_flags):
        try:
            pid, sts, ru = os.wait4(self.pid, wait_flags)
        except ChildProcessError:
            return (self.pid, 0)
        if pid == self.pid and _GEM5_LOG[0]:
            try:
                args = self.args if isinstance(self.args, (list, tuple)) else [str(self.args)]
                a0 = str(args[0]) if args else ""
                if a0.endswith(("gem5.opt", "gem5.fast", "gem5.debug")):
                    rec = dict(t_end=time.time(),
                               wall_s=round(time.monotonic() - getattr(self, "_timing_t0", time.monotonic()), 4),
                               utime_s=ru.ru_utime, stime_s=ru.ru_stime, maxrss_kb=ru.ru_maxrss,
                               rc=(os.WEXITSTATUS(sts) if os.WIFEXITED(sts) else -os.WTERMSIG(sts)
                                   if os.WIFSIGNALED(sts) else None),
                               argv0=a0, cmd=[str(x) for x in args if str(x).startswith("--cmd=")])
                    with open(_GEM5_LOG[0], "a") as f:
                        f.write(json.dumps(rec) + "\n")
            except Exception as e:
                try:
                    with open(_GEM5_LOG[0] + ".err", "a") as f:
                        f.write(f"{time.time()} fastpath_worker gem5 rusage log error: {e!r}\n")
                except Exception:
                    pass
        return (pid, sts)

    subprocess.Popen.__init__ = _init
    subprocess.Popen._try_wait = _try_wait


@contextlib.contextmanager
def _fds(out_fd: int, err_fd: int):
    """Point fd 1 / fd 2 at the given fds (what a subprocess's stdout/stderr would have been)."""
    sys.stdout.flush(); sys.stderr.flush()
    s1, s2 = os.dup(1), os.dup(2)
    os.dup2(out_fd, 1); os.dup2(err_fd, 2)
    try:
        yield
    finally:
        try:
            sys.stdout.flush(); sys.stderr.flush()
        finally:
            os.dup2(s1, 1); os.dup2(s2, 2); os.close(s1); os.close(s2)


def _run_as_main(fn) -> int:
    """Exit status a `python3 script.py` process would have had."""
    try:
        fn()
        return 0
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code & 0xFF
        print(code, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        raise
    except BaseException:
        traceback.print_exc()
        return 1


@contextlib.contextmanager
def _process_state():
    env, argv, path, cwd = dict(os.environ), list(sys.argv), list(sys.path), os.getcwd()
    try:
        yield
    finally:
        os.environ.clear(); os.environ.update(env)
        sys.argv[:] = argv; sys.path[:] = path
        os.chdir(cwd)


def _snapshot(env: dict) -> dict:
    return {k: v for k, v in env.items() if k.startswith("SIMSPECT_") and k != "SIMSPECT_FAST_PATH_LOG"}


def _checker_call(cmd, a, kw):
    """pipeline._run_checker_batch's subprocess.run -> run in-process, or None = real subprocess."""
    import runpy
    if a or not isinstance(cmd, list) or len(cmd) < 3 or cmd[0] != sys.executable:
        return None
    script = Path(cmd[1])
    if not (script.suffix == ".py" and script.name.startswith("check")):
        return None
    if script.resolve().parent != _STAGE3[0]:
        _EVENTS.append(f"checker_subprocess: {script} is outside {_STAGE3[0]}")
        wlog(f"FALLBACK checker batch as a real subprocess: {script} is outside {_STAGE3[0]}")
        return None
    if not (kw.get("capture_output") and kw.get("text") and kw.get("check") is False):
        _EVENTS.append(f"checker_subprocess: unexpected subprocess.run arguments {sorted(kw)}")
        wlog(f"FALLBACK checker batch as a real subprocess: unexpected arguments {sorted(kw)}")
        return None
    env = kw.get("env")
    if env is None:
        env = dict(os.environ)
    snap = _snapshot(env)
    why = None
    if not _BOUND:
        if "gem5_common" in sys.modules:
            why = "gem5_common already imported before the first checker run (env could differ)"
            _BOUND.update(unbindable=why)
        else:
            _BOUND.update(checker=str(script.resolve()), env=snap)
            wlog(f"BIND checker={script.name} SIMSPECT_env={json.dumps(snap, sort_keys=True)}")
    elif _BOUND.get("unbindable"):
        why = _BOUND["unbindable"]
    elif _BOUND["checker"] != str(script.resolve()):
        why = f"checker {script.name} != bound {Path(_BOUND['checker']).name}"
    elif _BOUND["env"] != snap:
        diff = sorted(k for k in set(snap) | set(_BOUND["env"]) if snap.get(k) != _BOUND["env"].get(k))
        why = f"SIMSPECT_* env differs from the bound one in {diff}"
    if why:
        _EVENTS.append(f"checker_subprocess: {why}")
        wlog(f"FALLBACK checker batch as a real subprocess: {why}")
        return None
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        with _process_state():
            os.environ.clear(); os.environ.update(env)
            sys.argv[:] = [str(script)] + [str(x) for x in cmd[2:]]
            sys.path.insert(0, str(script.resolve().parent))
            with _fds(fo.fileno(), fe.fileno()):
                rc = _run_as_main(lambda: runpy.run_path(str(script), run_name="__main__"))
        fo.seek(0); fe.seek(0)
        out = fo.read().decode(errors="replace").replace("\r\n", "\n")
        err = fe.read().decode(errors="replace").replace("\r\n", "\n")
    return subprocess.CompletedProcess(cmd, rc, out, err)


class _SubprocessProxy:
    """Stands in for the `subprocess` module inside pipeline.py only: checker launches run in-process,
    everything else goes to the real module."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def run(self, cmd, *a, **kw):
        r = _checker_call(cmd, a, kw)
        return r if r is not None else self._real.run(cmd, *a, **kw)


def serve(code_root: str, log: str, key: str) -> None:
    _WLOG[0] = log
    t_start = time.time()
    proto = os.fdopen(os.dup(1), "w", buffering=1)
    lf = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    os.dup2(lf, 1)                     # stray prints go to the log, never into the protocol
    os.close(lf)
    stdin = sys.stdin
    try:
        code = Path(code_root).resolve()
        _STAGE3[0] = (code / "STAGE3_gem5").resolve()
        here = str(HERE)
        sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]
        sys.path.insert(0, str(code))
        sys.path.insert(0, str(_STAGE3[0]))     # a checker process has its script dir first
        os.chdir(code)
        import pipeline
        pipeline.subprocess = _SubprocessProxy(subprocess)
        _install_gem5_rusage_hook()
        base_env = dict(os.environ)
        startup = sum(_ru())
        wlog(f"START key={key} code_root={code} python={sys.version.split()[0]} pipeline={pipeline.__file__} "
             f"startup_cpu_s={startup:.3f} nice={os.nice(0)}")
        proto.write(json.dumps(dict(op="ready", pid=os.getpid(), startup_cpu_s=round(startup, 4),
                                    python=sys.version.split()[0])) + "\n")
    except BaseException:
        wlog(f"ERROR at startup:\n{traceback.format_exc()}")
        try:
            proto.write(json.dumps(dict(op="error", error=traceback.format_exc()[-2000:])) + "\n")
        except Exception:
            pass
        return
    n = 0
    tot = 0.0
    while True:
        line = stdin.readline()
        if not line:
            wlog(f"END stdin closed: tests={n} test_cpu_s={tot:.2f} lifetime_s={time.time() - t_start:.0f}")
            return
        try:
            req = json.loads(line)
        except Exception:
            wlog(f"ERROR bad request {line[:200]!r}")
            proto.write(json.dumps(dict(op="error", error="bad request")) + "\n")
            continue
        if req.get("op") == "exit":
            wlog(f"END exit requested: tests={n} test_cpu_s={tot:.2f} lifetime_s={time.time() - t_start:.0f}")
            proto.write(json.dumps(dict(op="bye")) + "\n")
            return
        if req.get("op") != "run":
            proto.write(json.dumps(dict(op="error", error=f"unknown op {req.get('op')!r}")) + "\n")
            continue
        _EVENTS.clear()
        try:
            env = dict(req["env"])
            env.setdefault("SIMSPECT_FAST_PATH_LOG", log)
            s0 = _ru()
            t0 = time.monotonic()
            with _process_state():
                os.environ.clear(); os.environ.update(env)
                os.chdir(req["cwd"])
                sys.argv[:] = list(req["argv"])
                _GEM5_LOG[0] = env.get("TIMING_GEM5_LOG")
                with open(req["log"], "w") as plog:
                    with _fds(plog.fileno(), plog.fileno()):
                        rc = _run_as_main(pipeline.main)
            _GEM5_LOG[0] = None
            s1 = _ru()
            cpu_self, cpu_ch = s1[0] - s0[0], s1[1] - s0[1]
            n += 1
            tot += cpu_self + cpu_ch
            path = "fast_partial" if _EVENTS else "fast"
            wlog(f"TEST {req.get('tag')} rc={rc} path={path} cpu_self={cpu_self:.3f} cpu_children={cpu_ch:.3f} "
                 f"wall={time.monotonic() - t0:.2f}" + (f" events={_EVENTS}" if _EVENTS else ""))
            proto.write(json.dumps(dict(op="done", rc=rc, cpu_self=cpu_self, cpu_children=cpu_ch,
                                        wall=time.monotonic() - t0, path=path, events=list(_EVENTS),
                                        n=n)) + "\n")
        except KeyboardInterrupt:
            raise
        except BaseException:
            _GEM5_LOG[0] = None
            wlog(f"ERROR test {req.get('tag')}:\n{traceback.format_exc()}")
            proto.write(json.dumps(dict(op="error", error=traceback.format_exc()[-2000:])) + "\n")
        finally:
            os.environ.clear(); os.environ.update(base_env)


# ═════════════════════════════ driver side ═══════════════════════════════════

class FastPathError(RuntimeError):
    pass


class _Worker:
    def __init__(self, pool, key: str, n: int):
        self.key, self.n, self.tests = key, n, 0
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", key)
        self.log = pool.log_dir / f"worker_{n:03d}_{safe}.log"
        env = dict(os.environ)
        env.pop("TIMING_GEM5_LOG", None)
        errf = open(self.log, "ab")
        try:
            self.p = subprocess.Popen([sys.executable, "-u", str(WORKER_PY), "serve", "--code-root",
                                       str(pool.code_root), "--log", str(self.log), "--key", key],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errf,
                                      cwd=str(pool.code_root), env=env)
        finally:
            errf.close()
        try:
            msg = self._read(READY_TIMEOUT_S)
        except BaseException:
            self.kill()
            raise
        if msg.get("op") != "ready":
            self.kill()
            raise FastPathError(f"worker {n} failed to start: {str(msg)[:1500]}")
        self.pid, self.startup_cpu_s = msg["pid"], msg["startup_cpu_s"]

    def _read(self, timeout=None) -> dict:
        if timeout is not None:
            r, _, _ = select.select([self.p.stdout], [], [], timeout)
            if not r:
                raise FastPathError(f"worker {self.n} gave no answer in {timeout}s")
        line = self.p.stdout.readline()
        if not line:
            rc = self.p.poll()
            raise FastPathError(f"worker {self.n} exited (rc={rc}); see {self.log}")
        try:
            return json.loads(line)
        except Exception:
            raise FastPathError(f"worker {self.n} sent garbage: {line[:300]!r}")

    def request(self, req: dict) -> dict:
        self.p.stdin.write((json.dumps(req) + "\n").encode())
        self.p.stdin.flush()
        msg = self._read()
        if msg.get("op") != "done":
            raise FastPathError(f"worker {self.n} error: {str(msg.get('error', msg))[-1500:]}")
        self.tests += 1
        return msg

    def close(self, timeout=30):
        try:
            if self.p.poll() is None:
                self.p.stdin.write((json.dumps(dict(op="exit")) + "\n").encode())
                self.p.stdin.flush()
                self.p.stdin.close()
                self.p.wait(timeout=timeout)
        except Exception:
            self.kill()

    def kill(self):
        try:
            self.p.kill()
            self.p.wait(timeout=10)
        except Exception:
            pass


class FastPool:
    """Persistent workers, one pool per checker script; at most one test per worker at a time."""

    def __init__(self, code_root, out: Path, log_fn):
        self.code_root = Path(code_root).resolve()
        self.out = Path(out)
        self.log_dir = self.out / "fastpath_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log = log_fn
        self._lock = threading.Lock()
        self._idle = {}
        self._all = []
        self._n = 0
        self._spawn_fail = 0
        self.disabled = None
        self._closed = False
        atexit.register(self.close)
        self.log(f"fastpath: pool ready (code_root={self.code_root}, worker logs {self.log_dir})")

    def _record(self, rec: dict):
        try:
            with self._lock, open(self.out / "fastpath_workers.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass

    def _get(self, key: str) -> _Worker:
        with self._lock:
            if self.disabled:
                raise FastPathError(f"fast path disabled for this run: {self.disabled}")
            idle = self._idle.setdefault(key, [])
            if idle:
                return idle.pop()
            self._n += 1
            n = self._n
        try:
            w = _Worker(self, key, n)
        except Exception as e:
            with self._lock:
                self._spawn_fail += 1
                if self._spawn_fail >= 3:
                    self.disabled = f"{self._spawn_fail} consecutive worker start failures, last: {e}"
            raise
        with self._lock:
            self._spawn_fail = 0
            self._all.append(w)
        self._record(dict(event="spawn", t=time.time(), worker=n, pid=w.pid, key=key,
                          startup_cpu_s=w.startup_cpu_s, log=str(w.log)))
        self.log(f"fastpath: worker {n} pid={w.pid} for {key} started (startup_cpu_s={w.startup_cpu_s})")
        return w

    def run(self, key: str, req: dict) -> dict:
        w = self._get(key)
        try:
            msg = w.request(req)
        except BaseException:
            w.kill()
            with self._lock:
                if w in self._all:
                    self._all.remove(w)
            self._record(dict(event="killed", t=time.time(), worker=w.n, pid=w.pid, key=key, tests=w.tests))
            raise
        msg["worker"] = w.n
        with self._lock:
            self._idle.setdefault(key, []).append(w)
        return msg

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            ws = list(self._all)
        for w in ws:
            w.close()
            self._record(dict(event="exit", t=time.time(), worker=w.n, pid=w.pid, key=w.key, tests=w.tests,
                              rc=w.p.poll()))
        if ws:
            try:
                self.log(f"fastpath: pool closed ({len(ws)} workers, "
                         f"{sum(w.tests for w in ws)} tests on live workers)")
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--code-root", required=True)
    s.add_argument("--log", required=True)
    s.add_argument("--key", default="?")
    a = ap.parse_args()
    serve(a.code_root, a.log, a.key)


if __name__ == "__main__":
    main()

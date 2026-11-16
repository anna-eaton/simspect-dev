#!/usr/bin/env python3
"""linetrace.py -- minimal line-coverage tracer (no coverage.py on the Mac / nodes). Runs a script under sys.settrace
and appends the executed (file, line) pairs of files under PREFIX to <out>.jsonl. Used to find code that no make
target executes before pruning the anonymous artifact (agent anonrepo, 2026-11-16).
Usage: LT_PREFIX=<dir> LT_OUT=<file> python3 linetrace.py <script.py> [args...]
"""
import atexit, json, os, runpy, sys, threading

PREFIX = os.environ["LT_PREFIX"]
OUT = os.environ["LT_OUT"]
hits = {}


def tr(frame, event, arg):
    f = frame.f_code.co_filename
    if not f.startswith(PREFIX):
        return None
    s = hits.setdefault(f, set())

    def lt(fr, ev, a):
        if ev == "line":
            s.add(fr.f_lineno)
        return lt
    s.add(frame.f_lineno)
    return lt


def dump():
    sys.settrace(None)
    with open(OUT, "a") as fh:
        fh.write(json.dumps({k: sorted(v) for k, v in hits.items()}) + "\n")


atexit.register(dump)
sys.settrace(tr)
threading.settrace(tr)
script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")

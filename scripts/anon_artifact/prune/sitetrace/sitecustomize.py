"""sitecustomize.py -- line tracer for every Python process started with this dir on PYTHONPATH (agent anonrepo,
2026-11-16). Active only when LT_PREFIX and LT_OUT are set: records executed lines of files under LT_PREFIX and
appends them (one JSON object per process) to LT_OUT at exit and every 60 s (persistent workers may be killed)."""
import atexit, json, os, sys, threading, time

_P = os.environ.get("LT_PREFIX")
_O = os.environ.get("LT_OUT")
if _P and _O:
    _hits = {}
    _last = [time.time()]

    def _dump():
        try:
            with open(_O, "a") as fh:
                fh.write(json.dumps({k: sorted(v) for k, v in list(_hits.items())}) + "\n")
        except Exception:
            pass

    def _tr(frame, event, arg):
        f = frame.f_code.co_filename
        if not f.startswith(_P):
            return None
        s = _hits.setdefault(f, set())
        s.add(frame.f_lineno)

        def lt(fr, ev, a):
            if ev == "line":
                s.add(fr.f_lineno)
                if time.time() - _last[0] > 60:
                    _last[0] = time.time(); _dump()
            return lt
        return lt

    atexit.register(_dump)
    sys.settrace(_tr)
    threading.settrace(_tr)

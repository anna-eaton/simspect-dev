#!/usr/bin/env python3
"""rsa8_check.py -- apply rsa8_trace.py's R-SA-8 verdict (runconfigs/twostage_lp/eval_20261110/rsa8_trace.py lines 37-49, same
regexes and rule) to a kept full trace. Usage: rsa8_check.py <run dir with pipeview.txt.gz and ts/X/<mode>/ann/<stem>.ann.json>"""
import glob, gzip, json, re, sys
from pathlib import Path
W = Path(sys.argv[1]); ann = json.load(open(glob.glob(str(W / "ts/X/*/ann/*.ann.json"))[0])); xpc = ann["xmit"].get("addr")
lines = [l for l in gzip.open(W / "pipeview.txt.gz", "rt", errors="replace") if re.search(r"delay_unit|resolve_(hold|release|visible)", l)]
hold = [l for l in lines if "resolve_hold" in l and "mispred=1" in l]
fire = max((int(re.search(r"fire=(\d+)", l).group(1)) for l in hold), default=None)
xv = [l for l in lines if "resolve_visible" in l and f"pc={hex(xpc)}:" in l and "mispred=1" in l]
xtick = min((int(l.split(":")[2]) for l in xv), default=None)
ins = [l for l in lines if "Inserting branch" in l]; rel = [l for l in lines if "Released tainted branch" in l]
rtick = min((int(l.split(":")[0]) for l in rel), default=None)
ok = bool(ins) and rtick is not None and fire is not None and xtick is not None and rtick < fire and xtick < fire
print(json.dumps(dict(run=W.name, xmit_pc=hex(xpc), hold_fire=fire, xmit_mispred_resolve=xtick, first_release=rtick, n_inserted=len(ins), rsa8_signature=ok)))

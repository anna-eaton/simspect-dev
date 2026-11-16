#!/usr/bin/env python3
"""check_bound_consistency.py — read-only lint: is everything in a model that is tied to the instruction
bound N consistent with the run scope?  (stage15-bound S1-S4, wiki/design/TWO_PHASE_MODELS.md.)
Checks, for the FIRST run command:
  fold   the protection-set fold (last_committed_protset_p / protset_p) applies the step at >= N positions
         (too shallow = instructions past the fold depth never update the protection set -> invented leaks)
  ix     the IX position atoms number >= N for an exact scope (fewer = UNSAT by pigeonhole)
  int    if the model uses '#' and more than 9 operands can exist, the scope sets an Int bitwidth
         (default 4-bit Int wraps at 8: cardinality caps pass vacuously)
  ops    operand scope (informational)
  fixpt  WARN only (never fails): any other function applied to itself a fixed number of times inside one
         body (e.g. the ultimate SPT spt_public_p = spt_step_p nested 6 deep, in the defense block) with
         nesting depth < N.  Whether that depth must follow N is a model decision, so it is only reported.
Exit 1 if any check fails.  Usage: check_bound_consistency.py M.als [M2.als ...]"""
import re, sys
from pathlib import Path
bad = 0
for f in sys.argv[1:]:
    t = Path(f).read_text()
    code = "\n".join(l.split("//")[0] for l in t.splitlines())
    m = re.search(r"run\s+\w+\s*\{.*?\}\s*for\s+(\d+)\s+but\s+(exactly\s+)?(\d+)\s+Instruction([^\n]*)", code, re.S)
    if not m:
        print(f"{f}: no 'run ... for K but [exactly] N Instruction' found"); bad = 1; continue
    default, exact, n, rest = int(m.group(1)), bool(m.group(2)), int(m.group(3)), m.group(4)
    fm = re.search(r"fun\s+(protset_p|last_committed_protset_p)\b.*?\n\}", code, re.S)
    depth = len(re.findall(r"\ba\[p\s*,", fm.group(0))) if fm else 0
    ix = len(set(re.findall(r"one sig (IX\d+)", code)))
    om = re.search(r"(\d+)\s+Operand", rest); ops = int(om.group(1)) if om else default
    has_int = bool(re.search(r"\d+\s+Int\b", rest)); uses_card = "#" in code
    res = [("fold", depth >= n, f"depth {depth} vs N {n}"),
           ("ix", (ix == 0) or (ix >= n if not exact else ix == n), f"{ix} IX atoms vs {'exactly ' if exact else 'up to '}{n}"),
           ("int", (not uses_card) or ops <= 9 or has_int, f"'#' used={uses_card}, operand scope {ops}, Int set={has_int}")]
    ok = all(r[1] for r in res); bad |= not ok
    warn = []
    for b in re.finditer(r"(?:fun|pred)\s+(\w+)\b.*?\n\}", code, re.S):
        for name in set(re.findall(r"\b(\w+)\[p\s*,", b.group(0))) - {"a", b.group(1)}:
            k = len(re.findall(r"\b%s\[p\s*,\s*(?=%s\[p\s*,|\w+\s*\])" % (name, name), b.group(0)))
            nest = len(re.findall(r"\b%s\[p\s*,\s*(?=%s\[p\s*,)" % (name, name), b.group(0))) + 1
            if nest >= 3 and nest < n: warn.append(f"{b.group(1)}: {name} nested {nest} deep vs N {n}")
    print(f"{'OK  ' if ok else 'FAIL'} {f}: " + "; ".join(f"{k} {'ok' if v else 'FAIL'} ({d})" for k, v, d in res)
          + ("".join(f"\n  WARN fixpt {w}" for w in warn)))
sys.exit(bad)

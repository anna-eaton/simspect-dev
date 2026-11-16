#!/usr/bin/env python3
"""tokcheck.py -- stronger code-equivalence check for build_trees.py output (2026-11-16): for every file we touched,
the token stream the compiler/interpreter sees is identical between the node tree and the stripped tree.
C-like: comments replaced by one space (as the C preprocessor does), then tokenized. Python: ast.dump equality when the
file parses under Python 3, else tokenize token streams (COMMENT/NL/NEWLINE/INDENT-free) compared.
Usage: tokcheck.py <staging> <out root> [build ...]"""
import ast, io, json, re, sys, tokenize
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_trees as bt

TOK = re.compile(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|[A-Za-z_]\w*|\d[\w.]*|\S')


def ctoks(t):
    buf, last = [], 0
    for s, e in bt.c_comment_spans(t):
        buf.append(t[last:s]); buf.append(" "); last = e
    buf.append(t[last:])
    return TOK.findall("".join(buf))


def _norm(tree):
    for node in ast.walk(tree):
        for f in ("body", "orelse", "finalbody"):
            b = getattr(node, f, None)
            if isinstance(b, list) and b and all(isinstance(x, ast.stmt) for x in b):
                nb = [x for x in b if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant) and isinstance(x.value.value, str))]
                setattr(node, f, nb or [ast.Pass()])
    return tree


def ptoks(t):
    try:
        return ("ast", ast.dump(_norm(ast.parse(t))))
    except SyntaxError:
        pass
    for s, e, np, ind in reversed(bt.py_bare_string_spans(t)):
        t = t[:s] + ("pass" if np else "") + "\n" * t.count("\n", s, e) + t[e:]
    out = []
    for x in tokenize.generate_tokens(io.StringIO(t).readline):
        if x.type in (tokenize.COMMENT, tokenize.NL) or (x.type == tokenize.NAME and x.string == 'pass'):
            continue
        out.append((x.type, x.string if x.type != tokenize.INDENT else "IND"))
    return ("tok", out)


stg, outr = Path(sys.argv[1]), Path(sys.argv[2])
for b in sys.argv[3:] or list(bt.BUILDS):
    rep = json.loads((stg / f"report_{b}.json").read_text())
    bad, n, modes = [], 0, {}
    for rel in rep["modified"] + rep["added"] + rep.get("base_local_edit_stripped", []):
        p, q = stg / "node" / b / rel, outr / b / rel
        k = bt.kind(q)
        if not k:
            continue
        a, c = p.read_text(encoding="utf-8"), q.read_text(encoding="utf-8")
        n += 1
        if k == "c":
            ok = ctoks(a) == ctoks(c); modes["c"] = modes.get("c", 0) + 1
        else:
            try:
                x, y = ptoks(a), ptoks(c)
                ok = x == y; modes[x[0]] = modes.get(x[0], 0) + 1
            except Exception as e:
                ok = False
        if not ok:
            bad.append(rel)
    print(b, f"files {n} token-identical {n - len(bad)} modes {modes}", "MISMATCH " + " ".join(bad) if bad else "")

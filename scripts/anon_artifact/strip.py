#!/usr/bin/env python3
"""strip.py -- comment strippers used by build_anon.py / verify_anon.py (anonymous artifact, 2026-11-16).

Python: tokenize + ast based (never regex inside string literals). Removes every COMMENT token (shebang included)
and every bare string-expression statement (docstrings and any other statement-level string); a body left empty
gets `pass` at the same indentation. Behaviour is preserved: check_py_equiv() compares the AST of the original
(minus bare strings, plus `pass` where needed) with the AST of the stripped file.
Alloy / Java / C-like: character scanners that understand string (and, for Java/C, char) literals.
"""
import ast, io, tokenize


def _bodies(tree):
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            b = getattr(node, field, None)
            if isinstance(b, list) and b and all(isinstance(s, ast.stmt) for s in b):
                yield node, field, b
        for h in getattr(node, "handlers", []) or []:
            pass


def _is_bare_str(s):
    return isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)


def normalize_tree(tree):
    """Remove bare-string statements from every statement list; empty list -> [Pass]."""
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            b = getattr(node, field, None)
            if isinstance(b, list) and b and all(isinstance(s, ast.stmt) for s in b):
                nb = [s for s in b if not _is_bare_str(s)]
                if not nb and field == "body" or (not nb and b):
                    nb = [ast.Pass()]
                setattr(node, field, nb)
    return tree


def strip_py(src):
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    delete = set()
    replace_with_pass = {}
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            b = getattr(node, field, None)
            if not (isinstance(b, list) and b and all(isinstance(s, ast.stmt) for s in b)):
                continue
            bare = [s for s in b if _is_bare_str(s)]
            if not bare:
                continue
            for s in bare:
                first, last = s.lineno, s.end_lineno
                pre = lines[first - 1][: s.col_offset]
                post = lines[last - 1][s.end_col_offset:]
                if pre.strip() or (post.strip() and not post.strip().startswith("#")):
                    raise ValueError(f"bare string at line {first} shares its line with code")
                for ln in range(first, last + 1):
                    delete.add(ln)
            if len(bare) == len(b):
                s = bare[0]
                replace_with_pass[s.lineno] = " " * s.col_offset + "pass\n"
    comment_only, truncate = set(), {}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            row, col = tok.start
            if not lines[row - 1][:col].strip():
                comment_only.add(row)
            else:
                truncate[row] = col
    out = []
    for i, line in enumerate(lines, 1):
        if i in replace_with_pass:
            out.append(replace_with_pass[i]); continue
        if i in delete or i in comment_only:
            continue
        if i in truncate:
            nl = "\n" if line.endswith("\n") else ""
            line = line[: truncate[i]].rstrip() + nl
        out.append(line)
    res = "".join(out)
    while "\n\n\n\n" in res:
        res = _collapse_blank_runs(res)
        break
    return res


def _collapse_blank_runs(res):
    """Collapse runs of 3+ blank lines to 2, but only outside string tokens."""
    lines = res.splitlines(keepends=True)
    protected = set()
    for tok in tokenize.generate_tokens(io.StringIO(res).readline):
        if tok.type == tokenize.STRING or tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            if tok.end[0] > tok.start[0]:
                protected.update(range(tok.start[0], tok.end[0] + 1))
    out, run = [], 0
    for i, line in enumerate(lines, 1):
        if not line.strip() and i not in protected:
            run += 1
            if run > 2:
                continue
        else:
            run = 0
        out.append(line)
    return "".join(out)


def py_comment_report(src):
    """-> (n COMMENT tokens, n bare string statements)."""
    n_c = sum(1 for t in tokenize.generate_tokens(io.StringIO(src).readline) if t.type == tokenize.COMMENT)
    tree = ast.parse(src)
    n_s = 0
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            b = getattr(node, field, None)
            if isinstance(b, list):
                n_s += sum(1 for s in b if isinstance(s, ast.stmt) and _is_bare_str(s))
    return n_c, n_s


def _scan(src, line_markers, block=True, quotes='"', escapes=True):
    """Generic scanner. Returns (code_without_comments, n_comments)."""
    out, i, n, cnt = [], 0, len(src), 0
    while i < n:
        c = src[i]
        if c in quotes:
            j = i + 1
            while j < n and src[j] != c:
                if escapes and src[j] == "\\":
                    j += 1
                if src[j] == "\n" and c == "'":
                    break
                j += 1
            out.append(src[i:j + 1]); i = j + 1; continue
        if block and src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                raise ValueError("unterminated block comment")
            out.append("\n" * src.count("\n", i, j + 2)); cnt += 1; i = j + 2; continue
        m = next((mk for mk in line_markers if src.startswith(mk, i)), None)
        if m:
            j = src.find("\n", i)
            j = n if j < 0 else j
            cnt += 1; i = j; continue
        out.append(c); i += 1
    return "".join(out), cnt


def _tidy(orig, stripped):
    """Drop lines that held only a comment (now blank), rstrip the rest, keep genuinely blank lines (max 1 run)."""
    ol, sl = orig.split("\n"), stripped.split("\n")
    assert len(ol) == len(sl)
    out = []
    for o, s in zip(ol, sl):
        if not s.strip():
            if o.strip():
                continue
            if out and not out[-1].strip():
                continue
            out.append("")
        else:
            out.append(s.rstrip())
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out).rstrip("\n") + "\n"


def strip_als(src):
    s, _ = _scan(src, ("//", "--"), block=True, quotes='"')
    return _tidy(src, s)


def strip_java(src):
    s, _ = _scan(src, ("//",), block=True, quotes="\"'")
    return _tidy(src, s)


def count_als(src):
    return _scan(src, ("//", "--"), block=True, quotes='"')[1]


def count_java(src):
    return _scan(src, ("//",), block=True, quotes="\"'")[1]


def strip_c_line(line, state):
    """Strip // and /* */ comments from one C/C++/SLICC line; state = {'in_block': bool}. Returns stripped line."""
    out, i, n = [], 0, len(line)
    while i < n:
        if state["in_block"]:
            j = line.find("*/", i)
            if j < 0:
                return "".join(out)
            state["in_block"] = False; i = j + 2; continue
        c = line[i]
        if c in "\"'":
            j = i + 1
            while j < n and line[j] != c:
                if line[j] == "\\":
                    j += 1
                j += 1
            out.append(line[i:j + 1]); i = j + 1; continue
        if line.startswith("//", i):
            break
        if line.startswith("/*", i):
            state["in_block"] = True; i += 2; continue
        out.append(c); i += 1
    return "".join(out)


def strip_py_line(line):
    """Strip a # comment from one Python line (quote-aware within the line; for patch '+' lines)."""
    i, n, q = 0, len(line), None
    while i < n:
        c = line[i]
        if q:
            if c == "\\":
                i += 2; continue
            if line.startswith(q, i):
                i += len(q); q = None; continue
        else:
            if line.startswith('"""', i) or line.startswith("'''", i):
                q = line[i:i + 3]; i += 3; continue
            if c in "\"'":
                q = c
            elif c == "#":
                return line[:i]
        i += 1
    return line

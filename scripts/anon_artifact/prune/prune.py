#!/usr/bin/env python3
"""prune.py -- AST-guided source pruning for the anonymous artifact (agent anonrepo, 2026-11-16).

Anna: the artifact holds only the unified recipe-A pipeline and what the make targets execute, so switched-off
modes, legacy recipes, post-pass hooks and debug/one-off options are removed (chain interleaving stays, off by
default). Each operation is applied to the comment-free source and re-parsed; every op must match (count checked),
so a source change upstream makes the build fail loudly instead of silently keeping dead code.

Ops (tuples):
  ("del_def", "name" | "Class.name" | "outer.inner")      delete a def/class (any nesting, by dotted path)
  ("drop_if", scope, test_src, keep, n)                     replace every If whose ast.unparse(test) == test_src
                                                            inside scope (a dotted def path, or None = whole file)
                                                            by its else branch (keep="else") or its body (keep="body");
                                                            n = expected number of matches
  ("del_stmt", scope, prefix, n)                            delete statements whose ast.unparse starts with prefix
  ("text", old, new, n)                                     exact text replacement, n occurrences
  ("replace_def", "name", new_source)                       replace a def by new source (same indentation)
"""
import ast
import textwrap


def _find_def(tree, path):
    cur = [tree]
    node = None
    for part in path.split("."):
        found = None
        for c in cur:
            for n in ast.walk(c):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == part:
                    found = n
                    break
            if found:
                break
        if not found:
            raise KeyError(f"def {path!r} not found")
        node, cur = found, [found]
    return node


def _block_text(lines, stmts, target_col):
    a, b = stmts[0].lineno, stmts[-1].end_lineno
    seg = "\n".join(lines[a - 1:b])
    ded = textwrap.dedent(seg)
    return textwrap.indent(ded, " " * target_col, lambda l: True).split("\n")


def _first_stmt_line(n):
    return getattr(n, "decorator_list", None) and n.decorator_list[0].lineno or n.lineno


def apply(src, ops):
    for op in ops:
        kind = op[0]
        if kind == "text":
            _, old, new, n = op
            c = src.count(old)
            if c != n:
                raise ValueError(f"text op: {c} != {n} occurrences of {old[:70]!r}")
            src = src.replace(old, new)
            continue
        tree = ast.parse(src)
        lines = src.split("\n")
        if kind == "replace_def":
            node = _find_def(tree, op[1])
            a, b = _first_stmt_line(node), node.end_lineno
            new = textwrap.indent(textwrap.dedent(op[2]).strip("\n"), " " * node.col_offset).split("\n")
            lines[a - 1:b] = new
            src = "\n".join(lines)
            continue
        if kind == "del_def":
            node = _find_def(tree, op[1])
            a, b = _first_stmt_line(node), node.end_lineno
            parent_body = None
            for p in ast.walk(tree):
                for fld in ("body", "orelse", "finalbody"):
                    bl = getattr(p, fld, None)
                    if isinstance(bl, list) and node in bl:
                        parent_body = bl
            repl = []
            if parent_body is not None and len(parent_body) == 1:
                repl = [" " * node.col_offset + "pass"]
            lines[a - 1:b] = repl
            src = "\n".join(lines)
            continue
        scope = tree if op[1] is None else _find_def(tree, op[1])
        if kind == "drop_if":
            _, _, test_src, keep, n = op
            hits = [x for x in ast.walk(scope) if isinstance(x, ast.If) and ast.unparse(x.test) == test_src]
            if len(hits) != n:
                raise ValueError(f"drop_if {test_src!r} in {op[1]}: {len(hits)} != {n}")
            for node in sorted(hits, key=lambda x: -x.lineno):
                is_elif = lines[node.lineno - 1].lstrip().startswith("elif")
                col = node.col_offset
                chosen = node.body if keep == "body" else node.orelse
                if is_elif:
                    if keep == "else" and chosen and len(chosen) == 1 and isinstance(chosen[0], ast.If) and \
                            lines[chosen[0].lineno - 1].lstrip().startswith("elif"):
                        a, b = chosen[0].lineno, node.orelse[-1].end_lineno
                        new = lines[a - 1:b]
                        lines[node.lineno - 1:node.end_lineno] = new
                    elif keep == "else" and chosen:
                        else_line = next(i for i in range(chosen[0].lineno - 1, node.lineno - 1, -1)
                                         if lines[i - 1].strip() == "else:")
                        lines[node.lineno - 1:node.end_lineno] = [" " * col + "else:"] + lines[else_line:node.end_lineno]
                    elif keep == "else":
                        lines[node.lineno - 1:node.end_lineno] = []
                    else:
                        raise ValueError("keep=body on an elif is not supported")
                    continue
                if not chosen:
                    new = []
                elif keep == "else" and len(chosen) == 1 and isinstance(chosen[0], ast.If) and \
                        lines[chosen[0].lineno - 1].lstrip().startswith("elif"):
                    sub = chosen[0]
                    seg = lines[sub.lineno - 1:sub.end_lineno]
                    seg[0] = seg[0].replace("elif", "if", 1)
                    new = seg
                else:
                    new = _block_text(lines, chosen, col)
                parent = None
                for p in ast.walk(tree):
                    for fld in ("body", "orelse", "finalbody"):
                        bl = getattr(p, fld, None)
                        if isinstance(bl, list) and node in bl:
                            parent = bl
                if not new and parent is not None and len(parent) == 1:
                    new = [" " * col + "pass"]
                lines[node.lineno - 1:node.end_lineno] = new
            src = "\n".join(lines)
            continue
        if kind == "del_stmt":
            _, _, prefix, n = op
            hits = [x for x in ast.walk(scope) if isinstance(x, ast.stmt) and ast.unparse(x).startswith(prefix)
                    and not isinstance(x, (ast.FunctionDef, ast.ClassDef))]
            if n is not None and len(hits) != n:
                raise ValueError(f"del_stmt {prefix!r} in {op[1]}: {len(hits)} != {n}")
            for node in sorted(hits, key=lambda x: -x.lineno):
                a, b = node.lineno, node.end_lineno
                line = lines[a - 1]
                if line[:node.col_offset].strip() or lines[b - 1][node.end_col_offset:].strip().strip(";"):
                    seg = "\n".join(lines[a - 1:b])
                    start = sum(len(l) + 1 for l in lines[:a - 1]) + node.col_offset
                    whole = "\n".join(lines)
                    end = sum(len(l) + 1 for l in lines[:b - 1]) + node.end_col_offset
                    rest = whole[end:]
                    if rest.startswith(";"):
                        rest = rest[1:].lstrip(" ")
                    whole = whole[:start] + rest
                    lines = whole.split("\n")
                else:
                    lines[a - 1:b] = []
            src = "\n".join(lines)
            continue
        raise ValueError(f"unknown op {kind}")
    ast.parse(src)
    return src

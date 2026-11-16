#!/usr/bin/env python3
"""Check that two versions of a Python file differ only in comments/docstrings.

Usage: python3 scripts/check_ast_same.py <before.py> <after.py> [<before2> <after2> ...]
Exits 1 if any pair's AST (with docstrings stripped) differs.
"""
import ast
import sys


def _strip_docstrings(tree):
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return tree


def _dump(path):
    with open(path, encoding="utf-8") as f:
        return ast.dump(_strip_docstrings(ast.parse(f.read(), path)))


def main(argv):
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    bad = 0
    for before, after in zip(argv[0::2], argv[1::2]):
        same = _dump(before) == _dump(after)
        print(("SAME  " if same else "DIFF  ") + after)
        bad += not same
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

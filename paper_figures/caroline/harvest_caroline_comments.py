#!/usr/bin/env python3
"""Harvest every \\caroline{...} comment in the ISCA-27 paper's working tree.

Anna keeps Caroline's comments in the source until they are addressed; she
comments them out (a leading %) to hide them from the PDF, which does not mean
resolved. So this reads the current .tex files only (no git history), extracts
each \\caroline{...} with balanced braces, and prints markdown with file:line,
whether it is commented out, and the text around it.

Usage: python3 harvest_caroline_comments.py [--repo ~/trippel/ISCA-27]
"""
import argparse
import os
import re
from pathlib import Path

CTX = 350  # characters of surrounding text kept on each side


def extract(text):
    """Yield (start, end, body) for every \\caroline{...}, braces balanced."""
    for m in re.finditer(r"\\caroline\{", text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            depth += (c == "{") - (c == "}")
            i += 1
        if depth == 0:
            yield m.start(), i, text[m.end():i - 1]


def norm(s):
    return " ".join(s.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.expanduser("~/trippel/ISCA-27"))
    repo = ap.parse_args().repo

    rows = []
    for path in sorted(Path(repo).rglob("*.tex")):
        rel = str(path.relative_to(repo))
        text = path.read_text(errors="replace")
        for s, e, body in extract(text):
            if body.strip() == "#1":  # the \newcommand definition
                continue
            line_start = text.rfind("\n", 0, s) + 1
            out = text[line_start:s].lstrip().startswith("%")
            rows.append((rel, text.count("\n", 0, s) + 1, out, norm(body),
                         norm(text[max(0, s - CTX):s]), norm(text[e:e + CTX])))

    n_out = sum(r[2] for r in rows)
    print(f"{len(rows)} \\caroline comments in {repo} "
          f"({len(rows) - n_out} visible, {n_out} commented out; "
          f"commented out means hidden, not resolved)\n")
    for rel, line, out, body, before, after in rows:
        tag = " (commented out)" if out else ""
        print(f"- `{rel}:{line}`{tag}: **{body}**")
        print(f"  > …{before} ⟦CAROLINE⟧ {after}…\n")


if __name__ == "__main__":
    main()

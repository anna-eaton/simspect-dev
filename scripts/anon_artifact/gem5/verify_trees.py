#!/usr/bin/env python3
"""verify_trees.py -- checks for build_trees.py output (2026-11-16).
(a) our lines (stripped file vs pristine, difflib) carry 0 comments and 0 identity hits; every file we added/modified is
    identity-grepped in full on our lines; (b) code unchanged: node file and stripped file are equal once ALL comments
    are removed from both and blank lines / trailing spaces are normalized.
Usage: verify_trees.py <staging> <out root> [build ...]"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_trees as bt

ID_RE = re.compile(r"(?i)anna|eaton|trippel|caroline|stanford|cafe\d|\bcafe\b|acbeaton|anna-eaton|claude|anthropic|/users/|/work/|/tests/|/afs/|"
                   r"sherlock|gem5_dev|20\d\d-\d\d-\d\d|202[56]1[01]\d\d|@[a-z0-9-]+\.(edu|com|org)")


def nocomments(text, k):
    spans = bt.c_comment_spans(text) if k == "c" else sorted(bt.py_comment_spans(text) + [(x[0], x[1]) for x in bt.py_bare_string_spans(text)])
    buf, last = [], 0
    for s, e in spans:
        buf.append(text[last:s]); last = e
    buf.append(text[last:])
    return [l.rstrip() for l in "".join(buf).splitlines() if l.strip() and l.strip() != "pass"]


def main():
    stg, out = Path(sys.argv[1]), Path(sys.argv[2])
    names = sys.argv[3:] or list(bt.BUILDS)
    tot = {}
    for b in names:
        rep = json.loads((stg / f"report_{b}.json").read_text())
        node, base, dst = stg / "node" / b, stg / bt.BUILDS[b], out / b
        n_com, n_id, n_neq, ids, neq, coms = 0, 0, 0, [], [], []
        for rel in rep["modified"] + rep["added"] + rep["new_noncode"] + rep.get("base_local_edit_stripped", []):
            p, bp, q = node / rel, base / rel, dst / rel
            k = bt.kind(q)
            try:
                new = q.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            old = bp.read_text(encoding="utf-8", errors="surrogateescape") if bp.is_file() else None
            if old is None and rel in rep.get("derived_from", {}):
                old = (base / rep["derived_from"][rel]).read_text(encoding="utf-8", errors="surrogateescape")
            lines = new.splitlines(keepends=True)
            ours = bt.ours_lines(lines, old.splitlines(keepends=True) if old is not None else None)
            for i in sorted(ours):
                if ID_RE.search(lines[i - 1]):
                    n_id += 1; ids.append(f"{rel}:{i}: {lines[i-1].strip()[:100]}")
            if k:
                starts = [0]
                for l in lines:
                    starts.append(starts[-1] + len(l))
                spans = bt.c_comment_spans(new) if k == "c" else bt.py_comment_spans(new) + [(x[0], x[1]) for x in bt.py_bare_string_spans(new)]
                import bisect
                for s, e in spans:
                    l1 = bisect.bisect_right(starts, s); l2 = bisect.bisect_right(starts, max(s, e - 1))
                    if any(l in ours for l in range(l1, l2 + 1)):
                        n_com += 1; coms.append(f"{rel}:{l1}: {new[s:e][:80]}")
                if nocomments(p.read_text(encoding="utf-8"), k) != nocomments(new, k):
                    n_neq += 1; neq.append(rel)
        tot[b] = dict(files_touched=len(rep["modified"]) + len(rep["added"]), our_line_comments=n_com, identity_hits=n_id,
                      code_changed_files=n_neq, comments_removed=rep["comments_removed"], mixed_skipped=len(rep["skipped_mixed"]))
        print(b, json.dumps(tot[b]))
        for x in (coms + ids)[:30]:
            print("   ", x)
        for x in neq:
            print("    CODE DIFF", x)
    (stg / "verify_summary.json").write_text(json.dumps(tot, indent=1))


if __name__ == "__main__":
    main()

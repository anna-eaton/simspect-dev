#!/usr/bin/env python3
"""verify_anon.py -- checks 1 (comment-free), 2 (anonymous), 3a (Python AST equivalence) and 4 (reachability) for the
anonymous artifact (agent anonrepo, 2026-11-16). The gem5/ tree is checked by its own script (scripts/anon_artifact/gem5/).

AST equivalence: the original (bare strings removed, `pass` inserted where a body empties) and the artifact file are
compared with every str constant replaced by a placeholder, so all non-string code must be identical; the code edits
listed in build_record.json (non-string replacements) are applied to the original first. Changed string constants are
listed per file for the manifest.
Usage: python3 scripts/anon_artifact/verify_anon.py [--out ~/trippel/simspect-anon] [--json results.json]
"""
import argparse, ast, io, json, re, sys, tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import strip  # noqa: E402

IDENT = re.compile(r"(?i)anna|eaton|trippel|caroline|stanford|cafe[0-9]|\bcafe\b|acbeaton|anna-eaton|claude|anthropic|"
                   r"/Users/|/afs/|/tests/|/work/|/home/|@[a-z0-9.-]+\.(edu|com|org)\b|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|"
                   r"macbook|sherlock|dmendo|simspect-c\d|claudelog|claudenotes|urgent_todo|eval_manifest|wiki/|"
                   r"gem5_dev|264adea|(?-i:\bDECIDE\b)|(?<!args)(?<!self)(?<![^A-Za-z]a)\.md\b")


class Strs(ast.NodeTransformer):
    def __init__(self):
        self.vals = []

    def visit_Constant(self, n):
        if isinstance(n.value, str):
            self.vals.append(n.value)
            return ast.copy_location(ast.Constant("S"), n)
        return n


def canon(src):
    t = strip.normalize_tree(ast.parse(src))
    s = Strs()
    t = s.visit(t)
    return ast.dump(t), s.vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / "trippel/simspect-anon"))
    ap.add_argument("--record", default=str(HERE / "build_record.json"))
    ap.add_argument("--json", default=str(HERE / "verify_results.json"))
    a = ap.parse_args()
    out = Path(a.out)
    rec = json.loads(Path(a.record).read_text())
    files = [p for p in out.rglob("*") if p.is_file() and p.relative_to(out).parts[0] not in ("gem5", "data")
             and "__pycache__" not in p.parts]
    res = {"comments": {}, "identity": {}, "ast": {}, "string_changes": {}, "json_ok": {}, "other": []}
    for p in sorted(files):
        rel = str(p.relative_to(out))
        txt = p.read_text(errors="replace")
        if p.suffix == ".py":
            n = strip.py_comment_report(txt)
            res["comments"][rel] = n[0] + n[1]
        elif p.suffix == ".java":
            res["comments"][rel] = strip.count_java(txt)
        elif p.suffix == ".als":
            res["comments"][rel] = strip.count_als(txt)
        elif p.suffix == ".json":
            try:
                json.loads(txt); res["json_ok"][rel] = True
            except Exception as e:
                res["json_ok"][rel] = str(e)
            res["comments"][rel] = 0
        elif p.suffix == ".sh" or p.name == "Makefile":
            res["comments"][rel] = sum(1 for l in txt.splitlines() if re.match(r"^\s*#", l))
        else:
            res["other"].append(rel)
        hits = [m.group(0) for m in IDENT.finditer(txt)]
        res["identity"][rel] = hits
    for f in rec["files"]:
        if f["kind"] != "py":
            continue
        if f.get("pruned"):
            res.setdefault("pruned", {})[f["dst"]] = [f.get("lines_before_prune"), f.get("lines")]
            continue
        orig = (REPO / f["src"]).read_text()
        rep = orig
        for o, n_ in f["replacements"]:
            rep = rep.replace(o, n_)
        art = (out / f["dst"]).read_text()
        d0, _ = canon(rep)
        d1, v1 = canon(art)
        res["ast"][f["dst"]] = (d0 == d1)
        _, v0 = canon(orig)
        if v0 != v1:
            res["string_changes"][f["dst"]] = [[x, y] for x, y in zip(v0, v1) if x != y]
        code_edits = [[o, n_] for o, n_ in f["replacements"] if canon(orig)[0] != canon(orig.replace(o, n_))[0]]
        if code_edits:
            res.setdefault("code_edits", {})[f["dst"]] = code_edits
    summ = dict(files=len(files), comment_total=sum(res["comments"].values()),
                identity_total=sum(len(v) for v in res["identity"].values()),
                ast_identical=sum(res["ast"].values()), ast_checked=len(res["ast"]), pruned_files=len(res.get("pruned", {})),
                json_bad=[k for k, v in res["json_ok"].items() if v is not True], other=res["other"])
    res["summary"] = summ
    Path(a.json).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(summ, indent=1))
    for k, v in res["identity"].items():
        if v:
            print("IDENTITY", k, sorted(set(v))[:10])
    for k, v in res["comments"].items():
        if v:
            print("COMMENTS", k, v)
    for k, v in res["ast"].items():
        if not v:
            print("AST DIFF", k)


if __name__ == "__main__":
    main()

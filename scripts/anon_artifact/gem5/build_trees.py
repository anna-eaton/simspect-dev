#!/usr/bin/env python3
"""build_trees.py -- anonymous-artifact gem5 source trees (2026-11-16, fork of agent anonrepo).

For each instrumented build: output = the build's source dirs + top-level build files, where every file identical to the
pristine upstream is copied unchanged, and every file we ADDED or MODIFIED has the comments on OUR lines removed
(our lines = lines of the node file not matched to the pristine file by difflib; for new files every line is ours).
Upstream comments are kept. Usage:
  build_trees.py <staging root with node/<build> and pristine/<base>> <out root> [build ...]
Writes <out>/<build>/ and a per-build JSON report to <staging>/report_<build>.json.
"""
import difflib, io, json, os, re, shutil, sys, tokenize
from pathlib import Path

BUILDS = {  # out/node name -> pristine dir name (under staging/pristine or staging/node)
    "amulet-gem5-InvisiSpec_AE-v1.1": "pristine/amulet-gem5-InvisiSpec_AE-v1.1",
    "amulet-gem5-CleanupSpec_AE-v1.1": "pristine/amulet-gem5-CleanupSpec_AE-v1.1",
    "amulet-gem5-SpecLFB_AE-v1.1": "pristine/amulet-gem5-SpecLFB_AE-v1.1",
    "amulet-gem5-STT_AE-v1.1": "pristine/amulet-gem5-STT_AE-v1.1",
    "gem5-recon-modded": "node/gem5-recon",
    "gem5-recon-ruby3": "node/gem5-recon",
    "stt": "pristine/stt",
    "stt-master": "pristine/stt-master",
    "gem5-spt": "pristine/gem5-spt",
}
# ReCon builds: /work/gem5-recon (the base) itself carries three local, trace-only edits of ours (HOOK_AUDIT 2026-11-07,
# "gem5-recon (the unhooked control)"); there is no pristine upstream copy to diff against, so their comments are removed
# by exact match here (each must match exactly once).
BASE_LOCAL_COMMENTS = {
    "src/cpu/o3/dyn_inst.hh": ["        TrueEffAddrValid, //ANNACODE\n", "        TrueEffAddrValid,\n"],
    "src/cpu/o3/iew.cc": ["""        // For loads, completeTick is set in LSQUnit::writeback() when data
        // actually arrives from cache.  Setting it here (at executeLoad time)
        // is premature: STT-blocked loads also return NoFault from executeLoad
        // and would get a phantom "complete" timestamp indistinguishable from
        // an unblocked load.
""", ""],
    "src/cpu/o3/lsq_unit.cc": ["""        // Record the tick at which the load's data actually arrived from
        // cache (or store-to-load forwarding).  This overwrites the
        // placeholder set by updateExeInstStats so that the O3PipeView
        // "complete" timestamp reflects real cache completion, not just
        // when executeLoad() was called.
""", ""],
}
# New files of ours that start as a copy of an upstream file: diff against that file, so the copied upstream lines
# (license header, upstream comments) are kept and only our lines are stripped.
DERIVED = [(re.compile(r"^configs/example/se_\w+\.py$"), "configs/example/se.py"),
           (re.compile(r"^src/cpu/o3/store_set_annot\.(cc|hh)$"), None)]


def derived_base(rel):
    for rx, tgt in DERIVED:
        if rx.match(rel):
            return tgt or rel.replace("store_set_annot", "store_set")
    return None


SRC_DIRS = {"src", "configs", "build_opts", "site_scons", "ext", "util", "include", "system", "tests", "build_tools"}
TOP_BUILD_FILES = {"README", "SConstruct", "SConsopts", "Makefile", "KCONFIG.md", "requirements.txt", "pyproject.toml"}
JUNK_RE = re.compile(r"(\.orig$|\.bak|\.rej$|~$|\.pre-|\.swp$|\.log$|\.pyc$|/__pycache__/|parsetab|\.o$|\.os$|\.do$)")
C_EXT = {".cc", ".hh", ".h", ".c", ".cpp", ".hpp", ".sm", ".slicc", ".isa", ".proto", ".i"}
PY_EXT = {".py"}
PY_NAMES = {"SConscript", "SConstruct", "SConsopts"}


def kind(p):
    if p.suffix in C_EXT:
        return "c"
    if p.suffix in PY_EXT or p.name in PY_NAMES:
        return "py"
    return None


def c_comment_spans(text):
    """[(start, end)] char spans of // and /* */ comments; string and char literal aware."""
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                if text[j] == "\\":
                    j += 1
                j += 1
            i = j + 1; continue
        if text.startswith("//", i):
            j = text.find("\n", i); j = n if j < 0 else j
            spans.append((i, j)); i = j; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2); j = n if j < 0 else j + 2
            spans.append((i, j)); i = j; continue
        i += 1
    return spans


def py_comment_spans(text):
    spans = []
    try:
        offs = [0]
        for line in text.splitlines(keepends=True):
            offs.append(offs[-1] + len(line))
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type == tokenize.COMMENT:
                s = offs[t.start[0] - 1] + t.start[1]
                spans.append((s, s + len(t.string)))
        return spans
    except (tokenize.TokenError, SyntaxError, IndentationError):
        pass
    spans, off = [], 0  # fallback: per-line quote-aware '#'
    for line in text.splitlines(keepends=True):
        q, i = None, 0
        while i < len(line):
            ch = line[i]
            if q:
                if ch == "\\":
                    i += 2; continue
                if line.startswith(q, i):
                    i += len(q); q = None; continue
            elif line.startswith('"""', i) or line.startswith("'''", i):
                q = line[i:i + 3]; i += 3; continue
            elif ch in "\"'":
                q = ch
            elif ch == "#":
                spans.append((off + i, off + len(line.rstrip("\n")))); break
            i += 1
        off += len(line)
    return spans


def ours_lines(new_lines, old_lines):
    """1-based line numbers of new_lines not matched to old_lines."""
    if old_lines is None:
        return set(range(1, len(new_lines) + 1))
    sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    ours = set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            ours.update(range(j1 + 1, j2 + 1))
    return ours


def py_bare_string_spans(text):
    """[(start, end, needs_pass, indent)] spans of statement-level string literals (docstrings), via tokenize."""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return []
    offs = [0]
    for line in text.splitlines(keepends=True):
        offs.append(offs[-1] + len(line))
    off = lambda rc: offs[rc[0] - 1] + rc[1]
    sig = [t for t in toks if t.type not in (tokenize.COMMENT, tokenize.NL)]
    out = []
    for i, t in enumerate(sig):
        if t.type != tokenize.STRING:
            continue
        prev = sig[i - 1] if i else None
        if prev is not None and prev.type not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            continue
        j = i
        while j + 1 < len(sig) and sig[j + 1].type == tokenize.STRING:
            j += 1
        if j + 1 < len(sig) and sig[j + 1].type not in (tokenize.NEWLINE, tokenize.ENDMARKER):
            continue
        k = j + 2
        nxt = sig[k] if k < len(sig) else None
        needs_pass = (prev is not None and prev.type == tokenize.INDENT and (nxt is None or nxt.type in (tokenize.DEDENT, tokenize.ENDMARKER)))
        out.append((off(t.start), off(sig[j].end), needs_pass, " " * t.start[1]))
    return out


def strip_ours(text, old_text, k):
    lines = text.splitlines(keepends=True)
    ours = ours_lines(lines, old_text.splitlines(keepends=True) if old_text is not None else None)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))
    import bisect
    line_of = lambda o: bisect.bisect_right(starts, o)
    spans = [(s, e, None) for s, e in (c_comment_spans(text) if k == "c" else py_comment_spans(text))]
    if k == "py":
        spans += [(s, e, "pass" if np else "") for s, e, np, ind in py_bare_string_spans(text)]
        spans.sort()
    remove, skipped = [], []
    for s, e, rep in spans:
        l1, l2 = line_of(s), line_of(max(s, e - 1))
        if all(l in ours for l in range(l1, l2 + 1)):
            remove.append((s, e, rep))
        elif any(l in ours and re.search(r"[A-Za-z0-9]", lines[l - 1]) for l in range(l1, l2 + 1)):
            remove.append((s, e, rep))
            skipped.append((l1, l2, "REMOVED (comment block partly upstream, holds our text): " + text[s:e][:60]))
        elif any(l in ours for l in range(l1, l2 + 1)):
            skipped.append((l1, l2, "KEPT (our lines in it are punctuation only): " + text[s:e][:60]))
    if not remove:
        return text, 0, skipped
    buf, last = [], 0
    for s, e, rep in remove:
        buf.append(text[last:s]); buf.append((rep or "") + "\n" * text.count("\n", s, e)); last = e
    buf.append(text[last:])
    out = "".join(buf)
    olines = out.splitlines(keepends=True)
    assert len(olines) == len(lines), "line count changed"
    touched = set()
    for s, e, rep in remove:
        touched.update(range(line_of(s), line_of(max(s, e - 1)) + 1))
    res = []
    for i, (l, orig) in enumerate(zip(olines, lines), 1):
        if i in touched:
            if not l.strip():
                continue
            nl = "\n" if l.endswith("\n") else ""
            l = l.rstrip() + nl
        res.append(l)
    return "".join(res), len(remove), skipped


def include(rel):
    parts = rel.split("/")
    if JUNK_RE.search("/" + rel):
        return False
    if len(parts) == 1:
        return True
    return parts[0] in SRC_DIRS


def main():
    stg, out = Path(sys.argv[1]), Path(sys.argv[2])
    names = sys.argv[3:] or list(BUILDS)
    for b in names:
        node, base = stg / "node" / b, stg / BUILDS[b]
        rep = dict(build=b, base=str(BUILDS[b]), copied=0, modified=[], added=[], deleted=[], comments_removed=0,
                   skipped_mixed=[], new_binary=[], top_excluded=[], new_noncode=[])
        dst = out / b
        if dst.exists():
            shutil.rmtree(dst)
        base_files = {str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and not p.is_symlink()}
        for p in sorted(node.rglob("*")):
            if not (p.is_file() or p.is_symlink()):
                continue
            rel = str(p.relative_to(node))
            top_level = "/" not in rel
            if top_level and rel not in base_files and rel not in TOP_BUILD_FILES:
                rep["top_excluded"].append(rel); continue
            if not top_level and rel.split("/")[0] not in SRC_DIRS:
                continue
            if JUNK_RE.search("/" + rel):
                if rel not in base_files:
                    rep["top_excluded"].append(rel)
                    continue
            q = dst / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            if p.is_symlink():
                os.symlink(os.readlink(p), q); continue
            bp = base / rel
            data = p.read_bytes()
            if bp.is_file() and bp.read_bytes() == data:
                shutil.copy2(p, q); rep["copied"] += 1; continue
            k = kind(p)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is None or k is None:
                shutil.copy2(p, q)
                (rep["modified"] if bp.is_file() else (rep["new_binary"] if text is None else rep["new_noncode"])).append(rel)
                continue
            old = bp.read_text(encoding="utf-8", errors="surrogateescape") if bp.is_file() else None
            if old is None and derived_base(rel) and (base / derived_base(rel)).is_file():
                old = (base / derived_base(rel)).read_text(encoding="utf-8", errors="surrogateescape")
                rep.setdefault("derived_from", {})[rel] = derived_base(rel)
            new, n, sk = strip_ours(text, old, k)
            q.write_text(new, encoding="utf-8")
            shutil.copymode(p, q)
            (rep["modified"] if bp.is_file() else rep["added"]).append(rel)
            rep["comments_removed"] += n
            rep["skipped_mixed"] += [f"{rel}:{a}-{b2}: {t}" for a, b2, t in sk]
        if BUILDS[b] == "node/gem5-recon":
            rep["base_local_edit_stripped"] = []
            for rel, (old_s, new_s) in BASE_LOCAL_COMMENTS.items():
                q = dst / rel
                t = q.read_text(encoding="utf-8")
                assert t.count(old_s) == 1, (b, rel)
                q.write_text(t.replace(old_s, new_s), encoding="utf-8")
                rep["base_local_edit_stripped"].append(rel); rep["comments_removed"] += 1
        node_files = {str(p.relative_to(node)) for p in node.rglob("*") if p.is_file()}
        rep["deleted"] = sorted(f for f in base_files - node_files if include(f))
        (stg / f"report_{b}.json").write_text(json.dumps(rep, indent=1))
        print(b, "copied", rep["copied"], "modified", len(rep["modified"]), "added", len(rep["added"]),
              "comments_removed", rep["comments_removed"], "mixed", len(rep["skipped_mixed"]), "deleted", len(rep["deleted"]),
              "new_binary", len(rep["new_binary"]), "new_noncode", len(rep["new_noncode"]), flush=True)


if __name__ == "__main__":
    main()

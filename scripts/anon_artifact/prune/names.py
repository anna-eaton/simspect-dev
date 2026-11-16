"""names.py -- crude static check after pruning: global names a module reads but never defines/imports
(likely a removed helper still referenced), and module-level / nested defs never referenced (dead after pruning)."""
import ast, builtins, sys, symtable


def check(path):
    src = open(path).read()
    tree = ast.parse(src)
    defined = set(dir(builtins))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                defined.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            defined.add(n.id)
        elif isinstance(n, ast.arg):
            defined.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            defined.add(n.name)
    undefined = sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)} - defined)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    strs = " ".join(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str))
    unref = sorted(n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                   and n.name not in used and n.name not in strs and not n.name.startswith("__"))
    return undefined, unref


if __name__ == "__main__":
    for p in sys.argv[1:]:
        u, d = check(p)
        print(p, "UNDEFINED:", u, "UNREFERENCED defs:", d)


def unused_locals(path):
    tree = ast.parse(open(path).read())
    out = []
    for f in ast.walk(tree):
        if not isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        stores, loads = {}, set()
        for n in ast.walk(f):
            if isinstance(n, ast.Name):
                if isinstance(n.ctx, ast.Store):
                    stores.setdefault(n.id, n.lineno)
                else:
                    loads.add(n.id)
        params = {a.arg for a in f.args.args + f.args.kwonlyargs}
        for name, ln in stores.items():
            if name not in loads and not name.startswith("_") or (name.startswith("_") and name not in loads and name != "_"):
                if name not in loads:
                    out.append((f.name, name, ln))
        for p in params:
            if p not in loads and p not in ("self",):
                out.append((f.name, "PARAM " + p, f.lineno))
    return out

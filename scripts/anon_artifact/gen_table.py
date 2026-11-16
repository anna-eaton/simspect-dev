import json
from pathlib import Path
H = Path(__file__).resolve().parent
r = json.load(open(H / "build_record.json"))
v = json.load(open(H / "verify_results.json"))
DOC = ("drop top-level keys", "drop prose string fields", "substring")
print("| artifact path | source path | why needed (entry point) | transformations |")
print("|---|---|---|---|")
for f in r["files"]:
    t, k = [], f["kind"]
    t += {"py": ["comments + docstrings stripped (tokenize/AST)"], "java": ["comments stripped (string-aware scanner)"],
          "als": ["comments stripped (`//`, `--`, `/* */`)"], "json": ["JSONC→JSON"],
          "json-config": ["JSONC→JSON; machine paths → `@WORK@`/`@GEM5@` (rendered by simspect.py); run configs get gem5.fast_path true"],
          "authored": ["written for the artifact, comment-free"]}.get(k, [])
    for x in f["replacements"]:
        if x[0] == "substring":
            t.append("substring `, SIMSPECT_HOOKS.md` removed from prose values")
        elif x[0] in DOC and x[1]:
            t.append(f"{x[0]}: {', '.join(x[1])}")
    ce = v.get("code_edits", {}).get(f["dst"], [])
    if ce:
        t.append("CODE EDIT: " + "; ".join(f"`{o}` → `{n}`" for o, n in ce))
    nstr = len([x for x in f["replacements"] if x[0] not in DOC]) - len(ce)
    if k == "py" and nstr > 0:
        t.append(f"{nstr} string literal edit(s): paths / help / log text (all listed in scripts/anon_artifact/verify_results.json `string_changes`)")
    if k == "py" and f["dst"] != f["src"]:
        t.append("relocated")
    print(f"| `{f['dst']}` | `{f['src']}` | {f['why']} | {'; '.join(t).replace('|', '/')} |")

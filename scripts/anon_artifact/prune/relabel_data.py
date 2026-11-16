"""relabel_data.py -- apply labels.RENAMES to an existing anonymous-artifact data/ tree in place (E2w bucket labels,
the rerun file name and its signature field). Usage: python3 relabel_data.py <data dir> [<data dir> ...]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import relabel, FIELD_RENAMES

for d in sys.argv[1:]:
    e = Path(d) / "records" / "e2w" / "recon_stt"
    b = e / "buckets.json"
    x = json.loads(b.read_text())
    x["buckets"] = {k: dict(v, buckets={relabel(l): n for l, n in v["buckets"].items()}) for k, v in x["buckets"].items()}
    b.write_text(json.dumps(x, indent=1) + "\n")
    old, new = e / "rsa8_rerun.json", e / "oldest_taint_rerun.json"
    if old.exists():
        r = json.loads(old.read_text())
        for k, v in r.items():
            for a, c in FIELD_RENAMES:
                if a in v:
                    v[c] = v.pop(a)
        new.write_text(json.dumps(r, indent=1) + "\n")
        old.unlink()
    print(d, "relabelled")

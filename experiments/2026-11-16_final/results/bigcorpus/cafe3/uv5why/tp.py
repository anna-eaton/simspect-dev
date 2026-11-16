import json,sys
for v in ("uv5new","uv5sld"):
  for l in open("run_%s/results.jsonl"%v):
    r=json.loads(l); print(v,r["mode"],r["stem"],r["hit"],r["cache_setup"],r["timing_point"],r["stall_points"],r["terms_fired"])

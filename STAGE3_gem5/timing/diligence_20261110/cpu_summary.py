import json, collections, statistics as st
D="/tests/simspect_alloy_20261108/bugwork/diligence/cpu/"
GEN=3.02
# AMuLeT pooled CPU-s per violation and SimSpect expected tests (final table)
AM={"UV1":(270,2.05,"T1g"),"UV3":(105,24.2,"T2g"),"UV4":(6171,81.5,"T2g"),"UV5":(6171,9645,"T2g"),"UV6":(115,4.98,"T3g"),"jmp_shadow":(366,6.74,"T3g")}
per={}
for r in ["T1g","T2g","T3g"]:
    rows=[json.loads(l) for l in open(f"{D}{r}_cpu1000/results.jsonl")]
    t=[x["total_cpu_s"] for x in rows if x.get("total_cpu_s") is not None]; g=[x["gem5_cpu_s"] for x in rows if x.get("gem5_cpu_s") is not None]
    w=[x["wall_s"] for x in rows]
    per[r]=st.mean(t)
    print(r,"N",len(rows),collections.Counter(x["status"] for x in rows),"total CPU/test mean %.3f median %.3f | gem5 %.3f | wall %.3f"%(st.mean(t),st.median(t),st.mean(g),st.mean(w)),
          "by setup",{k:round(st.mean([x["total_cpu_s"] for x in rows if x["cache_setup"]==k]),2) for k in set(x["cache_setup"] for x in rows)})
for b,(acpu,exp,r) in AM.items():
    c=per[r]
    print("%-10s exp %.2f  CPU/test %.2f  SimSpect exp CPU incl gen %.0f  exec-only %.0f  AMuLeT %d  multiple incl gen %.3g  exec-only %.3g"%(b,exp,c,exp*(c+GEN),exp*c,acpu,acpu/(exp*(c+GEN)),acpu/(exp*c)))

# nm-diligence 2026-11-10: copy of diligence cpu_summary.py (EVAL_MANIFEST part 8 check 6) for the NON-MINIMAL corpus.
# Changed only: D (nm_diligence/cpu), GEN (1.84 CPU-s/test, nonmin PROVENANCE), SimSpect expected tests from the nonmin
# complete run ((N+1)/(K+1): UV1 1,982/4,000, UV3 1,659/52,940, UV4 383/52,940, UV5 6/52,940, UV6 883/4,000, jmp 606/4,000).
# AMuLeT pooled CPU-s per violation unchanged from cpu_summary.py.
import json, collections, statistics as st
D="/tests/simspect_alloy_20261108/bugwork/nm_diligence/cpu/"
GEN=1.84
E=lambda n,k:(n+1)/(k+1)
AM={"UV1":(270,E(4000,1982),"T1g"),"UV3":(105,E(52940,1659),"T2g"),"UV4":(6171,E(52940,383),"T2g"),"UV5":(6171,E(52940,6),"T2g"),"UV6":(115,E(4000,883),"T3g"),"jmp_shadow":(366,E(4000,606),"T3g")}
per={}
for r in ["T1g","T2g","T3g"]:
    rows=[json.loads(l) for l in open(f"{D}{r}_cpu1000/results.jsonl")]
    t=[x["total_cpu_s"] for x in rows if x.get("total_cpu_s") is not None]; g=[x["gem5_cpu_s"] for x in rows if x.get("gem5_cpu_s") is not None]
    w=[x["wall_s"] for x in rows]
    per[r]=st.mean(t)
    print(r,"N",len(rows),dict(collections.Counter(x["status"] for x in rows)),"total CPU/test mean %.3f median %.3f | gem5 %.3f | wall %.3f"%(st.mean(t),st.median(t),st.mean(g),st.mean(w)),
          "by setup",{k:round(st.mean([x["total_cpu_s"] for x in rows if x["cache_setup"]==k]),2) for k in sorted(set(x["cache_setup"] for x in rows))})
for b,(acpu,exp,r) in AM.items():
    c=per[r]
    print("%-10s exp %.2f  CPU/test %.2f  SimSpect exp CPU incl gen %.0f  exec-only %.0f  AMuLeT %d  multiple incl gen %.3g  exec-only %.3g"%(b,exp,c,exp*(c+GEN),exp*c,acpu,acpu/(exp*(c+GEN)),acpu/(exp*c)))

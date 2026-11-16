#!/usr/bin/env bash
# rsa8_node.sh (agent inttwin 2026-11-16) -- UV3 confirmation for the branch-shadow ReCon rows, both versions, as done for the paper's E2w
# number (EVAL_MANIFEST E2w: 22 of 24 candidates carry the signature): scripts/inttwin_20261116/rsa8_trace_cs.py (= rsa8_trace.py + the
# resolved xmit_pc, needed for non-warm cache setups; reuses existing reruns), one
# faithful rerun per 'R-SA-8 candidate' record with the row's own inttwin config + debug flags Commit,DelayUnit,Rename.
# Waits for cls/<row>/DONE. Not for E2wstl (R-SA-8's signature is branch-shadow specific; store shadows were triaged with oldest_taint_replay).
# Run inside gem5_dev from /tests/inttwin_20261116/code:  bash scripts/inttwin_20261116/rsa8_node.sh <row> [<row> ...]
# Out: cls/<row>/rsa8_keys_<ver>.txt, rsa8_<ver>.json, rsa8_<ver>.stdout; work dirs /tests/inttwin_20261116/rsa8work/<row>_<ver>/ ; log logs/rsa8.log
O=/tests/inttwin_20261116; cd $O/code; export TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 SIMSPECT_GEM5_MAX_TICK=2000000000
L=$O/logs/rsa8.log; log(){ echo "[$(date -u '+%F %T')] $*" >> $L; }
for R in "$@"; do
  D=$O/cls/$R; until [ -f $D/DONE ]; do sleep 120; done
  for V in fpr int; do
    python3 - $D/per_stem_$V.json $D/rsa8_keys_$V.txt <<'PY'
import json, sys
ps = json.load(open(sys.argv[1])); ks = sorted({"/".join([k.split("/")[0], k.split("/")[-1]]) for k, l in ps.items() if l.startswith("R-SA-8 candidate")})
open(sys.argv[2], "w").write("".join(k + "\n" for k in ks)); print(len(ks))
PY
    M=$(python3 -c "import json;print([c['model'] for c in json.load(open('runconfigs/inttwin_20261116/campaigns.json')) if c['row']=='$R' and c['version']=='$V'][0])")
    CF=$(python3 -c "import json;print([c['config'] for c in json.load(open('runconfigs/inttwin_20261116/campaigns.json')) if c['row']=='$R' and c['version']=='$V'][0])")
    log "START $R $V keys=$(wc -l < $D/rsa8_keys_$V.txt) model=$M"
    rm -f $D/rsa8_$V.json; nice -n 5 python3 scripts/inttwin_20261116/rsa8_trace_cs.py --config $CF --testset-dirs $O/testsets/$M \
      --keys $D/rsa8_keys_$V.txt --out $D/rsa8_$V.json --par 8 --work $O/rsa8work/${R}_$V > $D/rsa8_$V.stdout 2>&1
    log "END $R $V rc=$? $(tail -n 1 $D/rsa8_$V.stdout)"
    # x86 mov false-dependency share (as for E2w): static movmerge_check on the same candidate keys
    nice -n 5 python3 scripts/bigcorpus_20261115/movmerge_check.py --testset $O/testsets/$M --keys $D/rsa8_keys_$V.txt --out $D/movmerge_$V.json > $D/movmerge_$V.stdout 2>&1
    log "movmerge $R $V rc=$?"
  done
done
log "ALL DONE $*"

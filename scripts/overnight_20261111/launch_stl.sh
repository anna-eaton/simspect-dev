#!/usr/bin/env bash
# launch_stl.sh -- X4 of the overnight plan (stl-prep 2026-11-12): STL corpora (STL = the speculation primitive) as their OWN run,
# AFTER corpus A's gem5 rows (Anna 2026-11-11: "do them in their own run like afterwards"). Run FROM THE MAC, one command per node:
#   gen:   scripts/overnight_20261111/launch_stl.sh cafe3 STT_6_u_stl      scripts/overnight_20261111/launch_stl.sh cafe1 Recon_6_u_stl
#   score: scripts/overnight_20261111/launch_stl.sh cafe2 STT_6_u_stl score cafe3   (/work/gem5-recon-stl exists ONLY on cafe2;
#          refuses until <gen node>:<OUT>/testsets/<F>_core_lpP_stlA/READY exists; streams the corpus + STAGE3_gem5 + stl_score.py to cafe2)
# Needs launch_alloy.sh to have made the node snapshot <OUT>/code (X2a). Steps (idempotent):
#  1. disk check; install IN THE NODE SNAPSHOT ONLY (never the repo; DECIDE 'approve ..._stl_lpPc'): models/<F>_core_ri.als from
#     proposed/ultimate/, models/<F>_lpP.als = provenance header + loosepin/<F>_lpPc.als; refresh twostage_lp.py, stream_fp.py,
#     stl_final_A.jsonc, twostage_<F>.jsonc, stl_score.py in the snapshot (only these files).
#  2. copy cafe2 /tests/simspect_alloy_20261109u/out/<F>_core_ri/k3 -> <OUT>/cores/ (once).
#  3. tmux ovn_stl window <F> (node side): WAIT until every corpus-A gem5 row on this node logged `EXIT ...s2A.jsonc` in
#     <OUT>/logs/gem5_<row>.out (rows from campaigns_overnight.json; NOWAIT=1 skips), then twostage_lp.py (Stage 1.5 + streamed Stage 2,
#     stl_bypass, corpus <OUT>/testsets/<F>_core_lpP_stlA), then score on /work/gem5-recon-stl with stl_score.py (DRAFT: no STL
#     window checker; stale build without the 2026-10-30 resolve hooks) for schemes 2 (STT), 0 (Unsafe control), 1 (NDA), at
#     FRAC (default 1.0) of the corpus. DoM (3) not run (needs the cold-cache/miss criterion DECIDE).
# Logs: <OUT>/logs/stl_<F>.out, <OUT>/ws_<F>/logs/, <OUT>/results_stl/<F>/logs/*.log, ~/Library/Logs/simspect/overnight_stl_<node>.log.
# A node-side disk guard stops the window's work when /scr free < MIN_FREE_GB/2 (launch_alloy's diskwatch also covers ws_*).
set -euo pipefail
NODE=${1:?node}; F=${2:?family}; MODE=${3:-gen}; GEN=${4:-}
case "$F" in STT_6_u_stl|Recon_6_u_stl) ;; *) echo "family must be STT_6_u_stl or Recon_6_u_stl"; exit 1;; esac
REPO=$(cd "$(dirname "$0")/../.." && pwd); O=${OUT:-/tests/overnight_20261111}; MIN=${MIN_FREE_GB:-80}; FRAC=${FRAC:-1.0}; D=runconfigs/overnight_20261111
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/overnight_stl_${NODE}.log
log(){ echo "$(date -u '+%F %T') [$NODE] $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
log "START $F out=$O frac=$FRAC"
free=$($SSH "$NODE" "df -BG --output=avail /scr | tail -1 | tr -dc 0-9"); log "disk /scr free ${free}G (min $MIN)"
[ "$free" -ge "$MIN" ] || { log "ABORT: /scr free ${free}G < ${MIN}G"; exit 1; }
H=$((MIN / 2)); R=$O/results_stl/$F; T=$O/testsets/${F}_core_lpP_stlA
if [ "$MODE" = score ]; then
  [ -n "$GEN" ] || { log "ABORT: score needs the gen node as 4th arg"; exit 1; }
  rx "test -x /work/gem5-recon-stl/build/X86/gem5.opt" || { log "ABORT: /work/gem5-recon-stl missing on $NODE"; exit 1; }
  G(){ $SSH "$GEN" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
  G "test -f $T/READY" || { log "ABORT: $GEN:$T/READY missing (Stage 1b/2 not finished)"; exit 2; }
  if rx "tmux list-windows -t ovn_stl -F '#W' 2>/dev/null | grep -qx score_$F"; then log "skip score_$F (window exists)"; exit 0; fi
  COPYFILE_DISABLE=1 tar -C "$REPO" --exclude='*/__pycache__' -czf - STAGE3_gem5 scripts/overnight_20261111/stl_score.py | rx "mkdir -p $O/code $O/logs && tar -xzf - -C $O/code"
  rx "test -f $T/READY" || { G "tar -C $O/testsets -cf - ${F}_core_lpP_stlA" | rx "mkdir -p $O/testsets && tar -xf - -C $O/testsets"; }
  log "corpus on $NODE: $(rx "ls $T/stl_bypass/asm | grep -c '\.s\$'") .s"
  SB="L=$O/logs/stl_score_$F.out; echo START \$(date -u) >> \$L; mkdir -p $R/logs; cd $O/code && export TMPDIR=/tmp \
SIMSPECT_GEM5_BIN=/work/gem5-recon-stl/build/X86/gem5.opt SIMSPECT_SE_CONFIG=/work/gem5-recon-stl/configs/example/se.py SIMSPECT_GEM5_CPU=X86O3CPU \
SIMSPECT_BRANCH_ANN_ENABLE=1 SIMSPECT_FNC_COMMIT_STALL_CYCLES=150 SIMSPECT_STL_ANN_ENABLE=1 SIMSPECT_STL_STORE_STALL_CYCLES=5000 SIMSPECT_STL_ALIAS_PRED=no_alias LC_ALL=C.UTF-8; \
for s in 2:E2_stt_s2 0:E1_unsafe_s0 1:E8_nda_s1; do f=\$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); [ \"\$f\" -ge $H ] || { echo \"DISK STOP \${f}G\" >> \$L; exit 1; }; \
python3 -u scripts/overnight_20261111/stl_score.py $T/stl_bypass \${s%%:*} $R/\${s#*:}.json $FRAC ${JOBS:-12} >> $R/logs/\${s#*:}.log 2>&1; echo \"score \${s#*:} rc=\$? \$(date -u)\" >> \$L; done; echo END \$(date -u) >> \$L"
  rx "tmux has-session -t ovn_stl 2>/dev/null || tmux new-session -d -s ovn_stl -n ctl"
  rx "tmux new-window -d -t ovn_stl -n score_$F $(printf %q "bash -c $(printf %q "$SB")")"
  log "LAUNCHED score_$F on $NODE (DRAFT stl_score.py, schemes 2/0/1, frac $FRAC) -> $R"; exit 0
fi
rx "test -f $O/code/SNAPSHOT.txt" || { log "ABORT: no node snapshot $O/code (run launch_alloy.sh first)"; exit 1; }
if rx "tmux list-windows -t ovn_stl -F '#W' 2>/dev/null | grep -qx $F"; then log "skip $F (window exists)"; exit 0; fi
U=STAGE1_alloy/models/proposed/ultimate; LP=$U/loosepin
COPYFILE_DISABLE=1 tar -C "$REPO" -czf - twostage_lp.py $LP/stream_fp.py $LP/${F}_lpPc.als $U/${F}_core_ri.als $D/stl_final_A.jsonc \
  $D/twostage_$F.jsonc scripts/overnight_20261111/stl_score.py | rx "tar -xzf - -C $O/code"
rx "cd $O/code/STAGE1_alloy/models && cp proposed/ultimate/${F}_core_ri.als ${F}_core_ri.als && \
    { printf '%s\n' '// NOT APPROVED (stl-prep 2026-11-12): installed in this node snapshot only, from proposed/ultimate/loosepin/${F}_lpPc.als (make_loosepin.py --base ${F}.als --n 8 --operands 16 --intbits 6 --minimality prod --committed required --brcap 0 --pin core; defense block byte-identical).' \
      '// Pending DECIDE in URGENT_TODO.md: approve ${F}_lpPc.' '// ============================================================================='; cat proposed/ultimate/loosepin/${F}_lpPc.als; } > ${F}_lpP.als"
( cd "$REPO" && echo "stl refresh $(date -u '+%F %T') UTC (Mac HEAD $(git rev-parse --short HEAD) + working tree)" && shasum -a 256 twostage_lp.py $LP/stream_fp.py $LP/${F}_lpPc.als $U/${F}_core_ri.als $D/stl_final_A.jsonc $D/twostage_$F.jsonc ) | rx "cat >> $O/code/SNAPSHOT.txt"
log "snapshot: STL models + tooling installed"
if rx "test -f $O/cores/${F}_core_ri/COPIED"; then log "cores present"; else
  $SSH cafe2 "docker exec gem5_dev tar -C /tests/simspect_alloy_20261109u/out -cf - ${F}_core_ri/k3" | rx "mkdir -p $O/cores && tar -xf - -C $O/cores"
  n=$(rx "ls $O/cores/${F}_core_ri/k3/stage1_xml | grep -c '^inst-.*\.xml$'")
  rx "echo copied $(date -u '+%F %T') from cafe2:/tests/simspect_alloy_20261109u/out/${F}_core_ri/k3, $n core xml > $O/cores/${F}_core_ri/COPIED"
  log "cores copied: $n (expect 858)"
fi
ROWS=$(cd "$REPO" && python3 -c "import json;print(' '.join(sorted({x['row'] for x in json.load(open('$D/campaigns_overnight.json')) if x['node']=='$NODE' and x['recipe']=='A'})))")
[ "${NOWAIT:-0}" = 1 ] && ROWS=""
log "will wait for corpus-A gem5 rows on $NODE: [${ROWS}]"
BODY="L=$O/logs/stl_$F.out; echo START \$(date -u) >> \$L; for r in $ROWS; do until grep -q 'EXIT .*s2A.jsonc' $O/logs/gem5_\$r.out 2>/dev/null || grep -q \"ROW \$r DONE\" $O/logs/gem5_\$r.out 2>/dev/null; do sleep 600; done; echo \"row \$r corpus A done \$(date -u)\" >> \$L; done; \
guard(){ f=\$(df -BG --output=avail /tests | tail -1 | tr -dc 0-9); [ \"\$f\" -ge $H ] || { echo \"DISK STOP free \${f}G < ${H}G \$(date -u)\" >> \$L; exit 1; }; }; guard; \
cd $O/code && export TMPDIR=/tmp && python3 -u twostage_lp.py --config $D/twostage_$F.jsonc --ws $O/ws_$F >> \$L 2>&1; echo \"twostage rc=\$? \$(date -u)\" >> \$L; \
test -f $T/READY && echo \"READY \$(date -u); now run: launch_stl.sh cafe2 $F score $NODE\" >> \$L; echo END \$(date -u) >> \$L"
rx "mkdir -p $O/logs && tmux has-session -t ovn_stl 2>/dev/null || tmux new-session -d -s ovn_stl -n ctl"
rx "tmux new-window -d -t ovn_stl -n $F $(printf %q "bash -c $(printf %q "$BODY")")"
log "LAUNCHED $F (waits for rows [${ROWS}], then Stage 1b/2 -> $T; score later on cafe2)"

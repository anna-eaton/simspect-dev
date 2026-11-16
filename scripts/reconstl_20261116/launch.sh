#!/usr/bin/env bash
# launch.sh -- reconstl (simspect-c8, 2026-11-16). ReCon stl-flavor corpus Recon_6_u_stl_core_lpP_s2A on cafe1. Run FROM THE MAC, once.
# Anna 2026-11-16: approved changing only the ReCon execution-contract selector (spectre -> + stl); steps 2-3 only (no gem5: the
# store-shadow scoring blocker is her DECIDE). Two unattended jobs in tmux session `reconstl` (gem5_dev on cafe1), both nice 19:
#   s1   Stage 1a rerun of the ONE unfinished partition Recon_6_u_stl_core_ri__k6_Branchxs (DISK_GUARD 2026-11-09; k6_Loads EXHAUSTED),
#        exact production Stage 1a code copied from cafe2 /tests/simspect_alloy_20261109u (= cafe3 k6rerun's copy: run_stage1.py 2b4eb4c5,
#        alloy6.jar 6b8c1cb5, a6CountModels.class 0936b86a), cap 200000, Xmx8g, poll 60, run_stage1's disk guard (start >= 100 GB,
#        stop < 80 GB), wall budget 30 h (108000 s), same as k6rerun.
#   s15  twostage_lp.py with runconfigs/reconstl_20261116/twostage_Recon_6_u_stl.jsonc: Stage 1.5 on the 858 reused k3 cores + Stage 2
#        streamed (recipe A in stl_bypass mode) into /tests/reconstl_20261116/testsets/Recon_6_u_stl_core_lpP_s2A, via run_s15.sh
#        (disk guard: refuses to start below 60 GB free; kills the run if free < 40 GB).
# Code = copy of cafe1 /tests/bigcorpus_20261115/code (the snapshot that built the reported s2A corpora) + the stl models/configs only.
# Logs (node): W/logs/{setup,s1_driver,s15,diskwatch}.log, W/logs/Recon_6_u_stl_core_ri__k6_Branchxs.log (run_stage1), W/ws/logs/.
# Mac log: ~/Library/Logs/simspect/reconstl_launch.log
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd); NODE=cafe1; W=/tests/reconstl_20261116; SRCN=cafe2; S1SRC=/tests/simspect_alloy_20261109u
mkdir -p ~/Library/Logs/simspect; LOG=~/Library/Logs/simspect/reconstl_launch.log
log(){ echo "$(date -u '+%F %T') $*" | tee -a "$LOG"; }
trap 'log "ERROR line $LINENO (exit $?)"' ERR
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
rx(){ $SSH "$NODE" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
sx(){ $SSH "$SRCN" "docker exec -i gem5_dev bash -lc $(printf %q "$1")"; }
log "START reconstl launch"
free=$(rx "df -BG --output=avail /tests | tail -1 | tr -dc 0-9"); log "cafe1 /tests free ${free}G"
[ "$free" -ge 100 ] || { log "ABORT: cafe1 /tests free ${free}G < 100G"; exit 1; }
rx "test -e $W" && { log "ABORT: $W exists (already launched?)"; exit 1; }
rx "mkdir -p $W/logs $W/cores $W/stage1 && cp -a /tests/bigcorpus_20261115/code $W/code"
U=STAGE1_alloy/models/proposed/ultimate
COPYFILE_DISABLE=1 tar -C "$REPO" -czf - $U/Recon_6_u_stl_core_ri.als $U/loosepin/Recon_6_u_stl_lpP.als $U/loosepin/Recon_6_u_stl_lpPc.als \
  runconfigs/reconstl_20261116 scripts/reconstl_20261116 | rx "tar -xzf - -C $W/code"
rx "cd $W/code/STAGE1_alloy/models && cp $W/code/$U/Recon_6_u_stl_core_ri.als Recon_6_u_stl_core_ri.als && cp $W/code/$U/loosepin/Recon_6_u_stl_lpP.als Recon_6_u_stl_lpP.als"
sx "tar -C $S1SRC/out -cf - Recon_6_u_stl_core_ri/k3" | rx "tar -xf - -C $W/cores"
sx "tar -C $S1SRC -cf - STAGE1_alloy/alloy6.jar STAGE1_alloy/a6CountModels.class STAGE1_alloy/models/proposed_twophase/run_stage1.py parts/Recon_6_u_stl_core_ri" \
  | rx "tar -xf - -C $W/stage1"
rx "cd $W && { echo \"setup \$(date -u +%FT%TZ) from Mac $(hostname -s) (HEAD $(git -C "$REPO" rev-parse --short HEAD) + working tree)\"; \
  echo \"cores k3 xml: \$(ls cores/Recon_6_u_stl_core_ri/k3/stage1_xml | grep -c '^inst-.*\\.xml\$')\"; \
  sha256sum code/STAGE1_alloy/models/Recon_6_u_stl_core_ri.als code/STAGE1_alloy/models/Recon_6_u_stl_lpP.als code/STAGE1_alloy/models/Recon_6_u_lpP.als \
    code/twostage_lp.py code/STAGE2_compilation/parsexml.py code/runconfigs/reconstl_20261116/*.jsonc \
    stage1/STAGE1_alloy/alloy6.jar stage1/STAGE1_alloy/a6CountModels.class stage1/STAGE1_alloy/models/proposed_twophase/run_stage1.py \
    stage1/parts/Recon_6_u_stl_core_ri/Recon_6_u_stl_core_ri__k6_Branchxs.als; } > logs/setup.log"
log "setup done: $(rx "cat $W/logs/setup.log | head -2 | tr '\n' ' '")"
S1="cd $W/stage1 && N=Recon_6_u_stl_core_ri__k6_Branchxs && echo \"\$(date -u +%FT%TZ) START s1 host=\$(hostname)\" >> $W/logs/s1_driver.log && \
nice -n 19 python3 -u STAGE1_alloy/models/proposed_twophase/run_stage1.py --name \$N --model $W/stage1/parts/Recon_6_u_stl_core_ri/\$N.als \
 --out $W/stage1/out/Recon_6_u_stl_core_ri/k6_Branchxs/stage1_xml --log $W/logs/\$N.log --cap 200000 --timeout 108000 --xmx 8g --poll 60 \
 --min-free-start 100 --min-free-run 80 > $W/logs/\$N.stdout 2> $W/logs/\$N.stderr; echo \"\$(date -u +%FT%TZ) END s1 rc=\$? \$(grep -h VERDICT $W/logs/\$N.log | tail -1)\" >> $W/logs/s1_driver.log"
rx "tmux new-session -d -s reconstl -n s1 $(printf %q "bash -c $(printf %q "$S1")")"
# s15: the inline bash body first used here died silently at launch (2026-11-16 11:47Z, quoting); replaced by run_s15.sh (same steps), started 11:47:59Z.
cat "$REPO/scripts/reconstl_20261116/run_s15.sh" | $SSH "$NODE" "docker exec -i gem5_dev bash -c 'cat > $W/run_s15.sh; chmod +x $W/run_s15.sh; tmux new-window -d -t reconstl -n s15 \"bash $W/run_s15.sh; sleep 86400\"'"
log "LAUNCHED tmux reconstl (s1, s15) on $NODE in $W"

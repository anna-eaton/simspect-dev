#!/usr/bin/env bash
# stop_stt_recon.sh -- stop every STT_6_u / Recon_6_u piece of the big-corpus run on cafe3, keep all outputs (agent bigcorpus, 2026-11-15).
# Anna 2026-11-15: "just run the amulet stuff dont do spt stt recon rn bc we've hit those before."
# Run INSIDE cafe3 gem5_dev, fed on stdin (so this script's own command line matches none of the patterns):
#   ssh cafe3 'docker exec -i gem5_dev bash -s' < scripts/bigcorpus_20261115/stop_stt_recon.sh
# Kills only processes this run launched: roots matched by bigcorpus-specific paths, then each root's whole descendant tree.
# Footprint_6_u (ws_Footprint_6_u, Footprint corpora, T*g firstdet rows) is not matched. Writes STOPPED.txt next to every stopped output.
O=/tests/bigcorpus_20261115
WHY="STOPPED $(date -u '+%F %T') UTC by agent bigcorpus. Anna 2026-11-15: \"just run the amulet stuff dont do spt stt recon rn bc we've hit those before.\" Outputs kept as they were at the stop (partial)."
PATS=("$O/ws_STT_6_u" "$O/ws_Recon_6_u" "runconfigs/bigcorpus_20261115/E2_" "runconfigs/bigcorpus_20261115/E3_" "runconfigs/bigcorpus_20261115/E4_"
      "runconfigs/bigcorpus_20261115/E6_" "runconfigs/bigcorpus_20261115/race_" "$O/code/results/bc_E" "$O/code/results/bc_race" "results/bc_E" "results/bc_race")
desc(){ local p=$1; echo $p; for c in $(ps -o pid= --ppid $p); do desc $c; done; }
roots=$(for pat in "${PATS[@]}"; do pgrep -f -- "$pat"; done | sort -u | grep -vx "$$")
echo "roots: $(echo $roots | wc -w)"
all=$(for r in $roots; do desc $r; done | sort -u | grep -vx "$$")
echo "processes to stop: $(echo $all | wc -w)"
ps -o pid=,args= -p $(echo $all | tr ' ' ',') 2>/dev/null | cut -c1-150 | awk '{print}' | head -12
for s in bc_alloy:STT_6_u bc_alloy:Recon_6_u bc_s2:STT_6_u bc_s2:Recon_6_u bc_gem5:E2 bc_gem5:E3 bc_gem5:E4 bc_gem5:race_stt_d1 bc_gem5:race_stt_d3 \
         bc_gem5:race_stt_d4 bc_gem5:race_sttmaster_d1 bc_gem5:race_sttmaster_d3 bc_gem5:race_sttmaster_d4; do tmux kill-window -t "$s" 2>/dev/null && echo "killed window $s"; done
[ -n "$all" ] && kill -TERM $all 2>/dev/null; sleep 5
left=$(for p in $all; do [ -d /proc/$p ] && echo $p; done); [ -n "$left" ] && { echo "SIGKILL $(echo $left | wc -w) leftovers"; kill -KILL $left 2>/dev/null; }
for d in $O/ws_STT_6_u $O/ws_Recon_6_u $O/testsets/STT_6_u_core_lpP_s2A $O/testsets/STT_6_u_lp_s2A_base $O/testsets/Recon_6_u_core_lpP_s2A \
         $O/testsets/Recon_6_u_lp_s2A_base $O/cores/STT_6_u_core_ri $O/cores/Recon_6_u_core_ri $(ls -d $O/code/results/bc_E* $O/code/results/bc_race* 2>/dev/null | grep -v __latest); do
  [ -d "$d" ] && echo "$WHY" > "$d/STOPPED.txt" && echo "STOPPED.txt -> $d"
done
echo "$WHY (STT_6_u / Recon_6_u Alloy, Stage 2, gem5 rows E2/E3/E4, six STT race rows)" >> $O/logs/STOPPED_stt_recon.txt
echo "remaining bc_ windows:"; for s in bc_alloy bc_s2 bc_gem5; do echo "$s: $(tmux list-windows -t $s -F '#W' 2>/dev/null | tr '\n' ' ')"; done
echo "still matching: $(for pat in "${PATS[@]}"; do pgrep -f -- "$pat"; done | sort -u | grep -vx "$$" | wc -l)"

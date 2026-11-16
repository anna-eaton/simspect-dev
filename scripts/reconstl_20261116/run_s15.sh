#!/bin/bash
# run_s15.sh -- reconstl 2026-11-16: Stage 1.5 + streamed Stage 2 (recipe A, stl_bypass) for Recon_6_u_stl_core_lpP_s2A, nice 19.
# Disk guard: refuse below 60 GB free on /tests; watcher kills the run if free < 40 GB. Logs: logs/s15.log, logs/diskwatch.log, ws/logs/.
W=/tests/reconstl_20261116; L=$W/logs/s15.log; T=$W/testsets/Recon_6_u_stl_core_lpP_s2A
ts(){ date -u +%FT%TZ; }
freeg(){ df -BG --output=avail /tests | tail -1 | tr -dc 0-9; }
cd $W/code || { echo "$(ts) no code dir" >> $L; exit 1; }
export TMPDIR=/tmp
echo "$(ts) START s15 pid=$$ free=$(freeg)G" >> $L
f=$(freeg); if [ "$f" -lt 60 ]; then echo "$(ts) ABORT free ${f}G < 60G" >> $L; exit 1; fi
nice -n 19 python3 -u twostage_lp.py --config runconfigs/reconstl_20261116/twostage_Recon_6_u_stl.jsonc --ws $W/ws >> $L 2>&1 &
P=$!; echo "$(ts) twostage pid=$P" >> $L
while kill -0 $P 2>/dev/null; do
  sleep 600
  f=$(freeg); x=$(find $W/ws/runs15 -name '*.xml' 2>/dev/null | wc -l); a=$(find $T -name '*.s' 2>/dev/null | wc -l)
  echo "$(ts) free_GB=$f s15_xml=$x stage2_s=$a" >> $W/logs/diskwatch.log
  if [ "$f" -lt 40 ]; then echo "$(ts) DISK STOP free ${f}G < 40G: killing twostage tree" | tee -a $W/logs/diskwatch.log >> $L; pkill -TERM -P $P; kill $P; break; fi
done
wait $P; echo "$(ts) END s15 twostage rc=$? stage2_s=$(find $T -name '*.s' 2>/dev/null | wc -l)" >> $L

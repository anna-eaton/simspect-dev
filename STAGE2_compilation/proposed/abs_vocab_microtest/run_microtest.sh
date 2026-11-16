#!/bin/bash
# abs-vocab (2026-11-12): build microtest.s and run it natively + on every gem5 build on this node.
# Run inside the gem5_dev container. Usage: run_microtest.sh <workdir>. Logs to <workdir>/validate.log.
set -u
export LC_ALL=C.UTF-8 LANG=C.UTF-8   # gem5-recon-modded main.py decodes the config as text (ascii crash otherwise)
W=${1:?workdir}; cd "$W" || exit 2
LOG="$W/validate.log"
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
log "START microtest (host $(hostname))"
as -o microtest.o microtest.s && ld -static -o microtest microtest.o || { log "BUILD FAILED"; exit 3; }
out=$(./microtest); rc=$?; log "native: rc=$rc out=$out"
COMMON_RUBY="--num-cpu=1 --cpu-clock=2GHz --sys-clock=2GHz --ruby --L1_TBEs=256 --L2_TBEs=256 --DC_TBEs=256 --l1d_size=32kB --l1d_assoc=8 --l1i_size=32kB --cacheline_size=64 --l2_size=2MB --l2_assoc=8 --DTB_entries=64"
declare -A BIN CFG ARGS
BIN[stt-master]=/work/stt-master/build/X86/gem5.opt;          ARGS[stt-master]="--cpu-type=DerivO3CPU --caches --scheme=2"
BIN[stt]=/work/stt/build/X86/gem5.opt;                        ARGS[stt]="--cpu-type=DerivO3CPU --caches --scheme=2"
BIN[recon-modded]=/work/gem5-recon-modded/build/X86/gem5.opt; ARGS[recon-modded]="--cpu-type=X86O3CPU --caches --scheme=2"
BIN[amulet-stt]=/work/amulet/amulet-gem5-STT_AE-v1.1/build/X86/gem5.opt; ARGS[amulet-stt]="--cpu-type=DerivO3CPU --caches --scheme=2 $COMMON_RUBY --needsTSO=1 --STT=1 --implicit_channel=1 --threat_model=Futuristic --access-backing-store"
BIN[invisispec]=/work/amulet/amulet-gem5-InvisiSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt; ARGS[invisispec]="--cpu-type=DerivO3CPU --caches --scheme=2 $COMMON_RUBY --l1i_assoc=8 --needsTSO=0 --scheme=FuturisticSafeInvisibleSpec --access-backing-store"
BIN[cleanupspec]=/work/amulet/amulet-gem5-CleanupSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt; ARGS[cleanupspec]="--cpu-type=DerivO3CPU --caches --scheme=2 $COMMON_RUBY --l1i_assoc=2 --needsTSO=0 --scheme_invisispec=UnsafeBaseline --scheme_cleanupcache=Cleanup_FOR_L1L2 --access-backing-store"
BIN[speclfb]=/work/amulet/amulet-gem5-SpecLFB_AE-v1.1/build/X86/gem5.opt; ARGS[speclfb]="--cpu-type=DerivO3CPU --caches --scheme=2 --num-cpu=1 --cpu-clock=2GHz --sys-clock=2GHz --l2cache --l1d_size=32kB --l1d_assoc=8 --l1i_size=32kB --l1i_assoc=2 --cacheline_size=64 --l2_size=2MB --l2_assoc=8 --DTB_entries=64 --bp-type=BiModeBP --scheme=Speclfb"
BIN[spt]=/work/gem5-spt/build/X86_MESI_Two_Level/gem5.opt;    ARGS[spt]="--cpu-type=DerivO3CPU --caches --scheme=2"
BIN[recon-ruby3]=/work/gem5-recon-ruby3/build/X86/gem5.opt;   ARGS[recon-ruby3]="--cpu-type=X86O3CPU --caches --scheme=2"
for b in stt-master stt recon-modded amulet-stt invisispec cleanupspec speclfb spt recon-ruby3; do
  bin=${BIN[$b]}
  if [ ! -x "$bin" ]; then log "$b: SKIP (no build at $bin on this node)"; continue; fi
  cfg=$(dirname $(dirname $(dirname "$bin")))/configs/example/se.py
  od="$W/m5out_$b"; rm -rf "$od"
  timeout 600 "$bin" --outdir="$od" "$cfg" --cmd="$W/microtest" ${ARGS[$b]} > "$W/gem5_$b.out" 2>&1; rc=$?
  ok=$(grep -c "ABSVOCAB OK" "$W/gem5_$b.out"); bad=$(grep -ciE "unimplemented|unrecognized|illegal|warn: .*instruction|panic|fatal|ABSVOCAB FAIL" "$W/gem5_$b.out")
  exitline=$(grep -m1 "Exiting @" "$W/gem5_$b.out")
  log "$b: rc=$rc ok_lines=$ok suspicious_lines=$bad | $exitline"
  [ "$bad" -gt 0 ] && grep -iE "unimplemented|unrecognized|illegal|warn: .*instruction|panic|fatal|ABSVOCAB FAIL" "$W/gem5_$b.out" | head -5 | sed 's/^/    /' | tee -a "$LOG"
  rm -rf "$od"
done
log "END microtest"

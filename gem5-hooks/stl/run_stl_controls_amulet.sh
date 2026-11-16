#!/bin/bash
# SimSpect-STL port to the AMuLeT builds (2026-11-09, session stl-port): controls (b)
# and the STL-test half of the hooks-off check (a), on the STL binaries built in the
# COPIES /work/amulet/hooks_stl_work/<Build> (the in-place trees are only read, as the
# reference for the equivalence runs).
# Usage (inside gem5_dev on cafe2): run_stl_controls_amulet.sh <InvisiSpec|CleanupSpec|SpecLFB> [limit]
# Sample: the 60 STT_6_stl stl_bypass tests of the 2026-10-30 recon hook test
#   (/tests/simspect/testsets/STT_6_stl/stl_bypass), the same ones as STL_SPECULATION.md "Hook test".
# Output: $W/stlruns/<Build>/<cfg>.json (+ <cfg>.log), traces of the equivalence configs in
#   $W/stlruns/<Build>/keep_<cfg>/ (gzipped), compare_*.json. Driver: stl_hooktest_amulet.py.
# Log: $W/stlruns/<Build>/run.log (start/end, every config's exact env and gem5 flags, rc).
# gem5 flags per defense = the canonical footprint configs (runconfigs/footprint/*.jsonc extra_args);
# the unsafe baseline swaps only the scheme flag for the tree's own baseline choice.
# Hook-test settings as in results/STT_6_stl_hooktest/run_config.jsonc (cafe2): branch_ann_enable
# true, no fnc stall (stl_hooktest.py passes fnc_pc=None), store hold D=5000, warm unless noted.
# Doc: wiki/design/STL_SPECULATION.md "Port to the AMuLeT builds (2026-11-09)".
set -u
b=$1; LIM=${2:-60}
A=/work/amulet; W=${W:-$A/hooks_stl_work}
T=/tests/simspect/testsets/STT_6_stl/stl_bypass
D=$W/stlruns/$b; mkdir -p "$D"
LOG=$D/run.log
DRV=$W/tools/stl_hooktest_amulet.py
export SIMSPECT_HARNESS=$W/harness TMPDIR=/tmp LC_ALL=C.UTF-8
export SIMSPECT_GEM5_CPU=DerivO3CPU SIMSPECT_GEM5_DBG_FLAG=O3PipeView SIMSPECT_BRANCH_ANN_ENABLE=1
export SIMSPECT_FNC_COMMIT_STALL_CYCLES=0
case $b in
  InvisiSpec)
    ISA=build/X86_MESI_Two_Level/gem5.opt
    COMMON="--ruby --needsTSO=1 --allowSpecBuffHit=1 --l1d_size=1kB --l1d_assoc=2 --l1i_size=32kB --l1i_assoc=4 --l2_size=2MB --l2_assoc=16 --L1_TBEs=2 --L2_TBEs=2 --DC_TBEs=2"
    OFF="--scheme=UnsafeBaseline"; ON1="--scheme=SpectreSafeInvisibleSpec"; ON2="--scheme=FuturisticSafeInvisibleSpec"
    ALT=full ;;      # clflush is a no-op on InvisiSpec's Ruby (SIMSPECT_HOOKS.md), so the non-warm setup is full
  CleanupSpec)
    ISA=build/X86_MESI_Two_Level/gem5.opt
    COMMON="--ruby --scheme_invisispec=UnsafeBaseline --needsTSO=0 --l1d_size=2kB --l1d_assoc=4 --l1i_size=32kB --l1i_assoc=4 --l2_size=2MB --l2_assoc=16 --L1_TBEs=8 --L2_TBEs=3 --DC_TBEs=2 --abs-max-tick=3000000000"
    OFF="--scheme_cleanupcache=UnsafeBaseline"; ON1="--scheme_cleanupcache=Cleanup_FOR_L1L2"; ON2=""
    ALT=cold ;;
  SpecLFB)
    ISA=build/X86/gem5.opt
    COMMON="--l2cache --l1d_size=1kB --l1d_assoc=2 --l1i_size=32kB --l1i_assoc=8 --l2_size=2MB --l2_assoc=16"
    OFF="--scheme=unsafebaseline"; ON1="--scheme=Speclfb"; ON2=""
    ALT=cold ;;
  *) echo "unknown build $b"; exit 1 ;;
esac
NEWBIN=$W/$b/$ISA; NEWSE=$W/$b/configs/example/se.py
REFBIN=$A/amulet-gem5-${b}_AE-v1.1/$ISA; REFSE=$A/amulet-gem5-${b}_AE-v1.1/configs/example/se.py

cfg() {  # label bin se scheme_flags stl(0|1) D pred cache [keep]
  local lab=$1 bin=$2 se=$3 sch=$4 stl=$5 d=$6 pred=$7 cache=$8 keep=${9:-}
  export SIMSPECT_GEM5_BIN=$bin SIMSPECT_SE_CONFIG=$se SIMSPECT_CACHE_SETUP=$cache
  export SIMSPECT_STL_ANN_ENABLE=$stl SIMSPECT_STL_STORE_STALL_CYCLES=$d SIMSPECT_STL_ALIAS_PRED=$pred
  export SIMSPECT_GEM5_EXTRA=$(python3 -c "import sys;print('\x1f'.join(sys.argv[1:]))" $COMMON $sch)
  local kopt=""; [ -n "$keep" ] && { rm -rf "$D/keep_$lab"; kopt="--keep-traces $D/keep_$lab"; }
  echo "[$(date -Iseconds)] START $lab bin=$bin se=$se extra='$COMMON $sch' stl=$stl D=$d pred=$pred cache=$cache keep=${keep:-no}" >> "$LOG"
  python3 "$DRV" run "$T" "$D/$lab.json" --limit "$LIM" --jobs 16 --label "$b/$lab" $kopt > "$D/$lab.log" 2>&1
  echo "[$(date -Iseconds)] END $lab rc=$?" >> "$LOG"
}
echo "[$(date -Iseconds)] START run_stl_controls_amulet $b limit=$LIM new=$NEWBIN ($(md5sum < $NEWBIN | cut -c1-32)) ref=$REFBIN ($(md5sum < $REFBIN | cut -c1-32))" >> "$LOG"
# (a) on STL tests: no STL flag, new vs in-place (every line); file + D=0 + off vs in-place (STL lines ignored)
cfg off_new  $NEWBIN $NEWSE "$ON1" 0 0 off warm keep
cfg off_ref  $REFBIN $REFSE "$ON1" 0 0 off warm keep
cfg fileoff_new $NEWBIN $NEWSE "$ON1" 1 0 off warm keep
python3 "$DRV" compare "$D/keep_off_new" "$D/keep_off_ref" --out "$D/compare_off_new_vs_ref.json" > "$D/compare_off_new_vs_ref.log" 2>&1
python3 "$DRV" compare "$D/keep_fileoff_new" "$D/keep_off_ref" --ignore-stl --out "$D/compare_fileoff_new_vs_ref.json" > "$D/compare_fileoff_new_vs_ref.log" 2>&1
# (b) controls, mirroring STL_SPECULATION.md "Hook test" A-F
cfg B_unsafe          $NEWBIN $NEWSE "$OFF" 1 5000 no_alias warm keep
cfg E_unsafe_alias    $NEWBIN $NEWSE "$OFF" 1 5000 alias warm
cfg F_unsafe_hold0    $NEWBIN $NEWSE "$OFF" 1 0 no_alias warm
cfg A_on              $NEWBIN $NEWSE "$ON1" 1 5000 no_alias warm keep
cfg C_on_alias        $NEWBIN $NEWSE "$ON1" 1 5000 alias warm
if [ -n "$ON2" ]; then
  cfg A_on2           $NEWBIN $NEWSE "$ON2" 1 5000 no_alias warm keep
  cfg C_on2_alias     $NEWBIN $NEWSE "$ON2" 1 5000 alias warm
fi
# the same with the sandbox out of L1D, so transient loads miss and fills/cleanup show
cfg B_unsafe_$ALT     $NEWBIN $NEWSE "$OFF" 1 5000 no_alias $ALT keep
cfg A_on_$ALT         $NEWBIN $NEWSE "$ON1" 1 5000 no_alias $ALT keep
[ -n "$ON2" ] && cfg A_on2_$ALT $NEWBIN $NEWSE "$ON2" 1 5000 no_alias $ALT keep
echo "[$(date -Iseconds)] END run_stl_controls_amulet $b" >> "$LOG"

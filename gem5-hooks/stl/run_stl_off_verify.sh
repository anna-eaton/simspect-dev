#!/bin/bash
# SimSpect-STL port to the AMuLeT builds (2026-11-09), check (a): hooks-off equivalence.
# With NO --stl-* flag, the STL binary built in the COPY of each tree must give the
# same run as the in-place hooks-v2 binary other campaigns use. For each of the 10
# hooks-v2 verification cases (same tests, annotations, stalls and gem5 flags as
# gem5-hooks/verify/run_all_verify_v2.sh):
#   new = copy binary + copy se.py     (/work/amulet/hooks_stl_work/<Build>)
#   ref = in-place binary + in-place se.py (/work/amulet/amulet-gem5-<Build>_AE-v1.1, read only)
# and verify_simspect_hooks.py compares sim ticks, every line of the O3PipeView debug
# file (all_lines_identical), the non-simspect lines and parse_pipeview.
# Run inside gem5_dev from a dir holding verify_simspect_hooks.py, check_v2_trace.py,
# mkann.py, uv6x.s, uv6dep.s (cafe2: /work/amulet/hooks_stl_work/verifyoff; that path has the
# same length as /work/amulet/simspect_hooks_verify_v2, so the test-binary path on the simulated
# stack, and with it the sim ticks, match the 2026-11-08 table in wiki/design/SIMSPECT_HOOKS.md).
# Writes <case>/ dirs, <case>.log, <case>.check.json; prints one line per case.
# Doc: wiki/design/STL_SPECULATION.md "Port to the AMuLeT builds (2026-11-09)".
set -u
V=python3
A=/work/amulet
W=${W:-$A/hooks_stl_work}
R=/tests/simspect
T=$R/testsets/STT_6/mispredict_not_taken
C=$R/results/STT_6_cleanupspec_residue
INV=$A/amulet-gem5-InvisiSpec_AE-v1.1; CLN=$A/amulet-gem5-CleanupSpec_AE-v1.1; LFB=$A/amulet-gem5-SpecLFB_AE-v1.1
RB=build/X86_MESI_Two_Level/gem5.opt; CB=build/X86/gem5.opt
ISX="--ruby --scheme=SpectreSafeInvisibleSpec --needsTSO=1 --allowSpecBuffHit=1 --l1d_size=1kB --l1d_assoc=2"
FSX="--ruby --scheme=FuturisticSafeInvisibleSpec --needsTSO=1 --allowSpecBuffHit=1 --l1d_size=1kB --l1d_assoc=2"
CSX="--ruby --l2cache --scheme_invisispec=UnsafeBaseline --scheme_cleanupcache=Cleanup_FOR_L1L2 --needsTSO=0"

run() {  # name build copytree inplacetree bin s ann stall extra
  local n=$1 b=$2 new=$3 ref=$4 bin=$5; shift 5
  $V verify_simspect_hooks.py --bin "$new/$bin" --se "$new/configs/example/se.py" \
     --ref-bin "$ref/$bin" --ref-se "$ref/configs/example/se.py" \
     --s "$1" --ann "$2" --stall "$3" --extra="$4" --out "$n" > "$n.log" 2>&1
  local rc=$?
  $V check_v2_trace.py "$n/new/pipeview.txt" --build "$b" > "$n.check.json" 2>&1
  local crc=$?
  echo "$n rc=$rc check=$crc $(python3 -c "import json;d=json.load(open('$n/summary.json'));c=json.load(open('$n.check.json'));print('ok=%s ticks=%s/%s all_lines_same=%s non_simspect_same=%s pp_same=%s lines=%s stl_lines=%d hard=%s' % (d['ok'],d.get('sim_ticks_new'),d.get('sim_ticks_ref'),d.get('all_lines_identical'),d.get('non_simspect_identical'),d.get('parse_pipeview_identical'),d.get('non_simspect_lines_new'),sum(v for k,v in d['kinds'].items() if k.startswith('STL:')),[k for k,v in c['hard'].items() if not v] or 'all-pass'))" 2>&1)"
}
echo "[$(date -Iseconds)] START run_stl_off_verify new=$W ref=$A"
for b in InvisiSpec CleanupSpec; do md5sum $W/$b/$RB $A/amulet-gem5-${b}_AE-v1.1/$RB; done; md5sum $W/SpecLFB/$CB $LFB/$CB
run inv_uv1 InvisiSpec $W/InvisiSpec $INV $RB $T/asm/inst-002014.s $T/ann/inst-002014.ann.json 5000 "$ISX"
run inv_fut InvisiSpec $W/InvisiSpec $INV $RB $T/asm/inst-002014.s $T/ann/inst-002014.ann.json 5000 "$FSX"
run inv_014986 InvisiSpec $W/InvisiSpec $INV $RB $T/asm/inst-014986.s $T/ann/inst-014986.ann.json 5000 "$ISX"
for g in uv4align uv4split; do
  BR=$(python3 -c "import json;print(hex(json.load(open('$C/uv4_demo/$g.ann.json'))['annotations'][0]['branch_addr']))")
  run cln_$g CleanupSpec $W/CleanupSpec $CLN $RB $C/uv4_demo/$g.s $C/uv4_demo/$g.ann.json 2000 "$CSX --fnc-commit-stall-pc=$BR --fnc-commit-stall-cycles=150"
done
BR=$(python3 mkann.py $C/uv5_demo/uv5clean.s)
run cln_uv5clean CleanupSpec $W/CleanupSpec $CLN $RB $C/uv5_demo/uv5clean.s uv5clean.ann.json 2000 "$CSX --l1d_size=8kB --l1d_assoc=2 --L1_TBEs=8 --fnc-commit-stall-pc=$BR --fnc-commit-stall-cycles=150"
run cln_inst002014 CleanupSpec $W/CleanupSpec $CLN $RB $T/asm/inst-002014.s $T/ann/inst-002014.ann.json 5000 "$CSX"
python3 mkann.py uv6x.s > /dev/null
run lfb_uv6x SpecLFB $W/SpecLFB $LFB $CB uv6x.s uv6x.ann.json 2000 "--l2cache"
python3 mkann.py uv6dep.s > /dev/null
run lfb_uv6dep SpecLFB $W/SpecLFB $LFB $CB uv6dep.s uv6dep.ann.json 2000 "--l2cache"
run lfb_inst002014 SpecLFB $W/SpecLFB $LFB $CB $T/asm/inst-002014.s $T/ann/inst-002014.ann.json 5000 "--l2cache"
echo "[$(date -Iseconds)] END run_stl_off_verify"

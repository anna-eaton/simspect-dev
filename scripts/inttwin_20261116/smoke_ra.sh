#!/usr/bin/env bash
# smoke_ra.sh (agent e2wra 2026-11-16) -- smoke test of the four *_ra configs (cache_setup random_all) on ~10 tests each, on the node's
# inttwin code snapshot. Run inside gem5_dev on cafe3: bash /tests/inttwin_20261116/code/scripts/inttwin_20261116/smoke_ra.sh
# Per config: testset /tests/inttwin_20261116/smoke_ra/ts/<model>__smoke_<rn> (symlinks to the first 5 stems of each mode, 10 for stl),
# config = the _ra config with ONLY paths.results_name -> smoke_<rn> and paths.testset_dir -> smoke_ra/ts; testrun.py --once with run_queue.py's env.
# Also: an L1D-size check (gem5 se.py config.ini dcache size on both builds). Log: /tests/inttwin_20261116/smoke_ra/smoke.log
set -u
O=/tests/inttwin_20261116; S=$O/smoke_ra; mkdir -p $S/ts $S/cfg; L=$S/smoke.log; cd $O/code
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a $L; }
log "START smoke_ra (code $(head -1 SNAPSHOT.txt))"
for b in gem5-recon-modded gem5-recon-modded-stl; do
  rm -rf $S/l1d_$b; /work/$b/build/X86/gem5.opt -d $S/l1d_$b /work/$b/configs/example/se.py --cpu-type X86O3CPU --caches -c /bin/true > $S/l1d_$b.log 2>&1
  log "L1D $b: rc=$? $(awk '/^\[system.cpu.dcache\]/{f=1} f&&/^size=/{print "dcache size="$0; exit}' $S/l1d_$b/config.ini) $(awk '/^\[system.cpu.dcache\]/{f=1} f&&/^assoc=/{print $0; exit}' $S/l1d_$b/config.ini)"
done
for rn in E2w_STT_6_u_core_lpP_s2A_fpr_ra E2w_STT_6_u_core_lpP_s2A_int_ra E2wstl_Recon_6_u_stl_core_lpP_s2A_fpr_ra E2wstl_Recon_6_u_stl_core_lpP_s2A_int_ra; do
  cfg=runconfigs/inttwin_20261116/$rn.jsonc
  model=$(python3 -c "import json;print([c['model'] for c in json.load(open('runconfigs/inttwin_20261116/campaigns.json')) if c['results_name']=='$rn'][0])")
  modes=$(python3 -c "import json,re;print(' '.join(json.loads(re.sub(r'//[^\n]*','',open('$cfg').read()))['speculation']['branch_modes']))")
  n=5; [ "$modes" = stl_bypass ] && n=10
  d=$S/ts/${model}__smoke_$rn; rm -rf $d; mkdir -p $d; ln -s $O/testsets/$model/xml $d/xml
  for m in $modes; do mkdir -p $d/$m/asm $d/$m/ann
    for a in $(ls $O/testsets/$model/$m/ann | head -$n); do st=${a%.ann.json}; ln -sf $O/testsets/$model/$m/asm/$st.s $d/$m/asm/; ln -sf $O/testsets/$model/$m/ann/$a $d/$m/ann/; done
  done; touch $d/READY
  sed -e "0,/\"results_name\": \"$rn\"/s//\"results_name\": \"smoke_$rn\"/" -e "s#\"testset_dir\": \"$O/testsets\"#\"testset_dir\": \"$S/ts\"#" $cfg > $S/cfg/smoke_$rn.jsonc
  t0=$(date +%s); log "RUN $rn model=$model modes=$modes"
  TMPDIR=/tmp SIMSPECT_GEM5_TIMEOUT_S=900 SIMSPECT_GEM5_MAX_TICK=2000000000 nice -n 5 python3 -u testrun.py --config $S/cfg/smoke_$rn.jsonc \
     --model $(basename $d) --once --max-new 100000 > $S/$rn.log 2>&1
  log "END $rn rc=$? $(( $(date +%s)-t0 ))s"
done
log "DONE smoke_ra"

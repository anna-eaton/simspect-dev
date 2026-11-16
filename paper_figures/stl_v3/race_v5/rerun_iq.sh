#!/usr/bin/env bash
# rerun_iq.sh (agent figs-stl-race-v3, 2026-11-16) -- second attempt. rerun_track.sh (SPT --trackInstsFile) ABORTED at tick 3006500 in gem5-spt's own tracking print (regfile.hh:280 assertion in partialTaintVecAsInt, from BaseDynInst::toString in ROB::insertInst; log run.log), so the release cycle cannot come from SPT's tracking. This run instead adds the print-only debug flags IEW and IQ to the same command, to get the cycle the transmitter is issued (released by SPT) from the trace.
# (Original rerun_track.sh header follows; the --trackInstsFile part no longer applies.)
# cpu.cc:541-566, rob_impl.hh:557-566 "is now unsquashable", lsq_unit_impl.hh:1144-1160 "marked as delayed due to tainted srcs"), so the
# cycle at which SPT releases the transmitter comes from the trace instead of being inferred. Everything else is the exact command that
# gem5_common.run_gem5 (code tree cafe2 /tests/sptrace_20261116/code, lines 383-433) built for the race_v4 rerun
# (paper_figures/race_v4/README.md): the kept workdir of that run restored at its original path (same argv, so the same stack layout),
# its binary, branch_ann_se.json and patched program, cwd /work/gem5-spt (GEM5_DIR), SIMSPECT_COMMIT_IEW_DELAY=4, the config's
# extra_args (diag_d4_warm.jsonc), debug flags O3PipeView,LSQUnit,Commit. Faithfulness check: the new pipeview.txt must be byte-identical
# to the race_v4 one (it is compared below and the result logged).
# Run inside cafe2 gem5_dev: bash /tests/race_v5_20261116/rerun_track.sh   Log: /tests/race_v5_20261116/run.log
set -uo pipefail
O=/tests/race_v5_20261116; W=/tmp/race_inst-000125_zj4o8qm_; G=/work/gem5-spt
exec > >(tee -a $O/run_iq.log) 2>&1
echo "START $(date -u +%FT%TZ) host=$(hostname)"
[ -e $W ] && { echo "ERROR: $W exists, refusing to overwrite"; exit 2; }
mkdir -p /tmp/rv5 && tar -C /tmp -xzf $O/race_inst-000125_zj4o8qm_.tgz || { echo "ERROR: untar"; exit 3; }
cp $W/m5out/pipeview.txt $O/pipeview_v4_kept.txt
rm -rf $W/m5out && mkdir $W/m5out
:
md5sum $G/build/X86_MESI_Two_Level/gem5.opt; sha256sum $W/inst-000125 $W/branch_ann_se.json
CMD=($G/build/X86_MESI_Two_Level/gem5.opt --outdir=$W/m5out --debug-flags=O3PipeView,LSQUnit,Commit,IEW,IQ --debug-file=pipeview.txt
     $G/configs/example/se_exp.py --cmd=$W/inst-000125 --cpu-type=DerivO3CPU --caches --scheme=2 --abs-max-tick=100000000000
     --branch-ann-file=$W/branch_ann_se.json --branch-ann-base=0x401020
     --applyDDIFT=1 --fwdUntaint=1 --bwdUntaint=1 --configImpFlow=Lazy --freeParam=3 --scheme=SpectreSafeFence
     )
echo "cmd: ${CMD[*]}"
cd $G && SIMSPECT_COMMIT_IEW_DELAY=4 timeout 900 nice -n 19 "${CMD[@]}" > $O/gem5_stdout_iq.txt 2> $O/gem5_stderr_iq.txt; echo "gem5 rc=$?"
cp $W/m5out/pipeview.txt $O/pipeview_v5_iq.txt; cp $W/m5out/config.ini $W/m5out/stats.txt $O/ 2>/dev/null
grep -v -E "system.cpu.(iew|iq)[:.] |system.cpu.iew: |system.cpu.iq: " $O/pipeview_v5_iq.txt > $O/pv_filtered.txt; grep -v -E "system.cpu.(iew|iq)[:.] |system.cpu.iew: |system.cpu.iq: " $O/pipeview_v4_kept.txt > $O/pv4_filtered.txt; if cmp -s $O/pv4_filtered.txt $O/pv_filtered.txt; then echo "FAITHFUL: with the IEW and IQ lines removed, pipeview byte-identical to race_v4"; else echo "DIFFERS from race_v4:"; diff $O/pv4_filtered.txt $O/pv_filtered.txt | head -20; fi; rm -f $O/pv_filtered.txt $O/pv4_filtered.txt
grep -n "trackInsts\|commitToIEWDelay" $O/config.ini
echo "--- transmitter sn:612 IEW/IQ lines:"; grep -n "sn:612\]" $O/pipeview_v5_iq.txt | grep -v "Can.t commit" | head -60
gzip -f $O/pipeview_v5_iq.txt; rm -f $O/pipeview_v4_kept.txt
sha256sum $O/gem5_stdout_iq.txt $O/gem5_stderr_iq.txt $O/pipeview_v5_iq.txt.gz $O/config.ini
rm -rf $W
echo "END $(date -u +%FT%TZ)"

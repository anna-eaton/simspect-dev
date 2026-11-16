#!/bin/bash
# TIME-1 (agent timing, 2026-11-15): copy of STAGE3_gem5/timing/amulet_t5/run_t5.sh for cafe2. Changed ONLY: T5 dir
# (/tests/timing_20261115/amulet), REPO=$T5/amulet-repo (a copy of cafe2 /work/amulet-repo @ c871bdf, as T5 used a copy), the run is
# pinned to CPUs 0-31 (taskset; one hardware thread per physical core, same as the SimSpect runs), load snapshots before/after.
# AMuLeT's own YAMLs + benchmark_all.sh extra-args, CT-SEQ, -i 70 (140 inputs per program), instrumented benchmark_t5.py.
# Usage (cafe2 gem5_dev): run_amulet.sh <Defense> <instances> <programs-per-instance> [inputs=70]
set -u
D="$1"; R="$2"; N="$3"; I="${4:-70}"
T5=/tests/timing_20261115/amulet
REPO=$T5/amulet-repo
SRC=$REPO/src
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
RUN=$T5/runs/${D}_r${R}_n${N}_${STAMP}
mkdir -p "$RUN"
LOG=$RUN/run.log
exec > >(tee -a "$LOG") 2>&1
DOCK=$REPO/docker
case "$D" in
  InvisiSpec)  args="--ruby,--InvisiSpec,--InvisiSpec_Futuristic"; conf=$DOCK/docker_invisispec/docker_gem5_v1_final_cache_ipcFP.yaml; b=X86_MESI_Two_Level;;
  CleanupSpec) args="--ruby,--CleanupSpec";                      conf=$DOCK/docker_cleanupspec/docker_gem5_v1_final_cache_ipc.yaml; b=X86_MESI_Two_Level;;
  SpecLFB)     args="--SpecLFB";                                 conf=$DOCK/docker_speclfb/yamls/docker_gem5_v1_final_cache_tlb.yaml; b=X86;;
  *) echo "bad defense $D"; exit 2;;
esac
G=/work/amulet/amulet-gem5-${D}_AE-v1.1
Y=$RUN/$(basename "$conf")
sed -e "s#^gem5_location:.*#gem5_location: \"$G\"#" \
    -e "s#^gem5_checkpoint:.*#gem5_checkpoint: \"$RUN/checkpoint\"#" \
    -e "s#^gem5_output_location:.*#gem5_output_location: \"$RUN/m5out\"#" \
    -e "s#^gem5_binary:.*#gem5_binary: \"$G/build/$b/gem5.opt\"#" \
    -e "s#^gem5_se:.*#gem5_se: \"$G/configs/example/se.py\"#" "$conf" > "$Y"
diff "$conf" "$Y" > "$RUN/yaml.diff"
export PATH=/opt/amulet-venv/bin:$PATH
echo "=== TIME-1 AMuLeT START $(date -u +%FT%TZ) host=$(hostname) defense=$D instances=$R programs=$N inputs=$I taskset=0-31"
echo "python3: $(command -v python3) $(python3 --version 2>&1)"
echo "gem5: $G/build/$b/gem5.opt ($(stat -c '%y %s' $G/build/$b/gem5.opt)) md5 $(md5sum < $G/build/$b/gem5.opt)"
echo "yaml: $Y (from $conf); diff:"; cat "$RUN/yaml.diff"
echo "amulet-repo: $REPO @ $(cd $REPO && git rev-parse --short HEAD 2>/dev/null); benchmark_t5.py md5 $(md5sum < $T5/benchmark_t5.py)"
bash /tests/timing_20261115/scripts/snap.sh "before AMuLeT $D"
cd "$SRC" || exit 3
CMD=(taskset -c 0-31 python3 "$T5/benchmark_t5.py" -i "$I" -n "$N" -r "$R" -c "$Y" --extra-args="$args" -p "time1$D" -o "$RUN/benchmark-out-$D")
echo "cwd: $(pwd)"; echo "cmd: ${CMD[*]}"
"${CMD[@]}"
rc=$?
bash /tests/timing_20261115/scripts/snap.sh "after AMuLeT $D"
echo "=== TIME-1 AMuLeT END $(date -u +%FT%TZ) rc=$rc"
ls -d "$SRC"/debug-bench_time1${D}_* 2>/dev/null | head
exit $rc

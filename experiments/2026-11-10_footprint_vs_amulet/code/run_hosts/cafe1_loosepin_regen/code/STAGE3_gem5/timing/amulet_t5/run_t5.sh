#!/bin/bash
# T5 (firstdet-amulet, 2026-11-09): run AMuLeT's own benchmark campaign for one defense
# on cafe1, with AMuLeT's own YAML and extra-args (src/benchmark_all.sh), pointed at
# the AE gem5 builds in /work/amulet. Only paths in the YAML are changed.
#
# Usage (inside the cafe1 gem5_dev container):
#   run_t5.sh <Defense> <instances> <programs-per-instance> [inputs=70] [timeout_s]
# Defense in: SpecLFB CleanupSpec InvisiSpec STT
set -u
D="$1"; R="$2"; N="$3"; I="${4:-70}"; TMO="${5:-}"
T5=/tests/simspect_alloy_20261108/timing/amulet_t5
REPO=$T5/amulet-repo
SRC=$REPO/src
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
RUN=$T5/runs/${D}_${STAMP}
mkdir -p "$RUN"
LOG=$RUN/run.log
exec > >(tee -a "$LOG") 2>&1

DOCK=$REPO/docker
case "$D" in
  InvisiSpec)  args="--ruby,--InvisiSpec,--InvisiSpec_Futuristic"; conf=$DOCK/docker_invisispec/docker_gem5_v1_final_cache_ipcFP.yaml; b=X86_MESI_Two_Level;;
  CleanupSpec) args="--ruby,--CleanupSpec";                      conf=$DOCK/docker_cleanupspec/docker_gem5_v1_final_cache_ipc.yaml; b=X86_MESI_Two_Level;;
  STT)         args="--ruby,--STT,--STT_Futuristic";             conf=$DOCK/docker_stt/docker_gem5_v1_final_cache_tlb.yaml; b=X86;;
  SpecLFB)     args="--SpecLFB";                                 conf=$DOCK/docker_speclfb/yamls/docker_gem5_v1_final_cache_tlb.yaml; b=X86;;
  *) echo "bad defense $D"; exit 2;;
esac
G=/work/amulet/amulet-gem5-${D}_AE-v1.1

# YAML copy: only gem5 paths + output/checkpoint locations change.
Y=$RUN/$(basename "$conf")
sed -e "s#^gem5_location:.*#gem5_location: \"$G\"#" \
    -e "s#^gem5_checkpoint:.*#gem5_checkpoint: \"$RUN/checkpoint\"#" \
    -e "s#^gem5_output_location:.*#gem5_output_location: \"$RUN/m5out\"#" \
    -e "s#^gem5_binary:.*#gem5_binary: \"$G/build/$b/gem5.opt\"#" \
    -e "s#^gem5_se:.*#gem5_se: \"$G/configs/example/se.py\"#" "$conf" > "$Y"
diff "$conf" "$Y" > "$RUN/yaml.diff"

export PATH=/opt/amulet-venv/bin:$PATH
echo "=== T5 START $(date -u +%FT%TZ) host=$(hostname) defense=$D instances=$R programs=$N inputs=$I timeout=${TMO:-none}"
echo "python3: $(command -v python3) $(python3 --version 2>&1); python3.11: $(command -v python3.11)"
echo "gem5: $G/build/$b/gem5.opt ($(stat -c '%y %s' $G/build/$b/gem5.opt))"
echo "yaml: $Y (from $conf); diff:"; cat "$RUN/yaml.diff"
echo "amulet-repo: $REPO @ $(cd $REPO && git rev-parse --short HEAD 2>/dev/null)"
nproc; uptime

cd "$SRC" || exit 3
CMD=(python3 "$T5/benchmark_t5.py" -i "$I" -n "$N" -r "$R" -c "$Y" --extra-args="$args" -p "t5$D" -o "$RUN/benchmark-out-$D")
[ -n "$TMO" ] && CMD+=(-t "$TMO")
echo "cwd: $(pwd)"; echo "cmd: ${CMD[*]}"
"${CMD[@]}"
rc=$?
echo "=== T5 END $(date -u +%FT%TZ) rc=$rc"
uptime
# AMuLeT leaves per-instance debug dirs in src when they crash; record what's left.
ls -d "$SRC"/debug-bench_t5${D}_* 2>/dev/null | head
exit $rc

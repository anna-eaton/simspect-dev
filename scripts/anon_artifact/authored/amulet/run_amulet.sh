set -u
D="$1"; R="$2"; N="$3"; I="$4"; OUT="$5"
: "${AMULET_REPO:?}" "${GEM5_ROOT:?}" "${AMULET_PY:=python3}" "${CPUS:=}"
SRC=$AMULET_REPO/src
T5=${AMULET_T5:?}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
RUN=$OUT/runs/${D}_r${R}_n${N}_${STAMP}
mkdir -p "$RUN"
exec > >(tee -a "$RUN/run.log") 2>&1
DOCK=$AMULET_REPO/docker
case "$D" in
  InvisiSpec)  args="--ruby,--InvisiSpec,--InvisiSpec_Futuristic"; conf=$DOCK/docker_invisispec/docker_gem5_v1_final_cache_ipcFP.yaml; b=X86_MESI_Two_Level;;
  CleanupSpec) args="--ruby,--CleanupSpec";                      conf=$DOCK/docker_cleanupspec/docker_gem5_v1_final_cache_ipc.yaml; b=X86_MESI_Two_Level;;
  SpecLFB)     args="--SpecLFB";                                 conf=$DOCK/docker_speclfb/yamls/docker_gem5_v1_final_cache_tlb.yaml; b=X86;;
  *) echo "bad defense $D"; exit 2;;
esac
G=$GEM5_ROOT/amulet-gem5-${D}_AE-v1.1
mkdir -p "$G/build/X86"
Y=$RUN/$(basename "$conf")
sed -e "s#^gem5_location:.*#gem5_location: \"$G\"#" \
    -e "s#^gem5_checkpoint:.*#gem5_checkpoint: \"$RUN/checkpoint\"#" \
    -e "s#^gem5_output_location:.*#gem5_output_location: \"$RUN/m5out\"#" \
    -e "s#^gem5_binary:.*#gem5_binary: \"$G/build/$b/gem5.opt\"#" \
    -e "s#^gem5_se:.*#gem5_se: \"$G/configs/example/se.py\"#" "$conf" > "$Y"
diff "$conf" "$Y" > "$RUN/yaml.diff"
echo "=== AMuLeT START $(date -u +%FT%TZ) defense=$D instances=$R programs=$N inputs=$I cpus=${CPUS:-all}"
uptime
cd "$SRC" || exit 3
PIN=(); [ -n "$CPUS" ] && PIN=(taskset -c "$CPUS")
"${PIN[@]}" "$AMULET_PY" "$T5/benchmark_t5.py" -i "$I" -n "$N" -r "$R" -c "$Y" --extra-args="$args" -p "art$D" -o "$RUN/benchmark-out-$D"
rc=$?
uptime
echo "=== AMuLeT END $(date -u +%FT%TZ) rc=$rc run=$RUN"
exit $rc

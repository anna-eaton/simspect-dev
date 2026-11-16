#!/usr/bin/env bash
# run_inspv7.sh (inspector-v7-agent, 2026-11-16) -- one-test gem5 reruns of inst-023734 (STT_6_u_core_lpP_fv3, mispredict_not_taken)
# for Inspector figure v7: E3 (stt-master, STT, scheme 2) and its Unsafe twin E1 (gem5-recon-modded, X86O3CPU, scheme 0).
# Config = the E3 shard config that produced the campaign record (runconfigs/twostage_lp/eval_20261110/shards/E3_STT_6_u_core_lpP_fv3_sh100_1.jsonc)
# with ONLY: paths.testset_dir/results_dir/results_name (this workspace), pipeline.keep_tmp=true (keeps the trace), branch_modes=[not_taken],
# gem5.jobs=1. The E1 twin additionally swaps gem5.binary/config_script/cpu_type/scheme to E1's gem5 block
# (runconfigs/twostage_fv2_20261109/E1_STT_6_u_fv2fp.jsonc; the only differences between the E1 and E3 gem5 blocks). Timing = the campaign's
# whole-test timing-grid draw (sweep.timing_grid, sha256('tgrid-v1:inst-023734') mod 9), which pipeline.py's sweep path materialises itself
# (_enumerate_grid_for_corpus -> sweep/manifest.json, _materialise_grid_run -> sweep/variants/point_0000/inst-023734.ann.json); the draw is
# also printed below. Cache setup warm (row default). TMPDIR=/tmp as in the campaign (BUGS.md H-STK).
# Run inside cafe3 gem5_dev:  bash /tests/inspector_v7_20261116/run_inspv7.sh   Log: /tests/inspector_v7_20261116/logs/run.log
set -uo pipefail
O=/tests/inspector_v7_20261116; CODE=/tests/simspect_alloy_20261108/loosepin_regen/code_eval
SRC=/tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/mispredict_not_taken; STEM=inst-023734
M=STT_6_u_core_lpP_fv3__inspv7; MODE=mispredict_not_taken
mkdir -p $O/logs $O/configs $O/results $O/testsets/$M/$MODE/asm $O/testsets/$M/$MODE/ann
exec > >(tee -a $O/logs/run.log) 2>&1
echo "START $(date -u +%FT%TZ) host=$(hostname)"
cp -f $SRC/asm/$STEM.s $O/testsets/$M/$MODE/asm/ && cp -f $SRC/ann/$STEM.ann.json $O/testsets/$M/$MODE/ann/
sha256sum $SRC/asm/$STEM.s $SRC/ann/$STEM.ann.json $O/testsets/$M/$MODE/asm/$STEM.s $O/testsets/$M/$MODE/ann/$STEM.ann.json
md5sum /work/stt-master/build/X86/gem5.opt /work/gem5-recon-modded/build/X86/gem5.opt
cd $CODE || exit 1
head -1 CODE_SNAPSHOT.txt
python3 - <<'PY'
import json, re, sys
sys.path.insert(0, "."); import pipeline
O = "/tests/inspector_v7_20261116"
src = "runconfigs/twostage_lp/eval_20261110/shards/E3_STT_6_u_core_lpP_fv3_sh100_1.jsonc"
c = pipeline.load_config(__import__("pathlib").Path(src))
c["paths"].update(testset_dir=f"{O}/testsets", results_dir=f"{O}/results", results_name="INSPV7_inst-023734_E3")
c["pipeline"]["keep_tmp"] = True
c["speculation"]["branch_modes"] = ["mispredict_not_taken"]
c["gem5"].pop("sample_fraction", None); c["gem5"]["jobs"] = 1
json.dump(c, open(f"{O}/configs/INSPV7_E3.json", "w"), indent=1)
c["paths"]["results_name"] = "INSPV7_inst-023734_E1"
c["gem5"].update(binary="/work/gem5-recon-modded/build/X86/gem5.opt", config_script="/work/gem5-recon-modded/configs/example/se.py",
                 cpu_type="X86O3CPU", scheme=0)
json.dump(c, open(f"{O}/configs/INSPV7_E1.json", "w"), indent=1)
print("timing-grid draw (unresolved, resolved) for inst-023734:", pipeline._timing_grid_point("inst-023734", c["sweep"]))
PY
export TMPDIR=/tmp
for E in E3 E1; do
  echo "=== $E $(date -u +%FT%TZ)"
  python3 pipeline.py gem5 --model $M --config $O/configs/INSPV7_$E.json --force; echo "$E rc=$?"
  R=$O/results/INSPV7_inst-023734_$E/$MODE
  cat $R/window-results.json; cat $R/sweep/manifest.json
  python3 - $R <<'PY'
import json, sys, glob, shutil, os
R = sys.argv[1]
for f in sorted(glob.glob(f"{R}/sweep/raw_results/*.json")):
    for r in json.load(open(f)):
        keys = ("name status issued_in_window cache_fate data_obtained lc_retire fnc_retire fnc_complete xmit_issue xmit_complete "
                "xmit_signal xmit_execute xmit_retire packet_tick workdir criteria").split()
        print(f, json.dumps({k: r.get(k) for k in keys}))
PY
done
echo "END $(date -u +%FT%TZ)"

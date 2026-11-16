#!/bin/bash
# Re-copy the firstdet-final results (T*g final protocol, plus T*rt / T2u5 and the reports) from cafe3 + cafe1 into
# results/firstdet_final/, the same way the 2026-11-10 snapshot did: no raw/, traces/ or work/ dirs; order_seed.tsv
# deduplicated against order_seed20261109.tsv; files over 1 MB gzipped; then SHA256SUMS regenerated.
# Run from the Mac (needs ssh to cafe1/cafe3; read-only on the hosts):  bash recopy_results.sh
# Log: recopy_results.log in this directory.
set -euo pipefail
S=$(cd "$(dirname "$0")" && pwd); R=$S/results/firstdet_final; LOG=$S/recopy_results.log
exec > >(tee -a "$LOG") 2>&1
echo "[$(date -u '+%F %T')] recopy start"
F=/tests/simspect_alloy_20261108/firstdet_final
stage=$(mktemp -d); trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/cafe3" "$stage/cafe1"
ssh cafe3 "docker exec -i gem5_dev bash -lc 'cd $F && tar -czf - --exclude=raw --exclude=traces --exclude=work --exclude=*_cafe1 T1g_* T1rt_* T2g_* T2rt_* T2u5_* T3g_* T3rt_* report uv5diag uv1_sample300 uv1_sample.py launch.log 2>/dev/null'" | tar -xzf - -C "$stage/cafe3"
ssh cafe1 "docker exec -i gem5_dev bash -lc 'cd $F && tar -czf - --exclude=raw --exclude=traces --exclude=work T2g_*_cafe1 T2rt_*_cafe1 T2u5_*_cafe1 launch.log uv5diag 2>/dev/null'" | tar -xzf - -C "$stage/cafe1"
h=$(shasum -a 256 "$R/order_seed20261109.tsv" | awk '{print $1}')
for f in "$stage"/*/*/order_seed.tsv; do
  if [ "$(shasum -a 256 "$f" | awk '{print $1}')" = "$h" ]; then rm "$f"; else echo "WARNING: $f differs from order_seed20261109.tsv; kept"; fi
done
find "$stage" -type f -size +1M ! -name '*.gz' -exec gzip -9 {} \;
rm -rf "$R/cafe3" "$R/cafe1"; mv "$stage/cafe3" "$R/cafe3"; mv "$stage/cafe1" "$R/cafe1"
cd "$S" && find . -type f ! -name SHA256SUMS ! -name recopy_results.log ! -name .DS_Store -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
echo "[$(date -u '+%F %T')] recopy done; now update README 'Results' + 'Status' sections and EVAL_MANIFEST part 7"

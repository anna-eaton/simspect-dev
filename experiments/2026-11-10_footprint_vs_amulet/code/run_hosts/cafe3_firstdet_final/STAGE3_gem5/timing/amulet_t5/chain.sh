#!/bin/bash
# T5 chain (firstdet-amulet 2026-11-09): run AMuLeT campaigns one defense after another.
# Usage: chain.sh <instances> <programs> <inputs> <timeout_s|""> <Defense>...
# Log: $T5/chain.log (one line per start/end).
T5=/tests/simspect_alloy_20261108/timing/amulet_t5
R="$1"; N="$2"; I="$3"; TMO="$4"; shift 4
echo "$(date -u +%FT%TZ) chain start: R=$R N=$N I=$I timeout=${TMO:-none} defenses=$*" >> $T5/chain.log
for D in "$@"; do
  echo "$(date -u +%FT%TZ) start $D" >> $T5/chain.log
  bash $T5/run_t5.sh "$D" "$R" "$N" "$I" $TMO
  rc=$?
  echo "$(date -u +%FT%TZ) end $D rc=$rc" >> $T5/chain.log
done
echo "$(date -u +%FT%TZ) chain end" >> $T5/chain.log

#!/bin/bash
# T5 chain (firstdet-amulet 2026-11-09): SpecLFB, CleanupSpec, InvisiSpec; 32 instances x 200 programs x 70 inputs (AMuLeT defaults -n 200 -i 70).
T5=
echo "chain start $(date -u +%FT%TZ)" >> $T5/chain_main.log
for D in SpecLFB CleanupSpec InvisiSpec; do
  echo "$(date -u +%FT%TZ) start $D" >> $T5/chain_main.log
  bash $T5/run_t5.sh $D 32 200 70
  echo "$(date -u +%FT%TZ) end $D rc=$?" >> $T5/chain_main.log
done
echo "chain end $(date -u +%FT%TZ)" >> $T5/chain_main.log

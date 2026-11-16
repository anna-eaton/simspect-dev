#!/usr/bin/env bash
# relay_cafe3.sh -- regen-lp (2026-11-10): copy every PUBLISHED stream batch of a corpus from cafe1 to cafe3 (no direct
# cafe1->cafe3 ssh, so it runs on the Mac and pipes tar through it). Resumable: a batch is copied once (cafe3 marker
# <F>/.relay/<batch>.done). On cafe3 each batch is untarred into <F>/.incoming/<batch>/ and then moved in with renames:
# SHA256SUMS of the payload is verified first (size+hash), then xml, every .s, every .ann.json are moved in with renames,
# and only then this batch's rows are appended to MANIFEST.tsv / rmw_stems.tsv / jmp_stems.tsv (temp file + rename), so a
# consumer that sees a stem in MANIFEST.tsv sees its final, verified .s and .ann.json. Batches are relayed in name order.
# When cafe1 has <F>/READY and every batch is relayed, READY is copied last and the loop ends.
# Log: ~/Library/Logs/simspect/relay_<name>.log (every batch, counts, errors). Usage: relay_cafe3.sh <corpus name> [interval_s]
set -u
N=${1:?corpus name}; IV=${2:-120}
B=/tests/simspect_alloy_20261108; F=$B/testsets_twostage/$N; SB=$B/loosepin_regen/stream/$N/batches
LOG=~/Library/Logs/simspect/relay_$N.log; mkdir -p "$(dirname "$LOG")"
log(){ echo "$(date -u '+%F %T') $*" >> "$LOG"; }
log "START corpus=$N interval=$IV"
while true; do
  pub=$(ssh cafe1 "docker exec -i gem5_dev bash -lc 'ls $SB 2>/dev/null | while read b; do [ -e $SB/\$b/PUBLISHED ] && echo \$b; done'" 2>>"$LOG")
  done_=$(ssh cafe3 "docker exec -i gem5_dev bash -lc 'mkdir -p $F/.relay; ls $F/.relay'" 2>>"$LOG")
  for b in $pub; do
    echo "$done_" | grep -qx "$b.done" && continue
    if ssh cafe1 "docker exec -i gem5_dev bash -lc 'cd $SB/$b/out && tar cf - .'" 2>>"$LOG" | \
       ssh cafe3 "docker exec -i gem5_dev bash -lc 'set -e; I=$F/.incoming/$b; rm -rf \$I; mkdir -p \$I; tar xf - -C \$I; cd \$I
         sha256sum --quiet -c SHA256SUMS
         mkdir -p $F/xml; for f in xml/*; do [ -e \$f ] && mv -f \$f $F/xml/; done
         for m in mispredict_not_taken mispredict_taken; do mkdir -p $F/\$m/asm $F/\$m/ann
           for f in \$m/asm/*.s; do [ -e \$f ] && mv -f \$f $F/\$m/asm/; done; done
         for m in mispredict_not_taken mispredict_taken; do for f in \$m/ann/*.ann.json; do [ -e \$f ] && mv -f \$f $F/\$m/ann/; done; done
         for pair in MANIFEST_batch.tsv:MANIFEST.tsv rmw_batch.tsv:rmw_stems.tsv jmp_batch.tsv:jmp_stems.tsv; do src=\${pair%%:*}; dst=$F/\${pair##*:}
           [ -s \$src ] || continue
           if [ ! -e \$dst ]; then head -1 \$src > \$dst.tmp; else cp \$dst \$dst.tmp; fi
           tail -n +2 \$src | awk \"NR==FNR{s[\\\$0]=1;next} !s[\\\$0]\" \$dst.tmp - >> \$dst.tmp && mv -f \$dst.tmp \$dst; done
         cd $F && rm -rf \$I && touch $F/.relay/$b.done && echo ok'" 2>>"$LOG" | grep -q ok; then
      n=$(ssh cafe3 "docker exec -i gem5_dev bash -lc 'tail -n +2 $F/MANIFEST.tsv | wc -l'" 2>>"$LOG")
      log "relayed $b (cafe3 MANIFEST stems now $n)"
    else
      log "ERROR relaying $b (will retry)"
    fi
  done
  ssh cafe1 "docker exec -i gem5_dev bash -lc 'cat $F/PROVENANCE.json 2>/dev/null'" 2>>"$LOG" | ssh cafe3 "docker exec -i gem5_dev bash -lc 'cat > $F/.PROVENANCE.json.tmp && [ -s $F/.PROVENANCE.json.tmp ] && mv -f $F/.PROVENANCE.json.tmp $F/PROVENANCE.json || rm -f $F/.PROVENANCE.json.tmp'" 2>>"$LOG"
  if ssh cafe1 "docker exec -i gem5_dev bash -lc 'test -e $F/READY'" 2>/dev/null; then
    left=$(for b in $pub; do ssh cafe3 "docker exec -i gem5_dev bash -lc 'test -e $F/.relay/$b.done || echo $b'"; done)
    if [ -z "$left" ]; then
      ssh cafe1 "docker exec -i gem5_dev bash -lc 'cat $F/READY'" | ssh cafe3 "docker exec -i gem5_dev bash -lc 'cat > $F/.READY.tmp && mv -f $F/.READY.tmp $F/READY'"
      log "READY relayed; END"; break
    fi
  fi
  sleep "$IV"
done

cd /tests/simspect_alloy_20261108/testsets_twostage/STT_6_u_core_lpP_fv3/mispredict_not_taken/asm
for s in "$@"; do
  n=$(awk '/_pc0:/{f=1} f&&/^\t[a-z]/{c++} /^\.Ltmp0:/{print c; exit}' $s.s)
  echo "== $s ninstr_lines=$n xmm4=$(grep -c xmm4 $s.s) jmp=$(grep -c 'jmp' $s.s)"
  awk '/_pc[0-9]:$/{getline; while($0 ~ /^\t\.globl|^__litmus/){getline}; print "   " prev_lab " " $0} {if($0 ~ /_pc[0-9]:$/) prev_lab=$0}' $s.s | head -0
  grep -A3 -E '_pc[0-9]:$' $s.s | grep -vE 'globl|first_noncommitted:|last_committed:|^--' | sed 's/^/   /'
done

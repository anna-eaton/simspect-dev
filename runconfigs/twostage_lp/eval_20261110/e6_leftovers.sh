#!/bin/bash
# regen-lp 2026-11-10: E6 100% leftover diligence on cafe2: (a) faithful GPR twin (RMW + jmp kept) of the 27 unexplained /
# untainted-without-twin stems, run with the E6 twin config; (b) R-SA-8 delay-unit trace on the 146 br_x twin-hit tests.
set -u
R=/tests/simspect_alloy_20261108/loosepin_regen; cd $R/code_eval; E=runconfigs/twostage_lp/eval_20261110; T=/tests/simspect_alloy_20261108/testsets_twostage
echo "$(date -u '+%F %T') START"
( python3 $E/rsa8_trace.py --config $E/E6_Recon_6_u_core_lpP_fv3_gprtwin.jsonc --testset-dirs $T/Recon_6_u_core_lpP_fv3_gprtwin_e6 $T/Recon_6_u_core_lpP_fv3_gprtwin_e6b $T/Recon_6_u_core_lpP_fv3_gprtwin_e6c $T/Recon_6_u_core_lpP_fv3_gprtwin_e6d \
    --keys $R/bugwork/rsa8/keys_e6.txt --out $R/bugwork/rsa8/e6_rsa8.json --par 16 --work $R/bugwork/rsa8_e6 > $R/bugwork/rsa8/e6_rsa8.log 2>&1 ) &
(cd $R/code && bash make_faithful_twin.sh Recon_6_u_core_lpP_fv3 ../e6_leftovers.txt Recon_6_u_core_lpP_fv3_ftwin_e6left)
tail -2 $T/Recon_6_u_core_lpP_fv3_ftwin_e6left/make_faithful_twin.log; cat $T/Recon_6_u_core_lpP_fv3_ftwin_e6left/TWIN_MISMATCH.tsv
sed 's/"E6_Recon_6_u_core_lpP_fv3_gprtwin"/"E6_Recon_6_u_core_lpP_fv3_ftwin_left"/' $E/E6_Recon_6_u_core_lpP_fv3_gprtwin.jsonc > $E/E6_Recon_6_u_core_lpP_fv3_ftwin_left.jsonc
TMPDIR=/tmp python3 -u testrun.py --config $E/E6_Recon_6_u_core_lpP_fv3_ftwin_left.jsonc --model Recon_6_u_core_lpP_fv3_ftwin_e6left --once --max-new 1000 > ../logs/eval_E6_ftwin_left.log 2>&1
echo "$(date -u '+%F %T') ftwin run rc=$?"
wait
tail -1 $R/bugwork/rsa8/e6_rsa8.log
echo "$(date -u '+%F %T') ALLDONE"

#!/usr/bin/env python3
"""build_q_fp_eq.py (regen-lp, 2026-11-10): Alloy equivalence checks, footprint block on the OLD skeleton (InvisiSpec_6.als:
State-typed protection set, lifted with .(~opstate) in secure_*/tag_xm) vs Footprint_6_u.als (ultimate skeleton, Operand-typed).
Input Footprint_6_u.als (or one of its loose-pin drafts with --base); output q_fp_eq.als (or --out). The old-skeleton defense is
reproduced verbatim as *_old functions (hpp_old = Mem_s, identity propagation, the STT_6 fold, the .(~opstate) lift).
tag_xm is demoted to a pred so the checks range over every structure the skeleton facts allow.
Negative controls (expected SAT = a counterexample, so the checks are not vacuous): neg_control_*.
Checks: flag sets equal per perturbation family (no_p, RR, RC+RR, RS, RI, RO), tag equal, gen_useful_litmus equal.
A `check` that is UNSAT (no counterexample) holds at that scope."""
import argparse, re
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--base", default="../../Footprint_6_u.als"); ap.add_argument("--out", default="q_fp_eq.als")
ap.add_argument("--scope", default="for 9 but exactly 6 Instruction, exactly 1 rBool, exactly 1 cBool, exactly 1 tBool")
ap.add_argument("--gen-new", default=None, help="name of the let to compare (default gen_useful_litmus)")
a = ap.parse_args()
t = Path(a.base).read_text()
t, n = re.subn(r"\nrun gen_lit \{.*?\}[^\n]*\n", "\n", t, flags=re.S); assert n == 1
t, n = re.subn(r"\nfact tag_xm \{", "\npred tag_new {", t); assert n == 1
hm = re.search(r"^// footprint \(old skeleton\): fun hardware_protection_policy: State \{(.*)\}$", t, re.M)
assert hm, "old-skeleton seed comment not found (make_footprint_u.py writes it)"
HPP_OLD = hm.group(1)
depth = len(re.findall(r"\ba\[p,", re.search(r"fun last_committed_protset_p.*?\n\}", t, re.S).group(0)))
expr = "hpp_old"
for k in range(depth):
    expr = f"a_old[p,f[p]{'.(spo_p[p])' * k},{expr}]"
S = a.scope
aux = f"""
// ======== regen-lp equivalence aux (old-skeleton footprint defense, verbatim semantics) ========
fun hpp_old : State {{{HPP_OLD}}}   // the source footprint model's hardware_protection_policy, verbatim
fun prop_old[p:PTag->univ,i:Instruction,s:State] : State {{ s }}          // InvisiSpec_6: identity
fun a_old[p:PTag->univ,i:Instruction,s:State] : State {{ prop_old[p,i,s] }}
fun lcp_old[p: PTag->univ] : State {{ {expr} }}                           // fold, same depth ({depth}) as this file's
fun flag_old[p: PTag->univ] : Operand {{ (lcp_old[p].(~opstate) & speculative_xmit_p[p]) + (lcp_old[p].(~opstate).(^(op_edges_p[p])) & speculative_xmit_p[p]) }}
fun flag_new[p: PTag->univ] : Operand {{ (last_committed_protset_p[p] & speculative_xmit_p[p]) + (last_committed_protset_p[p].(^(op_edges_p[p])) & speculative_xmit_p[p]) }}
pred secure_old[p: PTag->univ] {{ no flag_old[p] }}
pred tag_old {{ some flag_old[no_p] & xm.operands }}
pred gul_old {{
  not secure_old[no_p]
  all i: (unresolved - first_uncommitted) | secure_old[RR->i]
  secure_old[RC->first_uncommitted + RR->first_uncommitted]
  all s: State | secure_old[RS->s]
}}
pred gul_new_prod {{
  not secure_speculation_scheme_p[no_p]
  all i: (unresolved - first_uncommitted) | secure_speculation_scheme_p[RR->i]
  secure_speculation_scheme_p[RC->first_uncommitted + RR->first_uncommitted]
  all s: State | secure_speculation_scheme_p[RS->s]
}}
check eq_nop {{ flag_old[no_p] = flag_new[no_p] }} {S}
check eq_tag {{ tag_old <=> tag_new }} {S}
check eq_RR {{ all i: Instruction | flag_old[RR->i] = flag_new[RR->i] }} {S}
check eq_RCRR {{ all i: Instruction | flag_old[RC->i + RR->i] = flag_new[RC->i + RR->i] }} {S}
check eq_RC {{ all i: Instruction | flag_old[RC->i] = flag_new[RC->i] }} {S}
check eq_RS {{ all s: State | flag_old[RS->s] = flag_new[RS->s] }} {S}
check eq_RI {{ all i: Instruction | flag_old[RI->i] = flag_new[RI->i] }} {S}
check eq_RO {{ all o: Operand | flag_old[RO->o] = flag_new[RO->o] }} {S}
check eq_gen {{ (gul_old and tag_old) <=> (gul_new_prod and tag_new) }} {S}
run gen_sanity {{ gul_new_prod and tag_new }} {S}
check neg_control_direct_term_only {{ flag_old[no_p] = (last_committed_protset_p[no_p] & speculative_xmit_p[no_p]) }} {S}
"""
Path(a.out).write_text(t + aux)
print(a.out, "fold depth", depth)

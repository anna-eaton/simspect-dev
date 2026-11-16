import json,re,subprocess,sys,os
from pathlib import Path
SP=Path(sys.argv[0]).resolve().parent.parent
ROOT=Path('/Users/annaeaton/trippel/simspect'); S2=ROOT/'STAGE2_compilation'
def jl(p):
    t=Path(p).read_text(); t=re.sub(r'^\s*//.*$','',t,flags=re.M); return json.loads(t)
cfg=jl(ROOT/'runconfigs/overnight_20261111/stl_final_A.jsonc')
variant=sys.argv[1]
if variant=='off':
    fv=cfg['fanout_v2']; fv.pop('vocab_rj',None); fv.pop('interleave_only',None)
    tables=sys.argv[2]
else: tables=cfg['paths']['instruction_tables']
for F in ['STT_6_u_stl','Recon_6_u_stl']:
    log=(SP/f'stlsmoke/{F}/stage2_sharded.log').read_text()
    stems=sorted(p.name for p in (SP/f'stlsmoke/{F}/xml').glob('inst-*.xml'))
    d=SP/f'stlfail/all_{variant}{len(sys.argv)}{Path(tables).stem}/{F}'; xd=d/'xml'; xd.mkdir(parents=True,exist_ok=True); od=d/'llvm'; od.mkdir(exist_ok=True)
    for s in stems:
        l=xd/s
        if not l.exists(): l.symlink_to(SP/f'stlsmoke/{F}/xml/{s}')
    cmd=[sys.executable,str(S2/'batch_generate.py'),str(xd),'--out',str(od),'--kind','--instruction-tables',str(ROOT/tables),'--mode','stl_bypass',
         '--interleave-config',json.dumps(cfg['interleave']),'--fpr-config',json.dumps(cfg['fpr']),'--reg-naming-config',json.dumps(cfg['reg_naming']),
         '--fanout-v2-config',json.dumps(cfg['fanout_v2']),'--branch-cond-config',json.dumps(cfg['branch_cond'])]
    r=subprocess.run(cmd,cwd=str(S2),capture_output=True,text=True)
    (d/'out.txt').write_text(r.stdout+'\n=====STDERR\n'+r.stderr)
    print(F,len(stems),r.stdout.strip().splitlines()[-2])

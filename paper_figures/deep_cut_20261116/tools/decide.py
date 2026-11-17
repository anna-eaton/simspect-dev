# Measure each DECIDE patch alone on top of a given tree state.
import sys, os, shutil, importlib.util, difflib, json
SC = '/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0, SC + '/tools'); import edit2 as edit, buildlib
spec = importlib.util.spec_from_file_location('dp', sys.argv[1]); dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)
state = sys.argv[2]; tag = sys.argv[3]; ids = sys.argv[4].split(',') if len(sys.argv) > 4 else [p[0] for p in dp.DECIDES]
patchdir = os.environ.get('PATCHDIR')
wd = f'{SC}/runs/{tag}'; os.makedirs(wd, exist_ok=True)
r0 = buildlib.build(state, wd, 'ref'); print('ref', r0, flush=True)
byid = {p[0]: p for p in dp.DECIDES}
for pid in ids:
    p = byid[pid]; t = f'{wd}/tree_{pid}'; shutil.rmtree(t, ignore_errors=True); shutil.copytree(state, t)
    edit.apply(t, p[3])
    if patchdir:
        txt = ''
        for f in sorted(set(e[1] for e in p[3])):
            A = os.path.join(state, f); Bf = os.path.join(t, f)
            txt += __import__('subprocess').run(['diff','-u','--label','a/'+f,'--label','b/'+f,A,Bf],capture_output=True,text=True).stdout
        open(os.path.join(patchdir, f'{pid}_{p[1]}.patch'), 'w').write(txt)
    r = buildlib.build(t, wd, pid); shutil.rmtree(t)
    print(pid, p[1], 'row', r[0], 'delta', r[0] - r0[0], 'undef', r[1], 'overfull', r[2], 'pages', r[3], flush=True)

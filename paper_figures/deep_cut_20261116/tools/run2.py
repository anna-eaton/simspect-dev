import sys, os, shutil, importlib.util, difflib, json
SC = '/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0, SC + '/tools'); import edit2, buildlib
spec = importlib.util.spec_from_file_location('pm', sys.argv[1]); pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
listname = os.environ.get('LIST', 'PATCHES')
order = sys.argv[2].split(','); tag = sys.argv[3]; base = sys.argv[4]
mode = os.environ.get('MODE', 'cumulative')   # cumulative | alone
patchdir = os.environ.get('PATCHDIR')
wd = f'{SC}/runs/{tag}'; shutil.rmtree(wd, ignore_errors=True); os.makedirs(wd)
cur = wd + '/cur'; shutil.copytree(base, cur)
r0 = buildlib.build(cur, wd, '00'); print('base', r0, flush=True); prev = r0[0]
byid = {p[0]: p for p in getattr(pm, listname)}
for pid in order:
    p = byid[pid]
    if mode == 'alone': shutil.rmtree(cur); shutil.copytree(base, cur)
    before = wd + '/before'; shutil.rmtree(before, ignore_errors=True); shutil.copytree(cur, before)
    edit2.apply(cur, p[3])
    if patchdir:
        txt = ''
        for f in sorted(set(e[1] for e in p[3])):
            A = os.path.join(before, f); Bf = os.path.join(cur, f)
            txt += __import__('subprocess').run(['diff','-u','--label','a/'+f,'--label','b/'+f,A,Bf],capture_output=True,text=True).stdout
        open(os.path.join(patchdir, f'{pid}_{p[1]}.patch'), 'w').write(txt)
    r1 = buildlib.build(cur, wd, pid)
    ref = r0[0] if mode == 'alone' else prev
    print(pid, p[1], p[2], 'row', r1[0], 'delta', r1[0] - ref, 'undef', r1[1], 'overfull', r1[2], 'pages', r1[3], flush=True)
    prev = r1[0]

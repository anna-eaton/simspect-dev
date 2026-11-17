import sys, os, shutil, subprocess, re, importlib.util, difflib, json
SC = '/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0, SC + '/tools')
import edit
spec = importlib.util.spec_from_file_location('patches', sys.argv[1]); pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
order = sys.argv[2].split(',')          # patch ids in order
tag = sys.argv[3]                       # run name
base = sys.argv[4] if len(sys.argv) > 4 else SC + '/base'
build_each = os.environ.get('BUILD_EACH', '1') == '1'
patchdir = os.environ.get('PATCHDIR')   # write patch files here if set
cur = f'{SC}/runs/{tag}/cur'; shutil.rmtree(f'{SC}/runs/{tag}', ignore_errors=True)
shutil.copytree(base, cur)
byid = {p[0]: p for p in pm.PATCHES}
def build(label):
    bld = f'{SC}/runs/{tag}/bld'; out = f'{SC}/runs/{tag}/out_{label}'
    shutil.rmtree(bld, ignore_errors=True); shutil.copytree(cur, bld)
    mt = open(bld + '/main.tex').read().split('\n')
    for i in range(59, 65): mt[i] = re.sub(r'^% (% )?', '', mt[i])
    open(bld + '/main.tex', 'w').write('\n'.join(mt))
    os.makedirs(out, exist_ok=True)
    subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', '-outdir=' + out, 'main.tex'], cwd=bld, capture_output=True)
    m = subprocess.run(['python3', SC + '/tools/measure.py', out + '/main.pdf'], capture_output=True, text=True).stdout
    row = int(re.search(r'row (\d+)\s+\(', m).group(1))
    log = open(out + '/main.log', errors='ignore').read()
    undef = len(re.findall(r'Reference .* undefined|Citation .* undefined', log))
    over = re.findall(r'Overfull \\hbox \(([\d.]+)pt', log)
    pages = subprocess.run(['pdfinfo', out + '/main.pdf'], capture_output=True, text=True).stdout
    np_ = re.search(r'Pages:\s+(\d+)', pages).group(1)
    return row, undef, [float(x) for x in over], np_
res = []
prev_row = None
if build_each:
    r0 = build('00'); prev_row = r0[0]; print('base', r0, flush=True); res.append(('00', 'base', '', r0[0], 0, r0[1], r0[2]))
for pid in order:
    p = byid[pid]
    before = f'{SC}/runs/{tag}/before'; shutil.rmtree(before, ignore_errors=True); shutil.copytree(cur, before)
    rep = edit.apply(cur, p[3])
    if patchdir:
        files = sorted(set(e[1] for e in p[3]))
        txt = ''
        for f in files:
            a = open(os.path.join(before, f)).read().split('\n'); b = open(os.path.join(cur, f)).read().split('\n')
            d = difflib.unified_diff(a, b, 'a/' + f, 'b/' + f, lineterm='', n=1)
            txt += '\n'.join(d) + '\n'
        open(os.path.join(patchdir, f'{pid}_{p[1]}.patch'), 'w').write(txt)
    if build_each:
        r1 = build(pid)
        print(pid, p[1], p[2], 'row', r1[0], 'delta', r1[0] - prev_row, 'undef', r1[1], 'overfull', r1[2], 'pages', r1[3], flush=True)
        res.append((pid, p[1], p[2], r1[0], r1[0] - prev_row, r1[1], r1[2])); prev_row = r1[0]
json.dump(res, open(f'{SC}/runs/{tag}/results.json', 'w'))

import os, shutil, subprocess, re
PREVIEW = os.environ.get('PREVIEW','1') == '1'
SC = '/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
def build(tree, workdir, label):
    bld = f'{workdir}/bld_{label}'; out = f'{workdir}/out_{label}'
    shutil.rmtree(bld, ignore_errors=True); shutil.copytree(tree, bld)
    mt = open(bld + '/main.tex').read().split('\n')
    for i, l in enumerate(mt):   # uncomment the note switches (content-based, so line shifts do not matter)
        if re.match(r'^% (% )?\\renewcommand\{\\(todo|anna|reviewnote|urgentnote|labnote|proposed)\}', l):
            mt[i] = re.sub(r'^% (% )?', '', l)
        if PREVIEW and l.startswith('% \\DeclareRobustCommand{\\cutrep}[2]{#2}'):
            mt[i] = l[2:]
    open(bld + '/main.tex', 'w').write('\n'.join(mt))
    os.makedirs(out, exist_ok=True)
    subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', '-outdir=' + out, 'main.tex'], cwd=bld, capture_output=True)
    shutil.rmtree(bld, ignore_errors=True)
    m = subprocess.run(['python3', SC + '/tools/measure.py', out + '/main.pdf'], capture_output=True, text=True).stdout
    row = int(re.search(r'row (\d+)\s+\(', m).group(1))
    log = open(out + '/main.log', errors='ignore').read()
    undef = re.findall(r'(?:Reference|Citation) `([^\']*)\' on page \d+ undefined', log)
    over = [float(x) for x in re.findall(r'Overfull \\hbox \(([\d.]+)pt', log)]
    np_ = re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', out + '/main.pdf'], capture_output=True, text=True).stdout).group(1)
    return row, undef, over, np_

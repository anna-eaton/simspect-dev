import sys, shutil, os
PF='/Users/annaeaton/trippel/simspect/paper_figures'
src, dst = sys.argv[1], sys.argv[2]
shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
for f in [PF+'/relaxation_grid_20261116/relaxation_v4_grid.tex', PF+'/table2_stt_20261116/tikz/execvocab_v4_8pt.tex', PF+'/table2_stt_20261116/tikz/stt_xmm4_code_v2_8pt.tex']:
    shutil.copy(f, dst + '/tikz/')
for f, a, b in [('sections/pipeline.tex', r'\input{tikz/relaxation_v3_short}', r'\input{tikz/relaxation_v4_grid}'),
                ('sections/model.tex', r'\input{tikz/execvocab_v3_8pt}', r'\input{tikz/execvocab_v4_8pt}'),
                ('sections/results.tex', r'\input{tikz/stt_xmm4_code_8pt}', r'\input{tikz/stt_xmm4_code_v2_8pt}')]:
    p = os.path.join(dst, f); t = open(p).read()
    lines = t.split('\n'); hits = [i for i, l in enumerate(lines) if l.startswith(a)]
    assert len(hits) == 1, (f, a, hits)
    lines[hits[0]] = lines[hits[0]].replace(a, b, 1); open(p, 'w').write('\n'.join(lines))
print('ok')

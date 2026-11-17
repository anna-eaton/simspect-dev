import sys, shutil, importlib.util
SC='/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0,SC+'/tools'); import edit2
s=importlib.util.spec_from_file_location('p',SC+'/tools/patches8.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
src, dst, ids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
shutil.rmtree(dst,ignore_errors=True); shutil.copytree(src,dst)
for p in m.PATCHES:
    if p[0] in ids: edit2.apply(dst,p[3])

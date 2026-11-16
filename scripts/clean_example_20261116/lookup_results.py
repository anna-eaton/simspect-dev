#!/usr/bin/env python3
"""Read-only: for stems on stdin, print every record in <results_root>/<glob>/<mode>/<kind>/window-results.json
Usage: lookup_results.py <results_root> <dir_glob> < stems.txt"""
import sys, os, glob, json
root, pat = sys.argv[1], sys.argv[2]
want = set(l.strip() for l in sys.stdin if l.strip())
for d in sorted(glob.glob(os.path.join(root, pat))):
    if os.path.islink(d): continue
    for wr in glob.glob(os.path.join(d, '*', '*', 'window-results.json')):
        mode, kind = wr.split('/')[-3], wr.split('/')[-2]
        for r in json.load(open(wr)):
            if r.get('name') in want:
                print('\t'.join([os.path.basename(d), mode, kind, r['name'], str(r.get('issued_in_window')), str(r.get('status'))]))

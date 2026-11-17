import sys, os, re, importlib.util
SC='/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
sys.path.insert(0, SC+'/tools'); from reasons3 import reason
def load(n, f):
    s=importlib.util.spec_from_file_location(n, SC+'/tools/'+f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
pm = load('p8','patches8.py'); dm = load('d2','decides2.py')
base = SC+'/base8'
def code(t):
    if t == '': return '*(cut)*'
    n = max([len(x) for x in re.findall(r'`+', t)] + [0]) + 1
    d = '`'*n; pad = ' ' if (t.startswith('`') or t.endswith('`')) else ''
    return f'{d}{pad}{t}{pad}{d}'
def where(f, old):
    txt = open(os.path.join(base, f)).read(); L = txt.split('\n')
    ln = [i+1 for i,l in enumerate(L) if not l.lstrip().startswith('%') and old in l]
    return (ln[0] if ln else None), txt.count(old)
def parse(log):
    res = {}
    for l in open(log):
        m = re.match(r'(\w+) (\S+) (?:\S+ )?row (\d+) delta (-?\d+) undef (\[.*?\]) overfull (\[.*?\]) pages (\d+)', l)
        if m: res[m.group(1)] = (int(m.group(3)), int(m.group(4)), m.group(5), m.group(6), m.group(7))
        m = re.match(r'(base|ref) \((\d+)', l)
        if m: res[m.group(1)] = int(m.group(2))
    return res
F = parse(SC+'/runs/final8.log'); Dm = parse(SC+'/runs/dec8.log'); D5m = parse(SC+'/runs/dec5.log')
tierof = {p[0]: p[2] for p in pm.PATCHES}
nameof = {p[0]: p[1] for p in pm.PATCHES}
lines = []
A = lines.append
def percut():
    for pid, name, tier, edits in pm.PATCHES:
        row, d = F[pid][0], F[pid][1]
        A(f'#### {pid} · {name} · {tier} · measured {d:+d} rows (body end row {row}) · `patches/{pid}_{name}.patch`')
        A('')
        for k, e in enumerate(edits):
            f = e[1]
            if e[0] == 'block':
                ln, c = where(f, e[2]); new = e[4]
                old_disp = f'the span from {code(e[2])} through {code(e[3])} (lines {ln}–{ln+2}; it is split over three source lines)'
            elif '\n' in e[2]:
                ln, c = where(f, e[2].split('\n')[0]); new = e[3].replace('\n', ' ⏎ '); old_disp = code(e[2].replace('\n', ' ⏎ ')) + ' (⏎ marks a source line break; the middle line is blank)'
                new = new
            else:
                ln, c = where(f, e[2]); new = e[3]; old_disp = code(e[2])
            twin = '' if c == 1 else f'; the file also has {c-1} %-commented copy, wrap the live one'
            A(f'- **{pid}.{k+1}** `{f}` (line {ln}{twin}): {old_disp} → {code(new)}. *Why:* {reason(e[2])}.')
        A('')
def decides():
    for pid, name, tier, edits in dm.DECIDES:
        if pid in ('D3','D4','D7'): continue
        r = Dm.get(pid)
        A(f'#### DECIDE {pid} · {name} · measured {r[1]:+d} rows on top of the recommended set (body end row {r[0]}, {r[4]} PDF pages) · `patches/{pid}_{name}.patch` (applies after 00–21)' if r else f'#### {pid} · {name} · not measured')
        A('')
        for k, e in enumerate(edits):
            f = e[1]
            if e[0] == 'block':
                A(f'- `{f}`: the span from {code(e[2])} through {code(e[3])} → *(cut)*' + (' (it contains 01.2\'s span; wrap the whole sentence)' if pid=='D9' else '') + '.')
            else:
                kind = ' (direct edit, not wrappable: comment out the old line)' if e[0] == 'rd' else (' (inside the \\cutrep that 10.9 adds; edit its second argument)' if e[0]=='rx' else '')
                A(f'- `{f}`{kind}: {code(e[2])} → {code(e[3])}.')
        A(f'- Options: (a) take it ({r[1]:+d} rows, measured alone on top of 00–21); (b) keep. *Recommendation:* {DESC[pid][1]}.')
        A('')

SECT = {'00':'§5.2 (fix)','01':'Related Work','02':'§3 (opening, §3.1, §3.2)','03':'§4.1, §4.3','04':'§4.3.2, §4.3.3, §7','06':'§6.1, §6.2, §6.3','07':'§7','08':'Table 2 caption','10':'Intro','12':'§3 opening','13':'§4.3.3','14':'§5, §5.1, §5.2','15':'§6.1','16':'§6.2','17':'§6.4','18':'§7','19':'§2','20':'Related Work (+ one intro pointer)','21':'Figs. 8–9 captions','22':'Intro','23':'Fig. 2 caption','24':'§7','25':'Intro'}
import handtext
NP0 = int(sys.argv[1]); NPF = int(sys.argv[2])   # notes-hidden rows without preview: HEAD, and with the recommended set (should equal HEAD)
b = F['base']
rec = ['00','01','02','03','04','06','07','08','10','12','13','14','15','16','17','18','19','20','21']
fit = next(p for p in rec if F[p][0] <= 1276); buf = next(p for p in rec if F[p][0] <= 1266)
endrec = F['21'][0]
H = []
A = H.append
H.append('# Deep cut of the whole paper (ISCA-27)')
H.append('')
H.append("Agent deep-cut, 2026-11-16. Started at ISCA-27 `8587638`; HEAD moved six times during the run (`11a20dd` wrapped the main session's cuts in `\\cutsug`/`\\cutrep`; `ead06d8` un-wrapped the §6.1 CleanupSpec sentence; `6f492f7` was the orphan pass; `7df37ef` brought in the Fig. 3 grid, Table 1 v4 and Fig. 6 v2; `cc2e8b3` dropped the Fig. 1 caption cut and applied the Fig. 7 caption cut; `37d287c` swapped in the Fig. 3 grid v5), so every number, span and patch below is re-done on **`37d287c`**, HEAD at the end of the run, and already includes the new Fig. 3, Table 1 and Fig. 6. Paper untouched, no git writes.")
H.append('')
H.append("**Method.** The tree at `37d287c` was exported to a scratch directory, every note group hidden (switches (1)–(5)), and built with latexmk; rows are the ISCA `review` grid (58 per column, 116 per page; the 11-page limit ends at row 1276), read off the PDF at the last line of the Acknowledgments. As the main session asked, each cut is written as a `\\cutsug{old}` (pure cut) or `\\cutrep{old}{new}` (replacement) span, and every measurement has **switch (7) on** (preview with every green cut applied, the main session's and mine). The patches were applied cumulatively in the order below and the paper rebuilt after each one, so the per-patch numbers are the measured change at the body end, not estimates; freed space that falls into a float gap shows as 0 and pays off later in the sequence. DECIDE items were each applied alone on top of the recommended set and rebuilt. Every patch was checked with `patch -p1` in sequence on a fresh export of `37d287c` (all apply cleanly and reproduce the measured tree); 0 undefined references and 0 overfull boxes in every build.")
H.append('')
H.append('## Bottom line')
H.append('')
H.append(f"- **Overflow now (`37d287c`, notes hidden):** body + Acknowledgments end on page 12, row {NP0}: **{NP0-1276} rows over** row 1276. With switch (7) on (the main session's still-wrapped cuts: cut plan L1, L3, L4, F2, F3; L2 was dropped, L6 un-wrapped, L7 applied): row **{b}**, still **{b-1276} rows over**. A 10-row buffer needs row 1266 or less, i.e., **{b-1266} more rows**.")
H.append(f"- **Recommended set = patches 00–21 (the §5.2 fix and all Free and Low): row {b} → {endrec} ({endrec-b:+d} rows), {1276-endrec} rows under the limit**, so {1276-endrec-10} rows of slack beyond the 10-row buffer for the open fixes that add text. The paper fits, with the 10-row buffer, after patch {fit} (row {F[fit][0]}); stopping there (00–10) is the minimal option, but several later patches fix terms and repetitions the reviews flagged, so I recommend taking all of 00–21 (00 in any case). Patches 22–25 are optional ({F['25'][0]-endrec:+d} rows together): take 22 (it removes a put-down of AMuLeT) and 24 (canonical name); 23 and 25 are your call.")
H.append(f"- **No DECIDE item is needed to fit.** The largest, measured alone on top of 00–21: In/Out lines {Dm['D2'][1]:+d}, SNI sentence {Dm['D1'][1]:+d}, Generality paragraph {Dm['D10'][1]:+d}. My recommendation on every DECIDE is to keep the content (details below). Fig. 3, Table 1, Fig. 6 (new versions in HEAD) and Figs. 10–11 (being merged by another agent) are left out, as the main session asked.")
H.append(f"- **One- and two-word last lines.** With switch (7) on and 00–21 applied, no paragraph ends on a one- or two-word line; the shortest last lines left are three to five words ('the cache state.' in §5.1, '§4.8], is out of scope.' in §6.1, 'source the same way.' in UV3). With switch (7) off the green text prints and the layout is exactly HEAD's (row {NPF} with every span wrapped, row {NP0} without), so the cuts add no short line in that view; HEAD itself has '(§5.2).' (model.tex:17, fixed by 02.1 once applied), '105, 127].' (related.tex, fixed by 01.2) and 'straint:'/'violate' (the §4.1 list the main session wrapped as L4) in that view.")
H.append('')
H.append('### Cumulative table (notes hidden, switch (7) on, measured)')
H.append('')
H.append('| Patch | Section | Rows saved (measured) | Body-end row | Tier |')
H.append('|---|---|---|---|---|')
H.append(f'| HEAD `37d287c`, switch (7) off | | | {NP0} | |')
H.append(f"| main session's wrapped cuts (L1, L3, L4, F2, F3) | Intro, §2, §4, Table 2 | {b-NP0:+d} (wrapped; measured with switch (7)) | {b} | wrapped |")
for pid in rec + ['22','23','24','25']:
    H.append(f"| {pid} {nameof[pid]} | {SECT[pid]} | {F[pid][1]:+d} | {F[pid][0]} | {tierof[pid]}{' (optional)' if pid in ('22','23','24','25') else ''} |")
H.append('')
H.append(f"Free alone (00–08) ends at row {F['08'][0]} ({F['08'][0]-b:+d}); Fix + Free + Low (00–21) at row {endrec}.")
H.append('')
H.append('### DECIDE items, each measured alone on top of 00–21')
H.append('')
H.append('| Item | What | Rows (measured) | Recommendation |')
H.append('|---|---|---|---|')
DESC = {
'D1': ('SNI sentence in §2.2 + "weak SNI" in Fig. 1', 'keep: Fig. 1 names weak SNI, and the fit does not need it'),
'D2': ('the six In/Out lines (empty `\\stageio`)', 'keep: your device, and it carries the input-to-output chain Caroline asked for'),
'D3': ('Table 1 out, one sentence in its place, three pointers re-aimed at Fig. 2', 'keep: the vocabulary key Table 2, Fig. 7 and §4.3.1 point to'),
'D4': ('Fig. 6 (STT taint code) out', 'keep (your 2026-11-16 decision), and cite it from UV1'),
'D5': ('UV2: drop the second count', "keep both: the ReCon-specification count is the paper's own-specification method"),
'D6': ('keywords out', 'keep: the ISCA 2027 template has them'),
'D7': ('Fig. 11 out (+ three ref edits)', 'keep: it is the only view of the abstract-level timing claim'),
'D8': ('Related Work: Scam-V/SpecFuzz/LmTest sentence (old O-a)', "keep: LmTest is the comparison point of Caroline's Helium"),
'D9': ('Related Work: the list of other defenses', 'keep: your cite-generously directive, and the fit does not need it'),
'D10': ('§7 Generality paragraph', 'keep: it answers "does this work beyond gem5?"'),
'D11': ('caption skip 12pt → 6pt (old WS-1)', 'no: template change'),
'D12': ('float separation 15/12pt → 10/8pt (old WS-2)', 'no: template change'),
}
for pid, name, tier, edits in dm.DECIDES:
    if pid in ('D3','D4','D7'): continue
    d = DESC[pid]; r = Dm[pid]
    H.append(f'| {pid} | {d[0]} | {r[1]:+d} | {d[1]} |')
H.append('')
H.append(f"Table 1 out and Fig. 6 out (measured {D5m['D3'][1]:+d} and {D5m['D4'][1]:+d} on 6f492f7, before their new versions) are not in this list: the main session asked to leave the redrawn figures, and Figs. 10–11 (being merged; this also drops the Fig. 11 caption edit, the A-UV5 count edit and the old 'Fig. 11 out' option, which measured −23 on top of 00–21 at cc2e8b3), to their own work.")
H.append('')
FG = parse(SC+'/runs/fig6.log'); DF = parse(SC+'/runs/decfig.log')
H.append('## How to use this')
H.append('')
H.append("Each item below gives the file, the line in `37d287c` (a hint only), the **exact current text**, verbatim and unique among the live lines of its file (where a `%`-commented copy of the same text exists, it says so), and the replacement: `old` → `new`, where *(cut)* means `\\cutsug{old}` and anything else means `\\cutrep{old}{new}`. The patches in `~/trippel/simspect/paper_figures/deep_cut_20261116/patches/` do exactly this wrapping (not `%` comments, since the paper now shows cuts in green), numbered in the recommended order; apply them in sequence with `cd ~/trippel/ISCA-27 && patch -p1 < <patch>`. The `D*.patch` files apply after 00–21. The scripts that measured everything are in `~/trippel/simspect/paper_figures/deep_cut_20261116/tools/`.")
H.append('')
H.append('## The cuts, in recommended order')
H.append('')
percut()
H.append('## DECIDE items (real tradeoffs; each measured alone on top of 00–21)')
H.append('')
decides()
H.append(handtext.NOTCUT)
H.append(handtext.OBS)
H.append(handtext.STATUS)
open('/Users/annaeaton/trippel/simspect/paper_figures/caroline/reviews/2026-11-16_deep_cut.md', 'w').write('\n'.join(H) + '\n')
print('wrote', len(H))

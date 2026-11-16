"""Write comment_cleanup_log.md from comment_cleanup_targets.json (2026-11-11)."""
import json, os
D = os.path.expanduser('~/trippel/simspect/paper_figures/paper_audit_20261110')
t = json.load(open(f'{D}/scripts/comment_cleanup_targets.json'))
R = lambda a, b=None: range(a, (b or a) + 1)
reason = [
 ('abstract.tex', R(5, 11), 'commented old abstract (OBSOLETE in pa5; superseded by live abstract :3)'),
 ('abstract.tex', R(14), 'commented old abstract fragment (OBSOLETE)'),
 ('abstract.tex', R(18, 19), 'commented older abstracts (OBSOLETE)'),
 ('abstract.tex', R(22, 25), 'commented fragment + commented urgentnote on the bug count; RESOLVED: Anna counts six new bugs and abstract :3 states the scope'),
 ('intro.tex', [2, 5], 'commented outline heading (OBSOLETE)'),
 ('intro.tex', [14], 'commented todo to cite benchmarks; RESOLVED: the benchmark sentence cites kocher2018msvc and canella2019systematic'),
 ('intro.tex', [16], 'commented old framing paragraph with anna note; superseded by live :13 and :19'),
 ('intro.tex', [18], 'commented anna note (validation, not verification); RESOLVED: live :13 says correctness is validated through testing, not proven'),
 ('intro.tex', R(24, 28), 'commented outline bullets (OBSOLETE)'),
 ('intro.tex', [35], '\\anna note "drop the SNI discussion here"; RESOLVED: that paragraph is commented out (:36 kept as source text) and related.tex carries the SNI/contract notes'),
 ('intro.tex', [44, 45], 'commented old paragraph and commented \\notebr (OBSOLETE)'),
 ('intro.tex', [65], 'commented sentence superseded by live :67'),
 ('intro.tex', [79, 81], '"% NO" and the commented future-work paragraph Anna rejected (RESOLVED)'),
 ('background.tex', [37], 'commented bridge sentence (OBSOLETE)'),
 ('model.tex', R(16, 22), 'commented duplicate of the three-component list above, plus a dead todo (OBSOLETE)'),
 ('model.tex', [27, 28], 'auditnote on the Table I caption + its \\notebr; SUPERSEDED by the "Update to the note above (2026-11-09)" note, which restates the remaining differences with new proposed text'),
 ('model.tex', [32], 'commented figtodo to cite Fig. ddi-rf; RESOLVED: :31 cites Figure~\\ref{fig:ddi-rf}; the I3 vs i3 point is carried by the live :64 note'),
 ('model.tex', [38, 39], '\\urgentbr + VOCAB resolved/committed definition; SUPERSEDED by the next note ("replaces the definition just above")'),
 ('model.tex', [55], 'commented figtodo to reference Table execvocab; RESOLVED: the text references it (Figure vs Table wording is carried by the live :53 note)'),
 ('model.tex', [71, 72], 'auditnote on Fig. 3 non-invasive / selects-hooks + \\notebr; SUPERSEDED by the 2026-11-09 update note after it'),
 ('model.tex', [75, 76], 'auditnote on Fig. 3 bounded-exhaustive + \\notebr; SUPERSEDED by the 2026-11-09 update note after it'),
 ('model.tex', [79, 80], 'auditnote on Fig. 3 Stage 1b minimal/prototype + \\notebr; SUPERSEDED by the 2026-11-09 update note after it'),
 ('model.tex', [93], 'commented heading fragment (OBSOLETE)'),
 ('model.tex', [103], 'commented old STT leakage-function paragraph; superseded by the live Example contract list'),
 ('model.tex', R(105, 121), 'commented old subsection headings and placeholder example figures (OBSOLETE)'),
 ('pipeline.tex', [4, 5], '\\anna "delete commented i think" + the commented paragraph it refers to (RESOLVED per pa5)'),
 ('pipeline.tex', [16], 'commented old \\input of pipeline_full (the figure is input in model.tex)'),
 ('pipeline.tex', [17], '\\anna "define leakage backbones"; RESOLVED: :24 defines a leakage backbone'),
 ('pipeline.tex', [20, 41], 'commented old prose (OBSOLETE)'),
 ('pipeline.tex', [48, 49, 50], 'commented old minimality prose; superseded by live :47'),
 ('pipeline.tex', [93], 'commented old prose referencing a nonexistent fig:statetable (OBSOLETE)'),
 ('pipeline.tex', [125], 'commented VOCAB urgentnote on Fig. resolutiontiming; superseded by the live notes that follow (pa5: delete the commented :125)'),
 ('pipeline.tex', [168], 'commented old paragraph heading (OBSOLETE)'),
 ('pipeline.tex', [249], 'commented sentence on the data-obtained gate; its content is in the live load-transmitter item (store-to-load forward)'),
 ('pipeline.tex', [257], 'commented old clause; the divide-fault sentence is finished in the live item'),
 ('pipeline.tex', [269, 274], 'commented trailing fragments (OBSOLETE)'),
 ('results.tex', [1], 'breadcrumb that the knobs moved to pipeline.tex; RESOLVED: that subsection exists'),
 ('results.tex', [34], 'orphan \\urgentbr with no note'),
 ('results.tex', [65], 'dead marker comment "[new subsubsection]"'),
 ('results.tex', [85], 'comment saying the old table below is superseded (deleted with the table)'),
 ('results.tex', R(87, 122), '\\iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference'),
 ('results.tex', R(180, 182), 'stale labnote "InvisiSpec, SpecLFB and CleanupSpec results still to be inserted" + \\labbr/\\notebr; RESOLVED: those results are in Known Bugs Replicated (:39)'),
 ('results.tex', R(184, 187), '\\iffalse placeholder subsubsection sec:bug-loadmech (never referenced); superseded by Known Bugs Replicated'),
 ('related.tex', [94], 'trailing "% \\todo add other contract/SNI works" removed, line text kept; RESOLVED by the CITE notes (Spectector, Cheang et al., ...)'),
 ('related.tex', [211], 'trailing "% \\todo add Spectre litmus benchmark + fuzzing cites" removed, line text kept; RESOLVED by the CITE notes below it'),
]
def why(f, n):
    for ff, r, s in reason:
        if ff == f and n in r: return s
    raise SystemExit(f'no reason {f}:{n}')
L = ['# Comment cleanup log (ISCA-27, 2026-11-11)', '',
 'Authorization: Anna, "get rid of the no longer relevant comments". Only review comments, note macros, their paired break macros and dead commented / \\iffalse blocks were removed; no prose, caption, figure, \\input, label, citation or .bib was changed. Line numbers are in the pre-cleanup files, backed up at `paper_figures/paper_audit_20261110/backup_before_comment_cleanup_20261110_232839/`. Script: `scripts/comment_cleanup.py` (targets: `scripts/comment_cleanup_targets.json`; this log: `scripts/make_cleanup_log.py`). No git writes; the changes are uncommitted in ~/trippel/ISCA-27.', '',
 'Compile check (private temp copies, latexmk main.tex): backup 0 errors, 19 pages; cleaned 0 errors, 19 pages; same warnings (only the pre-existing undefined \\ref{stage1}). A word-level diff of the rendered text shows only the removed notes (three [Anna:] notes, one superseded [URGENT] VOCAB note, the stale lab note) plus line-break reflow.', '',
 '## Deleted', '', '| file | orig line | first ~100 chars | reason |', '|---|---|---|---|']
for f, n, s in t:
    s = (s.strip() or '(blank line inside deleted block)').replace('|', '/').replace('`', "'")
    L.append(f'| {f} | {n} | `{s[:100]}` | {why(f, n)} |')
L += ['', '## Kept although pa5 marked them deletable', '', '| file:line | item | why kept |', '|---|---|---|',
 '| intro.tex:11 | `% not cycle accurate` | pa5 says delete or make it a Discussion point; that choice is Anna\'s |',
 '| intro.tex:36 | commented AMuLeT/SNI paragraph | substantive text not yet carried into the Related Work prose; keep as source until VI is written |',
 '| model.tex:60 | auditnote: protection set is not commit-based | the 2026-11-09 note after it is conditional on STT_6_u (H5 blocked), so :60 still applies if STT_6 is the evaluated model |',
 '| results.tex:2-5, :52, :58, :69 | reorganization breadcrumbs | pa5: obsolete only once the reorg is accepted; :52/:58/:69 point at commented detail that still exists |',
 '| results.tex:10-27 | \\iffalse results to-do list | still lists open items (coverage counts, cost) that pa5 new-suggestion 5 says are missing |',
 '| results.tex:42-44, :124-178, :189-204, :261-266 | commented detail sections, closing list, \\anna note | pa5: delete only after the merged PROPOSED TEXT notes are pasted; not pasted yet |',
 '| results.tex:47 | urgentnote HOW THIS SECTION IS ORGANIZED NOW | still tells Anna how to accept the per-bug notes; reorg not yet accepted |',
 '| results.tex:206-213 | \\iffalse Test targeting + \\anna{fixing this still} | OPEN: only source for the 17% claim |',
 '| results.tex:218-248 | \\iffalse timing sweeps and old detection-efficiency section | marked re-run-or-drop and "kept hidden" by Anna; the drop decision is hers |',
 '| results.tex:216, :236, :251 | `% figure ... moved to pendingfigures.tex` | live pointers; not marked by pa5 |',
 '| pipeline.tex:236-237 | commented \\input{xmitcriteria} + figtodo | an \\input line (out of scope) and Anna\'s note says file kept, content under review |',
 '| pipeline.tex:218 | auditnote: checker figure now in scope | pa5 RESOLVED, but its proposed re-caption is not done |',
 '| related.tex:68, :119, :141, :173, :202, :222, :231 + commented CUT blocks | CUT LISTs | OPEN until Related Work is prose |',
 '| related.tex:189 | `% \\todo{tighten/complete the defense citations}` | still open (blocker 2) |',
 '| main.tex:86-88 | template acks | prose, not a comment; OPEN blocker for Anna |']
open(f'{D}/comment_cleanup_log.md', 'w').write('\n'.join(L) + '\n')
print(len(t), 'rows')

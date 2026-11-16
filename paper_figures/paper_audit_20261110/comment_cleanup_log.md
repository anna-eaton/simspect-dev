# Comment cleanup log (ISCA-27, 2026-11-11)

Authorization: Anna, "get rid of the no longer relevant comments". Only review comments, note macros, their paired break macros and dead commented / \iffalse blocks were removed; no prose, caption, figure, \input, label, citation or .bib was changed. Line numbers are in the pre-cleanup files, backed up at `paper_figures/paper_audit_20261110/backup_before_comment_cleanup_20261110_232839/`. Script: `scripts/comment_cleanup.py` (targets: `scripts/comment_cleanup_targets.json`; this log: `scripts/make_cleanup_log.py`). No git writes; the changes are uncommitted in ~/trippel/ISCA-27.

Compile check (private temp copies, latexmk main.tex): backup 0 errors, 19 pages; cleaned 0 errors, 19 pages; same warnings (only the pre-existing undefined \ref{stage1}). A word-level diff of the rendered text shows only the removed notes (three [Anna:] notes, one superseded [URGENT] VOCAB note, the stale lab note) plus line-break reflow.

## Deleted

| file | orig line | first ~100 chars | reason |
|---|---|---|---|
| abstract.tex | 5 | `% We propose \textbf{SimSpect}, a rigorous, targeted, and automated approach for validating early-st` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 6 | `% Applying SimSpect to all accessible simulator prototypes of state-of-the-art defenses, we replicat` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 7 | `% (1) STT mistakenly fails to taint one register,` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 8 | `% ReCon's underlying implementation of STT (2) skips a taint check on store-to-load forwarding and (` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 9 | `% SpecLFB (4) misimplements its ROB walk order and (5) fails to protect under the shadow of a jmp in` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 10 | `% (6) there is a visibility-point/squash timing race shared by STT and SPT.` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 11 | `% Compared to prior work, SimSpect decreases the number of tests needed to find known bugs on averag` | commented old abstract (OBSOLETE in pa5; superseded by live abstract :3) |
| abstract.tex | 14 | `% find a bug in STT where it fails to taint an FPR, uncover a previously unknown visibility-point/sq` | commented old abstract fragment (OBSOLETE) |
| abstract.tex | 18 | `% Hardware side-channel attacks pass secrets to instructions with data-dependent optimizations that` | commented older abstracts (OBSOLETE) |
| abstract.tex | 19 | `% Many hardware defenses have been proposed to mitigate the dangers posed by side-channel attacks, p` | commented older abstracts (OBSOLETE) |
| abstract.tex | 22 | `% security bugs \anna{that violate their defense's proposed security guarantees} as well as \textit{` | commented fragment + commented urgentnote on the bug count; RESOLVED: Anna counts six new bugs and abstract :3 states the scope |
| abstract.tex | 23 | `% \urgentbr` | commented fragment + commented urgentnote on the bug count; RESOLVED: Anna counts six new bugs and abstract :3 states the scope |
| abstract.tex | 24 | `% \urgentnote{''All known security bugs'' needs its scope and count. AMuLeT reports nine bugs on the` | commented fragment + commented urgentnote on the bug count; RESOLVED: Anna counts six new bugs and abstract :3 states the scope |
| abstract.tex | 25 | `% \notebr` | commented fragment + commented urgentnote on the bug count; RESOLVED: Anna counts six new bugs and abstract :3 states the scope |
| intro.tex | 2 | `% \textit{What is a hardware side channel, why are they bad, what is spectre in particular}` | commented outline heading (OBSOLETE) |
| intro.tex | 5 | `% \textit{HSCDs exist for HSCAs }` | commented outline heading (OBSOLETE) |
| intro.tex | 14 | `% \todo{cite the spectre benchmarks}` | commented todo to cite benchmarks; RESOLVED: the benchmark sentence cites kocher2018msvc and canella2019systematic |
| intro.tex | 16 | `% First, there is a lack of formal specification to describe the security guarantees a particular de` | commented old framing paragraph with anna note; superseded by live :13 and :19 |
| intro.tex | 18 | `% \anna{it's important to note this is early in the design process => validation not verification, w` | commented anna note (validation, not verification); RESOLVED: live :13 says correctness is validated through testing, not proven |
| intro.tex | 24 | `% When generating a set of litmus tests to validate some` | commented outline bullets (OBSOLETE) |
| intro.tex | 25 | `% - we need litmus test suite` | commented outline bullets (OBSOLETE) |
| intro.tex | 26 | `% - security different than functional correctness, because edge case could be very niche and that i` | commented outline bullets (OBSOLETE) |
| intro.tex | 27 | `% - people have done this with randomized test generation, but it does not target potentially violat` | commented outline bullets (OBSOLETE) |
| intro.tex | 28 | `% - people have benchmarks of tests that trigger spectre attacks, but they are not specialized to th` | commented outline bullets (OBSOLETE) |
| intro.tex | 35 | `\anna{I think maybe drop the security property vs leakage predicate discussion here, and pick that u` | \anna note "drop the SNI discussion here"; RESOLVED: that paragraph is commented out (:36 kept as source text) and related.tex carries the SNI/contract notes |
| intro.tex | 44 | `% \toolname enables validation of the hardware implementation Spectre defense against a defense secu` | commented old paragraph and commented \notebr (OBSOLETE) |
| intro.tex | 45 | `% \notebr` | commented old paragraph and commented \notebr (OBSOLETE) |
| intro.tex | 65 | `% We have run the \toolname{} testing pipeline with an instruction bound of six on the gem5 implemen` | commented sentence superseded by live :67 |
| intro.tex | 79 | `% NO` | "% NO" and the commented future-work paragraph Anna rejected (RESOLVED) |
| intro.tex | 81 | `% Because the leakage predicate is formal, it can be related to the end-to-end properties. A bounded` | "% NO" and the commented future-work paragraph Anna rejected (RESOLVED) |
| background.tex | 37 | `% A similar such axiomatic definition of side channel leakage would allow generation of a similar te` | commented bridge sentence (OBSOLETE) |
| model.tex | 16 | `% \textbf{1. Leakage contract}` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 17 | `% A leakage contract is the set of pairs of \textit{transmitters} (instructions that leak one or mor` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 18 | `% \textbf{2. Execution contract}` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 19 | `% An execution contract characterizes what speculative control- and data-flow is allowed on the micr` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 20 | `% \textbf{3. Protection set}` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 21 | `% A protection set is the set of architectural state (memory and registers) that the defense promise` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 22 | `% todo these components sufficient for now etc etc` | commented duplicate of the three-component list above, plus a dead todo (OBSOLETE) |
| model.tex | 27 | `\auditnote{fact}{fact}{\textbf{About the caption of Table~\ref{tab:execvocab}:} The vocabulary is sh` | auditnote on the Table I caption + its \notebr; SUPERSEDED by the "Update to the note above (2026-11-09)" note, which restates the remaining differences with new proposed text |
| model.tex | 28 | `\notebr` | auditnote on the Table I caption + its \notebr; SUPERSEDED by the "Update to the note above (2026-11-09)" note, which restates the remaining differences with new proposed text |
| model.tex | 32 | `% \figtodo{cite the basic execution-graph example, Fig.~\ref{fig:ddi-rf} (the dataflow figure, redra` | commented figtodo to cite Fig. ddi-rf; RESOLVED: :31 cites Figure~\ref{fig:ddi-rf}; the I3 vs i3 point is carried by the live :64 note |
| model.tex | 38 | `\urgentbr` | \urgentbr + VOCAB resolved/committed definition; SUPERSEDED by the next note ("replaces the definition just above") |
| model.tex | 39 | `\urgentnote{\textbf{VOCAB}: \textbf{ADD DEFINITION} (new text, insert here): \emph{resolved} (a bran` | \urgentbr + VOCAB resolved/committed definition; SUPERSEDED by the next note ("replaces the definition just above") |
| model.tex | 55 | `% \figtodo{new vocabulary table, Table~\ref{tab:execvocab}: reference it here; the prose above can s` | commented figtodo to reference Table execvocab; RESOLVED: the text references it (Figure vs Table wording is carried by the live :53 note) |
| model.tex | 71 | `\auditnote{fig}{figure}{\textbf{About the caption of Fig.~\ref{fig:pipeline}:} 'Non-invasive' (also` | auditnote on Fig. 3 non-invasive / selects-hooks + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 72 | `\notebr` | auditnote on Fig. 3 non-invasive / selects-hooks + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 75 | `\auditnote{fig}{figure, high}{\textbf{About the caption of Fig.~\ref{fig:pipeline}:} No evaluated en` | auditnote on Fig. 3 bounded-exhaustive + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 76 | `\notebr` | auditnote on Fig. 3 bounded-exhaustive + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 79 | `\auditnote{fig}{figure, high}{\textbf{About the caption of Fig.~\ref{fig:pipeline}:} The caption cal` | auditnote on Fig. 3 Stage 1b minimal/prototype + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 80 | `\notebr` | auditnote on Fig. 3 Stage 1b minimal/prototype + \notebr; SUPERSEDED by the 2026-11-09 update note after it |
| model.tex | 93 | `% scope of the types of defenses we can represent` | commented heading fragment (OBSOLETE) |
| model.tex | 103 | `% STT's leakage function is (load, load address), (branch, input register), and (reg-op transmitter,` | commented old STT leakage-function paragraph; superseded by the live Example contract list |
| model.tex | 105 | `% \subsection{Execution contracts in practice}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 106 | `% \subsection{Scope of defenses}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 107 | `% \begin{wrapfigure}{r}{.5\textwidth}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 108 | `%   \begin{center}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 109 | `%     \includegraphics[width=.5\textwidth]{images/examplefigure.png}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 110 | `%   \end{center}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 111 | `%   \caption{We generate a test from STT using our pipeline.}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 112 | `(blank line inside deleted block)` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 113 | `%   \label{fig:pipeline}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 114 | `(blank line inside deleted block)` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 115 | `% \end{wrapfigure}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 116 | `% \begin{figure}[h]` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 117 | `%   \centering` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 118 | `%   \includegraphics[width=0.4\textwidth]{images/examplefigure.png}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 119 | `%   \caption{We generate a test from STT using our pipeline.}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 120 | `%   \label{fig:pipeline}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| model.tex | 121 | `% \end{figure}` | commented old subsection headings and placeholder example figures (OBSOLETE) |
| pipeline.tex | 4 | `\anna{delete commented i think:}` | \anna "delete commented i think" + the commented paragraph it refers to (RESOLVED per pa5) |
| pipeline.tex | 5 | `% We designate the design dimensions we identify as either \textbf{1. comprehensively enumerated, 2.` | \anna "delete commented i think" + the commented paragraph it refers to (RESOLVED per pa5) |
| pipeline.tex | 16 | `% \input{tikz/pipeline_full}` | commented old \input of pipeline_full (the figure is input in model.tex) |
| pipeline.tex | 17 | `\anna{define leakage backbones}` | \anna "define leakage backbones"; RESOLVED: :24 defines a leakage backbone |
| pipeline.tex | 20 | `% Once we have a formal model of a defense's security guarantee, we can use this specification as in` | commented old prose (OBSOLETE) |
| pipeline.tex | 41 | `% The model describes a space of executions partitioned by the leakage predicate, which allows us to` | commented old prose (OBSOLETE) |
| pipeline.tex | 48 | `% and make claims about fundamental bounds on leakage backbone size and quntity` | commented old minimality prose; superseded by live :47 |
| pipeline.tex | 49 | `% . We want to group executions that exhibit the same form of leakage, to allow us to reason about t` | commented old minimality prose; superseded by live :47 |
| pipeline.tex | 50 | `% For this reason we follow MCM work~\cite{lustig} to define a minimality criterion restricts synthe` | commented old minimality prose; superseded by live :47 |
| pipeline.tex | 93 | `% Figure~\ref{fig:statetable} shows the types of instructions and state enumerated in each phase. To` | commented old prose referencing a nonexistent fig:statetable (OBSOLETE) |
| pipeline.tex | 125 | `% \urgentnote{\textbf{VOCAB}: In Fig.~\ref{fig:resolutiontiming} the graph is a violation under both` | commented VOCAB urgentnote on Fig. resolutiontiming; superseded by the live notes that follow (pa5: delete the commented :125) |
| pipeline.tex | 168 | `% \paragraph{Directives passed from concretization.}` | commented old paragraph heading (OBSOLETE) |
| pipeline.tex | 249 | `% This data-obtained gate is essential: store-to-load forwarding lets a speculative load complete` | commented sentence on the data-obtained gate; its content is in the live load-transmitter item (store-to-load forward) |
| pipeline.tex | 257 | `% ; a speculative divide fault is promoted to a leak, which is what makes a guard such as the \tex` | commented old clause; the divide-fault sentence is finished in the live item |
| pipeline.tex | 269 | `% , and (for a \emph{demonstrable} leak rather than a dataflow signal) optionally with a data-taint` | commented trailing fragments (OBSOLETE) |
| pipeline.tex | 274 | `% --- is fixed, while every knob that \emph{probes} it, from the window stalls to the micro-architec` | commented trailing fragments (OBSOLETE) |
| results.tex | 1 | `% (leakage-prompting knobs: written up as a subsection in the Test Generation Pipeline section, sect` | breadcrumb that the knobs moved to pipeline.tex; RESOLVED: that subsection exists |
| results.tex | 34 | `\urgentbr` | orphan \urgentbr with no note |
| results.tex | 65 | `% [new subsubsection]. (2026-11-10: marker moved to a comment)` | dead marker comment "[new subsubsection]" |
| results.tex | 85 | `% The older table below, under \iffalse, is superseded by bugtable_v3_8pt.` | comment saying the old table below is superseded (deleted with the table) |
| results.tex | 87 | `\iffalse` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 88 | `\begin{table*}[t]\centering\small` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 89 | `\setlength{\tabcolsep}{5pt}\renewcommand{\arraystretch}{1.2}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 90 | `\begin{tabular}{@{}p{2.3cm}p{4.7cm}p{3.0cm}p{3.1cm}cl@{}}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 91 | `\toprule` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 92 | `\textbf{Defense} & \textbf{Bug} & \textbf{First known from} & \textbf{Found by} & \textbf{In scope?}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 93 | `\midrule` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 94 | `\multicolumn{6}{@{}l}{\textbf{STT}}\\` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 95 | `& Visibility-point\,$\leftrightarrow$\,squash race (load channel) & This work & \textcolor{cclean}{\` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 96 | `& Pending-squash race --- secret-dependent squash signal & N.~Mosier (\texttt{cwfletcher/stt}\,@18e3` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 97 | `& Tainted spec \emph{store} $\to$ D-TLB entry (KV3) & DOLMA; via AMuLeT & \textcolor{camulet}{AMuLeT` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 98 | `\addlinespace[2pt]` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 99 | `\multicolumn{6}{@{}l}{\textbf{SPT-Fence}}\\` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 100 | `& Same visibility-point\,$\leftrightarrow$\,squash race (= STT) & This work & \textcolor{cclean}{\to` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 101 | `\addlinespace[2pt]` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 102 | `\multicolumn{6}{@{}l}{\textcolor{gray}{\textbf{InvisiSpec \& CleanupSpec} \,{\footnotesize\itshape c` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 103 | `& \textcolor{gray}{UV1, UV2, KV1 --- L1D eviction / MSHR contention / L1I spec-fetch} & \textcolor{g` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 104 | `& \textcolor{gray}{UV3--UV5 --- post-squash L1D residue / over-clean evicts non-spec line} & \textco` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 105 | `\addlinespace[2pt]` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 106 | `\multicolumn{6}{@{}l}{\textbf{SpecLFB}}\\` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 107 | `& First speculative load left unprotected (UV6) & AMuLeT & \textbf{Both} (\textcolor{camulet}{AMuLeT` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 108 | `\bottomrule` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 109 | `\end{tabular}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 110 | `\caption{Speculative-execution defense bugs, grouped by defense: where each was first` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 111 | `known, which tool exhibits it (\textcolor{cclean}{\toolname{}} / \textcolor{camulet}{AMuLeT}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 112 | `/ Both / neither), whether it falls in \toolname{}'s leakage model, and the verdict. The` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 113 | `pending-squash race (a secret-dependent squash signal, fixed upstream by Mosier) is a real STT bug` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 114 | `that \emph{neither} automated tool found. $^{1}$not a bug: a tainted-store$\to$TLB leak is consisten` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 115 | `specification, which does not recognize store transmitters, so it is outside the property STT claims` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 116 | `enforce. The visibility-point\,$\leftrightarrow$\,squash race is a genuine logic bug: STT and SPT` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 117 | `release the transmitter's protection on the branch-resolution signal but do \emph{not} wait for the` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 118 | `squash to \emph{complete}, so the wrong-path transmitter reaches the cache in the gap before it is` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 119 | `killed.}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 120 | `\label{tab:bugs}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 121 | `\end{table*}` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 122 | `\fi` | \iffalse old bug table (tab:bugs), explicitly superseded by bugtable_v3/v4; no live reference |
| results.tex | 180 | `\labbr` | stale labnote "InvisiSpec, SpecLFB and CleanupSpec results still to be inserted" + \labbr/\notebr; RESOLVED: those results are in Known Bugs Replicated (:39) |
| results.tex | 181 | `\labnote{InvisiSpec, SpecLFB and CleanupSpec results still to be inserted here.}` | stale labnote "InvisiSpec, SpecLFB and CleanupSpec results still to be inserted" + \labbr/\notebr; RESOLVED: those results are in Known Bugs Replicated (:39) |
| results.tex | 182 | `\notebr` | stale labnote "InvisiSpec, SpecLFB and CleanupSpec results still to be inserted" + \labbr/\notebr; RESOLVED: those results are in Known Bugs Replicated (:39) |
| results.tex | 184 | `\iffalse % LAB-REVIEW CUT (2026-11-03): placeholder subsubsection, not written yet` | \iffalse placeholder subsubsection sec:bug-loadmech (never referenced); superseded by Known Bugs Replicated |
| results.tex | 185 | `\subsubsection{Defenses with their own load transmission mechanisms}\label{sec:bug-loadmech}` | \iffalse placeholder subsubsection sec:bug-loadmech (never referenced); superseded by Known Bugs Replicated |
| results.tex | 186 | `\reviewtag{[TODO placeholder: InvisiSpec, SpecLFB (UV6) and CleanupSpec hide or undo a speculative l` | \iffalse placeholder subsubsection sec:bug-loadmech (never referenced); superseded by Known Bugs Replicated |
| results.tex | 187 | `\fi` | \iffalse placeholder subsubsection sec:bug-loadmech (never referenced); superseded by Known Bugs Replicated |
| related.tex | 94 | `% \todo{add other contract/SNI works}` | trailing "% \todo add other contract/SNI works" removed, line text kept; RESOLVED by the CITE notes (Spectector, Cheang et al., ...) |
| related.tex | 211 | `% \todo{add Spectre litmus benchmark + fuzzing cites}` | trailing "% \todo add Spectre litmus benchmark + fuzzing cites" removed, line text kept; RESOLVED by the CITE notes below it |

## Kept although pa5 marked them deletable

| file:line | item | why kept |
|---|---|---|
| intro.tex:11 | `% not cycle accurate` | pa5 says delete or make it a Discussion point; that choice is Anna's |
| intro.tex:36 | commented AMuLeT/SNI paragraph | substantive text not yet carried into the Related Work prose; keep as source until VI is written |
| model.tex:60 | auditnote: protection set is not commit-based | the 2026-11-09 note after it is conditional on STT_6_u (H5 blocked), so :60 still applies if STT_6 is the evaluated model |
| results.tex:2-5, :52, :58, :69 | reorganization breadcrumbs | pa5: obsolete only once the reorg is accepted; :52/:58/:69 point at commented detail that still exists |
| results.tex:10-27 | \iffalse results to-do list | still lists open items (coverage counts, cost) that pa5 new-suggestion 5 says are missing |
| results.tex:42-44, :124-178, :189-204, :261-266 | commented detail sections, closing list, \anna note | pa5: delete only after the merged PROPOSED TEXT notes are pasted; not pasted yet |
| results.tex:47 | urgentnote HOW THIS SECTION IS ORGANIZED NOW | still tells Anna how to accept the per-bug notes; reorg not yet accepted |
| results.tex:206-213 | \iffalse Test targeting + \anna{fixing this still} | OPEN: only source for the 17% claim |
| results.tex:218-248 | \iffalse timing sweeps and old detection-efficiency section | marked re-run-or-drop and "kept hidden" by Anna; the drop decision is hers |
| results.tex:216, :236, :251 | `% figure ... moved to pendingfigures.tex` | live pointers; not marked by pa5 |
| pipeline.tex:236-237 | commented \input{xmitcriteria} + figtodo | an \input line (out of scope) and Anna's note says file kept, content under review |
| pipeline.tex:218 | auditnote: checker figure now in scope | pa5 RESOLVED, but its proposed re-caption is not done |
| related.tex:68, :119, :141, :173, :202, :222, :231 + commented CUT blocks | CUT LISTs | OPEN until Related Work is prose |
| related.tex:189 | `% \todo{tighten/complete the defense citations}` | still open (blocker 2) |
| main.tex:86-88 | template acks | prose, not a comment; OPEN blocker for Anna |

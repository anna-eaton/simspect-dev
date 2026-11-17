# DECIDE items on 11a20dd, each measured alone on top of the recommended set (preview on). 'rd' = direct edit (not wrappable).
I = 'sections/intro.tex'; B = 'sections/background.tex'; M = 'sections/model.tex'; P = 'sections/pipeline.tex'
R = 'sections/results.tex'; D = 'sections/discussion.tex'; W = 'sections/related.tex'
T = lambda n: 'tikz/' + n + '.tex'
DECIDES = [
('D1', 'bg_sni', 'DECIDE', [
  ('r', B, r'Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant weak SNI~\cite[Def.~4]{guarnieri2021contracts} are the matching program properties: a program is weakly SNI if its observations under a contract reveal nothing beyond its \contract{ARCH-SEQ} observations, so a CPU that upholds \contract{ARCH-SEQ} makes every program weakly SNI.', ''),
  ('r', T('intro_threelayer_v9'), r', which guarantees weak speculative non-interference', ''),
]),
('D2', 'inout_lines', 'DECIDE', [
  ('rd', M, r'\providecommand{\stageio}[2]{\par\noindent{\itshape\textbf{Input:}~#1\enspace\textbf{Output:}~#2\par}\nopagebreak\smallskip}', r'\providecommand{\stageio}[2]{}'),
]),
('D3', 'drop_table1', 'DECIDE', [
  ('rd', M, r'\input{tikz/execvocab_v3_8pt}', ''),
  ('r', M, r'Table~\ref{tab:execvocab} lists the execution graph vocabulary. Instructions are totally ordered',
           r'Instructions are loads, stores, branches, and ALU ops (\texttt{Other}); a branch or ALU op whose kind ends in \texttt{\_n} is never in a leakage contract. They are totally ordered'),
  ('r', P, r'(Table~\ref{tab:execvocab})', r'(\S\ref{sec:execution-syntax})'),
  ('rx', T('instrtable_v2_short'), r'}{(notation of Table~\ref{tab:execvocab})}', r'}{(notation of Fig.~\ref{fig:ddi-rf})}'),
  ('r', T('reconstl_v5_8pt'), r'(notation of Table~\ref{tab:execvocab})', r'(notation of Fig.~\ref{fig:ddi-rf})'),
]),
('D4', 'drop_fig6_xmm4_code', 'DECIDE', [
  ('rd', R, r'\input{tikz/stt_xmm4_code_8pt}', ''),
]),
('D5', 'uv2_one_count', 'DECIDE', [
  ('r', R, r", and so do 2{,}848 of the 60{,}342 tests of ReCon's own specification", ''),
]),
('D6', 'keywords', 'DECIDE', [
  ('rd', 'main.tex', r'\keywords{hardware security, side-channel attacks, Spectre defenses, security litmus tests, formal specification, microarchitectural simulation}', ''),
]),
('D7', 'drop_fig11_timing', 'DECIDE', [
  ('rd', R, r'\input{tikz/timedet_bars_v8_8pt}', ''),
  ('r', R, r'Figs.~\ref{fig:firstdetv2} and~\ref{fig:timedet}', r'Fig.~\ref{fig:firstdetv2}'),
  ('r', R, r' faster (Fig.~\ref{fig:timedet})', r' faster'),
  ('rx', I, r'faster (Fig.~\ref{fig:timedet}).}', r'faster (\S\ref{sec:timing}).}'),
]),
('D8', 'related_scamv_sentence', 'DECIDE', [
  ('r', W, r'Scam-V~\cite{nemati2020scamv} validates side-channel models against hardware, and software tools test programs for Spectre gadgets~\cite{oleksenko2020specfuzz} or against leakage models~\cite{barthe2024lmtest}. ', ''),
]),
('D9', 'related_defense_list', 'DECIDE', [
  ('block', W, r' Beyond those in \S\ref{sec:introduction}', r'zhao2020invarspec,hajiabadi2024levioso}.', ''),
]),
('D10', 'discussion_generality', 'DECIDE', [
  ('block', D, r'\noindent\textbf{Generality.}', r'harness directive.', ''),
]),
('D11', 'ws1_caption_skip', 'DECIDE', [
  ('rd', 'main.tex', r'\begin{document}', r'\begin{document}\captionsetup{skip=6pt}'),
]),
('D12', 'ws2_float_sep', 'DECIDE', [
  ('rd', 'main.tex', r'\begin{document}', r'\begin{document}\setlength{\textfloatsep}{10pt plus 4pt minus 3pt}\setlength{\floatsep}{8pt plus 4pt minus 2pt}'),
]),
]

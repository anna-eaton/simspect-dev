# DECIDE (real tradeoff) patches, each measured alone on top of the recommended Free + Low state.
I = 'sections/intro.tex'; B = 'sections/background.tex'; M = 'sections/model.tex'; P = 'sections/pipeline.tex'
R = 'sections/results.tex'; D = 'sections/discussion.tex'; W = 'sections/related.tex'
T = lambda n: 'tikz/' + n + '.tex'
DECIDES = [
('D01', 'intro_overview_list', 'DECIDE', [
  ('r', I, r" \toolname{} provides (1) a \textbf{defense specification language} for formalizing a hardware Spectre defense's natural-language security guarantee, (2)", ''),
  ('r', I, r'a \textbf{synthesizer} that uses such a specification to generate a systematic set of \emph{security litmus tests}~\cite{checkmate}, each a program paired with a \emph{target execution} that exhibits leakage the defense forbids,', ''),
  ('r', I, r'and (3) an \textbf{executor} that steers each test toward its target execution on a simulated Spectre defense in gem5 and checks whether the defense prevents that leakage.', ''),
  ('r', I, r'and concretizes each graph into security litmus tests: pairs of x86 programs', r'and concretizes each graph into \emph{security litmus tests}~\cite{checkmate}: pairs of x86 programs'),
]),
('D02', 'bg_adversary_paragraph', 'DECIDE', [
  ('r', B, r'An adversary model observes only microarchitectural state, so it cannot tell which instruction changed it: a line installed by a speculative store looks the same as one installed by a speculative load. A guarantee that holds for some transmitters but not others, such as STT\'s, which excludes stores~\cite[\S 7.3]{yu2019stt}, therefore matches no contract built from these modes, and testing against one can report leaks outside the guarantee (\S\ref{sec:known-bugs}).'.replace("\\'", "'"), ''),
]),
('D03', 'bg_sni', 'DECIDE', [
  ('r', B, r'Speculative non-interference (SNI)~\cite{guarnieri2020spectector} and its variant weak SNI~\cite[Def.~4]{guarnieri2021contracts} are the matching program properties: a program is weakly SNI if its observations under a contract reveal nothing beyond its \contract{ARCH-SEQ} observations, so a CPU that upholds \contract{ARCH-SEQ} makes every program weakly SNI.', ''),
  ('r', T('intro_threelayer_v9'), r', which guarantees weak speculative non-interference}~\cite{guarnieri2021contracts}', r'}~\cite{guarnieri2021contracts}'),
]),
('D04', 'inout_lines', 'DECIDE', [
  ('r', M, r'\providecommand{\stageio}[2]{\par\noindent{\itshape\textbf{Input:}~#1\enspace\textbf{Output:}~#2\par}\nopagebreak\smallskip}', r'\providecommand{\stageio}[2]{}'),
]),
('D05', 'drop_table1', 'DECIDE', [
  ('r', M, r'\input{tikz/execvocab_v3_8pt}', ''),
  ('r', M, r'Table~\ref{tab:execvocab} lists the execution graph vocabulary. Instructions are totally ordered',
           r'Instructions are loads, stores, branches, and ALU ops (\texttt{Other}); a branch or ALU op whose kind ends in \texttt{\_n} is never in a leakage contract. They are totally ordered'),
  ('r', P, r'(Table~\ref{tab:execvocab})', r'(\S\ref{sec:execution-syntax})'),
  ('r', T('instrtable_v2_short'), r'(notation of Table~\ref{tab:execvocab})', r'(notation of Fig.~\ref{fig:ddi-rf})'),
  ('r', T('reconstl_v5_8pt'), r'(notation of Table~\ref{tab:execvocab})', r'(notation of Fig.~\ref{fig:ddi-rf})'),
]),
('D06', 'drop_fig6_xmm4_code', 'DECIDE', [
  ('r', R, r'\input{tikz/stt_xmm4_code_8pt}', ''),
]),
('D07', 'uv2_one_count', 'DECIDE', [
  ('r', R, r", and so do 2{,}848 of the 60{,}342 tests of ReCon's own specification", ''),
]),
('D08', 'keywords', 'DECIDE', [
  ('r', 'main.tex', r'\keywords{hardware security, side-channel attacks, Spectre defenses, security litmus tests, formal specification, microarchitectural simulation}', ''),
]),
('D09', 'drop_fig11_timing', 'DECIDE', [
  ('r', R, r'\input{tikz/timedet_bars_v8_8pt}', ''),
  ('r', R, r'error bars in Figs.~\ref{fig:firstdetv2} and~\ref{fig:timedet} are', r'error bars in Fig.~\ref{fig:firstdetv2} are'),
  ('r', R, r' faster (Fig.~\ref{fig:timedet})', r' faster'),
  ('r', I, r'faster (Fig.~\ref{fig:timedet}).', r'faster (\S\ref{sec:timing}).'),
]),
('D10', 'related_scamv_sentence', 'DECIDE', [
  ('r', W, r'Scam-V~\cite{nemati2020scamv} validates side-channel models against hardware, and software tools test programs for Spectre gadgets~\cite{oleksenko2020specfuzz} or against leakage models~\cite{barthe2024lmtest}. ', ''),
]),
('D11', 'related_defense_list', 'DECIDE', [
  ('r', W, r' Beyond those in \S\ref{sec:introduction}, some address only cache-based channels~\cite{taram2019csf,li2019conditional,kiriansky2018dawg} or only some speculation primitives~\cite{koruyeh2020speccfi}; others rely on source-level secrecy annotations~\cite{yu2019oisa,daniel2023prospect,schwarz2020context,fustos2019spectreguard} or require memory-layout changes~\cite{green2023safebet,kim2024perspective}; and security-preserving optimizations speed up existing defenses~\cite{tran2020clearing,zhao2020invarspec,hajiabadi2024levioso}.', ''),
]),
('D12', 'spec_forward_sentence', 'DECIDE', [
  ('r', M, r"The leakage predicate is the synthesizer's defense-specific input (\S\ref{sec:synthesizer}), and the transmission criterion the Inspector's (\S\ref{sec:transmission-requirement}).", ''),
]),
('D13', 'discussion_generality', 'DECIDE', [
  ('block', D, r'\noindent\textbf{Generality.}', r'\noindent\textbf{Generality.}', ''),
]),
('D14', 'ws1_caption_skip', 'DECIDE', [
  ('r', 'main.tex', r'\begin{document}', r'\begin{document}\captionsetup{skip=6pt}'),
]),
('D15', 'ws2_float_sep', 'DECIDE', [
  ('r', 'main.tex', r'\begin{document}', r'\begin{document}\setlength{\textfloatsep}{10pt plus 4pt minus 3pt}\setlength{\floatsep}{8pt plus 4pt minus 2pt}'),
]),
]

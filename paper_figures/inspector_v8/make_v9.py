#!/usr/bin/env python3
"""make_v9.py (agent stt-int-fig, 2026-11-16) -- writes ISCA-27 tikz/checkerwindow_v9_8pt.tex (STT) and checkerwindow_v9b_8pt.tex (Unsafe):
the v8/v8b data in the 'Timeline figure style' of paper_figures/FIGURES.md, with the macro block copied verbatim from tikz/checkerwindow_v7c_8pt.tex
(plus \\cwstarat and the cwred style from squashrace_v5_8pt.tex). Header comments (every tick) come from the v8/v8b files. Run from ISCA-27/tikz.
Writes only new files; refuses to overwrite an existing one unless --force."""
import os, sys
FORCE = "--force" in sys.argv
src = open('checkerwindow_v7c_8pt.tex').read()
macros = src[src.index(r"\newcommand\cwx[2]"):src.index(r"\pgfmathsetmacro\cwyA{0}")]
star = r"\newcommand\cwstarat[2]{\node[star, star points=5, star point ratio=2.4, fill=ssxmitink, draw=white, line width=0.5pt, minimum size=\cwstar, inner sep=0pt] at ({#2},#1) {};}%" + "\n"
macros = macros.replace(r"\begin{tikzpicture}", star + r"\begin{tikzpicture}", 1)
macros = macros.replace(r"  cwwhite/.style={cwann, fill=white, inner sep=0.6pt},%", r"  cwwhite/.style={cwann, fill=white, inner sep=0.6pt},%" + "\n" + r"  cwred/.style={cwband, text=ssxmitink},%", 1)
pre = r"""\providecommand{\figfont}{\fontsize{8pt}{9.5pt}\selectfont}% 8pt figure text regardless of document class (acmart sigconf \footnotesize is 7pt)
\begin{figure}[t]
\centering
% Body only; everything is wrapped in { } so no macro or style leaks into other figures; all helper names are prefixed \cw.%
{%
\providecolor{ssspecfill}{gray}{0.94}\providecolor{ssspecink}{gray}{0}%
\providecolor{ssxmitfill}{gray}{0.76}\providecolor{ssxmitink}{gray}{0}%
\providecolor{sssrcfill}{gray}{0.85}\providecolor{sssrcink}{gray}{0}\providecolor{sssrcbg}{gray}{0.90}%
"""
ys = r"""\pgfmathsetmacro\cwyA{0}%                        lc%
\pgfmathsetmacro\cwyB{-\cwrowAB}%                fnc (the branch)%
\pgfmathsetmacro\cwyC{-\cwrowAB-\cwrowBC}%       xmit%
\pgfmathsetmacro\cwyW{\cwyA+14.5}%               top of the violation-window band%
\pgfmathsetmacro\cwyX{\cwyC-16}%                 time axis line (room for the label under xmit)%
\pgfmathsetmacro\cwyT{\cwyX-3.4}%                top of the row of cycle numbers%
\pgfmathsetmacro\cwyK{\cwyT-11.5}%               top of the criterion box%
\pgfmathsetmacro\cwgT{\cwyA+3}%                  top of the dotted cycle lines%
"""
rows = r"""% ------------- row labels: the roles come from the execution graph -------------%
\node[cwrow] at (0,\cwyA-2.7) {\cwab{lc}};%
\node[cwgloss] at (0,\cwyA-11.7) {Last committed};%
\node[cwrow] at (0,\cwyB-2.7) {i0: \cwab{fnc} (branch)};%
\node[cwgloss] at (0,\cwyB-11.7) {First uncommitted};%
\node[cwrow] at (0,\cwyC-2.7) {i3: \cwab{xmit}};%
\node[cwgloss, text=ssxmitink] at (0,\cwyC-11.7) {Transmitter};%
"""
box = r"""% ------ the defense's transmission criterion (blue = defense-specific) ------%
\pgfmathsetmacro\cwtw{\cwboxw-4.4}%
\node[draw=sssrcink, fill=sssrcbg, line width=0.4pt, anchor=north west, inner xsep=1.8pt, inner ysep=2.2pt] at (0,\cwyK)%
  {\parbox{\cwtw pt}{\raggedright\textit{Transmission criterion:} a load transmits when it executes in the window and obtains its data, by a cache access or a store-to-load forward}};%

\end{tikzpicture}%
}%
"""


def knobs(segs, brks):
    s = (r"""% ============================ TUNING KNOBS ============================%
\def\cwcyc{12}%         pt per simulated cycle (same scale in every axis segment)%
% pt width of the elided (dotted) stretch before each segment (wide enough that neighbouring cycle numbers never touch)%
""" + "".join(r"\def\cwbrk" + k + "{" + str(v) + "}" for k, v in brks) + "%\n" +
         r"""\def\cwtl{57}%          pt, x of the time axis origin; left of it: row labels%
\def\cwrowAB{19}\def\cwrowBC{19}% pt between rows lc-fnc and fnc-xmit%
\def\cwbarh{4}%         pt height of an instruction bar%
\def\cwdot{1.9pt}%      radius of an event dot%
\def\cwstar{8pt}%       outer diameter of the transmission star%
\def\cwlane{3.2}%       pt from a bar's edge to the near edge of a label on a leader%
\def\cwboxw{237}%       pt, width of the criterion box (the whole picture stays within 237.5pt)%
\def\cwfs{\figfont}%    the one font size (8pt)%
% axis segments [start,end], in cycles after lc's fetch; an elided stretch before each segment after the first%
""")
    for k, a, b, c in segs:
        s += r"\def\cws" + k + "{" + a + r"}\def\cwe" + k + "{" + b + "}%   " + c + "%\n"
    s += "% ======================================================================%\n"
    prev = None
    for k, a, b, c in segs:
        s += (r"\pgfmathsetmacro\cwo" + k + "{0}%\n") if prev is None else (r"\pgfmathsetmacro\cwo" + k + r"{\cwo" + prev + r"+(\cwe" + prev + r"-\cws" + prev + r")*\cwcyc+\cwbrk" + k + "}%\n")
        prev = k
    return s


def axis(keys, nums):
    solid = " ".join(r"({\cwxs{" + k + r"}},\cwyX) -- ({\cwxe{" + k + r"}},\cwyX)" for k in keys)
    dots = " ".join(r"({\cwxe{" + a + r"}},\cwyX) -- ({\cwxs{" + b + r"}},\cwyX)" for a, b in zip(keys, keys[1:]))
    return ("% ------------------------------ time axis: one row of cycle numbers ------------------------------%\n"
            r"\draw " + solid + ";%\n" + r"\draw[densely dotted] " + dots + ";%\n" + r"\node[anchor=north west] at (0,\cwyT) {Cycle};%" + "\n" +
            r"\foreach \cwc/\cws/\cwan/\cwdx in {" + nums + "}%\n" + r"  \cwnum{\cwx{\cws}{\cwc}}{\cwan}{\cwdx}{\cwc};%" + "\n\n")


def header(path, title, label_old):
    h = [l for l in open(path).read().splitlines() if l.startswith('%')]
    h = h[:next(i for i, l in enumerate(h) if l.startswith('% Drawing rules'))]
    h[0] = title
    h = [l for l in h if l != label_old]
    return "\n".join(h) + "\n% Label: fig:checkerwindow (as v5-v8; input one version only).\n"


def write(path, text):
    if os.path.exists(path) and not FORCE:
        sys.exit(f"refusing to overwrite {path}")
    open(path, 'w').write(text); print("wrote", path)


segs9 = [("A", "-0.5", "0.5", "lc fetch 0"), ("H", "19.5", "20.5", "lc retires 20"), ("B", "114.5", "116.5", "fnc fetch 115, xmit fetch 116"),
         ("C", "121.5", "122.5", "fnc held 122"), ("G", "126.5", "127.5", "xmit's address ready 127 (STT holds it from here)"),
         ("E", "2622.5", "2624.5", "fnc resolves 2623, squash lands on xmit 2624"), ("F", "2636.5", "2637.5", "fnc retires 2637")]
body9 = r"""% ---------- the violation window: a tan band from lc's retirement (20) to the squash landing on xmit (2624) ----------%
\fill[ssspecfill] ({\cwx{H}{20}},\cwyW) rectangle ({\cwx{E}{2624}},\cwyX);%
\foreach \cwc/\cws in {0/A, 115/B, 116/B, 122/C, 127/G, 2623/E, 2637/F} \draw[cwgrid] ({\cwx{\cws}{\cwc}},\cwyX) -- ({\cwx{\cws}{\cwc}},\cwgT);%
\draw[cwedge] ({\cwx{H}{20}},\cwyW) -- ({\cwx{H}{20}},\cwyX) ({\cwx{E}{2624}},\cwyW) -- ({\cwx{E}{2624}},\cwyX);%
\node[anchor=base] at ({(\cwx{H}{20}+\cwx{E}{2624})/2},\cwyA+6.5) {Violation window};%

""" + rows + r"""
% ------------------- lc: the committed load, fetched at 0; its retirement (20) opens the window -------------------%
\cwbar{\cwyA}{\cwx{A}{0}}{\cwx{H}{20}}{white}\cwgap{\cwyA}{A}{H}{white}\cwend{\cwyA}{\cwx{A}{0}}%
\cwdotat{\cwyA}{\cwx{H}{20}}%
\node[cwband, anchor=west] at ({\cwx{H}{20}+3},\cwyA) {Retires};%

% ------------- fnc: the branch, fetched at 115, forced to mispredict, its resolution held 2,500 cycles -------------%
\cwbar{\cwyB}{\cwx{B}{115}}{\cwx{F}{2637}}{white}\cwgap{\cwyB}{B}{C}{white}\cwgap{\cwyB}{C}{G}{white}\cwgap{\cwyB}{G}{E}{white}\cwgap{\cwyB}{E}{F}{white}\cwend{\cwyB}{\cwx{B}{115}}%
\cwflag{\cwyB}{\cwx{C}{122}}{-1}{e}{0}{cwband}{2{,}500-cycle hold}% under the bar: nothing else is between fnc and xmit there%
\cwflag{\cwyB}{\cwx{E}{2623}}{1}{w}{0}{cwband}{Resolves}%
\cwflag{\cwyB}{\cwx{F}{2637}}{1}{c}{0}{cwwhite}{Retires}% centred: right of the window's edge%
\cwdotat{\cwyB}{\cwx{C}{122}}\cwdotat{\cwyB}{\cwx{E}{2623}}\cwdotat{\cwyB}{\cwx{F}{2637}}%

% ------------- xmit: fetched at 116; STT holds it (blue) from the cycle its address is ready (127) until the squash lands (2624) -------------%
\cwbar{\cwyC}{\cwx{B}{116}}{\cwx{G}{127}}{white}\cwgap{\cwyC}{B}{C}{white}\cwgap{\cwyC}{C}{G}{white}\cwend{\cwyC}{\cwx{B}{116}}%
\cwbar{\cwyC}{\cwx{G}{127}}{\cwx{E}{2624}}{sssrcfill}\cwgap{\cwyC}{G}{E}{sssrcfill}%
\cwflag{\cwyC}{\cwx{G}{127}}{-1}{w}{0}{cwband}{Held by STT}%
\cwdotat{\cwyC}{\cwx{G}{127}}%
\cwcross{\cwyC}{\cwx{E}{2624}}%
\node[cwwhite, anchor=west] at ({\cwx{E}{2624}+3.8},\cwyC) {Squashed};%

""" + axis(["A", "H", "B", "C", "G", "E", "F"], "0/A/north/0, 20/H/north/0, 115/B/north east/1.2, 116/B/north west/-1.2, 122/C/north/0, 127/G/north/0, 2623/E/north east/1.2, 2624/E/north west/-1.2, 2637/F/north/0") + box
cap9 = r"""\caption{How the Inspector decides, on a gem5 trace of STT running the test of Fig.~\ref{fig:concretization}. Each bar runs from an instruction's fetch to its retirement or squash; dots and the cross mark events at their trace cycles, and dotted stretches are elided cycles. The violation window (tan) opens when lc retires and closes when the branch's squash lands on xmit, before fnc retires. STT holds xmit (blue) from the cycle its address is ready until it is squashed, so xmit never transmits and the verdict is no hit.}
\label{fig:checkerwindow}
\end{figure}
"""
t9 = ("% Inspector figure v9 (2026-11-16, one column, agent stt-int-fig): v8's data (integer version of inst-023734 on STT, no hit) in the timeline style\n"
      "% of simspect paper_figures/FIGURES.md 'Timeline figure style' (as checkerwindow_v7c_8pt): every labeled event is a mark on its bar at its trace\n"
      "% cycle, each label beside its mark or on a vertical leader to it, one row of cycle numbers at 12pt per cycle, no F/D/I letter ticks (a bar runs\n"
      "% from the instruction's fetch to its retirement or squash). Macro block copied from checkerwindow_v7c_8pt.tex. Generator: simspect\n"
      "% paper_figures/inspector_v8/make_v9.py. v8 drew F letters, a slanted Resolves leader and 5pt per cycle.")
write('checkerwindow_v9_8pt.tex', header('checkerwindow_v8_8pt.tex', t9, "% Label: fig:checkerwindow (as v5/v6/v7; input one version only).") + pre + knobs(segs9, [("H", 7), ("B", 7), ("C", 7), ("G", 7), ("E", 12), ("F", 12)]) + macros + ys + "\n" + body9 + cap9)

segs9b = [("A", "-0.5", "0.5", "lc fetch 0"), ("H", "18.5", "19.5", "lc retires 19"), ("B", "102.5", "104.5", "fnc fetch 103, xmit fetch 104"),
          ("C", "108.5", "109.5", "fnc held 109"), ("G", "115.5", "116.5", "xmit's cache access 116"),
          ("E", "2609.5", "2611.5", "fnc resolves 2610; squash lands on xmit and fnc retires 2611")]
body9b = r"""% ---------- the violation window: a tan band from lc's retirement (19) to the squash landing on xmit (2611) ----------%
\fill[ssspecfill] ({\cwx{H}{19}},\cwyW) rectangle ({\cwx{E}{2611}},\cwyX);%
\foreach \cwc/\cws in {0/A, 103/B, 104/B, 109/C, 116/G, 2610/E} \draw[cwgrid] ({\cwx{\cws}{\cwc}},\cwyX) -- ({\cwx{\cws}{\cwc}},\cwgT);%
\draw[cwedge] ({\cwx{H}{19}},\cwyW) -- ({\cwx{H}{19}},\cwyX) ({\cwx{E}{2611}},\cwyW) -- ({\cwx{E}{2611}},\cwyX);%
\node[anchor=base] at ({(\cwx{H}{19}+\cwx{E}{2611})/2},\cwyA+6.5) {Violation window};%

""" + rows + r"""
% ------------------- lc: the committed load, fetched at 0; its retirement (19) opens the window -------------------%
\cwbar{\cwyA}{\cwx{A}{0}}{\cwx{H}{19}}{white}\cwgap{\cwyA}{A}{H}{white}\cwend{\cwyA}{\cwx{A}{0}}%
\cwdotat{\cwyA}{\cwx{H}{19}}%
\node[cwband, anchor=west] at ({\cwx{H}{19}+3},\cwyA) {Retires};%

% ------------- fnc: the branch, fetched at 103, forced to mispredict, its resolution held 2,500 cycles -------------%
\cwbar{\cwyB}{\cwx{B}{103}}{\cwx{E}{2611}}{white}\cwgap{\cwyB}{B}{C}{white}\cwgap{\cwyB}{C}{G}{white}\cwgap{\cwyB}{G}{E}{white}\cwend{\cwyB}{\cwx{B}{103}}%
\cwflag{\cwyB}{\cwx{C}{109}}{-1}{e}{0}{cwband}{2{,}500-cycle hold}% under the bar: nothing else is between fnc and xmit there%
\cwflag{\cwyB}{\cwx{E}{2610}}{1}{w}{0}{cwband}{Resolves}%
\cwdotat{\cwyB}{\cwx{C}{109}}\cwdotat{\cwyB}{\cwx{E}{2610}}\cwdotat{\cwyB}{\cwx{E}{2611}}%
\node[cwwhite, anchor=west] at ({\cwx{E}{2611}+3},\cwyB) {Retires};% beside its mark: the bar ends here, right of the window's edge%

% ------------- xmit: fetched at 104; it reads the cache inside the window (116), then the squash lands (2611) -------------%
\cwbar{\cwyC}{\cwx{B}{104}}{\cwx{E}{2611}}{white}\cwgap{\cwyC}{B}{C}{white}\cwgap{\cwyC}{C}{G}{white}\cwgap{\cwyC}{G}{E}{white}\cwend{\cwyC}{\cwx{B}{104}}%
\cwflag{\cwyC}{\cwx{G}{116}}{-1}{c}{0}{cwred}{Cache access}%
\cwstarat{\cwyC}{\cwx{G}{116}}%
\cwcross{\cwyC}{\cwx{E}{2611}}%
\node[cwwhite, anchor=west] at ({\cwx{E}{2611}+3.8},\cwyC) {Squashed};%

""" + axis(["A", "H", "B", "C", "G", "E"], "0/A/north/0, 19/H/north/0, 103/B/north east/1.2, 104/B/north west/-1.2, 109/C/north/0, 116/G/north/0, 2610/E/north east/1.2, 2611/E/north west/-1.2") + box
cap9b = r"""\caption{How the Inspector decides, on a gem5 trace of the undefended Unsafe build running the test of Fig.~\ref{fig:concretization}. Each bar runs from an instruction's fetch to its retirement or squash; dots, the star, and the cross mark events at their trace cycles, and dotted stretches are elided cycles. The violation window (tan) opens when lc retires and closes when the branch's squash lands on xmit, as fnc retires. Inside it, xmit reads its data from the cache ($\star$), which meets STT's transmission criterion (blue), so the test is a hit.}
\label{fig:checkerwindow}
\end{figure}
"""
t9b = ("% Inspector figure v9b (2026-11-16, one column, agent stt-int-fig): v8b's data (integer version of inst-023734 on the undefended Unsafe build,\n"
       "% hit) in the timeline style of simspect paper_figures/FIGURES.md 'Timeline figure style' (as checkerwindow_v7c_8pt and v9).\n"
       "% Generator: simspect paper_figures/inspector_v8/make_v9.py.")
write('checkerwindow_v9b_8pt.tex', header('checkerwindow_v8b_8pt.tex', t9b, "% Label: fig:checkerwindow (as v5/v6/v7/v8; input one version only).") + pre + knobs(segs9b, [("H", 7), ("B", 7), ("C", 7), ("G", 7), ("E", 12)]) + macros + ys + "\n" + body9b + cap9b)

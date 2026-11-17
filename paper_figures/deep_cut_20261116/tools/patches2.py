# Rebased deep-cut list: patches.py minus the eight items the main session wrapped (cut plan L1, L2, L3, L4, L6, F2, L7, F3).
import importlib.util
SC = '/private/tmp/claude-501/-Users-annaeaton-trippel-simspect/1fbcfc80-239b-4566-ba1b-6aed142a4ddd/scratchpad'
spec = importlib.util.spec_from_file_location('p1', SC + '/tools/patches.py'); p1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p1)
WRAPPED = [  # substrings identifying my edits that overlap the wrapped items
  'running the solver until no graph is left (UNSAT)',           # F2
  'The executor then runs each test',                             # F2
  'one test per misprediction direction. \\textbf{Executor:}',    # F3
  'resolution delayed 0, 500, or 2{,}500 cycles.',                # F3
  'in inline asm so the compiler cannot forward',                 # F3
  '\\caption{\\toolname{} has three parts:',                      # L2
  'A solution graph must satisfy three kinds of constraint:',     # L4
  '\\begin{enumerate}',                                           # L4
  'The well-formedness axioms and the leakage predicate are those of', # L4
  'CleanupSpec also leaves a constant-time cleanup to future work',    # L6
  'i1 is the unresolved branch, so i2--i4 are speculative',       # L7
  '\\subsubsection{',
  "(a) also specifies i2's destination",                          # Fig. 3 is being redesigned by another agent (coordinator, ead06d8)                                             # run-in heads: not wrappable in \cutrep (sectioning inside a color group); listed separately
]
PATCHES = []
for pid, name, tier, edits in p1.PATCHES:
    keep = [e for e in edits if not any(w in e[2] for w in WRAPPED)]
    if keep: PATCHES.append((pid, name, tier, keep))
# overfull fix for 18 (commitToIEWDelay could not break): put gem5's first
for k, (pid, name, tier, edits) in enumerate(PATCHES):
    if pid == '18':
        edits = [(e[0], e[1], e[2], e[3].replace(r"needs \texttt{commitToIEWDelay} above its default of one cycle.", r"needs a squash slower than gem5's default of \texttt{commitToIEWDelay}~$=1$.")) for e in edits]
        PATCHES[k] = (pid, name, tier, edits)
I = 'sections/intro.tex'; D = 'sections/discussion.tex'
PATCHES += [
('22', 'intro_amulet_luck', 'Low', [
  ('r', I, 'AMuLeT relies heavily on luck to find violations.', ''),
  ('r', I, 'A randomly generated program must happen to create', 'To find a violation, a randomly generated program must happen to create'),
]),
('23', 'fig2_caption', 'Free', [
  ('r', 'tikz/dataflow_v2_8pt.tex', 'In this and every later execution graph,', 'In every execution graph,'),
]),
('24', 'discussion_protean_mechanism', 'Low', [
  ('r', D, "Protean's extension of AMuLeT found", "Protean's fuzzer found"),
  ('r', D, "an older tainted branch that mispredicts blocks the squash of a younger untainted branch that mispredicts in the same cycle, so whether the younger branch squashes reveals the tainted branch's condition",
           "whether a younger untainted branch that mispredicts in the same cycle squashes reveals an older tainted branch's condition"),
]),
('25', 'intro_execution_sentence', 'Low', [
  ('r', I, "The execution captures the microarchitectural state that the defense's guarantee depends on, e.g., which branches are unresolved and which instructions have committed.", ''),
]),
]

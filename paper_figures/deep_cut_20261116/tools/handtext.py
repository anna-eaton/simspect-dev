NOTCUT = """## What I deliberately did not cut, and why

- **The abstract.** It carries every headline claim, and the intro and body already repeat it; cutting there moves no claim but costs the most-read text.
- **The intro's "The graph is detailed enough to express how the defense decides what to protect, yet abstract enough for a solver (our implementation uses Alloy) to enumerate every minimal violating execution up to a bound."** It carries the abstract's "enough detail … yet simply enough for formal analysis" claim and labels Alloy as an implementation detail, both of which Caroline asked for.
- **The intro's commitToIEWDelay caveat ("The race appears when gem5's \\texttt{commitToIEWDelay} is raised …").** Shortened (10.5), never cut: without it the intro overclaims UV6.
- **§5's four result terms (violation, hit, leak, bug).** Canonical definitions every later section uses.
- **§5.2's resolved-branch condition ("A hit also requires every branch that the graph marks resolved …").** It is what makes a hit sound; a reviewer will look for it.
- **§5.1's sweep clause ("a sweep runs every setting and reports a hit if any setting triggers one").** UV3 says "the swept … delay", so some counts may rest on sweeps; cutting it could leave a count without its method.
- **UV1's xmm3 control ("and none when it is moved through \\texttt{xmm3}").** Eight words, and the only evidence that register index 16, not vector registers in general, is the cause.
- **UV1's master-branch sentence.** Trimming it (old cut plan L22) only moved its last word to a new line; it also shows the bug is unfixed upstream.
- **UV3's scoping sentence ("In all 17, the older operand reaches the transmitter only through register reads that gem5's x86 instructions make and the x86 specification does not").** Without it the UV3 count overclaims; only its alternative counts go (16.2).
- **UV4's "and its patch for A-UV6 would also close this bug".** The honest statement of how new UV4 is.
- **UV5's AMuLeT-fuzzer result (47 of 248 violations).** §7 uses it as the harness-soundness evidence.
- **§6.3's "Two factors contribute, and we do not separate them".** It keeps the 3.7×–1,655× multiples from being read as the effect of synthesis alone.
- **§6.4's "Generation is a one-time cost … its time per detection already includes generation".** The fairness argument for the timing comparison.
- **§6.1's CleanupSpec sentence.** Anna's call at ead06d8 (it carries the reason A-KV2 is out of scope); only tightened (06.3).
- **§7 "What we count" (ReCon floating-point loads).** It discloses that about 70% of the vector version's ReCon hits are not counted; cutting it would hide a methodology choice.
- **§7 "Known bugs we miss".** The intro's "seven such bugs" includes Protean's two, which SimSpect misses; the paper must say so. Only the mechanism clause is shortened (24, optional).
- **§7 "Specifications" (the SPT untaint gap).** A known way the specification is stricter than SPT.
- **Related Work's Kvalsvik/UV3 distinction.** It is the novelty argument for UV3.
- **Fig. 2's caption legend and Fig. 5's caption.** They are the notation keys that Figs. 3, 7, 8, 9 and Table 2 point to.
- **Fig. 3, Table 1, Fig. 6, and Figs. 10–11.** The new Fig. 3 grid, Table 1 v4 and Fig. 6 v2 are in HEAD, and another agent is merging Figs. 10–11; as the main session asked, I left all of them to that work (the old cut plan's F6, F20, D7 and the Fig. 11 option go with it, and so does the A-UV5 count in §6.1, which Fig. 10's caption repeats today).
- **The §4.3 run-in subsubsection heads (old cut plan F9).** A `\\subsubsection` cannot sit inside `\\cutrep` (its color group breaks the run-in head), and the change measured 0 rows on 8587638.
- **Fig. 4's two-line annotation (old L30) and Fig. 1's arrow label (old L29).** Figure geometry; neither moved the body end in the whitespace pass.
- **The Acknowledgments' AI disclosure.** Required.
- **The §5.1 cache-state paragraph's last line "the cache state."** A three-word last line; the only shortening I found drops the reason for starting ReCon runs warm or the reason the cache state is random, both design justifications.
"""

OBS = """## Things I noticed that are not cuts

- **§5.2 has a forced break in the middle of a word** (pipeline.tex:153–155 at `37d287c`: `instru-`, a blank line, `\\noindent ction`), from `efa0c79` ('Updates from Overleaf'). It prints correctly only while 'instru-' happens to fall at a line end; any change above it breaks the word in mid-column. Patch 00 joins it; take it before or with any other cut.
- **Fig. 6 is never cited in the text** (`\\label{fig:sttxmm4}` has no `\\ref`). A reviewer will notice. Fix at no row cost: in results.tex UV1, `so a speculatively loaded secret copied through \\texttt{xmm4} and back loses its taint` → `so a speculatively loaded secret copied through \\texttt{xmm4} and back loses its taint (Fig.~\\ref{fig:sttxmm4})`.
- **Fig. 8's caption says "after a 500-cycle hold" for i2, a branch the graph marks resolved.** The canonical word for a resolved branch is "delay" (16.1 uses it in the text).
- **UV2 and UV3 say "tests from our STT model".** The canonical-terms list bans "model" for a specification: "tests of STT's specification".
- **Table 2 says "divide: unguarded, so a zero divisor faults … a divide's fault counts as a transmission", while §7 says "our tests are not built to fault (§4.3.3)".** Both can be true (the divide faults only on the wrong path and never reaches commit, which Protean's SPT bug needs), but the §7 sentence should say "not built to fault at commit" or similar.
"""

STATUS = """## Status of the earlier lists (re-checked against 37d287c)

- **Cut plan Free tier:** F1, F7, F8 applied earlier; F2, F3 wrapped by the main session (11a20dd); F10 wrapped with L4; F4 → 02.1 (trimmed instead of cut, since Anna's §3 note asks for the synthesizer link); F11 → 14.1; F12 → 02.3; F13 → 02.4; F14 → 02.2; F17 and F23 done by the orphan pass (6f492f7); F18 → 14.3; F19 → 06.1; F20 left to the Figs. 10–11 merge; F5 not taken (Fig. 2's caption is the only walk-through of Fig. 2); F6 went with the Fig. 3 redesign (7df37ef); F9 not taken (see above); F15, F16, F21, F22, F24, F26 no longer live (the text changed); F25 not taken (intro ¶2, already fixed by the orphan pass).
- **Cut plan Low tier:** L1, L3, L4 wrapped (11a20dd); L2 dropped (Option B commented out, cc2e8b3); L7 applied in the text (cc2e8b3); L6 only partly live, its CleanupSpec sentence kept by Anna and tightened in 06.3; L5 → 16.1, 16.2; L8 mostly done by Anna's condensed Related Work, its Isla clause → 20.1; L9 → 19.1–19.6; L10 → 14.2, 14.3; L11 → 10.1; L12 → 10.2; L13 → 10.3–10.5; L14 → 10.9; L15 → 21.1; L16 → 21.2; L17 → 10.6 and 22; L19 → 13.2; L20 → 13.1; L21 → 14.3; L22 not taken (see above); L23 → D5; L24 → 16.4; L25 → 17.1; L26 → 15.1; L27 → 06.2; L28 → 10.7 (keeps "(via committed instructions)", which defines "architecturally"); L18 no longer live; L29, L30 not taken.
- **Cut plan real tradeoffs:** D1 (In/Out) → D2; D3 (Figs. 10–11) left to the merge (another agent); D2 (Table 1) and D4 (Fig. 6) left to the pending figure work (measured −14 each on HEAD, not proposed); D6 (defense list) → D9; D8 (SNI) → D1; D5 (rule boxes) not measured (figure redesign); D7 (Fig. 3) done by the redesign (7df37ef); D9 (copyright block) not proposed (template); D10 kept.
- **Related Work optional cuts:** O-a → D8; O-b not proposed (it removes Serberus); O-c → 20.1.
- **Whitespace decisions:** WS-1 → D11; WS-2 → D12; WS-3 and WS-4 not re-measured (figure geometry).
- **Citation audit:** Anna's condensed Related Work already dropped most padding citations; the Background MCM list → 19.5.
"""

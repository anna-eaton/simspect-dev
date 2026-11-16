# UV3 vs. Kvalsvik and Själander (ReConnaissance), 2026-11-16

**Verdict: (a) UV3 is new.** Kvalsvik and Själander report a different flaw, at the design level: STT tracks only the *youngest* taint source, and ReCon's reveal of that younger source releases an older, unrevealed one. UV3 is the mirror image in ReCon's gem5 implementation of STT: it keeps only the *oldest* source, and the leak needs no reveal at all, only the older source's branch resolving first. Recommendation: keep UV3 as new, cite them precisely in Related Work, optionally contrast in UV3. No bug-count change.

## Source

- The paper itself ("ReConnaissance: Correctly Tracking Multiple Secrets using Reveal/Conceal Paradigms", Kvalsvik and Själander, "Submitted to 63rd ACM/IEEE ... DAC") is **not public**. Its only public text is the IEEE DataPort abstract (DOI 10.21227/dkjt-k008, the current bib key `kvalsvik2025reconnaissance`, which is a dataset with one .xlsx file) and Kvalsvik's PhD thesis, which says of Paper C: "This paper is submitted for publication and is therefore not included." (thesis p. 143).
- The thesis summarizes Paper C in §4.3 "Reveal/Conceal for Multiple Secrets" (pp. 43–44, incl. Fig. 4.3) and pp. 3–4 of the introduction. Thesis: Amund Bergland Kvalsvik, *Haunt Me No Longer! Finding Meaningful Solutions to Speculative Side-Channel Attacks*, PhD thesis, NTNU, Trondheim, July 2025 (NVA record 019a82409b67-a562a0db-fe67-4839-952d-4c3aa4694689). Saved copy: `paper_figures/caroline/papers/kvalsvik-2025-phd-thesis-haunt-me-no-longer.{pdf,txt}`.
- So everything below is from the thesis summary, not from Paper C's body. A web search for the title found no published version.

## (1) What leak, through which mechanism

- Thesis §4.3, p. 43: "When an instruction has multiple taint sources, only information about the youngest of these is preserved during the tainting process, creating the Youngest Root-of-Taint (YRoT). It is secure for STT to only track YRoTs, because speculation resolves chronologically ... by the time the youngest taint is non-speculative, any older taints must also be non-speculative."
- Same page: "When a YRoT source is found to be revealed, it is immediately broadcast as secure, allowing transmitting instructions with that YRoT to execute. This breaks the previous concept of chronology, because a younger taint can be declared revealed before an older taint is non-speculative. As such, using STT and ReCon, an older taint can be transmitted if the younger taint is revealed".
- Fig. 4.3 (p. 44): `MOV ECX,[0x80]` (source 0, not revealed), `MOV EBX,[0x96]` (source 1, revealed), `MOV EAX,[EBX+ECX]` has YRoT = 1, so "The final load instruction leaks the value at 0x80 ... because only a single taint source is tracked via the YRoT, which is set to Taint Source 1 ... and has been revealed."
- Fix (p. 43): mark any output where tracking loses a source as "having multiple secret data sources", propagate the mark, and exclude such instructions from ReCon.
- So it is the ReCon **reveal** interacting with STT's correct youngest-source rule. It is not the oldest-source rule, and it does not exist without ReCon's reveal.

## (2) Code or design

- Design level only. The thesis describes STT as tracking the youngest source and never mentions an implementation that keeps the oldest one, `getOldestTaint`, `taint_tracker.cc`, or gem5 taint code. (Paper C's evaluation is gem5-based, judging by the dataset file `gem5-reconnaissance.xlsx`, but the body is not available to check.)

## (3) Same scenario as UV3?

- **Different.** Theirs: the *younger* source is tracked and *revealed* early, so the older, still-speculative source leaks; it requires ReCon's reveal mechanism. UV3 (`results.tex:58`, `taint_tracker.cc:108–131`): the *older* source is tracked, so once the *older* load's branch resolves the merged value is untainted while the *younger* source is still speculative; it occurs on the STT scheme of gem5-recon with no reveal (Fig. `recon_otb_v4_8pt`).
- Neither is a superset of the other. Their premise ("It is secure for STT to only track YRoTs") is exactly what ReCon's implementation violates, so UV3 breaks the assumption their analysis rests on.
- Inference (not verified against Paper C): their fix restricts ReCon eligibility and leaves the STT untaint path alone, so it would not remove UV3.

## (4) Verdict

- **(a) new**, not (b) or (c). Same trigger class (an instruction with several tainted operands), but a different root cause (oldest vs. youngest tracking), a different enabling event (branch resolution vs. reveal), and a different level (gem5 code vs. design). Abstract/intro "six new bugs" stays.
- Hard decision for Anna (DECIDE D-3 / R-4): whether to also contrast in the UV3 paragraph (option A below) or only in Related Work (option B). Recommendation: B only, to save space, since the Related Work sentence must change anyway.

## (5) Proposed text (paper is read-only; for Anna to paste)

- **Related Work** (`related.tex:16`). Old: `and two of ReCon's authors report that ReCon leaks when an instruction has multiple secret sources~\cite{kvalsvik2025reconnaissance}.` New: `and two of ReCon's authors show that ReCon's design leaks when an instruction has multiple secret sources: STT tracks only the youngest one, and revealing it releases the older ones~\cite[\S 4.3]{kvalsvik2025thesis}. UV3 (\S~\ref{sec:bug-otb}) is a different flaw in ReCon's implementation of STT, which tracks the oldest source.`
- **Bib** (replace the dataset entry, whose note already says to): `@phdthesis{kvalsvik2025thesis, author = {Amund Bergland Kvalsvik}, title = {Haunt Me No Longer! Finding Meaningful Solutions to Speculative Side-Channel Attacks}, school = {Norwegian University of Science and Technology}, address = {Trondheim, Norway}, year = {2025}, month = jul}`. Their Paper C can replace it if it is published.
- **UV3, option A** (`results.tex:58`, optional). Old: `which is dropped once that source stops being speculative.` New: `which is dropped once that source stops being speculative. This is the reverse of the multi-source leak in ReCon's design, where the youngest source is tracked and revealed early~\cite[\S 4.3]{kvalsvik2025thesis}.`
- **Abstract / intro / conclusion counts**: no change (`abstract.tex:16` "six new bugs", `intro.tex:247` "six previously unknown bugs", `conclusion.tex:2` "six new bugs").

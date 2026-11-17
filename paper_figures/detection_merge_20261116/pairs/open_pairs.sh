#!/bin/bash
# Figs. 10 + 11 merged (2026-11-16, fig10-11-merge): old Fig. 10, old Fig. 11, merged v1, merged v1b (10% shorter axes), all standalone at 250 dpi (same scale),
# then page 10 of the notes-hidden build before and after the swap (ISCA-27 37d287c copy, switches (1)-(5) on, \input swapped in the copy only).
cd "$(dirname "$0")"
open -a Preview old_fig10.png old_fig11.png new.png new_v1b.png page10_old.png page10_new.png

#!/bin/bash
# Fig. 3 relaxation: v3 (one column of four panes) vs v4 grid (2x2), same scale (250 dpi).
# Order: standalone old, standalone new, page crop old (p.6 left column), page crop new (p.5 right column).
# Builds: ISCA-27 6f492f7 copy with every note group hidden (switches (1)-(5)), \input swapped in the copy only.
cd "$(dirname "$0")"
open -a Preview old.png new.png page_old.png page_new.png

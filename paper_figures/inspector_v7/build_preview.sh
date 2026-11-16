#!/usr/bin/env bash
# build_preview.sh <standalone-stem>  -- builds ISCA-27 tikz/<stem>.tex in a scratch dir and writes the 200 dpi preview tikz/<stem>-1.png
# (same as the other standalones: pdflatex from the paper root, pdftoppm -r 200). Prints the PDF page size and any LaTeX warnings about overfull boxes.
set -euo pipefail
P=/Users/annaeaton/trippel/ISCA-27; S=$1; B=${TMPDIR:-/tmp}/cwbuild_$S; mkdir -p $B
cd $P && pdflatex -interaction=nonstopmode -halt-on-error -output-directory $B tikz/$S.tex > $B/build.out 2>&1 || { tail -30 $B/build.out; exit 1; }
grep -i "overfull\|warning" $B/$S.log | grep -v "pdfTeX warning\|Font Warning" | head -5 || true
pdfinfo $B/$S.pdf | grep "Page size"
pdftoppm -r 200 -png $B/$S.pdf $P/tikz/$S && ls -la $P/tikz/$S-1.png

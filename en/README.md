# Neural Networks and Deep Learning — LaTeX Edition

Michael A. Nielsen, *Neural Networks and Deep Learning*, Determination Press, 2015.

This is a LaTeX typesetting of the book, converted from the author's free online
edition at <http://neuralnetworksanddeeplearning.com> (text and figures © Michael
A. Nielsen, released under the Creative Commons Attribution-NonCommercial 3.0
Unported license).

## Build

Requires XeLaTeX (TeX Live / MiKTeX / Overleaf all work):

```bash
latexmk -xelatex main.tex
```

or on Overleaf: upload the whole folder as a zip, set the compiler to **XeLaTeX**
in project settings, and compile `main.tex`.

## Structure

```
main.tex          # document class, template design, title page, front/back matter
chapters/         # auto-converted chapter bodies (from the online HTML)
  about.tex       #   What this book is about (preface)
  chap1..6.tex    #   Chapters 1-6
  sai.tex         #   Appendix: Is there a simple algorithm for intelligence?
  exercises_and_problems.tex, acknowledgements.tex
images/           # all book figures (PNG/JPG, downloaded from the online edition)
```

## Design notes

The visual design is adapted from the "Maki 梦幻数学讲义" LaTeX template
(XeLaTeX, TeX Gyre Pagella + mathpazo, rose `LogicColor` chapter headings,
tcolorbox exercise boxes, rose header rule):

- Chapter titles: centered, rose, letterspaced "Chapter N" kicker
- Exercises / Problems: breakable steel-blue `tcolorbox`es
- Equations keep the book's original numbering via `\tag{N}`
- The `eqnarray` displays of the web edition were converted to amsmath `align`/`equation`
- Figures are placed inline in the narrative (non-floating), matching the web edition
- The three videos of Chapter 4 are replaced by "movie note" placeholders
- Margin notes of the web edition become footnotes

## Regenerating the chapter sources

`chapters/*.tex` are generated from the site HTML by `../convert.py`
(Python 3 + beautifulsoup4 + lxml):

```bash
python ../convert.py && python ../qa_check.py
```

## License

Book content: CC BY-NC 3.0 (© Michael A. Nielsen) — free to share and build on,
not to sell. LaTeX conversion: same license for the added formatting code.

# Attribution and licensing of the book content

## The work

**Neural Networks and Deep Learning**
Michael A. Nielsen, *Determination Press*, 2015
Free online edition: <http://neuralnetworksanddeeplearning.com>

## Licence of the text and figures

> This work is licensed under a Creative Commons
> Attribution-NonCommercial 3.0 Unported License.
> <https://creativecommons.org/licenses/by-nc/3.0>

© 2015 Michael A. Nielsen. You are free to **share** (copy and redistribute the
material in any medium or format) and to **adapt** (remix, transform, and build
upon the material) under these terms:

- **Attribution** — you must give appropriate credit, provide a link to the
  licence, and indicate if changes were made.
- **NonCommercial** — you may not use the material for commercial purposes.

No additional restrictions may be applied.

## What that means for this repository

| Part | Licence |
|---|---|
| Book text and figures (`en/chapters/`, `en/images/`, `zh/chapters/`, `zh/images/`) | **CC BY-NC 3.0** — © Michael A. Nielsen |
| The Chinese translation (`zh/`) | a derivative work of the above, therefore also **CC BY-NC 3.0** |
| HTML→LaTeX converter, LaTeXTrans patches, post-processing and QA tooling, CI workflow (`convert.py`, `qa_check.py`, `pipeline/`, `.github/`) | **MIT** — see [LICENSE](LICENSE) |
| LaTeX markup / template code in `en/main.tex`, `zh/main-zh.tex`, `pipeline/reference-template/` | **MIT** |

**This repository is not for sale and must not be used commercially.**

> The MIT licence in [LICENSE](LICENSE) covers the *software* in this
> repository only — the converter, the LaTeXTrans book patches, the
> post-processing and QA tooling, the CI workflow and the LaTeX markup/template
> code. It does **not** cover the book content, which stays under
> CC BY-NC 3.0 as described above.

## Changes made to the original

This repository is an *adaptation*, and the licence requires that the changes be
stated:

1. The author's HTML edition at neuralnetworksanddeeplearning.com was converted
   to LaTeX (`en/`) — the prose, figures and equation numbering are unchanged;
   only markup was added.
2. The book was translated into simplified Chinese with the LaTeXTrans
   multi-agent system (`zh/`), then post-processed for terminology and
   punctuation consistency. This is a machine translation and **has not been
   reviewed sentence by sentence by a human**.
3. The web edition's interactive figures and videos are not reproducible on
   paper; see `en/README.md`.

## Acknowledgements

All credit for the book itself belongs to **Michael A. Nielsen**. If you enjoy
it, please read the original free online edition and consider supporting the
author. The LaTeXTrans translation system is by the **NiuTrans** group
(<https://github.com/NiuTrans/LaTeXTrans>). The visual design follows the
"Maki 梦幻数学讲义" LaTeX template.

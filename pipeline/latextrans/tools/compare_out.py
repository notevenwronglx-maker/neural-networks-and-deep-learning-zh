#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compare an English chapter with its LaTeXTrans Chinese counterpart.

Counts LaTeX commands and environment delimiters on both sides and prints any
difference, plus translation-coverage statistics (CJK ratio, full-width stop
count, term glosses, residual placeholders).

Usage:  python tools/compare_out.py <en.tex> <zh.tex>
"""
import io
import re
import sys
from collections import Counter

MATH_SPLIT = re.compile(
    r"(\$[^$]*\$|\\\[.*?\\\]"
    r"|\\begin\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\}"
    r".*?\\end\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\})",
    re.DOTALL,
)


def command_counts(text):
    c = Counter()
    for m in re.finditer(r"\\begin\{([^}]+)\}", text):
        c["\\begin{%s}" % m.group(1)] += 1
    for m in re.finditer(r"\\end\{([^}]+)\}", text):
        c["\\end{%s}" % m.group(1)] += 1
    for m in re.finditer(r"\\([a-zA-Z]+)", text):
        c["\\" + m.group(1)] += 1
    return c


def main():
    en = io.open(sys.argv[1], encoding="utf-8").read()
    zh = io.open(sys.argv[2], encoding="utf-8").read()

    ce, cz = command_counts(en), command_counts(zh)
    keys = sorted(set(ce) | set(cz))
    diffs = [(k, ce.get(k, 0), cz.get(k, 0)) for k in keys if ce.get(k, 0) != cz.get(k, 0)]

    body = MATH_SPLIT.sub(" ", zh)
    body = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", body)
    body = re.sub(r"[{}]", " ", body)

    print("=" * 70)
    print("COMMAND DIFFERENCES (en vs zh): %d" % len(diffs))
    for k, a, b in diffs:
        print("   %-28s en=%-4d zh=%-4d" % (k, a, b))
    print("=" * 70)
    print("zh chars            : %d" % len(zh))
    print("zh CJK chars        : %d" % len(re.findall(r"[\u4e00-\u9fff]", zh)))
    print("zh ascii words      : %d" % len(re.findall(r"\b[A-Za-z]{3,}\b", body)))
    print("full-width stops 。 : %d" % zh.count("。"))
    print("half-width '. '     : %d" % len(re.findall(r"\.\s", zh)))
    print("residual placeholders: %d" % len(re.findall(r"<PLACEHOLDER_[^>]*>", zh)))
    print("markdown fences     : %d" % zh.count("```"))
    glosses = re.findall(r"\\emph\{([^{}]+)\}\s*[（(]\s*([A-Za-z][^）)]{1,60})[）)]", zh)
    print("term glosses        : %d" % len(glosses))
    for zh_t, en_t in glosses[:15]:
        print("   %s（%s）" % (zh_t, en_t.strip()))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Census of punctuation in the Chinese output, outside math.

mathtranslations.org requires Chinese punctuation in the body with a half-width
sentence-final "."; this tells us how far the machine output deviates.

Usage: python tools/punct_census.py <chapters dir>
"""
import glob
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

PAIRS = [("，", ","), ("：", ":"), ("；", ";"), ("？", "?"), ("！", "!"),
         ("（", "("), ("）", ")"), ("。", ".")]


def main():
    root = sys.argv[1]
    full = Counter()
    half = Counter()
    examples = {}

    for path in sorted(glob.glob(root + r"\*.tex")):
        text = io.open(path, encoding="utf-8").read()
        parts = MATH_SPLIT.split(text)
        body = "".join(p for i, p in enumerate(parts) if i % 2 == 0)

        full["，"] += body.count("，")
        full["："] += body.count("：")
        full["；"] += body.count("；")
        full["？"] += body.count("？")
        full["！"] += body.count("！")
        full["（"] += body.count("（")
        full["）"] += body.count("）")
        full["。"] += body.count("。")

        # half-width variants surrounded by CJK
        for half_ch, pat in [
            (",", r"[\u4e00-\u9fff][ \t]*,[ \t]*[\u4e00-\u9fff]"),
            (":", r"[\u4e00-\u9fff][ \t]*:[ \t]*[\u4e00-\u9fff]"),
            (";", r"[\u4e00-\u9fff][ \t]*;[ \t]*[\u4e00-\u9fff]"),
            ("?", r"[\u4e00-\u9fff][ \t]*\?[ \t]*[\u4e00-\u9fff]"),
            ("!", r"[\u4e00-\u9fff][ \t]*![ \t]*[\u4e00-\u9fff]"),
            ("(", r"[\u4e00-\u9fff][ \t]*\([^()]{0,40}\)"),
        ]:
            for m in re.finditer(pat, body):
                half[half_ch] += 1
                examples.setdefault(half_ch, m.group(0)[:40])

    print("%-4s %-4s %10s %10s" % ("full", "half", "count_full", "count_half"))
    for f, h in PAIRS:
        print("%-4s %-4s %10d %10d   %s"
              % (f, h, full[f], half[h], examples.get(h, "")))


if __name__ == "__main__":
    main()

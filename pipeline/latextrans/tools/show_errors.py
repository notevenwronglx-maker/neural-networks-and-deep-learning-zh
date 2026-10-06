#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show where a validator error lives: compare the LaTeX commands around each
\\rm / \\emph in the source section against its translation.

Usage: python tools/show_errors.py <out/ch_.../sections_map.json>
"""
import io
import json
import re
import sys


def ctx(text, needle, span=90):
    out = []
    for m in re.finditer(re.escape(needle), text):
        a = max(0, m.start() - span)
        b = min(len(text), m.end() + span)
        out.append(text[a:b].replace("\n", " | "))
    return out


def main():
    path = sys.argv[1]
    sections = json.load(io.open(path, encoding="utf-8"))
    idx = {s["section"]: s for s in sections}

    for sid, needle in [("17#1", r"\rm"), ("22", r"\rm"), ("45#1", r"\emph")]:
        s = idx.get(sid)
        print("=" * 78)
        print("section %s   source hits=%d   translation hits=%d"
              % (sid, len(re.findall(re.escape(needle), s["content"])),
                 len(re.findall(re.escape(needle), s["trans_content"]))))
        print("-" * 78)
        print("SOURCE:")
        for c in ctx(s["content"], needle):
            print("   ...%s..." % c)
        print("TRANSLATION:")
        for c in ctx(s["trans_content"], needle):
            print("   ...%s..." % c)


if __name__ == "__main__":
    main()

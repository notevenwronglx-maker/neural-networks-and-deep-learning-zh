#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Locate the unbalanced $ in a chapter, ignoring verbatim/code blocks."""
import io
import re
import sys

PROT = re.compile(
    r"(\\begin\{(?:lstlisting|verbatim|minted|Verbatim)\*?\}.*?"
    r"\\end\{(?:lstlisting|verbatim|minted|Verbatim)\*?\})", re.DOTALL)


def main():
    path = sys.argv[1]
    text = io.open(path, encoding="utf-8").read()
    spans = []
    for m in PROT.finditer(text):
        spans.append((m.start(), m.end()))

    def protected(i):
        return any(a <= i < b for a, b in spans)

    positions = [m.start() for m in re.finditer(r"(?<!\\)\$", text)
                 if not protected(m.start())]
    print("unprotected $ count:", len(positions), "odd" if len(positions) % 2 else "even")
    for i, p in enumerate(positions):
        if i >= len(positions) - 1:
            print("LAST $ at %d:" % p)
            print(repr(text[max(0, p - 260):p + 160]))
    # pair them up and report long spans
    for k in range(0, len(positions) - 1, 2):
        a, b = positions[k], positions[k + 1]
        if b - a > 100:
            print("LONG span %d..%d (%d): %r" % (a, b, b - a, text[a:b][:120]))


if __name__ == "__main__":
    main()

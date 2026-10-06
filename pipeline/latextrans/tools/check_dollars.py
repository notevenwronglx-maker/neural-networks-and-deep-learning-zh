#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check $ pairing in the Chinese chapters and show any unbalanced region."""
import glob
import io
import re

ROOT = (r"C:\Users\22713\Desktop\nndl-book\latextrans-run"
        r"\out\ch_nndl-book\nndl-book\chapters\*.tex")

for path in sorted(glob.glob(ROOT)):
    text = io.open(path, encoding="utf-8").read()
    body = text.split(r"\begin{document}")[-1]
    body = body.replace(r"\$", "")
    n = body.count("$")
    print("%-24s $ = %-5d %s" % (path.split("\\")[-1], n,
                                 "ODD <-- unbalanced" if n % 2 else ""))
    if n % 2:
        pos = [m.start() for m in re.finditer(r"\$", body)]
        for k in range(0, min(len(pos), 40), 2):
            a = pos[k]
            b = pos[k + 1] if k + 1 < len(pos) else len(body)
            seg = body[a:b]
            if len(seg) > 120:
                print("     long span %d..%d (%d chars): %r"
                      % (a, b, len(seg), seg[:100]))

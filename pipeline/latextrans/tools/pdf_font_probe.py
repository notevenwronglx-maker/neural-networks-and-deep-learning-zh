#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify that a PDF really embeds its CJK fonts (poppler in this TeX Live has
no CJK language pack, so pdftoppm/pdffonts cannot be trusted here).

Decompresses every FlateDecode stream and reports the font machinery found.

Usage: python tools/pdf_font_probe.py <file.pdf> [--page <n>]
"""
import re
import sys
import zlib
from pathlib import Path

KEYS = [b"/FontFile", b"/FontFile2", b"/FontFile3", b"/Identity-H",
        b"/CIDFontType0", b"/CIDFontType2", b"/Type0", b"/ToUnicode",
        b"/BaseFont"]


def main():
    data = Path(sys.argv[1]).read_bytes()
    print("file size          : %d bytes" % len(data))
    print("compressed streams : %d" % data.count(b"stream"))

    blob = bytearray(data)
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        raw = data[start:end]
        try:
            blob += zlib.decompress(raw)
        except Exception:
            try:
                blob += zlib.decompressobj().decompress(raw)
            except Exception:
                pass

    obj = bytes(blob)
    print("inflated bytes     : %d" % len(obj))
    print("-" * 60)
    for k in KEYS:
        print("  %-14s : %d" % (k.decode(), obj.count(k)))

    names = sorted(set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-_,\.]+)", obj)))
    print("-" * 60)
    print("BaseFont names (%d):" % len(names))
    for n in names[:40]:
        print("   %s" % n.decode("latin-1"))

    # sample of a content stream: are there multi-byte glyph runs?
    tj = re.findall(rb"<([0-9A-Fa-f]{8,})>\s*Tj", obj)
    print("-" * 60)
    print("hex-string Tj runs : %d (first: %s)"
          % (len(tj), tj[0][:60].decode("latin-1") if tj else "-"))

    # FontDescriptor / FontFile presence per font
    ff = re.findall(rb"/FontFile3\s+(\d+)\s+0\s+R", obj)
    ff += re.findall(rb"/FontFile2\s+(\d+)\s+0\s+R", obj)
    ff += re.findall(rb"/FontFile\s+(\d+)\s+0\s+R", obj)
    print("embedded font file refs: %d" % len(ff))


if __name__ == "__main__":
    main()

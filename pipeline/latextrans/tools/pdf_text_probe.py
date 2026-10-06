#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Decisive check that a PDF really carries CJK text.

poppler in this TeX Live lacks its CJK language pack, so pdftoppm/pdffonts
cannot render or even enumerate the fonts.  Instead we inflate every stream and
decode the /ToUnicode CMaps that xeCJK/xdvipdfmx writes next to each embedded
subset font: the destination values of those mappings are the actual Unicode
characters shown on the page.

Usage: python tools/pdf_text_probe.py <file.pdf>
"""
import re
import sys
import zlib
from collections import Counter
from pathlib import Path


def inflate_all(data):
    out = bytearray()
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            out += zlib.decompress(data[start:end])
        except Exception:
            pass
    return bytes(out)


def decode_tounicode(blob):
    chars = []
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", blob, re.DOTALL):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            chars.append(utf16be(dst))
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", blob, re.DOTALL):
        for lo, hi, dst in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            chars.append(utf16be(dst))
    return [c for c in chars if c]


def utf16be(hexbytes):
    try:
        return bytes.fromhex(hexbytes.decode("ascii")).decode("utf-16-be", "ignore")
    except Exception:
        return ""


def main():
    data = Path(sys.argv[1]).read_bytes()
    blob = inflate_all(data)
    print("inflated bytes      : %d" % len(blob))

    cmaps = len(re.findall(rb"beginbfchar|beginbfrange", blob))
    print("ToUnicode CMap blocks: %d" % cmaps)

    chars = decode_tounicode(blob)
    cjk = [c for c in chars if "\u4e00" <= c <= "\u9fff"]
    print("mapped characters   : %d" % len(chars))
    print("  of which CJK      : %d (%.1f%%)"
          % (len(cjk), 100.0 * len(cjk) / max(1, len(chars))))
    print("  distinct CJK      : %d" % len(set(cjk)))
    sample = "".join(sorted(set(cjk))[:60])
    print("  sample            : %s" % sample)

    counts = Counter(cjk)
    print("  most frequent     : %s"
          % "".join(c for c, _ in counts.most_common(20)))

    # sanity: does the doc contain whole Chinese words?
    for probe in ("神经网络", "感知机", "深度学习", "反向传播", "训练样本"):
        print("  contains %-8s: %s" % (probe, probe in "".join(chars)))


if __name__ == "__main__":
    main()

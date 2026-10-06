#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify that \\rm subscripts (a_{\\rm in}, n_{\\rm in}, ...) survived the
ordinal clean-up, which must only remove ^{\\rm th}."""
import glob
import io
import re

EN = r"C:\Users\22713\Desktop\nndl-book\latex\chapters"
ZH = r"C:\Users\22713\Desktop\nndl-book\latex-zh\chapters"

for name in ["chap1", "chap2", "chap3", "chap5", "chap6"]:
    en = io.open("%s\\%s.tex" % (EN, name), encoding="utf-8").read()
    zh = io.open("%s\\%s.tex" % (ZH, name), encoding="utf-8").read()
    for label, text in (("en", en), ("zh", zh)):
        th = len(re.findall(r"\^\{?\\rm\s*th\}?", text))
        sub = len(re.findall(r"_\{?\\rm\s+(?!th)", text))
        print("%-6s %-3s  ^{\\rm th}=%-3d  _\\rm sub=%-3d" % (name, label, th, sub))
    print()

# where did the \\rm subscripts go in chap2?
en = io.open("%s\\chap2.tex" % EN, encoding="utf-8").read()
zh = io.open("%s\\chap2.tex" % ZH, encoding="utf-8").read()
en_subs = re.findall(r"_\{?\\rm\s+[a-zA-Z]+", en)
zh_subs = re.findall(r"_\{?\\rm\s+[a-zA-Z]+", zh)
print("chap2 en subs:", sorted(set(en_subs)), len(en_subs))
print("chap2 zh subs:", sorted(set(zh_subs)), len(zh_subs))
print()
print("chap2 zh n_in count:", zh.count("n_{\\rm in}"), " a_in count:", zh.count("a_{\\rm in}"))
print("chap2 en n_in count:", en.count("n_{\\rm in}"), " a_in count:", en.count("a_{\\rm in}"))
print("chap2 zh n_{in}:", zh.count("n_{in}"), " a_{in}:", zh.count("a_{in}"))

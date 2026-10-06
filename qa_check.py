# -*- coding: utf-8 -*-
"""QA checks for converted chapters.

Usage:  python qa_check.py            (from the repository root)
"""
import os, re, glob, sys

base = os.path.dirname(os.path.abspath(__file__))

RE_ENV = re.compile(r"\\begin\{([a-zA-Z*]+)\}|\\end\{([a-zA-Z*]+)\}")

def top_level_offenders(body):
    """Return True if body has & or \\\\ at env top level."""
    depth = 0
    i = 0
    while i < len(body):
        m = RE_ENV.match(body, i)
        if m:
            depth += 1 if m.group(1) else -1
            i = m.end(); continue
        if depth == 0 and body[i] == "&":
            return True
        if depth == 0 and body[i:i + 2] == "\\\\":
            return True
        i += 1
    return False

issues = 0
for fn in sorted(glob.glob(os.path.join(base, "en", "chapters", "*.tex"))):
    src = open(fn, encoding="utf-8").read()
    name = os.path.basename(fn)
    # 1. equation envs with top-level & or \\\\
    for m in re.finditer(r"\\begin\{equation\}(.*?)\\end\{equation\}", src, re.S):
        if top_level_offenders(m.group(1)):
            issues += 1
            print(f"[{name}] equation with top-level & or rows: {m.group(1)[:70]!r}")
    # 2. stray oindent (an 'oindent' not preceded by 'n' of \noindent)
    for m in re.finditer(r"(?<![n\\])oindent", src):
        issues += 1
        print(f"[{name}] stray 'oindent' at char {m.start()}: {src[max(0,m.start()-30):m.start()+20]!r}")
    # 3. eqnarray remnants
    n = src.count("eqnarray")
    if n:
        issues += n
        print(f"[{name}] eqnarray remnants: {n}")
    # 4. odd number of $ per block
    for i, para in enumerate(src.split("\n\n")):
        if "$" in para and para.count("$") % 2 != 0 and "lstlisting" not in para:
            issues += 1
            print(f"[{name}] odd $ in block {i}: {para[:90]!r}")
    # 5. leftover img tokens
    if "\x01" in src:
        issues += src.count("\x01")
        print(f"[{name}] leftover img tokens")
    # 6. HTML remnants
    for pat in ("<p>", "</p>", "<img", "<div", "&nbsp;", "<em>", "<a href"):
        n = src.count(pat)
        if n:
            issues += n
            print(f"[{name}] HTML remnant {pat!r}: {n}")
    # 7. \footnote containing align/equation (illegal break env in footnote)
    for m in re.finditer(r"\\footnote\{", src):
        depth = 1
        j = m.end()
        while j < len(src) and depth:
            if src[j] == "{": depth += 1
            elif src[j] == "}": depth -= 1
            j += 1
        inner = src[m.end():j - 1]
        if "\\begin{align" in inner or "\\begin{equation" in inner:
            issues += 1
            print(f"[{name}] footnote with display env: {inner[:60]!r}")
print("TOTAL ISSUES:", issues)

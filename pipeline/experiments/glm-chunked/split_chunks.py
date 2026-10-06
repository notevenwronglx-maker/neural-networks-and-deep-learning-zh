# -*- coding: utf-8 -*-
"""Split English chapter .tex files into translation chunks.

Splits only at top-level safe points (sectionTitle / subsectionTitle lines
or blank lines), never inside protected environments.
"""
import os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(BASE, "latex", "chapters")
OUT = os.path.join(BASE, "zh_work", "chunks")
os.makedirs(OUT, exist_ok=True)

CHAPTERS = ["about", "chap1", "chap2", "chap3", "chap4", "chap5", "chap6",
            "sai", "exercises_and_problems", "acknowledgements"]

PROTECT = ["exerciseBox", "lstlisting", "align", "align*", "equation", "equation*",
           "itemize", "enumerate", "table", "movieNote", "quote", "tabular",
           "tikzpicture", "center"]
RE_ENV_LINE = re.compile(r"\\(begin|end)\{([a-zA-Z*]+)\}")
RE_HEADING = re.compile(r"^\\(sub)?sectionTitle\{")

def protected_depth(line, depth):
    for m in RE_ENV_LINE.finditer(line):
        env = m.group(2)
        if env in PROTECT:
            depth += 1 if m.group(1) == "begin" else -1
    return depth

def split_chapter(name):
    src = open(os.path.join(EN, name + ".tex"), encoding="utf-8").read()
    lines = src.split("\n")
    chunks = []
    cur = []
    depth = 0
    size = 0
    for line in lines:
        cur.append(line)
        size += len(line)
        depth = protected_depth(line, depth)
        safe = (depth == 0)
        is_heading = bool(RE_HEADING.match(line.strip()))
        if safe and depth == 0 and (is_heading and size > 1500 or size > 7000):
            chunks.append("\n".join(cur).strip())
            cur, size = [], 0
    if cur and "\n".join(cur).strip():
        chunks.append("\n".join(cur).strip())
    return chunks

def main():
    manifest = []
    for name in CHAPTERS:
        chunks = split_chapter(name)
        for i, ch in enumerate(chunks):
            cid = f"{name}_{i:02d}"
            with open(os.path.join(OUT, cid + ".tex"), "w", encoding="utf-8") as f:
                f.write(ch + "\n")
            manifest.append({"id": cid, "chapter": name, "chars": len(ch)})
    with open(os.path.join(BASE, "zh_work", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    total = sum(m["chars"] for m in manifest)
    print(f"{len(manifest)} chunks, {total} chars total")
    big = [m for m in manifest if m["chars"] > 9000]
    print("oversized chunks:", [(m['id'], m['chars']) for m in big] or "none")

if __name__ == "__main__":
    main()

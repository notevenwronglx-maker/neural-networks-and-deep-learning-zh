# -*- coding: utf-8 -*-
"""Pre-process chunks: extract lstlisting blocks to placeholders (reinserted later)."""
import os, re, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(BASE, "zh_work", "chunks")
STORE = os.path.join(BASE, "zh_work", "codeblocks.json")

RE_CODE = re.compile(r"(\\begin\{lstlisting\}.*?\\end\{lstlisting\})", re.S)

def main():
    store = {}
    for path in sorted(glob.glob(os.path.join(CHUNKS, "*.tex"))):
        cid = os.path.basename(path)[:-4]
        src = open(path, encoding="utf-8").read()
        blocks = []
        def repl(m):
            blocks.append(m.group(1))
            return "\n%%CODEBLOCK_%d%%\n" % (len(blocks) - 1)
        pre = RE_CODE.sub(repl, src)
        if blocks:
            store[cid] = blocks
            open(path, "w", encoding="utf-8").write(pre)
    json.dump(store, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("stripped code from", len(store), "chunks;",
          sum(len(v) for v in store.values()), "blocks total")
    # report remaining sizes
    sizes = sorted(((os.path.basename(p)[:-4], os.path.getsize(p)) for p in glob.glob(os.path.join(CHUNKS, '*.tex'))),
                   key=lambda x: -x[1])[:8]
    print("largest after strip:", sizes)

if __name__ == "__main__":
    main()

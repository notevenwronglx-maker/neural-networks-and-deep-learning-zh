#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dry-run the (patched) LaTeXTrans parser on the NNDL book project.

No LLM calls: this exercises LatexParser.parse() only, then reports the chunk
layout so that oversized sections / unexpected environments can be spotted
before spending any API budget.

Usage:
  python tools/dryrun_parse.py [--project <dir>] [--out <dir>]
"""
import argparse
import json
import sys
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parent.parent
LATEXTRANS = RUN_ROOT / "LaTeXTrans"
sys.path.insert(0, str(LATEXTRANS))

import tiktoken  # noqa: E402
from src.formats.latex.parser import LatexParser  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=str(RUN_ROOT / "input" / "nndl-book"))
    ap.add_argument("--out", default=str(RUN_ROOT / "out" / "_dryrun"))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    parser = LatexParser(args.project, str(out))
    parser.parse()

    enc = tiktoken.encoding_for_model("gpt-4")
    sections = parser.sections_json
    sizes = [(s["section"], len(s["content"]), len(enc.encode(s["content"])))
             for s in sections]
    translated = [s for s in sizes if s[0] not in ("-1", "0")]

    print("\n" + "=" * 78)
    print("SECTION LAYOUT  (%d sections total, %d to translate)"
          % (len(sections), len(translated)))
    print("=" * 78)
    for sid, chars, toks in sizes:
        tag = "  (not translated)" if sid in ("-1", "0") else ""
        print("  %-12s chars=%7d  tokens=%6d%s" % (sid, chars, toks, tag))

    if translated:
        toks = sorted(t[2] for t in translated)
        print("\n  translated-section tokens: min=%d median=%d max=%d total=%d"
              % (toks[0], toks[len(toks) // 2], toks[-1], sum(toks)))
        over = [t for t in sizes if t[0] not in ("-1", "0") and t[2] > 6000]
        print("  sections > 6000 tokens: %d %s"
              % (len(over), [t[0] for t in over]))

    print("\n" + "=" * 78)
    print("INPUTS (%d) / NEWCOMMANDS (%d) / CAPTIONS (%d) / ENVS (%d)"
          % (len(parser.inputs_json), len(parser.newcommands_json),
             len(parser.captions_json), len(parser.envs_json)))
    print("=" * 78)
    for item in parser.inputs_json:
        print("  input   : %s" % item["path"])
    for item in parser.newcommands_json[:20]:
        print("  newcmd  : %s" % item["name"])
    if len(parser.newcommands_json) > 20:
        print("  newcmd  : ... (%d more)" % (len(parser.newcommands_json) - 20))
    for cap in parser.captions_json[:10]:
        print("  caption : %s -> %s" % (cap["cap_type"], cap["content"][:70]))

    from collections import Counter
    env_counter = Counter((e["env_name"], e["need_trans"]) for e in parser.envs_json)
    for (name, need), count in sorted(env_counter.items()):
        print("  env     : %-18s need_trans=%-5s x%d" % (name, need, count))

    # Anything referenced from the untranslated front matter?
    for sid in ("-1", "0"):
        sec = next((s for s in sections if s["section"] == sid), None)
        if sec:
            ph = [e["placeholder"] for e in parser.envs_json
                  if e["placeholder"] in sec["content"]]
            phs = [c["placeholder"] for c in parser.captions_json
                   if c["placeholder"] in sec["content"]]
            print("\n  section %s references envs=%s captions=%s"
                  % (sid, ph, phs))

    meta = {
        "sections": [(s, c, t) for s, c, t in sizes],
        "envs": env_counter_out(env_counter),
        "inputs": [i["path"] for i in parser.inputs_json],
    }
    (out / "dryrun_report.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nwrote %s" % (out / "dryrun_report.json"))


def env_counter_out(counter):
    return [{"env": k[0], "need_trans": k[1], "count": v}
            for k, v in sorted(counter.items())]


if __name__ == "__main__":
    main()

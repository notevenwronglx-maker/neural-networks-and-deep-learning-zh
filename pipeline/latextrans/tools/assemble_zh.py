#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assemble the publishable Chinese edition of NNDL from the LaTeXTrans output.

Steps
  1. read the raw LaTeXTrans project (main.tex + chapters/*.tex + images/)
  2. clean the prose: exerciseBox titles, first-occurrence term glosses,
     half-width sentence stops (see tools/postprocess.py)
  3. optionally build a 术语索引 (terminology index) appendix: every surviving
     \\emph{中文}（english） gloss gets a \\label, and the index lists
     中文术语 / 英文术语 / 首次出现页码 via \\pageref
  4. write the finished project (main-zh.tex + chapters/ + images/) and compile
     it with latexmk -xelatex

Usage:
  python tools/assemble_zh.py --src <latexTrans output project> --dst <target dir>
                              [--no-terminology] [--no-build]
"""
import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from postprocess import (  # noqa: E402
    GLOSS_RE, MATH_SPLIT, fix_periods, normalize_exercise_boxes, audit,
    drop_english_ordinals, normalize_punctuation, normalize_period_spacing,
)

RUN = Path(__file__).resolve().parent.parent

# reading order matters: the first \\emph{...}（...） gloss wins
CHAPTER_ORDER = [
    "chapters/about.tex",
    "chapters/exercises_and_problems.tex",
    "chapters/chap1.tex",
    "chapters/chap2.tex",
    "chapters/chap3.tex",
    "chapters/chap4.tex",
    "chapters/chap5.tex",
    "chapters/chap6.tex",
    "chapters/sai.tex",
    "chapters/acknowledgements.tex",
    "main.tex",
]

TERMINOLOGY_INPUT = r"""
\chapter*{术语索引}
\markboth{术语索引}{}
\phantomsection
\addcontentsline{toc}{chapter}{术语索引}

\begingroup
\small
\renewcommand{\arraystretch}{1.25}
\begin{longtable}{p{0.26\textwidth}p{0.46\textwidth}r}
\textbf{中文术语} & \textbf{英文术语} & \textbf{首次出现页} \\
\hline
\endfirsthead
\multicolumn{3}{l}{\small（续）}\\
\hline
\textbf{中文术语} & \textbf{英文术语} & \textbf{首次出现页} \\
\hline
\endhead
\hline
\endfoot
%s
\end{longtable}
\endgroup
"""


def tex_escape(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"),
                 ("_", r"\_"), ("$", r"\$"), ("{", r"\{"), ("}", r"\}")):
        s = s.replace(a, b)
    return s


def add_term_labels(text, terms):
    """Label every surviving gloss so the index can print its first page."""
    def repl(m):
        zh, en = m.group(1).strip(), m.group(2).strip()
        key = "term:%d" % len(terms)
        # a gloss sitting inside a heading must not carry a \label
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start:text.find("\n", m.start())]
        if re.search(r"\\(chapter|section|subsection|sectionTitle"
                     r"|subsectionTitle|markboth|addcontentsline)", line):
            terms.append((zh, en, None))
            return m.group(0)
        terms.append((zh, en, key))
        return m.group(0) + r"\label{%s}" % key
    return GLOSS_RE.sub(repl, text)


HEADING_CMD = re.compile(
    r"\\(chapter|section|subsection|sectionTitle|subsectionTitle"
    r"|markboth|addcontentsline|label|ref|cite|texttt|url|href)\b")


def fix_heading_arity(text):
    """\\sectionTitle{A}{B} must carry the same text twice.

    The template prints #1 as the heading and puts #2 in the table of contents;
    if the model renders them differently (e.g. $s \\odot t$ vs a Unicode ⊙)
    the TOC and the heading disagree.  Keep the LaTeX-formatted variant.
    """
    n = 0

    def repl(m):
        nonlocal n
        a, b = m.group(1), m.group(2)
        if a.strip() == b.strip():
            return m.group(0)
        n += 1
        rich = a if ("$" in a or "\\" in a) else (b if ("$" in b or "\\" in b) else a)
        return r"\sectionTitle{%s}{%s}" % (rich, rich)

    text = re.sub(r"\\sectionTitle\{([^{}]*)\}\{([^{}]*)\}", repl, text)
    return text, n


def load_glossary_terms(path):
    """Lower-case glossary entries = domain terms (headings start upper-case)."""
    pairs = []
    seen = set()
    for line in io.open(path, encoding="utf-8"):
        parts = re.findall(r'"([^"]*)"', line)
        if len(parts) < 2:
            continue
        en, zh = parts[0].strip(), parts[1].strip()
        if not en or not zh or not en[0].islower() or len(zh) < 2:
            continue
        if zh in seen:
            continue
        seen.add(zh)
        pairs.append((zh, en))
    return pairs


def add_index_labels(text, pairs, terms, done):
    """Add a first-occurrence \\label for glossary terms that were never glossed.

    Only plain running text is touched: math, code and command arguments are
    skipped so that a \\label can never land inside \\texttt{}, a heading or a
    verbatim block.
    """
    from postprocess import PROTECTED_SPLIT
    chunks = PROTECTED_SPLIT.split(text)
    added = 0
    for i, chunk in enumerate(chunks):
        if i % 2:                       # math / verbatim: leave alone
            continue
        lines = chunk.split("\n")
        for li, line in enumerate(lines):
            if HEADING_CMD.search(line):
                continue
            new_line = line
            for zh, en in pairs:
                if zh in done:
                    continue
                pos = new_line.find(zh)
                if pos < 0:
                    continue
                end = pos + len(zh)
                if pos and new_line[pos - 1] == "{" and new_line[end:end + 1] == "}":
                    continue            # a command argument: skip
                key = "term:%d" % len(terms)
                new_line = new_line[:end] + r"\label{%s}" % key + new_line[end:]
                terms.append((zh, en, key))
                done.add(zh)
                added += 1
            lines[li] = new_line
        chunks[i] = "\n".join(lines)
    return "".join(chunks), added


def build_index(terms):
    rows = []
    for zh, en, key in terms:
        page = r"\pageref{%s}" % key if key else "--"
        rows.append("%s & %s & %s \\\\" % (tex_escape(zh), tex_escape(en), page))
    return TERMINOLOGY_INPUT % "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(RUN / "out" / "ch_nndl-book" / "nndl-book"))
    ap.add_argument("--dst", default=str(RUN.parent / "latex-zh"))
    ap.add_argument("--no-terminology", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--glossary",
                    default=str(RUN / "glossary" / "nndl_terms.csv"))
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    if not (src / "main.tex").exists():
        print("!! no main.tex in %s" % src, file=sys.stderr)
        return 1

    # ---- 1. fresh destination, plus images -------------------------------
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    if (src / "images").is_dir():
        shutil.copytree(src / "images", dst / "images")
    (dst / "chapters").mkdir()

    seen_en, seen_zh = set(), set()
    terms = []
    term_done = set()
    glossary_pairs = ([] if args.no_terminology
                      else load_glossary_terms(args.glossary))
    report = {"files": [], "problems": []}
    totals = {"boxes": 0, "glosses": 0, "periods": 0}

    order = [p for p in CHAPTER_ORDER if (src / p).exists()]
    extra = [p for p in sorted(src.rglob("*.tex"))
             if str(p.relative_to(src)).replace("\\", "/") not in CHAPTER_ORDER]
    for rel in order + [str(p.relative_to(src)).replace("\\", "/") for p in extra]:
        tex = src / rel
        text = io.open(tex, encoding="utf-8").read()

        text, n_boxes = normalize_exercise_boxes(text)
        text, n_ordinals = drop_english_ordinals(text)

        dropped = []
        def dedup(m):
            zh, en = m.group(1).strip(), m.group(2).strip()
            if en.lower() in seen_en or zh in seen_zh:
                dropped.append((zh, en))
                return zh
            seen_en.add(en.lower())
            seen_zh.add(zh)
            return m.group(0)
        text = GLOSS_RE.sub(dedup, text)

        n_new_terms = 0
        if not args.no_terminology:
            before = len(terms)
            text = add_term_labels(text, terms)
            n_new_terms = len(terms) - before
            term_done.update(zh for zh, _, _ in terms)

        # Punctuation is only normalised in the document body: the preamble
        # legitimately contains half-width marks in LaTeX constructs such as
        # \ctexset{chapter={name={第,章}}} which must stay untouched.
        marker = r"\begin{document}"
        cut = text.find(marker)
        if cut >= 0:
            head, body = text[:cut + len(marker)], text[cut + len(marker):]
        else:
            head, body = "", text          # chapter files are all body
        body, n_periods = fix_periods(body)
        body, n_punct = normalize_punctuation(body)
        body, n_space = normalize_period_spacing(body)
        body, n_title = fix_heading_arity(body)
        if glossary_pairs:
            body, n_index = add_index_labels(body, glossary_pairs, terms,
                                             term_done)
        else:
            n_index = 0
        text = head + body

        out_rel = "main-zh.tex" if rel == "main.tex" else rel
        out_path = dst / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        io.open(out_path, "w", encoding="utf-8").write(text)

        problems = audit(out_rel, text)
        report["problems"] += ["%s: %s" % (out_rel, p) for p in problems]
        report["files"].append({
            "file": out_rel, "exercise_boxes_fixed": n_boxes,
            "glosses_dropped": len(dropped), "new_terms": n_new_terms,
            "index_terms_added": n_index, "headings_fixed": n_title,
            "ordinals_dropped": n_ordinals, "punctuation_fixed": n_punct,
            "period_spacing_fixed": n_space,
            "periods_fixed": n_periods, "problems": problems,
        })
        totals["boxes"] += n_boxes
        totals["glosses"] += len(dropped)
        totals["periods"] += n_periods
        totals["punctuation"] = totals.get("punctuation", 0) + n_punct
        totals["period_spacing"] = totals.get("period_spacing", 0) + n_space
        totals["ordinals"] = totals.get("ordinals", 0) + n_ordinals
        totals["index_terms"] = totals.get("index_terms", 0) + n_index
        totals["headings_fixed"] = totals.get("headings_fixed", 0) + n_title
        print("  %-38s boxes=%-3d gloss=%-3d term=%-3d new=%-3d ord=%-3d "
              "punct=%-4d spc=%-5d periods=%-5d"
              % (out_rel, n_boxes, len(dropped), n_new_terms, n_index,
                 n_ordinals, n_punct, n_space, n_periods))

    # ---- 2. terminology index -------------------------------------------
    main_zh = dst / "main-zh.tex"
    text = io.open(main_zh, encoding="utf-8").read()
    if not args.no_terminology and terms:
        io.open(dst / "chapters" / "terminology.tex", "w",
                encoding="utf-8").write(build_index(terms))
        # extra packages for the longtable index
        if "\\usepackage{longtable}" not in text:
            text = text.replace(
                "\\usepackage{etoolbox}",
                "\\usepackage{etoolbox}\n\\usepackage{longtable}\n"
                "\\usepackage{array}", 1)
        anchor = "\\input{chapters/sai}"
        block = (anchor + "\n\n\\input{chapters/terminology}\n")
        assert anchor in text, "cannot find the appendix input to anchor the index"
        text = text.replace(anchor, block, 1)
        io.open(main_zh, "w", encoding="utf-8").write(text)
        print("  terminology index: %d entries" % len(terms))

    totals["terms"] = len(terms)
    report["totals"] = totals
    io.open(dst / "qa_report.json", "w", encoding="utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=2))

    print("\ntotals: %s" % totals)
    print("problems: %d" % len(report["problems"]))
    for p in report["problems"][:30]:
        print("   ! %s" % p)

    # ---- 3. compile ------------------------------------------------------
    if args.no_build:
        return 0
    print("\ncompiling with latexmk -xelatex ...")
    cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode",
           "-file-line-error", "-f", "main-zh.tex"]
    res = subprocess.run(cmd, cwd=str(dst), capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    log = (res.stdout or "") + (res.stderr or "")
    io.open(dst / "compile.log", "w", encoding="utf-8").write(log)
    pdf = dst / "main-zh.pdf"
    if pdf.exists():
        print("OK  -> %s (%.2f MB)" % (pdf, pdf.stat().st_size / 1048576))
        return 0
    print("!! compile produced no PDF; see %s" % (dst / "compile.log"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Post-process the raw LaTeXTrans output into a publishable Chinese edition.

Three deterministic clean-ups are applied, all of them things an LLM cannot be
trusted to get right globally:

  1. exerciseBox titles        -> 练习 / 习题   (fixed vocabulary)
  2. \\emph{中文}（english）      -> only the FIRST occurrence of each concept
                                  keeps the Roman-script gloss; later ones are
                                  reduced to plain Chinese, as required by the
                                  mathtranslations.org guide ("同一术语在后文
                                  普通行文中再次出现时…不必再次附注英文")
  3. ideographic full stop 。  -> half-width "."  outside math, per the guide
                                  ("句子末尾统一使用半角英文句点")

It also reports structural problems (chapter/sectionTitle arity, residual
English headings, stray 。 inside math) so they can be fixed by hand.

Usage:
  python tools/postprocess.py --in <dir> --out <dir> [--report <json>]
"""
import argparse
import io
import json
import re
from pathlib import Path

MATH_SPLIT = re.compile(
    r"(\$[^$]*\$"
    r"|\\\[.*?\\\]"
    r"|\\begin\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\}"
    r".*?"
    r"\\end\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\})",
    re.DOTALL,
)

# Math *and* verbatim/code, i.e. everything whose content must stay byte-exact.
# lstlisting bodies contain commas, colons and ! in ASCII code context, so they
# must never be reached by the punctuation normaliser.
PROTECTED_SPLIT = re.compile(
    r"(\$[^$]*\$"
    r"|\\\[.*?\\\]"
    r"|\\begin\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\}"
    r".*?"
    r"\\end\{(?:equation|align|alignat|gather|multline|flalign|eqnarray|split|cases|array)\*?\}"
    r"|\\begin\{(?:lstlisting|verbatim|minted|Verbatim)\*?\}"
    r".*?"
    r"\\end\{(?:lstlisting|verbatim|minted|Verbatim)\*?\}"
    r"|\\[a-zA-Z]*verb\*?[^a-zA-Z].)",
    re.DOTALL,
)

CJK_MIN, CJK_MAX = "\u3400", "\u9fff"

EXERCISE_TITLES = {
    "exercise": "练习", "exercises": "练习",
    "problem": "习题", "problems": "习题",
    "练习": "练习", "习题": "习题",
    "思考题": "习题", "问题": "习题",
}

GLOSS_RE = re.compile(
    r"\\emph\{([^{}]+)\}\s*[（(]\s*([A-Za-z][A-Za-z0-9 .'\-/,]{1,60}?)\s*[）)]"
)


def normalize_exercise_boxes(text):
    """\\begin{exerciseBox}{Exercise} -> \\begin{exerciseBox}{练习}"""
    n = 0

    def repl(m):
        nonlocal n
        title = m.group(1).strip()
        key = title.lower().rstrip(":")
        new = EXERCISE_TITLES.get(key) or EXERCISE_TITLES.get(title)
        if new is None:
            # "Exercise 3" / "Problems 1-5" style
            head = re.split(r"[\s:：]", key, 1)[0]
            new = EXERCISE_TITLES.get(head)
            if new is not None and len(title) > len(head):
                new = new + title[len(head):]
        if new is None or new == title:
            return m.group(0)
        n += 1
        return r"\begin{exerciseBox}{%s}" % new

    text = re.sub(r"\\begin\{exerciseBox\}\{([^{}]*)\}", repl, text)
    return text, n


def dedupe_term_glosses(text):
    """Keep only the first \\emph{中文}（english） gloss for each concept."""
    return dedupe_term_glosses_global(text, set(), set())


def fix_periods(text):
    """Replace 。 with . outside math / code environments."""
    count = 0

    def fix(chunk):
        nonlocal count
        count += chunk.count("。")
        return chunk.replace("。", ".")

    parts = PROTECTED_SPLIT.split(text)
    # one capture group -> odd indices are the protected chunks
    out = [p if i % 2 else fix(p) for i, p in enumerate(parts)]
    return "".join(out), count


HALF_TO_FULL = [(",", "，"), (":", "："), (";", "；"), ("?", "？"),
                ("!", "！")]
CJK_CLASS = r"[\u3400-\u9fff\u3000-\u303f\uff01-\uff60]"


def normalize_period_spacing(text):
    """One space after a sentence-final half-width period before Chinese.

    The house template implements 句末半角句点 as `\\newunicodechar{。}{.\\ }`,
    i.e. period + space; the machine output mixes both spellings, so make it
    uniform.  Decimals (3.5) and dots inside math/code are never touched.
    """
    n = 0

    def fix(chunk):
        nonlocal n
        new = re.sub(r"\.([ \t]*)(?=[\u4e00-\u9fff])", ". ", chunk)
        n += sum(1 for a, b in zip(chunk.split(". "), new.split(". "))
                 if a != b)
        return new

    parts = PROTECTED_SPLIT.split(text)
    out = [p if i % 2 else fix(p) for i, p in enumerate(parts)]
    return "".join(out), n


def normalize_punctuation(text):
    """Turn half-width , : ; ? ! into their full-width forms next to Chinese.

    mathtranslations.org: "中文正文原则上使用中文标点符号；句子末尾统一使用半角
    英文句点".  So every mark except the sentence-final period is full-width.
    The conversion only fires when the mark actually touches a CJK character,
    which leaves numbers (1,000), English name lists (Krizhevsky, Ilya) and
    \\label/\\cite arguments untouched.
    """
    n = 0

    def fix(chunk):
        nonlocal n
        for half, full in HALF_TO_FULL:
            new = re.sub(re.escape(half) + r"[ \t]*(?=" + CJK_CLASS + ")",
                         full, chunk)
            new = re.sub(r"(?<=" + CJK_CLASS + r")[ \t]*" + re.escape(half),
                         full, new)
            n += len(re.findall(re.escape(half), chunk)) - len(
                re.findall(re.escape(half), new))
            chunk = new
        return chunk

    parts = PROTECTED_SPLIT.split(text)
    out = [p if i % 2 else fix(p) for i, p in enumerate(parts)]
    return "".join(out), n


ORDINAL_RE = re.compile(r"\^\{?\\rm\s*th\}?")


def drop_english_ordinals(text):
    """$j^{\\rm th}$ -> $j$.

    The source spells English ordinals inside math mode ("the $j^{\\rm th}$
    neuron").  Chinese expresses the same thing with 第 j 个 and has no ordinal
    superscript, so the suffix is dropped.  Variable names and formula meaning
    are untouched; \\rm subscripts such as a_{\\rm in} / n_{\\rm in} are NOT
    affected because the pattern only matches the literal "th".
    """
    return ORDINAL_RE.subn("", text)


def audit(path, text):
    problems = []
    # --- chapter / heading sanity -----------------------------------------
    for m in re.finditer(r"\\sectionTitle\{([^{}]*)\}\{([^{}]*)\}", text):
        if m.group(1).strip() != m.group(2).strip():
            problems.append("sectionTitle args differ: %r vs %r"
                            % (m.group(1)[:40], m.group(2)[:40]))
    for m in re.finditer(r"\\chapter\*?\{([^{}]*)\}", text):
        title = m.group(1)
        if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{3,}", title):
            problems.append("chapter heading looks untranslated: %r" % title[:60])
    for m in re.finditer(r"\\subsectionTitle\{([^{}]*)\}", text):
        if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{3,}", m.group(1)):
            problems.append("subsectionTitle looks untranslated: %r" % m.group(1)[:60])
    # --- stray full-width stops inside math -------------------------------
    parts = PROTECTED_SPLIT.split(text)
    for i in range(1, len(parts), 2):
        span = parts[i]
        # a real math/code span is short; a long "span" means the regex paired
        # a $ from a code block with one in the prose - not a real problem
        if "。" in span and len(span) < 300:
            problems.append("ideographic full stop inside math: %r"
                            % span[:60].replace("\n", " "))
    # --- leftover placeholders / fences -----------------------------------
    for m in re.finditer(r"<PLACEHOLDER_[^>]*>", text):
        problems.append("residual placeholder: %s" % m.group(0))
    if "```" in text:
        problems.append("markdown code fence present")
    # --- was the file translated at all? ----------------------------------
    stripped = MATH_SPLIT.sub(" ", text)
    stripped = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", stripped)
    stripped = re.sub(r"[{}]", " ", stripped)
    body = "\n".join(l for l in stripped.splitlines()
                     if not l.strip().startswith("%"))
    words = len(re.findall(r"\b[A-Za-z]{3,}\b", body))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    if words > 150 and cjk < words:
        problems.append("file does not look translated (ascii_words=%d cjk=%d)"
                        % (words, cjk))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    report = {"files": [], "totals": {}}

    seen_en, seen_zh = set(), set()
    total_boxes = total_periods = 0
    all_dropped = []
    all_problems = []

    for tex in sorted(src.rglob("*.tex")):
        rel = tex.relative_to(src)
        text = io.open(tex, encoding="utf-8").read()

        text, n_boxes = normalize_exercise_boxes(text)
        # cross-file de-duplication of \\emph{中文}（english） glosses: the sets
        # are shared across every file so the whole book keeps each gloss once
        text, dropped = dedupe_term_glosses_global(text, seen_en, seen_zh)
        text, n_periods = fix_periods(text)

        problems = audit(str(rel), text)

        out_path = dst / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        io.open(out_path, "w", encoding="utf-8").write(text)

        total_boxes += n_boxes
        total_periods += n_periods
        all_dropped += dropped
        all_problems += ["%s: %s" % (rel, p) for p in problems]
        report["files"].append({
            "file": str(rel),
            "exercise_boxes_fixed": n_boxes,
            "glosses_dropped": len(dropped),
            "periods_fixed": n_periods,
            "problems": problems,
        })

    report["totals"] = {
        "exercise_boxes_fixed": total_boxes,
        "glosses_dropped": len(all_dropped),
        "periods_fixed": total_periods,
        "problems": len(all_problems),
    }
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        io.open(args.report, "w", encoding="utf-8").write(
            json.dumps(report, ensure_ascii=False, indent=2))

    print("exercise boxes normalised : %d" % total_boxes)
    print("second glosses dropped    : %d" % len(all_dropped))
    print("full-width stops fixed    : %d" % total_periods)
    print("problems                  : %d" % len(all_problems))
    for p in all_problems[:40]:
        print("   ! %s" % p)
    return 0


def dedupe_term_glosses_global(text, seen_en, seen_zh):
    dropped = []

    def repl(m):
        zh, en = m.group(1).strip(), m.group(2).strip()
        key_en = en.lower()
        if key_en in seen_en or zh in seen_zh:
            dropped.append((zh, en))
            return zh
        seen_en.add(key_en)
        seen_zh.add(zh)
        return m.group(0)

    return GLOSS_RE.sub(repl, text), dropped


if __name__ == "__main__":
    raise SystemExit(main())

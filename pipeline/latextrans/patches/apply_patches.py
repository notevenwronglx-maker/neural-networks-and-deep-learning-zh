#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
apply_patches.py - make the vendored LaTeXTrans copy able to translate a whole
book (as opposed to a single arXiv paper).

The upstream project targets arXiv papers: one main.tex, \\section-based
splitting, ctex injection, 8192-token replies.  This script applies six
surgical patches so that it can digest the NNDL book LaTeX project:

  P1  parser.py        : book-aware section splitting (\\chapter, \\chapter*,
                         \\sectionTitle, \\subsectionTitle in addition to
                         \\section/\\subsection/\\subsubsection)
  P2  utils.py         : keep inline list/exercise environments inside the
                         flowing text instead of extracting them as opaque
                         blocks (better context for the translator)
  P3  reconstruct.py   : never inject \\usepackage[UTF8]{ctex} into a document
                         that already uses a ctex document class
  P4  prompts.py       : append the book / mathtranslations.org house rules to
                         every system prompt
  P5  translator_agent : send "max_tokens" (the OpenAI/DeepSeek parameter)
                         instead of the ignored "max_new_tokens", and lower the
                         sampling temperature for faithful translation
  P6  parser_agent.py  : skip the per-environment "does this need translation?"
                         LLM round trip for the book's known inline environments

Usage:  python patches/apply_patches.py [--root <vendored LaTeXTrans root>]
Idempotent: re-running detects the markers and does nothing.
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent / "LaTeXTrans"


# --------------------------------------------------------------------------
# P1 - book-aware section splitting
# --------------------------------------------------------------------------
NEW_SPLIT = r'''    # --- NNDL patch (P1): commands that start a new translation chunk ------
    SECTION_CMD = (
        r'chapter\*|chapter|sectionTitle|subsectionTitle|subsubsectionTitle'
        r'|section\*|section|subsection\*|subsection|subsubsection\*|subsubsection'
    )
    SECTION_LEVEL = {
        'chapter': 1, 'chapter*': 1,
        'section': 1, 'section*': 1, 'sectionTitle': 1,
        'subsection': 2, 'subsection*': 2, 'subsectionTitle': 2,
        'subsubsection': 3, 'subsubsection*': 3, 'subsubsectionTitle': 3,
    }

    @classmethod
    def _next_section_id(cls, command, section_count, subsection_count,
                         subsubsection_count):
        """Advance the heading counters and return (counts..., section_id)."""
        level = cls.SECTION_LEVEL.get(command, 1)
        if level == 1:
            section_count += 1
            subsection_count = 0
            subsubsection_count = 0
            return (section_count, subsection_count, subsubsection_count,
                    f'{section_count}')
        if level == 2:
            subsection_count += 1
            subsubsection_count = 0
            return (section_count, subsection_count, subsubsection_count,
                    f'{section_count}_{subsection_count}')
        subsubsection_count += 1
        return (section_count, subsection_count, subsubsection_count,
                f'{section_count}_{subsection_count}_{subsubsection_count}')

    def _split_to_sections(self, tex: str) -> Any:
        """
        Split the full tex to sections and generate a json structure for them.

        NNDL patch (P1): upstream only splits on \\section / \\subsection /
        \\subsubsection, which collapses a whole book chapter into a single
        oversized request.  Here \\chapter, \\chapter*, \\sectionTitle and
        \\subsectionTitle are split points as well.  Section "-1" is the
        preamble (never translated) and section "0" is everything between
        \\begin{document} and the first heading (the book's already-Chinese
        front matter, also left untouched).
        """
        full_tex = remove_comments(tex)
        pattern_section = get_command_pattern(self.SECTION_CMD)
        begin_document_pattern = get_begin_document_pattern()
        begin_document_match = begin_document_pattern.search(full_tex)
        preamble = full_tex[:begin_document_match.start()] if begin_document_match else full_tex

        self.sections_json.append({
            "section": "-1",
            "content": preamble,
            "trans_content": preamble
        })

        document = full_tex[begin_document_match.start():] if begin_document_match else full_tex

        first_section_match = pattern_section.search(document)

        if not first_section_match:
            print("There is no section in the full tex.")
            self.sections_json.append({
                "section": "0",
                "content": document,
                "trans_content": ''
            })
            return

        self.sections_json.append({
            "section": "0",
            "content": document[:first_section_match.start()],
            "trans_content": ''
        })

        matches = list(pattern_section.finditer(document))

        section_count = 0
        subsection_count = 0
        subsubsection_count = 0

        last_pos = matches[0].start()
        last_cmd = matches[0].group(1)

        for result in matches[1:]:
            section_count, subsection_count, subsubsection_count, sec_id = \
                self._next_section_id(last_cmd, section_count, subsection_count,
                                      subsubsection_count)
            self.sections_json.append({
                "section": sec_id,
                "content": document[last_pos:result.start()],
                "trans_content": ''
            })
            last_pos = result.start()
            last_cmd = result.group(1)

        section_count, subsection_count, subsubsection_count, sec_id = \
            self._next_section_id(last_cmd, section_count, subsection_count,
                                  subsubsection_count)
        self.sections_json.append({
            "section": sec_id,
            "content": document[last_pos:],
            "trans_content": ''
        })

'''


def patch_parser(root: Path) -> str:
    path = root / "src" / "formats" / "latex" / "parser.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P1)" in src:
        return "P1 parser.py            : already applied"

    start_marker = "    def _split_to_sections(self, tex: str) -> Any:"
    end_marker = "    def _merge_short_sections(self, min_tokens=20):"
    i = src.index(start_marker)
    j = src.index(end_marker)
    src = src[:i] + NEW_SPLIT + src[j:]
    path.write_text(src, encoding="utf-8")
    return "P1 parser.py            : book-aware section splitting installed"


# --------------------------------------------------------------------------
# P2 - keep inline environments in the flowing text
# --------------------------------------------------------------------------
OLD_ENV_LAMBDA = r'''    get_command_env = lambda name: rf"\\begin{spaces}\{{(?!document\b|center\b|proof\b|multicols\b)({name})\}}{spaces}({options})?(.*?)\\end{spaces}\{{\1\}}"'''

NEW_ENV_LAMBDA = r'''    # NNDL patch (P2): inline / structural environments are deliberately NOT
    # extracted, so that lists and exercise boxes stay inside the flowing
    # paragraph the translator sees (upstream skips only document/center/
    # proof/multicols).  Equation, figure, table, ... are still extracted and
    # left untranslated, exactly as upstream does.
    _inline_envs = (
        r'document|center|proof|multicols|enumerate|itemize|description'
        r'|quote|quotation|verse|exerciseBox'
    )
    get_command_env = lambda name: rf"\\begin{spaces}\{{(?!{_inline_envs}\b)({name})\}}{spaces}({options})?(.*?)\\end{spaces}\{{\1\}}"'''

OLD_NO_TRANS_TAIL = (
    "'algorithm', 'algorithmic', 'algorithmicx', 'algorithm2e', "
    "'algorithmicx*', 'algorithmic*', 'algorithm*'"
)
NEW_NO_TRANS_TAIL = (
    "'algorithm', 'algorithmic', 'algorithmicx', 'algorithm2e', "
    "'algorithmicx*', 'algorithmic*', 'algorithm*',\n"
    "                             'movieNote'"
)


def patch_env_pattern(root: Path) -> str:
    path = root / "src" / "formats" / "latex" / "utils.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P2)" in src:
        return "P2 utils.py             : already applied"

    assert OLD_ENV_LAMBDA in src, "P2: get_env_pattern lambda not found verbatim"
    src = src.replace(OLD_ENV_LAMBDA, NEW_ENV_LAMBDA)
    path.write_text(src, encoding="utf-8")
    return "P2 utils.py             : inline environments kept in flowing text"


def patch_no_translate_envs(root: Path) -> str:
    """P2b: \\movieNote carries a file name - never send it to the translator.

    The no_translate_envs list lives in parser.py, not in utils.py.
    """
    path = root / "src" / "formats" / "latex" / "parser.py"
    src = path.read_text(encoding="utf-8")
    if "'movieNote'" in src:
        return "P2b parser.py           : already applied"
    assert OLD_NO_TRANS_TAIL in src, "P2b: no_translate_envs tail not found"
    src = src.replace(OLD_NO_TRANS_TAIL, NEW_NO_TRANS_TAIL)
    path.write_text(src, encoding="utf-8")
    return "P2b parser.py           : movieNote marked untranslatable"


# --------------------------------------------------------------------------
# P3 - do not double-load ctex
# --------------------------------------------------------------------------
OLD_CTEX_CALL = "        tex = add_ctex_package(tex) # zh"
NEW_CTEX_CALL = (
    "        # NNDL patch (P3): a ctexbook/ctexart document class already loads\n"
    "        # ctex; adding \\usepackage[UTF8]{ctex} afterwards raises an option\n"
    "        # clash.  Only inject it for non-ctex documents (upstream behaviour).\n"
    "        if not re.search(r'\\documentclass(?:\\[[^\\]]*\\])?\\{ctex\\w+\\}', tex):\n"
    "            tex = add_ctex_package(tex) # zh"
)


def patch_reconstruct(root: Path) -> str:
    path = root / "src" / "formats" / "latex" / "reconstruct.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P3)" in src:
        return "P3 reconstruct.py       : already applied"

    assert OLD_CTEX_CALL in src, "P3: add_ctex_package call not found"
    src = src.replace(OLD_CTEX_CALL, NEW_CTEX_CALL)
    path.write_text(src, encoding="utf-8")
    return "P3 reconstruct.py       : ctex injection guarded"


# --------------------------------------------------------------------------
# P4 - house style rules appended to every prompt
# --------------------------------------------------------------------------
BOOK_RULES = r'''

# ===========================================================================
# NNDL patch (P4) - book overlay.
# Appended to every translation system prompt.  The rules follow the
# mathtranslations.org guide plus the conventions already recorded in
# zh_work/style_guide.md of the book project.
# ===========================================================================
_BOOK_RULES = r"""
=== PROJECT-SPECIFIC RULES - these OVERRIDE anything conflicting above ===
You are translating the book "Neural Networks and Deep Learning" by
Michael A. Nielsen into simplified Chinese.

R1 PUNCTUATION. Use Chinese punctuation in the Chinese text, with ONE
   exception: a sentence-ending full stop MUST be the half-width ASCII
   period "."  Never emit the ideographic full stop "。" anywhere.
   Opening double quotes must be `` (two backticks) and closing ones ''.
   The source writes ``like this'' so translate it as ``像这样''.
   Punctuation inside formulas follows mathematical convention.
R2 FIDELITY. Never add, delete, merge, split or reorder content. Every source
   sentence must yield exactly one translated sentence. Never add explanations,
   examples, proofs or commentary that are not in the source, and never drop
   anything. If a more natural Chinese phrasing would alter the mathematical
   meaning (quantifiers, logical connectives, hypotheses, negation), keep the
   faithful wording even if it reads slightly stiffer.
R3 TERMINOLOGY. Use the supplied glossary verbatim for every occurrence of the
   listed terms. When a term is formally introduced for the first time within
   the passage you are translating, write \emph{中文术语}（english term） - the
   Chinese inside \emph, the English original in FULL-WIDTH parentheses.
   Afterwards write only the Chinese term, with no \emph and no English gloss.
   Never gloss the same term twice.
R4 NAMES. Keep person names in their original Latin spelling (Nielsen,
   Rosenblatt, McCulloch, Pitts, LeCun, Hinton, ...). Keep MNIST, Python,
   NumPy, GitHub, AWS, IPython, LaTeX, softmax, dropout, ReLU, tanh, sigmoid,
   QWERTY in English. Do not transliterate names.
R5 MATH AND CODE ARE INVARIANT. Never translate or reformat anything inside
   $...$, \[...\], \(...\), equation / align / gather / array / cases
   environments, \mbox{...} used inside math, \label{}, \ref{}, \eqref{},
   \cite{}, \tag{}, \includegraphics[...]{...}, lstlisting bodies, file names,
   code identifiers and \texttt{...} contents. Preserve \tag{N} exactly.
R6 TEMPLATE MACROS. Keep the syntax, translate the arguments:
   \sectionTitle{A}{B} and \subsectionTitle{A}{B}: replace BOTH arguments with
   the SAME Chinese heading, taken from the heading glossary when present.
   \begin{exerciseBox}{Exercises} -> \begin{exerciseBox}{练习};
   {Exercise} -> {练习}; {Problem} -> {习题}; {Problems} -> {习题}.
   \movieNote{...} and \inlineImg{...}: keep the argument exactly as it is.
   Keep \noindent exactly where it appears.
R7 VOICE. The author writes in a friendly, conversational first-person voice
   ("I", "we", "you"). Preserve that register in Chinese: 我 / 我们 / 你
   (never 您). Aim for idiomatic Chinese science writing, but never at the
   expense of R2.
R8 LAYOUT. Preserve every blank line and the paragraph structure. Do not turn
   a paragraph into a list or vice versa.
R9 OUTPUT. Emit only the translated LaTeX. No code fences, no preamble, no
   commentary, no trailing remarks.
"""

_PROMPTS_WITH_BOOK_RULES = (
    "caption_system_prompt",
    "section_system_prompt",
    "env_system_prompt",
    "caption_system_prompt_with_dict",
    "section_system_prompt_with_dict",
    "env_system_prompt_with_dict",
)


def _apply_book_rules():
    """NNDL patch (P4): append the house rules to every built prompt."""
    g = globals()
    for _name in _PROMPTS_WITH_BOOK_RULES:
        _value = g.get(_name)
        if isinstance(_value, str) and "PROJECT-SPECIFIC RULES" not in _value:
            g[_name] = _value + _BOOK_RULES


_init_prompts_base = init_prompts


def init_prompts(source_lang, target_lang):
    """NNDL patch (P4): build the upstream prompts, then add the book rules."""
    _init_prompts_base(source_lang, target_lang)
    _apply_book_rules()
'''


def patch_prompts(root: Path) -> str:
    path = root / "src" / "formats" / "latex" / "prompts.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P4)" in src:
        return "P4 prompts.py           : already applied"
    src = src.rstrip("\n") + "\n" + BOOK_RULES
    path.write_text(src, encoding="utf-8")
    return "P4 prompts.py           : house rules appended to every prompt"


# --------------------------------------------------------------------------
# P5 - real token limit + faithful sampling
# --------------------------------------------------------------------------
def patch_translator(root: Path) -> str:
    path = root / "src" / "agents" / "tool_agents" / "translator_agent.py"
    src = path.read_text(encoding="utf-8")
    changed = []
    if '"max_new_tokens": 8192' in src:
        n = src.count('"max_new_tokens": 8192')
        src = src.replace('"max_new_tokens": 8192', '"max_tokens": 8192')
        changed.append("max_tokens x%d" % n)
    if '"temperature": 0.7' in src:
        n = src.count('"temperature": 0.7')
        src = src.replace('"temperature": 0.7', '"temperature": 0.3')
        changed.append("temperature x%d" % n)
    if not changed:
        return "P5 translator_agent.py  : already applied"
    path.write_text(src, encoding="utf-8")
    return "P5 translator_agent.py  : " + ", ".join(changed)


# --------------------------------------------------------------------------
# P6 - skip the judge round trip for known inline environments
# --------------------------------------------------------------------------
OLD_JUDGE_HEAD = r'''    def _request_llm_for_judge(self, system_prompt: str, text: str) -> bool:
        """
        Request the api to set need trans for env
        """
'''

NEW_JUDGE_HEAD = OLD_JUDGE_HEAD + r'''        # NNDL patch (P6): these environments always contain prose that has to
        # be translated; answering locally avoids one sequential LLM round trip
        # per list / exercise box.
        _head = text.lstrip()[:40]
        for _marker in ('\\begin{exerciseBox}', '\\begin{enumerate}',
                        '\\begin{itemize}', '\\begin{description}',
                        '\\begin{quote}', '\\begin{quotation}'):
            if _head.startswith(_marker):
                return True

'''


def patch_parser_agent(root: Path) -> str:
    path = root / "src" / "agents" / "tool_agents" / "parser_agent.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P6)" in src:
        return "P6 parser_agent.py      : already applied"

    assert OLD_JUDGE_HEAD in src, "P6: _request_llm_for_judge header not found"
    src = src.replace(OLD_JUDGE_HEAD, NEW_JUDGE_HEAD)
    path.write_text(src, encoding="utf-8")
    return "P6 parser_agent.py      : local judgement for inline environments"


# --------------------------------------------------------------------------
# P7 - split oversized sections before translating them
# --------------------------------------------------------------------------
P7_ANCHOR = "    def _merge_short_sections(self, min_tokens=20):"

P7_CODE = r'''    # --- NNDL patch (P7): long-section splitter ---------------------------
    MAX_SECTION_TOKENS = 3200

    @staticmethod
    def _env_delta(paragraph):
        """Net \\begin{...} minus \\end{...} (plus \\[ / \\]) in a paragraph."""
        delta = 0
        delta += len(re.findall(r'\\begin\s*\{', paragraph))
        delta -= len(re.findall(r'\\end\s*\{', paragraph))
        delta += len(re.findall(r'\\\[', paragraph))
        delta -= len(re.findall(r'\\\]', paragraph))
        return delta

    @classmethod
    def _chunk_tex(cls, text, max_tokens, enc):
        """Cut a section into <= max_tokens parts, only on blank lines that are
        outside every LaTeX environment / display-math block."""
        paragraphs = re.split(r'\n[ \t]*\n', text)
        parts = []
        buf = []
        buf_tokens = 0
        depth = 0
        for para in paragraphs:
            para_tokens = len(enc.encode(para))
            if buf and depth == 0 and buf_tokens + para_tokens > max_tokens:
                parts.append("\n\n".join(buf))
                buf = []
                buf_tokens = 0
            buf.append(para)
            buf_tokens += para_tokens
            depth += cls._env_delta(para)
            if depth < 0:
                depth = 0
        if buf:
            parts.append("\n\n".join(buf))
        return parts

    def _split_long_sections(self, max_tokens=None):
        """NNDL patch (P7): keep every request comfortably inside the model's
        reply budget.  Long sections are cut on paragraph boundaries only, and
        never inside an environment, so the reconstructed document is still
        byte-for-byte the concatenation of the translated parts."""
        max_tokens = max_tokens or self.MAX_SECTION_TOKENS
        enc = tiktoken.encoding_for_model("gpt-4")
        out = []
        for sec in self.sections_json:
            if sec["section"] in ("-1", "0"):
                out.append(sec)
                continue
            if len(enc.encode(sec["content"])) <= max_tokens:
                out.append(sec)
                continue
            parts = self._chunk_tex(sec["content"], max_tokens, enc)
            if len(parts) <= 1:
                out.append(sec)
                continue
            print("  [P7] section %s (%d tokens) -> %d parts"
                  % (sec["section"], len(enc.encode(sec["content"])), len(parts)))
            for k, part in enumerate(parts, start=1):
                out.append({
                    "section": "%s#%d" % (sec["section"], k),
                    "content": part,
                    "trans_content": "",
                })
        self.sections_json = out

'''


def patch_long_sections(root: Path) -> str:
    path = root / "src" / "formats" / "latex" / "parser.py"
    src = path.read_text(encoding="utf-8")
    if "NNDL patch (P7)" in src:
        return "P7 parser.py           : already applied"

    # hook the splitter into parse()
    hook_old = "        self._split_to_sections(full_tex)\n"
    assert hook_old in src, "P7: split_to_sections call not found"
    src = src.replace(
        hook_old,
        hook_old + "        self._split_long_sections()  # NNDL patch (P7)\n",
        1,
    )
    # and define the helper methods just before _merge_short_sections
    assert P7_ANCHOR in src, "P7: _merge_short_sections anchor not found"
    src = src.replace(P7_ANCHOR, P7_CODE + P7_ANCHOR, 1)
    path.write_text(src, encoding="utf-8")
    return "P7 parser.py           : oversized sections split at paragraph bounds"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    args = ap.parse_args()
    root = Path(args.root)
    if not (root / "main.py").exists():
        print("!! not a LaTeXTrans checkout: %s" % root, file=sys.stderr)
        return 1
    for fn in (patch_parser, patch_env_pattern, patch_no_translate_envs,
               patch_reconstruct, patch_prompts, patch_translator,
               patch_parser_agent, patch_long_sections):
        print(fn(root))
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

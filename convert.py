# -*- coding: utf-8 -*-
"""Convert Nielsen's Neural Networks and Deep Learning HTML -> LaTeX.

Site facts (verified against source):
- inline math: $...$ (raw LaTeX in text nodes)
- display math: \\begin{eqnarray}...\\end{eqnarray} (+ optional \\tag{N})
- figures: <p><center><img src="images/x.png" width="Npx"></center></p>
- content column width: 600px
- margin notes: <span class="marginnote">...</span>  (Nielsen's footnotes)
- exercises: h4 headings titled Exercise/Exercises/Problem/Problems
- other h4: sub-subsection headings
- h3: section headings
- code: <pre> + Pygments spans
"""
import os, re, shutil, html as html_mod
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src_html")
# In this repository the English LaTeX edition lives in en/ (it used to be
# latex/ in the authoring workspace); everything else is unchanged.
OUT = os.path.join(BASE, "en")
CHAPTERS = [
    ("about.html", "preface"),
    ("chap1.html", "chapter"), ("chap2.html", "chapter"), ("chap3.html", "chapter"),
    ("chap4.html", "chapter"), ("chap5.html", "chapter"), ("chap6.html", "chapter"),
    ("sai.html", "appendix"),
    ("exercises_and_problems.html", "backmatter"),
    ("acknowledgements.html", "backmatter"),
]
CONTENT_W = 600.0  # site content column px
warnings = []

def warn(page, msg):
    warnings.append(f"[{page}] {msg}")

RE_EQNARRAY = re.compile(r"\\begin\{(eqnarray\*?)\}.*?\\end\{\1\}", re.S)

# ---------------- text-level helpers ----------------

def unescape(s):
    return html_mod.unescape(s)

SPECIALS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#",
    "_": r"\_\allowbreak{}", "{": r"\{", "}": r"\}",
    "^": r"\textasciicircum{}", "~": r"\textasciitilde",
}

def escape_prose(s):
    return "".join(SPECIALS.get(ch, ch) for ch in s)

def split_math_text(s, page):
    """Split a text node into (is_math, text) segments on $...$ pairs."""
    segs = []
    i, n = 0, len(s)
    while i < n:
        j = s.find("$", i)
        if j == -1:
            segs.append((False, s[i:])); break
        if j > i:
            segs.append((False, s[i:j]))
        k = s.find("$", j + 1)
        if k == -1:
            warn(page, "odd $ in text: %r" % s[max(0, j - 40):j + 40])
            segs.append((False, s[j:])); break
        segs.append((True, s[j:k + 1]))
        i = k + 1
    return [x for x in segs if x[1] != ""]

def _escape_text_with_math(s, page):
    parts = []
    for is_math, seg in split_math_text(s, page):
        parts.append(seg if is_math else escape_prose(seg))
    return "".join(parts)

def text_to_latex(s, page):
    """Convert a plain text node (may contain $math$ and eqnarray displays) to LaTeX."""
    s = unescape(s)
    s = re.sub(r"\s+", " ", s)
    parts = []
    pos = 0
    for m in RE_EQNARRAY.finditer(s):
        if m.start() > pos:
            parts.append(_escape_text_with_math(s[pos:m.start()], page))
        parts.append(m.group(0))  # display math passes through untouched
        pos = m.end()
    if pos < len(s):
        parts.append(_escape_text_with_math(s[pos:], page))
    return "".join(parts)

# ---------------- eqnarray -> align/equation ----------------

RE_ENV_BOUND = re.compile(r"\\begin\{([a-zA-Z*]+)\}|\\end\{([a-zA-Z*]+)\}")

def fix_alignment(body):
    """Top-level '& mid &' -> amsmath '&mid', skipping nested environments."""
    out = []
    depth = 0
    i = 0
    pat = re.compile(r"&\s*([^&\s](?:[^&]*?[^&\s])?)\s*&")
    while i < len(body):
        m = RE_ENV_BOUND.match(body, i)
        if m:
            depth += 1 if m.group(1) else -1
            out.append(m.group(0)); i = m.end(); continue
        ch = body[i]
        if ch == "&" and depth == 0:
            m2 = pat.match(body, i)
            if m2:
                out.append(" &" + m2.group(1) + " ")
                i = m2.end(); continue
        out.append(ch); i += 1
    return "".join(out)

def strip_top_level_align(body):
    """Remove top-level & alignment chars (keep those inside nested envs like array)."""
    out = []
    depth = 0
    i = 0
    while i < len(body):
        m = RE_ENV_BOUND.match(body, i)
        if m:
            depth += 1 if m.group(1) else -1
            out.append(m.group(0)); i = m.end(); continue
        if body[i] == "&" and depth == 0:
            i += 1; continue
        out.append(body[i]); i += 1
    return "".join(out)

def display_to_latex(whole, page):
    """whole: raw \\begin{eqnarray}...\\end{eqnarray} text -> LaTeX display block."""
    star = False
    bm = re.match(r"\\begin\{(eqnarray\*?)\}(.*)\\end\{\1\}$", whole, re.S)
    if not bm:
        return whole
    star = bm.group(1).endswith("*")
    body = bm.group(2)
    body = re.sub(r"<a class=\"displaced_anchor\"[^>]*></a>", "", body)
    body = fix_alignment(body)
    has_tag = re.search(r"\\tag\{([^}]*)\}", body)
    tagtext = has_tag.group(1) if has_tag else None

    def split_rows(body):
        parts, depth, last, i = [], 0, 0, 0
        while i < len(body):
            m = RE_ENV_BOUND.match(body, i)
            if m:
                depth += 1 if m.group(1) else -1
                i = m.end(); continue
            if depth == 0 and body[i:i + 2] == "\\\\":
                parts.append(body[last:i]); last = i + 2; i += 2; continue
            i += 1
        parts.append(body[last:])
        return parts

    rows = split_rows(body)
    nrows = len(rows)
    if star:
        return "\\begin{align*}\n%s\n\\end{align*}" % body.strip()
    if tagtext and nrows == 1:
        inner = re.sub(r"\\tag\{[^}]*\}", "", body).strip()
        inner = re.sub(r"\\nonumber\b\s*", "", inner)
        inner = strip_top_level_align(inner)
        inner = re.sub(r"  +", " ", inner)
        return "\\begin{equation}\n%s\n\\tag{%s}\n\\end{equation}" % (inner, tagtext)
    if tagtext:
        fixed = []
        for idx, r in enumerate(rows):
            if ("\\tag" not in r) and ("\\nonumber" not in r):
                if not (idx == nrows - 1 and "\\tag" in body):
                    r = r.rstrip() + " \\nonumber "
            fixed.append(r)
        return "\\begin{align}\n%s\n\\end{align}" % " \\\\ ".join(fixed).strip()
    return "\\begin{align*}\n%s\n\\end{align*}" % body.strip()

def display_to_inline(whole):
    """Convert a display eqnarray to inline math (for footnotes)."""
    bm = re.match(r"\\begin\{eqnarray\*?\}(.*)\\end\{eqnarray\*?\}$", whole, re.S)
    if not bm:
        return whole
    body = bm.group(1)
    body = re.sub(r"\\tag\{[^}]*\}", "", body)
    body = re.sub(r"\\nonumber\b\s*", "", body)
    body = strip_top_level_align(body)
    # join rows with \quad
    rows, depth, last, i = [], 0, 0, 0
    while i < len(body):
        m = RE_ENV_BOUND.match(body, i)
        if m:
            depth += 1 if m.group(1) else -1
            i = m.end(); continue
        if depth == 0 and body[i:i + 2] == "\\\\":
            rows.append(body[last:i]); last = i + 2; i += 2; continue
        i += 1
    rows.append(body[last:])
    joined = " \\quad ".join(r.strip(" \t\n") for r in rows if r.strip())
    return "$" + joined.strip() + "$"

def split_display_math(s):
    """Split raw text into [(kind, text)] with kind in {'text','display'}."""
    segs, pos = [], 0
    for m in RE_EQNARRAY.finditer(s):
        if m.start() > pos:
            segs.append(("text", s[pos:m.start()]))
        segs.append(("display", m.group(0)))
        pos = m.end()
    if pos < len(s):
        segs.append(("text", s[pos:]))
    return segs

# ---------------- image sizing ----------------

def img_width_option(px):
    if not px:
        return r"width=0.9\textwidth"
    frac = min(px / CONTENT_W, 1.0)
    return r"width=%.3f\textwidth" % frac

def img_is_content(src):
    return src.startswith("images/") and "play.png" not in src

# ---------------- inline walking ----------------

def get_text_prespace(tag):
    return unescape(tag.get_text())

def inline_walk(node, page, ctx=None):
    if ctx is None:
        ctx = {}
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        s = str(node)
        if re.sub(r"\s+", "", s) == "":
            return " " if s else ""
        return text_to_latex(s, page)
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    cls = node.get("class") or []
    if name in ("script", "style", "form", "input", "noscript", "button", "iframe"):
        return ""
    if name == "span" and "marginnote" in cls:
        inner = "".join(inline_walk(c, page, ctx) for c in node.children).strip()
        inner = re.sub(r"^[\*\u2042]\s*", "", inner)
        inner = re.sub(r"\s+", " ", inner)
        inner = RE_EQNARRAY.sub(lambda m: display_to_inline(m.group(0)), inner)
        return r"\footnote{" + inner + "}"
    if name == "span" and "sidebar_title" in cls:
        return ""
    if name in ("em", "i"):
        inner = "".join(inline_walk(c, page, ctx) for c in node.children).strip()
        return r"\emph{" + inner + "}" if inner else ""
    if name in ("strong", "b"):
        inner = "".join(inline_walk(c, page, ctx) for c in node.children).strip()
        return r"\textbf{" + inner + "}" if inner else ""
    if name in ("tt", "code"):
        return r"\texttt{" + escape_prose(unescape(node.get_text())) + "}"
    if name == "a":
        return "".join(inline_walk(c, page, ctx) for c in node.children)
    if name == "img":
        src = node.get("src", "")
        if img_is_content(src):
            pxs = node.get("width", "")
            px = int(re.sub(r"[^0-9]", "", pxs)) if pxs else None
            if px and px <= 40:
                return r"\inlineImg{" + src + "}"
            # images sitting in plain text: treat as display block via marker
            return "\x01IMG\x02" + src + "\x01W\x02" + str(px or 0) + "\x01END\x02"
        return ""
    if name == "br":
        return r"\\ "
    if name in ("span", "small", "sub", "sup", "big", "font"):
        return "".join(inline_walk(c, page, ctx) for c in node.children)
    return "".join(inline_walk(c, page, ctx) for c in node.children)

RE_IMG_TOKEN = re.compile(r"\x01IMG\x02(.+?)\x01W\x02(\d+)\x01END\x02")

def inline_latex_to_stream(s, stream, pid):
    """Convert inline-walked text into stream items, extracting img markers and displays."""
    pos = 0
    for m in RE_IMG_TOKEN.finditer(s):
        if m.start() > pos:
            _push_inline_text(s[pos:m.start()], stream, pid)
        stream.append(("img", m.group(1), int(m.group(2)), pid))
        pos = m.end()
    if pos < len(s):
        _push_inline_text(s[pos:], stream, pid)

def _push_inline_text(s, stream, pid):
    segs = split_display_math(s)
    for kind, val in segs:
        val = val.strip()
        if not val:
            continue
        if kind == "display":
            stream.append(("display", display_to_latex(val, "page"), pid))
        else:
            stream.append(("text", val, pid))

# ---------------- continuation logic ----------------

TERMINAL_RE = re.compile(r"[.!?][\"'\u201d\u2019)\]]*$")

def para_is_continuation(prev_text, next_text):
    prev = prev_text.rstrip()
    nxt = next_text.lstrip()
    if not prev or not nxt:
        return False
    # ignore trailing latex commands / math for the terminal test
    prev_bare = re.sub(r"(\\[a-zA-Z]+\{[^{}]*\}|\$[^$]*\$)+$", "", prev).rstrip()
    terminal = bool(TERMINAL_RE.search(prev_bare)) or bool(TERMINAL_RE.search(prev))
    starts_lower = nxt[0].islower() or nxt[0] in "$\\(\u2018\u201c"
    return (not terminal) or starts_lower

# ---------------- emitter ----------------

class Emitter:
    """Two-phase: build a stream of items, then merge into paragraphs."""

    def __init__(self, page):
        self.page = page
        self.stream = []      # ('text', latex, pid) | ('img', src, px, pid)
                              # | ('display', latex, pid) | ('movie', name, pid)
                              # | ('frozen', latex)
        self.out = []

    # ---------- phase 1: stream building ----------
    def emit_block(self, node, pid=None):
        page = self.page
        if pid is None:
            pid = id(node)
        if isinstance(node, NavigableString):
            if isinstance(node, Comment):
                return ""
            t = str(node)
            if t.strip():
                inline_latex_to_stream(text_to_latex(t, page), self.stream, pid)
            return
        if not isinstance(node, Tag):
            return
        name = node.name.lower()
        cls = node.get("class") or []
        if name in ("script", "style", "form", "input", "noscript", "button",
                    "iframe", "link", "meta", "head", "title"):
            return
        if name == "div" and "footer" in cls:
            return
        if node.get("id") in ("toc", "disqus_thread"):
            return
        if name == "div" and "header" in cls:
            return
        if name == "div" and "nonumber_header" in cls:
            return
        if name == "p" and "sidebar" in cls:
            return
        if name == "p" or name == "h6":
            plain = node.get_text(strip=True).lower()
            if any(pat in plain for pat in DROP_PATTERNS):
                return
            if plain in (".", "..", "..."):
                return
            if not node.get_text(strip=True):
                has_img = any(isinstance(c, Tag) and c.name.lower() == "img"
                              and img_is_content(c.get("src", ""))
                              for c in node.descendants)
                if has_img:
                    self.emit_block_children(node, id(node))
                return
            inline_latex_to_stream("".join(inline_walk(c, page) for c in node.children),
                                   self.stream, id(node))
            return
        if name == "h3":
            self.flush()
            tex = inline_walk_title(node)
            self.emit_frozen("\n\n\\sectionTitle{" + tex + "}{" + pdf_plain(tex) + "}\n")
            return
        if name == "h4":
            t = re.sub(r"\s+", " ", node.get_text()).strip()
            if t.lower().rstrip(":") in EXERCISE_TITLES:
                self.emit_exercise_box(node)
            else:
                self.flush()
                tex = inline_walk_title(node)
                self.emit_frozen("\n\n\\subsectionTitle{" + tex + "}{" + pdf_plain(tex) + "}\n")
            return
        if name == "center":
            vids = node.find_all("video")
            imgs = [c for c in node.find_all("img") if img_is_content(c.get("src", ""))]
            if imgs:
                for im in imgs:
                    pxs = im.get("width", "")
                    px = int(re.sub(r"[^0-9]", "", pxs)) if pxs else None
                    self.stream.append(("img", im.get("src", ""), px, pid))
            elif vids:
                self.stream.append(("movie", self.video_name(vids[0]), pid))
            else:
                txt = "".join(inline_walk(c, page) for c in node.children).strip()
                if txt:
                    inline_latex_to_stream(txt, self.stream, id(node))
            return
        if name == "video":
            self.stream.append(("movie", self.video_name(node), pid))
            return
        if name == "pre":
            self.flush()
            code = get_text_prespace(node)
            self.emit_frozen("\n\n\\begin{lstlisting}\n" + code + "\n\\end{lstlisting}\n")
            return
        if name == "div" and "highlight" in cls:
            self.flush()
            for c in node.find_all("pre"):
                code = get_text_prespace(c)
                self.emit_frozen("\n\n\\begin{lstlisting}\n" + code + "\n\\end{lstlisting}\n")
            return
        if name == "ul":
            self.flush()
            self.emit("\n\n\\begin{itemize}\n")
            for li in node.find_all("li", recursive=False):
                self.emit_list_item(li)
            self.emit("\\end{itemize}\n")
            return
        if name == "ol":
            self.flush()
            self.emit("\n\n\\begin{enumerate}\n")
            for li in node.find_all("li", recursive=False):
                self.emit_list_item(li)
            self.emit("\\end{enumerate}\n")
            return
        if name == "table":
            self.flush()
            self.emit_table(node)
            return
        if name == "hr":
            return
        if name == "blockquote":
            self.flush()
            inner = "".join(inline_walk(c, page) for c in node.children).strip()
            self.emit_frozen("\n\n\\begin{quote}\n" + inner + "\n\\end{quote}\n")
            return
        self.emit_block_children(node, pid)

    def emit_block_children(self, node, pid):
        for c in node.children:
            self.emit_block(c, pid)

    def video_name(self, vtag):
        srcs = [s.get("src", "") for s in vtag.find_all("source")]
        n = os.path.basename(srcs[0]) if srcs else "movie"
        return escape_prose(re.sub(r"\.(webm|mp4)$", "", n))

    def emit_frozen(self, latex):
        self.out.append(latex)

    def emit(self, s):
        self.out.append(s)

    def emit_list_item(self, li):
        inner = "".join(inline_walk(c, self.page) for c in li.children).strip()
        segs = split_display_math(inner)
        imgs = [im for im in li.find_all("img") if img_is_content(im.get("src", ""))]
        if len(segs) <= 1 and not imgs:
            self.emit("\\item " + (segs[0][1].strip() if segs else inner) + "\n")
            return
        self.emit("\\item ")
        for kind, val in segs:
            val = val.strip()
            if not val:
                continue
            if kind == "display":
                self.emit("\n" + display_to_latex(val, self.page) + "\n")
            else:
                self.emit(val + "\n")
        for im in imgs:
            src = im.get("src", "")
            pxs = im.get("width", "")
            px = int(re.sub(r"[^0-9]", "", pxs)) if pxs else None
            self.emit("\n\\begin{center}\n\\includegraphics[" + img_width_option(px)
                      + "]{" + src + "}\n\\end{center}\n")
        self.emit("\n")

    def emit_exercise_box(self, h4tag):
        page = self.page
        title = re.sub(r"\s+", " ", h4tag.get_text()).strip()
        parent = h4tag.parent
        siblist = list(parent.children)
        i = siblist.index(h4tag)
        sibs = []
        j = i + 1
        while j < len(siblist):
            s = siblist[j]
            if isinstance(s, Tag) and s.name.lower() in ("h3", "h4"):
                break
            sibs.append(s)
            j += 1
        sub = Emitter(page)
        for s in sibs:
            sub.emit_block(s)
        sub.flush()
        body = "\n".join(x for x in sub.out if x.strip())
        # remove the consumed siblings from the parent so the outer walk skips them
        for s in sibs:
            s.extract()
        self.flush()
        self.emit_frozen("\n\n\\begin{exerciseBox}{" + inline_walk_title(h4tag) + "}\n"
                         + body + "\n\\end{exerciseBox}\n")

    def emit_table(self, tag):
        rows = []
        for tr in tag.find_all("tr"):
            cells = ["".join(inline_walk(c, self.page) for c in cell.children).strip()
                     for cell in tr.find_all(["td", "th"])]
            rows.append(cells)
        if not rows:
            return
        ncol = max(len(r) for r in rows)
        self.emit("\n\n\\begin{table}[htbp]\n\\centering\n\\small\n"
                  "\\begin{tabular}{" + "c" * ncol + "}\n\\toprule\n")
        for ridx, r in enumerate(rows):
            r = r + [""] * (ncol - len(r))
            self.emit(" & ".join(r) + " \\\\\n")
            if ridx == 0:
                self.emit("\\midrule\n")
        self.emit("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    # ---------- phase 2: stream merging ----------
    def flush(self):
        """Merge stream items into paragraphs and append to out."""
        if not self.stream:
            return
        paras = []
        cur = None            # {"items": [...], "cont": bool, "last_pid": pid|None}
        last_item = None      # ("text", txt, pid) | ("block", prev_text)

        def start(txt, cont, pid):
            return {"items": [("text", txt)], "cont": cont, "last_pid": pid}

        for item in self.stream:
            kind = item[0]
            if kind == "text":
                txt, pid = item[1], item[2]
                if cur is None:
                    cont = (last_item is not None and last_item[0] == "block"
                            and last_item[1] and para_is_continuation(last_item[1], txt))
                    cur = start(txt, cont, pid)
                elif cur["items"][-1][0] == "text":
                    if cur["last_pid"] == pid:
                        cur["items"].append(("text", txt))
                    elif para_is_continuation(cur["items"][-1][1], txt):
                        cur["items"].append(("text", txt))
                        cur["last_pid"] = pid
                    else:
                        paras.append(cur)
                        cur = start(txt, False, pid)
                else:  # last item in cur is a block
                    prev_text = self.last_text_of(cur)
                    if prev_text and para_is_continuation(prev_text, txt):
                        cur["items"].append(("text", txt))
                        cur["last_pid"] = pid
                    else:
                        paras.append(cur)
                        cur = start(txt, False, pid)
                last_item = ("text", txt, pid)
            else:
                if kind == "img":
                    blk = ("img", item[1], item[2])
                elif kind == "display":
                    blk = ("display", item[1])
                else:
                    blk = ("movie", item[1])
                if cur is None:
                    cur = {"items": [("block", blk)], "cont": False, "last_pid": None}
                else:
                    cur["items"].append(("block", blk))
                last_item = ("block", self.last_text_of(cur) or "")
        if cur is not None:
            paras.append(cur)

        for p in paras:
            self.render_para(p)
        self.stream = []

    def last_text_of(self, para):
        for k, v in reversed(para["items"]):
            if k == "text":
                return v
        return None

    def render_para(self, p):
        body = ""
        prev_kind = None
        for k, v in p["items"]:
            if k == "text":
                if prev_kind is None:
                    body += v
                elif prev_kind == "text":
                    body += " " + v
                else:
                    body += "\\noindent " + v
            else:
                if v[0] == "img":
                    body += "\n\n\\begin{center}\n\\includegraphics["
                    body += img_width_option(v[2]) + "]{" + v[1] + "}\n\\end{center}\n\n"
                elif v[0] == "display":
                    body += "\n\n" + v[1] + "\n\n"
                else:
                    body += "\n\n\\begin{movieNote}{" + v[1] + "}\n\\end{movieNote}\n\n"
            prev_kind = k
        body = re.sub(r"[ \t]+\n", "\n", body).strip()
        if not body:
            return
        if p["cont"]:
            body = "\\noindent " + body
        self.out.append("\n" + body + "\n")

    def result(self):
        self.flush()
        return "\n".join(x for x in self.out if x.strip())

EXERCISE_TITLES = {"exercise", "exercises", "problem", "problems"}

MATHCMD_PLAIN = {
    "odot": "\u2299", "times": "\u00d7", "ldots": "\u2026", "cdots": "\u22ef",
    "sigma": "\u03c3", "alpha": "\u03b1", "beta": "\u03b2", "eta": "\u03b7",
    "nabla": "\u2207", "partial": "\u2202", "infty": "\u221e",
}

def pdf_plain(s):
    """Plain-text version of a title for PDF bookmarks/TOC strings."""
    s = re.sub(r"\$([^$]*)\$", r"\1", s)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\\([a-zA-Z]+)\{([^{}]*)\}", lambda m: m.group(2), s)
        s = re.sub(r"\\([a-zA-Z]+)",
                   lambda m: MATHCMD_PLAIN.get(m.group(1), ""), s)
    s = s.replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()

def inline_walk_title(tag):
    t = "".join(inline_walk(c, "title") for c in tag.children)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    return t

# ---------------- page conversion ----------------

def clean_page(soup):
    for sel in soup.find_all(["script", "style", "form", "input", "noscript",
                              "iframe", "button", "link", "meta"]):
        sel.decompose()
    for sel in soup.find_all(id=["toc", "disqus_thread"]):
        sel.decompose()
    for sel in soup.find_all("div", class_="footer"):
        sel.decompose()
    for sel in soup.find_all("p", class_="sidebar"):
        sel.decompose()
    for sel in soup.find_all("a", class_="displaced_anchor"):
        sel.decompose()

def get_chapter_title(soup):
    m = soup.find("h1", class_="chapter_title")
    n = soup.find("h1", class_="chapter_number")
    if m:
        return (re.sub(r"\s+", " ", n.get_text()).strip() if n else ""), inline_walk_title(m)
    h2 = soup.find("div", class_="nonumber_header")
    if h2:
        return "", inline_walk_title(h2)
    return "", ""

def convert_page(fname, kind):
    page = fname.replace(".html", "")
    html = open(os.path.join(SRC, fname), encoding="utf-8").read()
    soup = BeautifulSoup(html, "lxml")
    clean_page(soup)
    num, title = get_chapter_title(soup)
    root = soup.find("div", class_="section") or soup.body
    em = Emitter(page)
    em.emit_block_children(root, id(root))
    return num, title, em.result()

DROP_PATTERNS = [
    "seems to be necessary to ensure the font loads",
]

RE_SPLIT_LST = re.compile(r"(\\begin\{lstlisting\}.*?\\end\{lstlisting\})", re.S)

def curly_quotes(text):
    """Pair straight double quotes into LaTeX ``...'' (per block, even count only)."""
    if text.count('"') < 2 or text.count('"') % 2 != 0:
        return text
    return re.sub(r'"([^"\n]+?)"', r"``\1''", text)

def tidy_spacing(text):
    """Remove space before punctuation left by stripped anchors, etc."""
    text = re.sub(r"[ \t]+([,.;:!?])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return curly_quotes(text)

def tidy_body(body):
    parts = RE_SPLIT_LST.split(body)
    for i in range(0, len(parts)):
        if not RE_SPLIT_LST.fullmatch(parts[i] or ""):
            parts[i] = tidy_spacing(parts[i])
    return "".join(parts)

def main():
    os.makedirs(os.path.join(OUT, "images"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "chapters"), exist_ok=True)
    # refresh chapters (keep main.tex if present)
    if os.path.isdir(os.path.join(OUT, "chapters")):
        for f in os.listdir(os.path.join(OUT, "chapters")):
            os.remove(os.path.join(OUT, "chapters", f))
    for d in ("images", "assets"):
        srcd = os.path.join(BASE, d)
        if os.path.isdir(srcd):
            for f in os.listdir(srcd):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    shutil.copy2(os.path.join(srcd, f), os.path.join(OUT, "images", f))
    summary = []
    for fname, kind in CHAPTERS:
        num, title, body = convert_page(fname, kind)
        body = tidy_body(body)
        key = fname.replace(".html", "")
        with open(os.path.join(OUT, "chapters", key + ".tex"), "w", encoding="utf-8") as f:
            f.write(body)
        summary.append((fname, kind, num, title, len(body)))
    with open(os.path.join(BASE, "convert_summary.txt"), "w", encoding="utf-8") as f:
        for row in summary:
            f.write(str(row[0]).ljust(32) + " kind=" + str(row[1]).ljust(10)
                    + " num=" + str(row[2])[:12].ljust(12)
                    + " title=" + repr(str(row[3] or "-")[:70])
                    + " chars=" + str(row[4]) + "\n")
        f.write("\n--- WARNINGS (%d) ---\n" % len(warnings))
        for w in warnings:
            f.write(w + "\n")
    print("converted", len(summary), "pages;", len(warnings), "warnings")

if __name__ == "__main__":
    main()

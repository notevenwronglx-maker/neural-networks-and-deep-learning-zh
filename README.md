<div align="center">

# 神经网络与深度学习 · 中文 LaTeX 版
# Neural Networks and Deep Learning · Chinese LaTeX Edition

Michael A. Nielsen 著 · 由 **LaTeXTrans (NiuTrans)** 多智能体系统翻译

[![license: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![content: CC BY-NC 3.0](https://img.shields.io/badge/content-CC%20BY--NC%203.0-lightgrey.svg)](NOTICE.md)

[中文](#中文说明) · [English](#english)

</div>

---

## 中文说明

本仓库提供 Michael A. Nielsen《Neural Networks and Deep Learning》的**两个 LaTeX 版本**，
以及把它们做出来的**完整流水线**：

| 版本 | 源码 | 成品 PDF | 页数 |
|---|---|---|---|
| 英文版（网页版转排） | [`en/`](en/) | [`en/main.pdf`](en/main.pdf) | 227 |
| **中文版（机器翻译）** | [`zh/`](zh/) | [`zh/main-zh.pdf`](zh/main-zh.pdf) | 204 |

中文版由 **LaTeXTrans**（NiuTrans 的多智能体 LaTeX 翻译系统）直接翻译 LaTeX 源码，
因此公式、编号、图片、交叉引用与原文完全一致；随后按
[mathtranslations.org《数学译本制作指南》](https://mathtranslations.org/guide/)
统一了术语与标点。**译文未经人工逐句审校**，欢迎提 Issue 勘误。

### 目录结构

```
├── en/                    英文版 LaTeX 工程（main.tex + chapters/ + images/）
├── zh/                    中文版 LaTeX 工程（main-zh.tex + chapters/ + images/ + 术语索引）
├── convert.py             HTML → LaTeX 转换器（英文版的生成脚本）
├── qa_check.py            转换结果的自检脚本
├── src_html/              转换器的输入：作者网页版各章 HTML
├── assets/                网页版附属图片
└── pipeline/
    ├── reference-template/  版式参考模板（"Maki 梦幻数学讲义"）
    ├── latextrans/          LaTeXTrans 整本书翻译流水线
    │   ├── patches/           对 LaTeXTrans 源码的 7 处补丁
    │   ├── tools/             干跑解析 / 后处理 / 装配 / QA 脚本
    │   ├── glossary/          180 条中英术语表
    │   └── config/            配置示例
    ├── ci/                  可选的 GitHub Actions 构建工作流
    └── experiments/         早期基于分块 + GLM 的尝试（已被取代，留作记录）
```

### 自己编译

需要 TeX Live 2020+ 或 MiKTeX（含 `ctex`、`fontspec`、`tcolorbox`、`longtable`
与 Fandol 字体）。**必须用 XeLaTeX**（本模板在 LuaLaTeX 下会卡在导言区）：

```bash
cd en && latexmk -xelatex main.tex      # → en/main.pdf
cd zh && latexmk -xelatex main-zh.tex   # → zh/main-zh.pdf   （跑 2–3 遍以稳定目录）
```

或者直接把 `en/`、`zh/` 目录上传到 Overleaf，在项目设置里选 **XeLaTeX**。

### 重新生成英文版

```bash
pip install beautifulsoup4 lxml
python convert.py     # src_html/ → en/chapters/
python qa_check.py    # 自检
```

### 复现中文翻译

翻译流程、补丁说明与全部统计见 **[`pipeline/latextrans/README.md`](pipeline/latextrans/README.md)**。
简版：

```bash
cd pipeline/latextrans
cp config/nndl.toml.example config/nndl.toml   # 填入你自己的 API key
python patches/apply_patches.py                # 给 LaTeXTrans 源码打 7 个补丁
python tools/dryrun_parse.py                   # 只解析，检查分段规模，不花钱
python LaTeXTrans/main.py --config config/nndl.toml \
       --project input/nndl-book --output out  # 解析 → 翻译 → 校验 → 重构 → 编译
python tools/assemble_zh.py --src out/ch_nndl-book/nndl-book --dst ../../zh
```

### 翻译规范落实

| 规范 | 落实 |
|---|---|
| 忠于原文、不增删 | 逐段对照；段落结构与空行一致 |
| 数学正确优先 | 数学环境、`\label`/`\ref`/`\tag`、代码块一字未改 |
| 术语统一 | 全程注入术语表；首次出现写 `\emph{中文}（english）` |
| 句末半角句点 | 1781 处全角 `。` → 半角 `.`，并在其后统一补空格 |
| 其余中文标点 | 833 处半角 `, : ; ? !` 改回全角 |
| 术语索引 | 文末 78 条（中文 / 英文 / 首次出现页） |
| 首页信息 | 扉页含原书名、作者、出版社与年份、译者、模型、版本 |

### 已知限制

- 译文**未经人工逐句审校**；LaTeXTrans 自带的校验器最后仍报告 3 个分段的命令计数
  差异（2 处 `^{\rm th}`、1 处 `\emph`），语义无影响，详见流水线 README。
- XeLaTeX/xdvipdfmx 不为此处的 CJK 子集字体写 `/ToUnicode` CMap，
  **从 PDF 复制中文可能乱码**（引擎限制，不影响显示与打印）。
- CI 工作流 `build.yml` 已提供但**尚未启用**（创建仓库用的 token 没有 `workflow` 权限，
  GitHub 不允许 OAuth App 写入 `.github/workflows/`）。启用方法见
  [`pipeline/ci/README.md`](pipeline/ci/README.md)。

---

## English

This repository contains **two LaTeX editions** of Michael A. Nielsen's
*Neural Networks and Deep Learning*, plus the **complete toolchain** used to
produce them:

| Edition | Source | PDF | Pages |
|---|---|---|---|
| English (typeset from the web edition) | [`en/`](en/) | [`en/main.pdf`](en/main.pdf) | 227 |
| **Chinese (machine translated)** | [`zh/`](zh/) | [`zh/main-zh.pdf`](zh/main-zh.pdf) | 204 |

The Chinese edition was produced by **LaTeXTrans** (NiuTrans' multi-agent LaTeX
translation system) working directly on the LaTeX source, so equations,
numbering, figures and cross-references match the original exactly. It was then
post-processed for terminology and punctuation consistency following the
[mathtranslations.org guide](https://mathtranslations.org/guide/).
**The translation has not been reviewed sentence by sentence by a human** —
issues and corrections are very welcome.

### Build

```bash
cd en && latexmk -xelatex main.tex
cd zh && latexmk -xelatex main-zh.tex
```

XeLaTeX is required; LuaLaTeX hangs in this template's preamble.

### Why LaTeXTrans needed patching

Upstream LaTeXTrans targets a single arXiv paper: one `main.tex`, splitting on
`\section`, auto-injecting `ctex`, 8192-token replies. A whole book breaks it —
most importantly this book's chapters use the custom `\sectionTitle` macro and
`\chapter` was not recognised at all, which collapsed the entire book into one
oversized request. Seven surgical patches fix that:

| Patch | Problem | Fix |
|---|---|---|
| P1 | `\chapter` / `\sectionTitle` not split points | book-aware section splitting |
| P2 | lists and exercise boxes extracted as opaque blocks | keep them in the flowing text |
| P3 | `ctex` injected into a `ctexbook` document → option clash | skip when already ctex |
| P4 | default prompts ignore Chinese typography rules | append the house rules R1–R9 |
| P5 | `max_new_tokens` ignored by DeepSeek (4096 cap) | send `max_tokens`, lower temperature |
| P6 | one serial LLM round trip per environment | answer known cases locally |
| P7 | 3 sections exceeded the reply budget | split long sections at paragraph bounds, never inside maths |

All 72 sections translated; the validator reported 4 problematic sections, which
three retry rounds reduced to 3 cosmetic ones. Post-processing then applied
1781 period fixes, 833 punctuation fixes, 513 spacing fixes, removed 29 English
ordinals and built a 78-entry terminology index. The final LaTeX log has
**0 errors, 0 undefined references, 0 missing characters, 0 overfull boxes**.

### Licence

- **Code** (converter, patches, tooling, LaTeX markup) — [MIT](LICENSE)
- **Book text and figures** — [CC BY-NC 3.0](NOTICE.md), © 2015 Michael A. Nielsen.
  The Chinese edition is a derivative work under the same licence.
  **Not for commercial use.**

All credit for the book belongs to **Michael A. Nielsen** — please read the
[free online edition](http://neuralnetworksanddeeplearning.com).

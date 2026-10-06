# 《神经网络与深度学习》中文版 — LaTeX 工程

Michael A. Nielsen, *Neural Networks and Deep Learning*, Determination Press, 2015
的中文译本，由 **LaTeXTrans (NiuTrans)** 多智能体翻译系统译出并重排。

- **`main-zh.tex`** — 主文件（`ctexbook`，XeLaTeX）
- **`chapters/`** — 各章中文正文（由 LaTeXTrans 生成后统一后处理）
- **`chapters/terminology.tex`** — 术语索引（78 条，含首次出现页码）
- **`images/`** — 原书插图
- **`main-zh.pdf`** — 编译成果（204 页，约 3.8 MB）
- **`qa_report.json`** — 后处理与校对的统计报告

## 编译

```bash
latexmk -xelatex main-zh.tex     # 需要 2–3 遍以稳定目录与 \pageref
```

需要 TeX Live 2020+ / MiKTeX（含 `ctex`、`fontspec`、`tcolorbox`、`longtable`
与 Fandol 字体）。**必须使用 XeLaTeX**：LuaLaTeX 在本工程的导言区会卡住。

## 版式

沿用本书英文 LaTeX 版所依据的模板（Overleaf *jtrrymvgxhmj*，即
"Maki 梦幻数学讲义" 设计）的视觉语言：

- XeLaTeX + `ctexbook`，正文宋体、章标题楷体、练习盒仿宋
- TeX Gyre Pagella + `mathpazo` 西文与数学字体
- 玫红 `LogicColor` 章标题、页眉横线；钢蓝 `tcolorbox` 练习/习题盒
- 公式编号沿用原书 `\tag{N}`
- 网页版的 `eqnarray` 已改为 amsmath 的 `equation` / `align`

## 翻译规范

遵循 [mathtranslations.org《数学译本制作指南》](https://mathtranslations.org/guide/)：

| 规范 | 落实方式 |
|---|---|
| 忠于原文、不增删 | 逐段对照翻译，段落结构一致 |
| 数学正确优先 | 数学环境、`\label`/`\ref`/`\tag`、代码块一律原样保留 |
| 术语统一 | 全程注入 180 条术语表；首次出现写作 `\emph{中文}（english）` |
| 句末半角句点 | 全稿 1781 处全角 `。` 已改为半角 `.` |
| 其余中文标点 | 833 处半角 `, : ; ? !` 已改回全角 |
| 术语索引 | 文末 78 条术语索引（中文 / 英文 / 首次出现页） |
| 首页信息 | 扉页含原书名、原作者、出版社与年份、译者、模型、版本 |

### 后处理中做过的确定性修正

1. `\begin{exerciseBox}{Exercise(s)}` → `{练习}`，`{Problem(s)}` → `{习题}`
2. `\emph{中文}（english）` 只在全书首次出现时保留，其余去掉英文注
3. `$j^{\rm th}$` → `$j$`（中文用"第 j 个"，无英语序数后缀）；
   `a_{\rm in}`、`n_{\rm in}` 等 `\rm` 下标**全部保留**
4. 句末句点后统一补一个空格（与模板 `\newunicodechar{。}{.\ }` 一致）
5. `\sectionTitle{A}{B}` 两个参数强制一致（正文标题与目录一致）

## 已知限制

- LaTeXTrans 自带的校验器最后仍报告 3 个分段的命令计数差异（2 处
  `^{\rm th}`、1 处 `\emph`），均为上述第 3 条与强调丢失导致，不影响编译与语义。
- 中文内容由机器翻译，**未经人工逐句审校**。如发现错误，欢迎对照原书勘正。
- XeLaTeX/xdvipdfmx 不为此处的 CJK 子集字体写入 `/ToUnicode` CMap，
  因此从 PDF 中**复制中文可能得到乱码**；这属于引擎限制，不影响显示与打印。

## 许可

原书文字与插图 © Michael A. Nielsen，以 CC BY-NC 3.0 Unported 许可发布
（<https://creativecommons.org/licenses/by-nc/3.0>）：可自由复制、传播与再创作，
不得用于商业目的。本译本的著作权安排与原书一致。

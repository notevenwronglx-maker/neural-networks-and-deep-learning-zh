# NNDL 整本书的 LaTeXTrans 翻译流水线

本目录是用 **LaTeXTrans (NiuTrans)** 翻译《Neural Networks and Deep Learning》
整本书所需的全部工程文件、补丁与工具。原始工具位于

```
C:\Users\22713\Documents\deepseek-harness\default-workspace\LaTeXTrans
C:\Users\22713\Documents\deepseek-harness\default-workspace\.venv   ← 依赖环境
```

因为运行沙箱只允许写入本工作区，这里**复制**了一份 LaTeXTrans 源码并打上补丁
（`LaTeXTrans/`），用原 venv 的解释器运行。上游检出保持原样、未被修改。

## 目录

```
config/nndl.toml           LaTeXTrans 配置（mode=2 术语表模式，deepseek-chat）
glossary/nndl_terms.csv    180 条中英术语表 + 章节标题译表（user_term）
input/nndl-book/           翻译输入工程：中文模板 main.tex + 英文 chapters/ + images/
input/pilot/               Chapter 1 试运行用的迷你工程
patches/apply_patches.py   对 LaTeXTrans 源码的 7 处补丁（幂等）
tools/                     干跑解析、后处理、装配、QA 脚本
out/                       LaTeXTrans 全部输出（原始译文与中间 JSON）
logs/                      运行日志
```

## 为什么需要补丁

上游 LaTeXTrans 面向 arXiv 单篇论文：只有一个 `main.tex`、按 `\section` 切分、
自动注入 `ctex`、每次回复上限 8192 token。整本书直接跑会失败：

| 补丁 | 问题 | 处理 |
|---|---|---|
| **P1** `parser.py` | 本书章节用自定义 `\sectionTitle`/`\subsectionTitle`，且 `\chapter` 不被识别 → 整本书塌成一个请求 | 把 `\chapter`/`\chapter*`/`\sectionTitle`/`\subsectionTitle` 也作为切分点，按层级重新编号 |
| **P2** `utils.py` | `enumerate`/`exerciseBox` 等被抽成独立环境单独翻译，上下文丢失 | 这些内联环境不再抽取，随正文一起翻译 |
| **P2b** `parser.py` | `\movieNote{文件名}` 的参数不该翻译 | 加入 `no_translate_envs` |
| **P3** `reconstruct.py` | 对 `ctexbook` 文档再 `\usepackage[UTF8]{ctex}` → option clash | 已是 ctex 文档类时跳过注入 |
| **P4** `prompts.py` | 默认提示词不涉及中文标点、术语注、模板宏 | 给全部 system prompt 追加本书规范 R1–R9 |
| **P5** `translator_agent.py` | `max_new_tokens` 不被 DeepSeek 识别（实际 4096），temperature 0.7 偏高 | 改用 `max_tokens: 8192`、`temperature: 0.3` |
| **P6** `parser_agent.py` | 每个内联环境都要一次串行 LLM 判断 | 已知内联环境直接返回 True |
| **P7** `parser.py` | 抽环境前有 3 个分段超过 6000 token，回复有截断风险 | 按空行切分超长分段，且绝不在环境/公式内部切开 |

```bash
python patches/apply_patches.py          # 幂等，可重复执行
```

## 复现步骤

```bash
PY=C:\Users\22713\Documents\deepseek-harness\default-workspace\.venv\Scripts\python.exe

# 1) 只解析、不调 LLM，检查分段规模
$PY tools/dryrun_parse.py

# 2) 整本书翻译（解析 → 翻译 → 校验/重译 → 重构 → 编译）
$PY LaTeXTrans\main.py --config config\nndl.toml \
    --project input\nndl-book --output out

# 3) 后处理 + 装配 + 编译到 ..\latex-zh\
$PY tools\assemble_zh.py
```

## 实际统计（2026-10-06 运行）

| 项目 | 数值 |
|---|---|
| 模型 | `deepseek-chat`（`https://api.deepseek.com/v1/chat/completions`） |
| 解析出的分段 | 72（其中 70 段需翻译、2 段为导言区与中文前置页） |
| 抽取且不翻译的环境 | 311（equation/align/lstlisting/table） |
| LaTeXTrans 校验器 | 首轮 4 段有误 → 3 轮重译后仍余 3 段（见下） |
| 输出 PDF | `out/ch_nndl-book/ch_nndl-book.pdf` |
| 后处理 | 全角句号→半角 1781；半角标点→全角 833；句点后加空格 513；删除英语序数 29；标题参数对齐 1；术语索引 78 条 |
| 最终成品 | `../latex-zh/main-zh.pdf`（204 页 / 3.84 MB / 227 页英文版） |

最终 LaTeX 日志：**0 个 `!` 错误、0 个未定义引用、0 个缺字、0 个 overfull box**。

## QA 工具

| 脚本 | 用途 |
|---|---|
| `tools/dryrun_parse.py` | 只跑解析器，打印分段/环境/输入的规模分布 |
| `tools/compare_out.py` | 英中逐章比对 LaTeX 命令计数与翻译覆盖率 |
| `tools/punct_census.py` | 统计中文标点使用（全角/半角对照） |
| `tools/show_errors.py` | 定位校验器报错所在分段的具体上下文 |
| `tools/pdf_font_probe.py` | 解压 PDF 检查字体是否真正内嵌（本机 poppler 缺 CJK 数据） |
| `tools/check_dollars.py` / `find_unbalanced_dollar.py` | 检查 `$` 配对 |
| `tools/check_rm_subscripts.py` | 确认 `\rm` 下标未被序数清理误伤 |

## 遗留问题

1. LaTeXTrans 校验器最终仍报 3 段命令数不符（`17#1`/`22` 少 `\rm`、`45#1` 少
   `\emph`）。前者是模型把 `the $l^{\rm th}$ layer` 译成"第 $l$ 层"所致，
   已由后处理的序数统一规则覆盖；后者是一处强调丢失，语义无影响。
2. 本机 poppler（TeX Live 自带）缺少 CJK language pack，`pdftoppm`/`pdffonts`
   无法预览或枚举中文 PDF 的字体；已改用 `tools/pdf_font_probe.py` 解压 PDF
   直接确认 17 个 CFF 子集字体全部内嵌（Identity-H），PDF 本身正常。
3. LuaLaTeX 在该模板导言区会卡死，请使用 XeLaTeX。

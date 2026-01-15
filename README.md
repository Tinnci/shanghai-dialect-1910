# Shanghai Dialect Exercises (1910) - Digitized Archive
# 上海方言练习 (1910) - 数字化档案

A digitized archive of Rev. D.H. Davis's *Shanghai Dialect Exercises in Romanized and Character with Key to Pronunciation and English Index* (1910).

D.H. Davis 牧师所著《上海方言练习》(1910) 的数字化档案。

---

## Quick Links / 快速链接

| | |
|---|---|
| **Full Documentation / 完整文档** | [digitized/README.md](digitized/README.md) |
| **Page Index / 页面索引** | [digitized/PAGE_INDEX.md](digitized/PAGE_INDEX.md) |
| **Original Source / 原始来源** | [Internet Archive](https://archive.org/details/shanghai-dialect-exercises-in-romanized-and-character-with-key-to-pronunciation-and-english-index) |

---

## License & Copyright / 版权与许可

- **Original Text (1910):** Public Domain.
- **Digital Edition (Code & Layout):** Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

- **原著文本 (1910):** 公有领域。
- **数字化版本 (源码与排版):** 基于 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 协议授权。

---

## Repository Structure / 仓库结构

```
├── digitized/          # Original digitized content / 数字化内容 (JXL images)
├── typst_source/       # Digital Edition Source / 数字化排版源码 (Typst)
│   ├── contents/       # Lessons, preliminary, and appendices / 课文与附件
│   ├── template.typ    # Typography and styling / 样式与宏定义
│   └── main.typ        # Main document entry / 主入口
├── src/                # Python backend for tools / 自动化工具源码
├── xtask.py            # Project Management Tool / 项目管理工具入口
└── shanghai-dialect-exercises.pdf # Latest compiled edition / 最新编译成品
```

---

## Project Tools / 项目工具 (xtask.py)

We use a specialized toolchain (`xtask.py`) to manage the digitization project, ensure phonetic consistency, and automate corrections.

我们使用专门的工具链 (`xtask.py`) 来管理数字化进程、确保发音一致性并自动化修正工作。

### Features / 功能特性
- **Automated Quality Control**: Phonetic consistency analysis and alignment shift (displacement) detection.
- **Intelligent Fixer**: Auto-correction of OCR artifacts (ghost numbers) and safe alignment fixes.
- **Rule Induction**: Automatically learns phonetic mapping rules from the corpus to guide corrections.
- **Typst Integration**: One-click compilation of the digital edition with standardized metadata.

### Usage / 使用方法
Requires [uv](https://github.com/astral-sh/uv) or standard Python 3.10+.

```bash
# Analysis
uv run python xtask.py analyze all          # Run all quality checks
uv run python xtask.py analyze displacement # Check for page alignment issues

# Repair
uv run python xtask.py fix --auto           # Apply safe fixes project-wide

# Build
uv run python xtask.py compile              # Build the PDF edition
```

---

*Digitized & Maintained 2026-01-15*

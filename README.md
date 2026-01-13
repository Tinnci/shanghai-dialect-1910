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

## Public Domain / 公有版权

This work was published in 1910 and is in the **public domain**.

本书出版于 1910 年，已进入**公有领域**。

---

## Repository Structure / 仓库结构

```
├── digitized/                    # Digitized content / 数字化内容
│   ├── 10-19_preliminary/        # Preface, TOC / 前言、目录
│   ├── 20-29_pronunciation-guide/# Pronunciation key / 发音说明
│   ├── 30-39_lessons/            # 155 lessons / 155课练习
│   ├── 40-49_appendices/         # Index, Errata / 索引、勘误
│   ├── 90-99_metadata/           # JXL images / 图片文件
│   ├── PAGE_INDEX.md             # Detailed content index / 详细索引
│   └── README.md                 # Full documentation / 完整说明
├── extract_pdf.py                # PDF extraction tool / 提取工具
└── convert_to_jxl.py             # JXL conversion tool / 转换工具
```

---

## Tools / 工具脚本

The Python scripts are provided for reproducibility:

提供 Python 脚本以便复现数字化流程：

- `extract_pdf.py` - Extract images from PDF / 从 PDF 提取图片
- `convert_to_jxl.py` - Convert to JPEG XL / 转换为 JXL 格式

**Requirements**: `pymupdf`, `pillow`, `pillow-jxl-plugin`

---

*Digitized 2026-01-13*

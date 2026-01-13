# Typst Source / Typst 源文件

This directory contains the Typst source files for creating a reflowable digital edition of the book.

本目录包含用于创建可重排数字版本的 Typst 源文件。

## Build / 编译

```bash
# 编译为 PDF
typst compile main.typ output.pdf

# 实时预览
typst watch main.typ
```

## Structure / 结构

```
typst_source/
├── main.typ              # 主入口
├── template.typ          # 样式模板
├── metadata.typ          # 书籍元信息
├── contents/
│   ├── preliminary.typ   # 前言、发音指南
│   ├── lessons/          # 课文 (按10课分组)
│   │   ├── lesson-01-10.typ
│   │   └── ...
│   └── appendices.typ    # 附录
└── fonts/                # 自定义字体
```

## Ruby Syntax / 注音语法

使用 `rubby` 包进行汉字下方注音：

```typst
#r[上][Zaung] #r[海][he] #r[方][faung] #r[言][yien]
```

## Footnotes / 脚注

每课脚注自动从 (1) 重新编号：

```typst
#r[賺][dzan-] #r[頭][deu]#footnote[Profit.]
```

## Requirements / 依赖

- Typst >= 0.11
- `rubby` package (自动从 Typst Universe 下载)
- 思源宋体 (Source Han Serif SC) 或 Noto Serif CJK SC

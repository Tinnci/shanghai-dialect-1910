# Workspace Skills (工作区技能)

该文档分类并描述了当前工作区中的所有Python脚本及其用途。

## 运行规则 (Execution Rules)

本工作区采用 **`xtask`** 模式来管理所有自动化任务。请使用以下命令作为统一入口：

```bash
uv run python xtask.py <command>
```

---

## 可用任务 (Available Tasks)

### 1. 质量分析 (Analysis)
执行各种代码和文本质量检查。

- **`analyze all`**: 运行所有分析检查（推荐）。
- **`analyze phonetic`**: 仅运行音韵一致性分析。
- **`analyze displacement`**: 仅运行错位检测。
- **`analyze priority`**: 生成修正优先级列表。

**示例**:
```bash
uv run python xtask.py analyze all
```

### 2. 数据提取与转换 (Data Processing)
用于处理 PDF 源文件和图像资源。

- **`extract`**: 
  - 从源 PDF 提取图像和页面。
  - 生成 Johnny Decimal 目录结构。
  - 需要根目录下存在源 PDF 文件。
  
- **`convert`**:
  - 将提取的图像批量转换为 JPEG XL (JXL) 格式。
  - 自动优化文件大小。

**示例**:
```bash
uv run python xtask.py extract
uv run python xtask.py convert
```

---

## 项目结构 (Project Structure)

```text
.
├── xtask.py             # 统一任务入口 CLI
├── src/                 # 核心代码库
│   ├── utils.py         # 通用工具函数
│   ├── loader.py        # 文件加载器
│   ├── tasks/           # 独立任务模块
│   │   ├── pdf_extract.py   # PDF 提取逻辑
│   │   └── jxl_convert.py   # JXL 转换逻辑
│   └── analyzers/       # 分析器模块
│       ├── phonetic.py      # 音韵分析
│       ├── displacement.py  # 错位分析
│       └── stats.py         # 统计分析
├── digitize/            # 数据输出目录
└── typst_source/        # Typst 源代码
```

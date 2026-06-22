---
name: literature-processor
description: |
  文献智能处理 Skill - 自动将中文学术论文/学位论文按章节拆分为独立的 Markdown 文件。
  
  **使用方法**: 当用户需要处理 PDF 文献、将论文按章节分块、提取学术文档内容时，
  自动使用此 skill。特别适用于：
  - 处理中文学位论文(博士/硕士)
  - 按章节生成独立笔记(1.1, 1.2, 1.3 等)
  - 提取 PDF 文本并保留章节结构
  - 处理知网下载的 CAJ/PDF 文献
  
  **触发关键词**: "处理PDF", "文献拆分", "章节提取", "论文分块", "知网文献",
  "按章节生成", "学术文献处理", "PDF转Markdown"

version: 1.0.0
author: Assistant
tags: [pdf, academic, literature, markdown, chinese]
---

# Literature Processor Skill

## 核心功能

智能处理中文学术 PDF，按章节标题精确拆分内容，每个章节生成独立的 Markdown 文件。

### 解决的问题

1. **内容不截断** - 精确按标题位置分割，不会出现句子被截断
2. **子章节归属正确** - 1.2.1, 1.2.2 等子章节完整包含在 1.2 文件中
3. **识别绪论** - 正确处理第0章/绪论部分
4. **跨页内容处理** - 同一章节跨多页时内容连续

## 使用方式

### 命令行调用

```bash
# 基本用法 - 处理 PDF 并生成章节文件
python -m literature_skill "/path/to/paper.pdf"

# 指定输出目录
python -m literature_skill "/path/to/paper.pdf" -o "./output"

# 强制重新处理
python -m literature_skill "/path/to/paper.pdf" -f
```

### Python API 调用

```python
from literature_skill import LiteratureProcessor

# 创建处理器
processor = LiteratureProcessor(
    output_dir="./processed",
    grobid_url="http://127.0.0.1:8070"  # 可选
)

# 处理 PDF
result = processor.process("/path/to/paper.pdf")

# 查看结果
print(f"生成 {len(result['sections'])} 个章节文件")
for section in result['sections']:
    print(f"  - {section['title']}: {section['pages']}")
```

## 输出结构

```
{output_dir}/
├── {pdf_name}_index.json          # 处理结果索引
├── {pdf_name}_processed.md        # 完整合并文档(可选)
└── {pdf_name}_sections/             # 章节拆分目录
    ├── 001_绪论.md
    ├── 002_0.1_研究背景与意义.md
    ├── 003_0.2_国内外研究述评.md
    ├── 004_第一章_标题.md
    ├── 005_1.1_小节标题.md
    └── ...
```

## 技术特点

### 1. 精确内容边界

- 使用字符级位置信息而非整页分配
- 同一页内多个标题时，按标题位置精确切分

### 2. 标题层级识别

- 一级标题: `第X章`, `绪论`, `第0章`
- 二级标题: `X.X` 格式 (如 1.1, 1.2, 0.1)
- 子章节(1.2.1)归属到父章节(1.2)

### 3. 质量检测

- 检测加密 PDF
- 检测知网乱码 PDF
- 检测多栏布局并重建阅读顺序

### 4. 元数据提取

每个生成的 Markdown 文件包含 YAML frontmatter:

```yaml
---
title: "章节标题"
source_pdf: 原始文件名.pdf
section_level: 2
pdf_type: dissertation
pages: 14-19
word_count: 6551
---
```

## 依赖安装

```bash
# 必需依赖
pip install pymupdf

# 可选依赖(用于学术论文结构化提取)
# Grobid Docker 部署
docker run -d --name grobid -p 8070:8070 grobid/grobid:0.8.0
```

## 支持的文档类型

- **学位论文**: 博士/硕士论文(最优)
- **学术论文**: 期刊论文
- **书籍**: 多章节图书
- **政策文件**: 政府公文

## 处理流程

```
PDF输入
  → 质量检测(加密/乱码/扫描件)
  → PDF类型分类
  → 文本提取(PyMuPDF)
  → 标题识别(第X章, X.X格式)
  → 精确内容分割(字符级位置)
  → 生成章节Markdown文件
```

## 注意事项

1. **Windows 路径**: 自动处理 Windows 路径中的空格
2. **编码**: 自动处理中文编码问题
3. **大文件**: >100MB PDF 可能需要较长时间
4. **知网 PDF**: 部分 CAJ 转换的 PDF 需预处理

## 文件说明

- `__init__.py`: 主处理器实现 (LiteratureProcessor 类)
- `core.py`: PDF 分类、质量检测、多栏处理核心模块
- `__main__.py`: 命令行入口

## 版本历史

- v1.0.0: 初始版本，支持精确章节分割

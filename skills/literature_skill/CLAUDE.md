# Literature Processing Skill

## 功能概述

文献智能处理 Skill，提供以下功能：

1. **PDF分类检测** - 自动识别文献类型（学术论文/学位论文/书籍/政策文件）
2. **质量检测** - 检测加密PDF、知网乱码PDF、扫描件等
3. **多引擎提取** - Grobid(学术论文) → PyMuPDF(通用)
4. **多栏布局重建** - 自动检测并重建双栏/多栏PDF的阅读顺序
5. **按标题分块** - 根据章节标题智能分块，而非固定页数
6. **结构化输出** - 生成包含元数据、目录、正文块的Markdown文件

## 安装依赖

```bash
pip install pymupdf requests
```

可选依赖（推荐）：
```bash
# Grobid (Docker)
docker run -d --name grobid -p 8070:8070 grobid/grobid:0.8.0
```

## 使用方法

### 命令行

```bash
# 基本用法
python -m literature_skill "/path/to/paper.pdf"

# 指定输出目录
python -m literature_skill "/path/to/paper.pdf" -o "./output"

# 强制重新处理
python -m literature_skill "/path/to/paper.pdf" -f

# 自定义Grobid地址
python -m literature_skill "/path/to/paper.pdf" --grobid-url http://localhost:8070
```

### Python API

```python
from literature_skill import LiteratureProcessor

# 创建处理器
processor = LiteratureProcessor(
    output_dir="./processed",
    grobid_url="http://127.0.0.1:8070"
)

# 处理PDF
result = processor.process("/path/to/paper.pdf")

# 检查结果
if result.get("status") == "requires_intervention":
    print(f"需要人工处理: {result['message']}")
else:
    print(f"PDF类型: {result['analysis']['pdf_type']}")
    print(f"页数: {result['analysis']['page_count']}")
    print(f"分块数: {len(result['chunks'])}")
```

## 处理流程

```
输入PDF
    │
    ├─→ 质量检测
    │   ├─→ 加密? → 请求人工干预
    │   ├─→ CNKI乱码? → 请求人工干预
    │   └─→ 扫描件? → 标记警告继续
    │
    ├─→ 分类检测
    │   ├─→ 学位论文 (Dissertation)
    │   ├─→ 学术论文 (Academic)
    │   ├─→ 政策文件 (Policy)
    │   ├─→ 书籍 (Book)
    │   └─→ 未知 (Unknown)
    │
    ├─→ 文本提取 (多引擎)
    │   ├─→ Grobid (学术论文首选)
    │   └─→ PyMuPDF (通用后备)
    │
    ├─→ 布局处理
    │   └─→ 多栏检测与重建
    │
    ├─→ 标题提取
    │   └─→ 基于字体/样式的智能识别
    │
    └─→ 按标题分块
        ├─→ 生成结构化Markdown
        └─→ 保存JSON元数据
```

## 输出文件

处理完成后生成两个文件：

1. **`{filename}_processed.md`** - 结构化Markdown文件
   - YAML frontmatter (元数据)
   - 目录
   - 按章节分块的内容

2. **`{hash}.json`** - 处理结果元数据
   - 分析结果 (PDF类型、质量等)
   - 标题结构
   - 分块信息

## 人工干预处理

当检测到以下情况时，Skill会返回人工干预请求：

### 加密PDF
```json
{
  "status": "requires_intervention",
  "reason": "encrypted",
  "message": "PDF已加密，无法自动处理。",
  "suggestions": [
    "1. 使用PDF密码解除工具",
    "2. 从原源重新下载未加密版本",
    "3. 使用浏览器打印为PDF"
  ]
}
```

### 知网乱码PDF
```json
{
  "status": "requires_intervention",
  "reason": "cnki_garbled",
  "message": "检测到知网乱码PDF，需要人工转换。",
  "suggestions": [
    "1. 使用CAJViewer打开文件",
    "2. 文件 → 另存为 → PDF",
    "3. 或使用知网海外版直接下载PDF",
    "4. 或使用Zotero + 茉莉花插件自动转换"
  ]
}
```

## 核心类说明

### PDFClassifier
分类器，基于关键词和模式识别PDF类型。

### PDFQualityChecker
质量检测器，检测加密、乱码、扫描件等问题。

### ColumnDetector
多栏布局检测器，重建阅读顺序。

### HeadingExtractor
标题提取器，基于字体大小和样式识别标题。

### GrobidExtractor
Grobid API客户端，用于学术论文结构化提取。

### DocumentChunker
文档分块器，按标题边界智能分块。

## 注意事项

1. **编码问题**: Windows上可能遇到GBK编码问题，已通过stdout重定向修复
2. **Grobid**: 学术论文处理推荐使用Grobid，但需单独部署
3. **大文件**: 处理大PDF(>100MB)可能需要较长时间
4. **中文PDF**: 部分知网PDF可能存在乱码问题，需人工预处理

---
name: md-to-word
description: |
  将Markdown文件转换为格式良好的Word文档(.docx)。
  当用户需要把md文件转成word、markdown转docx、保留markdown格式生成word文档时触发。
  支持表格、各级标题、列表、代码块、加粗斜体等格式，中文字体使用黑体和宋体。
  适用于Obsidian笔记导出、文档转换、保持格式从Markdown生成Word等场景。
---

# Markdown转Word Skill

## 功能

将Markdown(.md)文件转换为Microsoft Word(.docx)文档，保持原有格式结构。

## 支持特性

- ✅ 标题层级（H1-H6），使用黑体
- ✅ 加粗、斜体、删除线
- ✅ 无序列表和有序列表
- ✅ 表格（保持结构）
- ✅ 代码块和行内代码
- ✅ 引用块
- ✅ 水平分隔线
- ✅ 中文字体：标题用黑体，正文用宋体

## 使用方法

### 基本用法

```
转换文档: /md-to-word input.md
指定输出: /md-to-word input.md output.docx
```

### 具体示例

1. **转换当前目录的md文件**
   ```
   /md-to-word readme.md
   ```

2. **指定输出路径**
   ```
   /md-to-word notes.md /path/to/output.docx
   ```

3. **转换带空格的文件名**
   ```
   /md-to-word "my notes.md" "output.docx"
   ```

## 技术实现

脚本位于 `scripts/md_to_word.py`，使用 `python-docx` 库生成Word文档。

### 依赖安装

```bash
pip install python-docx
```

### 直接运行脚本

```bash
python scripts/md_to_word.py input.md [output.docx]
```

## 字体设置

| 元素 | 字体 | 字号 |
|------|------|------|
| 正文 | 宋体 | 12pt |
| 一级标题 | 黑体 | 22pt |
| 二级标题 | 黑体 | 18pt |
| 三级标题 | 黑体 | 16pt |
| 四级标题 | 黑体 | 14pt |
| 五/六级标题 | 黑体 | 12pt |
| 表格内容 | 宋体 | 10.5pt |
| 代码 | Consolas | 9-10pt |

## 限制

- 不支持图片导出（显示为占位符）
- 复杂嵌套表格可能需手动调整
- LaTeX数学公式不支持

---
name: paper-memory-manager
description: |
  论文记忆管理 Skill - 增量读取 DOCX 章节并同步到记忆文件。
  
  **核心功能**：
  1. 混合策略识别章节（Word样式优先 + 文本模式回退）
  2. 层级包含提取（指定章节 + 所有子节）
  3. 用户审核模式（生成 diff，确认后写入）
  4. 自动备份（每次更新生成 .backup.YYYYMMDD）
  
  **触发关键词**: "更新第X章", "/update-X.X", "记住当前状态", "章节提取"

version: 1.0.0
author: Assistant
tags: [docx, thesis, memory, incremental]
---

# Paper Memory Manager Skill

## 设计概述

### 核心目标

解决大型论文（DOCX）增量更新的问题：
- **禁止全量读取** → 按需提取指定章节
- **容错解析** → 处理工作文件中的标题不规范
- **安全更新** → 用户审核 diff 后再写入

### 架构决策

采用**分层解析器架构**（方案 A）：

```
PaperMemoryManager (主控制器)
    ├── HeadingDetector (章节识别器)
    ├── SectionExtractor (内容提取器)
    └── MemoryUpdater (记忆更新器)
```

### 关键特性

| 特性 | 实现方式 |
|------|---------|
| 章节识别 | Word样式优先，失败回退文本模式 |
| 容错策略 | 宽松模式（允许编号跳跃） |
| 更新粒度 | 包含子节（2.1 → 2.1 + 2.1.x） |
| 审核模式 | Markdown表格 diff |
| 备份策略 | 每次更新生成 .backup.YYYYMMDD |

---

## 核心模块设计

### 1. HeadingDetector（章节识别器）

**职责**：解析 DOCX 结构，生成章节树

**识别策略**（混合模式）：

```python
class HeadingDetector:
    def detect(self, docx_path) -> HeadingTree:
        # 第一优先：Word Heading样式
        headings = self._detect_by_style(doc)
        
        # 第二优先：文本模式（样式失败时）
        if not headings:
            headings = self._detect_by_text(doc)
        
        # 容错修复（宽松模式）
        headings = self._repair_numbering(headings)
        
        return HeadingTree(headings)
```

**样式识别规则**：
- `Heading 1` → 一级（第X章）
- `Heading 2` → 二级（X.X）
- `Heading 3` → 三级（X.X.X）
- `Heading 4` → 四级（X.X.X.X）

**文本识别规则**（样式失败时）：
```regex
一级: ^第[一二三四五六七八九十\d]+章[\s\.].+
二级: ^\d+\.\d+[\s\.].+
三级: ^\d+\.\d+\.\d+[\s\.].+
四级: ^\d+\.\d+\.\d+\.\d+[\s\.].+
```

**宽松容错修复**：
- 自动补全缺失编号（`相关概念` → `1.3 相关概念`）
- 修复编号跳跃（1.2 → 1.4 → 自动插入 1.3 占位）
- 清理无效标题（页眉/页脚/目录页过滤）

### 2. SectionExtractor（内容提取器）

**职责**：根据章节号提取内容（含子节）

**层级包含算法**：

```python
class SectionExtractor:
    def extract(self, tree: HeadingTree, section_id: str) -> SectionContent:
        # 解析章节号（如 "2.1" → level=2, [2, 1]）
        target = self._parse_section_id(section_id)
        
        # 收集目标章节及其所有子节
        contents = []
        for heading in tree.headings:
            if self._is_descendant(heading, target):
                content = self._extract_between(
                    doc, 
                    heading.start_para, 
                    heading.end_para
                )
                contents.append({
                    'level': heading.level,
                    'title': heading.title,
                    'content': content
                })
        
        return SectionContent(contents)
    
    def _is_descendant(self, heading, target) -> bool:
        # 2.1 包含 2.1, 2.1.1, 2.1.2, 2.1.2.1...
        return heading.numbering[:len(target)] == target
```

### 3. MemoryUpdater（记忆更新器）

**职责**：生成 diff、用户审核、原子写入

**Diff 生成格式**（Markdown 表格）：

```markdown
### 2.1 存量更新规划相关理论和内容

| 状态 | 内容 |
|------|------|
| 🟢 保留 | [原有内容摘要...] |
| 🟡 修改 | ~~旧内容~~ → **新内容** |
| 🔴 删除 | ~~删除的内容~~ |
| 🟢 新增 | **新增的内容** |

**段落级对比**：
| 段落 | 记忆文件 | DOCX提取 | 操作 |
|------|---------|---------|------|
| 1 | 理论A... | 理论A... | 保留 |
| 2 | 旧观点... | 新观点... | 修改 |
| 3 | - | 新增内容... | 新增 |
```

**写入流程**：

```python
class MemoryUpdater:
    def update(self, section_content: SectionContent, memory_path: str):
        # 1. 读取现有记忆
        old_content = self._read_memory(memory_path)
        
        # 2. 生成 diff
        diff = self._generate_diff(old_content, section_content)
        
        # 3. 用户审核（返回确认/取消）
        if not self._user_confirm(diff):
            return {'status': 'cancelled'}
        
        # 4. 创建备份
        self._create_backup(memory_path)
        
        # 5. 原子写入
        self._atomic_write(memory_path, section_content)
        
        return {'status': 'success'}
```

---

## 数据流

```
用户输入: "更新 2.1"
    │
    ▼
PaperMemoryManager
    │
    ├───► HeadingDetector
    │       ├── 读取 DOCX
    │       ├── 样式识别（Heading 1-4）
    │       └── 生成章节树
    │
    ├───► SectionExtractor
    │       ├── 解析 "2.1" → [2, 1]
    │       ├── 收集 2.1 + 2.1.x 所有段落
    │       └── 组装 SectionContent
    │
    └───► MemoryUpdater
            ├── 读取现有记忆文件
            ├── 生成 Markdown diff
            ├── 等待用户确认
            ├── 创建 .backup.YYYYMMDD
            └── 原子写入更新
    │
    ▼
输出: 更新成功 + 备份路径
```

---

## 接口定义

### Python API

```python
from paper_memory_manager import PaperMemoryManager

# 初始化
manager = PaperMemoryManager(memory_dir="./wiki/meta")

# 更新指定章节
result = manager.update_section(
    docx_path="论文.docx",
    section_id="2.1",  # 支持 "2" / "2.1" / "2.1.3"
    memory_name="论文记忆-XXX.md"
)

# 全量扫描（记住当前状态）
result = manager.scan_full(
    docx_path="论文.docx",
    memory_name="论文记忆-XXX.md"
)
```

### CLI 接口

```bash
# 更新指定章节
python -m paper_memory_manager "论文.docx" --section "2.1" --memory "论文记忆-XXX.md"

# 全量扫描
python -m paper_memory_manager "论文.docx" --scan --memory "论文记忆-XXX.md"

# 输出 diff 不写入（预览模式）
python -m paper_memory_manager "论文.docx" --section "2.1" --dry-run
```

---

## 错误处理

| 错误类型 | 处理策略 |
|---------|---------|
| DOCX 文件不存在 | 明文报错，返回错误码 `FILE_NOT_FOUND` |
| 章节号不存在 | 列出可用章节，建议最接近的匹配 |
| 记忆文件不存在 | 询问是否创建新文件 |
| 标题识别失败 | 降级到文本模式，标记置信度 |
| 用户取消审核 | 保留备份，不写入，返回 `CANCELLED` |
| 写入失败 | 从备份恢复，返回 `WRITE_ERROR` |

---

## 记忆文件格式

**YAML Frontmatter**：

```yaml
---
type: thesis-memory
topic: 论文标题
source_docx: "[[../../raw/unprocessed/论文.docx]]"
status: 进行中
created: 2026-06-01
updated: 2026-06-01
---
```

**章节状态标记**：

```markdown
## 第2章 研究基础

**状态**：🟡 部分完成

### 2.1 存量更新规划相关理论和内容
**状态**：🟢 已完成

**核心内容**：
...
```

---

## 依赖安装

```bash
pip install python-docx
```

---

## 版本历史

- v1.0.0: 初始版本，支持增量章节提取与记忆更新

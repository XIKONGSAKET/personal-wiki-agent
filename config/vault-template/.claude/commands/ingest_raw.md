---
name: ingest_raw
description: 处理 inspool-wiki-zh/raw/unprocessed 中的下一个 ingest 单元，使用Python工具读取PDF内容，严禁编造，更新 wiki 并将 raw 标记为 pending_review。
---

# ingest_raw

用于处理 `inspool-wiki-zh/raw/unprocessed/` 中的下一个 ingest 单元，并把结果整合进 wiki。

**执行前必须首先阅读 `inspool-wiki-zh/CLAUDE.md` 获取详细规则。**

**核心原则：严禁编造，只基于实际读取的内容创建 wiki。**

## 执行步骤

### Phase 1: 准备与扫描

1. 读取 `inspool-wiki-zh/CLAUDE.md`
2. 查看 `inspool-wiki-zh/raw/index.md`、`inspool-wiki-zh/wiki/index.md` 与 `inspool-wiki-zh/wiki/log.md`
3. 扫描 `inspool-wiki-zh/raw/unprocessed/`，识别所有待处理文件
4. 根据以下优先级选择"下一个 ingest 单元"：
   - 同一子文件夹中的文件
   - 拥有相同 `ingest_group` 的文件
   - 否则选择单篇文件
5. 如果存在多个候选 ingest 单元，优先选择最早进入队列的那一组；如无法判断，则按名字典序选择第一组
6. 如果选中的是批次，确认它们确实主题相关；如批次明显过大（超过5篇），则拆成 2 到 5 篇的小批次

### Phase 2: PDF 内容提取（关键阶段）

**⚠️ 强制要求：必须使用 literature_skill 读取 PDF，禁止根据文件名或标题推测内容**

对于每个选中的 PDF 文件，执行以下流程：

#### 2.1 尝试读取 PDF

**必须使用 literature_skill 处理 PDF：**

```bash
python -m literature_skill "PDF文件路径" -o "输出目录"
```

**可选参数：**
- `-f`: 强制重新处理（如果之前已处理过）
- `--grobid-url URL`: 指定 Grobid 服务地址（如需学术论文结构化提取）

**读取成功后的文件：**
- `{filename}_processed.md` - 包含元数据和分章节内容的结构化 Markdown
- `{filename}_index.json` - 处理结果索引，包含章节信息和质量检测报告
- `{filename}_sections/` - 按章节拆分后的独立 Markdown 文件（适用于学位论文）

**如果上述命令失败，尝试备用方案：**

```bash
python tools/smart_pdf_reader.py "PDF文件路径" -o "输出txt路径"
```

或检查PDF可读性：

```bash
python tools/smart_pdf_reader.py "PDF文件路径" --check
```

#### 2.2 读取结果处理

**成功情况：**
- literature_skill 成功返回 JSON 索引文件 `{filename}_index.json`
- 从索引中提取以下信息：
  - `analysis.pdf_type`: PDF 类型（学位论文/学术论文/政策文件/书籍）
  - `analysis.page_count`: 总页数
  - `quality`: 质量检测报告（加密、乱码、扫描件等）
  - `chunks`: 内容分块信息（标题、页码范围、字数）
- 读取 `{filename}_processed.md` 获取完整结构化内容
- 如果存在 `{filename}_sections/` 目录，记录各章节文件路径
- 继续处理下一篇

**需要人工干预的情况（literature_skill 返回特定状态）：**

```
【PDF 读取需要人工干预报告】
文件名: [具体文件名]
文件路径: [完整路径]
状态码: requires_intervention
原因: [encrypted/cnki_garbled/scanned/...]
失败原因: [具体原因，如"PDF已加密/知网乱码/扫描件"等]
literature_skill 建议:
- [建议1]
- [建议2]
- [建议3]
状态: 跳过本文件，继续处理同批次其他PDF
```

**处理失败情况（技术错误）：**

```
【PDF 读取失败报告】
文件名: [具体文件名]
文件路径: [完整路径]
故障码: [错误信息或异常类型]
失败原因: [具体原因，如"PyMuPDF无法打开/文件损坏/编码错误"等]
处理建议: [如"需要人工转换为可读格式"]
状态: 跳过本文件，继续处理同批次其他PDF
```

**⚠️ 严禁行为：**
- 不得根据文件名、标题推测内容
- 不得编造摘要、关键词、结论
- 不得跳过读取直接标记为 pending_review
- 不得用训练语料中的知识替代PDF实际内容

#### 2.3 批量处理策略

如果同一批次有多篇PDF：
1. 对每篇PDF单独执行读取流程
2. 读取失败的PDF明确报错后继续处理下一篇
3. 最终报告需列出：成功读取X篇，失败Y篇，失败文件及原因

### Phase 3: 内容分析与 wiki 创建

**⚠️ 学术规范约束：严格遵守 academic-writing-assistant/SKILL.md 的规则**

#### 3.1 内容分析约束

**只能基于成功提取的文本内容进行分析：**
- 提取标题、作者、摘要、关键词（必须从文本中提取，不是从文件名）
- 识别论文结构（引言、文献综述、方法、结果、讨论等）
- 摘录核心观点和关键结论

**如果关键信息缺失：**
- 标记为"原文未提供摘要"/"原文未明确关键词"等
- 不得根据主题推测补全

#### 3.2 创建来源摘要页

在 `inspool-wiki-zh/wiki/sources/` 中创建来源页：

**必须包含的字段：**
- `type`: source
- `status`: pending_review
- `raw_note`: 指向原始PDF的路径
- `processed_at`: 处理日期

**正文结构：**
```markdown
## 来源信息
- 标题: [从PDF提取的实际标题，不是文件名]
- 作者: [从PDF提取的实际作者]
- 年份: [从PDF提取的实际年份]
- 期刊/来源: [如有]
- 原始文件: [[raw/unprocessed/文件名]]

## 核心摘要
[基于PDF内容的摘要，不是编造的]

## 关键观点
1. [观点1]: [基于原文的摘录]
   - 原文依据: [引用页码或段落]

## 可抽取的实体
[论文中提到的具体实体]

## 可抽取的概念
[论文中涉及的理论概念]

## 待确认问题
[如果某些内容不明确]
```

#### 3.3 更新相关页面

根据实际内容创建或更新：
- 实体页 (`wiki/entities/`)
- 概念页 (`wiki/concepts/`)
- 综合页 (`wiki/synthesis/`)

**必须遵守的规则：**
1. 所有结论必须有原文支持
2. 不确定的内容标记为"待确认"
3. 不得将推测写成事实
4. 使用学术审慎表达（"可能"、"或"、"有待验证"）

### Phase 4: 链接与索引更新

1. 为新增知识补充必要的 `[[双链]]`
2. 关键结论优先链接到 `[[sources/...]]` 或 `[[sources/...#某小节]]`
3. 为核心页面维护 frontmatter 关系字段
4. 更新 `inspool-wiki-zh/wiki/index.md`
5. 在 `inspool-wiki-zh/wiki/log.md` 中追加 `ingest` 日志

### Phase 5: 状态标记与报告

1. 对本次成功处理的每个 raw 文件更新流程字段：
   - `processing_status: pending_review`
   - `processed_at: <日期>`
   - `processed_into: <对应来源页路径>`

2. 对读取失败的文件：
   - 保持 `processing_status: unprocessed`
   - 在 frontmatter 中添加 `read_error: <错误信息>`
   - 在 raw/index.md 中标记为"待人工处理"

3. 更新 `inspool-wiki-zh/raw/index.md`

4. **明确告知用户处理结果：**
   - 成功处理X篇，失败Y篇
   - 失败的文件及原因
   - 已进入 pending_review 的文件列表

## 质量控制检查点

在处理过程中，必须逐项核对：

- [ ] 是否使用 literature_skill 实际读取了 PDF？
- [ ] 是否成功生成了索引 JSON 和结构化 Markdown？
- [ ] 读取失败的是否明确报错并记录原因？
- [ ] 需人工干预的是否明确原因和建议？
- [ ] 是否根据实际内容创建 wiki，而非根据标题编造？
- [ ] 所有结论是否有原文直接支持？
- [ ] 不确定的内容是否标记为"待确认"？
- [ ] 是否有绝对化表述（如"必然"、"毫无疑问"）？
- [ ] wiki/index.md、wiki/log.md、raw/index.md 是否已更新？

**如有任何一项未通过，不得将状态改为 pending_review。**

## 约束与禁止事项

### 绝对禁止

1. **严禁编造内容**
   - 不得根据文件名推测论文内容
   - 不得编造摘要、关键词、数据或结论
   - 不得用训练语料替代PDF实际内容

2. **严禁跳过读取**
   - 必须使用 literature_skill 处理PDF后才能创建wiki
   - 检测到需人工干预必须明确报告，不能蒙混过关
   - 读取失败必须明确报错，不能蒙混过关

3. **严禁学术不端**
   - 不得将推测写成事实
   - 不得使用绝对化表达
   - 必须遵守 academic-writing-assistant 的学术规范

### 技术要求

1. **必须使用 literature_skill**
   - 遇到PDF第一时间调用 `python -m literature_skill`
   - 自动检测PDF类型（学位论文/学术论文/政策文件/书籍）
   - 自动处理质量检测（加密/乱码/扫描件）
   - 自动生成结构化输出（索引JSON + 分章节Markdown）
   - 不要等待用户提醒才使用工具

2. **错误处理**
   - 返回 `requires_intervention` 状态必须明文报告原因和建议
   - 技术故障必须明文报告错误信息
   - 继续处理同批次其他PDF
   - 标记需干预/失败的文件供人工处理

3. **中文PDF处理**
   - literature_skill 已内置中文编码处理
   - 自动检测知网乱码PDF并请求人工干预
   - 保留原文中的中文术语
   - 自动重建多栏布局阅读顺序

## 空队列处理

如果 `inspool-wiki-zh/raw/unprocessed/` 为空：
- 明确说明当前没有待处理素材
- 不要创建空日志或空页面
- 直接停止

## 输出要求

**必须包含以下内容：**

1. **处理概览**
   - 选中的 ingest 单元（文件名列表）
   - 计划更新的页面

2. **PDF 读取报告**
   ```
   【PDF 读取报告】
   ✅ 成功: X篇
      - 文件1: 标题XX，类型(学位论文/学术论文/...)，页数XX，章节数X
      - 文件2: ...
   ⚠️ 需人工干预: Y篇
      - 文件3: 原因(加密/知网乱码/扫描件)，建议处理方式
      - 文件4: ...
   ❌ 失败: Z篇
      - 文件5: 故障原因XX
      - 文件6: ...
   ```

3. **wiki 创建结果**
   - 新建/更新的来源页列表
   - 新建/更新的实体/概念/综合页

4. **失败文件处理建议**
   - 哪些文件需要人工干预
   - 建议的处理方式

5. **最终状态**
   - 已进入 pending_review 的文件
   - 仍需处理的文件

## 故障排查指南

### PDF 无法读取的常见原因

| 故障现象 | 可能原因 | 处理建议 |
|---------|---------|---------|
| requires_intervention: encrypted | PDF已加密 | 使用PDF密码解除工具，或从原源重新下载未加密版本 |
| requires_intervention: cnki_garbled | 知网乱码PDF | 使用CAJViewer另存为PDF，或使用知网海外版直接下载 |
| requires_intervention: scanned | 扫描件PDF | 需要OCR处理，报告人工 |
| 提取文本为空 | 图片PDF | 标记为扫描件，报告人工 |
| 中文乱码 | 编码问题 | literature_skill 已自动处理，如仍失败则报告人工 |
| Grobid 连接失败 | 服务未启动 | 使用 PyMuPDF 后备方案 |

### 处理流程图

```
扫描 unprocessed/
    ↓
选择 ingest 单元
    ↓
对每篇PDF:
    ├─ 调用 literature_skill 处理
    ├─ 质量检测(PDF类型/加密/乱码/扫描件)
    ├─ 成功? → 生成分章节 Markdown，读取索引 JSON
    ├─ 需干预? → 按 requires_intervention 原因报告
    └─ 失败? → 明文报错，记录原因，继续下一篇
    ↓
从索引 JSON 提取元数据和分块信息
    ↓
读取结构化 Markdown 内容
    ↓
创建/更新 wiki 页面
    ↓
更新索引和日志
    ↓
报告处理结果（成功+需干预+失败）
    ↓
标记 pending_review（仅成功文件）
```

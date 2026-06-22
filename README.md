# Personal Wiki Agent

> 基于 Obsidian + Claudian + Claude Code CLI 的个人知识库 AI 代理
> 把你的 Obsidian 变成一个由 AI 代理维护的、结构化、可交叉引用的个人 wiki

---

## 🧠 这是什么

**LLM Wiki 模式**（源自 [Andrej Karpathy 的核心理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)）：不是简单的 RAG 检索，而是**增量构建和维护一个持久的 wiki**——一个结构化、相互关联的 Markdown 文件集合，位于你和原始资料之间。

本项目基于 [songzhuozhu/obsidian-llm-wiki](https://github.com/songzhuozhu/obsidian-llm-wiki) 的启发，并直接受益于 [YishenTu/claudian](https://github.com/YishenTu/claudian) 插件，将这套工作流落地为可复用的配置包。

**核心工作流：**
1. 把原始资料（PDF、网页剪藏等）丢进 `raw/` 文件夹
2. AI 代理自动 ingest、提炼、交叉链接，沉淀到 `wiki/`
3. 你提问时，代理基于已有的 wiki 结构综合回答
4. 知识库随着你添加的资料和提出的问题逐步丰富

---

## ✅ 前置条件（请自行安装）

| 软件 | 下载地址 | 用途 |
|------|---------|------|
| **Obsidian** | [https://obsidian.md/download](https://obsidian.md/download) | 知识库编辑器 |
| **Node.js** | [https://nodejs.org/](https://nodejs.org/) | 运行 JavaScript |
| **Git** | [https://git-scm.com/downloads](https://git-scm.com/downloads) | 版本控制 |
| **Python 3** | [https://www.python.org/downloads/](https://www.python.org/downloads/) | 运行脚本（含论文处理） |
| **Claude Code CLI** | 安装 Node.js 后运行 `npm install -g @anthropic-ai/claude-code` | AI 代理引擎 |

> 以上软件均为当前主流工具，官网下载安装即可，建议使用默认安装路径。

---

## 🚀 快速开始

### 第一步：克隆本仓库

```bash
git clone https://github.com/XIKONGSAKET/personal-wiki-agent.git
cd personal-wiki-agent
```

### 第二步：创建 Obsidian Vault

1. 打开 Obsidian
2. 点击「创建新库」
3. 选择一个文件夹作为你的 Vault（例如 `D:\MyWiki`）
4. 创建后关闭 Obsidian

### 第三步：部署配置

以管理员身份打开 PowerShell，运行部署脚本：

```powershell
# 将 vault-template 部署到你的 vault
# 将 skills 部署到 Claude Code CLI
.\scripts\deploy.ps1 -VaultPath "D:\MyWiki"
```

这个脚本会做三件事：
1. 把 `config/vault-template/` 复制到你的 Vault 目录（包含 Obsidian 插件配置 + Claudian 配置）
2. 把 `skills/` 目录复制到 `%USERPROFILE%\.claude\skills\`（AI 代理的专业技能包）
3. 提示你配置 API Key

### 第四步：获取 API Key

选择以下任一供应商获取 API Key：

**选项 A：DeepSeek**
- 注册：[https://platform.deepseek.com](https://platform.deepseek.com)
- 在 API Keys 页面创建 Key
- API 地址：`https://api.deepseek.com/anthropic`
- 模型：`deepseek-v4-pro`

**选项 B：智谱 GLM（通过阿里云百炼）**
- 注册：[https://bailian.console.aliyun.com](https://bailian.console.aliyun.com)
- 开通 DashScope 服务获取 API Key
- API 地址：`https://dashscope.aliyuncs.com/apps/anthropic`
- 模型：`glm-5.2`

### 第五步：配置 API Key

在 Obsidian 中：
1. 打开你的 Vault
2. 按 `Ctrl+P` 打开命令面板
3. 搜索并运行「Claudian: Toggle」
4. 在 Claudian 设置中选择供应商并填写 API Key

### 第六步：开始使用

在 Obsidian 中按 `Ctrl+P` → 选择「Claudian: Toggle」→ 开始对话。

---

## 📁 仓库结构

```
personal-wiki-agent/
├── README.md                          # 本文档
├── CLAUDE.md                          # 核心规则（LLM Wiki 工作引擎）
├── config/
│   └── vault-template/               # Obsidian Vault 配置模板
│       ├── .obsidian/                 # Obsidian 设置 + 插件
│       │   └── plugins/
│       │       ├── claudian/          # AI 聊天插件
│       │       ├── dataview/          # 数据查询
│       │       ├── templater-obsidian/# 模板引擎
│       │       └── ...
│       ├── .claudian/
│       │   └── claudian-settings.json # Claudian 配置（含供应商模板，不含 API Key）
│       └── .claude/                   # Claude Code CLI 配置
├── skills/                            # AI 代理专业技能包（50+ 个 Skill）
│   ├── literature_skill/              # 🏗️ PDF 论文处理工具（原创）
│   ├── arxiv-paper-analyze/           # 论文深度分析
│   ├── frontend-design/               # 前端设计
│   ├── ...
│   └── skills.json                    # 完整清单
└── scripts/
    └── deploy.ps1                     # Windows 一键部署脚本
```

---

## 🎯 预装 Skills 一览

本项目预装 50 个 Skills，覆盖以下领域：

| 类别 | Skills |
|------|--------|
| **学术论文** | `literature_skill`（原创）、`arxiv-paper-analyze`、`arxiv-paper-search`、`arxiv-start-my-day`、`arxiv-conf-papers`、`arxiv-extract-paper-images`、`paper_memory_manager` |
| **CNKI 知网** | `cnki-search`、`cnki-advanced-search`、`cnki-paper-detail`、`cnki-download`、`cnki-export`、`cnki-parse-results`、`cnki-navigate-pages`、`cnki-journal-search`、`cnki-journal-index`、`cnki-journal-toc` |
| **前端/AI 生成** | `frontend-design`、`canvas-design`、`web-artifacts-builder`、`algorithmic-art`、`brand-guidelines`、`theme-factory` |
| **思维框架** | `brainstorming`、`ideation`、`sun-yimin-perspective`、`nuwa`、`humanizer` |
| **文档协作** | `doc-coauthoring`、`research-paper-writing`、`internal-comms`、`md-to-word` |
| **Obsidian** | `obsidian-markdown`、`obsidian-bases`、`obsidian-cli`、`json-canvas` |
| **MCP/工具** | `mcp-builder`、`skill-creator`、`claude-api` |
| **搜索** | `anysearch`、`tavily-search`、`defuddle` |
| **办公** | `docx`、`xlsx`、`pptx`、`pdf`、`slack-gif-creator` |
| **其他** | `webapp-testing`、`literature_skill`、`academic-writing-assistant` |

---

## 🏗️ `literature_skill`（原创）

`literature_skill` 是本项目作者 **[@XIKONGSAKET](https://github.com/XIKONGSAKET)** 独立开发的 PDF 论文处理工具，用于：知网论文的智能识别、质量检测、按章节分块、内容提取。

**核心功能：**
- 自动识别文档类型（期刊论文、学位论文、书籍等）
- 质量检测（知网乱码、扫描件、加密 PDF）
- 按小标题智能分块（3-10 页独立成块）
- 多栏布局重建
- 生成结构化 Markdown 摘要

使用方式：
```bash
python -m literature_skill "/path/to/paper.pdf" -o "./output"
```

---

## 🙏 致谢

- [songzhuozhu/obsidian-llm-wiki](https://github.com/songzhuozhu/obsidian-llm-wiki) — 直接启发本项目
- [Andrej Karpathy 的 LLM Wiki 理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — LLM Wiki 理论的开山鼻祖
- [YishenTu/claudian](https://github.com/YishenTu/claudian) — Obsidian AI 聊天插件
- [Anthropic Claude Code CLI](https://code.claude.com/docs/en/overview) — AI 代理引擎

---

## 📄 许可

MIT License

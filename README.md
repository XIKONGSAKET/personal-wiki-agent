# Personal Wiki Agent

> 把你的 Obsidian 变成 AI 帮你写笔记的知识库

---

## 🧠 这是什么

这个项目让你在 Obsidian 里直接和一个 AI 助手对话，它能帮你：
- **整理资料**：丢给它一篇 PDF，它自动读完、总结、分类
- **回答问题**：问你存过的所有资料，它都能找到答案
- **写笔记**：你的碎片想法，它能帮你写成有条理的笔记

**使用的时候不需要翻墙就能用。** 用国产 DeepSeek 的 API 就行。（安装 Claude Code CLI 时需要临时翻墙一下，后面不再需要）

---

## 🙏 致谢

- [songzhuozhu/obsidian-llm-wiki](https://github.com/songzhuozhu/obsidian-llm-wiki) — 这个项目的灵感来源
- [Andrej Karpathy 的 LLM Wiki 理念](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — LLM Wiki 理论的开山鼻祖
- [YishenTu/claudian](https://github.com/YishenTu/claudian) — Obsidian AI 聊天插件
- [Anthropic Claude Code CLI](https://code.claude.com/docs/en/overview) — AI 代理引擎

---

## 📋 安装前的准备

> **请严格按照以下顺序安装！** 跳步或顺序不对会导致后面出错。
> **注意：所有路径中不要包含中文（目录名必须用英文），否则可能报错。**

### 先注册 DeepSeek，获取 API Key

1. 打开 https://platform.deepseek.com/api_keys
2. 点「Register」注册账号（可以用邮箱）
3. 登录后点「Create API Key」
4. 给你的 Key 起个名字（比如 "mywiki"），点创建
5. **复制出现的 Key**（以 `sk-` 开头，很重要！）
6. 把 Key 先粘贴到记事本里存着，后面要用

---

### 第一步：安装 Node.js

1. 打开 https://nodejs.org/
2. 下载左边的「LTS」（长期支持版）
3. 双击下载好的安装包
4. 一路点「Next」（下一步）
5. 点「Install」（安装）
6. 安装完成后点「Finish」
7. **重启电脑**

> 怎么确认装好了？按 `Win + R`，输入 `cmd` 回车，输入 `node -v` 回车。如果显示版本号（比如 v20.x.x），说明装好了。

---

### 第二步：安装 Git

1. 打开 https://git-scm.com/downloads/win
2. 下载会自动开始
3. 双击安装包
4. 一路点「Next」
5. 点「Install」
6. 安装完成后点「Finish」
7. **重启电脑**

---

### 第三步：安装 Python

1. 打开 https://www.python.org/downloads/
2. 点黄色的「Download Python 3.xx.x」按钮
3. 双击下载好的安装包
4. **⚠️ 这一步很重要：** 安装界面最下面有个「Add Python to PATH」，**一定要勾上！**
5. 点「Install Now」
6. 安装完成后点「Close」
7. **重启电脑**

---

### 第四步：安装 Claude Code CLI（AI 引擎）

> ⚠️ **这一步需要打开你的加速器（VPN/翻墙工具）**，因为 npm install 需要从外网下载。装完后可以关掉。

这是 AI 的大脑，需要在 PowerShell 里安装。

**怎么打开 PowerShell：**
1. 点屏幕左下角的「开始」按钮（Windows 图标）
2. 键盘输入 **PowerShell**（不用点，直接打字）
3. 你会看到搜索结果里出现「Windows PowerShell」
4. **右键**点它，选择「以管理员身份运行」
5. 如果弹出窗口问「是否允许此应用……」，点「是」

**在 PowerShell 里执行安装命令：**

复制下面这行命令，在 PowerShell 窗口里点**右键**（会自动粘贴），然后按回车：

```powershell
npm install -g @anthropic-ai/claude-code --ignore-scripts
```

等待安装完成（可能需要 1-2 分钟），看到出现 `C:\...` 之类的提示就说明装好了。

---

### 第五步：安装 Obsidian

1. 打开 https://obsidian.md/download
2. 点「Download for Windows」
3. 双击安装包
4. 安装完成后，**暂时不要打开 Obsidian**

---

## 🚀 开始配置

### 第六步：下载本项目的文件

1. 打开 https://github.com/XIKONGSAKET/personal-wiki-agent
2. 点绿色的「Code」按钮
3. 点「Download ZIP」
4. 下载完成后，**右键**这个 ZIP 文件，选择「解压到……」
5. **解压到桌面**（这样好找）

解压后会有一个名叫 `personal-wiki-agent-main` 的文件夹。**注意：这个文件夹路径中不能有中文。**

---

### 第七步：创建你的 Obsidian 知识库（Vault）

1. 打开 Obsidian
2. 你会看到「创建新库」（Create new vault）
3. 给你的库起个名字，**用英文字母**（比如 "MyWiki"）
4. 选择一个文件夹位置（比如 `D:\MyWiki`），**路径中不要有中文**
5. 点「创建」
6. Obsidian 会自动打开你的新库
7. **直接关掉 Obsidian**（点右上角的 X）

---

### 第八步：运行部署脚本

1. **重新打开 PowerShell（以管理员身份）**
   - 点「开始」，输入 PowerShell
   - 右键「Windows PowerShell」→「以管理员身份运行」

2. **进入解压的文件夹**
   在 PowerShell 里输入下面这个命令，按回车：
   ```powershell
   cd C:\Users\你的用户名\Desktop\personal-wiki-agent-main
   ```
   > 把「你的用户名」换成你自己的 Windows 用户名。如果你不确定，可以打开文件资源管理器，进入 `C:\Users\` 看一眼。

3. **运行部署脚本**
   在 PowerShell 里输入：
   ```powershell
   .\scripts\deploy.ps1
   ```
   按回车
   
   如果弹出提示「无法加载文件……因为在此系统上禁止运行脚本」，请输入：
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
   ```
   然后再试一次 `.\scripts\deploy.ps1`

4. **按照提示操作：**
   - 输入你的 Obsidian Vault 路径（就是第七步创建的那个文件夹路径，例如 `D:\MyWiki`）
   - 粘贴你的 DeepSeek API Key（从第一步保存的那个 `sk-` 开头的 Key）
   - 等脚本自动完成

---

### 第九步：开始使用

1. 打开 Obsidian
2. 点击左下角「打开其他库」→「打开本地库」
3. 选择你刚才创建的 Vault 文件夹（例如 `D:\MyWiki`）
4. 按键盘上的 `Ctrl + P`
5. 在弹出的输入框里打字：**Claudian: Toggle**
6. 按回车
7. 你会看到右侧出现一个聊天窗口
8. 现在你就可以和 AI 对话了！试试说：
   > 「你好，帮我整理一下这个知识库」

---

## ❓ 常见问题

**问：安装时提示「管理员权限不足」**
答：右键 PowerShell，选「以管理员身份运行」，再试一次

**问：Claudian 聊天窗口没出现**
答：检查 Obsidian → 设置 → 第三方插件 → 安全模式已关闭 → Claudian 已在已安装插件列表中

**问：API 连接失败**
答：检查 API Key 是否正确。打开 https://platform.deepseek.com/api_keys 确认你的 Key 还有余额

**问：AI 不回答或回答很慢**
答：DeepSeek 免费额度有限，确认你的账户有余额

**问：PowerShell 里中文路径报错**
答：所有路径（Vault 路径、项目文件夹路径）都不要用中文，用英文字母和数字。

---

## 📁 这个文件夹里都有什么

```
personal-wiki-agent-main/
├── README.md                    ← 你正在看的这个说明
├── CLAUDE.md                    ← AI 助手的工作规则（不用管它）
├── config/
│   └── vault-template/          ← Obsidian 的配置文件（不用管它）
│       ├── .obsidian/            ← Obsidian 插件
│       └── .claudian/           ← AI 聊天插件的设置
├── skills/                      ← AI 的专业技能包（49 个）
│   ├── literature_skill/        ← 📚 论文处理工具（基于 DeepSeek 开发）
│   ├── arxiv-paper-analyze/     ← 论文分析
│   ├── frontend-design/         ← 网页设计
│   └── ...
├── scripts/
│   └── deploy.ps1               ← 部署脚本（你刚才运行的）
└── assets/
```

**关于 `literature_skill`**（文献处理技能）：由 @XIKONGSAKET 借助 DeepSeek Agent 开发，用于自动处理 PDF 论文（知网论文识别、按章节分块、内容提取）。

---

## 📄 许可

MIT License

<#
.SYNOPSIS
    Personal Wiki Agent - Windows 部署脚本
.DESCRIPTION
    将 vault-template 和 skills 部署到本地环境
    由 @XIKONGSAKET 维护
#>

param(
    [string]$VaultPath = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Split-Path $scriptDir -Parent
$vaultTemplate = Join-Path $repoDir "config\vault-template"
$skillsSrc = Join-Path $repoDir "skills"
$claudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"

Write-Host ""
Write-Host "============================================"
Write-Host " Personal Wiki Agent - 部署脚本"
Write-Host "============================================"
Write-Host ""

# ===== Step 1: Get Vault path =====
if (-not $VaultPath) {
    $VaultPath = Read-Host "请输入你的 Obsidian Vault 路径`n（例如 D:\MyWiki）"
}
if (-not (Test-Path $VaultPath)) {
    try {
        New-Item -ItemType Directory -Path $VaultPath -Force | Out-Null
        Write-Host "[OK] 已创建目录: $VaultPath" -ForegroundColor Green
    } catch {
        Write-Error "无法创建目录: $VaultPath"
        exit 1
    }
}

# ===== Step 2: Deploy vault template =====
Write-Host "[1/4] 部署 Vault 配置到你的 Obsidian 库..." -ForegroundColor Cyan
if (Test-Path $vaultTemplate) {
    Copy-Item "$vaultTemplate\.obsidian\*" "$VaultPath\.obsidian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claudian\*" "$VaultPath\.claudian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claude\*" "$VaultPath\.claude\" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Vault 配置已部署到: $VaultPath" -ForegroundColor Green
} else {
    Write-Warning "未找到 vault-template 目录，跳过"
}

# ===== Step 3: Deploy skills =====
Write-Host "[2/4] 部署 Skills 到 Claude Code CLI..." -ForegroundColor Cyan
if (Test-Path $skillsSrc) {
    if (-not (Test-Path $claudeSkillsDir)) {
        New-Item -ItemType Directory -Path $claudeSkillsDir -Force | Out-Null
    }
    $count = 0
    Get-ChildItem -Path $skillsSrc -Directory | ForEach-Object {
        $dest = Join-Path $claudeSkillsDir $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        $count++
    }
    Write-Host "[OK] $count 个 Skill 已部署到: $claudeSkillsDir" -ForegroundColor Green
} else {
    Write-Warning "未找到 skills 目录，跳过"
}

# ===== Step 4: Configure API Key =====
Write-Host "[3/4] 配置 DeepSeek API Key..." -ForegroundColor Cyan
Write-Host ""
Write-Host "你需要先注册 DeepSeek 账号获取 API Key："
Write-Host "  1. 打开 https://platform.deepseek.com/api_keys"
Write-Host "  2. 注册/登录账号"
Write-Host "  3. 点击「Create API Key」"
Write-Host "  4. 复制生成的 Key（以 sk- 开头）"
Write-Host ""

$apiKey = Read-Host "请输入你的 DeepSeek API Key（sk-开头）"

if ($apiKey -and $apiKey.StartsWith("sk-")) {
    $settingsPath = Join-Path $VaultPath ".claudian\claudian-settings.json"
    if (Test-Path $settingsPath) {
        $settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $envVars = "ANTHROPIC_BASE_URL=`"https://api.deepseek.com/anthropic`"`nANTHROPIC_AUTH_TOKEN=$apiKey`nANTHROPIC_MODEL=`"deepseek-v4-pro`""
        $hash = "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic|ANTHROPIC_MODEL=deepseek-v4-pro"
        $settings.providerConfigs.claude.environmentVariables = $envVars
        $settings.providerConfigs.claude.environmentHash = $hash
        $settings | ConvertTo-Json -Depth 10 | Out-File $settingsPath -Encoding UTF8 -Force
        Write-Host "[OK] API Key 已写入配置" -ForegroundColor Green
    } else {
        Write-Warning "未找到 $settingsPath，请先部署 Vault 配置"
    }
} else {
    Write-Warning "API Key 格式不正确，请检查是否以 sk- 开头"
    Write-Warning "你可以稍后在 Obsidian 中手动配置"
}

# ===== Step 5: Verify =====
Write-Host "[4/4] 验证部署..." -ForegroundColor Cyan
$obsidianPath = Join-Path $VaultPath ".obsidian\plugins\claudian"
if (Test-Path $obsidianPath) {
    Write-Host "[OK] Claudian 插件已就位" -ForegroundColor Green
} else {
    Write-Warning "Claudian 插件未找到，请检查 vault-template 是否正确部署"
}

$skillsCount = (Get-ChildItem $claudeSkillsDir -Directory).Count
Write-Host "[OK] Skills 已就位: $skillsCount 个" -ForegroundColor Green

Write-Host ""
Write-Host "============================================"
Write-Host " 部署完成！"
Write-Host "============================================"
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 打开 Obsidian"
Write-Host "  2. 点击左下角「打开其他库」→「打开本地库」，选择：$VaultPath"
Write-Host "  3. 按 Ctrl+P（Mac 是 Cmd+P）打开命令面板"
Write-Host "  4. 输入 Claudian: Toggle 并按回车"
Write-Host "  5. 在对话框中开始和 AI 对话！"
Write-Host ""
Read-Host "按回车退出"

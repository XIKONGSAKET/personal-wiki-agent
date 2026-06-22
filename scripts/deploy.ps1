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
    $VaultPath = Read-Host "请输入你的 Obsidian Vault 路径（例如 D:\MyWiki）"
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
Write-Host "[1/3] 部署 Vault 配置..." -ForegroundColor Cyan
if (Test-Path $vaultTemplate) {
    Copy-Item "$vaultTemplate\.obsidian\*" "$VaultPath\.obsidian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claudian\*" "$VaultPath\.claudian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claude\*" "$VaultPath\.claude\" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Vault 配置已部署到: $VaultPath" -ForegroundColor Green
} else {
    Write-Warning "未找到 vault-template 目录，跳过"
}

# ===== Step 3: Deploy skills =====
Write-Host "[2/3] 部署 Skills..." -ForegroundColor Cyan
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
Write-Host "[3/3] 配置 API Key..." -ForegroundColor Cyan
Write-Host ""
Write-Host "选择 AI 供应商："
Write-Host "  1) DeepSeek"
Write-Host "  2) 智谱 GLM（via 阿里云百炼）"
$choice = Read-Host "请选择 (1 或 2)"

if ($choice -eq "1" -or $choice -eq "2") {
    $apiKey = Read-Host -Prompt "请输入你的 API Key（sk-开头）"
    if ($apiKey -and $apiKey.StartsWith("sk-")) {
        $settingsPath = Join-Path $VaultPath ".claudian\claudian-settings.json"
        if (Test-Path $settingsPath) {
            $settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($choice -eq "1") {
                $envVars = "ANTHROPIC_BASE_URL=`"https://api.deepseek.com/anthropic`"`nANTHROPIC_AUTH_TOKEN=$apiKey`nANTHROPIC_MODEL=`"deepseek-v4-pro`""
                $hash = "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic|ANTHROPIC_MODEL=deepseek-v4-pro"
            } else {
                $envVars = "ANTHROPIC_BASE_URL=`"https://dashscope.aliyuncs.com/apps/anthropic`"`nANTHROPIC_API_KEY=$apiKey`nANTHROPIC_MODEL=`"glm-5.2`""
                $hash = "ANTHROPIC_BASE_URL=https://dashscope.aliyuncs.com/apps/anthropic|ANTHROPIC_MODEL=glm-5.2"
            }
            $settings.providerConfigs.claude.environmentVariables = $envVars
            $settings.providerConfigs.claude.environmentHash = $hash
            $settings | ConvertTo-Json -Depth 10 | Out-File $settingsPath -Encoding UTF8 -Force
            Write-Host "[OK] API Key 已写入配置" -ForegroundColor Green
        } else {
            Write-Warning "未找到 $settingsPath，请先部署 Vault 配置"
        }
    } else {
        Write-Warning "API Key 格式不正确，请检查是否以 sk- 开头"
    }
} else {
    Write-Warning "跳过 API 配置，稍后可在 Obsidian 中手动设置"
}

Write-Host ""
Write-Host "============================================"
Write-Host " 部署完成！"
Write-Host "============================================"
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 打开 Obsidian，加载 Vault：$VaultPath"
Write-Host "  2. 按 Ctrl+P → 搜索 Claudian: Toggle → 回车"
Write-Host "  3. 开始构建你的知识库！"
Write-Host ""
Read-Host "按回车退出"

<#
.SYNOPSIS
    Personal Wiki Agent - Windows 閮ㄧ讲鑴氭湰
.DESCRIPTION
    灏?vault-template 鍜?skills 閮ㄧ讲鍒版湰鍦扮幆澧?    鐢?@XIKONGSAKET 缁存姢
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
Write-Host " Personal Wiki Agent - 閮ㄧ讲鑴氭湰"
Write-Host "============================================"
Write-Host ""

# ===== Step 1: Get Vault path =====
if (-not $VaultPath) {
    $VaultPath = Read-Host "璇疯緭鍏ヤ綘鐨?Obsidian Vault 璺緞`n锛堜緥濡?D:\MyWiki锛?
}
if (-not (Test-Path $VaultPath)) {
    try {
        New-Item -ItemType Directory -Path $VaultPath -Force | Out-Null
        Write-Host "[OK] 宸插垱寤虹洰褰? $VaultPath" -ForegroundColor Green
    } catch {
        Write-Error "鏃犳硶鍒涘缓鐩綍: $VaultPath"
        exit 1
    }
}

# ===== Step 2: Deploy vault template =====
Write-Host "[1/4] 閮ㄧ讲 Vault 閰嶇疆鍒颁綘鐨?Obsidian 搴?.." -ForegroundColor Cyan
if (Test-Path $vaultTemplate) {
    Copy-Item "$vaultTemplate\.obsidian\*" "$VaultPath\.obsidian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claudian\*" "$VaultPath\.claudian\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "$vaultTemplate\.claude\*" "$VaultPath\.claude\" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Vault 閰嶇疆宸查儴缃插埌: $VaultPath" -ForegroundColor Green
} else {
    Write-Warning "鏈壘鍒?vault-template 鐩綍锛岃烦杩?
}

# ===== Step 3: Deploy skills =====
Write-Host "[2/4] 閮ㄧ讲 Skills 鍒?Claude Code CLI..." -ForegroundColor Cyan
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
    Write-Host "[OK] $count 涓?Skill 宸查儴缃插埌: $claudeSkillsDir" -ForegroundColor Green
} else {
    Write-Warning "鏈壘鍒?skills 鐩綍锛岃烦杩?
}

# ===== Step 4: Configure API Key =====
Write-Host "[3/4] 閰嶇疆 DeepSeek API Key..." -ForegroundColor Cyan
Write-Host ""
Write-Host "浣犻渶瑕佸厛娉ㄥ唽 DeepSeek 璐﹀彿鑾峰彇 API Key锛?
Write-Host "  1. 鎵撳紑 https://platform.deepseek.com/api_keys"
Write-Host "  2. 娉ㄥ唽/鐧诲綍璐﹀彿"
Write-Host "  3. 鐐瑰嚮銆孋reate API Key銆?
Write-Host "  4. 澶嶅埗鐢熸垚鐨?Key锛堜互 sk- 寮€澶达級"
Write-Host ""

$apiKey = Read-Host "璇疯緭鍏ヤ綘鐨?DeepSeek API Key锛坰k-寮€澶达級"

if ($apiKey -and $apiKey.StartsWith("sk-")) {
    $settingsPath = Join-Path $VaultPath ".claudian\claudian-settings.json"
    if (Test-Path $settingsPath) {
        $settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $envVars = "ANTHROPIC_BASE_URL=`"https://api.deepseek.com/anthropic`"`nANTHROPIC_AUTH_TOKEN=$apiKey`nANTHROPIC_MODEL=`"deepseek-v4-pro`""
        $hash = "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic|ANTHROPIC_MODEL=deepseek-v4-pro"
        $settings.providerConfigs.claude.environmentVariables = $envVars
        $settings.providerConfigs.claude.environmentHash = $hash
        $settings | ConvertTo-Json -Depth 10 | Out-File $settingsPath -Encoding UTF8 -Force
        Write-Host "[OK] API Key 宸插啓鍏ラ厤缃? -ForegroundColor Green
    } else {
        Write-Warning "鏈壘鍒?$settingsPath锛岃鍏堥儴缃?Vault 閰嶇疆"
    }
} else {
    Write-Warning "API Key 鏍煎紡涓嶆纭紝璇锋鏌ユ槸鍚︿互 sk- 寮€澶?
    Write-Warning "浣犲彲浠ョ◢鍚庡湪 Obsidian 涓墜鍔ㄩ厤缃?
}

# ===== Step 5: Verify =====
Write-Host "[4/4] 楠岃瘉閮ㄧ讲..." -ForegroundColor Cyan
$obsidianPath = Join-Path $VaultPath ".obsidian\plugins\claudian"
if (Test-Path $obsidianPath) {
    Write-Host "[OK] Claudian 鎻掍欢宸插氨浣? -ForegroundColor Green
} else {
    Write-Warning "Claudian 鎻掍欢鏈壘鍒帮紝璇锋鏌?vault-template 鏄惁姝ｇ‘閮ㄧ讲"
}

$skillsCount = (Get-ChildItem $claudeSkillsDir -Directory).Count
Write-Host "[OK] Skills 宸插氨浣? $skillsCount 涓? -ForegroundColor Green

Write-Host ""
Write-Host "============================================"
Write-Host " 閮ㄧ讲瀹屾垚锛?
Write-Host "============================================"
Write-Host ""
Write-Host "涓嬩竴姝ワ細"
Write-Host "  1. 鎵撳紑 Obsidian"
Write-Host "  2. 鐐瑰嚮宸︿笅瑙掋€屾墦寮€鍏朵粬搴撱€嶁啋銆屾墦寮€鏈湴搴撱€嶏紝閫夋嫨锛?VaultPath"
Write-Host "  3. 鎸?Ctrl+P锛圡ac 鏄?Cmd+P锛夋墦寮€鍛戒护闈㈡澘"
Write-Host "  4. 杈撳叆 Claudian: Toggle 骞舵寜鍥炶溅"
Write-Host "  5. 鍦ㄥ璇濇涓紑濮嬪拰 AI 瀵硅瘽锛?
Write-Host ""
Read-Host "鎸夊洖杞﹂€€鍑?

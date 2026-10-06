<#
.SYNOPSIS
    GitHub Auto Push & Real-time Release Script for AhBiYout / PowerController
.DESCRIPTION
    동적 버전 추출(Single Source of Truth), 개인정보 보호, Git 태깅 및 GitHub Releases 연동을 일괄 수행합니다.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 1. 다단 동적 버전 추출
$appVersion = "2.9.1"
if (Test-Path "package.json") {
    try {
        $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
        if ($pkg.version) { $appVersion = $pkg.version }
    } catch {}
} elseif (Test-Path "docs/PATCHNOTES.md") {
    $match = Select-String -Path "docs/PATCHNOTES.md" -Pattern "## \[v([0-9]+\.[0-9]+\.[0-9]+)\]" | Select-Object -First 1
    if ($match -and $match.Matches.Groups[1].Value) {
        $appVersion = $match.Matches.Groups[1].Value
    }
}

$Host.UI.RawUI.WindowTitle = "GitHub Auto Sync [v$appVersion] - ahbiyout-all / PowerController"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  [GitHub Auto Push & Real-time Release Tool (PowerShell)]" -ForegroundColor Cyan
Write-Host "  - GitHub Account : ahbiyout-all" -ForegroundColor Yellow
Write-Host "  - Git Username   : AhBiYout-all" -ForegroundColor Yellow
Write-Host "  - App Version    : v$appVersion (Single Source of Truth)" -ForegroundColor Green
Write-Host "  - Repository     : https://github.com/ahbiyout-all/PowerController.git" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 2. Git 설치 확인
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[오류] 시스템에 Git이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "https://git-scm.com/ 에서 Git을 설치한 후 다시 시도해주세요." -ForegroundColor Yellow
    Read-Host "엔터 키를 누르면 종료합니다..."
    exit 1
}

# 3. .git 초기화 확인
if (-not (Test-Path ".git")) {
    Write-Host "[*] Git 저장소를 초기화합니다 (git init)..." -ForegroundColor Green
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[오류] git init 실패" -ForegroundColor Red
        exit 1
    }
}

# 4. 작성자 정보 자동 설정 (GitHub 공식 보안 비공개 이메일 전용)
$selectedEmail = "ahbiyout-all@users.noreply.github.com"
git config user.name "AhBiYout-all"
git config user.email $selectedEmail
Write-Host "[V] 작성자 이름 : AhBiYout-all" -ForegroundColor Cyan
Write-Host "[V] 보안 이메일 : $selectedEmail (개인정보 완벽 보호)" -ForegroundColor Green
Write-Host ""

# 5. 원격 저장소(origin) 등록 및 확인
$remoteUrl = "https://github.com/ahbiyout-all/PowerController.git"
$existingRemote = git remote get-url origin 2>$null

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($existingRemote)) {
    Write-Host "[*] 원격 저장소(origin) 등록: $remoteUrl" -ForegroundColor Green
    git remote add origin $remoteUrl
} else {
    git remote set-url origin $remoteUrl
    Write-Host "[*] 원격 저장소: $remoteUrl" -ForegroundColor Gray
}

# 6. 브랜치 main 통일
git branch -M main

# 7. 커밋 메시지 입력 (버전 정보 동적 포함)
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$defaultMsg = "Release v$appVersion - $timestamp"
$customMsg = Read-Host "커밋 메시지를 입력하세요 (엔터 시 '$defaultMsg' 사용)"

if ([string]::IsNullOrWhiteSpace($customMsg)) {
    $commitMsg = $defaultMsg
} else {
    $commitMsg = $customMsg
}

Write-Host ""
Write-Host "[*] 변경된 모든 파일 추가 중 (git add -A)..." -ForegroundColor Green
git add -A

Write-Host "[*] 커밋 생성 중 (git commit)..." -ForegroundColor Green
git commit -m "$commitMsg"

# 8. GitHub Releases 연동을 위한 동적 버전 태깅
$tagName = "v$appVersion"
$tagExists = git tag -l $tagName
$pushTag = $false

if (-not $tagExists) {
    Write-Host "[*] 신규 릴리스 버전 태그 생성 ($tagName)..." -ForegroundColor Green
    git tag -a $tagName -m "Release $tagName"
    $pushTag = $true
} else {
    Write-Host "[*] 버전 태그 $tagName 이(가) 이미 존재합니다." -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  GitHub 원격 저장소(main 브랜치)로 푸시(git push)를 시작합니다..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

git push -u origin main

if ($pushTag) {
    Write-Host "[*] GitHub Releases 연동을 위해 버전 태그($tagName)를 푸시합니다..." -ForegroundColor Green
    git push origin $tagName
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "  [성공] GitHub에 성공적으로 업로드 및 릴리스되었습니다!" -ForegroundColor Green
    Write-Host "  - 버전 태그: v$appVersion" -ForegroundColor White
    Write-Host "  - 저장소 링크: https://github.com/AhBiYout/PowerController" -ForegroundColor Green
    Write-Host "  - 릴리스 링크: https://github.com/AhBiYout/PowerController/releases" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host "  [확인 필요] git push 중 인증 요청 또는 오류가 발생했습니다." -ForegroundColor Yellow
    Write-Host "  1. GitHub 웹(https://github.com/new)에 'PowerController' 레포지토리가 생성되어 있는지 확인하세요." -ForegroundColor White
    Write-Host "  2. 비밀번호 대신 GitHub Personal Access Token(PAT)을 입력해야 합니다." -ForegroundColor White
    Write-Host "================================================================" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "엔터 키를 누르면 종료합니다..."

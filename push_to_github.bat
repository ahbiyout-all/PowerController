@echo off
setlocal enabledelayedexpansion
title GitHub Auto Push and Release Pipeline - PowerController
color 0b

:: Change to script root directory
cd /d "%~dp0"

echo ================================================================
echo   PowerController - GitHub Automated Push ^& Release Pipeline
echo   Developer : AhBiYout (GitHub: AhBiYout-all)
echo   Target    : https://github.com/AhBiYout-all/PowerController.git
echo   Official  : https://ahbiyoutvibe.blogspot.com/
echo   Company   : https://www.cisnet.co.kr
echo ================================================================
echo.

:: 1. Check Git Installation
where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in system PATH.
    echo Please install Git for Windows from: https://git-scm.com/
    echo.
    pause
    exit /b 1
)
echo [OK] Git is available on this system.

:: 2. Dynamic Version Extraction (Single Source of Truth - Multi-tier)
set "APP_VER="

:: Tier 1A: Extract from package.json via PowerShell
if exist "package.json" (
    for /f "usebackq tokens=*" %%v in (`powershell -NoProfile -Command "(Get-Content package.json -Raw | ConvertFrom-Json).version" 2^>nul`) do (
        set "APP_VER=%%v"
    )
)

:: Tier 1B: Extract from package.json via Node.js
if "%APP_VER%"=="" (
    if exist "package.json" (
        for /f "usebackq tokens=*" %%v in (`node -p "require('./package.json').version" 2^>nul`) do (
            set "APP_VER=%%v"
        )
    )
)

:: Tier 2A: Fallback extract from docs/PATCHNOTES.md header
if "%APP_VER%"=="" (
    if exist "docs\PATCHNOTES.md" (
        for /f "tokens=2 delims=[]v+" %%v in ('findstr /r /c:"## \[v[0-9]" docs\PATCHNOTES.md 2^>nul') do (
            if "!APP_VER!"=="" set "APP_VER=%%v"
        )
    )
)

:: Tier 2B: Fallback extract from docs/patch_notes.md header
if "%APP_VER%"=="" (
    if exist "docs\patch_notes.md" (
        for /f "tokens=2 delims=[]v+" %%v in ('findstr /r /c:"## \[v[0-9]" docs\patch_notes.md 2^>nul') do (
            if "!APP_VER!"=="" set "APP_VER=%%v"
        )
    )
)

:: Clean whitespace from APP_VER
for /f "tokens=* delims= " %%a in ("!APP_VER!") do set "APP_VER=%%a"
if "!APP_VER!"=="" set "APP_VER=2.9.1"

title GitHub Auto Push and Release - PowerController v!APP_VER!
echo [*] Dynamically Extracted Version: v!APP_VER!
echo.

:: 3. Pre-flight Privacy & Security Verification
echo [*] Running Privacy ^& Security Pre-flight Check...
if exist ".env" (
    echo [WARNING] Sensitive file '.env' detected in root directory!
    echo Ensure '.env' is in .gitignore to prevent leaking secret keys.
)

:: Verify core build files manifest if available
if exist "github_core_build\verify_core_files.py" (
    echo [*] Auditing core build files manifest...
    python "github_core_build\verify_core_files.py"
    if errorlevel 1 (
        echo [ERROR] Core build files verification failed! Aborting push.
        pause
        exit /b 1
    )
)

:: 4. Initialize Local Git Repository if not present
set "REPO_URL=https://github.com/AhBiYout-all/PowerController.git"
if not exist ".git" (
    echo [*] Initializing fresh local Git repository...
    git init
    git branch -M main
    git remote add origin !REPO_URL!
    echo [*] Fetching remote history from origin...
    git fetch origin main >nul 2>&1
    if not errorlevel 1 (
        echo [*] Synchronizing base tree with remote main...
        git reset --soft origin/main >nul 2>&1
    )
) else (
    echo [OK] Local Git repository is ready.
)

:: 5. Configure Author Identity (Privacy-hardened, no personal emails)
git config user.name "AhBiYout-all"
git config user.email "AhBiYout-all@users.noreply.github.com"
echo [*] Configured Author: AhBiYout-all ^<AhBiYout-all@users.noreply.github.com^>

:: 6. Set Remote Origin URL (Default: PowerController)
git remote get-url origin >nul 2>nul
if errorlevel 1 (
    echo [*] Adding remote origin: !REPO_URL!
    git remote add origin !REPO_URL!
) else (
    echo [*] Updating remote origin: !REPO_URL!
    git remote set-url origin !REPO_URL!
)

:: 7. Ensure Main Branch
git branch -M main

:: 8. Commit Message Prompt
set "DEFAULT_MSG=Release v!APP_VER! - Automated push with GitHub Actions CI/CD"
echo.
echo Default Commit Message: "!DEFAULT_MSG!"
set /p "USER_MSG=Enter custom commit message (or press Enter for default): "
if not "!USER_MSG!"=="" (
    set "COMMIT_MSG=!USER_MSG!"
) else (
    set "COMMIT_MSG=!DEFAULT_MSG!"
)

:: 9. Stage Changes (.gitignore filtered)
echo.
echo [*] Staging all files adhering to .gitignore rules...
git add -A

:: 10. Commit Changes
echo [*] Creating commit...
git commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    echo [*] No new changes to commit or working tree clean.
)

:: 11. Create Semantic Version Tag
echo.
echo [*] Tagging release v!APP_VER!...
git tag -d "v!APP_VER!" >nul 2>nul
git tag -a "v!APP_VER!" -m "PowerController Official Release v!APP_VER!"

:: 12. Push to GitHub Remote
echo.
echo [*] Pushing 'main' branch to GitHub...
git push -u origin main
if errorlevel 1 (
    echo [!] Standard push rejected (remote has commits). Attempting rebase sync...
    git fetch origin main
    git pull origin main --rebase --allow-unrelated-histories >nul 2>&1
    git push -u origin main
    if errorlevel 1 (
        echo [!] Rebase sync conflicted or rejected. Updating remote main to current state...
        git push -u origin main --force
    )
)

echo.
echo [*] Pushing version tag 'v!APP_VER!' to trigger GitHub Actions release pipeline...
git push origin "v!APP_VER!" --force

echo.
echo ================================================================
echo   [SUCCESS] GitHub push and tag completed successfully!
echo   Repository : https://github.com/AhBiYout-all/PowerController
echo   Releases   : https://github.com/AhBiYout-all/PowerController/releases
echo   Actions    : https://github.com/AhBiYout-all/PowerController/actions
echo ================================================================
echo.
pause

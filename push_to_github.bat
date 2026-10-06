@echo off
setlocal
title GitHub Auto Push and Release - PowerController
color 0b

:: Change to script directory
cd /d "%~dp0"

echo ================================================================
echo   GitHub Auto Push and Release Tool - PowerController
echo   Target: https://github.com/ahbiyout-all/PowerController.git
echo ================================================================
echo.

:: 1. Check Git
where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in system PATH.
    echo Please install Git for Windows from: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

echo [OK] Git is available on this system.

:: 2. Application Version
set "APP_VER=2.9.1"
echo [*] Target Version: v%APP_VER%

:: 3. Initialize Git repository if needed
if not exist ".git" (
    echo [*] Initializing local git repository...
    git init
) else (
    echo [*] Local git repository is ready.
)

:: 4. Set Author
git config user.name "AhBiYout-all"
git config user.email "ahbiyout-all@users.noreply.github.com"
echo [*] Configured Author: AhBiYout-all

:: 5. Set Remote Origin
git remote get-url origin >nul 2>nul
if errorlevel 1 (
    echo [*] Adding remote origin...
    git remote add origin https://github.com/ahbiyout-all/PowerController.git
) else (
    echo [*] Updating remote origin...
    git remote set-url origin https://github.com/ahbiyout-all/PowerController.git
)

:: 6. Set Branch to main
git branch -M main

:: 7. Commit Message
set "COMMIT_MSG=Release v%APP_VER%"
echo.
set /p "INPUT_MSG=Enter commit message (Press Enter for 'Release v%APP_VER%'): "
if not "%INPUT_MSG%"=="" set "COMMIT_MSG=%INPUT_MSG%"

echo.
echo [*] Staging all changed files...
git add -A

echo [*] Committing changes...
git commit -m "%COMMIT_MSG%"

:: 8. Create Tag
git tag -d "v%APP_VER%" >nul 2>nul
echo [*] Creating version tag: v%APP_VER%
git tag -a "v%APP_VER%" -m "Release v%APP_VER%"

:: 9. Push to GitHub
echo.
echo [*] Pushing main branch to GitHub...
git push -u origin main
if errorlevel 1 (
    echo [*] Synchronizing with remote force push...
    git push -u origin main --force
)

echo.
echo [*] Pushing version tag to trigger GitHub Actions release...
git push origin "v%APP_VER%" --force

echo.
echo ================================================================
echo   Execution finished!
echo   Repository : https://github.com/ahbiyout-all/PowerController
echo   Releases   : https://github.com/ahbiyout-all/PowerController/releases
echo ================================================================
echo.
pause

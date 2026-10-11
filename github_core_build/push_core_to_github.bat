@echo off
setlocal enabledelayedexpansion
title GitHub Core Build Auto Push - PowerController
color 0b

:: Change to root directory
cd /d "%~dp0\.."

echo ================================================================
echo   PowerController - GitHub Core Build Auto Push Pipeline
echo   Developer : AhBiYout (GitHub: AhBiYout-all)
echo   Target    : https://github.com/AhBiYout-all/PowerController.git
echo   Official  : https://ahbiyoutvibe.blogspot.com/
echo   Company   : https://www.cisnet.co.kr
echo ================================================================
echo.

:: 1. Step 1: Pre-flight Audit & Verification of Core Build Files
echo [*] Step 1: Verifying core build files via github_core_build\verify_core_files.py...
python github_core_build\verify_core_files.py
if errorlevel 1 (
    echo.
    echo [ERROR] Verification failed! Unwanted files or missing core files detected.
    echo Please resolve issues before pushing to GitHub.
    echo.
    pause
    exit /b 1
)
echo [OK] Core build files verification passed successfully!
echo.

:: 2. Step 2: Invoke Root Push Script (Adhering to Single Source of Truth & .gitignore)
echo [*] Step 2: Executing automated Git staging, tagging, and push pipeline...
call push_to_github.bat

exit /b %errorlevel%

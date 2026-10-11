@echo off
setlocal enabledelayedexpansion
title Clean GitHub Release Non-Installer Assets - PowerController
color 0c

echo ================================================================
echo   GitHub Release Asset Cleaner (Keep Setup Installer ONLY)
echo   Repository: https://github.com/ahbiyout-all/PowerController
echo ================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python scripts\clean_github_release_assets.py %*
    goto :END
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py scripts\clean_github_release_assets.py %*
    goto :END
)

echo [!] Python is required to run the cleanup script.
pause

:END
echo.
pause

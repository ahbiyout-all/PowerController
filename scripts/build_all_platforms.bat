@echo off
setlocal enabledelayedexpansion
title PowerController Official Windows Installer Builder
color 0b

:: -----------------------------------------------------------------------------
:: Windows Official Setup Installer Builder for PowerController
:: Target: PowerController_Setup_v%APP_VER%.exe (Inno Setup 6)
:: -----------------------------------------------------------------------------

set "APP_VER=2.9.1"
if exist "package.json" (
    for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Content package.json -Raw | ConvertFrom-Json).version" 2^>nul`) do (
        set "APP_VER=%%i"
    )
)

echo ================================================================
echo   [PowerController Windows Official Installer Builder]
echo   - Target Version : v%APP_VER%
echo   - Output Package : release_assets\PowerController_Setup_v%APP_VER%.exe
echo   - Developer      : AhBiYout (GitHub: AhBiYout-all)
echo ================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Running Python packaging engine...
    python scripts\build_packages.py
    goto :BUILD_DONE
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Running py launcher packaging engine...
    py scripts\build_packages.py
    goto :BUILD_DONE
)

echo [*] Python not detected. Running npm run build...
call npm run build

:BUILD_DONE
echo.
echo ================================================================
echo   [SUCCESS] Official Windows installer packaging complete!
echo   - Target : release_assets\PowerController_Setup_v%APP_VER%.exe
echo ================================================================
echo.
pause

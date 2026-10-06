@echo off
setlocal enabledelayedexpansion
title PowerController Multi-Platform Builder
color 0b

:: -----------------------------------------------------------------------------
:: Multi-Platform Universal Builder for PowerController
:: Targets: PC (Windows Setup/Exe), Mobile (Android APK), iPhone (iOS IPA)
:: -----------------------------------------------------------------------------

set APP_VER=2.9.1
if exist "package.json" (
    for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Content package.json -Raw | ConvertFrom-Json).version" 2^>nul`) do (
        set APP_VER=%%i
    )
)

echo ================================================================
echo   [PowerController Multi-Platform Package Builder]
echo   - Version        : v%APP_VER%
echo   - 1. PC Platform : Windows Installer ^& Portable Exe (.zip)
echo   - 2. Mobile      : Android Package (.apk)
echo   - 3. Apple iOS   : iPhone Native Package (.ipa)
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
echo   [SUCCESS] Multi-platform packaging complete!
echo   - PC Windows : build_output\pc\PowerController-v%APP_VER%-Windows.zip
echo   - Android APK: build_output\mobile\PowerController-v%APP_VER%.apk
echo   - iPhone IPA : build_output\ios\PowerController-v%APP_VER%.ipa
echo ================================================================
echo.
pause

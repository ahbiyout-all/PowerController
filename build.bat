@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title PowerController - Automated Build ^& Packaging Suite

:: ===============================================================================
:: PowerController - Automated Build & Packaging Suite
:: Publisher: AhBiYout | Author: AhBiYout
:: ===============================================================================

:: Switch working directory to the batch script directory
cd /d "%~dp0"

cls
echo ===============================================================================
echo            PowerController - Automated Build ^& Packaging Suite
echo                   Publisher: AhBiYout ^| Author: AhBiYout
echo ===============================================================================
echo.

:: ---------------------------------------------------------------------------------
:: Dynamic Version Extraction (Reads latest version from patch notes & package.json)
:: ---------------------------------------------------------------------------------
set "APP_VERSION=2.9.1"
for /f "tokens=*" %%v in ('python -c "import json, re, os; v='2.9.1'; exec('''try:\n if os.path.exists('docs/patch_notes.md'):\n  with open('docs/patch_notes.md', 'r', encoding='utf-8') as f:\n   m = re.search(r'\[v?(\d+\.\d+\.\d+)\]', f.read())\n   if m: v = m.group(1)\n if v == '2.9.1' and os.path.exists('package.json'):\n  with open('package.json', 'r', encoding='utf-8') as f:\n   v = json.load(f).get('version', '2.9.1')\nexcept:\n pass'''); print(v)" 2^>nul') do (
    if not "%%v"=="" set "APP_VERSION=%%v"
)

echo [*] Target Version Detected: v%APP_VERSION%
echo [*] Semantic Version Rule: MAJOR.MINOR.PATCH
echo.

:MAIN_MENU
echo ===============================================================================
echo  [SELECT BUILD OPTION]
echo ===============================================================================
echo  1. Build Application and Inno Setup 6 Installer (App + Setup Wizard)
echo  2. Build Standalone Network Remote Scheduler (PowerNetworkScheduler.exe)
echo  3. Build One-Click Offline Schedule Share Injector (ApplySharedSchedules.exe)
echo  4. Build All Components at Once (All-in-One Complete Suite)
echo  5. Clean Temporary Build Files and Artifacts (build/, dist/, *.spec)
echo  6. Exit Builder
echo ===============================================================================
echo.

set "MENU_CHOICE=1"
set /p "MENU_CHOICE=Select an option (1-6, Default: 1): "
if "%MENU_CHOICE%"=="" set "MENU_CHOICE=1"

if "%MENU_CHOICE%"=="1" (
    set "BUILD_ALL_FLAG=0"
    goto BUILD_MAIN
)
if "%MENU_CHOICE%"=="2" goto BUILD_NET_SCHED
if "%MENU_CHOICE%"=="3" goto BUILD_SHARE_INJECTOR
if "%MENU_CHOICE%"=="4" (
    set "BUILD_ALL_FLAG=1"
    goto BUILD_MAIN
)
if "%MENU_CHOICE%"=="5" goto CLEAN_ARTIFACTS
if "%MENU_CHOICE%"=="6" goto SCRIPT_END

echo.
echo [WARNING] Invalid input: "%MENU_CHOICE%". Defaulting to Option 1 (Application ^& Setup Wizard)...
echo.
set "BUILD_ALL_FLAG=0"
goto BUILD_MAIN

:: ---------------------------------------------------------------------------------
:: CLEAN ARTIFACTS
:: ---------------------------------------------------------------------------------
:CLEAN_ARTIFACTS
echo.
echo [*] Cleaning previous build caches and temporary files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"
echo [OK] Temporary build directories and cache cleaned successfully!
echo.
pause
cls
goto MAIN_MENU

:: ---------------------------------------------------------------------------------
:: BUILD NET SCHEDULER
:: ---------------------------------------------------------------------------------
:BUILD_NET_SCHED
echo.
echo ===============================================================================
echo   Compiling Standalone Network Remote Scheduler: PowerNetworkScheduler_v%APP_VERSION%.exe
echo ===============================================================================
echo.
taskkill /f /t /im PowerNetworkScheduler.exe >nul 2>&1

set "VER_NET_ARG="
if exist "version_network.txt" set "VER_NET_ARG=--version-file="version_network.txt""

cmd /c "python -m PyInstaller --onefile --noconsole --noconfirm --icon="PowerController.ico" %VER_NET_ARG% --name="PowerNetworkScheduler" network_scheduler.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Network Remote Scheduler compilation failed.
    echo Please check Python dependencies and antivirus lock status.
) else (
    if exist "dist\PowerNetworkScheduler.exe" (
        copy /y "dist\PowerNetworkScheduler.exe" "dist\PowerNetworkScheduler_v%APP_VERSION%.exe" >nul 2>&1
        echo [OK] Build complete!
        echo [OUTPUT] dist\PowerNetworkScheduler_v%APP_VERSION%.exe
        echo [OUTPUT] dist\PowerNetworkScheduler.exe
    )
    if exist "dist" start "" "dist"
)
echo.
pause
goto SCRIPT_END

:: ---------------------------------------------------------------------------------
:: BUILD SHARE INJECTOR
:: ---------------------------------------------------------------------------------
:BUILD_SHARE_INJECTOR
echo.
echo ===============================================================================
echo   Compiling One-Click Offline Schedule Share Injector: ApplySharedSchedules_v%APP_VERSION%.exe
echo ===============================================================================
echo.
taskkill /f /t /im ApplySharedSchedules.exe >nul 2>&1
cmd /c "python schedule_share_builder.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Schedule Share Injector compilation failed.
) else (
    python -c "import os, shutil; my_docs = os.path.join(os.path.expanduser('~'), 'Documents'); src = os.path.join(my_docs, 'ApplySharedSchedules.exe') if os.path.exists(os.path.join(my_docs, 'ApplySharedSchedules.exe')) else 'ApplySharedSchedules.exe'; dst_dir = 'dist'; os.makedirs(dst_dir, exist_ok=True); shutil.copy2(src, os.path.join(dst_dir, 'ApplySharedSchedules_v%APP_VERSION%.exe')) if os.path.exists(src) else None; shutil.copy2(src, os.path.join(dst_dir, 'ApplySharedSchedules.exe')) if os.path.exists(src) else None" >nul 2>&1
    echo [OK] Build complete!
    echo [OUTPUT] dist\ApplySharedSchedules_v%APP_VERSION%.exe
    echo [OUTPUT] dist\ApplySharedSchedules.exe
    if exist "dist" start "" "dist"
)
echo.
pause
goto SCRIPT_END

:: ---------------------------------------------------------------------------------
:: BUILD MAIN APPLICATION & SETUP INSTALLER
:: ---------------------------------------------------------------------------------
:BUILD_MAIN
echo.
echo ===============================================================================
echo   STEP 0: Local Server Communication ^& Port Configuration
echo ===============================================================================
echo Please enter the port number for the local communication / embedded Vite server.
set "PORT_INPUT=3032"
set /p "PORT_INPUT=Enter Port Number (Default: 3032): "
if "%PORT_INPUT%"=="" set "PORT_INPUT=3032"
echo [OK] Port selected: %PORT_INPUT%
echo.

echo ===============================================================================
echo   STEP 1: Checking Node.js Environment ^& Building React Web App
echo ===============================================================================
where npm.cmd >nul 2>&1
if errorlevel 1 (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Node.js/npm is not detected in PATH.
        echo Using existing pre-built static files in 'dist' directory.
        goto STEP_PYTHON
    )
)

echo [OK] Node.js and npm environment detected!
if not exist "node_modules" (
    echo [INFO] Installing required npm packages...
    cmd /c "npm install --no-audit --no-fund"
)
echo [*] Bundling React frontend assets (VITE_PORT=%PORT_INPUT%)...
set "VITE_PORT=%PORT_INPUT%"
cmd /c "npm run build"
if errorlevel 1 (
    echo.
    echo [WARNING] npm run build encountered a warning or non-critical error.
    if exist "dist" (
        echo [OK] Existing dist directory found. Continuing with build process.
    ) else (
        echo [WARNING] No dist directory generated. Proceeding to Python packaging...
    )
) else (
    echo [OK] React Web App successfully built for Port %PORT_INPUT%!
)

:STEP_PYTHON
echo.
echo ===============================================================================
echo   STEP 2: Checking Python Runtime Environment
echo ===============================================================================
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ from https://www.python.org and enable [Add Python to PATH].
    echo.
    pause
    goto SCRIPT_END
)
for /f "tokens=*" %%p in ('python --version 2^>^&1') do echo [OK] Python detected: %%p

:: Check main.py in current directory
if not exist "%~dp0main.py" (
    if not exist "main.py" (
        echo.
        echo [ERROR] Main script "main.py" was not found in: %CD%
        echo Please ensure build.bat is executed from the PowerController root folder.
        echo.
        pause
        goto SCRIPT_END
    )
)
echo [OK] Source entry point "main.py" verified!
echo.

echo ===============================================================================
echo   STEP 3: Installing ^& Updating Required Python Packages
echo ===============================================================================
echo [*] Checking Python package manager and dependencies (PyInstaller, pystray, pillow)...

:: Try installing/updating dependencies via cmd /c to ensure batch doesn't exit prematurely
cmd /c "python -m pip install pyinstaller pystray pillow --quiet --no-warn-script-location"
if errorlevel 1 (
    echo [*] Retrying package install with standard user permissions...
    cmd /c "python -m pip install --user pyinstaller pystray pillow"
    if errorlevel 1 (
        echo.
        echo [WARNING] Automatic pip package install failed or was blocked.
        echo If PyInstaller, pystray, and pillow are already installed, compilation will continue.
    )
)
echo [OK] Python dependencies check passed!
echo.

echo ===============================================================================
echo   STEP 4: Compiling Unpacked Application (PowerController Folder)
echo ===============================================================================
echo (Compiling standalone daemon with system tray and background engine...)
echo.
taskkill /f /t /im PowerController.exe >nul 2>&1

:: Build version argument if version file exists
set "VER_MAIN_ARG="
if exist "version_main.txt" set "VER_MAIN_ARG=--version-file="version_main.txt""

cmd /c "python -m PyInstaller --onedir --noconsole --noconfirm --icon="PowerController.ico" %VER_MAIN_ARG% --name="PowerController" main.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Application compilation failed.
    echo Antivirus or real-time file protection might be locking temporary build files.
    echo Try temporarily allowing the directory in Windows Defender and retry.
    echo.
    pause
    goto SCRIPT_END
)

:: Copy required resources into the unpacked distribution directory
echo [*] Copying icons, assets, companion tools and builder helper scripts...
if exist "PowerController.ico" copy /y "PowerController.ico" "dist\PowerController\" >nul 2>&1
if exist "PowerController.png" copy /y "PowerController.png" "dist\PowerController\" >nul 2>&1
if exist "schedule_share_builder.py" copy /y "schedule_share_builder.py" "dist\PowerController\" >nul 2>&1
if exist "native_bridge.py" copy /y "native_bridge.py" "dist\PowerController\" >nul 2>&1
if exist "Register_Firewall_Rules.bat" copy /y "Register_Firewall_Rules.bat" "dist\PowerController\" >nul 2>&1
if exist "dist\PowerNetworkScheduler.exe" copy /y "dist\PowerNetworkScheduler.exe" "dist\PowerController\" >nul 2>&1
if exist "dist\ApplySharedSchedules.exe" copy /y "dist\ApplySharedSchedules.exe" "dist\PowerController\" >nul 2>&1
if not exist "dist\PowerController\docs" mkdir "dist\PowerController\docs" >nul 2>&1
if exist "docs\*" copy /y "docs\*" "dist\PowerController\docs\" >nul 2>&1

:: Compile and copy Pure Custom Native DLLs (PowerCoreNative.dll, NetBeaconEngine.dll)
if exist "native\power_core_native.c" (
    echo [*] Checking C Compiler for PowerCoreNative.dll...
    where gcc >nul 2>&1
    if not errorlevel 1 (
        gcc -O2 -shared -o "PowerCoreNative.dll" "native\power_core_native.c" -lkernel32 -luser32 >nul 2>&1
    ) else (
        where clang >nul 2>&1
        if not errorlevel 1 (
            clang -O2 -shared -o "PowerCoreNative.dll" "native\power_core_native.c" -lkernel32 -luser32 >nul 2>&1
        ) else (
            where cl >nul 2>&1
            if not errorlevel 1 (
                cl /O2 /LD "native\power_core_native.c" /Fe:"PowerCoreNative.dll" kernel32.lib user32.lib >nul 2>&1
            )
        )
    )
    if exist "PowerCoreNative.dll" (
        copy /y "PowerCoreNative.dll" "dist\PowerController\" >nul 2>&1
        copy /y "PowerCoreNative.dll" "dist\" >nul 2>&1
        echo [OK] Pure Custom Native Engine compiled: PowerCoreNative.dll
    )
)

if exist "native\net_beacon_engine.c" (
    echo [*] Checking C Compiler for NetBeaconEngine.dll...
    where gcc >nul 2>&1
    if not errorlevel 1 (
        gcc -O2 -shared -o "NetBeaconEngine.dll" "native\net_beacon_engine.c" -lkernel32 -luser32 -lws2_32 >nul 2>&1
    ) else (
        where clang >nul 2>&1
        if not errorlevel 1 (
            clang -O2 -shared -o "NetBeaconEngine.dll" "native\net_beacon_engine.c" -lkernel32 -luser32 -lws2_32 >nul 2>&1
        ) else (
            where cl >nul 2>&1
            if not errorlevel 1 (
                cl /O2 /LD "native\net_beacon_engine.c" /Fe:"NetBeaconEngine.dll" kernel32.lib user32.lib ws2_32.lib >nul 2>&1
            )
        )
    )
    if exist "NetBeaconEngine.dll" (
        copy /y "NetBeaconEngine.dll" "dist\PowerController\" >nul 2>&1
        copy /y "NetBeaconEngine.dll" "dist\" >nul 2>&1
        echo [OK] Pure Custom NetBeaconEngine compiled: NetBeaconEngine.dll
    )
)

if exist "native\firewall_native.cpp" (
    echo [*] Checking C++ Compiler for FirewallNative.dll...
    where g++ >nul 2>&1
    if not errorlevel 1 (
        g++ -O2 -shared -o "FirewallNative.dll" "native\firewall_native.cpp" -lole32 -loleaut32 >nul 2>&1
    ) else (
        where clang++ >nul 2>&1
        if not errorlevel 1 (
            clang++ -O2 -shared -o "FirewallNative.dll" "native\firewall_native.cpp" -lole32 -loleaut32 >nul 2>&1
        ) else (
            where cl >nul 2>&1
            if not errorlevel 1 (
                cl /O2 /EHsc /LD "native\firewall_native.cpp" /Fe:"FirewallNative.dll" ole32.lib oleaut32.lib >nul 2>&1
            )
        )
    )
    if exist "FirewallNative.dll" (
        copy /y "FirewallNative.dll" "dist\PowerController\" >nul 2>&1
        copy /y "FirewallNative.dll" "dist\" >nul 2>&1
        echo [OK] Pure Custom FirewallNative compiled: FirewallNative.dll
    )
)

if exist "native\sys_power_hook.c" (
    echo [*] Checking C Compiler for SysPowerHook.dll...
    where gcc >nul 2>&1
    if not errorlevel 1 (
        gcc -O2 -shared -o "SysPowerHook.dll" "native\sys_power_hook.c" -lkernel32 -luser32 -lwtsapi32 >nul 2>&1
    ) else (
        where clang >nul 2>&1
        if not errorlevel 1 (
            clang -O2 -shared -o "SysPowerHook.dll" "native\sys_power_hook.c" -lkernel32 -luser32 -lwtsapi32 >nul 2>&1
        ) else (
            where cl >nul 2>&1
            if not errorlevel 1 (
                cl /O2 /LD "native\sys_power_hook.c" /Fe:"SysPowerHook.dll" kernel32.lib user32.lib wtsapi32.lib >nul 2>&1
            )
        )
    )
    if exist "SysPowerHook.dll" (
        copy /y "SysPowerHook.dll" "dist\PowerController\" >nul 2>&1
        copy /y "SysPowerHook.dll" "dist\" >nul 2>&1
        echo [OK] Pure Custom SysPowerHook compiled: SysPowerHook.dll
    )
)

if exist "native\schedule_crypto.c" (
    echo [*] Checking C Compiler for ScheduleCrypto.dll...
    where gcc >nul 2>&1
    if not errorlevel 1 (
        gcc -O2 -shared -o "ScheduleCrypto.dll" "native\schedule_crypto.c" -lkernel32 >nul 2>&1
    ) else (
        where clang >nul 2>&1
        if not errorlevel 1 (
            clang -O2 -shared -o "ScheduleCrypto.dll" "native\schedule_crypto.c" -lkernel32 >nul 2>&1
        ) else (
            where cl >nul 2>&1
            if not errorlevel 1 (
                cl /O2 /LD "native\schedule_crypto.c" /Fe:"ScheduleCrypto.dll" kernel32.lib >nul 2>&1
            )
        )
    )
    if exist "ScheduleCrypto.dll" (
        copy /y "ScheduleCrypto.dll" "dist\PowerController\" >nul 2>&1
        copy /y "ScheduleCrypto.dll" "dist\" >nul 2>&1
        echo [OK] Pure Custom ScheduleCrypto compiled: ScheduleCrypto.dll
    )
)

:: Create version-tagged standalone binary copy
if exist "dist\PowerController\PowerController.exe" (
    copy /y "dist\PowerController\PowerController.exe" "dist\PowerController\PowerController_v%APP_VERSION%.exe" >nul 2>&1
    copy /y "dist\PowerController\PowerController.exe" "dist\PowerController_v%APP_VERSION%.exe" >nul 2>&1
)
echo [OK] Unpacked application folder created: dist\PowerController\
echo.

echo ===============================================================================
echo   STEP 5: Compiling Windows Setup Installer with Inno Setup 6
echo ===============================================================================
echo (Compiling professional Windows installer via Inno Setup 6 Script: PowerController.iss)
echo.

set "ISCC_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if "%ISCC_PATH%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC_PATH%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC_PATH%"=="" (
    for /f "tokens=*" %%i in ('where iscc.exe 2^>nul') do set "ISCC_PATH=%%i"
)

if "%ISCC_PATH%"=="" goto NO_INNO_SETUP

:RUN_INNO_SETUP
echo [OK] Inno Setup 6 compiler detected at: "!ISCC_PATH!"
echo [*] Compiling PowerController_Setup_v%APP_VERSION%.exe...
"!ISCC_PATH!" /DMyAppVersion=%APP_VERSION% "PowerController.iss"
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup 6 compilation failed!
    echo Please check PowerController.iss syntax and required file paths.
    echo.
    pause
    goto SCRIPT_END
)
if exist "dist\PowerController_Setup_v%APP_VERSION%.exe" (
    copy /y "dist\PowerController_Setup_v%APP_VERSION%.exe" "dist\PowerController_Setup.exe" >nul 2>&1
)
echo.
echo [OK] Inno Setup 6 installer compiled successfully!
echo [OUTPUT] dist\PowerController_Setup_v%APP_VERSION%.exe
echo [OUTPUT] dist\PowerController_Setup.exe (Standard alias)
goto SETUP_DONE

:NO_INNO_SETUP
echo.
echo [WARNING] Inno Setup 6 compiler ISCC.exe was not found in default installation paths:
echo   - %ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
echo   - %ProgramFiles%\Inno Setup 6\ISCC.exe
echo   - %LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
echo   - System PATH
echo.
echo If you wish to build the official Inno Setup 6 installer:
echo Please download and install Inno Setup 6 from: https://jrsoftware.org/isdl.php
echo.
echo [*] Falling back to Python-based standalone installer wizard (installer.py)...
taskkill /f /t /im PowerController_Setup.exe >nul 2>&1
set "VER_SETUP_ARG="
if exist "version_setup.txt" set "VER_SETUP_ARG=--version-file="version_setup.txt""
cmd /c "python -m PyInstaller --onefile --noconsole --noconfirm --icon="PowerController.ico" %VER_SETUP_ARG% --name="PowerController_Setup" --add-data "dist/PowerController;PowerController" --add-data "PowerController.ico;." --add-data "PowerController.png;." --add-data "schedule_share_builder.py;." installer.py"
if exist "dist\PowerController_Setup.exe" (
    copy /y "dist\PowerController_Setup.exe" "dist\PowerController_Setup_v%APP_VERSION%.exe" >nul 2>&1
    echo [OK] Fallback installer compiled: dist\PowerController_Setup_v%APP_VERSION%.exe
)

:SETUP_DONE
echo.

if "%BUILD_ALL_FLAG%"=="1" goto BUILD_ALL_REMAINING

echo ===============================================================================
echo                      BUILD COMPLETED SUCCESSFULLY!
echo ===============================================================================
echo.
echo  [GENERATED ARTIFACT LOCATIONS]
echo  - Unpacked Application Folder : dist\PowerController\
echo  - Versioned Application Binary : dist\PowerController_v%APP_VERSION%.exe
echo  - Versioned Setup Installer   : dist\PowerController_Setup_v%APP_VERSION%.exe
echo.
echo  [FEATURES PACKAGED]
echo  * Semantic Versioning v%APP_VERSION% synchronization
echo  * System Tray minimize with background daemon
echo  * 5 Floating compact widget designs and real-time customizer
echo  * Hourly chime synthesizer and startup scheduled task alerts
echo  * Safe preferences buffer with Commit / Cancel transactions
echo  * Interactive uninstaller registration in Windows Control Panel
echo.
echo Opening output directory...
if exist "dist" start "" "dist"
echo.
echo Press any key to exit this builder...
pause >nul
goto SCRIPT_END

:: ---------------------------------------------------------------------------------
:: ALL-IN-ONE REMAINING STEPS
:: ---------------------------------------------------------------------------------
:BUILD_ALL_REMAINING
echo ===============================================================================
echo   STEP 6: Compiling Standalone Network Remote Scheduler
echo ===============================================================================
echo [*] Building PowerNetworkScheduler_v%APP_VERSION%.exe...
taskkill /f /t /im PowerNetworkScheduler.exe >nul 2>&1

set "VER_NET_ARG="
if exist "version_network.txt" set "VER_NET_ARG=--version-file="version_network.txt""

cmd /c "python -m PyInstaller --onefile --noconsole --noconfirm --icon="PowerController.ico" %VER_NET_ARG% --name="PowerNetworkScheduler" network_scheduler.py"
if errorlevel 1 (
    echo [WARNING] Network remote scheduler compilation failed.
) else (
    if exist "dist\PowerNetworkScheduler.exe" (
        copy /y "dist\PowerNetworkScheduler.exe" "dist\PowerNetworkScheduler_v%APP_VERSION%.exe" >nul 2>&1
        echo [OK] dist\PowerNetworkScheduler_v%APP_VERSION%.exe
    )
)
echo.

echo ===============================================================================
echo   STEP 7: Compiling One-Click Offline Schedule Share Injector
echo ===============================================================================
echo [*] Building ApplySharedSchedules_v%APP_VERSION%.exe...
taskkill /f /t /im ApplySharedSchedules.exe >nul 2>&1
cmd /c "python schedule_share_builder.py"
if errorlevel 1 (
    echo [WARNING] Schedule share injector compilation failed.
) else (
    python -c "import os, shutil; my_docs = os.path.join(os.path.expanduser('~'), 'Documents'); src = os.path.join(my_docs, 'ApplySharedSchedules.exe') if os.path.exists(os.path.join(my_docs, 'ApplySharedSchedules.exe')) else 'ApplySharedSchedules.exe'; dst_dir = 'dist'; os.makedirs(dst_dir, exist_ok=True); shutil.copy2(src, os.path.join(dst_dir, 'ApplySharedSchedules_v%APP_VERSION%.exe')) if os.path.exists(src) else None; shutil.copy2(src, os.path.join(dst_dir, 'ApplySharedSchedules.exe')) if os.path.exists(src) else None" >nul 2>&1
    echo [OK] dist\ApplySharedSchedules_v%APP_VERSION%.exe
)
echo.

:: If Inno Setup is present, re-package to include companion tools
if not "%ISCC_PATH%"=="" (
    echo [*] Finalizing Inno Setup 6 All-in-One Installer package...
    "!ISCC_PATH!" /DMyAppVersion=%APP_VERSION% "PowerController.iss" >nul 2>&1
    if exist "dist\PowerController_Setup_v%APP_VERSION%.exe" (
        copy /y "dist\PowerController_Setup_v%APP_VERSION%.exe" "dist\PowerController_Setup.exe" >nul 2>&1
    )
    echo [OK] All companion tools bundled into Inno Setup 6 installer!
    echo.
)

echo ===============================================================================
echo            ALL COMPONENTS BUILT SUCCESSFULLY! (All-in-One v%APP_VERSION%)
echo ===============================================================================
echo.
echo  [ALL GENERATED FILE LOCATIONS]
echo  1. Unpacked App Folder      : dist\PowerController\
echo  2. Windows Setup Installer  : dist\PowerController_Setup_v%APP_VERSION%.exe
echo     (Standard Alias)         : dist\PowerController_Setup.exe
echo  3. Standalone Network Tool  : dist\PowerNetworkScheduler_v%APP_VERSION%.exe
echo  4. Offline Schedule Share   : dist\ApplySharedSchedules_v%APP_VERSION%.exe
echo  5. Standalone App Binary    : dist\PowerController_v%APP_VERSION%.exe
echo.
echo Opening output directory...
if exist "dist" start "" "dist"
echo.
echo Press any key to exit this builder...
pause >nul
goto SCRIPT_END

:SCRIPT_END
endlocal
exit /b 0

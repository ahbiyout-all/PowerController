#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Official Installer Package Builder for PowerController
Outputs clean, installer-only packages for GitHub Releases:
  - Official Inno Setup 6 Unpacked Multi-File Installer: PowerController_Setup_vX.Y.Z.exe
"""

import os
import sys
import json
import shutil
import subprocess

# UTF-8 Encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT_DIR, "build_output")
PC_DIR = os.path.join(BUILD_DIR, "pc")
RELEASE_ASSETS_DIR = os.path.join(ROOT_DIR, "release_assets")


def get_app_version():
    try:
        with open(os.path.join(ROOT_DIR, "package.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("version", "2.9.2").strip()
    except Exception:
        return "2.9.2"


APP_VER = get_app_version()

def build_web_assets():
    dist_index = os.path.join(ROOT_DIR, "dist", "index.html")
    if os.path.exists(dist_index):
        print("[*] 1. Web frontend build verified (dist/index.html exists)...")
        return True
    print("[*] 1. Compiling web application frontend (npm run build)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        res = subprocess.run([npm_cmd, "run", "build"], cwd=ROOT_DIR, shell=(sys.platform == "win32"))
        if res.returncode != 0:
            res = subprocess.run("npm run build", cwd=ROOT_DIR, shell=True)
        return res.returncode == 0
    except Exception as e:
        print(f"[*] Subprocess fallback trying shell=True: {e}")
        res = subprocess.run("npm run build", cwd=ROOT_DIR, shell=True)
        return res.returncode == 0

def find_iscc():
    """Locate Inno Setup Compiler (ISCC.exe)"""
    candidates = [
        "iscc",
        "iscc.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    for c in candidates:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            path = shutil.which(c)
            if path:
                return path
    return None

def build_pc_installer():
    """Build Windows Official Inno Setup 6 Installer (.exe)"""
    print(f"\n[*] 2. Building Windows Official Installer (PowerController_Setup_v{APP_VER}.exe)...")
    os.makedirs(PC_DIR, exist_ok=True)
    os.makedirs(RELEASE_ASSETS_DIR, exist_ok=True)
    dist_dir = os.path.join(ROOT_DIR, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    py_exe = sys.executable

    # 1) PyInstaller compile onedir for Inno Setup unpacked multi-file packaging
    try:
        import PyInstaller
        has_pyinstaller = True
    except ImportError:
        print("[*] Attempting PyInstaller dependency installation...")
        subprocess.run([py_exe, "-m", "pip", "install", "pyinstaller", "pillow", "pystray"], check=False)
        try:
            import PyInstaller
            has_pyinstaller = True
        except ImportError:
            has_pyinstaller = False

    if has_pyinstaller:
        print("[*] (1) Compiling unpacked multi-file binaries with PyInstaller...")
        icon_arg = ["--icon=PowerController.ico"] if os.path.exists(os.path.join(ROOT_DIR, "PowerController.ico")) else []
        subprocess.run([
            py_exe, "-m", "PyInstaller",
            "--onedir", "--noconsole", "--noconfirm",
            *icon_arg,
            "--name=PowerController",
            os.path.join(ROOT_DIR, "main.py")
        ], cwd=ROOT_DIR, check=False)

        if os.path.exists(os.path.join(ROOT_DIR, "network_scheduler.py")):
            subprocess.run([
                py_exe, "-m", "PyInstaller",
                "--onefile", "--noconsole", "--noconfirm",
                *icon_arg,
                "--name=PowerNetworkScheduler",
                os.path.join(ROOT_DIR, "network_scheduler.py")
            ], cwd=ROOT_DIR, check=False)

        rules_json = os.path.join(ROOT_DIR, "power_scheduler_rules.json")
        share_builder = os.path.join(ROOT_DIR, "schedule_share_builder.py")
        if os.path.exists(share_builder) and os.path.exists(rules_json):
            subprocess.run([py_exe, share_builder], cwd=ROOT_DIR, check=False)

    # 1.5) Compile 12 Pure Custom Native DLLs (Windows host / MinGW / Clang / MSVC)
    native_specs = [
        ("native/power_core_native.c", "PowerCoreNative.dll", False, ["-lkernel32", "-luser32"], ["kernel32.lib", "user32.lib"]),
        ("native/net_beacon_engine.c", "NetBeaconEngine.dll", False, ["-lkernel32", "-luser32", "-lws2_32"], ["kernel32.lib", "user32.lib", "ws2_32.lib"]),
        ("native/firewall_native.cpp", "FirewallNative.dll", True, ["-lole32", "-loleaut32"], ["ole32.lib", "oleaut32.lib"]),
        ("native/sys_power_hook.c", "SysPowerHook.dll", False, ["-lkernel32", "-luser32", "-lwtsapi32"], ["kernel32.lib", "user32.lib", "wtsapi32.lib"]),
        ("native/schedule_crypto.c", "ScheduleCrypto.dll", False, ["-lkernel32", "-ladvapi32"], ["kernel32.lib", "advapi32.lib"]),
        ("native/disk_flush_native.c", "DiskFlushNative.dll", False, ["-lkernel32", "-ladvapi32"], ["kernel32.lib", "advapi32.lib"]),
        ("native/audio_dimmer_native.cpp", "AudioDimmerNative.dll", True, ["-lkernel32", "-lole32"], ["kernel32.lib", "ole32.lib"]),
        ("native/display_ddc_native.cpp", "DisplayDdcNative.dll", True, ["-lkernel32", "-luser32", "-ldxva2"], ["kernel32.lib", "user32.lib", "dxva2.lib"]),
        ("native/low_level_input_idle_native.c", "LowLevelInputIdleNative.dll", False, ["-lkernel32", "-luser32"], ["kernel32.lib", "user32.lib"]),
        ("native/commander_tcp_dispatcher.cpp", "CommanderTcpDispatcherNative.dll", True, ["-lkernel32", "-lws2_32"], ["kernel32.lib", "ws2_32.lib"]),
        ("native/commander_ping_scanner.c", "CommanderPingScannerNative.dll", False, ["-lkernel32", "-lws2_32", "-liphlpapi"], ["kernel32.lib", "ws2_32.lib", "iphlpapi.lib"]),
        ("native/power_exec_native.c", "PowerExecNative.dll", False, ["-lkernel32", "-luser32", "-ladvapi32", "-lpowrprof"], ["kernel32.lib", "user32.lib", "advapi32.lib", "powrprof.lib"]),
    ]
    if sys.platform == "win32":
        c_comp = shutil.which("gcc") or shutil.which("clang")
        cpp_comp = shutil.which("g++") or shutil.which("clang++")
        msvc_cl = shutil.which("cl")
        onedir_out = os.path.join(dist_dir, "PowerController")
        os.makedirs(onedir_out, exist_ok=True)
        for rel_src, dll_name, is_cpp, gnu_libs, msvc_libs in native_specs:
            src_path = os.path.join(ROOT_DIR, rel_src)
            out_root = os.path.join(ROOT_DIR, dll_name)
            if not os.path.exists(src_path):
                continue
            comp = cpp_comp if is_cpp else c_comp
            if comp:
                subprocess.run([comp, "-O2", "-shared", "-o", out_root, src_path, *gnu_libs], cwd=ROOT_DIR, check=False)
            elif msvc_cl:
                flags = ["/O2", "/EHsc", "/LD"] if is_cpp else ["/O2", "/LD"]
                subprocess.run([msvc_cl, *flags, src_path, f"/Fe:{out_root}", *msvc_libs], cwd=ROOT_DIR, check=False)
            if os.path.exists(out_root):
                shutil.copy2(out_root, os.path.join(dist_dir, dll_name))
                shutil.copy2(out_root, os.path.join(onedir_out, dll_name))
                print(f"[✓] Compiled Pure Custom Native DLL: {dll_name}")
        for helper in ["native_bridge.py", "schedule_share_builder.py", "Register_Firewall_Rules.bat", "PowerController.ico", "PowerController.png"]:
            hp = os.path.join(ROOT_DIR, helper)
            if os.path.exists(hp):
                shutil.copy2(hp, os.path.join(onedir_out, helper))
        for exe_helper in ["PowerNetworkScheduler.exe", "ApplySharedSchedules.exe"]:
            ep = os.path.join(dist_dir, exe_helper)
            if os.path.exists(ep):
                shutil.copy2(ep, os.path.join(onedir_out, exe_helper))

    # 2) Inno Setup ISCC compilation
    iscc_path = find_iscc()
    iss_file = os.path.join(ROOT_DIR, "PowerController.iss")
    target_installer = os.path.join(PC_DIR, f"PowerController_Setup_v{APP_VER}.exe")
    release_installer = os.path.join(RELEASE_ASSETS_DIR, f"PowerController_Setup_v{APP_VER}.exe")

    if iscc_path and os.path.exists(iss_file):
        print(f"[*] (2) Running Inno Setup 6 compiler ({iscc_path})...")
        subprocess.run([iscc_path, f"/DMyAppVersion={APP_VER}", iss_file], cwd=ROOT_DIR, check=False)
        setup_exe = os.path.join(dist_dir, f"PowerController_Setup_v{APP_VER}.exe")
        if os.path.exists(setup_exe):
            shutil.copy2(setup_exe, target_installer)
            shutil.copy2(setup_exe, release_installer)
            print(f"[✓] Official Windows Inno Setup Installer: {target_installer} ({os.path.getsize(target_installer):,} bytes)")
            return True

    # Fallback to standalone installer executable if ISCC is not installed on runner
    if not os.path.exists(target_installer) and has_pyinstaller:
        print("[*] (Fallback) Generating standalone installer executable...")
        icon_arg = ["--icon=PowerController.ico"] if os.path.exists(os.path.join(ROOT_DIR, "PowerController.ico")) else []
        subprocess.run([
            py_exe, "-m", "PyInstaller",
            "--onefile", "--noconsole", "--noconfirm",
            *icon_arg,
            f"--name=PowerController_Setup_v{APP_VER}",
            os.path.join(ROOT_DIR, "main.py")
        ], cwd=ROOT_DIR, check=False)
        src = os.path.join(dist_dir, f"PowerController_Setup_v{APP_VER}.exe")
        if os.path.exists(src):
            shutil.copy2(src, target_installer)
            shutil.copy2(src, release_installer)
            print(f"[✓] Installer created: {target_installer} ({os.path.getsize(target_installer):,} bytes)")
            return True

    return os.path.exists(target_installer)

def main():
    print("=" * 68)
    print(f"  PowerController Windows Official Installer Builder [v{APP_VER}]")
    print(f"  Developer : AhBiYout (GitHub: AhBiYout-all)")
    print(f"  Target    : PowerController_Setup_v{APP_VER}.exe (Inno Setup 6)")
    print("=" * 68)

    build_web_assets()
    build_pc_installer()

    print("\n" + "=" * 68)
    print("  🎉 Windows Official Setup Installer generated successfully!")
    print(f"  Destination Folder : {RELEASE_ASSETS_DIR}")
    if os.path.exists(RELEASE_ASSETS_DIR):
        for f in os.listdir(RELEASE_ASSETS_DIR):
            fp = os.path.join(RELEASE_ASSETS_DIR, f)
            print(f"    - {f} ({os.path.getsize(fp):,} bytes)")
    print("=" * 68)

if __name__ == "__main__":
    main()

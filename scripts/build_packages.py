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

def get_app_version():
    try:
        with open("package.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("version", "2.9.1").strip()
    except Exception:
        return "2.9.1"

APP_VER = get_app_version()
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT_DIR, "build_output")
PC_DIR = os.path.join(BUILD_DIR, "pc")
RELEASE_ASSETS_DIR = os.path.join(ROOT_DIR, "release_assets")

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

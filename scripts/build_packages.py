#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC Release Installer (.exe) Builder for PowerController
Outputs:
  - Official Inno Setup Installer: build_output/pc/PowerController_Setup_vX.Y.Z.exe
"""

import os
import sys
import json
import shutil
import subprocess

# Windows cp1252 / ANSI 환경 대응 UTF-8 강제
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

def build_web_assets():
    dist_index = os.path.join(ROOT_DIR, "dist", "index.html")
    if os.path.exists(dist_index):
        print("[*] 1. 웹 프론트엔드 빌드 확인 (dist/index.html 존재)...")
        return True
    print("[*] 1. 웹 프론트엔드 및 대시보드 빌드 (npm run build)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        res = subprocess.run([npm_cmd, "run", "build"], cwd=ROOT_DIR, shell=(sys.platform == "win32"))
        if res.returncode != 0:
            res = subprocess.run("npm run build", cwd=ROOT_DIR, shell=True)
        if res.returncode != 0:
            print("[!] npm run build 실패!")
            return False
        return True
    except Exception as e:
        print(f"[*] Subprocess fallback trying shell=True: {e}")
        res = subprocess.run("npm run build", cwd=ROOT_DIR, shell=True)
        return res.returncode == 0

def find_iscc():
    """Inno Setup Compiler (ISCC.exe) 경로 탐색"""
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

def build_installer():
    """Inno Setup 6 기반 공식 Windows 설치 프로그램(.exe) 단독 생성"""
    print(f"\n[*] 2. Inno Setup 6 기반 Windows 설치 프로그램(.exe) 빌드 중...")
    os.makedirs(PC_DIR, exist_ok=True)
    dist_dir = os.path.join(ROOT_DIR, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    py_exe = sys.executable

    # 1) PyInstaller 의존성 준비 및 메인 앱 onedir 빌드 (Inno Setup 패키징용)
    try:
        import PyInstaller
        has_pyinstaller = True
    except ImportError:
        print("[*] PyInstaller 패키지 자동 설치 시도...")
        subprocess.run([py_exe, "-m", "pip", "install", "pyinstaller", "pillow", "pystray"], check=False)
        try:
            import PyInstaller
            has_pyinstaller = True
        except ImportError:
            has_pyinstaller = False

    if has_pyinstaller:
        print("[*] (1) PyInstaller 패키징용 바이너리 컴파일...")
        icon_arg = ["--icon=PowerController.ico"] if os.path.exists(os.path.join(ROOT_DIR, "PowerController.ico")) else []
        subprocess.run([
            py_exe, "-m", "PyInstaller",
            "--onedir", "--noconsole", "--noconfirm",
            *icon_arg,
            "--name=PowerController",
            os.path.join(ROOT_DIR, "main.py")
        ], cwd=ROOT_DIR, check=False)

    # 2) Inno Setup 인스톨러 컴파일
    iscc_path = find_iscc()
    iss_file = os.path.join(ROOT_DIR, "PowerController.iss")
    target_installer = os.path.join(PC_DIR, f"PowerController_Setup_v{APP_VER}.exe")
    
    if iscc_path and os.path.exists(iss_file):
        print(f"[*] (2) Inno Setup 6 컴파일러 실행 중 ({iscc_path})...")
        res = subprocess.run([iscc_path, f"/DMyAppVersion={APP_VER}", iss_file], cwd=ROOT_DIR, check=False)
        setup_exe = os.path.join(dist_dir, f"PowerController_Setup_v{APP_VER}.exe")
        if os.path.exists(setup_exe):
            shutil.copy2(setup_exe, target_installer)
            print(f"[✓] 공식 설치 프로그램(Inno Setup) 생성 완료: {target_installer} ({os.path.getsize(target_installer):,} bytes)")
            return True
    
    # 만약 ISCC가 없을 경우 pyinstaller 단일 실행 파일로 인스톨러 대체 생성
    if not os.path.exists(target_installer) and has_pyinstaller:
        print("[*] (대체) PyInstaller 단일 설치 프로그램 빌드 진행...")
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
            print(f"[✓] 설치 프로그램 생성 완료: {target_installer} ({os.path.getsize(target_installer):,} bytes)")
            return True

    return os.path.exists(target_installer)

def main():
    print("=" * 64)
    print(f"  PowerController Official Windows Installer Builder [v{APP_VER}]")
    print(f"  Target: Windows Installer Executable (PowerController_Setup_v{APP_VER}.exe)")
    print("=" * 64)
    
    if not build_web_assets():
        sys.exit(1)
        
    build_installer()
    
    print("\n" + "=" * 64)
    print("  🎉 Windows 공식 인스톨러(.exe) 생성이 완료되었습니다!")
    installer_path = os.path.join(PC_DIR, f"PowerController_Setup_v{APP_VER}.exe")
    if os.path.exists(installer_path):
        print(f"  💿 단독 설치 파일 : {installer_path} ({os.path.getsize(installer_path):,} bytes)")
    print("=" * 64)

if __name__ == "__main__":
    main()

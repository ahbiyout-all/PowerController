#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Source of Truth (SSOT) Version Synchronizer
Propagates version from package.json to all codebase files:
  - main.py (APP_VERSION)
  - network_scheduler.py (VERSION)
  - installer.py (APP_VERSION)
  - index.html (title, og:title, meta)
  - PowerController.iss (#define MyAppVersion)
"""

import os
import re
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sync_versions():
    # 1. Read base version from package.json
    pkg_path = os.path.join(ROOT_DIR, "package.json")
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg_data = json.load(f)
    version = pkg_data.get("version", "2.9.1").strip()
    print(f"[*] Base Version (package.json): v{version}")

    # 2. Sync main.py
    main_py = os.path.join(ROOT_DIR, "main.py")
    if os.path.exists(main_py):
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'APP_VERSION\s*=\s*["\'][^"\']+["\']', f'APP_VERSION = "{version}"', content)
        with open(main_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced main.py -> v{version}")

    # 3. Sync network_scheduler.py
    net_py = os.path.join(ROOT_DIR, "network_scheduler.py")
    if os.path.exists(net_py):
        with open(net_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'VERSION\s*=\s*["\'][^"\']+["\']', f'VERSION = "{version}"', content)
        with open(net_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced network_scheduler.py -> v{version}")

    # 4. Sync installer.py
    inst_py = os.path.join(ROOT_DIR, "installer.py")
    if os.path.exists(inst_py):
        with open(inst_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'APP_VERSION\s*=\s*["\'][^"\']+["\']', f'APP_VERSION = "{version}"', content)
        with open(inst_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced installer.py -> v{version}")

    # 5. Sync PowerController.iss
    iss_file = os.path.join(ROOT_DIR, "PowerController.iss")
    if os.path.exists(iss_file):
        with open(iss_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'#define MyAppVersion\s+["\'][^"\']+["\']', f'#define MyAppVersion "{version}"', content)
        with open(iss_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced PowerController.iss -> v{version}")

    # 6. Sync index.html
    html_file = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'<title>PowerController[^<]*</title>', f'<title>PowerController v{version}</title>', content)
        content = re.sub(r'content="PowerController[^"]*" property="og:title"', f'content="PowerController v{version}" property="og:title"', content)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced index.html -> v{version}")

    print("\n🎉 All project version references successfully synchronized to v" + version)

if __name__ == "__main__":
    sync_versions()

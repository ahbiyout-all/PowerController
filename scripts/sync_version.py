#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Source of Truth (SSOT) Dynamic Version Synchronizer
Propagates version from package.json to all codebase and configuration files:
  - src/types.ts (APP_VERSION)
  - main.py (APP_VERSION)
  - network_scheduler.py (VERSION)
  - installer.py (APP_VERSION)
  - index.html (title, og:title, meta)
  - PowerController.iss (#define MyAppVersion)
  - docs/PATCHNOTES.md & docs/patch_notes.md (Header)
  - version_*.txt (Windows version info stamps)
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

    # 2. Sync src/types.ts
    types_ts = os.path.join(ROOT_DIR, "src", "types.ts")
    if os.path.exists(types_ts):
        with open(types_ts, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'export const APP_VERSION\s*=\s*["\'][^"\']+["\'];', f"export const APP_VERSION = '{version}';", content)
        with open(types_ts, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced src/types.ts -> v{version}")

    # 3. Sync main.py
    main_py = os.path.join(ROOT_DIR, "main.py")
    if os.path.exists(main_py):
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'APP_VERSION\s*=\s*["\'][^"\']+["\']', f'APP_VERSION = "{version}"', content)
        with open(main_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced main.py -> v{version}")

    # 4. Sync network_scheduler.py
    net_py = os.path.join(ROOT_DIR, "network_scheduler.py")
    if os.path.exists(net_py):
        with open(net_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'VERSION\s*=\s*["\'][^"\']+["\']', f'VERSION = "{version}"', content)
        with open(net_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced network_scheduler.py -> v{version}")

    # 5. Sync installer.py
    inst_py = os.path.join(ROOT_DIR, "installer.py")
    if os.path.exists(inst_py):
        with open(inst_py, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'APP_VERSION\s*=\s*["\'][^"\']+["\']', f'APP_VERSION = "{version}"', content)
        with open(inst_py, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced installer.py -> v{version}")

    # 6. Sync PowerController.iss
    iss_file = os.path.join(ROOT_DIR, "PowerController.iss")
    if os.path.exists(iss_file):
        with open(iss_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'#define MyAppVersion\s+["\'][^"\']+["\']', f'#define MyAppVersion "{version}"', content)
        with open(iss_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced PowerController.iss -> v{version}")

    # 7. Sync index.html
    html_file = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'<title>PowerController[^<]*</title>', f'<title>PowerController v{version}</title>', content)
        content = re.sub(r'content="PowerController[^"]*" property="og:title"', f'content="PowerController v{version}" property="og:title"', content)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] Synced index.html -> v{version}")

    # 8. Sync docs/PATCHNOTES.md & docs/patch_notes.md
    for doc in ["PATCHNOTES.md", "patch_notes.md"]:
        doc_path = os.path.join(ROOT_DIR, "docs", doc)
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_content = f.read()
            doc_content = re.sub(r'## \[v[0-9]+(?:\.[0-9]+)*[^\]]*\]', f'## [v{version}]', doc_content, count=1)
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(doc_content)
            print(f"[✓] Synced docs/{doc} -> v{version}")

    # 9. Sync version_*.txt
    v_parts = version.split('.')
    while len(v_parts) < 4:
        v_parts.append('0')
    v_tuple = f"({', '.join(v_parts)})"
    v_str = version

    for v_file in ["version_main.txt", "version_network.txt", "version_setup.txt", "version_share.txt"]:
        vp = os.path.join(ROOT_DIR, v_file)
        if os.path.exists(vp):
            with open(vp, "r", encoding="utf-8") as f:
                vc = f.read()
            vc = re.sub(r'filevers=\([^)]+\)', f'filevers={v_tuple}', vc)
            vc = re.sub(r'prodvers=\([^)]+\)', f'prodvers={v_tuple}', vc)
            vc = re.sub(r'StringStruct\(\'ProductVersion\',\s*\'[^\']+\'\)', f"StringStruct('ProductVersion', '{v_str}')", vc)
            vc = re.sub(r'StringStruct\(\'FileVersion\',\s*\'[^\']+\'\)', f"StringStruct('FileVersion', '{v_str}')", vc)
            with open(vp, "w", encoding="utf-8") as f:
                f.write(vc)
            print(f"[✓] Synced {v_file} -> v{version}")

    print("\n🎉 All project version references successfully synchronized to v" + version)

if __name__ == "__main__":
    sync_versions()

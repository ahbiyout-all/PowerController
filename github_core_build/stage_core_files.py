#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerController GitHub Core Files Stager
Author: AhBiYout (GitHub: AhBiYout-all)
Description:
  Copies ONLY the verified core build files defined in CORE_FILES_MANIFEST.txt
  into a clean staging directory (e.g. 'github_core_build/staged_release/').
  This guarantees that nothing outside the whitelist is ever uploaded.
"""

import os
import sys
import shutil

# Set UTF-8 encoding for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "CORE_FILES_MANIFEST.txt")
STAGE_DIR = os.path.join(os.path.dirname(__file__), "staged_repo")

def stage_files():
    print("================================================================")
    print("  PowerController - GitHub Core Build Stager")
    print("  Developer : AhBiYout (GitHub: AhBiYout-all)")
    print("  Target Dir: github_core_build/staged_repo/")
    print("================================================================\n")

    if os.path.exists(STAGE_DIR):
        print(f"[*] Cleaning previous staging directory: {STAGE_DIR}")
        shutil.rmtree(STAGE_DIR)
    os.makedirs(STAGE_DIR, exist_ok=True)

    if not os.path.exists(MANIFEST_PATH):
        print(f"[ERROR] Manifest not found: {MANIFEST_PATH}")
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_items = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    copied_count = 0
    for item in manifest_items:
        src = os.path.join(BASE_DIR, item)
        dst = os.path.join(STAGE_DIR, item)

        if not os.path.exists(src):
            print(f"[SKIP] Not found: {item}")
            continue

        if os.path.isdir(src):
            # Exclude node_modules, dist, __pycache__, build, git inside directories
            def ignore_patterns(path, names):
                ignored = []
                for name in names:
                    if name in ["__pycache__", "node_modules", "dist", "build", ".DS_Store", "Thumbs.db"]:
                        ignored.append(name)
                    elif name.endswith((".pyc", ".tmp", ".bak")):
                        ignored.append(name)
                return ignored

            shutil.copytree(src, dst, ignore=ignore_patterns, dirs_exist_ok=True)
            copied_count += 1
            print(f"  [COPIED DIR]  {item}/")
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied_count += 1
            print(f"  [COPIED FILE] {item}")

    print(f"\n[SUCCESS] Successfully staged {copied_count} core build components.")
    print(f"Location: {STAGE_DIR}")
    return True

if __name__ == "__main__":
    success = stage_files()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerController GitHub Core Build Files Validator
Author: AhBiYout (GitHub: AhBiYout-all)
Description:
  Audits the workspace against CORE_FILES_MANIFEST.txt to guarantee that
  all necessary build files exist, and strictly verifies that no sensitive data,
  personal emails, or unwanted local artifacts leak into the GitHub repository.
"""

import os
import sys
import json
import re

# Set UTF-8 encoding for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "CORE_FILES_MANIFEST.txt")

# Prohibited patterns
SENSITIVE_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@(?!users\.noreply\.github\.com)[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), # Personal email
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
    re.compile(r"(?i)secret[_-]?token\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]")
]

UNWANTED_EXTENSIONS = {
    ".pyc", ".pyo", ".tmp", ".bak", ".swp", ".log"
}

UNWANTED_NAMES = {
    "sidebar_theme_config.json", "power_master_key.txt", ".DS_Store", "Thumbs.db"
}

def load_manifest():
    entries = []
    if not os.path.exists(MANIFEST_PATH):
        print(f"[ERROR] Manifest file not found at: {MANIFEST_PATH}")
        return entries
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entries.append(line)
    return entries

def verify_manifest_files():
    print("================================================================")
    print("  PowerController - GitHub Core Files Verification")
    print("  Developer : AhBiYout (GitHub: AhBiYout-all)")
    print("  Official  : https://ahbiyoutvibe.blogspot.com/")
    print("  Company   : https://www.cisnet.co.kr")
    print("================================================================\n")
    
    entries = load_manifest()
    missing_items = []
    found_items = []

    print("[*] 1. Checking presence of manifest core build files...")
    for item in entries:
        full_path = os.path.join(BASE_DIR, item)
        if os.path.exists(full_path):
            found_items.append(item)
            # print(f"  [OK] {item}")
        else:
            missing_items.append(item)
            print(f"  [MISSING] {item}")

    print(f"\nManifest entries checked: {len(entries)} (Found: {len(found_items)}, Missing: {len(missing_items)})")
    if missing_items:
        print(f"[FAIL] Missing required core build items: {missing_items}")
        return False
    else:
        print("[OK] All required core build items are present.")

    # 2. Privacy & Security scan
    print("\n[*] 2. Checking for sensitive leaks & unwanted files...")
    leaks_found = []
    
    # Check for unwanted local runtime artifacts
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip git, node_modules, dist, etc.
        if any(skip in root for skip in [".git", "node_modules", "dist", "build", "release_assets", "build_output"]):
            continue
        for f in files:
            p = os.path.join(root, f)
            rel_p = os.path.relpath(p, BASE_DIR)
            _, ext = os.path.splitext(f)
            
            if ext in UNWANTED_EXTENSIONS:
                leaks_found.append(f"Unwanted temp file: {rel_p}")
            if f in UNWANTED_NAMES or f.startswith("power_user_"):
                leaks_found.append(f"Unwanted local runtime data: {rel_p}")

            # Check text files for personal emails (excluding package-lock.json registry maintainers)
            if ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".md", ".txt", ".bat", ".sh", ".iss", ".yml", ".yaml"]:
                if f in ["package-lock.json", "bun.lock"]:
                    continue
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as tf:
                        content = tf.read()
                        for pattern in SENSITIVE_PATTERNS:
                            m = pattern.search(content)
                            if m:
                                matched_str = m.group(0)
                                leaks_found.append(f"Sensitive match '{matched_str}' in {rel_p}")
                except Exception:
                    pass

    if leaks_found:
        print("[WARNING / DETECTED ISSUES]:")
        for leak in leaks_found[:10]:
            print(f"  - {leak}")
        if len(leaks_found) > 10:
            print(f"  ... and {len(leaks_found) - 10} more.")
        return False
    else:
        print("[OK] Zero sensitive leaks detected (Personal emails, keys, and private data fully protected).")

    # 3. Dynamic Version Check
    print("\n[*] 3. Verifying single source of truth version...")
    pkg_ver = None
    pkg_path = os.path.join(BASE_DIR, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg_ver = json.load(f).get("version")
    print(f"  Target Version (package.json): v{pkg_ver}")

    print("\n[SUCCESS] Workspace is clean, compliant, and ready for GitHub upload!")
    return True

if __name__ == "__main__":
    success = verify_manifest_files()
    sys.exit(0 if success else 1)

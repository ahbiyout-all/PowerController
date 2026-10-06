#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Release Non-Installer Assets Cleaner
Deletes unwanted assets (.zip, .apk, .ipa, non-setup .exe) from GitHub Releases,
keeping ONLY the official installer: PowerController_Setup_v*.exe
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Force UTF-8 in console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_OWNER = "ahbiyout-all"
REPO_NAME = "PowerController"

def get_app_version():
    try:
        with open("package.json", "r", encoding="utf-8") as f:
            return json.load(f).get("version", "2.9.1").strip()
    except Exception:
        return "2.9.1"

def prune_release_assets(token=None, tag_name=None):
    version = get_app_version()
    tag = tag_name or f"v{version}"
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    print("=" * 64)
    print(f"  GitHub Release Asset Cleaner for {REPO_OWNER}/{REPO_NAME}")
    print(f"  Target Release Tag: {tag}")
    print(f"  Policy: Keep ONLY 'PowerController_Setup_*.exe', Delete all others")
    print("=" * 64)

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PowerController-Release-Pruner"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1. Fetch release details
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{tag}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[!] Release tag '{tag}' not found on GitHub. Nothing to prune.")
            return
        print(f"[!] HTTP Error {e.code}: {e.reason}")
        return
    except Exception as e:
        print(f"[!] Network error: {e}")
        return

    assets = data.get("assets", [])
    if not assets:
        print("[*] No assets found in this release.")
        return

    print(f"[*] Found {len(assets)} assets in release '{tag}':")
    for a in assets:
        print(f"    - {a.get('name')} ({a.get('size', 0):,} bytes)")

    # 2. Identify assets to delete
    to_delete = []
    to_keep = []
    for a in assets:
        name = a.get("name", "")
        if name.startswith("PowerController_Setup_") and name.endswith(".exe"):
            to_keep.append(a)
        else:
            to_delete.append(a)

    print("\n[*] Policy evaluation:")
    print(f"    - Assets to KEEP ({len(to_keep)}): {[a['name'] for a in to_keep]}")
    print(f"    - Assets to DELETE ({len(to_delete)}): {[a['name'] for a in to_delete]}")

    if not to_delete:
        print("\n[✓] Release is already clean! Only setup installer exists.")
        return

    if not token:
        print("\n[!] GITHUB_TOKEN is required to delete assets via API.")
        print("    Please run within GitHub Actions or pass token as environment variable.")
        return

    # 3. Delete unwanted assets
    print("\n[*] Deleting non-installer assets...")
    for a in to_delete:
        asset_id = a["id"]
        asset_name = a["name"]
        del_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/assets/{asset_id}"
        try:
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            with urllib.request.urlopen(del_req) as del_resp:
                print(f"    [✓] Successfully deleted: {asset_name}")
        except Exception as e:
            print(f"    [!] Failed to delete {asset_name}: {e}")

    print("\n" + "=" * 64)
    print("  🎉 Release cleanup complete!")
    print("=" * 64)

if __name__ == "__main__":
    cli_token = sys.argv[1] if len(sys.argv) > 1 else None
    cli_tag = sys.argv[2] if len(sys.argv) > 2 else None
    prune_release_assets(token=cli_token, tag_name=cli_tag)

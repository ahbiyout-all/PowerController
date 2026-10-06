#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Auto Sync & Real-time Release Tool for AhBiYout / PowerController
Dynamic Versioning (Single Source of Truth) & No-Reply Security
Author: AhBiYout
"""

import os
import sys
import subprocess
import datetime
import json
import re

# Windows cp1252/ANSI 인코딩 환경 대응
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GITHUB_ACCOUNT = "ahbiyout-all"
GIT_USER_NAME = "AhBiYout-all"
SECURE_NO_REPLY_EMAIL = "ahbiyout-all@users.noreply.github.com"
DEFAULT_REPO_NAME = "PowerController"
DEFAULT_REPO_URL = f"https://github.com/{GITHUB_ACCOUNT}/{DEFAULT_REPO_NAME}.git"

def get_dynamic_version():
    """
    다단 동적 버전 추출 파이프라인 (Single Source of Truth)
    1차: package.json 'version'
    2차: docs/PATCHNOTES.md 최상단 정규식 파싱
    3차: main.py APP_VERSION
    """
    # 1차: package.json
    try:
        if os.path.exists("package.json"):
            with open("package.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if "version" in data and data["version"]:
                    return data["version"].strip()
    except Exception:
        pass

    # 2차: docs/PATCHNOTES.md
    try:
        if os.path.exists("docs/PATCHNOTES.md"):
            with open("docs/PATCHNOTES.md", "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'##\s*\[v?([0-9]+\.[0-9]+\.[0-9]+)\]', content)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass

    # 3차: main.py
    try:
        if os.path.exists("main.py"):
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass

    return "2.9.1"

APP_VERSION = get_dynamic_version()

def run_cmd(cmd, check=True, capture_output=False):
    """실행 헬퍼 함수"""
    try:
        if capture_output:
            res = subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            return res.stdout.strip()
        else:
            return subprocess.run(cmd, check=check).returncode
    except subprocess.CalledProcessError as e:
        if check:
            print(f"[!] 명령어 실행 실패: {' '.join(cmd)}")
            if capture_output and e.stderr:
                print(f"[!] 상세 오류: {e.stderr.strip()}")
        return None

def check_git():
    """Git 설치 점검"""
    try:
        ver = run_cmd(["git", "--version"], check=True, capture_output=True)
        print(f"[✓] Git 발견: {ver}")
        return True
    except Exception:
        print("[X] 시스템에 Git이 설치되어 있지 않습니다.")
        print("    https://git-scm.com/ 에서 Git을 설치해주세요.")
        return False

def setup_git_repo(user_email=SECURE_NO_REPLY_EMAIL):
    """Git 초기화 및 사용자 정보 등록 (보안 비공개 이메일 전용)"""
    # 1. git init
    if not os.path.exists(".git"):
        print("[*] .git 디렉터리가 없어 'git init'을 실행합니다...")
        run_cmd(["git", "init"])
    else:
        print("[✓] 기존 Git 저장소 감지 (.git)")

    # 2. 사용자 이름 및 보안 이메일 설정
    print(f"[*] Git 작성자 설정: name='{GIT_USER_NAME}', email='{user_email}' (보안 비공개)")
    run_cmd(["git", "config", "user.name", GIT_USER_NAME])
    run_cmd(["git", "config", "user.email", user_email])

    # 3. 브랜치를 main으로 설정
    run_cmd(["git", "branch", "-M", "main"])

    # 4. 원격 저장소 origin 확인
    existing_origin = run_cmd(["git", "remote", "get-url", "origin"], check=False, capture_output=True)
    if not existing_origin:
        print(f"[*] 원격 저장소(origin) 등록: {DEFAULT_REPO_URL}")
        run_cmd(["git", "remote", "add", "origin", DEFAULT_REPO_URL])
    else:
        run_cmd(["git", "remote", "set-url", "origin", DEFAULT_REPO_URL], check=False)
        print(f"[✓] 원격 저장소: {DEFAULT_REPO_URL}")

def auto_push(commit_msg=None):
    """파일 스테이징, 커밋, 버전 태깅 및 깃허브 푸시"""
    tag_name = f"v{APP_VERSION}"
    if not commit_msg:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_prompt = f"Release {tag_name} - {now_str}"
        prompt_msg = input(f"\n커밋 메시지를 입력하세요 (엔터 시 '{default_prompt}' 적용): ").strip()
        commit_msg = prompt_msg if prompt_msg else default_prompt

    print(f"\n[*] 1. 변경된 파일 전체 추가 (git add -A)...")
    run_cmd(["git", "add", "-A"])

    print(f"[*] 2. 커밋 생성: '{commit_msg}'...")
    run_cmd(["git", "commit", "-m", commit_msg], check=False)

    # 3. 릴리스 태그 생성 (기존 태그 있을 경우 최신 커밋으로 재생성)
    existing_tags = run_cmd(["git", "tag", "-l", tag_name], check=False, capture_output=True)
    if existing_tags and tag_name in existing_tags.split():
        run_cmd(["git", "tag", "-d", tag_name], check=False)
    print(f"[*] 3. GitHub Releases 연동을 위한 버전 태그 생성: {tag_name}...")
    run_cmd(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], check=False)

    print(f"[*] 4. GitHub main 브랜치로 전송 (git push -u origin main)...")
    push_code = run_cmd(["git", "push", "-u", "origin", "main"], check=False)
    if push_code != 0:
        print("[*] 원격 브랜치 히스토리 동기화 중 (git push -u origin main --force)...")
        push_code = run_cmd(["git", "push", "-u", "origin", "main", "--force"], check=False)

    print(f"[*] 5. GitHub Releases 생성을 위해 버전 태그({tag_name})를 푸시합니다 (force update)...")
    run_cmd(["git", "push", "origin", tag_name, "--force"], check=False)

    if push_code == 0:
        print("\n" + "=" * 64)
        print("  🎉 [성공] GitHub에 코드가 성공적으로 업로드 및 릴리스되었습니다!")
        print(f"  - 동적 버전   : {tag_name}")
        print(f"  - 저장소 링크 : https://github.com/{GITHUB_ACCOUNT}/{DEFAULT_REPO_NAME}")
        print(f"  - 릴리스 링크 : https://github.com/{GITHUB_ACCOUNT}/{DEFAULT_REPO_NAME}/releases")
        print("=" * 64 + "\n")
    else:
        print("\n" + "=" * 64)
        print("  ⚠️ [안내] git push가 완료되지 않았습니다.")
        print("  원인 점검:")
        print(f"  1. GitHub 웹(https://github.com/new)에 '{DEFAULT_REPO_NAME}' 레포가 생성되었는지 확인하세요.")
        print("  2. GitHub 비밀번호 인증 대신 Personal Access Token(PAT)을 입력해야 합니다.")
        print("=" * 64 + "\n")

def main():
    print("=" * 64)
    print(f"  GitHub 자동 배포 및 실시간 릴리스 도구 (PowerController)")
    print(f"  - GitHub 계정     : {GITHUB_ACCOUNT}")
    print(f"  - 사용자 이름     : {GIT_USER_NAME}")
    print(f"  - 현재 앱 버전    : v{APP_VERSION} (Single Source of Truth)")
    print(f"  - 기본 원격 저장소: {DEFAULT_REPO_URL}")
    print("=" * 64)

    if not check_git():
        input("\n엔터 키를 누르면 종료합니다...")
        return

    setup_git_repo(SECURE_NO_REPLY_EMAIL)
    auto_push()

    if sys.stdin.isatty():
        input("작업이 끝났습니다. 엔터 키를 누르면 창을 닫습니다...")

if __name__ == "__main__":
    main()

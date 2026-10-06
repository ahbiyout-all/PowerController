#!/usr/bin/env bash
# ==============================================================================
# GitHub Auto Push & Real-time Release Script for AhBiYout / PowerController
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 다단 동적 버전 추출
APP_VER="2.9.1"
if [ -f "package.json" ]; then
    APP_VER=$(grep -m 1 '"version":' package.json | sed -E 's/.*"version": *"([^"]+)".*/\1/' || echo "2.9.1")
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  [GitHub Auto Push & Real-time Release Tool]${NC}"
echo -e "${YELLOW}  - GitHub Account : ahbiyout-all${NC}"
echo -e "${YELLOW}  - Git User Name  : AhBiYout-all${NC}"
echo -e "${GREEN}  - App Version    : v${APP_VER} (Single Source of Truth)${NC}"
echo -e "${YELLOW}  - Repository     : https://github.com/ahbiyout-all/PowerController.git${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

# 2. Git 설치 확인
if ! command -v git &> /dev/null; then
    echo -e "${RED}[오류] git 명령어를 찾을 수 없습니다. Git을 설치해주세요.${NC}"
    exit 1
fi

# 3. .git 초기화 확인
if [ ! -d ".git" ]; then
    echo -e "${GREEN}[*] Git 저장소를 초기화합니다 (git init)...${NC}"
    git init
fi

# 4. 작성자 정보 자동 설정 (GitHub 공식 보안 비공개 이메일 전용)
SELECTED_EMAIL="ahbiyout-all@users.noreply.github.com"
git config user.name "AhBiYout-all"
git config user.email "$SELECTED_EMAIL"
echo -e "${GREEN}[V] 작성자 이름 : AhBiYout-all${NC}"
echo -e "${GREEN}[V] 보안 이메일 : $SELECTED_EMAIL (개인정보 완벽 보호)${NC}"
echo ""

# 5. 원격 저장소(origin) 등록 및 확인
REPO_URL="https://github.com/ahbiyout-all/PowerController.git"
if ! git remote get-url origin &> /dev/null; then
    echo -e "${GREEN}[*] 원격 저장소(origin) 추가: ${REPO_URL}${NC}"
    git remote add origin "$REPO_URL"
else
    git remote set-url origin "$REPO_URL"
    echo -e "${CYAN}[*] 원격 저장소: ${REPO_URL}${NC}"
fi

# 6. 브랜치 main 통일
git branch -M main

# 7. 커밋 메시지 입력 (버전 정보 동적 포함)
DEFAULT_MSG="Release v${APP_VER} - $(date '+%Y-%m-%d %H:%M:%S')"
read -r -p "커밋 메시지를 입력하세요 (엔터 시 '$DEFAULT_MSG' 사용): " USER_MSG
COMMIT_MSG="${USER_MSG:-$DEFAULT_MSG}"

echo ""
echo -e "${GREEN}[*] 변경 사항 추가 중 (git add -A)...${NC}"
git add -A

echo -e "${GREEN}[*] 커밋 생성 중 (git commit)...${NC}"
git commit -m "$COMMIT_MSG" || true

# 8. GitHub Releases 연동을 위한 동적 버전 태깅
TAG_NAME="v${APP_VER}"
PUSH_TAG=0
if ! git tag -l "$TAG_NAME" | grep -q "^$TAG_NAME$"; then
    echo -e "${GREEN}[*] 신규 릴리스 버전 태그 생성 (${TAG_NAME})...${NC}"
    git tag -a "$TAG_NAME" -m "Release $TAG_NAME"
    PUSH_TAG=1
else
    echo -e "${CYAN}[*] 버전 태그 ${TAG_NAME} 은(는) 이미 등록되어 있습니다.${NC}"
fi

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  GitHub 원격 저장소로 업로드(git push)를 시작합니다...${NC}"
echo -e "${CYAN}================================================================${NC}"

git push -u origin main

if [ $PUSH_TAG -eq 1 ]; then
    echo -e "${GREEN}[*] GitHub Releases 연동을 위해 버전 태그(${TAG_NAME})를 푸시합니다...${NC}"
    git push origin "$TAG_NAME"
fi

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  [완료] GitHub(AhBiYout/PowerController)에 성공적으로 푸시되었습니다!${NC}"
echo -e "${GREEN}  - 버전 태그: v${APP_VER}${NC}"
echo -e "${GREEN}  - 저장소 링크: https://github.com/AhBiYout/PowerController${NC}"
echo -e "${GREEN}  - 릴리스 링크: https://github.com/AhBiYout/PowerController/releases${NC}"
echo -e "${GREEN}================================================================${NC}"

#!/bin/bash

# =================================================================
# MLOps Git 환경 자동 설정 스크립트
# =================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_header() {
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================${NC}"
}

print_header "🚀 MLOps Git 환경 설정"

# Git 사용자 설정 (이미 설정되어 있다면 스킵)
if [ -z "$(git config --global user.name)" ]; then
    print_info "Git 사용자 이름을 설정합니다..."
    read -p "Git 사용자 이름을 입력하세요: " username
    git config --global user.name "$username"
    print_success "Git 사용자 이름 설정: $username"
else
    print_success "Git 사용자 이름: $(git config --global user.name)"
fi

if [ -z "$(git config --global user.email)" ]; then
    print_info "Git 이메일을 설정합니다..."
    read -p "Git 이메일을 입력하세요: " email
    git config --global user.email "$email"
    print_success "Git 이메일 설정: $email"
else
    print_success "Git 이메일: $(git config --global user.email)"
fi

# Git 기본 브랜치 설정
if [ -z "$(git config --global init.defaultBranch)" ]; then
    git config --global init.defaultBranch main
    print_success "기본 브랜치 설정: main"
else
    print_success "기본 브랜치: $(git config --global init.defaultBranch)"
fi

# WSL 최적화 설정
print_info "WSL Git 최적화 설정 적용 중..."

git config --global core.autocrlf input
git config --global core.filemode false
git config --global core.ignorecase false
git config --global core.preloadindex true
git config --global core.fscache true

print_success "WSL Git 최적화 설정 완료"

# MLOps Git 별칭 설정
print_info "MLOps Git 별칭 설정 중..."

git config --global alias.mlops-stage 'add -A'
git config --global alias.mlops-exp 'checkout -b experiment/'
git config --global alias.mlops-bugfix 'checkout -b bugfix/'
git config --global alias.mlops-status 'status --porcelain'

print_success "MLOps Git 별칭 설정 완료"

# 파일 권한 설정
print_info "스크립트 파일 권한 설정 중..."

[ -f "scripts/validate_branch_name.sh" ] && chmod +x scripts/validate_branch_name.sh
[ -f "tests/run_3_1_tests.sh" ] && chmod +x tests/run_3_1_tests.sh
[ -f "run_docker_tests.sh" ] && chmod +x run_docker_tests.sh

print_success "파일 권한 설정 완료"

print_header "✅ MLOps Git 환경 설정 완료!"
print_info "이제 다음 명령어로 테스트를 실행할 수 있습니다:"
print_info "bash tests/run_3_1_tests.sh all"
print_info "bash run_docker_tests.sh all"

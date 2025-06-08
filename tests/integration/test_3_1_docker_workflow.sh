#!/bin/bash

# =================================================================
# Docker 워크플로우 통합 테스트
# Docker 환경에서 Git 워크플로우 테스트
# =================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_header() {
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================${NC}"
}

# 테스트 시작
print_header "🐳 Docker 워크플로우 통합 테스트"

# 프로젝트 루트 확인
if [ -z "$MLOPS_PROJECT_ROOT" ]; then
    if [ -d "/workspace" ] && [ -f "/workspace/docker-compose.git-workflow.yml" ]; then
        export MLOPS_PROJECT_ROOT="/workspace"
    elif [ -f "./docker-compose.git-workflow.yml" ]; then
        export MLOPS_PROJECT_ROOT="$(pwd)"
    else
        print_error "MLOPS_PROJECT_ROOT를 찾을 수 없습니다."
        exit 1
    fi
fi

print_info "프로젝트 루트: $MLOPS_PROJECT_ROOT"

# Docker 관련 파일 존재 확인
test_docker_files() {
    print_info "Docker 설정 파일 확인 중..."
    
    # Docker Compose 파일 위치 확인 (루트에 있음)
    if [ -f "$MLOPS_PROJECT_ROOT/docker-compose.git-workflow.yml" ]; then
        print_success "docker-compose.git-workflow.yml 존재 확인"
    else
        print_error "docker-compose.git-workflow.yml이 없습니다"
        return 1
    fi
    
    if [ -f "$MLOPS_PROJECT_ROOT/docker-compose.simple.yml" ]; then
        print_success "docker-compose.simple.yml 존재 확인"
    else
        print_error "docker-compose.simple.yml이 없습니다"
        return 1
    fi
    
    # Dockerfile 확인
    if [ -f "$MLOPS_PROJECT_ROOT/Dockerfile.dev" ]; then
        print_success "Dockerfile.dev 존재 확인"
    else
        print_info "Dockerfile.dev가 없습니다 (선택적)"
    fi
    
    return 0
}

# Docker 명령어 확인
test_docker_commands() {
    print_info "Docker 명령어 확인 중..."
    
    # Docker 환경 내부에서는 Docker 명령어가 없는 것이 정상
    if [ -d "/workspace" ]; then
        print_info "Docker 컨테이너 내부 환경 감지"
        print_success "Docker 컨테이너 내부에서는 Docker 명령어 불필요"
        return 0
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다"
        return 1
    fi
    print_success "Docker 명령어 사용 가능"
    
    # Docker 실행 상태 확인 (선택적)
    if docker info &> /dev/null; then
        print_success "Docker 데몬 실행 중"
    else
        print_info "Docker 데몬이 실행되지 않음 (CI 환경에서는 정상)"
    fi
    
    return 0
}

# Git 설정 확인
test_git_configuration() {
    print_info "Git 설정 확인 중..."
    
    if ! command -v git &> /dev/null; then
        print_error "Git이 설치되지 않았습니다"
        return 1
    fi
    print_success "Git 명령어 사용 가능"
    
    # Git 버전 확인
    git_version=$(git --version)
    print_success "Git 버전: $git_version"
    
    # Git 설정 확인 (있는 경우만)
    if git config --global user.name &> /dev/null; then
        user_name=$(git config --global user.name)
        print_success "Git 사용자: $user_name"
    else
        print_info "Git 사용자 설정 없음 (테스트 환경에서는 정상)"
    fi
    
    return 0
}

# 브랜치 검증 스크립트 테스트
test_branch_validation_script() {
    print_info "브랜치 검증 스크립트 테스트 중..."
    
    local script_path="$MLOPS_PROJECT_ROOT/scripts/validate_branch_name.sh"
    
    if [ ! -f "$script_path" ]; then
        print_error "브랜치 검증 스크립트가 없습니다: $script_path"
        return 1
    fi
    
    if [ ! -x "$script_path" ]; then
        print_error "브랜치 검증 스크립트에 실행 권한이 없습니다"
        return 1
    fi
    print_success "브랜치 검증 스크립트 실행 권한 확인"
    
    # 유효한 브랜치명 테스트
    if "$script_path" "feature/stage1-test" &> /dev/null; then
        print_success "유효한 브랜치명 검증 통과"
    else
        print_error "유효한 브랜치명 검증 실패"
        return 1
    fi
    
    # 무효한 브랜치명 테스트
    if ! "$script_path" "invalid-branch" &> /dev/null; then
        print_success "무효한 브랜치명 검증 통과 (올바르게 거부됨)"
    else
        print_error "무효한 브랜치명 검증 실패 (잘못 허용됨)"
        return 1
    fi
    
    return 0
}

# 테스트 실행 스크립트 확인
test_script_structure() {
    print_info "테스트 스크립트 구조 확인 중..."
    
    local test_script="$MLOPS_PROJECT_ROOT/scripts/test/run_3_1_tests.sh"
    
    if [ ! -f "$test_script" ]; then
        print_error "테스트 실행 스크립트가 없습니다: $test_script"
        return 1
    fi
    print_success "테스트 실행 스크립트 존재 확인"
    
    if [ ! -x "$test_script" ]; then
        print_error "테스트 실행 스크립트에 실행 권한이 없습니다"
        return 1
    fi
    print_success "테스트 실행 스크립트 실행 권한 확인"
    
    return 0
}

# 환경 변수 테스트
test_environment_variables() {
    print_info "환경 변수 확인 중..."
    
    if [ -z "$MLOPS_PROJECT_ROOT" ]; then
        print_error "MLOPS_PROJECT_ROOT 환경 변수가 설정되지 않았습니다"
        return 1
    fi
    print_success "MLOPS_PROJECT_ROOT: $MLOPS_PROJECT_ROOT"
    
    if [ "$TEST_MODE" = "true" ]; then
        print_success "TEST_MODE: $TEST_MODE"
    else
        print_info "TEST_MODE가 설정되지 않았습니다 (선택적)"
    fi
    
    return 0
}

# 모든 테스트 실행
main() {
    local failed_tests=0
    
    # 각 테스트 실행
    test_docker_files || ((failed_tests++))
    test_docker_commands || ((failed_tests++))
    test_git_configuration || ((failed_tests++))
    test_branch_validation_script || ((failed_tests++))
    test_script_structure || ((failed_tests++))
    test_environment_variables || ((failed_tests++))
    
    print_header "🧪 Docker 워크플로우 테스트 결과"
    
    if [ $failed_tests -eq 0 ]; then
        print_success "모든 Docker 워크플로우 테스트 통과!"
        return 0
    else
        print_error "$failed_tests개의 테스트 실패"
        return 1
    fi
}

# 메인 실행
main

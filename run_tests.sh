#!/bin/bash

# =================================================================
# MLOps Git 워크플로우 메인 테스트 실행기
# =================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_header "🚀 MLOps Git 워크플로우 테스트 시스템"

# 프로젝트 루트 확인
if [ ! -f "docker/docker-compose.git-workflow.yml" ]; then
    print_error "프로젝트 루트에서 실행해주세요: cd /mnt/c/dev/movie-mlops"
    exit 1
fi

# 도움말
if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ $# -eq 0 ]; then
    print_info "사용법: $0 [옵션] [테스트타입]"
    echo ""
    echo "옵션:"
    echo "  --setup          초기 설정 실행 (최초 1회만)"
    echo "  --wsl            WSL 환경에서 테스트 실행"
    echo "  --docker         Docker 환경에서 테스트 실행"
    echo "  --help, -h       이 도움말 표시"
    echo ""
    echo "테스트 타입:"
    echo "  unit             단위 테스트만"
    echo "  integration      통합 테스트만"
    echo "  e2e              E2E 테스트만"
    echo "  branch           브랜치 검증만"
    echo "  coverage         커버리지 테스트"
    echo "  all              모든 테스트 (기본값)"
    echo ""
    echo "예시:"
    echo "  $0 --setup                # 최초 설정"
    echo "  $0 --wsl all              # WSL에서 모든 테스트"
    echo "  $0 --docker unit          # Docker에서 단위 테스트"
    echo "  $0 --wsl                  # WSL에서 기본 테스트"
    exit 0
fi

# 초기 설정
if [ "$1" = "--setup" ]; then
    print_header "🔧 MLOps Git 환경 초기 설정"
    
    print_info "Git 환경 설정 중..."
    bash scripts/setup/setup_mlops_git.sh
    
    print_info "Docker 네트워크 설정 중..."
    bash scripts/setup/setup_docker_network.sh
    
    print_success "초기 설정 완료!"
    print_info "이제 다음 명령어로 테스트를 실행하세요:"
    print_info "$0 --wsl all"
    exit 0
fi

# 테스트 실행 환경 및 타입 결정
if [ "$1" = "--wsl" ]; then
    TEST_ENV="wsl"
    TEST_TYPE=${2:-all}
elif [ "$1" = "--docker" ]; then
    TEST_ENV="docker"
    TEST_TYPE=${2:-all}
else
    # 기본값: WSL 환경
    TEST_ENV="wsl"
    TEST_TYPE=${1:-all}
fi

print_info "실행 환경: $TEST_ENV"
print_info "테스트 타입: $TEST_TYPE"

# WSL 환경에서 테스트 실행
if [ "$TEST_ENV" = "wsl" ]; then
    print_header "🖥️ WSL 환경에서 테스트 실행"
    export MLOPS_PROJECT_ROOT="$(pwd)"
    export TEST_MODE=true
    bash scripts/test/run_3_1_tests.sh "$TEST_TYPE"

# Docker 환경에서 테스트 실행  
elif [ "$TEST_ENV" = "docker" ]; then
    print_header "🐳 Docker 환경에서 테스트 실행"
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker가 실행되지 않고 있습니다. Docker Desktop을 시작해주세요."
        exit 1
    fi
    
    # Docker Compose 파일 선택
    if docker network inspect mlops-network &> /dev/null; then
        COMPOSE_FILE="docker/docker-compose.git-workflow.yml"
        print_info "네트워크 포함 Docker 설정 사용"
    else
        COMPOSE_FILE="docker/docker-compose.simple.yml"
        print_info "간단한 Docker 설정 사용"
    fi
    
    # Docker 컨테이너에서 테스트 실행
    docker compose -f "$COMPOSE_FILE" run --rm mlops-git-workflow bash -c "
        export MLOPS_PROJECT_ROOT=/workspace
        export TEST_MODE=true
        bash scripts/test/run_3_1_tests.sh $TEST_TYPE
    " || {
        print_error "Docker 테스트 실행 실패"
        exit 1
    }
fi

print_success "테스트 완료!"

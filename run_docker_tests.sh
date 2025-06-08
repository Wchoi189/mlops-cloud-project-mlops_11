#!/bin/bash

# =================================================================
# Docker를 통한 MLOps Git 워크플로우 테스트 실행 스크립트
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

# 현재 디렉터리가 프로젝트 루트인지 확인
if [ ! -f "docker/docker-compose.git-workflow.yml" ]; then
    print_error "프로젝트 루트에서 실행해주세요: cd /mnt/c/dev/movie-mlops"
    exit 1
fi

print_header "🐳 Docker를 통한 MLOps Git 워크플로우 테스트"

# Docker 설정 확인
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되지 않았습니다."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker가 실행되지 않고 있습니다. Docker Desktop을 시작해주세요."
    exit 1
fi

# 테스트 타입 설정
TEST_TYPE=${1:-all}

print_info "테스트 타입: $TEST_TYPE"
print_info "현재 디렉터리: $(pwd)"

# Docker 네트워크 확인 및 생성
print_info "Docker 네트워크 확인 중..."
if ! docker network inspect mlops-network &> /dev/null; then
    print_info "mlops-network 생성 중..."
    docker network create mlops-network || {
        print_error "Docker 네트워크 생성 실패. docker/docker-compose.simple.yml을 사용합니다."
        COMPOSE_FILE="docker/docker-compose.simple.yml"
    }
else
    print_success "mlops-network 존재 확인"
    COMPOSE_FILE="docker/docker-compose.git-workflow.yml"
fi

# Docker Compose 파일 선택
if [ -z "$COMPOSE_FILE" ]; then
    if [ -f "docker/docker-compose.simple.yml" ]; then
        COMPOSE_FILE="docker/docker-compose.simple.yml"
        print_info "간단한 Docker 설정 사용: $COMPOSE_FILE"
    else
        COMPOSE_FILE="docker/docker-compose.git-workflow.yml"
        print_info "기본 Docker 설정 사용: $COMPOSE_FILE"
    fi
fi

# 환경 변수 설정
export MLOPS_PROJECT_ROOT="/workspace"
export TEST_MODE=true

print_info "Docker Compose 파일: $COMPOSE_FILE"

# Docker 컨테이너에서 테스트 실행
print_header "🧪 Docker 컨테이너에서 테스트 실행"

# Docker 컨테이너 실행
docker compose -f "$COMPOSE_FILE" run --rm mlops-git-workflow bash -c "
    set -e
    export MLOPS_PROJECT_ROOT=/workspace
    export TEST_MODE=true
    export WSL_DISTRO_NAME=Ubuntu
    
    echo '📍 컨테이너 내부 환경 확인'
    echo 'PWD:' \$(pwd)
    echo 'Python:' \$(python --version)
    echo 'Git:' \$(git --version)
    echo 'MLOPS_PROJECT_ROOT:' \$MLOPS_PROJECT_ROOT
    
    echo '🧪 테스트 실행 중...'
    bash scripts/test/run_3_1_tests.sh $TEST_TYPE
" || {
    print_error "Docker 테스트 실행 실패"
    
    # 대안: 네트워크 없이 시도
    if [ "$COMPOSE_FILE" = "docker/docker-compose.git-workflow.yml" ]; then
        print_info "네트워크 없는 설정으로 재시도 중..."
        if [ -f "docker/docker-compose.simple.yml" ]; then
            docker compose -f docker/docker-compose.simple.yml run --rm mlops-git-workflow bash -c "
                export MLOPS_PROJECT_ROOT=/workspace
                export TEST_MODE=true
                bash scripts/test/run_3_1_tests.sh $TEST_TYPE
            "
        fi
    fi
    
    exit 1
}

print_success "Docker 테스트 완료!"

# 사용법 안내
echo ""
print_header "📋 사용법 안내"
echo "새로운 방법:"
echo "  ./run_tests.sh --wsl all        # WSL에서 모든 테스트"
echo "  ./run_tests.sh --docker unit    # Docker에서 단위 테스트"
echo "  ./run_tests.sh --setup          # 초기 설정"
echo ""
echo "기존 방법 (호환성):"
echo "  bash scripts/test/run_3_1_tests.sh all"
echo "  bash run_docker_tests.sh all"

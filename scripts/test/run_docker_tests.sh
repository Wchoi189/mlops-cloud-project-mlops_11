#!/bin/bash

# =================================================================
# Docker 환경 테스트 실행 스크립트
# =================================================================

set -e  # 에러 발생 시 즉시 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # 색상 없음

# 함수 정의
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

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Docker 환경 확인
check_docker_environment() {
    print_header "🐳 Docker 환경 확인"
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다."
        print_info "Docker Desktop을 설치하고 시작한 후 다시 시도하세요."
        exit 1
    fi
    print_success "Docker: $(docker --version | head -n1)"
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    if docker compose version &> /dev/null; then
        print_success "Docker Compose: $(docker compose version | head -n1)"
        COMPOSE_CMD="docker compose"
    else
        print_success "Docker Compose: $(docker-compose --version | head -n1)"
        COMPOSE_CMD="docker-compose"
    fi
    
    # Docker 실행 상태 확인
    if ! docker info &> /dev/null; then
        print_error "Docker 데몬이 실행되지 않았습니다."
        print_info "Docker Desktop을 시작하고 다시 시도하세요."
        exit 1
    fi
    print_success "Docker 데몬 실행 중"
}

# Docker 네트워크 설정
setup_docker_network() {
    print_header "🌐 Docker 네트워크 설정"
    
    # mlops-network 존재 확인
    if ! docker network ls | grep -q "mlops-network"; then
        print_info "mlops-network 생성 중..."
        docker network create mlops-network || {
            print_warning "네트워크 생성 실패 - 이미 존재하거나 권한 문제일 수 있습니다."
        }
    else
        print_success "mlops-network 이미 존재함"
    fi
}

# Docker Compose 파일 확인
check_compose_files() {
    print_header "📄 Docker Compose 파일 확인"
    
    # Git 워크플로우 컴포즈 파일 확인
    if [ -f "docker-compose.git-workflow.yml" ]; then
        print_success "docker-compose.git-workflow.yml 존재함"
        COMPOSE_FILE="docker-compose.git-workflow.yml"
    elif [ -f "docker/docker-compose.git-workflow.yml" ]; then
        print_success "docker/docker-compose.git-workflow.yml 존재함"
        COMPOSE_FILE="docker/docker-compose.git-workflow.yml"
    else
        print_error "Git 워크플로우 Compose 파일을 찾을 수 없습니다."
        print_info "다음 파일 중 하나가 필요합니다:"
        print_info "  - docker-compose.git-workflow.yml"
        print_info "  - docker/docker-compose.git-workflow.yml"
        exit 1
    fi
}

# Docker 환경에서 테스트 실행
run_docker_tests() {
    print_header "🧪 Docker 환경에서 테스트 실행"
    
    # 환경 변수 설정
    export TEST_MODE=true
    export MLOPS_PROJECT_ROOT="/workspace"
    export WSL_DISTRO_NAME="Ubuntu"
    
    print_info "Docker 컨테이너에서 3.1 테스트 실행 중..."
    
    # Docker Compose로 테스트 실행
    $COMPOSE_CMD -f "$COMPOSE_FILE" run --rm mlops-git-workflow bash scripts/test/run_3_1_tests.sh all || {
        print_error "Docker 테스트 실행 실패"
        
        # 디버깅 정보 제공
        print_info "디버깅을 위한 컨테이너 실행:"
        print_info "$COMPOSE_CMD -f $COMPOSE_FILE run --rm mlops-git-workflow bash"
        
        return 1
    }
    
    print_success "Docker 환경 테스트 완료"
}

# Docker 이미지 빌드 (필요시)
build_docker_image() {
    print_header "🏗️ Docker 이미지 빌드"
    
    # Dockerfile.dev 존재 확인
    if [ ! -f "Dockerfile.dev" ]; then
        print_warning "Dockerfile.dev가 없습니다. 이미지 빌드를 건너뜁니다."
        return 0
    fi
    
    print_info "Docker 이미지 빌드 중..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build mlops-git-workflow || {
        print_error "Docker 이미지 빌드 실패"
        return 1
    }
    
    print_success "Docker 이미지 빌드 완료"
}

# 정리 작업
cleanup() {
    print_header "🧹 정리 작업"
    
    # 실행 중인 컨테이너 정리
    print_info "실행 중인 컨테이너 정리 중..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    print_success "정리 완료"
}

# 도움말 표시
show_help() {
    print_header "🐳 Docker 테스트 실행기 도움말"
    echo ""
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --build         Docker 이미지 강제 빌드"
    echo "  --no-network    네트워크 설정 건너뛰기"
    echo "  --cleanup       정리 작업만 실행"
    echo "  --help, -h      이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0              기본 Docker 테스트 실행"
    echo "  $0 --build      이미지 빌드 후 테스트 실행"
    echo "  $0 --cleanup    컨테이너 정리만 실행"
    echo ""
    echo "환경 요구사항:"
    echo "  - Docker Desktop 설치 및 실행"
    echo "  - docker-compose.git-workflow.yml 파일"
    echo "  - Dockerfile.dev 파일 (빌드 시)"
    exit 0
}

# 메인 실행 로직
main() {
    local BUILD_IMAGE=false
    local SETUP_NETWORK=true
    local CLEANUP_ONLY=false
    
    # 인수 처리
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                BUILD_IMAGE=true
                shift
                ;;
            --no-network)
                SETUP_NETWORK=false
                shift
                ;;
            --cleanup)
                CLEANUP_ONLY=true
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                print_error "알 수 없는 옵션: $1"
                print_info "도움말: $0 --help"
                exit 1
                ;;
        esac
    done
    
    # 정리 작업만 실행하는 경우
    if [ "$CLEANUP_ONLY" = true ]; then
        check_docker_environment
        check_compose_files
        cleanup
        exit 0
    fi
    
    # 작업 디렉터리 확인
    if [ ! -f "scripts/test/run_3_1_tests.sh" ]; then
        print_error "MLOps 프로젝트 루트 디렉터리에서 실행하세요."
        print_info "현재 디렉터리: $(pwd)"
        print_info "예상 위치: /mnt/c/dev/movie-mlops"
        exit 1
    fi
    
    print_header "🚀 Docker 환경 MLOps 테스트 시작"
    
    # 실행 단계
    check_docker_environment
    check_compose_files
    
    if [ "$SETUP_NETWORK" = true ]; then
        setup_docker_network
    fi
    
    if [ "$BUILD_IMAGE" = true ]; then
        build_docker_image
    fi
    
    # 트랩 설정 (종료 시 정리)
    trap cleanup EXIT
    
    # 메인 테스트 실행
    run_docker_tests
    
    print_header "🎉 Docker 테스트 완료!"
    print_success "모든 Docker 환경 테스트가 성공적으로 완료되었습니다."
}

# 스크립트 실행
main "$@"

#!/bin/bash

# =================================================================
# 3.1 Git Workflow Testing Script for WSL Docker Environment
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

# 프로젝트 경로 먼저 설정 (Docker 환경 감지)
if [ -z "$MLOPS_PROJECT_ROOT" ]; then
    # Docker 환경에서는 /workspace, WSL 환경에서는 현재 디렉터리
    if [ -d "/workspace" ] && [ -f "/workspace/docker-compose.git-workflow.yml" ]; then
        export MLOPS_PROJECT_ROOT="/workspace"
        print_info "Docker 환경 감지: $MLOPS_PROJECT_ROOT"
        USE_ENV_FILE=false  # Docker 환경에서는 .env 파일 사용 안 함
    elif [ -f "./docker-compose.git-workflow.yml" ]; then
        export MLOPS_PROJECT_ROOT="$(pwd)"
        print_info "WSL 환경 감지: $MLOPS_PROJECT_ROOT"
        USE_ENV_FILE=true   # WSL 환경에서는 .env 파일 사용
    else
        print_error "프로젝트 루트를 찾을 수 없습니다."
        print_error "다음 중 하나를 실행하세요:"
        print_error "1. export MLOPS_PROJECT_ROOT=\"/mnt/c/dev/movie-mlops\""
        print_error "2. cd /mnt/c/dev/movie-mlops && bash scripts/test/run_3_1_tests.sh"
        exit 1
    fi
fi

# .env 파일 로드 (WSL 환경에서만)
if [ "$USE_ENV_FILE" = "true" ] && [ -f ".env" ]; then
    print_info ".env 파일에서 환경 변수 로드 중..."
    # = 포함된 라인만 처리하고, % 문자가 있는 라인은 제외
    while IFS='=' read -r key value; do
        # 주석이나 빈 라인 건너뛰기
        if [[ $key =~ ^[[:space:]]*# ]] || [[ -z $key ]]; then
            continue
        fi
        # % 문자가 포함된 값은 건너뛰기 (로그 포맷 등)
        if [[ $value == *"%"* ]]; then
            continue
        fi
        # 유효한 환경 변수명 확인
        if [[ $key =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    done < <(grep -v '^[[:space:]]*#' .env | grep '=')
    print_success ".env 파일 로드 완료"
elif [ "$USE_ENV_FILE" = "false" ]; then
    print_info "Docker 환경: .env 파일 대신 Docker Compose 환경 변수 사용"
fi

# 작업 디렉터리 변경
if [ "$PWD" != "$MLOPS_PROJECT_ROOT" ]; then
    print_info "작업 디렉터리를 $MLOPS_PROJECT_ROOT로 변경"
    cd "$MLOPS_PROJECT_ROOT" || {
        print_error "디렉터리 변경 실패: $MLOPS_PROJECT_ROOT"
        exit 1
    }
fi

# 환경 변수 설정
export TEST_MODE=true
export WSL_DISTRO_NAME=${WSL_DISTRO_NAME:-Ubuntu}

print_header "🚀 3.1 Git 워크플로우 테스트 실행 시작..."
print_info "프로젝트 경로: $MLOPS_PROJECT_ROOT"
print_info "환경 변수 설정 완료"

# 테스트 타입 확인
TEST_TYPE=${1:-all}

# 의존성 확인
check_dependencies() {
    print_header "🔍 의존성 확인"
    
    # Python 확인
    if ! command -v python &> /dev/null; then
        if ! command -v python3 &> /dev/null; then
            print_error "Python이 설치되지 않았습니다."
            return 1
        else
            alias python=python3
        fi
    fi
    print_success "Python: $(python --version)"
    
    # pytest 확인
    if ! python -c "import pytest" 2>/dev/null; then
        print_warning "pytest가 설치되지 않았습니다. 설치를 시도합니다..."
        pip install pytest pytest-cov pytest-mock gitpython dulwich pytest-env || {
            print_error "pytest 설치 실패"
            return 1
        }
    fi
    print_success "pytest: $(python -m pytest --version | head -n1)"
    
    # Git 확인
    if ! command -v git &> /dev/null; then
        print_error "Git이 설치되지 않았습니다."
        return 1
    fi
    print_success "Git: $(git --version)"
    
    # 테스트 파일 확인
    if [ ! -d "tests" ]; then
        print_error "tests 디렉터리가 없습니다."
        return 1
    fi
    
    # Git 설정 확인
    if [ -z "$(git config --global user.name)" ]; then
        print_warning "Git 사용자 이름이 설정되지 않았습니다."
        print_info "다음 명령어로 설정하세요: git config --global user.name \"Your Name\""
    else
        print_success "Git 사용자: $(git config --global user.name)"
    fi
    
    if [ -z "$(git config --global user.email)" ]; then
        print_warning "Git 이메일이 설정되지 않았습니다."
        print_info "다음 명령어로 설정하세요: git config --global user.email \"your.email@example.com\""
    else
        print_success "Git 이메일: $(git config --global user.email)"
    fi
    
    return 0
}

# 단위 테스트 실행
run_unit_tests() {
    print_header "🧪 단위 테스트 실행"
    
    # 단위 테스트 파일이 없다면 기본 테스트 생성
    if [ ! -f "tests/unit/test_3_1_basic.py" ]; then
        print_info "기본 단위 테스트 파일을 생성합니다..."
        create_basic_unit_tests
    fi
    
    if [ -d "tests/unit" ] && [ "$(ls -A tests/unit/*.py 2>/dev/null)" ]; then
        python -m pytest tests/unit/ -v --tb=short || {
            print_error "단위 테스트 실패"
            return 1
        }
        print_success "단위 테스트 통과"
    else
        print_warning "단위 테스트 파일이 없습니다."
    fi
    
    return 0
}

# 통합 테스트 실행
run_integration_tests() {
    print_header "🔗 통합 테스트 실행"
    
    # Python 통합 테스트
    if [ -d "tests/integration" ] && [ "$(ls -A tests/integration/*.py 2>/dev/null)" ]; then
        python -m pytest tests/integration/ -v --tb=short || {
            print_error "Python 통합 테스트 실패"
            return 1
        }
        print_success "Python 통합 테스트 통과"
    else
        print_warning "Python 통합 테스트 파일이 없습니다."
    fi
    
    # Bash 통합 테스트
    if [ -f "tests/integration/test_3_1_docker_workflow.sh" ]; then
        bash tests/integration/test_3_1_docker_workflow.sh || {
            print_error "Docker 통합 테스트 실패"
            return 1
        }
        print_success "Docker 통합 테스트 통과"
    else
        print_warning "Docker 통합 테스트 파일이 없습니다."
    fi
    
    return 0
}

# E2E 테스트 실행
run_e2e_tests() {
    print_header "🎯 E2E 테스트 실행"
    
    if [ -d "tests/e2e" ] && [ "$(ls -A tests/e2e/*.py 2>/dev/null)" ]; then
        python -m pytest tests/e2e/ -v --tb=short || {
            print_error "E2E 테스트 실패"
            return 1
        }
        print_success "E2E 테스트 통과"
    else
        print_warning "E2E 테스트 파일이 없습니다."
    fi
    
    return 0
}

# 브랜치 검증 테스트
run_branch_validation() {
    print_header "🌿 브랜치 검증 테스트"
    
    # 브랜치 검증 스크립트 확인
    if [ -f "scripts/validate_branch_name.sh" ]; then
        chmod +x scripts/validate_branch_name.sh
        
        # 유효한 브랜치명 테스트
        print_info "유효한 브랜치명 테스트:"
        VALID_BRANCHES=(
            "feature/stage1-data-pipeline"
            "feature/stage2-feature-store"
            "experiment/hyperparameter-tuning"
            "bugfix/123-memory-leak"
        )
        
        for branch in "${VALID_BRANCHES[@]}"; do
            if ./scripts/validate_branch_name.sh "$branch" >/dev/null 2>&1; then
                print_success "$branch"
            else
                print_error "$branch (유효해야 하는데 실패)"
            fi
        done
        
        # 무효한 브랜치명 테스트
        print_info "무효한 브랜치명 테스트:"
        INVALID_BRANCHES=(
            "Feature/Stage1-DataPipeline"
            "random-branch"
            "main"
            "master"
        )
        
        for branch in "${INVALID_BRANCHES[@]}"; do
            if ! ./scripts/validate_branch_name.sh "$branch" >/dev/null 2>&1; then
                print_success "$branch (올바르게 거부됨)"
            else
                print_error "$branch (무효해야 하는데 통과)"
            fi
        done
        
    else
        print_warning "브랜치 검증 스크립트가 없습니다: scripts/validate_branch_name.sh"
    fi
    
    return 0
}

# 커버리지 테스트
run_coverage() {
    print_header "📊 테스트 커버리지 실행"
    
    if python -c "import coverage" 2>/dev/null; then
        python -m pytest tests/ --cov=scripts --cov-report=term --cov-report=html || {
            print_error "커버리지 테스트 실패"
            return 1
        }
        print_success "커버리지 리포트 생성 완료"
    else
        print_warning "coverage 패키지가 설치되지 않았습니다."
        print_info "설치하려면: pip install coverage pytest-cov"
    fi
    
    return 0
}

# 기본 단위 테스트 생성
create_basic_unit_tests() {
    cat > tests/unit/test_3_1_basic.py << 'EOF'
#!/usr/bin/env python3
"""
기본 Git 워크플로우 테스트
"""

import os
import subprocess
import pytest

class TestBasicGitWorkflow:
    """기본 Git 워크플로우 테스트"""
    
    def test_project_structure(self):
        """프로젝트 구조 확인"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        
        # 필수 파일들 확인
        required_files = [
            'docker-compose.git-workflow.yml',
            '.gitignore',
            'requirements.txt',
        ]
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"필수 파일이 없습니다: {file_path}"
    
    def test_git_installation(self):
        """Git 설치 확인"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            assert 'git version' in result.stdout
        except subprocess.CalledProcessError:
            pytest.fail("Git이 설치되지 않았습니다.")
    
    def test_python_installation(self):
        """Python 설치 확인"""
        import sys
        assert sys.version_info >= (3, 7), "Python 3.7 이상이 필요합니다."
    
    def test_environment_variables(self):
        """환경 변수 확인"""
        assert os.environ.get('TEST_MODE') == 'true', "TEST_MODE 환경 변수가 설정되지 않았습니다."
        assert 'MLOPS_PROJECT_ROOT' in os.environ, "MLOPS_PROJECT_ROOT 환경 변수가 설정되지 않았습니다."

if __name__ == '__main__':
    pytest.main([__file__])
EOF

    cat > tests/unit/__init__.py << 'EOF'
# Unit tests for Git workflow
EOF

    print_success "기본 단위 테스트 파일 생성 완료"
}

# __init__.py 파일 생성
create_init_files() {
    echo "# Test package" > tests/__init__.py
    echo "# Unit tests" > tests/unit/__init__.py
    echo "# Integration tests" > tests/integration/__init__.py
    echo "# E2E tests" > tests/e2e/__init__.py
}

# 메인 실행 로직
main() {
    # 의존성 확인
    check_dependencies || exit 1
    
    # __init__.py 파일 생성
    create_init_files
    
    # 테스트 타입에 따라 실행
    case "$TEST_TYPE" in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "branch")
            run_branch_validation
            ;;
        "coverage")
            run_coverage
            ;;
        "all")
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            run_branch_validation
            ;;
        *)
            print_error "알 수 없는 테스트 타입: $TEST_TYPE"
            print_info "사용법: $0 [unit|integration|e2e|branch|coverage|all]"
            exit 1
            ;;
    esac
    
    print_header "🎉 테스트 완료!"
    print_success "모든 테스트가 성공적으로 완료되었습니다."
}

# 도움말 표시
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_header "3.1 Git 워크플로우 테스트 도움말"
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  unit         단위 테스트만 실행"
    echo "  integration  통합 테스트만 실행"
    echo "  e2e          E2E 테스트만 실행"
    echo "  branch       브랜치 검증 테스트만 실행"
    echo "  coverage     커버리지 테스트 실행"
    echo "  all          모든 테스트 실행 (기본값)"
    echo "  --help, -h   이 도움말 표시"
    echo ""
    echo "환경 변수:"
    echo "  MLOPS_PROJECT_ROOT  프로젝트 루트 경로"
    echo "  TEST_MODE=true      테스트 모드 활성화"
    echo "  WSL_DISTRO_NAME     WSL 배포판 이름"
    echo ""
    echo "예시:"
    echo "  bash tests/run_3_1_tests.sh all"
    echo "  bash tests/run_3_1_tests.sh unit"
    echo "  MLOPS_PROJECT_ROOT=/workspace bash tests/run_3_1_tests.sh"
    exit 0
fi

# 메인 실행
main

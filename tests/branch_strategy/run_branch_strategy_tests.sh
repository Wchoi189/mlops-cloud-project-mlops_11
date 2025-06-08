#!/bin/bash
# 브랜치 전략 설정 종합 테스트 스크립트
# Movie MLOps 프로젝트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🌿 Movie MLOps 브랜치 전략 설정 테스트${NC}"
echo "==============================================="
echo

# 프로젝트 루트 확인
if [ ! -f "pyproject.toml" ] || [ ! -d ".git" ]; then
    echo -e "${RED}❌ 프로젝트 루트에서 실행해주세요.${NC}"
    exit 1
fi

# 테스트 결과 추적
total_tests=0
passed_tests=0
failed_tests=()

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}🧪 $test_name 테스트 중...${NC}"
    ((total_tests++))
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ 통과${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}  ❌ 실패${NC}"
        failed_tests+=("$test_name")
    fi
    echo
}

# 1. 스크립트 존재 확인
echo -e "${CYAN}📋 1. 필수 스크립트 존재 확인${NC}"
echo "----------------------------------------"

required_scripts=(
    "scripts/validate-branch-name.sh:브랜치명 검증 스크립트"
    "scripts/install-git-hooks.sh:Git Hook 설치 스크립트"
    "scripts/branch-manager.sh:브랜치 관리 스크립트"
    "scripts/git-hooks/pre-push:Pre-push Hook"
)

for script_info in "${required_scripts[@]}"; do
    IFS=':' read -r script_path script_description <<< "$script_info"
    
    if [ -f "$script_path" ]; then
        echo -e "${GREEN}  ✅ $script_description${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}  ❌ $script_description - 파일 없음: $script_path${NC}"
        failed_tests+=("$script_description")
    fi
    ((total_tests++))
done

echo

# 2. 스크립트 실행 권한 확인
echo -e "${CYAN}📋 2. 스크립트 실행 권한 확인${NC}"
echo "----------------------------------------"

for script_info in "${required_scripts[@]}"; do
    IFS=':' read -r script_path script_description <<< "$script_info"
    
    if [ -f "$script_path" ]; then
        if [ -x "$script_path" ]; then
            echo -e "${GREEN}  ✅ $script_description - 실행 권한 있음${NC}"
            ((passed_tests++))
        else
            echo -e "${YELLOW}  ⚠️ $script_description - 실행 권한 없음, 권한 부여 중...${NC}"
            chmod +x "$script_path"
            if [ -x "$script_path" ]; then
                echo -e "${GREEN}     ✅ 권한 부여 완료${NC}"
                ((passed_tests++))
            else
                echo -e "${RED}     ❌ 권한 부여 실패${NC}"
                failed_tests+=("$script_description 권한")
            fi
        fi
    else
        echo -e "${RED}  ❌ $script_description - 파일 없음${NC}"
        failed_tests+=("$script_description 권한")
    fi
    ((total_tests++))
done

echo

# 3. 브랜치명 검증 테스트
echo -e "${CYAN}📋 3. 브랜치명 검증 테스트${NC}"
echo "----------------------------------------"

if [ -x "scripts/validate-branch-name.sh" ]; then
    # 올바른 브랜치명 테스트
    valid_branches=(
        "feature/tmdb-api-integration"
        "bugfix/data-validation-error"
        "hotfix/critical-security-patch"
        "experiment/new-ml-algorithm"
        "docs/api-documentation"
        "data/collection-pipeline"
        "model/training-pipeline"
        "pipeline/airflow-setup"
        "infra/docker-optimization"
    )
    
    echo "올바른 브랜치명 테스트:"
    for branch in "${valid_branches[@]}"; do
        if bash scripts/validate-branch-name.sh "$branch" >/dev/null 2>&1; then
            echo -e "${GREEN}  ✅ $branch${NC}"
            ((passed_tests++))
        else
            echo -e "${RED}  ❌ $branch${NC}"
            failed_tests+=("Valid branch: $branch")
        fi
        ((total_tests++))
    done
    
    echo
    echo "잘못된 브랜치명 테스트:"
    invalid_branches=(
        "Feature/TmdbApiIntegration"  # 대문자
        "fix-bug"                     # 타입 없음
        "main"                        # 보호된 브랜치
        "develop"                     # 보호된 브랜치
        "feature/with spaces"         # 공백
        "invalid/type"                # 잘못된 타입
    )
    
    for branch in "${invalid_branches[@]}"; do
        if ! bash scripts/validate-branch-name.sh "$branch" >/dev/null 2>&1; then
            echo -e "${GREEN}  ✅ $branch (올바르게 거부됨)${NC}"
            ((passed_tests++))
        else
            echo -e "${RED}  ❌ $branch (잘못 통과됨)${NC}"
            failed_tests+=("Invalid branch: $branch")
        fi
        ((total_tests++))
    done
else
    echo -e "${RED}  ❌ 브랜치명 검증 스크립트를 찾을 수 없습니다.${NC}"
    failed_tests+=("브랜치명 검증 스크립트")
fi

echo

# 4. Git 설정 확인
echo -e "${CYAN}📋 4. Git 설정 확인${NC}"
echo "----------------------------------------"

run_test "Git 설치" "git --version"
run_test "Git 저장소" "git status"
run_test "Git 사용자 설정" "git config user.name && git config user.email"

# 5. 브랜치 관리 스크립트 테스트
echo -e "${CYAN}📋 5. 브랜치 관리 스크립트 테스트${NC}"
echo "----------------------------------------"

if [ -x "scripts/branch-manager.sh" ]; then
    run_test "브랜치 관리 도움말" "bash scripts/branch-manager.sh help"
    run_test "브랜치 목록 조회" "bash scripts/branch-manager.sh list"
    run_test "브랜치 상태 확인" "bash scripts/branch-manager.sh status"
else
    echo -e "${RED}  ❌ 브랜치 관리 스크립트를 찾을 수 없습니다.${NC}"
    failed_tests+=("브랜치 관리 스크립트")
fi

# 6. Git Hook 설치 테스트
echo -e "${CYAN}📋 6. Git Hook 설치 테스트${NC}"
echo "----------------------------------------"

if [ -x "scripts/install-git-hooks.sh" ]; then
    echo "Git Hook 설치 스크립트 테스트 (dry-run)..."
    
    # Hook 디렉터리 확인
    if [ -d ".git/hooks" ]; then
        echo -e "${GREEN}  ✅ Git Hook 디렉터리 존재${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}  ❌ Git Hook 디렉터리 없음${NC}"
        failed_tests+=("Git Hook 디렉터리")
    fi
    ((total_tests++))
    
    # Hook 소스 파일 확인
    if [ -f "scripts/git-hooks/pre-push" ]; then
        echo -e "${GREEN}  ✅ Pre-push Hook 소스 파일 존재${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}  ❌ Pre-push Hook 소스 파일 없음${NC}"
        failed_tests+=("Pre-push Hook 소스")
    fi
    ((total_tests++))
else
    echo -e "${RED}  ❌ Git Hook 설치 스크립트를 찾을 수 없습니다.${NC}"
    failed_tests+=("Git Hook 설치 스크립트")
fi

echo

# 7. Python 테스트 스크립트 실행
echo -e "${CYAN}📋 7. Python 테스트 스크립트 실행${NC}"
echo "----------------------------------------"

if [ -f "tests/branch_strategy/test_branch_naming.py" ]; then
    echo "Python 브랜치명 테스트 실행 중..."
    if python tests/branch_strategy/test_branch_naming.py >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Python 테스트 통과${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}  ❌ Python 테스트 실패${NC}"
        failed_tests+=("Python 브랜치명 테스트")
    fi
    ((total_tests++))
else
    echo -e "${YELLOW}  ⚠️ Python 테스트 스크립트를 찾을 수 없습니다.${NC}"
fi

echo

# 8. 결과 요약
echo "==============================================="
echo -e "${BLUE}📊 브랜치 전략 설정 테스트 결과${NC}"
echo "==============================================="
echo
echo "전체 테스트: $total_tests개"
echo -e "${GREEN}통과: $passed_tests개${NC}"
echo -e "${RED}실패: $((total_tests - passed_tests))개${NC}"

if [ ${#failed_tests[@]} -gt 0 ]; then
    echo
    echo -e "${RED}실패한 테스트:${NC}"
    for test in "${failed_tests[@]}"; do
        echo "  - $test"
    done
fi

echo
success_rate=$(( passed_tests * 100 / total_tests ))
echo "성공률: $success_rate%"

if [ $success_rate -ge 90 ]; then
    echo -e "${GREEN}🎉 우수! 브랜치 전략이 잘 구축되었습니다!${NC}"
elif [ $success_rate -ge 70 ]; then
    echo -e "${YELLOW}👍 양호! 대부분의 기능이 정상 작동합니다.${NC}"
else
    echo -e "${RED}⚠️ 개선 필요! 일부 설정을 점검해주세요.${NC}"
fi

echo
echo "💡 다음 단계:"
if [ $success_rate -ge 90 ]; then
    echo "  1. 팀원들에게 브랜치 명명 규칙 공유"
    echo "  2. Git Hook 설치: bash scripts/install-git-hooks.sh"
    echo "  3. GitHub에서 브랜치 보호 규칙 설정"
    echo "  4. 정기적인 브랜치 정리 프로세스 구축"
else
    echo "  1. 실패한 테스트들을 확인하고 수정"
    echo "  2. 스크립트 실행 권한 확인: chmod +x scripts/*.sh"
    echo "  3. Git 설정 확인: git config --list"
    echo "  4. 이 테스트를 다시 실행"
fi

echo
echo "📄 테스트 상세 로그는 다음 명령어로 확인 가능:"
echo "  bash $0 2>&1 | tee branch_strategy_test.log"

# 종료 코드 설정
if [ $success_rate -ge 70 ]; then
    exit 0
else
    exit 1
fi

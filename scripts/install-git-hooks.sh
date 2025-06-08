#!/bin/bash
# Git Hook 설치 스크립트
# Movie MLOps 프로젝트용 Git Hook 자동 설치

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🪝 Git Hook 설치 시작...${NC}"

# 프로젝트 루트 디렉터리 확인
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Git 저장소가 아닙니다. 프로젝트 루트에서 실행해주세요.${NC}"
    exit 1
fi

# Hook 소스 디렉터리
HOOK_SOURCE_DIR="scripts/git-hooks"
GIT_HOOKS_DIR=".git/hooks"

echo "📂 Hook 디렉터리 확인 중..."

# Hook 소스 디렉터리 존재 확인
if [ ! -d "$HOOK_SOURCE_DIR" ]; then
    echo -e "${RED}❌ Hook 소스 디렉터리를 찾을 수 없습니다: $HOOK_SOURCE_DIR${NC}"
    exit 1
fi

# Git Hook 디렉터리 확인
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo -e "${RED}❌ Git Hook 디렉터리를 찾을 수 없습니다: $GIT_HOOKS_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Hook 디렉터리 확인 완료${NC}"

# 사용 가능한 Hook 목록
AVAILABLE_HOOKS=()
for hook_file in "$HOOK_SOURCE_DIR"/*; do
    if [ -f "$hook_file" ]; then
        hook_name=$(basename "$hook_file")
        AVAILABLE_HOOKS+=("$hook_name")
    fi
done

if [ ${#AVAILABLE_HOOKS[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️ 설치할 Hook을 찾을 수 없습니다.${NC}"
    exit 0
fi

echo "📋 설치 가능한 Hook 목록:"
for hook in "${AVAILABLE_HOOKS[@]}"; do
    echo "  - $hook"
done

# Hook 설치 함수
install_hook() {
    local hook_name=$1
    local source_file="$HOOK_SOURCE_DIR/$hook_name"
    local target_file="$GIT_HOOKS_DIR/$hook_name"
    
    echo "🔧 $hook_name Hook 설치 중..."
    
    # 기존 Hook 백업
    if [ -f "$target_file" ]; then
        backup_file="$target_file.backup.$(date +%Y%m%d_%H%M%S)"
        echo "   📦 기존 Hook 백업: $backup_file"
        cp "$target_file" "$backup_file"
    fi
    
    # Hook 복사
    cp "$source_file" "$target_file"
    
    # 실행 권한 부여
    chmod +x "$target_file"
    
    # 설치 확인
    if [ -x "$target_file" ]; then
        echo -e "${GREEN}   ✅ $hook_name Hook 설치 완료${NC}"
        return 0
    else
        echo -e "${RED}   ❌ $hook_name Hook 설치 실패${NC}"
        return 1
    fi
}

# 모든 Hook 설치
installed_count=0
failed_count=0

for hook in "${AVAILABLE_HOOKS[@]}"; do
    if install_hook "$hook"; then
        ((installed_count++))
    else
        ((failed_count++))
    fi
done

echo
echo "📊 설치 결과:"
echo "  설치 완료: $installed_count"
echo "  설치 실패: $failed_count"

# 결과에 따른 메시지
if [ $failed_count -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 Git Hook이 성공적으로 설치되었습니다!${NC}"
    
    echo
    echo "📋 설치된 Hook들:"
    for hook in "${AVAILABLE_HOOKS[@]}"; do
        echo "  🪝 $hook"
        case $hook in
            "pre-push")
                echo "     - 푸시 전 브랜치명 및 커밋 메시지 검증"
                echo "     - 보호된 브랜치 직접 푸시 방지"
                ;;
            "pre-commit")
                echo "     - 커밋 전 코드 품질 검사"
                echo "     - 린팅 및 포맷팅 검증"
                ;;
            "commit-msg")
                echo "     - 커밋 메시지 형식 검증"
                echo "     - Conventional Commits 스타일 강제"
                ;;
        esac
        echo
    done
    
    echo "💡 사용 팁:"
    echo "  - Hook은 자동으로 실행됩니다."
    echo "  - Hook을 일시적으로 비활성화하려면: git push --no-verify"
    echo "  - Hook을 제거하려면: rm .git/hooks/<hook-name>"
    echo "  - Hook을 업데이트하려면: 이 스크립트를 다시 실행하세요."
    
else
    echo -e "${YELLOW}⚠️ 일부 Hook 설치에 실패했습니다.${NC}"
    echo "스크립트 권한과 파일 경로를 확인해주세요."
fi

echo
echo -e "${BLUE}🔧 추가 설정 안내:${NC}"
echo "1. 브랜치명 검증을 위해 validate-branch-name.sh 스크립트가 필요합니다."
echo "2. 팀원들도 동일한 Hook을 설치해야 일관성이 유지됩니다."
echo "3. Hook 설정은 로컬에만 적용되며, 저장소에는 포함되지 않습니다."

exit 0

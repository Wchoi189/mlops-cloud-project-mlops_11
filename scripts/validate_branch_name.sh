#!/bin/bash

# =================================================================
# MLOps 브랜치 네이밍 검증 스크립트
# =================================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 도움말 표시
show_help() {
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}MLOps 브랜치 네이밍 규칙${NC}"
    echo -e "${BLUE}==============================${NC}"
    echo ""
    echo -e "${GREEN}유효한 브랜치 패턴:${NC}"
    echo -e "  ${GREEN}feature/stage[1-9]-<설명>${NC}     # MLOps 단계별 기능"
    echo -e "  ${GREEN}experiment/<설명>${NC}             # 실험 브랜치"
    echo -e "  ${GREEN}bugfix/<번호>-<설명>${NC}          # 버그 수정"
    echo -e "  ${GREEN}hotfix/<번호>-<설명>${NC}          # 긴급 수정"
    echo -e "  ${GREEN}docs/<설명>${NC}                   # 문서 작업"
    echo ""
    echo -e "${GREEN}예시:${NC}"
    echo -e "  feature/stage1-data-pipeline"
    echo -e "  feature/stage4-cicd-pipeline"
    echo -e "  experiment/hyperparameter-tuning"
    echo -e "  bugfix/123-memory-leak"
    echo -e "  hotfix/456-security-patch"
    echo -e "  docs/api-documentation"
    echo ""
    echo -e "${RED}금지된 브랜치:${NC}"
    echo -e "  main, master, develop, staging, production"
    echo -e "  대문자 포함 브랜치"
    echo -e "  타입 접두사 없는 브랜치"
    echo ""
    echo -e "${YELLOW}사용법:${NC}"
    echo -e "  $0 <브랜치명>"
    echo -e "  $0 feature/stage5-model-serving"
}

# 브랜치명 검증 함수
validate_branch_name() {
    local branch_name="$1"
    
    # 보호된 브랜치 체크
    if [[ "$branch_name" =~ ^(main|master|develop|staging|production)$ ]]; then
        echo -e "${RED}❌ 오류: 보호된 브랜치명입니다: $branch_name${NC}"
        echo -e "${YELLOW}💡 보호된 브랜치는 직접 작업할 수 없습니다.${NC}"
        return 1
    fi
    
    # MLOps 단계별 브랜치 패턴: feature/stage[1-9]-<설명>
    if [[ "$branch_name" =~ ^feature/stage[1-9]-[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        # 단계 번호 추출
        stage_num=$(echo "$branch_name" | sed 's/feature\/stage\([1-9]\)-.*/\1/')
        echo -e "${GREEN}✅ 유효한 MLOps Stage $stage_num 브랜치: $branch_name${NC}"
        return 0
    fi
    
    # 실험 브랜치 패턴: experiment/<설명>
    if [[ "$branch_name" =~ ^experiment/[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        echo -e "${GREEN}✅ 유효한 실험 브랜치: $branch_name${NC}"
        return 0
    fi
    
    # 버그 수정 브랜치 패턴: bugfix/<번호>-<설명>
    if [[ "$branch_name" =~ ^bugfix/[0-9]+-[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        echo -e "${GREEN}✅ 유효한 버그 수정 브랜치: $branch_name${NC}"
        return 0
    fi
    
    # 긴급 수정 브랜치 패턴: hotfix/<번호>-<설명>
    if [[ "$branch_name" =~ ^hotfix/[0-9]+-[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        echo -e "${GREEN}✅ 유효한 긴급 수정 브랜치: $branch_name${NC}"
        return 0
    fi
    
    # 문서 브랜치 패턴: docs/<설명>
    if [[ "$branch_name" =~ ^docs/[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
        echo -e "${GREEN}✅ 유효한 문서 브랜치: $branch_name${NC}"
        return 0
    fi
    
    # 유효하지 않은 브랜치명
    echo -e "${RED}❌ 오류: 유효하지 않은 브랜치명입니다: $branch_name${NC}"
    echo -e "${YELLOW}💡 도움말을 보려면 $0 명령어를 실행하세요.${NC}"
    return 1
}

# 메인 로직
main() {
    # 인수가 없으면 도움말 표시
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 도움말 요청
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    # 브랜치명 검증
    local branch_name="$1"
    
    if validate_branch_name "$branch_name"; then
        exit 0
    else
        exit 1
    fi
}

# 스크립트 실행
main "$@"

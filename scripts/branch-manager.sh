#!/bin/bash
# 브랜치 전략 자동화 스크립트
# Movie MLOps 프로젝트 브랜치 관리 도구

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 브랜치 타입별 설명
declare -A BRANCH_TYPES=(
    ["feature"]="새로운 기능 개발"
    ["bugfix"]="버그 수정"
    ["hotfix"]="긴급 수정"
    ["experiment"]="실험적 기능"
    ["docs"]="문서 작업"
    ["data"]="데이터 관련 작업"
    ["model"]="모델 관련 작업"
    ["pipeline"]="파이프라인 작업"
    ["infra"]="인프라 작업"
)

# 브랜치 타입별 권장 작업 범위
declare -A BRANCH_SCOPES=(
    ["feature"]="api ui model data pipeline monitoring auth"
    ["bugfix"]="critical high medium low"
    ["hotfix"]="security performance data"
    ["experiment"]="ml-algorithm performance ui-ux"
    ["docs"]="api user-guide deployment architecture"
    ["data"]="collection preprocessing validation cleaning"
    ["model"]="training evaluation deployment tuning"
    ["pipeline"]="airflow cicd automation orchestration"
    ["infra"]="docker kubernetes terraform monitoring"
)

# 도움말 출력
show_help() {
    echo -e "${BLUE}🌿 Movie MLOps 브랜치 전략 관리 도구${NC}"
    echo
    echo "사용법:"
    echo "  $0 <명령어> [옵션]"
    echo
    echo "명령어:"
    echo "  create    - 새 브랜치 생성"
    echo "  validate  - 브랜치명 검증"
    echo "  list      - 브랜치 목록 조회"
    echo "  cleanup   - 완료된 브랜치 정리"
    echo "  status    - 현재 브랜치 상태"
    echo "  help      - 도움말 표시"
    echo
    echo "옵션:"
    echo "  -t, --type TYPE       브랜치 타입 지정"
    echo "  -d, --description DESC 브랜치 설명"
    echo "  -i, --interactive     대화형 모드"
    echo "  --dry-run            실제 실행 없이 미리보기"
    echo
    echo "예시:"
    echo "  $0 create -t feature -d \"tmdb-api-integration\""
    echo "  $0 validate feature/tmdb-api-integration"
    echo "  $0 list --type feature"
    echo "  $0 cleanup --dry-run"
}

# 브랜치 타입 선택 (대화형)
select_branch_type() {
    echo -e "${CYAN}📋 브랜치 타입을 선택하세요:${NC}"
    echo
    
    local types=($(printf "%s\n" "${!BRANCH_TYPES[@]}" | sort))
    local i=1
    
    for type in "${types[@]}"; do
        echo "  $i) $type - ${BRANCH_TYPES[$type]}"
        ((i++))
    done
    
    echo
    read -p "선택 (1-${#types[@]}): " choice
    
    if [[ $choice =~ ^[0-9]+$ ]] && [ $choice -ge 1 ] && [ $choice -le ${#types[@]} ]; then
        echo "${types[$((choice-1))]}"
    else
        echo ""
    fi
}

# 브랜치 설명 입력 도우미
get_branch_description() {
    local type=$1
    
    echo -e "${CYAN}📝 브랜치 설명을 입력하세요:${NC}"
    
    # 타입별 권장 스코프 표시
    if [ -n "${BRANCH_SCOPES[$type]}" ]; then
        echo "권장 스코프: ${BRANCH_SCOPES[$type]}"
    fi
    
    echo "예시: tmdb-api-integration, user-authentication, data-preprocessing"
    echo
    read -p "설명: " description
    
    # 공백을 하이픈으로 변경
    description=$(echo "$description" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
    
    echo "$description"
}

# 브랜치 생성
create_branch() {
    local type=""
    local description=""
    local interactive=false
    local dry_run=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                type="$2"
                shift 2
                ;;
            -d|--description)
                description="$2"
                shift 2
                ;;
            -i|--interactive)
                interactive=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                echo -e "${RED}❌ 알 수 없는 옵션: $1${NC}"
                return 1
                ;;
        esac
    done
    
    # 대화형 모드
    if [ "$interactive" = true ] || [ -z "$type" ]; then
        type=$(select_branch_type)
        if [ -z "$type" ]; then
            echo -e "${RED}❌ 올바른 브랜치 타입을 선택해주세요.${NC}"
            return 1
        fi
    fi
    
    if [ "$interactive" = true ] || [ -z "$description" ]; then
        description=$(get_branch_description "$type")
        if [ -z "$description" ]; then
            echo -e "${RED}❌ 브랜치 설명을 입력해주세요.${NC}"
            return 1
        fi
    fi
    
    # 브랜치명 생성
    local branch_name="$type/$description"
    
    echo -e "${BLUE}🌿 브랜치 생성 정보:${NC}"
    echo "  타입: $type"
    echo "  설명: $description"
    echo "  브랜치명: $branch_name"
    echo
    
    # 브랜치명 검증
    if [ -f "scripts/validate-branch-name.sh" ]; then
        echo "🔍 브랜치명 검증 중..."
        if ! bash scripts/validate-branch-name.sh "$branch_name"; then
            echo -e "${RED}❌ 브랜치명 검증 실패${NC}"
            return 1
        fi
    fi
    
    # Dry-run 모드
    if [ "$dry_run" = true ]; then
        echo -e "${YELLOW}🔍 Dry-run 모드: 실제로 브랜치를 생성하지 않습니다.${NC}"
        echo "실행될 명령어: git checkout -b $branch_name"
        return 0
    fi
    
    # 현재 브랜치 확인
    local current_branch=$(git branch --show-current)
    echo "현재 브랜치: $current_branch"
    
    # main 브랜치에서 분기하도록 권장
    if [ "$current_branch" != "main" ]; then
        echo -e "${YELLOW}⚠️ main 브랜치에서 분기하는 것을 권장합니다.${NC}"
        read -p "main 브랜치로 이동하시겠습니까? (y/N): " move_to_main
        
        if [[ $move_to_main =~ ^[Yy]$ ]]; then
            git checkout main
            git pull origin main
        fi
    fi
    
    # 브랜치 생성
    echo "🌿 브랜치 생성 중..."
    if git checkout -b "$branch_name"; then
        echo -e "${GREEN}✅ 브랜치 '$branch_name'가 성공적으로 생성되었습니다!${NC}"
        
        # 첫 커밋 가이드
        echo
        echo "💡 다음 단계:"
        echo "  1. 작업 파일들을 수정하세요"
        echo "  2. git add <파일명> 으로 변경사항을 스테이징하세요"
        echo "  3. git commit -m \"$type: 초기 작업 설정\" 으로 커밋하세요"
        echo "  4. git push -u origin $branch_name 으로 원격 저장소에 푸시하세요"
        
    else
        echo -e "${RED}❌ 브랜치 생성에 실패했습니다.${NC}"
        return 1
    fi
}

# 브랜치 목록 조회
list_branches() {
    local filter_type=""
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                filter_type="$2"
                shift 2
                ;;
            *)
                echo -e "${RED}❌ 알 수 없는 옵션: $1${NC}"
                return 1
                ;;
        esac
    done
    
    echo -e "${BLUE}🌿 브랜치 목록:${NC}"
    echo
    
    # 현재 브랜치 표시
    local current_branch=$(git branch --show-current)
    echo -e "${GREEN}📍 현재 브랜치: $current_branch${NC}"
    echo
    
    # 로컬 브랜치 목록
    echo "📂 로컬 브랜치:"
    
    local branches=($(git branch --format='%(refname:short)' | grep -v '^main$\|^develop$'))
    
    if [ ${#branches[@]} -eq 0 ]; then
        echo "  (브랜치 없음)"
    else
        for branch in "${branches[@]}"; do
            # 타입 필터링
            if [ -n "$filter_type" ] && [[ ! $branch =~ ^$filter_type/ ]]; then
                continue
            fi
            
            # 현재 브랜치 표시
            if [ "$branch" = "$current_branch" ]; then
                echo -e "  ${GREEN}* $branch${NC}"
            else
                echo "    $branch"
            fi
            
            # 브랜치 정보 표시
            local last_commit=$(git log -1 --format="%h %s" "$branch" 2>/dev/null)
            if [ -n "$last_commit" ]; then
                echo "      └─ $last_commit"
            fi
        done
    fi
    
    echo
    
    # 원격 브랜치 중 로컬에 없는 것들
    echo "📡 원격 전용 브랜치:"
    local remote_only=($(git branch -r --format='%(refname:short)' | sed 's/origin\///' | grep -v '^HEAD\|^main$\|^develop$'))
    local has_remote_only=false
    
    for remote_branch in "${remote_only[@]}"; do
        # 로컬에 해당 브랜치가 있는지 확인
        if ! git show-ref --verify --quiet "refs/heads/$remote_branch"; then
            # 타입 필터링
            if [ -n "$filter_type" ] && [[ ! $remote_branch =~ ^$filter_type/ ]]; then
                continue
            fi
            
            echo "    origin/$remote_branch"
            has_remote_only=true
        fi
    done
    
    if [ "$has_remote_only" = false ]; then
        echo "  (브랜치 없음)"
    fi
}

# 브랜치 정리
cleanup_branches() {
    local dry_run=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                echo -e "${RED}❌ 알 수 없는 옵션: $1${NC}"
                return 1
                ;;
        esac
    done
    
    echo -e "${BLUE}🧹 브랜치 정리 시작...${NC}"
    echo
    
    # 원격 저장소 정보 업데이트
    echo "📡 원격 저장소 정보 업데이트 중..."
    git fetch --prune
    
    # 병합된 브랜치 찾기
    local merged_branches=($(git branch --merged main | grep -v '^\*\|main\|develop' | xargs))
    
    if [ ${#merged_branches[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ 정리할 브랜치가 없습니다.${NC}"
        return 0
    fi
    
    echo "🔍 병합된 브랜치 발견:"
    for branch in "${merged_branches[@]}"; do
        echo "  - $branch"
    done
    
    if [ "$dry_run" = true ]; then
        echo -e "${YELLOW}🔍 Dry-run 모드: 실제로 삭제하지 않습니다.${NC}"
        echo "삭제될 브랜치: ${merged_branches[*]}"
        return 0
    fi
    
    echo
    read -p "이 브랜치들을 삭제하시겠습니까? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        for branch in "${merged_branches[@]}"; do
            echo "🗑️ 브랜치 삭제 중: $branch"
            if git branch -d "$branch"; then
                echo -e "${GREEN}  ✅ 삭제 완료: $branch${NC}"
            else
                echo -e "${RED}  ❌ 삭제 실패: $branch${NC}"
            fi
        done
        
        echo
        echo -e "${GREEN}🎉 브랜치 정리 완료!${NC}"
    else
        echo "브랜치 정리를 취소했습니다."
    fi
}

# 현재 브랜치 상태
show_status() {
    echo -e "${BLUE}📊 현재 브랜치 상태:${NC}"
    echo
    
    local current_branch=$(git branch --show-current)
    echo -e "${GREEN}📍 현재 브랜치: $current_branch${NC}"
    
    # 브랜치 타입 분석
    if [[ $current_branch =~ ^([^/]+)/ ]]; then
        local branch_type="${BASH_REMATCH[1]}"
        echo "   타입: $branch_type (${BRANCH_TYPES[$branch_type]:-알 수 없음})"
    fi
    
    # 커밋 상태
    echo
    echo "📈 커밋 상태:"
    
    # 원격 브랜치와 비교
    if git show-ref --verify --quiet "refs/remotes/origin/$current_branch"; then
        local ahead=$(git rev-list --count "origin/$current_branch..HEAD")
        local behind=$(git rev-list --count "HEAD..origin/$current_branch")
        
        echo "   원격 브랜치 대비:"
        echo "     앞선 커밋: $ahead개"
        echo "     뒤처진 커밋: $behind개"
        
        if [ $behind -gt 0 ]; then
            echo -e "${YELLOW}   ⚠️ git pull을 실행하여 최신 상태로 업데이트하세요.${NC}"
        fi
        
        if [ $ahead -gt 0 ]; then
            echo -e "${BLUE}   📤 git push로 변경사항을 원격 저장소에 반영하세요.${NC}"
        fi
    else
        echo "   원격 브랜치: 없음 (첫 푸시 필요)"
    fi
    
    # main 브랜치와 비교
    local ahead_main=$(git rev-list --count "main..HEAD")
    local behind_main=$(git rev-list --count "HEAD..main")
    
    echo "   main 브랜치 대비:"
    echo "     앞선 커밋: $ahead_main개"
    echo "     뒤처진 커밋: $behind_main개"
    
    # 작업 디렉터리 상태
    echo
    echo "📂 작업 디렉터리 상태:"
    
    local status_output=$(git status --porcelain)
    if [ -z "$status_output" ]; then
        echo -e "${GREEN}   ✅ 깨끗함 (변경사항 없음)${NC}"
    else
        echo "   변경된 파일:"
        while IFS= read -r line; do
            local status_char=${line:0:2}
            local file_name=${line:3}
            
            case $status_char in
                "M ")
                    echo -e "     ${YELLOW}M${NC} $file_name (수정됨, 스테이징됨)"
                    ;;
                " M")
                    echo -e "     ${RED}M${NC} $file_name (수정됨, 스테이징 안됨)"
                    ;;
                "A ")
                    echo -e "     ${GREEN}A${NC} $file_name (추가됨)"
                    ;;
                "??")
                    echo -e "     ${CYAN}?${NC} $file_name (추적되지 않음)"
                    ;;
                *)
                    echo "     $status_char $file_name"
                    ;;
            esac
        done <<< "$status_output"
    fi
    
    # 최근 커밋
    echo
    echo "📝 최근 커밋:"
    git log --oneline -3 | sed 's/^/     /'
}

# 메인 실행 로직
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    local command=$1
    shift
    
    case $command in
        create)
            create_branch "$@"
            ;;
        validate)
            if [ -n "$1" ]; then
                if [ -f "scripts/validate-branch-name.sh" ]; then
                    bash scripts/validate-branch-name.sh "$1"
                else
                    echo -e "${RED}❌ 브랜치명 검증 스크립트를 찾을 수 없습니다.${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}❌ 검증할 브랜치명을 입력해주세요.${NC}"
                exit 1
            fi
            ;;
        list)
            list_branches "$@"
            ;;
        cleanup)
            cleanup_branches "$@"
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 알 수 없는 명령어: $command${NC}"
            echo "도움말을 보려면: $0 help"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"

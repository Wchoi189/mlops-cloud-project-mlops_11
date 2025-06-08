#!/bin/bash
#
# TMDB 스케줄러 제어 스크립트
# 스케줄러 데몬의 시작, 중지, 재시작, 상태 확인을 담당
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DAEMON_SCRIPT="$PROJECT_ROOT/src/data_processing/scheduler_daemon.py"
PID_FILE="$PROJECT_ROOT/logs/scheduler_daemon.pid"
LOG_FILE="$PROJECT_ROOT/logs/scheduler_daemon.log"
STATUS_FILE="$PROJECT_ROOT/logs/scheduler_status.json"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 로그 출력
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 함수: PID 확인
get_scheduler_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE" 2>/dev/null
    else
        echo ""
    fi
}

# 함수: 프로세스 실행 여부 확인
is_scheduler_running() {
    local pid=$(get_scheduler_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0  # 실행 중
    else
        return 1  # 실행 중이 아님
    fi
}

# 함수: 스케줄러 시작
start_scheduler() {
    log_info "TMDB 스케줄러 시작 중..."
    
    # 이미 실행 중인지 확인
    if is_scheduler_running; then
        local pid=$(get_scheduler_pid)
        log_warn "스케줄러가 이미 실행 중입니다. (PID: $pid)"
        return 1
    fi
    
    # 로그 디렉토리 생성
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$PID_FILE")"
    
    # Python 가상환경 활성화 (있는 경우)
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        log_debug "Python 가상환경 활성화됨"
    fi
    
    # 환경변수 설정
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # 백그라운드에서 데몬 시작
    nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
    local daemon_pid=$!
    
    # 잠시 대기 후 실제 시작 여부 확인
    sleep 2
    
    if is_scheduler_running; then
        log_info "✅ 스케줄러가 성공적으로 시작되었습니다."
        log_info "   PID: $(get_scheduler_pid)"
        log_info "   로그 파일: $LOG_FILE"
        log_info "   상태 파일: $STATUS_FILE"
        return 0
    else
        log_error "❌ 스케줄러 시작에 실패했습니다."
        log_error "   로그를 확인하세요: $LOG_FILE"
        return 1
    fi
}

# 함수: 스케줄러 중지
stop_scheduler() {
    log_info "TMDB 스케줄러 중지 중..."
    
    local pid=$(get_scheduler_pid)
    
    if [ -z "$pid" ]; then
        log_warn "실행 중인 스케줄러를 찾을 수 없습니다."
        return 1
    fi
    
    # 우아한 종료 시도 (SIGTERM)
    log_debug "SIGTERM 신호 전송 (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null
    
    # 종료 대기 (최대 30초)
    local count=0
    while [ $count -lt 30 ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
        count=$((count + 1))
        if [ $((count % 5)) -eq 0 ]; then
            log_debug "종료 대기 중... ($count초)"
        fi
    done
    
    # 여전히 실행 중이면 강제 종료
    if kill -0 "$pid" 2>/dev/null; then
        log_warn "우아한 종료 실패, 강제 종료 시도..."
        kill -KILL "$pid" 2>/dev/null
        sleep 2
    fi
    
    # 최종 확인 및 정리
    if ! kill -0 "$pid" 2>/dev/null; then
        # PID 파일 정리
        if [ -f "$PID_FILE" ]; then
            rm -f "$PID_FILE"
        fi
        log_info "✅ 스케줄러가 중지되었습니다."
        return 0
    else
        log_error "❌ 스케줄러 중지에 실패했습니다."
        return 1
    fi
}

# 함수: 스케줄러 재시작
restart_scheduler() {
    log_info "TMDB 스케줄러 재시작 중..."
    
    if is_scheduler_running; then
        stop_scheduler
    fi
    
    sleep 2
    start_scheduler
}

# 함수: 스케줄러 상태 확인
status_scheduler() {
    echo "=== TMDB 스케줄러 상태 ==="
    
    local pid=$(get_scheduler_pid)
    
    if is_scheduler_running; then
        log_info "상태: ✅ 실행 중"
        log_info "PID: $pid"
        
        # 프로세스 정보
        if command -v ps >/dev/null 2>&1; then
            local ps_info=$(ps -p "$pid" -o pid,ppid,etime,pcpu,pmem,cmd --no-headers 2>/dev/null)
            if [ -n "$ps_info" ]; then
                echo "프로세스 정보:"
                echo "  PID   PPID  ELAPSED  %CPU %MEM COMMAND"
                echo "  $ps_info"
            fi
        fi
        
        # 상태 파일 정보
        if [ -f "$STATUS_FILE" ]; then
            echo ""
            echo "상세 상태:"
            if command -v jq >/dev/null 2>&1; then
                jq -r '. | "  상태: " + .status + "\n  메시지: " + .message + "\n  업타임: " + .uptime + "\n  메모리: " + (.memory_usage.rss_mb | tostring) + "MB (" + (.memory_usage.percent | tostring) + "%)\n  업데이트: " + .timestamp' "$STATUS_FILE" 2>/dev/null
            else
                cat "$STATUS_FILE" | head -10
            fi
        fi
        
        # 최근 로그
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "최근 로그 (마지막 5줄):"
            tail -5 "$LOG_FILE" | sed 's/^/  /'
        fi
        
    else
        log_warn "상태: ❌ 실행 중이 아님"
        
        # 좀비 PID 파일 정리
        if [ -f "$PID_FILE" ]; then
            log_debug "좀비 PID 파일 정리 중..."
            rm -f "$PID_FILE"
        fi
    fi
    
    echo ""
    echo "파일 위치:"
    echo "  PID 파일: $PID_FILE"
    echo "  로그 파일: $LOG_FILE"
    echo "  상태 파일: $STATUS_FILE"
}

# 함수: 로그 실시간 보기
logs_scheduler() {
    if [ ! -f "$LOG_FILE" ]; then
        log_error "로그 파일을 찾을 수 없습니다: $LOG_FILE"
        return 1
    fi
    
    log_info "로그 실시간 보기 (Ctrl+C로 종료):"
    echo "파일: $LOG_FILE"
    echo "==========================================="
    tail -f "$LOG_FILE"
}

# 함수: 설정 재로드
reload_scheduler() {
    local pid=$(get_scheduler_pid)
    
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        log_error "실행 중인 스케줄러를 찾을 수 없습니다."
        return 1
    fi
    
    log_info "설정 재로드 중..."
    kill -USR1 "$pid" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "✅ 설정 재로드 신호를 전송했습니다."
    else
        log_error "❌ 설정 재로드 신호 전송에 실패했습니다."
        return 1
    fi
}

# 함수: 통계 보고
stats_scheduler() {
    local pid=$(get_scheduler_pid)
    
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        log_error "실행 중인 스케줄러를 찾을 수 없습니다."
        return 1
    fi
    
    log_info "통계 보고 요청 중..."
    kill -USR2 "$pid" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "✅ 통계 보고 신호를 전송했습니다."
        log_info "   로그 파일에서 통계를 확인하세요: $LOG_FILE"
    else
        log_error "❌ 통계 보고 신호 전송에 실패했습니다."
        return 1
    fi
}

# 함수: 도움말 출력
show_help() {
    echo "TMDB 스케줄러 제어 스크립트"
    echo ""
    echo "사용법: $0 <command> [options]"
    echo ""
    echo "명령어:"
    echo "  start        스케줄러 시작"
    echo "  stop         스케줄러 중지"
    echo "  restart      스케줄러 재시작"
    echo "  status       스케줄러 상태 확인"
    echo "  logs         로그 실시간 보기"
    echo "  reload       설정 재로드"
    echo "  stats        통계 보고 요청"
    echo "  help         이 도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 start                 # 스케줄러 시작"
    echo "  $0 status                # 상태 확인"
    echo "  $0 logs                  # 로그 보기"
    echo "  $0 restart               # 재시작"
    echo ""
    echo "파일 위치:"
    echo "  스크립트: $DAEMON_SCRIPT"
    echo "  PID 파일: $PID_FILE"
    echo "  로그 파일: $LOG_FILE"
}

# 메인 로직
case "${1:-}" in
    start)
        start_scheduler
        ;;
    stop)
        stop_scheduler
        ;;
    restart)
        restart_scheduler
        ;;
    status)
        status_scheduler
        ;;
    logs)
        logs_scheduler
        ;;
    reload)
        reload_scheduler
        ;;
    stats)
        stats_scheduler
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        log_error "명령어가 필요합니다."
        echo ""
        show_help
        exit 1
        ;;
    *)
        log_error "알 수 없는 명령어: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit $?

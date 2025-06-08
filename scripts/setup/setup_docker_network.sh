#!/bin/bash

# =================================================================
# Docker 네트워크 설정 스크립트
# =================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 색상 없음

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_info "Docker 네트워크 설정 중..."

# mlops-network 존재 확인 및 생성
if ! docker network ls | grep -q "mlops-network"; then
    print_info "mlops-network 생성 중..."
    docker network create mlops-network
    print_success "mlops-network 생성 완료"
else
    print_success "mlops-network 이미 존재함"
fi

# 네트워크 상태 확인
docker network inspect mlops-network > /dev/null 2>&1 && {
    print_success "mlops-network 상태 확인 완료"
} || {
    print_warning "mlops-network 상태 확인 실패"
}

print_success "Docker 네트워크 설정 완료!"

#!/bin/bash

# Docker 환경에서 jq 설치 확인 및 설정 스크립트

echo "=== MLOps Docker 환경 설정 (jq 포함) ==="

# 1. Docker 상태 확인
echo "1. Docker 상태 확인..."
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker가 설치되지 않았습니다."
    exit 1
fi

if ! docker compose --version > /dev/null 2>&1; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    exit 1
fi

echo "✅ Docker 설치 확인 완료"

# 2. 기존 컨테이너 정리
echo "2. 기존 컨테이너 정리..."
docker compose down

# 3. Docker 이미지 재빌드 (jq 포함)
echo "3. Docker 이미지 재빌드 (jq 및 유틸리티 도구 포함)..."
docker compose build dev --no-cache

# 4. 컨테이너 시작
echo "4. 컨테이너 시작..."
docker compose up -d dev

# 5. 컨테이너 상태 확인
echo "5. 컨테이너 상태 확인..."
sleep 5
docker compose ps

# 6. jq 설치 확인
echo "6. jq 설치 확인..."
if docker exec mlops-dev jq --version > /dev/null 2>&1; then
    echo "✅ jq 설치 완료: $(docker exec mlops-dev jq --version)"
else
    echo "❌ jq가 설치되지 않았습니다. Dockerfile을 확인하세요."
    exit 1
fi

# 7. tree 명령어 확인
echo "7. tree 명령어 확인..."
if docker exec mlops-dev tree --version > /dev/null 2>&1; then
    echo "✅ tree 설치 완료"
else
    echo "⚠️ tree가 설치되지 않았습니다."
fi

# 8. 필수 디렉토리 확인
echo "8. 필수 디렉토리 확인..."
docker exec mlops-dev bash -c "
mkdir -p data/{raw,processed,backup,test,staging}
mkdir -p data/raw/movies/{daily,weekly,monthly,genre,trending}
mkdir -p logs/{app,data,error,performance,health}
mkdir -p reports
echo '✅ 디렉토리 구조 확인 완료'
"

# 9. Python 환경 확인
echo "9. Python 환경 확인..."
PYTHON_VERSION=$(docker exec mlops-dev python --version)
echo "✅ Python 버전: $PYTHON_VERSION"

# 10. 환경변수 파일 확인
echo "10. 환경변수 파일 확인..."
if docker exec mlops-dev test -f .env; then
    echo "✅ .env 파일 존재"
else
    echo "⚠️ .env 파일이 없습니다. .env.template을 복사하여 생성하세요."
    docker exec mlops-dev cp .env.template .env 2>/dev/null || echo "  .env.template도 없습니다."
fi

echo ""
echo "============================================================"
echo "🎉 Docker 환경 설정 완료!"
echo "============================================================"
echo ""
echo "다음 명령으로 테스트를 시작할 수 있습니다:"
echo "docker exec -it mlops-dev bash"
echo "cd /app"
echo "python src/data_processing/test_integration.py"
echo ""
echo "또는 jq를 사용한 JSON 분석:"
echo "docker exec mlops-dev ls reports/*.json | head -1 | xargs docker exec mlops-dev cat | docker exec -i mlops-dev jq '.summary'"

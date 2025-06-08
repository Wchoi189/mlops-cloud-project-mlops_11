#!/bin/bash

# Docker 환경변수 문제 해결 스크립트

echo "=== Docker 환경변수 문제 해결 ==="

# 1. 호스트 환경변수 확인
echo "1. 호스트 환경변수 확인..."
if [ -n "$TMDB_API_KEY" ]; then
    echo "⚠️ 호스트에 TMDB_API_KEY가 설정되어 있습니다: $TMDB_API_KEY"
    echo "이 값이 Docker 컨테이너로 전달될 수 있습니다."
else
    echo "✅ 호스트에 TMDB_API_KEY가 설정되어 있지 않습니다."
fi

# 2. Docker 컨테이너 재시작
echo "2. Docker 컨테이너 재시작..."
docker compose down
sleep 2
docker compose up -d dev

# 3. 컨테이너 상태 확인
echo "3. 컨테이너 상태 확인..."
sleep 3
docker compose ps

# 4. .env 파일 vs 환경변수 비교
echo "4. .env 파일 vs 환경변수 비교..."
echo "=== .env 파일의 API 키 ==="
docker exec mlops-dev bash -c "cat .env | grep TMDB_API_KEY"

echo "=== Docker 환경변수의 API 키 ==="
docker exec mlops-dev bash -c "echo \$TMDB_API_KEY"

# 5. 문제가 있다면 강제 해결
ENV_FILE_KEY=$(docker exec mlops-dev bash -c "cat .env | grep TMDB_API_KEY | cut -d'=' -f2")
DOCKER_ENV_KEY=$(docker exec mlops-dev bash -c "echo \$TMDB_API_KEY")

if [ "$ENV_FILE_KEY" != "$DOCKER_ENV_KEY" ]; then
    echo "❌ 환경변수 불일치 발견!"
    echo "강제 해결을 시도합니다..."
    
    # 강제 해결 방법
    docker exec mlops-dev bash -c "
    # 기존 환경변수 제거
    unset TMDB_API_KEY
    unset DB_PASSWORD
    
    # .env 파일에서 API 키 추출
    API_KEY=\$(grep '^TMDB_API_KEY=' .env | cut -d'=' -f2 | tr -d ' ')
    
    if [ -n '\$API_KEY' ] && [ '\$API_KEY' != 'your_tmdb_api_key_here' ]; then
        export TMDB_API_KEY=\$API_KEY
        echo '✅ API 키 강제 설정 완료:' \$TMDB_API_KEY
        
        # 테스트 실행
        cd /app
        python -c 'from src.data_processing.tmdb_api_connector import test_tmdb_connection; print(\"✅ API 연결 성공\" if test_tmdb_connection() else \"❌ API 연결 실패\")'
    else
        echo '❌ .env 파일에 올바른 API 키가 없습니다.'
    fi
    "
else
    echo "✅ 환경변수가 일치합니다!"
    
    # 연결 테스트
    docker exec mlops-dev python -c "
from src.data_processing.tmdb_api_connector import test_tmdb_connection
result = test_tmdb_connection()
print('✅ API 연결 성공' if result else '❌ API 연결 실패')
"
fi

echo ""
echo "=== 해결 완료 ==="
echo "이제 테스트를 실행할 수 있습니다:"
echo "docker exec -it mlops-dev bash"
echo "cd /app"
echo "python src/data_processing/test_integration.py"

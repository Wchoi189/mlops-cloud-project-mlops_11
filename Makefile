```makefile

# MLOps IMDB 프로젝트용 Docker 전용 Makefile
.PHONY: docker-help docker-build docker-run docker-stop docker-clean docker-logs docker-test

docker-help:
	@echo "🐳 MLOps IMDB 프로젝트 Docker 명령어"
	@echo "=========================================="
	@echo "  docker-build       모든 Docker 이미지 빌드"
	@echo "  docker-run         Docker Compose로 모든 서비스 시작"
	@echo "  docker-run-prod    프로덕션 서비스 시작"
	@echo "  docker-stop        실행 중인 모든 컨테이너 중지"
	@echo "  docker-clean       컨테이너, 이미지, 볼륨 정리"
	@echo "  docker-logs        모든 서비스의 로그 표시"
	@echo "  docker-test        Docker 컨테이너화 테스트 실행"
	@echo "  docker-train       컨테이너에서 훈련 실행"
	@echo ""
	@echo "📊 서비스 URL:"
	@echo "  API:           http://localhost:8000"
	@echo "  API 문서:      http://localhost:8000/docs"
	@echo "  MLflow:        http://localhost:5000"
	@echo ""

# 모든 Docker 이미지 빌드
docker-build:
	@echo "🔨 Docker 이미지 빌드 중..."
	cd docker && docker-compose build --no-cache

# 특정 이미지 빌드
docker-build-api:
	@echo "🔨 API 이미지 빌드 중..."
	cd docker && docker-compose build api

# 훈련과 함께 실행
docker-build-train:
	@echo "🔨 훈련 이미지 빌드 중..."
	cd docker && docker-compose build trainer

# 서비스 실행
docker-run:
	@echo "🚀 MLOps 서비스 시작 중..."
	cd docker && docker-compose up -d
	@echo "✅ 서비스가 시작되었습니다!"
	@echo "📊 API: http://localhost:8000"
	@echo "📊 MLflow: http://localhost:5000"

# 프로덕션 서비스 실행
docker-run-prod:
	@echo "🚀 프로덕션 서비스 시작 중..."
	cd docker && docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ 프로덕션 서비스가 시작되었습니다!"

# 훈련과 함께 실행
docker-run-train:
	@echo "🎯 훈련과 함께 서비스 시작 중..."
	cd docker && docker-compose --profile training up -d

# 서비스 중지
docker-stop:
	@echo "🛑 MLOps 서비스 중지 중..."
	cd docker && docker-compose down
	cd docker && docker-compose -f docker-compose.prod.yml down

# 정리 작업
docker-clean:
	@echo "🧹 Docker 리소스 정리 중..."
	cd docker && docker-compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ 정리가 완료되었습니다!"

docker-clean-all:
	@echo "🧹 Docker 리소스 전체 정리 중..."
	cd docker && docker-compose down --volumes --remove-orphans --rmi all
	docker system prune -af --volumes
	@echo "✅ 전체 정리가 완료되었습니다!"

# 로그
docker-logs:
	@echo "📋 서비스 로그 표시 중..."
	cd docker && docker-compose logs -f

docker-logs-api:
	@echo "📋 API 로그 표시 중..."
	cd docker && docker-compose logs -f api

docker-logs-mlflow:
	@echo "📋 MLflow 로그 표시 중..."
	cd docker && docker-compose logs -f mlflow

# 테스트
docker-test:
	@echo "🧪 Docker 컨테이너화 테스트 실행 중..."
	python scripts/tests/test_section5.py

docker-test-quick:
	@echo "🔧 빠른 Docker 테스트 실행 중..."
	python scripts/tests/test_section5.py --quick

# 훈련
docker-train:
	@echo "🎯 컨테이너에서 훈련 실행 중..."
	cd docker && docker-compose run --rm trainer

# 헬스 체크
docker-health:
	@echo "🏥 서비스 헬스 체크 중..."
	@echo "API 헬스:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API 응답 없음"
	@echo "\nMLflow 헬스:"
	@curl -s http://localhost:5000/health | python -m json.tool || echo "❌ MLflow 응답 없음"

# 개발 도우미
docker-shell-api:
	@echo "🐚 API 컨테이너에서 셸 열기..."
	cd docker && docker-compose exec api bash

docker-shell-train:
	@echo "🐚 훈련 컨테이너에서 셸 열기..."
	cd docker && docker-compose run --rm trainer bash

# 재빌드 및 재시작
docker-restart:
	@echo "🔄 서비스 재시작 중..."
	cd docker && docker-compose down
	cd docker && docker-compose up -d
	@echo "✅ 서비스가 재시작되었습니다!"

docker-rebuild:
	@echo "🔄 서비스 재빌드 및 재시작 중..."
	cd docker && docker-compose down
	cd docker && docker-compose build --no-cache
	cd docker && docker-compose up -d
	@echo "✅ 서비스가 재빌드되고 재시작되었습니다!"

# 상태 확인
docker-status:
	@echo "📊 Docker 서비스 상태:"
	cd docker && docker-compose ps
	@echo "\n🐳 Docker 시스템 정보:"
	docker system df
```

# 피처 스토어 테스트 가이드

## 📋 테스트 진행 순서

피처 스토어 시스템을 체계적으로 테스트하기 위한 단계별 가이드입니다.

---

## 🚀 시작하기

### 1단계: 사전 준비 (**필수**)
먼저 시스템 환경을 준비하고 Docker 환경을 설정해야 합니다.

📄 **[2.0-prerequisite-setup.md](./2.0-prerequisite-setup.md)**
- Docker 환경 확인
- 프로젝트 구조 검증
- 이미지 빌드 및 기본 서비스 시작
- 헬스체크 및 사전 검증

**🔧 빠른 시작 (자동화)**:
```cmd
# 프로젝트 루트에서 실행
.\setup-feature-store-prerequisites.bat
```

### 2단계: 환경 설정 테스트
Docker 환경에서 피처 스토어의 기본 환경을 검증합니다.

📄 **[2.1-environment-setup-testing.md](./2.1-environment-setup-testing.md)**
- 기본 서비스 연결 확인
- Python 환경 및 모듈 테스트
- 데이터베이스 기본 작업 검증
- 파일 시스템 권한 확인

### 3단계: 핵심 컴포넌트 테스트
피처 스토어의 핵심 기능들을 개별적으로 테스트합니다.

📄 **[2.2-core-component-testing.md](./2.2-core-component-testing.md)**
- 피처 엔지니어링 로직 테스트
- 피처 스토어 CRUD 작업 검증
- 파이프라인 기본 동작 확인
- 검증 시스템 테스트

### 4단계: API 통합 테스트
피처 스토어 API의 통합 기능을 테스트합니다.

📄 **[2.3-api-integration-testing.md](./2.3-api-integration-testing.md)**
- FastAPI 서버 기동 및 확인
- REST API 엔드포인트 테스트
- 데이터 플로우 통합 검증
- 에러 처리 및 예외 상황 테스트

### 5단계: 성능 테스트
시스템의 성능과 확장성을 평가합니다.

📄 **[2.4-performance-testing.md](./2.4-performance-testing.md)**
- 대용량 데이터 처리 성능
- 동시 요청 처리 능력
- 메모리 및 CPU 사용량 모니터링
- 병목 지점 식별

### 6단계: Feast 통합 테스트
Feast 피처 스토어와의 통합을 검증합니다.

📄 **[2.5-feast-integration-testing.md](./2.5-feast-integration-testing.md)**
- Feast 설정 및 초기화
- 피처 정의 및 등록
- 온라인/오프라인 스토어 테스트
- 피처 서빙 성능 검증

### 7단계: 모니터링 테스트
시스템 모니터링 및 알럿 기능을 검증합니다.

📄 **[2.6-monitoring-testing.md](./2.6-monitoring-testing.md)**
- 메트릭 수집 및 저장
- 알럿 규칙 및 임계값 테스트
- 대시보드 기능 확인
- 로그 수집 및 분석

### 8단계: 완전성 검증
전체 시스템의 통합성과 완전성을 최종 검증합니다.

📄 **[2.7-complete-verification-checklist.md](./2.7-complete-verification-checklist.md)**
- 종합 시나리오 테스트
- 데이터 일관성 검증
- 장애 복구 테스트
- 최종 체크리스트

---

## 📊 테스트 현황 추적

각 단계별 완료 상태를 추적하세요:

- [ ] **2.0** - 사전 준비 완료
- [ ] **2.1** - 환경 설정 테스트 통과
- [ ] **2.2** - 핵심 컴포넌트 테스트 통과  
- [ ] **2.3** - API 통합 테스트 통과
- [ ] **2.4** - 성능 테스트 통과
- [ ] **2.5** - Feast 통합 테스트 통과
- [ ] **2.6** - 모니터링 테스트 통과
- [ ] **2.7** - 완전성 검증 통과

---

## 🛠️ 유용한 명령어

### 일반적인 Docker 명령어
```cmd
# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f dev

# 컨테이너 접속
docker-compose exec dev bash

# 서비스 재시작
docker-compose restart dev

# 전체 환경 정리
docker-compose down -v
```

### 테스트 관련 명령어
```cmd
# Python 테스트 실행
docker-compose exec dev python -m pytest tests/

# 특정 모듈 테스트
docker-compose exec dev python -c "import module; module.test()"

# 성능 모니터링
docker stats

# 서비스 헬스체크
docker-compose exec dev python -c "import redis; print(redis.Redis(host='redis').ping())"
```

---

## 🔧 문제 해결

### 자주 발생하는 문제들

1. **Docker 이미지 빌드 실패**
   ```cmd
   # 캐시 없이 재빌드
   docker-compose build --no-cache dev
   ```

2. **서비스 시작 실패**
   ```cmd
   # 서비스 로그 확인
   docker-compose logs service_name
   
   # 강제 재생성
   docker-compose up -d --force-recreate
   ```

3. **포트 충돌**
   ```cmd
   # 포트 사용 현황 확인
   netstat -an | findstr "5432 6379 8001"
   
   # docker-compose.yml에서 포트 변경
   ```

4. **권한 문제**
   ```cmd
   # Windows에서 볼륨 권한 문제
   # Docker Desktop의 Settings > Resources > File Sharing 확인
   ```

### 완전 초기화 (문제가 계속될 때)
```cmd
# 주의: 모든 데이터가 삭제됩니다
docker-compose down -v
docker system prune -a -f
docker volume prune -f

# 처음부터 다시 시작
.\setup-feature-store-prerequisites.bat
```

---

## 📞 도움말

- 각 테스트 파일의 상단에 있는 개요를 먼저 읽어보세요
- 문제 발생 시 로그를 확인하고 문제 해결 섹션을 참조하세요
- 테스트는 순차적으로 진행하는 것을 권장합니다
- 각 단계별로 성공 기준을 만족하는지 확인하세요

**테스트 시작: [2.0-prerequisite-setup.md](./2.0-prerequisite-setup.md)부터 시작하세요!** 🚀

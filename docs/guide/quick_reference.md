```markdown
# 🚀 섹션 5 빠른 참조 카드

## ⚡ 즉시 시작 명령어

```bash
# 🎯 원클릭 배포
python scripts/docker_quick_start.py

# 🧪 빠른 테스트 (빌드 없이)
python scripts/tests/test_section5.py --quick

# 🔨 전체 테스트 (빌드 포함)
python scripts/tests/test_section5.py

# 🚀 수동 Docker Compose
cd docker && docker-compose up -d
```

## 📊 서비스 URL

| 서비스 | URL | 설명 |
|---------|-----|-------------|
| **API** | <http://localhost:8000> | FastAPI 서비스 |
| **API 문서** | <http://localhost:8000/docs> | Swagger 문서 |
| **상태 확인** | <http://localhost:8000/health> | 헬스 체크 |
| **MLflow** | <http://localhost:5000> | 실험 추적 UI |

## 🎨 향상된 라이브러리 데모

```bash
# 🔥 Fire CLI
python src/utils/enhanced.py predict --title="인셉션" --year=2010 --runtime=148

# 🐛 icecream 디버깅
python -c "from src.utils.enhanced import ic; ic('안녕 Docker!')"

# 📊 Rich 테이블
python src/utils/enhanced.py demo

# 📈 진행률 표시줄
python src/models/enhanced_trainer.py
```

## 🔧 필수 명령어

### Docker 관리

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 로그
docker-compose logs -f api

# 재빌드
docker-compose up --build -d

# 정리
docker-compose down --volumes --remove-orphans
```

### 향상된 Makefile

```bash
make -f Makefile.docker docker-run      # 서비스 시작
make -f Makefile.docker docker-logs     # 로그 보기
make -f Makefile.docker docker-health   # 상태 확인
make -f Makefile.docker docker-stop     # 서비스 중지
```

## 🧪 빠른 API 테스트

```bash
# 상태 확인
curl http://localhost:8000/health

# 모델 정보
curl http://localhost:8000/model/info

# 영화 예측
curl -X POST "http://localhost:8000/predict/movie" \
     -H "Content-Type: application/json" \
     -d '{"title":"다크 나이트","startYear":2008,"runtimeMinutes":152,"numVotes":2500000}'
```

## 🚨 문제 해결

| 문제 | 해결책 |
|---------|----------|
| 포트 8000 사용 중 | `lsof -i :8000` 후 `kill -9 PID` |
| Docker 빌드 실패 | `docker system prune -f` |
| 모델 로딩 안됨 | `ls -la models/` 확인 |
| 컨테이너 시작 안됨 | `docker-compose logs api` |

## 📦 설치

```bash
# 향상된 라이브러리 (선택사항이지만 권장)
pip install icecream tqdm fire rich

# 또는 전체 향상된 패키지
pip install -r requirements-enhanced.txt

# Docker (설치되지 않은 경우)
# Ubuntu: sudo apt-get install docker.io docker-compose
# macOS: brew install docker docker-compose
```

## ✅ 성공 체크리스트

- [ ] Docker 이미지가 성공적으로 빌드됨
- [ ] `docker-compose up -d`로 서비스 시작됨
- [ ] API가 <http://localhost:8000/health> 에서 응답함
- [ ] MLflow UI가 <http://localhost:5000> 에서 접근 가능함
- [ ] 영화 예측 API가 작동함
- [ ] 향상된 CLI 명령어가 작동함
- [ ] 모든 테스트 통과: `python scripts/tests/test_section5.py`

## 🎯 다음 단계

1. **섹션 5 검증**: 위의 모든 체크마크가 녹색 ✅
2. **섹션 6**: 모니터링 & CI/CD
3. **프로덕션**: 클라우드 배포
4. **최종 발표**: 6.10 (화) 14:00-19:00

---

**🐳 섹션 5 완료! Docker 컨테이너가 MLOps 파이프라인을 실행 중입니다!**
```

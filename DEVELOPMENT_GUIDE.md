# MLOps 프로젝트 빠른 시작 가이드

## 팀: mlops-cloud-project-mlops_11

---

## 🚀 빠른 설정 (5분)

### 1단계: 저장소 클론

```bash
# 팀 저장소 클론
git clone https://github.com/AIBootcamp13/mlops-cloud-project-mlops_11.git

# 프로젝트 디렉토리로 이동
cd mlops-cloud-project-mlops_11
```

### 1.5단계: 프로젝트 구조 설정 (자동화)

```bash
# 프로젝트 구조 설정 스크립트 실행
python setup_project.py

# 생성된 프로젝트 디렉토리로 이동
cd mlops-cloud-project-mlops_11

# 필수 파일 설정 실행 (설정파일, requirements 등 생성)
bash ../setup_essential_files.sh
```

### 2단계: Python 가상환경 설정

```bash
# Python 3.11로 가상환경 생성
python3.11 -m venv mlops-env

# python3.11이 없다면 python3 사용
python3 -m venv mlops-env

# 가상환경 활성화
source mlops-env/bin/activate

# Python 버전 확인 (3.11.x 여야 함)
python --version

# pip 업그레이드
pip install --upgrade pip
```

### 3단계: 의존성 설치

```bash
# 모든 필수 패키지 설치
pip install -r requirements.txt

# 설치 확인
python -c "import pandas, numpy, sklearn, fastapi, mlflow, evidently; print('✅ 모든 패키지가 성공적으로 설치되었습니다!')"
```

### 4단계: 설정 테스트

```bash
# API 서버 시작
uvicorn src.api.main:app --reload --port 8000

# 다른 터미널에서 API 테스트
curl http://localhost:8000
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "이 영화 정말 멋져요!"}'
```

---

## 📋 Requirements.txt 내용

```
# 데이터 사이언스 핵심
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.1.0
matplotlib>=3.5.0
seaborn>=0.11.0

# 자연어 처리
nltk>=3.7

# API 프레임워크
fastapi>=0.85.0
uvicorn>=0.18.0
python-multipart>=0.0.5

# MLOps
mlflow>=2.0.0

# 데이터 검증
pydantic>=1.10.0

# ML 모니터링 및 데이터 드리프트 감지
evidently>=0.4.0

# 데이터베이스 (SQLite 유틸리티)
sqlalchemy>=1.4.0
alembic>=1.8.0

# 추가 유틸리티
python-dotenv>=1.0.0
requests>=2.28.0
```

---

## 🗂️ 프로젝트 구조 (자동 생성)

```
mlops-cloud-project-mlops_11/
├── data/
│   ├── raw/                     # 원본 데이터셋
│   ├── processed/               # 정제된 처리 데이터
│   ├── external/                # 외부 데이터 소스
│   └── interim/                 # 중간 데이터 처리
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_loader.py       # 데이터 로딩 유틸리티
│   │   ├── preprocessing.py     # 데이터 전처리
│   │   └── feature_engineering.py # 피처 생성
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py             # 모델 훈련
│   │   ├── predict.py           # 모델 예측
│   │   ├── evaluate.py          # 모델 평가
│   │   └── model_registry.py    # 모델 버전 관리
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 애플리케이션
│   │   ├── schemas.py           # Pydantic 스키마
│   │   └── endpoints.py         # API 엔드포인트
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # 설정 관리
│       ├── logging.py           # 로깅 유틸리티
│       └── monitoring.py        # 모니터링 유틸리티
├── scripts/
│   ├── train_model.py           # 훈련 파이프라인
│   ├── evaluate_model.py        # 평가 파이프라인
│   ├── deploy_model.py          # 배포 파이프라인
│   └── data_pipeline.py         # 데이터 처리 파이프라인
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_development.ipynb
│   └── 04_model_evaluation.ipynb
├── tests/
│   ├── __init__.py
│   ├── test_data/               # 데이터 처리 테스트
│   ├── test_models/             # 모델 테스트
│   └── test_api/                # API 테스트
├── docker/
│   ├── Dockerfile.train         # 훈련 컨테이너
│   ├── Dockerfile.api           # API 컨테이너
│   └── docker-compose.yml       # 멀티 컨테이너 설정
├── configs/
│   ├── model_config.yaml        # 모델 설정
│   ├── data_config.yaml         # 데이터 설정
│   └── deployment_config.yaml   # 배포 설정
├── .github/
│   └── workflows/
│       ├── ci.yml               # 지속적 통합
│       └── cd.yml               # 지속적 배포
├── mlflow/                      # MLflow 아티팩트
├── models/                      # 저장된 모델 파일
├── logs/                        # 애플리케이션 로그
├── requirements.txt             # 프로덕션 의존성
├── requirements-dev.txt         # 개발 의존성
├── setup.py                     # 패키지 설정
├── Makefile                     # 공통 명령어
├── .gitignore                   # Git 무시 규칙
├── .dockerignore               # Docker 무시 규칙
└── README.md                    # 프로젝트 문서
```

---

## 💻 개발 워크플로우

### 일일 워크플로우

```bash
# 1. 가상환경 활성화
source mlops-env/bin/activate

# 2. 최신 변경사항 가져오기
git pull origin main

# 3. 새로운 의존성 설치
pip install -r requirements.txt

# 4. 개발 서버 시작
uvicorn src.api.main:app --reload --port 8000

# 5. 실험용 Jupyter 시작
jupyter lab --port 8888
```

### Git 워크플로우

```bash
# 1. 피처 브랜치 생성
git checkout -b feature/기능이름

# 2. 변경사항 커밋
git add .
git commit -m "feat: 변경사항 설명"

# 3. 피처 브랜치 푸시
git push origin feature/기능이름

# 4. GitHub에서 Pull Request 생성
# 5. 리뷰 후 main에 병합
```

---

## 🔧 공통 명령어

### 공통 명령어 (Makefile 사용)

```bash
# 의존성 설치
make install          # 프로덕션 의존성
make install-dev      # 개발 의존성

# 개발
make run-api          # FastAPI 서버 시작
make run-mlflow       # MLflow UI 시작
make test            # 테스트 실행
make lint            # 코드 품질 검사
make format          # 코드 포맷팅
make clean           # 캐시 파일 정리

# Docker
make docker-build    # Docker 이미지 빌드
make docker-run      # Docker 컨테이너 실행
```

### API 개발

```bash
# API 서버 시작
uvicorn src.api.main:app --reload --port 8000

# 백그라운드에서 API 시작
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# API 엔드포인트 테스트
curl http://localhost:8000                    # 루트 엔드포인트
curl http://localhost:8000/health            # 헬스 체크
curl http://localhost:8000/predictions/history  # 예측 기록 조회
```

### MLflow 추적

```bash
# MLflow UI 시작
mlflow ui --port 5000

# MLflow 접속: http://localhost:5000
```

### 데이터베이스 조작

```bash
# SQLite 데이터베이스 연결
sqlite3 database/mlops_imdb.db

# 테이블 조회
.tables

# 예측 테이블 조회
SELECT * FROM predictions LIMIT 5;

# SQLite 종료
.quit
```

---

## 🧪 설정 테스트

### 1. Python 환경 테스트

```bash
python -c "
import sys
print(f'Python 버전: {sys.version}')
print(f'Python 경로: {sys.executable}')
"
```

### 2. 모든 Import 테스트

```bash
python -c "
try:
    import pandas as pd
    import numpy as np
    import sklearn
    import fastapi
    import mlflow
    import evidently
    import sqlite3
    print('✅ 모든 핵심 패키지가 성공적으로 import되었습니다!')
    print(f'Pandas: {pd.__version__}')
    print(f'FastAPI: {fastapi.__version__}')
    print(f'MLflow: {mlflow.__version__}')
    print(f'Evidently: {evidently.__version__}')
except ImportError as e:
    print(f'❌ Import 오류: {e}')
"
```

### 3. API 기능 테스트

```bash
# API 시작
uvicorn src.api.main:app --port 8000 &
sleep 3

# 엔드포인트 테스트
echo "루트 엔드포인트 테스트:"
curl -s http://localhost:8000 | python -m json.tool

echo -e "\n\n예측 엔드포인트 테스트:"
curl -s -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "이 영화 정말 환상적이에요!"}' | python -m json.tool

echo -e "\n\n헬스 엔드포인트 테스트:"
curl -s http://localhost:8000/health | python -m json.tool

# API 중지
pkill -f uvicorn
```

---

## 🚨 문제 해결

### 자주 발생하는 문제 및 해결방법

#### 1. 가상환경 문제

```bash
# python3.11을 찾을 수 없는 경우
python3 -m venv mlops-env

# 권한 거부된 경우
sudo python3.11 -m venv mlops-env
sudo chown -R $USER:$USER mlops-env
```

#### 2. 패키지 설치 충돌

```bash
# pip 캐시 지우기
pip cache purge

# 캐시 없이 설치
pip install --no-cache-dir -r requirements.txt

# 충돌 확인을 위해 패키지를 하나씩 설치
pip install pandas numpy scikit-learn
pip install fastapi uvicorn
pip install mlflow evidently
```

#### 3. API가 시작되지 않는 경우

```bash
# 포트 사용 중인지 확인
lsof -i :8000

# 포트 8000을 사용하는 프로세스 종료
kill -9 $(lsof -t -i:8000)

# 다른 포트 사용
uvicorn src.api.main:app --port 8001
```

#### 4. 데이터베이스 문제

```bash
# 데이터베이스 디렉토리 생성
mkdir -p database

# SQLite 설치 확인
sqlite3 --version

# 데이터베이스 초기화
rm -f database/mlops_imdb.db
```

---

## 📚 유용한 자료

- **FastAPI 문서**: <https://fastapi.tiangolo.com/>
- **MLflow 문서**: <https://mlflow.org/docs/latest/index.html>
- **Evidently 문서**: <https://docs.evidentlyai.com/>
- **Pandas 문서**: <https://pandas.pydata.org/docs/>
- **Scikit-learn 문서**: <https://scikit-learn.org/stable/>

---

## 👥 팀 협업

### 코드 리뷰 체크리스트

- [ ] 코드가 프로젝트 구조를 따름
- [ ] 모든 테스트 통과
- [ ] 문서 업데이트됨
- [ ] 새로운 패키지 추가 시 requirements.txt 업데이트
- [ ] 민감한 데이터 커밋되지 않음
- [ ] API 엔드포인트 테스트됨

### 소통 방법

- 버그 리포트와 기능 요청은 GitHub Issues 사용
- 일반적인 질문은 GitHub Discussions 사용
- PR에서 팀원 태그하여 리뷰 요청
- 필요시 프로젝트 문서 업데이트

---

## 🎯 설정 후 다음 단계

1. **프로젝트 주제 선택**: 기상 예측, IMDB 평점, 또는 자유 주제
2. **데이터 파이프라인 설정**: 데이터 수집 및 전처리 생성
3. **ML 모델 구현**: 선택한 모델 훈련 및 검증
4. **모니터링 설정**: 데이터 드리프트 감지를 위한 Evidently 설정
5. **컨테이너화**: 배포를 위한 Docker 컨테이너 생성
6. **CI/CD 생성**: 자동화된 테스트 및 배포 설정

---

## 📊 Section 1: IMDb 데이터 파이프라인 구현 (Rating Prediction)

### 1.1 IMDb 데이터셋 다운로드 및 준비 (최소 구성)

#### 프로젝트 철학: MLOps 파이프라인 중심

- **목표**: 복잡한 ML 모델이 아닌 **MLOps 파이프라인 구축**에 집중
- **데이터**: 필수 2개 파일만 사용 (title.basics + title.ratings)
- **피처**: 간단하지만 효과적인 4-5개 피처로 제한
- **이유**: 팀 협업 용이성, 빠른 구현, 디버깅 단순화

#### Step 1: 데이터 로더 구현

`src/data/data_loader.py` 파일 생성:

#### Step 2: 데이터 검증 스크립트

`scripts/validate_data.py` 파일 생성:

#### Step 3: 실행 명령어

```bash
# 1. 추가 의존성 설치
pip install requests

# 2. 데이터 다운로드 및 처리
python -c "from src.data.data_loader import IMDbDataLoader; loader = IMDbDataLoader(); movies_df = loader.create_movie_dataset()"

# 3. 데이터 검증
python scripts/validate_data.py
```

#### 예상 결과

- `data/raw/` 폴더에 2개 압축 파일 다운로드
- `data/processed/movies_with_ratings.csv` 생성
- 약 10,000-30,000개 영화 데이터 (품질 필터링 후)
- 4-5개 핵심 피처 (title, year, genre, rating, votes)

---

## 📊 Section 2: Data Preprocessing Pipeline

✅ Step 1: Create the preprocessing module # Create src/data/preprocessing.py
✅ Step 2: Create the test script # Create scripts/test_preprocessing.py
✅ Step 3: Run the preprocessing pipeline

# 1. 전처리 파이프라인 실행

bash

# Using single quotes to avoid bash interpretation

python -c 'from src.data.preprocessing import IMDbPreprocessor; p = IMDbPreprocessor(); df = p.load_data(); X, y, features = p.fit_transform(df); p.save_preprocessor(); print("전처리 완료!")'

# 2. 전처리 파이프라인 테스트

python scripts/test_preprocessing.py
---

*즐거운 코딩하세요! 🚀*

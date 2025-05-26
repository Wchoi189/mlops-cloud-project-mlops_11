
# MLOps를 구성하는 3가지 핵심 파이프라인: 도구 및 툴 상세 정리

좋습니다. **MLOps를 구성하는 3가지 핵심 파이프라인**에 대해, 각 단계에서 사용할 수 있는 도구와 툴들을 **아주 자세히, 목적별로** 정리해드리겠습니다.

---

## ✅ 1. 데이터 파이프라인 (Data Pipeline)

### 📥 수집 (Ingestion)

| 도구 | 설명 |
|------|------|
| **Apache Kafka** | 실시간 데이터 스트리밍 수집에 최적화 |
| **Apache NiFi** | GUI 기반의 데이터 흐름 설계 및 연결 |
| **Fluentd / Logstash** | 로그 기반 데이터 수집 |
| **Airbyte** | 다양한 소스(DB, API) 연결 가능한 오픈소스 ELT |
| **Google Cloud Dataflow** | GCP의 데이터 스트리밍 및 배치 수집 서비스 |

### 🧼 전처리 및 정제 (Cleaning, ETL)

| 도구 | 설명 |
|------|------|
| **Apache Spark** | 대용량 분산 데이터 처리 |
| **dbt (Data Build Tool)** | SQL 기반의 데이터 변환 자동화 및 버전 관리 |
| **Pandas / Dask** | 소규모 또는 병렬 전처리용 파이썬 기반 라이브러리 |
| **Great Expectations** | 데이터 품질 검사 및 validation 자동화 |

### 📦 저장 (Storage)

| 도구 | 설명 |
|------|------|
| **Amazon S3 / Google Cloud Storage** | 비정형 데이터 저장용 데이터 레이크 |
| **Delta Lake / Apache Hudi / Iceberg** | 버저닝 및 ACID 트랜잭션이 가능한 확장형 저장소 |
| **PostgreSQL / MySQL** | 정형 데이터 저장 |
| **MongoDB / Elasticsearch** | NoSQL 및 검색용 저장소 |

### 🔃 오케스트레이션 및 스케줄링

| 도구 | 설명 |
|------|------|
| **Apache Airflow** | DAG 기반 작업 흐름 스케줄링 및 모니터링 |
| **Prefect / Dagster** | 파이썬 친화적이고 에러 처리가 강력한 워크플로우 툴 |

---

## ✅ 2. 모델 훈련 파이프라인 (Model Training Pipeline)

### 🧠 학습 스크립트 실행 및 환경 관리

| 도구 | 설명 |
|------|------|
| **Docker** | 환경 일관성을 위한 컨테이너 기반 학습 실행 |
| **Kubernetes** | 대규모 분산 학습 환경 관리 |
| **Conda / Poetry / venv** | 파이썬 패키지 및 환경 관리 |
| **SageMaker / Vertex AI / Azure ML** | 클라우드 기반 ML 학습 및 배포 서비스 통합 제공 |

### 🔧 하이퍼파라미터 튜닝 (AutoML 포함)

| 도구 | 설명 |
|------|------|
| **Optuna** | 빠르고 직관적인 하이퍼파라미터 튜닝 프레임워크 |
| **Ray Tune** | 분산 튜닝 및 스케일아웃 |
| **KerasTuner / Scikit-Optimize** | 사용이 간단한 튜닝 도구 |
| **Google Vizier / SageMaker Hyperparameter Tuner** | 클라우드 자동화 튜닝 지원 |

### 🧪 실험 추적 (Experiment Tracking)

| 도구 | 설명 |
|------|------|
| **MLflow** | 실험 로깅, 모델 저장, 메트릭 추적 등 All-in-One |
| **Weights & Biases (W&B)** | GUI 기반 실험 추적 및 팀 협업 기능 탁월 |
| **Comet ML / Neptune.ai** | 유사한 기능을 제공하는 대체 실험 관리 도구 |

### 💾 모델 아티팩트 저장 (Model Registry)

| 도구 | 설명 |
|------|------|
| **MLflow Model Registry** | 모델 버전 관리 및 stage(Production/Staging) 관리 |
| **SageMaker Model Registry** | AWS에서 자동 통합되는 모델 저장소 |
| **DVC** | 모델 파일 및 데이터 버전 관리에 유리한 Git 연동 툴 |
| **LakeFS** | 데이터 및 모델 파일의 Git-like 버전 관리 시스템 |

---

## ✅ 3. 배포 및 서빙 파이프라인 (Deployment & Serving Pipeline)

### 🚀 API/모델 서빙

| 도구 | 설명 |
|------|------|
| **FastAPI / Flask** | 모델을 REST API로 제공 |
| **BentoML** | 모델 패키징 + REST API + Docker 빌드 자동화 |
| **TorchServe / TensorFlow Serving** | 프레임워크에 최적화된 서빙 솔루션 |
| **KServe (ex-KFServing)** | Kubernetes 기반 고급 서빙 솔루션 (자동 스케일링, Canary 지원) |
| **Triton Inference Server (NVIDIA)** | GPU 최적화 고속 추론 서버 |

### 🔁 CI/CD (지속적 배포 자동화)

| 도구 | 설명 |
|------|------|
| **GitHub Actions / GitLab CI** | 모델 빌드 → 테스트 → 배포 자동화 |
| **Jenkins** | 유연하지만 설정이 복잡한 파이프라인 도구 |
| **ArgoCD / FluxCD** | Kubernetes용 GitOps 기반 CD 도구 |
| **MLflow + Airflow 연동** | 실험 후 모델 자동 배포 설정 가능 |

### 🩺 모니터링 및 재학습

| 도구 | 설명 |
|------|------|
| **Prometheus + Grafana** | 성능/상태 모니터링 및 시각화 |
| **Evidently AI** | 입력 데이터 및 예측 결과의 분포 변화 감지 (드리프트 탐지) |
| **WhyLogs / Arize AI / Fiddler** | ML 모델 모니터링 전문 SaaS 도구 |
| **Seldon Alibi Detect** | 이상 탐지 및 데이터 드리프트 오픈소스 프레임워크 |

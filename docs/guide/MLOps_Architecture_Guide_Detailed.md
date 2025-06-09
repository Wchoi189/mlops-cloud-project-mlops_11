
# MLOps 아키텍처 가이드: 구성 요소 및 도구 상세 설명

이 문서는 다양한 아키텍처 다이어그램과 함께, MLOps를 구성하는 핵심 파이프라인과 각 단계별 대표 도구를 통합적으로 정리한 가이드입니다.

---

## 🔁 MLOps 전체 흐름 요약

```
[Data Pipeline] → [Feature Store] → [Experiment] → [Source Repo]
                 ↓                  ↓
            [Metadata Store]     [CI/CD]
                                   ↓
                        [Model Registry] → [Serving] → [Prediction]
                        ↑
                   [Evaluation] ← [Training]
```

각 구성 요소는 다양한 오픈소스 및 클라우드 도구로 구축 가능하며, 주요 범주는 아래와 같습니다:

---

## 1️⃣ 데이터 파이프라인 (Data Pipeline)

### 주요 구성 요소

- **Data Ingestion**: Kafka, RabbitMQ, Amazon SQS, Google Pub/Sub, Azure Service Bus
- **Batch/Streaming 처리**: Apache Spark, Hadoop, Flink
- **ETL 자동화**: Airflow, Prefect, Argo Workflows
- **저장소**: S3, MinIO, HDFS, PostgreSQL

### 관련 도구 예시

- Kafka, Spark, Airflow, S3, MinIO

---

## 2️⃣ Feature Store

### 역할

- 반복 재사용 가능한 피처를 관리
- 실시간/배치 피처 제공

### 대표 도구

- **Feast** (오픈소스 피처 저장소)
- **Hopsworks**, **Tecton**, **SageMaker Feature Store**

---

## 3️⃣ 실험 오케스트레이션 (Experiment Orchestration)

### 역할

- 실험 관리, 재현 가능한 워크플로우 실행

### 대표 도구

- **Kubeflow Pipelines**: Kubernetes 기반
- **MLflow**: 실험 추적, 모델 저장소, 서빙 연동
- **Argo Workflows / Prefect**: 워크플로우 기반 오케스트레이션

---

## 4️⃣ 모델 학습 파이프라인 (Model Training)

### 단계 구성

- **Data Extraction / Validation / Preparation**
- **Training / Evaluation / Validation**

### 자동화 도구

- MLflow Tracking
- DVC, Metaflow, SageMaker Pipelines
- **Metadata 관리**: ML Metadata Store

---

## 5️⃣ 모델 저장소 (Model Registry)

### 기능

- 학습된 모델 버전 관리
- Production/Staging 구분

### 도구

- MLflow Model Registry
- SageMaker Model Registry
- TensorFlow Model Registry

---

## 6️⃣ 서빙 및 배포 (Serving & Deployment)

### 서빙 기술

- REST API: FastAPI, Flask
- 모델 서빙 프레임워크: BentoML, TorchServe, KServe, Triton

### 배포 자동화 (CI/CD)

- GitHub Actions, GitLab CI, Jenkins, ArgoCD, CircleCI
- 패키징: Docker, Helm, K8s

---

## 7️⃣ 성능 모니터링 및 재학습 트리거

### 주요 도구

- **Prometheus + Grafana**: 리소스 모니터링
- **Evidently AI / WhyLogs**: 데이터 드리프트 감지
- **WandB / TensorBoard / ELK / EFK 스택**: 실험 추적, 시각화

---

## ✅ 통합 도구 매핑

| 범주 | 대표 도구 |
|------|-----------|
| 수집 / 스트리밍 | Kafka, RabbitMQ, Pub/Sub |
| 처리 / ETL | Spark, Airflow, dbt |
| 피처 저장소 | Feast, Tecton, SageMaker FS |
| 실험 관리 | MLflow, Kubeflow, Prefect |
| 학습 파이프라인 | Metaflow, MLflow, SageMaker |
| 서빙 | BentoML, Triton, KServe |
| CI/CD | GitHub Actions, ArgoCD |
| 모니터링 | Prometheus, Grafana, Evidently AI |

---

## 📌 참고 아키텍처 다이어그램 요약

1. **전체 파이프라인 개요**: 데이터 수집 → 학습 → 서빙 → 예측 순서
2. **각 구성 요소별 도구 명시 다이어그램**:
    - 데이터 흐름은 고정 구조, 도구는 교체 가능 모듈로 표현
    - 예: Feature Store에 S3/MinIO, Serving에 Triton/KServe 등 대체 가능

---

필요에 따라 각 도구의 설치 방법, 실습 예제도 문서에 포함할 수 있습니다.

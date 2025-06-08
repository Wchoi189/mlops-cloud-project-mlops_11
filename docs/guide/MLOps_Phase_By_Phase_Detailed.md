
# MLOps 아키텍처 가이드 (단계별 상세 설명)

---

## ✅ 1단계: 데이터 파이프라인 (Data Pipeline)

### 📌 목적

- 원천 데이터 수집 → 정제 → 가공 → 저장까지 전처리 흐름 구축

### 🔨 주요 작업

- 데이터 수집 (Batch / Stream)
- 전처리, 정제 및 저장

### 🧰 대표 도구

- 스트리밍: Kafka, RabbitMQ, SQS, Pub/Sub
- ETL: Spark, Beam, dbt
- 스케줄링: Airflow, Prefect, Argo Workflows
- 저장소: S3, MinIO, HDFS

---

## ✅ 2단계: 피처 저장소 (Feature Store)

### 📌 목적

- 모델 학습/서빙에 일관된 피처 제공

### 🔨 주요 작업

- 피처 등록 및 버전 관리
- 오프라인/온라인 피처 제공

### 🧰 대표 도구

- Feast, Tecton, Hopsworks, SageMaker Feature Store

---

## ✅ 3단계: 실험 오케스트레이션 (Experiment Orchestration)

### 📌 목적

- 실험 자동화 및 재현성 확보

### 🔨 주요 작업

- 파이프라인 구성
- 실험 추적 및 비교

### 🧰 대표 도구

- MLflow, Kubeflow Pipelines, Argo Workflows, Prefect

---

## ✅ 4단계: 모델 학습 파이프라인 (Training Pipeline)

### 📌 목적

- 학습 및 평가 자동화

### 🔨 주요 작업

- 데이터 추출, 검증, 학습, 튜닝, 평가

### 🧰 주요 도구

- Training: PyTorch, TensorFlow, Scikit-learn
- Tuning: Optuna, Ray Tune
- Validation: Great Expectations
- Metadata: ML Metadata Store, Neptune.ai

---

## ✅ 5단계: 모델 저장소 (Model Registry)

### 📌 목적

- 모델 버전 관리 및 배포 상태 추적

### 🔨 주요 작업

- 모델 등록, promotion 관리

### 🧰 대표 도구

- MLflow Registry, SageMaker Model Registry, DVC

---

## ✅ 6단계: 서빙 및 배포 (Serving & Deployment)

### 📌 목적

- 모델을 API로 배포 및 스케일링

### 🔨 주요 작업

- REST API 제공, 배포 자동화, 스케일링

### 🧰 대표 도구

- Serving: FastAPI, BentoML, TorchServe, KServe, Triton
- CI/CD: GitHub Actions, GitLab CI, Jenkins, ArgoCD

---

## ✅ 7단계: 성능 모니터링 및 재학습 (Monitoring & Retraining)

### 📌 목적

- 모델 상태 모니터링 및 품질 유지

### 🔨 주요 작업

- 모니터링, 드리프트 감지, 로그 분석

### 🧰 대표 도구

- Monitoring: Prometheus, Grafana
- Drift Detection: Evidently AI, WhyLogs
- Visualization: TensorBoard, WandB
- Logging: ELK, EFK Stack

---

## 📌 전체 구성 요약

| 단계 | 주요 도구 |
|------|-----------|
| 수집 | Kafka, Airbyte, Spark |
| 피처 저장 | Feast, Tecton |
| 실험 관리 | MLflow, Kubeflow |
| 학습 | PyTorch, TensorFlow, Optuna |
| 레지스트리 | MLflow Registry, SageMaker |
| 서빙 | KServe, BentoML, Triton |
| 모니터링 | Prometheus, Grafana, Evidently |

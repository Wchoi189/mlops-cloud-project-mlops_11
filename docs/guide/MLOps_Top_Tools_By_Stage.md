
# MLOps 7단계별 대표 도구 TOP 3 및 공통 도구

---

## ✅ MLOps 7단계별 대표 도구 TOP 3

| 단계 | TOP 1 | TOP 2 | TOP 3 |
|------|-------|-------|-------|
| **1. 데이터 파이프라인** | **Apache Airflow** (스케줄링/ETL) | **Apache Kafka** (실시간 수집) | **Apache Spark** (대용량 처리) |
| **2. 피처 저장소** | **Feast** (오픈소스 표준) | **Tecton** (엔터프라이즈 실시간) | **SageMaker Feature Store** (AWS 통합형) |
| **3. 실험 오케스트레이션** | **Kubeflow Pipelines** (K8s 기반 파이프라인) | **MLflow** (실험 기록 & 추적) | **Argo Workflows** (YAML 기반 GitOps) |
| **4. 모델 학습 파이프라인** | **PyTorch** (유연성 + 연구용) | **TensorFlow** (산업계 채택 높음) | **Scikit-learn** (클래식 ML 학습용) |
| **5. 모델 저장소** | **MLflow Registry** (가장 대중적 오픈소스) | **SageMaker Model Registry** | **DVC** (Git 기반 모델 버전 관리) |
| **6. 모델 서빙 및 배포** | **KServe** (Kubernetes-native 서빙) | **BentoML** (API+패키징 통합) | **Triton Inference Server** (GPU 최적화) |
| **7. 성능 모니터링 및 재학습** | **Prometheus + Grafana** (모니터링 시각화) | **Evidently AI** (드리프트 감지) | **WandB** (실험 & 예측 추적, 시각화) |

---

## 🔁 공통적으로 사용되는 MLOps 도구 (전 단계에서 자주 사용됨)

| 도구 | 역할 |
|------|------|
| **Docker** | 모든 파이프라인 단계에서 환경 일관성 보장 |
| **Kubernetes** | 서빙/오케스트레이션/스케일링에 핵심 |
| **MLflow** | 실험 관리 + 모델 추적 + 서빙까지 통합 사용 가능 |
| **Git** (GitHub, GitLab 등) | 코드/모델 버전 관리 및 CI/CD 연동 |
| **Jupyter Notebook** | 실험, 학습, 검증 단계에서 데이터 탐색용 UI로 널리 활용 |

---

## 📌 요약

- **Airflow, MLflow, Docker, Kubernetes, Git**은 거의 모든 MLOps 프로젝트에서 사용됨
- 각 단계별로 **전문 특화 도구**를 골라 구성하되, 도구 간 호환성과 팀 경험 고려가 중요
- 특히 **Kubeflow + MLflow + KServe** 조합은 오픈소스 기반 통합 구성으로 매우 인기

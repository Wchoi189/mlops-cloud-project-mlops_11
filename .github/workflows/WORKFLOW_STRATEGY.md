# MLOps Git 워크플로우 전략

## 🎯 워크플로우 전략 비교

| 특징 | GitHub Flow | GitFlow |
|------|-------------|---------|
| **복잡도** | 단순 | 복잡 |
| **브랜치 수** | 적음 (main + feature) | 많음 (main, develop, feature, release, hotfix) |
| **릴리스 주기** | 지속적 배포 | 정기 릴리스 |
| **팀 크기** | 소규모 ~ 중규모 | 대규모 |
| **학습 난이도** | 쉬움 | 어려움 |
| **MLOps 적합성** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **WSL Docker 최적화** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🎯 MLOps 프로젝트에 GitHub Flow 선택 이유

### 1. MLOps 특성과의 조화
- **지속적 실험**: 데이터 과학 실험의 빠른 반복
- **빠른 프로토타이핑**: 모델 개발 및 테스트 주기
- **데이터 버전 관리**: 간단한 브랜치 구조로 데이터 추적 용이
- **컨테이너 기반**: Docker 환경에서의 빠른 배포

### 2. WSL + Docker 환경 최적화
- **경량화**: WSL 환경에서 빠른 브랜치 작업
- **컨테이너 호환성**: Docker 볼륨 마운트와 호환
- **개발 효율성**: 복잡한 브랜치 관리 오버헤드 최소화

## 🌿 MLOps 브랜치 전략

### 장기 브랜치 (Long-running)

**main 브랜치**
- 프로덕션 배포 브랜치
- 항상 안정적이고 배포 가능한 상태 유지
- 직접 push 금지 (WSL hook으로 강제)
- PR을 통해서만 병합 허용
- Docker 이미지 자동 빌드 트리거

### 단기 브랜치 (Short-lived)

**MLOps 9단계별 기능 개발 브랜치**
- `feature/stage1-data-pipeline`
- `feature/stage2-feature-store`
- `feature/stage3-version-control`
- `feature/stage4-cicd-pipeline`
- `feature/stage5-model-serving`
- `feature/stage6-monitoring`
- `feature/stage7-security`
- `feature/stage8-governance`
- `feature/stage9-event-driven`

**ML 실험 브랜치**
- `experiment/new-ml-algorithm`
- `experiment/hyperparameter-tuning`
- `experiment/feature-engineering`
- `experiment/model-comparison`

**버그 수정 브랜치**
- `bugfix/123-memory-leak`
- `bugfix/456-api-timeout`
- `bugfix/789-data-validation`

**긴급 수정 브랜치**
- `hotfix/security-vulnerability`
- `hotfix/data-corruption`
- `hotfix/model-performance`

**문서화 브랜치**
- `docs/api-documentation`
- `docs/deployment-guide`
- `docs/architecture-update`

### 수동 검사
- **기능 테스트**: Docker 환경에서 테스트
- **통합 테스트**: MLOps 파이프라인 전체 검증
- **문서 업데이트**: README 및 가이드 업데이트

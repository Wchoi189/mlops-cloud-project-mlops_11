# 🌿 브랜치 전략 설정 및 테스트

Movie MLOps 프로젝트의 브랜치 전략 구현과 테스트 시스템입니다.

## 📋 개요

이 구현은 **3.2 브랜치 전략 설정**에서 요구하는 모든 기능을 포함합니다:

- ✅ 브랜치 명명 규칙 검증 스크립트
- ✅ Git Hook 자동화 (Pre-push 검증)
- ✅ 브랜치 관리 도구
- ✅ 포괄적인 테스트 시스템
- ✅ MLOps 특화 브랜치 타입 지원

## 🏗️ 구조

```
scripts/
├── validate-branch-name.sh      # 브랜치명 검증 스크립트
├── install-git-hooks.sh         # Git Hook 설치 스크립트
├── branch-manager.sh            # 브랜치 관리 도구
└── git-hooks/
    └── pre-push                 # Pre-push Hook

tests/branch_strategy/
├── test_branch_naming.py        # Python 테스트 스크립트
└── run_branch_strategy_tests.sh # 종합 테스트 스크립트
```

## 🚀 빠른 시작

### 1. 전체 시스템 테스트

```bash
# 프로젝트 루트에서 실행
cd /mnt/c/dev/movie-mlops

# 종합 테스트 실행
bash tests/branch_strategy/run_branch_strategy_tests.sh
```

### 2. Git Hook 설치

```bash
# Git Hook 설치
bash scripts/install-git-hooks.sh
```

### 3. 브랜치 생성 (대화형)

```bash
# 브랜치 관리 도구 사용
bash scripts/branch-manager.sh create -i
```

## 🎯 브랜치 명명 규칙

### 지원되는 브랜치 타입

| 타입 | 설명 | 예시 |
|------|------|------|
| `feature/` | 새로운 기능 개발 | `feature/tmdb-api-integration` |
| `bugfix/` | 버그 수정 | `bugfix/data-validation-error` |
| `hotfix/` | 긴급 수정 | `hotfix/critical-security-patch` |
| `experiment/` | 실험적 기능 | `experiment/new-ml-algorithm` |
| `docs/` | 문서 작업 | `docs/api-documentation` |
| `data/` | 데이터 관련 작업 | `data/collection-pipeline` |
| `model/` | 모델 관련 작업 | `model/training-pipeline` |
| `pipeline/` | 파이프라인 작업 | `pipeline/airflow-setup` |
| `infra/` | 인프라 작업 | `infra/docker-optimization` |

### 명명 규칙

- **형식**: `<타입>/<설명>`
- **길이**: 최대 50자
- **문자**: 영문 소문자, 숫자, 하이픈(-), 슬래시(/) 만 사용
- **금지**: 대문자, 공백, 특수문자, 연속된 하이픈

### 올바른 예시

```bash
✅ feature/tmdb-api-integration
✅ bugfix/memory-leak-preprocessing
✅ data/collection-automation
✅ model/recommendation-training
✅ pipeline/airflow-dag-setup
✅ infra/monitoring-setup
```

### 잘못된 예시

```bash
❌ Feature/TmdbApiIntegration    # 대문자 사용
❌ fix-bug                      # 타입 없음
❌ feature/with spaces          # 공백 포함
❌ main                         # 보호된 브랜치
❌ feature/very-long-branch-name-that-exceeds-fifty-chars  # 너무 긴 이름
```

## 🔧 도구 사용법

### 1. 브랜치명 검증

```bash
# 단일 브랜치명 검증
bash scripts/validate-branch-name.sh "feature/new-api"

# 현재 브랜치 검증
bash scripts/validate-branch-name.sh $(git branch --show-current)
```

### 2. 브랜치 관리

```bash
# 도움말
bash scripts/branch-manager.sh help

# 대화형 브랜치 생성
bash scripts/branch-manager.sh create -i

# 빠른 브랜치 생성
bash scripts/branch-manager.sh create -t feature -d "new-feature"

# 브랜치 목록 조회
bash scripts/branch-manager.sh list

# 현재 브랜치 상태
bash scripts/branch-manager.sh status

# 완료된 브랜치 정리
bash scripts/branch-manager.sh cleanup --dry-run
```

### 3. Git Hook 관리

```bash
# Hook 설치
bash scripts/install-git-hooks.sh

# Hook 일시 비활성화
git push --no-verify

# Hook 제거
rm .git/hooks/pre-push
```

## 🧪 테스트 시스템

### 개별 테스트

```bash
# Python 브랜치명 테스트
python tests/branch_strategy/test_branch_naming.py

# Bash 스크립트 개별 테스트
bash scripts/validate-branch-name.sh "test-branch-name"
```

### 종합 테스트

```bash
# 전체 브랜치 전략 테스트
bash tests/branch_strategy/run_branch_strategy_tests.sh

# 상세 로그와 함께 테스트
bash tests/branch_strategy/run_branch_strategy_tests.sh 2>&1 | tee test.log
```

### 테스트 항목

1. **스크립트 존재 확인** - 필수 스크립트 파일들이 존재하는지 확인
2. **실행 권한 확인** - 스크립트들이 실행 가능한지 확인
3. **브랜치명 검증** - 올바른/잘못된 브랜치명 패턴 테스트
4. **Git 설정 확인** - Git 설치, 저장소, 사용자 설정 확인
5. **브랜치 관리 도구** - 브랜치 관리 스크립트 기능 테스트
6. **Git Hook 시스템** - Hook 설치 및 실행 환경 확인
7. **Python 테스트** - 상세한 브랜치명 패턴 검증

## 🔄 워크플로우 예시

### 새 기능 개발

```bash
# 1. 새 브랜치 생성 (대화형)
bash scripts/branch-manager.sh create -i
# 또는 직접 지정
bash scripts/branch-manager.sh create -t feature -d "tmdb-api-integration"

# 2. 작업 진행
# ... 코드 수정 ...

# 3. 커밋 (Conventional Commits 스타일 권장)
git add .
git commit -m "feat(api): add TMDB movie data collection endpoint"

# 4. 푸시 (pre-push hook 자동 실행)
git push -u origin feature/tmdb-api-integration
```

### 브랜치 정리

```bash
# 1. 병합된 브랜치 확인
bash scripts/branch-manager.sh cleanup --dry-run

# 2. 실제 정리 실행
bash scripts/branch-manager.sh cleanup
```

## 🎨 Git Hook 동작

Pre-push Hook이 다음을 자동으로 검증합니다:

1. **브랜치명 검증** - 명명 규칙 준수 확인
2. **보호된 브랜치** - main, develop 등 직접 푸시 방지
3. **커밋 메시지** - Conventional Commits 스타일 권장
4. **동기화 상태** - 원격 저장소와의 동기화 확인

## 🔍 문제 해결

### 일반적인 문제

1. **스크립트 실행 권한 오류**
   ```bash
   chmod +x scripts/*.sh
   chmod +x scripts/git-hooks/*
   ```

2. **브랜치명 검증 실패**
   ```bash
   # 현재 브랜치명 확인
   git branch --show-current
   
   # 새 브랜치로 전환
   git checkout -b feature/correct-name
   ```

3. **Git Hook이 작동하지 않음**
   ```bash
   # Hook 재설치
   bash scripts/install-git-hooks.sh
   
   # Hook 파일 확인
   ls -la .git/hooks/
   ```

### 테스트 실패 시

```bash
# 상세 테스트 실행
bash tests/branch_strategy/run_branch_strategy_tests.sh

# Python 환경 확인
python --version
which python

# Git 설정 확인
git config --list
```

## 📊 성공 지표

테스트 성공률에 따른 상태:

- **90% 이상**: 🎉 우수 - 브랜치 전략이 완벽하게 구축됨
- **70% 이상**: 👍 양호 - 대부분의 기능이 정상 작동
- **70% 미만**: ⚠️ 개선 필요 - 설정 점검 필요

## 🔗 관련 문서

- [Git Workflow Guide](../git-workflow/)
- [Commit Convention](../testing/3.3-commit-convention-testing.md)
- [Pull Request Process](../testing/3.4-pull-request-process-testing.md)
- [Code Quality Tools](../testing/3.5-code-quality-tools-testing.md)

## 🤝 팀 협업

### 새 팀원 온보딩

1. 이 README 문서 숙지
2. Git Hook 설치: `bash scripts/install-git-hooks.sh`
3. 브랜치 관리 도구 사용법 학습
4. 테스트 실행으로 환경 검증

### 일관성 유지

- 모든 팀원이 동일한 Git Hook 사용
- 브랜치 명명 규칙 준수
- 정기적인 브랜치 정리 수행
- 코드 리뷰 시 브랜치 전략 준수 확인

---

이 브랜치 전략 시스템은 Movie MLOps 프로젝트의 체계적인 버전 관리를 위해 설계되었습니다. 문제가 있거나 개선 사항이 있다면 이슈를 생성하거나 Pull Request를 제출해 주세요.

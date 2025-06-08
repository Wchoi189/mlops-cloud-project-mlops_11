#!/usr/bin/env python3
"""
브랜치 명명 규칙 테스트
Movie MLOps 프로젝트 브랜치 전략 검증
"""
import subprocess
import sys
import os
from pathlib import Path

class BranchNamingTest:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.validation_script = self.root_dir / "scripts" / "validate-branch-name.sh"
    
    def test_validation_script_exists(self):
        """브랜치명 검증 스크립트 존재 확인"""
        print("🧪 브랜치명 검증 스크립트 존재 확인...")
        
        if self.validation_script.exists():
            print(f"✅ 검증 스크립트 발견: {self.validation_script}")
            return True
        else:
            print(f"❌ 검증 스크립트 없음: {self.validation_script}")
            return False
    
    def test_valid_branch_names(self):
        """올바른 브랜치명 테스트"""
        print("\n🧪 올바른 브랜치명 테스트...")
        
        valid_names = [
            "feature/tmdb-api-integration",
            "feature/user-authentication",
            "feature/docker-compose-setup",
            "bugfix/data-validation-error",
            "bugfix/memory-leak-preprocessing",
            "bugfix/api-rate-limiting",
            "hotfix/critical-security-patch",
            "hotfix/production-data-loss",
            "experiment/new-ml-algorithm",
            "experiment/performance-optimization",
            "experiment/alternative-architecture",
            "docs/api-documentation",
            "docs/deployment-guide",
            "docs/user-manual",
            "data/collection-pipeline",
            "data/preprocessing-optimization",
            "model/training-pipeline",
            "model/evaluation-metrics",
            "pipeline/airflow-setup",
            "pipeline/cicd-automation",
            "infra/docker-optimization",
            "infra/kubernetes-deployment"
        ]
        
        failed_tests = []
        
        for branch_name in valid_names:
            try:
                result = subprocess.run(
                    ["bash", str(self.validation_script), branch_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"  ✅ {branch_name}")
            except subprocess.CalledProcessError:
                print(f"  ❌ {branch_name} - 올바른 이름이지만 실패")
                failed_tests.append(branch_name)
            except Exception as e:
                print(f"  💥 {branch_name} - 테스트 실행 오류: {e}")
                failed_tests.append(branch_name)
        
        return len(failed_tests) == 0
    
    def test_invalid_branch_names(self):
        """잘못된 브랜치명 테스트"""
        print("\n🧪 잘못된 브랜치명 테스트...")
        
        invalid_names = [
            "Feature/TmdbApiIntegration",    # 대문자 사용
            "fix-bug",                       # type 없음
            "feature-new",                   # 잘못된 구분자
            "main",                          # 보호된 브랜치
            "develop",                       # 보호된 브랜치
            "staging",                       # 보호된 브랜치
            "production",                    # 보호된 브랜치
            "random-branch",                 # 타입 없음
            "feature/",                      # 설명 없음
            "feature/very-long-branch-name-that-is-too-descriptive-and-should-be-shorter-than-fifty-characters",  # 너무 긴 이름
            "feature/with spaces",           # 공백 포함
            "feature/with@special#chars",    # 특수문자 포함
            "feature/--double-dash",         # 연속된 하이픈
            "invalid/type",                  # 허용되지 않은 타입
            "feature/ab",                    # 너무 짧은 설명
        ]
        
        failed_tests = []
        
        for branch_name in invalid_names:
            try:
                result = subprocess.run(
                    ["bash", str(self.validation_script), branch_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"  ❌ {branch_name} - 잘못된 이름이지만 통과")
                    failed_tests.append(branch_name)
                else:
                    print(f"  ✅ {branch_name} - 올바르게 거부됨")
            except Exception as e:
                print(f"  ⚠️ {branch_name} - 테스트 실행 오류: {e}")
                failed_tests.append(branch_name)
        
        return len(failed_tests) == 0
    
    def test_mlops_specific_patterns(self):
        """MLOps 특화 패턴 테스트"""
        print("\n🧪 MLOps 특화 패턴 테스트...")
        
        mlops_patterns = [
            "data/tmdb-collection-automation",
            "data/feature-preprocessing",
            "model/recommendation-training",
            "model/evaluation-pipeline",
            "pipeline/airflow-dag-setup",
            "pipeline/cicd-integration",
            "infra/docker-optimization",
            "infra/monitoring-setup",
            "experiment/new-embeddings",
            "experiment/hyperparameter-tuning"
        ]
        
        failed_tests = []
        
        for branch_name in mlops_patterns:
            try:
                result = subprocess.run(
                    ["bash", str(self.validation_script), branch_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"  ✅ {branch_name}")
            except subprocess.CalledProcessError:
                print(f"  ❌ {branch_name} - MLOps 패턴이지만 실패")
                failed_tests.append(branch_name)
            except Exception as e:
                print(f"  💥 {branch_name} - 테스트 실행 오류: {e}")
                failed_tests.append(branch_name)
        
        return len(failed_tests) == 0
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 브랜치 명명 규칙 테스트 시작...\n")
        
        tests = [
            ("스크립트 존재 확인", self.test_validation_script_exists),
            ("올바른 브랜치명", self.test_valid_branch_names),
            ("잘못된 브랜치명", self.test_invalid_branch_names),
            ("MLOps 특화 패턴", self.test_mlops_specific_patterns),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} 테스트 통과\n")
                else:
                    print(f"❌ {test_name} 테스트 실패\n")
            except Exception as e:
                print(f"💥 {test_name} 테스트 오류: {e}\n")
        
        # 결과 요약
        print("📊 테스트 결과 요약:")
        print(f"  통과: {passed}/{total}")
        print(f"  성공률: {(passed/total*100):.1f}%")
        
        return passed == total

if __name__ == "__main__":
    tester = BranchNamingTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

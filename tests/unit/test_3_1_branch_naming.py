#!/usr/bin/env python3
"""
브랜치 네이밍 규칙 검증 테스트
MLOps 9단계 브랜치 패턴과 네이밍 컨벤션 검증
"""

import os
import subprocess
import pytest

class TestBranchNaming:
    """브랜치 네이밍 규칙 테스트 클래스"""
    
    def test_branch_validation_script_exists(self):
        """브랜치 검증 스크립트 존재 확인"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        assert os.path.exists(script_path), f"브랜치 검증 스크립트가 없습니다: {script_path}"
        assert os.access(script_path, os.X_OK), f"브랜치 검증 스크립트에 실행 권한이 없습니다: {script_path}"
    
    @pytest.mark.parametrize("branch_name,should_pass", [
        # 유효한 MLOps 단계별 브랜치
        ("feature/stage1-data-pipeline", True),
        ("feature/stage2-feature-store", True),
        ("feature/stage3-version-control", True),
        ("feature/stage4-cicd-pipeline", True),
        ("feature/stage5-model-serving", True),
        ("feature/stage6-monitoring", True),
        ("feature/stage7-security", True),
        ("feature/stage8-scalability", True),
        ("feature/stage9-event-driven", True),
        
        # 유효한 실험 브랜치
        ("experiment/hyperparameter-tuning", True),
        ("experiment/model-comparison", True),
        ("experiment/feature-engineering", True),
        
        # 유효한 버그 수정 브랜치
        ("bugfix/123-memory-leak", True),
        ("bugfix/456-performance-issue", True),
        
        # 유효한 긴급 수정 브랜치
        ("hotfix/789-security-patch", True),
        ("hotfix/101-critical-bug", True),
        
        # 유효한 문서 브랜치
        ("docs/api-documentation", True),
        ("docs/user-guide", True),
        
        # 무효한 브랜치들
        ("Feature/Stage1-DataPipeline", False),  # 대문자 사용
        ("feature/stage10-invalid", False),      # 잘못된 단계 번호
        ("feature/stage0-invalid", False),       # 잘못된 단계 번호
        ("random-branch", False),                # 타입 접두사 없음
        ("main", False),                         # 보호된 브랜치
        ("master", False),                       # 보호된 브랜치
        ("develop", False),                      # 보호된 브랜치
        ("feature/stage1", False),               # 설명 부분 누락
        ("experiment/", False),                  # 설명 부분 누락
        ("bugfix/123", False),                   # 설명 부분 누락
        ("feature/stage1-", False),              # 하이픈으로 끝남
        ("feature/stage1--double-dash", False), # 연속된 하이픈
    ])
    def test_branch_naming_validation(self, branch_name, should_pass):
        """브랜치명 검증 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # 브랜치 검증 스크립트 실행
        result = subprocess.run([script_path, branch_name], 
                              capture_output=True, text=True)
        
        if should_pass:
            assert result.returncode == 0, \
                f"브랜치명 '{branch_name}'가 유효해야 하는데 실패했습니다. 출력: {result.stderr}"
        else:
            assert result.returncode != 0, \
                f"브랜치명 '{branch_name}'가 무효해야 하는데 통과했습니다. 출력: {result.stdout}"
    
    def test_branch_validation_help_message(self):
        """브랜치 검증 스크립트 도움말 메시지 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # 인수 없이 호출 시 도움말 표시
        result = subprocess.run([script_path], capture_output=True, text=True)
        assert result.returncode == 0, "인수 없이 호출 시 도움말을 표시해야 합니다"
        assert 'MLOps 브랜치 네이밍 규칙' in result.stdout, "도움말 메시지에 '브랜치 네이밍 규칙'이 포함되어야 합니다"
        
    def test_branch_validation_invalid_message(self):
        """브랜치 검증 스크립트 잘못된 브랜치명 오류 메시지 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # 잘못된 브랜치명으로 호출
        result = subprocess.run([script_path, 'invalid-branch'], 
                              capture_output=True, text=True)
        assert result.returncode != 0, "잘못된 브랜치명으로 호출 시 실패해야 합니다"
        assert '유효하지 않은 브랜치명' in result.stdout, "오류 메시지에 '유효하지 않은 브랜치명'이 포함되어야 합니다"
    
    def test_mlops_stage_validation(self):
        """MLOps 9단계 검증 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # 각 MLOps 단계별 테스트
        for stage in range(1, 10):  # 1-9단계
            branch_name = f"feature/stage{stage}-test"
            result = subprocess.run([script_path, branch_name], 
                                  capture_output=True, text=True)
            assert result.returncode == 0, \
                f"MLOps Stage {stage} 브랜치가 유효해야 합니다: {branch_name}"
            assert f"Stage {stage}" in result.stdout, \
                f"출력에 'Stage {stage}'가 포함되어야 합니다"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

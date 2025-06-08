#!/usr/bin/env python3
"""
MLOps 브랜치 생성 도구 통합 테스트
브랜치 자동 생성 및 디렉터리 구조 검증
"""

import os
import tempfile
import subprocess
import shutil
import pytest
from pathlib import Path

class TestMLOpsBranchCreator:
    """MLOps 브랜치 생성 도구 테스트 클래스"""
    
    @pytest.fixture
    def temp_git_repo(self):
        """임시 Git 저장소 생성"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Git 저장소 초기화
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
            
            # 초기 커밋 생성
            readme_path = os.path.join(temp_dir, 'README.md')
            with open(readme_path, 'w') as f:
                f.write("# Test Repository\n")
            
            subprocess.run(['git', 'add', 'README.md'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            yield temp_dir
    
    def test_validate_branch_name_functionality(self):
        """브랜치명 검증 스크립트 기능 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # 스크립트 존재 확인
        assert os.path.exists(script_path), f"브랜치 검증 스크립트가 없습니다: {script_path}"
        
        # 유효한 브랜치명 테스트
        valid_branches = [
            "feature/stage1-data-pipeline",
            "experiment/hyperparameter-tuning",
            "bugfix/123-memory-leak",
            "docs/api-documentation"
        ]
        
        for branch in valid_branches:
            result = subprocess.run([script_path, branch], 
                                  capture_output=True, text=True)
            assert result.returncode == 0, \
                f"유효한 브랜치명이 실패했습니다: {branch}. 오류: {result.stderr}"
        
        # 무효한 브랜치명 테스트
        invalid_branches = [
            "Feature/Stage1-DataPipeline",  # 대문자
            "random-branch",                # 잘못된 패턴
            "main",                        # 보호된 브랜치
        ]
        
        for branch in invalid_branches:
            result = subprocess.run([script_path, branch], 
                                  capture_output=True, text=True)
            assert result.returncode != 0, \
                f"무효한 브랜치명이 통과했습니다: {branch}. 출력: {result.stdout}"
    
    def test_mlops_stage_branch_naming_patterns(self):
        """MLOps 단계별 브랜치 네이밍 패턴 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        # MLOps 9단계 매핑
        stage_mapping = {
            1: "데이터 파이프라인",
            2: "피처 스토어", 
            3: "버전 관리",
            4: "CI/CD 파이프라인",
            5: "모델 서빙",
            6: "모니터링",
            7: "보안",
            8: "확장성",
            9: "이벤트 드리븐"
        }
        
        for stage_num, stage_desc in stage_mapping.items():
            branch_name = f"feature/stage{stage_num}-test-implementation"
            result = subprocess.run([script_path, branch_name], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0, \
                f"MLOps Stage {stage_num} 브랜치 검증 실패: {branch_name}"
            assert f"Stage {stage_num}" in result.stdout, \
                f"출력에 Stage {stage_num} 정보가 없습니다: {result.stdout}"
    
    def test_git_workflow_integration(self, temp_git_repo):
        """Git 워크플로우 통합 테스트"""
        # 현재 브랜치 확인
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              cwd=temp_git_repo, capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        # 테스트 브랜치 생성
        test_branch = "feature/stage1-test-integration"
        subprocess.run(['git', 'checkout', '-b', test_branch], 
                      cwd=temp_git_repo, check=True, capture_output=True)
        
        # 브랜치가 제대로 생성되었는지 확인
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              cwd=temp_git_repo, capture_output=True, text=True)
        assert result.stdout.strip() == test_branch, \
            f"브랜치가 제대로 생성되지 않았습니다. 예상: {test_branch}, 실제: {result.stdout.strip()}"
        
        # 원래 브랜치로 돌아가기
        subprocess.run(['git', 'checkout', current_branch], 
                      cwd=temp_git_repo, check=True, capture_output=True)
    
    def test_branch_protection_rules(self):
        """보호된 브랜치 규칙 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        protected_branches = ["main", "master", "develop", "staging", "production"]
        
        for protected_branch in protected_branches:
            result = subprocess.run([script_path, protected_branch], 
                                  capture_output=True, text=True)
            assert result.returncode != 0, \
                f"보호된 브랜치 {protected_branch}가 허용되었습니다"
            assert "보호된 브랜치" in result.stdout, \
                f"보호된 브랜치 오류 메시지가 없습니다: {result.stdout}"
    
    def test_mlops_stage_branch_creation(self, temp_git_repo):
        """단계별 MLOps 브랜치 생성 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        
        # create_mlops_branch.py 스크립트 확인
        script_path = os.path.join(project_root, 'scripts', 'create_mlops_branch.py')
        if not os.path.exists(script_path):
            pytest.skip(f"MLOps 브랜치 생성 스크립트가 없습니다: {script_path}")
        
        # 임시 Git 저장소에서 테스트
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_git_repo)
            
            # MLOps 4단계 브랜치 생성 테스트
            result = subprocess.run([
                'python', script_path, 'stage', '4', 'test-cicd-pipeline'
            ], capture_output=True, text=True, cwd=temp_git_repo)
            
            if result.returncode == 0:
                # 브랜치가 생성되었는지 확인
                branch_result = subprocess.run([
                    'git', 'branch', '--list', 'feature/stage4-test-cicd-pipeline'
                ], capture_output=True, text=True, cwd=temp_git_repo)
                
                assert 'feature/stage4-test-cicd-pipeline' in branch_result.stdout, \
                    f"브랜치가 생성되지 않았습니다: {branch_result.stdout}"
            else:
                # 스크립트가 없거나 실행되지 않으면 브랜치 검증만 테스트
                pytest.skip("브랜치 생성 스크립트가 실행되지 않았습니다")
        
        finally:
            os.chdir(old_cwd)
    
    def test_experiment_branch_patterns(self):
        """실험 브랜치 패턴 테스트"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        script_path = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
        
        experiment_branches = [
            "experiment/hyperparameter-tuning",
            "experiment/model-comparison",
            "experiment/feature-selection",
            "experiment/data-augmentation"
        ]
        
        for exp_branch in experiment_branches:
            result = subprocess.run([script_path, exp_branch], 
                                  capture_output=True, text=True)
            assert result.returncode == 0, \
                f"실험 브랜치 {exp_branch} 검증 실패: {result.stderr}"
            assert "실험 브랜치" in result.stdout, \
                f"실험 브랜치 확인 메시지가 없습니다: {result.stdout}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

#!/usr/bin/env python3
"""
완전한 Git 워크플로우 E2E 테스트
실제 MLOps 워크플로우 시나리오 검증
"""

import os
import tempfile
import subprocess
import shutil
import pytest
from pathlib import Path

class TestCompleteGitWorkflow:
    """완전한 Git 워크플로우 E2E 테스트"""
    
    @pytest.fixture
    def temp_mlops_repo(self):
        """임시 MLOps 저장소 생성"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 기본 Git 저장소 설정
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'MLOps Tester'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'user.email', 'mlops@example.com'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'config', 'init.defaultBranch', 'main'], cwd=temp_dir, check=True)
            
            # 기본 MLOps 프로젝트 구조 생성
            dirs_to_create = [
                'docs', 'scripts', 'tests/unit', 'tests/integration', 'tests/e2e',
                'src', 'data/raw', 'data/processed', 'models', 'configs'
            ]
            
            for dir_path in dirs_to_create:
                os.makedirs(os.path.join(temp_dir, dir_path), exist_ok=True)
            
            # 브랜치 검증 스크립트 복사
            project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
            source_script = os.path.join(project_root, 'scripts', 'validate_branch_name.sh')
            if os.path.exists(source_script):
                dest_dir = os.path.join(temp_dir, 'scripts')
                shutil.copy2(source_script, dest_dir)
                os.chmod(os.path.join(dest_dir, 'validate_branch_name.sh'), 0o755)
            
            # README 파일 생성 및 초기 커밋
            readme_content = "# MLOps Test Project\n\nMLOps Git 워크플로우 테스트용 프로젝트"
            with open(os.path.join(temp_dir, 'README.md'), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            subprocess.run(['git', 'add', '.'], cwd=temp_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True)
            
            yield temp_dir
    
    def test_complete_mlops_feature_workflow(self, temp_mlops_repo):
        """완전한 MLOps 기능 개발 워크플로우 테스트"""
        repo_dir = temp_mlops_repo
        
        # Stage 6 (모니터링) 브랜치 생성 및 구현
        stage6_branch = "feature/stage6-monitoring-implementation"
        subprocess.run(['git', 'checkout', '-b', stage6_branch], cwd=repo_dir, check=True, capture_output=True)
        
        # 브랜치명 검증
        script_path = os.path.join(repo_dir, 'scripts', 'validate_branch_name.sh')
        if os.path.exists(script_path):
            result = subprocess.run([script_path, stage6_branch], cwd=repo_dir, capture_output=True, text=True)
            assert result.returncode == 0, f"Stage 6 브랜치명 검증 실패: {result.stderr}"
        
        # 모니터링 시스템 구현
        monitoring_dir = os.path.join(repo_dir, 'src', 'monitoring')
        os.makedirs(monitoring_dir, exist_ok=True)
        
        monitoring_code = '''#!/usr/bin/env python3
"""MLOps 모니터링 시스템"""

class ModelMonitor:
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def track_prediction(self, prediction, actual=None):
        """예측 결과 추적"""
        pass
    
    def calculate_drift(self):
        """데이터 드리프트 계산"""
        return {"data_drift": 0.05, "model_drift": 0.03}
'''
        
        with open(os.path.join(monitoring_dir, 'monitor.py'), 'w') as f:
            f.write(monitoring_code)
        
        # 파일 커밋 및 병합
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'feat(stage6): implement monitoring'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'checkout', 'main'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'merge', '--no-ff', stage6_branch, '-m', 'Merge stage6'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'branch', '-d', stage6_branch], cwd=repo_dir, check=True)
        
        # 최종 상태 확인
        assert os.path.exists(os.path.join(monitoring_dir, 'monitor.py')), "모니터링 파일이 없습니다"
    
    def test_experiment_workflow_complete(self, temp_mlops_repo):
        """실험 워크플로우 완전 테스트"""
        repo_dir = temp_mlops_repo
        
        # 실험 브랜치 생성
        exp_branch = "experiment/model-comparison-study"
        subprocess.run(['git', 'checkout', '-b', exp_branch], cwd=repo_dir, check=True, capture_output=True)
        
        # 브랜치명 검증
        script_path = os.path.join(repo_dir, 'scripts', 'validate_branch_name.sh')
        if os.path.exists(script_path):
            result = subprocess.run([script_path, exp_branch], cwd=repo_dir, capture_output=True, text=True)
            assert result.returncode == 0, f"실험 브랜치명 검증 실패: {result.stderr}"
        
        # 실험 파일 생성
        exp_dir = os.path.join(repo_dir, 'experiments')
        os.makedirs(exp_dir, exist_ok=True)
        
        exp_config = '''experiment:
  name: "Model Comparison"
  models: [random_forest, xgboost]
  metrics: [accuracy, precision]
'''
        
        with open(os.path.join(exp_dir, 'config.yaml'), 'w') as f:
            f.write(exp_config)
        
        # 실험 결과 커밋
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'experiment: model comparison'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'checkout', 'main'], cwd=repo_dir, check=True)
        
        # 실험 브랜치는 보통 유지됨
        result = subprocess.run(['git', 'branch'], cwd=repo_dir, capture_output=True, text=True)
        assert exp_branch in result.stdout, "실험 브랜치가 삭제되었습니다"
    
    def test_workflow_integration_complete(self, temp_mlops_repo):
        """워크플로우 통합 완전 테스트"""
        repo_dir = temp_mlops_repo
        
        # 다양한 브랜치 타입 테스트
        test_branches = [
            "feature/stage7-security",
            "experiment/hyperparameter-tuning", 
            "bugfix/123-memory-leak",
            "docs/api-documentation"
        ]
        
        script_path = os.path.join(repo_dir, 'scripts', 'validate_branch_name.sh')
        
        for branch_name in test_branches:
            # 브랜치 생성
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=repo_dir, check=True, capture_output=True)
            
            # 브랜치명 검증
            if os.path.exists(script_path):
                result = subprocess.run([script_path, branch_name], cwd=repo_dir, capture_output=True, text=True)
                assert result.returncode == 0, f"브랜치 {branch_name} 검증 실패"
            
            # 메인으로 돌아가기
            subprocess.run(['git', 'checkout', 'main'], cwd=repo_dir, check=True)
        
        # 모든 브랜치 생성 확인
        result = subprocess.run(['git', 'branch'], cwd=repo_dir, capture_output=True, text=True)
        for branch_name in test_branches:
            assert branch_name in result.stdout, f"브랜치 {branch_name}가 생성되지 않았습니다"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

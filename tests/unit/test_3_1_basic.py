#!/usr/bin/env python3
"""
기본 Git 워크플로우 테스트
"""

import os
import subprocess
import pytest

class TestBasicGitWorkflow:
    """기본 Git 워크플로우 테스트"""
    
    def test_project_structure(self):
        """프로젝트 구조 확인"""
        project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
        
        # 필수 파일들 확인
        required_files = [
            'docker-compose.git-workflow.yml',
            '.gitignore',
            'requirements.txt',
        ]
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            assert os.path.exists(full_path), f"필수 파일이 없습니다: {file_path}"
    
    def test_git_installation(self):
        """Git 설치 확인"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            assert 'git version' in result.stdout
        except subprocess.CalledProcessError:
            pytest.fail("Git이 설치되지 않았습니다.")
    
    def test_python_installation(self):
        """Python 설치 확인"""
        import sys
        assert sys.version_info >= (3, 7), "Python 3.7 이상이 필요합니다."
    
    def test_environment_variables(self):
        """환경 변수 확인"""
        assert os.environ.get('TEST_MODE') == 'true', "TEST_MODE 환경 변수가 설정되지 않았습니다."
        assert 'MLOPS_PROJECT_ROOT' in os.environ, "MLOPS_PROJECT_ROOT 환경 변수가 설정되지 않았습니다."

if __name__ == '__main__':
    pytest.main([__file__])

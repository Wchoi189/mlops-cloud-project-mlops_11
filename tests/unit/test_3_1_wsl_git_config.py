#!/usr/bin/env python3
"""
WSL Git 설정 테스트
WSL 환경에 최적화된 Git 설정과 MLOps 별칭 검증
"""

import os
import subprocess
import pytest

class TestWSLGitConfig:
    """WSL Git 설정 테스트 클래스"""
    
    def test_wsl_git_core_settings(self):
        """WSL 핵심 Git 설정 검증"""
        # core.autocrlf 설정 확인
        result = subprocess.run(['git', 'config', '--global', 'core.autocrlf'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "core.autocrlf 설정이 없습니다"
        assert result.stdout.strip() == 'input', f"core.autocrlf가 'input'이어야 하는데 '{result.stdout.strip()}'입니다"
        
        # core.filemode 설정 확인
        result = subprocess.run(['git', 'config', '--global', 'core.filemode'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "core.filemode 설정이 없습니다"
        assert result.stdout.strip() == 'false', f"core.filemode가 'false'여야 하는데 '{result.stdout.strip()}'입니다"
        
        # core.ignorecase 설정 확인
        result = subprocess.run(['git', 'config', '--global', 'core.ignorecase'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "core.ignorecase 설정이 없습니다"
        assert result.stdout.strip() == 'false', f"core.ignorecase가 'false'여야 하는데 '{result.stdout.strip()}'입니다"
    
    def test_wsl_git_performance_settings(self):
        """WSL Git 성능 최적화 설정 검증"""
        # core.preloadindex 설정 확인
        result = subprocess.run(['git', 'config', '--global', 'core.preloadindex'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "core.preloadindex 설정이 없습니다"
        assert result.stdout.strip() == 'true', f"core.preloadindex가 'true'여야 하는데 '{result.stdout.strip()}'입니다"
        
        # core.fscache 설정 확인
        result = subprocess.run(['git', 'config', '--global', 'core.fscache'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "core.fscache 설정이 없습니다"
        assert result.stdout.strip() == 'true', f"core.fscache가 'true'여야 하는데 '{result.stdout.strip()}'입니다"
    
    def test_mlops_git_aliases(self):
        """MLOps Git 별칭 설정 검증"""
        expected_aliases = {
            'mlops-stage': 'add -A',
            'mlops-exp': 'checkout -b experiment/',
            'mlops-bugfix': 'checkout -b bugfix/',
            'mlops-status': 'status --porcelain'
        }
        
        for alias, expected_command in expected_aliases.items():
            result = subprocess.run(['git', 'config', '--global', f'alias.{alias}'], 
                                  capture_output=True, text=True)
            assert result.returncode == 0, f"{alias} 별칭이 설정되지 않았습니다"
            assert result.stdout.strip() == expected_command, \
                f"{alias} 별칭이 '{expected_command}'여야 하는데 '{result.stdout.strip()}'입니다"
    
    def test_git_user_configuration(self):
        """Git 사용자 설정 검증"""
        # 사용자 이름 확인
        result = subprocess.run(['git', 'config', '--global', 'user.name'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "Git 사용자 이름이 설정되지 않았습니다"
        assert len(result.stdout.strip()) > 0, "Git 사용자 이름이 비어있습니다"
        
        # 이메일 확인
        result = subprocess.run(['git', 'config', '--global', 'user.email'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "Git 이메일이 설정되지 않았습니다"
        assert '@' in result.stdout.strip(), "Git 이메일 형식이 올바르지 않습니다"
    
    def test_default_branch_configuration(self):
        """기본 브랜치 설정 검증"""
        result = subprocess.run(['git', 'config', '--global', 'init.defaultBranch'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "기본 브랜치가 설정되지 않았습니다"
        assert result.stdout.strip() == 'main', \
            f"기본 브랜치가 'main'이어야 하는데 '{result.stdout.strip()}'입니다"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

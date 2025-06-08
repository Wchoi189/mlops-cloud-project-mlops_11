#!/usr/bin/env python3
"""
Git 워크플로우 상태 확인 도구
"""
import subprocess
import sys
import os
from pathlib import Path
import argparse

class GitWorkflowManager:
    """Git 워크플로우 관리 클래스"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        
    def get_workflow_status(self):
        """MLOps Git 워크플로우 상태 확인"""
        print("🔍 MLOps Git 워크플로우 상태")
        print("=" * 50)
        
        # 현재 브랜치 확인
        try:
            current_branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                text=True
            ).strip()
            print(f"📍 현재 브랜치: {current_branch}")
        except subprocess.CalledProcessError:
            print("❌ Git 저장소가 아니거나 브랜치 정보를 가져올 수 없습니다.")
            return
        
        # 브랜치 목록 확인
        try:
            branches = subprocess.check_output(
                ['git', 'branch'],
                text=True
            ).strip().split('\n')
            
            feature_branches = []
            experiment_branches = []
            bugfix_branches = []
            other_branches = []
            
            for branch in branches:
                branch_name = branch.strip('* ').strip()
                if branch_name.startswith('feature/stage'):
                    feature_branches.append(branch_name)
                elif branch_name.startswith('experiment/'):
                    experiment_branches.append(branch_name)
                elif branch_name.startswith('bugfix/'):
                    bugfix_branches.append(branch_name)
                else:
                    other_branches.append(branch_name)
            
            print(f"\n🌟 MLOps 단계별 브랜치 ({len(feature_branches)}개):")
            for branch in feature_branches:
                print(f"  - {branch}")
            
            print(f"\n🧪 실험 브랜치 ({len(experiment_branches)}개):")
            for branch in experiment_branches:
                print(f"  - {branch}")
            
            print(f"\n🐛 버그 수정 브랜치 ({len(bugfix_branches)}개):")
            for branch in bugfix_branches:
                print(f"  - {branch}")
            
            print(f"\n📋 기타 브랜치 ({len(other_branches)}개):")
            for branch in other_branches:
                print(f"  - {branch}")
                
        except subprocess.CalledProcessError:
            print("❌ 브랜치 목록을 가져올 수 없습니다.")
        
        # Git 상태 확인
        try:
            status_output = subprocess.check_output(
                ['git', 'status', '--porcelain'],
                text=True
            ).strip()
            
            if status_output:
                print(f"\n⚠️ 변경된 파일들:")
                for line in status_output.split('\n'):
                    print(f"  {line}")
            else:
                print(f"\n✅ 작업 디렉터리가 깨끗합니다.")
                
        except subprocess.CalledProcessError:
            print("❌ Git 상태를 확인할 수 없습니다.")
        
        # 원격 저장소 상태 확인
        try:
            remote_info = subprocess.check_output(
                ['git', 'remote', '-v'],
                text=True
            ).strip()
            
            if remote_info:
                print(f"\n🌐 원격 저장소:")
                for line in remote_info.split('\n'):
                    print(f"  {line}")
            else:
                print(f"\n⚠️ 원격 저장소가 설정되지 않았습니다.")
                
        except subprocess.CalledProcessError:
            print("❌ 원격 저장소 정보를 확인할 수 없습니다.")
        
        print("\n" + "=" * 50)
    
    def check_branch_validation(self, branch_name):
        """브랜치명 검증"""
        validator_script = self.project_root / "scripts" / "validate_branch_name.sh"
        
        if not validator_script.exists():
            print(f"❌ 브랜치 검증 스크립트를 찾을 수 없습니다: {validator_script}")
            return False
        
        try:
            result = subprocess.run(
                [str(validator_script), branch_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print(f"✅ 브랜치명 '{branch_name}'이 유효합니다.")
                return True
            else:
                print(f"❌ 브랜치명 '{branch_name}'이 유효하지 않습니다.")
                print(result.stdout)
                return False
                
        except Exception as e:
            print(f"❌ 브랜치 검증 중 오류 발생: {e}")
            return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Git 워크플로우 관리 도구')
    parser.add_argument('command', choices=['status', 'validate'],
                        help='실행할 명령')
    parser.add_argument('--branch', help='검증할 브랜치명 (validate 명령 시 필요)')
    
    args = parser.parse_args()
    
    # 프로젝트 루트 경로 확인
    project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
    manager = GitWorkflowManager(project_root)
    
    if args.command == 'status':
        manager.get_workflow_status()
    elif args.command == 'validate':
        if not args.branch:
            print("❌ --branch 옵션이 필요합니다.")
            sys.exit(1)
        manager.check_branch_validation(args.branch)

if __name__ == "__main__":
    main()

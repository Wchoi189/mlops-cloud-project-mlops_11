#!/usr/bin/env python3
"""
MLOps 브랜치 생성 자동화 도구
"""
import sys
import subprocess
import os
from pathlib import Path
import argparse

class MLOpsBranchCreator:
    """MLOps 브랜치 생성 클래스"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.valid_stages = list(range(1, 10))  # 1-9단계
        
    def create_stage_branch(self, stage_num, description):
        """MLOps 단계별 브랜치 생성"""
        if stage_num not in self.valid_stages:
            raise ValueError(f"Invalid stage number: {stage_num}. Must be 1-9")
        
        branch_name = f"feature/stage{stage_num}-{description}"
        
        # 브랜치 생성 및 체크아웃
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        # 단계별 디렉터리 구조 생성
        stage_mapping = {
            1: "data-pipeline",
            2: "feature-store", 
            3: "version-control",
            4: "cicd-pipeline",
            5: "model-serving",
            6: "monitoring",
            7: "security",
            8: "scalability",
            9: "event-driven"
        }
        
        stage_dirname = stage_mapping.get(stage_num, f"stage{stage_num}")
        stage_dir = self.project_root / f"docs/{stage_num:02d}-{stage_dirname}"
        stage_dir.mkdir(exist_ok=True)
        
        # 구현 디렉터리 생성
        impl_dir = stage_dir / "implementation"
        impl_dir.mkdir(exist_ok=True)
        
        # README 파일 생성
        readme_file = stage_dir / "README.md"
        if not readme_file.exists():
            readme_content = f"""# {stage_num:02d}. {stage_dirname.title().replace('-', ' ')}

## 개요
MLOps {stage_num}단계: {description}

## 구현 내용
- [ ] 기본 설정
- [ ] 핵심 기능 구현
- [ ] 테스트 작성
- [ ] 문서화

## 진행 상황
- 브랜치 생성: ✅
- 구현 진행: 🔄
- 테스트 완료: ⏳
- 문서화 완료: ⏳

## 관련 파일
- Implementation: `./implementation/`
- Tests: `../../tests/`
- Scripts: `../../scripts/`
"""
            readme_file.write_text(readme_content)
        
        print(f"✅ MLOps {stage_num}단계 브랜치 생성 완료: {branch_name}")
        print(f"📁 디렉터리 생성: {stage_dir}")
        return branch_name
    
    def create_experiment_branch(self, description):
        """실험 브랜치 생성"""
        branch_name = f"experiment/{description}"
        
        # 브랜치 생성 및 체크아웃
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        # 실험 디렉터리 생성
        exp_dir = self.project_root / "experiments" / description
        exp_dir.mkdir(parents=True, exist_ok=True)
        
        # 실험 파일 생성
        exp_file = exp_dir / f"{description}-experiment.md"
        if not exp_file.exists():
            exp_content = f"""# 실험: {description}

## 실험 목표
{description} 관련 실험

## 가설
- 

## 실험 설계
- 

## 실험 결과
- 

## 결론
- 

## 다음 단계
- 
"""
            exp_file.write_text(exp_content)
        
        print(f"✅ 실험 브랜치 생성 완료: {branch_name}")
        print(f"📁 실험 디렉터리 생성: {exp_dir}")
        return branch_name
    
    def create_bugfix_branch(self, issue_number, description):
        """버그 수정 브랜치 생성"""
        branch_name = f"bugfix/{issue_number}-{description}"
        
        # 브랜치 생성 및 체크아웃
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        print(f"✅ 버그 수정 브랜치 생성 완료: {branch_name}")
        print(f"🐛 이슈 번호: {issue_number}")
        return branch_name
    
    def create_hotfix_branch(self, issue_number, description):
        """긴급 수정 브랜치 생성"""
        branch_name = f"hotfix/{issue_number}-{description}"
        
        # 브랜치 생성 및 체크아웃
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        print(f"✅ 긴급 수정 브랜치 생성 완료: {branch_name}")
        print(f"🚨 긴급 이슈 번호: {issue_number}")
        return branch_name

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='MLOps 브랜치 생성 도구')
    parser.add_argument('type', choices=['stage', 'experiment', 'bugfix', 'hotfix'],
                        help='브랜치 타입')
    parser.add_argument('args', nargs='+', help='브랜치 생성에 필요한 인자들')
    
    args = parser.parse_args()
    
    # 프로젝트 루트 경로 확인
    project_root = os.environ.get('MLOPS_PROJECT_ROOT', os.getcwd())
    creator = MLOpsBranchCreator(project_root)
    
    try:
        if args.type == 'stage':
            if len(args.args) != 2:
                print("❌ 사용법: python create_mlops_branch.py stage <stage_number> <description>")
                sys.exit(1)
            stage_num = int(args.args[0])
            description = args.args[1]
            creator.create_stage_branch(stage_num, description)
            
        elif args.type == 'experiment':
            if len(args.args) != 1:
                print("❌ 사용법: python create_mlops_branch.py experiment <description>")
                sys.exit(1)
            description = args.args[0]
            creator.create_experiment_branch(description)
            
        elif args.type == 'bugfix':
            if len(args.args) != 2:
                print("❌ 사용법: python create_mlops_branch.py bugfix <issue_number> <description>")
                sys.exit(1)
            issue_number = args.args[0]
            description = args.args[1]
            creator.create_bugfix_branch(issue_number, description)
            
        elif args.type == 'hotfix':
            if len(args.args) != 2:
                print("❌ 사용법: python create_mlops_branch.py hotfix <issue_number> <description>")
                sys.exit(1)
            issue_number = args.args[0]
            description = args.args[1]
            creator.create_hotfix_branch(issue_number, description)
            
    except Exception as e:
        print(f"❌ 브랜치 생성 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

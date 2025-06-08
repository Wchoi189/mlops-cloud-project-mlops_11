#!/usr/bin/env python3
"""
Airflow 운영 관리 스크립트
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import argparse
import os

class AirflowManager:
    """Airflow 운영 관리"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.airflow_dir = self.project_root / 'airflow'
        self.compose_file = self.airflow_dir / 'docker-compose-airflow.yml'
        
    def start_airflow(self):
        """Airflow 서비스 시작"""
        print("Airflow 서비스 시작 중...")
        
        if not self.compose_file.exists():
            print(f"❌ Docker Compose 파일을 찾을 수 없습니다: {self.compose_file}")
            return False
        
        try:
            # 환경변수 파일 확인
            env_file = self.project_root / '.env'
            if not env_file.exists():
                print("⚠️ .env 파일이 없습니다. 기본 설정으로 진행합니다.")
            
            # .env 파일을 airflow 디렉토리로 복사
            if env_file.exists():
                import shutil
                airflow_env = self.airflow_dir / '.env'
                shutil.copy2(env_file, airflow_env)
                print(f"✅ 환경변수 파일 복사: {airflow_env}")
            
            # Airflow UID 설정
            os.environ['AIRFLOW_UID'] = '50000'
            
            # 초기화 실행
            print("Airflow 초기화 중...")
            init_result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'up', 'airflow-init'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if init_result.returncode != 0:
                print(f"❌ Airflow 초기화 실패: {init_result.stderr}")
                return False
            
            # 서비스 시작
            print("Airflow 서비스 시작 중...")
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'up', '-d'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Airflow 서비스가 성공적으로 시작되었습니다.")
                self._check_services()
                self._show_access_info()
                return True
            else:
                print(f"❌ Airflow 시작 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Airflow 시작 중 오류: {e}")
            return False
    
    def stop_airflow(self):
        """Airflow 서비스 중지"""
        print("Airflow 서비스 중지 중...")
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'down'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Airflow 서비스가 중지되었습니다.")
                return True
            else:
                print(f"❌ Airflow 중지 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Airflow 중지 중 오류: {e}")
            return False
    
    def restart_airflow(self):
        """Airflow 서비스 재시작"""
        print("Airflow 서비스 재시작 중...")
        if self.stop_airflow():
            import time
            time.sleep(5)  # 잠시 대기
            return self.start_airflow()
        return False
    
    def _check_services(self):
        """서비스 상태 확인"""
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'ps'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            print("\n=== Airflow 서비스 상태 ===")
            print(result.stdout)
            
        except Exception as e:
            print(f"서비스 상태 확인 실패: {e}")
    
    def _show_access_info(self):
        """접속 정보 표시"""
        print("\n" + "="*50)
        print("🚀 Airflow 웹 UI 접속 정보")
        print("="*50)
        print("URL: http://localhost:8080")
        print("사용자명: airflow")
        print("비밀번호: airflow")
        print("\n브라우저에서 위 URL로 접속하여 DAG를 확인하고 실행할 수 있습니다.")
        print("="*50)
    
    def get_dag_status(self, dag_id=None):
        """DAG 상태 조회"""
        try:
            if dag_id:
                cmd = ['docker-compose', '-f', str(self.compose_file), 'exec', 
                       'airflow-webserver', 'airflow', 'dags', 'state', dag_id]
            else:
                cmd = ['docker-compose', '-f', str(self.compose_file), 'exec', 
                       'airflow-webserver', 'airflow', 'dags', 'list']
            
            result = subprocess.run(cmd, cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("=== DAG 상태 ===")
                print(result.stdout)
            else:
                print(f"DAG 상태 조회 실패: {result.stderr}")
                
        except Exception as e:
            print(f"DAG 상태 조회 중 오류: {e}")
    
    def trigger_dag(self, dag_id, execution_date=None):
        """DAG 수동 트리거"""
        print(f"DAG 트리거: {dag_id}")
        
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'exec', 
                   'airflow-webserver', 'airflow', 'dags', 'trigger', dag_id]
            
            if execution_date:
                cmd.extend(['-e', execution_date])
            
            result = subprocess.run(cmd, cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ DAG {dag_id} 트리거 성공")
                print(result.stdout)
            else:
                print(f"❌ DAG 트리거 실패: {result.stderr}")
                
        except Exception as e:
            print(f"DAG 트리거 중 오류: {e}")
    
    def list_dags(self):
        """등록된 DAG 목록 조회"""
        print("=== 등록된 DAG 목록 ===")
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 
                'airflow-webserver', 'airflow', 'dags', 'list'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"DAG 목록 조회 실패: {result.stderr}")
                
        except Exception as e:
            print(f"DAG 목록 조회 중 오류: {e}")
    
    def test_dag(self, dag_id, task_id, execution_date=None):
        """DAG 태스크 테스트"""
        if not execution_date:
            execution_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"DAG 태스크 테스트: {dag_id}.{task_id} ({execution_date})")
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 
                'airflow-webserver', 'airflow', 'tasks', 'test', 
                dag_id, task_id, execution_date
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 태스크 테스트 성공")
                print("=== 테스트 출력 ===")
                print(result.stdout)
            else:
                print(f"❌ 태스크 테스트 실패: {result.stderr}")
                
        except Exception as e:
            print(f"태스크 테스트 중 오류: {e}")
    
    def show_logs(self, dag_id, task_id, execution_date=None):
        """DAG 태스크 로그 조회"""
        if not execution_date:
            execution_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"태스크 로그 조회: {dag_id}.{task_id} ({execution_date})")
        
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 
                'airflow-webserver', 'airflow', 'tasks', 'logs', 
                dag_id, task_id, execution_date
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            print("=== 태스크 로그 ===")
            print(result.stdout)
            
            if result.stderr:
                print("=== 오류 로그 ===")
                print(result.stderr)
                
        except Exception as e:
            print(f"로그 조회 중 오류: {e}")
    
    def backup_metadata(self):
        """메타데이터 백업"""
        backup_dir = self.project_root / 'data' / 'backup' / 'airflow'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'airflow_metadata_backup_{timestamp}.sql'
        
        print(f"Airflow 메타데이터 백업 중: {backup_file}")
        
        try:
            # PostgreSQL 백업
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 'postgres',
                'pg_dump', '-U', 'airflow', '-d', 'airflow'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                with open(backup_file, 'w') as f:
                    f.write(result.stdout)
                print(f"✅ 백업 완료: {backup_file}")
                return backup_file
            else:
                print(f"❌ 백업 실패: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"백업 중 오류: {e}")
            return None
    
    def validate_dags(self):
        """DAG 파일 유효성 검증"""
        print("=== DAG 파일 유효성 검증 ===")
        
        dag_files = list(self.airflow_dir.glob('dags/*.py'))
        
        if not dag_files:
            print("DAG 파일을 찾을 수 없습니다.")
            return False
        
        all_valid = True
        
        for dag_file in dag_files:
            try:
                print(f"검증 중: {dag_file.name}")
                
                result = subprocess.run([
                    'python3', '-m', 'py_compile', str(dag_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"  ✅ {dag_file.name} - 구문 유효")
                else:
                    print(f"  ❌ {dag_file.name} - 구문 오류: {result.stderr}")
                    all_valid = False
                    
            except Exception as e:
                print(f"  ❌ {dag_file.name} - 검증 오류: {e}")
                all_valid = False
        
        if all_valid:
            print("\n✅ 모든 DAG 파일이 유효합니다.")
        else:
            print("\n❌ 일부 DAG 파일에 오류가 있습니다.")
        
        return all_valid
    
    def get_dag_info(self, dag_id):
        """특정 DAG 상세 정보 조회"""
        print(f"=== DAG 정보: {dag_id} ===")
        
        try:
            # DAG 정보 조회
            result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 
                'airflow-webserver', 'airflow', 'dags', 'show', dag_id
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("DAG 구조:")
                print(result.stdout)
            else:
                print(f"DAG 정보 조회 실패: {result.stderr}")
                
            # 최근 실행 기록 조회
            runs_result = subprocess.run([
                'docker-compose', '-f', str(self.compose_file), 'exec', 
                'airflow-webserver', 'airflow', 'dags', 'list-runs', 
                '-d', dag_id, '--limit', '5'
            ], cwd=self.airflow_dir, capture_output=True, text=True)
            
            if runs_result.returncode == 0:
                print("\n최근 실행 기록:")
                print(runs_result.stdout)
                
        except Exception as e:
            print(f"DAG 정보 조회 중 오류: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Airflow 운영 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 시작 명령어
    start_parser = subparsers.add_parser('start', help='Airflow 서비스 시작')
    
    # 중지 명령어
    stop_parser = subparsers.add_parser('stop', help='Airflow 서비스 중지')
    
    # 재시작 명령어
    restart_parser = subparsers.add_parser('restart', help='Airflow 서비스 재시작')
    
    # 상태 확인 명령어
    status_parser = subparsers.add_parser('status', help='DAG 상태 확인')
    status_parser.add_argument('--dag-id', help='특정 DAG ID')
    
    # DAG 목록 명령어
    list_parser = subparsers.add_parser('list', help='DAG 목록 조회')
    
    # DAG 트리거 명령어
    trigger_parser = subparsers.add_parser('trigger', help='DAG 수동 트리거')
    trigger_parser.add_argument('dag_id', help='DAG ID')
    trigger_parser.add_argument('--execution-date', help='실행 날짜 (YYYY-MM-DD)')
    
    # DAG 테스트 명령어
    test_parser = subparsers.add_parser('test', help='DAG 태스크 테스트')
    test_parser.add_argument('dag_id', help='DAG ID')
    test_parser.add_argument('task_id', help='태스크 ID')
    test_parser.add_argument('--execution-date', help='실행 날짜 (YYYY-MM-DD)')
    
    # 로그 조회 명령어
    logs_parser = subparsers.add_parser('logs', help='태스크 로그 조회')
    logs_parser.add_argument('dag_id', help='DAG ID')
    logs_parser.add_argument('task_id', help='태스크 ID')
    logs_parser.add_argument('--execution-date', help='실행 날짜 (YYYY-MM-DD)')
    
    # 백업 명령어
    backup_parser = subparsers.add_parser('backup', help='메타데이터 백업')
    
    # 검증 명령어
    validate_parser = subparsers.add_parser('validate', help='DAG 파일 유효성 검증')
    
    # DAG 정보 명령어
    info_parser = subparsers.add_parser('info', help='DAG 상세 정보')
    info_parser.add_argument('dag_id', help='DAG ID')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    manager = AirflowManager()
    
    try:
        if args.command == 'start':
            success = manager.start_airflow()
            sys.exit(0 if success else 1)
            
        elif args.command == 'stop':
            success = manager.stop_airflow()
            sys.exit(0 if success else 1)
            
        elif args.command == 'restart':
            success = manager.restart_airflow()
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            manager.get_dag_status(args.dag_id)
            
        elif args.command == 'list':
            manager.list_dags()
            
        elif args.command == 'trigger':
            manager.trigger_dag(args.dag_id, args.execution_date)
            
        elif args.command == 'test':
            manager.test_dag(args.dag_id, args.task_id, args.execution_date)
            
        elif args.command == 'logs':
            manager.show_logs(args.dag_id, args.task_id, args.execution_date)
            
        elif args.command == 'backup':
            manager.backup_metadata()
            
        elif args.command == 'validate':
            valid = manager.validate_dags()
            sys.exit(0 if valid else 1)
            
        elif args.command == 'info':
            manager.get_dag_info(args.dag_id)
            
        else:
            print(f"알 수 없는 명령어: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n작업이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

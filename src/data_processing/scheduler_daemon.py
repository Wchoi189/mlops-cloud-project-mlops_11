#!/usr/bin/env python3
"""
TMDB 데이터 수집 스케줄러 데몬
시스템 서비스로 실행되어 백그라운드에서 지속적으로 동작
"""

import signal
import sys
import os
import logging
from pathlib import Path
import json
import time
from datetime import datetime

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from data_processing.scheduler import TMDBDataScheduler
except ImportError:
    # 메인 스케줄러 import 실패 시 간단한 버전 사용
    from data_processing.simple_scheduler import TMDBDataScheduler

class SchedulerDaemon:
    def __init__(self):
        self.scheduler = TMDBDataScheduler()
        self.setup_signal_handlers()
        self.setup_logging()
        self.running = False
    
    def setup_signal_handlers(self):
        """시스템 시그널 핸들러 설정"""
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
        signal.signal(signal.SIGINT, self.graceful_shutdown)
    
    def setup_logging(self):
        """데몬 로깅 설정"""
        log_file = project_root / 'logs' / 'scheduler_daemon.log'
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file)),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def graceful_shutdown(self, signum, frame):
        """우아한 종료 처리"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if hasattr(self.scheduler, 'stop_scheduler'):
            self.scheduler.stop_scheduler()
        sys.exit(0)
    
    def create_status_file(self, status="running"):
        """상태 파일 생성"""
        status_file = project_root / 'logs' / 'scheduler_status.json'
        status_data = {
            'status': status,
            'pid': os.getpid(),
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def run(self):
        """데몬 메인 실행"""
        try:
            self.logger.info("TMDB 스케줄러 데몬 시작")
            
            # PID 파일 생성
            pid_file = project_root / 'logs' / 'scheduler_daemon.pid'
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # 상태 파일 생성
            self.create_status_file("running")
            
            # 스케줄러 시작
            self.scheduler.setup_jobs()
            self.running = True
            
            # 스케줄러 실행 (간단한 루프)
            self.logger.info("스케줄러 루프 시작")
            while self.running:
                try:
                    import schedule
                    schedule.run_pending()
                    time.sleep(30)  # 30초마다 체크
                    
                    # 상태 파일 업데이트
                    self.create_status_file("running")
                    
                except KeyboardInterrupt:
                    self.logger.info("키보드 인터럽트 수신")
                    break
                except Exception as e:
                    self.logger.error(f"스케줄러 실행 중 오류: {e}")
                    time.sleep(60)  # 오류 시 1분 대기
            
        except Exception as e:
            self.logger.error(f"데몬 실행 실패: {e}")
            self.create_status_file("failed")
            sys.exit(1)
        finally:
            # 정리 작업
            self.create_status_file("stopped")
            pid_file = project_root / 'logs' / 'scheduler_daemon.pid'
            if pid_file.exists():
                pid_file.unlink()
            self.logger.info("스케줄러 데몬 종료")

if __name__ == "__main__":
    daemon = SchedulerDaemon()
    daemon.run()

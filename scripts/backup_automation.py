#!/usr/bin/env python3
"""
백업 자동화 스크립트
정기적인 백업 작업을 자동으로 실행
"""

import sys
import schedule
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

from data_processing.backup_manager import BackupManager

class BackupAutomation:
    """백업 자동화 관리자"""
    
    def __init__(self):
        self.backup_manager = BackupManager()
        self.logger = logging.getLogger(__name__)
        self.running = False
    
    def daily_backup_job(self):
        """일일 백업 작업"""
        try:
            self.logger.info("일일 자동 백업 시작")
            result = self.backup_manager.create_daily_backup()
            
            if result['success']:
                self.logger.info(f"일일 백업 성공: {len(result['files_backed_up'])}개 파일")
            else:
                self.logger.error(f"일일 백업 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"일일 백업 작업 실패: {e}")
    
    def weekly_backup_job(self):
        """주간 백업 작업"""
        try:
            self.logger.info("주간 자동 백업 시작")
            current_date = datetime.now()
            year = current_date.year
            week = current_date.isocalendar()[1]
            
            result = self.backup_manager.create_weekly_backup(year, week)
            
            if result['success']:
                self.logger.info(f"주간 백업 성공: {result['total_size_bytes']/1024/1024:.1f}MB")
            else:
                self.logger.error(f"주간 백업 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"주간 백업 작업 실패: {e}")
    
    def monthly_backup_job(self):
        """월간 백업 작업"""
        try:
            self.logger.info("월간 자동 백업 시작")
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            
            result = self.backup_manager.create_monthly_backup(year, month)
            
            if result['success']:
                self.logger.info(f"월간 백업 성공: {result['total_size_bytes']/1024/1024:.1f}MB")
            else:
                self.logger.error(f"월간 백업 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"월간 백업 작업 실패: {e}")
    
    def cleanup_job(self):
        """백업 정리 작업"""
        try:
            self.logger.info("백업 정리 작업 시작")
            result = self.backup_manager.cleanup_old_backups()
            
            if result['success']:
                freed_mb = result['total_space_freed_bytes'] / 1024 / 1024
                self.logger.info(f"백업 정리 성공: {freed_mb:.1f}MB 정리")
            else:
                self.logger.error(f"백업 정리 실패: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"백업 정리 작업 실패: {e}")
    
    def backup_verification_job(self):
        """백업 무결성 검증 작업"""
        try:
            self.logger.info("백업 무결성 검증 시작")
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            result = self.backup_manager.verify_backup_integrity(yesterday)
            
            if result['success']:
                self.logger.info(f"백업 검증 성공: {len(result['verified_files'])}개 파일 검증")
            else:
                self.logger.warning(f"백업 검증 이슈: {len(result['integrity_issues'])}개 문제 발견")
                for issue in result['integrity_issues']:
                    self.logger.warning(f"  - {issue}")
                    
        except Exception as e:
            self.logger.error(f"백업 검증 작업 실패: {e}")
    
    def setup_schedule(self):
        """백업 스케줄 설정"""
        # 일일 백업: 매일 새벽 1시
        schedule.every().day.at("01:00").do(self.daily_backup_job)
        
        # 주간 백업: 매주 일요일 새벽 2시
        schedule.every().sunday.at("02:00").do(self.weekly_backup_job)
        
        # 월간 백업: 매월 1일 새벽 3시
        schedule.every().month.do(self.monthly_backup_job)
        
        # 백업 정리: 매주 화요일 새벽 4시
        schedule.every().tuesday.at("04:00").do(self.cleanup_job)
        
        # 백업 검증: 매일 새벽 5시
        schedule.every().day.at("05:00").do(self.backup_verification_job)
        
        self.logger.info("백업 스케줄 설정 완료")
    
    def run_automation(self):
        """백업 자동화 실행"""
        self.running = True
        self.setup_schedule()
        
        self.logger.info("백업 자동화 시작")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    
    def stop_automation(self):
        """백업 자동화 중지"""
        self.running = False
        self.logger.info("백업 자동화 중지")

def main():
    """메인 실행 함수"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description='백업 자동화 스크립트')
    parser.add_argument('command', choices=['start', 'test'], help='실행 명령')
    parser.add_argument('--test-type', choices=['daily', 'weekly', 'monthly', 'cleanup', 'verify'],
                       help='테스트할 백업 유형')
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/backup_automation.log'),
            logging.StreamHandler()
        ]
    )
    
    automation = BackupAutomation()
    
    if args.command == 'start':
        # 자동화 시작
        def signal_handler(signum, frame):
            automation.stop_automation()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            automation.run_automation()
        except KeyboardInterrupt:
            automation.stop_automation()
            
    elif args.command == 'test':
        # 테스트 실행
        if args.test_type == 'daily':
            automation.daily_backup_job()
        elif args.test_type == 'weekly':
            automation.weekly_backup_job()
        elif args.test_type == 'monthly':
            automation.monthly_backup_job()
        elif args.test_type == 'cleanup':
            automation.cleanup_job()
        elif args.test_type == 'verify':
            automation.backup_verification_job()
        else:
            print("테스트 유형을 지정하세요: --test-type {daily|weekly|monthly|cleanup|verify}")

if __name__ == "__main__":
    main()

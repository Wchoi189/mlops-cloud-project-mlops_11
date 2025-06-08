#!/usr/bin/env python3
"""
품질 관리 자동화 스크립트
데이터 품질 검증, 이상 탐지, 자동 정제를 통합 관리
"""

import sys
import schedule
import time
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

from data_processing.quality_validator import DataQualityValidator
from data_processing.anomaly_detector import AnomalyDetector
from data_processing.data_cleaner import DataCleaner
from data_processing.metadata_manager import MetadataManager

class QualityAutomation:
    """품질 관리 자동화"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.validator = DataQualityValidator()
        self.anomaly_detector = AnomalyDetector()
        self.data_cleaner = DataCleaner()
        self.metadata_manager = MetadataManager()
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # 품질 자동화 설정
        self.config = {
            'auto_clean_threshold': 70,  # 품질 점수 70점 미만 시 자동 정제
            'alert_threshold': 60,       # 품질 점수 60점 미만 시 알림
            'anomaly_alert_threshold': 5, # 이상 현상 5개 이상 시 알림
            'quality_report_retention_days': 30
        }
    
    def daily_quality_check_job(self):
        """일일 품질 검사 작업"""
        try:
            self.logger.info("일일 품질 검사 시작")
            
            # 최근 수집된 파일들 찾기
            today = datetime.now().strftime('%Y%m%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            
            daily_files = []
            for date_str in [today, yesterday]:
                daily_files.extend(self._find_daily_files(date_str))
            
            if not daily_files:
                self.logger.warning("검사할 일일 데이터 파일이 없습니다")
                return
            
            total_quality_scores = []
            all_reports = []
            
            # 각 파일 품질 검증
            for file_path in daily_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    movies = data.get('movies', data.get('results', []))
                    if not movies:
                        continue
                    
                    # 품질 검증 실행
                    batch_results = self.validator.validate_batch_data(movies)
                    quality_score = self._calculate_file_quality_score(batch_results)
                    total_quality_scores.append(quality_score)
                    
                    # 품질 리포트 생성
                    report = {
                        'file_path': str(file_path),
                        'validation_date': datetime.now().isoformat(),
                        'quality_score': quality_score,
                        'batch_results': batch_results
                    }
                    all_reports.append(report)
                    
                    # 품질 점수에 따른 자동 처리
                    if quality_score < self.config['auto_clean_threshold']:
                        self.logger.info(f"품질 점수 낮음 ({quality_score:.1f}), 자동 정제 실행: {file_path}")
                        self._auto_clean_file(file_path, movies)
                    
                    if quality_score < self.config['alert_threshold']:
                        self.logger.warning(f"품질 알림: {file_path} 품질 점수 {quality_score:.1f}")
                        self._send_quality_alert(file_path, quality_score, batch_results)
                    
                except Exception as e:
                    self.logger.error(f"파일 품질 검사 실패 {file_path}: {e}")
                    continue
            
            # 전체 품질 요약
            if total_quality_scores:
                avg_quality = sum(total_quality_scores) / len(total_quality_scores)
                self.logger.info(f"일일 평균 품질 점수: {avg_quality:.1f} ({len(daily_files)}개 파일)")
                
                # 일일 품질 리포트 저장
                self._save_daily_quality_report(all_reports, avg_quality)
            
        except Exception as e:
            self.logger.error(f"일일 품질 검사 실패: {e}")
    
    def anomaly_detection_job(self):
        """이상 탐지 작업"""
        try:
            self.logger.info("이상 탐지 분석 시작")
            
            # 최근 데이터 수집
            collection_stats = self._get_recent_collection_stats(days=7)
            quality_reports = self._get_recent_quality_reports(days=7)
            performance_logs = self._get_recent_performance_logs(days=1)
            error_logs = self._get_recent_error_logs(days=1)
            file_metadata = self._get_recent_file_metadata(days=1)
            
            # 종합 이상 탐지 실행
            anomaly_result = self.anomaly_detector.run_comprehensive_analysis(
                collection_stats=collection_stats,
                quality_reports=quality_reports,
                performance_logs=performance_logs,
                error_logs=error_logs,
                file_metadata=file_metadata
            )
            
            # 이상 현상 알림
            total_anomalies = anomaly_result['analysis_summary']['total_anomalies']
            critical_anomalies = anomaly_result['analysis_summary']['critical_anomalies']
            
            if total_anomalies >= self.config['anomaly_alert_threshold']:
                self.logger.warning(f"이상 현상 다수 탐지: {total_anomalies}개 (심각: {critical_anomalies}개)")
                self._send_anomaly_alert(anomaly_result)
            else:
                self.logger.info(f"이상 탐지 완료: {total_anomalies}개 이상 현상")
            
        except Exception as e:
            self.logger.error(f"이상 탐지 작업 실패: {e}")
    
    def auto_cleaning_job(self):
        """자동 정제 작업"""
        try:
            self.logger.info("자동 정제 작업 시작")
            
            # 정제가 필요한 파일들 찾기
            raw_files = list(self.data_dir.glob('raw/**/*.json'))
            files_to_clean = []
            
            for file_path in raw_files:
                # 이미 정제된 파일인지 확인
                cleaned_version = self._get_cleaned_version_path(file_path)
                if cleaned_version.exists():
                    continue
                
                # 파일이 최근 생성되었는지 확인 (24시간 이내)
                file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > timedelta(days=1):
                    continue
                
                files_to_clean.append(file_path)
            
            cleaned_count = 0
            
            for file_path in files_to_clean:
                try:
                    # 파일 정제 실행
                    result = self.data_cleaner.clean_file(file_path)
                    
                    cleaning_stats = result['cleaning_summary']['statistics']
                    retention_rate = cleaning_stats['retention_rate']
                    
                    self.logger.info(f"자동 정제 완료: {file_path.name} "
                                   f"({cleaning_stats['final_records']}/{cleaning_stats['original_records']}개, "
                                   f"보존율 {retention_rate:.1f}%)")
                    
                    cleaned_count += 1
                    
                    # 메타데이터 업데이트
                    self._update_cleaning_metadata(file_path, result)
                    
                except Exception as e:
                    self.logger.error(f"파일 자동 정제 실패 {file_path}: {e}")
                    continue
            
            self.logger.info(f"자동 정제 작업 완료: {cleaned_count}개 파일 정제")
            
        except Exception as e:
            self.logger.error(f"자동 정제 작업 실패: {e}")
    
    def metadata_sync_job(self):
        """메타데이터 동기화 작업"""
        try:
            self.logger.info("메타데이터 동기화 시작")
            
            # 고아 메타데이터 정리
            cleanup_result = self.metadata_manager.cleanup_orphaned_metadata()
            cleaned_files = len(cleanup_result['cleaned_files'])
            
            if cleaned_files > 0:
                self.logger.info(f"고아 메타데이터 정리: {cleaned_files}개 파일")
            
            # 누락된 메타데이터 생성
            data_files = list(self.data_dir.glob('**/*.json'))
            created_count = 0
            
            for file_path in data_files:
                if 'metadata' in str(file_path) or 'backup' in str(file_path):
                    continue
                
                # 메타데이터 존재 여부 확인
                existing_metadata = self.metadata_manager.get_file_metadata(file_path)
                if existing_metadata is None:
                    try:
                        # 메타데이터 생성
                        self.metadata_manager.create_file_metadata(
                            file_path,
                            data_type='raw' if 'raw' in str(file_path) else 'processed'
                        )
                        created_count += 1
                    except Exception as e:
                        self.logger.error(f"메타데이터 생성 실패 {file_path}: {e}")
            
            if created_count > 0:
                self.logger.info(f"누락 메타데이터 생성: {created_count}개 파일")
            
            # 데이터 카탈로그 갱신
            catalog = self.metadata_manager.generate_data_catalog()
            self.logger.info(f"데이터 카탈로그 갱신: {catalog['total_files']}개 파일")
            
        except Exception as e:
            self.logger.error(f"메타데이터 동기화 실패: {e}")
    
    def quality_report_cleanup_job(self):
        """오래된 품질 리포트 정리"""
        try:
            self.logger.info("품질 리포트 정리 시작")
            
            cutoff_date = datetime.now() - timedelta(days=self.config['quality_report_retention_days'])
            report_dirs = [
                self.data_dir / 'raw' / 'metadata' / 'quality_reports',
                self.data_dir / 'raw' / 'metadata' / 'anomalies'
            ]
            
            total_cleaned = 0
            
            for report_dir in report_dirs:
                if not report_dir.exists():
                    continue
                
                for report_file in report_dir.glob('*.json'):
                    try:
                        file_date = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if file_date < cutoff_date:
                            report_file.unlink()
                            total_cleaned += 1
                    except Exception as e:
                        self.logger.error(f"리포트 파일 정리 실패 {report_file}: {e}")
            
            if total_cleaned > 0:
                self.logger.info(f"오래된 품질 리포트 정리: {total_cleaned}개 파일")
            
        except Exception as e:
            self.logger.error(f"품질 리포트 정리 실패: {e}")
    
    def _find_daily_files(self, date_str: str) -> List[Path]:
        """특정 날짜의 데이터 파일 찾기"""
        files = []
        search_dirs = [
            self.data_dir / 'raw' / 'movies' / 'daily',
            self.data_dir / 'raw' / 'movies' / 'trending'
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                files.extend(search_dir.glob(f'*{date_str}*.json'))
        
        return files
    
    def _calculate_file_quality_score(self, batch_results: Dict) -> float:
        """파일 품질 점수 계산"""
        if batch_results['total_movies'] == 0:
            return 0.0
        
        valid_rate = batch_results['valid_movies'] / batch_results['total_movies']
        quality_dist = batch_results['quality_distribution']
        total = batch_results['total_movies']
        
        if total == 0:
            return 0.0
        
        # 가중 평균 품질 점수
        weighted_score = (
            quality_dist['excellent'] * 95 +
            quality_dist['good'] * 85 +
            quality_dist['fair'] * 75 +
            quality_dist['poor'] * 50
        ) / total
        
        # 유효성 비율로 조정
        final_score = weighted_score * valid_rate
        
        return round(final_score, 1)
    
    def _auto_clean_file(self, file_path: Path, movies_data: List[Dict]):
        """파일 자동 정제"""
        try:
            result = self.data_cleaner.clean_batch_data(movies_data)
            
            # 정제된 데이터 저장
            cleaned_filename = f"cleaned_{file_path.name}"
            self.data_cleaner.save_cleaned_data(result, cleaned_filename)
            
            self.logger.info(f"자동 정제 완료: {file_path} -> {cleaned_filename}")
            
        except Exception as e:
            self.logger.error(f"자동 정제 실패 {file_path}: {e}")
    
    def _send_quality_alert(self, file_path: Path, quality_score: float, batch_results: Dict):
        """품질 알림 발송"""
        alert_info = {
            'alert_type': 'low_quality',
            'file_path': str(file_path),
            'quality_score': quality_score,
            'threshold': self.config['alert_threshold'],
            'issues': batch_results.get('common_issues', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        # 알림 로그 저장
        alert_file = self.data_dir / 'raw' / 'metadata' / 'alerts' / f"quality_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert_info, f, ensure_ascii=False, indent=2, default=str)
    
    def _send_anomaly_alert(self, anomaly_result: Dict):
        """이상 탐지 알림 발송"""
        alert_info = {
            'alert_type': 'anomaly_detection',
            'total_anomalies': anomaly_result['analysis_summary']['total_anomalies'],
            'critical_anomalies': anomaly_result['analysis_summary']['critical_anomalies'],
            'recommendations': anomaly_result['recommendations'],
            'timestamp': datetime.now().isoformat()
        }
        
        # 알림 로그 저장
        alert_file = self.data_dir / 'raw' / 'metadata' / 'alerts' / f"anomaly_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert_info, f, ensure_ascii=False, indent=2, default=str)
    
    def _save_daily_quality_report(self, all_reports: List[Dict], avg_quality: float):
        """일일 품질 리포트 저장"""
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'average_quality_score': avg_quality,
            'total_files_checked': len(all_reports),
            'file_reports': all_reports,
            'quality_summary': {
                'excellent_files': len([r for r in all_reports if r['quality_score'] >= 90]),
                'good_files': len([r for r in all_reports if 80 <= r['quality_score'] < 90]),
                'fair_files': len([r for r in all_reports if 70 <= r['quality_score'] < 80]),
                'poor_files': len([r for r in all_reports if r['quality_score'] < 70])
            }
        }
        
        report_file = self.data_dir / 'raw' / 'metadata' / 'quality_reports' / f"daily_quality_{datetime.now().strftime('%Y%m%d')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    def _get_cleaned_version_path(self, original_path: Path) -> Path:
        """정제된 버전 파일 경로 반환"""
        cleaned_dir = self.data_dir / 'processed' / 'cleaned'
        return cleaned_dir / f"cleaned_{original_path.name}"
    
    def _update_cleaning_metadata(self, file_path: Path, cleaning_result: Dict):
        """정제 메타데이터 업데이트"""
        try:
            metadata_updates = {
                'cleaning_info': {
                    'cleaned_date': datetime.now().isoformat(),
                    'cleaning_stats': cleaning_result['cleaning_summary']['statistics'],
                    'quality_improvement': True
                }
            }
            
            self.metadata_manager.update_file_metadata(file_path, metadata_updates)
            
        except Exception as e:
            self.logger.error(f"정제 메타데이터 업데이트 실패 {file_path}: {e}")
    
    def _get_recent_collection_stats(self, days: int) -> List[Dict]:
        """최근 수집 통계 조회"""
        try:
            stats_dir = self.data_dir / 'raw' / 'metadata' / 'collection_stats'
            if not stats_dir.exists():
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_stats = []
            
            for stats_file in stats_dir.glob('*.json'):
                try:
                    file_date = datetime.fromtimestamp(stats_file.stat().st_mtime)
                    if file_date >= cutoff_date:
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                            recent_stats.append(stats)
                except Exception:
                    continue
            
            return recent_stats
            
        except Exception as e:
            self.logger.error(f"수집 통계 조회 실패: {e}")
            return []
    
    def _get_recent_quality_reports(self, days: int) -> List[Dict]:
        """최근 품질 리포트 조회"""
        try:
            reports_dir = self.data_dir / 'raw' / 'metadata' / 'quality_reports'
            if not reports_dir.exists():
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_reports = []
            
            for report_file in reports_dir.glob('*.json'):
                try:
                    file_date = datetime.fromtimestamp(report_file.stat().st_mtime)
                    if file_date >= cutoff_date:
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report = json.load(f)
                            recent_reports.append(report)
                except Exception:
                    continue
            
            return recent_reports
            
        except Exception as e:
            self.logger.error(f"품질 리포트 조회 실패: {e}")
            return []
    
    def _get_recent_performance_logs(self, days: int) -> List[Dict]:
        """최근 성능 로그 조회"""
        # 실제 구현에서는 로그 파일을 파싱하여 성능 데이터 추출
        return []
    
    def _get_recent_error_logs(self, days: int) -> List[Dict]:
        """최근 에러 로그 조회"""
        # 실제 구현에서는 로그 파일을 파싱하여 에러 데이터 추출
        return []
    
    def _get_recent_file_metadata(self, days: int) -> List[Dict]:
        """최근 파일 메타데이터 조회"""
        try:
            metadata_dir = self.data_dir / 'raw' / 'metadata' / 'catalogs'
            if not metadata_dir.exists():
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_metadata = []
            
            for metadata_file in metadata_dir.rglob('*_file_metadata.json'):
                try:
                    file_date = datetime.fromtimestamp(metadata_file.stat().st_mtime)
                    if file_date >= cutoff_date:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            recent_metadata.append(metadata)
                except Exception:
                    continue
            
            return recent_metadata
            
        except Exception as e:
            self.logger.error(f"파일 메타데이터 조회 실패: {e}")
            return []
    
    def setup_schedule(self):
        """품질 관리 스케줄 설정"""
        # 일일 품질 검사: 매일 오전 8시
        schedule.every().day.at("08:00").do(self.daily_quality_check_job)
        
        # 이상 탐지: 매일 오전 9시
        schedule.every().day.at("09:00").do(self.anomaly_detection_job)
        
        # 자동 정제: 매일 오전 10시
        schedule.every().day.at("10:00").do(self.auto_cleaning_job)
        
        # 메타데이터 동기화: 매일 오후 6시
        schedule.every().day.at("18:00").do(self.metadata_sync_job)
        
        # 품질 리포트 정리: 매주 일요일 오후 11시
        schedule.every().sunday.at("23:00").do(self.quality_report_cleanup_job)
        
        self.logger.info("품질 관리 스케줄 설정 완료")
    
    def run_automation(self):
        """품질 관리 자동화 실행"""
        self.running = True
        self.setup_schedule()
        
        self.logger.info("품질 관리 자동화 시작")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    
    def stop_automation(self):
        """품질 관리 자동화 중지"""
        self.running = False
        self.logger.info("품질 관리 자동화 중지")

def main():
    """메인 실행 함수"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description='품질 관리 자동화 스크립트')
    parser.add_argument('command', choices=['start', 'test'], help='실행 명령')
    parser.add_argument('--test-type', choices=['quality', 'anomaly', 'cleaning', 'metadata', 'cleanup'],
                       help='테스트할 작업 유형')
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/quality_automation.log'),
            logging.StreamHandler()
        ]
    )
    
    automation = QualityAutomation()
    
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
        if args.test_type == 'quality':
            automation.daily_quality_check_job()
        elif args.test_type == 'anomaly':
            automation.anomaly_detection_job()
        elif args.test_type == 'cleaning':
            automation.auto_cleaning_job()
        elif args.test_type == 'metadata':
            automation.metadata_sync_job()
        elif args.test_type == 'cleanup':
            automation.quality_report_cleanup_job()
        else:
            print("테스트 유형을 지정하세요: --test-type {quality|anomaly|cleaning|metadata|cleanup}")

if __name__ == "__main__":
    main()

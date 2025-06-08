# src/data_processing/quality_reporter.py
"""
데이터 품질 리포트 생성 시스템
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_processing.quality_validator import DataQualityValidator, AnomalyDetector, DataCleaner
from data.file_formats import DataFileManager

class QualityReporter:
    """데이터 품질 리포트 생성 클래스"""
    
    def __init__(self):
        self.validator = DataQualityValidator()
        self.anomaly_detector = AnomalyDetector()
        self.data_cleaner = DataCleaner()
        self.file_manager = DataFileManager()
        self.logger = logging.getLogger(__name__)
        
        # 기준선 로드 시도
        baseline_file = Path("data/quality_baseline.json")
        if baseline_file.exists():
            self.anomaly_detector.load_baseline(str(baseline_file))
    
    def generate_daily_report(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """일간 품질 리포트 생성"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"일간 품질 리포트 생성 시작: {date_str}")
        
        # 해당 날짜 데이터 로드
        daily_files = self._find_daily_files(date_str)
        if not daily_files:
            return {'status': 'no_data', 'date': date_str}
        
        all_movies = []
        collection_stats = {}
        
        for file_path in daily_files:
            try:
                data = self.file_manager.load_data(file_path)
                if data and isinstance(data, dict):
                    if 'movies' in data:
                        all_movies.extend(data['movies'])
                    if 'collection_info' in data:
                        collection_stats.update(data['collection_info'])
            except Exception as e:
                self.logger.error(f"파일 로드 실패 {file_path}: {e}")
                continue
        
        if not all_movies:
            return {'status': 'no_movies', 'date': date_str}
        
        # 품질 분석 실행
        batch_results = self.validator.validate_batch_data(all_movies)
        anomaly_results = self.anomaly_detector.detect_rating_anomalies(all_movies)
        popularity_anomalies = self.anomaly_detector.detect_popularity_anomalies(all_movies)
        collection_anomalies = self.anomaly_detector.detect_collection_anomalies(collection_stats)
        
        # 데이터 정제 분석
        cleaned_movies, cleaning_report = self.data_cleaner.apply_batch_cleaning(all_movies)
        
        # 리포트 생성
        report = {
            'report_date': date_str,
            'generation_time': datetime.now().isoformat(),
            'data_summary': {
                'total_files_processed': len(daily_files),
                'total_movies_analyzed': len(all_movies),
                'unique_movies': len(set(m.get('id') for m in all_movies if m.get('id'))),
                'collection_stats': collection_stats
            },
            'quality_summary': {
                'overall_quality_score': self._calculate_overall_quality(batch_results),
                'valid_rate': batch_results['valid_movies'] / batch_results['total_movies'] * 100 if batch_results['total_movies'] > 0 else 0,
                'quality_distribution': batch_results['quality_distribution'],
                'common_issues': batch_results['common_issues'],
                'recommendations': batch_results['recommendations']
            },
            'anomaly_analysis': {
                'rating_anomalies': anomaly_results.get('anomalies', []),
                'popularity_anomalies': popularity_anomalies.get('anomalies', []),
                'collection_anomalies': collection_anomalies.get('anomalies', []),
                'total_anomalies': len(anomaly_results.get('anomalies', [])) + 
                                  len(popularity_anomalies.get('anomalies', [])) + 
                                  len(collection_anomalies.get('anomalies', []))
            },
            'cleaning_analysis': {
                'cleaning_report': cleaning_report,
                'cleanable_movies': len(cleaned_movies),
                'cleaning_success_rate': (cleaning_report['successfully_cleaned'] / cleaning_report['total_processed'] * 100) if cleaning_report['total_processed'] > 0 else 0
            },
            'data_health': self._assess_data_health(batch_results, anomaly_results, popularity_anomalies, collection_anomalies)
        }
        
        # 기준선 업데이트
        self.anomaly_detector.update_baseline(all_movies, collection_stats)
        
        # 리포트 저장
        self._save_report(report, date_str)
        
        return report
    
    def generate_weekly_summary(self, week_start_date: str) -> Dict[str, Any]:
        """주간 요약 리포트 생성"""
        self.logger.info(f"주간 요약 리포트 생성: {week_start_date}")
        
        # 주간 날짜 범위 계산
        start_dt = datetime.strptime(week_start_date, '%Y%m%d')
        week_dates = [(start_dt + timedelta(days=i)).strftime('%Y%m%d') for i in range(7)]
        
        weekly_data = {
            'week_start': week_start_date,
            'daily_reports': [],
            'weekly_summary': {
                'total_movies': 0,
                'total_valid': 0,
                'average_quality_score': 0,
                'weekly_trends': {},
                'issues_summary': {}
            }
        }
        
        daily_scores = []
        all_issues = []
        
        for date_str in week_dates:
            daily_report = self.generate_daily_report(date_str)
            if daily_report.get('status') in ['no_data', 'no_movies']:
                continue
            
            weekly_data['daily_reports'].append(daily_report)
            weekly_data['weekly_summary']['total_movies'] += daily_report['data_summary']['total_movies_analyzed']
            weekly_data['weekly_summary']['total_valid'] += daily_report['quality_summary']['valid_rate'] * daily_report['data_summary']['total_movies_analyzed'] / 100
            
            daily_scores.append(daily_report['quality_summary']['overall_quality_score'])
            all_issues.extend(daily_report['quality_summary']['common_issues'].keys())
        
        if daily_scores:
            weekly_data['weekly_summary']['average_quality_score'] = sum(daily_scores) / len(daily_scores)
            
            # 주간 트렌드 분석
            weekly_data['weekly_summary']['weekly_trends'] = {
                'quality_trend': 'improving' if daily_scores[-1] > daily_scores[0] else 'declining' if daily_scores[-1] < daily_scores[0] else 'stable',
                'score_variance': max(daily_scores) - min(daily_scores),
                'best_day': week_dates[daily_scores.index(max(daily_scores))],
                'worst_day': week_dates[daily_scores.index(min(daily_scores))]
            }
            
            # 이슈 요약
            from collections import Counter
            issue_counts = Counter(all_issues)
            weekly_data['weekly_summary']['issues_summary'] = dict(issue_counts.most_common(5))
        
        # 주간 리포트 저장
        self._save_weekly_report(weekly_data, week_start_date)
        
        return weekly_data
    
    def generate_quality_dashboard_data(self) -> Dict[str, Any]:
        """품질 대시보드 데이터 생성"""
        self.logger.info("품질 대시보드 데이터 생성")
        
        # 최근 7일 데이터 수집
        recent_dates = [(datetime.now() - timedelta(days=i)).strftime('%Y%m%d') for i in range(7)]
        
        dashboard_data = {
            'last_updated': datetime.now().isoformat(),
            'time_series': {
                'dates': [],
                'quality_scores': [],
                'movie_counts': [],
                'anomaly_counts': []
            },
            'current_status': {
                'latest_quality_score': 0,
                'total_anomalies': 0,
                'data_health_grade': 'Unknown',
                'trending_issues': []
            },
            'statistics': {
                'total_movies_processed': 0,
                'average_quality_score': 0,
                'anomaly_detection_rate': 0,
                'data_cleaning_effectiveness': 0
            }
        }
        
        scores = []
        counts = []
        anomaly_counts = []
        all_issues = []
        
        for date_str in reversed(recent_dates):  # 날짜 순으로 정렬
            daily_report = self.generate_daily_report(date_str)
            if daily_report.get('status') in ['no_data', 'no_movies']:
                continue
            
            dashboard_data['time_series']['dates'].append(date_str)
            
            quality_score = daily_report['quality_summary']['overall_quality_score']
            movie_count = daily_report['data_summary']['total_movies_analyzed']
            anomaly_count = daily_report['anomaly_analysis']['total_anomalies']
            
            dashboard_data['time_series']['quality_scores'].append(quality_score)
            dashboard_data['time_series']['movie_counts'].append(movie_count)
            dashboard_data['time_series']['anomaly_counts'].append(anomaly_count)
            
            scores.append(quality_score)
            counts.append(movie_count)
            anomaly_counts.append(anomaly_count)
            all_issues.extend(daily_report['quality_summary']['common_issues'].keys())
        
        if scores:
            # 현재 상태 업데이트
            dashboard_data['current_status'].update({
                'latest_quality_score': scores[-1],
                'total_anomalies': sum(anomaly_counts),
                'data_health_grade': self._get_health_grade(scores[-1]),
                'trending_issues': list(Counter(all_issues).most_common(3))
            })
            
            # 통계 업데이트
            dashboard_data['statistics'].update({
                'total_movies_processed': sum(counts),
                'average_quality_score': sum(scores) / len(scores),
                'anomaly_detection_rate': sum(anomaly_counts) / sum(counts) * 100 if sum(counts) > 0 else 0,
                'data_cleaning_effectiveness': 85.0  # 임시값, 실제로는 정제 성공률 계산
            })
        
        # 대시보드 데이터 저장
        self._save_dashboard_data(dashboard_data)
        
        return dashboard_data
    
    def _calculate_overall_quality(self, batch_results: Dict[str, Any]) -> float:
        """전체 품질 점수 계산"""
        quality_dist = batch_results['quality_distribution']
        total = batch_results['total_movies']
        
        if total == 0:
            return 0
        
        weighted_score = (
            quality_dist['excellent'] * 95 +
            quality_dist['good'] * 85 +
            quality_dist['fair'] * 75 +
            quality_dist['poor'] * 50
        ) / total
        
        return round(weighted_score, 2)
    
    def _assess_data_health(self, batch_results: Dict[str, Any], rating_anomalies: Dict[str, Any], 
                           popularity_anomalies: Dict[str, Any], collection_anomalies: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 건강도 평가"""
        health_score = 100
        issues = []
        
        # 품질 불량률 체크
        if batch_results['total_movies'] > 0:
            invalid_rate = batch_results['invalid_movies'] / batch_results['total_movies']
            if invalid_rate > 0.2:  # 20% 이상
                health_score -= 30
                issues.append("high_invalid_rate")
            elif invalid_rate > 0.1:  # 10% 이상
                health_score -= 15
                issues.append("moderate_invalid_rate")
        
        # 이상 탐지 결과 체크
        total_anomalies = (len(rating_anomalies.get('anomalies', [])) + 
                          len(popularity_anomalies.get('anomalies', [])) + 
                          len(collection_anomalies.get('anomalies', [])))
        
        if total_anomalies > 2:
            health_score -= 25
            issues.append("multiple_anomalies")
        elif total_anomalies > 0:
            health_score -= 10
            issues.append("minor_anomalies")
        
        # 데이터 완전성 체크
        if batch_results['total_movies'] < 50:  # 너무 적은 데이터
            health_score -= 20
            issues.append("insufficient_data")
        
        # 건강도 등급 결정
        if health_score >= 90:
            grade = "🟢 Excellent"
        elif health_score >= 80:
            grade = "🟡 Good"
        elif health_score >= 70:
            grade = "🟠 Fair"
        else:
            grade = "🔴 Poor"
        
        return {
            'health_score': max(0, health_score),
            'grade': grade,
            'issues': issues,
            'recommendations': self._generate_health_recommendations(issues)
        }
    
    def _generate_health_recommendations(self, issues: List[str]) -> List[str]:
        """건강도 기반 권장사항 생성"""
        recommendations = []
        
        if "high_invalid_rate" in issues:
            recommendations.append("데이터 품질이 매우 낮습니다. 수집 로직과 필터링 규칙을 점검하세요.")
        
        if "multiple_anomalies" in issues:
            recommendations.append("다수의 이상 패턴이 감지되었습니다. 데이터 소스를 점검하세요.")
        
        if "insufficient_data" in issues:
            recommendations.append("수집된 데이터가 부족합니다. 수집 범위를 확대하거나 수집 빈도를 높이세요.")
        
        if not issues:
            recommendations.append("데이터 품질이 양호합니다. 현재 수준을 유지하세요.")
        
        return recommendations
    
    def _get_health_grade(self, score: float) -> str:
        """점수에 따른 건강도 등급"""
        if score >= 90:
            return "🟢 Excellent"
        elif score >= 80:
            return "🟡 Good"
        elif score >= 70:
            return "🟠 Fair"
        else:
            return "🔴 Poor"
    
    def _find_daily_files(self, date_str: str) -> List[Path]:
        """해당 날짜 데이터 파일 찾기"""
        data_dir = Path('data/raw/movies')
        pattern = f"*{date_str}*.json"
        
        files = []
        for subdir in ['daily', 'trending', 'genre']:
            subdir_path = data_dir / subdir
            if subdir_path.exists():
                files.extend(subdir_path.glob(pattern))
        
        return files
    
    def _save_report(self, report: Dict[str, Any], date_str: str):
        """일간 리포트 저장"""
        report_dir = Path('data/raw/metadata/quality_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"daily_quality_report_{date_str}.json"
        success = self.file_manager.save_json(report, report_file)
        
        if success:
            # 최신 리포트 링크 생성
            latest_link = report_dir / "latest_quality_report.json"
            if latest_link.exists():
                latest_link.unlink()
            
            # Windows에서는 심볼릭 링크 대신 복사
            import shutil
            shutil.copy2(report_file, latest_link)
            
            self.logger.info(f"일간 품질 리포트 저장 완료: {report_file}")
    
    def _save_weekly_report(self, weekly_data: Dict[str, Any], week_start: str):
        """주간 리포트 저장"""
        report_dir = Path('data/raw/metadata/quality_reports/weekly')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"weekly_quality_summary_{week_start}.json"
        self.file_manager.save_json(weekly_data, report_file)
        self.logger.info(f"주간 품질 리포트 저장 완료: {report_file}")
    
    def _save_dashboard_data(self, dashboard_data: Dict[str, Any]):
        """대시보드 데이터 저장"""
        dashboard_dir = Path('data/processed/dashboard')
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        dashboard_file = dashboard_dir / "quality_dashboard.json"
        self.file_manager.save_json(dashboard_data, dashboard_file)
        self.logger.info(f"품질 대시보드 데이터 저장 완료: {dashboard_file}")

def generate_daily_quality_report(date_str: Optional[str] = None):
    """일간 품질 리포트 생성 편의 함수"""
    reporter = QualityReporter()
    return reporter.generate_daily_report(date_str)

def generate_quality_dashboard():
    """품질 대시보드 생성 편의 함수"""
    reporter = QualityReporter()
    return reporter.generate_quality_dashboard_data()

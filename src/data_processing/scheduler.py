"""
TMDB 데이터 수집 스케줄러
Python schedule 라이브러리 기반 자동화 시스템
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
from threading import Thread
import signal
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import traceback

from .tmdb_api_connector import TMDBAPIConnector
from .quality_validator import DataQualityValidator


class TMDBDataScheduler:
    """TMDB 데이터 수집 스케줄러"""
    
    def __init__(self):
        self.running = False
        self.logger = self._setup_logging()
        self.job_history = []
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'daily_collection_min': 100,
            'quality_rate_min': 80.0
        }
        
        # 스케줄러 상태 추적
        self.last_successful_jobs = {}
        self.failure_counts = {}
        
    def _setup_logging(self):
        """로깅 설정"""
        logger = logging.getLogger('tmdb_scheduler')
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / 'scheduler.log')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러  
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s | %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def setup_jobs(self):
        """스케줄 작업 설정"""
        self.logger.info("스케줄 작업 설정 중...")
        
        # 일일 수집: 매일 새벽 2시
        schedule.every().day.at("02:00").do(self._safe_job_wrapper, self.daily_collection, "daily_collection")
        
        # 주간 수집: 매주 일요일 새벽 3시  
        schedule.every().sunday.at("03:00").do(self._safe_job_wrapper, self.weekly_collection, "weekly_collection")
        
        # 시간별 트렌딩: 매시간 정각 (운영시간만)
        schedule.every().hour.at(":00").do(self._safe_job_wrapper, self.hourly_trending, "hourly_trending")
        
        # 월간 전체 갱신: 매월 1일 새벽 4시 (대안: 매일 체크하는 방식)
        schedule.every().day.at("04:00").do(self._safe_job_wrapper, self._monthly_check, "monthly_check")
        
        # 헬스체크: 매 10분마다
        schedule.every(10).minutes.do(self._safe_job_wrapper, self.health_check, "health_check")
        
        self.logger.info(f"총 {len(schedule.jobs)}개 작업이 스케줄되었습니다.")
        
    def _safe_job_wrapper(self, job_func, job_name):
        """작업 실행 래퍼 (에러 처리 및 로깅)"""
        job_id = self._record_job_start(job_name)
        
        try:
            result = job_func()
            self._record_job_success(job_id, job_name, result)
            return result
            
        except Exception as e:
            self._record_job_failure(job_id, job_name, str(e))
            self._handle_job_failure(job_name, str(e))
            raise
    
    def daily_collection(self):
        """매일 새벽 2시 실행되는 일일 데이터 수집"""
        self.logger.info("=== 일일 데이터 수집 시작 ===")
        
        connector = TMDBAPIConnector()
        validator = DataQualityValidator()
        
        try:
            # 신규 인기 영화 (최신 5페이지)
            popular_movies = []
            for page in range(1, 6):
                response = connector.get_popular_movies(page)
                if response and 'results' in response:
                    popular_movies.extend(response['results'])
                else:
                    break
            
            self.logger.info(f"인기 영화 수집: {len(popular_movies)}개")
            
            # 당일 트렌딩 영화
            trending_response = connector.get_trending_movies('day')
            trending_movies = trending_response.get('results', []) if trending_response else []
            self.logger.info(f"트렌딩 영화 수집: {len(trending_movies)}개")
            
            # 최신 개봉 영화
            latest_movies = []
            for page in range(1, 4):
                response = connector.get_latest_movies(page)
                if response and 'results' in response:
                    latest_movies.extend(response['results'])
                else:
                    break
            
            self.logger.info(f"최신 영화 수집: {len(latest_movies)}개")
            
            # 결과 통합 및 중복 제거
            all_movies = popular_movies + trending_movies + latest_movies
            unique_movies = self._remove_duplicates(all_movies)
            
            # 데이터 품질 검증
            batch_results = validator.validate_batch_data(unique_movies)
            valid_movies = [m for m in unique_movies if validator.validate_single_movie(m)[0]]
            
            # 결과 저장
            timestamp = datetime.now().strftime('%Y%m%d')
            collection_stats = {
                'collection_type': 'daily',
                'timestamp': timestamp,
                'total_collected': len(unique_movies),
                'total_valid': len(valid_movies),
                'quality_rate': len(valid_movies) / len(unique_movies) * 100 if unique_movies else 0,
                'sources': {
                    'popular': len(popular_movies),
                    'trending': len(trending_movies), 
                    'latest': len(latest_movies)
                }
            }
            
            self._save_collection_results(valid_movies, f"daily_{timestamp}", collection_stats)
            
            # 품질 검사
            if collection_stats['quality_rate'] < self.alert_thresholds['quality_rate_min']:
                self.logger.warning(f"품질 경고: 데이터 품질률이 {collection_stats['quality_rate']:.1f}%로 낮습니다.")
            
            if len(valid_movies) < self.alert_thresholds['daily_collection_min']:
                self.logger.warning(f"수집량 경고: 수집된 영화가 {len(valid_movies)}개로 적습니다.")
            
            self.logger.info(f"일일 수집 완료: {len(valid_movies)}개 영화 (품질률: {collection_stats['quality_rate']:.1f}%)")
            
            return collection_stats
            
        finally:
            connector.close()
    
    def weekly_collection(self):
        """매주 일요일 새벽 3시 실행되는 주간 종합 수집"""
        self.logger.info("=== 주간 종합 데이터 수집 시작 ===")
        
        connector = TMDBAPIConnector()
        validator = DataQualityValidator()
        
        try:
            all_movies = []
            
            # 장르별 순환 수집
            MAJOR_GENRES = {
                28: "액션", 35: "코미디", 18: "드라마", 
                27: "공포", 10749: "로맨스"
            }
            
            for genre_id, genre_name in MAJOR_GENRES.items():
                genre_movies = []
                for page in range(1, 11):  # 10페이지씩
                    response = connector.get_movies_by_genre(genre_id, page)
                    if response and 'results' in response:
                        genre_movies.extend(response['results'])
                    else:
                        break
                
                all_movies.extend(genre_movies)
                self.logger.info(f"{genre_name} 장르: {len(genre_movies)}개 수집")
            
            # 평점 높은 영화
            top_rated_movies = []
            for page in range(1, 11):
                response = connector.get_top_rated_movies(page)
                if response and 'results' in response:
                    # 평점 7.5 이상만 필터링
                    high_rated = [m for m in response['results'] if m.get('vote_average', 0) >= 7.5]
                    top_rated_movies.extend(high_rated)
                else:
                    break
            
            all_movies.extend(top_rated_movies)
            self.logger.info(f"평점 높은 영화: {len(top_rated_movies)}개 수집")
            
            # 주간 트렌딩
            weekly_trending_response = connector.get_trending_movies('week')
            weekly_trending = weekly_trending_response.get('results', []) if weekly_trending_response else []
            all_movies.extend(weekly_trending)
            
            # 중복 제거 및 품질 검증
            unique_movies = self._remove_duplicates(all_movies)
            validated_movies = [m for m in unique_movies if validator.validate_single_movie(m)[0]]
            
            # 주간 결과 저장
            week_number = datetime.now().isocalendar()[1]
            collection_stats = {
                'collection_type': 'weekly',
                'week_number': week_number,
                'timestamp': datetime.now().strftime('%Y%m%d'),
                'total_collected': len(unique_movies),
                'total_valid': len(validated_movies),
                'quality_rate': len(validated_movies) / len(unique_movies) * 100 if unique_movies else 0,
                'by_source': {
                    'genres': len(all_movies) - len(top_rated_movies) - len(weekly_trending),
                    'top_rated': len(top_rated_movies),
                    'trending': len(weekly_trending)
                }
            }
            
            self._save_collection_results(validated_movies, f"weekly_W{week_number}", collection_stats)
            
            self.logger.info(f"주간 수집 완료: {len(validated_movies)}개 영화")
            
            # 주간 리포트 생성
            self._generate_weekly_report(validated_movies, collection_stats)
            
            return collection_stats
            
        finally:
            connector.close()
    
    def hourly_trending(self):
        """매시간 정각 실행되는 트렌딩 데이터 수집"""
        # 운영 시간만 실행 (오전 8시 ~ 오후 10시)
        current_hour = datetime.now().hour
        if not (8 <= current_hour <= 22):
            return None
        
        self.logger.info("=== 시간별 트렌딩 수집 시작 ===")
        
        connector = TMDBAPIConnector()
        
        try:
            # 실시간 트렌딩 영화
            trending_response = connector.get_trending_movies('day')
            trending_movies = trending_response.get('results', []) if trending_response else []
            
            # 간단한 저장 (덮어쓰기 방식)
            timestamp = datetime.now().strftime('%Y%m%d_%H')
            collection_stats = {
                'collection_type': 'hourly_trending',
                'timestamp': timestamp,
                'hour': current_hour,
                'total_collected': len(trending_movies)
            }
            
            self._save_collection_results(trending_movies, f"trending_{timestamp}", collection_stats)
            
            self.logger.info(f"시간별 트렌딩 수집 완료: {len(trending_movies)}개 영화")
            
            return collection_stats
            
        finally:
            connector.close()
    
    def _monthly_check(self):
        """월간 갱신 체크 (매월 1일에만 실행)"""
        today = datetime.now()
        if today.day == 1:  # 매월 1일에만 실행
            return self.monthly_full_refresh()
        return None
    
    def monthly_full_refresh(self):
        """매월 1일 새벽 4시 실행되는 전체 데이터 갱신"""
        self.logger.info("=== 월간 전체 데이터 갱신 시작 ===")
        
        connector = TMDBAPIConnector()
        validator = DataQualityValidator()
        
        try:
            # 인기 영화 대량 수집 (1-50 페이지)
            all_movies = []
            for page in range(1, 51):
                response = connector.get_popular_movies(page)
                if response and 'results' in response:
                    all_movies.extend(response['results'])
                else:
                    break
                
                # 진행 상황 로그 (10페이지마다)
                if page % 10 == 0:
                    self.logger.info(f"월간 수집 진행: {page}/50 페이지 완료")
            
            # 중복 제거 및 품질 검증
            unique_movies = self._remove_duplicates(all_movies)
            validated_movies = [m for m in unique_movies if validator.validate_single_movie(m)[0]]
            
            # 월간 결과 저장
            month_str = datetime.now().strftime('%Y%m')
            collection_stats = {
                'collection_type': 'monthly',
                'month': month_str,
                'timestamp': datetime.now().strftime('%Y%m%d'),
                'pages_processed': 50,
                'total_collected': len(unique_movies),
                'total_valid': len(validated_movies),
                'quality_rate': len(validated_movies) / len(unique_movies) * 100 if unique_movies else 0
            }
            
            self._save_collection_results(validated_movies, f"monthly_{month_str}", collection_stats)
            
            self.logger.info(f"월간 갱신 완료: {len(validated_movies)}개 영화")
            
            # 월간 리포트 생성
            self._generate_monthly_report(validated_movies, collection_stats)
            
            return collection_stats
            
        finally:
            connector.close()
    
    def health_check(self):
        """스케줄러 헬스체크"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'scheduler_running': self.running,
            'pending_jobs': len(schedule.jobs),
            'recent_job_failures': self._get_recent_failures(),
            'last_successful_jobs': self.last_successful_jobs,
            'system_status': 'healthy'
        }
        
        # 연속 실패 체크
        for job_name, count in self.failure_counts.items():
            if count >= self.alert_thresholds['consecutive_failures']:
                health_status['system_status'] = 'unhealthy'
                self.logger.error(f"연속 실패 감지: {job_name} ({count}회)")
        
        # 헬스체크 결과 저장
        health_dir = Path('logs/health')
        health_dir.mkdir(exist_ok=True)
        
        health_file = health_dir / 'latest_health.json'
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health_status, f, ensure_ascii=False, indent=2, default=str)
        
        if health_status['system_status'] != 'healthy':
            self.logger.warning(f"시스템 상태: {health_status['system_status']}")
        
        return health_status
    
    def start_scheduler(self):
        """스케줄러 시작"""
        self.running = True
        self.logger.info("TMDB 데이터 스케줄러 시작")
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 30초마다 체크
            except KeyboardInterrupt:
                self.logger.info("사용자 중단 요청")
                break
            except Exception as e:
                self.logger.error(f"스케줄러 실행 중 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기
    
    def stop_scheduler(self):
        """스케줄러 정지"""
        self.running = False
        self.logger.info("TMDB 데이터 스케줄러 정지")
    
    def _signal_handler(self, signum, frame):
        """시스템 시그널 핸들러"""
        self.logger.info(f"시그널 {signum} 수신, 스케줄러 종료 중...")
        self.stop_scheduler()
    
    def _remove_duplicates(self, movies):
        """중복 영화 제거"""
        seen_ids = set()
        unique_movies = []
        
        for movie in movies:
            movie_id = movie.get('id')
            if movie_id and movie_id not in seen_ids:
                seen_ids.add(movie_id)
                unique_movies.append(movie)
        
        return unique_movies
    
    def _save_collection_results(self, movies, collection_type, metadata):
        """수집 결과 저장"""
        # 데이터 저장 디렉토리 생성
        data_dir = Path('data/raw/movies')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = data_dir / f"{collection_type}_{timestamp}.json"
        
        data_to_save = {
            'movies': movies,
            'collection_info': metadata,
            'save_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"수집 결과 저장: {output_file}")
    
    def _record_job_start(self, job_name):
        """작업 시작 기록"""
        job_record = {
            'job_name': job_name,
            'start_time': datetime.now(),
            'status': 'running',
            'end_time': None,
            'duration': None,
            'error': None,
            'result': None
        }
        
        self.job_history.append(job_record)
        job_id = len(self.job_history) - 1
        
        self.logger.info(f"작업 시작: {job_name} (ID: {job_id})")
        return job_id
    
    def _record_job_success(self, job_id, job_name, result):
        """작업 성공 기록"""
        if job_id < len(self.job_history):
            job_record = self.job_history[job_id]
            job_record['end_time'] = datetime.now()
            job_record['duration'] = (job_record['end_time'] - job_record['start_time']).total_seconds()
            job_record['status'] = 'success'
            job_record['result'] = result
            
            # 성공 시 실패 카운터 리셋
            if job_name in self.failure_counts:
                del self.failure_counts[job_name]
            
            # 마지막 성공 시간 기록
            self.last_successful_jobs[job_name] = datetime.now()
            
            self.logger.info(f"작업 완료: {job_name} ({job_record['duration']:.1f}초)")
    
    def _record_job_failure(self, job_id, job_name, error):
        """작업 실패 기록"""
        if job_id < len(self.job_history):
            job_record = self.job_history[job_id]
            job_record['end_time'] = datetime.now()
            job_record['duration'] = (job_record['end_time'] - job_record['start_time']).total_seconds()
            job_record['status'] = 'failed'
            job_record['error'] = error
            
            # 실패 카운터 증가
            self.failure_counts[job_name] = self.failure_counts.get(job_name, 0) + 1
            
            self.logger.error(f"작업 실패: {job_name} - {error}")
    
    def _handle_job_failure(self, job_name, error):
        """작업 실패 처리"""
        failure_count = self.failure_counts.get(job_name, 0)
        
        if failure_count >= self.alert_thresholds['consecutive_failures']:
            self.logger.critical(f"연속 실패 임계값 초과: {job_name} ({failure_count}회)")
            # 여기에 알림 로직 추가 가능 (이메일, Slack 등)
    
    def _get_recent_failures(self, hours=24):
        """최근 실패 작업 목록"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_failures = []
        
        for job in self.job_history:
            if (job.get('status') == 'failed' and 
                job.get('end_time') and 
                job['end_time'] > cutoff):
                recent_failures.append({
                    'job_name': job['job_name'],
                    'error': job['error'],
                    'time': job['end_time'].isoformat()
                })
        
        return recent_failures
    
    def _generate_weekly_report(self, movies, stats):
        """주간 리포트 생성"""
        report_dir = Path('data/raw/metadata/weekly_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        week_number = stats['week_number']
        report_file = report_dir / f"weekly_report_W{week_number}.json"
        
        report = {
            'report_type': 'weekly',
            'week_number': week_number,
            'generation_time': datetime.now().isoformat(),
            'collection_stats': stats,
            'top_movies': sorted(movies, key=lambda x: x.get('popularity', 0), reverse=True)[:10],
            'genre_distribution': self._analyze_genre_distribution(movies),
            'rating_distribution': self._analyze_rating_distribution(movies)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"주간 리포트 생성: {report_file}")
    
    def _generate_monthly_report(self, movies, stats):
        """월간 리포트 생성"""
        report_dir = Path('data/raw/metadata/monthly_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        month = stats['month']
        report_file = report_dir / f"monthly_report_{month}.json"
        
        report = {
            'report_type': 'monthly',
            'month': month,
            'generation_time': datetime.now().isoformat(),
            'collection_stats': stats,
            'top_movies': sorted(movies, key=lambda x: x.get('vote_average', 0), reverse=True)[:20],
            'genre_distribution': self._analyze_genre_distribution(movies),
            'rating_distribution': self._analyze_rating_distribution(movies),
            'release_year_distribution': self._analyze_release_year_distribution(movies)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"월간 리포트 생성: {report_file}")
    
    def _analyze_genre_distribution(self, movies):
        """장르 분포 분석"""
        genre_counts = {}
        
        for movie in movies:
            genres = movie.get('genre_ids', [])
            for genre_id in genres:
                genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 1
        
        return dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_rating_distribution(self, movies):
        """평점 분포 분석"""
        rating_ranges = {
            '9.0-10.0': 0, '8.0-8.9': 0, '7.0-7.9': 0,
            '6.0-6.9': 0, '5.0-5.9': 0, '0.0-4.9': 0
        }
        
        for movie in movies:
            rating = movie.get('vote_average', 0)
            if rating >= 9.0:
                rating_ranges['9.0-10.0'] += 1
            elif rating >= 8.0:
                rating_ranges['8.0-8.9'] += 1
            elif rating >= 7.0:
                rating_ranges['7.0-7.9'] += 1
            elif rating >= 6.0:
                rating_ranges['6.0-6.9'] += 1
            elif rating >= 5.0:
                rating_ranges['5.0-5.9'] += 1
            else:
                rating_ranges['0.0-4.9'] += 1
        
        return rating_ranges
    
    def _analyze_release_year_distribution(self, movies):
        """출시연도 분포 분석"""
        year_counts = {}
        
        for movie in movies:
            release_date = movie.get('release_date', '')
            if release_date and len(release_date) >= 4:
                year = release_date[:4]
                year_counts[year] = year_counts.get(year, 0) + 1
        
        return dict(sorted(year_counts.items(), reverse=True))
    
    def get_job_statistics(self, days=7):
        """작업 통계 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_jobs = [
            job for job in self.job_history 
            if job.get('start_time') and job['start_time'] > cutoff_date
        ]
        
        if not recent_jobs:
            return {
                'period': f'최근 {days}일',
                'total_jobs': 0,
                'successful_jobs': 0,
                'failed_jobs': 0,
                'success_rate': 0,
                'avg_duration': 0
            }
        
        successful_jobs = [j for j in recent_jobs if j.get('status') == 'success']
        failed_jobs = [j for j in recent_jobs if j.get('status') == 'failed']
        
        # 평균 실행 시간 계산
        durations = [j['duration'] for j in recent_jobs if j.get('duration')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'period': f'최근 {days}일',
            'total_jobs': len(recent_jobs),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': len(failed_jobs),
            'success_rate': len(successful_jobs) / len(recent_jobs) * 100,
            'avg_duration': avg_duration,
            'job_breakdown': self._get_job_breakdown(recent_jobs)
        }
    
    def _get_job_breakdown(self, jobs):
        """작업 유형별 분석"""
        breakdown = {}
        
        for job in jobs:
            job_name = job['job_name']
            if job_name not in breakdown:
                breakdown[job_name] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'avg_duration': 0
                }
            
            breakdown[job_name]['total'] += 1
            if job.get('status') == 'success':
                breakdown[job_name]['successful'] += 1
            elif job.get('status') == 'failed':
                breakdown[job_name]['failed'] += 1
        
        # 성공률 및 평균 시간 계산
        for job_name, stats in breakdown.items():
            if stats['total'] > 0:
                stats['success_rate'] = stats['successful'] / stats['total'] * 100
            
            job_durations = [j['duration'] for j in jobs 
                           if j['job_name'] == job_name and j.get('duration')]
            stats['avg_duration'] = sum(job_durations) / len(job_durations) if job_durations else 0
        
        return breakdown

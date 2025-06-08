"""
간단한 스케줄러 버전 (의존성 최소화)
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import json

class SimpleTMDBDataScheduler:
    """간단한 TMDB 데이터 수집 스케줄러"""
    
    def __init__(self):
        self.running = False
        self.logger = self._setup_logging()
        self.job_history = []
        
    def _setup_logging(self):
        """로깅 설정"""
        logger = logging.getLogger('simple_scheduler')
        logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러만 사용
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s | %(message)s')
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def setup_jobs(self):
        """스케줄 작업 설정"""
        self.logger.info("스케줄 작업 설정 중...")
        
        # 일일 수집: 매일 새벽 2시
        schedule.every().day.at("02:00").do(self._safe_job_wrapper, self.daily_collection, "daily_collection")
        
        # 주간 수집: 매주 일요일 새벽 3시  
        schedule.every().sunday.at("03:00").do(self._safe_job_wrapper, self.weekly_collection, "weekly_collection")
        
        # 시간별 트렌딩: 매시간 정각
        schedule.every().hour.at(":00").do(self._safe_job_wrapper, self.hourly_trending, "hourly_trending")
        
        # 월간 체크: 매일 새벽 4시 (매월 1일에만 실행)
        schedule.every().day.at("04:00").do(self._safe_job_wrapper, self._monthly_check, "monthly_check")
        
        # 헬스체크: 매 10분마다
        schedule.every(10).minutes.do(self._safe_job_wrapper, self.health_check, "health_check")
        
        self.logger.info(f"총 {len(schedule.jobs)}개 작업이 스케줄되었습니다.")
    
    def _safe_job_wrapper(self, job_func, job_name):
        """작업 실행 래퍼"""
        try:
            self.logger.info(f"작업 시작: {job_name}")
            result = job_func()
            self.logger.info(f"작업 완료: {job_name}")
            return result
        except Exception as e:
            self.logger.error(f"작업 실패: {job_name} - {e}")
            return None
    
    def daily_collection(self):
        """일일 데이터 수집 (간단한 버전)"""
        self.logger.info("=== 일일 데이터 수집 시작 ===")
        
        try:
            from ..tmdb_api_connector import TMDBAPIConnector
            
            connector = TMDBAPIConnector()
            
            # 인기 영화 5페이지 수집
            movies = []
            for page in range(1, 6):
                response = connector.get_popular_movies(page)
                if response and 'results' in response:
                    movies.extend(response['results'])
            
            # 결과 저장
            timestamp = datetime.now().strftime('%Y%m%d')
            result = {
                'collection_type': 'daily',
                'timestamp': timestamp,
                'total_collected': len(movies),
                'total_valid': len(movies)  # 간단한 버전에서는 모든 영화를 유효하다고 가정
            }
            
            # 파일 저장
            data_dir = Path('data/raw/movies')
            data_dir.mkdir(parents=True, exist_ok=True)
            
            save_data = {
                'movies': movies,
                'collection_info': result,
                'save_timestamp': datetime.now().isoformat()
            }
            
            filename = data_dir / f"daily_{timestamp}_{datetime.now().strftime('%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"일일 수집 완료: {len(movies)}개 영화")
            connector.close()
            
            return result
            
        except Exception as e:
            self.logger.error(f"일일 수집 실패: {e}")
            return None
    
    def weekly_collection(self):
        """주간 수집 (간단한 버전)"""
        self.logger.info("=== 주간 수집 시작 ===")
        return {'message': '주간 수집 실행됨 (간단한 버전)'}
    
    def hourly_trending(self):
        """시간별 트렌딩 (간단한 버전)"""
        current_hour = datetime.now().hour
        if not (8 <= current_hour <= 22):
            return None
        
        self.logger.info("=== 시간별 트렌딩 수집 시작 ===")
        return {'message': f'시간별 트렌딩 실행됨 ({current_hour}시)'}
    
    def _monthly_check(self):
        """월간 체크"""
        today = datetime.now()
        if today.day == 1:
            self.logger.info("=== 월간 갱신 실행 ===")
            return {'message': '월간 갱신 실행됨'}
        return None
    
    def health_check(self):
        """헬스체크"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'jobs_count': len(schedule.jobs)
        }
        
        # 헬스체크 저장
        health_dir = Path('logs/health')
        health_dir.mkdir(parents=True, exist_ok=True)
        
        with open(health_dir / 'latest_health.json', 'w', encoding='utf-8') as f:
            json.dump(health, f, ensure_ascii=False, indent=2, default=str)
        
        return health

# 별칭
TMDBDataScheduler = SimpleTMDBDataScheduler

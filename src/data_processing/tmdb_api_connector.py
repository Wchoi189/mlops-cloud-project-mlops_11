import os
import time
import requests
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class TMDBAPIConnector:
    """
    TMDB API 연동을 위한 안정적인 커넥터 클래스
    
    Features:
    - 자동 재시도 로직
    - Rate Limiting 처리
    - 에러 핸들링
    - 로깅 시스템
    - 환경변수 기반 설정
    """
    
    def __init__(self, api_key: Optional[str] = None, region: str = "KR", language: str = "ko-KR"):
        """
        TMDB API 커넥터 초기화
        
        Args:
            api_key: TMDB API 키 (환경변수에서 자동 로드)
            region: 지역 코드 (기본값: KR)
            language: 언어 코드 (기본값: ko-KR)
        """
        # 로깅 설정 (초기 단계에서 설정)
        self.logger = logging.getLogger(__name__)
        
        # 환경변수 강제 로드
        self._ensure_valid_api_key()
        
        # API 키 설정 (환경변수 우선)
        self.api_key = api_key or os.getenv('TMDB_API_KEY')
        
        # API 키 검증
        if not self.api_key:
            raise ValueError("TMDB API 키가 필요합니다. 환경변수 TMDB_API_KEY를 설정하거나 직접 전달해주세요.")
        
        if 'your_' in self.api_key.lower() or 'here' in self.api_key.lower():
            raise ValueError(f"잘못된 API 키입니다: {self.api_key}. 실제 TMDB API 키를 설정해주세요.")
        
        self.logger.info(f"TMDB API 키 로드 완료: {self.api_key[:8]}...")
        
        # 기본 설정
        self.base_url = "https://api.themoviedb.org/3"
        self.region = region
        self.language = language
        
        # 요청 제한 설정
        self.request_delay = 0.25  # API 호출 간격 (초)
        self.max_retries = 3
        self.timeout = 30
        
        # 세션 설정 (연결 풀링 및 재시도 로직)
        self.session = self._create_session()
        
        # API 사용량 추적
        self.request_count = 0
        self.last_request_time = 0
        
    def _ensure_valid_api_key(self):
        """환경변수에서 올바른 API 키 로드 보장"""
        try:
            from .environment_manager import EnvironmentManager
            env_manager = EnvironmentManager()
            # 환경변수 강제 로드 수행
        except Exception as e:
            # 환경변수 매니저 로드 실패 시 백업 방법
            import os
            from dotenv import load_dotenv
            
            # 플레이스홀더 값 제거
            if os.getenv('TMDB_API_KEY') and 'your_' in os.getenv('TMDB_API_KEY', '').lower():
                os.environ.pop('TMDB_API_KEY', None)
            
            # .env 파일에서 강제 로드
            load_dotenv(override=True)
        
    def _create_session(self) -> requests.Session:
        """
        재시도 로직이 포함된 requests 세션 생성
        """
        session = requests.Session()
        
        # 재시도 전략 설정 (urllib3 v2 호환)
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # urllib3 v2 호환
            backoff_factor=1  # 지수적 백오프
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 기본 헤더 설정
        session.headers.update({
            'User-Agent': 'MLOps-TMDB-Crawler/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def _build_url(self, endpoint: str) -> str:
        """API 엔드포인트 URL 구성"""
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _build_params(self, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        API 요청 파라미터 구성
        
        Args:
            additional_params: 추가 파라미터
            
        Returns:
            완성된 파라미터 딕셔너리
        """
        params = {
            'api_key': self.api_key,
            'language': self.language,
            'region': self.region
        }
        
        if additional_params:
            params.update(additional_params)
            
        return params
    
    def _handle_rate_limit(self):
        """Rate Limiting 처리"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: {sleep_time:.2f}초 대기")
            time.sleep(sleep_time)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        안전한 API 요청 실행
        
        Args:
            endpoint: API 엔드포인트
            params: 추가 파라미터
            
        Returns:
            API 응답 데이터
            
        Raises:
            requests.RequestException: API 요청 실패 시
        """
        # Rate Limiting 적용
        self._handle_rate_limit()
        
        # URL 및 파라미터 구성
        url = self._build_url(endpoint)
        request_params = self._build_params(params)
        
        try:
            # API 요청 실행
            self.logger.debug(f"API 요청: {endpoint}")
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            
            # 요청 시간 기록
            self.last_request_time = time.time()
            self.request_count += 1
            
            # HTTP 에러 확인
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            # 성공 로그
            self.logger.debug(f"API 요청 성공: {endpoint} (상태코드: {response.status_code})")
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                self.logger.warning("API 요청 한도 초과, 재시도 대기 중...")
                time.sleep(60)  # 1분 대기 후 재시도
                raise
            else:
                self.logger.error(f"HTTP 에러: {e}")
                raise
                
        except requests.exceptions.Timeout:
            self.logger.error(f"요청 타임아웃: {endpoint}")
            raise
            
        except requests.exceptions.ConnectionError:
            self.logger.error(f"연결 에러: {endpoint}")
            raise
            
        except json.JSONDecodeError:
            self.logger.error("잘못된 JSON 응답")
            raise
            
        except Exception as e:
            self.logger.error(f"예상치 못한 에러: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        try:
            # TMDB API v3 엔드포인트로 연결 테스트
            self._make_request('/3/configuration')
            self.logger.info("TMDB API 연결 성공")
            return True
        except Exception as e:
            self.logger.error(f"TMDB API 연결 실패: {e}")
            return False
    
    def get_popular_movies(self, page: int = 1) -> Dict[str, Any]:
        """
        인기 영화 목록 조회
        
        Args:
            page: 페이지 번호 (1-1000)
            
        Returns:
            인기 영화 데이터
        """
        if page < 1 or page > 1000:
            raise ValueError("페이지 번호는 1-1000 범위여야 합니다.")
        
        params = {'page': page}
        return self._make_request('/3/movie/popular', params)
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """
        특정 영화 상세 정보 조회
        
        Args:
            movie_id: 영화 ID
            
        Returns:
            영화 상세 정보
        """
        endpoint = f'/3/movie/{movie_id}'
        return self._make_request(endpoint)
    
    def discover_movies(self, **kwargs) -> Dict[str, Any]:
        """
        조건별 영화 검색
        
        Args:
            **kwargs: 검색 조건 (genre, year, rating 등)
            
        Returns:
            검색된 영화 목록
        """
        return self._make_request('/3/discover/movie', kwargs)
    
    def get_trending_movies(self, time_window: str = 'day') -> Dict[str, Any]:
        """
        트렌딩 영화 조회
        
        Args:
            time_window: 'day' 또는 'week'
            
        Returns:
            트렌딩 영화 데이터
        """
        if time_window not in ['day', 'week']:
            raise ValueError("time_window는 'day' 또는 'week'이어야 합니다.")
        
        endpoint = f'/3/trending/movie/{time_window}'
        return self._make_request(endpoint)
    
    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> Dict[str, Any]:
        """
        장르별 영화 조회
        
        Args:
            genre_id: 장르 ID
            page: 페이지 번호
            
        Returns:
            장르별 영화 데이터
        """
        params = {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc'
        }
        return self._make_request('/3/discover/movie', params)
    
    def get_latest_movies(self, page: int = 1) -> Dict[str, Any]:
        """
        최신 개봉 영화 조회
        
        Args:
            page: 페이지 번호
            
        Returns:
            최신 영화 데이터
        """
        from datetime import datetime, timedelta
        
        # 최근 3개월 내 개봉 영화
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        params = {
            'primary_release_date.gte': start_date,
            'primary_release_date.lte': end_date,
            'page': page,
            'sort_by': 'primary_release_date.desc'
        }
        return self._make_request('/3/discover/movie', params)
    
    def get_top_rated_movies(self, page: int = 1) -> Dict[str, Any]:
        """
        평점 높은 영화 조회
        
        Args:
            page: 페이지 번호
            
        Returns:
            평점 높은 영화 데이터
        """
        params = {'page': page}
        return self._make_request('/3/movie/top_rated', params)
    
    def save_collection_results(self, movies: List[Dict], collection_type: str, metadata: Dict) -> str:
        """
        수집 결과 저장
        
        Args:
            movies: 수집된 영화 데이터 리스트
            collection_type: 수집 유형
            metadata: 메타데이터
            
        Returns:
            저장된 파일 경로
        """
        from pathlib import Path
        
        # 데이터 저장 디렉토리 생성
        data_dir = Path('data/raw/movies')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{collection_type}_{timestamp}.json"
        filepath = data_dir / filename
        
        # 저장할 데이터 구성
        result_data = {
            'movies': movies,
            'collection_info': {
                **metadata,
                'collection_timestamp': datetime.now().isoformat(),
                'total_movies': len(movies),
                'api_requests_used': self.request_count
            }
        }
        
        # JSON 파일로 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"수집 결과 저장 완료: {filepath}")
        return str(filepath)
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        API 사용량 통계 반환
        
        Returns:
            API 사용량 정보
        """
        return {
            'total_requests': self.request_count,
            'average_delay': self.request_delay,
            'last_request_time': datetime.fromtimestamp(self.last_request_time) if self.last_request_time else None,
            'session_active': True
        }
    
    def close(self):
        """세션 종료"""
        if self.session:
            self.session.close()
            self.logger.info("TMDB API 세션 종료")


# 편의 함수들
def create_tmdb_connector(api_key: Optional[str] = None) -> TMDBAPIConnector:
    """TMDB 커넥터 생성 편의 함수"""
    return TMDBAPIConnector(api_key=api_key)

def test_tmdb_connection(api_key: Optional[str] = None) -> bool:
    """TMDB 연결 테스트 편의 함수"""
    connector = create_tmdb_connector(api_key)
    result = connector.test_connection()
    connector.close()
    return result

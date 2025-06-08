# src/data_processing/tmdb_crawler.py
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import sys

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_processing.tmdb_api_connector import TMDBAPIConnector
from data.naming_convention import DataFileNamingConvention
from data.file_formats import DataFileManager

class TMDBCrawler:
    """TMDB 대량 데이터 수집 크롤러"""
    
    def __init__(self, region: str = "KR", language: str = "ko-KR"):
        self.connector = TMDBAPIConnector(region=region, language=language)
        self.file_manager = DataFileManager()
        self.naming = DataFileNamingConvention()
        self.logger = logging.getLogger(__name__)
        
        # 수집 통계
        self.collection_stats = {
            'total_collected': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 주요 장르 정의
        self.major_genres = {
            28: "액션",
            35: "코미디", 
            18: "드라마",
            27: "공포",
            10749: "로맨스",
            878: "SF",
            53: "스릴러",
            16: "애니메이션",
            14: "판타지",
            80: "범죄"
        }
    
    def get_popular_movies_bulk(self, start_page: int = 1, end_page: int = 10) -> List[Dict[str, Any]]:
        """다중 페이지 인기 영화 수집"""
        self.logger.info(f"인기 영화 대량 수집 시작: 페이지 {start_page}-{end_page}")
        self.collection_stats['start_time'] = datetime.now()
        
        all_movies = []
        
        for page in range(start_page, end_page + 1):
            try:
                self.logger.debug(f"페이지 {page} 수집 중...")
                response = self.connector.get_popular_movies(page)
                
                if response and 'results' in response:
                    movies = response['results']
                    all_movies.extend(movies)
                    self.collection_stats['successful_requests'] += 1
                    self.logger.debug(f"페이지 {page}: {len(movies)}개 영화 수집")
                else:
                    self.logger.warning(f"페이지 {page}: 빈 응답")
                    
            except Exception as e:
                self.logger.error(f"페이지 {page} 수집 실패: {e}")
                self.collection_stats['failed_requests'] += 1
                continue
        
        # 중복 제거
        unique_movies = self.remove_duplicates(all_movies)
        self.collection_stats['total_collected'] = len(unique_movies)
        self.collection_stats['end_time'] = datetime.now()
        
        self.logger.info(f"인기 영화 수집 완료: {len(unique_movies)}개 (중복 제거 후)")
        return unique_movies
    
    def get_movies_by_genre(self, genre_id: int, max_pages: int = 10) -> List[Dict[str, Any]]:
        """장르별 영화 수집"""
        genre_name = self.major_genres.get(genre_id, f"Genre_{genre_id}")
        self.logger.info(f"{genre_name} 장르 영화 수집 시작: 최대 {max_pages}페이지")
        
        all_movies = []
        
        for page in range(1, max_pages + 1):
            try:
                # discover/movie 엔드포인트 사용
                params = {
                    'with_genres': genre_id,
                    'page': page,
                    'sort_by': 'popularity.desc'
                }
                
                response = self.connector.discover_movies(**params)
                
                if response and 'results' in response:
                    movies = response['results']
                    all_movies.extend(movies)
                    self.logger.debug(f"{genre_name} 페이지 {page}: {len(movies)}개 수집")
                    
                    # 결과가 없으면 중단
                    if not movies:
                        break
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"{genre_name} 페이지 {page} 수집 실패: {e}")
                continue
        
        unique_movies = self.remove_duplicates(all_movies)
        self.logger.info(f"{genre_name} 장르 수집 완료: {len(unique_movies)}개")
        return unique_movies
    
    def get_latest_movies(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """최신 영화 수집"""
        self.logger.info(f"최신 영화 수집 시작: 최대 {max_pages}페이지")
        
        all_movies = []
        
        # 최근 3개월 영화 수집
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        for page in range(1, max_pages + 1):
            try:
                params = {
                    'primary_release_date.gte': start_date.strftime('%Y-%m-%d'),
                    'primary_release_date.lte': end_date.strftime('%Y-%m-%d'),
                    'page': page,
                    'sort_by': 'release_date.desc'
                }
                
                response = self.connector.discover_movies(**params)
                
                if response and 'results' in response:
                    movies = response['results']
                    all_movies.extend(movies)
                    self.logger.debug(f"최신 영화 페이지 {page}: {len(movies)}개 수집")
                    
                    if not movies:
                        break
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"최신 영화 페이지 {page} 수집 실패: {e}")
                continue
        
        unique_movies = self.remove_duplicates(all_movies)
        self.logger.info(f"최신 영화 수집 완료: {len(unique_movies)}개")
        return unique_movies
    
    def get_top_rated_movies(self, min_rating: float = 7.0, max_pages: int = 20) -> List[Dict[str, Any]]:
        """평점 높은 영화 수집"""
        self.logger.info(f"평점 {min_rating} 이상 영화 수집 시작: 최대 {max_pages}페이지")
        
        all_movies = []
        
        for page in range(1, max_pages + 1):
            try:
                params = {
                    'vote_average.gte': min_rating,
                    'vote_count.gte': 100,  # 최소 투표 수
                    'page': page,
                    'sort_by': 'vote_average.desc'
                }
                
                response = self.connector.discover_movies(**params)
                
                if response and 'results' in response:
                    movies = response['results']
                    # 평점 필터링 재확인
                    high_rated = [m for m in movies if m.get('vote_average', 0) >= min_rating]
                    all_movies.extend(high_rated)
                    self.logger.debug(f"평점 높은 영화 페이지 {page}: {len(high_rated)}개 수집")
                    
                    if not movies:
                        break
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"평점 높은 영화 페이지 {page} 수집 실패: {e}")
                continue
        
        unique_movies = self.remove_duplicates(all_movies)
        self.logger.info(f"평점 높은 영화 수집 완료: {len(unique_movies)}개")
        return unique_movies
    
    def get_trending_movies(self, time_window: str = 'day', max_pages: int = 5) -> List[Dict[str, Any]]:
        """트렌딩 영화 수집"""
        self.logger.info(f"트렌딩 영화 수집 시작: {time_window}")
        
        try:
            response = self.connector.get_trending_movies(time_window)
            
            if response and 'results' in response:
                movies = response['results']
                self.logger.info(f"트렌딩 영화 수집 완료: {len(movies)}개")
                return movies
            else:
                self.logger.warning("트렌딩 영화 응답이 비어있음")
                return []
                
        except Exception as e:
            self.logger.error(f"트렌딩 영화 수집 실패: {e}")
            return []
    
    def validate_movie_data(self, movie: Dict[str, Any]) -> Tuple[bool, str]:
        """영화 데이터 유효성 검증"""
        required_fields = ['id', 'title', 'release_date', 'vote_average', 'popularity']
        
        # 필수 필드 확인
        for field in required_fields:
            if field not in movie or movie[field] is None:
                return False, f"Missing required field: {field}"
        
        # 데이터 타입 검증
        if not isinstance(movie.get('vote_average'), (int, float)):
            return False, "Invalid vote_average type"
        
        # 값 범위 검증
        if not (0 <= movie.get('vote_average', 0) <= 10):
            return False, "vote_average out of range"
        
        # 비즈니스 로직 검증
        if movie.get('adult', False):
            return False, "Adult content filtered"
        
        # 개봉 전 영화 제외 (현재 날짜 기준)
        release_date = movie.get('release_date')
        if release_date:
            try:
                release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                if release_dt > datetime.now():
                    return False, "Unreleased movie filtered"
            except ValueError:
                return False, "Invalid release date format"
        
        # 평점 0인 영화 제외
        if movie.get('vote_average', 0) == 0:
            return False, "Zero rating filtered"
        
        # 투표 수 너무 적은 영화 제외
        if movie.get('vote_count', 0) < 10:
            return False, "Insufficient votes filtered"
        
        return True, "Valid"
    
    def remove_duplicates(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 영화 제거"""
        seen_ids = set()
        unique_movies = []
        
        for movie in movies:
            movie_id = movie.get('id')
            if movie_id and movie_id not in seen_ids:
                seen_ids.add(movie_id)
                unique_movies.append(movie)
        
        removed_count = len(movies) - len(unique_movies)
        if removed_count > 0:
            self.logger.info(f"중복 제거: {removed_count}개 영화 제거")
        
        return unique_movies
    
    def filter_valid_movies(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """유효한 영화만 필터링"""
        valid_movies = []
        invalid_count = 0
        
        for movie in movies:
            is_valid, reason = self.validate_movie_data(movie)
            if is_valid:
                valid_movies.append(movie)
            else:
                invalid_count += 1
                self.logger.debug(f"Invalid movie {movie.get('id', 'unknown')}: {reason}")
        
        if invalid_count > 0:
            self.logger.info(f"데이터 검증: {invalid_count}개 영화 필터링됨")
        
        return valid_movies
    
    def save_collection_results(self, movies: List[Dict[str, Any]], collection_type: str, 
                               metadata: Dict[str, Any]) -> str:
        """수집 결과 저장"""
        try:
            # 파일명 생성
            if collection_type.startswith('daily'):
                filename = self.naming.daily_collection()
                save_dir = Path("data/raw/movies/daily")
            elif collection_type.startswith('weekly'):
                filename = self.naming.weekly_collection(
                    datetime.now().year, 
                    datetime.now().isocalendar()[1]
                )
                save_dir = Path("data/raw/movies/weekly")
            elif collection_type.startswith('genre'):
                genre_name = metadata.get('genre_name', 'unknown')
                filename = self.naming.genre_collection(genre_name)
                save_dir = Path("data/raw/movies/genre")
            elif collection_type.startswith('trending'):
                time_window = metadata.get('time_window', 'day')
                filename = self.naming.trending_collection(time_window)
                save_dir = Path("data/raw/movies/trending")
            else:
                filename = f"{collection_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_dir = Path("data/raw/movies")
            
            # 저장 데이터 구성
            save_data = {
                'collection_info': {
                    'collection_type': collection_type,
                    'collection_time': datetime.now().isoformat(),
                    'total_movies': len(movies),
                    'metadata': metadata,
                    'stats': self.collection_stats
                },
                'movies': movies
            }
            
            # 파일 저장
            filepath = save_dir / filename
            success = self.file_manager.save_json(save_data, filepath, create_dirs=True)
            
            if success:
                self.logger.info(f"수집 결과 저장 완료: {filepath}")
                return str(filepath)
            else:
                self.logger.error(f"수집 결과 저장 실패: {filepath}")
                return ""
                
        except Exception as e:
            self.logger.error(f"수집 결과 저장 중 오류: {e}")
            return ""
    
    def collect_comprehensive_dataset(self) -> Dict[str, Any]:
        """종합 데이터셋 수집"""
        self.logger.info("종합 데이터셋 수집 시작")
        
        results = {
            'collection_summary': {
                'start_time': datetime.now().isoformat(),
                'collections': {}
            }
        }
        
        try:
            # 1. 인기 영화 수집
            self.logger.info("1. 인기 영화 수집 중...")
            popular_movies = self.get_popular_movies_bulk(1, 20)  # 20페이지 (400개)
            valid_popular = self.filter_valid_movies(popular_movies)
            
            results['collections']['popular'] = {
                'total_collected': len(popular_movies),
                'valid_movies': len(valid_popular),
                'file_path': self.save_collection_results(
                    valid_popular, 'daily_popular', 
                    {'source': 'popular', 'pages': 20}
                )
            }
            
            # 2. 장르별 영화 수집
            self.logger.info("2. 장르별 영화 수집 중...")
            for genre_id, genre_name in list(self.major_genres.items())[:5]:  # 주요 5개 장르
                genre_movies = self.get_movies_by_genre(genre_id, 10)
                valid_genre = self.filter_valid_movies(genre_movies)
                
                results['collections'][f'genre_{genre_name}'] = {
                    'total_collected': len(genre_movies),
                    'valid_movies': len(valid_genre),
                    'file_path': self.save_collection_results(
                        valid_genre, f'genre_{genre_name}',
                        {'genre_id': genre_id, 'genre_name': genre_name}
                    )
                }
            
            # 3. 트렌딩 영화 수집
            self.logger.info("3. 트렌딩 영화 수집 중...")
            trending_movies = self.get_trending_movies('day')
            valid_trending = self.filter_valid_movies(trending_movies)
            
            results['collections']['trending'] = {
                'total_collected': len(trending_movies),
                'valid_movies': len(valid_trending),
                'file_path': self.save_collection_results(
                    valid_trending, 'trending_day',
                    {'time_window': 'day'}
                )
            }
            
            # 4. 평점 높은 영화 수집
            self.logger.info("4. 평점 높은 영화 수집 중...")
            top_rated_movies = self.get_top_rated_movies(7.5, 15)
            valid_top_rated = self.filter_valid_movies(top_rated_movies)
            
            results['collections']['top_rated'] = {
                'total_collected': len(top_rated_movies),
                'valid_movies': len(valid_top_rated),
                'file_path': self.save_collection_results(
                    valid_top_rated, 'top_rated',
                    {'min_rating': 7.5, 'pages': 15}
                )
            }
            
            # 종합 통계
            total_collected = sum(c['total_collected'] for c in results['collections'].values())
            total_valid = sum(c['valid_movies'] for c in results['collections'].values())
            
            results['collection_summary'].update({
                'end_time': datetime.now().isoformat(),
                'total_collected': total_collected,
                'total_valid': total_valid,
                'validation_rate': (total_valid / total_collected * 100) if total_collected > 0 else 0,
                'collection_types': len(results['collections'])
            })
            
            # 요약 저장
            summary_file = self.save_collection_results(
                [], 'collection_summary',
                results['collection_summary']
            )
            
            self.logger.info(f"종합 데이터셋 수집 완료: 총 {total_valid}개 유효 영화")
            return results
            
        except Exception as e:
            self.logger.error(f"종합 데이터셋 수집 실패: {e}")
            return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """수집 통계 반환"""
        stats = self.collection_stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['duration_seconds'] = duration.total_seconds()
            stats['duration_minutes'] = duration.total_seconds() / 60
        
        # API 사용량 통계 추가
        api_stats = self.connector.get_api_usage_stats()
        stats['api_usage'] = api_stats
        
        return stats
    
    def close(self):
        """크롤러 종료"""
        self.connector.close()
        self.logger.info("TMDB 크롤러 종료")

# 편의 함수들
def create_tmdb_crawler(region: str = "KR", language: str = "ko-KR") -> TMDBCrawler:
    """TMDB 크롤러 생성 편의 함수"""
    return TMDBCrawler(region=region, language=language)

def quick_collect_popular_movies(pages: int = 5) -> List[Dict[str, Any]]:
    """빠른 인기 영화 수집"""
    crawler = create_tmdb_crawler()
    try:
        movies = crawler.get_popular_movies_bulk(1, pages)
        return crawler.filter_valid_movies(movies)
    finally:
        crawler.close()

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class MovieData:
    """영화 데이터 구조체"""
    movie_id: int
    title: str
    original_title: str
    overview: str
    release_date: Optional[date]
    popularity: float
    vote_average: float
    vote_count: int
    genre_ids: List[int]
    adult: bool
    original_language: str
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    video: bool
    
    # 메타데이터
    collected_at: datetime
    source: str = "tmdb_api"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # 날짜 객체를 문자열로 변환
        if self.release_date:
            data['release_date'] = self.release_date.isoformat()
        data['collected_at'] = self.collected_at.isoformat()
        return data
    
    @classmethod
    def from_tmdb_response(cls, tmdb_data: Dict[str, Any]) -> 'MovieData':
        """TMDB API 응답에서 MovieData 생성"""
        # 날짜 파싱
        release_date = None
        if tmdb_data.get('release_date'):
            try:
                release_date = datetime.strptime(tmdb_data['release_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        return cls(
            movie_id=tmdb_data.get('id', 0),
            title=tmdb_data.get('title', ''),
            original_title=tmdb_data.get('original_title', ''),
            overview=tmdb_data.get('overview', ''),
            release_date=release_date,
            popularity=float(tmdb_data.get('popularity', 0.0)),
            vote_average=float(tmdb_data.get('vote_average', 0.0)),
            vote_count=int(tmdb_data.get('vote_count', 0)),
            genre_ids=tmdb_data.get('genre_ids', []),
            adult=bool(tmdb_data.get('adult', False)),
            original_language=tmdb_data.get('original_language', ''),
            poster_path=tmdb_data.get('poster_path'),
            backdrop_path=tmdb_data.get('backdrop_path'),
            video=bool(tmdb_data.get('video', False)),
            collected_at=datetime.now()
        )

@dataclass
class PaginationInfo:
    """페이지네이션 정보"""
    page: int
    total_pages: int
    total_results: int
    results_per_page: int
    
    def has_next_page(self) -> bool:
        """다음 페이지 존재 여부"""
        return self.page < self.total_pages
    
    def has_prev_page(self) -> bool:
        """이전 페이지 존재 여부"""
        return self.page > 1
    
    def next_page(self) -> int:
        """다음 페이지 번호"""
        return self.page + 1 if self.has_next_page() else self.page
    
    def prev_page(self) -> int:
        """이전 페이지 번호"""
        return self.page - 1 if self.has_prev_page() else self.page

class TMDBResponseParser:
    """
    TMDB API 응답 파싱 유틸리티
    
    Features:
    - 안전한 데이터 파싱
    - 데이터 유효성 검증
    - 구조화된 데이터 변환
    - 에러 처리
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_movie_list_response(self, response: Dict[str, Any]) -> tuple[List[MovieData], PaginationInfo]:
        """
        영화 목록 응답 파싱
        
        Args:
            response: TMDB API 응답
            
        Returns:
            (영화 데이터 리스트, 페이지네이션 정보)
        """
        try:
            # 페이지네이션 정보 추출
            pagination = PaginationInfo(
                page=response.get('page', 1),
                total_pages=response.get('total_pages', 1),
                total_results=response.get('total_results', 0),
                results_per_page=len(response.get('results', []))
            )
            
            # 영화 데이터 파싱
            movies = []
            for movie_data in response.get('results', []):
                try:
                    movie = MovieData.from_tmdb_response(movie_data)
                    movies.append(movie)
                except Exception as e:
                    self.logger.warning(f"영화 데이터 파싱 실패: {e}, 데이터: {movie_data}")
                    continue
            
            self.logger.info(f"영화 목록 파싱 완료: {len(movies)}개 영화, 페이지 {pagination.page}/{pagination.total_pages}")
            return movies, pagination
            
        except Exception as e:
            self.logger.error(f"영화 목록 응답 파싱 실패: {e}")
            return [], PaginationInfo(1, 1, 0, 0)
    
    def parse_movie_details_response(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        영화 상세 정보 응답 파싱
        
        Args:
            response: TMDB API 응답
            
        Returns:
            파싱된 영화 상세 정보
        """
        try:
            # 기본 영화 정보
            movie_details = {
                'movie_id': response.get('id'),
                'title': response.get('title'),
                'original_title': response.get('original_title'),
                'overview': response.get('overview'),
                'tagline': response.get('tagline'),
                'release_date': response.get('release_date'),
                'runtime': response.get('runtime'),
                'popularity': response.get('popularity'),
                'vote_average': response.get('vote_average'),
                'vote_count': response.get('vote_count'),
                'adult': response.get('adult'),
                'original_language': response.get('original_language'),
                'poster_path': response.get('poster_path'),
                'backdrop_path': response.get('backdrop_path'),
                'homepage': response.get('homepage'),
                'imdb_id': response.get('imdb_id'),
                'status': response.get('status'),
                'budget': response.get('budget'),
                'revenue': response.get('revenue')
            }
            
            # 장르 정보
            genres = response.get('genres', [])
            movie_details['genres'] = [
                {'id': genre.get('id'), 'name': genre.get('name')} 
                for genre in genres
            ]
            
            # 제작 국가
            production_countries = response.get('production_countries', [])
            movie_details['production_countries'] = [
                {'iso_3166_1': country.get('iso_3166_1'), 'name': country.get('name')}
                for country in production_countries
            ]
            
            # 제작사
            production_companies = response.get('production_companies', [])
            movie_details['production_companies'] = [
                {
                    'id': company.get('id'),
                    'name': company.get('name'),
                    'logo_path': company.get('logo_path'),
                    'origin_country': company.get('origin_country')
                }
                for company in production_companies
            ]
            
            # 사용 언어
            spoken_languages = response.get('spoken_languages', [])
            movie_details['spoken_languages'] = [
                {
                    'iso_639_1': lang.get('iso_639_1'),
                    'name': lang.get('name'),
                    'english_name': lang.get('english_name')
                }
                for lang in spoken_languages
            ]
            
            # 수집 시간 추가
            movie_details['collected_at'] = datetime.now().isoformat()
            
            self.logger.debug(f"영화 상세 정보 파싱 완료: {movie_details.get('title')}")
            return movie_details
            
        except Exception as e:
            self.logger.error(f"영화 상세 정보 파싱 실패: {e}")
            return None
    
    def validate_movie_data(self, movie: Union[MovieData, Dict[str, Any]]) -> bool:
        """
        영화 데이터 유효성 검증
        
        Args:
            movie: 검증할 영화 데이터
            
        Returns:
            유효성 여부
        """
        try:
            if isinstance(movie, MovieData):
                data = movie.to_dict()
            else:
                data = movie
            
            # 필수 필드 확인
            required_fields = ['movie_id', 'title']
            for field in required_fields:
                if not data.get(field):
                    self.logger.warning(f"필수 필드 누락: {field}")
                    return False
            
            # 데이터 타입 검증
            if not isinstance(data.get('movie_id'), int) or data.get('movie_id') <= 0:
                self.logger.warning(f"잘못된 movie_id: {data.get('movie_id')}")
                return False
            
            if not isinstance(data.get('title'), str) or len(data.get('title').strip()) == 0:
                self.logger.warning(f"잘못된 title: {data.get('title')}")
                return False
            
            # 평점 범위 확인
            vote_average = data.get('vote_average', 0)
            if not (0 <= vote_average <= 10):
                self.logger.warning(f"잘못된 평점 범위: {vote_average}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"데이터 검증 중 에러: {e}")
            return False
    
    def filter_valid_movies(self, movies: List[MovieData]) -> List[MovieData]:
        """
        유효한 영화 데이터만 필터링
        
        Args:
            movies: 영화 데이터 리스트
            
        Returns:
            유효한 영화 데이터 리스트
        """
        valid_movies = []
        for movie in movies:
            if self.validate_movie_data(movie):
                valid_movies.append(movie)
        
        self.logger.info(f"데이터 필터링 완료: {len(valid_movies)}/{len(movies)} 유효")
        return valid_movies
    
    def extract_trending_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        트렌딩 데이터 응답 파싱
        
        Args:
            response: TMDB 트렌딩 API 응답
            
        Returns:
            파싱된 트렌딩 데이터
        """
        try:
            movies, pagination = self.parse_movie_list_response(response)
            
            trending_data = {
                'extracted_at': datetime.now().isoformat(),
                'total_movies': len(movies),
                'pagination': asdict(pagination),
                'movies': [movie.to_dict() for movie in movies],
                'trending_scores': []
            }
            
            # 트렌딩 점수 계산 (인기도 + 평점 조합)
            for movie in movies:
                score = (movie.popularity * 0.7) + (movie.vote_average * movie.vote_count * 0.3)
                trending_data['trending_scores'].append({
                    'movie_id': movie.movie_id,
                    'title': movie.title,
                    'trending_score': round(score, 2),
                    'popularity': movie.popularity,
                    'vote_average': movie.vote_average,
                    'vote_count': movie.vote_count
                })
            
            # 트렌딩 점수로 정렬
            trending_data['trending_scores'].sort(
                key=lambda x: x['trending_score'], reverse=True
            )
            
            return trending_data
            
        except Exception as e:
            self.logger.error(f"트렌딩 데이터 파싱 실패: {e}")
            return {}
    
    def save_parsed_data(self, data: Dict[str, Any], file_path: str):
        """
        파싱된 데이터를 파일로 저장
        
        Args:
            data: 저장할 데이터
            file_path: 저장 경로
        """
        try:
            # 디렉토리 생성
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"데이터 저장 완료: {file_path}")
            
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {e}")


# 편의 함수들
def parse_tmdb_response(response: Dict[str, Any], response_type: str = 'movie_list') -> Any:
    """
    TMDB 응답 파싱 편의 함수
    
    Args:
        response: TMDB API 응답
        response_type: 응답 타입 ('movie_list', 'movie_details', 'trending')
        
    Returns:
        파싱된 데이터
    """
    parser = TMDBResponseParser()
    
    if response_type == 'movie_list':
        return parser.parse_movie_list_response(response)
    elif response_type == 'movie_details':
        return parser.parse_movie_details_response(response)
    elif response_type == 'trending':
        return parser.extract_trending_data(response)
    else:
        raise ValueError(f"지원하지 않는 응답 타입: {response_type}")

def validate_movie_data(movie: Union[MovieData, Dict[str, Any]]) -> bool:
    """영화 데이터 검증 편의 함수"""
    parser = TMDBResponseParser()
    return parser.validate_movie_data(movie)

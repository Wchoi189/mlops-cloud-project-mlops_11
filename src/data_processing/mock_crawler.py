# src/data_processing/mock_crawler.py
"""
Mock 크롤러 - 테스트용 데이터 수집 시뮬레이션
"""

import random
import time
from datetime import datetime
from typing import List, Dict, Any
import json
from pathlib import Path

class MockTMDBCrawler:
    """테스트용 Mock TMDB 크롤러"""
    
    def __init__(self):
        self.collected_count = 0
        
    def get_popular_movies(self, page=1) -> Dict[str, Any]:
        """Mock 인기 영화 데이터 생성"""
        movies = []
        
        for i in range(20):  # 페이지당 20개 영화
            movie_id = random.randint(100000, 999999)
            movie = {
                'id': movie_id,
                'title': f'Test Movie {movie_id}',
                'release_date': '2024-01-01',
                'vote_average': round(random.uniform(5.0, 9.0), 1),
                'popularity': round(random.uniform(10.0, 200.0), 1),
                'overview': f'This is a test movie {movie_id} for MLOps testing.',
                'adult': False,
                'vote_count': random.randint(100, 5000),
                'genre_ids': [random.randint(1, 50) for _ in range(random.randint(1, 3))]
            }
            movies.append(movie)
        
        self.collected_count += len(movies)
        
        return {
            'results': movies,
            'page': page,
            'total_pages': 100,
            'total_results': 2000
        }
    
    def get_bulk_popular_movies(self, start_page: int, end_page: int) -> List[Dict]:
        """대량 인기 영화 수집 시뮬레이션"""
        all_movies = []
        
        for page in range(start_page, end_page + 1):
            response = self.get_popular_movies(page)
            all_movies.extend(response['results'])
            time.sleep(0.1)  # API 호출 시뮬레이션
        
        return all_movies
    
    def save_collection_results(self, movies: List[Dict], collection_type: str, metadata: Dict):
        """수집 결과 저장"""
        data_dir = Path('data/raw/movies')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{collection_type}_{timestamp}.json"
        filepath = data_dir / filename
        
        result_data = {
            'movies': movies,
            'collection_info': {
                **metadata,
                'collection_timestamp': datetime.now().isoformat(),
                'total_movies': len(movies)
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Mock 데이터 저장 완료: {filepath}")
        return str(filepath)
    
    def close(self):
        """크롤러 종료"""
        print(f"Mock 크롤러 종료. 총 수집: {self.collected_count}개")

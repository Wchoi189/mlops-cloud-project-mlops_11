"""
대량 데이터 수집 테스트 스크립트

1.1 단계 요구사항:
- 일일 최소 1000개 영화 데이터 수집 검증
- 다중 페이지 수집 (1-100 페이지)
- 장시간 수집 시 안정성 확인
"""

import sys
import os
import logging
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from data_processing.tmdb_api_connector import TMDBAPIConnector
from data_processing.response_parser import TMDBResponseParser
from data_processing.rate_limiter import RateLimiter, RateLimitConfig

def setup_logging():
    """로깅 설정"""
    log_dir = project_root / 'logs' / 'data'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'bulk_collection_test.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_bulk_collection(target_movies: int = 1000, max_pages: int = 50):
    """
    대량 데이터 수집 테스트
    
    Args:
        target_movies: 목표 영화 수
        max_pages: 최대 페이지 수
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"대량 데이터 수집 테스트 시작 - 목표: {target_movies}개 영화")
    
    # API 키 확인
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.error("TMDB_API_KEY가 설정되지 않음")
        return False
    
    try:
        # 컴포넌트 초기화
        rate_limiter = RateLimiter(RateLimitConfig(
            requests_per_second=2.0,  # 안전한 속도
            requests_per_minute=100,
            requests_per_hour=2000
        ))
        
        connector = TMDBAPIConnector()
        parser = TMDBResponseParser()
        
        # 수집 통계
        stats = {
            'start_time': datetime.now(),
            'total_pages': 0,
            'total_movies': 0,
            'unique_movies': 0,
            'failed_requests': 0,
            'api_errors': 0,
            'processing_errors': 0
        }
        
        all_movies = []
        unique_movie_ids = set()
        
        logger.info("데이터 수집 시작...")
        
        for page in range(1, max_pages + 1):
            if stats['total_movies'] >= target_movies:
                logger.info(f"목표 달성! {stats['total_movies']}개 영화 수집 완료")
                break
            
            try:
                # Rate Limiting 적용
                if not rate_limiter.acquire(timeout=30):
                    logger.warning(f"페이지 {page}: Rate Limiter 타임아웃")
                    stats['failed_requests'] += 1
                    continue
                
                # API 호출
                logger.info(f"페이지 {page} 수집 중...")
                response = connector.get_popular_movies(page=page)
                
                if not response or 'results' not in response:
                    logger.warning(f"페이지 {page}: 잘못된 응답")
                    stats['api_errors'] += 1
                    continue
                
                # 응답 파싱
                movies, pagination = parser.parse_movie_list_response(response)
                valid_movies = parser.filter_valid_movies(movies)
                
                # 중복 제거
                new_movies = []
                for movie in valid_movies:
                    if movie.movie_id not in unique_movie_ids:
                        unique_movie_ids.add(movie.movie_id)
                        new_movies.append(movie)
                
                all_movies.extend(new_movies)
                
                # 통계 업데이트
                stats['total_pages'] += 1
                stats['total_movies'] += len(movies)
                stats['unique_movies'] = len(unique_movie_ids)
                
                logger.info(f"페이지 {page} 완료: {len(movies)}개 영화, 누적 {stats['unique_movies']}개 (중복 제거)")
                
                # 진행률 출력
                if page % 10 == 0:
                    elapsed = (datetime.now() - stats['start_time']).total_seconds()
                    rate = stats['unique_movies'] / elapsed * 60  # 분당 처리율
                    logger.info(f"진행 상황: {page}페이지, {stats['unique_movies']}개 영화, {rate:.1f}개/분")
                
            except Exception as e:
                logger.error(f"페이지 {page} 처리 중 오류: {e}")
                stats['processing_errors'] += 1
                continue
        
        # 최종 통계
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        stats['average_rate'] = stats['unique_movies'] / stats['duration'] * 60 if stats['duration'] > 0 else 0
        
        # 결과 저장
        save_collection_results(all_movies, stats)
        
        # 성능 분석
        analyze_performance(stats)
        
        # 성공 기준 확인
        success = stats['unique_movies'] >= target_movies
        
        if success:
            logger.info(f"✅ 대량 수집 테스트 성공: {stats['unique_movies']}개 영화 수집")
        else:
            logger.warning(f"⚠️ 대량 수집 테스트 부분 성공: {stats['unique_movies']}/{target_movies}개 영화 수집")
        
        connector.close()
        return success
        
    except Exception as e:
        logger.error(f"대량 수집 테스트 실패: {e}")
        return False

def save_collection_results(movies: List, stats: Dict[str, Any]):
    """수집 결과 저장"""
    logger = logging.getLogger(__name__)
    
    try:
        # 데이터 저장 디렉토리
        output_dir = project_root / 'data' / 'raw' / 'movies'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 영화 데이터 저장
        movies_file = output_dir / f'bulk_collection_{timestamp}.json'
        movies_data = {
            'collection_info': {
                'timestamp': timestamp,
                'total_movies': len(movies),
                'collection_duration': stats.get('duration', 0)
            },
            'movies': [movie.to_dict() for movie in movies]
        }
        
        with open(movies_file, 'w', encoding='utf-8') as f:
            json.dump(movies_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 통계 저장
        stats_file = output_dir / f'collection_stats_{timestamp}.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"수집 결과 저장 완료:")
        logger.info(f"  영화 데이터: {movies_file}")
        logger.info(f"  수집 통계: {stats_file}")
        
    except Exception as e:
        logger.error(f"결과 저장 실패: {e}")

def analyze_performance(stats: Dict[str, Any]):
    """성능 분석"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== 성능 분석 결과 ===")
    logger.info(f"수집 시간: {stats['duration']:.1f}초 ({stats['duration']/60:.1f}분)")
    logger.info(f"처리된 페이지: {stats['total_pages']}개")
    logger.info(f"수집된 영화: {stats['unique_movies']}개 (중복 제거)")
    logger.info(f"평균 처리 속도: {stats['average_rate']:.1f}개/분")
    logger.info(f"실패한 요청: {stats['failed_requests']}개")
    logger.info(f"API 오류: {stats['api_errors']}개")
    logger.info(f"처리 오류: {stats['processing_errors']}개")
    
    # 성능 등급 평가
    if stats['average_rate'] >= 50:
        grade = "🟢 우수"
    elif stats['average_rate'] >= 30:
        grade = "🟡 양호"
    elif stats['average_rate'] >= 15:
        grade = "🟠 보통"
    else:
        grade = "🔴 개선 필요"
    
    logger.info(f"성능 등급: {grade}")
    
    # 안정성 평가
    error_rate = (stats['failed_requests'] + stats['api_errors'] + stats['processing_errors']) / stats['total_pages'] if stats['total_pages'] > 0 else 0
    
    if error_rate <= 0.05:
        stability = "🟢 매우 안정적"
    elif error_rate <= 0.1:
        stability = "🟡 안정적"
    elif error_rate <= 0.2:
        stability = "🟠 보통"
    else:
        stability = "🔴 불안정"
    
    logger.info(f"시스템 안정성: {stability} (오류율: {error_rate*100:.1f}%)")

def main():
    """메인 실행 함수"""
    logger = setup_logging()
    
    print("\n" + "="*60)
    print("TMDB 대량 데이터 수집 테스트")
    print("="*60)
    
    # 테스트 시나리오들
    test_scenarios = [
        {"name": "소규모 테스트", "target": 100, "pages": 5},
        {"name": "중간 규모 테스트", "target": 500, "pages": 25},
        {"name": "대량 수집 테스트", "target": 1000, "pages": 50}
    ]
    
    print("\n테스트 시나리오를 선택하세요:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. {scenario['name']} ({scenario['target']}개 영화, {scenario['pages']}페이지)")
    
    try:
        choice = input("\n선택 (1-3, 기본값 1): ").strip()
        choice = int(choice) if choice else 1
        choice = max(1, min(3, choice))  # 1-3 범위로 제한
        
        scenario = test_scenarios[choice - 1]
        
        print(f"\n{scenario['name']} 시작...")
        success = test_bulk_collection(
            target_movies=scenario['target'],
            max_pages=scenario['pages']
        )
        
        if success:
            print("\n✅ 테스트 완료! 로그 파일에서 상세 결과를 확인하세요.")
        else:
            print("\n⚠️ 테스트 부분 완료. 로그 파일에서 상세 내용을 확인하세요.")
        
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")
        print(f"\n❌ 테스트 실행 실패: {e}")

if __name__ == "__main__":
    main()

# src/data_processing/test_crawler.py
"""
TMDB 크롤러 테스트 스크립트
"""

import sys
import os
import logging
from pathlib import Path
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_processing.tmdb_crawler import TMDBCrawler, create_tmdb_crawler, quick_collect_popular_movies

def setup_logging():
    """로깅 설정"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'test_crawler.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_basic_crawler():
    """기본 크롤러 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 기본 크롤러 테스트 시작 ===")
    
    # API 키 확인
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 크롤러 테스트 건너뜀")
        return False
    
    try:
        # 크롤러 생성
        crawler = create_tmdb_crawler()
        
        # 연결 테스트
        if not crawler.connector.test_connection():
            logger.error("TMDB API 연결 실패")
            return False
        
        logger.info("TMDB API 연결 성공")
        
        # 단일 페이지 인기 영화 수집 테스트
        logger.info("단일 페이지 수집 테스트")
        single_page = crawler.get_popular_movies_bulk(1, 1)
        logger.info(f"단일 페이지 수집 결과: {len(single_page)}개 영화")
        
        # 데이터 검증 테스트
        if single_page:
            valid_movies = crawler.filter_valid_movies(single_page)
            logger.info(f"유효한 영화: {len(valid_movies)}개")
            
            # 첫 번째 영화 상세 정보
            first_movie = valid_movies[0] if valid_movies else None
            if first_movie:
                logger.info(f"첫 번째 영화: {first_movie.get('title')} (ID: {first_movie.get('id')})")
        
        # 수집 통계
        stats = crawler.get_collection_stats()
        logger.info(f"수집 통계: {json.dumps(stats, indent=2, default=str)}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"기본 크롤러 테스트 실패: {e}")
        return False

def test_bulk_collection():
    """대량 수집 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 대량 수집 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 대량 수집 테스트 건너뜀")
        return False
    
    try:
        crawler = create_tmdb_crawler()
        
        # 다중 페이지 수집 테스트 (3페이지)
        logger.info("다중 페이지 수집 테스트 (3페이지)")
        bulk_movies = crawler.get_popular_movies_bulk(1, 3)
        logger.info(f"대량 수집 결과: {len(bulk_movies)}개 영화")
        
        # 유효성 검증
        valid_movies = crawler.filter_valid_movies(bulk_movies)
        validation_rate = len(valid_movies) / len(bulk_movies) * 100 if bulk_movies else 0
        logger.info(f"검증 통과율: {validation_rate:.1f}% ({len(valid_movies)}/{len(bulk_movies)})")
        
        # 중복 확인
        unique_movies = crawler.remove_duplicates(bulk_movies)
        duplicate_rate = (len(bulk_movies) - len(unique_movies)) / len(bulk_movies) * 100 if bulk_movies else 0
        logger.info(f"중복률: {duplicate_rate:.1f}% ({len(bulk_movies) - len(unique_movies)}개 중복)")
        
        # 결과 저장 테스트
        if valid_movies:
            save_path = crawler.save_collection_results(
                valid_movies[:10],  # 처음 10개만 저장
                'test_bulk_collection',
                {'test_type': 'bulk_collection', 'pages': 3}
            )
            logger.info(f"테스트 결과 저장: {save_path}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"대량 수집 테스트 실패: {e}")
        return False

def test_genre_collection():
    """장르별 수집 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 장르별 수집 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 장르별 수집 테스트 건너뜀")
        return False
    
    try:
        crawler = create_tmdb_crawler()
        
        # 액션 영화 수집 테스트 (장르 ID: 28)
        logger.info("액션 영화 수집 테스트")
        action_movies = crawler.get_movies_by_genre(28, 3)  # 3페이지
        logger.info(f"액션 영화 수집 결과: {len(action_movies)}개")
        
        # 코미디 영화 수집 테스트 (장르 ID: 35)
        logger.info("코미디 영화 수집 테스트")
        comedy_movies = crawler.get_movies_by_genre(35, 2)  # 2페이지
        logger.info(f"코미디 영화 수집 결과: {len(comedy_movies)}개")
        
        # 검증 및 저장
        if action_movies:
            valid_action = crawler.filter_valid_movies(action_movies)
            save_path = crawler.save_collection_results(
                valid_action[:5],
                'test_genre_action',
                {'genre_id': 28, 'genre_name': '액션', 'test_type': 'genre_collection'}
            )
            logger.info(f"액션 영화 테스트 결과 저장: {save_path}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"장르별 수집 테스트 실패: {e}")
        return False

def test_trending_collection():
    """트렌딩 수집 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 트렌딩 수집 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 트렌딩 수집 테스트 건너뜀")
        return False
    
    try:
        crawler = create_tmdb_crawler()
        
        # 일간 트렌딩 수집
        logger.info("일간 트렌딩 영화 수집 테스트")
        daily_trending = crawler.get_trending_movies('day')
        logger.info(f"일간 트렌딩 결과: {len(daily_trending)}개")
        
        # 주간 트렌딩 수집
        logger.info("주간 트렌딩 영화 수집 테스트")
        weekly_trending = crawler.get_trending_movies('week')
        logger.info(f"주간 트렌딩 결과: {len(weekly_trending)}개")
        
        # 결과 저장
        if daily_trending:
            valid_trending = crawler.filter_valid_movies(daily_trending)
            save_path = crawler.save_collection_results(
                valid_trending,
                'test_trending_daily',
                {'time_window': 'day', 'test_type': 'trending_collection'}
            )
            logger.info(f"트렌딩 테스트 결과 저장: {save_path}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"트렌딩 수집 테스트 실패: {e}")
        return False

def test_top_rated_collection():
    """평점 높은 영화 수집 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 평점 높은 영화 수집 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 평점 높은 영화 테스트 건너뜀")
        return False
    
    try:
        crawler = create_tmdb_crawler()
        
        # 평점 8.0 이상 영화 수집
        logger.info("평점 8.0 이상 영화 수집 테스트")
        top_rated = crawler.get_top_rated_movies(8.0, 5)  # 5페이지
        logger.info(f"평점 높은 영화 결과: {len(top_rated)}개")
        
        # 평점 분석
        if top_rated:
            ratings = [m.get('vote_average', 0) for m in top_rated]
            avg_rating = sum(ratings) / len(ratings)
            max_rating = max(ratings)
            min_rating = min(ratings)
            
            logger.info(f"평점 분석 - 평균: {avg_rating:.2f}, 최고: {max_rating}, 최저: {min_rating}")
            
            # 결과 저장
            valid_top_rated = crawler.filter_valid_movies(top_rated)
            save_path = crawler.save_collection_results(
                valid_top_rated[:5],
                'test_top_rated',
                {'min_rating': 8.0, 'test_type': 'top_rated_collection'}
            )
            logger.info(f"평점 높은 영화 테스트 결과 저장: {save_path}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"평점 높은 영화 수집 테스트 실패: {e}")
        return False

def test_comprehensive_collection():
    """종합 수집 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 종합 수집 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 종합 수집 테스트 건너뜀")
        return False
    
    try:
        crawler = create_tmdb_crawler()
        
        # 소규모 종합 수집 (테스트용)
        logger.info("소규모 종합 데이터 수집 시작")
        
        # 인기 영화 5페이지
        popular = crawler.get_popular_movies_bulk(1, 5)
        logger.info(f"인기 영화: {len(popular)}개")
        
        # 액션 영화 3페이지
        action = crawler.get_movies_by_genre(28, 3)
        logger.info(f"액션 영화: {len(action)}개")
        
        # 트렌딩 영화
        trending = crawler.get_trending_movies('day')
        logger.info(f"트렌딩 영화: {len(trending)}개")
        
        # 전체 통합
        all_movies = popular + action + trending
        unique_movies = crawler.remove_duplicates(all_movies)
        valid_movies = crawler.filter_valid_movies(unique_movies)
        
        logger.info(f"통합 결과 - 총 수집: {len(all_movies)}, 중복 제거: {len(unique_movies)}, 유효: {len(valid_movies)}")
        
        # 최종 결과 저장
        if valid_movies:
            save_path = crawler.save_collection_results(
                valid_movies,
                'test_comprehensive',
                {
                    'test_type': 'comprehensive_collection',
                    'sources': ['popular', 'action', 'trending'],
                    'total_unique': len(unique_movies),
                    'total_valid': len(valid_movies)
                }
            )
            logger.info(f"종합 테스트 결과 저장: {save_path}")
        
        # 통계 출력
        stats = crawler.get_collection_stats()
        logger.info(f"최종 통계: {json.dumps(stats, indent=2, default=str)}")
        
        crawler.close()
        return True
        
    except Exception as e:
        logger.error(f"종합 수집 테스트 실패: {e}")
        return False

def test_quick_functions():
    """빠른 함수들 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 빠른 함수 테스트 시작 ===")
    
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 빠른 함수 테스트 건너뜀")
        return False
    
    try:
        # 빠른 인기 영화 수집
        logger.info("빠른 인기 영화 수집 테스트")
        quick_movies = quick_collect_popular_movies(2)  # 2페이지
        logger.info(f"빠른 수집 결과: {len(quick_movies)}개 영화")
        
        return True
        
    except Exception as e:
        logger.error(f"빠른 함수 테스트 실패: {e}")
        return False

def generate_test_report(test_results):
    """테스트 결과 보고서 생성"""
    logger = logging.getLogger(__name__)
    
    report = {
        'test_date': datetime.now().isoformat(),
        'test_results': test_results,
        'summary': {
            'total_tests': len(test_results),
            'passed_tests': sum(1 for result in test_results.values() if result),
            'failed_tests': sum(1 for result in test_results.values() if not result),
            'success_rate': sum(1 for result in test_results.values() if result) / len(test_results) * 100
        },
        'recommendations': []
    }
    
    # 권장사항 생성
    if not test_results.get('basic_crawler'):
        report['recommendations'].append("기본 크롤러 테스트가 실패했습니다. API 키와 네트워크 연결을 확인하세요.")
    
    if test_results.get('basic_crawler') and not test_results.get('bulk_collection'):
        report['recommendations'].append("대량 수집이 실패했습니다. Rate Limiting 설정을 확인하세요.")
    
    if all(test_results.values()):
        report['recommendations'].append("모든 크롤러 테스트가 성공했습니다. 이제 스케줄링 시스템을 구현할 수 있습니다.")
    
    # 보고서 저장
    try:
        report_dir = project_root / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f'crawler_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"크롤러 테스트 보고서 저장: {report_file}")
        
    except Exception as e:
        logger.error(f"테스트 보고서 저장 실패: {e}")
    
    return report

def main():
    """메인 테스트 실행 함수"""
    logger = setup_logging()
    logger.info("TMDB 크롤러 통합 테스트 시작")
    
    test_results = {}
    
    print("\n" + "="*60)
    print("TMDB 크롤러 1.2 단계 통합 테스트")
    print("="*60)
    
    # 1. 기본 크롤러 테스트
    print("\n1. 기본 크롤러 테스트...")
    test_results['basic_crawler'] = test_basic_crawler()
    print(f"   결과: {'✅ 성공' if test_results['basic_crawler'] else '❌ 실패'}")
    
    # 2. 대량 수집 테스트
    print("\n2. 대량 수집 테스트...")
    test_results['bulk_collection'] = test_bulk_collection()
    print(f"   결과: {'✅ 성공' if test_results['bulk_collection'] else '❌ 실패'}")
    
    # 3. 장르별 수집 테스트
    print("\n3. 장르별 수집 테스트...")
    test_results['genre_collection'] = test_genre_collection()
    print(f"   결과: {'✅ 성공' if test_results['genre_collection'] else '❌ 실패'}")
    
    # 4. 트렌딩 수집 테스트
    print("\n4. 트렌딩 수집 테스트...")
    test_results['trending_collection'] = test_trending_collection()
    print(f"   결과: {'✅ 성공' if test_results['trending_collection'] else '❌ 실패'}")
    
    # 5. 평점 높은 영화 테스트
    print("\n5. 평점 높은 영화 테스트...")
    test_results['top_rated_collection'] = test_top_rated_collection()
    print(f"   결과: {'✅ 성공' if test_results['top_rated_collection'] else '❌ 실패'}")
    
    # 6. 종합 수집 테스트
    print("\n6. 종합 수집 테스트...")
    test_results['comprehensive_collection'] = test_comprehensive_collection()
    print(f"   결과: {'✅ 성공' if test_results['comprehensive_collection'] else '❌ 실패'}")
    
    # 7. 빠른 함수 테스트
    print("\n7. 빠른 함수 테스트...")
    test_results['quick_functions'] = test_quick_functions()
    print(f"   결과: {'✅ 성공' if test_results['quick_functions'] else '❌ 실패'}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:25}: {status}")
    
    print(f"\n전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    
    # 보고서 생성
    report = generate_test_report(test_results)
    
    # 권장사항 출력
    if report['recommendations']:
        print("\n권장사항:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print("\n크롤러 테스트 완료!")
    
    return test_results

if __name__ == "__main__":
    results = main()

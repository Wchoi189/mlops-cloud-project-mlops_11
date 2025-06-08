"""
TMDB API 연동 테스트 스크립트

1.1 단계의 모든 구현 사항을 테스트합니다:
- API 연결 테스트
- 환경변수 로딩
- 응답 파싱
- Rate Limiting
"""

import sys
import os
import logging
from pathlib import Path
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from data_processing.tmdb_api_connector import TMDBAPIConnector, test_tmdb_connection
from data_processing.environment_manager import EnvironmentManager, validate_environment
from data_processing.response_parser import TMDBResponseParser, parse_tmdb_response
from data_processing.rate_limiter import RateLimiter, RateLimitConfig

def setup_logging():
    """로깅 설정"""
    # logs 디렉토리 생성
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일 경로를 logs 디렉토리로 설정
    log_file = log_dir / 'test_tmdb_integration.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_environment_setup():
    """환경변수 설정 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 환경변수 설정 테스트 시작 ===")
    
    try:
        # 환경변수 매니저 생성
        env_manager = EnvironmentManager()
        
        # .env 템플릿 파일 생성
        template_path = project_root / '.env.template'
        env_manager.create_env_template(str(template_path))
        logger.info(f"환경변수 템플릿 생성됨: {template_path}")
        
        # 환경변수 검증
        validation_results = validate_environment()
        logger.info(f"환경변수 검증 결과: {validation_results}")
        
        # TMDB 설정 확인 (API 키가 있는 경우에만)
        if os.getenv('TMDB_API_KEY'):
            tmdb_config = env_manager.get_tmdb_config()
            logger.info(f"TMDB 설정 로드 성공: {tmdb_config}")
        else:
            logger.warning("TMDB_API_KEY가 설정되지 않음")
        
        return True
        
    except Exception as e:
        logger.error(f"환경변수 설정 테스트 실패: {e}")
        return False

def test_rate_limiter():
    """Rate Limiter 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== Rate Limiter 테스트 시작 ===")
    
    try:
        # Rate Limiter 설정
        config = RateLimitConfig(
            requests_per_second=2.0,
            requests_per_minute=10,
            burst_allowance=5
        )
        rate_limiter = RateLimiter(config)
        
        # 연속 요청 테스트
        logger.info("연속 요청 테스트 시작")
        for i in range(3):
            if rate_limiter.acquire(timeout=5):
                logger.info(f"요청 {i+1} 성공")
            else:
                logger.warning(f"요청 {i+1} 실패")
        
        # 통계 확인
        stats = rate_limiter.get_stats()
        logger.info(f"Rate Limiter 통계: {json.dumps(stats, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Rate Limiter 테스트 실패: {e}")
        return False

def test_api_connection():
    """API 연결 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== API 연결 테스트 시작 ===")
    
    # API 키 확인
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. API 연결 테스트 건너뜀")
        return False
    
    try:
        # 기본 연결 테스트
        if test_tmdb_connection():
            logger.info("TMDB API 기본 연결 성공")
        else:
            logger.error("TMDB API 기본 연결 실패")
            return False
        
        # 상세 API 테스트
        connector = TMDBAPIConnector()
        
        # 연결 테스트
        if connector.test_connection():
            logger.info("TMDB API 상세 연결 성공")
        else:
            logger.error("TMDB API 상세 연결 실패")
            return False
        
        # 인기 영화 조회 테스트
        logger.info("인기 영화 조회 테스트")
        popular_response = connector.get_popular_movies(page=1)
        logger.info(f"인기 영화 조회 성공: {len(popular_response.get('results', []))}개 영화")
        
        # 트렌딩 영화 조회 테스트
        logger.info("트렌딩 영화 조회 테스트")
        trending_response = connector.get_trending_movies('day')
        logger.info(f"트렌딩 영화 조회 성공: {len(trending_response.get('results', []))}개 영화")
        
        # API 사용량 통계
        stats = connector.get_api_usage_stats()
        logger.info(f"API 사용량 통계: {json.dumps(stats, indent=2, default=str)}")
        
        connector.close()
        return True
        
    except Exception as e:
        logger.error(f"API 연결 테스트 실패: {e}")
        return False

def test_response_parsing():
    """응답 파싱 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 응답 파싱 테스트 시작 ===")
    
    try:
        # 샘플 응답 데이터 (실제 TMDB API 응답 형식)
        sample_response = {
            "page": 1,
            "results": [
                {
                    "adult": False,
                    "backdrop_path": "/path1.jpg",
                    "genre_ids": [28, 12, 878],
                    "id": 12345,
                    "original_language": "en",
                    "original_title": "Sample Movie",
                    "overview": "This is a sample movie for testing.",
                    "popularity": 1234.567,
                    "poster_path": "/poster1.jpg",
                    "release_date": "2025-06-01",
                    "title": "샘플 영화",
                    "video": False,
                    "vote_average": 8.5,
                    "vote_count": 1000
                }
            ],
            "total_pages": 100,
            "total_results": 2000
        }
        
        # 응답 파싱 테스트
        parser = TMDBResponseParser()
        movies, pagination = parser.parse_movie_list_response(sample_response)
        
        logger.info(f"파싱된 영화 수: {len(movies)}")
        logger.info(f"페이지네이션 정보: 페이지 {pagination.page}/{pagination.total_pages}")
        
        # 첫 번째 영화 데이터 확인
        if movies:
            first_movie = movies[0]
            logger.info(f"첫 번째 영화: {first_movie.title} (ID: {first_movie.movie_id})")
            
            # 데이터 검증
            if parser.validate_movie_data(first_movie):
                logger.info("영화 데이터 검증 성공")
            else:
                logger.warning("영화 데이터 검증 실패")
            
            # 딕셔너리 변환 테스트
            movie_dict = first_movie.to_dict()
            logger.info(f"딕셔너리 변환 성공: {len(movie_dict)} 필드")
        
        # 트렌딩 데이터 파싱 테스트
        trending_data = parser.extract_trending_data(sample_response)
        logger.info(f"트렌딩 데이터 파싱 완료: {trending_data.get('total_movies')}개 영화")
        
        return True
        
    except Exception as e:
        logger.error(f"응답 파싱 테스트 실패: {e}")
        return False

def test_integration():
    """통합 테스트"""
    logger = logging.getLogger(__name__)
    logger.info("=== 통합 테스트 시작 ===")
    
    # API 키 확인
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않음. 통합 테스트 건너뜀")
        return False
    
    try:
        # Rate Limiter와 함께 API 커넥터 생성
        rate_limiter = RateLimiter(RateLimitConfig(requests_per_second=1.0))
        
        # API 커넥터 생성
        connector = TMDBAPIConnector()
        parser = TMDBResponseParser()
        
        # 실제 API 호출 및 파싱 테스트
        logger.info("실제 데이터 수집 및 파싱 테스트")
        
        # Rate Limiter 적용하여 요청
        if rate_limiter.acquire(timeout=10):
            # 인기 영화 조회
            response = connector.get_popular_movies(page=1)
            movies, pagination = parser.parse_movie_list_response(response)
            
            logger.info(f"실제 데이터 수집 성공: {len(movies)}개 영화")
            
            # 유효한 데이터만 필터링
            valid_movies = parser.filter_valid_movies(movies)
            logger.info(f"유효한 영화 데이터: {len(valid_movies)}개")
            
            # 데이터 저장 테스트
            output_dir = project_root / 'data' / 'test'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # JSON 형태로 저장
            output_data = {
                'collected_at': datetime.now().isoformat(),
                'total_movies': len(valid_movies),
                'pagination': {
                    'page': pagination.page,
                    'total_pages': pagination.total_pages,
                    'total_results': pagination.total_results
                },
                'movies': [movie.to_dict() for movie in valid_movies[:5]]  # 처음 5개만 저장
            }
            
            output_file = output_dir / f'test_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            parser.save_parsed_data(output_data, str(output_file))
            logger.info(f"테스트 데이터 저장 완료: {output_file}")
        
        else:
            logger.error("Rate Limiter로 인한 요청 실패")
            return False
        
        # 통계 수집
        api_stats = connector.get_api_usage_stats()
        rate_stats = rate_limiter.get_stats()
        
        logger.info(f"API 통계: {json.dumps(api_stats, indent=2, default=str)}")
        logger.info(f"Rate Limiter 통계: {json.dumps(rate_stats, indent=2, default=str)}")
        
        connector.close()
        return True
        
    except Exception as e:
        logger.error(f"통합 테스트 실패: {e}")
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
    if not test_results.get('environment'):
        report['recommendations'].append("환경변수 설정을 확인하세요. .env.template을 참조하여 .env 파일을 생성하세요.")
    
    if not test_results.get('api_connection'):
        report['recommendations'].append("TMDB API 키를 확인하고 네트워크 연결을 점검하세요.")
    
    if test_results.get('rate_limiter') and test_results.get('api_connection'):
        report['recommendations'].append("모든 기본 테스트가 통과했습니다. 이제 실제 데이터 수집을 시작할 수 있습니다.")
    
    # 보고서 저장
    try:
        report_dir = project_root / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f'tmdb_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"테스트 보고서 저장됨: {report_file}")
        
    except Exception as e:
        logger.error(f"테스트 보고서 저장 실패: {e}")
    
    return report

def main():
    """메인 테스트 실행 함수"""
    logger = setup_logging()
    logger.info("TMDB API 연동 통합 테스트 시작")
    
    # 테스트 결과 저장
    test_results = {}
    
    print("\n" + "="*60)
    print("TMDB API 연동 1.1 단계 통합 테스트")
    print("="*60)
    
    # 1. 환경변수 설정 테스트
    print("\n1. 환경변수 설정 테스트...")
    test_results['environment'] = test_environment_setup()
    print(f"   결과: {'✅ 성공' if test_results['environment'] else '❌ 실패'}")
    
    # 2. Rate Limiter 테스트
    print("\n2. Rate Limiter 테스트...")
    test_results['rate_limiter'] = test_rate_limiter()
    print(f"   결과: {'✅ 성공' if test_results['rate_limiter'] else '❌ 실패'}")
    
    # 3. 응답 파싱 테스트
    print("\n3. 응답 파싱 테스트...")
    test_results['response_parsing'] = test_response_parsing()
    print(f"   결과: {'✅ 성공' if test_results['response_parsing'] else '❌ 실패'}")
    
    # 4. API 연결 테스트 (API 키가 있는 경우에만)
    print("\n4. API 연결 테스트...")
    test_results['api_connection'] = test_api_connection()
    print(f"   결과: {'✅ 성공' if test_results['api_connection'] else '❌ 실패 (API 키 없음)'}")
    
    # 5. 통합 테스트 (API 키가 있는 경우에만)
    if test_results['api_connection']:
        print("\n5. 통합 테스트...")
        test_results['integration'] = test_integration()
        print(f"   결과: {'✅ 성공' if test_results['integration'] else '❌ 실패'}")
    else:
        test_results['integration'] = False
        print("\n5. 통합 테스트... ⏭️ 건너뜀 (API 키 필요)")
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:20}: {status}")
    
    print(f"\n전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    
    # 보고서 생성
    report = generate_test_report(test_results)
    
    # 권장사항 출력
    if report['recommendations']:
        print("\n권장사항:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print("\n테스트 완료!")
    
    return test_results

if __name__ == "__main__":
    results = main()

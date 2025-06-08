#!/usr/bin/env python3
"""
TMDB 일일 데이터 수집 스크립트
독립적으로 실행 가능한 일일 데이터 수집 도구
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import argparse
import traceback

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from data_processing.tmdb_api_connector import TMDBAPIConnector
from data_processing.quality_validator import DataQualityValidator


class DailyCollector:
    """일일 데이터 수집기"""
    
    def __init__(self, output_dir=None, log_level='INFO'):
        self.output_dir = Path(output_dir) if output_dir else project_root / 'data' / 'raw' / 'movies'
        self.setup_logging(log_level)
        
    def setup_logging(self, log_level):
        """로깅 설정"""
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='[%(asctime)s] %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'daily_collection.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('daily_collector')
        
    def collect_popular_movies(self, max_pages=5):
        """인기 영화 수집"""
        self.logger.info(f"인기 영화 수집 시작 (최대 {max_pages}페이지)")
        
        connector = TMDBAPIConnector()
        movies = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.debug(f"페이지 {page} 수집 중...")
                
                response = connector.get_popular_movies(page)
                if response and 'results' in response:
                    page_movies = response['results']
                    movies.extend(page_movies)
                    self.logger.debug(f"페이지 {page}: {len(page_movies)}개 영화 수집")
                    
                    # API 제한 준수를 위한 대기
                    time.sleep(0.25)
                else:
                    self.logger.warning(f"페이지 {page} 수집 실패")
                    break
            
            self.logger.info(f"인기 영화 수집 완료: 총 {len(movies)}개")
            return movies
            
        except Exception as e:
            self.logger.error(f"인기 영화 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def collect_trending_movies(self, time_window='day'):
        """트렌딩 영화 수집"""
        self.logger.info(f"트렌딩 영화 수집 시작 ({time_window})")
        
        connector = TMDBAPIConnector()
        
        try:
            response = connector.get_trending_movies(time_window)
            if response and 'results' in response:
                movies = response['results']
                self.logger.info(f"트렌딩 영화 수집 완료: {len(movies)}개")
                return movies
            else:
                self.logger.warning("트렌딩 영화 수집 실패")
                return []
                
        except Exception as e:
            self.logger.error(f"트렌딩 영화 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def collect_latest_movies(self, max_pages=3):
        """최신 영화 수집"""
        self.logger.info(f"최신 영화 수집 시작 (최대 {max_pages}페이지)")
        
        connector = TMDBAPIConnector()
        movies = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.debug(f"페이지 {page} 수집 중...")
                
                response = connector.get_latest_movies(page)
                if response and 'results' in response:
                    page_movies = response['results']
                    movies.extend(page_movies)
                    self.logger.debug(f"페이지 {page}: {len(page_movies)}개 영화 수집")
                    
                    time.sleep(0.25)
                else:
                    self.logger.warning(f"페이지 {page} 수집 실패")
                    break
            
            self.logger.info(f"최신 영화 수집 완료: 총 {len(movies)}개")
            return movies
            
        except Exception as e:
            self.logger.error(f"최신 영화 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def remove_duplicates(self, movies):
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
            self.logger.info(f"중복 제거: {removed_count}개 영화 제거됨")
        
        return unique_movies
    
    def validate_data(self, movies):
        """데이터 품질 검증"""
        self.logger.info("데이터 품질 검증 시작")
        
        validator = DataQualityValidator()
        
        try:
            batch_results = validator.validate_batch_data(movies)
            
            self.logger.info(f"검증 결과:")
            self.logger.info(f"  총 영화: {batch_results['total_movies']}")
            self.logger.info(f"  유효한 영화: {batch_results['valid_movies']}")
            self.logger.info(f"  유효율: {batch_results['valid_movies']/batch_results['total_movies']*100:.1f}%")
            
            # 유효한 영화만 반환
            valid_movies = []
            for movie in movies:
                is_valid, reason, details = validator.validate_single_movie(movie)
                if is_valid:
                    valid_movies.append(movie)
            
            return valid_movies, batch_results
            
        except Exception as e:
            self.logger.error(f"데이터 검증 중 오류: {e}")
            return movies, None
    
    def save_data(self, movies, collection_type, metadata=None):
        """데이터 저장"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{collection_type}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        data_to_save = {
            'movies': movies,
            'collection_info': metadata or {},
            'save_timestamp': datetime.now().isoformat(),
            'total_count': len(movies)
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"데이터 저장 완료: {filepath}")
            self.logger.info(f"저장된 영화 수: {len(movies)}")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"데이터 저장 중 오류: {e}")
            raise
    
    def generate_summary_report(self, collection_results):
        """일일 수집 요약 리포트 생성"""
        report_dir = project_root / 'data' / 'raw' / 'metadata' / 'daily_summaries'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y%m%d')
        report_file = report_dir / f"daily_summary_{date_str}.json"
        
        # 총 수집 통계 계산
        total_collected = sum(result.get('total_collected', 0) for result in collection_results.values())
        total_valid = sum(result.get('total_valid', 0) for result in collection_results.values())
        
        summary = {
            'date': date_str,
            'generation_time': datetime.now().isoformat(),
            'collection_summary': {
                'total_collected': total_collected,
                'total_valid': total_valid,
                'validity_rate': (total_valid / total_collected * 100) if total_collected > 0 else 0,
                'by_type': collection_results
            },
            'files_generated': list(collection_results.keys())
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"일일 요약 리포트 생성: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"리포트 생성 중 오류: {e}")
            return None
    
    def run_daily_collection(self, popular_pages=5, latest_pages=3, include_trending=True):
        """일일 수집 실행"""
        self.logger.info("=== TMDB 일일 데이터 수집 시작 ===")
        start_time = datetime.now()
        
        collection_results = {}
        
        try:
            # 1. 인기 영화 수집
            popular_movies = self.collect_popular_movies(popular_pages)
            popular_movies = self.remove_duplicates(popular_movies)
            valid_popular, popular_validation = self.validate_data(popular_movies)
            
            popular_metadata = {
                'collection_type': 'daily_popular',
                'pages_collected': popular_pages,
                'total_collected': len(popular_movies),
                'total_valid': len(valid_popular),
                'validation_results': popular_validation
            }
            
            popular_file = self.save_data(valid_popular, 'daily_popular', popular_metadata)
            collection_results['popular'] = popular_metadata
            
            # 2. 트렌딩 영화 수집 (선택적)
            if include_trending:
                trending_movies = self.collect_trending_movies('day')
                trending_movies = self.remove_duplicates(trending_movies)
                valid_trending, trending_validation = self.validate_data(trending_movies)
                
                trending_metadata = {
                    'collection_type': 'daily_trending',
                    'time_window': 'day',
                    'total_collected': len(trending_movies),
                    'total_valid': len(valid_trending),
                    'validation_results': trending_validation
                }
                
                trending_file = self.save_data(valid_trending, 'daily_trending', trending_metadata)
                collection_results['trending'] = trending_metadata
            
            # 3. 최신 영화 수집
            latest_movies = self.collect_latest_movies(latest_pages)
            latest_movies = self.remove_duplicates(latest_movies)
            valid_latest, latest_validation = self.validate_data(latest_movies)
            
            latest_metadata = {
                'collection_type': 'daily_latest',
                'pages_collected': latest_pages,
                'total_collected': len(latest_movies),
                'total_valid': len(valid_latest),
                'validation_results': latest_validation
            }
            
            latest_file = self.save_data(valid_latest, 'daily_latest', latest_metadata)
            collection_results['latest'] = latest_metadata
            
            # 4. 요약 리포트 생성
            report_file = self.generate_summary_report(collection_results)
            
            # 5. 최종 요약 출력
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            total_collected = sum(r.get('total_collected', 0) for r in collection_results.values())
            total_valid = sum(r.get('total_valid', 0) for r in collection_results.values())
            
            self.logger.info("=== 일일 수집 완료 ===")
            self.logger.info(f"실행 시간: {duration:.1f}초")
            self.logger.info(f"총 수집: {total_collected}개 영화")
            self.logger.info(f"총 유효: {total_valid}개 영화")
            self.logger.info(f"유효율: {total_valid/total_collected*100:.1f}%" if total_collected > 0 else "유효율: N/A")
            
            return {
                'success': True,
                'duration': duration,
                'results': collection_results,
                'report_file': str(report_file) if report_file else None
            }
            
        except Exception as e:
            self.logger.error(f"일일 수집 중 치명적 오류: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='TMDB 일일 데이터 수집')
    parser.add_argument('--popular-pages', type=int, default=5,
                       help='인기 영화 수집 페이지 수 (기본: 5)')
    parser.add_argument('--latest-pages', type=int, default=3,
                       help='최신 영화 수집 페이지 수 (기본: 3)')
    parser.add_argument('--no-trending', action='store_true',
                       help='트렌딩 영화 수집 제외')
    parser.add_argument('--output-dir', help='출력 디렉토리')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='로그 레벨')
    parser.add_argument('--dry-run', action='store_true',
                       help='실제 수집 없이 테스트만 실행')
    
    args = parser.parse_args()
    
    # 일일 수집기 생성
    collector = DailyCollector(
        output_dir=args.output_dir,
        log_level=args.log_level
    )
    
    if args.dry_run:
        collector.logger.info("DRY RUN 모드: 실제 수집 없이 테스트 실행")
        return 0
    
    # 일일 수집 실행
    result = collector.run_daily_collection(
        popular_pages=args.popular_pages,
        latest_pages=args.latest_pages,
        include_trending=not args.no_trending
    )
    
    if result['success']:
        print(f"\n✅ 일일 수집 성공!")
        print(f"실행 시간: {result['duration']:.1f}초")
        if result.get('report_file'):
            print(f"리포트: {result['report_file']}")
        return 0
    else:
        print(f"\n❌ 일일 수집 실패: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

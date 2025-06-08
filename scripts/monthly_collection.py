#!/usr/bin/env python3
"""
TMDB 월간 데이터 수집 스크립트
대량 데이터 수집 및 전체 데이터베이스 갱신
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


class MonthlyCollector:
    """월간 데이터 수집기"""
    
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
                logging.FileHandler(log_dir / 'monthly_collection.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('monthly_collector')
    
    def collect_popular_movies_bulk(self, max_pages=100):
        """인기 영화 대량 수집"""
        self.logger.info(f"인기 영화 대량 수집 시작 (최대 {max_pages}페이지)")
        
        connector = TMDBAPIConnector()
        movies = []
        failed_pages = []
        
        try:
            for page in range(1, max_pages + 1):
                try:
                    self.logger.debug(f"페이지 {page}/{max_pages} 수집 중...")
                    
                    response = connector.get_popular_movies(page)
                    if response and 'results' in response:
                        page_movies = response['results']
                        movies.extend(page_movies)
                        
                        # 진행 상황 로그 (10페이지마다)
                        if page % 10 == 0:
                            self.logger.info(f"진행률: {page}/{max_pages} ({page/max_pages*100:.1f}%) - 수집: {len(movies)}개")
                        
                        # API 제한 준수
                        time.sleep(0.25)
                    else:
                        self.logger.warning(f"페이지 {page} 수집 실패 - 응답 없음")
                        failed_pages.append(page)
                        
                except Exception as e:
                    self.logger.warning(f"페이지 {page} 수집 실패: {e}")
                    failed_pages.append(page)
                    time.sleep(1)  # 오류 시 대기 시간 증가
                    continue
            
            # 중복 제거
            unique_movies = self.remove_duplicates(movies)
            
            self.logger.info(f"인기 영화 대량 수집 완료:")
            self.logger.info(f"  처리된 페이지: {max_pages - len(failed_pages)}")
            self.logger.info(f"  수집된 영화: {len(movies)}개")
            self.logger.info(f"  고유 영화: {len(unique_movies)}개")
            
            return unique_movies
            
        except Exception as e:
            self.logger.error(f"인기 영화 대량 수집 중 치명적 오류: {e}")
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
        
        return unique_movies
    
    def validate_and_clean_data(self, movies, collection_type=""):
        """데이터 검증 및 정제"""
        if not movies:
            return [], None
            
        self.logger.info(f"데이터 검증 및 정제 시작{f' ({collection_type})' if collection_type else ''}")
        
        validator = DataQualityValidator()
        
        try:
            # 배치 검증
            batch_results = validator.validate_batch_data(movies)
            
            # 유효한 영화만 필터링
            valid_movies = []
            for movie in movies:
                is_valid, reason, details = validator.validate_single_movie(movie)
                if is_valid:
                    valid_movies.append(movie)
            
            validation_rate = len(valid_movies) / len(movies) * 100 if movies else 0
            
            self.logger.info(f"검증 완료{f' ({collection_type})' if collection_type else ''}:")
            self.logger.info(f"  총 영화: {len(movies)}")
            self.logger.info(f"  유효한 영화: {len(valid_movies)}")
            self.logger.info(f"  유효율: {validation_rate:.1f}%")
            
            return valid_movies, batch_results
            
        except Exception as e:
            self.logger.error(f"데이터 검증 중 오류: {e}")
            return movies, None
    
    def save_monthly_data(self, movies, collection_type, metadata=None):
        """월간 데이터 저장"""
        if not movies:
            self.logger.warning(f"저장할 데이터가 없습니다: {collection_type}")
            return None
            
        # 저장 디렉토리 생성
        save_dir = self.output_dir / 'monthly'
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        month_str = datetime.now().strftime('%Y%m')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{collection_type}_{month_str}_{timestamp}.json"
        filepath = save_dir / filename
        
        # 저장할 데이터 구성
        data_to_save = {
            'movies': movies,
            'collection_info': metadata or {},
            'save_timestamp': datetime.now().isoformat(),
            'month': month_str,
            'total_count': len(movies)
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"월간 데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"데이터 저장 중 오류: {e}")
            raise
    
    def generate_monthly_report(self, collection_results):
        """월간 수집 리포트 생성"""
        report_dir = project_root / 'data' / 'raw' / 'metadata' / 'monthly_reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        month_str = datetime.now().strftime('%Y%m')
        report_file = report_dir / f"monthly_report_{month_str}.json"
        
        # 수집 통계 계산
        total_collected = sum(
            result.get('metadata', {}).get('total_collected', 0) 
            for result in collection_results.values()
        )
        total_valid = sum(
            result.get('metadata', {}).get('total_valid', 0) 
            for result in collection_results.values()
        )
        
        # 전체 영화 데이터 수집
        all_movies = []
        for result in collection_results.values():
            all_movies.extend(result.get('movies', []))
        
        # 월간 리포트 생성
        report = {
            'report_type': 'monthly',
            'month': month_str,
            'generation_time': datetime.now().isoformat(),
            'collection_summary': {
                'total_collected': total_collected,
                'total_valid': total_valid,
                'validity_rate': (total_valid / total_collected * 100) if total_collected > 0 else 0,
                'unique_movies': len(self.remove_duplicates(all_movies)),
                'by_collection_type': {
                    ctype: result.get('metadata', {})
                    for ctype, result in collection_results.items()
                }
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"월간 리포트 생성: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"리포트 생성 중 오류: {e}")
            return None
    
    def run_monthly_collection(self, popular_pages=100):
        """월간 수집 실행"""
        self.logger.info("=== TMDB 월간 데이터 수집 시작 ===")
        start_time = datetime.now()
        
        collection_results = {}
        
        try:
            # 1. 인기 영화 대량 수집
            self.logger.info("--- 인기 영화 대량 수집 시작 ---")
            popular_movies = self.collect_popular_movies_bulk(popular_pages)
            valid_popular, popular_validation = self.validate_and_clean_data(
                popular_movies, "인기 영화"
            )
            
            popular_metadata = {
                'collection_type': 'monthly_popular',
                'pages_collected': popular_pages,
                'total_collected': len(popular_movies),
                'total_valid': len(valid_popular),
                'validation_results': popular_validation
            }
            
            if valid_popular:
                file_path = self.save_monthly_data(valid_popular, "popular_bulk", popular_metadata)
                collection_results['popular_bulk'] = {
                    'movies': valid_popular,
                    'metadata': popular_metadata,
                    'file_path': file_path
                }
            
            # 2. 월간 리포트 생성
            if collection_results:
                self.logger.info("--- 월간 리포트 생성 시작 ---")
                report_file = self.generate_monthly_report(collection_results)
            else:
                self.logger.warning("수집된 데이터가 없어 리포트 생성을 건너뜁니다.")
                report_file = None
            
            # 3. 최종 요약
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            total_movies = sum(len(r['movies']) for r in collection_results.values())
            
            self.logger.info("=== 월간 수집 완료 ===")
            self.logger.info(f"실행 시간: {duration/60:.1f}분")
            self.logger.info(f"총 영화: {total_movies}개")
            
            return {
                'success': True,
                'duration': duration,
                'total_movies': total_movies,
                'report_file': str(report_file) if report_file else None,
                'collection_results': collection_results
            }
            
        except Exception as e:
            self.logger.error(f"월간 수집 중 치명적 오류: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='TMDB 월간 데이터 수집')
    parser.add_argument('--popular-pages', type=int, default=100,
                       help='인기 영화 수집 페이지 수 (기본: 100)')
    parser.add_argument('--output-dir', help='출력 디렉토리')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='로그 레벨')
    parser.add_argument('--dry-run', action='store_true',
                       help='실제 수집 없이 테스트만 실행')
    
    args = parser.parse_args()
    
    # 월간 수집기 생성
    collector = MonthlyCollector(
        output_dir=args.output_dir,
        log_level=args.log_level
    )
    
    if args.dry_run:
        collector.logger.info("DRY RUN 모드: 실제 수집 없이 테스트 실행")
        return 0
    
    # 월간 수집 실행
    result = collector.run_monthly_collection(
        popular_pages=args.popular_pages
    )
    
    if result['success']:
        print(f"\n✅ 월간 수집 성공!")
        print(f"실행 시간: {result['duration']/60:.1f}분")
        print(f"총 영화: {result['total_movies']}개")
        if result.get('report_file'):
            print(f"리포트: {result['report_file']}")
        return 0
    else:
        print(f"\n❌ 월간 수집 실패: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

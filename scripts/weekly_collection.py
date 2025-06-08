#!/usr/bin/env python3
"""
TMDB 주간 데이터 수집 스크립트
장르별, 평점별 영화 데이터를 종합적으로 수집
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


class WeeklyCollector:
    """주간 데이터 수집기"""
    
    # 주요 장르 정의
    MAJOR_GENRES = {
        28: "액션",
        35: "코미디", 
        18: "드라마",
        27: "공포",
        10749: "로맨스",
        878: "SF",
        53: "스릴러",
        16: "애니메이션",
        80: "범죄",
        14: "판타지"
    }
    
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
                logging.FileHandler(log_dir / 'weekly_collection.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('weekly_collector')
    
    def collect_genre_movies(self, genre_id, genre_name, max_pages=15):
        """장르별 영화 수집"""
        self.logger.info(f"{genre_name} 장르 영화 수집 시작 (최대 {max_pages}페이지)")
        
        connector = TMDBAPIConnector()
        movies = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.debug(f"{genre_name} 페이지 {page} 수집 중...")
                
                response = connector.get_movies_by_genre(genre_id, page)
                if response and 'results' in response:
                    page_movies = response['results']
                    movies.extend(page_movies)
                    self.logger.debug(f"{genre_name} 페이지 {page}: {len(page_movies)}개 영화")
                    
                    # API 제한 준수
                    time.sleep(0.25)
                else:
                    self.logger.warning(f"{genre_name} 페이지 {page} 수집 실패")
                    break
            
            # 중복 제거
            unique_movies = self.remove_duplicates(movies)
            self.logger.info(f"{genre_name} 장르 수집 완료: {len(unique_movies)}개 영화")
            
            return unique_movies
            
        except Exception as e:
            self.logger.error(f"{genre_name} 장르 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def collect_top_rated_movies(self, min_rating=7.5, max_pages=20):
        """평점 높은 영화 수집"""
        self.logger.info(f"평점 높은 영화 수집 시작 (평점 {min_rating}+ 이상, 최대 {max_pages}페이지)")
        
        connector = TMDBAPIConnector()
        movies = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.debug(f"평점 높은 영화 페이지 {page} 수집 중...")
                
                response = connector.get_top_rated_movies(page)
                if response and 'results' in response:
                    # 최소 평점 이상만 필터링
                    high_rated = [
                        movie for movie in response['results'] 
                        if movie.get('vote_average', 0) >= min_rating
                    ]
                    movies.extend(high_rated)
                    self.logger.debug(f"평점 높은 영화 페이지 {page}: {len(high_rated)}개 영화")
                    
                    time.sleep(0.25)
                else:
                    self.logger.warning(f"평점 높은 영화 페이지 {page} 수집 실패")
                    break
            
            unique_movies = self.remove_duplicates(movies)
            self.logger.info(f"평점 높은 영화 수집 완료: {len(unique_movies)}개 영화")
            
            return unique_movies
            
        except Exception as e:
            self.logger.error(f"평점 높은 영화 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def collect_weekly_trending(self):
        """주간 트렌딩 영화 수집"""
        self.logger.info("주간 트렌딩 영화 수집 시작")
        
        connector = TMDBAPIConnector()
        
        try:
            response = connector.get_trending_movies('week')
            if response and 'results' in response:
                movies = response['results']
                self.logger.info(f"주간 트렌딩 영화 수집 완료: {len(movies)}개")
                return movies
            else:
                self.logger.warning("주간 트렌딩 영화 수집 실패")
                return []
                
        except Exception as e:
            self.logger.error(f"주간 트렌딩 영화 수집 중 오류: {e}")
            raise
        finally:
            connector.close()
    
    def collect_discover_movies(self, filters, max_pages=10, description=""):
        """조건별 영화 발견 수집"""
        self.logger.info(f"조건별 영화 수집 시작{f' ({description})' if description else ''}")
        
        connector = TMDBAPIConnector()
        movies = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.debug(f"조건별 영화 페이지 {page} 수집 중...")
                
                response = connector.discover_movies(page=page, **filters)
                if response and 'results' in response:
                    page_movies = response['results']
                    movies.extend(page_movies)
                    self.logger.debug(f"조건별 영화 페이지 {page}: {len(page_movies)}개 영화")
                    
                    time.sleep(0.25)
                else:
                    self.logger.warning(f"조건별 영화 페이지 {page} 수집 실패")
                    break
            
            unique_movies = self.remove_duplicates(movies)
            self.logger.info(f"조건별 영화 수집 완료: {len(unique_movies)}개 영화")
            
            return unique_movies
            
        except Exception as e:
            self.logger.error(f"조건별 영화 수집 중 오류: {e}")
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
    
    def validate_and_filter_data(self, movies, collection_type=""):
        """데이터 검증 및 필터링"""
        if not movies:
            return [], None
            
        self.logger.info(f"데이터 검증 시작{f' ({collection_type})' if collection_type else ''}")
        
        validator = DataQualityValidator()
        
        try:
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
    
    def save_collection_data(self, movies, collection_type, metadata=None):
        """수집 데이터 저장"""
        if not movies:
            self.logger.warning(f"저장할 데이터가 없습니다: {collection_type}")
            return None
            
        # 저장 디렉토리 생성
        save_dir = self.output_dir / 'weekly'
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        week_number = datetime.now().isocalendar()[1]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{collection_type}_W{week_number:02d}_{timestamp}.json"
        filepath = save_dir / filename
        
        # 저장할 데이터 구성
        data_to_save = {
            'movies': movies,
            'collection_info': metadata or {},
            'save_timestamp': datetime.now().isoformat(),
            'week_number': week_number,
            'total_count': len(movies)
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"데이터 저장 중 오류: {e}")
            raise
    
    def consolidate_weekly_data(self, collection_results):
        """주간 수집 데이터 통합"""
        self.logger.info("주간 데이터 통합 시작")
        
        all_movies = []
        consolidation_stats = {
            'total_collections': len(collection_results),
            'by_type': {},
            'total_unique_movies': 0,
            'consolidation_time': datetime.now().isoformat()
        }
        
        # 모든 수집 결과 통합
        for collection_type, data in collection_results.items():
            movies = data.get('movies', [])
            count = len(movies)
            
            all_movies.extend(movies)
            consolidation_stats['by_type'][collection_type] = count
            
            self.logger.debug(f"{collection_type}: {count}개 영화 통합")
        
        # 전체 중복 제거
        unique_movies = self.remove_duplicates(all_movies)
        consolidation_stats['total_unique_movies'] = len(unique_movies)
        
        removed_duplicates = len(all_movies) - len(unique_movies)
        if removed_duplicates > 0:
            self.logger.info(f"전체 중복 제거: {removed_duplicates}개 영화 제거")
        
        # 통합 데이터 저장
        consolidated_dir = project_root / 'data' / 'processed' / 'weekly'
        consolidated_dir.mkdir(parents=True, exist_ok=True)
        
        week_number = datetime.now().isocalendar()[1]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        consolidated_file = consolidated_dir / f"consolidated_week_{week_number:02d}_{timestamp}.json"
        
        consolidated_data = {
            'movies': unique_movies,
            'consolidation_info': consolidation_stats,
            'source_collections': list(collection_results.keys()),
            'generation_time': datetime.now().isoformat()
        }
        
        try:
            with open(consolidated_file, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"통합 데이터 저장: {consolidated_file}")
            self.logger.info(f"최종 고유 영화 수: {len(unique_movies)}")
            
            return consolidated_file, consolidation_stats
            
        except Exception as e:
            self.logger.error(f"통합 데이터 저장 중 오류: {e}")
            raise
    
    def generate_weekly_report(self, collection_results, consolidation_stats):
        """주간 수집 리포트 생성"""
        report_dir = project_root / 'data' / 'raw' / 'metadata' / 'weekly_reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        week_number = datetime.now().isocalendar()[1]
        year = datetime.now().year
        report_file = report_dir / f"weekly_report_{year}_W{week_number:02d}.json"
        
        # 수집 통계 계산
        total_collected = sum(
            result.get('metadata', {}).get('total_collected', 0) 
            for result in collection_results.values()
        )
        total_valid = sum(
            result.get('metadata', {}).get('total_valid', 0) 
            for result in collection_results.values()
        )
        
        # 장르 분포 분석
        all_movies = []
        for result in collection_results.values():
            all_movies.extend(result.get('movies', []))
        
        genre_distribution = self.analyze_genre_distribution(all_movies)
        rating_distribution = self.analyze_rating_distribution(all_movies)
        
        # 리포트 생성
        report = {
            'report_type': 'weekly',
            'week_number': week_number,
            'year': year,
            'generation_time': datetime.now().isoformat(),
            'collection_summary': {
                'total_collected': total_collected,
                'total_valid': total_valid,
                'validity_rate': (total_valid / total_collected * 100) if total_collected > 0 else 0,
                'unique_movies': consolidation_stats.get('total_unique_movies', 0),
                'by_collection_type': {
                    ctype: result.get('metadata', {})
                    for ctype, result in collection_results.items()
                }
            },
            'data_analysis': {
                'genre_distribution': genre_distribution,
                'rating_distribution': rating_distribution,
                'top_rated_movies': self.get_top_movies(all_movies, 'vote_average', 10),
                'most_popular_movies': self.get_top_movies(all_movies, 'popularity', 10)
            },
            'file_locations': {
                ctype: str(result.get('file_path', ''))
                for ctype, result in collection_results.items()
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"주간 리포트 생성: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"리포트 생성 중 오류: {e}")
            return None
    
    def analyze_genre_distribution(self, movies):
        """장르 분포 분석"""
        genre_counts = {}
        
        for movie in movies:
            genres = movie.get('genre_ids', [])
            for genre_id in genres:
                genre_name = self.MAJOR_GENRES.get(genre_id, f"Genre_{genre_id}")
                genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1
        
        return dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_rating_distribution(self, movies):
        """평점 분포 분석"""
        rating_ranges = {
            '9.0-10.0': 0, '8.0-8.9': 0, '7.0-7.9': 0,
            '6.0-6.9': 0, '5.0-5.9': 0, '0.0-4.9': 0
        }
        
        for movie in movies:
            rating = movie.get('vote_average', 0)
            if rating >= 9.0:
                rating_ranges['9.0-10.0'] += 1
            elif rating >= 8.0:
                rating_ranges['8.0-8.9'] += 1
            elif rating >= 7.0:
                rating_ranges['7.0-7.9'] += 1
            elif rating >= 6.0:
                rating_ranges['6.0-6.9'] += 1
            elif rating >= 5.0:
                rating_ranges['5.0-5.9'] += 1
            else:
                rating_ranges['0.0-4.9'] += 1
        
        return rating_ranges
    
    def get_top_movies(self, movies, sort_key, limit=10):
        """상위 영화 목록 반환"""
        if not movies:
            return []
            
        sorted_movies = sorted(
            movies, 
            key=lambda x: x.get(sort_key, 0), 
            reverse=True
        )
        
        return [
            {
                'id': movie.get('id'),
                'title': movie.get('title'),
                'vote_average': movie.get('vote_average'),
                'popularity': movie.get('popularity'),
                'release_date': movie.get('release_date')
            }
            for movie in sorted_movies[:limit]
        ]
    
    def run_weekly_collection(self, genre_pages=15, top_rated_pages=20, 
                            min_rating=7.5, include_trending=True, 
                            include_recent_releases=True):
        """주간 수집 실행"""
        self.logger.info("=== TMDB 주간 데이터 수집 시작 ===")
        start_time = datetime.now()
        
        collection_results = {}
        
        try:
            # 1. 장르별 영화 수집
            self.logger.info("--- 장르별 영화 수집 시작 ---")
            for genre_id, genre_name in self.MAJOR_GENRES.items():
                try:
                    genre_movies = self.collect_genre_movies(genre_id, genre_name, genre_pages)
                    valid_movies, validation_results = self.validate_and_filter_data(
                        genre_movies, f"{genre_name} 장르"
                    )
                    
                    metadata = {
                        'collection_type': 'genre',
                        'genre_id': genre_id,
                        'genre_name': genre_name,
                        'pages_collected': genre_pages,
                        'total_collected': len(genre_movies),
                        'total_valid': len(valid_movies),
                        'validation_results': validation_results
                    }
                    
                    if valid_movies:
                        file_path = self.save_collection_data(valid_movies, f"genre_{genre_name.lower()}", metadata)
                        collection_results[f"genre_{genre_name.lower()}"] = {
                            'movies': valid_movies,
                            'metadata': metadata,
                            'file_path': file_path
                        }
                    
                    # 장르 간 적절한 대기 시간
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"{genre_name} 장르 수집 실패: {e}")
                    continue
            
            # 2. 평점 높은 영화 수집
            self.logger.info("--- 평점 높은 영화 수집 시작 ---")
            try:
                top_rated_movies = self.collect_top_rated_movies(min_rating, top_rated_pages)
                valid_top_rated, top_rated_validation = self.validate_and_filter_data(
                    top_rated_movies, "평점 높은 영화"
                )
                
                top_rated_metadata = {
                    'collection_type': 'top_rated',
                    'min_rating': min_rating,
                    'pages_collected': top_rated_pages,
                    'total_collected': len(top_rated_movies),
                    'total_valid': len(valid_top_rated),
                    'validation_results': top_rated_validation
                }
                
                if valid_top_rated:
                    file_path = self.save_collection_data(valid_top_rated, "top_rated", top_rated_metadata)
                    collection_results['top_rated'] = {
                        'movies': valid_top_rated,
                        'metadata': top_rated_metadata,
                        'file_path': file_path
                    }
                    
            except Exception as e:
                self.logger.error(f"평점 높은 영화 수집 실패: {e}")
            
            # 3. 주간 트렌딩 영화 수집 (선택적)
            if include_trending:
                self.logger.info("--- 주간 트렌딩 영화 수집 시작 ---")
                try:
                    trending_movies = self.collect_weekly_trending()
                    valid_trending, trending_validation = self.validate_and_filter_data(
                        trending_movies, "주간 트렌딩"
                    )
                    
                    trending_metadata = {
                        'collection_type': 'weekly_trending',
                        'time_window': 'week',
                        'total_collected': len(trending_movies),
                        'total_valid': len(valid_trending),
                        'validation_results': trending_validation
                    }
                    
                    if valid_trending:
                        file_path = self.save_collection_data(valid_trending, "weekly_trending", trending_metadata)
                        collection_results['weekly_trending'] = {
                            'movies': valid_trending,
                            'metadata': trending_metadata,
                            'file_path': file_path
                        }
                        
                except Exception as e:
                    self.logger.error(f"주간 트렌딩 수집 실패: {e}")
            
            # 4. 최근 개봉 영화 수집 (선택적)
            if include_recent_releases:
                self.logger.info("--- 최근 개봉 영화 수집 시작 ---")
                try:
                    # 최근 3개월 개봉 영화
                    recent_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                    filters = {
                        'primary_release_date.gte': recent_date,
                        'sort_by': 'popularity.desc'
                    }
                    
                    recent_movies = self.collect_discover_movies(
                        filters, max_pages=10, description="최근 개봉 영화"
                    )
                    valid_recent, recent_validation = self.validate_and_filter_data(
                        recent_movies, "최근 개봉"
                    )
                    
                    recent_metadata = {
                        'collection_type': 'recent_releases',
                        'release_date_from': recent_date,
                        'pages_collected': 10,
                        'total_collected': len(recent_movies),
                        'total_valid': len(valid_recent),
                        'validation_results': recent_validation
                    }
                    
                    if valid_recent:
                        file_path = self.save_collection_data(valid_recent, "recent_releases", recent_metadata)
                        collection_results['recent_releases'] = {
                            'movies': valid_recent,
                            'metadata': recent_metadata,
                            'file_path': file_path
                        }
                        
                except Exception as e:
                    self.logger.error(f"최근 개봉 영화 수집 실패: {e}")
            
            # 5. 데이터 통합
            if collection_results:
                self.logger.info("--- 데이터 통합 시작 ---")
                consolidated_file, consolidation_stats = self.consolidate_weekly_data(collection_results)
                
                # 6. 주간 리포트 생성
                self.logger.info("--- 주간 리포트 생성 시작 ---")
                report_file = self.generate_weekly_report(collection_results, consolidation_stats)
            else:
                self.logger.warning("수집된 데이터가 없어 통합 및 리포트 생성을 건너뜁니다.")
                consolidated_file = None
                report_file = None
            
            # 7. 최종 요약
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            total_collections = len(collection_results)
            total_movies = sum(len(r['movies']) for r in collection_results.values())
            
            self.logger.info("=== 주간 수집 완료 ===")
            self.logger.info(f"실행 시간: {duration/60:.1f}분")
            self.logger.info(f"수집 유형: {total_collections}개")
            self.logger.info(f"총 영화: {total_movies}개")
            if consolidation_stats:
                self.logger.info(f"고유 영화: {consolidation_stats.get('total_unique_movies', 0)}개")
            
            return {
                'success': True,
                'duration': duration,
                'collection_count': total_collections,
                'total_movies': total_movies,
                'unique_movies': consolidation_stats.get('total_unique_movies', 0) if consolidation_stats else 0,
                'consolidated_file': str(consolidated_file) if consolidated_file else None,
                'report_file': str(report_file) if report_file else None,
                'collection_results': collection_results
            }
            
        except Exception as e:
            self.logger.error(f"주간 수집 중 치명적 오류: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='TMDB 주간 데이터 수집')
    parser.add_argument('--genre-pages', type=int, default=15,
                       help='장르별 수집 페이지 수 (기본: 15)')
    parser.add_argument('--top-rated-pages', type=int, default=20,
                       help='평점 높은 영화 수집 페이지 수 (기본: 20)')
    parser.add_argument('--min-rating', type=float, default=7.5,
                       help='최소 평점 기준 (기본: 7.5)')
    parser.add_argument('--no-trending', action='store_true',
                       help='주간 트렌딩 수집 제외')
    parser.add_argument('--no-recent', action='store_true',
                       help='최근 개봉 영화 수집 제외')
    parser.add_argument('--output-dir', help='출력 디렉토리')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='로그 레벨')
    parser.add_argument('--dry-run', action='store_true',
                       help='실제 수집 없이 테스트만 실행')
    
    args = parser.parse_args()
    
    # 주간 수집기 생성
    collector = WeeklyCollector(
        output_dir=args.output_dir,
        log_level=args.log_level
    )
    
    if args.dry_run:
        collector.logger.info("DRY RUN 모드: 실제 수집 없이 테스트 실행")
        return 0
    
    # 주간 수집 실행
    result = collector.run_weekly_collection(
        genre_pages=args.genre_pages,
        top_rated_pages=args.top_rated_pages,
        min_rating=args.min_rating,
        include_trending=not args.no_trending,
        include_recent_releases=not args.no_recent
    )
    
    if result['success']:
        print(f"\n✅ 주간 수집 성공!")
        print(f"실행 시간: {result['duration']/60:.1f}분")
        print(f"수집 유형: {result['collection_count']}개")
        print(f"총 영화: {result['total_movies']}개")
        print(f"고유 영화: {result['unique_movies']}개")
        if result.get('report_file'):
            print(f"리포트: {result['report_file']}")
        return 0
    else:
        print(f"\n❌ 주간 수집 실패: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

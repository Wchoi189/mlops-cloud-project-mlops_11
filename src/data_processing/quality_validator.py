# src/data_processing/quality_validator.py
"""
데이터 품질 검증 시스템
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

class DataQualityValidator:
    """데이터 품질 검증 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._setup_validation_rules()
        self.quality_stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'error_details': {}
        }
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """검증 규칙 설정"""
        return {
            'required_fields': [
                'id', 'title', 'release_date', 
                'vote_average', 'popularity', 'overview'
            ],
            'field_types': {
                'id': int,
                'title': str,
                'vote_average': (int, float),
                'popularity': (int, float),
                'adult': bool
            },
            'field_ranges': {
                'vote_average': (0, 10),
                'popularity': (0, float('inf')),
                'vote_count': (0, float('inf'))
            },
            'field_patterns': {
                'release_date': r'^\d{4}-\d{2}-\d{2}$',
                'imdb_id': r'^tt\d+$'
            }
        }
    
    def validate_single_movie(self, movie: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """단일 영화 데이터 검증"""
        self.quality_stats['total_validated'] += 1
        validation_result = {
            'movie_id': movie.get('id', 'unknown'),
            'checks': {},
            'overall_score': 0,
            'issues': []
        }
        
        try:
            # 필수 필드 존재 확인
            required_check = self._check_required_fields(movie)
            validation_result['checks']['required_fields'] = required_check
            
            # 데이터 타입 검증
            type_check = self._check_field_types(movie)
            validation_result['checks']['field_types'] = type_check
            
            # 값 범위 검증
            range_check = self._check_field_ranges(movie)
            validation_result['checks']['field_ranges'] = range_check
            
            # 패턴 검증
            pattern_check = self._check_field_patterns(movie)
            validation_result['checks']['field_patterns'] = pattern_check
            
            # 비즈니스 로직 검증
            business_check = self._check_business_logic(movie)
            validation_result['checks']['business_logic'] = business_check
            
            # 전체 점수 계산
            validation_result['overall_score'] = self._calculate_quality_score(validation_result['checks'])
            
            # 이슈 수집
            for check_name, check_result in validation_result['checks'].items():
                if not check_result.get('passed', False):
                    for error_key in ['missing_fields', 'type_errors', 'range_errors', 'pattern_errors', 'business_errors']:
                        if error_key in check_result and check_result[error_key]:
                            validation_result['issues'].extend(check_result[error_key])
            
            # 통과/실패 판정 (70점 이상 통과)
            is_valid = validation_result['overall_score'] >= 70
            
            if is_valid:
                self.quality_stats['passed'] += 1
                return True, "Valid", validation_result
            else:
                self.quality_stats['failed'] += 1
                return False, f"Quality score too low: {validation_result['overall_score']}", validation_result
                
        except Exception as e:
            self.quality_stats['failed'] += 1
            self.logger.error(f"Validation error for movie {movie.get('id', 'unknown')}: {e}")
            return False, f"Validation error: {str(e)}", validation_result
    
    def _check_required_fields(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """필수 필드 존재 확인"""
        missing_fields = []
        for field in self.validation_rules['required_fields']:
            if field not in movie or movie[field] is None or movie[field] == '':
                missing_fields.append(field)
        
        return {
            'passed': len(missing_fields) == 0,
            'score': max(0, 100 - len(missing_fields) * 20),
            'missing_fields': missing_fields
        }
    
    def _check_field_types(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 타입 검증"""
        type_errors = []
        for field, expected_type in self.validation_rules['field_types'].items():
            if field in movie and movie[field] is not None:
                if not isinstance(movie[field], expected_type):
                    type_errors.append(f"{field}: expected {expected_type}, got {type(movie[field])}")
        
        return {
            'passed': len(type_errors) == 0,
            'score': max(0, 100 - len(type_errors) * 25),
            'type_errors': type_errors
        }
    
    def _check_field_ranges(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """값 범위 검증"""
        range_errors = []
        for field, (min_val, max_val) in self.validation_rules['field_ranges'].items():
            if field in movie and movie[field] is not None:
                value = movie[field]
                if not (min_val <= value <= max_val):
                    range_errors.append(f"{field}: {value} not in range [{min_val}, {max_val}]")
        
        return {
            'passed': len(range_errors) == 0,
            'score': max(0, 100 - len(range_errors) * 20),
            'range_errors': range_errors
        }
    
    def _check_field_patterns(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """패턴 검증"""
        pattern_errors = []
        for field, pattern in self.validation_rules['field_patterns'].items():
            if field in movie and movie[field] is not None:
                if not re.match(pattern, str(movie[field])):
                    pattern_errors.append(f"{field}: {movie[field]} doesn't match pattern {pattern}")
        
        return {
            'passed': len(pattern_errors) == 0,
            'score': max(0, 100 - len(pattern_errors) * 15),
            'pattern_errors': pattern_errors
        }
    
    def _check_business_logic(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 로직 검증"""
        business_errors = []
        
        # 성인 영화 필터링
        if movie.get('adult', False):
            business_errors.append("Adult content not allowed")
        
        # 개봉 전 영화 제외
        release_date = movie.get('release_date')
        if release_date:
            try:
                release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                if release_dt > datetime.now():
                    business_errors.append("Unreleased movie")
            except ValueError:
                business_errors.append("Invalid release date format")
        
        # 평점 0인 영화 제외
        if movie.get('vote_average', 0) == 0:
            business_errors.append("Zero rating")
        
        # 투표 수 너무 적은 영화 제외
        if movie.get('vote_count', 0) < 10:
            business_errors.append("Insufficient votes")
        
        return {
            'passed': len(business_errors) == 0,
            'score': max(0, 100 - len(business_errors) * 25),
            'business_errors': business_errors
        }
    
    def _calculate_quality_score(self, checks: Dict[str, Any]) -> float:
        """전체 품질 점수 계산"""
        total_score = 0
        weights = {
            'required_fields': 0.3,
            'field_types': 0.25,
            'field_ranges': 0.2,
            'field_patterns': 0.1,
            'business_logic': 0.15
        }
        
        for check_name, weight in weights.items():
            if check_name in checks:
                total_score += checks[check_name]['score'] * weight
        
        return round(total_score, 2)
    
    def validate_batch_data(self, movies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """배치 데이터 품질 분석"""
        batch_results = {
            'total_movies': len(movies),
            'valid_movies': 0,
            'invalid_movies': 0,
            'quality_distribution': {},
            'common_issues': {},
            'recommendations': []
        }
        
        valid_movies = []
        invalid_movies = []
        quality_scores = []
        all_issues = []
        
        for movie in movies:
            is_valid, message, details = self.validate_single_movie(movie)
            quality_scores.append(details['overall_score'])
            
            if is_valid:
                valid_movies.append(movie)
                batch_results['valid_movies'] += 1
            else:
                invalid_movies.append(movie)
                batch_results['invalid_movies'] += 1
                all_issues.extend(details['issues'])
        
        # 품질 분포 분석
        batch_results['quality_distribution'] = {
            'excellent': len([s for s in quality_scores if s >= 90]),
            'good': len([s for s in quality_scores if 80 <= s < 90]),
            'fair': len([s for s in quality_scores if 70 <= s < 80]),
            'poor': len([s for s in quality_scores if s < 70])
        }
        
        # 공통 이슈 분석
        issue_counts = Counter(all_issues)
        batch_results['common_issues'] = dict(issue_counts.most_common(10))
        
        # 개선 권장사항
        batch_results['recommendations'] = self._generate_recommendations(batch_results)
        
        return batch_results
    
    def _generate_recommendations(self, batch_results: Dict[str, Any]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        total = batch_results['total_movies']
        invalid_rate = batch_results['invalid_movies'] / total * 100
        
        if invalid_rate > 10:
            recommendations.append(f"데이터 품질 불량률이 {invalid_rate:.1f}%로 높습니다. 수집 로직 점검 필요")
        
        common_issues = batch_results['common_issues']
        if 'Zero rating' in common_issues:
            recommendations.append("평점 0인 영화가 많습니다. 필터링 강화 필요")
        
        if 'Insufficient votes' in common_issues:
            recommendations.append("투표 수 부족 영화가 많습니다. 최소 투표 수 기준 상향 검토")
        
        if 'Adult content not allowed' in common_issues:
            recommendations.append("성인 영화가 포함되어 있습니다. 수집 시 필터링 강화 필요")
        
        if not recommendations:
            recommendations.append("데이터 품질이 양호합니다.")
        
        return recommendations
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """검증 통계 반환"""
        return self.quality_stats.copy()
    
    def reset_stats(self):
        """통계 초기화"""
        self.quality_stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'error_details': {}
        }

class AnomalyDetector:
    """통계적 이상 탐지 클래스"""
    
    def __init__(self):
        self.baseline_stats = {}
        self.alert_thresholds = {
            'rating_mean_change': 0.5,
            'popularity_variance_change': 2.0,
            'collection_volume_change': 0.3
        }
        self.logger = logging.getLogger(__name__)
    
    def detect_rating_anomalies(self, movies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """평점 분포 이상 탐지"""
        ratings = [m.get('vote_average', 0) for m in movies if m.get('vote_average')]
        
        if not ratings:
            return {'status': 'no_data', 'anomalies': []}
        
        current_stats = {
            'mean': np.mean(ratings),
            'std': np.std(ratings),
            'median': np.median(ratings),
            'q1': np.percentile(ratings, 25),
            'q3': np.percentile(ratings, 75)
        }
        
        anomalies = []
        
        # 기준 통계와 비교
        if 'ratings' in self.baseline_stats:
            baseline = self.baseline_stats['ratings']
            
            # 평균 변화 확인
            mean_change = abs(current_stats['mean'] - baseline['mean'])
            if mean_change > self.alert_thresholds['rating_mean_change']:
                anomalies.append({
                    'type': 'rating_mean_shift',
                    'current': current_stats['mean'],
                    'baseline': baseline['mean'],
                    'change': mean_change
                })
        
        # 극값 탐지
        iqr = current_stats['q3'] - current_stats['q1']
        lower_bound = current_stats['q1'] - 1.5 * iqr
        upper_bound = current_stats['q3'] + 1.5 * iqr
        
        outliers = [r for r in ratings if r < lower_bound or r > upper_bound]
        if len(outliers) > len(ratings) * 0.1:  # 10% 이상이 극값
            anomalies.append({
                'type': 'excessive_outliers',
                'outlier_count': len(outliers),
                'outlier_rate': len(outliers) / len(ratings),
                'outliers': outliers[:10]  # 처음 10개만 저장
            })
        
        return {
            'status': 'analyzed',
            'current_stats': current_stats,
            'anomalies': anomalies
        }
    
    def detect_collection_anomalies(self, collection_stats: Dict[str, Any]) -> Dict[str, Any]:
        """수집량 이상 탐지"""
        anomalies = []
        
        current_count = collection_stats.get('total_collected', 0)
        
        if 'collection' in self.baseline_stats:
            baseline_count = self.baseline_stats['collection']['average_count']
            change_rate = abs(current_count - baseline_count) / baseline_count if baseline_count > 0 else 0
            
            if change_rate > self.alert_thresholds['collection_volume_change']:
                anomalies.append({
                    'type': 'collection_volume_change',
                    'current': current_count,
                    'baseline': baseline_count,
                    'change_rate': change_rate
                })
        
        return {
            'status': 'analyzed',
            'anomalies': anomalies
        }
    
    def detect_popularity_anomalies(self, movies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """인기도 이상 탐지"""
        popularity_scores = [m.get('popularity', 0) for m in movies if m.get('popularity')]
        
        if not popularity_scores:
            return {'status': 'no_data', 'anomalies': []}
        
        current_stats = {
            'mean': np.mean(popularity_scores),
            'std': np.std(popularity_scores),
            'max': max(popularity_scores),
            'min': min(popularity_scores)
        }
        
        anomalies = []
        
        # 인기도 급등/급락 감지
        if 'popularity' in self.baseline_stats:
            baseline = self.baseline_stats['popularity']
            
            # 분산 변화 확인
            variance_change = abs(current_stats['std'] - baseline['std']) / baseline['std'] if baseline['std'] > 0 else 0
            if variance_change > self.alert_thresholds['popularity_variance_change']:
                anomalies.append({
                    'type': 'popularity_variance_change',
                    'current_std': current_stats['std'],
                    'baseline_std': baseline['std'],
                    'variance_change': variance_change
                })
        
        return {
            'status': 'analyzed',
            'current_stats': current_stats,
            'anomalies': anomalies
        }
    
    def update_baseline(self, movies: List[Dict[str, Any]], collection_stats: Dict[str, Any]):
        """기준선 업데이트"""
        # 평점 통계 업데이트
        ratings = [m.get('vote_average', 0) for m in movies if m.get('vote_average')]
        if ratings:
            self.baseline_stats['ratings'] = {
                'mean': np.mean(ratings),
                'std': np.std(ratings),
                'median': np.median(ratings)
            }
        
        # 인기도 통계 업데이트
        popularity_scores = [m.get('popularity', 0) for m in movies if m.get('popularity')]
        if popularity_scores:
            self.baseline_stats['popularity'] = {
                'mean': np.mean(popularity_scores),
                'std': np.std(popularity_scores)
            }
        
        # 수집량 통계 업데이트
        if 'collection' not in self.baseline_stats:
            self.baseline_stats['collection'] = {'average_count': collection_stats.get('total_collected', 0)}
        else:
            # 지수 이동 평균 적용
            alpha = 0.1
            current_avg = self.baseline_stats['collection']['average_count']
            new_count = collection_stats.get('total_collected', 0)
            self.baseline_stats['collection']['average_count'] = alpha * new_count + (1 - alpha) * current_avg
    
    def get_baseline_stats(self) -> Dict[str, Any]:
        """기준선 통계 반환"""
        return self.baseline_stats.copy()
    
    def save_baseline(self, filepath: str):
        """기준선 저장"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.baseline_stats, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"기준선 저장 완료: {filepath}")
        except Exception as e:
            self.logger.error(f"기준선 저장 실패: {e}")
    
    def load_baseline(self, filepath: str):
        """기준선 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.baseline_stats = json.load(f)
            self.logger.info(f"기준선 로드 완료: {filepath}")
        except Exception as e:
            self.logger.error(f"기준선 로드 실패: {e}")

class DataCleaner:
    """자동 데이터 정제 클래스"""
    
    def __init__(self):
        self.cleaning_stats = {
            'processed': 0,
            'cleaned': 0,
            'removed': 0,
            'actions': []
        }
        self.logger = logging.getLogger(__name__)
    
    def clean_movie_data(self, movie: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """개별 영화 데이터 정제"""
        self.cleaning_stats['processed'] += 1
        original_movie = movie.copy()
        actions = []
        
        # 1. 빈 문자열을 None으로 변환
        for key, value in movie.items():
            if value == "":
                movie[key] = None
                actions.append(f"empty_to_none_{key}")
        
        # 2. 제목 정제
        if movie.get('title'):
            cleaned_title = self._clean_title(movie['title'])
            if cleaned_title != movie['title']:
                movie['title'] = cleaned_title
                actions.append("title_cleaned")
        
        # 3. 개요 정제
        if movie.get('overview'):
            cleaned_overview = self._clean_overview(movie['overview'])
            if cleaned_overview != movie['overview']:
                movie['overview'] = cleaned_overview
                actions.append("overview_cleaned")
        
        # 4. 장르 정규화
        if movie.get('genre_ids'):
            movie['genre_ids'] = self._normalize_genres(movie['genre_ids'])
            actions.append("genres_normalized")
        
        # 5. 날짜 형식 표준화
        if movie.get('release_date'):
            standardized_date = self._standardize_date(movie['release_date'])
            if standardized_date != movie['release_date']:
                movie['release_date'] = standardized_date
                actions.append("date_standardized")
        
        if actions:
            self.cleaning_stats['cleaned'] += 1
            self.cleaning_stats['actions'].extend(actions)
        
        return movie, '; '.join(actions) if actions else 'no_cleaning_needed'
    
    def _clean_title(self, title: str) -> str:
        """제목 정제"""
        # 불필요한 공백 제거
        title = re.sub(r'\s+', ' ', title.strip())
        # 특수 문자 정제 (기본적인 문장 부호는 유지)
        title = re.sub(r'[^\w\s\-\.\,\!\?\:\(\)\'\"&]', '', title)
        return title
    
    def _clean_overview(self, overview: str) -> str:
        """개요 정제"""
        # HTML 태그 제거
        overview = re.sub(r'<[^>]+>', '', overview)
        # 불필요한 공백 제거
        overview = re.sub(r'\s+', ' ', overview.strip())
        return overview
    
    def _normalize_genres(self, genre_ids) -> List[int]:
        """장르 정규화"""
        if not isinstance(genre_ids, list):
            return []
        
        normalized = []
        for g in genre_ids:
            if isinstance(g, (int, str)) and str(g).isdigit():
                normalized.append(int(g))
        
        return normalized
    
    def _standardize_date(self, date_str: str) -> str:
        """날짜 형식 표준화"""
        # 이미 YYYY-MM-DD 형식인지 확인
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # 다양한 날짜 형식 처리
        date_patterns = [
            '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d',
            '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y'
        ]
        
        for pattern in date_patterns:
            try:
                dt = datetime.strptime(date_str, pattern)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # 변환 실패 시 원본 반환
    
    def apply_batch_cleaning(self, movies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """배치 데이터 정제"""
        cleaned_movies = []
        cleaning_report = {
            'total_processed': len(movies),
            'successfully_cleaned': 0,
            'removed_count': 0,
            'cleaning_actions': {},
            'removed_reasons': {}
        }
        
        validator = DataQualityValidator()
        
        for movie in movies:
            try:
                cleaned_movie, actions = self.clean_movie_data(movie)
                
                # 정제 후 재검증
                is_valid, reason, details = validator.validate_single_movie(cleaned_movie)
                
                if is_valid:
                    cleaned_movies.append(cleaned_movie)
                    cleaning_report['successfully_cleaned'] += 1
                    
                    # 정제 액션 통계
                    if actions != 'no_cleaning_needed':
                        for action in actions.split('; '):
                            cleaning_report['cleaning_actions'][action] = cleaning_report['cleaning_actions'].get(action, 0) + 1
                else:
                    # 정제 후에도 유효하지 않으면 제거
                    cleaning_report['removed_count'] += 1
                    cleaning_report['removed_reasons'][reason] = cleaning_report['removed_reasons'].get(reason, 0) + 1
                    
            except Exception as e:
                cleaning_report['removed_count'] += 1
                error_reason = f'cleaning_error: {str(e)}'
                cleaning_report['removed_reasons'][error_reason] = cleaning_report['removed_reasons'].get(error_reason, 0) + 1
        
        return cleaned_movies, cleaning_report
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """정제 통계 반환"""
        return self.cleaning_stats.copy()
    
    def reset_stats(self):
        """통계 초기화"""
        self.cleaning_stats = {
            'processed': 0,
            'cleaned': 0,
            'removed': 0,
            'actions': []
        }

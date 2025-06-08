"""
자동 데이터 정제 시스템
품질 검증에서 발견된 문제를 자동으로 정제하고 수정
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import logging
from collections import Counter
import pandas as pd

class DataCleaner:
    """자동 데이터 정제 클래스"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # 정제 규칙 정의
        self.cleaning_rules = self._define_cleaning_rules()
        
        # 정제 통계
        self.cleaning_stats = {
            'processed_files': 0,
            'processed_records': 0,
            'cleaned_records': 0,
            'removed_records': 0,
            'applied_rules': Counter(),
            'error_records': []
        }
        
        # 정제 결과 저장 디렉토리
        self.cleaned_dir = self.data_dir / 'processed' / 'cleaned'
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    def _define_cleaning_rules(self) -> Dict[str, Any]:
        """데이터 정제 규칙 정의"""
        return {
            'text_cleaning': {
                'trim_whitespace': True,
                'normalize_unicode': True,
                'remove_html_tags': True,
                'fix_encoding_issues': True,
                'standardize_quotes': True
            },
            'field_standardization': {
                'standardize_dates': True,
                'normalize_ratings': True,
                'clean_genres': True,
                'format_ids': True,
                'standardize_language_codes': True
            },
            'data_validation': {
                'remove_duplicates': True,
                'filter_adult_content': True,
                'validate_date_ranges': True,
                'check_required_fields': True,
                'validate_data_types': True
            },
            'quality_enhancement': {
                'fill_missing_values': True,
                'correct_obvious_errors': True,
                'standardize_naming': True,
                'normalize_scores': True
            }
        }
    
    def clean_text_field(self, text: str, field_name: str = 'text') -> Tuple[str, List[str]]:
        """텍스트 필드 정제"""
        if not isinstance(text, str):
            return str(text) if text is not None else '', []
        
        original_text = text
        applied_rules = []
        
        # 공백 정제
        if self.cleaning_rules['text_cleaning']['trim_whitespace']:
            text = re.sub(r'\s+', ' ', text.strip())
            if text != original_text:
                applied_rules.append('trim_whitespace')
        
        # HTML 태그 제거
        if self.cleaning_rules['text_cleaning']['remove_html_tags']:
            cleaned = re.sub(r'<[^>]+>', '', text)
            if cleaned != text:
                text = cleaned
                applied_rules.append('remove_html_tags')
        
        # 인코딩 문제 수정
        if self.cleaning_rules['text_cleaning']['fix_encoding_issues']:
            # 일반적인 인코딩 문제 패턴 수정
            encoding_fixes = [
                (r'â€™', "'"),  # 잘못된 아포스트로피
                (r'â€œ', '"'),  # 잘못된 여는 따옴표
                (r'â€\x9d', '"'),  # 잘못된 닫는 따옴표
                (r'Ã¡', 'á'),  # 잘못된 액센트
                (r'Ã©', 'é'),  # 잘못된 액센트
                (r'Ã­', 'í'),  # 잘못된 액센트
                (r'Ã³', 'ó'),  # 잘못된 액센트
                (r'Ãº', 'ú'),  # 잘못된 액센트
            ]
            
            for pattern, replacement in encoding_fixes:
                new_text = re.sub(pattern, replacement, text)
                if new_text != text:
                    text = new_text
                    applied_rules.append('fix_encoding_issues')
                    break
        
        # 따옴표 표준화
        if self.cleaning_rules['text_cleaning']['standardize_quotes']:
            # 다양한 따옴표를 표준 따옴표로 변환
            quote_fixes = [
                (r'[""„‚]', '"'),  # 다양한 큰따옴표를 표준으로
                (r'[''‛]', "'"),   # 다양한 작은따옴표를 표준으로
            ]
            
            for pattern, replacement in quote_fixes:
                new_text = re.sub(pattern, replacement, text)
                if new_text != text:
                    text = new_text
                    applied_rules.append('standardize_quotes')
        
        # 특수 문자 정리 (필드별 맞춤)
        if field_name in ['title', 'overview']:
            # 제목과 개요에서 불필요한 특수문자 제거
            text = re.sub(r'[^\w\s\-\.\,\!\?\:\;\(\)\[\]\'\"]+', '', text)
            if text != original_text:
                applied_rules.append('clean_special_chars')
        
        return text, applied_rules
    
    def standardize_date_field(self, date_str: str) -> Tuple[str, List[str]]:
        """날짜 필드 표준화"""
        if not date_str or pd.isna(date_str):
            return '', []
        
        date_str = str(date_str).strip()
        applied_rules = []
        
        # 이미 표준 형식인지 확인 (YYYY-MM-DD)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str, applied_rules
        
        # 다양한 날짜 형식 처리
        date_patterns = [
            (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', r'\1-\2-\3'),  # YYYY/M/D
            (r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', r'\1-\2-\3'),  # YYYY.M.D
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', r'\3-\1-\2'),  # M/D/YYYY
            (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', r'\3-\1-\2'),  # M-D-YYYY
            (r'^(\d{4})(\d{2})(\d{2})$', r'\1-\2-\3'),  # YYYYMMDD
        ]
        
        for pattern, replacement in date_patterns:
            if re.match(pattern, date_str):
                standardized = re.sub(pattern, replacement, date_str)
                
                # 월/일 형식 보정 (01, 02 형태로)
                parts = standardized.split('-')
                if len(parts) == 3:
                    year, month, day = parts
                    month = month.zfill(2)
                    day = day.zfill(2)
                    
                    # 날짜 유효성 검사
                    try:
                        datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')
                        applied_rules.append('standardize_date_format')
                        return f"{year}-{month}-{day}", applied_rules
                    except ValueError:
                        # 유효하지 않은 날짜
                        applied_rules.append('invalid_date_detected')
                        return '', applied_rules
        
        # 패턴에 맞지 않는 경우
        applied_rules.append('unrecognized_date_format')
        return '', applied_rules
    
    def normalize_rating_field(self, rating: Union[str, int, float]) -> Tuple[float, List[str]]:
        """평점 필드 정규화"""
        applied_rules = []
        
        if pd.isna(rating) or rating == '':
            return 0.0, ['missing_rating_set_to_zero']
        
        try:
            rating_value = float(rating)
            
            # 10점 척도로 정규화
            if rating_value > 10:
                if rating_value <= 100:
                    # 100점 척도를 10점 척도로 변환
                    rating_value = rating_value / 10
                    applied_rules.append('convert_100_to_10_scale')
                elif rating_value <= 5:
                    # 5점 척도를 10점 척도로 변환
                    rating_value = rating_value * 2
                    applied_rules.append('convert_5_to_10_scale')
                else:
                    # 비정상적으로 큰 값
                    rating_value = 0.0
                    applied_rules.append('invalid_rating_set_to_zero')
            
            # 범위 검증 (0-10)
            if rating_value < 0:
                rating_value = 0.0
                applied_rules.append('negative_rating_corrected')
            elif rating_value > 10:
                rating_value = 10.0
                applied_rules.append('excessive_rating_corrected')
            
            # 소수점 1자리로 반올림
            rating_value = round(rating_value, 1)
            
            return rating_value, applied_rules
            
        except (ValueError, TypeError):
            applied_rules.append('invalid_rating_type_set_to_zero')
            return 0.0, applied_rules
    
    def clean_genre_field(self, genres: Union[str, List, Dict]) -> Tuple[List[int], List[str]]:
        """장르 필드 정제"""
        applied_rules = []
        
        if not genres or pd.isna(genres):
            return [], ['empty_genres']
        
        # 다양한 형태의 장르 데이터 처리
        genre_ids = []
        
        if isinstance(genres, str):
            try:
                # JSON 문자열인 경우
                genres = json.loads(genres)
                applied_rules.append('parsed_json_genres')
            except json.JSONDecodeError:
                # 쉼표로 구분된 문자열인 경우
                genre_names = [g.strip() for g in genres.split(',')]
                genre_ids = self._convert_genre_names_to_ids(genre_names)
                applied_rules.append('converted_genre_names_to_ids')
                return genre_ids, applied_rules
        
        if isinstance(genres, list):
            for item in genres:
                if isinstance(item, dict):
                    # TMDB API 형태: [{"id": 28, "name": "Action"}, ...]
                    if 'id' in item:
                        try:
                            genre_ids.append(int(item['id']))
                        except (ValueError, TypeError):
                            continue
                elif isinstance(item, (int, str)):
                    # ID 리스트 또는 이름 리스트
                    try:
                        genre_ids.append(int(item))
                    except (ValueError, TypeError):
                        # 이름인 경우 ID로 변환
                        converted_ids = self._convert_genre_names_to_ids([str(item)])
                        genre_ids.extend(converted_ids)
                        applied_rules.append('converted_genre_name_to_id')
            
            applied_rules.append('processed_genre_list')
        
        # 중복 제거 및 정렬
        if genre_ids:
            unique_genres = sorted(list(set(genre_ids)))
            if len(unique_genres) != len(genre_ids):
                applied_rules.append('removed_duplicate_genres')
            genre_ids = unique_genres
        
        return genre_ids, applied_rules
    
    def _convert_genre_names_to_ids(self, genre_names: List[str]) -> List[int]:
        """장르 이름을 ID로 변환"""
        # TMDB 장르 매핑
        genre_mapping = {
            'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Fantasy': 14, 'History': 36, 'Horror': 27, 'Music': 10402,
            'Mystery': 9648, 'Romance': 10749, 'Science Fiction': 878,
            'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37,
            # 한국어 장르명
            '액션': 28, '모험': 12, '애니메이션': 16, '코미디': 35,
            '범죄': 80, '다큐멘터리': 99, '드라마': 18, '가족': 10751,
            '판타지': 14, '역사': 36, '공포': 27, '음악': 10402,
            '미스터리': 9648, '로맨스': 10749, 'SF': 878, '스릴러': 53,
            '전쟁': 10752, '서부': 37
        }
        
        genre_ids = []
        for name in genre_names:
            name = name.strip()
            if name in genre_mapping:
                genre_ids.append(genre_mapping[name])
        
        return genre_ids
    
    def validate_and_filter_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """레코드 유효성 검증 및 필터링"""
        issues = []
        
        # 필수 필드 검증
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in record or not record[field]:
                issues.append(f'missing_required_field_{field}')
        
        # 성인 콘텐츠 필터링
        if self.cleaning_rules['data_validation']['filter_adult_content']:
            if record.get('adult', False):
                issues.append('adult_content_filtered')
                return False, issues
        
        # 날짜 범위 검증
        if self.cleaning_rules['data_validation']['validate_date_ranges']:
            release_date = record.get('release_date', '')
            if release_date:
                try:
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                    # 너무 오래된 영화 (1900년 이전) 또는 미래 영화 필터링
                    if release_dt.year < 1900 or release_dt > datetime.now() + timedelta(days=365):
                        issues.append('invalid_release_date_range')
                        return False, issues
                except ValueError:
                    issues.append('invalid_release_date_format')
        
        # 평점 범위 검증
        vote_average = record.get('vote_average', 0)
        if vote_average and (vote_average < 0 or vote_average > 10):
            issues.append('invalid_vote_average_range')
        
        # 투표 수 검증
        vote_count = record.get('vote_count', 0)
        if vote_count and vote_count < 0:
            issues.append('invalid_vote_count')
        
        return len([issue for issue in issues if 'filtered' in issue or 'missing_required' in issue]) == 0, issues
    
    def fill_missing_values(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """누락된 값 채우기"""
        applied_rules = []
        cleaned_record = record.copy()
        
        # 기본값 설정
        default_values = {
            'vote_average': 0.0,
            'vote_count': 0,
            'popularity': 0.0,
            'adult': False,
            'video': False,
            'genre_ids': [],
            'overview': '',
            'poster_path': None,
            'backdrop_path': None,
            'original_language': 'en',
            'original_title': cleaned_record.get('title', '')
        }
        
        for field, default_value in default_values.items():
            if field not in cleaned_record or cleaned_record[field] is None or cleaned_record[field] == '':
                cleaned_record[field] = default_value
                applied_rules.append(f'filled_missing_{field}')
        
        # 제목이 없는 경우 원제목 사용
        if not cleaned_record.get('title') and cleaned_record.get('original_title'):
            cleaned_record['title'] = cleaned_record['original_title']
            applied_rules.append('used_original_title_as_title')
        
        return cleaned_record, applied_rules
    
    def clean_single_record(self, record: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """단일 레코드 정제"""
        self.cleaning_stats['processed_records'] += 1
        
        cleaning_report = {
            'original_record_id': record.get('id', 'unknown'),
            'applied_rules': [],
            'issues_found': [],
            'validation_passed': True,
            'cleaning_successful': True
        }
        
        try:
            cleaned_record = record.copy()
            
            # 1. 레코드 유효성 검증
            is_valid, validation_issues = self.validate_and_filter_record(record)
            cleaning_report['issues_found'].extend(validation_issues)
            cleaning_report['validation_passed'] = is_valid
            
            if not is_valid:
                self.cleaning_stats['removed_records'] += 1
                return None, cleaning_report
            
            # 2. 텍스트 필드 정제
            text_fields = ['title', 'original_title', 'overview']
            for field in text_fields:
                if field in cleaned_record and cleaned_record[field]:
                    cleaned_text, rules = self.clean_text_field(cleaned_record[field], field)
                    cleaned_record[field] = cleaned_text
                    cleaning_report['applied_rules'].extend([f'{field}_{rule}' for rule in rules])
            
            # 3. 날짜 필드 표준화
            if 'release_date' in cleaned_record:
                standardized_date, rules = self.standardize_date_field(cleaned_record['release_date'])
                cleaned_record['release_date'] = standardized_date
                cleaning_report['applied_rules'].extend([f'release_date_{rule}' for rule in rules])
            
            # 4. 평점 정규화
            if 'vote_average' in cleaned_record:
                normalized_rating, rules = self.normalize_rating_field(cleaned_record['vote_average'])
                cleaned_record['vote_average'] = normalized_rating
                cleaning_report['applied_rules'].extend([f'vote_average_{rule}' for rule in rules])
            
            # 5. 장르 정제
            if 'genre_ids' in cleaned_record:
                cleaned_genres, rules = self.clean_genre_field(cleaned_record['genre_ids'])
                cleaned_record['genre_ids'] = cleaned_genres
                cleaning_report['applied_rules'].extend([f'genre_ids_{rule}' for rule in rules])
            
            # 6. 누락 값 채우기
            cleaned_record, fill_rules = self.fill_missing_values(cleaned_record)
            cleaning_report['applied_rules'].extend(fill_rules)
            
            # 7. 데이터 타입 표준화
            type_standardization = {
                'id': int,
                'vote_count': int,
                'popularity': float,
                'adult': bool,
                'video': bool
            }
            
            for field, target_type in type_standardization.items():
                if field in cleaned_record and cleaned_record[field] is not None:
                    try:
                        if target_type == bool:
                            cleaned_record[field] = bool(cleaned_record[field])
                        else:
                            cleaned_record[field] = target_type(cleaned_record[field])
                        cleaning_report['applied_rules'].append(f'standardized_type_{field}')
                    except (ValueError, TypeError):
                        cleaning_report['issues_found'].append(f'type_conversion_failed_{field}')
            
            # 정제 통계 업데이트
            if cleaning_report['applied_rules']:
                self.cleaning_stats['cleaned_records'] += 1
                for rule in cleaning_report['applied_rules']:
                    self.cleaning_stats['applied_rules'][rule] += 1
            
            return cleaned_record, cleaning_report
            
        except Exception as e:
            cleaning_report['cleaning_successful'] = False
            cleaning_report['error'] = str(e)
            self.cleaning_stats['error_records'].append({
                'record_id': record.get('id', 'unknown'),
                'error': str(e)
            })
            self.logger.error(f"레코드 정제 실패 ID {record.get('id', 'unknown')}: {e}")
            return None, cleaning_report
    
    def clean_batch_data(self, data: List[Dict[str, Any]], 
                        source_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """배치 데이터 정제"""
        start_time = datetime.now()
        
        # 정제 통계 초기화
        self.cleaning_stats = {
            'processed_files': 0,
            'processed_records': 0,
            'cleaned_records': 0,
            'removed_records': 0,
            'applied_rules': Counter(),
            'error_records': []
        }
        
        cleaned_data = []
        cleaning_reports = []
        duplicate_ids = set()
        
        self.logger.info(f"배치 데이터 정제 시작: {len(data)}개 레코드")
        
        # 중복 제거를 위한 ID 수집
        if self.cleaning_rules['data_validation']['remove_duplicates']:
            seen_ids = set()
            unique_data = []
            
            for record in data:
                record_id = record.get('id')
                if record_id not in seen_ids:
                    seen_ids.add(record_id)
                    unique_data.append(record)
                else:
                    duplicate_ids.add(record_id)
            
            data = unique_data
            self.logger.info(f"중복 제거: {len(duplicate_ids)}개 중복 레코드 제거")
        
        # 각 레코드 정제
        for i, record in enumerate(data):
            if i % 100 == 0:
                self.logger.info(f"정제 진행률: {i}/{len(data)} ({i/len(data)*100:.1f}%)")
            
            cleaned_record, report = self.clean_single_record(record)
            cleaning_reports.append(report)
            
            if cleaned_record is not None:
                cleaned_data.append(cleaned_record)
        
        # 정제 결과 요약
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        cleaning_summary = {
            'cleaning_info': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'source_info': source_info or {},
                'cleaning_rules_applied': dict(self.cleaning_stats['applied_rules'].most_common())
            },
            'statistics': {
                'original_records': len(data) + len(duplicate_ids),
                'duplicate_records_removed': len(duplicate_ids),
                'processed_records': self.cleaning_stats['processed_records'],
                'cleaned_records': self.cleaning_stats['cleaned_records'],
                'removed_records': self.cleaning_stats['removed_records'],
                'final_records': len(cleaned_data),
                'cleaning_rate': (self.cleaning_stats['cleaned_records'] / self.cleaning_stats['processed_records'] * 100) if self.cleaning_stats['processed_records'] > 0 else 0,
                'retention_rate': (len(cleaned_data) / (len(data) + len(duplicate_ids)) * 100) if (len(data) + len(duplicate_ids)) > 0 else 0
            },
            'quality_metrics': {
                'records_with_issues': len([r for r in cleaning_reports if r['issues_found']]),
                'validation_failure_rate': len([r for r in cleaning_reports if not r['validation_passed']]) / len(cleaning_reports) * 100 if cleaning_reports else 0,
                'most_common_issues': self._get_most_common_issues(cleaning_reports),
                'most_applied_rules': dict(self.cleaning_stats['applied_rules'].most_common(10))
            },
            'recommendations': self._generate_cleaning_recommendations(cleaning_reports)
        }
        
        # 결과 저장
        result = {
            'cleaned_data': cleaned_data,
            'cleaning_summary': cleaning_summary,
            'cleaning_reports': cleaning_reports
        }
        
        self.logger.info(f"배치 정제 완료: {len(cleaned_data)}/{len(data)}개 레코드 정제 성공 ({duration:.1f}초)")
        
        return result
    
    def _get_most_common_issues(self, cleaning_reports: List[Dict[str, Any]]) -> Dict[str, int]:
        """가장 흔한 문제들 집계"""
        all_issues = []
        for report in cleaning_reports:
            all_issues.extend(report.get('issues_found', []))
        
        issue_counter = Counter(all_issues)
        return dict(issue_counter.most_common(10))
    
    def _generate_cleaning_recommendations(self, cleaning_reports: List[Dict[str, Any]]) -> List[str]:
        """정제 결과 기반 권장사항 생성"""
        recommendations = []
        
        # 이슈 분석
        all_issues = []
        for report in cleaning_reports:
            all_issues.extend(report.get('issues_found', []))
        
        issue_counter = Counter(all_issues)
        
        # 가장 흔한 문제들에 대한 권장사항
        for issue, count in issue_counter.most_common(5):
            if 'missing_required_field' in issue:
                recommendations.append(f"필수 필드 누락이 빈번합니다 ({count}건). 데이터 수집 시 필수 필드 검증을 강화하세요.")
            elif 'adult_content_filtered' in issue:
                recommendations.append(f"성인 콘텐츠가 많이 필터링되었습니다 ({count}건). 수집 시 성인 콘텐츠 필터를 적용하세요.")
            elif 'invalid_date' in issue:
                recommendations.append(f"날짜 형식 문제가 많습니다 ({count}건). API 응답의 날짜 형식을 확인하세요.")
            elif 'encoding' in issue:
                recommendations.append(f"인코딩 문제가 발견되었습니다 ({count}건). 데이터 수집 시 UTF-8 인코딩을 확인하세요.")
        
        # 정제율 기반 권장사항
        cleaning_rate = len([r for r in cleaning_reports if r.get('applied_rules')]) / len(cleaning_reports) * 100 if cleaning_reports else 0
        
        if cleaning_rate > 50:
            recommendations.append("정제율이 높습니다. 데이터 소스의 품질 개선을 고려하세요.")
        elif cleaning_rate < 10:
            recommendations.append("정제율이 낮습니다. 현재 데이터 품질이 양호합니다.")
        
        if not recommendations:
            recommendations.append("데이터 품질이 전반적으로 양호합니다.")
        
        return recommendations
    
    def save_cleaned_data(self, cleaned_result: Dict[str, Any], 
                         output_filename: str = None) -> str:
        """정제된 데이터 저장"""
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"cleaned_data_{timestamp}.json"
        
        output_path = self.cleaned_dir / output_filename
        
        # 정제된 데이터만 저장 (리포트는 별도 저장)
        data_to_save = {
            'movies': cleaned_result['cleaned_data'],
            'cleaning_info': cleaned_result['cleaning_summary']['cleaning_info'],
            'statistics': cleaned_result['cleaning_summary']['statistics'],
            'quality_metrics': cleaned_result['cleaning_summary']['quality_metrics']
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)
        
        # 상세 리포트는 별도 저장
        report_path = self.cleaned_dir / f"cleaning_report_{output_filename}"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_result['cleaning_summary'], f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"정제된 데이터 저장: {output_path}")
        self.logger.info(f"정제 리포트 저장: {report_path}")
        
        return str(output_path)
    
    def clean_file(self, file_path: Union[str, Path], 
                   output_path: str = None) -> Dict[str, Any]:
        """파일 데이터 정제"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        self.logger.info(f"파일 정제 시작: {file_path}")
        
        # 파일 로드
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            # 영화 데이터 추출
            if isinstance(file_data, dict):
                if 'movies' in file_data:
                    movies_data = file_data['movies']
                    source_info = file_data.get('collection_info', {})
                elif 'results' in file_data:
                    movies_data = file_data['results']
                    source_info = {k: v for k, v in file_data.items() if k != 'results'}
                else:
                    movies_data = [file_data]  # 단일 레코드
                    source_info = {}
            elif isinstance(file_data, list):
                movies_data = file_data
                source_info = {}
            else:
                raise ValueError("지원하지 않는 파일 형식입니다.")
            
            # 소스 정보 추가
            source_info.update({
                'source_file': str(file_path),
                'source_file_size': file_path.stat().st_size,
                'source_modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
            
            # 배치 정제 실행
            result = self.clean_batch_data(movies_data, source_info)
            
            # 결과 저장
            if output_path:
                self.save_cleaned_data(result, output_path)
            else:
                # 자동 파일명 생성
                original_stem = file_path.stem
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                auto_filename = f"cleaned_{original_stem}_{timestamp}.json"
                self.save_cleaned_data(result, auto_filename)
            
            return result
            
        except Exception as e:
            self.logger.error(f"파일 정제 실패 {file_path}: {e}")
            raise

def main():
    """데이터 정제 도구 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터 자동 정제 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 파일 정제
    clean_parser = subparsers.add_parser('clean', help='파일 데이터 정제')
    clean_parser.add_argument('input_file', help='입력 파일 경로')
    clean_parser.add_argument('--output', help='출력 파일 경로')
    
    # 배치 정제
    batch_parser = subparsers.add_parser('batch', help='디렉토리 내 모든 파일 정제')
    batch_parser.add_argument('input_dir', help='입력 디렉토리 경로')
    batch_parser.add_argument('--pattern', default='*.json', help='파일 패턴')
    
    # 정제 규칙 설정
    config_parser = subparsers.add_parser('config', help='정제 규칙 설정')
    config_parser.add_argument('--show', action='store_true', help='현재 규칙 표시')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    cleaner = DataCleaner()
    
    try:
        if args.command == 'clean':
            result = cleaner.clean_file(args.input_file, args.output)
            stats = result['cleaning_summary']['statistics']
            print(f"정제 완료: {stats['final_records']}/{stats['original_records']}개 레코드")
            print(f"정제율: {stats['cleaning_rate']:.1f}%")
            print(f"보존율: {stats['retention_rate']:.1f}%")
            
        elif args.command == 'batch':
            input_dir = Path(args.input_dir)
            if not input_dir.exists():
                print(f"디렉토리를 찾을 수 없습니다: {input_dir}")
                return
            
            files = list(input_dir.glob(args.pattern))
            print(f"배치 정제 시작: {len(files)}개 파일")
            
            total_processed = 0
            total_cleaned = 0
            
            for file_path in files:
                try:
                    result = cleaner.clean_file(file_path)
                    stats = result['cleaning_summary']['statistics']
                    total_processed += stats['original_records']
                    total_cleaned += stats['final_records']
                    print(f"✅ {file_path.name}: {stats['final_records']}/{stats['original_records']}개")
                except Exception as e:
                    print(f"❌ {file_path.name}: {e}")
            
            print(f"\n배치 정제 완료: {total_cleaned}/{total_processed}개 레코드")
            
        elif args.command == 'config':
            if args.show:
                print("현재 정제 규칙:")
                print(json.dumps(cleaner.cleaning_rules, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"명령 실행 실패: {e}")

if __name__ == "__main__":
    main()

"""
통계적 이상 탐지 시스템
데이터 수집 및 품질 지표에서 이상 패턴을 자동으로 감지
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import json
import logging
from collections import defaultdict, deque
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AnomalyDetector:
    """통계적 이상 탐지"""
    
    def __init__(self, data_dir: str = 'data', baseline_days: int = 30):
        self.data_dir = Path(data_dir)
        self.baseline_days = baseline_days
        self.logger = logging.getLogger(__name__)
        
        # 이상 탐지 임계값 설정
        self.thresholds = {
            'z_score_threshold': 3.0,      # Z-score 기반 이상치 임계값
            'iqr_multiplier': 1.5,         # IQR 기반 이상치 배수
            'collection_volume_change': 0.5,  # 수집량 변화율 임계값 (50%)
            'quality_score_drop': 20,      # 품질 점수 하락 임계값 (20점)
            'response_time_increase': 2.0, # 응답 시간 증가 배수
            'error_rate_threshold': 0.1    # 에러율 임계값 (10%)
        }
        
        # 기준선 통계 저장
        self.baseline_stats = {}
        self.historical_data = {
            'collection_volumes': deque(maxlen=100),
            'quality_scores': deque(maxlen=100),
            'response_times': deque(maxlen=100),
            'error_rates': deque(maxlen=100)
        }
        
        # 이상 탐지 결과 저장 디렉토리
        self.anomaly_dir = self.data_dir / 'raw' / 'metadata' / 'anomalies'
        self.anomaly_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_z_score(self, value: float, mean: float, std: float) -> float:
        """Z-score 계산"""
        if std == 0:
            return 0
        return abs(value - mean) / std
    
    def _detect_outliers_iqr(self, data: List[float]) -> Tuple[float, float, List[int]]:
        """IQR 방법으로 이상치 탐지"""
        if len(data) < 4:
            return 0, 0, []
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.thresholds['iqr_multiplier'] * iqr
        upper_bound = q3 + self.thresholds['iqr_multiplier'] * iqr
        
        outliers = [i for i, x in enumerate(data) if x < lower_bound or x > upper_bound]
        
        return lower_bound, upper_bound, outliers
    
    def _detect_outliers_isolation_forest(self, data: List[Dict[str, Any]]) -> List[bool]:
        """Isolation Forest를 사용한 다차원 이상치 탐지 (간단 구현)"""
        if len(data) < 10:
            return [False] * len(data)
        
        # 주요 수치 특성들 추출
        features = []
        for item in data:
            feature_vector = [
                item.get('volume', 0),
                item.get('quality_score', 0),
                item.get('duration', 0),
                item.get('error_count', 0)
            ]
            features.append(feature_vector)
        
        features_array = np.array(features)
        
        # 간단한 이상치 탐지: 각 특성에 대해 Z-score 계산
        outliers = []
        for i, feature_vector in enumerate(features_array):
            is_outlier = False
            for j, value in enumerate(feature_vector):
                if len(features_array) > 1:
                    mean = np.mean(features_array[:, j])
                    std = np.std(features_array[:, j])
                    z_score = self._calculate_z_score(value, mean, std)
                    if z_score > self.thresholds['z_score_threshold']:
                        is_outlier = True
                        break
            outliers.append(is_outlier)
        
        return outliers
    
    def detect_collection_volume_anomalies(self, 
                                         collection_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """수집량 이상 패턴 탐지"""
        if not collection_stats:
            return {'status': 'no_data', 'anomalies': []}
        
        volumes = [stats.get('total_collected', 0) for stats in collection_stats]
        dates = [stats.get('collection_date', '') for stats in collection_stats]
        
        anomaly_info = {
            'detection_type': 'collection_volume',
            'analysis_date': datetime.now().isoformat(),
            'total_samples': len(volumes),
            'anomalies': [],
            'statistics': {
                'mean': np.mean(volumes) if volumes else 0,
                'std': np.std(volumes) if volumes else 0,
                'median': np.median(volumes) if volumes else 0,
                'min': min(volumes) if volumes else 0,
                'max': max(volumes) if volumes else 0
            }
        }
        
        if len(volumes) < 3:
            return anomaly_info
        
        # Z-score 기반 이상치 탐지
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        for i, (volume, date) in enumerate(zip(volumes, dates)):
            z_score = self._calculate_z_score(volume, mean_volume, std_volume)
            
            if z_score > self.thresholds['z_score_threshold']:
                anomaly_info['anomalies'].append({
                    'index': i,
                    'date': date,
                    'value': volume,
                    'z_score': z_score,
                    'anomaly_type': 'volume_outlier',
                    'severity': 'high' if z_score > 4 else 'medium',
                    'description': f"수집량이 평균 대비 {z_score:.1f} 표준편차 벗어남"
                })
        
        # 연속적인 감소 패턴 탐지
        if len(volumes) >= 5:
            for i in range(2, len(volumes)):
                recent_volumes = volumes[i-2:i+1]
                if all(recent_volumes[j] > recent_volumes[j+1] for j in range(len(recent_volumes)-1)):
                    decrease_rate = (recent_volumes[0] - recent_volumes[-1]) / recent_volumes[0]
                    if decrease_rate > self.thresholds['collection_volume_change']:
                        anomaly_info['anomalies'].append({
                            'index': i,
                            'date': dates[i],
                            'value': volumes[i],
                            'anomaly_type': 'decreasing_trend',
                            'severity': 'medium',
                            'decrease_rate': decrease_rate,
                            'description': f"수집량이 연속적으로 {decrease_rate*100:.1f}% 감소"
                        })
        
        # 급격한 변화 탐지
        for i in range(1, len(volumes)):
            if volumes[i-1] > 0:
                change_rate = abs(volumes[i] - volumes[i-1]) / volumes[i-1]
                if change_rate > self.thresholds['collection_volume_change']:
                    anomaly_info['anomalies'].append({
                        'index': i,
                        'date': dates[i],
                        'value': volumes[i],
                        'previous_value': volumes[i-1],
                        'change_rate': change_rate,
                        'anomaly_type': 'sudden_change',
                        'severity': 'high' if change_rate > 1.0 else 'medium',
                        'description': f"수집량이 이전 대비 {change_rate*100:.1f}% 변화"
                    })
        
        return anomaly_info
    
    def detect_quality_score_anomalies(self, 
                                     quality_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """품질 점수 이상 패턴 탐지"""
        if not quality_reports:
            return {'status': 'no_data', 'anomalies': []}
        
        scores = [report.get('overall_quality_score', 0) for report in quality_reports]
        dates = [report.get('report_date', '') for report in quality_reports]
        
        anomaly_info = {
            'detection_type': 'quality_score',
            'analysis_date': datetime.now().isoformat(),
            'total_samples': len(scores),
            'anomalies': [],
            'statistics': {
                'mean': np.mean(scores) if scores else 0,
                'std': np.std(scores) if scores else 0,
                'median': np.median(scores) if scores else 0,
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0
            }
        }
        
        if len(scores) < 3:
            return anomaly_info
        
        # 급격한 품질 하락 탐지
        for i in range(1, len(scores)):
            score_drop = scores[i-1] - scores[i]
            if score_drop > self.thresholds['quality_score_drop']:
                anomaly_info['anomalies'].append({
                    'index': i,
                    'date': dates[i],
                    'value': scores[i],
                    'previous_value': scores[i-1],
                    'score_drop': score_drop,
                    'anomaly_type': 'quality_drop',
                    'severity': 'high' if score_drop > 30 else 'medium',
                    'description': f"품질 점수가 {score_drop:.1f}점 하락"
                })
        
        # 지속적인 품질 저하 탐지
        if len(scores) >= 5:
            for i in range(4, len(scores)):
                recent_scores = scores[i-4:i+1]
                # 연속 5일 모두 감소하는 패턴
                if all(recent_scores[j] > recent_scores[j+1] for j in range(len(recent_scores)-1)):
                    total_drop = recent_scores[0] - recent_scores[-1]
                    anomaly_info['anomalies'].append({
                        'index': i,
                        'date': dates[i],
                        'value': scores[i],
                        'anomaly_type': 'sustained_degradation',
                        'severity': 'high',
                        'total_drop': total_drop,
                        'description': f"품질이 지속적으로 하락 (총 {total_drop:.1f}점)"
                    })
        
        # 낮은 품질 점수 탐지
        for i, (score, date) in enumerate(zip(scores, dates)):
            if score < 70:  # 품질 점수 70점 미만
                severity = 'critical' if score < 50 else 'high' if score < 60 else 'medium'
                anomaly_info['anomalies'].append({
                    'index': i,
                    'date': date,
                    'value': score,
                    'anomaly_type': 'low_quality',
                    'severity': severity,
                    'description': f"품질 점수가 {score:.1f}점으로 낮음"
                })
        
        return anomaly_info
    
    def detect_response_time_anomalies(self, 
                                     performance_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """응답 시간 이상 패턴 탐지"""
        if not performance_logs:
            return {'status': 'no_data', 'anomalies': []}
        
        response_times = [log.get('duration', 0) for log in performance_logs]
        operations = [log.get('operation', 'unknown') for log in performance_logs]
        timestamps = [log.get('timestamp', '') for log in performance_logs]
        
        anomaly_info = {
            'detection_type': 'response_time',
            'analysis_date': datetime.now().isoformat(),
            'total_samples': len(response_times),
            'anomalies': [],
            'statistics': {
                'mean': np.mean(response_times) if response_times else 0,
                'std': np.std(response_times) if response_times else 0,
                'median': np.median(response_times) if response_times else 0,
                'p95': np.percentile(response_times, 95) if response_times else 0,
                'max': max(response_times) if response_times else 0
            }
        }
        
        if len(response_times) < 5:
            return anomaly_info
        
        # 작업별 응답 시간 기준선 계산
        operation_baselines = defaultdict(list)
        for time, operation in zip(response_times, operations):
            operation_baselines[operation].append(time)
        
        # 기준선 통계 계산
        baselines = {}
        for operation, times in operation_baselines.items():
            if len(times) >= 3:
                baselines[operation] = {
                    'mean': np.mean(times),
                    'std': np.std(times),
                    'p95': np.percentile(times, 95)
                }
        
        # 이상치 탐지
        for i, (time, operation, timestamp) in enumerate(zip(response_times, operations, timestamps)):
            # 전체 데이터 기준 이상치
            if len(response_times) > 10:
                mean_time = np.mean(response_times)
                std_time = np.std(response_times)
                z_score = self._calculate_z_score(time, mean_time, std_time)
                
                if z_score > self.thresholds['z_score_threshold']:
                    anomaly_info['anomalies'].append({
                        'index': i,
                        'timestamp': timestamp,
                        'operation': operation,
                        'value': time,
                        'z_score': z_score,
                        'anomaly_type': 'response_time_outlier',
                        'severity': 'high' if z_score > 5 else 'medium',
                        'description': f"{operation} 작업 응답시간이 평균 대비 {z_score:.1f} 표준편차 초과"
                    })
            
            # 작업별 기준선 대비 이상치
            if operation in baselines:
                baseline = baselines[operation]
                if time > baseline['mean'] * self.thresholds['response_time_increase']:
                    increase_factor = time / baseline['mean']
                    anomaly_info['anomalies'].append({
                        'index': i,
                        'timestamp': timestamp,
                        'operation': operation,
                        'value': time,
                        'baseline_mean': baseline['mean'],
                        'increase_factor': increase_factor,
                        'anomaly_type': 'slow_operation',
                        'severity': 'critical' if increase_factor > 5 else 'high',
                        'description': f"{operation} 작업이 평상시보다 {increase_factor:.1f}배 느림"
                    })
        
        return anomaly_info
    
    def detect_error_rate_anomalies(self, 
                                  error_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """에러율 이상 패턴 탐지"""
        if not error_logs:
            return {'status': 'no_data', 'anomalies': []}
        
        # 시간대별 에러율 계산
        hourly_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
        
        for log in error_logs:
            timestamp = log.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    
                    hourly_stats[hour_key]['total'] += 1
                    if log.get('level') in ['ERROR', 'CRITICAL']:
                        hourly_stats[hour_key]['errors'] += 1
                except ValueError:
                    continue
        
        # 에러율 계산
        error_rates = []
        hours = []
        for hour, stats in sorted(hourly_stats.items()):
            if stats['total'] > 0:
                error_rate = stats['errors'] / stats['total']
                error_rates.append(error_rate)
                hours.append(hour)
        
        anomaly_info = {
            'detection_type': 'error_rate',
            'analysis_date': datetime.now().isoformat(),
            'total_samples': len(error_rates),
            'anomalies': [],
            'statistics': {
                'mean_error_rate': np.mean(error_rates) if error_rates else 0,
                'max_error_rate': max(error_rates) if error_rates else 0,
                'hours_with_errors': len([r for r in error_rates if r > 0]),
                'hours_analyzed': len(error_rates)
            }
        }
        
        if len(error_rates) < 3:
            return anomaly_info
        
        # 높은 에러율 탐지
        for i, (rate, hour) in enumerate(zip(error_rates, hours)):
            if rate > self.thresholds['error_rate_threshold']:
                severity = 'critical' if rate > 0.5 else 'high' if rate > 0.3 else 'medium'
                anomaly_info['anomalies'].append({
                    'index': i,
                    'hour': hour,
                    'error_rate': rate,
                    'anomaly_type': 'high_error_rate',
                    'severity': severity,
                    'description': f"에러율이 {rate*100:.1f}%로 임계값 초과"
                })
        
        # 에러율 급증 탐지
        for i in range(1, len(error_rates)):
            if error_rates[i-1] < 0.05 and error_rates[i] > 0.2:  # 5%에서 20%로 급증
                anomaly_info['anomalies'].append({
                    'index': i,
                    'hour': hours[i],
                    'error_rate': error_rates[i],
                    'previous_rate': error_rates[i-1],
                    'anomaly_type': 'error_rate_spike',
                    'severity': 'high',
                    'description': f"에러율이 {error_rates[i-1]*100:.1f}%에서 {error_rates[i]*100:.1f}%로 급증"
                })
        
        return anomaly_info
    
    def detect_data_freshness_anomalies(self, 
                                       file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """데이터 신선도 이상 탐지"""
        if not file_metadata:
            return {'status': 'no_data', 'anomalies': []}
        
        current_time = datetime.now()
        anomaly_info = {
            'detection_type': 'data_freshness',
            'analysis_date': current_time.isoformat(),
            'total_files': len(file_metadata),
            'anomalies': [],
            'statistics': {
                'fresh_files': 0,  # 1시간 이내
                'recent_files': 0,  # 24시간 이내
                'stale_files': 0,   # 24시간 초과
                'oldest_file_age_hours': 0
            }
        }
        
        file_ages = []
        
        for i, metadata in enumerate(file_metadata):
            modified_date = metadata.get('modified_date', '')
            file_path = metadata.get('file_path', '')
            
            if not modified_date:
                continue
            
            try:
                file_time = datetime.fromisoformat(modified_date)
                age_hours = (current_time - file_time).total_seconds() / 3600
                file_ages.append(age_hours)
                
                # 분류
                if age_hours <= 1:
                    anomaly_info['statistics']['fresh_files'] += 1
                elif age_hours <= 24:
                    anomaly_info['statistics']['recent_files'] += 1
                else:
                    anomaly_info['statistics']['stale_files'] += 1
                
                # 너무 오래된 파일 탐지
                if age_hours > 72:  # 3일 이상
                    severity = 'critical' if age_hours > 168 else 'high'  # 1주일 이상이면 critical
                    anomaly_info['anomalies'].append({
                        'index': i,
                        'file_path': file_path,
                        'age_hours': age_hours,
                        'age_days': age_hours / 24,
                        'anomaly_type': 'stale_data',
                        'severity': severity,
                        'description': f"파일이 {age_hours/24:.1f}일 동안 업데이트되지 않음"
                    })
                
            except ValueError:
                anomaly_info['anomalies'].append({
                    'index': i,
                    'file_path': file_path,
                    'anomaly_type': 'invalid_timestamp',
                    'severity': 'medium',
                    'description': "파일 수정 시간을 파싱할 수 없음"
                })
        
        if file_ages:
            anomaly_info['statistics']['oldest_file_age_hours'] = max(file_ages)
        
        # 신선한 데이터 부족 탐지
        if anomaly_info['statistics']['fresh_files'] == 0 and len(file_metadata) > 0:
            anomaly_info['anomalies'].append({
                'anomaly_type': 'no_fresh_data',
                'severity': 'high',
                'description': "최근 1시간 이내에 업데이트된 파일이 없음"
            })
        
        return anomaly_info
    
    def run_comprehensive_analysis(self, 
                                 collection_stats: List[Dict[str, Any]] = None,
                                 quality_reports: List[Dict[str, Any]] = None,
                                 performance_logs: List[Dict[str, Any]] = None,
                                 error_logs: List[Dict[str, Any]] = None,
                                 file_metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """종합 이상 탐지 분석"""
        
        analysis_result = {
            'analysis_date': datetime.now().isoformat(),
            'analysis_summary': {
                'total_anomalies': 0,
                'critical_anomalies': 0,
                'high_anomalies': 0,
                'medium_anomalies': 0,
                'analysis_types': []
            },
            'anomaly_details': {},
            'recommendations': []
        }
        
        # 각 유형별 이상 탐지 실행
        if collection_stats:
            volume_anomalies = self.detect_collection_volume_anomalies(collection_stats)
            analysis_result['anomaly_details']['collection_volume'] = volume_anomalies
            analysis_result['analysis_summary']['analysis_types'].append('collection_volume')
        
        if quality_reports:
            quality_anomalies = self.detect_quality_score_anomalies(quality_reports)
            analysis_result['anomaly_details']['quality_score'] = quality_anomalies
            analysis_result['analysis_summary']['analysis_types'].append('quality_score')
        
        if performance_logs:
            performance_anomalies = self.detect_response_time_anomalies(performance_logs)
            analysis_result['anomaly_details']['response_time'] = performance_anomalies
            analysis_result['analysis_summary']['analysis_types'].append('response_time')
        
        if error_logs:
            error_anomalies = self.detect_error_rate_anomalies(error_logs)
            analysis_result['anomaly_details']['error_rate'] = error_anomalies
            analysis_result['analysis_summary']['analysis_types'].append('error_rate')
        
        if file_metadata:
            freshness_anomalies = self.detect_data_freshness_anomalies(file_metadata)
            analysis_result['anomaly_details']['data_freshness'] = freshness_anomalies
            analysis_result['analysis_summary']['analysis_types'].append('data_freshness')
        
        # 전체 이상 현상 통계 집계
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for analysis_type, anomaly_data in analysis_result['anomaly_details'].items():
            anomalies = anomaly_data.get('anomalies', [])
            analysis_result['analysis_summary']['total_anomalies'] += len(anomalies)
            
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'medium')
                severity_counts[severity] += 1
        
        analysis_result['analysis_summary']['critical_anomalies'] = severity_counts['critical']
        analysis_result['analysis_summary']['high_anomalies'] = severity_counts['high']
        analysis_result['analysis_summary']['medium_anomalies'] = severity_counts['medium']
        
        # 권장사항 생성
        recommendations = self._generate_recommendations(analysis_result['anomaly_details'])
        analysis_result['recommendations'] = recommendations
        
        # 결과 저장
        result_file = self.anomaly_dir / f'anomaly_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"종합 이상 탐지 분석 완료: {analysis_result['analysis_summary']['total_anomalies']}개 이상 현상 탐지")
        
        return analysis_result
    
    def _generate_recommendations(self, anomaly_details: Dict[str, Any]) -> List[str]:
        """이상 탐지 결과 기반 권장사항 생성"""
        recommendations = []
        
        # 수집량 이상
        if 'collection_volume' in anomaly_details:
            volume_anomalies = anomaly_details['collection_volume'].get('anomalies', [])
            if any(a['anomaly_type'] == 'decreasing_trend' for a in volume_anomalies):
                recommendations.append("데이터 수집량이 지속적으로 감소하고 있습니다. 수집 시스템을 점검하세요.")
            if any(a['anomaly_type'] == 'sudden_change' for a in volume_anomalies):
                recommendations.append("데이터 수집량에 급격한 변화가 감지되었습니다. API 상태를 확인하세요.")
        
        # 품질 이상
        if 'quality_score' in anomaly_details:
            quality_anomalies = anomaly_details['quality_score'].get('anomalies', [])
            if any(a['anomaly_type'] == 'quality_drop' for a in quality_anomalies):
                recommendations.append("데이터 품질이 급격히 하락했습니다. 데이터 소스를 점검하세요.")
            if any(a['anomaly_type'] == 'sustained_degradation' for a in quality_anomalies):
                recommendations.append("데이터 품질이 지속적으로 하락하고 있습니다. 검증 규칙을 강화하세요.")
        
        # 성능 이상
        if 'response_time' in anomaly_details:
            perf_anomalies = anomaly_details['response_time'].get('anomalies', [])
            if any(a['anomaly_type'] == 'slow_operation' for a in perf_anomalies):
                recommendations.append("API 응답시간이 비정상적으로 느립니다. 네트워크와 서버 상태를 확인하세요.")
        
        # 에러율 이상
        if 'error_rate' in anomaly_details:
            error_anomalies = anomaly_details['error_rate'].get('anomalies', [])
            if any(a['anomaly_type'] == 'high_error_rate' for a in error_anomalies):
                recommendations.append("에러율이 높습니다. 로그를 분석하여 원인을 파악하세요.")
            if any(a['anomaly_type'] == 'error_rate_spike' for a in error_anomalies):
                recommendations.append("에러율이 급증했습니다. 즉시 시스템 상태를 점검하세요.")
        
        # 데이터 신선도 이상
        if 'data_freshness' in anomaly_details:
            freshness_anomalies = anomaly_details['data_freshness'].get('anomalies', [])
            if any(a['anomaly_type'] == 'stale_data' for a in freshness_anomalies):
                recommendations.append("오래된 데이터 파일들이 있습니다. 데이터 갱신 프로세스를 확인하세요.")
            if any(a['anomaly_type'] == 'no_fresh_data' for a in freshness_anomalies):
                recommendations.append("최근 업데이트된 데이터가 없습니다. 자동 수집 시스템을 점검하세요.")
        
        if not recommendations:
            recommendations.append("현재 탐지된 이상 현상이 모두 정상 범위 내에 있습니다.")
        
        return recommendations
    
    def get_anomaly_summary(self, days: int = 7) -> Dict[str, Any]:
        """최근 이상 탐지 요약"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        summary = {
            'period_days': days,
            'summary_date': datetime.now().isoformat(),
            'total_analyses': 0,
            'total_anomalies': 0,
            'anomaly_types': defaultdict(int),
            'severity_distribution': defaultdict(int),
            'trend_analysis': {
                'increasing_anomalies': False,
                'most_frequent_type': None,
                'critical_periods': []
            }
        }
        
        # 최근 분석 결과 파일들 읽기
        for analysis_file in self.anomaly_dir.glob('anomaly_analysis_*.json'):
            try:
                # 파일명에서 날짜 추출
                file_date_str = analysis_file.stem.split('_')[-2]  # YYYYMMDD
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    continue
                
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                
                summary['total_analyses'] += 1
                summary['total_anomalies'] += analysis_data['analysis_summary']['total_anomalies']
                
                # 이상 유형별 집계
                for analysis_type, anomaly_data in analysis_data['anomaly_details'].items():
                    anomalies = anomaly_data.get('anomalies', [])
                    for anomaly in anomalies:
                        anomaly_type = anomaly.get('anomaly_type', 'unknown')
                        severity = anomaly.get('severity', 'medium')
                        
                        summary['anomaly_types'][anomaly_type] += 1
                        summary['severity_distribution'][severity] += 1
                
                # 심각한 이상이 많은 기간 식별
                critical_count = analysis_data['analysis_summary']['critical_anomalies']
                high_count = analysis_data['analysis_summary']['high_anomalies']
                
                if critical_count > 0 or high_count > 5:
                    summary['trend_analysis']['critical_periods'].append({
                        'date': file_date.strftime('%Y-%m-%d'),
                        'critical_anomalies': critical_count,
                        'high_anomalies': high_count
                    })
                
            except Exception as e:
                self.logger.error(f"분석 파일 읽기 실패 {analysis_file}: {e}")
                continue
        
        # 가장 빈번한 이상 유형
        if summary['anomaly_types']:
            summary['trend_analysis']['most_frequent_type'] = max(
                summary['anomaly_types'].items(), key=lambda x: x[1]
            )[0]
        
        # 이상 증가 추세 분석 (간단한 버전)
        if len(summary['trend_analysis']['critical_periods']) >= 3:
            summary['trend_analysis']['increasing_anomalies'] = True
        
        return summary

def main():
    """이상 탐지 도구 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터 이상 탐지 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 종합 분석
    analyze_parser = subparsers.add_parser('analyze', help='종합 이상 탐지 분석')
    analyze_parser.add_argument('--days', type=int, default=7, help='분석 기간 (일)')
    
    # 요약 조회
    summary_parser = subparsers.add_parser('summary', help='이상 탐지 요약')
    summary_parser.add_argument('--days', type=int, default=7, help='요약 기간 (일)')
    
    # 특정 유형 분석
    type_parser = subparsers.add_parser('detect', help='특정 유형 이상 탐지')
    type_parser.add_argument('type', choices=['volume', 'quality', 'performance', 'error', 'freshness'],
                            help='이상 탐지 유형')
    type_parser.add_argument('--input', help='입력 데이터 파일 (JSON)')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    detector = AnomalyDetector()
    
    try:
        if args.command == 'analyze':
            # 최근 데이터를 기반으로 종합 분석 수행
            # 실제 구현에서는 데이터 파일들을 읽어와서 전달
            print("종합 이상 탐지 분석을 수행합니다...")
            
            # 예시: 빈 분석 (실제로는 데이터 로드 필요)
            result = detector.run_comprehensive_analysis(
                collection_stats=[],
                quality_reports=[],
                performance_logs=[],
                error_logs=[],
                file_metadata=[]
            )
            
            print(f"분석 완료: {result['analysis_summary']['total_anomalies']}개 이상 현상 탐지")
            
        elif args.command == 'summary':
            summary = detector.get_anomaly_summary(args.days)
            print(f"\n=== 최근 {args.days}일 이상 탐지 요약 ===")
            print(f"총 분석 횟수: {summary['total_analyses']}")
            print(f"총 이상 현상: {summary['total_anomalies']}")
            print(f"가장 빈번한 유형: {summary['trend_analysis']['most_frequent_type']}")
            
            if summary['severity_distribution']:
                print("\n심각도별 분포:")
                for severity, count in summary['severity_distribution'].items():
                    print(f"  {severity}: {count}개")
            
        elif args.command == 'detect':
            if not args.input:
                print("입력 데이터 파일이 필요합니다.")
                return
            
            # 특정 유형 이상 탐지 수행
            with open(args.input, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
            
            if args.type == 'volume':
                result = detector.detect_collection_volume_anomalies(input_data)
            elif args.type == 'quality':
                result = detector.detect_quality_score_anomalies(input_data)
            elif args.type == 'performance':
                result = detector.detect_response_time_anomalies(input_data)
            elif args.type == 'error':
                result = detector.detect_error_rate_anomalies(input_data)
            elif args.type == 'freshness':
                result = detector.detect_data_freshness_anomalies(input_data)
            
            print(f"{args.type} 이상 탐지 완료: {len(result.get('anomalies', []))}개 이상 현상")
            
    except Exception as e:
        print(f"명령 실행 실패: {e}")

if __name__ == "__main__":
    main()

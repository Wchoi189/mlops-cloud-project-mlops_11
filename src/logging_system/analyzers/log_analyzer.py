"""
로그 분석 도구
로그 파일을 분석하여 패턴, 오류, 성능 이슈를 자동으로 탐지
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np

class LogAnalyzer:
    """로그 파일 분석기"""
    
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = Path(log_dir)
        self.error_patterns = [
            (r'ERROR.*?ConnectionError', 'connection_error'),
            (r'ERROR.*?TimeoutError', 'timeout_error'),
            (r'ERROR.*?HTTP 404', 'not_found_error'),
            (r'ERROR.*?HTTP 500', 'server_error'),
            (r'ERROR.*?ValidationError', 'validation_error'),
            (r'CRITICAL', 'critical_error'),
            (r'API.*?failed', 'api_failure'),
            (r'Database.*?error', 'database_error')
        ]
        
        self.performance_thresholds = {
            'api_call': 5.0,  # 5초
            'data_processing': 30.0,  # 30초
            'database_operation': 2.0,  # 2초
            'file_operation': 1.0,  # 1초
            'validation': 10.0  # 10초
        }
    
    def analyze_error_logs(self, hours: int = 24) -> Dict[str, Any]:
        """에러 로그 분석"""
        since = datetime.now() - timedelta(hours=hours)
        error_files = list(self.log_dir.glob('error/*.log')) + list(self.log_dir.glob('app/*.log'))
        
        error_analysis = {
            'analysis_period': f'Last {hours} hours',
            'analysis_time': datetime.now().isoformat(),
            'total_errors': 0,
            'error_types': {},
            'error_timeline': [],
            'frequent_errors': [],
            'critical_errors': [],
            'error_trend': 'stable'
        }
        
        all_errors = []
        
        for log_file in error_files:
            try:
                if not log_file.exists():
                    continue
                    
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        # 시간 파싱
                        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            try:
                                log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                if log_time < since:
                                    continue
                            except ValueError:
                                continue
                        
                        # 에러 패턴 매칭
                        if 'ERROR' in line or 'CRITICAL' in line:
                            error_type = 'unknown_error'
                            for pattern, etype in self.error_patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    error_type = etype
                                    break
                            
                            error_info = {
                                'file': str(log_file),
                                'line_num': line_num,
                                'timestamp': log_time.isoformat() if timestamp_match else None,
                                'type': error_type,
                                'message': line.strip(),
                                'severity': 'CRITICAL' if 'CRITICAL' in line else 'ERROR'
                            }
                            all_errors.append(error_info)
            
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
                continue
        
        # 분석 결과 집계
        error_analysis['total_errors'] = len(all_errors)
        
        # 에러 유형별 집계
        error_type_counts = Counter(error['type'] for error in all_errors)
        error_analysis['error_types'] = dict(error_type_counts.most_common())
        
        # 시간대별 에러 분포
        hourly_errors = defaultdict(int)
        for error in all_errors:
            if error['timestamp']:
                hour = datetime.fromisoformat(error['timestamp']).strftime('%Y-%m-%d %H:00')
                hourly_errors[hour] += 1
        
        error_analysis['error_timeline'] = [
            {'hour': hour, 'count': count} 
            for hour, count in sorted(hourly_errors.items())
        ]
        
        # 빈번한 에러 메시지
        message_counts = Counter(error['message'][:100] for error in all_errors)
        error_analysis['frequent_errors'] = [
            {'message': msg, 'count': count}
            for msg, count in message_counts.most_common(10)
        ]
        
        # 심각한 에러
        critical_errors = [error for error in all_errors if error['severity'] == 'CRITICAL']
        error_analysis['critical_errors'] = critical_errors[-10:]  # 최근 10개
        
        # 에러 트렌드 분석
        if len(error_analysis['error_timeline']) >= 2:
            recent_errors = sum(item['count'] for item in error_analysis['error_timeline'][-6:])  # 최근 6시간
            earlier_errors = sum(item['count'] for item in error_analysis['error_timeline'][-12:-6])  # 이전 6시간
            
            if recent_errors > earlier_errors * 1.5:
                error_analysis['error_trend'] = 'increasing'
            elif recent_errors < earlier_errors * 0.5:
                error_analysis['error_trend'] = 'decreasing'
        
        return error_analysis
    
    def analyze_performance_logs(self, hours: int = 24) -> Dict[str, Any]:
        """성능 로그 분석"""
        since = datetime.now() - timedelta(hours=hours)
        perf_files = list(self.log_dir.glob('performance/*.log')) + list(self.log_dir.glob('app/*.log'))
        
        performance_analysis = {
            'analysis_period': f'Last {hours} hours',
            'analysis_time': datetime.now().isoformat(),
            'total_operations': 0,
            'slow_operations': [],
            'component_stats': {},
            'performance_trend': 'stable'
        }
        
        all_operations = []
        
        for log_file in perf_files:
            try:
                if not log_file.exists():
                    continue
                    
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # 성능 로그 파싱 (다양한 패턴 지원)
                        patterns = [
                            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] PERF ([\w\.]+)\s+\| (\w+) completed in ([\d\.]+)s',
                            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*?(\w+) completed in ([\d\.]+)s',
                            r'(\w+) took ([\d\.]+) seconds'
                        ]
                        
                        for pattern in patterns:
                            perf_match = re.search(pattern, line)
                            if perf_match:
                                if len(perf_match.groups()) == 4:
                                    timestamp_str, component, operation, duration_str = perf_match.groups()
                                    try:
                                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        if log_time < since:
                                            continue
                                    except ValueError:
                                        continue
                                elif len(perf_match.groups()) == 3:
                                    timestamp_str, operation, duration_str = perf_match.groups()
                                    component = 'unknown'
                                    try:
                                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        if log_time < since:
                                            continue
                                    except ValueError:
                                        continue
                                elif len(perf_match.groups()) == 2:
                                    operation, duration_str = perf_match.groups()
                                    component = 'unknown'
                                    log_time = datetime.now()
                                else:
                                    continue
                                
                                try:
                                    duration = float(duration_str)
                                except ValueError:
                                    continue
                                
                                op_info = {
                                    'timestamp': log_time.isoformat(),
                                    'component': component,
                                    'operation': operation,
                                    'duration': duration
                                }
                                all_operations.append(op_info)
                                break
            
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
                continue
        
        performance_analysis['total_operations'] = len(all_operations)
        
        # 느린 작업 탐지
        slow_ops = []
        for op in all_operations:
            operation_type = self._categorize_operation(op['operation'])
            threshold = self.performance_thresholds.get(operation_type, 10.0)
            
            if op['duration'] > threshold:
                slow_ops.append({
                    **op,
                    'threshold': threshold,
                    'slowness_factor': op['duration'] / threshold
                })
        
        performance_analysis['slow_operations'] = sorted(
            slow_ops, key=lambda x: x['slowness_factor'], reverse=True
        )[:20]
        
        # 컴포넌트별 통계
        component_stats = defaultdict(lambda: {
            'count': 0, 'total_time': 0, 'avg_time': 0, 
            'max_time': 0, 'min_time': float('inf')
        })
        
        for op in all_operations:
            comp_stats = component_stats[op['component']]
            comp_stats['count'] += 1
            comp_stats['total_time'] += op['duration']
            comp_stats['max_time'] = max(comp_stats['max_time'], op['duration'])
            comp_stats['min_time'] = min(comp_stats['min_time'], op['duration'])
        
        for comp, stats in component_stats.items():
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                if stats['min_time'] == float('inf'):
                    stats['min_time'] = 0
        
        performance_analysis['component_stats'] = dict(component_stats)
        
        return performance_analysis
    
    def _categorize_operation(self, operation: str) -> str:
        """작업 유형 분류"""
        operation_lower = operation.lower()
        
        if any(term in operation_lower for term in ['api', 'request', 'call', 'fetch']):
            return 'api_call'
        elif any(term in operation_lower for term in ['process', 'transform', 'clean', 'parse']):
            return 'data_processing'
        elif any(term in operation_lower for term in ['select', 'insert', 'update', 'delete', 'query']):
            return 'database_operation'
        elif any(term in operation_lower for term in ['read', 'write', 'save', 'load', 'file']):
            return 'file_operation'
        elif any(term in operation_lower for term in ['validate', 'check', 'verify']):
            return 'validation'
        else:
            return 'other'
    
    def generate_health_report(self) -> Dict[str, Any]:
        """시스템 건강 상태 리포트 생성"""
        error_analysis = self.analyze_error_logs(24)
        perf_analysis = self.analyze_performance_logs(24)
        
        # 건강 점수 계산 (100점 만점)
        health_score = 100
        issues = []
        recommendations = []
        
        # 에러 점수 (최대 40점 감점)
        error_rate = error_analysis['total_errors']
        if error_rate > 100:
            health_score -= 40
            issues.append('high_error_rate')
            recommendations.append("에러 발생률이 매우 높습니다. 로그를 점검하고 근본 원인을 파악하세요.")
        elif error_rate > 50:
            health_score -= 25
            issues.append('moderate_error_rate')
            recommendations.append("에러 발생률이 증가했습니다. 시스템 상태를 점검하세요.")
        elif error_rate > 20:
            health_score -= 10
            issues.append('some_errors')
        
        # 심각한 에러 (최대 30점 감점)
        critical_count = len(error_analysis['critical_errors'])
        if critical_count > 5:
            health_score -= 30
            issues.append('critical_errors')
            recommendations.append("심각한 에러가 다수 발견되었습니다. 즉시 조치가 필요합니다.")
        elif critical_count > 0:
            health_score -= 15
            issues.append('some_critical_errors')
            recommendations.append("심각한 에러가 발견되었습니다. 확인이 필요합니다.")
        
        # 성능 점수 (최대 30점 감점)
        slow_ops = len(perf_analysis['slow_operations'])
        if slow_ops > 20:
            health_score -= 30
            issues.append('performance_issues')
            recommendations.append("성능 저하가 감지되었습니다. 느린 작업들을 최적화하세요.")
        elif slow_ops > 10:
            health_score -= 15
            issues.append('some_slow_operations')
            recommendations.append("일부 작업의 성능이 저하되었습니다.")
        
        # 트렌드 분석
        if error_analysis['error_trend'] == 'increasing':
            health_score -= 10
            issues.append('error_trend_increasing')
            recommendations.append("에러 발생률이 증가하는 추세입니다. 모니터링을 강화하세요.")
        
        # 건강 등급
        if health_score >= 90:
            grade = "🟢 Excellent"
        elif health_score >= 80:
            grade = "🟡 Good"
        elif health_score >= 70:
            grade = "🟠 Fair"
        elif health_score >= 60:
            grade = "🟠 Poor"
        else:
            grade = "🔴 Critical"
        
        # 기본 권장사항
        if not recommendations:
            recommendations.append("시스템이 정상적으로 운영되고 있습니다.")
        
        # 가장 빈번한 에러 유형 기반 권장사항
        if error_analysis['error_types']:
            top_error = list(error_analysis['error_types'].keys())[0]
            if top_error == 'connection_error':
                recommendations.append("연결 오류가 빈번합니다. 네트워크 상태와 외부 서비스를 점검하세요.")
            elif top_error == 'timeout_error':
                recommendations.append("타임아웃 오류가 많습니다. 요청 시간 제한을 조정하거나 성능을 개선하세요.")
            elif top_error == 'validation_error':
                recommendations.append("데이터 검증 오류가 많습니다. 입력 데이터 품질을 확인하세요.")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': max(0, health_score),
            'grade': grade,
            'issues': issues,
            'recommendations': recommendations,
            'error_summary': {
                'total_errors': error_analysis['total_errors'],
                'critical_errors': critical_count,
                'top_error_types': list(error_analysis['error_types'].keys())[:3],
                'error_trend': error_analysis['error_trend']
            },
            'performance_summary': {
                'total_operations': perf_analysis['total_operations'],
                'slow_operations': slow_ops,
                'slowest_component': max(
                    perf_analysis['component_stats'].items(),
                    key=lambda x: x[1]['avg_time'],
                    default=('none', {'avg_time': 0})
                )[0]
            }
        }
    
    def analyze_api_usage(self, hours: int = 24) -> Dict[str, Any]:
        """API 사용 패턴 분석"""
        since = datetime.now() - timedelta(hours=hours)
        api_files = list(self.log_dir.glob('app/api_calls.log')) + list(self.log_dir.glob('app/*.log'))
        
        api_analysis = {
            'analysis_period': f'Last {hours} hours',
            'total_api_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'api_endpoints': {},
            'response_times': [],
            'error_rates': {}
        }
        
        for log_file in api_files:
            try:
                if not log_file.exists():
                    continue
                    
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        # API 호출 패턴 매칭
                        api_match = re.search(
                            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*?API Call (\w+) (succeeded|failed).*?in ([\d\.]+)s',
                            line
                        )
                        
                        if api_match:
                            timestamp_str, endpoint, status, duration_str = api_match.groups()
                            try:
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                if log_time < since:
                                    continue
                            except ValueError:
                                continue
                            
                            api_analysis['total_api_calls'] += 1
                            
                            if status == 'succeeded':
                                api_analysis['successful_calls'] += 1
                            else:
                                api_analysis['failed_calls'] += 1
                            
                            # 엔드포인트별 통계
                            if endpoint not in api_analysis['api_endpoints']:
                                api_analysis['api_endpoints'][endpoint] = {
                                    'total': 0, 'success': 0, 'failed': 0, 'avg_response_time': 0
                                }
                            
                            api_analysis['api_endpoints'][endpoint]['total'] += 1
                            if status == 'succeeded':
                                api_analysis['api_endpoints'][endpoint]['success'] += 1
                            else:
                                api_analysis['api_endpoints'][endpoint]['failed'] += 1
                            
                            try:
                                duration = float(duration_str)
                                api_analysis['response_times'].append(duration)
                            except ValueError:
                                pass
            
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
                continue
        
        # 통계 계산
        if api_analysis['total_api_calls'] > 0:
            api_analysis['success_rate'] = (api_analysis['successful_calls'] / api_analysis['total_api_calls']) * 100
        else:
            api_analysis['success_rate'] = 0
        
        if api_analysis['response_times']:
            api_analysis['avg_response_time'] = np.mean(api_analysis['response_times'])
            api_analysis['median_response_time'] = np.median(api_analysis['response_times'])
            api_analysis['p95_response_time'] = np.percentile(api_analysis['response_times'], 95)
        
        return api_analysis

def generate_daily_log_report():
    """일일 로그 리포트 생성"""
    analyzer = LogAnalyzer()
    
    print("로그 분석 중...")
    
    # 건강 상태 리포트 생성
    health_report = analyzer.generate_health_report()
    
    # 상세 분석
    error_analysis = analyzer.analyze_error_logs(24)
    perf_analysis = analyzer.analyze_performance_logs(24)
    api_analysis = analyzer.analyze_api_usage(24)
    
    # 리포트 파일 저장
    report_dir = Path('logs/reports')
    report_dir.mkdir(exist_ok=True, parents=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    report_file = report_dir / f'daily_log_report_{date_str}.json'
    
    full_report = {
        'report_date': date_str,
        'generation_time': datetime.now().isoformat(),
        'health_report': health_report,
        'error_analysis': error_analysis,
        'performance_analysis': perf_analysis,
        'api_analysis': api_analysis
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2, default=str)
    
    # 콘솔 출력
    print("\n" + "="*60)
    print(f"📊 일일 로그 분석 리포트 ({date_str})")
    print("="*60)
    print(f"🏥 시스템 건강도: {health_report['grade']} ({health_report['health_score']}/100)")
    print(f"❌ 총 에러 수: {error_analysis['total_errors']}")
    print(f"🚨 심각한 에러: {len(error_analysis['critical_errors'])}")
    print(f"⚡ 총 작업 수: {perf_analysis['total_operations']}")
    print(f"🐌 느린 작업 수: {len(perf_analysis['slow_operations'])}")
    print(f"🌐 API 호출 수: {api_analysis['total_api_calls']}")
    print(f"✅ API 성공률: {api_analysis.get('success_rate', 0):.1f}%")
    
    print(f"\n📋 주요 권장사항:")
    for i, rec in enumerate(health_report['recommendations'][:3], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n📁 상세 리포트: {report_file}")
    print("="*60)
    
    return full_report

if __name__ == "__main__":
    generate_daily_log_report()

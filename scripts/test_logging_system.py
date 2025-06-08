#!/usr/bin/env python3
"""
로깅 시스템 종합 테스트 스크립트
모든 로깅 컴포넌트의 기능을 검증하고 성능을 측정
"""

import sys
import time
import random
import json
from pathlib import Path
from datetime import datetime
import traceback

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

from logging_system.log_manager import get_logger, log_performance
from logging_system.decorators import log_execution, LogContext, log_api_call
from logging_system.analyzers.log_analyzer import LogAnalyzer

class LoggingSystemTester:
    """로깅 시스템 테스터"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
        
        # 테스트용 로거들
        self.api_logger = get_logger('test_api', 'test_api.log')
        self.data_logger = get_logger('test_data', 'test_data.log')
        self.system_logger = get_logger('test_system', 'test_system.log')
    
    def run_test(self, test_name, test_func):
        """개별 테스트 실행"""
        self.test_results['tests_run'] += 1
        start_time = time.time()
        
        try:
            print(f"🧪 {test_name} 테스트 실행 중...")
            test_func()
            
            duration = time.time() - start_time
            self.test_results['tests_passed'] += 1
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'PASSED',
                'duration': duration,
                'error': None
            })
            print(f"✅ {test_name} 테스트 성공 ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results['tests_failed'] += 1
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'FAILED',
                'duration': duration,
                'error': str(e)
            })
            print(f"❌ {test_name} 테스트 실패: {e}")
            print(f"   스택 트레이스: {traceback.format_exc()}")
    
    @log_execution('test', log_args=True, log_result=True)
    def test_function_logging(self, param1, param2=None):
        """함수 로깅 데코레이터 테스트"""
        time.sleep(0.1)  # 시뮬레이션
        result = f"Result: {param1} + {param2}"
        return result
    
    def test_context_logging(self):
        """컨텍스트 로깅 테스트"""
        with LogContext('test', 'context_operation') as ctx:
            ctx.add_metadata('test_data', 'sample')
            ctx.log_info("Context operation started")
            
            time.sleep(0.2)
            
            ctx.add_metadata('processed_items', 100)
            ctx.log_info("Processing completed")
            
            # 의도적으로 성공적인 완료
            return "Context test completed"
    
    def test_error_logging(self):
        """에러 로깅 테스트"""
        try:
            # 의도적 에러 발생
            result = 1 / 0
        except ZeroDivisionError as e:
            self.api_logger.error(f"Test error occurred: {e}")
            self.api_logger.critical("This is a critical test error for demonstration")
        
        # 다양한 에러 유형 시뮬레이션
        self.api_logger.error("ConnectionError: Failed to connect to TMDB API")
        self.api_logger.error("TimeoutError: Request timed out after 30 seconds")
        self.api_logger.error("ValidationError: Invalid movie data format")
    
    def test_performance_logging(self):
        """성능 로깅 테스트"""
        operations = [
            ('data_processing', 0.5, 2.0),
            ('api_call', 0.1, 1.0),
            ('database_query', 0.2, 0.8),
            ('file_operation', 0.05, 0.3),
            ('validation', 0.3, 1.5)
        ]
        
        for operation, min_time, max_time in operations:
            # 랜덤 실행 시간 시뮬레이션
            duration = random.uniform(min_time, max_time)
            time.sleep(duration)
            
            metadata = {
                'records_processed': random.randint(100, 1000),
                'memory_used_mb': random.randint(50, 500),
                'cpu_usage_percent': random.randint(10, 80)
            }
            
            log_performance('test', operation, duration, metadata)
    
    @log_api_call('test_endpoint', log_request=True, log_response=True)
    def simulate_api_call(self, endpoint, params=None, timeout=30):
        """API 호출 시뮬레이션"""
        # 랜덤 응답 시간
        response_time = random.uniform(0.1, 2.0)
        time.sleep(response_time)
        
        # 랜덤 성공/실패
        if random.random() < 0.8:  # 80% 성공률
            return {
                'status': 'success',
                'data': {'movies': [{'id': i} for i in range(20)]},
                'response_time': response_time
            }
        else:
            raise Exception("API call failed: Rate limit exceeded")
    
    def test_api_simulation(self):
        """API 호출 시뮬레이션 테스트"""
        scenarios = [
            ('get_popular_movies', {'page': 1}),
            ('get_movie_details', {'movie_id': 123}),
            ('search_movies', {'query': 'action'}),
            ('get_trending', {'time_window': 'day'}),
            ('get_genres', {})
        ]
        
        for endpoint, params in scenarios:
            try:
                result = self.simulate_api_call(endpoint, params)
                self.api_logger.info(f"API call to {endpoint} succeeded")
            except Exception as e:
                self.api_logger.error(f"API call to {endpoint} failed: {e}")
    
    def test_data_quality_simulation(self):
        """데이터 품질 검증 시뮬레이션"""
        with LogContext('data_quality', 'batch_validation') as ctx:
            total_records = 1000
            valid_records = random.randint(800, 950)
            
            ctx.add_metadata('total_records', total_records)
            ctx.add_metadata('valid_records', valid_records)
            ctx.add_metadata('validation_rate', valid_records / total_records * 100)
            
            ctx.log_info(f"Validating {total_records} records")
            
            # 시뮬레이션 진행
            for i in range(0, total_records, 100):
                time.sleep(0.02)
                progress = min(i + 100, total_records)
                ctx.log_info(f"Processed {progress}/{total_records} records")
            
            validation_rate = valid_records / total_records * 100
            if validation_rate < 85:
                self.data_logger.warning(f"Low validation rate: {validation_rate:.1f}%")
            
            ctx.log_info(f"Validation completed: {validation_rate:.1f}% valid")
    
    def test_bulk_logging(self):
        """대량 로깅 성능 테스트"""
        start_time = time.time()
        
        # 1000개의 로그 메시지 생성
        for i in range(1000):
            if i % 100 == 0:
                self.system_logger.info(f"Bulk logging progress: {i}/1000")
            
            # 다양한 레벨의 로그
            level = random.choice(['debug', 'info', 'warning', 'error'])
            message = f"Bulk log message {i}: {random.choice(['processing', 'validating', 'saving', 'loading'])} data"
            
            if level == 'debug':
                self.system_logger.debug(message)
            elif level == 'info':
                self.system_logger.info(message)
            elif level == 'warning':
                self.system_logger.warning(message)
            elif level == 'error':
                self.system_logger.error(message)
        
        duration = time.time() - start_time
        throughput = 1000 / duration
        
        self.system_logger.info(f"Bulk logging completed: {throughput:.1f} messages/second")
        print(f"📊 대량 로깅 성능: {throughput:.1f} 메시지/초")
    
    def test_log_analyzer(self):
        """로그 분석기 테스트"""
        analyzer = LogAnalyzer()
        
        # 에러 분석 테스트
        error_analysis = analyzer.analyze_error_logs(1)  # 최근 1시간
        assert 'total_errors' in error_analysis
        
        # 성능 분석 테스트
        perf_analysis = analyzer.analyze_performance_logs(1)
        assert 'total_operations' in perf_analysis
        
        # 건강도 리포트 테스트
        health_report = analyzer.generate_health_report()
        assert 'health_score' in health_report
        assert 0 <= health_report['health_score'] <= 100
        
        print(f"📊 분석 결과: 에러 {error_analysis['total_errors']}개, "
              f"작업 {perf_analysis['total_operations']}개, "
              f"건강도 {health_report['health_score']}/100")
    
    def test_log_file_creation(self):
        """로그 파일 생성 확인"""
        log_files = [
            'logs/app/test_api.log',
            'logs/app/test_data.log',
            'logs/app/test_system.log',
            'logs/performance/test_performance.log'
        ]
        
        for log_file in log_files:
            file_path = Path(log_file)
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"📁 {log_file}: {size} bytes")
            else:
                print(f"⚠️ {log_file}: 파일이 생성되지 않았습니다")
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("\n" + "="*60)
        print("🧪 로깅 시스템 종합 테스트 시작")
        print("="*60)
        
        # 모든 테스트 실행
        test_cases = [
            ("함수 로깅 데코레이터", lambda: self.test_function_logging("test_param1", param2="test_param2")),
            ("컨텍스트 로깅", self.test_context_logging),
            ("에러 로깅", self.test_error_logging),
            ("성능 로깅", self.test_performance_logging),
            ("API 시뮬레이션", self.test_api_simulation),
            ("데이터 품질 시뮬레이션", self.test_data_quality_simulation),
            ("대량 로깅 성능", self.test_bulk_logging),
            ("로그 분석기", self.test_log_analyzer),
            ("로그 파일 생성", self.test_log_file_creation)
        ]
        
        for test_name, test_func in test_cases:
            self.run_test(test_name, test_func)
            time.sleep(0.1)  # 테스트 간 간격
        
        # 테스트 결과 요약
        self.test_results['end_time'] = datetime.now().isoformat()
        duration = time.time() - time.mktime(
            datetime.fromisoformat(self.test_results['start_time']).timetuple()
        )
        self.test_results['total_duration'] = duration
        
        print("\n" + "="*60)
        print("📊 테스트 결과 요약")
        print("="*60)
        print(f"총 테스트: {self.test_results['tests_run']}")
        print(f"성공: {self.test_results['tests_passed']}")
        print(f"실패: {self.test_results['tests_failed']}")
        print(f"성공률: {(self.test_results['tests_passed'] / self.test_results['tests_run'] * 100):.1f}%")
        print(f"총 실행 시간: {duration:.2f}초")
        
        if self.test_results['tests_failed'] > 0:
            print(f"\n❌ 실패한 테스트:")
            for test in self.test_results['test_details']:
                if test['status'] == 'FAILED':
                    print(f"  - {test['name']}: {test['error']}")
        
        print(f"\n📁 로그 파일 위치:")
        print(f"  - 애플리케이션: logs/app/")
        print(f"  - 에러: logs/error/")
        print(f"  - 성능: logs/performance/")
        print(f"  - 분석 결과: logs/reports/")
        
        # 테스트 결과 저장
        result_file = Path('logs/reports/logging_test_results.json')
        result_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📋 상세 테스트 결과: {result_file}")
        print("="*60)
        
        return self.test_results

def run_quick_test():
    """빠른 테스트 실행"""
    print("⚡ 빠른 로깅 테스트 실행 중...")
    
    # 기본 로거 테스트
    logger = get_logger('quick_test', 'quick_test.log')
    logger.info("Quick test started")
    logger.warning("This is a test warning")
    logger.error("This is a test error")
    
    # 성능 로깅 테스트
    start_time = time.time()
    time.sleep(0.1)
    log_performance('quick_test', 'test_operation', time.time() - start_time)
    
    print("✅ 빠른 테스트 완료")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='로깅 시스템 테스트')
    parser.add_argument('--quick', action='store_true', help='빠른 테스트만 실행')
    parser.add_argument('--comprehensive', action='store_true', help='종합 테스트 실행')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    elif args.comprehensive or len(sys.argv) == 1:
        tester = LoggingSystemTester()
        tester.run_comprehensive_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

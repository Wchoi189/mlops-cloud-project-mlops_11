# src/logging_system/decorators.py
"""
로깅 데코레이터 (테스트용 간소화 버전)
"""

import functools
import time
import logging
from .log_manager import get_logger, log_performance

class LogContext:
    """로그 컨텍스트 관리"""
    
    def __init__(self, component: str, operation: str, log_file: str = None):
        self.component = component
        self.operation = operation
        self.logger = get_logger(component, log_file)
        self.start_time = None
        self.metadata = {}
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"{self.operation} started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            self.logger.info(f"{self.operation} completed successfully in {duration:.3f}s")
            log_performance(self.component, self.operation, duration, self.metadata)
        else:
            self.logger.error(f"{self.operation} failed after {duration:.3f}s: {str(exc_val)}")
    
    def add_metadata(self, key: str, value):
        """메타데이터 추가"""
        self.metadata[key] = value
    
    def log_info(self, message: str):
        """컨텍스트 내 정보 로그"""
        self.logger.info(f"{self.operation} | {message}")

def log_execution(component: str = None, log_file: str = None, 
                 level: str = 'INFO', log_args: bool = False, 
                 log_result: bool = False):
    """함수 실행 로깅 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            comp_name = component or func.__module__.split('.')[-1]
            logger = get_logger(comp_name, log_file, level)
            
            start_time = time.time()
            func_name = func.__name__
            
            logger.info(f"Starting {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Completed {func_name} in {duration:.3f}s")
                log_performance(comp_name, func_name, duration)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed {func_name} after {duration:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_data_quality(component: str):
    """데이터 품질 로깅 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('data_quality', 'data_quality.log')
            
            start_time = time.time()
            func_name = func.__name__
            
            logger.info(f"Data quality check started: {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 품질 결과 로깅
                if isinstance(result, dict) and 'valid_movies' in result:
                    total = result.get('total_movies', 0)
                    valid = result.get('valid_movies', 0)
                    rate = (valid / total * 100) if total > 0 else 0
                    logger.info(f"Data quality check completed: {rate:.1f}% valid rate")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Data quality check failed: {str(e)}")
                raise
        
        return wrapper
    return decorator

# src/logging_system/log_manager.py
"""
간단한 로깅 매니저 (테스트용)
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# 전역 로거 인스턴스
_loggers = {}

def get_logger(name: str, log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """로거 인스턴스 반환"""
    logger_key = f"{name}_{log_file or 'default'}"
    
    if logger_key in _loggers:
        return _loggers[logger_key]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        log_dir = Path('logs/app')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_dir / log_file),
            maxBytes=10485760,
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter(
                '[%(asctime)s] %(levelname)-8s %(name)-15s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        logger.addHandler(file_handler)
    
    _loggers[logger_key] = logger
    return logger

def log_performance(component: str, operation: str, duration: float, metadata: dict = None):
    """성능 로그 기록"""
    perf_logger = logging.getLogger(f'performance.{component}')
    
    if not perf_logger.handlers:
        log_dir = Path('logs/performance')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            str(log_dir / f'{component}_performance.log'),
            maxBytes=10485760,
            backupCount=3
        )
        handler.setFormatter(
            logging.Formatter(
                '[%(asctime)s] PERF %(name)-15s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        perf_logger.addHandler(handler)
        perf_logger.setLevel(logging.INFO)
    
    message = f"{operation} completed in {duration:.3f}s"
    if metadata:
        import json
        message += f" | {json.dumps(metadata, default=str)}"
    
    perf_logger.info(message)

# MovieMLOpsLogger 초기화 메시지
logger = get_logger('system', 'system.log')
logger.info("MovieMLOps 로깅 시스템 초기화 완료")

import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from functools import wraps
import queue

@dataclass
class RateLimitConfig:
    """Rate Limit 설정"""
    requests_per_second: float = 4.0  # TMDB는 초당 최대 40회, 안전하게 4회로 설정
    requests_per_minute: int = 200    # 분당 최대 요청 수
    requests_per_hour: int = 10000    # 시간당 최대 요청 수
    burst_allowance: int = 10         # 버스트 허용량
    cooldown_period: float = 60.0     # 제한 발생 시 대기 시간 (초)

class RateLimiter:
    """
    Rate Limiting 관리 클래스
    
    Features:
    - 토큰 버킷 알고리즘
    - 계층적 제한 (초/분/시간)
    - 자동 복구
    - 통계 추적
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Rate Limiter 초기화
        
        Args:
            config: Rate Limit 설정
        """
        self.config = config or RateLimitConfig()
        self.logger = logging.getLogger(__name__)
        
        # 토큰 버킷
        self.tokens = self.config.burst_allowance
        self.max_tokens = self.config.burst_allowance
        self.last_refill = time.time()
        
        # 요청 기록 (시간창 기반)
        self.requests_per_minute = queue.Queue()
        self.requests_per_hour = queue.Queue()
        
        # 통계
        self.total_requests = 0
        self.blocked_requests = 0
        self.last_request_time = 0
        
        # 스레드 안전성
        self.lock = threading.Lock()
        
        # 상태
        self.is_rate_limited = False
        self.rate_limit_until = 0
    
    def _refill_tokens(self):
        """토큰 버킷 리필"""
        now = time.time()
        time_passed = now - self.last_refill
        
        # 초당 요청 제한에 따라 토큰 추가
        tokens_to_add = time_passed * self.config.requests_per_second
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _clean_old_requests(self, request_queue: queue.Queue, window_seconds: int):
        """오래된 요청 기록 정리"""
        now = time.time()
        cutoff_time = now - window_seconds
        
        # 임시 리스트로 유효한 요청만 보관
        valid_requests = []
        while not request_queue.empty():
            try:
                request_time = request_queue.get_nowait()
                if request_time > cutoff_time:
                    valid_requests.append(request_time)
            except queue.Empty:
                break
        
        # 유효한 요청들을 다시 큐에 넣기
        for request_time in valid_requests:
            request_queue.put(request_time)
    
    def _check_time_windows(self) -> bool:
        """시간창 기반 제한 확인"""
        now = time.time()
        
        # 분당 요청 수 확인
        self._clean_old_requests(self.requests_per_minute, 60)
        if self.requests_per_minute.qsize() >= self.config.requests_per_minute:
            self.logger.warning("분당 요청 한도 초과")
            return False
        
        # 시간당 요청 수 확인
        self._clean_old_requests(self.requests_per_hour, 3600)
        if self.requests_per_hour.qsize() >= self.config.requests_per_hour:
            self.logger.warning("시간당 요청 한도 초과")
            return False
        
        return True
    
    def can_make_request(self) -> bool:
        """
        요청 허용 여부 확인
        
        Returns:
            요청 허용 여부
        """
        with self.lock:
            now = time.time()
            
            # Rate Limit 상태 확인
            if self.is_rate_limited and now < self.rate_limit_until:
                return False
            elif self.is_rate_limited and now >= self.rate_limit_until:
                self.is_rate_limited = False
                self.logger.info("Rate Limit 해제됨")
            
            # 토큰 리필
            self._refill_tokens()
            
            # 토큰 확인
            if self.tokens < 1:
                self.logger.debug("토큰 부족으로 요청 대기")
                return False
            
            # 시간창 제한 확인
            if not self._check_time_windows():
                return False
            
            return True
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        요청 허가 획득 (블로킹)
        
        Args:
            timeout: 최대 대기 시간 (초)
            
        Returns:
            획득 성공 여부
        """
        start_time = time.time()
        
        while True:
            if self.can_make_request():
                with self.lock:
                    # 토큰 소비
                    self.tokens -= 1
                    
                    # 요청 기록
                    now = time.time()
                    self.requests_per_minute.put(now)
                    self.requests_per_hour.put(now)
                    self.total_requests += 1
                    self.last_request_time = now
                    
                    self.logger.debug(f"요청 허가 - 남은 토큰: {self.tokens:.2f}")
                    return True
            
            # 타임아웃 확인
            if timeout and (time.time() - start_time) > timeout:
                with self.lock:
                    self.blocked_requests += 1
                self.logger.warning("요청 획득 타임아웃")
                return False
            
            # 짧은 대기
            time.sleep(0.1)
    
    def set_rate_limited(self, duration: Optional[float] = None):
        """
        Rate Limit 상태 설정
        
        Args:
            duration: 제한 지속 시간 (초)
        """
        with self.lock:
            duration = duration or self.config.cooldown_period
            self.is_rate_limited = True
            self.rate_limit_until = time.time() + duration
            self.logger.warning(f"Rate Limit 설정됨 - {duration}초간 대기")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        통계 정보 반환
        
        Returns:
            통계 딕셔너리
        """
        with self.lock:
            now = time.time()
            
            # 현재 시간창별 요청 수 계산
            self._clean_old_requests(self.requests_per_minute, 60)
            self._clean_old_requests(self.requests_per_hour, 3600)
            
            return {
                'total_requests': self.total_requests,
                'blocked_requests': self.blocked_requests,
                'success_rate': (self.total_requests - self.blocked_requests) / max(1, self.total_requests),
                'current_tokens': round(self.tokens, 2),
                'max_tokens': self.max_tokens,
                'requests_last_minute': self.requests_per_minute.qsize(),
                'requests_last_hour': self.requests_per_hour.qsize(),
                'is_rate_limited': self.is_rate_limited,
                'rate_limit_until': datetime.fromtimestamp(self.rate_limit_until) if self.is_rate_limited else None,
                'last_request_time': datetime.fromtimestamp(self.last_request_time) if self.last_request_time else None,
                'config': {
                    'requests_per_second': self.config.requests_per_second,
                    'requests_per_minute': self.config.requests_per_minute,
                    'requests_per_hour': self.config.requests_per_hour
                }
            }
    
    def reset(self):
        """Rate Limiter 재설정"""
        with self.lock:
            self.tokens = self.max_tokens
            self.last_refill = time.time()
            
            # 큐 비우기
            while not self.requests_per_minute.empty():
                try:
                    self.requests_per_minute.get_nowait()
                except queue.Empty:
                    break
            
            while not self.requests_per_hour.empty():
                try:
                    self.requests_per_hour.get_nowait()
                except queue.Empty:
                    break
            
            # 상태 초기화
            self.is_rate_limited = False
            self.rate_limit_until = 0
            
            self.logger.info("Rate Limiter 재설정 완료")

class RateLimitDecorator:
    """Rate Limiting 데코레이터"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 요청 허가 획득
            if not self.rate_limiter.acquire(timeout=30):
                raise Exception("Rate Limit으로 인한 요청 실패")
            
            try:
                # 원본 함수 실행
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                # HTTP 429 에러 처리
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    if e.response.status_code == 429:
                        self.rate_limiter.set_rate_limited()
                        self.logger.warning("HTTP 429 에러로 인한 Rate Limit 설정")
                raise
        
        return wrapper

# 전역 Rate Limiter 인스턴스
default_rate_limiter = RateLimiter()

def rate_limited(rate_limiter: Optional[RateLimiter] = None):
    """
    Rate Limiting 데코레이터 팩토리
    
    Args:
        rate_limiter: 사용할 Rate Limiter (기본값: 전역 인스턴스)
        
    Returns:
        데코레이터 함수
    """
    limiter = rate_limiter or default_rate_limiter
    return RateLimitDecorator(limiter)

def wait_for_rate_limit_reset(rate_limiter: Optional[RateLimiter] = None):
    """
    Rate Limit 해제까지 대기
    
    Args:
        rate_limiter: 사용할 Rate Limiter
    """
    limiter = rate_limiter or default_rate_limiter
    
    if limiter.is_rate_limited:
        wait_time = limiter.rate_limit_until - time.time()
        if wait_time > 0:
            limiter.logger.info(f"Rate Limit 해제까지 {wait_time:.1f}초 대기")
            time.sleep(wait_time)

def get_rate_limit_stats(rate_limiter: Optional[RateLimiter] = None) -> Dict[str, Any]:
    """
    Rate Limit 통계 조회
    
    Args:
        rate_limiter: 사용할 Rate Limiter
        
    Returns:
        통계 정보
    """
    limiter = rate_limiter or default_rate_limiter
    return limiter.get_stats()

# 사용 예제
if __name__ == "__main__":
    # Rate Limiter 테스트
    config = RateLimitConfig(requests_per_second=2.0)
    limiter = RateLimiter(config)
    
    @rate_limited(limiter)
    def test_api_call():
        print(f"API 호출 - {datetime.now()}")
        return "성공"
    
    # 연속 호출 테스트
    for i in range(5):
        try:
            result = test_api_call()
            print(f"호출 {i+1}: {result}")
        except Exception as e:
            print(f"호출 {i+1} 실패: {e}")
    
    # 통계 출력
    stats = limiter.get_stats()
    print(f"통계: {stats}")

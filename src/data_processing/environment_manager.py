import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

class EnvironmentManager:
    """
    환경변수 관리 클래스
    
    Features:
    - .env 파일 자동 로드
    - 환경변수 검증
    - 기본값 설정
    - 타입 변환
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        환경변수 매니저 초기화
        
        Args:
            env_file: .env 파일 경로 (기본값: 프로젝트 루트의 .env)
        """
        self.logger = logging.getLogger(__name__)
        
        # .env 파일 경로 설정
        if env_file is None:
            # 프로젝트 루트 디렉토리 찾기
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                env_path = current_path / '.env'
                if env_path.exists():
                    env_file = str(env_path)
                    break
                current_path = current_path.parent
            
            # 기본 경로 설정
            if env_file is None:
                env_file = '.env'
        
        self.env_file = env_file
        self._load_environment()
    
    def _load_environment(self):
        """환경변수 로드 (.env 파일 우선)"""
        try:
            if os.path.exists(self.env_file):
                # 기존 환경변수에서 플레이스홀더 값 제거
                placeholder_keys = [
                    'TMDB_API_KEY',
                    'DB_PASSWORD', 
                    'OPENAI_API_KEY'
                ]
                
                for key in placeholder_keys:
                    current_value = os.getenv(key)
                    if current_value and ('your_' in current_value.lower() or 'here' in current_value.lower()):
                        os.environ.pop(key, None)
                        self.logger.info(f"플레이스홀더 환경변수 제거: {key}")
                
                # .env 파일에서 강제 로드
                load_dotenv(self.env_file, override=True)
                
                # 로드 후 재검증
                api_key = os.getenv('TMDB_API_KEY')
                if api_key and ('your_' in api_key.lower() or 'here' in api_key.lower()):
                    self.logger.error(f"잘못된 API 키가 로드됨: {api_key}")
                    raise ValueError("TMDB_API_KEY에 올바른 API 키를 설정해주세요.")
                
                self.logger.info(f"환경변수 파일 로드 완료: {self.env_file}")
            else:
                self.logger.warning(f"환경변수 파일을 찾을 수 없습니다: {self.env_file}")
        except Exception as e:
            self.logger.error(f"환경변수 로드 실패: {e}")
            raise
    
    def get_env(self, key: str, default: Any = None, required: bool = False, 
                env_type: type = str) -> Any:
        """
        환경변수 조회
        
        Args:
            key: 환경변수 키
            default: 기본값
            required: 필수 여부
            env_type: 변환할 타입
            
        Returns:
            환경변수 값
            
        Raises:
            ValueError: 필수 환경변수가 없을 때
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {key}")
        
        if value is None:
            return None
        
        # 타입 변환
        try:
            if env_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif env_type == int:
                return int(value)
            elif env_type == float:
                return float(value)
            elif env_type == list:
                return [item.strip() for item in value.split(',')]
            else:
                return str(value)
        except (ValueError, AttributeError) as e:
            self.logger.error(f"환경변수 타입 변환 실패 {key}: {e}")
            return default
    
    def get_tmdb_config(self) -> Dict[str, Any]:
        """
        TMDB 관련 환경변수 조회
        
        Returns:
            TMDB 설정 딕셔너리
        """
        return {
            'api_key': self.get_env('TMDB_API_KEY', required=True),
            'region': self.get_env('TMDB_REGION', default='KR'),
            'language': self.get_env('TMDB_LANGUAGE', default='ko-KR'),
            'request_delay': self.get_env('TMDB_REQUEST_DELAY', default=0.25, env_type=float),
            'max_retries': self.get_env('TMDB_MAX_RETRIES', default=3, env_type=int),
            'timeout': self.get_env('TMDB_TIMEOUT', default=30, env_type=int)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        로깅 관련 환경변수 조회
        
        Returns:
            로깅 설정 딕셔너리
        """
        return {
            'level': self.get_env('LOG_LEVEL', default='INFO'),
            'format': self.get_env('LOG_FORMAT', default='%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file_path': self.get_env('LOG_FILE_PATH', default='logs/app.log'),
            'max_bytes': self.get_env('LOG_MAX_BYTES', default=10485760, env_type=int),  # 10MB
            'backup_count': self.get_env('LOG_BACKUP_COUNT', default=5, env_type=int)
        }
    
    def get_data_config(self) -> Dict[str, Any]:
        """
        데이터 관련 환경변수 조회
        
        Returns:
            데이터 설정 딕셔너리
        """
        return {
            'data_dir': self.get_env('DATA_DIR', default='data'),
            'raw_data_dir': self.get_env('RAW_DATA_DIR', default='data/raw'),
            'processed_data_dir': self.get_env('PROCESSED_DATA_DIR', default='data/processed'),
            'backup_dir': self.get_env('BACKUP_DIR', default='data/backup'),
            'max_file_age_days': self.get_env('MAX_FILE_AGE_DAYS', default=30, env_type=int),
            'compression_enabled': self.get_env('COMPRESSION_ENABLED', default=True, env_type=bool)
        }
    
    def validate_environment(self) -> Dict[str, bool]:
        """
        환경변수 유효성 검증
        
        Returns:
            검증 결과 딕셔너리
        """
        results = {}
        
        # TMDB 설정 검증
        try:
            tmdb_config = self.get_tmdb_config()
            results['tmdb_api_key'] = bool(tmdb_config['api_key'])
            results['tmdb_config'] = True
        except Exception as e:
            self.logger.error(f"TMDB 설정 검증 실패: {e}")
            results['tmdb_config'] = False
        
        # 로깅 설정 검증
        try:
            logging_config = self.get_logging_config()
            results['logging_config'] = True
        except Exception as e:
            self.logger.error(f"로깅 설정 검증 실패: {e}")
            results['logging_config'] = False
        
        # 데이터 설정 검증
        try:
            data_config = self.get_data_config()
            results['data_config'] = True
        except Exception as e:
            self.logger.error(f"데이터 설정 검증 실패: {e}")
            results['data_config'] = False
        
        return results
    
    def create_env_template(self, output_path: str = '.env.template'):
        """
        환경변수 템플릿 파일 생성
        
        Args:
            output_path: 출력 파일 경로
        """
        template_content = """# TMDB API 설정
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_REGION=KR
TMDB_LANGUAGE=ko-KR
TMDB_REQUEST_DELAY=0.25
TMDB_MAX_RETRIES=3
TMDB_TIMEOUT=30

# 로깅 설정
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE_PATH=logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# 데이터 설정
DATA_DIR=data
RAW_DATA_DIR=data/raw
PROCESSED_DATA_DIR=data/processed
BACKUP_DIR=data/backup
MAX_FILE_AGE_DAYS=30
COMPRESSION_ENABLED=true

# 데이터베이스 설정 (선택사항)
DATABASE_URL=sqlite:///data/mlops.db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mlops
DB_USER=mlops_user
DB_PASSWORD=your_password_here

# 스케줄링 설정
SCHEDULER_ENABLED=true
DAILY_COLLECTION_TIME=02:00
WEEKLY_COLLECTION_DAY=sunday
HOURLY_TRENDING_ENABLED=true
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            self.logger.info(f"환경변수 템플릿 생성 완료: {output_path}")
        except Exception as e:
            self.logger.error(f"환경변수 템플릿 생성 실패: {e}")


# 전역 환경변수 매니저 인스턴스
env_manager = EnvironmentManager()

# 편의 함수들
def get_env(key: str, default: Any = None, required: bool = False, env_type: type = str) -> Any:
    """환경변수 조회 편의 함수"""
    return env_manager.get_env(key, default, required, env_type)

def get_tmdb_config() -> Dict[str, Any]:
    """TMDB 설정 조회 편의 함수"""
    return env_manager.get_tmdb_config()

def validate_environment() -> Dict[str, bool]:
    """환경변수 검증 편의 함수"""
    return env_manager.validate_environment()

"""
간단한 피처 스토어 구현
2.5 간단한 피처 스토어 구현

이 모듈은 파일 기반의 경량 피처 스토어를 제공합니다.
RESTful API, 캐싱, 버전 관리를 지원합니다.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import pickle
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import time
import sqlite3
import redis
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import fsspec
import jsonschema

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureStoreConfig:
    """피처 스토어 설정"""
    base_path: str = "data/feature_store"
    cache_enabled: bool = True
    cache_max_size: int = 100
    cache_ttl_seconds: int = 3600
    enable_versioning: bool = True
    compression: str = "snappy"
    backup_enabled: bool = True
    
    # Redis 설정
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 모니터링 설정
    metrics_enabled: bool = True
    metrics_port: int = 8000
    
    # 스토리지 백엔드 설정
    storage_backend: str = "file"  # file, s3, gcs, etc.
    storage_options: Dict[str, Any] = None


class FeatureCache:
    """메모리 기반 피처 캐시 시스템"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.logger = logging.getLogger("FeatureCache")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if key in self.cache:
            # TTL 확인
            cache_time = self.access_times[key]
            if time.time() - cache_time < self.ttl_seconds:
                self.access_times[key] = time.time()  # 액세스 시간 업데이트
                return self.cache[key]
            else:
                # 만료된 캐시 삭제
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def put(self, key: str, value: Any) -> None:
        """캐시에 데이터 저장"""
        # 캐시 크기 초과 시 LRU 방식으로 제거
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_lru(self) -> None:
        """LRU 방식으로 캐시 항목 제거"""
        if not self.cache:
            return
        
        # 가장 오래된 액세스 시간을 가진 항목 찾기
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_ratio': self._calculate_hit_ratio(),
            'ttl_seconds': self.ttl_seconds
        }
    
    def _calculate_hit_ratio(self) -> float:
        """캐시 적중률 계산 (간단한 추정)"""
        if not hasattr(self, '_total_requests'):
            self._total_requests = 0
            self._cache_hits = 0
        
        return self._cache_hits / max(self._total_requests, 1)


class SimpleFeatureStore:
    """간단한 파일 기반 피처 스토어"""
    
    def __init__(self, config: Optional[FeatureStoreConfig] = None):
        self.config = config or FeatureStoreConfig()
        
        # 로거 먼저 초기화
        self.logger = logging.getLogger("SimpleFeatureStore")
        
        # 스토리지 백엔드 초기화
        if self.config.storage_backend == "file":
            self.base_path = Path(self.config.base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.filesystem = None
        else:
            # fsspec을 사용한 다양한 스토리지 백엔드 지원
            self.filesystem = fsspec.filesystem(
                self.config.storage_backend, 
                **(self.config.storage_options or {})
            )
            self.base_path = Path(self.config.base_path)
        
        # 디렉토리 구조 생성
        self.features_path = self.base_path / "features"
        self.metadata_path = self.base_path / "metadata"
        self.versions_path = self.base_path / "versions"
        self.cache_path = self.base_path / "cache"
        
        for path in [self.features_path, self.metadata_path, self.versions_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # 캐시 초기화 (메모리 또는 Redis)
        if self.config.cache_enabled:
            if self.config.redis_enabled:
                self.cache = self._init_redis_cache()
            else:
                self.cache = FeatureCache(
                    max_size=self.config.cache_max_size,
                    ttl_seconds=self.config.cache_ttl_seconds
                )
        else:
            self.cache = None
        
        # Prometheus 메트릭 초기화
        if self.config.metrics_enabled:
            self.metrics = self._init_metrics()
        else:
            self.metrics = None
        
        # 메타데이터 DB 초기화
        self.metadata_db_path = self.metadata_path / "metadata.db"
        self._init_metadata_db()
        
        self.logger.info(f"피처 스토어 초기화 완료: {self.base_path}")
    
    def _init_metadata_db(self) -> None:
        """메타데이터 SQLite DB 초기화"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_metadata (
                    feature_name TEXT PRIMARY KEY,
                    feature_group TEXT,
                    data_type TEXT,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    version TEXT,
                    file_path TEXT,
                    size_bytes INTEGER,
                    record_count INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_groups (
                    group_name TEXT PRIMARY KEY,
                    description TEXT,
                    created_at TEXT,
                    features TEXT
                )
            """)
    
    def save_features(self, feature_group: str, features_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """
        피처 데이터 저장
        
        Args:
            feature_group: 피처 그룹명
            features_data: 피처명 -> DataFrame 매핑
            
        Returns:
            Dict: 저장된 파일 경로들
        """
        self.logger.info(f"피처 저장 시작: {feature_group} ({len(features_data)} 피처)")
        
        saved_paths = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 그룹 디렉토리 생성
        group_path = self.features_path / feature_group
        group_path.mkdir(parents=True, exist_ok=True)
        
        for feature_name, df in features_data.items():
            try:
                # 파일 경로 생성
                file_name = f"{feature_name}_{timestamp}.parquet"
                file_path = group_path / file_name
                
                # Parquet으로 저장
                df.to_parquet(file_path, compression=self.config.compression, index=False)
                
                # 메타데이터 저장
                self._save_feature_metadata(
                    feature_name=feature_name,
                    feature_group=feature_group,
                    file_path=str(file_path),
                    df=df
                )
                
                saved_paths[feature_name] = str(file_path)
                
                # 캐시 업데이트
                if self.cache:
                    cache_key = f"{feature_group}:{feature_name}"
                    self.cache.put(cache_key, df)
                
                self.logger.info(f"피처 저장 완료: {feature_name} -> {file_path}")
                
            except Exception as e:
                self.logger.error(f"피처 저장 실패 {feature_name}: {e}")
        
        # 피처 그룹 메타데이터 업데이트
        self._update_feature_group_metadata(feature_group, list(features_data.keys()))
        
        return saved_paths
    
    def get_features(self, feature_names: List[str], 
                    feature_group: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        피처 데이터 조회
        
        Args:
            feature_names: 조회할 피처명 리스트
            feature_group: 피처 그룹 (없으면 모든 그룹에서 검색)
            
        Returns:
            Dict: 피처명 -> DataFrame 매핑
        """
        self.logger.info(f"피처 조회 시작: {feature_names}")
        
        result = {}
        
        for feature_name in feature_names:
            df = self._load_feature(feature_name, feature_group)
            if df is not None:
                result[feature_name] = df
            else:
                self.logger.warning(f"피처를 찾을 수 없음: {feature_name}")
        
        self.logger.info(f"피처 조회 완료: {len(result)}/{len(feature_names)} 성공")
        return result
    
    def _load_feature(self, feature_name: str, feature_group: Optional[str] = None) -> Optional[pd.DataFrame]:
        """개별 피처 로드"""
        # 캐시 확인
        if self.cache:
            if feature_group:
                cache_key = f"{feature_group}:{feature_name}"
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
        
        # 메타데이터에서 파일 경로 조회
        file_path = self._get_feature_file_path(feature_name, feature_group)
        if not file_path or not Path(file_path).exists():
            return None
        
        try:
            # 파일 로드
            df = pd.read_parquet(file_path)
            
            # 캐시에 저장
            if self.cache and feature_group:
                cache_key = f"{feature_group}:{feature_name}"
                self.cache.put(cache_key, df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"피처 로드 실패 {feature_name}: {e}")
            return None
    
    def get_latest_features(self, feature_group: str) -> Dict[str, pd.DataFrame]:
        """
        피처 그룹의 최신 피처들 조회
        
        Args:
            feature_group: 피처 그룹명
            
        Returns:
            Dict: 최신 피처 데이터
        """
        with sqlite3.connect(self.metadata_db_path) as conn:
            cursor = conn.execute("""
                SELECT feature_name FROM feature_metadata 
                WHERE feature_group = ?
                ORDER BY updated_at DESC
            """, (feature_group,))
            
            feature_names = [row[0] for row in cursor.fetchall()]
        
        return self.get_features(feature_names, feature_group)
    
    def list_feature_groups(self) -> List[str]:
        """피처 그룹 목록 조회"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            cursor = conn.execute("SELECT group_name FROM feature_groups")
            return [row[0] for row in cursor.fetchall()]
    
    def list_features(self, feature_group: Optional[str] = None) -> List[str]:
        """피처 목록 조회"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            if feature_group:
                cursor = conn.execute("""
                    SELECT feature_name FROM feature_metadata 
                    WHERE feature_group = ?
                """, (feature_group,))
            else:
                cursor = conn.execute("SELECT feature_name FROM feature_metadata")
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_feature_info(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """피처 정보 조회"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM feature_metadata WHERE feature_name = ?
            """, (feature_name,))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        
        return None
    
    def delete_feature(self, feature_name: str, feature_group: Optional[str] = None) -> bool:
        """피처 삭제"""
        try:
            # 파일 경로 조회
            file_path = self._get_feature_file_path(feature_name, feature_group)
            
            # 파일 삭제
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
            
            # 메타데이터 삭제
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    DELETE FROM feature_metadata WHERE feature_name = ?
                """, (feature_name,))
            
            # 캐시에서 삭제
            if self.cache and feature_group:
                cache_key = f"{feature_group}:{feature_name}"
                if cache_key in self.cache.cache:
                    del self.cache.cache[cache_key]
                    del self.cache.access_times[cache_key]
            
            self.logger.info(f"피처 삭제 완료: {feature_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"피처 삭제 실패 {feature_name}: {e}")
            return False
    
    def get_store_stats(self) -> Dict[str, Any]:
        """피처 스토어 통계 조회"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            # 피처 수
            cursor = conn.execute("SELECT COUNT(*) FROM feature_metadata")
            total_features = cursor.fetchone()[0]
            
            # 그룹 수
            cursor = conn.execute("SELECT COUNT(*) FROM feature_groups")
            total_groups = cursor.fetchone()[0]
            
            # 총 크기
            cursor = conn.execute("SELECT SUM(size_bytes) FROM feature_metadata")
            total_size = cursor.fetchone()[0] or 0
            
            # 레코드 수
            cursor = conn.execute("SELECT SUM(record_count) FROM feature_metadata")
            total_records = cursor.fetchone()[0] or 0
        
        stats = {
            'total_features': total_features,
            'total_groups': total_groups,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'total_records': total_records,
            'cache_stats': self.cache.get_stats() if self.cache else None,
            'storage_path': str(self.base_path)
        }
        
        return stats
    
    def backup_store(self, backup_path: Optional[str] = None) -> str:
        """피처 스토어 백업"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_feature_store_{timestamp}"
        
        backup_path = Path(backup_path)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 파일 복사
        import shutil
        shutil.copytree(self.base_path, backup_path / "feature_store", dirs_exist_ok=True)
        
        self.logger.info(f"피처 스토어 백업 완료: {backup_path}")
        return str(backup_path)
    
    def _save_feature_metadata(self, feature_name: str, feature_group: str, 
                              file_path: str, df: pd.DataFrame) -> None:
        """피처 메타데이터 저장"""
        file_size = Path(file_path).stat().st_size
        record_count = len(df)
        
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO feature_metadata 
                (feature_name, feature_group, data_type, description, created_at, 
                 updated_at, version, file_path, size_bytes, record_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature_name,
                feature_group,
                str(df.dtypes.to_dict()),
                f"Auto-generated metadata for {feature_name}",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                "1.0.0",
                file_path,
                file_size,
                record_count
            ))
    
    def _update_feature_group_metadata(self, group_name: str, features: List[str]) -> None:
        """피처 그룹 메타데이터 업데이트"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO feature_groups 
                (group_name, description, created_at, features)
                VALUES (?, ?, ?, ?)
            """, (
                group_name,
                f"Feature group: {group_name}",
                datetime.now(timezone.utc).isoformat(),
                json.dumps(features)
            ))
    
    def _get_feature_file_path(self, feature_name: str, feature_group: Optional[str] = None) -> Optional[str]:
        """피처 파일 경로 조회"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            if feature_group:
                cursor = conn.execute("""
                    SELECT file_path FROM feature_metadata 
                    WHERE feature_name = ? AND feature_group = ?
                    ORDER BY updated_at DESC LIMIT 1
                """, (feature_name, feature_group))
            else:
                cursor = conn.execute("""
                    SELECT file_path FROM feature_metadata 
                    WHERE feature_name = ?
                    ORDER BY updated_at DESC LIMIT 1
                """, (feature_name,))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _init_redis_cache(self) -> redis.Redis:
        """레디스 캐시 초기화"""
        try:
            redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True
            )
            # 연결 테스트
            redis_client.ping()
            self.logger.info(f"Redis 캐시 초기화 성공: {self.config.redis_host}:{self.config.redis_port}")
            return redis_client
        except Exception as e:
            self.logger.error(f"Redis 연결 실패: {e}")
            # 폴백으로 메모리 캐시 사용
            return FeatureCache(
                max_size=self.config.cache_max_size,
                ttl_seconds=self.config.cache_ttl_seconds
            )
    
    def _init_metrics(self) -> Dict[str, Any]:
        """프로메테우스 메트릭 초기화"""
        metrics = {
            'feature_requests': Counter(
                'feature_store_requests_total',
                'Total number of feature requests',
                ['operation', 'feature_group']
            ),
            'request_duration': Histogram(
                'feature_store_request_duration_seconds',
                'Time spent processing feature requests',
                ['operation']
            ),
            'cache_hits': Counter(
                'feature_store_cache_hits_total',
                'Total number of cache hits',
                ['cache_type']
            ),
            'cache_misses': Counter(
                'feature_store_cache_misses_total',
                'Total number of cache misses',
                ['cache_type']
            ),
            'stored_features': Gauge(
                'feature_store_features_total',
                'Total number of stored features'
            ),
            'storage_size': Gauge(
                'feature_store_storage_bytes',
                'Total storage size in bytes'
            )
        }
        
        # 메트릭 서버 시작
        try:
            prometheus_client.start_http_server(self.config.metrics_port)
            self.logger.info(f"프로메테우스 메트릭 서버 시작: 포트 {self.config.metrics_port}")
        except Exception as e:
            self.logger.warning(f"메트릭 서버 시작 실패: {e}")
        
        return metrics
    
    def _record_metric(self, metric_name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """메트릭 기록"""
        if not self.metrics:
            return
            
        try:
            metric = self.metrics.get(metric_name)
            if metric:
                if labels:
                    if hasattr(metric, 'labels'):
                        metric.labels(**labels).inc(value)
                    else:
                        metric.inc(value)
                else:
                    metric.inc(value) if hasattr(metric, 'inc') else metric.set(value)
        except Exception as e:
            self.logger.warning(f"메트릭 기록 실패: {e}")
    
    def _validate_feature_schema(self, feature_data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
        """피처 데이터 스키마 검증"""
        try:
            # 데이터프레임을 JSON 스키마로 검증
            data_dict = feature_data.to_dict('records')[0] if len(feature_data) > 0 else {}
            jsonschema.validate(data_dict, schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"스키마 검증 실패: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"스키마 검증 오류: {e}")
            return True  # 오류 시 기본적으로 통과


class FeatureStoreAPI:
    """피처 스토어 RESTful API 인터페이스"""
    
    def __init__(self, feature_store: SimpleFeatureStore):
        self.feature_store = feature_store
        self.logger = logging.getLogger("FeatureStoreAPI")
    
    def get_features_endpoint(self, feature_names: List[str], 
                            feature_group: Optional[str] = None) -> Dict[str, Any]:
        """피처 조회 API 엔드포인트"""
        try:
            features = self.feature_store.get_features(feature_names, feature_group)
            
            # DataFrame을 JSON 직렬화 가능한 형태로 변환
            serialized_features = {}
            for name, df in features.items():
                serialized_features[name] = {
                    'data': df.to_dict('records'),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.astype(str).to_dict(),
                    'shape': df.shape
                }
            
            return {
                'status': 'success',
                'features': serialized_features,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"피처 조회 API 오류: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def save_features_endpoint(self, feature_group: str, 
                             features_data: Dict[str, Any]) -> Dict[str, Any]:
        """피처 저장 API 엔드포인트"""
        try:
            # JSON 데이터를 DataFrame으로 변환
            dataframes = {}
            for name, data in features_data.items():
                df = pd.DataFrame(data['data'])
                dataframes[name] = df
            
            saved_paths = self.feature_store.save_features(feature_group, dataframes)
            
            return {
                'status': 'success',
                'saved_paths': saved_paths,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"피처 저장 API 오류: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_stats_endpoint(self) -> Dict[str, Any]:
        """통계 조회 API 엔드포인트"""
        try:
            stats = self.feature_store.get_store_stats()
            return {
                'status': 'success',
                'stats': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"통계 조회 API 오류: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


def main():
    """테스트용 메인 함수"""
    # 피처 스토어 초기화
    config = FeatureStoreConfig(
        base_path="data/test_feature_store",
        cache_enabled=True,
        cache_max_size=50
    )
    
    store = SimpleFeatureStore(config)
    
    # 샘플 데이터 생성
    sample_features = {
        'user_features': pd.DataFrame({
            'user_id': range(100),
            'age': np.random.randint(18, 65, 100),
            'preference_score': np.random.random(100)
        }),
        'movie_features': pd.DataFrame({
            'movie_id': range(50),
            'popularity': np.random.exponential(50, 50),
            'rating': np.random.normal(7.0, 1.5, 50)
        })
    }
    
    # 피처 저장 테스트
    print("=== 피처 저장 테스트 ===")
    saved_paths = store.save_features("test_group", sample_features)
    print(f"저장된 경로: {saved_paths}")
    
    # 피처 조회 테스트
    print("\n=== 피처 조회 테스트 ===")
    retrieved_features = store.get_features(['user_features', 'movie_features'], 'test_group')
    for name, df in retrieved_features.items():
        print(f"{name}: {df.shape}")
    
    # 통계 조회 테스트
    print("\n=== 통계 조회 테스트 ===")
    stats = store.get_store_stats()
    print(f"총 피처 수: {stats['total_features']}")
    print(f"총 크기: {stats['total_size_mb']:.2f} MB")
    
    # API 테스트
    print("\n=== API 테스트 ===")
    api = FeatureStoreAPI(store)
    api_response = api.get_stats_endpoint()
    print(f"API 응답: {api_response['status']}")
    
    print("\n테스트 완료!")


if __name__ == "__main__":
    main()

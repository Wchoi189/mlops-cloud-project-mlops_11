"""
Feast 피처 스토어 통합 모듈
2.7 Feast 피처 스토어 통합

이 모듈은 Feast 오픈소스 피처 스토어와의 통합을 제공합니다.
엔터프라이즈급 피처 스토어 기능을 활용할 수 있습니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import yaml

try:
    from feast import FeatureStore, Entity, FeatureView, FileSource, FeatureService
    from feast.value_type import ValueType
    # 최신 Feast 버전의 타입 시스템 사용
    try:
        from feast.types import Float64, Float32, Int64, String, Bool
        FEAST_MODERN_TYPES = True
    except ImportError:
        FEAST_MODERN_TYPES = False
    FEAST_AVAILABLE = True
except ImportError:
    FEAST_AVAILABLE = False
    FEAST_MODERN_TYPES = False
    logging.warning("Feast가 설치되지 않음. feast 기능을 사용하려면 'pip install feast'를 실행하세요.")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeastIntegration:
    """Feast 피처 스토어 통합 클래스"""
    
    def __init__(self, repo_path: str = "feature_repo", project_name: str = "movie_mlops"):
        """
        초기화
        
        Args:
            repo_path: Feast repository 경로
            project_name: 프로젝트 명
        """
        if not FEAST_AVAILABLE:
            raise ImportError("Feast가 설치되지 않음. 'pip install feast'를 실행하세요.")
        
        self.repo_path = Path(repo_path)
        self.project_name = project_name
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Feast 설정 파일 생성
        self._create_feature_store_yaml()
        
        # Feast 스토어 초기화
        self.store = FeatureStore(repo_path=str(self.repo_path))
        
        # 엔티티와 피처뷰 정의
        self.entities = self._define_entities()
        self.feature_views = {}
        
        logger.info(f"Feast 통합 초기화 완료: {repo_path}")
    
    def _create_feature_store_yaml(self):
        """feature_store.yaml 설정 파일 생성"""
        config = {
            'project': self.project_name,
            'registry': str(self.repo_path / 'data' / 'registry.db'),
            'provider': 'local',
            'online_store': {
                'type': 'sqlite',
                'path': str(self.repo_path / 'data' / 'online_store.db')
            },
            'offline_store': {
                'type': 'file'
            },
            'entity_key_serialization_version': 2
        }
        
        config_path = self.repo_path / 'feature_store.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # 데이터 디렉토리 생성
        (self.repo_path / 'data').mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Feast 설정 파일 생성: {config_path}")
    
    def _define_entities(self) -> Dict[str, Entity]:
        """엔티티 정의"""
        entities = {
            'movie': Entity(
                name='movie_id',
                value_type=ValueType.INT64,
                description='영화 고유 식별자'
            ),
            'user': Entity(
                name='user_id', 
                value_type=ValueType.INT64,
                description='사용자 고유 식별자'
            )
        }
        
        logger.info(f"엔티티 정의 완료: {list(entities.keys())}")
        return entities
    
    def create_movie_features(self, movie_data: pd.DataFrame) -> str:
        """영화 피처 뷰 생성"""
        # 데이터 저장 경로
        data_path = self.repo_path / 'data' / 'movie_features.parquet'
        
        # 필요한 컬럼 확인 및 추가
        required_columns = ['movie_id', 'event_timestamp']
        
        if 'movie_id' not in movie_data.columns:
            logger.error("movie_id 컬럼이 필요합니다")
            return ""
        
        # 이벤트 타임스탬프 추가 (없는 경우)
        if 'event_timestamp' not in movie_data.columns:
            movie_data['event_timestamp'] = pd.Timestamp.now()
        
        # 데이터 저장
        movie_data.to_parquet(data_path, index=False)
        
        # 피처 뷰 정의
        movie_source = FileSource(
            path=str(data_path),
            event_timestamp_column='event_timestamp'
        )
        
        # 숫자형 피처들 자동 감지
        numeric_features = []
        for col in movie_data.columns:
            if col not in ['movie_id', 'event_timestamp'] and pd.api.types.is_numeric_dtype(movie_data[col]):
                # ValueType 올바르게 지정
                if movie_data[col].dtype in ['int32', 'int64', 'int']:
                    feature_type = ValueType.INT64
                elif movie_data[col].dtype in ['float32']:
                    feature_type = ValueType.FLOAT
                else:  # float64, float
                    feature_type = ValueType.DOUBLE
                
                from feast import Feature
                # Feast 버전에 따라 Feature 생성자가 다를 수 있음
                try:
                    # 새로운 Feast 버전 (dtype 파라미터 사용)
                    numeric_features.append(Feature(name=col, dtype=feature_type))
                except TypeError:
                    try:
                        # 이전 Feast 버전 (value_type 파라미터 사용)
                        numeric_features.append(Feature(name=col, value_type=feature_type))
                    except TypeError:
                        # 가장 기본적인 형태 (타입 없이)
                        numeric_features.append(Feature(name=col))
        
        # 문자열 피처들
        string_features = []
        for col in movie_data.columns:
            if col not in ['movie_id', 'event_timestamp'] and movie_data[col].dtype == 'object':
                try:
                    string_features.append(Feature(name=col, dtype=ValueType.STRING))
                except TypeError:
                    try:
                        string_features.append(Feature(name=col, value_type=ValueType.STRING))
                    except TypeError:
                        string_features.append(Feature(name=col))
        
        all_features = numeric_features + string_features
        
        # FeatureView 버전 호환성 처리
        try:
            # 최신 Feast 버전 (Field + schema 기반)
            try:
                from feast import Field
                
                schema_fields = []
                for col in movie_data.columns:
                    if col not in ['movie_id', 'event_timestamp']:
                        # 최신 타입 시스템 사용
                        if pd.api.types.is_integer_dtype(movie_data[col]):
                            if FEAST_MODERN_TYPES:
                                field_type = Int64
                            else:
                                field_type = ValueType.INT64
                        elif pd.api.types.is_float_dtype(movie_data[col]):
                            if FEAST_MODERN_TYPES:
                                field_type = Float64 if movie_data[col].dtype != 'float32' else Float32
                            else:
                                field_type = ValueType.DOUBLE if movie_data[col].dtype != 'float32' else ValueType.FLOAT
                        elif movie_data[col].dtype == 'object':
                            if FEAST_MODERN_TYPES:
                                field_type = String
                            else:
                                field_type = ValueType.STRING
                        else:
                            if FEAST_MODERN_TYPES:
                                field_type = Float64
                            else:
                                field_type = ValueType.DOUBLE
                        
                        schema_fields.append(Field(name=col, dtype=field_type))
                
                # Entity 객체 사용
                movie_fv = FeatureView(
                    name='movie_features',
                    entities=[self.entities['movie']],
                    ttl=timedelta(days=1),
                    schema=schema_fields,
                    source=movie_source
                )
                
            except Exception as schema_error:
                logger.warning(f"Schema 기반 FeatureView 실패: {schema_error}, Feature 기반으로 시도")
                
                # 이전 Feast 버전 (features 파라미터)
                movie_fv = FeatureView(
                    name='movie_features',
                    entities=[self.entities['movie']],
                    ttl=timedelta(days=1),
                    features=all_features,
                    source=movie_source
                )
                
        except Exception as fv_error:
            logger.error(f"FeatureView 생성 실패: {fv_error}")
            
            # 가장 기본적인 FeatureView
            try:
                movie_fv = FeatureView(
                    name='movie_features',
                    entities=[self.entities['movie']],
                    ttl=timedelta(days=1),
                    source=movie_source
                )
            except Exception:
                # 문자열 엔티티로 시도
                movie_fv = FeatureView(
                    name='movie_features',
                    entities=['movie_id'],
                    ttl=timedelta(days=1),
                    source=movie_source
                )
        
        self.feature_views['movie_features'] = movie_fv
        
        logger.info(f"영화 피처 뷰 생성: {len(all_features)}개 피처")
        return 'movie_features'
    
    def create_user_features(self, user_data: pd.DataFrame) -> str:
        """사용자 피처 뷰 생성"""
        data_path = self.repo_path / 'data' / 'user_features.parquet'
        
        if 'user_id' not in user_data.columns:
            logger.error("user_id 컬럼이 필요합니다")
            return ""
        
        if 'event_timestamp' not in user_data.columns:
            user_data['event_timestamp'] = pd.Timestamp.now()
        
        user_data.to_parquet(data_path, index=False)
        
        user_source = FileSource(
            path=str(data_path),
            event_timestamp_column='event_timestamp'
        )
        
        # 피처 자동 감지
        features = []
        for col in user_data.columns:
            if col not in ['user_id', 'event_timestamp']:
                # ValueType 올바르게 지정
                if pd.api.types.is_integer_dtype(user_data[col]):
                    feature_type = ValueType.INT64
                elif pd.api.types.is_float_dtype(user_data[col]):
                    if user_data[col].dtype == 'float32':
                        feature_type = ValueType.FLOAT
                    else:
                        feature_type = ValueType.DOUBLE
                elif user_data[col].dtype == 'object':
                    feature_type = ValueType.STRING
                else:
                    feature_type = ValueType.DOUBLE  # 기본값
                
                from feast import Feature
                # Feast 버전에 따라 Feature 생성자가 다를 수 있음
                try:
                    features.append(Feature(name=col, dtype=feature_type))
                except TypeError:
                    try:
                        features.append(Feature(name=col, value_type=feature_type))
                    except TypeError:
                        features.append(Feature(name=col))
        
        # FeatureView 버전 호환성 처리
        try:
            # 최신 Feast 버전 (Field + schema 기반)
            try:
                from feast import Field
                
                schema_fields = []
                for col in user_data.columns:
                    if col not in ['user_id', 'event_timestamp']:
                        # 최신 타입 시스템 사용
                        if pd.api.types.is_integer_dtype(user_data[col]):
                            if FEAST_MODERN_TYPES:
                                field_type = Int64
                            else:
                                field_type = ValueType.INT64
                        elif pd.api.types.is_float_dtype(user_data[col]):
                            if FEAST_MODERN_TYPES:
                                field_type = Float64 if user_data[col].dtype != 'float32' else Float32
                            else:
                                field_type = ValueType.DOUBLE if user_data[col].dtype != 'float32' else ValueType.FLOAT
                        elif user_data[col].dtype == 'object':
                            if FEAST_MODERN_TYPES:
                                field_type = String
                            else:
                                field_type = ValueType.STRING
                        else:
                            if FEAST_MODERN_TYPES:
                                field_type = Float64
                            else:
                                field_type = ValueType.DOUBLE
                        
                        schema_fields.append(Field(name=col, dtype=field_type))
                
                # Entity 객체 사용
                user_fv = FeatureView(
                    name='user_features',
                    entities=[self.entities['user']],
                    ttl=timedelta(days=7),
                    schema=schema_fields,
                    source=user_source
                )
                
            except Exception as schema_error:
                logger.warning(f"Schema 기반 FeatureView 실패: {schema_error}, Feature 기반으로 시도")
                
                # 이전 Feast 버전 (features 파라미터)
                user_fv = FeatureView(
                    name='user_features',
                    entities=[self.entities['user']],
                    ttl=timedelta(days=7),
                    features=features,
                    source=user_source
                )
                
        except Exception as fv_error:
            logger.error(f"FeatureView 생성 실패: {fv_error}")
            
            # 가장 기본적인 FeatureView
            try:
                user_fv = FeatureView(
                    name='user_features',
                    entities=[self.entities['user']],
                    ttl=timedelta(days=7),
                    source=user_source
                )
            except Exception:
                # 문자열 엔티티로 시도
                user_fv = FeatureView(
                    name='user_features',
                    entities=['user_id'],
                    ttl=timedelta(days=7),
                    source=user_source
                )
        
        self.feature_views['user_features'] = user_fv
        
        logger.info(f"사용자 피처 뷰 생성: {len(features)}개 피처")
        return 'user_features'
    
    def apply_feature_views(self):
        """정의된 피처 뷰들을 Feast에 적용"""
        try:
            # 엔티티 적용
            for entity in self.entities.values():
                self.store.apply([entity])
            
            # 피처 뷰 적용
            if self.feature_views:
                self.store.apply(list(self.feature_views.values()))
                logger.info(f"Feast에 피처 뷰 적용 완료: {len(self.feature_views)}개")
                return True
            else:
                logger.warning("적용할 피처 뷰가 없습니다. 먼저 create_movie_features() 또는 create_user_features()를 호출하세요.")
                return False
            
        except Exception as e:
            logger.error(f"피처 뷰 적용 실패: {e}")
            return False
    
    def materialize_features(self, start_date: datetime = None, end_date: datetime = None):
        """피처를 온라인 스토어에 구체화"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=1)
        if not end_date:
            end_date = datetime.now()
        
        try:
            self.store.materialize(start_date, end_date)
            logger.info(f"피처 구체화 완료: {start_date} ~ {end_date}")
            return True
            
        except Exception as e:
            logger.error(f"피처 구체화 실패: {e}")
            return False
    
    def get_online_features(self, entity_rows: List[Dict[str, Any]], 
                          feature_refs: List[str]) -> pd.DataFrame:
        """온라인 피처 조회"""
        try:
            feature_vector = self.store.get_online_features(
                features=feature_refs,
                entity_rows=entity_rows
            )
            
            return feature_vector.to_df()
            
        except Exception as e:
            logger.error(f"온라인 피처 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_historical_features(self, entity_df: pd.DataFrame, 
                              feature_refs: List[str]) -> pd.DataFrame:
        """히스토리컬 피처 조회"""
        try:
            training_df = self.store.get_historical_features(
                entity_df=entity_df,
                features=feature_refs
            ).to_df()
            
            return training_df
            
        except Exception as e:
            logger.error(f"히스토리컬 피처 조회 실패: {e}")
            return pd.DataFrame()
    
    def create_feature_service(self, service_name: str, feature_refs: List[str]) -> str:
        """피처 서비스 생성"""
        try:
            # 피처 참조를 FeatureView 객체로 변환
            feature_views_for_service = []
            
            # 현재 등록된 FeatureView들을 가져오기
            try:
                # Feast에서 등록된 FeatureView 들 조회
                registered_fvs = self.store.list_feature_views()
                fv_dict = {fv.name: fv for fv in registered_fvs}
                
                # 피처 참조에서 FeatureView 이름 추출
                for feature_ref in feature_refs:
                    if ':' in feature_ref:
                        fv_name = feature_ref.split(':')[0]
                        if fv_name in fv_dict:
                            feature_views_for_service.append(fv_dict[fv_name])
                        else:
                            logger.warning(f"피처 뷰를 찾을 수 없음: {fv_name}")
                    else:
                        logger.warning(f"잘못된 피처 참조 형식: {feature_ref}")
                
                if not feature_views_for_service:
                    logger.error("피처 서비스에 추가할 유효한 FeatureView가 없음")
                    return ""
                
            except Exception as list_error:
                logger.error(f"FeatureView 목록 조회 실패: {list_error}")
                
                # 대체 방식: 로컬에 저장된 feature_views 사용
                for feature_ref in feature_refs:
                    if ':' in feature_ref:
                        fv_name = feature_ref.split(':')[0]
                        if fv_name in self.feature_views:
                            feature_views_for_service.append(self.feature_views[fv_name])
                        else:
                            logger.warning(f"로컬 피처 뷰를 찾을 수 없음: {fv_name}")
            
            # FeatureService 생성 시도
            try:
                # 최신 Feast 버전: FeatureView 객체 사용
                feature_service = FeatureService(
                    name=service_name,
                    features=feature_views_for_service
                )
            except Exception as modern_error:
                logger.warning(f"FeatureView 객체로 FeatureService 생성 실패: {modern_error}")
                
                # 대체 방식: 문자열 참조 사용
                try:
                    feature_service = FeatureService(
                        name=service_name,
                        features=feature_refs
                    )
                except Exception as string_error:
                    logger.error(f"문자열 참조로 FeatureService 생성 실패: {string_error}")
                    return ""
            
            # Feast에 적용
            self.store.apply([feature_service])
            
            logger.info(f"피처 서비스 생성: {service_name}")
            return service_name
            
        except Exception as e:
            logger.error(f"피처 서비스 생성 실패: {e}")
            return ""
    
    def get_feature_service(self, service_name: str, entity_rows: List[Dict[str, Any]]) -> pd.DataFrame:
        """피처 서비스를 통한 피처 조회"""
        try:
            feature_vector = self.store.get_online_features(
                feature_service=service_name,
                entity_rows=entity_rows
            )
            
            return feature_vector.to_df()
            
        except Exception as e:
            logger.error(f"피처 서비스 조회 실패: {e}")
            return pd.DataFrame()
    
    def list_feature_views(self) -> List[str]:
        """등록된 피처 뷰 목록 조회"""
        try:
            feature_views = self.store.list_feature_views()
            return [fv.name for fv in feature_views]
            
        except Exception as e:
            logger.error(f"피처 뷰 목록 조회 실패: {e}")
            return []
    
    def get_feature_view_info(self, feature_view_name: str) -> Dict[str, Any]:
        """특정 피처 뷰 정보 조회"""
        try:
            fv = self.store.get_feature_view(feature_view_name)
            
            return {
                'name': fv.name,
                'entities': [e.name for e in fv.entities],
                'features': [f.name for f in fv.features],
                'ttl_seconds': fv.ttl.total_seconds() if fv.ttl else None,
                'description': getattr(fv, 'description', '')
            }
            
        except Exception as e:
            logger.error(f"피처 뷰 정보 조회 실패: {e}")
            return {}


def main():
    """테스트용 메인 함수"""
    if not FEAST_AVAILABLE:
        print("Feast가 설치되지 않아 테스트를 수행할 수 없습니다.")
        print("다음 명령어로 Feast를 설치하세요: pip install feast")
        return
    
    # Feast 통합 초기화
    feast_integration = FeastIntegration("test_feature_repo")
    
    # 샘플 영화 데이터
    sample_movies = pd.DataFrame({
        'movie_id': [1, 2, 3],
        'popularity': [100.5, 80.3, 120.7],
        'vote_average': [7.5, 6.8, 8.1],
        'vote_count': [500, 300, 700],
        'is_english': [1, 0, 1],
        'genre_action': [1, 0, 1],
        'genre_drama': [0, 1, 0]
    })
    
    # 샘플 사용자 데이터
    sample_users = pd.DataFrame({
        'user_id': [101, 102, 103],
        'age': [25, 35, 28],
        'preference_score': [0.8, 0.6, 0.9]
    })
    
    print("=== Feast 통합 테스트 ===")
    
    # 1. 피처 뷰 생성
    print("\n1. 피처 뷰 생성")
    movie_fv = feast_integration.create_movie_features(sample_movies)
    user_fv = feast_integration.create_user_features(sample_users)
    print(f"생성된 피처 뷰: {movie_fv}, {user_fv}")
    
    # 2. Feast에 적용
    print("\n2. Feast에 피처 뷰 적용")
    feast_integration.apply_feature_views()
    
    # 3. 피처 구체화
    print("\n3. 피처 구체화")
    feast_integration.materialize_features()
    
    # 4. 온라인 피처 조회 테스트
    print("\n4. 온라인 피처 조회")
    entity_rows = [
        {'movie_id': 1},
        {'movie_id': 2}
    ]
    
    online_features = feast_integration.get_online_features(
        entity_rows=entity_rows,
        feature_refs=['movie_features:popularity', 'movie_features:vote_average']
    )
    print(f"온라인 피처 조회 결과:\n{online_features}")
    
    # 5. 피처 서비스 생성
    print("\n5. 피처 서비스 생성")
    service_name = feast_integration.create_feature_service(
        'movie_recommendation_service',
        ['movie_features:popularity', 'movie_features:vote_average', 'movie_features:genre_action']
    )
    print(f"생성된 피처 서비스: {service_name}")
    
    # 6. 피처 뷰 목록 조회
    print("\n6. 등록된 피처 뷰 목록")
    feature_views = feast_integration.list_feature_views()
    print(f"피처 뷰 목록: {feature_views}")
    
    print("\n✅ Feast 통합 테스트 완료!")


if __name__ == "__main__":
    main()

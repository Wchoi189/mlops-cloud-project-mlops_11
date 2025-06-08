"""
피처 메타데이터 관리 시스템
2.4 피처 메타데이터 관리 구현

이 모듈은 피처의 메타데이터를 체계적으로 관리하고 추적합니다.
"""

import json
import yaml
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import logging
from enum import Enum

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """피처 타입 열거형"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"  
    BINARY = "binary"
    TEMPORAL = "temporal"
    TEXT = "text"
    DERIVED = "derived"


class DataType(Enum):
    """데이터 타입 열거형"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"


@dataclass
class FeatureMetadata:
    """개별 피처 메타데이터"""
    name: str
    feature_type: FeatureType
    data_type: DataType
    description: str
    source: str
    creation_logic: str
    dependencies: List[str]
    version: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # 통계 정보
    statistics: Dict[str, Any]
    
    # 품질 정보
    quality_score: float
    missing_ratio: float
    unique_ratio: float
    
    # 비즈니스 정보
    business_meaning: str
    usage_examples: List[str]
    
    # 기술 정보
    computation_cost: str  # low, medium, high
    update_frequency: str  # real-time, daily, weekly, monthly
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # Enum 값들을 문자열로 변환
        data['feature_type'] = self.feature_type.value
        data['data_type'] = self.data_type.value
        # datetime을 ISO 형식으로 변환
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureMetadata':
        """딕셔너리에서 생성"""
        # Enum 변환
        data['feature_type'] = FeatureType(data['feature_type'])
        data['data_type'] = DataType(data['data_type'])
        # datetime 변환
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class FeatureGroupMetadata:
    """피처 그룹 메타데이터"""
    name: str
    description: str
    features: List[str]
    creation_date: datetime
    version: str
    source_dataset: str
    processing_pipeline: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['creation_date'] = self.creation_date.isoformat()
        return data


class MetadataGenerator:
    """메타데이터 자동 생성기"""
    
    def __init__(self):
        self.logger = logging.getLogger("MetadataGenerator")
    
    def generate_feature_metadata(self, 
                                 df: pd.DataFrame,
                                 feature_name: str,
                                 source: str = "unknown",
                                 created_by: str = "system") -> FeatureMetadata:
        """
        데이터프레임에서 피처 메타데이터 자동 생성
        
        Args:
            df: 데이터프레임
            feature_name: 피처명
            source: 데이터 소스
            created_by: 생성자
            
        Returns:
            FeatureMetadata: 생성된 메타데이터
        """
        if feature_name not in df.columns:
            raise ValueError(f"피처 '{feature_name}'이 데이터프레임에 없습니다")
        
        series = df[feature_name]
        
        # 피처 타입 자동 추론
        feature_type = self._infer_feature_type(series)
        data_type = self._infer_data_type(series)
        
        # 통계 정보 계산
        statistics = self._calculate_statistics(series)
        
        # 품질 지표 계산
        quality_metrics = self._calculate_quality_metrics(series)
        
        # 자동 설명 생성
        description = self._generate_description(feature_name, feature_type, statistics)
        
        # 비즈니스 의미 추론
        business_meaning = self._infer_business_meaning(feature_name)
        
        # 계산 비용 추정
        computation_cost = self._estimate_computation_cost(feature_type)
        
        now = datetime.now(timezone.utc)
        
        return FeatureMetadata(
            name=feature_name,
            feature_type=feature_type,
            data_type=data_type,
            description=description,
            source=source,
            creation_logic="auto_generated",
            dependencies=[],
            version="1.0.0",
            created_at=now,
            updated_at=now,
            created_by=created_by,
            statistics=statistics,
            quality_score=quality_metrics['quality_score'],
            missing_ratio=quality_metrics['missing_ratio'],
            unique_ratio=quality_metrics['unique_ratio'],
            business_meaning=business_meaning,
            usage_examples=[],
            computation_cost=computation_cost,
            update_frequency="daily"
        )
    
    def _infer_feature_type(self, series: pd.Series) -> FeatureType:
        """피처 타입 자동 추론"""
        # 바이너리 체크
        unique_values = series.dropna().unique()
        if len(unique_values) == 2 and set(unique_values).issubset({0, 1, True, False}):
            return FeatureType.BINARY
        
        # 날짜/시간 체크
        if pd.api.types.is_datetime64_any_dtype(series) or 'date' in series.name.lower():
            return FeatureType.TEMPORAL
        
        # 텍스트 체크
        if pd.api.types.is_string_dtype(series):
            if 'text' in series.name.lower() or 'description' in series.name.lower():
                return FeatureType.TEXT
            else:
                return FeatureType.CATEGORICAL
        
        # 수치형 체크
        if pd.api.types.is_numeric_dtype(series):
            # 카테고리형 수치 체크 (유니크 값이 적으면)
            if series.nunique() <= 20 and series.nunique() / len(series) < 0.1:
                return FeatureType.CATEGORICAL
            else:
                return FeatureType.NUMERICAL
        
        return FeatureType.CATEGORICAL
    
    def _infer_data_type(self, series: pd.Series) -> DataType:
        """데이터 타입 추론"""
        if pd.api.types.is_integer_dtype(series):
            return DataType.INTEGER
        elif pd.api.types.is_float_dtype(series):
            return DataType.FLOAT
        elif pd.api.types.is_bool_dtype(series):
            return DataType.BOOLEAN
        elif pd.api.types.is_datetime64_any_dtype(series):
            return DataType.DATETIME
        else:
            return DataType.STRING
    
    def _calculate_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """통계 정보 계산"""
        stats = {
            'count': len(series),
            'missing_count': series.isnull().sum(),
            'unique_count': series.nunique()
        }
        
        if pd.api.types.is_numeric_dtype(series):
            stats.update({
                'mean': float(series.mean()) if not series.empty else 0.0,
                'std': float(series.std()) if not series.empty else 0.0,
                'min': float(series.min()) if not series.empty else 0.0,
                'max': float(series.max()) if not series.empty else 0.0,
                'median': float(series.median()) if not series.empty else 0.0,
                'q25': float(series.quantile(0.25)) if not series.empty else 0.0,
                'q75': float(series.quantile(0.75)) if not series.empty else 0.0,
                'skewness': float(series.skew()) if not series.empty else 0.0,
                'kurtosis': float(series.kurtosis()) if not series.empty else 0.0
            })
        else:
            # 범주형 통계
            value_counts = series.value_counts()
            stats.update({
                'mode': str(series.mode().iloc[0]) if not series.mode().empty else 'None',
                'top_categories': value_counts.head(5).to_dict()
            })
        
        return stats
    
    def _calculate_quality_metrics(self, series: pd.Series) -> Dict[str, float]:
        """품질 지표 계산"""
        missing_ratio = series.isnull().sum() / len(series)
        unique_ratio = series.nunique() / len(series)
        
        # 품질 점수 계산 (간단한 휴리스틱)
        quality_score = 1.0
        quality_score -= missing_ratio * 0.5  # 결측값 페널티
        
        if unique_ratio < 0.01:  # 너무 적은 다양성
            quality_score -= 0.3
        elif unique_ratio > 0.95:  # 너무 높은 유니크성 (ID성 피처일 가능성)
            quality_score -= 0.1
        
        quality_score = max(0.0, quality_score)
        
        return {
            'quality_score': quality_score,
            'missing_ratio': missing_ratio,
            'unique_ratio': unique_ratio
        }
    
    def _generate_description(self, feature_name: str, feature_type: FeatureType, 
                            statistics: Dict[str, Any]) -> str:
        """자동 설명 생성"""
        description_parts = []
        
        # 타입 기반 설명
        type_descriptions = {
            FeatureType.NUMERICAL: "수치형 피처",
            FeatureType.CATEGORICAL: "범주형 피처", 
            FeatureType.BINARY: "이진 피처",
            FeatureType.TEMPORAL: "시간 관련 피처",
            FeatureType.TEXT: "텍스트 피처"
        }
        
        description_parts.append(type_descriptions.get(feature_type, "피처"))
        
        # 통계 기반 설명
        if feature_type == FeatureType.NUMERICAL:
            mean = statistics.get('mean', 0)
            std = statistics.get('std', 0)
            description_parts.append(f"평균: {mean:.2f}, 표준편차: {std:.2f}")
        
        unique_count = statistics.get('unique_count', 0)
        description_parts.append(f"고유값: {unique_count}개")
        
        return " | ".join(description_parts)
    
    def _infer_business_meaning(self, feature_name: str) -> str:
        """비즈니스 의미 추론"""
        name_lower = feature_name.lower()
        
        # 키워드 기반 의미 추론
        if 'rating' in name_lower or 'score' in name_lower:
            return "영화 평가 관련 지표"
        elif 'popularity' in name_lower:
            return "인기도 측정 지표"
        elif 'genre' in name_lower:
            return "영화 장르 분류"
        elif 'release' in name_lower or 'date' in name_lower:
            return "출시 관련 시간 정보"
        elif 'vote' in name_lower:
            return "투표/리뷰 관련 지표"
        elif 'revenue' in name_lower or 'budget' in name_lower:
            return "재정 관련 지표"
        else:
            return "영화 관련 속성"
    
    def _estimate_computation_cost(self, feature_type: FeatureType) -> str:
        """계산 비용 추정"""
        cost_mapping = {
            FeatureType.NUMERICAL: "low",
            FeatureType.CATEGORICAL: "low", 
            FeatureType.BINARY: "low",
            FeatureType.TEMPORAL: "medium",
            FeatureType.TEXT: "high",
            FeatureType.DERIVED: "medium"
        }
        return cost_mapping.get(feature_type, "medium")


class MetadataRepository:
    """메타데이터 저장소"""
    
    def __init__(self, storage_path: str = "data/metadata"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.features_file = self.storage_path / "features.json"
        self.groups_file = self.storage_path / "feature_groups.json"
        self.lineage_file = self.storage_path / "lineage.json"
        
        self.logger = logging.getLogger("MetadataRepository")
        
        # 메타데이터 로드
        self.features_metadata = self._load_features_metadata()
        self.groups_metadata = self._load_groups_metadata()
        self.lineage_data = self._load_lineage_data()
    
    def save_feature_metadata(self, metadata: FeatureMetadata) -> None:
        """피처 메타데이터 저장"""
        self.features_metadata[metadata.name] = metadata.to_dict()
        self._save_features_metadata()
        self.logger.info(f"피처 메타데이터 저장: {metadata.name}")
    
    def get_feature_metadata(self, feature_name: str) -> Optional[FeatureMetadata]:
        """피처 메타데이터 조회"""
        if feature_name in self.features_metadata:
            return FeatureMetadata.from_dict(self.features_metadata[feature_name])
        return None
    
    def list_features(self, feature_type: Optional[FeatureType] = None) -> List[str]:
        """피처 목록 조회"""
        if feature_type is None:
            return list(self.features_metadata.keys())
        
        filtered_features = []
        for name, metadata in self.features_metadata.items():
            if metadata['feature_type'] == feature_type.value:
                filtered_features.append(name)
        
        return filtered_features
    
    def save_feature_group(self, group_metadata: FeatureGroupMetadata) -> None:
        """피처 그룹 메타데이터 저장"""
        self.groups_metadata[group_metadata.name] = group_metadata.to_dict()
        self._save_groups_metadata()
        self.logger.info(f"피처 그룹 메타데이터 저장: {group_metadata.name}")
    
    def search_features(self, query: str) -> List[str]:
        """피처 검색"""
        matching_features = []
        query_lower = query.lower()
        
        for name, metadata in self.features_metadata.items():
            # 이름, 설명, 비즈니스 의미에서 검색
            searchable_text = " ".join([
                name.lower(),
                metadata.get('description', '').lower(),
                metadata.get('business_meaning', '').lower()
            ])
            
            if query_lower in searchable_text:
                matching_features.append(name)
        
        return matching_features
    
    def update_feature_lineage(self, feature_name: str, 
                              dependencies: List[str],
                              transformation: str) -> None:
        """피처 리니지 업데이트"""
        self.lineage_data[feature_name] = {
            'dependencies': dependencies,
            'transformation': transformation,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        self._save_lineage_data()
        self.logger.info(f"피처 리니지 업데이트: {feature_name}")
    
    def get_feature_lineage(self, feature_name: str) -> Dict[str, Any]:
        """피처 리니지 조회"""
        return self.lineage_data.get(feature_name, {})
    
    def get_downstream_features(self, feature_name: str) -> List[str]:
        """하위 의존 피처 조회"""
        downstream = []
        for name, lineage in self.lineage_data.items():
            if feature_name in lineage.get('dependencies', []):
                downstream.append(name)
        return downstream
    
    def export_metadata(self, format: str = "json") -> str:
        """메타데이터 내보내기"""
        export_data = {
            'features': self.features_metadata,
            'groups': self.groups_metadata,
            'lineage': self.lineage_data,
            'export_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format == "yaml":
            return yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
    
    def generate_documentation(self) -> str:
        """피처 문서 자동 생성"""
        doc_lines = ["# 피처 문서", ""]
        doc_lines.append(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append(f"총 피처 수: {len(self.features_metadata)}")
        doc_lines.append("")
        
        # 타입별 피처 개수
        type_counts = {}
        for metadata in self.features_metadata.values():
            feature_type = metadata['feature_type']
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        
        doc_lines.append("## 피처 타입별 분포")
        for feature_type, count in type_counts.items():
            doc_lines.append(f"- {feature_type}: {count}개")
        doc_lines.append("")
        
        # 피처별 상세 정보
        doc_lines.append("## 피처 상세 정보")
        for name, metadata in self.features_metadata.items():
            doc_lines.append(f"### {name}")
            doc_lines.append(f"- **타입**: {metadata['feature_type']}")
            doc_lines.append(f"- **설명**: {metadata['description']}")
            doc_lines.append(f"- **비즈니스 의미**: {metadata['business_meaning']}")
            doc_lines.append(f"- **품질 점수**: {metadata['quality_score']:.2f}")
            doc_lines.append("")
        
        return "\n".join(doc_lines)
    
    def _load_features_metadata(self) -> Dict[str, Dict]:
        """피처 메타데이터 로드"""
        if self.features_file.exists():
            with open(self.features_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_features_metadata(self) -> None:
        """피처 메타데이터 저장"""
        with open(self.features_file, 'w', encoding='utf-8') as f:
            json.dump(self.features_metadata, f, indent=2, ensure_ascii=False)
    
    def _load_groups_metadata(self) -> Dict[str, Dict]:
        """그룹 메타데이터 로드"""
        if self.groups_file.exists():
            with open(self.groups_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_groups_metadata(self) -> None:
        """그룹 메타데이터 저장"""
        with open(self.groups_file, 'w', encoding='utf-8') as f:
            json.dump(self.groups_metadata, f, indent=2, ensure_ascii=False)
    
    def _load_lineage_data(self) -> Dict[str, Dict]:
        """리니지 데이터 로드"""
        if self.lineage_file.exists():
            with open(self.lineage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_lineage_data(self) -> None:
        """리니지 데이터 저장"""
        with open(self.lineage_file, 'w', encoding='utf-8') as f:
            json.dump(self.lineage_data, f, indent=2, ensure_ascii=False)


def main():
    """테스트용 메인 함수"""
    # 샘플 데이터 생성
    sample_data = pd.DataFrame({
        'movie_id': range(100),
        'popularity': np.random.exponential(50, 100),
        'vote_average': np.random.normal(6.5, 1.2, 100),
        'vote_count': np.random.poisson(100, 100),
        'genre_action': np.random.binomial(1, 0.3, 100),
        'release_year': np.random.randint(2000, 2025, 100)
    })
    
    # 메타데이터 생성기 테스트
    generator = MetadataGenerator()
    
    # 저장소 초기화
    repo = MetadataRepository()
    
    # 각 피처에 대해 메타데이터 생성 및 저장
    for column in sample_data.columns:
        if column != 'movie_id':
            metadata = generator.generate_feature_metadata(
                sample_data, column, source="sample_data"
            )
            repo.save_feature_metadata(metadata)
    
    # 피처 그룹 생성
    group_metadata = FeatureGroupMetadata(
        name="basic_movie_features",
        description="영화의 기본 정보 피처들",
        features=['popularity', 'vote_average', 'vote_count'],
        creation_date=datetime.now(timezone.utc),
        version="1.0.0",
        source_dataset="tmdb_movies",
        processing_pipeline="basic_preprocessing"
    )
    repo.save_feature_group(group_metadata)
    
    # 검색 테스트
    search_results = repo.search_features("vote")
    print(f"'vote' 검색 결과: {search_results}")
    
    # 문서 생성
    documentation = repo.generate_documentation()
    print("=== 자동 생성 문서 ===")
    print(documentation[:500] + "...")


if __name__ == "__main__":
    main()

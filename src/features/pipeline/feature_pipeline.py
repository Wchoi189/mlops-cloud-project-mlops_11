"""
피처 생성 파이프라인 시스템
2.2 피처 파이프라인 구축 구현

이 모듈은 YAML 설정 기반의 확장 가능한 피처 생성 파이프라인을 제공합니다.
단계별 처리, 병렬 실행, 진행률 모니터링을 지원합니다.
"""

import yaml
import json
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import logging
import time
from datetime import datetime
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """파이프라인 설정 클래스"""
    input_source: str
    input_format: str
    output_destination: str
    output_format: str
    stages: List[Dict[str, Any]]
    parallel_processing: bool = True
    max_workers: int = 4
    chunk_size: int = 1000
    enable_caching: bool = True
    progress_reporting: bool = True


class PipelineStage(ABC):
    """파이프라인 단계 추상 클래스"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self.logger = logging.getLogger(f"Stage.{name}")
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """데이터 처리 메서드"""
        pass
    
    def validate_input(self, data: Any) -> bool:
        """입력 데이터 검증"""
        return data is not None
    
    def validate_output(self, data: Any) -> bool:
        """출력 데이터 검증"""
        return data is not None


class DataValidationStage(PipelineStage):
    """데이터 검증 단계"""
    
    def process(self, data: Any) -> Any:
        self.logger.info(f"데이터 검증 시작: {len(data) if hasattr(data, '__len__') else '?'}개 항목")
        
        if isinstance(data, list):
            # 필수 필드 검증
            required_fields = self.params.get('required_fields', ['movie_id'])
            valid_data = []
            
            for item in data:
                if all(field in item for field in required_fields):
                    valid_data.append(item)
            
            self.logger.info(f"검증 완료: {len(valid_data)}/{len(data)} 항목 유효")
            return valid_data
        
        return data


class FeatureExtractionStage(PipelineStage):
    """피처 추출 단계"""
    
    def process(self, data: Any) -> Any:
        self.logger.info("피처 추출 시작")
        
        from ..engineering.tmdb_processor import AdvancedTMDBPreProcessor
        
        # 프로세서 초기화
        processor = AdvancedTMDBPreProcessor(data, self.params)
        
        # 피처 추출 방식 결정
        extraction_type = self.params.get('extraction_type', 'all')
        
        if extraction_type == 'all':
            features = processor.extract_all_features()
        elif extraction_type == 'basic':
            features = {'basic': processor.extract_basic_features()}
        elif extraction_type == 'temporal':
            features = {'temporal': processor.extract_temporal_features()}
        else:
            features = processor.extract_all_features()
        
        self.logger.info(f"피처 추출 완료: {len(features)} 카테고리")
        return features


class FeatureTransformationStage(PipelineStage):
    """피처 변환 단계"""
    
    def process(self, data: Any) -> Any:
        self.logger.info("피처 변환 시작")
        
        if not isinstance(data, dict):
            return data
        
        transformed_data = {}
        
        for category, features in data.items():
            if isinstance(features, pd.DataFrame):
                # 리스트나 복잡한 타입의 컬럼을 변환에서 제외
                clean_features = self._prepare_for_transformation(features)
                
                # 스케일링
                if self.params.get('enable_scaling', True):
                    clean_features = self._apply_scaling(clean_features)
                
                # 결측값 처리
                if self.params.get('handle_missing', True):
                    clean_features = self._handle_missing_values(clean_features)
                
                # 이상치 처리
                if self.params.get('handle_outliers', True):
                    clean_features = self._handle_outliers(clean_features)
                
                transformed_data[category] = clean_features
            else:
                transformed_data[category] = features
        
        self.logger.info("피처 변환 완료")
        return transformed_data
    
    def _prepare_for_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
        """변환을 위한 데이터 준비 (미지원 타입 제거)"""
        clean_df = df.copy()
        
        # 리스트나 복잡한 타입을 가진 컬럼 제거
        columns_to_remove = []
        
        for col in clean_df.columns:
            if clean_df[col].dtype == 'object':
                # 문자열 컬럼 중에서 리스트나 복잡한 타입을 가진 것들 확인
                sample_values = clean_df[col].dropna()
                if len(sample_values) > 0:
                    first_val = sample_values.iloc[0]
                    if isinstance(first_val, (list, dict, tuple)):
                        columns_to_remove.append(col)
                        self.logger.info(f"변환에서 제외되는 컬럼: {col} (타입: {type(first_val).__name__})")
        
        # 복잡한 타입 컬럼 제거
        if columns_to_remove:
            # 제거된 컬럼들을 별도로 저장 (필요시 나중에 다시 추가 가능)
            excluded_cols = clean_df[columns_to_remove].copy()
            clean_df = clean_df.drop(columns=columns_to_remove)
            
            # 메타데이터에 제외된 컬럼 정보 저장
            if not hasattr(self, 'excluded_columns'):
                self.excluded_columns = {}
            self.excluded_columns[id(df)] = excluded_cols
        
        return clean_df
    
    def _apply_scaling(self, df: pd.DataFrame) -> pd.DataFrame:
        """수치형 피처 스케일링"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            # 수치형 컬럼이 없으면 원본 반환
            return df
            
        scaling_method = self.params.get('scaling_method', 'standard')
        
        if scaling_method == 'standard':
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
        elif scaling_method == 'minmax':
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
        else:
            return df
        
        df_scaled = df.copy()
        
        try:
            df_scaled[numeric_columns] = scaler.fit_transform(df[numeric_columns])
        except Exception as e:
            self.logger.warning(f"스케일링 실패: {e}. 원본 데이터 반환")
            return df
        
        return df_scaled
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """결측값 처리 (간단한 방식)"""
        strategy = self.params.get('missing_strategy', 'median')
        
        if strategy == 'drop':
            return df.dropna()
        
        df_filled = df.copy()
        
        # 수치형 컬럼 처리
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            if strategy == 'median':
                df_filled[numeric_cols] = df_filled[numeric_cols].fillna(df[numeric_cols].median())
            elif strategy == 'mean':
                df_filled[numeric_cols] = df_filled[numeric_cols].fillna(df[numeric_cols].mean())
            elif strategy == 'zero':
                df_filled[numeric_cols] = df_filled[numeric_cols].fillna(0)
        
        # 문자열/범주형 컬럼 처리
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if strategy in ['median', 'mean']:
                # 최빈값으로 채움
                mode_vals = df[col].mode()
                if len(mode_vals) > 0:
                    df_filled[col] = df_filled[col].fillna(mode_vals.iloc[0])
                else:
                    df_filled[col] = df_filled[col].fillna('unknown')
            elif strategy == 'zero':
                df_filled[col] = df_filled[col].fillna('none')
            else:
                df_filled[col] = df_filled[col].fillna('unknown')
        
        return df_filled
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """이상치 처리"""
        method = self.params.get('outlier_method', 'iqr')
        
        if method == 'iqr':
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        
        return df


class FeatureValidationStage(PipelineStage):
    """피처 검증 단계"""
    
    def process(self, data: Any) -> Any:
        self.logger.info("피처 검증 시작")
        
        validation_results = {}
        
        if isinstance(data, dict):
            for category, features in data.items():
                if isinstance(features, pd.DataFrame):
                    results = self._validate_dataframe(features, category)
                    validation_results[category] = results
        
        # 검증 실패 시 예외 발생
        failed_validations = [cat for cat, result in validation_results.items() 
                            if not result.get('passed', False)]
        
        if failed_validations and self.params.get('strict_validation', False):
            raise ValueError(f"피처 검증 실패: {failed_validations}")
        
        self.logger.info(f"피처 검증 완료: {len(validation_results)} 카테고리")
        
        # 원본 데이터에 검증 결과 추가
        if isinstance(data, dict):
            data['validation_results'] = validation_results
        
        return data
    
    def _validate_dataframe(self, df: pd.DataFrame, category: str) -> Dict[str, Any]:
        """데이터프레임 검증"""
        results = {
            'category': category,
            'record_count': len(df),
            'column_count': len(df.columns),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': 0,  # 기본값
            'passed': True,
            'issues': []
        }
        
        # 중복 행 검사 (리스트 컬럼 제외)
        try:
            # 리스트나 복잡한 타입을 가진 컬럼 제외
            safe_columns = []
            for col in df.columns:
                try:
                    # 컬럼의 첫 번째 비널 값 확인
                    if df[col].dtype == 'object':
                        sample_values = df[col].dropna()
                        if len(sample_values) > 0:
                            first_val = sample_values.iloc[0]
                            if not isinstance(first_val, (list, dict, tuple)):
                                safe_columns.append(col)
                        else:
                            safe_columns.append(col)  # 빈 컬럼도 안전
                    else:
                        safe_columns.append(col)  # 비-object 타입은 안전
                except Exception:
                    # 예외 발생 시 해당 컬럼 제외
                    continue
            
            # 안전한 컬럼들로만 중복 검사
            if safe_columns:
                safe_df = df[safe_columns]
                results['duplicate_rows'] = safe_df.duplicated().sum()
            else:
                self.logger.warning(f"{category}: 중복 검사에 사용할 수 있는 컬럼이 없습니다.")
                results['duplicate_rows'] = 0
                
        except Exception as e:
            self.logger.warning(f"{category}: 중복 검사 실패: {e}")
            results['duplicate_rows'] = 0
        
        # 최소 레코드 수 확인
        min_records = self.params.get('min_records', 10)
        if len(df) < min_records:
            results['passed'] = False
            results['issues'].append(f"레코드 수 부족: {len(df)} < {min_records}")
        
        # 결측값 비율 확인
        max_missing_ratio = self.params.get('max_missing_ratio', 0.5)
        total_cells = len(df) * len(df.columns)
        if total_cells > 0:
            missing_ratio = results['missing_values'] / total_cells
            if missing_ratio > max_missing_ratio:
                results['passed'] = False
                results['issues'].append(f"결측값 비율 초과: {missing_ratio:.2%}")
        
        return results


class FeatureStorageStage(PipelineStage):
    """피처 저장 단계"""
    
    def process(self, data: Any) -> Any:
        self.logger.info("피처 저장 시작")
        
        output_path = Path(self.params.get('output_path', 'data/features'))
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if isinstance(data, dict):
            for category, features in data.items():
                if isinstance(features, pd.DataFrame):
                    # Parquet 형식으로 저장
                    file_path = output_path / f"{category}_{timestamp}.parquet"
                    features.to_parquet(file_path, index=False)
                    self.logger.info(f"저장 완료: {file_path}")
                
                elif isinstance(features, dict):
                    # JSON 형식으로 저장 (numpy 타입 변환 포함)
                    file_path = output_path / f"{category}_{timestamp}.json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        # numpy 타입을 직렬화 가능한 타입으로 변환
                        serializable_features = self._make_json_serializable(features)
                        json.dump(serializable_features, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"저장 완료: {file_path}")
        
        self.logger.info("피처 저장 완료")
        return data
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """데이터를 JSON 직렬화 가능한 형태로 변환"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj


class FeaturePipeline:
    """메인 피처 파이프라인 클래스"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stages = self._initialize_stages()
        self.logger = logging.getLogger("FeaturePipeline")
        
        # 진행률 추적
        self.progress_callback: Optional[Callable] = None
        self.current_stage = 0
        self.total_stages = len(self.stages)
    
    def _initialize_stages(self) -> List[PipelineStage]:
        """설정 기반 스테이지 초기화"""
        stages = []
        stage_mapping = {
            'DataValidationStage': DataValidationStage,
            'FeatureExtractionStage': FeatureExtractionStage,
            'FeatureTransformationStage': FeatureTransformationStage,
            'FeatureValidationStage': FeatureValidationStage,
            'FeatureStorageStage': FeatureStorageStage
        }
        
        for stage_config in self.config.stages:
            stage_type = stage_config.get('type')
            stage_name = stage_config.get('name', stage_type)
            stage_params = stage_config.get('params', {})
            
            if stage_type in stage_mapping:
                stage_class = stage_mapping[stage_type]
                stage = stage_class(stage_name, stage_params)
                stages.append(stage)
            else:
                self.logger.warning(f"알 수 없는 스테이지 타입: {stage_type}")
        
        return stages
    
    def run(self, input_data: Any) -> Any:
        """파이프라인 실행"""
        self.logger.info(f"파이프라인 실행 시작: {len(self.stages)} 단계")
        start_time = time.time()
        
        current_data = input_data
        
        for i, stage in enumerate(self.stages):
            self.current_stage = i + 1
            stage_start_time = time.time()
            
            try:
                # 입력 검증
                if not stage.validate_input(current_data):
                    raise ValueError(f"스테이지 {stage.name} 입력 검증 실패")
                
                # 스테이지 실행
                self.logger.info(f"스테이지 {i+1}/{len(self.stages)} 실행: {stage.name}")
                current_data = stage.process(current_data)
                
                # 출력 검증
                if not stage.validate_output(current_data):
                    raise ValueError(f"스테이지 {stage.name} 출력 검증 실패")
                
                stage_duration = time.time() - stage_start_time
                self.logger.info(f"스테이지 {stage.name} 완료 ({stage_duration:.2f}초)")
                
                # 진행률 콜백 호출
                if self.progress_callback:
                    progress = (i + 1) / len(self.stages) * 100
                    self.progress_callback(progress, stage.name)
                
            except Exception as e:
                self.logger.error(f"스테이지 {stage.name} 실행 실패: {e}")
                self.logger.error(traceback.format_exc())
                raise
        
        total_duration = time.time() - start_time
        self.logger.info(f"파이프라인 실행 완료 ({total_duration:.2f}초)")
        
        return current_data
    
    def run_parallel(self, input_data: List[Any]) -> Any:
        """병렬 파이프라인 실행"""
        if not self.config.parallel_processing:
            return self.run(input_data)
        
        self.logger.info(f"병렬 파이프라인 실행 시작: {self.config.max_workers} 워커")
        
        # 데이터를 청크로 분할
        chunks = self._split_into_chunks(input_data, self.config.chunk_size)
        
        results = []
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 각 청크에 대해 파이프라인 실행
            future_to_chunk = {
                executor.submit(self._run_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"청크 처리 실패: {e}")
        
        # 결과 병합
        merged_result = self._merge_results(results)
        
        return merged_result
    
    def _run_chunk(self, chunk_data: Any) -> Any:
        """청크 단위 파이프라인 실행"""
        return self.run(chunk_data)
    
    def _split_into_chunks(self, data: List[Any], chunk_size: int) -> List[List[Any]]:
        """데이터를 청크로 분할"""
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    def _merge_results(self, results: List[Any]) -> Any:
        """병렬 처리 결과 병합"""
        if not results:
            return None
        
        if isinstance(results[0], dict):
            merged = {}
            for result in results:
                for key, value in result.items():
                    if key not in merged:
                        merged[key] = []
                    if isinstance(value, pd.DataFrame):
                        merged[key].append(value)
                    else:
                        merged[key] = value
            
            # DataFrame 병합
            for key, value_list in merged.items():
                if isinstance(value_list, list) and value_list and isinstance(value_list[0], pd.DataFrame):
                    merged[key] = pd.concat(value_list, ignore_index=True)
            
            return merged
        
        return results[0]  # 기본적으로 첫 번째 결과 반환
    
    def set_progress_callback(self, callback: Callable):
        """진행률 콜백 설정"""
        self.progress_callback = callback


def load_pipeline_config(config_path: str) -> PipelineConfig:
    """YAML 설정 파일에서 파이프라인 설정 로드"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    return PipelineConfig(**config_dict)


def create_default_config() -> Dict[str, Any]:
    """기본 파이프라인 설정 생성"""
    return {
        'input_source': 'data/raw/movies',
        'input_format': 'json',
        'output_destination': 'data/features',
        'output_format': 'parquet',
        'parallel_processing': True,
        'max_workers': 4,
        'chunk_size': 1000,
        'enable_caching': True,
        'progress_reporting': True,
        'stages': [
            {
                'name': 'data_validation',
                'type': 'DataValidationStage',
                'params': {
                    'required_fields': ['movie_id', 'title'],
                    'min_records': 10
                }
            },
            {
                'name': 'feature_extraction',
                'type': 'FeatureExtractionStage',
                'params': {
                    'extraction_type': 'all'
                }
            },
            {
                'name': 'feature_transformation',
                'type': 'FeatureTransformationStage',
                'params': {
                    'enable_scaling': True,
                    'scaling_method': 'standard',
                    'handle_missing': True,
                    'missing_strategy': 'median',
                    'handle_outliers': True,
                    'outlier_method': 'iqr'
                }
            },
            {
                'name': 'feature_validation',
                'type': 'FeatureValidationStage',
                'params': {
                    'min_records': 10,
                    'max_missing_ratio': 0.5,
                    'strict_validation': False
                }
            },
            {
                'name': 'feature_storage',
                'type': 'FeatureStorageStage',
                'params': {
                    'output_path': 'data/features'
                }
            }
        ]
    }


def main():
    """테스트용 메인 함수"""
    # 기본 설정으로 테스트
    config_dict = create_default_config()
    config = PipelineConfig(**config_dict)
    
    # 샘플 데이터
    sample_data = [
        {
            "movie_id": 552524,
            "title": "릴로 & 스티치",
            "overview": "보송보송한 파란 솜털...",
            "release_date": "2025-05-21",
            "popularity": 630.32,
            "vote_average": 7.107,
            "vote_count": 460,
            "genre_ids": [10751, 35, 878],
            "adult": False,
            "original_language": "en"
        }
    ]
    
    # 파이프라인 실행
    pipeline = FeaturePipeline(config)
    
    def progress_callback(progress: float, stage_name: str):
        print(f"진행률: {progress:.1f}% - {stage_name}")
    
    pipeline.set_progress_callback(progress_callback)
    
    result = pipeline.run(sample_data)
    print("파이프라인 실행 완료!")


if __name__ == "__main__":
    main()

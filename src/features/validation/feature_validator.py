"""
피처 검증 및 테스트 시스템
2.3 피처 검증 및 테스트 구현

이 모듈은 피처 품질 검증, A/B 테스트, 중요도 분석을 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, roc_auc_score
from sklearn.feature_selection import mutual_info_regression, f_regression
from scipy import stats
import logging
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureQualityReport:
    """피처 품질 리포트"""
    feature_name: str
    quality_score: float
    missing_ratio: float
    unique_ratio: float
    outlier_ratio: float
    distribution_type: str
    issues: List[str]
    recommendations: List[str]


@dataclass
class ABTestResult:
    """A/B 테스트 결과"""
    experiment_id: str
    control_features: List[str]
    treatment_features: List[str]
    control_performance: float
    treatment_performance: float
    improvement: float
    p_value: float
    is_significant: bool
    confidence_interval: Tuple[float, float]


class FeatureQualityChecker:
    """피처 품질 검증 시스템"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.quality_thresholds = {
            'min_quality_score': 0.7,
            'max_missing_ratio': 0.3,
            'min_unique_ratio': 0.01,
            'max_outlier_ratio': 0.1
        }
        self.logger = logging.getLogger("FeatureQualityChecker")
    
    def validate_features(self, features_df: pd.DataFrame) -> Dict[str, FeatureQualityReport]:
        """
        피처 품질 검증
        
        Args:
            features_df: 검증할 피처 데이터프레임
            
        Returns:
            Dict: 피처별 품질 리포트
        """
        self.logger.info(f"피처 품질 검증 시작: {len(features_df.columns)}개 피처")
        
        quality_reports = {}
        
        for column in features_df.columns:
            if column == 'movie_id':  # ID 컬럼 스킵
                continue
                
            report = self._analyze_feature_quality(features_df, column)
            quality_reports[column] = report
        
        self.logger.info(f"품질 검증 완료: {len(quality_reports)}개 피처 분석")
        return quality_reports
    
    def _analyze_feature_quality(self, df: pd.DataFrame, column: str) -> FeatureQualityReport:
        """개별 피처 품질 분석"""
        series = df[column]
        
        # 기본 통계
        missing_ratio = series.isnull().sum() / len(series)
        unique_ratio = series.nunique() / len(series)
        
        # 이상치 비율 (수치형만)
        outlier_ratio = 0.0
        if pd.api.types.is_numeric_dtype(series):
            outlier_ratio = self._calculate_outlier_ratio(series)
        
        # 분포 타입 추정
        distribution_type = self._estimate_distribution_type(series)
        
        # 품질 점수 계산
        quality_score = self._calculate_quality_score(
            missing_ratio, unique_ratio, outlier_ratio, distribution_type
        )
        
        # 이슈 및 권장사항
        issues, recommendations = self._generate_quality_insights(
            missing_ratio, unique_ratio, outlier_ratio, distribution_type
        )
        
        return FeatureQualityReport(
            feature_name=column,
            quality_score=quality_score,
            missing_ratio=missing_ratio,
            unique_ratio=unique_ratio,
            outlier_ratio=outlier_ratio,
            distribution_type=distribution_type,
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_outlier_ratio(self, series: pd.Series) -> float:
        """이상치 비율 계산 (IQR 방식)"""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = (series < lower_bound) | (series > upper_bound)
            return outliers.sum() / len(series)
        except:
            return 0.0
    
    def _estimate_distribution_type(self, series: pd.Series) -> str:
        """분포 타입 추정"""
        if pd.api.types.is_numeric_dtype(series):
            if series.nunique() <= 10:
                return "discrete"
            else:
                # 정규성 검정 (샘플 크기가 클 때는 간단한 휴리스틱 사용)
                if len(series) > 5000:
                    skewness = stats.skew(series.dropna())
                    if abs(skewness) < 0.5:
                        return "normal"
                    elif skewness > 0.5:
                        return "right_skewed"
                    else:
                        return "left_skewed"
                else:
                    try:
                        _, p_value = stats.normaltest(series.dropna())
                        return "normal" if p_value > 0.05 else "non_normal"
                    except:
                        return "unknown"
        else:
            return "categorical"
    
    def _calculate_quality_score(self, missing_ratio: float, unique_ratio: float, 
                                outlier_ratio: float, distribution_type: str) -> float:
        """품질 점수 계산 (0-1)"""
        score = 1.0
        
        # 결측값 페널티
        score -= missing_ratio * 0.5
        
        # 유니크 비율 (너무 낮거나 높으면 페널티)
        if unique_ratio < 0.01:  # 너무 적은 유니크 값
            score -= 0.2
        elif unique_ratio > 0.95:  # 거의 모든 값이 유니크
            score -= 0.1
        
        # 이상치 페널티
        score -= outlier_ratio * 0.3
        
        # 분포 타입 보너스
        if distribution_type in ["normal", "discrete"]:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_quality_insights(self, missing_ratio: float, unique_ratio: float,
                                 outlier_ratio: float, distribution_type: str) -> Tuple[List[str], List[str]]:
        """품질 이슈와 권장사항 생성"""
        issues = []
        recommendations = []
        
        # 결측값 이슈
        if missing_ratio > 0.3:
            issues.append(f"높은 결측값 비율: {missing_ratio:.1%}")
            recommendations.append("결측값 처리 전략 검토 필요")
        
        # 유니크 값 이슈
        if unique_ratio < 0.01:
            issues.append(f"낮은 분산: 유니크 비율 {unique_ratio:.1%}")
            recommendations.append("피처 변환 또는 제거 고려")
        elif unique_ratio > 0.95:
            issues.append(f"높은 고유성: 유니크 비율 {unique_ratio:.1%}")
            recommendations.append("ID성 피처 가능성 검토")
        
        # 이상치 이슈
        if outlier_ratio > 0.1:
            issues.append(f"높은 이상치 비율: {outlier_ratio:.1%}")
            recommendations.append("이상치 처리 또는 로그 변환 고려")
        
        # 분포 권장사항
        if distribution_type == "right_skewed":
            recommendations.append("로그 변환으로 정규화 시도")
        elif distribution_type == "left_skewed":
            recommendations.append("제곱 변환 시도")
        
        return issues, recommendations


class FeatureImportanceAnalyzer:
    """피처 중요도 분석 시스템"""
    
    def __init__(self, target_column: str = 'vote_average'):
        self.target_column = target_column
        self.logger = logging.getLogger("FeatureImportanceAnalyzer")
    
    def analyze_importance(self, features_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        다양한 방법으로 피처 중요도 분석
        
        Args:
            features_df: 피처 데이터프레임
            
        Returns:
            Dict: 방법별 피처 중요도
        """
        self.logger.info("피처 중요도 분석 시작")
        
        # 타겟 컬럼 확인
        if self.target_column not in features_df.columns:
            self.logger.warning(f"타겟 컬럼 '{self.target_column}' 없음. 'vote_average' 사용")
            if 'vote_average' in features_df.columns:
                self.target_column = 'vote_average'
            else:
                raise ValueError("적절한 타겟 컬럼을 찾을 수 없습니다")
        
        # 피처와 타겟 분리
        feature_columns = [col for col in features_df.columns 
                          if col not in ['movie_id', self.target_column]]
        
        X = features_df[feature_columns]
        y = features_df[self.target_column]
        
        # 수치형 피처만 선택
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numeric = X[numeric_features]
        
        importance_results = {}
        
        # 1. Random Forest 중요도
        importance_results['random_forest'] = self._rf_importance(X_numeric, y)
        
        # 2. 상호 정보량
        importance_results['mutual_info'] = self._mutual_info_importance(X_numeric, y)
        
        # 3. F-통계량
        importance_results['f_statistic'] = self._f_statistic_importance(X_numeric, y)
        
        # 4. 상관관계
        importance_results['correlation'] = self._correlation_importance(X_numeric, y)
        
        # 5. 통합 중요도
        importance_results['combined'] = self._combine_importance_scores(importance_results)
        
        self.logger.info(f"중요도 분석 완료: {len(importance_results)} 방법")
        return importance_results
    
    def _rf_importance(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Random Forest 피처 중요도"""
        try:
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(X, y)
            
            importance_dict = dict(zip(X.columns, rf.feature_importances_))
            return importance_dict
        except Exception as e:
            self.logger.error(f"RF 중요도 계산 실패: {e}")
            return {}
    
    def _mutual_info_importance(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """상호 정보량 기반 중요도"""
        try:
            mi_scores = mutual_info_regression(X, y, random_state=42)
            importance_dict = dict(zip(X.columns, mi_scores))
            return importance_dict
        except Exception as e:
            self.logger.error(f"상호 정보량 계산 실패: {e}")
            return {}
    
    def _f_statistic_importance(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """F-통계량 기반 중요도"""
        try:
            f_scores, _ = f_regression(X, y)
            importance_dict = dict(zip(X.columns, f_scores))
            return importance_dict
        except Exception as e:
            self.logger.error(f"F-통계량 계산 실패: {e}")
            return {}
    
    def _correlation_importance(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """상관관계 기반 중요도"""
        try:
            correlations = X.corrwith(y).abs()
            importance_dict = correlations.to_dict()
            return importance_dict
        except Exception as e:
            self.logger.error(f"상관관계 계산 실패: {e}")
            return {}
    
    def _combine_importance_scores(self, importance_results: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """중요도 점수 통합"""
        all_features = set()
        for method_scores in importance_results.values():
            all_features.update(method_scores.keys())
        
        combined_scores = {}
        
        for feature in all_features:
            scores = []
            for method, method_scores in importance_results.items():
                if method != 'combined' and feature in method_scores:
                    # 정규화
                    max_score = max(method_scores.values()) if method_scores.values() else 1
                    normalized_score = method_scores[feature] / max_score if max_score > 0 else 0
                    scores.append(normalized_score)
            
            # 평균 점수
            combined_scores[feature] = np.mean(scores) if scores else 0.0
        
        return combined_scores


class ABTestFramework:
    """A/B 테스트 프레임워크"""
    
    def __init__(self):
        self.experiments = {}
        self.logger = logging.getLogger("ABTestFramework")
    
    def create_experiment(self, experiment_id: str, control_features: List[str], 
                         treatment_features: List[str], 
                         test_data: pd.DataFrame,
                         target_column: str = 'vote_average') -> ABTestResult:
        """
        A/B 테스트 실험 생성 및 실행
        
        Args:
            experiment_id: 실험 ID
            control_features: 대조군 피처 리스트
            treatment_features: 실험군 피처 리스트
            test_data: 테스트 데이터
            target_column: 타겟 컬럼명
            
        Returns:
            ABTestResult: 실험 결과
        """
        self.logger.info(f"A/B 테스트 시작: {experiment_id}")
        
        # 데이터 분할
        control_data, treatment_data = train_test_split(test_data, test_size=0.5, random_state=42)
        
        # 대조군 성능 측정
        control_performance = self._measure_performance(
            control_data, control_features, target_column
        )
        
        # 실험군 성능 측정
        treatment_performance = self._measure_performance(
            treatment_data, treatment_features, target_column
        )
        
        # 개선 정도 계산
        improvement = (treatment_performance - control_performance) / control_performance * 100
        
        # 통계적 유의성 검정
        p_value = self._statistical_test(
            control_data[target_column], treatment_data[target_column]
        )
        
        # 신뢰구간 계산
        confidence_interval = self._calculate_confidence_interval(
            control_performance, treatment_performance
        )
        
        result = ABTestResult(
            experiment_id=experiment_id,
            control_features=control_features,
            treatment_features=treatment_features,
            control_performance=control_performance,
            treatment_performance=treatment_performance,
            improvement=improvement,
            p_value=p_value,
            is_significant=p_value < 0.05,
            confidence_interval=confidence_interval
        )
        
        # 실험 결과 저장
        self.experiments[experiment_id] = result
        
        self.logger.info(f"A/B 테스트 완료: {experiment_id} (개선율: {improvement:.2f}%)")
        return result
    
    def _measure_performance(self, data: pd.DataFrame, features: List[str], 
                           target_column: str) -> float:
        """모델 성능 측정"""
        try:
            # 피처와 타겟 분리
            available_features = [f for f in features if f in data.columns]
            if not available_features:
                self.logger.warning("사용 가능한 피처가 없습니다")
                return 0.0
                
            X = data[available_features]
            y = data[target_column]
            
            # 훈련/테스트 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42
            )
            
            # 모델 훈련
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)
            
            # 성능 측정
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            
            # R² 점수 반환 (높을수록 좋음)
            return model.score(X_test, y_test)
            
        except Exception as e:
            self.logger.error(f"성능 측정 실패: {e}")
            return 0.0
    
    def _statistical_test(self, control_values: pd.Series, treatment_values: pd.Series) -> float:
        """통계적 유의성 검정 (t-test)"""
        try:
            _, p_value = stats.ttest_ind(control_values, treatment_values)
            return p_value
        except:
            return 1.0  # 검정 실패 시 유의하지 않음으로 처리
    
    def _calculate_confidence_interval(self, control_perf: float, 
                                     treatment_perf: float, 
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """신뢰구간 계산"""
        # 간단한 추정 (실제로는 더 정교한 계산 필요)
        diff = treatment_perf - control_perf
        margin_error = abs(diff) * 0.1  # 대략적인 오차
        
        lower = diff - margin_error
        upper = diff + margin_error
        
        return (lower, upper)


class DriftDetector:
    """데이터 드리프트 감지 시스템"""
    
    def __init__(self, reference_data: pd.DataFrame):
        self.reference_data = reference_data
        self.logger = logging.getLogger("DriftDetector")
    
    def detect_drift(self, new_data: pd.DataFrame, 
                    threshold: float = 0.05) -> Dict[str, Dict[str, Any]]:
        """
        데이터 드리프트 감지
        
        Args:
            new_data: 새로운 데이터
            threshold: 드리프트 임계값
            
        Returns:
            Dict: 컬럼별 드리프트 감지 결과
        """
        self.logger.info("데이터 드리프트 감지 시작")
        
        drift_results = {}
        
        common_columns = set(self.reference_data.columns) & set(new_data.columns)
        
        for column in common_columns:
            if column == 'movie_id':
                continue
                
            drift_result = self._detect_column_drift(
                self.reference_data[column], 
                new_data[column], 
                threshold
            )
            
            drift_results[column] = drift_result
        
        self.logger.info(f"드리프트 감지 완료: {len(drift_results)}개 컬럼")
        return drift_results
    
    def _detect_column_drift(self, reference_series: pd.Series, 
                           new_series: pd.Series, 
                           threshold: float) -> Dict[str, Any]:
        """개별 컬럼 드리프트 감지"""
        result = {
            'has_drift': False,
            'p_value': 1.0,
            'test_statistic': 0.0,
            'drift_magnitude': 0.0,
            'test_method': 'unknown'
        }
        
        try:
            if pd.api.types.is_numeric_dtype(reference_series):
                # KS 테스트 (연속형 변수)
                statistic, p_value = stats.ks_2samp(
                    reference_series.dropna(), 
                    new_series.dropna()
                )
                result.update({
                    'p_value': p_value,
                    'test_statistic': statistic,
                    'has_drift': p_value < threshold,
                    'test_method': 'ks_test'
                })
                
                # 드리프트 크기 (평균 차이)
                ref_mean = reference_series.mean()
                new_mean = new_series.mean()
                drift_magnitude = abs(new_mean - ref_mean) / (ref_mean + 1e-8)
                result['drift_magnitude'] = drift_magnitude
                
            else:
                # 카이제곱 테스트 (범주형 변수)
                ref_counts = reference_series.value_counts()
                new_counts = new_series.value_counts()
                
                # 공통 카테고리만 사용
                common_categories = set(ref_counts.index) & set(new_counts.index)
                if len(common_categories) > 1:
                    ref_freq = [ref_counts.get(cat, 0) for cat in common_categories]
                    new_freq = [new_counts.get(cat, 0) for cat in common_categories]
                    
                    statistic, p_value = stats.chisquare(new_freq, ref_freq)
                    result.update({
                        'p_value': p_value,
                        'test_statistic': statistic,
                        'has_drift': p_value < threshold,
                        'test_method': 'chi_square'
                    })
        
        except Exception as e:
            self.logger.warning(f"드리프트 감지 실패 ({reference_series.name}): {e}")
        
        return result


def main():
    """테스트용 메인 함수"""
    # 샘플 데이터 생성
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'movie_id': range(100),
        'popularity': np.random.exponential(50, 100),
        'vote_average': np.random.normal(6.5, 1.2, 100),
        'vote_count': np.random.poisson(100, 100),
        'genre_action': np.random.binomial(1, 0.3, 100),
        'genre_drama': np.random.binomial(1, 0.4, 100),
        'release_year': np.random.randint(2000, 2025, 100)
    })
    
    # 품질 검증 테스트
    quality_checker = FeatureQualityChecker()
    quality_reports = quality_checker.validate_features(sample_data)
    
    print("=== 품질 검증 결과 ===")
    for feature, report in quality_reports.items():
        print(f"{feature}: 품질점수 {report.quality_score:.2f}")
    
    # 중요도 분석 테스트
    importance_analyzer = FeatureImportanceAnalyzer()
    importance_results = importance_analyzer.analyze_importance(sample_data)
    
    print("\n=== 피처 중요도 (통합) ===")
    combined_importance = importance_results.get('combined', {})
    sorted_features = sorted(combined_importance.items(), key=lambda x: x[1], reverse=True)
    for feature, score in sorted_features[:5]:
        print(f"{feature}: {score:.3f}")
    
    # A/B 테스트
    ab_tester = ABTestFramework()
    control_features = ['popularity', 'vote_count']
    treatment_features = ['popularity', 'vote_count', 'genre_action', 'release_year']
    
    ab_result = ab_tester.create_experiment(
        'test_exp_1', control_features, treatment_features, sample_data
    )
    
    print(f"\n=== A/B 테스트 결과 ===")
    print(f"개선율: {ab_result.improvement:.2f}%")
    print(f"유의성: {ab_result.is_significant} (p={ab_result.p_value:.3f})")


if __name__ == "__main__":
    main()

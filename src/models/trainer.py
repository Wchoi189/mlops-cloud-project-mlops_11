import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# 로깅 설정
logger = logging.getLogger(__name__)


class MovieRatingTrainer:
    """
    영화 평점 예측 모델 훈련 클래스
    MLOps 파이프라인 중심 설계
    """

    # 🎯 중앙집중화된 피처 정의 (핵심 수정사항)
    BASE_FEATURES = ["startYear", "runtimeMinutes", "numVotes"]
    TARGET_COLUMN = "averageRating"

    def __init__(self, experiment_name: str = "imdb_movie_rating"):
        self.experiment_name = experiment_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

        # MLflow 설정
        try:
            mlflow.set_experiment(self.experiment_name)
            logger.info(f"MLflow 실험 설정: {self.experiment_name}")
        except Exception as e:
            logger.warning(f"MLflow 설정 실패: {e}")

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """피처 준비 - 중앙집중화된 정의 사용"""
        logger.info("피처 준비 시작")

        # 기본 피처만 사용 (단순화)
        available_features = [col for col in self.BASE_FEATURES if col in df.columns]

        if not available_features:
            raise ValueError(
                f"필요한 피처가 없습니다. 필요: {self.BASE_FEATURES}, 사용가능: {list(df.columns)}"
            )

        logger.info(f"X contents####: {df[available_features].columns}")

        # 피처 매트릭스 생성
        X = df[available_features].copy()

        # 결측값 처리
        X = X.fillna(X.median())

        # 타겟 변수
        if self.TARGET_COLUMN not in df.columns:
            raise ValueError(f"타겟 컬럼이 없습니다: {self.TARGET_COLUMN}")

        y = df[self.TARGET_COLUMN].values

        # 피처명 저장
        self.feature_names = available_features

        logger.info(
            f"피처 준비 완료: {len(X)}개 샘플, {len(available_features)}개 피처"
        )
        logger.info(f"피처 목록: {self.feature_names}")

        return X.values, y

    def train_model(
        self, X: np.ndarray, y: np.ndarray, model_type: str = "random_forest"
    ) -> Dict[str, float]:
        """모델 훈련"""
        logger.info(f"모델 훈련 시작: {model_type}")

        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 피처 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 모델 선택
        if model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == "linear_regression":
            self.model = LinearRegression()
        else:
            raise ValueError(f"지원하지 않는 모델: {model_type}")

        # MLflow 실험 시작
        with mlflow.start_run():
            # 모델 훈련
            self.model.fit(X_train_scaled, y_train)

            # 예측 및 평가
            y_pred = self.model.predict(X_test_scaled)

            # 메트릭 계산
            metrics = {
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "mae": mean_absolute_error(y_test, y_pred),
                "r2_score": r2_score(y_test, y_pred),
            }

            # MLflow 로깅 (수정된 부분)
            try:
                # 파라미터 로깅
                mlflow.log_param("model_type", model_type)
                mlflow.log_param("features", self.feature_names)
                mlflow.log_param("n_features", len(self.feature_names))

                # 메트릭 로깅
                for metric_name, metric_value in metrics.items():
                    mlflow.log_metric(metric_name, metric_value)

                # 🎯 모델 로깅 개선 (서명과 예제 추가)
                input_example = pd.DataFrame(
                    X_train_scaled[:5], columns=self.feature_names
                )

                mlflow.sklearn.log_model(
                    self.model,
                    "model",
                    input_example=input_example,
                    registered_model_name=f"{model_type}_movie_rating",
                )

                logger.info("MLflow 로깅 완료")

            except Exception as e:
                logger.warning(f"MLflow 로깅 실패: {e}")

            logger.info("모델 훈련 완료:")
            logger.info(f"  - RMSE: {metrics['rmse']:.4f}")
            logger.info(f"  - MAE: {metrics['mae']:.4f}")
            logger.info(f"  - R²: {metrics['r2_score']:.4f}")

        return metrics

    def save_model(self) -> Dict[str, Union[str, List[str]]]:
        """모델과 스케일러 저장"""
        if self.model is None:
            raise ValueError("훈련된 모델이 없습니다.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{type(self.model).__name__.lower()}_{timestamp}.joblib"
        scaler_filename = f"scaler_{timestamp}.joblib"

        model_path = self.models_dir / model_filename
        scaler_path = self.models_dir / scaler_filename

        # 모델 정보와 함께 저장
        model_info = {
            "model": self.model,
            "feature_names": self.feature_names,
            "model_type": type(self.model).__name__,
            "timestamp": timestamp,
        }

        joblib.dump(model_info, model_path)
        joblib.dump(self.scaler, scaler_path)

        logger.info(f"모델 저장 완료: {model_path}")
        logger.info(f"스케일러 저장 완료: {scaler_path}")

        return {
            "model_path": str(model_path),
            "scaler_path": str(scaler_path),
            "feature_names": self.feature_names,
        }

    def get_feature_names(self) -> List[str]:
        """피처 이름 반환 (외부에서 사용할 수 있도록)"""
        return self.feature_names.copy()


def run_training_pipeline():
    """훈련 파이프라인 실행"""
    try:
        # 데이터 로드
        data_path = "data/processed/movies_with_ratings.csv"
        df = pd.read_csv(data_path)

        logger.info(f"데이터 로드 완료: {len(df):,}개 샘플")

        # 트레이너 초기화
        trainer = MovieRatingTrainer()

        # 피처 준비
        X, y = trainer.prepare_features(df)

        # 모델 훈련 (Random Forest)
        metrics = trainer.train_model(X, y, model_type="random_forest")

        # 모델 저장
        model_info = trainer.save_model()

        print("\n🎉 훈련 파이프라인 완료!")
        print(f"📊 성능: RMSE={metrics['rmse']:.4f}, R²={metrics['r2_score']:.4f}")
        print(f"💾 저장된 모델: {model_info['model_path']}")
        print(f"🔧 피처: {model_info['feature_names']}")

        return model_info

    except Exception as e:
        logger.error(f"훈련 파이프라인 실패: {e}")
        raise


if __name__ == "__main__":
    run_training_pipeline()

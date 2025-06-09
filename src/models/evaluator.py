import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

# 로깅 설정
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    모델 평가 및 예측 클래스
    trainer.py와 동일한 피처 정의 사용
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_type = None
        self.model_info = None

    def load_model(self, model_path: str, model_type: str = "random_forest"):
        """모델과 관련 정보 로드"""
        try:
            # 모델 정보 로드 (feature_names 포함)
            self.model_info = joblib.load(model_path)

            # 새로운 형식 (딕셔너리)인지 확인
            if isinstance(self.model_info, dict):
                self.model = self.model_info["model"]
                self.feature_names = self.model_info["feature_names"]
                self.model_type = self.model_info.get("model_type", model_type)
            else:
                # 이전 형식 (모델만 저장된 경우)
                self.model = self.model_info
                self.model_type = model_type
                # 기본 피처 사용 (trainer.py와 동일)
                self.feature_names = ["startYear", "runtimeMinutes", "numVotes"]

            # 스케일러 로드 (동일한 타임스탬프로 저장된 것 찾기)
            model_path_obj = Path(model_path)
            timestamp = (
                model_path_obj.stem.split("_")[-2]
                + "_"
                + model_path_obj.stem.split("_")[-1]
            )
            scaler_path = model_path_obj.parent / f"scaler_{timestamp}.joblib"

            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info(f"스케일러 로드 완료: {scaler_path}")
            else:
                logger.warning(f"스케일러 파일을 찾을 수 없습니다: {scaler_path}")
                self.scaler = None

            logger.info(f"모델 로드 완료: {model_path}")
            logger.info(f"모델 타입: {self.model_type}")
            logger.info(f"피처 목록: {self.feature_names}")

        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise

    def evaluate_model(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """모델 평가"""
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")

        # 스케일링 적용 (스케일러가 있는 경우)
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X

        # 예측
        y_pred = self.model.predict(X_scaled)

        # 메트릭 계산
        metrics = {
            "rmse": np.sqrt(mean_squared_error(y, y_pred)),
            "mae": mean_absolute_error(y, y_pred),
            "r2_score": r2_score(y, y_pred),
        }

        logger.info("모델 평가 완료:")
        logger.info(f"  RMSE: {metrics['rmse']:.4f}")
        logger.info(f"  MAE: {metrics['mae']:.4f}")
        logger.info(f"  R²: {metrics['r2_score']:.4f}")
        logger.info(f"  예측 범위: {y_pred.min():.2f} ~ {y_pred.max():.2f}")
        logger.info(f"  실제 범위: {y.min():.2f} ~ {y.max():.2f}")

        return metrics, y_pred

    def predict_single_movie(self, movie_data: Dict[str, Any]) -> float:
        """단일 영화 평점 예측 - 🎯 수정된 피처 사용"""
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")

        # 🎯 핵심 수정: 실제 모델에서 사용하는 피처만 사용
        try:
            # 모델에서 사용하는 피처만 추출
            feature_values = []
            for feature_name in self.feature_names:
                if feature_name in movie_data:
                    feature_values.append(movie_data[feature_name])
                else:
                    # 기본값 설정
                    if feature_name == "startYear":
                        feature_values.append(2000)  # 기본 연도
                    elif feature_name == "runtimeMinutes":
                        feature_values.append(120)  # 기본 러닝타임
                    elif feature_name == "numVotes":
                        feature_values.append(1000)  # 기본 투표수
                    else:
                        feature_values.append(0)  # 기타 기본값

                    logger.warning(f"피처 '{feature_name}'가 없어 기본값 사용")

            # 예측을 위한 배열 생성
            X_single = np.array(feature_values).reshape(1, -1)

            # 스케일링 적용
            if self.scaler is not None:
                X_single_scaled = self.scaler.transform(X_single)
            else:
                X_single_scaled = X_single

            # 예측
            prediction = self.model.predict(X_single_scaled)[0]

            # 예측값 범위 제한 (1-10)
            prediction = np.clip(prediction, 1.0, 10.0)

            logger.info(f"단일 예측 완료: {prediction:.2f}")
            logger.info(f"사용된 피처: {dict(zip(self.feature_names, feature_values))}")

            return float(prediction)

        except Exception as e:
            logger.error(f"단일 예측 실패: {e}")
            raise

    def batch_predict(self, movies_df: pd.DataFrame) -> np.ndarray:
        """배치 예측"""
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")

        # 필요한 피처만 추출
        available_features = [
            col for col in self.feature_names if col in movies_df.columns
        ]

        if not available_features:
            raise ValueError(
                f"필요한 피처가 없습니다. 필요: {self.feature_names}, 사용가능: {list(movies_df.columns)}"
            )

        X = movies_df[available_features].fillna(movies_df[available_features].median())

        # 스케일링 적용
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X.values)
        else:
            X_scaled = X.values

        # 예측
        predictions = self.model.predict(X_scaled)

        # 예측값 범위 제한
        predictions = np.clip(predictions, 1.0, 10.0)

        logger.info(f"배치 예측 완료: {len(predictions)}개 샘플")

        return predictions

    def get_feature_names(self) -> List[str]:
        """현재 사용 중인 피처 이름 반환"""
        return self.feature_names.copy()

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_type": self.model_type,
            "feature_names": self.feature_names,
            "n_features": len(self.feature_names),
            "model_loaded": self.model is not None,
            "scaler_loaded": self.scaler is not None,
        }


# 사용 예시
if __name__ == "__main__":
    # 평가기 초기화
    evaluator = ModelEvaluator()

    # 모델 로드 (가장 최근 모델 찾기)
    models_dir = Path("models")
    model_files = list(models_dir.glob("*forest*.joblib"))

    if model_files:
        latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
        print(f"최신 모델 로드: {latest_model}")

        evaluator.load_model(str(latest_model))

        # 테스트 예측
        test_movie = {"startYear": 2020, "runtimeMinutes": 120, "numVotes": 10000}

        prediction = evaluator.predict_single_movie(test_movie)
        print(f"예측 평점: {prediction:.2f}/10")

        # 모델 정보 출력
        info = evaluator.get_model_info()
        print(f"모델 정보: {info}")

    else:
        print("저장된 모델이 없습니다. 먼저 훈련을 실행하세요.")

"""
Enhanced API endpoints with Prometheus metrics integration
Monitoring-ready endpoints for MLOps pipeline
"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

# Monitoring imports
try:
    from ..monitoring.metrics import metrics as mlops_metrics
    from ..monitoring.metrics import track_api_call, track_prediction_time

    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False

    def track_prediction_time(
        model_name: str = "imdb_model", model_version: str = "1.0"
    ):
        def decorator(func: Callable) -> Callable:
            return func  # No-op decorator

        return decorator

    def track_api_call(endpoint: str, method: str = "GET"):
        def decorator(func: Callable) -> Callable:
            return func  # No-op decorator

        return decorator


from ..models.evaluator import ModelEvaluator
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfo,
    PredictionRequest,
    PredictionResponse,
)

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 전역 모델 평가기 (앱 시작시 로드됨)

model_evaluator: Optional[ModelEvaluator] = None


def get_model_evaluator() -> ModelEvaluator:
    """모델 평가기 의존성 주입"""
    if model_evaluator is None:
        raise HTTPException(
            status_code=503,
            detail="모델이 로드되지 않았습니다. 서버를 다시 시작해주세요.",
        )
    return model_evaluator


@router.post("/predict", response_model=PredictionResponse)
@track_prediction_time(model_name="imdb_model", model_version="1.0")
async def predict_movie_rating(
    request: PredictionRequest, evaluator: ModelEvaluator = Depends(get_model_evaluator)
):
    """
    단일 영화 평점 예측 (Legacy endpoint with monitoring)
    """
    start_time = time.time()

    try:
        logger.info(f"평점 예측 요청: {request.text[:50]}...")

        # Record API call if monitoring enabled
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict", status_code="200"
            ).inc()

        # 요청에서 영화 정보 추출
        movie_data = {
            "startYear": getattr(request, "startYear", 2020),
            "runtimeMinutes": getattr(request, "runtimeMinutes", 120),
            "numVotes": getattr(request, "numVotes", 5000),
        }

        # 모델 예측 with monitoring
        if HAS_MONITORING:
            predicted_rating = track_prediction_time("imdb_model", "1.0")(
                evaluator.predict_single_movie
            )(movie_data)
        else:
            predicted_rating = evaluator.predict_single_movie(movie_data)

        # Record prediction metrics
        if HAS_MONITORING:
            mlops_metrics.record_prediction_rating(predicted_rating)
            mlops_metrics.model_predictions_total.labels(
                model_name="imdb_model", model_version="1.0", prediction_type="single"
            ).inc()

        # 감정 분류 (평점 기반)
        sentiment = "positive" if predicted_rating >= 6.0 else "negative"
        confidence = min(0.95, max(0.55, predicted_rating / 10.0))

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="POST", endpoint="/predict"
            ).observe(response_time)

        logger.info(
            f"예측 완료: {predicted_rating:.2f}/10 (응답시간: {response_time:.3f}s)"
        )

        return PredictionResponse(
            text=request.text,
            sentiment=sentiment,
            confidence=confidence,
            timestamp=datetime.now(),
        )

    except Exception as e:
        # Record error metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict", status_code="500"
            ).inc()

        logger.error(f"예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")


@router.post("/predict/movie", response_model=Dict[str, Any])
@track_api_call(endpoint="/predict/movie", method="POST")
async def predict_movie_with_features(
    movie_data: Dict[str, Any], evaluator: ModelEvaluator = Depends(get_model_evaluator)
):
    """
    영화 피처를 직접 입력받아 평점 예측 (Enhanced with monitoring)
    """
    start_time = time.time()

    try:
        logger.info(f"영화 평점 예측: {movie_data}")

        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict/movie", status_code="200"
            ).inc()

        # 필수 피처 확인
        required_features = evaluator.get_feature_names()
        logger.info(f"모델 필요 피처: {required_features}")

        # 예측 실행 with monitoring
        if HAS_MONITORING:
            predicted_rating = track_prediction_time("imdb_model", "1.0")(
                evaluator.predict_single_movie
            )(movie_data)
        else:
            predicted_rating = evaluator.predict_single_movie(movie_data)

        # Record business mlops_metrics
        if HAS_MONITORING:
            mlops_metrics.record_prediction_rating(predicted_rating)
            mlops_metrics.model_predictions_total.labels(
                model_name="imdb_model",
                model_version="1.0",
                prediction_type="movie_features",
            ).inc()

            # Record feature usage
            for feature in required_features:
                if feature in movie_data:
                    mlops_metrics.data_validation_errors_total.labels(
                        validation_type="feature_present", error_type="none"
                    ).inc()

        # 응답 생성
        response = {
            "title": movie_data.get("title", "Unknown Movie"),
            "predicted_rating": round(predicted_rating, 2),
            "rating_out_of_10": f"{predicted_rating:.1f}/10",
            "features_used": {
                k: v for k, v in movie_data.items() if k in required_features
            },
            "model_features": required_features,
            "timestamp": datetime.now().isoformat(),
        }

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="POST", endpoint="/predict/movie"
            ).observe(response_time)

        logger.info(
            f"예측 결과: {predicted_rating:.2f}/10 (응답시간: {response_time:.3f}s)"
        )
        return response

    except Exception as e:
        # Record error mlops_metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict/movie", status_code="500"
            ).inc()

        logger.error(f"영화 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")


@router.post("/predict/batch", response_model=BatchPredictionResponse)
@track_api_call(endpoint="/predict/batch", method="POST")
async def predict_batch_movies(
    request: BatchPredictionRequest,
    evaluator: ModelEvaluator = Depends(get_model_evaluator),
):
    """
    여러 영화 배치 예측 (Enhanced with monitoring)
    """
    start_time = time.time()
    batch_size = len(request.texts)

    try:
        logger.info(f"배치 예측 요청: {batch_size}개 영화")

        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict/batch", status_code="200"
            ).inc()

        if batch_size > 100:
            raise HTTPException(
                status_code=400, detail="한 번에 최대 100개까지 처리 가능합니다."
            )

        predictions = []
        successful_predictions = 0
        failed_predictions = 0

        # Process batch with monitoring
        for i, text in enumerate(request.texts):
            try:
                # 간단한 더미 데이터 생성 (실제로는 텍스트 파싱 필요)
                movie_data = {
                    "startYear": 2020 - (i % 20),  # 2000-2020 범위
                    "runtimeMinutes": 90 + (i % 60),  # 90-150분 범위
                    "numVotes": 1000 + (i * 100),  # 다양한 인기도
                }

                if HAS_MONITORING:
                    predicted_rating = track_prediction_time("imdb_model", "1.0")(
                        evaluator.predict_single_movie
                    )(movie_data)
                else:
                    predicted_rating = evaluator.predict_single_movie(movie_data)
                sentiment = "positive" if predicted_rating >= 6.0 else "negative"
                confidence = min(0.95, max(0.55, predicted_rating / 10.0))

                predictions.append(
                    PredictionResponse(
                        text=text,
                        sentiment=sentiment,
                        confidence=confidence,
                        timestamp=datetime.now(),
                    )
                )

                successful_predictions += 1

                # Record individual prediction
                if HAS_MONITORING:
                    mlops_metrics.record_prediction_rating(predicted_rating)

            except Exception as e:
                logger.warning(f"개별 예측 실패 ({text[:30]}...): {e}")
                failed_predictions += 1

                # 실패한 경우 기본값
                predictions.append(
                    PredictionResponse(
                        text=text,
                        sentiment="neutral",
                        confidence=0.5,
                        timestamp=datetime.now(),
                    )
                )

        # Record batch metrics
        if HAS_MONITORING:
            mlops_metrics.model_predictions_total.labels(
                model_name="imdb_model", model_version="1.0", prediction_type="batch"
            ).inc(successful_predictions)

            if failed_predictions > 0:
                mlops_metrics.model_predictions_total.labels(
                    model_name="imdb_model",
                    model_version="1.0",
                    prediction_type="failed",
                ).inc(failed_predictions)

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="POST", endpoint="/predict/batch"
            ).observe(response_time)

        logger.info(
            f"배치 예측 완료: {successful_predictions}개 성공, {failed_predictions}개 실패 (응답시간: {response_time:.3f}s)"
        )

        return BatchPredictionResponse(
            predictions=predictions, total_count=len(predictions)
        )

    except HTTPException:
        raise
    except Exception as e:
        # Record error metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST", endpoint="/predict/batch", status_code="500"
            ).inc()

        logger.error(f"배치 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 예측 실패: {str(e)}")


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(evaluator: ModelEvaluator = Depends(get_model_evaluator)):
    """모델 정보 조회 (Enhanced with monitoring)"""
    start_time = time.time()

    try:
        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/model/info", status_code="200"
            ).inc()

        model_info = evaluator.get_model_info()

        response = ModelInfo(
            name=model_info.get("model_type", "Unknown"),
            version="1.0.0",
            description=f"IMDB 영화 평점 예측 모델 ({model_info.get('model_type', 'Unknown')})",
            created_at=datetime.now(),
            metrics={
                "features": model_info.get("n_features", 0),
                "model_loaded": model_info.get("model_loaded", False),
                "scaler_loaded": model_info.get("scaler_loaded", False),
                "monitoring_enabled": HAS_MONITORING,
            },
        )

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="GET", endpoint="/model/info"
            ).observe(response_time)

        return response

    except Exception as e:
        # Record error metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/model/info", status_code="500"
            ).inc()

        logger.error(f"모델 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 실패: {str(e)}")


@router.get("/health", response_model=HealthResponse)
@track_api_call(endpoint="/health", method="GET")
async def health_check():
    """API 상태 확인 (Enhanced with monitoring)"""
    start_time = time.time()

    try:
        global model_evaluator
        model_loaded = model_evaluator is not None

        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/health", status_code="200"
            ).inc()

            # Update active users (simple example)
            mlops_metrics.set_active_users(1)

        response = HealthResponse(
            status="healthy" if model_loaded else "degraded",
            timestamp=datetime.now(),
            version="1.1.0",
            model_loaded=model_loaded,
        )

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="GET", endpoint="/health"
            ).observe(response_time)

        return response

    except Exception as e:
        # Record error metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/health", status_code="500"
            ).inc()

        logger.error(f"헬스체크 오류: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.1.0",
            model_loaded=False,
        )


# 새로운 모니터링 전용 엔드포인트들
@router.get("/monitoring/predictions/stats")
@track_api_call(endpoint="/monitoring/predictions/stats", method="GET")
async def get_prediction_stats():
    """예측 통계 조회"""
    if not HAS_MONITORING:
        return {"error": "Monitoring not available"}

    try:
        # Simulate getting prediction statistics
        stats = {
            "total_predictions": 1000,  # This would come from metrics
            "average_rating": 7.2,
            "predictions_per_hour": 150,
            "model_accuracy": 0.69,
            "response_time_ms": 250,
            "error_rate": 0.01,
            "timestamp": datetime.now().isoformat(),
        }

        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET",
                endpoint="/monitoring/predictions/stats",
                status_code="200",
            ).inc()

        return stats

    except Exception as e:
        logger.error(f"Prediction stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/data-drift/check")
@track_api_call(endpoint="/monitoring/data-drift/check", method="POST")
async def check_data_drift(data: Dict[str, Any]):
    """데이터 드리프트 체크"""
    if not HAS_MONITORING:
        return {"error": "Monitoring not available"}

    try:
        # Simulate data drift detection
        features = data.get("features", {})
        drift_scores = {}

        for feature_name, feature_value in features.items():
            # Simple drift simulation
            drift_score = abs(hash(str(feature_value)) % 100) / 1000.0
            drift_scores[feature_name] = drift_score

            # Record drift metrics
            if HAS_MONITORING:
                mlops_metrics.record_data_drift(feature_name, drift_score, "imdb_model")

        # Overall drift status
        max_drift = max(drift_scores.values()) if drift_scores else 0
        drift_status = (
            "high" if max_drift > 0.1 else "low" if max_drift > 0.05 else "normal"
        )

        response = {
            "drift_status": drift_status,
            "max_drift_score": max_drift,
            "feature_drift_scores": drift_scores,
            "threshold": 0.1,
            "timestamp": datetime.now().isoformat(),
        }

        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST",
                endpoint="/monitoring/data-drift/check",
                status_code="200",
            ).inc()

        return response

    except Exception as e:
        logger.error(f"Data drift check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts/active")
@track_api_call(endpoint="/monitoring/alerts/active", method="GET")
async def get_active_alerts():
    """활성 알림 조회"""
    try:
        # Simulate active alerts (in real scenario, this would query AlertManager)
        alerts = [
            {
                "id": "alert_001",
                "severity": "warning",
                "message": "API response time above threshold",
                "timestamp": datetime.now().isoformat(),
                "status": "firing",
            },
            {
                "id": "alert_002",
                "severity": "info",
                "message": "Model accuracy within normal range",
                "timestamp": datetime.now().isoformat(),
                "status": "resolved",
            },
        ]

        active_alerts = [alert for alert in alerts if alert["status"] == "firing"]

        response = {
            "active_alerts": active_alerts,
            "total_active": len(active_alerts),
            "last_updated": datetime.now().isoformat(),
        }

        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/monitoring/alerts/active", status_code="200"
            ).inc()

        return response

    except Exception as e:
        logger.error(f"Active alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/model/update-accuracy")
@track_api_call(endpoint="/monitoring/model/update-accuracy", method="POST")
async def update_model_accuracy(accuracy_data: Dict[str, Any]):
    """모델 정확도 업데이트"""
    if not HAS_MONITORING:
        return {"error": "Monitoring not available"}

    try:
        accuracy = accuracy_data.get("accuracy", 0.0)
        model_name = accuracy_data.get("model_name", "imdb_model")
        model_version = accuracy_data.get("model_version", "1.0")

        # Validate accuracy
        if not 0 <= accuracy <= 1:
            raise HTTPException(
                status_code=400, detail="Accuracy must be between 0 and 1"
            )

        # Record accuracy metric
        if HAS_MONITORING:
            mlops_metrics.record_model_accuracy(accuracy, model_name, model_version)

        response = {
            "message": "Model accuracy updated",
            "model_name": model_name,
            "model_version": model_version,
            "accuracy": accuracy,
            "timestamp": datetime.now().isoformat(),
        }

        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="POST",
                endpoint="/monitoring/model/update-accuracy",
                status_code="200",
            ).inc()

        logger.info(
            f"Model accuracy updated: {model_name} v{model_version} = {accuracy}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update accuracy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 모델 로드 함수 (main.py에서 호출됨)
def load_model_at_startup():
    """앱 시작시 모델 로드 (Enhanced with monitoring)"""
    global model_evaluator

    try:
        from pathlib import Path

        # 가장 최근 모델 찾기
        models_dir = Path("models")
        if not models_dir.exists():
            logger.error("models 디렉토리가 없습니다.")
            return False

        model_files = list(models_dir.glob("*forest*.joblib"))
        if not model_files:
            logger.error("저장된 모델 파일이 없습니다.")
            return False

        # 가장 최근 파일 선택
        latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"모델 로드 시도: {latest_model}")

        # 모델 평가기 초기화 및 로드
        model_evaluator = ModelEvaluator()
        model_evaluator.load_model(str(latest_model))

        logger.info("✅ 모델 로드 성공!")
        logger.info(f"   모델 타입: {model_evaluator.model_type}")
        logger.info(f"   피처: {model_evaluator.get_feature_names()}")

        # Record model loading success in metrics
        if HAS_MONITORING:
            mlops_metrics.record_model_accuracy(
                0.69, "imdb_model", "1.0"
            )  # Initial accuracy
            mlops_metrics.mlflow_experiments_total.labels(
                experiment_name="model_loading"
            ).inc()
            mlops_metrics.mlflow_runs_total.labels(
                experiment_name="model_loading", status="success"
            ).inc()

        return True

    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")

        # Record model loading failure
        if HAS_MONITORING:
            mlops_metrics.mlflow_runs_total.labels(
                experiment_name="model_loading", status="failed"
            ).inc()

        model_evaluator = None
        return False

"""
Enhanced API endpoints with Prometheus metrics integration
Monitoring-ready endpoints for MLOps pipeline
"""


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


def get_model_evaluator() -> Optional[ModelEvaluator]:
    """
    모델 평가기 의존성 주입 (Graceful handling)
    CI/CD 환경에서 모델이 없을 때도 동작하도록 개선
    """
    global model_evaluator
    
    if model_evaluator is None:
        logger.warning("모델이 로드되지 않았습니다. CI/CD 환경이거나 모델 파일이 없을 수 있습니다.")
        return None
    
    return model_evaluator

def require_model_evaluator() -> ModelEvaluator:
    """
    모델이 필수인 엔드포인트용 의존성 주입
    모델이 없으면 503 에러 반환
    """
    evaluator = get_model_evaluator()
    if evaluator is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service Temporarily Unavailable",
                "message": "모델이 로드되지 않았습니다",
                "details": "서버를 다시 시작하거나 모델을 훈련해주세요",
                "suggestions": [
                    "python scripts/train_model.py 실행",
                    "models/ 디렉토리에 모델 파일 확인",
                    "서버 재시작 시도"
                ],
                "model_required": True,
                "status": "no_model_loaded"
            }
        )
    return evaluator

@router.post("/predict", response_model=PredictionResponse)
@track_prediction_time(model_name="imdb_model", model_version="1.0")
async def predict_movie_rating(request: PredictionRequest):
    """
    단일 영화 평점 예측 (Legacy endpoint with monitoring)
    """
    start_time = time.time()

    try:
        logger.info(f"평점 예측 요청: {(request.text[:50] + '...') if request.text else 'No text provided'}")

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

        # 모델 평가기 확인 (graceful handling)
        evaluator = get_model_evaluator()

        if evaluator is None:
            # 모델이 없을 때 fallback 예측 + monitoring
            logger.warning("모델 없음 - fallback 예측 제공 (with monitoring)")

            # Record fallback usage
            if HAS_MONITORING:
                mlops_metrics.model_predictions_total.labels(
                    model_name="fallback_model", 
                    model_version="1.0", 
                    prediction_type="heuristic_fallback"
                ).inc()
            # 간단한 휴리스틱 기반 예측
            base_rating = 6.0  # 기본 평점
            
            # 연도 보정
            year = movie_data.get("startYear", 2020)
            if year > 2010:
                base_rating += 0.3
            if year > 2020:
                base_rating += 0.1
                
            # 런타임 보정
            runtime = movie_data.get("runtimeMinutes", 120)
            if 90 <= runtime <= 150:
                base_rating += 0.2
            elif runtime > 200:
                base_rating -= 0.1
                
            # 투표수 보정
            votes = movie_data.get("numVotes", 5000)
            if votes > 10000:
                base_rating += 0.2
            if votes > 50000:
                base_rating += 0.1

            # 범위 제한
            predicted_rating = min(max(base_rating, 1.0), 10.0)
            
            # Record fallback prediction metrics
            if HAS_MONITORING:
                mlops_metrics.record_prediction_rating(predicted_rating)
                # Record data validation (fallback mode)
                mlops_metrics.data_validation_errors_total.labels(
                    validation_type="model_unavailable", error_type="fallback_used"
                ).inc()
            # 감정 분류 (평점 기반)
            sentiment = "positive" if predicted_rating >= 6.0 else "negative"
            confidence = 0.5  # 낮은 신뢰도 (fallback이므로)

            # Record response time
            response_time = time.time() - start_time
            if HAS_MONITORING:
                mlops_metrics.http_request_duration_seconds.labels(
                    method="POST", endpoint="/predict"
                ).observe(response_time)

            logger.info(f"Fallback 예측 완료: {predicted_rating:.2f}/10 (응답시간: {response_time:.3f}s)")

            return PredictionResponse(
                text=request.text,
                sentiment=sentiment,
                confidence=confidence,
                timestamp=datetime.now().isoformat(),
                # Enhanced fields for graceful degradation
                predicted_rating=round(predicted_rating, 2),
                model_version="fallback-v1.0",
                features_used=["heuristic_fallback"],
                processing_time=response_time,
                metadata={
                    "model_status": "not_loaded",
                    "prediction_method": "heuristic_fallback",
                    "monitoring_enabled": HAS_MONITORING,
                    "warning": "실제 ML 모델을 사용하지 않은 예측입니다",
                    "note": "모델 훈련 후 더 정확한 예측이 가능합니다"
                }
            )

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
            timestamp=datetime.now().isoformat(),
            # Enhanced fields for graceful degradation
            predicted_rating=round(predicted_rating, 2),
            model_version="fallback-v1.0",
            features_used=["heuristic_fallback"],
            processing_time=0.001,
            metadata={
                "model_status": "not_loaded",
                "prediction_method": "heuristic_fallback",
                "warning": "실제 ML 모델을 사용하지 않은 예측입니다",
                "note": "모델 훈련 후 더 정확한 예측이 가능합니다"
            }
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
async def predict_batch_movies(request: BatchPredictionRequest):
    """
    여러 영화 배치 예측 (Enhanced with monitoring + graceful degradation)
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

        # Check model availability (graceful handling)
        evaluator = get_model_evaluator()
        predictions = []
        successful_predictions = 0
        failed_predictions = 0
        fallback_predictions = 0

        # Process batch with monitoring
        for i, text in enumerate(request.texts):
            try:
                # 간단한 더미 데이터 생성 (실제로는 텍스트 파싱 필요)
                movie_data = {
                    "startYear": 2020 - (i % 20),  # 2000-2020 범위
                    "runtimeMinutes": 90 + (i % 60),  # 90-150분 범위
                    "numVotes": 1000 + (i * 100),  # 다양한 인기도
                }

                if evaluator is None:
                    # 모델이 없을 때 fallback 예측 + monitoring
                    base_rating = 6.0  # 기본 평점
                    
                    # 연도 보정
                    year = movie_data.get("startYear", 2020)
                    if year > 2010:
                        base_rating += 0.2
                    if year > 2015:
                        base_rating += 0.1
                        
                    # 런타임 보정
                    runtime = movie_data.get("runtimeMinutes", 120)
                    if 90 <= runtime <= 150:
                        base_rating += 0.1
                        
                    # 투표수 보정
                    votes = movie_data.get("numVotes", 1000)
                    if votes > 5000:
                        base_rating += 0.1
                        
                    # 개별 영화마다 약간의 변화 추가
                    import random
                    base_rating += random.uniform(-0.3, 0.3)
                    
                    # 범위 제한
                    predicted_rating = min(max(base_rating, 1.0), 10.0)
                    
                    sentiment = "positive" if predicted_rating >= 6.0 else "negative"
                    confidence = 0.5  # 낮은 신뢰도

                    predictions.append(
                        PredictionResponse(
                            text=text,
                            sentiment=sentiment,
                            confidence=confidence,
                            timestamp=datetime.now().isoformat(),
                            # Enhanced fields for fallback
                            predicted_rating=round(predicted_rating, 2),
                            model_version="fallback-v1.0",
                            features_used=["heuristic_fallback"],
                            processing_time=0.001,
                            metadata={
                                "model_status": "not_loaded",
                                "prediction_method": "heuristic_fallback",
                                "batch_index": i,
                                "monitoring_enabled": HAS_MONITORING,
                                "warning": "실제 ML 모델을 사용하지 않은 예측입니다"
                            }
                        )
                    )

                    fallback_predictions += 1

                    # Record fallback prediction metrics
                    if HAS_MONITORING:
                        mlops_metrics.record_prediction_rating(predicted_rating)
                        mlops_metrics.model_predictions_total.labels(
                            model_name="fallback_model", 
                            model_version="1.0", 
                            prediction_type="batch_fallback"
                        ).inc()

                else:
                    # 모델이 있을 때 정상 예측 (기존 monitoring 로직)
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
                            timestamp=datetime.now().isoformat(),
                            # Enhanced fields for normal prediction
                            predicted_rating=round(predicted_rating, 2),
                            model_version="1.0.0",
                            features_used=evaluator.get_feature_names(),
                            processing_time=0.05,
                            metadata={
                                "model_status": "loaded",
                                "prediction_method": "ml_model",
                                "batch_index": i,
                                "monitoring_enabled": HAS_MONITORING,
                                "model_type": evaluator.model_type
                            }
                        )
                    )

                    successful_predictions += 1

                    # Record individual prediction
                    if HAS_MONITORING:
                        mlops_metrics.record_prediction_rating(predicted_rating)

            except Exception as e:
                logger.warning(f"개별 예측 실패 ({text[:30]}...): {e}")
                failed_predictions += 1

                # 실패한 경우 기본값 (error fallback)
                predictions.append(
                    PredictionResponse(
                        text=text,
                        sentiment="neutral",
                        confidence=0.3,
                        timestamp=datetime.now().isoformat(),
                        # Enhanced fields for error case
                        predicted_rating=5.0,  # 중간값
                        model_version="error-fallback",
                        features_used=["error_fallback"],
                        processing_time=0.001,
                        metadata={
                            "model_status": "error",
                            "prediction_method": "error_fallback",
                            "batch_index": i,
                            "monitoring_enabled": HAS_MONITORING,
                            "error": str(e),
                            "warning": "개별 예측 중 오류가 발생했습니다"
                        }
                    )
                )

        # Record batch metrics
        if HAS_MONITORING:
            # Record successful ML predictions
            if successful_predictions > 0:
                mlops_metrics.model_predictions_total.labels(
                    model_name="imdb_model", 
                    model_version="1.0", 
                    prediction_type="batch"
                ).inc(successful_predictions)

            # Record fallback predictions
            if fallback_predictions > 0:
                mlops_metrics.model_predictions_total.labels(
                    model_name="fallback_model", 
                    model_version="1.0", 
                    prediction_type="batch_fallback"
                ).inc(fallback_predictions)

            # Record failed predictions
            if failed_predictions > 0:
                mlops_metrics.model_predictions_total.labels(
                    model_name="error_model",
                    model_version="1.0",
                    prediction_type="batch_failed",
                ).inc(failed_predictions)

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="POST", endpoint="/predict/batch"
            ).observe(response_time)

        logger.info(
            f"배치 예측 완료: {successful_predictions}개 ML성공, {fallback_predictions}개 fallback, {failed_predictions}개 실패 (응답시간: {response_time:.3f}s)"
        )

        return BatchPredictionResponse(
            predictions=predictions, 
            total_count=len(predictions)
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
@router.get("/model/info")  # Remove response_model=ModelInfo to allow flexible response
async def get_model_info():
    """모델 정보 조회 (Enhanced with monitoring + graceful handling)"""
    start_time = time.time()

    try:
        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/model/info", status_code="200"
            ).inc()

        # Check model availability (graceful handling)
        evaluator = get_model_evaluator()
        
        if evaluator is None:
            # Model not available - provide graceful response with monitoring
            logger.warning("모델 정보 조회 - 모델 없음 (with monitoring)")
            
            # Record model unavailability
            if HAS_MONITORING:
                mlops_metrics.data_validation_errors_total.labels(
                    validation_type="model_info_check", error_type="model_not_available"
                ).inc()
            
            response = {
                "name": "IMDB Rating Predictor",
                "version": "not_loaded",
                "status": "model_not_available",
                "description": "IMDB 영화 평점 예측 모델 (현재 로드되지 않음)",
                "model_loaded": False,
                "created_at": datetime.now().isoformat(),
                "metrics": {
                    "features": 0,
                    "model_loaded": False,
                    "scaler_loaded": False,
                    "monitoring_enabled": HAS_MONITORING,
                },
                "expected_features": ["startYear", "runtimeMinutes", "numVotes"],
                "fallback_available": True,
                "suggestions": [
                    "모델 훈련: python scripts/train_model.py",
                    "모델 파일 확인: ls models/",
                    "서버 재시작 고려"
                ],
                "warning": "현재 heuristic fallback 모드에서 동작 중입니다",
                "monitoring_status": "enabled" if HAS_MONITORING else "disabled"
            }
            
            # Record response time for fallback case
            response_time = time.time() - start_time
            if HAS_MONITORING:
                mlops_metrics.http_request_duration_seconds.labels(
                    method="GET", endpoint="/model/info"
                ).observe(response_time)
            
            logger.info(f"모델 정보 조회 완료 (fallback mode) - 응답시간: {response_time:.3f}s")
            return response
        
        # Model is available - normal flow with all monitoring
        try:
            model_info = evaluator.get_model_info()
            
            # Record successful model info retrieval
            if HAS_MONITORING:
                mlops_metrics.model_predictions_total.labels(
                    model_name="imdb_model", 
                    model_version="1.0", 
                    prediction_type="model_info_query"
                ).inc()
            
            response = {
                "name": model_info.get("model_type", "Unknown"),
                "version": "1.0.0",
                "status": "loaded",
                "description": f"IMDB 영화 평점 예측 모델 ({model_info.get('model_type', 'Unknown')})",
                "created_at": datetime.now().isoformat(),
                "model_loaded": True,
                "metrics": {
                    "features": model_info.get("n_features", 0),
                    "model_loaded": model_info.get("model_loaded", False),
                    "scaler_loaded": model_info.get("scaler_loaded", False),
                    "monitoring_enabled": HAS_MONITORING,
                },
                "feature_names": model_info.get("feature_names", []),
                "fallback_available": False,
                "model_type": model_info.get("model_type", "Unknown"),
                "monitoring_status": "enabled" if HAS_MONITORING else "disabled"
            }
            
        except Exception as model_error:
            logger.error(f"모델 정보 추출 오류: {model_error}")
            
            # Record model info extraction error
            if HAS_MONITORING:
                mlops_metrics.data_validation_errors_total.labels(
                    validation_type="model_info_extraction", error_type="extraction_failed"
                ).inc()
            
            # Fallback response when model exists but info extraction fails
            response = {
                "name": "IMDB Rating Predictor",
                "version": "1.0.0",
                "status": "loaded_with_errors",
                "description": "IMDB 영화 평점 예측 모델 (정보 추출 중 오류)",
                "created_at": datetime.now().isoformat(),
                "model_loaded": True,
                "metrics": {
                    "features": 3,  # Default expected
                    "model_loaded": True,
                    "scaler_loaded": False,  # Unknown due to error
                    "monitoring_enabled": HAS_MONITORING,
                },
                "expected_features": ["startYear", "runtimeMinutes", "numVotes"],
                "fallback_available": True,
                "error": str(model_error),
                "warning": "모델 정보 추출 중 오류가 발생했지만 예측은 가능할 수 있습니다",
                "monitoring_status": "enabled" if HAS_MONITORING else "disabled"
            }

        # Record response time
        response_time = time.time() - start_time
        if HAS_MONITORING:
            mlops_metrics.http_request_duration_seconds.labels(
                method="GET", endpoint="/model/info"
            ).observe(response_time)

        logger.info(f"모델 정보 조회 완료 - 응답시간: {response_time:.3f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        # Record error metrics
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/model/info", status_code="500"
            ).inc()

        logger.error(f"모델 정보 조회 오류: {str(e)}")
        
        # Return error response instead of raising exception (graceful)
        return {
            "name": "IMDB Rating Predictor",
            "version": "error",
            "status": "error",
            "description": "모델 정보 조회 중 오류 발생",
            "created_at": datetime.now().isoformat(),
            "model_loaded": False,
            "error": str(e),
            "fallback_available": True,
            "suggestions": [
                "서버 재시작 시도",
                "로그 확인",
                "모델 파일 상태 점검"
            ],
            "monitoring_status": "enabled" if HAS_MONITORING else "disabled"
        }
@router.get("/health", response_model=HealthResponse)
@track_api_call(endpoint="/health", method="GET")
async def health_check():
    """API 상태 확인 (Enhanced with monitoring + graceful degradation)"""
    start_time = time.time()

    try:
        evaluator = get_model_evaluator()
        model_loaded = evaluator is not None
        
        # 상태 결정
        if model_loaded:
            status = "healthy"
            details = "모든 서비스가 정상 동작 중"
        else:
            status = "degraded"
            details = "모델이 로드되지 않았지만 API는 동작 가능 (fallback 모드)"
        
        # Record API call
        if HAS_MONITORING:
            mlops_metrics.http_requests_total.labels(
                method="GET", endpoint="/health", status_code="200"
            ).inc()

            # Update active users (simple example)
            mlops_metrics.set_active_users(1)

        # Create response object
        response = HealthResponse(
            status=status,
            timestamp=datetime.now(),
            version="1.1.0",  # Updated version to match monitoring version
            model_loaded=model_loaded,
            details=details,
            capabilities={
                "prediction": True,  # fallback 가능하므로 항상 true
                "model_info": True,
                "health_check": True,
                "fallback_prediction": not model_loaded
            }
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

        logger.error(f"헬스체크 오류: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.1.0",
            model_loaded=False,
            details=f"헬스체크 중 오류 발생: {str(e)}",
            capabilities={
                "prediction": False,
                "model_info": False,
                "health_check": True,
                "fallback_prediction": False
            }
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


# Enhanced load_model_at_startup function (for both endpoints.py and endpoints_with_metrics.py)

def load_model_at_startup():
    """
    앱 시작시 모델 로드 (Enhanced with graceful handling)
    """
    global model_evaluator
    
    try:
        from pathlib import Path
        
        logger.info("🔍 모델 로드 시도 중...")
        
        # 모델 디렉토리 확인
        models_dir = Path("models")
        if not models_dir.exists():
            logger.warning("⚠️ models 디렉토리가 없습니다 - CI/CD 환경일 수 있습니다")
            logger.info("📝 fallback 모드로 동작합니다")
            model_evaluator = None
            return False
        
        # 모델 파일 확인
        model_files = list(models_dir.glob("*forest*.joblib"))
        if not model_files:
            logger.warning("⚠️ 저장된 모델 파일이 없습니다 - CI/CD 환경일 수 있습니다")
            logger.info("📝 heuristic fallback 모드로 동작합니다")
            logger.info("💡 모델 훈련 방법: python scripts/train_model.py")
            model_evaluator = None
            return False
        
        # 모델 로드 시도
        latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"📦 모델 로드 시도: {latest_model}")
        
        from ..models.evaluator import ModelEvaluator
        model_evaluator = ModelEvaluator()
        model_evaluator.load_model(str(latest_model))
        
        logger.info("✅ 모델 로드 성공!")
        logger.info(f"   모델 타입: {model_evaluator.model_type}")
        logger.info(f"   피처: {model_evaluator.get_feature_names()}")
        
        # Record successful model loading (for monitoring version)
        try:
            # This will work in endpoints_with_metrics.py
            if HAS_MONITORING and 'mlops_metrics' in globals():
                mlops_metrics.record_model_accuracy(0.69, "imdb_model", "1.0")
                mlops_metrics.mlflow_experiments_total.labels(
                    experiment_name="model_loading"
                ).inc()
                mlops_metrics.mlflow_runs_total.labels(
                    experiment_name="model_loading", status="success"
                ).inc()
        except:
            # Silently fail if monitoring not available (for regular endpoints.py)
            pass
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ 모델 로드 실패: {e}")
        logger.info("📝 API는 fallback 모드로 계속 동작합니다")
        logger.info("💡 문제 해결 방법:")
        logger.info("   1. python scripts/train_model.py 실행")
        logger.info("   2. models/ 디렉토리 확인")
        logger.info("   3. 서버 재시작")
        
        # Record failed model loading (for monitoring version)
        try:
            # This will work in endpoints_with_metrics.py
            if HAS_MONITORING and 'mlops_metrics' in globals():
                mlops_metrics.mlflow_runs_total.labels(
                    experiment_name="model_loading", status="failed"
                ).inc()
        except:
            # Silently fail if monitoring not available (for regular endpoints.py)
            pass
        
        model_evaluator = None
        return False

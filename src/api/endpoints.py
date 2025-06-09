import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

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
async def predict_movie_rating(
    request: PredictionRequest, evaluator: ModelEvaluator = Depends(get_model_evaluator)
):
    """
    단일 영화 평점 예측

    요청 예시:
    {
        "text": "영화 제목",
        "startYear": 2020,
        "runtimeMinutes": 120,
        "numVotes": 10000
    }
    """
    try:
        logger.info(f"평점 예측 요청: {request.text[:50]}...")

        # 요청에서 영화 정보 추출
        # 실제로는 text에서 영화 정보를 파싱하거나, API 요청에 직접 포함
        # 여기서는 간단한 예시로 기본값 사용
        movie_data = {
            "startYear": getattr(request, "startYear", 2020),
            "runtimeMinutes": getattr(request, "runtimeMinutes", 120),
            "numVotes": getattr(request, "numVotes", 5000),
        }

        # 모델 예측
        predicted_rating = evaluator.predict_single_movie(movie_data)

        # 감정 분류 (평점 기반)
        sentiment = "positive" if predicted_rating >= 6.0 else "negative"
        confidence = min(0.95, max(0.55, predicted_rating / 10.0))

        logger.info(f"예측 완료: {predicted_rating:.2f}/10")

        return PredictionResponse(
            text=request.text,
            sentiment=sentiment,
            confidence=confidence,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")


@router.post("/predict/movie", response_model=Dict[str, Any])
async def predict_movie_with_features(
    movie_data: Dict[str, Any], evaluator: ModelEvaluator = Depends(get_model_evaluator)
):
    """
    영화 피처를 직접 입력받아 평점 예측

    요청 예시:
    {
        "title": "영화 제목",
        "startYear": 2020,
        "runtimeMinutes": 120,
        "numVotes": 10000
    }
    """
    try:
        logger.info(f"영화 평점 예측: {movie_data}")

        # 필수 피처 확인
        required_features = evaluator.get_feature_names()
        logger.info(f"모델 필요 피처: {required_features}")

        # 예측 실행
        predicted_rating = evaluator.predict_single_movie(movie_data)

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

        logger.info(f"예측 결과: {predicted_rating:.2f}/10")
        return response

    except Exception as e:
        logger.error(f"영화 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_movies(
    request: BatchPredictionRequest,
    evaluator: ModelEvaluator = Depends(get_model_evaluator),
):
    """
    여러 영화 배치 예측
    """
    try:
        logger.info(f"배치 예측 요청: {len(request.texts)}개 영화")

        if len(request.texts) > 100:
            raise HTTPException(
                status_code=400, detail="한 번에 최대 100개까지 처리 가능합니다."
            )

        predictions = []

        for i, text in enumerate(request.texts):
            try:
                # 간단한 더미 데이터 생성 (실제로는 텍스트 파싱 필요)
                movie_data = {
                    "startYear": 2020 - (i % 20),  # 2000-2020 범위
                    "runtimeMinutes": 90 + (i % 60),  # 90-150분 범위
                    "numVotes": 1000 + (i * 100),  # 다양한 인기도
                }

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

            except Exception as e:
                logger.warning(f"개별 예측 실패 ({text[:30]}...): {e}")
                # 실패한 경우 기본값
                predictions.append(
                    PredictionResponse(
                        text=text,
                        sentiment="neutral",
                        confidence=0.5,
                        timestamp=datetime.now(),
                    )
                )

        logger.info(f"배치 예측 완료: {len(predictions)}개 결과")

        return BatchPredictionResponse(
            predictions=predictions, total_count=len(predictions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 예측 실패: {str(e)}")


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(evaluator: ModelEvaluator = Depends(get_model_evaluator)):
    """모델 정보 조회"""
    try:
        model_info = evaluator.get_model_info()

        return ModelInfo(
            name=model_info.get("model_type", "Unknown"),
            version="1.0.0",
            description=f"IMDB 영화 평점 예측 모델 ({model_info.get('model_type', 'Unknown')})",
            created_at=datetime.now(),
            metrics={
                "features": model_info.get("n_features", 0),
                "model_loaded": model_info.get("model_loaded", False),
                "scaler_loaded": model_info.get("scaler_loaded", False),
            },
        )

    except Exception as e:
        logger.error(f"모델 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 실패: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """API 상태 확인"""
    try:
        model_loaded = model_evaluator is not None

        return HealthResponse(
            status="healthy" if model_loaded else "degraded",
            timestamp=datetime.now(),
            version="1.0.0",
            model_loaded=model_loaded,
        )

    except Exception as e:
        logger.error(f"헬스체크 오류: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0",
            model_loaded=False,
        )


# 모델 로드 함수 (main.py에서 호출됨)
def load_model_at_startup():
    """앱 시작시 모델 로드"""
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

        return True

    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")
        model_evaluator = None
        return False

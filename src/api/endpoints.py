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
async def predict_movie_rating(request: PredictionRequest):
    """
    단일 영화 평점 예측 (Enhanced with graceful degradation)

    요청 예시:
    {
        "text": "영화 제목",
        "startYear": 2020,
        "runtimeMinutes": 120,
        "numVotes": 10000
    }
    """
    try:
        logger.info(f"평점 예측 요청: {(request.text[:50] + '...') if request.text else 'No text provided'}")

        # 요청에서 영화 정보 추출
        movie_data = {
            "startYear": getattr(request, "startYear", 2020),
            "runtimeMinutes": getattr(request, "runtimeMinutes", 120),
            "numVotes": getattr(request, "numVotes", 5000),
        }

        # 모델 평가기 확인 (graceful handling)
        evaluator = get_model_evaluator()
        
        if evaluator is None:
            # 모델이 없을 때 fallback 예측
            logger.warning("모델 없음 - fallback 예측 제공")
            
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
            
            # 감정 분류 (평점 기반)
            sentiment = "positive" if predicted_rating >= 6.0 else "negative"
            confidence = 0.5  # 낮은 신뢰도 (fallback이므로)

            logger.info(f"Fallback 예측 완료: {predicted_rating:.2f}/10")

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
        
        # 모델이 있을 때 정상 예측 (기존 로직)
        predicted_rating = evaluator.predict_single_movie(movie_data)

        # 감정 분류 (평점 기반)
        sentiment = "positive" if predicted_rating >= 6.0 else "negative"
        confidence = min(0.95, max(0.55, predicted_rating / 10.0))

        logger.info(f"예측 완료: {predicted_rating:.2f}/10")

        return PredictionResponse(
            text=request.text,
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
                "model_type": evaluator.model_type
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")   
@router.post("/predict/movie", response_model=Dict[str, Any])
async def predict_movie_with_features(movie_data: Dict[str, Any]):
    """
    영화 피처 기반 평점 예측 (Graceful degradation)
    모델이 없을 때 적절한 응답 제공
    """
    try:
        evaluator = get_model_evaluator()
        
        # 모델이 없는 경우 graceful degradation
        if evaluator is None:
            logger.warning("모델 없음 - 기본 응답 제공")
            
            # 단순한 휴리스틱 기반 예측 (CI/CD 테스트용)
            base_rating = 6.5  # 평균 영화 평점
            
            # 연도 보정
            year = movie_data.get("startYear", 2000)
            if year > 2010:
                base_rating += 0.2
            if year > 2020:
                base_rating += 0.1
                
            # 런타임 보정
            runtime = movie_data.get("runtimeMinutes", 120)
            if 90 <= runtime <= 150:
                base_rating += 0.1
                
            # 투표수 보정
            votes = movie_data.get("numVotes", 1000)
            if votes > 10000:
                base_rating += 0.2
            if votes > 100000:
                base_rating += 0.1
                
            predicted_rating = min(max(base_rating, 1.0), 10.0)
            
            return {
                "title": movie_data.get("title", "Unknown Movie"),
                "predicted_rating": round(predicted_rating, 2),
                "rating_out_of_10": f"{predicted_rating:.1f}/10",
                "features_used": ["heuristic_fallback"],
                "model_features": ["startYear", "runtimeMinutes", "numVotes"],
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.5,  # 낮은 신뢰도
                "model_version": "fallback-v1.0",
                "metadata": {
                    "model_status": "not_loaded",
                    "prediction_method": "heuristic_fallback",
                    "warning": "실제 ML 모델을 사용하지 않은 예측입니다",
                    "accuracy_note": "모델 훈련 후 정확한 예측이 가능합니다"
                }
            }
        
        # 모델이 있는 경우 정상 예측 (기존 로직 유지)
        logger.info(f"영화 평점 예측: {movie_data}")
        
        required_features = evaluator.get_feature_names()
        predicted_rating = evaluator.predict_single_movie(movie_data)
        
        response = {
            "title": movie_data.get("title", "Unknown Movie"),
            "predicted_rating": round(predicted_rating, 2),
            "rating_out_of_10": f"{predicted_rating:.1f}/10",
            "features_used": {
                k: v for k, v in movie_data.items() if k in required_features
            },
            "model_features": required_features,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.85,
            "model_version": "1.0.0",
            "metadata": {
                "model_status": "loaded",
                "model_type": evaluator.model_type,
                "prediction_method": "ml_model"
            }
        }
        
        logger.info(f"예측 결과: {predicted_rating:.2f}/10")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"영화 예측 오류: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"예측 처리 중 오류가 발생했습니다: {str(e)}"
        )
@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_movies(request: BatchPredictionRequest):
    """
    여러 영화 배치 예측 (Enhanced with graceful degradation)
    """
    try:
        logger.info(f"배치 예측 요청: {len(request.texts)}개 영화")

        if len(request.texts) > 100:
            raise HTTPException(
                status_code=400, detail="한 번에 최대 100개까지 처리 가능합니다."
            )

        # 모델 평가기 확인 (graceful handling)
        evaluator = get_model_evaluator()
        predictions = []

        for i, text in enumerate(request.texts):
            try:
                # 간단한 더미 데이터 생성 (실제로는 텍스트 파싱 필요)
                movie_data = {
                    "startYear": 2020 - (i % 20),  # 2000-2020 범위
                    "runtimeMinutes": 90 + (i % 60),  # 90-150분 범위
                    "numVotes": 1000 + (i * 100),  # 다양한 인기도
                }

                if evaluator is None:
                    # 모델이 없을 때 fallback 예측
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
                                "warning": "실제 ML 모델을 사용하지 않은 예측입니다"
                            }
                        )
                    )
                else:
                    # 모델이 있을 때 정상 예측
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
                                "model_type": evaluator.model_type
                            }
                        )
                    )

            except Exception as e:
                logger.warning(f"개별 예측 실패 ({text[:30]}...): {e}")
                # 실패한 경우 기본값 (fallback)
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
                            "error": str(e),
                            "warning": "개별 예측 중 오류가 발생했습니다"
                        }
                    )
                )

        logger.info(f"배치 예측 완료: {len(predictions)}개 결과")

        return BatchPredictionResponse(
            predictions=predictions, 
            total_count=len(predictions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 예측 실패: {str(e)}")

@router.get("/model/info")
async def get_model_info():
    """
    모델 정보 조회 (Graceful handling)
    모델이 없어도 유용한 정보 제공
    """
    try:
        evaluator = get_model_evaluator()
        
        if evaluator is None:
            return {
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
                },
                "expected_features": ["startYear", "runtimeMinutes", "numVotes"],
                "fallback_available": True,
                "suggestions": [
                    "모델 훈련: python scripts/train_model.py",
                    "모델 파일 확인: ls models/",
                    "서버 재시작 고려"
                ],
                "warning": "현재 heuristic fallback 모드에서 동작 중입니다"
            }
        
        # 모델이 로드된 경우 (기존 로직 유지)
        model_info = evaluator.get_model_info()
        
        return {
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
            },
            "feature_names": model_info.get("feature_names", []),
            "fallback_available": False
        }
        
    except Exception as e:
        logger.error(f"모델 정보 조회 오류: {str(e)}")
        return {
            "name": "IMDB Rating Predictor",
            "version": "error",
            "status": "error",
            "description": "모델 정보 조회 중 오류 발생",
            "created_at": datetime.now().isoformat(),
            "model_loaded": False,
            "error": str(e),
            "fallback_available": True
        }
    
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    API 상태 확인 (Enhanced with graceful degradation info)
    """
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
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now(),
            version="1.0.0",
            model_loaded=model_loaded,
            details=details,
            capabilities={
                "prediction": True,  # fallback 가능하므로 항상 true
                "model_info": True,
                "health_check": True,
                "fallback_prediction": not model_loaded
            }
        )
        
    except Exception as e:
        logger.error(f"헬스체크 오류: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0",
            model_loaded=False,
            details=f"헬스체크 중 오류 발생: {str(e)}",
            capabilities={
                "prediction": False,
                "model_info": False,
                "health_check": True,
                "fallback_prediction": False
            }
        )
def load_model_at_startup():
    """
    Enhanced model loading with Docker packaging support
    Priority: 1) Packaged model 2) Latest trained model 3) Fallback
    """
    global model_evaluator

    try:
        from pathlib import Path
        import os

        # CI/CD environment detection
        is_ci_environment = any([
            os.getenv('CI') == 'true',
            os.getenv('GITHUB_ACTIONS') == 'true',
            os.getenv('DOCKER_ENV') == 'ci',
            os.getenv('ENVIRONMENT') == 'ci'
        ])
        
        is_docker_environment = any([
            os.path.exists('/.dockerenv'),
            os.getenv('DOCKER_CONTAINER') == 'true'
        ])

        models_dir = Path("models")
        if not models_dir.exists():
            logger.warning("⚠️ models 디렉토리가 없습니다")
            return False

        # 🎯 PRIORITY 1: Look for packaged CI/CD model (Docker containers)
        packaged_models = [
            "cicd_default_model.joblib",
            # "docker_model.joblib", 
            "cicd_linear_model.joblib",
            # "scaler_default_model.joblib",
            # "latest_model.joblib"

        ]
        
        for packaged_model in packaged_models:
            packaged_path = models_dir / packaged_model
            if packaged_path.exists():
                try:
                    logger.info(f"🐳 Found packaged model: {packaged_model}")
                    model_evaluator = ModelEvaluator()
                    model_evaluator.load_model(str(packaged_path))
                    
                    logger.info("✅ Packaged model loaded successfully!")
                    logger.info(f"   Model type: {model_evaluator.model_type}")
                    logger.info(f"   Features: {model_evaluator.get_feature_names()}")
                    logger.info(f"   Source: Packaged for containers")
                    
                    return True
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load packaged model {packaged_model}: {e}")
                    continue

        # 🎯 PRIORITY 2: Look for latest trained model (development/production)
        model_files = list(models_dir.glob("*forest*.joblib"))
        model_files.extend(list(models_dir.glob("*regressor*.joblib")))
        model_files.extend(list(models_dir.glob("*model*.joblib")))
        
        # Filter out packaged models from search
        model_files = [f for f in model_files if f.name not in packaged_models]
        
        if model_files:
            # Get the most recent model
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            
            try:
                logger.info(f"📦 Found trained model: {latest_model.name}")
                model_evaluator = ModelEvaluator()
                model_evaluator.load_model(str(latest_model))
                
                logger.info("✅ Trained model loaded successfully!")
                logger.info(f"   Model type: {model_evaluator.model_type}")
                logger.info(f"   Features: {model_evaluator.get_feature_names()}")
                logger.info(f"   Source: Training pipeline")
                
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load trained model: {e}")

        # 🎯 PRIORITY 3: No model found - log appropriate message
        if is_docker_environment and is_ci_environment:
            logger.info("ℹ️ CI/CD 컨테이너에서 모델을 찾을 수 없습니다")
            logger.info("💡 컨테이너에 모델이 패키징되지 않았을 수 있습니다")
        elif is_ci_environment:
            logger.info("ℹ️ CI/CD 환경 - 모델 없이 fallback 모드로 실행")
        else:
            logger.error("❌ 모델 파일이 없습니다")
            logger.info("💡 모델 훈련 방법: python scripts/train_model.py")

        model_evaluator = None
        return False

    except Exception as e:
        if is_ci_environment:
            logger.info(f"ℹ️ CI/CD 환경에서 모델 로드 건너뜀: {e}")
        else:
            logger.error(f"❌ 모델 로드 실패: {e}")
        model_evaluator = None
        return False


def get_model_status():
    """Get detailed model status for debugging"""
    try:
        from pathlib import Path
        import os
        
        models_dir = Path("models")
        status = {
            "models_directory_exists": models_dir.exists(),
            "is_docker": os.path.exists('/.dockerenv'),
            "is_ci": os.getenv('CI') == 'true',
            "model_evaluator_loaded": model_evaluator is not None,
            "available_models": [],
            "packaged_models": [],
            "environment": {
                "DOCKER_CONTAINER": os.getenv('DOCKER_CONTAINER'),
                "CI": os.getenv('CI'),
                "GITHUB_ACTIONS": os.getenv('GITHUB_ACTIONS'),
                "MODEL_PATH": os.getenv('MODEL_PATH')
            }
        }
        
        if models_dir.exists():
            # List all model files
            all_models = list(models_dir.glob("*.joblib")) + list(models_dir.glob("*.pkl"))
            status["available_models"] = [f.name for f in all_models]
            
            # Identify packaged models
            packaged_names = ["cicd_default_model.joblib", "docker_model.joblib", "cicd_linear_model.joblib"]
            status["packaged_models"] = [name for name in packaged_names if (models_dir / name).exists()]
        
        if model_evaluator is not None:
            try:
                status["current_model"] = {
                    "type": model_evaluator.model_type if hasattr(model_evaluator, 'model_type') else "unknown",
                    "features": model_evaluator.get_feature_names() if hasattr(model_evaluator, 'get_feature_names') else []
                }
            except:
                status["current_model"] = "loaded_but_details_unavailable"
        
        return status
        
    except Exception as e:
        return {"error": str(e)}
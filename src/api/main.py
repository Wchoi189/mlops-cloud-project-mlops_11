from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 앱 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("🚀 MLOps IMDB API 시작 중...")
    
    # 모델 로드
    from .endpoints import load_model_at_startup
    model_loaded = load_model_at_startup()
    
    if model_loaded:
        logger.info("✅ 모델 로드 완료 - API 준비됨")
    else:
        logger.warning("⚠️ 모델 로드 실패 - 일부 기능이 제한됩니다")
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 MLOps IMDB API 종료 중...")

# FastAPI 앱 생성
app = FastAPI(
    title="MLOps IMDB Movie Rating Prediction API",
    description="""
    🎬 IMDB 영화 평점 예측 MLOps API
    
    ## 기능
    - 영화 평점 예측 (Random Forest 모델)
    - 배치 예측 지원
    - 모델 정보 조회
    - 헬스 체크
    
    ## 사용되는 피처
    - startYear: 개봉 연도
    - runtimeMinutes: 상영 시간
    - numVotes: 투표 수
    
    ## 모델 성능
    - RMSE: ~0.69
    - R²: ~0.31
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (개발 환경용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from .endpoints import router as prediction_router
app.include_router(prediction_router, tags=["predictions"])

@app.get("/", response_model=Dict[str, Any])
async def root():
    """루트 엔드포인트 - API 정보 제공"""
    return {
        "message": "MLOps IMDB Movie Rating Prediction API",
        "status": "running",
        "version": "1.0.0",
        "description": "영화 평점 예측을 위한 MLOps API",
        "endpoints": {
            "predict_text": "POST /predict - 텍스트 기반 예측 (레거시)",
            "predict_movie": "POST /predict/movie - 영화 피처 기반 예측",
            "predict_batch": "POST /predict/batch - 배치 예측",
            "model_info": "GET /model/info - 모델 정보",
            "health": "GET /health - 상태 확인",
            "docs": "GET /docs - API 문서"
        },
        "features_used": ["startYear", "runtimeMinutes", "numVotes"],
        "model_info": {
            "type": "Random Forest Regressor", 
            "performance": "RMSE ~0.69, R² ~0.31",
            "target": "IMDB Rating (1-10)"
        },
        "timestamp": datetime.now().isoformat(),
        "github": "https://github.com/AIBootcamp13/mlops-cloud-project-mlops_11"
    }

@app.get("/status")
async def get_api_status():
    """상세한 API 상태 정보"""
    try:
        from .endpoints import model_evaluator
        
        model_loaded = model_evaluator is not None
        
        if model_loaded:
            model_info = model_evaluator.get_model_info()
        else:
            model_info = {"status": "모델이 로드되지 않음"}
        
        return {
            "api_status": "running",
            "model_status": "loaded" if model_loaded else "not_loaded",
            "model_info": model_info,
            "timestamp": datetime.now().isoformat(),
            "uptime": "계산 중...",
            "endpoints_count": len(app.routes),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        return {
            "api_status": "running", 
            "model_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 오류 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "요청한 엔드포인트를 찾을 수 없습니다.",
        "available_endpoints": [
            "/",
            "/predict/movie", 
            "/predict/batch",
            "/model/info",
            "/health",
            "/docs"
        ]
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"내부 서버 오류: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "서버 내부 오류가 발생했습니다.",
        "timestamp": datetime.now().isoformat()
    }

# 개발 서버 실행 (python src/api/main.py로 실행 가능)
if __name__ == "__main__":
    import uvicorn
    logger.info("개발 서버 시작...")
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
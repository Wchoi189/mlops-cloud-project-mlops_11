"""
Enhanced FastAPI application with Prometheus metrics integration
Monitoring-ready MLOps API with comprehensive observability
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import logging
import asyncio
from typing import Dict, Any, Union
from datetime import datetime

# Monitoring imports
try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, multiprocess, CollectorRegistry
    from ..monitoring.metrics import metrics, PrometheusMiddleware, metrics_collector, update_health_metrics
    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False
    logging.warning("Monitoring dependencies not available")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 앱 생명주기 관리 with monitoring
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("🚀 MLOps IMDB API with Monitoring 시작 중...")
    
    # Start metrics collection
    if HAS_MONITORING:
        metrics_collector.start()
        logger.info("📊 Metrics collection started")
    
    # 모델 로드
    from .endpoints import load_model_at_startup
    model_loaded = load_model_at_startup()
    
    if model_loaded:
        logger.info("✅ 모델 로드 완료 - API 준비됨")
        if HAS_MONITORING:
            metrics.record_model_accuracy(0.69, "imdb_model", "1.0")  # Initial accuracy
    else:
        logger.warning("⚠️ 모델 로드 실패 - 일부 기능이 제한됩니다")
    
    # Start background health metrics update
    if HAS_MONITORING:
        asyncio.create_task(periodic_health_update())
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 MLOps IMDB API 종료 중...")
    if HAS_MONITORING:
        metrics_collector.stop()

async def periodic_health_update():
    """Periodic health metrics update"""
    while True:
        try:
            update_health_metrics()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Health metrics update error: {e}")
            await asyncio.sleep(30)

# FastAPI 앱 생성
app = FastAPI(
    title="MLOps IMDB Movie Rating Prediction API (Monitoring Edition)",
    description="""
    🎬 IMDB 영화 평점 예측 MLOps API with Comprehensive Monitoring
    
    ## 기능
    - 영화 평점 예측 (Random Forest 모델)
    - 배치 예측 지원
    - 모델 정보 조회
    - 헬스 체크
    - **📊 Prometheus 메트릭스 수집**
    - **🚨 실시간 알림 시스템**
    - **📈 성능 모니터링**
    
    ## 모니터링 엔드포인트
    - `/metrics` - Prometheus 메트릭스
    - `/health` - 상세 헬스 체크
    - `/monitoring/status` - 모니터링 시스템 상태
    
    ## 사용되는 피처
    - startYear: 개봉 연도
    - runtimeMinutes: 상영 시간
    - numVotes: 투표 수
    
    ## 모델 성능
    - RMSE: ~0.69
    - R²: ~0.31
    """,
    version="1.1.0",
    lifespan=lifespan
)

# Add Prometheus middleware
if HAS_MONITORING:
    app.add_middleware(PrometheusMiddleware, metrics_instance=metrics)

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

# 모니터링 전용 엔드포인트들
@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def get_metrics():
    """Prometheus metrics endpoint"""
    if not HAS_MONITORING:
        return "# Monitoring not available\n"
    
    try:
        # Update health metrics before serving
        update_health_metrics()
        return metrics.get_metrics()
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"# Error generating metrics: {e}\n"

@app.get("/monitoring/status")
async def monitoring_status():
    """Monitoring system status"""
    return {
        "monitoring_enabled": HAS_MONITORING,
        "metrics_collector_running": metrics_collector.running if HAS_MONITORING else False,
        "prometheus_endpoint": "/metrics",
        "grafana_dashboard": "http://localhost:3000",
        "alertmanager": "http://localhost:9093",
        "services": {
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3000", 
            "alertmanager": "http://localhost:9093"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_model=Dict[str, Any])
async def root():
    """루트 엔드포인트 - API 정보 제공"""
    
    # Record API call if monitoring enabled
    if HAS_MONITORING:
        metrics.http_requests_total.labels(
            method="GET",
            endpoint="/",
            status_code="200"
        ).inc()
    
    return {
        "message": "MLOps IMDB Movie Rating Prediction API (Monitoring Edition)",
        "status": "running",
        "version": "1.1.0",
        "description": "영화 평점 예측을 위한 모니터링 지원 MLOps API",
        "monitoring": {
            "enabled": HAS_MONITORING,
            "prometheus_metrics": "/metrics",
            "health_check": "/health",
            "monitoring_status": "/monitoring/status"
        },
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
        "monitoring_dashboards": {
            "grafana": "http://localhost:3000",
            "prometheus": "http://localhost:9090",
            "alertmanager": "http://localhost:9093"
        },
        "timestamp": datetime.now().isoformat(),
        "github": "https://github.com/AIBootcamp13/mlops-cloud-project-mlops_11"
    }

@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check with monitoring metrics"""
    try:
        from .endpoints import model_evaluator
        
        model_loaded = model_evaluator is not None
        
        # Get system health if monitoring available
        health_data = {
            "status": "healthy" if model_loaded else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.1.0",
            "model_loaded": model_loaded,
            "monitoring_enabled": HAS_MONITORING
        }
        
        if HAS_MONITORING:
            try:
                import psutil
                import os
                
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                
                health_data["system_metrics"] = {
                    "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                }
                
                # Update health metrics
                update_health_metrics()
                
            except ImportError:
                health_data["system_metrics"] = "psutil not available"
        
        if model_loaded and HAS_MONITORING:
            model_info = model_evaluator.get_model_info()
            health_data["model_info"] = model_info
            
            # Record model status
            metrics.set_active_users(1)  # Simple active user tracking
        
        return health_data
        
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.1.0",
            "model_loaded": False,
            "error": str(e)
        }
        
        if HAS_MONITORING:
            metrics.http_requests_total.labels(
                method="GET",
                endpoint="/health",
                status_code="500"
            ).inc()
        
        return error_response

@app.get("/metrics/custom")
async def custom_metrics():
    """Custom business metrics endpoint"""
    if not HAS_MONITORING:
        return {"error": "Monitoring not available"}
    
    try:
        # Example custom metrics calculation
        from .endpoints import model_evaluator
        
        custom_data: Dict[str, Union[str, int, float]] = {
            "timestamp": datetime.now().isoformat(), # str
            "model_status": "loaded" if model_evaluator else "not_loaded", # str
            "api_version": "1.1.0" # str
        }
        
        # Record some example business metrics
        if model_evaluator:
            # Simulate some business metrics
            metrics.record_prediction_rating(7.5)  # Example rating
            metrics.set_active_users(5)  # Example active users
            
            custom_data["predictions_today"] = 42  # Example data
            custom_data["average_rating"] = 7.2   # Example data
            custom_data["active_users"] = 5
        
        return custom_data
        
    except Exception as e:
        logger.error(f"Custom metrics error: {e}")
        return {"error": str(e)}

# 모니터링 관련 미들웨어
@app.middleware("http")
async def add_monitoring_headers(request: Request, call_next):
    """Add monitoring headers to responses"""
    response = await call_next(request)
    
    # Add monitoring-related headers
    response.headers["X-MLOps-Version"] = "1.1.0"
    response.headers["X-Monitoring-Enabled"] = str(HAS_MONITORING)
    
    if HAS_MONITORING:
        response.headers["X-Prometheus-Metrics"] = "/metrics"
        response.headers["X-Health-Check"] = "/health"
    
    return response

# 오류 핸들러 with monitoring
@app.exception_handler(404)
async def not_found_handler(request, exc):
    if HAS_MONITORING:
        metrics.http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code="404"
        ).inc()
    
    return {
        "error": "Not Found",
        "message": "요청한 엔드포인트를 찾을 수 없습니다.",
        "available_endpoints": [
            "/",
            "/predict/movie", 
            "/predict/batch",
            "/model/info",
            "/health",
            "/metrics",
            "/monitoring/status",
            "/docs"
        ]
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"내부 서버 오류: {exc}")
    
    if HAS_MONITORING:
        metrics.http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code="500"
        ).inc()
    
    return {
        "error": "Internal Server Error",
        "message": "서버 내부 오류가 발생했습니다.",
        "monitoring": "Check /metrics for system health" if HAS_MONITORING else "Monitoring disabled",
        "timestamp": datetime.now().isoformat()
    }

# 개발 서버 실행 (python src/api/main_with_metrics.py로 실행 가능)
if __name__ == "__main__":
    import uvicorn
    logger.info("모니터링 지원 개발 서버 시작...")
    uvicorn.run(
        "src.api.main_with_metrics:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
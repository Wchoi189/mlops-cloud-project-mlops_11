"""
Enhanced FastAPI application with Prometheus metrics integration
Monitoring-ready MLOps API with comprehensive observability
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Union

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

# Monitoring imports
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        generate_latest,
        multiprocess,
    )

    from ..monitoring.metrics import (
        PrometheusMiddleware,
        metrics,
        metrics_collector,
        update_health_metrics,
    )

    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False
    logging.warning("Monitoring dependencies not available")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 앱 생명주기 관리 with monitoring
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("🚀 MLOps IMDB API with Monitoring 시작 중...")

    # Start metrics collection
    if HAS_MONITORING and "metrics_collector" in globals():
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
    if HAS_MONITORING and "update_health_metrics" in globals():
        asyncio.create_task(periodic_health_update())

    yield

    # 종료 시 실행
    logger.info("🛑 MLOps IMDB API 종료 중...")
    if HAS_MONITORING and "metrics_collector" in globals():
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
    lifespan=lifespan,
)


# Enable Prometheus metrics
@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


# Add Prometheus middleware safely
if HAS_MONITORING and PrometheusMiddleware is not None:
    try:
        app.add_middleware(PrometheusMiddleware, metrics_instance=metrics)
        logger.info("📊 Prometheus middleware added successfully")
    except Exception as e:
        logger.warning(f"Failed to add Prometheus middleware: {e}")
        HAS_MONITORING = False

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


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    if not HAS_MONITORING:
        return Response(
            content='# Monitoring not enabled\n# TYPE info gauge\ninfo{version="1.1.0",status="monitoring_disabled"} 1\n',
            media_type="text/plain",
            status_code=200,  # Changed from 503 to 200
        )

    try:
        # Try multiprocess metrics collection first
        try:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            metrics_data = generate_latest(registry)
        except (ValueError, OSError, Exception) as e:
            logger.warning(f"Multiprocess metrics failed, using default: {e}")
            # Fallback to default registry
            metrics_data = generate_latest()

        # Return as Response with correct content type
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        # Return basic error metrics instead of failing
        error_metrics = f"""# Error generating metrics: {e}
        # TYPE mlops_api_error_total counter
        mlops_api_error_total{{error_type="metrics_generation"}} 1
        # TYPE mlops_api_info gauge
        mlops_api_info{{version="1.1.0",status="metrics_error"}} 1
        """
        return Response(
            content=error_metrics,
            media_type="text/plain",
            status_code=200,  # Return 200 with error info instead of 500
        )


@app.get("/monitoring/status")
async def monitoring_status():
    """Monitoring system status"""
    return {
        "monitoring_enabled": HAS_MONITORING,
        "metrics_collector_running": (
            metrics_collector.running
            if HAS_MONITORING and "metrics_collector" in globals()
            else False
        ),
        "prometheus_endpoint": "/metrics",
        "grafana_dashboard": "http://localhost:3000",
        "alertmanager": "http://localhost:9093",
        "services": {
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3000",
            "alertmanager": "http://localhost:9093",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """루트 엔드포인트 - API 정보 제공"""

    # Record API call if monitoring enabled
    if HAS_MONITORING:
        metrics.http_requests_total.labels(
            method="GET", endpoint="/", status_code="200"
        ).inc()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to the MLOps IMDB Movie Rating Prediction API (Monitoring Edition)",
            "version": "1.1.0",
            "description": "영화 평점 예측을 위한 모니터링 지원 MLOps API",
            "endpoints": {
                "/predict/movie": "POST - 영화 피처 기반 예측",
                "/predict/batch": "POST - 배치 예측",
                "/model/info": "GET - 모델 정보 조회",
                "/health": "GET - 헬스 체크",
                "/metrics": "GET - Prometheus 메트릭스",
                "/monitoring/status": "GET - 모니터링 시스템 상태",
            },
            "features_used": ["startYear", "runtimeMinutes", "numVotes"],
            "model_info": {
                "type": "Random Forest Regressor",
                "performance": "RMSE ~0.69, R² ~0.31",
                "target": "IMDB Rating (1-10)",
            },
            "monitoring_enabled": HAS_MONITORING,
            "timestamp": datetime.now().isoformat(),
            "github": "https://github.com/AIBootcamp13/mlops-cloud-project-mlops_11",
        },
    )


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
            "monitoring_enabled": HAS_MONITORING,
        }

        if HAS_MONITORING:
            try:
                import os

                import psutil

                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()

                health_data["system_metrics"] = {
                    "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                }

                # Update health metrics safely
                if "update_health_metrics" in globals() and callable(
                    update_health_metrics
                ):
                    update_health_metrics()

            except ImportError:
                health_data["system_metrics"] = "psutil not available"
            except Exception as e:
                health_data["system_metrics"] = f"Error: {str(e)}"

        if model_loaded and HAS_MONITORING:
            if model_evaluator is not None:
                model_info = model_evaluator.get_model_info()
                health_data["model_info"] = model_info
            else:
                health_data["model_info"] = "Model evaluator not available"

            # Record model status safely
            if "metrics" in globals() and hasattr(metrics, "set_active_users"):
                try:
                    metrics.set_active_users(1)  # Simple active user tracking
                except Exception as e:
                    logger.warning(f"Failed to set active users metric: {e}")

        return JSONResponse(status_code=200, content=health_data)

    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.1.0",
            "model_loaded": False,
            "error": str(e),
        }

        if HAS_MONITORING and "metrics" in globals():
            try:
                metrics.http_requests_total.labels(
                    method="GET", endpoint="/health", status_code="500"
                ).inc()
            except Exception as metrics_error:
                logger.warning(f"Metrics recording failed: {metrics_error}")

        return JSONResponse(status_code=500, content=error_response)


@app.get("/metrics/custom")
async def custom_metrics():
    """Custom business metrics endpoint"""
    if not HAS_MONITORING:
        return {"error": "Monitoring not available"}

    try:
        # Example custom metrics calculation
        from .endpoints import model_evaluator

        custom_data: Dict[str, Union[str, int, float]] = {
            "timestamp": datetime.now().isoformat(),  # str
            "model_status": "loaded" if model_evaluator else "not_loaded",  # str
            "api_version": "1.1.0",  # str
        }

        # Record some example business metrics
        if model_evaluator:
            # Simulate some business metrics
            metrics.record_prediction_rating(7.5)  # Example rating
            metrics.set_active_users(5)  # Example active users

            custom_data["predictions_today"] = 42  # Example data
            custom_data["average_rating"] = 7.2  # Example data
            custom_data["active_users"] = 5

            custom_data["predictions_today"] = 42  # Example data
            custom_data["average_rating"] = 7.2  # Example data
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if HAS_MONITORING:
            metrics.http_requests_total.labels(
                method=request.method, endpoint=request.url.path, status_code="404"
            ).inc()
        return JSONResponse(
            status_code=404,
            content={
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
                    "/docs",
                ],
            },
        )
    else:
        if HAS_MONITORING and "metrics" in globals():
            metrics.http_requests_total.labels(
                method=request.method, endpoint=request.url.path, status_code="500"
            ).inc()
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": (
                    exc.detail if exc.status_code != 500 else "Internal Server Error"
                ),
                "message": (
                    "An error occurred."
                    if exc.status_code != 500
                    else "서버 내부 오류가 발생했습니다."
                ),
                "monitoring": (
                    "Check /metrics for system health"
                    if HAS_MONITORING and exc.status_code == 500
                    else None
                ),
                "timestamp": datetime.now().isoformat(),
            },
        )


# 개발 서버 실행 (python src/api/main_with_metrics.py로 실행 가능)
if __name__ == "__main__":
    import uvicorn

    logger.info("모니터링 지원 개발 서버 시작...")
    uvicorn.run(
        "src.api.main_with_metrics:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

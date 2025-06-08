"""
FastAPI 기반 피처 스토어 API 서버
2.5 간단한 피처 스토어 구현 - API 인터페이스

이 모듈은 피처 스토어에 RESTful API 인터페이스를 제공합니다.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import uvicorn
from pathlib import Path
import sys

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parents[2]
sys.path.append(str(project_root))

from src.features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig
from src.features.engineering.tmdb_processor import AdvancedTMDBPreProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Movie MLOps Feature Store API",
    description="2단계 피처 스토어 RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
feature_store: Optional[SimpleFeatureStore] = None


# Pydantic 모델들
class FeatureRequest(BaseModel):
    """피처 조회 요청 모델"""
    feature_names: List[str] = Field(..., description="조회할 피처명 리스트")
    feature_group: Optional[str] = Field(None, description="피처 그룹 (선택사항)")


class FeatureData(BaseModel):
    """피처 데이터 모델"""
    data: List[Dict[str, Any]] = Field(..., description="피처 데이터 레코드들")
    columns: List[str] = Field(..., description="컬럼명 리스트")
    dtypes: Dict[str, str] = Field(..., description="데이터 타입 정보")
    shape: List[int] = Field(..., description="데이터 형태 [행, 열]")


class SaveFeatureRequest(BaseModel):
    """피처 저장 요청 모델"""
    feature_group: str = Field(..., description="피처 그룹명")
    features_data: Dict[str, FeatureData] = Field(..., description="피처명 -> 데이터 매핑")


class MovieProcessRequest(BaseModel):
    """영화 데이터 처리 요청 모델"""
    movies: List[Dict[str, Any]] = Field(..., description="TMDB 영화 데이터 리스트")
    config: Optional[Dict[str, Any]] = Field(None, description="처리 설정")
    save_to_store: bool = Field(True, description="피처 스토어에 자동 저장 여부")


class APIResponse(BaseModel):
    """API 응답 모델"""
    status: str = Field(..., description="응답 상태")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    timestamp: str = Field(..., description="응답 시간")


# 의존성 함수들
def get_feature_store() -> SimpleFeatureStore:
    """피처 스토어 인스턴스 반환"""
    global feature_store
    if feature_store is None:
        config = FeatureStoreConfig(
            base_path="data/feature_store",
            cache_enabled=True,
            metrics_enabled=True
        )
        feature_store = SimpleFeatureStore(config)
    return feature_store


# API 엔드포인트들
@app.get("/", response_model=APIResponse)
async def root():
    """루트 엔드포인트"""
    return APIResponse(
        status="success",
        message="Movie MLOps Feature Store API 서버가 실행 중입니다.",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "features": "2단계 피처 스토어 구현 완료"
        },
        timestamp=datetime.now().isoformat()
    )


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        store = get_feature_store()
        stats = store.get_store_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "feature_store": {
                "total_features": stats.get("total_features", 0),
                "total_groups": stats.get("total_groups", 0),
                "storage_mb": round(stats.get("total_size_mb", 0), 2)
            }
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 불가: {str(e)}")


@app.post("/features/get", response_model=APIResponse)
async def get_features(request: FeatureRequest, store: SimpleFeatureStore = Depends(get_feature_store)):
    """피처 조회 API"""
    try:
        logger.info(f"피처 조회 요청: {request.feature_names}")
        
        # 피처 조회
        features = store.get_features(request.feature_names, request.feature_group)
        
        if not features:
            return APIResponse(
                status="not_found",
                message="요청한 피처를 찾을 수 없습니다.",
                timestamp=datetime.now().isoformat()
            )
        
        # DataFrame을 JSON 직렬화 가능한 형태로 변환
        serialized_features = {}
        for name, df in features.items():
            serialized_features[name] = {
                "data": df.to_dict('records'),
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "shape": list(df.shape),
                "description": f"피처 '{name}' 데이터"
            }
        
        return APIResponse(
            status="success",
            message=f"{len(features)}개 피처 조회 완료",
            data=serialized_features,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"피처 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 조회 실패: {str(e)}")


@app.post("/features/save", response_model=APIResponse)
async def save_features(
    request: SaveFeatureRequest, 
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """피처 저장 API"""
    try:
        logger.info(f"피처 저장 요청: 그룹 '{request.feature_group}', {len(request.features_data)}개 피처")
        
        # FeatureData를 DataFrame으로 변환
        dataframes = {}
        for feature_name, feature_data in request.features_data.items():
            df = pd.DataFrame(feature_data.data)
            # 컬럼 순서 맞추기
            if feature_data.columns:
                df = df[feature_data.columns]
            dataframes[feature_name] = df
        
        # 피처 저장
        saved_paths = store.save_features(request.feature_group, dataframes)
        
        return APIResponse(
            status="success",
            message=f"{len(saved_paths)}개 피처 저장 완료",
            data={
                "feature_group": request.feature_group,
                "saved_features": list(saved_paths.keys()),
                "saved_paths": saved_paths
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"피처 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 저장 실패: {str(e)}")


@app.get("/features/list")
async def list_features(
    feature_group: Optional[str] = None,
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """피처 목록 조회 API"""
    try:
        features = store.list_features(feature_group)
        groups = store.list_feature_groups()
        
        return {
            "status": "success",
            "data": {
                "features": features,
                "feature_groups": groups,
                "total_features": len(features),
                "total_groups": len(groups)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"피처 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 목록 조회 실패: {str(e)}")


@app.get("/features/info/{feature_name}")
async def get_feature_info(
    feature_name: str,
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """특정 피처 정보 조회 API"""
    try:
        info = store.get_feature_info(feature_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"피처 '{feature_name}'을 찾을 수 없습니다.")
        
        return {
            "status": "success",
            "data": info,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"피처 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 정보 조회 실패: {str(e)}")


@app.delete("/features/{feature_name}")
async def delete_feature(
    feature_name: str,
    feature_group: Optional[str] = None,
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """피처 삭제 API"""
    try:
        success = store.delete_feature(feature_name, feature_group)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"피처 '{feature_name}' 삭제 실패")
        
        return {
            "status": "success",
            "message": f"피처 '{feature_name}' 삭제 완료",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"피처 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 삭제 실패: {str(e)}")


@app.get("/stats")
async def get_stats(store: SimpleFeatureStore = Depends(get_feature_store)):
    """피처 스토어 통계 조회 API"""
    try:
        stats = store.get_store_stats()
        
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@app.post("/process/movies", response_model=APIResponse)
async def process_movies(
    request: MovieProcessRequest,
    background_tasks: BackgroundTasks,
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """영화 데이터 처리 및 피처 생성 API"""
    try:
        logger.info(f"영화 데이터 처리 요청: {len(request.movies)}개 영화")
        
        # TMDBPreProcessor로 피처 생성
        processor = AdvancedTMDBPreProcessor(request.movies, request.config)
        features = processor.extract_all_features()
        
        # 피처 스토어에 저장 (백그라운드에서)
        if request.save_to_store:
            background_tasks.add_task(save_processed_features, store, features)
        
        # 메타데이터만 즉시 반환
        return APIResponse(
            status="success",
            message=f"{len(request.movies)}개 영화의 피처 생성 완료",
            data={
                "processed_movies": len(request.movies),
                "feature_categories": list(features.keys()),
                "metadata": features.get('metadata', {}),
                "saved_to_store": request.save_to_store
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"영화 데이터 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영화 데이터 처리 실패: {str(e)}")


@app.post("/backup")
async def backup_store(
    backup_path: Optional[str] = None,
    store: SimpleFeatureStore = Depends(get_feature_store)
):
    """피처 스토어 백업 API"""
    try:
        backup_location = store.backup_store(backup_path)
        
        return {
            "status": "success",
            "message": "피처 스토어 백업 완료",
            "data": {
                "backup_path": backup_location
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"백업 실패: {e}")
        raise HTTPException(status_code=500, detail=f"백업 실패: {str(e)}")


# 백그라운드 작업 함수
async def save_processed_features(store: SimpleFeatureStore, features: Dict[str, Any]):
    """처리된 피처를 백그라운드에서 저장"""
    try:
        # DataFrame 피처만 저장
        dataframes = {}
        for category, data in features.items():
            if isinstance(data, pd.DataFrame) and category != 'metadata':
                dataframes[category] = data
        
        if dataframes:
            store.save_features("processed_movies", dataframes)
            logger.info(f"백그라운드 피처 저장 완료: {len(dataframes)}개 카테고리")
    
    except Exception as e:
        logger.error(f"백그라운드 피처 저장 실패: {e}")


# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "요청한 리소스를 찾을 수 없습니다.",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "내부 서버 오류가 발생했습니다.",
            "timestamp": datetime.now().isoformat()
        }
    )


# 시작 및 종료 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("🚀 Feature Store API 서버 시작")
    logger.info("📊 피처 스토어 초기화 중...")
    
    # 피처 스토어 초기화
    global feature_store
    feature_store = get_feature_store()
    
    logger.info("✅ Feature Store API 서버 시작 완료")
    logger.info("📚 API 문서: http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("⏹️ Feature Store API 서버 종료")


def main():
    """API 서버 실행 함수"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()

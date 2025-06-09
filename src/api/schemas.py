from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    # Optional movie features for enhanced prediction
    startYear: Optional[int] = Field(
        None, ge=1900, le=2030, description="Movie release year"
    )
    runtimeMinutes: Optional[int] = Field(
        None, ge=1, le=600, description="Movie runtime in minutes"
    )
    numVotes: Optional[int] = Field(None, ge=1, description="Number of votes")


class MoviePredictionRequest(BaseModel):
    """영화 피처 기반 예측 요청"""

    title: str = Field(..., min_length=1, max_length=200, description="Movie title")
    startYear: int = Field(..., ge=1900, le=2030, description="Movie release year")
    runtimeMinutes: int = Field(
        ..., ge=1, le=600, description="Movie runtime in minutes"
    )
    numVotes: int = Field(..., ge=1, description="Number of votes")


class PredictionResponse(BaseModel):
    text: str
    sentiment: str = Field(..., description="Predicted sentiment: positive or negative")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    timestamp: datetime


class MoviePredictionResponse(BaseModel):
    """영화 평점 예측 응답"""

    title: str
    predicted_rating: float = Field(
        ..., ge=1.0, le=10.0, description="Predicted rating (1-10)"
    )
    rating_out_of_10: str
    features_used: Dict[str, Any]
    model_features: List[str]
    timestamp: str


# class BatchPredictionRequest(BaseModel):
#     texts: List[str] = Field(..., max_length =100, description="List of texts to analyze")


# v2
class BatchPredictionRequest(BaseModel):
    texts: Annotated[
        List[str], Field(max_length=100, description="List of texts to analyze")
    ]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_count: int


class ModelInfo(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    created_at: datetime
    metrics: Optional[Dict[str, Union[float, int, bool]]] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    model_loaded: bool = False


# 추가 스키마들
class ApiStatus(BaseModel):
    """API 상태 정보"""

    api_status: str
    model_status: str
    model_info: Dict[str, Any]
    timestamp: str
    uptime: str
    endpoints_count: int
    version: str


class ErrorResponse(BaseModel):
    """오류 응답"""

    error: str
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# Metrics
class CustomMetricsResponse(BaseModel):
    """Response model for custom metrics endpoint"""

    timestamp: str
    model_status: str
    api_version: str
    predictions_today: Optional[int] = None
    average_rating: Optional[float] = None
    active_users: Optional[int] = None
    error: Optional[str] = None

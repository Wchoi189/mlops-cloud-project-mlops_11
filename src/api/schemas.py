from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: Optional[str] = Field(..., min_length=1, max_length=5000, description="Text to analyze")
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


# Enhanced PredictionResponse to support fallback predictions
class PredictionResponse(BaseModel):
    text: Optional[str] = Field(None, description="Input text (for legacy compatibility)")
    sentiment: Optional[str] = Field(None, description="Predicted sentiment (for legacy)")
    confidence:  Optional[float] = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    timestamp: Optional[str] = None
    
    # Enhanced fields for movie prediction
    predicted_rating: Optional[float] = Field(None, ge=1.0, le=10.0, description="Predicted movie rating")
    model_version: Optional[str] = Field(None, description="Model version used")
    features_used: Optional[List[str]] = Field(None, description="Features used for prediction")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional prediction metadata")


# Enhanced MoviePredictionResponse with fallback support
class MoviePredictionResponse(BaseModel):
    """영화 평점 예측 응답 (Enhanced with fallback support)"""
    title: str
    predicted_rating: float = Field(..., ge=1.0, le=10.0, description="Predicted rating (1-10)")
    rating_out_of_10: str
    features_used: Union[Dict[str, Any], List[str]]  # Support both formats
    model_features: Optional[List[str]] = Field(None, description="Model features available")
    timestamp: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Prediction confidence")
    model_version: Optional[str] = Field(None, description="Model version")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchPredictionRequest(BaseModel):
    texts: Annotated[
        List[str], Field(max_length=100, description="List of texts to analyze")
    ]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_count: int


# Enhanced ModelInfo with graceful degradation support  
class ModelInfo(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    created_at: datetime
    metrics: Optional[Dict[str, Union[float, int, bool]]] = None
    status: Optional[str] = Field(None, description="Model status: loaded, not_loaded, error")
    model_loaded: Optional[bool] = Field(None, description="Whether model is loaded")
    expected_features: Optional[List[str]] = Field(None, description="Expected input features")
    feature_names: Optional[List[str]] = Field(None, description="Actual feature names (when loaded)")
    fallback_available: Optional[bool] = Field(None, description="Whether fallback prediction is available")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for improvement")
    warning: Optional[str] = Field(None, description="Warning message if applicable")


class HealthResponse(BaseModel):
    status: str = Field(..., description="API status: healthy, degraded, or unhealthy")
    timestamp: datetime
    version: str
    model_loaded: bool = False
    details: Optional[str] = Field(None, description="Additional status details")
    capabilities: Optional[Dict[str, bool]] = Field(None, description="Available API capabilities")


# API Status with enhanced information
class ApiStatus(BaseModel):
    """API 상태 정보 (Enhanced)"""
    api_status: str
    model_status: str
    model_info: Dict[str, Any]
    timestamp: str
    uptime: str
    endpoints_count: int
    version: str
    capabilities: Optional[Dict[str, bool]] = Field(None, description="API capabilities")
    environment: Optional[str] = Field(None, description="Environment (production, staging, development)")
    fallback_mode: Optional[bool] = Field(None, description="Whether running in fallback mode")


# Enhanced ErrorResponse with more details
class ErrorResponse(BaseModel):
    """오류 응답 (Enhanced)"""
    error: str
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = Field(None, description="Suggestions to fix the error")
    model_required: Optional[bool] = Field(None, description="Whether this endpoint requires a model")
    status: Optional[str] = Field(None, description="Error status code")

# New schema for fallback prediction requests
class FallbackPredictionRequest(BaseModel):
    """Fallback prediction request (when no ML model available)"""
    title: Optional[str] = Field(..., min_length=1, max_length=200, description="Movie title")
    startYear: int = Field(..., ge=1900, le=2030, description="Movie release year")
    runtimeMinutes: int = Field(..., ge=1, le=600, description="Movie runtime in minutes")
    numVotes: int = Field(..., ge=1, description="Number of votes")
    use_fallback: Optional[bool] = Field(False, description="Force use of fallback prediction")


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
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")

class PredictionResponse(BaseModel):
    text: str
    sentiment: str = Field(..., description="Predicted sentiment: positive or negative")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    timestamp: datetime

class BatchPredictionRequest(BaseModel):
    texts: List[str] = Field(..., max_items=100, description="List of texts to analyze")

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_count: int

class ModelInfo(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    created_at: datetime
    metrics: Optional[Dict[str, float]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    model_loaded: bool = False

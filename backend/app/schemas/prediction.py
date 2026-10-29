from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class WasteType(str, Enum):
    WET = "wet"
    DRY = "dry"
    PLASTIC = "plastic"
    GLASS = "glass"
    METAL = "metal"
    MEDICAL = "medical"


class HorizonType(str, Enum):
    NEXT_DAY = "next_day"
    DAY_AFTER_NEXT = "day_after_next"


class WasteTypePrediction(BaseModel):
    waste_type: WasteType
    predicted_kg: float


class UserPredictionResponse(BaseModel):
    user_id: str
    area: str
    prediction_date: str
    predicted_waste_kg: float
    waste_type_breakdown: List[WasteTypePrediction]
    model: str
    horizon: str


class AreaPredictionResponse(BaseModel):
    id: str
    area: str
    prediction_date: date
    predicted_waste_kg: float
    horizon: Optional[str] = None
    contributing_users: Optional[int] = None
    model: Optional[str] = None
    wet_predicted_kg: Optional[float] = None
    dry_predicted_kg: Optional[float] = None
    plastic_predicted_kg: Optional[float] = None
    glass_predicted_kg: Optional[float] = None
    metal_predicted_kg: Optional[float] = None
    medical_predicted_kg: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class OverflowRiskResponse(BaseModel):
    id: str
    area: str
    city: Optional[str] = None
    prediction_date: date
    horizon: Optional[str] = None
    model: Optional[str] = None
    predicted_total_waste_kg: Optional[float] = None
    capacity_proxy_kg: Optional[float] = None
    capacity_source: Optional[str] = None
    capacity_utilization: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    wet_predicted_kg: Optional[float] = None
    dry_predicted_kg: Optional[float] = None
    plastic_predicted_kg: Optional[float] = None
    glass_predicted_kg: Optional[float] = None
    metal_predicted_kg: Optional[float] = None
    medical_predicted_kg: Optional[float] = None
    wet_risk_score: Optional[float] = None
    dry_risk_score: Optional[float] = None
    plastic_risk_score: Optional[float] = None
    glass_risk_score: Optional[float] = None
    metal_risk_score: Optional[float] = None
    medical_risk_score: Optional[float] = None
    hotspot_flag: Optional[bool] = None
    contributing_users: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionAccuracyResponse(BaseModel):
    id: str
    area: str
    prediction_date: date
    horizon: Optional[str] = None
    model: Optional[str] = None
    waste_type: Optional[str] = None
    predicted_kg: Optional[float] = None
    actual_kg: Optional[float] = None
    absolute_error_kg: Optional[float] = None
    percentage_error: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AreaWasteSummary(BaseModel):
    area: str
    total_waste_kg: float
    wet_kg: float
    dry_kg: float
    plastic_kg: float
    glass_kg: float
    metal_kg: float
    medical_kg: float
    submissions_count: int


class TrainingReferenceStatsResponse(BaseModel):
    id: str
    feature_name: str
    feature_type: str
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    median: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    sample_count: Optional[int] = None
    category_counts: Optional[Dict[str, int]] = None
    category_proportions: Optional[Dict[str, float]] = None
    source: str
    training_period_start: Optional[date] = None
    training_period_end: Optional[date] = None
    model_version: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
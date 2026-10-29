from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
from datetime import date, datetime, time
from enum import Enum


class WasteType(str, Enum):
    WET = "wet"
    DRY = "dry"
    PLASTIC = "plastic"
    GLASS = "glass"
    METAL = "metal"
    MEDICAL = "medical"


class DayType(str, Enum):
    NORMAL = "normal_day"
    WEEKEND = "weekend"
    HOLIDAY = "public_holiday"
    FESTIVAL = "festival"


class WasteItemBase(BaseModel):
    waste_type: WasteType
    quantity_kg: float
    
    @field_validator('quantity_kg')
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity must be non-negative')
        return v


class WasteItemCreate(WasteItemBase):
    pass


class WasteItemResponse(WasteItemBase):
    id: str
    submission_id: str
    
    class Config:
        from_attributes = True


class WasteSubmissionBase(BaseModel):
    submission_date: date
    submission_time: Optional[time] = None
    day_type: Optional[DayType] = None
    people_present: Optional[int] = None


class WasteSubmissionCreate(WasteSubmissionBase):
    items: List[WasteItemCreate]
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one waste item is required')
        return v
    
    @field_validator('people_present')
    @classmethod
    def validate_people(cls, v):
        if v is not None and v < 0:
            raise ValueError('People present must be non-negative')
        return v


class WasteSubmissionVerify(WasteSubmissionCreate):
    area: str
    account_type: str
    family_members: Optional[int] = None
    customers: Optional[int] = None
    total_waste_kg: float


class WasteSubmissionResponse(WasteSubmissionBase):
    id: str
    user_id: str
    total_waste_kg: float
    collection_status: str
    collected_at: Optional[datetime] = None
    created_at: datetime
    items: List[WasteItemResponse] = []
    
    class Config:
        from_attributes = True


class WasteSubmissionSummary(BaseModel):
    id: str
    submission_date: date
    total_waste_kg: float
    collection_status: str
    items_count: int
    
    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime, time
from enum import Enum


class CollectionStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class AreaCollectionResponse(BaseModel):
    id: str
    area: str
    collector_id: Optional[str] = None
    collection_date: date
    status: str
    predicted_waste_kg: Optional[float] = None
    collected_waste_kg: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    waste_breakdown_predicted: Optional[str] = None
    facility_assignments: Optional[str] = None
    route_sequence: Optional[int] = None
    planned_load_kg: Optional[float] = None
    waste_breakdown_collected: Optional[str] = None
    actual_sequence: Optional[int] = None
    actual_collection_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollectorCollectionUpdate(BaseModel):
    status: Optional[CollectionStatus] = None
    collected_waste_kg: Optional[float] = None
    waste_breakdown_collected: Optional[str] = None
    actual_sequence: Optional[int] = None
    actual_collection_time: Optional[datetime] = None


class ActualCollectionRecord(BaseModel):
    """Record actual collected waste with per-type breakdown."""
    area_collection_id: str
    wet_kg: float = 0.0
    dry_kg: float = 0.0
    plastic_kg: float = 0.0
    glass_kg: float = 0.0
    metal_kg: float = 0.0
    medical_kg: float = 0.0
    vehicle_capacity_kg: Optional[float] = None
    
    @property
    def total_kg(self) -> float:
        return self.wet_kg + self.dry_kg + self.plastic_kg + self.glass_kg + self.metal_kg + self.medical_kg


class CollectorVehicleInfo(BaseModel):
    capacity_kg: float
    planned_load_kg: float
    remaining_kg: float
    utilization_pct: float
    over_capacity: bool
    warning: bool


class VehicleCapacityUpdate(BaseModel):
    capacity_kg: float


class CollectionRouteResponse(BaseModel):
    depot: Dict[str, float]
    areas: List[Dict]
    facilities: List[Dict]
    total_distance_km: float
    estimated_time_minutes: float
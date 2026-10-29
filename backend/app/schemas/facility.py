from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FacilityType(str):
    DWCC = "DWCC"
    WET_PROCESSING = "Wet Processing"
    PLASTIC_RECYCLING = "Plastic Recycling"
    GLASS_RECYCLING = "Glass Recycling"
    METAL_RECYCLING = "Metal Recycling"
    BIOMEDICAL_TREATMENT = "Biomedical Treatment"
    BIOMEDICAL_INCINERATOR = "Biomedical Incinerator"
    LANDFILL = "Landfill"
    DUMPING_GROUND = "Dumping Ground"
    CD_PROCESSING = "C&D Processing"
    EWASTE_RECYCLING = "E-Waste Recycling"
    TRANSFER_STATION = "Transfer Station"
    OTHER = "Other"


class FacilityStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PLANNED = "planned"
    UNKNOWN = "unknown"


class WasteFacilityResponse(BaseModel):
    id: str
    facility_name: str
    facility_type: str
    waste_categories: Optional[str] = None
    address: Optional[str] = None
    area_name: Optional[str] = None
    city: Optional[str] = None
    ward_name: Optional[str] = None
    ward_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_kg_per_day: Optional[float] = None
    operator_name: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    data_quality_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WasteGenerationZoneResponse(BaseModel):
    id: str
    area_name: str
    city: Optional[str] = None
    ward_name: Optional[str] = None
    ward_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = None
    source_date: Optional[datetime] = None
    source_year: Optional[int] = None
    source_reference: Optional[str] = None
    observations: Optional[str] = None
    total_waste_kg_per_day: Optional[float] = None
    household_waste_kg_per_day: Optional[float] = None
    commercial_waste_kg_per_day: Optional[float] = None
    bulk_generator_waste_kg_per_day: Optional[float] = None
    wet_waste_kg_per_day: Optional[float] = None
    dry_waste_kg_per_day: Optional[float] = None
    plastic_waste_kg_per_day: Optional[float] = None
    glass_waste_kg_per_day: Optional[float] = None
    metal_waste_kg_per_day: Optional[float] = None
    medical_waste_kg_per_day: Optional[float] = None
    data_quality_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FacilityMatchResponse(BaseModel):
    waste_type: str
    facility_id: str
    facility_name: str
    facility_type: str
    distance_km: float
    capacity_kg_per_day: Optional[float] = None
    current_load_kg: Optional[float] = None
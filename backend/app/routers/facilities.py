from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.schemas.facility import WasteFacilityResponse, WasteGenerationZoneResponse
from app.models.facility import WasteFacility, WasteGenerationZone

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=List[WasteFacilityResponse])
def get_facilities(
    facility_type: Optional[str] = None,
    area: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(WasteFacility)
    
    if facility_type:
        query = query.filter(WasteFacility.facility_type == facility_type)
    if area:
        query = query.filter(WasteFacility.area_name == area)
    if status:
        query = query.filter(WasteFacility.status == status)
    
    facilities = query.order_by(WasteFacility.facility_name).offset(offset).limit(limit).all()
    return [WasteFacilityResponse.model_validate(f) for f in facilities]


@router.get("/types/list")
def get_facility_types(db: Session = Depends(get_db)):
    types = db.query(WasteFacility.facility_type).distinct().all()
    return [t[0] for t in types if t[0]]


@router.get("/areas/list")
def get_facility_areas(db: Session = Depends(get_db)):
    areas = db.query(WasteFacility.area_name).distinct().all()
    return [a[0] for a in areas if a[0]]


@router.get("/zones", response_model=List[WasteGenerationZoneResponse])
def get_waste_zones(
    area: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(WasteGenerationZone)
    
    if area:
        query = query.filter(WasteGenerationZone.area_name == area)
    if city:
        query = query.filter(WasteGenerationZone.city == city)
    
    zones = query.order_by(WasteGenerationZone.area_name).offset(offset).limit(limit).all()
    return [WasteGenerationZoneResponse.model_validate(z) for z in zones]


@router.get("/zones/{zone_id}", response_model=WasteGenerationZoneResponse)
def get_waste_zone(
    zone_id: str,
    db: Session = Depends(get_db)
):
    zone = db.query(WasteGenerationZone).filter(WasteGenerationZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return WasteGenerationZoneResponse.model_validate(zone)


@router.get("/{facility_id}", response_model=WasteFacilityResponse)
def get_facility(
    facility_id: str,
    db: Session = Depends(get_db)
):
    facility = db.query(WasteFacility).filter(WasteFacility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return WasteFacilityResponse.model_validate(facility)
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional, Dict

from app.database.session import get_db
from app.schemas.collector import (
    AreaCollectionResponse,
    CollectorCollectionUpdate,
    CollectorVehicleInfo,
    VehicleCapacityUpdate,
    ActualCollectionRecord,
)
from app.schemas.facility import FacilityMatchResponse
from app.schemas.prediction import OverflowRiskResponse
from app.services.collector import (
    get_collector_by_user_id,
    get_collector_collections,
    get_today_collections,
    update_collection,
    get_vehicle_info,
    get_facilities_for_waste_type,
    get_overflow_risks_for_collector,
    update_vehicle_capacity,
    optimize_collection_route,
    record_actual_collection,
)
from app.schemas.collector import CollectorVehicleInfo
from app.services.auth import get_current_collector
from app.models.user import Collector

router = APIRouter(prefix="/collector", tags=["collector"])


async def get_current_collector_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Collector:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    token = authorization.replace("Bearer ", "")
    collector = get_current_collector(db, token)
    if not collector:
        raise HTTPException(status_code=401, detail="Invalid collector token")
    return collector


@router.get("/dashboard")
def get_collector_dashboard(
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    today_collections = get_today_collections(db, collector.id)
    vehicle_info = get_vehicle_info(db, collector.id)
    overflow_risks = get_overflow_risks_for_collector(db, collector.id)
    
    return {
        "collector": {
            "id": collector.id,
            "name": collector.name,
            "vehicle_number": collector.vehicle_number,
            "vehicle_capacity_kg": collector.vehicle_capacity_kg,
            "assigned_areas": collector.assigned_areas.split(",") if collector.assigned_areas else []
        },
        "today_collections": [c.model_dump() for c in today_collections],
        "vehicle_info": vehicle_info.model_dump(),
        "overflow_risks": [r.model_dump() for r in overflow_risks]
    }


@router.get("/collections", response_model=List[AreaCollectionResponse])
def get_collections(
    collector = Depends(get_current_collector_from_token),
    collection_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return get_collector_collections(db, collector.id, collection_date)


@router.get("/collections/today", response_model=List[AreaCollectionResponse])
def get_todays_collections(
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    return get_today_collections(db, collector.id)


@router.patch("/collection/{collection_id}", response_model=AreaCollectionResponse)
def update_collection_endpoint(
    collection_id: str,
    update: CollectorCollectionUpdate,
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    collection = update_collection(db, collection_id, update)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if collection.collector_id != collector.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this collection")
    
    return collection


@router.get("/vehicle-info", response_model=CollectorVehicleInfo)
def get_vehicle_info_endpoint(
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    return get_vehicle_info(db, collector.id)


@router.get("/facilities/{waste_type}", response_model=List[FacilityMatchResponse])
def get_facilities(
    waste_type: str,
    collector = Depends(get_current_collector_from_token),
    area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return get_facilities_for_waste_type(db, waste_type, area)


@router.get("/overflow-risks", response_model=List[OverflowRiskResponse])
def get_overflow_risks(
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    return get_overflow_risks_for_collector(db, collector.id)


@router.patch("/vehicle-capacity")
def update_vehicle_capacity_endpoint(
    update: VehicleCapacityUpdate,
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    updated = update_vehicle_capacity(db, collector.id, update.capacity_kg)
    if not updated:
        raise HTTPException(status_code=404, detail="Collector not found")
    return {"message": "Vehicle capacity updated", "capacity_kg": updated.vehicle_capacity_kg}


@router.get("/optimize-route")
def optimize_route_endpoint(
    collector = Depends(get_current_collector_from_token),
    max_capacity_kg: Optional[float] = None,
    db: Session = Depends(get_db)
):
    route = optimize_collection_route(db, collector.id, max_capacity_kg)
    return route


@router.post("/collection/{collection_id}/actual", response_model=Dict)
def record_actual_collection_endpoint(
    collection_id: str,
    record: ActualCollectionRecord,
    collector = Depends(get_current_collector_from_token),
    db: Session = Depends(get_db)
):
    """Record actual collected waste with per-type breakdown."""
    try:
        result = record_actual_collection(db, collector.id, record)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record actual collection: {str(e)}")
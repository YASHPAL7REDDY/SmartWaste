from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
import json
import uuid

from app.models.user import Collector
from app.models.waste import AreaCollection, WasteSubmission, WasteItem
from app.models.facility import WasteFacility, WasteGenerationZone
from app.models.prediction import AreaPrediction, OverflowRiskPrediction, PredictionAccuracy, ActualCollection
from app.schemas.collector import AreaCollectionResponse, CollectorVehicleInfo, CollectorCollectionUpdate
from app.schemas.facility import FacilityMatchResponse
from app.schemas.prediction import OverflowRiskResponse


def get_collector_by_user_id(db: Session, user_id: str) -> Optional[Collector]:
    return db.query(Collector).filter(Collector.user_id == user_id).first()


def get_collector_collections(db: Session, collector_id: str, collection_date: date = None) -> List[AreaCollectionResponse]:
    query = db.query(AreaCollection).filter(AreaCollection.collector_id == collector_id)
    if collection_date:
        query = query.filter(AreaCollection.collection_date == collection_date)
    collections = query.order_by(AreaCollection.route_sequence).all()
    return [AreaCollectionResponse.model_validate(c) for c in collections]


def get_today_collections(db: Session, collector_id: str) -> List[AreaCollectionResponse]:
    return get_collector_collections(db, collector_id, date.today())


def update_collection(db: Session, collection_id: str, update: CollectorCollectionUpdate) -> Optional[AreaCollectionResponse]:
    collection = db.query(AreaCollection).filter(AreaCollection.id == collection_id).first()
    if not collection:
        return None
    
    if update.status:
        collection.status = update.status.value
    if update.collected_waste_kg is not None:
        collection.collected_waste_kg = update.collected_waste_kg
    if update.waste_breakdown_collected:
        collection.waste_breakdown_collected = update.waste_breakdown_collected
    if update.actual_sequence is not None:
        collection.actual_sequence = update.actual_sequence
    if update.actual_collection_time:
        collection.actual_collection_time = update.actual_collection_time
    
    collection.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(collection)
    return AreaCollectionResponse.model_validate(collection)


def get_vehicle_info(db: Session, collector_id: str) -> CollectorVehicleInfo:
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector:
        raise ValueError("Collector not found")
    
    capacity = collector.vehicle_capacity_kg or 120.0
    
    # Get today's planned load
    today_collections = get_today_collections(db, collector_id)
    planned_load = sum(c.predicted_waste_kg or 0 for c in today_collections)
    
    remaining = capacity - planned_load
    utilization = (planned_load / capacity * 100) if capacity > 0 else 0
    
    return CollectorVehicleInfo(
        capacity_kg=capacity,
        planned_load_kg=planned_load,
        remaining_kg=max(0, remaining),
        utilization_pct=utilization,
        over_capacity=planned_load > capacity,
        warning=utilization >= 90
    )


def get_facilities_for_waste_type(db: Session, waste_type: str, area: str = None) -> List[FacilityMatchResponse]:
    query = db.query(WasteFacility).filter(
        WasteFacility.status.ilike("active"),
        WasteFacility.waste_categories.ilike(f"%{waste_type}%")
    )
    if area:
        query = query.filter(WasteFacility.area_name == area)
    
    facilities = query.all()
    results = []
    for f in facilities:
        results.append(FacilityMatchResponse(
            waste_type=waste_type,
            facility_id=f.id,
            facility_name=f.facility_name,
            facility_type=f.facility_type,
            distance_km=0.0,  # Would calculate actual distance
            capacity_kg_per_day=f.capacity_kg_per_day,
            current_load_kg=0.0
        ))
    return results


def get_overflow_risks_for_collector(db: Session, collector_id: str) -> List[OverflowRiskResponse]:
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector or not collector.assigned_areas:
        return []
    
    areas = collector.assigned_areas.split(",")
    risks = []
    for area in areas:
        area = area.strip()
        risk = db.query(OverflowRiskPrediction).filter(
            OverflowRiskPrediction.area == area,
            OverflowRiskPrediction.prediction_date == date.today()
        ).first()
        if risk:
            risks.append(OverflowRiskResponse.model_validate(risk))
    return risks


def update_vehicle_capacity(db: Session, collector_id: str, capacity_kg: float) -> Optional[Collector]:
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector:
        return None
    
    collector.vehicle_capacity_kg = capacity_kg
    collector.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(collector)
    return collector


def record_actual_collection(db: Session, collector_id: str, record: 'ActualCollectionRecord') -> Dict:
    """Record actual collected waste with per-type breakdown and match to prediction."""
    from app.schemas.collector import ActualCollectionRecord
    
    # Get the area collection
    area_collection = db.query(AreaCollection).filter(
        AreaCollection.id == record.area_collection_id,
        AreaCollection.collector_id == collector_id
    ).first()
    
    if not area_collection:
        raise ValueError("Area collection not found or not assigned to this collector")
    
    if area_collection.status == "completed":
        raise ValueError("Collection already completed")
    
    # Validate quantities
    if any(q < 0 for q in [record.wet_kg, record.dry_kg, record.plastic_kg, 
                           record.glass_kg, record.metal_kg, record.medical_kg]):
        raise ValueError("Quantities cannot be negative")
    
    total_actual = record.total_kg
    
    # Check vehicle capacity
    vehicle_capacity = record.vehicle_capacity_kg or 120.0
    if total_actual > vehicle_capacity:
        raise ValueError(f"Total collected ({total_actual:.1f} kg) exceeds vehicle capacity ({vehicle_capacity:.1f} kg)")
    
    # Update area collection with actual data
    area_collection.status = "completed"
    area_collection.collected_waste_kg = total_actual
    area_collection.completed_at = datetime.utcnow()
    area_collection.waste_breakdown_collected = json.dumps({
        "wet": record.wet_kg,
        "dry": record.dry_kg,
        "plastic": record.plastic_kg,
        "glass": record.glass_kg,
        "metal": record.metal_kg,
        "medical": record.medical_kg
    })
    area_collection.updated_at = datetime.utcnow()
    
    # Create ActualCollection record
    actual_collection = ActualCollection(
        id=str(uuid.uuid4()),
        area=area_collection.area,
        collection_date=area_collection.collection_date,
        collector_id=collector_id,
        area_collection_id=area_collection.id,
        wet_actual_kg=record.wet_kg,
        dry_actual_kg=record.dry_kg,
        plastic_actual_kg=record.plastic_kg,
        glass_actual_kg=record.glass_kg,
        metal_actual_kg=record.metal_kg,
        medical_actual_kg=record.medical_kg,
        total_actual_kg=total_actual,
        vehicle_capacity_kg=vehicle_capacity,
        remaining_capacity_kg=vehicle_capacity - total_actual,
    )
    db.add(actual_collection)
    db.commit()
    db.refresh(actual_collection)
    
    # Match to prediction and calculate accuracy
    match_and_calculate_accuracy(db, actual_collection)
    
    return {
        "message": "Actual collection recorded successfully",
        "actual_collection_id": actual_collection.id,
        "total_collected_kg": total_actual,
        "vehicle_capacity_kg": vehicle_capacity,
        "remaining_capacity_kg": vehicle_capacity - total_actual,
        "breakdown": {
            "wet": record.wet_kg,
            "dry": record.dry_kg,
            "plastic": record.plastic_kg,
            "glass": record.glass_kg,
            "metal": record.metal_kg,
            "medical": record.medical_kg
        }
    }


def match_and_calculate_accuracy(db: Session, actual_collection: ActualCollection) -> Dict:
    """Match actual collection to area prediction and calculate accuracy metrics.
    
    Returns a dict with match result and reason if unmatched.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find matching area prediction for this area, date, and horizon
    # First try exact match including horizon if available
    prediction_query = db.query(AreaPrediction).filter(
        AreaPrediction.area == actual_collection.area,
        AreaPrediction.prediction_date == actual_collection.collection_date
    )
    
    # If actual_collection has horizon info (from area_collection), use it
    # For now, match without horizon constraint but check for duplicates
    predictions = prediction_query.all()
    
    if not predictions:
        reason = f"No matching prediction for area='{actual_collection.area}' date='{actual_collection.collection_date}'"
        logger.info(f"PREDICTION MATCH: {reason}")
        actual_collection.is_matched = False
        actual_collection.matched_at = None
        db.commit()
        return {"matched": False, "reason": reason}
    
    # Check if any prediction already has accuracy records (already evaluated)
    evaluated_predictions = []
    unevaluated_predictions = []
    
    for pred in predictions:
        existing_accuracy = db.query(PredictionAccuracy).filter(
            PredictionAccuracy.area == pred.area,
            PredictionAccuracy.prediction_date == pred.prediction_date,
            PredictionAccuracy.horizon == pred.horizon,
            PredictionAccuracy.model == pred.model
        ).first()
        
        if existing_accuracy:
            evaluated_predictions.append(pred)
        else:
            unevaluated_predictions.append(pred)
    
    # If all predictions already evaluated, don't create duplicates
    if not unevaluated_predictions:
        reason = f"All {len(predictions)} matching prediction(s) already evaluated"
        logger.info(f"PREDICTION MATCH: {reason}")
        actual_collection.is_matched = True  # It's matched, just already evaluated
        actual_collection.matched_at = datetime.utcnow()
        db.commit()
        return {"matched": False, "reason": reason, "already_evaluated": True}
    
    # Use the first unevaluated prediction (or the one with matching horizon if available)
    prediction = unevaluated_predictions[0]
    
    # If there are multiple unevaluated, prefer one matching horizon
    if len(unevaluated_predictions) > 1:
        # Try to find prediction with horizon matching the collection's time
        # For now, just use the first one
        prediction = unevaluated_predictions[0]
    
    # Get predicted breakdown
    predicted_breakdown = {}
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']:
        predicted_breakdown[wt] = getattr(prediction, f"{wt}_predicted_kg", 0.0) or 0.0
    
    actual_breakdown = {
        'wet': actual_collection.wet_actual_kg or 0.0,
        'dry': actual_collection.dry_actual_kg or 0.0,
        'plastic': actual_collection.plastic_actual_kg or 0.0,
        'glass': actual_collection.glass_actual_kg or 0.0,
        'metal': actual_collection.metal_actual_kg or 0.0,
        'medical': actual_collection.medical_actual_kg or 0.0,
    }
    
    # Calculate accuracy for each waste type and total
    waste_types = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
    
    for wt in waste_types:
        if wt == 'total':
            predicted = prediction.predicted_waste_kg or 0.0
            actual = actual_collection.total_actual_kg or 0.0
        else:
            predicted = predicted_breakdown.get(wt, 0.0)
            actual = actual_breakdown.get(wt, 0.0)
        
        absolute_error = abs(predicted - actual)
        percentage_error = (absolute_error / predicted * 100) if predicted > 0 else None
        
        # Create PredictionAccuracy record
        accuracy_record = PredictionAccuracy(
            id=str(uuid.uuid4()),
            area=actual_collection.area,
            prediction_date=actual_collection.collection_date,
            horizon=prediction.horizon,
            model=prediction.model,
            waste_type=wt,
            predicted_kg=predicted,
            actual_kg=actual,
            absolute_error_kg=absolute_error,
            percentage_error=percentage_error,
        )
        db.add(accuracy_record)
    
    # Mark actual collection as matched
    actual_collection.is_matched = True
    actual_collection.matched_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"PREDICTION MATCH: Successfully matched area='{actual_collection.area}' date='{actual_collection.collection_date}' horizon='{prediction.horizon}' -> {len(waste_types)} accuracy records created")
    
    return {
        "matched": True, 
        "prediction_id": prediction.id,
        "horizon": prediction.horizon,
        "accuracy_records_created": len(waste_types)
    }


def get_prediction_evaluation_status(db: Session, days: int = 30) -> Dict:
    """Get comprehensive prediction evaluation status including coverage metrics."""
    from datetime import date, timedelta
    
    cutoff = date.today() - timedelta(days=days)
    
    # Get all area predictions in the period
    all_predictions = db.query(AreaPrediction).filter(
        AreaPrediction.prediction_date >= cutoff
    ).all()
    
    # Get all actual collections in the period
    all_collections = db.query(ActualCollection).filter(
        ActualCollection.collection_date >= cutoff
    ).all()
    
    # Get all accuracy records in the period
    all_accuracy = db.query(PredictionAccuracy).filter(
        PredictionAccuracy.prediction_date >= cutoff
    ).all()
    
    # Track prediction evaluation status
    predictions_evaluated = 0
    predictions_unmatched = 0
    predictions_pending = 0
    unmatched_reasons = {}
    
    for pred in all_predictions:
        # Check if this prediction has accuracy records
        accuracy_exists = db.query(PredictionAccuracy).filter(
            PredictionAccuracy.area == pred.area,
            PredictionAccuracy.prediction_date == pred.prediction_date,
            PredictionAccuracy.horizon == pred.horizon,
            PredictionAccuracy.model == pred.model
        ).first()
        
        if accuracy_exists:
            predictions_evaluated += 1
        else:
            # Check if there's a collection for this area/date
            collection_exists = db.query(ActualCollection).filter(
                ActualCollection.area == pred.area,
                ActualCollection.collection_date == pred.prediction_date
            ).first()
            
            if collection_exists:
                if collection_exists.is_matched:
                    # Collection exists and is matched but no accuracy record? Shouldn't happen
                    predictions_unmatched += 1
                    reason = "Collection matched but no accuracy record"
                else:
                    predictions_unmatched += 1
                    reason = f"Collection exists but not matched: {collection_exists.is_matched}"
            else:
                predictions_pending += 1
                reason = "No matching collection yet"
            
            unmatched_reasons[reason] = unmatched_reasons.get(reason, 0) + 1
    
    # Collection stats
    collections_total = len(all_collections)
    collections_matched = sum(1 for c in all_collections if c.is_matched)
    collections_unmatched = collections_total - collections_matched
    
    # Coverage calculation
    eligible_predictions = predictions_evaluated + predictions_unmatched
    coverage_pct = (predictions_evaluated / eligible_predictions * 100) if eligible_predictions > 0 else 0
    
    return {
        "period_days": days,
        "predictions": {
            "total": len(all_predictions),
            "evaluated": predictions_evaluated,
            "unmatched": predictions_unmatched,
            "pending": predictions_pending,
        },
        "collections": {
            "total": collections_total,
            "matched": collections_matched,
            "unmatched": collections_unmatched,
        },
        "accuracy_records": len(all_accuracy),
        "coverage": {
            "eligible_predictions": eligible_predictions,
            "matched_predictions": predictions_evaluated,
            "coverage_pct": round(coverage_pct, 1),
        },
        "unmatched_reasons": unmatched_reasons,
    }


def get_reliability_level(sample_count: int) -> Dict:
    """Get reliability level based on sample count."""
    if sample_count < 6:
        return {
            "level": "INSUFFICIENT_DATA",
            "label": "Insufficient Data",
            "description": "Accuracy metrics should not be considered reliable yet.",
            "color": "text-red-400",
            "bg_color": "bg-red-500/10 border-red-500/30"
        }
    elif sample_count < 21:
        return {
            "level": "EARLY_EVALUATION",
            "label": "Early Evaluation",
            "description": "Early evaluation. Continue collecting real-world data.",
            "color": "text-yellow-400",
            "bg_color": "bg-yellow-500/10 border-yellow-500/30"
        }
    elif sample_count < 51:
        return {
            "level": "MODERATE_CONFIDENCE",
            "label": "Moderate Confidence",
            "description": "Moderate evaluation confidence.",
            "color": "text-blue-400",
            "bg_color": "bg-blue-500/10 border-blue-500/30"
        }
    else:
        return {
            "level": "STRONG_EVALUATION",
            "label": "Strong Evaluation",
            "description": "Strong evaluation confidence.",
            "color": "text-emerald-400",
            "bg_color": "bg-emerald-500/10 border-emerald-500/30"
        }


def get_real_world_accuracy_metrics(db: Session, days: int = 30) -> Dict:
    """Get real-world prediction accuracy metrics from actual collections."""
    cutoff = date.today() - timedelta(days=days)
    
    # Get all matched accuracy records
    accuracy_records = db.query(PredictionAccuracy).filter(
        PredictionAccuracy.prediction_date >= cutoff
    ).all()
    
    if not accuracy_records:
        return {
            "available": False,
            "message": "No matched prediction-actual data available yet.",
            "predictions_evaluated": 0
        }
    
    # Group by waste type (case-insensitive)
    waste_types = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
    results = {}
    
    for wt in waste_types:
        wt_records = [r for r in accuracy_records if (r.waste_type or '').lower() == wt.lower()]
        if not wt_records:
            results[wt] = {"available": False, "sample_count": 0}
            continue
        
        predicted = [r.predicted_kg or 0 for r in wt_records]
        actual = [r.actual_kg or 0 for r in wt_records]
        errors = [r.absolute_error_kg or 0 for r in wt_records]
        pct_errors = [r.percentage_error for r in wt_records if r.percentage_error is not None]
        
        n = len(wt_records)
        mae = sum(errors) / n if n > 0 else 0
        rmse = math.sqrt(sum(e**2 for e in errors) / n) if n > 0 else 0
        
        # R² calculation
        if n >= 2:
            mean_actual = sum(actual) / n
            ss_tot = sum((a - mean_actual)**2 for a in actual)
            ss_res = sum((actual[i] - predicted[i])**2 for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            r2 = None
        
        mape = sum(pct_errors) / len(pct_errors) if pct_errors else None
        
        reliability = get_reliability_level(n)
        
        results[wt] = {
            "available": True,
            "sample_count": n,
            "total_predicted_kg": round(sum(predicted), 2),
            "total_actual_kg": round(sum(actual), 2),
            "mae_kg": round(mae, 4),
            "rmse_kg": round(rmse, 4),
            "r2": round(r2, 4) if r2 is not None else "N/A",
            "mape_pct": round(mape, 1) if mape is not None else "N/A",
            "reliability": reliability,
            "warning": reliability["description"],
        }
    
    # Overall summary
    total_records = len(accuracy_records)
    all_predicted = sum(r.predicted_kg or 0 for r in accuracy_records)
    all_actual = sum(r.actual_kg or 0 for r in accuracy_records)
    all_errors = [r.absolute_error_kg or 0 for r in accuracy_records]
    
    overall_mae = sum(all_errors) / total_records if total_records > 0 else 0
    overall_rmse = math.sqrt(sum(e**2 for e in all_errors) / total_records) if total_records > 0 else 0
    
    # Get evaluation status for coverage metrics
    eval_status = get_prediction_evaluation_status(db, days)
    
    return {
        "available": True,
        "predictions_evaluated": total_records,
        "total_predicted_kg": round(all_predicted, 2),
        "total_actual_kg": round(all_actual, 2),
        "overall_mae_kg": round(overall_mae, 4),
        "overall_rmse_kg": round(overall_rmse, 4),
        "by_waste_type": results,
        "evaluation_status": eval_status,
    }


def get_actual_vs_predicted_chart_data(db: Session, days: int = 30, waste_type: str = 'total') -> Dict:
    """Get data for Actual vs Predicted chart."""
    cutoff = date.today() - timedelta(days=days)
    
    # Use case-insensitive filter
    records = db.query(PredictionAccuracy).filter(
        PredictionAccuracy.prediction_date >= cutoff,
        PredictionAccuracy.waste_type.ilike(waste_type)
    ).order_by(PredictionAccuracy.prediction_date).all()
    
    if not records:
        return {"available": False, "data": []}
    
    chart_data = []
    for r in records:
        chart_data.append({
            "date": r.prediction_date.isoformat(),
            "predicted": r.predicted_kg or 0,
            "actual": r.actual_kg or 0,
            "error": r.absolute_error_kg or 0,
        })
    
    return {
        "available": True,
        "waste_type": waste_type,
        "data": chart_data
    }


def optimize_collection_route(db: Session, collector_id: str, max_capacity_kg: float = None) -> Dict:
    """Optimize collection route using nearest neighbor with priority weighting."""
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector:
        raise ValueError("Collector not found")
    
    # Get today's pending collections for this collector
    today = date.today()
    collections = db.query(AreaCollection).filter(
        AreaCollection.collector_id == collector_id,
        AreaCollection.collection_date == today,
        AreaCollection.status.in_(["assigned", "in_progress"])
    ).all()
    
    if not collections:
        return {
            "route": [],
            "total_distance_km": 0,
            "total_waste_kg": 0,
            "facility_assignments": []
        }
    
    capacity = max_capacity_kg or collector.vehicle_capacity_kg or 120.0
    
    # Sort by priority: overflow risk > predicted waste > distance
    # Get overflow risks for areas
    area_risks = {}
    for c in collections:
        risk = db.query(OverflowRiskPrediction).filter(
            OverflowRiskPrediction.area == c.area,
            OverflowRiskPrediction.prediction_date == today
        ).first()
        area_risks[c.area] = risk
    
    # Priority scoring
    def get_priority_score(collection):
        risk = area_risks.get(collection.area)
        risk_score = 0
        if risk:
            risk_levels = {"critical": 100, "high": 75, "medium": 50, "low": 25}
            risk_score = risk_levels.get((risk.risk_level or "").lower(), 0)
        
        waste_score = (collection.predicted_waste_kg or 0) * 0.1
        return risk_score + waste_score
    
    # Sort collections by priority (highest first)
    sorted_collections = sorted(collections, key=get_priority_score, reverse=True)
    
    # Select collections within capacity (greedy approach)
    selected = []
    total_waste = 0
    for c in sorted_collections:
        waste = c.predicted_waste_kg or 0
        if total_waste + waste <= capacity:
            selected.append(c)
            total_waste += waste
        else:
            # Check if we can fit a partial collection
            remaining = capacity - total_waste
            if remaining > 0 and waste > remaining:
                # We'll note this as a partial collection needed
                pass
    
    # Simple nearest neighbor routing (depot -> areas -> facility -> depot)
    # Using area coordinates from waste generation zones
    depot = {"lat": 12.9716, "lon": 77.5946, "name": "Depot"}  # Bangalore center
    
    route = [{"name": "DEPOT", "lat": depot["lat"], "lon": depot["lon"], "type": "depot"}]
    
    total_distance = 0
    prev_lat, prev_lon = depot["lat"], depot["lon"]
    
    for c in selected:
        # Get area coordinates from waste generation zone
        zone = db.query(WasteGenerationZone).filter(
            WasteGenerationZone.area_name == c.area
        ).first()
        
        if zone and zone.latitude and zone.longitude:
            lat, lon = zone.latitude, zone.longitude
        else:
            lat, lon = depot["lat"], depot["lon"]
        
        dist = haversine_distance(prev_lat, prev_lon, lat, lon)
        total_distance += dist
        
        route.append({
            "name": c.area,
            "lat": lat,
            "lon": lon,
            "type": "collection",
            "predicted_waste_kg": c.predicted_waste_kg,
            "risk_level": area_risks.get(c.area, {}).get("risk_level") if hasattr(area_risks.get(c.area, {}), "get") else (area_risks.get(c.area).risk_level if area_risks.get(c.area) else None),
            "distance_from_prev_km": round(dist, 2)
        })
        
        prev_lat, prev_lon = lat, lon
    
    # Find appropriate facility for the waste types
    facility = find_best_facility(db, selected)
    if facility:
        dist = haversine_distance(prev_lat, prev_lon, facility.latitude, facility.longitude)
        total_distance += dist
        route.append({
            "name": facility.facility_name,
            "lat": facility.latitude,
            "lon": facility.longitude,
            "type": "facility",
            "facility_type": facility.facility_type,
            "distance_from_prev_km": round(dist, 2)
        })
        prev_lat, prev_lon = facility.latitude, facility.longitude
    
    # Return to depot
    dist = haversine_distance(prev_lat, prev_lon, depot["lat"], depot["lon"])
    total_distance += dist
    route.append({
        "name": "DEPOT",
        "lat": depot["lat"],
        "lon": depot["lon"],
        "type": "depot",
        "distance_from_prev_km": round(dist, 2)
    })
    
    return {
        "route": route,
        "total_distance_km": round(total_distance, 2),
        "total_waste_kg": round(total_waste, 2),
        "vehicle_capacity_kg": capacity,
        "utilization_pct": round((total_waste / capacity * 100) if capacity > 0 else 0, 1),
        "facility_assignments": [{"facility_id": facility.id, "facility_name": facility.facility_name}] if facility else []
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance between two points in km."""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def find_best_facility(db: Session, collections: List[AreaCollection]) -> Optional[WasteFacility]:
    """Find the best facility for the collected waste types."""
    # Get all unique waste types from collections
    waste_types = set()
    for c in collections:
        if c.waste_breakdown_predicted:
            import json
            try:
                breakdown = json.loads(c.waste_breakdown_predicted)
                for wt, qty in breakdown.items():
                    if qty and qty > 0:
                        waste_types.add(wt)
            except:
                pass
    
    if not waste_types:
        waste_types = {"wet", "dry", "plastic", "glass", "metal"}
    
    # Prioritize facilities that can handle medical waste separately
    has_medical = "medical" in waste_types
    
    if has_medical:
        # Medical waste must go to biomedical facility
        facility = db.query(WasteFacility).filter(
            WasteFacility.status == "active",
            WasteFacility.waste_categories.like("%medical%")
        ).first()
        if facility:
            return facility
    
    # For other waste, find DWCC or appropriate facility
    facility = db.query(WasteFacility).filter(
        WasteFacility.status == "active",
        WasteFacility.facility_type.in_(["DWCC", "Wet Processing", "Plastic Recycling", "Metal Recycling"])
    ).first()
    
    return facility
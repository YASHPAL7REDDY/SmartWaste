from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import uuid

from app.models.user import User
from app.models.waste import WasteSubmission, WasteItem
from app.models.prediction import WastePrediction, AreaPrediction, OverflowRiskPrediction
from app.schemas.prediction import (
    UserPredictionResponse, 
    AreaPredictionResponse, 
    OverflowRiskResponse,
    WasteTypePrediction,
    WasteType
)
from app.services.ml_predictor import get_db_rf_predictor


# Default areas with known predictions (fallback chain)
DEFAULT_PREDICTION_AREAS = ["Central", "Yelahanka", "sarjapur"]


def get_user_latest_submission(db: Session, user_id: str) -> Optional[WasteSubmission]:
    return db.query(WasteSubmission).filter(
        WasteSubmission.user_id == user_id
    ).order_by(WasteSubmission.submission_date.desc()).first()


def get_user_waste_history(db: Session, user_id: str, days: int = 30) -> List[WasteSubmission]:
    cutoff = date.today() - timedelta(days=days)
    return db.query(WasteSubmission).filter(
        WasteSubmission.user_id == user_id,
        WasteSubmission.submission_date >= cutoff
    ).order_by(WasteSubmission.submission_date.desc()).all()


def save_user_prediction(db: Session, user_id: str, prediction_result: Dict[str, Any]) -> WastePrediction:
    """Save a user prediction to the database."""
    now = datetime.utcnow()
    
    # Check if prediction already exists for this user/date/horizon
    existing = db.query(WastePrediction).filter(
        WastePrediction.user_id == user_id,
        WastePrediction.prediction_date == date.fromisoformat(prediction_result['prediction_date']),
        WastePrediction.horizon == prediction_result['horizon']
    ).first()
    
    if existing:
        # Update existing
        existing.predicted_waste_kg = prediction_result['predicted_waste_kg']
        existing.model = prediction_result['model']
        existing.wet_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'wet'), 0)
        existing.dry_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'dry'), 0)
        existing.plastic_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'plastic'), 0)
        existing.glass_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'glass'), 0)
        existing.metal_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'metal'), 0)
        existing.medical_predicted_kg = next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'medical'), 0)
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new
    prediction = WastePrediction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        area=prediction_result['area'],
        prediction_date=date.fromisoformat(prediction_result['prediction_date']),
        predicted_waste_kg=prediction_result['predicted_waste_kg'],
        model=prediction_result['model'],
        horizon=prediction_result['horizon'],
        wet_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'wet'), 0),
        dry_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'dry'), 0),
        plastic_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'plastic'), 0),
        glass_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'glass'), 0),
        metal_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'metal'), 0),
        medical_predicted_kg=next((b['predicted_kg'] for b in prediction_result['waste_type_breakdown'] if b['waste_type'] == 'medical'), 0),
        created_at=now,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def _get_area_based_prediction(db: Session, area: str, prediction_date: date, horizon: str) -> Optional[UserPredictionResponse]:
    """Get prediction from AreaPrediction table for a specific area and date."""
    # Try exact match first
    pred = db.query(AreaPrediction).filter(
        AreaPrediction.area == area,
        AreaPrediction.prediction_date == prediction_date,
        AreaPrediction.horizon == horizon
    ).first()
    
    if not pred:
        # Try without horizon filter
        pred = db.query(AreaPrediction).filter(
            AreaPrediction.area == area,
            AreaPrediction.prediction_date == prediction_date
        ).first()
    
    if not pred:
        return None
    
    breakdown = []
    for wt in WasteType:
        val = getattr(pred, f"{wt.value}_predicted_kg", None)
        if val is not None:
            breakdown.append(WasteTypePrediction(waste_type=wt, predicted_kg=val))
    
    return UserPredictionResponse(
        user_id=f"area_{area}",
        area=pred.area,
        prediction_date=pred.prediction_date.isoformat(),
        predicted_waste_kg=pred.predicted_waste_kg,
        waste_type_breakdown=breakdown,
        model=pred.model or "AreaBased",
        horizon=pred.horizon or horizon
    )


def _get_best_available_prediction(db: Session, area: str, prediction_date: date, horizon: str) -> Optional[UserPredictionResponse]:
    """Get the best available prediction for an area, with fallback to default areas."""
    # First try exact area match
    pred = _get_area_based_prediction(db, area, prediction_date, horizon)
    if pred:
        return pred
    
    # Try without horizon filter
    pred = db.query(AreaPrediction).filter(
        AreaPrediction.area == area,
        AreaPrediction.prediction_date == prediction_date
    ).first()
    
    if pred:
        breakdown = []
        for wt in WasteType:
            val = getattr(pred, f"{wt.value}_predicted_kg", None)
            if val is not None:
                breakdown.append(WasteTypePrediction(waste_type=wt, predicted_kg=val))
        
        return UserPredictionResponse(
            user_id=f"area_{area}",
            area=pred.area,
            prediction_date=pred.prediction_date.isoformat(),
            predicted_waste_kg=pred.predicted_waste_kg,
            waste_type_breakdown=breakdown,
            model=pred.model or "AreaBased",
            horizon=pred.horizon or horizon
        )
    
    # Fallback to default areas with predictions
    for default_area in DEFAULT_PREDICTION_AREAS:
        pred = db.query(AreaPrediction).filter(
            AreaPrediction.area == default_area,
            AreaPrediction.prediction_date == prediction_date,
            AreaPrediction.horizon == horizon
        ).first()
        
        if not pred:
            pred = db.query(AreaPrediction).filter(
                AreaPrediction.area == default_area,
                AreaPrediction.prediction_date == prediction_date
            ).first()
        
        if pred:
            breakdown = []
            for wt in WasteType:
                val = getattr(pred, f"{wt.value}_predicted_kg", None)
                if val is not None:
                    breakdown.append(WasteTypePrediction(waste_type=wt, predicted_kg=val))
            
            return UserPredictionResponse(
                user_id=f"area_{default_area}",
                area=pred.area,
                prediction_date=pred.prediction_date.isoformat(),
                predicted_waste_kg=pred.predicted_waste_kg,
                waste_type_breakdown=breakdown,
                model=pred.model or "AreaBased",
                horizon=pred.horizon or horizon
            )
    
    return None


def predict_user_next_day(db: Session, user_id: str, prediction_date: date = None) -> Optional[UserPredictionResponse]:
    if prediction_date is None:
        prediction_date = date.today() + timedelta(days=1)
    
    # Check if user has submission history
    latest = get_user_latest_submission(db, user_id)
    if not latest:
        return None
    
    # Try database-backed ML predictor first
    try:
        predictor = get_db_rf_predictor()
        result = predictor.predict_next_day(db, user_id, prediction_date)
        
        # Save to database
        save_user_prediction(db, user_id, result)
        
        breakdown = [
            WasteTypePrediction(waste_type=WasteType(item['waste_type']), predicted_kg=item['predicted_kg'])
            for item in result['waste_type_breakdown']
        ]
        
        return UserPredictionResponse(
            user_id=result['user_id'],
            area=result['area'],
            prediction_date=result['prediction_date'],
            predicted_waste_kg=result['predicted_waste_kg'],
            waste_type_breakdown=breakdown,
            model=result['model'],
            horizon=result['horizon']
        )
    except Exception as e:
        print(f"Database ML predictor failed for user {user_id}: {e}")
        # Fall back to area-based prediction from database
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.area:
            return _get_best_available_prediction(db, user.area, prediction_date, "next_day")
        return None


def predict_user_day_after_next(db: Session, user_id: str, prediction_date: date = None) -> Optional[UserPredictionResponse]:
    if prediction_date is None:
        prediction_date = date.today() + timedelta(days=1)
    
    latest = get_user_latest_submission(db, user_id)
    if not latest:
        return None
    
    try:
        predictor = get_db_rf_predictor()
        result = predictor.predict_day_after_next(db, user_id, prediction_date)
        
        # Save to database
        save_user_prediction(db, user_id, result)
        
        breakdown = [
            WasteTypePrediction(waste_type=WasteType(item['waste_type']), predicted_kg=item['predicted_kg'])
            for item in result['waste_type_breakdown']
        ]
        
        return UserPredictionResponse(
            user_id=result['user_id'],
            area=result['area'],
            prediction_date=result['prediction_date'],
            predicted_waste_kg=result['predicted_waste_kg'],
            waste_type_breakdown=breakdown,
            model=result['model'],
            horizon=result['horizon']
        )
    except Exception as e:
        print(f"Database ML predictor failed for user {user_id}: {e}")
        # Fall back to area-based prediction from database
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.area:
            return _get_best_available_prediction(db, user.area, prediction_date + timedelta(days=1), "day_after_next")
        return None


def get_area_predictions(db: Session, area: str = None, limit: int = 100) -> List[AreaPredictionResponse]:
    query = db.query(AreaPrediction)
    if area:
        query = query.filter(AreaPrediction.area == area)
    predictions = query.order_by(AreaPrediction.prediction_date.desc()).limit(limit).all()
    return [AreaPredictionResponse.model_validate(p) for p in predictions]


def get_overflow_risk(db: Session, area: str = None, limit: int = 100) -> List[OverflowRiskResponse]:
    query = db.query(OverflowRiskPrediction)
    if area:
        query = query.filter(OverflowRiskPrediction.area == area)
    risks = query.order_by(OverflowRiskPrediction.prediction_date.desc()).limit(limit).all()
    return [OverflowRiskResponse.model_validate(r) for r in risks]


def get_user_prediction_history(db: Session, user_id: str, limit: int = 20) -> List[UserPredictionResponse]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.area:
        return []
    
    area_preds = db.query(AreaPrediction).filter(
        AreaPrediction.area == user.area
    ).order_by(AreaPrediction.prediction_date.desc()).limit(limit).all()
    
    results = []
    for p in area_preds:
        breakdown = []
        for wt in WasteType:
            val = getattr(p, f"{wt.value}_predicted_kg", None)
            if val is not None:
                breakdown.append(WasteTypePrediction(waste_type=wt, predicted_kg=val))
        
        results.append(UserPredictionResponse(
            user_id=user_id,
            area=p.area,
            prediction_date=p.prediction_date.isoformat(),
            predicted_waste_kg=p.predicted_waste_kg,
            waste_type_breakdown=breakdown,
            model=p.model or "Unknown",
            horizon=p.horizon or "next_day"
        ))
    
    return results
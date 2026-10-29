from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from app.database.session import get_db
from app.schemas.prediction import (
    UserPredictionResponse,
    AreaPredictionResponse,
    OverflowRiskResponse,
    AreaWasteSummary,
)
from app.services.prediction import (
    predict_user_next_day,
    predict_user_day_after_next,
    get_area_predictions,
    get_overflow_risk,
    get_user_prediction_history,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/predictions", tags=["predictions"])


async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    token = authorization.replace("Bearer ", "")
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/my/next-day", response_model=Optional[UserPredictionResponse])
def get_my_next_day_prediction(
    user = Depends(get_current_user_from_token),
    prediction_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return predict_user_next_day(db, user.id, prediction_date)


@router.get("/my/day-after-next", response_model=Optional[UserPredictionResponse])
def get_my_day_after_next_prediction(
    user = Depends(get_current_user_from_token),
    prediction_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return predict_user_day_after_next(db, user.id, prediction_date)


@router.get("/my/history", response_model=List[UserPredictionResponse])
def get_my_prediction_history(
    user = Depends(get_current_user_from_token),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return get_user_prediction_history(db, user.id, limit)


@router.get("/area", response_model=List[AreaPredictionResponse])
def get_area_predictions_endpoint(
    area: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_area_predictions(db, area, limit)


@router.get("/overflow-risk", response_model=List[OverflowRiskResponse])
def get_overflow_risk_endpoint(
    area: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_overflow_risk(db, area, limit)


@router.get("/area-waste-summary", response_model=List[AreaWasteSummary])
def get_area_waste_summary(
    days: int = 30,
    db: Session = Depends(get_db)
):
    from app.services.admin import get_waste_by_area
    return get_waste_by_area(db, days)
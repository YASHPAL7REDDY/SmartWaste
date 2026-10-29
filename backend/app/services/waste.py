import uuid
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.waste import WasteSubmission, WasteItem
from app.schemas.waste import WasteSubmissionCreate, WasteItemCreate, WasteSubmissionVerify, WasteSubmissionResponse
from app.schemas.user import WasteType
from app.services.prediction import predict_user_next_day, predict_user_day_after_next


def get_user_profile(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_waste_submission(db: Session, user_id: str, submission: WasteSubmissionCreate) -> WasteSubmission:
    user = get_user_profile(db, user_id)
    if not user:
        raise ValueError("User not found")
    
    # Calculate total waste
    total_waste = sum(item.quantity_kg for item in submission.items)
    
    # Determine day type
    submission_date = submission.submission_date
    day_of_week = submission_date.weekday()
    day_type = "weekend" if day_of_week >= 5 else "normal_day"
    
    # Use current time if submission_time not provided
    submission_time = submission.submission_time or datetime.now().time()
    created_at = datetime.now()
    
    # Create submission
    db_submission = WasteSubmission(
        id=str(uuid.uuid4()),
        user_id=user_id,
        submission_date=submission_date,
        submission_time=submission_time,
        day_of_week=str(day_of_week),
        day_type=day_type,
        month=submission_date.month,
        account_type_snapshot=user.account_type,
        city_snapshot=user.city,
        area_snapshot=user.area,
        family_members_snapshot=user.family_members,
        customers_snapshot=user.avg_customers_per_day,
        people_present_snapshot=submission.people_present,
        total_waste_kg=total_waste,
        collection_status="pending",
        created_at=created_at,
    )
    
    db.add(db_submission)
    db.flush()
    
    # Create waste items
    for item in submission.items:
        db_item = WasteItem(
            id=str(uuid.uuid4()),
            submission_id=db_submission.id,
            waste_type=item.waste_type.value,
            quantity_kg=item.quantity_kg,
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_submission)
    
    # Trigger ML predictions for next day and day after next
    try:
        next_day_date = date.today() + timedelta(days=1)
        day_after_date = date.today() + timedelta(days=1)
        
        predict_user_next_day(db, user_id, next_day_date)
        predict_user_day_after_next(db, user_id, day_after_date)
    except Exception as e:
        # Don't fail the submission if prediction fails
        print(f"Prediction generation failed: {e}")
    
    return db_submission


def get_user_submissions(db: Session, user_id: str, limit: int = 50, offset: int = 0) -> List[WasteSubmission]:
    return db.query(WasteSubmission).filter(
        WasteSubmission.user_id == user_id
    ).order_by(WasteSubmission.submission_date.desc()).offset(offset).limit(limit).all()


def get_submission_with_items(db: Session, submission_id: str) -> Optional[WasteSubmission]:
    return db.query(WasteSubmission).filter(WasteSubmission.id == submission_id).first()


def get_submission_items(db: Session, submission_id: str) -> List[WasteItem]:
    return db.query(WasteItem).filter(WasteItem.submission_id == submission_id).all()


def prepare_verification_data(db: Session, user_id: str, submission: WasteSubmissionVerify) -> Dict:
    user = get_user_profile(db, user_id)
    if not user:
        raise ValueError("User not found")
    
    # Calculate total
    total_waste = sum(item.quantity_kg for item in submission.items)
    
    # Build breakdown
    breakdown = {}
    for item in submission.items:
        breakdown[item.waste_type.value] = item.quantity_kg
    
    # Ensure all waste types present
    for wt in WasteType:
        if wt.value not in breakdown:
            breakdown[wt.value] = 0.0
    
    return {
        "area": user.area,
        "date": submission.submission_date.isoformat(),
        "account_type": user.account_type,
        "family_members": user.family_members,
        "customers": user.avg_customers_per_day,
        "people_present": submission.people_present,
        "breakdown": breakdown,
        "total_waste_kg": total_waste,
    }
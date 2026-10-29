from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.schemas.waste import (
    WasteSubmissionCreate, 
    WasteSubmissionVerify, 
    WasteSubmissionResponse,
    WasteSubmissionSummary,
    WasteItemResponse
)
from app.services.waste import (
    create_waste_submission,
    get_user_submissions,
    get_submission_with_items,
    get_submission_items,
    prepare_verification_data,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/waste", tags=["waste"])


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


@router.post("/submit", response_model=WasteSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_waste(
    submission: WasteSubmissionCreate,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    db_submission = create_waste_submission(db, user.id, submission)
    
    # Get items for response
    items = get_submission_items(db, db_submission.id)
    
    return WasteSubmissionResponse(
        id=db_submission.id,
        user_id=db_submission.user_id,
        submission_date=db_submission.submission_date,
        submission_time=db_submission.submission_time,
        day_type=db_submission.day_type,
        people_present=db_submission.people_present_snapshot,
        total_waste_kg=db_submission.total_waste_kg,
        collection_status=db_submission.collection_status,
        collected_at=db_submission.collected_at,
        created_at=db_submission.created_at,
        items=[WasteItemResponse.model_validate(item) for item in items]
    )


@router.post("/verify", response_model=dict)
def verify_waste_submission(
    verification: WasteSubmissionVerify,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    verification_data = prepare_verification_data(db, user.id, verification)
    return verification_data


@router.get("/my-submissions", response_model=List[WasteSubmissionSummary])
def get_my_submissions(
    user = Depends(get_current_user_from_token),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    submissions = get_user_submissions(db, user.id, limit, offset)
    return [
        WasteSubmissionSummary(
            id=s.id,
            submission_date=s.submission_date,
            total_waste_kg=s.total_waste_kg,
            collection_status=s.collection_status,
            items_count=len(s.items) if s.items else 0
        )
        for s in submissions
    ]


@router.get("/submission/{submission_id}", response_model=WasteSubmissionResponse)
def get_submission(
    submission_id: str,
    user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    submission = get_submission_with_items(db, submission_id)
    if not submission or submission.user_id != user.id:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    items = get_submission_items(db, submission_id)
    
    return WasteSubmissionResponse(
        id=submission.id,
        user_id=submission.user_id,
        submission_date=submission.submission_date,
        submission_time=submission.submission_time,
        day_type=submission.day_type,
        people_present=submission.people_present_snapshot,
        total_waste_kg=submission.total_waste_kg,
        collection_status=submission.collection_status,
        collected_at=submission.collected_at,
        created_at=submission.created_at,
        items=[WasteItemResponse.model_validate(item) for item in items]
    )
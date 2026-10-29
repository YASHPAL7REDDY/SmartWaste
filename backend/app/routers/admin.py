from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from app.database.session import get_db
from app.services.admin import (
    get_total_stats,
    get_waste_by_area,
    get_waste_by_type,
    get_waste_by_account_type,
    get_facility_utilization,
    get_collector_performance,
    get_prediction_accuracy_stats,
    get_high_waste_areas,
    get_overflow_risk_summary,
    export_waste_data,
    get_all_collectors,
    get_waste_trends,
    get_ml_performance_metrics,
)
from app.services.collector import (
    get_real_world_accuracy_metrics,
    get_actual_vs_predicted_chart_data,
    get_prediction_evaluation_status,
    get_reliability_level,
)
from app.services.ml_monitoring import (
    detect_data_drift,
    get_performance_trend,
    get_model_health_status,
    get_model_comparison,
    get_ml_monitoring_full_report,
    ensure_training_reference_stats,
    persist_training_reference_stats,
    compute_training_reference_from_database,
    get_prediction_coverage,
)
from app.services.auth import get_current_user
from app.models.user import User
from app.models.prediction import AreaPrediction, OverflowRiskPrediction
from app.schemas.prediction import AreaPredictionResponse, OverflowRiskResponse

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_admin_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    token = authorization.replace("Bearer ", "")
    user = get_current_user(db, token)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats")
def get_admin_stats(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    return get_total_stats(db)


@router.get("/waste/by-area")
def get_waste_by_area_endpoint(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_waste_by_area(db, days)


@router.get("/waste/by-type")
def get_waste_by_type_endpoint(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_waste_by_type(db, days)


@router.get("/waste/by-account-type")
def get_waste_by_account_type_endpoint(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_waste_by_account_type(db, days)


@router.get("/facilities")
def get_facilities_endpoint(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    return get_facility_utilization(db)


@router.get("/collectors/performance")
def get_collectors_performance(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_collector_performance(db, days)


@router.get("/collectors")
def get_all_collectors_endpoint(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    return get_all_collectors(db)


@router.get("/waste/trends")
def get_waste_trends_endpoint(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_waste_trends(db, days)


@router.get("/predictions/accuracy")
def get_accuracy_stats(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    return get_prediction_accuracy_stats(db)


@router.get("/high-waste-areas")
def get_high_waste_areas_endpoint(
    user = Depends(get_admin_user_from_token),
    limit: int = 10,
    days: int = 30,
    db: Session = Depends(get_db)
):
    return get_high_waste_areas(db, limit, days)


@router.get("/overflow-risk/summary")
def get_overflow_risk_summary_endpoint(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    return get_overflow_risk_summary(db)


@router.get("/export")
def export_data_endpoint(
    start_date: date,
    end_date: date,
    format: str = "csv",
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    data = export_waste_data(db, start_date, end_date, format)
    
    media_type = "text/csv" if format.lower() == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = f"smartwaste_export_{start_date}_to_{end_date}.{format}"
    
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/predictions/by-type")
def get_predictions_by_type(
    user = Depends(get_admin_user_from_token),
    area: str = None,
    horizon: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(AreaPrediction)
    if area:
        query = query.filter(AreaPrediction.area == area)
    if horizon:
        query = query.filter(AreaPrediction.horizon == horizon)
    
    predictions = query.order_by(AreaPrediction.prediction_date.desc()).limit(limit).all()
    return [AreaPredictionResponse.model_validate(p) for p in predictions]


@router.get("/overflow-risk/details")
def get_overflow_risk_details(
    user = Depends(get_admin_user_from_token),
    area: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(OverflowRiskPrediction)
    if area:
        query = query.filter(OverflowRiskPrediction.area == area)
    
    risks = query.order_by(OverflowRiskPrediction.prediction_date.desc()).limit(limit).all()
    return [OverflowRiskResponse.model_validate(r) for r in risks]


@router.get("/ml-performance")
def get_ml_performance(
    user = Depends(get_admin_user_from_token)
):
    """Get ML model evaluation metrics and performance overview."""
    return get_ml_performance_metrics()


@router.get("/ml-performance/real-world-accuracy")
def get_real_world_accuracy(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get real-world prediction accuracy from actual collections."""
    return get_real_world_accuracy_metrics(db, days)


@router.get("/ml-performance/actual-vs-predicted")
def get_actual_vs_predicted(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    waste_type: str = 'total',
    db: Session = Depends(get_db)
):
    """Get Actual vs Predicted chart data for a specific waste type."""
    return get_actual_vs_predicted_chart_data(db, days, waste_type)


@router.get("/ml-performance/evaluation-status")
def get_evaluation_status(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get prediction evaluation status including coverage and unmatched reasons."""
    return get_prediction_evaluation_status(db, days)


@router.get("/ml-performance/reliability-level")
def get_reliability(
    user = Depends(get_admin_user_from_token),
    sample_count: int = 0,
):
    """Get reliability level for a given sample count."""
    return get_reliability_level(sample_count)


@router.get("/ml-monitoring/health")
def get_ml_health(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    """Get overall ML model health status."""
    return get_model_health_status(db)


@router.get("/ml-monitoring/data-drift")
def get_data_drift(
    user = Depends(get_admin_user_from_token),
    reference_days: int = 90,
    recent_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get data drift detection results."""
    return detect_data_drift(db, reference_days, recent_days)


@router.get("/ml-monitoring/performance-trend")
def get_performance_trend_endpoint(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    """Get model performance trends over rolling periods."""
    return get_performance_trend(db)


@router.get("/ml-monitoring/model-comparison")
def get_model_comparison_endpoint(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    """Compare production model against other trained models."""
    return get_model_comparison(db)


@router.get("/ml-monitoring/full-report")
def get_full_report(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    """Get complete ML monitoring report."""
    return get_ml_monitoring_full_report(db)


@router.get("/ml-monitoring/prediction-coverage")
def get_prediction_coverage_endpoint(
    user = Depends(get_admin_user_from_token),
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get prediction coverage analysis."""
    return get_prediction_coverage(db, days)


@router.get("/ml-monitoring/training-reference")
def get_training_reference(
    user = Depends(get_admin_user_from_token),
    db: Session = Depends(get_db)
):
    """Get training reference statistics."""
    return ensure_training_reference_stats(db)


@router.post("/ml-monitoring/training-reference/recompute")
def recompute_training_reference(
    user = Depends(get_admin_user_from_token),
    model_version: str = "PerTypeRF",
    db: Session = Depends(get_db)
):
    """Recompute training reference statistics from database history (proxy)."""
    computed = compute_training_reference_from_database(db, model_version)
    if not computed:
        raise HTTPException(status_code=404, detail="No database history available for reference computation")
    count = persist_training_reference_stats(db, computed, model_version)
    return {
        "message": f"Computed and persisted {count} training reference statistics from database history",
        "model_version": model_version,
        "source": "database_history_proxy",
        "note": "This is a PROXY computed from database history, NOT actual training data"
    }
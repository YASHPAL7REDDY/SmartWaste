import csv
import io
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date

from app.models.user import User, Collector
from app.models.waste import WasteSubmission, WasteItem, AreaCollection
from app.models.facility import WasteFacility, WasteGenerationZone
from app.models.prediction import AreaPrediction, OverflowRiskPrediction, PredictionAccuracy
from app.schemas.prediction import AreaWasteSummary


def get_total_stats(db: Session) -> Dict:
    total_users = db.query(func.count(User.id)).filter(User.is_admin == False, User.is_collector == False).scalar()
    total_collectors = db.query(func.count(User.id)).filter(User.is_collector == True).scalar()
    total_submissions = db.query(func.count(WasteSubmission.id)).scalar()
    total_waste_kg = db.query(func.sum(WasteSubmission.total_waste_kg)).scalar() or 0
    total_facilities = db.query(func.count(WasteFacility.id)).scalar()
    active_facilities = db.query(func.count(WasteFacility.id)).filter(WasteFacility.status.ilike("active")).scalar()
    
    return {
        "total_users": total_users,
        "total_collectors": total_collectors,
        "total_submissions": total_submissions,
        "total_waste_kg": round(total_waste_kg, 2),
        "total_facilities": total_facilities,
        "active_facilities": active_facilities,
    }


def get_waste_by_area(db: Session, days: int = 30) -> List[AreaWasteSummary]:
    cutoff = date.today() - timedelta(days=days)
    
    results = db.query(
        WasteSubmission.area_snapshot.label('area'),
        func.sum(WasteSubmission.total_waste_kg).label('total_waste'),
        func.count(WasteSubmission.id).label('submissions')
    ).filter(
        WasteSubmission.submission_date >= cutoff,
        WasteSubmission.area_snapshot.isnot(None)
    ).group_by(WasteSubmission.area_snapshot).order_by(desc('total_waste')).all()
    
    summaries = []
    for r in results:
        # Get waste type breakdown
        items = db.query(
            WasteItem.waste_type,
            func.sum(WasteItem.quantity_kg)
        ).join(WasteSubmission).filter(
            WasteSubmission.area_snapshot == r.area,
            WasteSubmission.submission_date >= cutoff
        ).group_by(WasteItem.waste_type).all()
        
        breakdown = {item.waste_type: float(item[1]) for item in items}
        
        summaries.append(AreaWasteSummary(
            area=r.area,
            total_waste_kg=round(float(r.total_waste), 2),
            wet_kg=round(breakdown.get('wet', 0), 2),
            dry_kg=round(breakdown.get('dry', 0), 2),
            plastic_kg=round(breakdown.get('plastic', 0), 2),
            glass_kg=round(breakdown.get('glass', 0), 2),
            metal_kg=round(breakdown.get('metal', 0), 2),
            medical_kg=round(breakdown.get('medical', 0), 2),
            submissions_count=r.submissions
        ))
    
    return summaries


def get_waste_by_type(db: Session, days: int = 30) -> Dict:
    cutoff = date.today() - timedelta(days=days)
    
    results = db.query(
        WasteItem.waste_type,
        func.sum(WasteItem.quantity_kg).label('total')
    ).join(WasteSubmission).filter(
        WasteSubmission.submission_date >= cutoff
    ).group_by(WasteItem.waste_type).all()
    
    # Normalize waste types to lowercase to avoid duplicates
    normalized = {}
    for r in results:
        key = r.waste_type.lower()
        normalized[key] = normalized.get(key, 0) + round(float(r.total), 2)
    
    # Return with proper capitalization for display
    display_names = {'wet': 'Wet', 'dry': 'Dry', 'plastic': 'Plastic', 'glass': 'Glass', 'metal': 'Metal', 'medical': 'Medical'}
    return {display_names.get(k, k.title()): v for k, v in normalized.items()}


def get_waste_by_account_type(db: Session, days: int = 30) -> Dict:
    cutoff = date.today() - timedelta(days=days)
    
    results = db.query(
        WasteSubmission.account_type_snapshot,
        func.sum(WasteSubmission.total_waste_kg).label('total'),
        func.count(WasteSubmission.id).label('count')
    ).filter(
        WasteSubmission.submission_date >= cutoff
    ).group_by(WasteSubmission.account_type_snapshot).all()
    
    return {
        r.account_type_snapshot: {
            "total_waste_kg": round(float(r.total), 2),
            "submissions": r.count
        }
        for r in results
    }


def get_facility_utilization(db: Session) -> List[Dict]:
    facilities = db.query(WasteFacility).filter(WasteFacility.status.ilike("active")).all()
    results = []
    for f in facilities:
        capacity = f.capacity_kg_per_day or 0
        results.append({
            "facility_id": f.id,
            "facility_name": f.facility_name,
            "facility_type": f.facility_type,
            "capacity_kg_per_day": capacity,
            "area": f.area_name,
            "status": f.status
        })
    return results


def get_collector_performance(db: Session, days: int = 30) -> List[Dict]:
    cutoff = date.today() - timedelta(days=days)
    
    collections = db.query(AreaCollection).filter(
        AreaCollection.collection_date >= cutoff
    ).all()
    
    collector_stats = {}
    for c in collections:
        if not c.collector_id:
            continue
        if c.collector_id not in collector_stats:
            collector_stats[c.collector_id] = {
                "collector_id": c.collector_id,
                "total_collections": 0,
                "completed": 0,
                "total_predicted": 0,
                "total_collected": 0
            }
        stats = collector_stats[c.collector_id]
        stats["total_collections"] += 1
        if c.status == "completed":
            stats["completed"] += 1
        stats["total_predicted"] += c.predicted_waste_kg or 0
        stats["total_collected"] += c.collected_waste_kg or 0
    
    return list(collector_stats.values())


def get_prediction_accuracy_stats(db: Session) -> List[Dict]:
    accuracy = db.query(PredictionAccuracy).order_by(PredictionAccuracy.prediction_date.desc()).limit(100).all()
    
    results = []
    for a in accuracy:
        results.append({
            "area": a.area,
            "prediction_date": a.prediction_date.isoformat(),
            "horizon": a.horizon,
            "model": a.model,
            "waste_type": a.waste_type,
            "predicted_kg": a.predicted_kg,
            "actual_kg": a.actual_kg,
            "absolute_error_kg": a.absolute_error_kg,
            "percentage_error": a.percentage_error
        })
    return results


def get_high_waste_areas(db: Session, limit: int = 10, days: int = 30) -> List[Dict]:
    # Get areas with highest waste generation from actual submissions
    cutoff = date.today() - timedelta(days=days)
    
    results = db.query(
        WasteSubmission.area_snapshot.label('area'),
        func.sum(WasteSubmission.total_waste_kg).label('total_waste'),
        func.count(WasteSubmission.id).label('submissions')
    ).filter(
        WasteSubmission.submission_date >= cutoff,
        WasteSubmission.area_snapshot.isnot(None)
    ).group_by(WasteSubmission.area_snapshot).order_by(desc('total_waste')).limit(limit).all()
    
    summaries = []
    for r in results:
        # Get waste type breakdown
        items = db.query(
            WasteItem.waste_type,
            func.sum(WasteItem.quantity_kg)
        ).join(WasteSubmission).filter(
            WasteSubmission.area_snapshot == r.area,
            WasteSubmission.submission_date >= cutoff
        ).group_by(WasteItem.waste_type).all()
        
        breakdown = {item.waste_type.lower(): float(item[1]) for item in items}
        
        # Get city from any submission in this area
        city_result = db.query(WasteSubmission.city_snapshot).filter(
            WasteSubmission.area_snapshot == r.area
        ).first()
        city = city_result[0] if city_result else "Unknown"
        
        summaries.append({
            "area": r.area,
            "city": city,
            "total_waste_kg_per_day": round(float(r.total_waste) / days, 2),
            "wet_kg": round(breakdown.get('wet', 0) / days, 2),
            "dry_kg": round(breakdown.get('dry', 0) / days, 2),
            "plastic_kg": round(breakdown.get('plastic', 0) / days, 2),
            "glass_kg": round(breakdown.get('glass', 0) / days, 2),
            "metal_kg": round(breakdown.get('metal', 0) / days, 2),
            "medical_kg": round(breakdown.get('medical', 0) / days, 2),
        })
    
    return summaries


def get_overflow_risk_summary(db: Session) -> Dict:
    today_risks = db.query(OverflowRiskPrediction).filter(
        OverflowRiskPrediction.prediction_date == date.today()
    ).all()
    
    if not today_risks:
        return {"total_areas_at_risk": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    
    risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in today_risks:
        level = (r.risk_level or "").lower()
        if level in risk_counts:
            risk_counts[level] += 1
    
    return {
        "total_areas_at_risk": len(today_risks),
        **risk_counts
    }


def export_waste_data(db: Session, start_date: date, end_date: date, format: str = "csv") -> bytes:
    """Export waste submission data with individual waste categories."""
    submissions = db.query(WasteSubmission).filter(
        WasteSubmission.submission_date >= start_date,
        WasteSubmission.submission_date <= end_date
    ).order_by(WasteSubmission.submission_date.desc()).all()
    
    # Prepare data rows
    rows = []
    for sub in submissions:
        # Get waste items for this submission
        items = db.query(WasteItem).filter(WasteItem.submission_id == sub.id).all()
        breakdown = {item.waste_type: item.quantity_kg for item in items}
        
        row = {
            "Date": sub.submission_date.isoformat() if sub.submission_date else "",
            "Area": sub.area_snapshot or "",
            "User ID": sub.user_id or "",
            "Account Type": sub.account_type_snapshot or "",
            "Wet (kg)": round(breakdown.get('wet', 0), 2),
            "Dry (kg)": round(breakdown.get('dry', 0), 2),
            "Plastic (kg)": round(breakdown.get('plastic', 0), 2),
            "Glass (kg)": round(breakdown.get('glass', 0), 2),
            "Metal (kg)": round(breakdown.get('metal', 0), 2),
            "Medical (kg)": round(breakdown.get('medical', 0), 2),
            "Total (kg)": round(sub.total_waste_kg, 2),
            "Collection Status": sub.collection_status or "",
        }
        rows.append(row)
    
    if format.lower() == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return output.getvalue().encode('utf-8')
    else:
        # For Excel, return CSV for now (can be enhanced with openpyxl)
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return output.getvalue().encode('utf-8')


def get_all_collectors(db: Session) -> List[Dict]:
    collectors = db.query(Collector).filter(Collector.is_active == True).all()
    results = []
    for c in collectors:
        user = db.query(User).filter(User.id == c.user_id).first()
        results.append({
            "id": c.id,
            "user_id": c.user_id,
            "employee_id": c.employee_id,
            "name": c.name,
            "mobile": c.mobile,
            "vehicle_number": c.vehicle_number,
            "vehicle_capacity_kg": c.vehicle_capacity_kg,
            "assigned_areas": c.assigned_areas,
            "is_active": c.is_active,
            "email": user.email if user else None,
        })
    return results


def get_waste_trends(db: Session, days: int = 30) -> List[Dict]:
    cutoff = date.today() - timedelta(days=days)
    
    results = db.query(
        WasteSubmission.submission_date.label('date'),
        func.sum(WasteSubmission.total_waste_kg).label('total_waste_kg'),
        func.count(WasteSubmission.id).label('submissions')
    ).filter(
        WasteSubmission.submission_date >= cutoff
    ).group_by(WasteSubmission.submission_date).order_by(WasteSubmission.submission_date).all()
    
    return [{
        "date": r.date.isoformat() if r.date else None,
        "total_waste_kg": round(float(r.total_waste_kg), 2),
        "submissions": r.submissions
    } for r in results]


def get_ml_performance_metrics() -> Dict:
    """Load ML model evaluation metrics from existing metric files."""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    improved_metrics_path = project_root / "MLproject" / "ml" / "models" / "improved" / "metrics.json"
    multi_rf_path = project_root / "ml" / "models" / "multi_waste_rf_metrics.json"
    multi_xgb_path = project_root / "ml" / "models" / "multi_waste_xgb_metrics.json"
    rf_path = project_root / "ml" / "models" / "rf_metrics.json"
    xgb_path = project_root / "ml" / "models" / "xgb_metrics.json"
    
    result = {
        "model_overview": {},
        "waste_type_performance": {},
        "model_comparison": {},
        "actual_vs_predicted": None,
        "model_insights": {},
        "project_summary": {}
    }
    
    # Load improved models metrics (main models used in production)
    improved_metrics = {}
    if improved_metrics_path.exists():
        with open(improved_metrics_path) as f:
            improved_metrics = json.load(f)
    
    # Load original multi-output models metrics
    multi_rf_metrics = {}
    if multi_rf_path.exists():
        with open(multi_rf_path) as f:
            multi_rf_metrics = json.load(f)
    
    multi_xgb_metrics = {}
    if multi_xgb_path.exists():
        with open(multi_xgb_path) as f:
            multi_xgb_metrics = json.load(f)
    
    rf_metrics = {}
    if rf_path.exists():
        with open(rf_path) as f:
            rf_metrics = json.load(f)
    
    xgb_metrics = {}
    if xgb_path.exists():
        with open(xgb_path) as f:
            xgb_metrics = json.load(f)
    
    # ===== SECTION 1: MODEL OVERVIEW =====
    models_to_show = [
        ("PerTypeRF", "Per-Type Random Forest (Two-Stage)", improved_metrics.get("RF_PerType", {})),
        ("RF_Multi", "Multi-Output Random Forest", improved_metrics.get("RF_Multi", {})),
        ("XGB_Multi", "Multi-Output XGBoost", improved_metrics.get("XGB_Multi", {})),
        ("XGB_PerType", "Per-Type XGBoost (Two-Stage)", improved_metrics.get("XGB_PerType", {})),
    ]
    
    for model_id, model_name, metrics in models_to_show:
        if metrics:
            result["model_overview"][model_id] = {
                "name": model_name,
                "type": "Per-Type Two-Stage" if "PerType" in model_id else "Multi-Output",
                "status": "Evaluated",
                "R2": round(metrics.get("R2", 0), 4),
                "MAE": round(metrics.get("MAE", 0), 4),
                "RMSE": round(metrics.get("RMSE", 0), 4),
                "MAPE": round(metrics.get("MAPE", 0), 2) if metrics.get("MAPE") else "N/A",
                "SMAPE": round(metrics.get("SMAPE", 0), 2) if metrics.get("SMAPE") else "N/A",
            }
        else:
            result["model_overview"][model_id] = {
                "name": model_name,
                "type": "Per-Type Two-Stage" if "PerType" in model_id else "Multi-Output",
                "status": "No evaluation metrics available",
                "R2": "N/A",
                "MAE": "N/A",
                "RMSE": "N/A",
                "MAPE": "N/A",
                "SMAPE": "N/A",
            }
    
    # ===== SECTION 2: WASTE TYPE PERFORMANCE (from multi-output model metrics) =====
    waste_types = ["wet", "dry", "plastic", "glass", "metal", "medical", "total"]
    waste_type_display = {
        "wet": "Wet Waste",
        "dry": "Dry Waste", 
        "plastic": "Plastic Waste",
        "glass": "Glass Waste",
        "metal": "Metal Waste",
        "medical": "Medical Waste",
        "total": "Total Waste"
    }
    
    # Extract per-type metrics from multi-output models
    for wt in waste_types:
        row = {"waste_type": waste_type_display[wt]}
        
        # Try to get from RF_Multi test metrics
        if multi_rf_metrics.get("test_metrics"):
            test_m = multi_rf_metrics["test_metrics"]
            if wt == "total":
                # Total waste metrics are in total_waste_metrics section
                total_m = multi_rf_metrics.get("total_waste_metrics", {})
                row["R2"] = round(total_m.get("test_TOTAL_R2", 0), 4)
                row["MAE"] = round(total_m.get("test_TOTAL_MAE", 0), 4)
                row["RMSE"] = round(total_m.get("test_TOTAL_RMSE", 0), 4)
                row["MAPE"] = round(total_m.get("test_TOTAL_MAPE", 0), 2)
            else:
                r2_key = f"test_next_day_{wt}_kg_R2"
                mae_key = f"test_next_day_{wt}_kg_MAE"
                rmse_key = f"test_next_day_{wt}_kg_RMSE"
                mape_key = f"test_next_day_{wt}_kg_MAPE"
                row["R2"] = round(test_m.get(r2_key, 0), 4)
                row["MAE"] = round(test_m.get(mae_key, 0), 4)
                row["RMSE"] = round(test_m.get(rmse_key, 0), 4)
                mape_val = test_m.get(mape_key, 0)
                row["MAPE"] = round(mape_val, 2) if mape_val < 1000 else "N/A"
        
        # If not available, try XGB_Multi
        if "R2" not in row and multi_xgb_metrics.get("test_metrics"):
            test_m = multi_xgb_metrics["test_metrics"]
            if wt == "total":
                total_m = multi_xgb_metrics.get("total_waste_metrics", {})
                row["R2"] = round(total_m.get("test_TOTAL_R2", 0), 4)
                row["MAE"] = round(total_m.get("test_TOTAL_MAE", 0), 4)
                row["RMSE"] = round(total_m.get("test_TOTAL_RMSE", 0), 4)
                row["MAPE"] = round(total_m.get("test_TOTAL_MAPE", 0), 2)
            else:
                r2_key = f"test_next_day_{wt}_kg_R2"
                mae_key = f"test_next_day_{wt}_kg_MAE"
                rmse_key = f"test_next_day_{wt}_kg_RMSE"
                mape_key = f"test_next_day_{wt}_kg_MAPE"
                row["R2"] = round(test_m.get(r2_key, 0), 4)
                row["MAE"] = round(test_m.get(mae_key, 0), 4)
                row["RMSE"] = round(test_m.get(rmse_key, 0), 4)
                mape_val = test_m.get(mape_key, 0)
                row["MAPE"] = round(mape_val, 2) if mape_val < 1000 else "N/A"
        
        # If still not available, mark as N/A
        for metric in ["R2", "MAE", "RMSE", "MAPE"]:
            if metric not in row:
                row[metric] = "N/A"
        
        result["waste_type_performance"][wt] = row
    
    # ===== SECTION 3: MODEL COMPARISON =====
    comparison_metrics = ["R2", "MAE", "RMSE"]
    for metric in comparison_metrics:
        result["model_comparison"][metric] = {}
        for model_id, model_name, metrics in models_to_show:
            if metrics:
                val = metrics.get(metric)
                result["model_comparison"][metric][model_id] = {
                    "name": model_name,
                    "value": round(val, 4) if val else "N/A"
                }
            else:
                result["model_comparison"][metric][model_id] = {
                    "name": model_name,
                    "value": "N/A"
                }
    
    # ===== SECTION 4: ACTUAL VS PREDICTED =====
    # Check if we have enough prediction accuracy data
    result["actual_vs_predicted"] = {
        "available": False,
        "message": "Actual vs Predicted analysis will appear after sufficient matched collection data is available."
    }
    
    # ===== SECTION 5: MODEL INSIGHTS =====
    # Find best model by R2
    best_model = None
    best_r2 = -1
    for model_id, model_name, metrics in models_to_show:
        if metrics and metrics.get("R2", 0) > best_r2:
            best_r2 = metrics["R2"]
            best_model = model_name
    
    # Find strongest/weakest category from waste type performance
    r2_values = {}
    for wt, data in result["waste_type_performance"].items():
        if isinstance(data.get("R2"), (int, float)):
            r2_values[wt] = data["R2"]
    
    strongest = max(r2_values.items(), key=lambda x: x[1]) if r2_values else ("N/A", "N/A")
    weakest = min(r2_values.items(), key=lambda x: x[1]) if r2_values else ("N/A", "N/A")
    
    total_waste_r2 = result["waste_type_performance"].get("total", {}).get("R2", "N/A")
    
    result["model_insights"] = {
        "best_performing_model": best_model or "N/A",
        "strongest_category": waste_type_display.get(strongest[0], strongest[0]) if strongest[0] != "N/A" else "N/A",
        "weakest_category": waste_type_display.get(weakest[0], weakest[0]) if weakest[0] != "N/A" else "N/A",
        "total_waste_r2": total_waste_r2
    }
    
    # ===== SECTION 6: PROJECT ML SUMMARY =====
    # Get dataset info from available metrics
    n_features = improved_metrics.get("RF_Multi", {}).get("n_features") or \
                 multi_rf_metrics.get("n_features") or \
                 rf_metrics.get("n_features", "N/A")
    
    n_train = multi_rf_metrics.get("n_train_samples") or \
              rf_metrics.get("n_train_samples", "N/A")
    n_val = multi_rf_metrics.get("n_val_samples") or \
            rf_metrics.get("n_val_samples", "N/A")
    n_test = multi_rf_metrics.get("n_test_samples") or \
             rf_metrics.get("n_test_samples", "N/A")
    
    result["project_summary"] = {
        "dataset_rows": {
            "train": n_train,
            "validation": n_val,
            "test": n_test,
            "total": (n_train if isinstance(n_train, int) else 0) + 
                     (n_val if isinstance(n_val, int) else 0) + 
                     (n_test if isinstance(n_test, int) else 0)
        },
        "feature_count": n_features,
        "training_approach": "Chronological/temporal split (train: ~2024-08, val: ~2024-11, test: ~2025+)",
        "validation_approach": "Time-series aware temporal validation",
        "test_approach": "Hold-out test set with future dates",
        "prediction_horizons": ["next_day", "day_after_next"],
        "evaluation_note": "Metrics computed on hold-out test set with chronological ordering to prevent data leakage"
    }
    
    return result
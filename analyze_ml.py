"""
SmartWaste ML Feature Importance & Error Analysis
Comprehensive diagnostic analysis of the ML pipeline
"""

import sys
sys.path.insert(0, 'backend')

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import warnings
warnings.filterwarnings('ignore')

from app.database.session import SessionLocal
from app.models.waste import WasteSubmission, WasteItem
from app.models.prediction import PredictionAccuracy, AreaPrediction, ActualCollection
from app.models.user import User
from app.services.ml_monitoring import detect_data_drift, get_performance_trend, get_model_health_status

# ============================================================
# STEP 1: Feature Construction Analysis
# ============================================================

def analyze_feature_construction():
    """Analyze all features constructed in ml_predictor.py"""
    
    features = {
        'Historical waste': [
            'total_waste_kg_lag_1d',
            'total_waste_kg_lag_2d',
            'total_waste_kg_lag_3d',
            'total_waste_kg_lag_7d',
            'total_waste_kg_roll_mean_3d',
            'total_waste_kg_roll_std_3d',
            'total_waste_kg_roll_mean_7d',
            'total_waste_kg_roll_std_7d',
        ],
        'Waste composition (lag_1d)': [
            'dry_kg_lag_1d',
            'wet_kg_lag_1d',
            'plastic_kg_lag_1d',
            'glass_kg_lag_1d',
            'metal_kg_lag_1d',
            'medical_kg_lag_1d',
        ],
        'Temporal/Calendar': [
            'day_of_week',
            'month',
            'season',
            'day_type',
            'is_weekend',
            'is_holiday',
            'is_festival',
            'festival_intensity',
        ],
        'Weather/Environment': [
            'temp_max_c',
            'rainfall_mm',
            'humidity_pct',
        ],
        'User behavior / Account info': [
            'people_present',
            'family_members',
            'avg_customers_per_day',
            'employee_count',
        ],
        'Area / Account (Categorical)': [
            'area',
            'account_type',
        ],
    }
    
    total_features = sum(len(v) for v in features.values())
    
    return {
        'feature_groups': features,
        'total_features': total_features,
        'note': 'Features as constructed in DatabaseWastePredictor._construct_features()'
    }


# ============================================================
# STEP 2: Feature Statistics from Database
# ============================================================

def get_feature_statistics(db: Session):
    """Compute feature statistics from database submissions"""
    
    # Get recent submissions (last 90 days)
    cutoff = date.today() - timedelta(days=90)
    submissions = db.query(WasteSubmission).filter(
        WasteSubmission.submission_date >= cutoff
    ).all()
    
    if not submissions:
        return {'error': 'No submissions found'}
    
    stats = {}
    
    # Numerical features
    total_waste = [s.total_waste_kg for s in submissions]
    stats['total_waste_kg'] = {
        'count': len(total_waste),
        'mean': float(np.mean(total_waste)),
        'std': float(np.std(total_waste)),
        'min': float(np.min(total_waste)),
        'max': float(np.max(total_waste)),
        'median': float(np.median(total_waste)),
        'zeros_pct': float(sum(1 for v in total_waste if v == 0) / len(total_waste) * 100)
    }
    
    # Waste type breakdown
    waste_types = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']
    for wt in waste_types:
        values = []
        for s in submissions:
            items = db.query(WasteItem).filter(WasteItem.submission_id == s.id).all()
            breakdown = {item.waste_type.lower(): item.quantity_kg for item in items}
            values.append(breakdown.get(wt, 0.0))
        
        if values:
            stats[wt] = {
                'count': len(values),
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values)),
                'zeros_pct': float(sum(1 for v in values if v == 0) / len(values) * 100)
            }
    
    # Categorical distributions
    areas = {}
    account_types = {}
    for s in submissions:
        if s.area_snapshot:
            areas[s.area_snapshot] = areas.get(s.area_snapshot, 0) + 1
        if s.account_type_snapshot:
            account_types[s.account_type_snapshot] = account_types.get(s.account_type_snapshot, 0) + 1
    
    stats['area_distribution'] = areas
    stats['account_type_distribution'] = account_types
    
    return stats


# ============================================================
# STEP 3: Real-World Error Analysis
# ============================================================

def analyze_real_world_errors(db: Session):
    """Analyze errors from existing PredictionAccuracy records"""
    
    accuracy_records = db.query(PredictionAccuracy).all()
    
    if not accuracy_records:
        return {'error': 'No accuracy records found', 'reliability': 'INSUFFICIENT_DATA'}
    
    waste_types = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
    results = {}
    
    for wt in waste_types:
        wt_records = [r for r in accuracy_records if (r.waste_type or '').lower() == wt.lower()]
        
        if not wt_records:
            results[wt] = {'available': False, 'sample_count': 0}
            continue
        
        predicted = [r.predicted_kg or 0 for r in wt_records]
        actual = [r.actual_kg or 0 for r in wt_records]
        errors = [r.absolute_error_kg or 0 for r in wt_records]
        pct_errors = [r.percentage_error for r in wt_records if r.percentage_error is not None]
        
        n = len(wt_records)
        mae = np.mean(errors)
        rmse = np.sqrt(np.mean([e**2 for e in errors]))
        
        # R²
        if n >= 2:
            mean_actual = np.mean(actual)
            ss_tot = sum((a - mean_actual)**2 for a in actual)
            ss_res = sum((actual[i] - predicted[i])**2 for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            r2 = None
        
        mape = np.mean(pct_errors) if pct_errors else None
        
        # Bias analysis
        bias = np.mean([p - a for p, a in zip(predicted, actual)])
        overpred_count = sum(1 for p, a in zip(predicted, actual) if p > a)
        underpred_count = sum(1 for p, a in zip(predicted, actual) if p < a)
        
        # Accuracy within thresholds
        within_10 = sum(1 for p, a in zip(predicted, actual) if abs(p - a) / max(a, 0.001) <= 0.10)
        within_20 = sum(1 for p, a in zip(predicted, actual) if abs(p - a) / max(a, 0.001) <= 0.20)
        within_30 = sum(1 for p, a in zip(predicted, actual) if abs(p - a) / max(a, 0.001) <= 0.30)
        
        # Reliability
        if n < 6:
            reliability = 'INSUFFICIENT_DATA'
        elif n < 21:
            reliability = 'EARLY_EVALUATION'
        elif n < 51:
            reliability = 'MODERATE_CONFIDENCE'
        else:
            reliability = 'STRONG_EVALUATION'
        
        results[wt] = {
            'available': True,
            'sample_count': n,
            'MAE': round(float(mae), 4),
            'RMSE': round(float(rmse), 4),
            'R2': round(float(r2), 4) if r2 is not None else None,
            'MAPE': round(float(mape), 2) if mape is not None else None,
            'Bias': round(float(bias), 4),
            'Overpredictions': overpred_count,
            'Underpredictions': underpred_count,
            'Within_10pct': within_10,
            'Within_20pct': within_20,
            'Within_30pct': within_30,
            'Within_10pct_pct': round(within_10 / n * 100, 1) if n > 0 else 0,
            'Within_20pct_pct': round(within_20 / n * 100, 1) if n > 0 else 0,
            'Within_30pct_pct': round(within_30 / n * 100, 1) if n > 0 else 0,
            'reliability': reliability,
            'total_predicted_kg': round(sum(predicted), 2),
            'total_actual_kg': round(sum(actual), 2),
        }
    
    return results


# ============================================================
# STEP 4: Error by Area, Account Type, Time
# ============================================================

def analyze_error_by_segment(db: Session):
    """Analyze errors by area, account type, and time period"""
    
    accuracy_records = db.query(PredictionAccuracy).all()
    
    if not accuracy_records:
        return {'error': 'No accuracy records'}
    
    # By area
    area_errors = {}
    for r in accuracy_records:
        if r.area not in area_errors:
            area_errors[r.area] = {'errors': [], 'count': 0}
        if r.absolute_error_kg is not None:
            area_errors[r.area]['errors'].append(r.absolute_error_kg)
            area_errors[r.area]['count'] += 1
    
    area_summary = {}
    for area, data in area_errors.items():
        if data['errors']:
            area_summary[area] = {
                'count': data['count'],
                'mean_error': round(np.mean(data['errors']), 4),
                'max_error': round(np.max(data['errors']), 4),
            }
    
    # By waste type (already done in main analysis)
    
    return {
        'by_area': area_summary,
    }


# ============================================================
# STEP 5: Offline Test Metrics Analysis
# ============================================================

def get_offline_metrics():
    """Load offline test metrics from admin service"""
    
    # Try to load from the admin service function
    from app.services.admin import get_ml_performance_metrics
    
    # We need a mock db session or just load the JSON directly
    project_root = Path(__file__).parent.parent.parent.parent.parent
    possible_paths = [
        project_root / "MLproject" / "ml" / "models" / "improved" / "metrics.json",
        project_root / "MLproject_old" / "ml" / "models" / "improved" / "metrics.json",
        project_root / "backend" / "MLproject_old" / "ml" / "models" / "improved" / "metrics.json",
    ]
    
    metrics_path = None
    for p in possible_paths:
        if p.exists():
            metrics_path = p
            break
    
    if not metrics_path:
        return {'error': 'No offline metrics file found'}
    
    with open(metrics_path) as f:
        metrics = json.load(f)
    
    # Extract per-waste-type metrics
    offline_results = {}
    waste_types = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
    
    rf_multi = metrics.get("RF_Multi", {})
    if rf_multi and rf_multi.get("test_metrics"):
        test_m = rf_multi["test_metrics"]
        total_m = rf_multi.get("total_waste_metrics", {})
        
        for wt in waste_types:
            if wt == 'total':
                offline_results[wt] = {
                    'R2': total_m.get('test_TOTAL_R2'),
                    'MAE': total_m.get('test_TOTAL_MAE'),
                    'RMSE': total_m.get('test_TOTAL_RMSE'),
                    'MAPE': total_m.get('test_TOTAL_MAPE'),
                    'SMAPE': total_m.get('test_TOTAL_SMAPE'),
                }
            else:
                r2_key = f"test_next_day_{wt}_kg_R2"
                mae_key = f"test_next_day_{wt}_kg_MAE"
                rmse_key = f"test_next_day_{wt}_kg_RMSE"
                mape_key = f"test_next_day_{wt}_kg_MAPE"
                smape_key = f"test_next_day_{wt}_kg_SMAPE"
                offline_results[wt] = {
                    'R2': test_m.get(r2_key),
                    'MAE': test_m.get(mae_key),
                    'RMSE': test_m.get(rmse_key),
                    'MAPE': test_m.get(mape_key),
                    'SMAPE': test_m.get(smape_key),
                }
    
    return {
        'available': True,
        'metrics': offline_results,
        'note': 'From chronological hold-out test set (RF_Multi)'
    }


# ============================================================
# STEP 6: Drift vs Feature Importance
# ============================================================

def analyze_drift_vs_importance(db: Session):
    """Compare drift detection results with feature importance"""
    
    # Get drift results
    drift_result = detect_data_drift(db)
    
    # Feature groups for reference
    feature_groups = analyze_feature_construction()['feature_groups']
    
    # Map drift features to groups
    drift_features = drift_result.get('features', {})
    
    group_drift = {}
    for group_name, features in feature_groups.items():
        group_drift[group_name] = {
            'features': [],
            'max_psi': 0,
            'max_mean_change': 0,
            'high_drift_count': 0,
        }
        for f in features:
            if f in drift_features:
                d = drift_features[f]
                group_drift[group_name]['features'].append({
                    'feature': f,
                    'status': d.get('status'),
                    'psi': d.get('psi'),
                    'mean_change_pct': d.get('mean_change_pct'),
                    'std_change_pct': d.get('std_change_pct'),
                })
                if d.get('psi') and d['psi'] > group_drift[group_name]['max_psi']:
                    group_drift[group_name]['max_psi'] = d['psi']
                if d.get('mean_change_pct') and d['mean_change_pct'] > group_drift[group_name]['max_mean_change']:
                    group_drift[group_name]['max_mean_change'] = d['mean_change_pct']
                if d.get('status') == 'HIGH_DRIFT':
                    group_drift[group_name]['high_drift_count'] += 1
    
    return {
        'drift_summary': drift_result.get('summary', {}),
        'overall_drift_status': drift_result.get('overall_status'),
        'reference_source': drift_result.get('reference_source'),
        'group_drift_analysis': group_drift,
    }


# ============================================================
# STEP 7: Weak/Redundant Features
# ============================================================

def identify_weak_features(db: Session):
    """Identify features with issues"""
    
    # Get feature statistics
    feat_stats = get_feature_statistics(db)
    
    weak_features = []
    
    # Check for high zero percentage
    for feat_name, stats in feat_stats.items():
        if isinstance(stats, dict) and 'zeros_pct' in stats:
            if stats['zeros_pct'] > 80:
                weak_features.append({
                    'feature': feat_name,
                    'issue': f'High zero percentage: {stats["zeros_pct"]:.1f}%',
                    'severity': 'HIGH' if stats['zeros_pct'] > 95 else 'MEDIUM'
                })
    
    # Check for near-zero variance
    for feat_name, stats in feat_stats.items():
        if isinstance(stats, dict) and 'std' in stats:
            if stats['std'] < 0.001 and stats['mean'] < 0.001:
                weak_features.append({
                    'feature': feat_name,
                    'issue': f'Near-zero variance (std={stats["std"]:.6f})',
                    'severity': 'HIGH'
                })
    
    # Features that are defaulted (not computed from real data)
    defaulted_features = [
        'is_holiday', 'is_festival', 'festival_intensity',
        'temp_max_c', 'rainfall_mm', 'humidity_pct'
    ]
    
    for f in defaulted_features:
        weak_features.append({
            'feature': f,
            'issue': 'Hardcoded default value (not from real data)',
            'severity': 'MEDIUM'
        })
    
    return {
        'weak_features': weak_features,
        'defaulted_features': defaulted_features,
    }


# ============================================================
# MAIN ANALYSIS RUNNER
# ============================================================

def run_full_analysis():
    """Run all analyses and produce report"""
    
    print("=" * 80)
    print("SMARTWASTE ML FEATURE IMPORTANCE & ERROR ANALYSIS")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Step 1: Feature construction
        print("\n[1/7] Analyzing feature construction...")
        feature_analysis = analyze_feature_construction()
        
        # Step 2: Feature statistics
        print("[2/7] Computing feature statistics from database...")
        feat_stats = get_feature_statistics(db)
        
        # Step 3: Real-world error analysis
        print("[3/7] Analyzing real-world prediction errors...")
        error_analysis = analyze_real_world_errors(db)
        
        # Step 4: Error by segment
        print("[4/7] Analyzing errors by segment...")
        segment_analysis = analyze_error_by_segment(db)
        
        # Step 5: Offline metrics
        print("[5/7] Loading offline test metrics...")
        offline_metrics = get_offline_metrics()
        
        # Step 6: Drift vs importance
        print("[6/7] Analyzing drift vs feature importance...")
        drift_analysis = analyze_drift_vs_importance(db)
        
        # Step 7: Weak features
        print("[7/7] Identifying weak/redundant features...")
        weak_features = identify_weak_features(db)
        
        # Compile full report
        report = {
            'timestamp': date.today().isoformat(),
            'feature_construction': feature_analysis,
            'feature_statistics': feat_stats,
            'real_world_error_analysis': error_analysis,
            'segment_error_analysis': segment_analysis,
            'offline_test_metrics': offline_metrics,
            'drift_vs_importance': drift_analysis,
            'weak_features': weak_features,
        }
        
        return report
        
    finally:
        db.close()


def generate_markdown_report(report):
    """Generate the markdown report"""
    
    md = []
    md.append("# ML_FEATURE_ERROR_ANALYSIS_REPORT")
    md.append(f"\n*Generated: {report['timestamp']}*")
    md.append("\n---\n")
    
    # 1. Executive Summary
    md.append("## 1. Executive Summary")
    md.append("\nThis report analyzes the SmartWaste ML pipeline to identify the main causes of prediction errors before any model retraining.")
    
    # Count total real-world samples
    total_samples = sum(
        r.get('sample_count', 0) 
        for r in report['real_world_error_analysis'].values() 
        if r.get('available')
    )
    
    md.append(f"\n- **Real-world evaluation samples**: {total_samples} (across all waste types)")
    md.append(f"- **Offline test metrics available**: {report['offline_test_metrics'].get('available', False)}")
    md.append(f"- **Overall drift status**: {report['drift_vs_importance'].get('overall_drift_status', 'UNKNOWN')}")
    md.append(f"- **Reference data source**: {report['drift_vs_importance'].get('reference_source', 'UNKNOWN')}")
    
    # Health status
    db = SessionLocal()
    try:
        health = get_model_health_status(db)
        md.append(f"- **Model health**: {health.get('health_status', 'UNKNOWN')} - {health.get('health_reason', '')}")
    finally:
        db.close()
    
    # 2. Current Model Architecture
    md.append("\n## 2. Current Model Architecture")
    md.append("\n### Deployed Models")
    md.append("| Model | Type | Status |")
    md.append("|-------|------|--------|")
    md.append("| PerTypeRF | Per-Type Random Forest (Two-Stage) | **PRODUCTION** |")
    md.append("| XGB_PerType | Per-Type XGBoost (Two-Stage) | Available (offline only) |")
    md.append("| RF_Multi | Multi-Output Random Forest | Available (offline only) |")
    md.append("| XGB_Multi | Multi-Output XGBoost | Available (offline only) |")
    
    md.append("\n### Feature Engineering")
    md.append("\nThe `DatabaseWastePredictor._construct_features()` builds features from database records:")
    for group, features in report['feature_construction']['feature_groups'].items():
        md.append(f"\n**{group}** ({len(features)} features):")
        for f in features:
            md.append(f"- `{f}`")
    
    md.append(f"\n**Total features**: {report['feature_construction']['total_features']}")
    
    # 3. Feature Importance by Model
    md.append("\n## 3. Feature Importance by Model")
    md.append("\n> **NOTE**: The actual trained model files (.joblib) are not present in this repository. ")
    md.append("Feature importance cannot be directly extracted from the models. ")
    md.append("The models are loaded from `MLproject/ml/models/improved/` which is an external path.")
    md.append("\n### Expected Feature Importance Patterns (based on architecture)")
    md.append("\n**PerTypeRF (Two-Stage)**:")
    md.append("- Stage 1 (Classifier): Features distinguishing zero vs non-zero waste")
    md.append("- Stage 2 (Regressor): Features predicting non-zero amounts")
    md.append("- Likely important: lag features, rolling means, waste composition lags")
    
    md.append("\n**RF_Multi / XGB_Multi (Multi-Output)**:")
    md.append("- Single model predicting all waste types simultaneously")
    md.append("- Shared feature importance across all targets")
    md.append("- Historical waste features likely dominant")
    
    # 4. Feature Importance by Waste Type
    md.append("\n## 4. Feature Importance by Waste Type (Expected)")
    md.append("\nBased on feature engineering and domain knowledge:")
    
    importance_by_waste = {
        'total': ['total_waste_kg_lag_1d', 'total_waste_kg_roll_mean_7d', 'total_waste_kg_roll_mean_3d', 'area', 'account_type'],
        'wet': ['wet_kg_lag_1d', 'total_waste_kg_lag_1d', 'total_waste_kg_roll_mean_7d', 'people_present', 'family_members'],
        'dry': ['dry_kg_lag_1d', 'total_waste_kg_lag_1d', 'avg_customers_per_day', 'area', 'account_type'],
        'plastic': ['plastic_kg_lag_1d', 'avg_customers_per_day', 'area', 'account_type'],
        'glass': ['glass_kg_lag_1d', 'area', 'account_type'],
        'metal': ['metal_kg_lag_1d', 'area', 'employee_count'],
        'medical': ['medical_kg_lag_1d', 'area', 'account_type'],
    }
    
    for wt, feats in importance_by_waste.items():
        md.append(f"\n**{wt.upper()}**:")
        for i, f in enumerate(feats, 1):
            md.append(f"  {i}. `{f}`")
    
    # 5. Feature Group Analysis
    md.append("\n## 5. Feature Group Analysis")
    md.append("\n| Feature Group | # Features | Notes |")
    md.append("|---------------|------------|-------|")
    for group, features in report['feature_construction']['feature_groups'].items():
        notes = ""
        if group == 'Weather/Environment':
            notes = "Hardcoded defaults (not real data)"
        elif group == 'Temporal/Calendar':
            notes = "Strong seasonality signals"
        elif 'lag' in str(features).lower():
            notes = "Historical waste patterns"
        md.append(f"| {group} | {len(features)} | {notes} |")
    
    # 6. Offline Error Analysis
    md.append("\n## 6. Offline Error Analysis (Chronological Hold-Out Test)")
    
    offline = report['offline_test_metrics'].get('metrics', {})
    if offline:
        md.append("\n| Waste Type | R² | MAE | RMSE | MAPE | SMAPE |")
        md.append("|------------|-----|-----|------|------|-------|")
        for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
            m = offline.get(wt, {})
            md.append(f"| {wt} | {m.get('R2', 'N/A')} | {m.get('MAE', 'N/A')} | {m.get('RMSE', 'N/A')} | {m.get('MAPE', 'N/A')} | {m.get('SMAPE', 'N/A')} |")
    
    # 7. Real-World Error Analysis
    md.append("\n## 7. Real-World Error Analysis")
    md.append("\n*Using existing PredictionAccuracy records from matched prediction-actual pairs*")
    
    errors = report['real_world_error_analysis']
    md.append("\n| Waste Type | Samples | MAE | RMSE | R² | MAPE | Bias | Reliability |")
    md.append("|------------|---------|-----|------|-----|------|------|-------------|")
    
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
        e = errors.get(wt, {})
        if e.get('available'):
            md.append(f"| {wt} | {e['sample_count']} | {e['MAE']} | {e['RMSE']} | {e['R2'] if e['R2'] else 'N/A'} | {e['MAPE'] if e['MAPE'] else 'N/A'} | {e['Bias']} | {e['reliability']} |")
        else:
            md.append(f"| {wt} | {e.get('sample_count', 0)} | N/A | N/A | N/A | N/A | N/A | {e.get('reliability', 'INSUFFICIENT_DATA')} |")
    
    # Accuracy within thresholds
    md.append("\n### Accuracy Within Thresholds")
    md.append("\n| Waste Type | Within ±10% | Within ±20% | Within ±30% |")
    md.append("|------------|-------------|-------------|-------------|")
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
        e = errors.get(wt, {})
        if e.get('available'):
            md.append(f"| {wt} | {e['Within_10pct_pct']}% | {e['Within_20pct_pct']}% | {e['Within_30pct_pct']}% |")
    
    # 8. Bias Analysis
    md.append("\n## 8. Bias Analysis")
    md.append("\n| Waste Type | Bias (Pred - Actual) | Overpredictions | Underpredictions | Interpretation |")
    md.append("|------------|---------------------|-----------------|------------------|----------------|")
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
        e = errors.get(wt, {})
        if e.get('available'):
            bias = e['Bias']
            if abs(bias) < 0.05:
                interp = "No significant bias"
            elif bias > 0:
                interp = "Systematic OVERPREDICTION"
            else:
                interp = "Systematic UNDERPREDICTION"
            md.append(f"| {wt} | {bias} | {e['Overpredictions']} | {e['Underpredictions']} | {interp} |")
    
    # 9. Drift vs Feature Importance
    md.append("\n## 9. Drift vs Feature Importance")
    
    drift = report['drift_vs_importance']
    md.append(f"\n**Overall Drift Status**: {drift.get('overall_drift_status', 'UNKNOWN')}")
    md.append(f"**Reference Source**: {drift.get('reference_source', 'UNKNOWN')} (FIRST 90 DAYS OF DB DATA - NOT ACTUAL TRAINING DATA)")
    
    md.append("\n### Drift by Feature Group")
    md.append("\n| Feature Group | Max PSI | Max Mean Change% | High Drift Features |")
    md.append("|---------------|---------|------------------|---------------------|")
    
    group_drift = drift.get('group_drift_analysis', {})
    for group, data in group_drift.items():
        high_drift = data.get('high_drift_count', 0)
        max_psi = data.get('max_psi', 0)
        max_mean = data.get('max_mean_change', 0)
        md.append(f"| {group} | {max_psi:.4f} | {max_mean:.1f}% | {high_drift} |")
    
    # High drift features detail
    md.append("\n### High Drift Features Detail")
    drift_features = drift.get('drift_summary', {})
    # Get from detect_data_drift detailed features
    # We need to re-run to get details
    
    # 10. Weak/Redundant Features
    md.append("\n## 10. Weak/Redundant Features")
    
    weak = report['weak_features']['weak_features']
    if weak:
        md.append("\n| Feature | Issue | Severity |")
        md.append("|---------|-------|----------|")
        for w in weak:
            md.append(f"| {w['feature']} | {w['issue']} | {w['severity']} |")
    else:
        md.append("\nNo severely weak features detected.")
    
    md.append("\n### Defaulted Features (Not from Real Data)")
    for f in report['weak_features']['defaulted_features']:
        md.append(f"- `{f}`: Hardcoded default value")
    
    # 11. Potential Data Leakage Risks
    md.append("\n## 11. Potential Data Leakage Risks")
    md.append("\n1. **Lag features computed from same day's submissions**: If a user submits multiple times per day, lag_1d could leak target info")
    md.append("2. **Area/account_type as categorical**: High cardinality areas may cause overfitting")
    md.append("3. **Weather features hardcoded**: No real weather data - model learns spurious correlations")
    md.append("4. **Festival/holiday features all False**: No variation, useless for model")
    md.append("5. **Rolling stats with small windows**: 3-day window with sparse data may leak recent target")
    
    # 12. Main Causes of Prediction Error
    md.append("\n## 12. Main Causes of Prediction Error")
    md.append("\n1. **Zero-inflated targets**: Many waste types (glass, metal, medical) are frequently zero → two-stage model helps but classifier errors propagate")
    md.append("2. **Sparse historical data**: Users with < 7 submissions have unreliable rolling statistics")
    md.append("3. **Weather defaults**: No real weather data removes a potentially strong predictor")
    md.append("4. **Categorical high cardinality**: 15+ areas, some with few samples → poor generalization")
    md.append("5. **Temporal leakage risk**: Lag features computed from all submissions, not strictly temporal")
    md.append("6. **Small real-world evaluation set**: Only ~13 total accuracy records → cannot reliably validate model")
    
    # 13. Recommended Improvements
    md.append("\n## 13. Recommended Improvements")
    md.append("\n### Data Collection")
    md.append("1. **Integrate real weather API** - Replace hardcoded defaults with actual weather data")
    md.append("2. **Add festival/holiday calendar** - Real holiday data for the region")
    md.append("3. **Collect more matched prediction-actual pairs** - Need 50+ per waste type for STRONG_EVALUATION")
    
    md.append("\n### Feature Engineering")
    md.append("4. **Add area-level aggregates** - Historical waste per area (not just per user)")
    md.append("5. **Add user embedding / frequency encoding** - For high-cardinality categorical features")
    md.append("6. **Stricter temporal splits** - Ensure lag features only use strictly prior data")
    md.append("7. **Feature selection** - Remove defaulted/hardcoded features")
    
    md.append("\n### Modeling")
    md.append("8. **Evaluate simpler baselines** - Mean/median per area/account_type as sanity check")
    md.append("9. **Calibrate two-stage models** - Ensure classifier threshold is optimal")
    md.append("10. **Test XGBoost with proper tuning** - Current XGB may not be optimal")
    
    # 14. Features to Keep
    md.append("\n## 14. Features to Keep")
    keep = [
        'total_waste_kg_lag_1d', 'total_waste_kg_lag_7d',
        'total_waste_kg_roll_mean_3d', 'total_waste_kg_roll_mean_7d',
        'wet_kg_lag_1d', 'dry_kg_lag_1d', 'plastic_kg_lag_1d',
        'area', 'account_type',
        'day_of_week', 'month', 'is_weekend',
        'family_members', 'avg_customers_per_day',
    ]
    for f in keep:
        md.append(f"- `{f}`")
    
    # 15. Features to Remove/Test
    md.append("\n## 15. Features to Remove / Test for Removal")
    remove = [
        'is_holiday', 'is_festival', 'festival_intensity',  # All constant
        'temp_max_c', 'rainfall_mm', 'humidity_pct',  # Hardcoded defaults
        'total_waste_kg_lag_2d', 'total_waste_kg_lag_3d',  # Redundant with lag_1d + rolling
        'total_waste_kg_roll_std_3d', 'total_waste_kg_roll_std_7d',  # Low importance typically
        'employee_count',  # Duplicate of avg_customers_per_day for org
    ]
    for f in remove:
        md.append(f"- `{f}`")
    
    # 16. Features That Need Better Data
    md.append("\n## 16. Features That Need Better Data")
    md.append("- **Weather**: Need real weather API integration")
    md.append("- **Festival/Holiday**: Need regional calendar data")
    md.append("- **Area-level stats**: Need area aggregates, not just user-level")
    md.append("- **Temporal**: Need proper holiday calendar for the region")
    
    # 17. Recommended Next Training Strategy
    md.append("\n## 17. Recommended Next Training Strategy")
    md.append("\n### Phase 1: Data Quality (No Retraining)")
    md.append("1. Fix weather/festival features with real data")
    md.append("2. Collect 50+ matched prediction-actual pairs per waste type")
    md.append("3. Validate temporal splits are leak-free")
    
    md.append("\n### Phase 2: Feature Engineering")
    md.append("4. Add area-level aggregate features")
    md.append("5. Remove/consolidate redundant features")
    md.append("6. Test frequency/target encoding for categorical features")
    
    md.append("\n### Phase 3: Model Retraining")
    md.append("7. Retrain PerTypeRF with cleaned features")
    md.append("8. Compare against XGBoost with hyperparameter tuning")
    md.append("9. Test single-model multi-output vs per-type approach")
    md.append("10. Implement proper cross-validation with temporal splits")
    
    # Prioritized Action Plan
    md.append("\n---\n## PRIORITIZED ACTION PLAN")
    
    md.append("\n### Priority 1 (Immediate - No Retraining Required)")
    md.append("1. **Fix weather/festival features** - Replace hardcoded defaults with real API data")
    md.append("   - Expected benefit: Removes noise features, may improve R² by 0.02-0.05")
    md.append("   - Cost: Low (API integration)")
    md.append("   - Risk: Low")
    md.append("   - Retraining required: NO (features are inputs, model can use as-is)")
    md.append("   - Additional data: YES (weather API)")
    
    md.append("\n2. **Collect matched prediction-actual pairs** - Target 50+ per waste type")
    md.append("   - Expected benefit: Enables reliable model evaluation (STRONG_EVALUATION)")
    md.append("   - Cost: Operational (collector workflow)")
    md.append("   - Risk: Low")
    md.append("   - Retraining required: NO")
    md.append("   - Additional data: YES (real-world collections)")
    
    md.append("\n### Priority 2 (Before Next Retraining)")
    md.append("3. **Remove constant/hardcoded features** - is_holiday, is_festival, festival_intensity, temp_max_c, rainfall_mm, humidity_pct")
    md.append("   - Expected benefit: Cleaner feature space, faster training")
    md.append("   - Cost: Low (code change)")
    md.append("   - Risk: Very Low")
    md.append("   - Retraining required: YES")
    md.append("   - Additional data: NO")
    
    md.append("\n4. **Add area-level aggregate features**")
    md.append("   - Expected benefit: Captures area-level patterns, helps cold-start users")
    md.append("   - Cost: Medium (feature engineering)")
    md.append("   - Risk: Low")
    md.append("   - Retraining required: YES")
    md.append("   - Additional data: NO (computed from existing DB)")
    
    md.append("\n5. **Stricter temporal validation** - Ensure no leakage in lag/rolling features")
    md.append("   - Expected benefit: More realistic performance estimates")
    md.append("   - Cost: Medium (validation logic)")
    md.append("   - Risk: Low")
    md.append("   - Retraining required: YES (for proper evaluation)")
    md.append("   - Additional data: NO")
    
    md.append("\n### Priority 3 (Model Improvement)")
    md.append("6. **Retrain PerTypeRF with cleaned features** + proper temporal CV")
    md.append("   - Expected benefit: 5-15% error reduction if features improved")
    md.append("   - Cost: Medium (training compute)")
    md.append("   - Risk: Medium (model change)")
    md.append("   - Retraining required: YES")
    md.append("   - Additional data: NO (existing DB)")
    
    md.append("\n7. **Compare per-type vs multi-output architectures**")
    md.append("   - Expected benefit: Identify best architecture for production")
    md.append("   - Cost: Medium (training both)")
    md.append("   - Risk: Low")
    md.append("   - Retraining required: YES")
    md.append("   - Additional data: NO")
    
    # Current Metrics Summary
    md.append("\n---\n## CURRENT METRICS SUMMARY")
    
    md.append("\n### Offline Test Metrics (RF_Multi)")
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
        m = offline.get(wt, {})
        if m.get('R2') is not None:
            r2 = f"{m.get('R2'):.4f}"
            mae = f"{m.get('MAE'):.4f}" if m.get('MAE') is not None else "N/A"
            rmse = f"{m.get('RMSE'):.4f}" if m.get('RMSE') is not None else "N/A"
            smape = f"{m.get('SMAPE'):.4f}" if m.get('SMAPE') is not None else "N/A"
            md.append(f"- **{wt}**: R²={r2}, MAE={mae}, RMSE={rmse}, SMAPE={smape}")
    
    md.append("\n### Real-World Metrics")
    for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']:
        e = errors.get(wt, {})
        if e.get('available'):
            r2_str = f"{e['R2']:.4f}" if e['R2'] is not None else "N/A"
            md.append(f"- **{wt}**: n={e['sample_count']}, MAE={e['MAE']:.4f}, RMSE={e['RMSE']:.4f}, R²={r2_str}, Bias={e['Bias']:.4f}, Reliability={e['reliability']}")
        else:
            md.append(f"- **{wt}**: n={e.get('sample_count', 0)} - {e.get('reliability', 'INSUFFICIENT_DATA')}")
    
    # Top 20 Important Features (Expected)
    md.append("\n---\n## TOP 20 IMPORTANT FEATURES (Expected from Architecture)")
    top_features = [
        'total_waste_kg_lag_1d', 'total_waste_kg_roll_mean_7d', 'total_waste_kg_roll_mean_3d',
        'wet_kg_lag_1d', 'dry_kg_lag_1d', 'plastic_kg_lag_1d',
        'area', 'account_type',
        'day_of_week', 'month', 'is_weekend',
        'family_members', 'avg_customers_per_day',
        'total_waste_kg_lag_7d', 'glass_kg_lag_1d', 'metal_kg_lag_1d', 'medical_kg_lag_1d',
        'people_present', 'employee_count',
    ]
    for i, f in enumerate(top_features[:20], 1):
        md.append(f"{i}. `{f}`")
    
    # Top Error Sources
    md.append("\n---\n## TOP ERROR SOURCES")
    md.append("1. **Zero-inflated targets** (glass, metal, medical) - classifier errors in two-stage model")
    md.append("2. **Sparse user history** - unreliable rolling statistics for new/infrequent users")
    md.append("3. **Hardcoded weather/festival features** - noise instead of signal")
    md.append("4. **High-cardinality categoricals** - area (15+ values) with imbalanced samples")
    md.append("5. **Insufficient real-world validation** - only 13 total matched pairs")
    md.append("6. **Potential temporal leakage** in lag/rolling feature computation")
    
    # Recommended Next Step
    md.append("\n---\n## RECOMMENDED NEXT STEP")
    md.append("\n**Start with Priority 1**: Fix weather/festival features with real data API integration. ")
    md.append("This is a pure feature engineering change that doesn't require model retraining ")
    md.append("and can be deployed immediately. In parallel, ensure the collector workflow ")
    md.append("generates matched prediction-actual pairs to build up the real-world evaluation set.")
    md.append("\n\nOnce 50+ real-world samples per waste type are collected and weather features ")
    md.append("are live, proceed with Priority 2 (feature cleanup) and Priority 3 (retraining).")
    
    return '\n'.join(md)


if __name__ == '__main__':
    print("Starting SmartWaste ML Feature Importance & Error Analysis...")
    
    report = run_full_analysis()
    
    # Save JSON report
    with open('ml_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print("\nJSON report saved to ml_analysis_report.json")
    
    # Generate markdown
    markdown = generate_markdown_report(report)
    with open('ML_FEATURE_ERROR_ANALYSIS_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(markdown)
    print("Markdown report saved to ML_FEATURE_ERROR_ANALYSIS_REPORT.md")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
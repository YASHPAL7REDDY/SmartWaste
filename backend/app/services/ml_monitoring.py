from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import numpy as np
import math
import json
import uuid
from pathlib import Path
from scipy import stats
from collections import Counter

from app.models.waste import WasteSubmission, WasteItem
from app.models.prediction import (
    PredictionAccuracy, AreaPrediction, ActualCollection, TrainingReferenceStats
)
from app.models.user import User
from app.services.collector import get_reliability_level
from app.schemas.prediction import TrainingReferenceStatsResponse

WASTE_TYPES = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
NUMERICAL_WASTE_TYPES = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical', 'total']
CATEGORICAL_FEATURES = ['area', 'account_type']

# Minimum samples for reliable statistical tests
MIN_SAMPLES_NUMERICAL_DRIFT = 30
MIN_SAMPLES_CATEGORICAL_DRIFT = 50
MIN_SAMPLES_PERFORMANCE = 10
MIN_SAMPLES_CATEGORICAL_PER_CELL = 5  # For chi-square test

DRIFT_THRESHOLDS = {
    'psi': {
        'no_drift': 0.1,
        'moderate': 0.25,
        'high': 0.25
    },
    'mean_change_pct': {
        'no_drift': 10,
        'moderate': 25,
        'high': 25
    },
    'std_change_pct': {
        'no_drift': 20,
        'moderate': 50,
        'high': 50
    },
    'ks_test_pvalue': {
        'no_drift': 0.05,
        'moderate': 0.01,
        'high': 0.01
    },
    'chi2_pvalue': {
        'no_drift': 0.05,
        'moderate': 0.01,
        'high': 0.01
    }
}

PERFORMANCE_DEGRADATION_THRESHOLDS = {
    'mae_increase_pct': {'warning': 15, 'critical': 30},
    'rmse_increase_pct': {'warning': 15, 'critical': 30},
    'r2_decrease_pct': {'warning': 10, 'critical': 25},
    'smape_increase_pct': {'warning': 15, 'critical': 30},
}


def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between two distributions."""
    if len(expected) < 2 or len(actual) < 2:
        return float('nan')
    
    try:
        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())
        
        if min_val == max_val:
            return 0.0
        
        bin_edges = np.linspace(min_val, max_val, bins + 1)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf
        
        expected_hist, _ = np.histogram(expected, bins=bin_edges)
        actual_hist, _ = np.histogram(actual, bins=bin_edges)
        
        expected_perc = expected_hist / len(expected)
        actual_perc = actual_hist / len(actual)
        
        expected_perc = np.where(expected_perc == 0, 0.0001, expected_perc)
        actual_perc = np.where(actual_perc == 0, 0.0001, actual_perc)
        
        psi = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))
        return float(psi)
    except Exception:
        return float('nan')


def calculate_smape(predicted: List[float], actual: List[float]) -> Optional[float]:
    """Calculate Symmetric Mean Absolute Percentage Error (SMAPE) - better for zero-heavy data."""
    if not predicted or not actual or len(predicted) != len(actual):
        return None
    
    n = len(predicted)
    smape_values = []
    for p, a in zip(predicted, actual):
        denom = (abs(p) + abs(a)) / 2
        if denom == 0:
            smape_values.append(0.0)
        else:
            smape_values.append(abs(p - a) / denom)
    
    return np.mean(smape_values) * 100 if smape_values else None


def classify_numerical_drift(
    psi: float, 
    mean_change_pct: float, 
    std_change_pct: float, 
    ks_pvalue: float,
    ref_samples: int,
    recent_samples: int
) -> Tuple[str, Dict]:
    """Classify numerical drift level with detailed reasoning."""
    if ref_samples < MIN_SAMPLES_NUMERICAL_DRIFT or recent_samples < MIN_SAMPLES_NUMERICAL_DRIFT:
        return ("INSUFFICIENT_DATA", {
            "reason": f"Insufficient samples (ref={ref_samples}, recent={recent_samples} < {MIN_SAMPLES_NUMERICAL_DRIFT})"
        })
    
    if np.isnan(psi) and np.isnan(mean_change_pct) and np.isnan(std_change_pct) and np.isnan(ks_pvalue):
        return ("INSUFFICIENT_DATA", {"reason": "All drift metrics are NaN"})
    
    high_count = 0
    moderate_count = 0
    details = []
    
    if not np.isnan(psi):
        if psi >= DRIFT_THRESHOLDS['psi']['high']:
            high_count += 1
            details.append(f"PSI={psi:.4f} >= HIGH({DRIFT_THRESHOLDS['psi']['high']})")
        elif psi >= DRIFT_THRESHOLDS['psi']['no_drift']:
            moderate_count += 1
            details.append(f"PSI={psi:.4f} >= MODERATE({DRIFT_THRESHOLDS['psi']['no_drift']})")
        else:
            details.append(f"PSI={psi:.4f} < NO_DRIFT({DRIFT_THRESHOLDS['psi']['no_drift']})")
    
    if not np.isnan(mean_change_pct):
        if mean_change_pct >= DRIFT_THRESHOLDS['mean_change_pct']['high']:
            high_count += 1
            details.append(f"Mean change={mean_change_pct:.1f}% >= HIGH({DRIFT_THRESHOLDS['mean_change_pct']['high']}%)")
        elif mean_change_pct >= DRIFT_THRESHOLDS['mean_change_pct']['no_drift']:
            moderate_count += 1
            details.append(f"Mean change={mean_change_pct:.1f}% >= MODERATE({DRIFT_THRESHOLDS['mean_change_pct']['no_drift']}%)")
        else:
            details.append(f"Mean change={mean_change_pct:.1f}% < NO_DRIFT({DRIFT_THRESHOLDS['mean_change_pct']['no_drift']}%)")
    
    if not np.isnan(std_change_pct):
        if std_change_pct >= DRIFT_THRESHOLDS['std_change_pct']['high']:
            high_count += 1
            details.append(f"Std change={std_change_pct:.1f}% >= HIGH({DRIFT_THRESHOLDS['std_change_pct']['high']}%)")
        elif std_change_pct >= DRIFT_THRESHOLDS['std_change_pct']['no_drift']:
            moderate_count += 1
            details.append(f"Std change={std_change_pct:.1f}% >= MODERATE({DRIFT_THRESHOLDS['std_change_pct']['no_drift']}%)")
        else:
            details.append(f"Std change={std_change_pct:.1f}% < NO_DRIFT({DRIFT_THRESHOLDS['std_change_pct']['no_drift']}%)")
    
    if not np.isnan(ks_pvalue):
        if ks_pvalue <= DRIFT_THRESHOLDS['ks_test_pvalue']['high']:
            high_count += 1
            details.append(f"KS p-value={ks_pvalue:.4f} <= HIGH({DRIFT_THRESHOLDS['ks_test_pvalue']['high']})")
        elif ks_pvalue <= DRIFT_THRESHOLDS['ks_test_pvalue']['no_drift']:
            moderate_count += 1
            details.append(f"KS p-value={ks_pvalue:.4f} <= MODERATE({DRIFT_THRESHOLDS['ks_test_pvalue']['no_drift']})")
        else:
            details.append(f"KS p-value={ks_pvalue:.4f} > NO_DRIFT({DRIFT_THRESHOLDS['ks_test_pvalue']['no_drift']})")
    
    if high_count >= 2:
        return ("HIGH_DRIFT", {"high_signals": high_count, "moderate_signals": moderate_count, "details": details})
    elif high_count >= 1 or moderate_count >= 2:
        return ("MODERATE_DRIFT", {"high_signals": high_count, "moderate_signals": moderate_count, "details": details})
    elif moderate_count >= 1:
        return ("MODERATE_DRIFT", {"high_signals": high_count, "moderate_signals": moderate_count, "details": details})
    else:
        return ("NO_DRIFT", {"high_signals": 0, "moderate_signals": moderate_count, "details": details})


def calculate_categorical_drift(
    reference_counts: Dict[str, int], 
    recent_counts: Dict[str, int]
) -> Tuple[str, Dict]:
    """Calculate categorical drift using Chi-square test."""
    # Align categories
    all_categories = set(reference_counts.keys()) | set(recent_counts.keys())
    
    ref_aligned = [reference_counts.get(cat, 0) for cat in all_categories]
    rec_aligned = [recent_counts.get(cat, 0) for cat in all_categories]
    
    ref_total = sum(ref_aligned)
    rec_total = sum(rec_aligned)
    
    if ref_total == 0 or rec_total == 0:
        return ("INSUFFICIENT_DATA", {
            "reason": f"Zero total counts (ref={ref_total}, recent={rec_total})"
        })
    
    # Check expected cell counts for chi-square validity
    expected_counts = [(ref + rec) * ref_total / (ref_total + rec_total) for ref, rec in zip(ref_aligned, rec_aligned)]
    min_expected = min(expected_counts) if expected_counts else 0
    
    if min_expected < MIN_SAMPLES_CATEGORICAL_PER_CELL:
        return ("INSUFFICIENT_DATA", {
            "reason": f"Expected cell count too low for chi-square test (min={min_expected:.1f} < {MIN_SAMPLES_CATEGORICAL_PER_CELL})"
        })
    
    if len(all_categories) < 2:
        return ("INSUFFICIENT_DATA", {"reason": "Less than 2 categories"})
    
    try:
        # Chi-square test of independence
        chi2_stat, chi2_pvalue = stats.chisquare(f_obs=rec_aligned, f_exp=ref_aligned)
        
        # Also calculate Cramér's V for effect size
        n = ref_total + rec_total
        min_dim = min(len(all_categories) - 1, 1)
        cramers_v = math.sqrt(chi2_stat / (n * min_dim)) if n > 0 and min_dim > 0 else 0
        
        if chi2_pvalue <= DRIFT_THRESHOLDS['chi2_pvalue']['high']:
            status = "HIGH_DRIFT"
        elif chi2_pvalue <= DRIFT_THRESHOLDS['chi2_pvalue']['no_drift']:
            status = "MODERATE_DRIFT"
        else:
            status = "NO_DRIFT"
        
        return (status, {
            "chi2_statistic": round(chi2_stat, 4),
            "chi2_pvalue": round(chi2_pvalue, 6),
            "cramers_v": round(cramers_v, 4),
            "categories": list(all_categories),
            "reference_counts": ref_aligned,
            "recent_counts": rec_aligned,
            "reference_proportions": [round(c/ref_total, 4) for c in ref_aligned],
            "recent_proportions": [round(c/rec_total, 4) for c in rec_aligned],
            "min_expected_count": round(min_expected, 2)
        })
    except Exception as e:
        return ("ERROR", {"reason": f"Chi-square test failed: {str(e)}"})


def load_training_reference_stats(db: Session) -> Dict[str, Any]:
    """Load training reference statistics from database."""
    stats_records = db.query(TrainingReferenceStats).all()
    
    result = {
        'numerical': {},
        'categorical': {},
        'metadata': {
            'source': 'unknown',
            'model_version': None,
            'features_count': 0
        }
    }
    
    if not stats_records:
        return result
    
    sources = set()
    model_versions = set()
    for record in stats_records:
        sources.add(record.source)
        if record.model_version:
            model_versions.add(record.model_version)
        
        if record.feature_type == 'numerical':
            result['numerical'][record.feature_name] = {
                'mean': record.mean,
                'std': record.std,
                'min': record.min_val,
                'max': record.max_val,
                'median': record.median,
                'q25': record.q25,
                'q75': record.q75,
                'sample_count': record.sample_count,
            }
        elif record.feature_type == 'categorical':
            try:
                cat_counts = json.loads(record.category_counts) if record.category_counts else {}
                cat_props = json.loads(record.category_proportions) if record.category_proportions else {}
            except json.JSONDecodeError:
                cat_counts = {}
                cat_props = {}
            
            result['categorical'][record.feature_name] = {
                'counts': cat_counts,
                'proportions': cat_props,
                'sample_count': record.sample_count,
            }
    
    result['metadata']['source'] = list(sources)[0] if len(sources) == 1 else 'mixed'
    result['metadata']['model_version'] = list(model_versions)[0] if len(model_versions) == 1 else 'mixed'
    result['metadata']['features_count'] = len(stats_records)
    
    return result


def compute_training_reference_from_database(db: Session, model_version: str = "PerTypeRF") -> Dict[str, Any]:
    """Compute reference statistics from earliest database history as a proxy.
    This is NOT the actual training data - it's a proxy that should be clearly labeled.
    """
    earliest_date = db.query(func.min(WasteSubmission.submission_date)).scalar()
    if not earliest_date:
        return {}
    
    # Use first 90 days as proxy for training period
    reference_end = earliest_date + timedelta(days=90)
    
    submissions = db.query(WasteSubmission).filter(
        WasteSubmission.submission_date >= earliest_date,
        WasteSubmission.submission_date < reference_end
    ).all()
    
    if not submissions:
        return {}
    
    # Numerical features
    waste_type_data = {wt: [] for wt in NUMERICAL_WASTE_TYPES}
    area_counts = Counter()
    account_type_counts = Counter()
    
    for s in submissions:
        items = db.query(WasteItem).filter(WasteItem.submission_id == s.id).all()
        breakdown = {item.waste_type.lower(): item.quantity_kg for item in items}
        
        for wt in NUMERICAL_WASTE_TYPES:
            if wt == 'total':
                waste_type_data[wt].append(s.total_waste_kg)
            else:
                waste_type_data[wt].append(breakdown.get(wt, 0.0))
        
        if s.area_snapshot:
            area_counts[s.area_snapshot] += 1
        if s.account_type_snapshot:
            account_type_counts[s.account_type_snapshot] += 1
    
    numerical_stats = {}
    for wt in NUMERICAL_WASTE_TYPES:
        values = waste_type_data[wt]
        if values:
            arr = np.array(values)
            numerical_stats[wt] = {
                'mean': float(np.mean(arr)),
                'std': float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
                'min': float(np.min(arr)),
                'max': float(np.max(arr)),
                'median': float(np.median(arr)),
                'q25': float(np.percentile(arr, 25)),
                'q75': float(np.percentile(arr, 75)),
                'sample_count': len(arr),
            }
    
    categorical_stats = {
        'area': {
            'counts': dict(area_counts),
            'proportions': {k: v/sum(area_counts.values()) for k, v in area_counts.items()} if area_counts else {},
            'sample_count': sum(area_counts.values()),
        },
        'account_type': {
            'counts': dict(account_type_counts),
            'proportions': {k: v/sum(account_type_counts.values()) for k, v in account_type_counts.items()} if account_type_counts else {},
            'sample_count': sum(account_type_counts.values()),
        }
    }
    
    return {
        'numerical': numerical_stats,
        'categorical': categorical_stats,
        'metadata': {
            'source': 'database_history_proxy',
            'model_version': model_version,
            'features_count': len(numerical_stats) + len(categorical_stats),
            'reference_period_start': earliest_date.isoformat(),
            'reference_period_end': reference_end.isoformat(),
            'note': 'COMPUTED FROM DATABASE HISTORY (first 90 days) - NOT ACTUAL TRAINING DATA'
        }
    }


def persist_training_reference_stats(db: Session, stats: Dict[str, Any], model_version: str = "PerTypeRF") -> int:
    """Persist training reference statistics to database."""
    # Clear existing records for this model version
    db.query(TrainingReferenceStats).filter(
        TrainingReferenceStats.model_version == model_version
    ).delete()
    
    count = 0
    now = datetime.utcnow()
    
    # Numerical features
    for feature_name, values in stats.get('numerical', {}).items():
        record = TrainingReferenceStats(
            id=str(uuid.uuid4()),
            feature_name=feature_name,
            feature_type='numerical',
            mean=values.get('mean'),
            std=values.get('std'),
            min_val=values.get('min'),
            max_val=values.get('max'),
            median=values.get('median'),
            q25=values.get('q25'),
            q75=values.get('q75'),
            sample_count=values.get('sample_count'),
            source=stats.get('metadata', {}).get('source', 'unknown'),
            training_period_start=date.fromisoformat(stats['metadata']['reference_period_start']) if stats['metadata'].get('reference_period_start') else None,
            training_period_end=date.fromisoformat(stats['metadata']['reference_period_end']) if stats['metadata'].get('reference_period_end') else None,
            model_version=model_version,
            notes=stats.get('metadata', {}).get('note'),
            created_at=now,
            updated_at=now,
        )
        db.add(record)
        count += 1
    
    # Categorical features
    for feature_name, values in stats.get('categorical', {}).items():
        record = TrainingReferenceStats(
            id=str(uuid.uuid4()),
            feature_name=feature_name,
            feature_type='categorical',
            category_counts=json.dumps(values.get('counts', {})),
            category_proportions=json.dumps(values.get('proportions', {})),
            sample_count=values.get('sample_count'),
            source=stats.get('metadata', {}).get('source', 'unknown'),
            training_period_start=date.fromisoformat(stats['metadata']['reference_period_start']) if stats['metadata'].get('reference_period_start') else None,
            training_period_end=date.fromisoformat(stats['metadata']['reference_period_end']) if stats['metadata'].get('reference_period_end') else None,
            model_version=model_version,
            notes=stats.get('metadata', {}).get('note'),
            created_at=now,
            updated_at=now,
        )
        db.add(record)
        count += 1
    
    db.commit()
    return count


def ensure_training_reference_stats(db: Session, model_version: str = "PerTypeRF") -> Dict[str, Any]:
    """Ensure training reference stats exist, compute from database if needed."""
    existing = load_training_reference_stats(db)
    
    if existing['metadata']['features_count'] == 0:
        # No stats exist, compute from database as proxy
        computed = compute_training_reference_from_database(db, model_version)
        if computed:
            persist_training_reference_stats(db, computed, model_version)
            return load_training_reference_stats(db)
        return {'numerical': {}, 'categorical': {}, 'metadata': {'source': 'unavailable'}}
    
    return existing


def get_recent_submission_stats(db: Session, days: int = 30) -> Dict[str, Any]:
    """Calculate statistics from recent waste submissions."""
    cutoff = date.today() - timedelta(days=days)
    
    submissions = db.query(WasteSubmission).filter(
        WasteSubmission.submission_date >= cutoff
    ).all()
    
    if not submissions:
        return {}
    
    waste_type_data = {wt: [] for wt in NUMERICAL_WASTE_TYPES}
    area_counts = Counter()
    account_type_counts = Counter()
    
    for s in submissions:
        items = db.query(WasteItem).filter(WasteItem.submission_id == s.id).all()
        breakdown = {item.waste_type.lower(): item.quantity_kg for item in items}
        
        for wt in NUMERICAL_WASTE_TYPES:
            if wt == 'total':
                waste_type_data[wt].append(s.total_waste_kg)
            else:
                waste_type_data[wt].append(breakdown.get(wt, 0.0))
        
        if s.area_snapshot:
            area_counts[s.area_snapshot] += 1
        if s.account_type_snapshot:
            account_type_counts[s.account_type_snapshot] += 1
    
    stats = {}
    for wt in NUMERICAL_WASTE_TYPES:
        values = waste_type_data[wt]
        if values:
            arr = np.array(values)
            stats[wt] = {
                'mean': float(np.mean(arr)),
                'std': float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
                'min': float(np.min(arr)),
                'max': float(np.max(arr)),
                'median': float(np.median(arr)),
                'q25': float(np.percentile(arr, 25)),
                'q75': float(np.percentile(arr, 75)),
                'count': len(values),
                'values': values
            }
    
    stats['area_distribution'] = {
        'counts': dict(area_counts),
        'proportions': {k: v/sum(area_counts.values()) for k, v in area_counts.items()} if area_counts else {},
        'sample_count': sum(area_counts.values()),
    }
    
    stats['account_type_distribution'] = {
        'counts': dict(account_type_counts),
        'proportions': {k: v/sum(account_type_counts.values()) for k, v in account_type_counts.items()} if account_type_counts else {},
        'sample_count': sum(account_type_counts.values()),
    }
    
    return stats


def detect_data_drift(db: Session, reference_days: int = 90, recent_days: int = 30, model_version: str = "PerTypeRF") -> Dict[str, Any]:
    """Detect data drift between training reference and recent submissions."""
    reference_stats = ensure_training_reference_stats(db, model_version)
    recent_stats = get_recent_submission_stats(db, recent_days)
    
    if not recent_stats:
        return {
            'available': False,
            'message': 'Insufficient recent submission data for drift detection',
            'features': {},
            'metadata': {
                'reference_source': reference_stats['metadata'].get('source', 'unknown'),
                'reference_period_days': reference_days,
                'recent_period_days': recent_days,
            }
        }
    
    features = {}
    overall_summary = {
        'high_drift': 0,
        'moderate_drift': 0,
        'no_drift': 0,
        'insufficient_data': 0,
        'error': 0,
    }
    
    # Numerical features
    for wt in NUMERICAL_WASTE_TYPES:
        ref = reference_stats['numerical'].get(wt, {})
        rec = recent_stats.get(wt, {})
        
        if not rec or rec.get('count', 0) < MIN_SAMPLES_NUMERICAL_DRIFT:
            features[wt] = {
                'feature_type': 'numerical',
                'status': 'INSUFFICIENT_DATA',
                'reference_samples': ref.get('sample_count', 0),
                'recent_samples': rec.get('count', 0) if rec else 0,
                'reference_mean': ref.get('mean'),
                'recent_mean': rec.get('mean') if rec else None,
                'reference_std': ref.get('std'),
                'recent_std': rec.get('std') if rec else None,
                'mean_change_pct': None,
                'std_change_pct': None,
                'psi': None,
                'ks_pvalue': None,
                'warning': f'Insufficient recent samples ({rec.get("count", 0) if rec else 0} < {MIN_SAMPLES_NUMERICAL_DRIFT})',
            }
            overall_summary['insufficient_data'] += 1
            continue
        
        ref_mean = ref.get('mean', rec['mean'])
        ref_std = ref.get('std', rec['std'])
        rec_mean = rec['mean']
        rec_std = rec['std']
        rec_values = rec['values']
        
        mean_change_pct = abs((rec_mean - ref_mean) / ref_mean * 100) if ref_mean != 0 else 0
        std_change_pct = abs((rec_std - ref_std) / ref_std * 100) if ref_std != 0 else 0
        
        # Use reference distribution for PSI/KS
        if ref_std > 0:
            ref_values = np.random.normal(ref_mean, ref_std, max(ref.get('sample_count', 1000), 1000))
        else:
            ref_values = np.full(max(ref.get('sample_count', 1000), 1000), ref_mean)
        
        psi = calculate_psi(ref_values, np.array(rec_values))
        
        try:
            ks_stat, ks_pvalue = stats.ks_2samp(ref_values, rec_values)
        except Exception:
            ks_pvalue = float('nan')
        
        status, details = classify_numerical_drift(
            psi, mean_change_pct, std_change_pct, ks_pvalue,
            ref.get('sample_count', 0), rec['count']
        )
        
        overall_summary[status.lower().replace('_', '_')] += 1
        
        features[wt] = {
            'feature_type': 'numerical',
            'status': status,
            'reference_samples': ref.get('sample_count', 0),
            'recent_samples': rec['count'],
            'reference_mean': round(ref_mean, 4),
            'recent_mean': round(rec_mean, 4),
            'reference_std': round(ref_std, 4),
            'recent_std': round(rec_std, 4),
            'mean_change_pct': round(mean_change_pct, 2),
            'std_change_pct': round(std_change_pct, 2),
            'psi': round(psi, 4) if not np.isnan(psi) else None,
            'ks_pvalue': round(ks_pvalue, 6) if not np.isnan(ks_pvalue) else None,
            'details': details,
        }
    
    # Categorical features
    for cat_feature in CATEGORICAL_FEATURES:
        cat_key = f'{cat_feature}_distribution'
        ref_cat = reference_stats['categorical'].get(cat_feature, {})
        rec_cat = recent_stats.get(cat_key, {})
        
        if not rec_cat or rec_cat.get('sample_count', 0) < MIN_SAMPLES_CATEGORICAL_DRIFT:
            features[cat_feature] = {
                'feature_type': 'categorical',
                'status': 'INSUFFICIENT_DATA',
                'reference_samples': ref_cat.get('sample_count', 0),
                'recent_samples': rec_cat.get('sample_count', 0) if rec_cat else 0,
                'categories': list(ref_cat.get('counts', {}).keys()) if rec_cat else [],
                'warning': f'Insufficient recent samples ({rec_cat.get("sample_count", 0) if rec_cat else 0} < {MIN_SAMPLES_CATEGORICAL_DRIFT})',
            }
            overall_summary['insufficient_data'] += 1
            continue
        
        ref_counts = ref_cat.get('counts', {})
        rec_counts = rec_cat.get('counts', {})
        
        status, details = calculate_categorical_drift(ref_counts, rec_counts)
        
        overall_summary[status.lower().replace('_', '_')] += 1
        
        features[cat_feature] = {
            'feature_type': 'categorical',
            'status': status,
            'reference_samples': ref_cat.get('sample_count', 0),
            'recent_samples': rec_cat.get('sample_count', 0),
            'categories': details.get('categories', []),
            'reference_counts': details.get('reference_counts', []),
            'recent_counts': details.get('recent_counts', []),
            'reference_proportions': details.get('reference_proportions', []),
            'recent_proportions': details.get('recent_proportions', []),
            'chi2_statistic': details.get('chi2_statistic'),
            'chi2_pvalue': details.get('chi2_pvalue'),
            'cramers_v': details.get('cramers_v'),
            'min_expected_count': details.get('min_expected_count'),
            'details': details,
        }
    
    # Determine overall status
    if overall_summary['high_drift'] > 0:
        overall_status = 'HIGH_DRIFT'
    elif overall_summary['moderate_drift'] > 0:
        overall_status = 'MODERATE_DRIFT'
    elif overall_summary['no_drift'] > 0:
        overall_status = 'NO_DRIFT'
    else:
        overall_status = 'INSUFFICIENT_DATA'
    
    return {
        'available': True,
        'overall_status': overall_status,
        'reference_source': reference_stats['metadata'].get('source', 'unknown'),
        'reference_model_version': reference_stats['metadata'].get('model_version'),
        'reference_period_days': reference_days,
        'recent_period_days': recent_days,
        'features': features,
        'summary': overall_summary,
        'thresholds_used': DRIFT_THRESHOLDS,
    }


def get_offline_test_metrics() -> Dict[str, Dict[str, float]]:
    """Load offline test metrics from training artifacts."""
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
    
    offline_metrics = {}
    
    if metrics_path:
        with open(metrics_path) as f:
            metrics = json.load(f)
        
        rf_multi = metrics.get("RF_Multi", {})
        if rf_multi and rf_multi.get("test_metrics"):
            test_m = rf_multi["test_metrics"]
            total_m = rf_multi.get("total_waste_metrics", {})
            
            for wt in WASTE_TYPES:
                if wt == 'total':
                    offline_metrics[wt] = {
                        'R2': total_m.get('test_TOTAL_R2', 0),
                        'MAE': total_m.get('test_TOTAL_MAE', 0),
                        'RMSE': total_m.get('test_TOTAL_RMSE', 0),
                        'MAPE': total_m.get('test_TOTAL_MAPE', 0),
                        'SMAPE': total_m.get('test_TOTAL_SMAPE', 0),
                    }
                else:
                    r2_key = f"test_next_day_{wt}_kg_R2"
                    mae_key = f"test_next_day_{wt}_kg_MAE"
                    rmse_key = f"test_next_day_{wt}_kg_RMSE"
                    mape_key = f"test_next_day_{wt}_kg_MAPE"
                    smape_key = f"test_next_day_{wt}_kg_SMAPE"
                    offline_metrics[wt] = {
                        'R2': test_m.get(r2_key, 0),
                        'MAE': test_m.get(mae_key, 0),
                        'RMSE': test_m.get(rmse_key, 0),
                        'MAPE': test_m.get(mape_key, 0),
                        'SMAPE': test_m.get(smape_key, 0),
                    }
    
    return offline_metrics


def calculate_real_world_performance(db: Session, days: int) -> Dict[str, Dict[str, Any]]:
    """Calculate real-world performance metrics for a given period."""
    cutoff = date.today() - timedelta(days=days)
    
    accuracy_records = db.query(PredictionAccuracy).filter(
        PredictionAccuracy.prediction_date >= cutoff
    ).all()
    
    if not accuracy_records:
        return {}
    
    results = {}
    for wt in WASTE_TYPES:
        wt_records = [r for r in accuracy_records if (r.waste_type or '').lower() == wt.lower()]
        if not wt_records or len(wt_records) < MIN_SAMPLES_PERFORMANCE:
            results[wt] = {
                'available': False,
                'sample_count': len(wt_records),
                'reliability': get_reliability_level(len(wt_records)),
                'warning': f'Insufficient samples ({len(wt_records)} < {MIN_SAMPLES_PERFORMANCE})'
            }
            continue
        
        predicted = [r.predicted_kg or 0 for r in wt_records]
        actual = [r.actual_kg or 0 for r in wt_records]
        errors = [r.absolute_error_kg or 0 for r in wt_records]
        pct_errors = [r.percentage_error for r in wt_records if r.percentage_error is not None]
        
        n = len(wt_records)
        mae = sum(errors) / n
        rmse = math.sqrt(sum(e**2 for e in errors) / n)
        
        if n >= 2:
            mean_actual = sum(actual) / n
            ss_tot = sum((a - mean_actual)**2 for a in actual)
            ss_res = sum((actual[i] - predicted[i])**2 for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            r2 = 0
        
        mape = sum(pct_errors) / len(pct_errors) if pct_errors else None
        smape = calculate_smape(predicted, actual)
        
        reliability = get_reliability_level(n)
        
        results[wt] = {
            'available': True,
            'sample_count': n,
            'MAE': round(mae, 4),
            'RMSE': round(rmse, 4),
            'R2': round(r2, 4),
            'MAPE': round(mape, 2) if mape is not None else None,
            'SMAPE': round(smape, 2) if smape is not None else None,
            'total_predicted_kg': round(sum(predicted), 2),
            'total_actual_kg': round(sum(actual), 2),
            'reliability': reliability,
        }
    
    return results


def get_performance_trend(db: Session) -> Dict[str, Any]:
    """Get performance metrics for rolling periods."""
    periods = [7, 30, 90]
    offline_metrics = get_offline_test_metrics()
    
    trend_data = {}
    
    for period in periods:
        real_world = calculate_real_world_performance(db, period)
        trend_data[f'last_{period}_days'] = {
            'period_days': period,
            'real_world': real_world,
            'offline_test': {wt: offline_metrics.get(wt, {}) for wt in WASTE_TYPES},
        }
    
    overall_real_world = calculate_real_world_performance(db, 365)
    trend_data['overall'] = {
        'period_days': 'all',
        'real_world': overall_real_world,
        'offline_test': {wt: offline_metrics.get(wt, {}) for wt in WASTE_TYPES},
    }
    
    return {
        'available': True,
        'periods': trend_data,
        'offline_test_note': 'Offline metrics from chronological hold-out test set (no data leakage)',
        'real_world_note': 'Real-world metrics from matched prediction-actual collection pairs',
    }


def classify_performance_degradation(offline: Dict, real_world: Dict) -> Dict[str, str]:
    """Classify performance degradation for each waste type."""
    if not real_world.get('available', False):
        return {'status': 'INSUFFICIENT_DATA', 'reason': real_world.get('warning', 'No real-world data')}
    
    offline_mae = offline.get('MAE', 0)
    offline_rmse = offline.get('RMSE', 0)
    offline_r2 = offline.get('R2', 0)
    offline_smape = offline.get('SMAPE', 0)
    
    rw_mae = real_world.get('MAE', 0)
    rw_rmse = real_world.get('RMSE', 0)
    rw_r2 = real_world.get('R2', 0)
    rw_smape = real_world.get('SMAPE', 0)
    
    if offline_mae == 0 and offline_rmse == 0:
        return {'status': 'NO_OFFLINE_BASELINE', 'reason': 'No offline baseline available'}
    
    mae_increase_pct = ((rw_mae - offline_mae) / offline_mae) * 100 if offline_mae > 0 else 0
    rmse_increase_pct = ((rw_rmse - offline_rmse) / offline_rmse) * 100 if offline_rmse > 0 else 0
    r2_decrease_pct = ((offline_r2 - rw_r2) / offline_r2) * 100 if offline_r2 > 0 else 0
    smape_increase_pct = ((rw_smape - offline_smape) / offline_smape) * 100 if offline_smape > 0 else 0
    
    warning_mae = mae_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['mae_increase_pct']['warning']
    critical_mae = mae_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['mae_increase_pct']['critical']
    warning_rmse = rmse_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['rmse_increase_pct']['warning']
    critical_rmse = rmse_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['rmse_increase_pct']['critical']
    warning_r2 = r2_decrease_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['r2_decrease_pct']['warning']
    critical_r2 = r2_decrease_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['r2_decrease_pct']['critical']
    warning_smape = smape_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['smape_increase_pct']['warning']
    critical_smape = smape_increase_pct >= PERFORMANCE_DEGRADATION_THRESHOLDS['smape_increase_pct']['critical']
    
    reliability = real_world.get('reliability', {})
    reliability_level = reliability.get('level', 'INSUFFICIENT_DATA')
    
    # If reliability is insufficient, we cannot trust the degradation assessment
    if reliability_level == 'INSUFFICIENT_DATA':
        return {
            'status': 'INSUFFICIENT_DATA',
            'reason': 'Insufficient real-world samples for reliable degradation assessment',
            'mae_increase_pct': round(mae_increase_pct, 1),
            'rmse_increase_pct': round(rmse_increase_pct, 1),
            'r2_decrease_pct': round(r2_decrease_pct, 1),
            'smape_increase_pct': round(smape_increase_pct, 1),
        }
    
    if critical_mae or critical_rmse or critical_r2 or critical_smape:
        return {
            'status': 'SIGNIFICANT_DEGRADATION',
            'mae_increase_pct': round(mae_increase_pct, 1),
            'rmse_increase_pct': round(rmse_increase_pct, 1),
            'r2_decrease_pct': round(r2_decrease_pct, 1),
            'smape_increase_pct': round(smape_increase_pct, 1),
            'reason': 'Performance significantly worse than offline test',
        }
    elif warning_mae or warning_rmse or warning_r2 or warning_smape:
        return {
            'status': 'NOTICEABLE_DEGRADATION',
            'mae_increase_pct': round(mae_increase_pct, 1),
            'rmse_increase_pct': round(rmse_increase_pct, 1),
            'r2_decrease_pct': round(r2_decrease_pct, 1),
            'smape_increase_pct': round(smape_increase_pct, 1),
            'reason': 'Performance noticeably worse than offline test',
        }
    else:
        return {
            'status': 'STABLE',
            'mae_increase_pct': round(mae_increase_pct, 1),
            'rmse_increase_pct': round(rmse_increase_pct, 1),
            'r2_decrease_pct': round(r2_decrease_pct, 1),
            'smape_increase_pct': round(smape_increase_pct, 1),
            'reason': 'Performance consistent with offline test',
        }


def get_prediction_coverage(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get comprehensive prediction coverage analysis."""
    cutoff = date.today() - timedelta(days=days)
    
    # All area predictions in period
    all_predictions = db.query(AreaPrediction).filter(
        AreaPrediction.prediction_date >= cutoff
    ).all()
    
    # All actual collections in period
    all_collections = db.query(ActualCollection).filter(
        ActualCollection.collection_date >= cutoff
    ).all()
    
    # All accuracy records in period
    all_accuracy = db.query(PredictionAccuracy).filter(
        PredictionAccuracy.prediction_date >= cutoff
    ).all()
    
    # Track each prediction's evaluation status
    predictions_evaluated = 0
    predictions_unmatched = 0
    predictions_pending = 0
    unmatched_reasons = {}
    
    for pred in all_predictions:
        accuracy_exists = db.query(PredictionAccuracy).filter(
            PredictionAccuracy.area == pred.area,
            PredictionAccuracy.prediction_date == pred.prediction_date,
            PredictionAccuracy.horizon == pred.horizon,
            PredictionAccuracy.model == pred.model
        ).first()
        
        if accuracy_exists:
            predictions_evaluated += 1
        else:
            collection_exists = db.query(ActualCollection).filter(
                ActualCollection.area == pred.area,
                ActualCollection.collection_date == pred.prediction_date
            ).first()
            
            if collection_exists:
                if collection_exists.is_matched:
                    predictions_unmatched += 1
                    reason = "Collection matched but no accuracy record (should not happen)"
                else:
                    predictions_unmatched += 1
                    reason = f"Collection exists but not matched (is_matched={collection_exists.is_matched})"
            else:
                predictions_pending += 1
                reason = "No matching collection yet"
            
            unmatched_reasons[reason] = unmatched_reasons.get(reason, 0) + 1
    
    collections_total = len(all_collections)
    collections_matched = sum(1 for c in all_collections if c.is_matched)
    collections_unmatched = collections_total - collections_matched
    
    eligible_predictions = predictions_evaluated + predictions_unmatched
    coverage_pct = (predictions_evaluated / eligible_predictions * 100) if eligible_predictions > 0 else 0
    
    return {
        'period_days': days,
        'predictions': {
            'total': len(all_predictions),
            'evaluated': predictions_evaluated,
            'unmatched': predictions_unmatched,
            'pending': predictions_pending,
        },
        'collections': {
            'total': collections_total,
            'matched': collections_matched,
            'unmatched': collections_unmatched,
        },
        'accuracy_records': len(all_accuracy),
        'coverage': {
            'eligible_predictions': eligible_predictions,
            'matched_predictions': predictions_evaluated,
            'coverage_pct': round(coverage_pct, 1),
        },
        'unmatched_reasons': unmatched_reasons,
    }


def get_model_health_status(db: Session) -> Dict[str, Any]:
    """Determine overall model health status based on drift AND real-world reliability."""
    drift_result = detect_data_drift(db)
    performance_trend = get_performance_trend(db)
    coverage = get_prediction_coverage(db, 30)
    
    overall_drift = drift_result.get('overall_status', 'INSUFFICIENT_DATA')
    
    # Analyze performance degradation with reliability consideration
    degradation_summary = {
        'significant_degradation': 0,
        'noticeable_degradation': 0,
        'stable': 0,
        'insufficient_data': 0,
        'no_offline_baseline': 0,
    }
    
    has_reliable_degradation_assessment = False
    
    for period_key in ['last_7_days', 'last_30_days', 'last_90_days', 'overall']:
        period_data = performance_trend.get('periods', {}).get(period_key, {})
        for wt in WASTE_TYPES:
            offline = period_data.get('offline_test', {}).get(wt, {})
            real_world = period_data.get('real_world', {}).get(wt, {})
            if real_world.get('available', False):
                degradation = classify_performance_degradation(offline, real_world)
                status = degradation.get('status', 'UNKNOWN')
                degradation_summary[status.lower().replace('-', '_')] += 1
                if status in ['STABLE', 'NOTICEABLE_DEGRADATION', 'SIGNIFICANT_DEGRADATION']:
                    has_reliable_degradation_assessment = True
    
    total_accuracy_records = db.query(func.count(PredictionAccuracy.id)).scalar() or 0
    overall_reliability = get_reliability_level(total_accuracy_records)
    reliability_level = overall_reliability['level']
    
    # Health status logic: BOTH drift severity AND real-world evaluation reliability matter
    if reliability_level == 'INSUFFICIENT_DATA' and overall_drift == 'INSUFFICIENT_DATA':
        health_status = 'INSUFFICIENT_DATA'
        health_reason = 'Insufficient data for both drift detection and real-world evaluation'
    elif reliability_level == 'INSUFFICIENT_DATA':
        health_status = 'INSUFFICIENT_DATA'
        health_reason = f'Insufficient real-world samples ({total_accuracy_records}) for reliable evaluation; drift status: {overall_drift}'
    elif overall_drift == 'HIGH_DRIFT' and degradation_summary['significant_degradation'] > 0:
        health_status = 'CRITICAL'
        health_reason = 'High data drift AND significant accuracy degradation'
    elif overall_drift == 'HIGH_DRIFT':
        health_status = 'WARNING'  # Drift alone doesn't make it critical without degradation evidence
        health_reason = 'High data drift detected; real-world evaluation needed to assess impact'
    elif degradation_summary['significant_degradation'] > 0:
        health_status = 'CRITICAL'
        health_reason = 'Significant accuracy degradation detected'
    elif overall_drift == 'MODERATE_DRIFT' or degradation_summary['noticeable_degradation'] > 0:
        health_status = 'WARNING'
        reasons = []
        if overall_drift == 'MODERATE_DRIFT':
            reasons.append('Moderate data drift detected')
        if degradation_summary['noticeable_degradation'] > 0:
            reasons.append('Noticeable performance degradation')
        health_reason = '; '.join(reasons)
    elif overall_drift == 'NO_DRIFT' and degradation_summary['stable'] > 0:
        health_status = 'HEALTHY'
        health_reason = 'No data drift and stable prediction accuracy'
    else:
        health_status = 'INSUFFICIENT_DATA'
        health_reason = 'Insufficient evidence for reliable health assessment'
    
    return {
        'health_status': health_status,
        'health_reason': health_reason,
        'overall_drift_status': overall_drift,
        'reliability_level': reliability_level,
        'total_real_world_samples': total_accuracy_records,
        'prediction_coverage': coverage,
        'performance_degradation_summary': degradation_summary,
        'has_reliable_degradation_assessment': has_reliable_degradation_assessment,
        'drift_summary': drift_result.get('summary', {}),
        'thresholds_documented': {
            'drift': DRIFT_THRESHOLDS,
            'performance_degradation': PERFORMANCE_DEGRADATION_THRESHOLDS,
        },
        'metadata': {
            'reference_source': drift_result.get('reference_source', 'unknown'),
            'reference_model_version': drift_result.get('reference_model_version'),
            'drift_reference_period_days': drift_result.get('reference_period_days'),
            'drift_recent_period_days': drift_result.get('recent_period_days'),
        }
    }


def generate_recommendations(health_status: Dict, drift_result: Dict, performance_trend: Dict, coverage: Dict) -> List[str]:
    """Generate actionable recommendations based on monitoring results."""
    recommendations = []
    
    overall_drift = drift_result.get('overall_status', 'INSUFFICIENT_DATA')
    health = health_status.get('health_status', 'INSUFFICIENT_DATA')
    total_samples = health_status.get('total_real_world_samples', 0)
    reliability = health_status.get('reliability_level', 'INSUFFICIENT_DATA')
    
    if health == 'INSUFFICIENT_DATA':
        if total_samples < 6:
            recommendations.append("Continue collecting real-world data — insufficient samples for reliable monitoring")
        else:
            recommendations.append("Collect more matched prediction-actual pairs to enable reliable evaluation")
    elif health == 'HEALTHY':
        recommendations.append("Model is healthy — continue monitoring with regular checks")
    elif health == 'WARNING':
        if overall_drift == 'MODERATE_DRIFT':
            moderate_features = [k for k, v in drift_result.get('features', {}).items() 
                               if v.get('status') == 'MODERATE_DRIFT']
            if moderate_features:
                recommendations.append(f"Moderate drift detected in: {', '.join(moderate_features)} — monitor distribution changes")
        if not health_status.get('has_reliable_degradation_assessment', False):
            recommendations.append("Real-world evaluation reliability is low — continue collecting matched data")
        else:
            recommendations.append("Monitor closely — investigate recent waste patterns if drift persists")
    elif health == 'CRITICAL':
        recommendations.append("URGENT: High drift and/or significant degradation — investigate immediately")
        if overall_drift == 'HIGH_DRIFT':
            high_features = [k for k, v in drift_result.get('features', {}).items() 
                           if v.get('status') == 'HIGH_DRIFT']
            if high_features:
                recommendations.append(f"High drift detected in: {', '.join(high_features)} — investigate recent waste patterns")
    
    # Performance-specific recommendations
    for period_key in ['last_30_days', 'last_90_days']:
        period_data = performance_trend.get('periods', {}).get(period_key, {})
        for wt in WASTE_TYPES:
            offline = period_data.get('offline_test', {}).get(wt, {})
            real_world = period_data.get('real_world', {}).get(wt, {})
            if real_world.get('available', False):
                degradation = classify_performance_degradation(offline, real_world)
                if degradation.get('status') == 'SIGNIFICANT_DEGRADATION':
                    recommendations.append(f"Model retraining may be considered for {wt} waste after sufficient samples (significant degradation in {period_key})")
                elif degradation.get('status') == 'NOTICEABLE_DEGRADATION':
                    recommendations.append(f"Monitor {wt} waste prediction accuracy (noticeable degradation in {period_key})")
    
    # Coverage recommendations
    coverage_pct = coverage.get('coverage', {}).get('coverage_pct', 0)
    if coverage_pct < 50:
        recommendations.append(f"Prediction coverage is low ({coverage_pct:.1f}%) — investigate unmatched predictions")
    
    # Reliability-based recommendations
    if reliability == 'EARLY_EVALUATION':
        recommendations.append("Early evaluation phase — continue collecting data for stronger confidence")
    elif reliability == 'MODERATE_CONFIDENCE':
        recommendations.append("Moderate confidence evaluation — trends are becoming more reliable")
    elif reliability == 'STRONG_EVALUATION':
        recommendations.append("Strong evaluation confidence — monitoring metrics are reliable")
    
    # Deduplicate
    seen = set()
    unique_recs = []
    for r in recommendations:
        if r not in seen:
            seen.add(r)
            unique_recs.append(r)
    
    return unique_recs[:10]


def get_model_comparison(db: Session) -> Dict[str, Any]:
    """Compare models: clearly separate offline vs real-world metrics."""
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
    
    models = {}
    
    if metrics_path:
        with open(metrics_path) as f:
            metrics = json.load(f)
        
        model_configs = [
            ("PerTypeRF", "Per-Type Random Forest (Two-Stage)", metrics.get("RF_PerType", {})),
            ("RF_Multi", "Multi-Output Random Forest", metrics.get("RF_Multi", {})),
            ("XGB_Multi", "Multi-Output XGBoost", metrics.get("XGB_Multi", {})),
            ("XGB_PerType", "Per-Type XGBoost (Two-Stage)", metrics.get("XGB_PerType", {})),
        ]
        
        for model_id, model_name, model_metrics in model_configs:
            if model_metrics:
                offline_r2 = model_metrics.get('R2', 0)
                offline_mae = model_metrics.get('MAE', 0)
                offline_rmse = model_metrics.get('RMSE', 0)
                offline_smape = model_metrics.get('SMAPE', 0)
                
                models[model_id] = {
                    'name': model_name,
                    'offline_R2': round(offline_r2, 4),
                    'offline_MAE': round(offline_mae, 4),
                    'offline_RMSE': round(offline_rmse, 4),
                    'offline_SMAPE': round(offline_smape, 4) if offline_smape else None,
                    'real_world_R2': None,
                    'real_world_MAE': None,
                    'real_world_RMSE': None,
                    'real_world_SMAPE': None,
                    'real_world_samples': 0,
                    'real_world_reliability': None,
                    'status': 'Offline metrics only',
                }
    
    # Add real-world metrics ONLY for the currently deployed model with sufficient samples
    real_world_overall = calculate_real_world_performance(db, 365)
    total_rw = real_world_overall.get('total', {})
    
    if total_rw.get('available', False) and total_rw.get('reliability', {}).get('level') in ['MODERATE_CONFIDENCE', 'STRONG_EVALUATION']:
        for model_id in models:
            if model_id == 'PerTypeRF':  # Currently deployed model
                models[model_id]['real_world_R2'] = total_rw.get('R2')
                models[model_id]['real_world_MAE'] = total_rw.get('MAE')
                models[model_id]['real_world_RMSE'] = total_rw.get('RMSE')
                models[model_id]['real_world_SMAPE'] = total_rw.get('SMAPE')
                models[model_id]['real_world_samples'] = total_rw.get('sample_count', 0)
                models[model_id]['real_world_reliability'] = total_rw.get('reliability')
                models[model_id]['status'] = 'Production (real-world evaluated with sufficient samples)'
    
    return {
        'models': models,
        'note': 'Real-world metrics only shown for deployed model (PerTypeRF) when sample size is sufficient (MODERATE_CONFIDENCE+). Other models show offline metrics only.',
        'offline_test_note': 'Offline metrics from chronological hold-out test set (no data leakage)',
        'real_world_note': 'Real-world metrics from matched prediction-actual collection pairs',
    }


def get_ml_monitoring_full_report(db: Session) -> Dict[str, Any]:
    """Generate complete ML monitoring report."""
    drift_result = detect_data_drift(db)
    performance_trend = get_performance_trend(db)
    coverage = get_prediction_coverage(db, 30)
    health_status = get_model_health_status(db)
    model_comparison = get_model_comparison(db)
    recommendations = generate_recommendations(health_status, drift_result, performance_trend, coverage)
    
    return {
        'generated_at': datetime.utcnow().isoformat(),
        'health': health_status,
        'data_drift': drift_result,
        'performance_trend': performance_trend,
        'prediction_coverage': coverage,
        'model_comparison': model_comparison,
        'recommendations': recommendations,
    }
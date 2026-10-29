import json
import joblib
import numpy as np
import pandas as pd
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.models.waste import WasteSubmission, WasteItem
from app.services.weather_service import get_weather_features

WASTE_TYPES = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']
PER_TYPE_TARGETS = [f'next_day_{wt}_kg' for wt in WASTE_TYPES]

# Model paths - improved models (located in MLproject/ml/models/improved)
IMPROVED_MODELS_PATH = settings.ML_MODELS_PATH / "improved"
MULTI_RF_PATH = IMPROVED_MODELS_PATH / 'RF_Multi.joblib'
MULTI_XGB_PATH = IMPROVED_MODELS_PATH / 'XGB_Multi.joblib'
PER_TYPE_RF_PATH = IMPROVED_MODELS_PATH / 'RF_PerType.joblib'
PREPROCESSOR_PATH = IMPROVED_MODELS_PATH / 'preprocessor.joblib'

# Import TwoStageModel from shared module for pickle compatibility
from app.services.ml_shared import TwoStageModel


class DatabaseWastePredictor:
    """ML predictor that constructs features from database for real users."""
    
    def __init__(self, model_type: str = 'rf', use_per_type: bool = True):
        self.model_type = model_type.lower()
        self.use_per_type = use_per_type
        self.multi_model = None
        self.per_type_model = None
        self.preprocessor = None
        self.feature_names = None
        self._load_models()
    
    def _load_models(self):
        """Load the appropriate models based on configuration."""
        # Register TwoStageModel for pickle compatibility (model was saved with train_improved.TwoStageModel)
        import types
        import MLproject.ml.preprocessing.pipeline as pipeline_module
        
        # Create a fake train_improved module with TwoStageModel
        train_improved = types.ModuleType('train_improved')
        from app.services.ml_shared import TwoStageModel
        train_improved.TwoStageModel = TwoStageModel
        # Also add any other classes that might be referenced
        train_improved.PreprocessingConfig = pipeline_module.PreprocessingConfig
        train_improved.OutlierClipper = pipeline_module.OutlierClipper
        sys.modules['train_improved'] = train_improved
        sys.modules['__main__'] = train_improved
        
        try:
            if self.use_per_type:
                # Load per-type model (handles zero-inflated targets)
                self.per_type_model = joblib.load(PER_TYPE_RF_PATH)
            else:
                # Load multi-output model
                if self.model_type == 'rf':
                    model_path = MULTI_RF_PATH
                elif self.model_type == 'xgb':
                    model_path = MULTI_XGB_PATH
                else:
                    raise ValueError(f"Unknown model_type: {self.model_type}. Use 'rf' or 'xgb'.")
                self.multi_model = joblib.load(model_path)
            
            # Load preprocessor
            preprocessor_dict = joblib.load(PREPROCESSOR_PATH)
        except FileNotFoundError as e:
            raise RuntimeError(
                f"ML model file not found: {e.filename}. "
                f"Please ensure model files are placed in {IMPROVED_MODELS_PATH}"
            )
        
        # Handle both dict format (from SmartWastePreprocessor.save) and object format
        if isinstance(preprocessor_dict, dict):
            self.preprocessor = preprocessor_dict['preprocessing_pipeline']
            self.feature_names = preprocessor_dict['feature_names']
            self.feature_columns = preprocessor_dict['feature_columns']
        else:
            self.preprocessor = preprocessor_dict
            self.feature_names = self.preprocessor.feature_names
            self.feature_columns = self.preprocessor.feature_columns
    
    def _get_user_history(self, db: Session, user_id: str, cutoff_date: date) -> pd.DataFrame:
        """Get user's waste history from database up to cutoff_date."""
        submissions = db.query(WasteSubmission).filter(
            WasteSubmission.user_id == user_id,
            WasteSubmission.submission_date <= cutoff_date
        ).order_by(WasteSubmission.submission_date).all()
        
        if not submissions:
            return pd.DataFrame()
        
        records = []
        for s in submissions:
            items = db.query(WasteItem).filter(WasteItem.submission_id == s.id).all()
            breakdown = {item.waste_type.lower(): item.quantity_kg for item in items}
            
            # Ensure all waste types present
            for wt in WASTE_TYPES:
                if wt not in breakdown:
                    breakdown[wt] = 0.0
            
            records.append({
                'user_id': s.user_id,
                'submission_date': s.submission_date,
                'area': s.area_snapshot,
                'account_type': s.account_type_snapshot,
                'day_of_week': s.submission_date.weekday(),
                'month': s.submission_date.month,
                'day_type': s.day_type,
                'is_weekend': s.day_type == 'weekend',
                'total_waste_kg': s.total_waste_kg,
                'dry_kg': breakdown.get('dry', 0.0),
                'wet_kg': breakdown.get('wet', 0.0),
                'plastic_kg': breakdown.get('plastic', 0.0),
                'glass_kg': breakdown.get('glass', 0.0),
                'metal_kg': breakdown.get('metal', 0.0),
                'medical_kg': breakdown.get('medical', 0.0),
            })
        
        df = pd.DataFrame(records)
        df['submission_date'] = pd.to_datetime(df['submission_date'])
        return df
    
    def _get_season(self, month: int) -> str:
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        else:
            return 'spring'
    
    def _get_day_type(self, dt: date) -> str:
        if dt.weekday() >= 5:
            return 'weekend'
        return 'normal_day'
    
    def _construct_features(self, db: Session, user_id: str, prediction_date: date) -> np.ndarray:
        """Construct feature vector for a user at prediction_date."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        area = user.area or 'Unknown'
        account_type = user.account_type
        
        cutoff_date = prediction_date - timedelta(days=1)
        hist = self._get_user_history(db, user_id, cutoff_date)
        
        if len(hist) == 0:
            raise ValueError(f"No history for user {user_id} before {prediction_date}")
        
        last_record = hist.iloc[-1]
        
        pred_day_of_week = prediction_date.weekday()
        pred_month = prediction_date.month
        pred_season = self._get_season(pred_month)
        pred_day_type = self._get_day_type(prediction_date)
        pred_is_weekend = pred_day_of_week >= 5
        
        # Use real weather service instead of hardcoded defaults
        temp_max_c, rainfall_mm, humidity_pct = get_weather_features(area, prediction_date)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Weather for {area} on {prediction_date}: temp={temp_max_c}, rain={rainfall_mm}, humidity={humidity_pct}")
        
        # Determine people count based on account type
        if user.account_type == 'family':
            people_present = int(user.family_members or 1)
        elif user.account_type == 'restaurant':
            people_present = int(user.avg_customers_per_day or 1)
        elif user.account_type == 'organization':
            people_present = int(user.avg_customers_per_day or 1)  # Using avg_customers_per_day for org workers
        else:
            people_present = 1
        
        family_members = float(user.family_members or 0)
        avg_customers_per_day = float(user.avg_customers_per_day or 0)
        employee_count = float(user.avg_customers_per_day or 0) if user.account_type == 'organization' else 0.0
        
        waste_history = hist['total_waste_kg'].values
        
        lag_1d = waste_history[-1] if len(waste_history) >= 1 else 0.0
        lag_2d = waste_history[-2] if len(waste_history) >= 2 else 0.0
        lag_3d = waste_history[-3] if len(waste_history) >= 3 else 0.0
        lag_7d = waste_history[-7] if len(waste_history) >= 7 else 0.0
        
        if len(waste_history) >= 1:
            roll_mean_3d = np.mean(waste_history[-3:]) if len(waste_history) >= 3 else np.mean(waste_history)
            roll_std_3d = np.std(waste_history[-3:], ddof=1) if len(waste_history) >= 3 else 0.0
            roll_mean_7d = np.mean(waste_history[-7:]) if len(waste_history) >= 7 else np.mean(waste_history)
            roll_std_7d = np.std(waste_history[-7:], ddof=1) if len(waste_history) >= 7 else 0.0
        else:
            roll_mean_3d = roll_std_3d = roll_mean_7d = roll_std_7d = 0.0
        
        features = {
            'area': area,
            'account_type': account_type,
            'day_of_week': pred_day_of_week,
            'month': pred_month,
            'season': pred_season,
            'day_type': pred_day_type,
            'is_weekend': pred_is_weekend,
            'is_holiday': False,
            'is_festival': False,
            'festival_intensity': 0.0,
            'temp_max_c': temp_max_c,
            'rainfall_mm': rainfall_mm,
            'humidity_pct': humidity_pct,
            'people_present': people_present,
            'family_members': family_members,
            'avg_customers_per_day': avg_customers_per_day,
            'employee_count': employee_count,
            'total_waste_kg_lag_1d': lag_1d,
            'total_waste_kg_lag_2d': lag_2d,
            'total_waste_kg_lag_3d': lag_3d,
            'total_waste_kg_lag_7d': lag_7d,
            'total_waste_kg_roll_mean_3d': roll_mean_3d,
            'total_waste_kg_roll_std_3d': roll_std_3d,
            'total_waste_kg_roll_mean_7d': roll_mean_7d,
            'total_waste_kg_roll_std_7d': roll_std_7d,
            'dry_kg_lag_1d': last_record['dry_kg'],
            'wet_kg_lag_1d': last_record['wet_kg'],
            'plastic_kg_lag_1d': last_record['plastic_kg'],
            'glass_kg_lag_1d': last_record['glass_kg'],
            'metal_kg_lag_1d': last_record['metal_kg'],
            'medical_kg_lag_1d': last_record['medical_kg'],
        }
        
        # Create DataFrame with all features expected by preprocessor
        X = pd.DataFrame([features])
        
        # Add missing columns with defaults (for features not in basic set)
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0.0  # Default for numeric features
        
        # Ensure column order matches preprocessor
        X = X[self.feature_columns]
        
        # Transform using preprocessor
        X_trans = self.preprocessor.transform(X)
        
        return X_trans
    
    def predict_next_day(self, db: Session, user_id: str, prediction_date: date = None) -> Dict[str, Any]:
        if prediction_date is None:
            prediction_date = date.today() + timedelta(days=1)
        
        X_trans = self._construct_features(db, user_id, prediction_date)
        
        if self.use_per_type and self.per_type_model:
            # Use per-type models
            predictions = []
            for target in PER_TYPE_TARGETS:
                model = self.per_type_model[target]
                if hasattr(model, 'classifier'):  # Two-stage model
                    pred = model.predict(X_trans)
                else:
                    pred = model.predict(X_trans)
                predictions.append(pred[0] if len(pred) > 0 else 0.0)
            predictions = np.array(predictions)
        else:
            # Use multi-output model
            predictions = self.multi_model.predict(X_trans)[0]
        
        user = db.query(User).filter(User.id == user_id).first()
        area = user.area if user else 'Unknown'
        
        breakdown = []
        total_kg = 0.0
        for i, waste_type in enumerate(WASTE_TYPES):
            pred_kg = max(0.0, round(float(predictions[i]), 2))
            breakdown.append({
                'waste_type': waste_type,
                'predicted_kg': pred_kg
            })
            total_kg += pred_kg
        
        return {
            'user_id': user_id,
            'area': area,
            'prediction_date': prediction_date.strftime('%Y-%m-%d'),
            'predicted_waste_kg': round(total_kg, 2),
            'waste_type_breakdown': breakdown,
            'model': f'PerTypeRF' if self.use_per_type else f'MultiOutput{self.model_type.upper()}',
            'horizon': 'next_day'
        }
    
    def predict_day_after_next(self, db: Session, user_id: str, prediction_date: date = None) -> Dict[str, Any]:
        if prediction_date is None:
            prediction_date = date.today() + timedelta(days=1)
        
        next_date = prediction_date + timedelta(days=1)
        X_trans = self._construct_features(db, user_id, next_date)
        
        if self.use_per_type and self.per_type_model:
            predictions = []
            for target in PER_TYPE_TARGETS:
                model = self.per_type_model[target]
                if hasattr(model, 'classifier'):
                    pred = model.predict(X_trans)
                else:
                    pred = model.predict(X_trans)
                predictions.append(pred[0] if len(pred) > 0 else 0.0)
            predictions = np.array(predictions)
        else:
            predictions = self.multi_model.predict(X_trans)[0]
        
        user = db.query(User).filter(User.id == user_id).first()
        area = user.area if user else 'Unknown'
        
        breakdown = []
        total_kg = 0.0
        for i, waste_type in enumerate(WASTE_TYPES):
            pred_kg = max(0.0, round(float(predictions[i]), 2))
            breakdown.append({
                'waste_type': waste_type,
                'predicted_kg': pred_kg
            })
            total_kg += pred_kg
        
        return {
            'user_id': user_id,
            'area': area,
            'prediction_date': next_date.strftime('%Y-%m-%d'),
            'predicted_waste_kg': round(total_kg, 2),
            'waste_type_breakdown': breakdown,
            'model': f'PerTypeRF' if self.use_per_type else f'MultiOutput{self.model_type.upper()}',
            'horizon': 'day_after_next'
        }


# Singleton instances
_db_rf_predictor: Optional[DatabaseWastePredictor] = None
_db_xgb_predictor: Optional[DatabaseWastePredictor] = None


def get_db_rf_predictor() -> DatabaseWastePredictor:
    global _db_rf_predictor
    if _db_rf_predictor is None:
        _db_rf_predictor = DatabaseWastePredictor(model_type='rf', use_per_type=True)
    return _db_rf_predictor


def get_db_xgb_predictor() -> DatabaseWastePredictor:
    global _db_xgb_predictor
    if _db_xgb_predictor is None:
        _db_xgb_predictor = DatabaseWastePredictor(model_type='xgb', use_per_type=False)
    return _db_xgb_predictor
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import timedelta
from typing import Optional, Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

from app.core.config import settings
from app.services.weather_service import get_weather_features
from app.services.calendar_service import get_calendar_features


WASTE_TYPES = ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']

# Model paths
OBJ1_MODEL_PATH = settings.ML_MODELS_PATH / 'random_forest_model.joblib'
OBJ1_METADATA_PATH = settings.ML_FEATURES_PATH / 'feature_metadata.json'
OBJ1_DATA_PATH = settings.ML_FEATURES_PATH / 'submissions_features.parquet'

MULTI_RF_PATH = settings.ML_MODELS_PATH / 'multi_waste_rf_model.joblib'
MULTI_XGB_PATH = settings.ML_MODELS_PATH / 'multi_waste_xgb_model.joblib'
MULTI_METADATA_PATH = settings.ML_FEATURES_PATH / 'feature_metadata.json'
MULTI_DATA_PATH = settings.ML_FEATURES_PATH / 'submissions_features.parquet'


def _check_model_files_exist() -> bool:
    """Check if all required model files exist."""
    required_files = [
        OBJ1_MODEL_PATH, OBJ1_METADATA_PATH, OBJ1_DATA_PATH,
        MULTI_RF_PATH, MULTI_XGB_PATH, MULTI_METADATA_PATH, MULTI_DATA_PATH
    ]
    return all(f.exists() for f in required_files)


class WastePredictor:
    """Local inference pipeline for Objective 1: next-day total waste prediction."""
    
    def __init__(self):
        self.model = None
        self.metadata = None
        self.feature_names = None
        self.categorical_features = None
        self.history_df = None
        self._load_model()
        self._load_metadata()
        self._load_history()
    
    def _load_model(self):
        try:
            self.model = joblib.load(OBJ1_MODEL_PATH)
        except FileNotFoundError:
            raise RuntimeError(
                f"ML model file not found: {OBJ1_MODEL_PATH}. "
                f"Please ensure model files are placed in {settings.ML_MODELS_PATH} "
                f"and feature files in {settings.ML_FEATURES_PATH}"
            )
    
    def _load_metadata(self):
        try:
            with open(OBJ1_METADATA_PATH) as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(
                f"Feature metadata file not found: {OBJ1_METADATA_PATH}. "
                f"Please ensure feature files are placed in {settings.ML_FEATURES_PATH}"
            )
        self.feature_names = self.metadata['feature_names']
        self.categorical_features = self.metadata['static_categorical_features'] + \
                                    self.metadata['calendar_features'][3:5]
    
    def _load_history(self):
        try:
            self.history_df = pd.read_parquet(OBJ1_DATA_PATH)
        except FileNotFoundError:
            raise RuntimeError(
                f"Training data file not found: {OBJ1_DATA_PATH}. "
                f"Please ensure feature files are placed in {settings.ML_FEATURES_PATH}"
            )
        self.history_df['submission_date'] = pd.to_datetime(self.history_df['submission_date'])
    
    def _get_user_history(self, user_id: str, cutoff_date: pd.Timestamp, 
                          max_lag_days: int = 7) -> pd.DataFrame:
        user_hist = self.history_df[
            (self.history_df['user_id'] == user_id) & 
            (self.history_df['submission_date'] <= cutoff_date)
        ].sort_values('submission_date')
        return user_hist
    
    def _construct_features(self, user_id: str, prediction_date: pd.Timestamp) -> pd.DataFrame:
        user_records = self.history_df[self.history_df['user_id'] == user_id]
        if len(user_records) == 0:
            raise ValueError(f"User {user_id} not found in history")
        
        latest = user_records.iloc[-1]
        area = latest['area']
        account_type = latest['account_type']
        
        cutoff_date = prediction_date - timedelta(days=1)
        hist = self._get_user_history(user_id, cutoff_date)
        
        if len(hist) == 0:
            raise ValueError(f"No history for user {user_id} before {prediction_date.date()}")
        
        last_record = hist.iloc[-1]
        
        pred_day_of_week = prediction_date.dayofweek
        pred_month = prediction_date.month
        pred_season = self._get_season(pred_month)
        pred_day_type = self._get_day_type(prediction_date)
        pred_is_weekend = pred_day_of_week >= 5
        
        # Use real calendar service instead of hardcoded values
        pred_is_holiday, pred_is_festival, pred_festival_intensity = get_calendar_features(
            prediction_date.date()
        )
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Calendar for {prediction_date.date()}: is_holiday={pred_is_holiday}, "
                    f"is_festival={pred_is_festival}, festival_intensity={pred_festival_intensity}")
        
        # Use real weather service instead of stale historical data
        temp_max_c, rainfall_mm, humidity_pct = get_weather_features(
            area, prediction_date.date()
        )
        logger.info(f"Weather for {area} on {prediction_date.date()}: temp={temp_max_c}, rain={rainfall_mm}, humidity={humidity_pct}")
        
        people_present = int(last_record['people_present'])
        family_members = float(last_record['family_members'])
        avg_customers_per_day = float(last_record['avg_customers_per_day'])
        employee_count = float(last_record['employee_count'])
        
        waste_history = hist['total_waste_kg'].values
        
        lag_1d = waste_history[-1] if len(waste_history) >= 1 else np.nan
        lag_2d = waste_history[-2] if len(waste_history) >= 2 else np.nan
        lag_3d = waste_history[-3] if len(waste_history) >= 3 else np.nan
        lag_7d = waste_history[-7] if len(waste_history) >= 7 else np.nan
        
        if len(waste_history) >= 1:
            roll_mean_3d = np.mean(waste_history[-3:]) if len(waste_history) >= 3 else np.mean(waste_history)
            roll_std_3d = np.std(waste_history[-3:], ddof=1) if len(waste_history) >= 3 else 0.0
            roll_mean_7d = np.mean(waste_history[-7:]) if len(waste_history) >= 7 else np.mean(waste_history)
            roll_std_7d = np.std(waste_history[-7:], ddof=1) if len(waste_history) >= 7 else 0.0
        else:
            roll_mean_3d = roll_std_3d = roll_mean_7d = roll_std_7d = np.nan
        
        dry_kg_lag_1d = last_record['dry_kg']
        wet_kg_lag_1d = last_record['wet_kg']
        plastic_kg_lag_1d = last_record['plastic_kg']
        glass_kg_lag_1d = last_record['glass_kg']
        medical_kg_lag_1d = last_record['medical_kg']
        
        features = {
            'area': area,
            'account_type': account_type,
            'day_of_week': pred_day_of_week,
            'month': pred_month,
            'season': pred_season,
            'day_type': pred_day_type,
            'is_weekend': pred_is_weekend,
            'is_holiday': pred_is_holiday,
            'is_festival': pred_is_festival,
            'festival_intensity': pred_festival_intensity,
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
            'dry_kg_lag_1d': dry_kg_lag_1d,
            'wet_kg_lag_1d': wet_kg_lag_1d,
            'plastic_kg_lag_1d': plastic_kg_lag_1d,
            'glass_kg_lag_1d': glass_kg_lag_1d,
            'medical_kg_lag_1d': medical_kg_lag_1d,
        }
        
        X = pd.DataFrame([features], columns=self.feature_names)
        return X
    
    def _get_season(self, month: int) -> str:
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        else:
            return 'spring'
    
    def _get_day_type(self, date: pd.Timestamp) -> str:
        if date.dayofweek >= 5:
            return 'weekend'
        return 'normal_day'
    
    def _is_holiday(self, date: pd.Timestamp, hist: pd.DataFrame) -> bool:
        return False
    
    def _is_festival(self, date: pd.Timestamp, hist: pd.DataFrame) -> bool:
        return False
    
    def _get_festival_intensity(self, date: pd.Timestamp, hist: pd.DataFrame) -> float:
        return 0.0
    
    def predict_next_day(self, user_id: str, prediction_date: pd.Timestamp) -> Dict[str, Any]:
        X = self._construct_features(user_id, prediction_date)
        prediction = self.model.predict(X)[0]
        
        user_records = self.history_df[self.history_df['user_id'] == user_id]
        area = user_records.iloc[-1]['area'] if len(user_records) > 0 else 'Unknown'
        
        return {
            'user_id': user_id,
            'area': area,
            'prediction_date': prediction_date.strftime('%Y-%m-%d'),
            'predicted_waste_kg': round(float(prediction), 2),
            'model': 'RandomForest',
            'horizon': 'next_day'
        }
    
    def predict_day_after_next(self, user_id: str, prediction_date: pd.Timestamp) -> Dict[str, Any]:
        next_day_result = self.predict_next_day(user_id, prediction_date)
        next_date = prediction_date + timedelta(days=1)
        X = self._construct_features(user_id, next_date)
        prediction = self.model.predict(X)[0]
        area = next_day_result['area']
        
        return {
            'user_id': user_id,
            'area': area,
            'prediction_date': next_date.strftime('%Y-%m-%d'),
            'predicted_waste_kg': round(float(prediction), 2),
            'model': 'RandomForest',
            'horizon': 'day_after_next'
        }


class MultiWastePredictor:
    """Local inference pipeline for Phase 3B: next-day waste-type prediction."""
    
    def __init__(self, model_type: str = 'rf'):
        self.model_type = model_type.lower()
        self.model = None
        self.metadata = None
        self.feature_names = None
        self.per_type_targets = None
        self.history_df = None
        self._load_model()
        self._load_metadata()
        self._load_history()
    
    def _load_model(self):
        if self.model_type == 'rf':
            model_path = MULTI_RF_PATH
        elif self.model_type == 'xgb':
            model_path = MULTI_XGB_PATH
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}. Use 'rf' or 'xgb'.")
        
        try:
            self.model = joblib.load(model_path)
        except FileNotFoundError:
            raise RuntimeError(
                f"ML model file not found: {model_path}. "
                f"Please ensure model files are placed in {settings.ML_MODELS_PATH}"
            )
    
    def _load_metadata(self):
        try:
            with open(MULTI_METADATA_PATH) as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(
                f"Feature metadata file not found: {MULTI_METADATA_PATH}. "
                f"Please ensure feature files are placed in {settings.ML_FEATURES_PATH}"
            )
        self.feature_names = self.metadata['feature_names']
        self.per_type_targets = self.metadata.get('per_type_targets', [
            'next_day_wet_kg', 'next_day_dry_kg', 'next_day_plastic_kg',
            'next_day_glass_kg', 'next_day_metal_kg', 'next_day_medical_kg'
        ])
    
    def _load_history(self):
        try:
            self.history_df = pd.read_parquet(MULTI_DATA_PATH)
        except FileNotFoundError:
            raise RuntimeError(
                f"Training data file not found: {MULTI_DATA_PATH}. "
                f"Please ensure feature files are placed in {settings.ML_FEATURES_PATH}"
            )
        self.history_df['submission_date'] = pd.to_datetime(self.history_df['submission_date'])
    
    def _get_user_history(self, user_id: str, cutoff_date: pd.Timestamp, 
                          max_lag_days: int = 7) -> pd.DataFrame:
        user_hist = self.history_df[
            (self.history_df['user_id'] == user_id) & 
            (self.history_df['submission_date'] <= cutoff_date)
        ].sort_values('submission_date')
        return user_hist
    
    def _construct_features(self, user_id: str, prediction_date: pd.Timestamp) -> pd.DataFrame:
        user_records = self.history_df[self.history_df['user_id'] == user_id]
        if len(user_records) == 0:
            raise ValueError(f"User {user_id} not found in history")
        
        latest = user_records.iloc[-1]
        area = latest['area']
        account_type = latest['account_type']
        
        cutoff_date = prediction_date - timedelta(days=1)
        hist = self._get_user_history(user_id, cutoff_date)
        
        if len(hist) == 0:
            raise ValueError(f"No history for user {user_id} before {prediction_date.date()}")
        
        last_record = hist.iloc[-1]
        
        pred_day_of_week = prediction_date.dayofweek
        pred_month = prediction_date.month
        pred_season = self._get_season(pred_month)
        pred_day_type = self._get_day_type(prediction_date)
        pred_is_weekend = pred_day_of_week >= 5
        
        # Use real calendar service instead of hardcoded values
        pred_is_holiday, pred_is_festival, pred_festival_intensity = get_calendar_features(
            prediction_date.date()
        )
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Calendar for {prediction_date.date()}: is_holiday={pred_is_holiday}, "
                    f"is_festival={pred_is_festival}, festival_intensity={pred_festival_intensity}")
        
        # Use real weather service instead of stale historical data
        temp_max_c, rainfall_mm, humidity_pct = get_weather_features(
            area, prediction_date.date()
        )
        logger.info(f"Weather for {area} on {prediction_date.date()}: temp={temp_max_c}, rain={rainfall_mm}, humidity={humidity_pct}")
        
        people_present = int(last_record['people_present'])
        family_members = float(last_record['family_members'])
        avg_customers_per_day = float(last_record['avg_customers_per_day'])
        employee_count = float(last_record['employee_count'])
        
        waste_history = hist['total_waste_kg'].values
        
        lag_1d = waste_history[-1] if len(waste_history) >= 1 else np.nan
        lag_2d = waste_history[-2] if len(waste_history) >= 2 else np.nan
        lag_3d = waste_history[-3] if len(waste_history) >= 3 else np.nan
        lag_7d = waste_history[-7] if len(waste_history) >= 7 else np.nan
        
        if len(waste_history) >= 1:
            roll_mean_3d = np.mean(waste_history[-3:]) if len(waste_history) >= 3 else np.mean(waste_history)
            roll_std_3d = np.std(waste_history[-3:], ddof=1) if len(waste_history) >= 3 else 0.0
            roll_mean_7d = np.mean(waste_history[-7:]) if len(waste_history) >= 7 else np.mean(waste_history)
            roll_std_7d = np.std(waste_history[-7:], ddof=1) if len(waste_history) >= 7 else 0.0
        else:
            roll_mean_3d = roll_std_3d = roll_mean_7d = roll_std_7d = np.nan
        
        dry_kg_lag_1d = last_record['dry_kg']
        wet_kg_lag_1d = last_record['wet_kg']
        plastic_kg_lag_1d = last_record['plastic_kg']
        glass_kg_lag_1d = last_record['glass_kg']
        metal_kg_lag_1d = last_record['metal_kg']
        medical_kg_lag_1d = last_record['medical_kg']
        
        features = {
            'area': area,
            'account_type': account_type,
            'day_of_week': pred_day_of_week,
            'month': pred_month,
            'season': pred_season,
            'day_type': pred_day_type,
            'is_weekend': pred_is_weekend,
            'is_holiday': pred_is_holiday,
            'is_festival': pred_is_festival,
            'festival_intensity': pred_festival_intensity,
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
            'dry_kg_lag_1d': dry_kg_lag_1d,
            'wet_kg_lag_1d': wet_kg_lag_1d,
            'plastic_kg_lag_1d': plastic_kg_lag_1d,
            'glass_kg_lag_1d': glass_kg_lag_1d,
            'metal_kg_lag_1d': metal_kg_lag_1d,
            'medical_kg_lag_1d': medical_kg_lag_1d,
        }
        
        X = pd.DataFrame([features], columns=self.feature_names)
        return X
    
    def _get_season(self, month: int) -> str:
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        else:
            return 'spring'
    
    def _get_day_type(self, date: pd.Timestamp) -> str:
        if date.dayofweek >= 5:
            return 'weekend'
        return 'normal_day'
    
    def _is_holiday(self, date: pd.Timestamp, hist: pd.DataFrame) -> bool:
        return False
    
    def _is_festival(self, date: pd.Timestamp, hist: pd.DataFrame) -> bool:
        return False
    
    def _get_festival_intensity(self, date: pd.Timestamp, hist: pd.DataFrame) -> float:
        return 0.0
    
    def predict_next_day(self, user_id: str, prediction_date: pd.Timestamp) -> Dict[str, Any]:
        X = self._construct_features(user_id, prediction_date)
        predictions = self.model.predict(X)[0]
        
        user_records = self.history_df[self.history_df['user_id'] == user_id]
        area = user_records.iloc[-1]['area'] if len(user_records) > 0 else 'Unknown'
        
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
            'model': f'MultiOutput{self.model_type.upper()}',
            'horizon': 'next_day'
        }
    
    def predict_day_after_next(self, user_id: str, prediction_date: pd.Timestamp) -> Dict[str, Any]:
        next_date = prediction_date + timedelta(days=1)
        X = self._construct_features(user_id, next_date)
        predictions = self.model.predict(X)[0]
        
        user_records = self.history_df[self.history_df['user_id'] == user_id]
        area = user_records.iloc[-1]['area'] if len(user_records) > 0 else 'Unknown'
        
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
            'model': f'MultiOutput{self.model_type.upper()}',
            'horizon': 'day_after_next'
        }


# Singleton instances
_obj1_predictor: Optional[WastePredictor] = None
_multi_rf_predictor: Optional[MultiWastePredictor] = None
_multi_xgb_predictor: Optional[MultiWastePredictor] = None


def get_obj1_predictor() -> WastePredictor:
    global _obj1_predictor
    if _obj1_predictor is None:
        _obj1_predictor = WastePredictor()
    return _obj1_predictor


def get_multi_rf_predictor() -> MultiWastePredictor:
    global _multi_rf_predictor
    if _multi_rf_predictor is None:
        _multi_rf_predictor = MultiWastePredictor(model_type='rf')
    return _multi_rf_predictor


def get_multi_xgb_predictor() -> MultiWastePredictor:
    global _multi_xgb_predictor
    if _multi_xgb_predictor is None:
        _multi_xgb_predictor = MultiWastePredictor(model_type='xgb')
    return _multi_xgb_predictor
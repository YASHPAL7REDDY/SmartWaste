import sys
sys.path.insert(0, '.')
import joblib
from pathlib import Path
from MLproject.ml.preprocessing.pipeline import SmartWastePreprocessor, PreprocessingConfig
import pandas as pd

df = pd.read_parquet('MLproject/data/features/submissions_features.parquet')
train_df = df[df['submission_date'] < '2024-09-01'].copy()

target_cols = [f'next_day_{wt}_kg' for wt in ['wet', 'dry', 'plastic', 'glass', 'metal', 'medical']] + ['next_day_total_waste_kg']
feature_cols = [c for c in train_df.columns if c not in target_cols + ['submission_id', 'user_id', 'submission_date', 'submission_time', 'collection_status', 'waste_types_sum', 'area', 'account_type']]

X_train = train_df[feature_cols].copy()
for col in X_train.columns:
    if pd.api.types.is_datetime64_any_dtype(X_train[col]):
        X_train[col] = X_train[col].astype('int64')

config = PreprocessingConfig()
preprocessor = SmartWastePreprocessor(config)
preprocessor.fit(X_train)

models_dir = Path('MLproject/ml/models/improved')
models_dir.mkdir(parents=True, exist_ok=True)
preprocessor.save(models_dir / 'preprocessor.joblib')
print('Preprocessor saved!')

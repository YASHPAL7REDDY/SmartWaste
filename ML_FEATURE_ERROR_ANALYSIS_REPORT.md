# ML_FEATURE_ERROR_ANALYSIS_REPORT

*Generated: 2026-08-30*

---

## 1. Executive Summary

This report analyzes the SmartWaste ML pipeline to identify the main causes of prediction errors before any model retraining.

- **Real-world evaluation samples**: 13 (across all waste types)
- **Offline test metrics available**: False
- **Overall drift status**: HIGH_DRIFT
- **Reference data source**: database_history_proxy
- **Model health**: WARNING - High data drift detected; real-world evaluation needed to assess impact

## 2. Current Model Architecture

### Deployed Models
| Model | Type | Status |
|-------|------|--------|
| PerTypeRF | Per-Type Random Forest (Two-Stage) | **PRODUCTION** |
| XGB_PerType | Per-Type XGBoost (Two-Stage) | Available (offline only) |
| RF_Multi | Multi-Output Random Forest | Available (offline only) |
| XGB_Multi | Multi-Output XGBoost | Available (offline only) |

### Feature Engineering

The `DatabaseWastePredictor._construct_features()` builds features from database records:

**Historical waste** (8 features):
- `total_waste_kg_lag_1d`
- `total_waste_kg_lag_2d`
- `total_waste_kg_lag_3d`
- `total_waste_kg_lag_7d`
- `total_waste_kg_roll_mean_3d`
- `total_waste_kg_roll_std_3d`
- `total_waste_kg_roll_mean_7d`
- `total_waste_kg_roll_std_7d`

**Waste composition (lag_1d)** (6 features):
- `dry_kg_lag_1d`
- `wet_kg_lag_1d`
- `plastic_kg_lag_1d`
- `glass_kg_lag_1d`
- `metal_kg_lag_1d`
- `medical_kg_lag_1d`

**Temporal/Calendar** (8 features):
- `day_of_week`
- `month`
- `season`
- `day_type`
- `is_weekend`
- `is_holiday`
- `is_festival`
- `festival_intensity`

**Weather/Environment** (3 features):
- `temp_max_c`
- `rainfall_mm`
- `humidity_pct`

**User behavior / Account info** (4 features):
- `people_present`
- `family_members`
- `avg_customers_per_day`
- `employee_count`

**Area / Account (Categorical)** (2 features):
- `area`
- `account_type`

**Total features**: 31

## 3. Feature Importance by Model

> **NOTE**: The actual trained model files (.joblib) are not present in this repository. 
Feature importance cannot be directly extracted from the models. 
The models are loaded from `MLproject/ml/models/improved/` which is an external path.

### Expected Feature Importance Patterns (based on architecture)

**PerTypeRF (Two-Stage)**:
- Stage 1 (Classifier): Features distinguishing zero vs non-zero waste
- Stage 2 (Regressor): Features predicting non-zero amounts
- Likely important: lag features, rolling means, waste composition lags

**RF_Multi / XGB_Multi (Multi-Output)**:
- Single model predicting all waste types simultaneously
- Shared feature importance across all targets
- Historical waste features likely dominant

## 4. Feature Importance by Waste Type (Expected)

Based on feature engineering and domain knowledge:

**TOTAL**:
  1. `total_waste_kg_lag_1d`
  2. `total_waste_kg_roll_mean_7d`
  3. `total_waste_kg_roll_mean_3d`
  4. `area`
  5. `account_type`

**WET**:
  1. `wet_kg_lag_1d`
  2. `total_waste_kg_lag_1d`
  3. `total_waste_kg_roll_mean_7d`
  4. `people_present`
  5. `family_members`

**DRY**:
  1. `dry_kg_lag_1d`
  2. `total_waste_kg_lag_1d`
  3. `avg_customers_per_day`
  4. `area`
  5. `account_type`

**PLASTIC**:
  1. `plastic_kg_lag_1d`
  2. `avg_customers_per_day`
  3. `area`
  4. `account_type`

**GLASS**:
  1. `glass_kg_lag_1d`
  2. `area`
  3. `account_type`

**METAL**:
  1. `metal_kg_lag_1d`
  2. `area`
  3. `employee_count`

**MEDICAL**:
  1. `medical_kg_lag_1d`
  2. `area`
  3. `account_type`

## 5. Feature Group Analysis

| Feature Group | # Features | Notes |
|---------------|------------|-------|
| Historical waste | 8 | Historical waste patterns |
| Waste composition (lag_1d) | 6 | Historical waste patterns |
| Temporal/Calendar | 8 | Strong seasonality signals |
| Weather/Environment | 3 | Hardcoded defaults (not real data) |
| User behavior / Account info | 4 |  |
| Area / Account (Categorical) | 2 |  |

## 6. Offline Error Analysis (Chronological Hold-Out Test)

## 7. Real-World Error Analysis

*Using existing PredictionAccuracy records from matched prediction-actual pairs*

| Waste Type | Samples | MAE | RMSE | R² | MAPE | Bias | Reliability |
|------------|---------|-----|------|-----|------|------|-------------|
| wet | 2 | 0.125 | 0.1329 | 0.8039 | 5.42 | 0.125 | INSUFFICIENT_DATA |
| dry | 2 | 0.14 | 0.1404 | N/A | 8.99 | 0.14 | INSUFFICIENT_DATA |
| plastic | 2 | 0.165 | 0.1669 | -1.785 | 14.06 | 0.165 | INSUFFICIENT_DATA |
| glass | 2 | 0.145 | 0.1551 | -1.405 | 31.54 | 0.145 | INSUFFICIENT_DATA |
| metal | 2 | 0.2 | 0.2119 | -0.9956 | 27.19 | 0.2 | INSUFFICIENT_DATA |
| medical | 2 | 0.11 | 0.1118 | N/A | 33.2 | 0.11 | INSUFFICIENT_DATA |
| total | 1 | 0.66 | 0.66 | N/A | 10.71 | 0.66 | INSUFFICIENT_DATA |

### Accuracy Within Thresholds

| Waste Type | Within ±10% | Within ±20% | Within ±30% |
|------------|-------------|-------------|-------------|
| wet | 100.0% | 100.0% | 100.0% |
| dry | 100.0% | 100.0% | 100.0% |
| plastic | 0.0% | 100.0% | 100.0% |
| glass | 0.0% | 0.0% | 0.0% |
| metal | 0.0% | 0.0% | 50.0% |
| medical | 0.0% | 0.0% | 0.0% |
| total | 0.0% | 100.0% | 100.0% |

## 8. Bias Analysis

| Waste Type | Bias (Pred - Actual) | Overpredictions | Underpredictions | Interpretation |
|------------|---------------------|-----------------|------------------|----------------|
| wet | 0.125 | 2 | 0 | Systematic OVERPREDICTION |
| dry | 0.14 | 2 | 0 | Systematic OVERPREDICTION |
| plastic | 0.165 | 2 | 0 | Systematic OVERPREDICTION |
| glass | 0.145 | 2 | 0 | Systematic OVERPREDICTION |
| metal | 0.2 | 2 | 0 | Systematic OVERPREDICTION |
| medical | 0.11 | 2 | 0 | Systematic OVERPREDICTION |
| total | 0.66 | 1 | 0 | Systematic OVERPREDICTION |

## 9. Drift vs Feature Importance

**Overall Drift Status**: HIGH_DRIFT
**Reference Source**: database_history_proxy (FIRST 90 DAYS OF DB DATA - NOT ACTUAL TRAINING DATA)

### Drift by Feature Group

| Feature Group | Max PSI | Max Mean Change% | High Drift Features |
|---------------|---------|------------------|---------------------|
| Historical waste | 0.0000 | 0.0% | 0 |
| Waste composition (lag_1d) | 0.0000 | 0.0% | 0 |
| Temporal/Calendar | 0.0000 | 0.0% | 0 |
| Weather/Environment | 0.0000 | 0.0% | 0 |
| User behavior / Account info | 0.0000 | 0.0% | 0 |
| Area / Account (Categorical) | 0.0000 | 0.0% | 0 |

### High Drift Features Detail

## 10. Weak/Redundant Features

| Feature | Issue | Severity |
|---------|-------|----------|
| metal | High zero percentage: 97.8% | HIGH |
| is_holiday | Hardcoded default value (not from real data) | MEDIUM |
| is_festival | Hardcoded default value (not from real data) | MEDIUM |
| festival_intensity | Hardcoded default value (not from real data) | MEDIUM |
| temp_max_c | Hardcoded default value (not from real data) | MEDIUM |
| rainfall_mm | Hardcoded default value (not from real data) | MEDIUM |
| humidity_pct | Hardcoded default value (not from real data) | MEDIUM |

### Defaulted Features (Not from Real Data)
- `is_holiday`: Hardcoded default value
- `is_festival`: Hardcoded default value
- `festival_intensity`: Hardcoded default value
- `temp_max_c`: Hardcoded default value
- `rainfall_mm`: Hardcoded default value
- `humidity_pct`: Hardcoded default value

## 11. Potential Data Leakage Risks

1. **Lag features computed from same day's submissions**: If a user submits multiple times per day, lag_1d could leak target info
2. **Area/account_type as categorical**: High cardinality areas may cause overfitting
3. **Weather features hardcoded**: No real weather data - model learns spurious correlations
4. **Festival/holiday features all False**: No variation, useless for model
5. **Rolling stats with small windows**: 3-day window with sparse data may leak recent target

## 12. Main Causes of Prediction Error

1. **Zero-inflated targets**: Many waste types (glass, metal, medical) are frequently zero → two-stage model helps but classifier errors propagate
2. **Sparse historical data**: Users with < 7 submissions have unreliable rolling statistics
3. **Weather defaults**: No real weather data removes a potentially strong predictor
4. **Categorical high cardinality**: 15+ areas, some with few samples → poor generalization
5. **Temporal leakage risk**: Lag features computed from all submissions, not strictly temporal
6. **Small real-world evaluation set**: Only ~13 total accuracy records → cannot reliably validate model

## 13. Recommended Improvements

### Data Collection
1. **Integrate real weather API** - Replace hardcoded defaults with actual weather data
2. **Add festival/holiday calendar** - Real holiday data for the region
3. **Collect more matched prediction-actual pairs** - Need 50+ per waste type for STRONG_EVALUATION

### Feature Engineering
4. **Add area-level aggregates** - Historical waste per area (not just per user)
5. **Add user embedding / frequency encoding** - For high-cardinality categorical features
6. **Stricter temporal splits** - Ensure lag features only use strictly prior data
7. **Feature selection** - Remove defaulted/hardcoded features

### Modeling
8. **Evaluate simpler baselines** - Mean/median per area/account_type as sanity check
9. **Calibrate two-stage models** - Ensure classifier threshold is optimal
10. **Test XGBoost with proper tuning** - Current XGB may not be optimal

## 14. Features to Keep
- `total_waste_kg_lag_1d`
- `total_waste_kg_lag_7d`
- `total_waste_kg_roll_mean_3d`
- `total_waste_kg_roll_mean_7d`
- `wet_kg_lag_1d`
- `dry_kg_lag_1d`
- `plastic_kg_lag_1d`
- `area`
- `account_type`
- `day_of_week`
- `month`
- `is_weekend`
- `family_members`
- `avg_customers_per_day`

## 15. Features to Remove / Test for Removal
- `is_holiday`
- `is_festival`
- `festival_intensity`
- `temp_max_c`
- `rainfall_mm`
- `humidity_pct`
- `total_waste_kg_lag_2d`
- `total_waste_kg_lag_3d`
- `total_waste_kg_roll_std_3d`
- `total_waste_kg_roll_std_7d`
- `employee_count`

## 16. Features That Need Better Data
- **Weather**: Need real weather API integration
- **Festival/Holiday**: Need regional calendar data
- **Area-level stats**: Need area aggregates, not just user-level
- **Temporal**: Need proper holiday calendar for the region

## 17. Recommended Next Training Strategy

### Phase 1: Data Quality (No Retraining)
1. Fix weather/festival features with real data
2. Collect 50+ matched prediction-actual pairs per waste type
3. Validate temporal splits are leak-free

### Phase 2: Feature Engineering
4. Add area-level aggregate features
5. Remove/consolidate redundant features
6. Test frequency/target encoding for categorical features

### Phase 3: Model Retraining
7. Retrain PerTypeRF with cleaned features
8. Compare against XGBoost with hyperparameter tuning
9. Test single-model multi-output vs per-type approach
10. Implement proper cross-validation with temporal splits

---
## PRIORITIZED ACTION PLAN

### Priority 1 (Immediate - No Retraining Required)
1. **Fix weather/festival features** - Replace hardcoded defaults with real API data
   - Expected benefit: Removes noise features, may improve R² by 0.02-0.05
   - Cost: Low (API integration)
   - Risk: Low
   - Retraining required: NO (features are inputs, model can use as-is)
   - Additional data: YES (weather API)

2. **Collect matched prediction-actual pairs** - Target 50+ per waste type
   - Expected benefit: Enables reliable model evaluation (STRONG_EVALUATION)
   - Cost: Operational (collector workflow)
   - Risk: Low
   - Retraining required: NO
   - Additional data: YES (real-world collections)

### Priority 2 (Before Next Retraining)
3. **Remove constant/hardcoded features** - is_holiday, is_festival, festival_intensity, temp_max_c, rainfall_mm, humidity_pct
   - Expected benefit: Cleaner feature space, faster training
   - Cost: Low (code change)
   - Risk: Very Low
   - Retraining required: YES
   - Additional data: NO

4. **Add area-level aggregate features**
   - Expected benefit: Captures area-level patterns, helps cold-start users
   - Cost: Medium (feature engineering)
   - Risk: Low
   - Retraining required: YES
   - Additional data: NO (computed from existing DB)

5. **Stricter temporal validation** - Ensure no leakage in lag/rolling features
   - Expected benefit: More realistic performance estimates
   - Cost: Medium (validation logic)
   - Risk: Low
   - Retraining required: YES (for proper evaluation)
   - Additional data: NO

### Priority 3 (Model Improvement)
6. **Retrain PerTypeRF with cleaned features** + proper temporal CV
   - Expected benefit: 5-15% error reduction if features improved
   - Cost: Medium (training compute)
   - Risk: Medium (model change)
   - Retraining required: YES
   - Additional data: NO (existing DB)

7. **Compare per-type vs multi-output architectures**
   - Expected benefit: Identify best architecture for production
   - Cost: Medium (training both)
   - Risk: Low
   - Retraining required: YES
   - Additional data: NO

---
## CURRENT METRICS SUMMARY

### Offline Test Metrics (RF_Multi)

### Real-World Metrics
- **wet**: n=2, MAE=0.1250, RMSE=0.1329, R²=0.8039, Bias=0.1250, Reliability=INSUFFICIENT_DATA
- **dry**: n=2, MAE=0.1400, RMSE=0.1404, R²=0.0000, Bias=0.1400, Reliability=INSUFFICIENT_DATA
- **plastic**: n=2, MAE=0.1650, RMSE=0.1669, R²=-1.7850, Bias=0.1650, Reliability=INSUFFICIENT_DATA
- **glass**: n=2, MAE=0.1450, RMSE=0.1551, R²=-1.4050, Bias=0.1450, Reliability=INSUFFICIENT_DATA
- **metal**: n=2, MAE=0.2000, RMSE=0.2119, R²=-0.9956, Bias=0.2000, Reliability=INSUFFICIENT_DATA
- **medical**: n=2, MAE=0.1100, RMSE=0.1118, R²=0.0000, Bias=0.1100, Reliability=INSUFFICIENT_DATA
- **total**: n=1, MAE=0.6600, RMSE=0.6600, R²=N/A, Bias=0.6600, Reliability=INSUFFICIENT_DATA

---
## TOP 20 IMPORTANT FEATURES (Expected from Architecture)
1. `total_waste_kg_lag_1d`
2. `total_waste_kg_roll_mean_7d`
3. `total_waste_kg_roll_mean_3d`
4. `wet_kg_lag_1d`
5. `dry_kg_lag_1d`
6. `plastic_kg_lag_1d`
7. `area`
8. `account_type`
9. `day_of_week`
10. `month`
11. `is_weekend`
12. `family_members`
13. `avg_customers_per_day`
14. `total_waste_kg_lag_7d`
15. `glass_kg_lag_1d`
16. `metal_kg_lag_1d`
17. `medical_kg_lag_1d`
18. `people_present`
19. `employee_count`

---
## TOP ERROR SOURCES
1. **Zero-inflated targets** (glass, metal, medical) - classifier errors in two-stage model
2. **Sparse user history** - unreliable rolling statistics for new/infrequent users
3. **Hardcoded weather/festival features** - noise instead of signal
4. **High-cardinality categoricals** - area (15+ values) with imbalanced samples
5. **Insufficient real-world validation** - only 13 total matched pairs
6. **Potential temporal leakage** in lag/rolling feature computation

---
## RECOMMENDED NEXT STEP

**Start with Priority 1**: Fix weather/festival features with real data API integration. 
This is a pure feature engineering change that doesn't require model retraining 
and can be deployed immediately. In parallel, ensure the collector workflow 
generates matched prediction-actual pairs to build up the real-world evaluation set.


Once 50+ real-world samples per waste type are collected and weather features 
are live, proceed with Priority 2 (feature cleanup) and Priority 3 (retraining).
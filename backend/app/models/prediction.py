from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, Date, ForeignKey
from sqlalchemy.sql import func
from app.database.session import Base


class WastePrediction(Base):
    __tablename__ = "waste_predictions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    area = Column(String, nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    predicted_waste_kg = Column(Float, nullable=False)
    model = Column(String, nullable=True)
    horizon = Column(String, nullable=True)
    wet_predicted_kg = Column(Float, nullable=True)
    dry_predicted_kg = Column(Float, nullable=True)
    plastic_predicted_kg = Column(Float, nullable=True)
    glass_predicted_kg = Column(Float, nullable=True)
    metal_predicted_kg = Column(Float, nullable=True)
    medical_predicted_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AreaPrediction(Base):
    __tablename__ = "area_predictions"
    
    id = Column(String, primary_key=True, index=True)
    area = Column(String, nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    predicted_waste_kg = Column(Float, nullable=False)
    horizon = Column(String, nullable=True)
    contributing_users = Column(Integer, nullable=True)
    model = Column(String, nullable=True)
    wet_predicted_kg = Column(Float, nullable=True)
    dry_predicted_kg = Column(Float, nullable=True)
    plastic_predicted_kg = Column(Float, nullable=True)
    glass_predicted_kg = Column(Float, nullable=True)
    metal_predicted_kg = Column(Float, nullable=True)
    medical_predicted_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OverflowRiskPrediction(Base):
    __tablename__ = "overflow_risk_predictions"
    
    id = Column(String, primary_key=True, index=True)
    area = Column(String, nullable=False, index=True)
    city = Column(String, nullable=True)
    prediction_date = Column(Date, nullable=False, index=True)
    horizon = Column(String, nullable=True)
    model = Column(String, nullable=True)
    predicted_total_waste_kg = Column(Float, nullable=True)
    wet_predicted_kg = Column(Float, nullable=True)
    dry_predicted_kg = Column(Float, nullable=True)
    plastic_predicted_kg = Column(Float, nullable=True)
    glass_predicted_kg = Column(Float, nullable=True)
    metal_predicted_kg = Column(Float, nullable=True)
    medical_predicted_kg = Column(Float, nullable=True)
    capacity_proxy_kg = Column(Float, nullable=True)
    capacity_source = Column(String, nullable=True)
    capacity_utilization = Column(Float, nullable=True)
    delay_days = Column(Integer, nullable=True)
    trend_slope = Column(Float, nullable=True)
    hotspot_flag = Column(Boolean, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    wet_risk_score = Column(Float, nullable=True)
    dry_risk_score = Column(Float, nullable=True)
    plastic_risk_score = Column(Float, nullable=True)
    glass_risk_score = Column(Float, nullable=True)
    metal_risk_score = Column(Float, nullable=True)
    medical_risk_score = Column(Float, nullable=True)
    contributing_users = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PredictionAccuracy(Base):
    __tablename__ = "prediction_accuracy"
    
    id = Column(String, primary_key=True, index=True)
    area = Column(String, nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    horizon = Column(String, nullable=True)
    model = Column(String, nullable=True)
    waste_type = Column(String, nullable=True)
    predicted_kg = Column(Float, nullable=True)
    actual_kg = Column(Float, nullable=True)
    absolute_error_kg = Column(Float, nullable=True)
    percentage_error = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ActualCollection(Base):
    """Record of actual waste collected by collectors."""
    __tablename__ = "actual_collections"
    
    id = Column(String, primary_key=True, index=True)
    area = Column(String, nullable=False, index=True)
    collection_date = Column(Date, nullable=False, index=True)
    collector_id = Column(String, nullable=False, index=True)
    area_collection_id = Column(String, nullable=True, index=True)
    
    # Actual collected quantities per waste type
    wet_actual_kg = Column(Float, default=0.0)
    dry_actual_kg = Column(Float, default=0.0)
    plastic_actual_kg = Column(Float, default=0.0)
    glass_actual_kg = Column(Float, default=0.0)
    metal_actual_kg = Column(Float, default=0.0)
    medical_actual_kg = Column(Float, default=0.0)
    
    # Total actual collected
    total_actual_kg = Column(Float, default=0.0)
    
    # Vehicle info
    vehicle_capacity_kg = Column(Float, nullable=True)
    remaining_capacity_kg = Column(Float, nullable=True)
    
    # Status
    is_matched = Column(Boolean, default=False)
    matched_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TrainingReferenceStats(Base):
    """Store actual training dataset feature statistics for drift detection."""
    __tablename__ = "training_reference_stats"
    
    id = Column(String, primary_key=True, index=True)
    feature_name = Column(String, nullable=False, index=True)  # e.g., 'wet', 'dry', 'area', 'account_type'
    feature_type = Column(String, nullable=False)  # 'numerical' or 'categorical'
    
    # For numerical features
    mean = Column(Float, nullable=True)
    std = Column(Float, nullable=True)
    min_val = Column(Float, nullable=True)
    max_val = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    q25 = Column(Float, nullable=True)
    q75 = Column(Float, nullable=True)
    sample_count = Column(Integer, nullable=True)
    
    # For categorical features (stored as JSON)
    category_counts = Column(Text, nullable=True)  # JSON string: {"category": count, ...}
    category_proportions = Column(Text, nullable=True)  # JSON string: {"category": proportion, ...}
    
    # Metadata
    source = Column(String, nullable=False)  # 'actual_training_data', 'database_history_proxy', 'manual_entry'
    training_period_start = Column(Date, nullable=True)
    training_period_end = Column(Date, nullable=True)
    model_version = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Unique constraint on feature_name + model_version (handled at application level)
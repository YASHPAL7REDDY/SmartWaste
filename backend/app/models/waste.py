from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, Date, Time, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base


class WasteSubmission(Base):
    __tablename__ = "waste_submissions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    submission_date = Column(Date, nullable=False, index=True)
    submission_time = Column(Time, nullable=True)
    day_of_week = Column(String, nullable=True)
    day_type = Column(String(14), nullable=True)
    month = Column(Integer, nullable=True)
    account_type_snapshot = Column(String(12), nullable=True)
    city_snapshot = Column(String, nullable=True)
    area_snapshot = Column(String, nullable=True)
    family_members_snapshot = Column(Integer, nullable=True)
    customers_snapshot = Column(Integer, nullable=True)
    people_present_snapshot = Column(Integer, nullable=True)
    total_waste_kg = Column(Float, nullable=False)
    collection_status = Column(String(9), default="pending")
    collected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    items = relationship("WasteItem", back_populates="submission", cascade="all, delete-orphan")


class WasteItem(Base):
    __tablename__ = "waste_items"
    
    id = Column(String, primary_key=True, index=True)
    submission_id = Column(String, ForeignKey("waste_submissions.id"), nullable=False, index=True)
    waste_type = Column(String(7), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    
    submission = relationship("WasteSubmission", back_populates="items")


class AreaCollection(Base):
    __tablename__ = "area_collections"
    
    id = Column(String, primary_key=True, index=True)
    area = Column(String, nullable=False, index=True)
    collector_id = Column(String, ForeignKey("collectors.id"), nullable=True, index=True)
    collection_date = Column(Date, nullable=False, index=True)
    status = Column(String(9), default="assigned")
    predicted_waste_kg = Column(Float, nullable=True)
    collected_waste_kg = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    waste_breakdown_predicted = Column(Text, nullable=True)
    facility_assignments = Column(Text, nullable=True)
    route_sequence = Column(Integer, nullable=True)
    planned_load_kg = Column(Float, nullable=True)
    waste_breakdown_collected = Column(Text, nullable=True)
    actual_sequence = Column(Integer, nullable=True)
    actual_collection_time = Column(DateTime, nullable=True)
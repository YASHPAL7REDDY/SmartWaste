from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, Date, ForeignKey
from sqlalchemy.sql import func
from app.database.session import Base


class WasteFacility(Base):
    __tablename__ = "waste_facilities"
    
    id = Column(String, primary_key=True, index=True)
    facility_name = Column(String, nullable=False)
    facility_type = Column(String(22), nullable=False)
    waste_categories = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    area_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    ward_name = Column(String, nullable=True)
    ward_number = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity_kg_per_day = Column(Float, nullable=True)
    operator_name = Column(String, nullable=True)
    status = Column(String(8), nullable=True)
    source = Column(String, nullable=True)
    source_reference = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    data_quality_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WasteGenerationZone(Base):
    __tablename__ = "waste_generation_zones"
    
    id = Column(String, primary_key=True, index=True)
    area_name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=True)
    ward_name = Column(String, nullable=True)
    ward_number = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String(18), nullable=True)
    source_date = Column(Date, nullable=True)
    source_year = Column(Integer, nullable=True)
    source_reference = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    total_waste_kg_per_day = Column(Float, nullable=True)
    household_waste_kg_per_day = Column(Float, nullable=True)
    commercial_waste_kg_per_day = Column(Float, nullable=True)
    bulk_generator_waste_kg_per_day = Column(Float, nullable=True)
    wet_waste_kg_per_day = Column(Float, nullable=True)
    dry_waste_kg_per_day = Column(Float, nullable=True)
    plastic_waste_kg_per_day = Column(Float, nullable=True)
    glass_waste_kg_per_day = Column(Float, nullable=True)
    metal_waste_kg_per_day = Column(Float, nullable=True)
    medical_waste_kg_per_day = Column(Float, nullable=True)
    data_quality_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
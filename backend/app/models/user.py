from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.database.session import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    account_type = Column(String(12), nullable=False)
    family_members = Column(Integer, nullable=True)
    restaurant_name = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    avg_customers_per_day = Column(Integer, nullable=True)
    organization_name = Column(String, nullable=True)
    organization_type = Column(String(10), nullable=True)
    city = Column(String, nullable=True)
    area = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    pincode = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_collector = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Collector(Base):
    __tablename__ = "collectors"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, unique=True)
    employee_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    vehicle_number = Column(String, nullable=True)
    assigned_areas = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    vehicle_capacity_kg = Column(Float, nullable=True)
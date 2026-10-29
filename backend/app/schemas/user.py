from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class AccountType(str, Enum):
    FAMILY = "family"
    RESTAURANT = "restaurant"
    ORGANIZATION = "organization"


class UserRole(str, Enum):
    USER = "user"
    COLLECTOR = "collector"
    ADMIN = "admin"


class WasteType(str, Enum):
    WET = "wet"
    DRY = "dry"
    PLASTIC = "plastic"
    GLASS = "glass"
    METAL = "metal"
    MEDICAL = "medical"


class UserBase(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    account_type: AccountType
    area: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None


class UserCreateFamily(UserBase):
    account_type: AccountType = AccountType.FAMILY
    family_members: int
    
    @field_validator('family_members')
    @classmethod
    def validate_family_members(cls, v):
        if v < 1:
            raise ValueError('Family members must be at least 1')
        return v


class UserCreateRestaurant(UserBase):
    account_type: AccountType = AccountType.RESTAURANT
    restaurant_name: str
    gstin: Optional[str] = None
    avg_customers_per_day: int
    
    @field_validator('avg_customers_per_day')
    @classmethod
    def validate_customers(cls, v):
        if v < 0:
            raise ValueError('Average daily customers must be non-negative')
        return v
    
    @field_validator('gstin')
    @classmethod
    def validate_gstin(cls, v):
        if v and len(v) != 15:
            raise ValueError('GSTIN must be 15 characters')
        return v


class UserCreateOrganization(UserBase):
    account_type: AccountType = AccountType.ORGANIZATION
    organization_name: str
    avg_daily_workers: int
    
    @field_validator('avg_daily_workers')
    @classmethod
    def validate_workers(cls, v):
        if v < 1:
            raise ValueError('Average daily workers must be at least 1')
        return v


UserCreate = UserCreateFamily | UserCreateRestaurant | UserCreateOrganization


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    name: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    mobile: str
    account_type: str
    area: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    family_members: Optional[int] = None
    restaurant_name: Optional[str] = None
    gstin: Optional[str] = None
    avg_customers_per_day: Optional[int] = None
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    avg_daily_workers: Optional[int] = None
    is_admin: bool
    is_collector: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: str
    name: str
    user: UserResponse


class CollectorResponse(BaseModel):
    id: str
    user_id: str
    employee_id: Optional[str] = None
    name: str
    mobile: str
    vehicle_number: Optional[str] = None
    assigned_areas: Optional[str] = None
    vehicle_capacity_kg: Optional[float] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
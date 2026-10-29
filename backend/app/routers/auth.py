from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.database.session import get_db
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse, UserRole, AccountType, RegisterResponse, CollectorResponse
from app.services.auth import authenticate_user, create_access_token, get_password_hash, verify_password, get_current_user
from app.models.user import User, Collector
from app.services.waste import get_user_profile

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterWithPassword(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str
    account_type: AccountType
    area: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    family_members: Optional[int] = None
    restaurant_name: Optional[str] = None
    gstin: Optional[str] = None
    avg_customers_per_day: Optional[int] = None
    organization_name: Optional[str] = None
    avg_daily_workers: Optional[int] = None


class CollectorLogin(BaseModel):
    email_or_mobile: str
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterWithPassword, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate based on account type
    if user_data.account_type == AccountType.FAMILY:
        if not user_data.family_members or user_data.family_members < 1:
            raise HTTPException(status_code=400, detail="Family members required for family account")
    elif user_data.account_type == AccountType.RESTAURANT:
        if not user_data.restaurant_name:
            raise HTTPException(status_code=400, detail="Restaurant name required")
        if not user_data.avg_customers_per_day or user_data.avg_customers_per_day < 0:
            raise HTTPException(status_code=400, detail="Average daily customers required")
    elif user_data.account_type == AccountType.ORGANIZATION:
        if not user_data.organization_name:
            raise HTTPException(status_code=400, detail="Organization name required")
        if not user_data.avg_daily_workers or user_data.avg_daily_workers < 1:
            raise HTTPException(status_code=400, detail="Average daily workers required")
    
    password_hash = get_password_hash(user_data.password)
    
    user = User(
        id=f"usr_{user_data.name.lower().replace(' ', '_')}_{user_data.email.split('@')[0]}",
        name=user_data.name,
        email=user_data.email,
        mobile=user_data.mobile,
        password_hash=password_hash,
        account_type=user_data.account_type.value,
        area=user_data.area,
        address=user_data.address,
        city=user_data.city,
        pincode=user_data.pincode,
        family_members=user_data.family_members,
        restaurant_name=user_data.restaurant_name,
        gstin=user_data.gstin,
        avg_customers_per_day=user_data.avg_customers_per_day,
        organization_name=user_data.organization_name,
        organization_type="ngo" if user_data.account_type == AccountType.ORGANIZATION else None,
        is_admin=False,
        is_collector=False,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token for auto-login
    access_token = create_access_token(
        data={"sub": user.id, "role": UserRole.USER.value}
    )
    
    return RegisterResponse(
        access_token=access_token,
        role=UserRole.USER,
        user_id=user.id,
        name=user.name,
        user=UserResponse.model_validate(user)
    )


@router.post("/register-with-password", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_with_password(
    name: str,
    email: str,
    mobile: str,
    password: str,
    account_type: AccountType,
    area: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    pincode: Optional[str] = None,
    family_members: Optional[int] = None,
    restaurant_name: Optional[str] = None,
    gstin: Optional[str] = None,
    avg_customers_per_day: Optional[int] = None,
    organization_name: Optional[str] = None,
    avg_daily_workers: Optional[int] = None,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate based on account type
    if account_type == AccountType.FAMILY:
        if not family_members or family_members < 1:
            raise HTTPException(status_code=400, detail="Family members required for family account")
    elif account_type == AccountType.RESTAURANT:
        if not restaurant_name:
            raise HTTPException(status_code=400, detail="Restaurant name required")
        if not avg_customers_per_day or avg_customers_per_day < 0:
            raise HTTPException(status_code=400, detail="Average daily customers required")
    elif account_type == AccountType.ORGANIZATION:
        if not organization_name:
            raise HTTPException(status_code=400, detail="Organization name required")
        if not avg_daily_workers or avg_daily_workers < 1:
            raise HTTPException(status_code=400, detail="Average daily workers required")
    
    password_hash = get_password_hash(password)
    
    user = User(
        id=f"usr_{name.lower().replace(' ', '_')}_{email.split('@')[0]}",
        name=name,
        email=email,
        mobile=mobile,
        password_hash=password_hash,
        account_type=account_type.value,
        area=area,
        address=address,
        city=city,
        pincode=pincode,
        family_members=family_members,
        restaurant_name=restaurant_name,
        gstin=gstin,
        avg_customers_per_day=avg_customers_per_day,
        organization_name=organization_name,
        organization_type="ngo" if account_type == AccountType.ORGANIZATION else None,
        is_admin=False,
        is_collector=False,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token for auto-login
    access_token = create_access_token(
        data={"sub": user.id, "role": UserRole.USER.value}
    )
    
    return RegisterResponse(
        access_token=access_token,
        role=UserRole.USER,
        user_id=user.id,
        name=user.name,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password, credentials.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "role": credentials.role.value}
    )
    
    return Token(
        access_token=access_token,
        role=credentials.role,
        user_id=user.id,
        name=user.name
    )


@router.post("/collector/login", response_model=Token)
def collector_login(credentials: CollectorLogin, db: Session = Depends(get_db)):
    # Try to find user by email or mobile
    user = db.query(User).filter(
        (User.email == credentials.email_or_mobile) | (User.mobile == credentials.email_or_mobile),
        User.is_collector == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get collector info
    collector = db.query(Collector).filter(Collector.user_id == user.id).first()
    
    access_token = create_access_token(
        data={"sub": user.id, "role": UserRole.COLLECTOR.value}
    )
    
    return Token(
        access_token=access_token,
        role=UserRole.COLLECTOR,
        user_id=user.id,
        name=user.name
    )


@router.post("/admin-login", response_model=Token)
def admin_login(credentials: AdminLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password, UserRole.ADMIN)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "role": UserRole.ADMIN.value}
    )
    
    return Token(
        access_token=access_token,
        role=UserRole.ADMIN,
        user_id=user.id,
        name=user.name
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    token = authorization.replace("Bearer ", "")
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
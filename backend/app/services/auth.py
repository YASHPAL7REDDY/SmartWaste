from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User, Collector
from app.schemas.user import UserRole, TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, role=UserRole(role))
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str, role: UserRole) -> Optional[User]:
    if role == UserRole.USER:
        user = db.query(User).filter(User.email == email, User.is_admin == False, User.is_collector == False).first()
    elif role == UserRole.COLLECTOR:
        user = db.query(User).filter(User.email == email, User.is_collector == True).first()
    elif role == UserRole.ADMIN:
        user = db.query(User).filter(User.email == email, User.is_admin == True).first()
    else:
        return None
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(db: Session, token: str) -> Optional[User]:
    token_data = decode_token(token)
    if not token_data:
        return None
    user = db.query(User).filter(User.id == token_data.user_id).first()
    return user


def get_current_collector(db: Session, token: str) -> Optional[Collector]:
    token_data = decode_token(token)
    if not token_data or token_data.role != UserRole.COLLECTOR:
        return None
    collector = db.query(Collector).filter(Collector.user_id == token_data.user_id).first()
    return collector
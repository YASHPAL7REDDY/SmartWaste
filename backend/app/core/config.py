import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartWaste"
    API_V1_STR: str = "/api/v1"
    
    # Database - use backend/database/ directory
    DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent.parent}/database/smartwaste.db"
    
    # ML Models Path - use backend/MLproject/ directory (will be created if needed)
    ML_MODELS_PATH: Path = Path(__file__).parent.parent.parent / "MLproject" / "ml" / "models"
    ML_FEATURES_PATH: Path = Path(__file__).parent.parent.parent / "MLproject" / "data" / "features"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "smartwaste-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Weather API
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
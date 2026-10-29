from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.session import engine, Base
from app.routers import auth, waste as waste_router, prediction as prediction_router, collector as collector_router, admin as admin_router, facilities as facilities_router
from app.models import user, waste, facility, prediction as pred_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SmartWaste - AI-Powered Waste Management API",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(waste_router.router, prefix=settings.API_V1_STR)
app.include_router(prediction_router.router, prefix=settings.API_V1_STR)
app.include_router(collector_router.router, prefix=settings.API_V1_STR)
app.include_router(admin_router.router, prefix=settings.API_V1_STR)
app.include_router(facilities_router.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "SmartWaste API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
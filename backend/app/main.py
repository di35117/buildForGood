# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_spatial_db, engine
from app.db.base_class import Base

# Import models explicitly so SQLAlchemy recognizes them during Base.metadata.create_all
from app.models.user import User
from app.models.route import Incident, ColdStartPrior

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware Configuration (Vital for Frontend-Backend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon convenience; tighten to specific ports if required later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # 1. Initialize PostGIS extension
    init_spatial_db()
    
    # 2. Automatically generate tables inside the spatial container
    Base.metadata.create_all(bind=engine)
    print("PostGIS active and database tables synced successfully.")

@app.get("/")
def root_check():
    return {"status": "healthy", "platform": "AWAAZ Women's Safety System", "year": 2026}
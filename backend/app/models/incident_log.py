from sqlalchemy import Column, String, Boolean, DateTime, JSON, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.base_class import Base

class IncidentLog(Base):
    __tablename__ = "incident_logs"

    incident_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    # Store the exact coordinates for the PostGIS spatial engine
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), index=True)
    
    # The full JSON dossier compiled during the SOS (for Legal Companion Module 2)
    evidence_payload = Column(JSON, nullable=False)
    
    # The ML Feedback triggers
    is_verified = Column(Boolean, default=False, index=True)
    ml_integrated = Column(Boolean, default=False) # Tracks if LightGBM has learned from this
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
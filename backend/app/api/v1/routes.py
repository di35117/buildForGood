# app/api/v1/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from app.api.deps import get_db, get_current_user  # 🔥 NEW: Auth dependency
from app.models.route import Incident
from app.schemas.route import IncidentCreate, IncidentResponse
from sqlalchemy import func

router = APIRouter()

@router.post("/incidents", response_model=IncidentResponse)
def report_incident(
    incident_in: IncidentCreate, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  # 🔥 FIX: Prevents fake spam reports
):
    """
    [P0] Submit a new community incident report.
    Converts frontend Lat/Lon into a PostGIS spatial point.
    """
    # PostGIS reads points as (Longitude, Latitude) -> X, Y
    point_wkt = f"POINT({incident_in.longitude} {incident_in.latitude})"
    
    new_incident = Incident(
        category=incident_in.category,
        description=incident_in.description,
        location=WKTElement(point_wkt, srid=4326)
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    # We map it back to the response schema for the frontend
    return IncidentResponse(
        id=new_incident.id,
        category=new_incident.category,
        description=new_incident.description,
        latitude=incident_in.latitude,
        longitude=incident_in.longitude,
        created_at=new_incident.created_at,
        is_active=new_incident.is_active
    )

@router.get("/incidents", response_model=list[IncidentResponse])
def get_active_incidents(
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  # 🔥 FIX: Protects incident data
):
    """
    [P0] Fetch all active incidents for the map frontend.
    Unpacks PostGIS geometry directly in the query for speed.
    """
    # We query the Incident object AND unpack the spatial point in one database trip
    records = db.query(
        Incident,
        func.ST_Y(Incident.location).label("lat"),
        func.ST_X(Incident.location).label("lon")
    ).filter(Incident.is_active == True).limit(limit).all()

    # Map the tuple results cleanly into your Pydantic schema
    return [
        IncidentResponse(
            id=incident.id,
            category=incident.category,
            description=incident.description,
            latitude=lat,
            longitude=lon,
            created_at=incident.created_at,
            is_active=incident.is_active
        )
        for incident, lat, lon in records
    ]
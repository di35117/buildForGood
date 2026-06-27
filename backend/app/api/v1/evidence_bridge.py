from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.incident_log import IncidentLog
from app.services.ml_feedback_service import MLFeedbackService
from datetime import datetime

router = APIRouter()

@router.post("/archive")
async def archive_sos_dossier(dossier: dict, db: Session = Depends(deps.get_db)):
    """Saves the JSON permanently to PostgreSQL."""
    
    # Safely extract location to prevent early-SOS crashes (Fixed Bug 1.4)
    loc = dossier.get("last_known_location")
    if not loc or "lat" not in loc or "lon" not in loc:
        raise HTTPException(
            status_code=400, 
            detail="Cannot archive SOS dossier: Missing location coordinates."
        )
        
    lat, lon = loc["lat"], loc["lon"]
    geom_point = f"SRID=4326;POINT({lon} {lat})"
    
    new_log = IncidentLog(
        incident_id=dossier["incident_id"],
        user_id=dossier["user_id"],
        latitude=lat,
        longitude=lon,
        geom=geom_point,
        evidence_payload=dossier
    )
    db.add(new_log)
    db.commit()
    return {"status": "Archived permanently to PostgreSQL"}

@router.post("/verify/{incident_id}")
async def verify_incident_and_learn(incident_id: str, db: Session = Depends(deps.get_db)):
    incident = db.query(IncidentLog).filter(IncidentLog.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.is_verified:
        return {"message": "Incident already verified."}
        
    incident.is_verified = True
    
    current_hour = datetime.utcnow().hour
    success = MLFeedbackService.integrate_verified_incident(
        lat=incident.latitude, 
        lon=incident.longitude, 
        time_of_day_hour=current_hour
    )
    
    if success:
        incident.ml_integrated = True
        
    db.commit()
    return {"status": "Verified", "ml_updated": success}
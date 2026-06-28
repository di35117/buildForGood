import os
import shutil
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement

from app.services.gemini_service import process_incident_audio
from app.schemas.legal import ComplaintDraftResponse
from app.api.deps import get_current_user, get_db
from app.models.shelter import Shelter

router = APIRouter()
logger = logging.getLogger("LegalIntake")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 

# ---------------------------------------------------------
# 1. VOICE INTAKE & COMPLAINT GENERATION
# ---------------------------------------------------------
def save_and_process_audio(upload_file: UploadFile, safe_filename: str) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        temp_path = tmp.name
        
    try:
        return process_incident_audio(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/intake", response_model=ComplaintDraftResponse)
async def voice_intake(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)  
):
    """[P0] Voice-based intake: transcribes audio, returns AI-drafted legal complaint."""
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    safe_filename = os.path.basename(file.filename)
    
    if not safe_filename.lower().endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid audio format.")
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")

    try:
        result = await run_in_threadpool(save_and_process_audio, file, safe_filename)
        return result
    except Exception as e:
        logger.error(f"Voice intake failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error processing audio.")

# ---------------------------------------------------------
# 2. 🔥 NEW: SHELTER / NGO DIRECTORY
# ---------------------------------------------------------
@router.get("/shelters")
def get_nearby_shelters(
    latitude: float,
    longitude: float,
    radius_km: float = 15.0, # Default search radius
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    [P0] Module 2: Fetches curated NGOs/Shelters near the user.
    Uses PostGIS ST_DWithin to calculate exact spherical distance.
    """
    point_wkt = f"POINT({longitude} {latitude})"
    radius_meters = radius_km * 1000

    # Query the DB for shelters within the radius, ordering them by closest first
    query = db.query(
        Shelter,
        func.ST_Distance(
            cast(Shelter.location, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography)
        ).label("distance")
    ).filter(
        func.ST_DWithin(
            cast(Shelter.location, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography),
            radius_meters
        )
    ).order_by("distance").limit(15).all()

    # Format the response for the frontend
    return [
        {
            "id": shelter.id,
            "name": shelter.name,
            "type": shelter.organization_type,
            "phone": shelter.phone_number,
            "address": shelter.address,
            "distance_km": round(distance / 1000, 2)
        }
        for shelter, distance in query
    ]
from pydantic import BaseModel, Field
from typing import List, Tuple

class SessionInitRequest(BaseModel):
    user_id: str
    route_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    safe_path: List[Tuple[float, float]] = Field(..., min_items=2)

class SessionInitResponse(BaseModel):
    session_id: str
    status: str

class TelemetryPing(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: float

class TelemetryResponse(BaseModel):
    session_id: str
    is_deviated: bool
    distance_from_route_meters: float
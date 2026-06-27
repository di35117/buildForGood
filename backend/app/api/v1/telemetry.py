from fastapi import APIRouter, HTTPException, status
from app.schemas.telemetry import SessionInitRequest, SessionInitResponse, TelemetryPing, TelemetryResponse
from app.services.telemetry_service import TelemetryService
from app.services.connection_manager import manager
router = APIRouter()

@router.post("/session/start", response_model=SessionInitResponse, status_code=status.HTTP_201_CREATED)
async def start_tracking_session(payload: SessionInitRequest):
    """
    Initializes a highly scalable tracking state. Captures planned path vectors 
    and pins them directly into memory.
    """
    try:
        session_id = await TelemetryService.initialize_session(
            user_id=payload.user_id,
            route_id=payload.route_id,
            safe_path=payload.safe_path
        )
        return SessionInitResponse(session_id=session_id, status="active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize tracking context: {str(e)}")

@router.post("/ping/{user_id}", response_model=TelemetryResponse)
async def ingest_telemetry(user_id: str, ping: TelemetryPing):
    """
    High-frequency geolocation ingest endpoint. Evaluates distance metrics 
    against cache constraints in micro-seconds.
    """
    is_deviated, distance = await TelemetryService.process_ping(
        user_id=user_id,
        current_lat=ping.latitude,
        current_lon=ping.longitude,
        timestamp=ping.timestamp
    )
    
    session_id = f"track:{user_id}"
    
    # NEW: The WebSocket Alert Trigger
    if is_deviated:
        alert_payload = {
            "type": "ROUTE_DEVIATION_ALERT",
            "session_id": session_id,
            "distance_meters": round(distance, 2),
            "message": "Deviation detected. Triggering confirmation window."
        }
        # Push the alert instantly to the frontend
        await manager.send_personal_alert(alert_payload, user_id)

    # Check for missing session
    if distance == 0.0 and not is_deviated:
        import redis.asyncio as aioredis
        from app.services.telemetry_service import redis_client
        if not await redis_client.exists(session_id):
            raise HTTPException(status_code=404, detail="Active tracking session not found.")

    return TelemetryResponse(
        session_id=session_id,
        is_deviated=is_deviated,
        distance_from_route_meters=round(distance, 2)
    )
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.services.fusion_engine import FusionEngine
from app.services.connection_manager import manager
from .escalation import start_escalation_countdown
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.core.security import verify_password
from app.core.config import settings

router = APIRouter()

# ---------------------------------------------------------
# 1. THE SECURED WEBSOCKET LISTENER (React Native connects here)
# ---------------------------------------------------------
# 🔥 FIX (Bug 2.5): No user_id in path. Requires token validation.
@router.websocket("/ws")
async def user_websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    """
    The mobile app connects here using ws://...?token=YOUR_JWT_TOKEN
    """
    user_id_str = None
    try:
        # 1. Cryptographically decode and verify the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        
        if not username:
            await websocket.close(code=1008, reason="Invalid Token")
            return
            
        # 2. Get the real database ID for this user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
            
        user_id_str = str(user.id)
        
        # 3. Securely connect them to the manager using their verified DB ID
        await manager.connect(websocket, user_id_str)
        print(f"User {user.username} securely authenticated to WebSocket.")
        
        while True:
            data = await websocket.receive_text()
            print(f"Received message from {user.username}: {data}")
            
    except JWTError:
        print("WebSocket rejected: Invalid JWT signature.")
        await websocket.close(code=1008, reason="Invalid JWT")
    except WebSocketDisconnect:
        if user_id_str:
            manager.disconnect(user_id_str)
            print(f"User {user_id_str} disconnected from WebSocket.")

# ---------------------------------------------------------
# 2. THE SENSOR SYNC & TRIGGER (The Fusion Engine)
# ---------------------------------------------------------
class SensorPayload(BaseModel):
    # 🔥 BOLA FIXED: user_id removed from payload entirely. Never trust the client.
    route_deviation: bool = False
    motion_anomaly: bool = False
    audio_scream: bool = False
    duress_pin: Optional[str] = None 

@router.post("/sync")
async def sync_device_sensors(
    payload: SensorPayload,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  
):
    """
    Ingests high-frequency sensor spikes from the mobile app.
    """
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_duress_verified = False
    if payload.duress_pin:
        if user.hashed_duress_pin and verify_password(payload.duress_pin, user.hashed_duress_pin):
            is_duress_verified = True
            print(f"⚠️ DURESS CODE VERIFIED for {user.username}. Silent SOS armed.")
        else:
            print(f"Failed duress PIN attempt for {user.username}")
            
    flags = {
        "route_deviation": payload.route_deviation,
        "motion_anomaly": payload.motion_anomaly,
        "audio_scream": payload.audio_scream,
        "duress_pin": is_duress_verified  
    }
    
    # 🔥 BOLA FIXED: Threat evaluated strictly against authenticated user ID
    user_id_str = str(user.id)
    is_critical, active_triggers, score = FusionEngine.evaluate_threat(
        user_id=user_id_str, 
        flags=flags
    )
    
    if is_critical:
        alert_payload = {
            "type": "CRITICAL_ESCALATION_WARNING",
            "message": "Corroborated threat detected. Initiating SOS sequence.",
            "countdown_seconds": 10,
            "active_triggers": active_triggers
        }
        
        await manager.send_personal_alert(alert_payload, user_id_str)
        print(f"🚨 WEBSOCKET PUSHED: Alert sent to {user_id_str}'s device.")
        
        await start_escalation_countdown(user_id_str)

    return {
        "status": "evaluated",
        "threat_score": score,
        "is_escalating": is_critical,
        "active_triggers": active_triggers
    }
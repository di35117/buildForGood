import json
from datetime import datetime
from app.services.telemetry_service import redis_client

class DossierService:
    @staticmethod
    async def compile_emergency_dossier(user_id: str) -> dict:
        """
        [P0] Compiles the user's active session, planned route, and actual 
        breadcrumb history into a single, structured emergency payload.
        """
        session_id = f"track:{user_id}"
        history_key = f"history:{user_id}"
        
        # 1. Fetch the core session data
        session_data = await redis_client.hgetall(session_id)
        if not session_data:
            return {"error": "No active tracking session found for this user."}
            
        # 2. Fetch the breadcrumb history (up to the last 50 pings to avoid massive payloads)
        raw_history = await redis_client.lrange(history_key, -50, -1)
        history_coords = [json.loads(ping) for ping in raw_history]
        
        # 3. Determine the last known location
        last_known = history_coords[-1] if history_coords else None
        
        # 4. Construct the Dossier
        dossier = {
            "incident_id": f"SOS-{user_id}-{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "CRITICAL_ESCALATION",
            "last_known_location": last_known,
            "route_metadata": {
                "route_id": session_data.get("route_id"),
                "is_deviated_at_trigger": session_data.get("is_deviated")
            },
            "recent_path_history": history_coords,
            "planned_safe_path": json.loads(session_data.get("safe_path", "[]"))
        }
        
        return dossier
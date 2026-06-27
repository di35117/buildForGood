from fastapi import APIRouter, HTTPException, status
from app.services.dossier_service import DossierService
from app.services.notification_service import NotificationService

router = APIRouter()

@router.post("/sos/{user_id}")
async def trigger_sos_escalation(user_id: str):
    """
    [P0] Triggered when the confirmation window expires or the user hits the panic button.
    Compiles live state into a dossier and fires the external notification gateways.
    """
    # 1. Gather all tracking telemetry from memory
    dossier = await DossierService.compile_emergency_dossier(user_id)
    
    if "error" in dossier:
        raise HTTPException(status_code=404, detail=dossier["error"])
        
    # 2. Fire notifications asynchronously to emergency contacts
    await NotificationService.send_emergency_alerts(dossier)
    
    return {
        "status": "ESCALATED",
        "message": "SOS system armed. Emergency contacts notified via gateway.",
        "incident_id": dossier.get("incident_id"),
        "dispatched_at": dossier.get("generated_at")
    }
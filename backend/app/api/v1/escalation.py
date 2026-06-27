from fastapi import APIRouter, HTTPException, status
from app.services.dossier_service import DossierService

router = APIRouter()

@router.post("/sos/{user_id}")
async def trigger_sos_escalation(user_id: str):
    """
    [P0] Triggered when the confirmation window expires or the user hits the panic button.
    Compiles the live state into a dossier for external dispatch.
    """
    dossier = await DossierService.compile_emergency_dossier(user_id)
    
    if "error" in dossier:
        raise HTTPException(status_code=404, detail=dossier["error"])
        
    # TODO: In the next step, we will hand this dossier to the External Gateway (Twilio/Email)
    # For now, we return it to verify it compiles correctly.
    
    return {
        "message": "SOS Triggered. Dossier compiled successfully.",
        "dossier": dossier
    }
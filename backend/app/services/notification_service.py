import logging
import asyncio
from app.db.session import SessionLocal
from app.models.user import EmergencyContact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NotificationGateway")

class NotificationService:
    @staticmethod
    async def send_emergency_alerts(dossier: dict):
        """
        [P0] Non-blocking dispatch engine. Blasts the compiled emergency 
        dossier to registered contacts and external responder nodes.
        """
        user_id = dossier.get("user_id")
        incident_id = dossier.get("incident_id")
        last_loc = dossier.get("last_known_location", {})
        
        # 🔥 FIX: Querying real emergency contacts dynamically
        db = SessionLocal()
        try:
            contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == int(user_id)).all()
            target_numbers = [c.phone_number for c in contacts]
            
            # Fallback to a national emergency line if user hasn't set contacts
            if not target_numbers:
                target_numbers = ["+91112"] 
        finally:
            db.close()
        
        tracking_url = f"https://awaaz-safety.org/track/{incident_id}"
        
        sms_message = (
            f"CRITICAL ALERT: Emergency contact requires assistance. "
            f"Last known location: Lat {last_loc.get('lat')}, Lon {last_loc.get('lon')}. "
            f"View live route track here: {tracking_url}"
        )
        
        asyncio.create_task(
            NotificationService._execute_broadcast(target_numbers, sms_message, dossier)
        )

    @staticmethod
    async def _execute_broadcast(contacts: list, message: str, dossier: dict):
        """Simulates network dispatch to external SMS/Push gateways."""
        logger.warning(f"!!! EMERGENCY ESCALATION INITIATED FOR {dossier.get('user_id')} !!!")
        
        for contact in contacts:
            logger.info(f"Sending Emergency SMS to {contact} -> Message: '{message}'")
            await asyncio.sleep(0.05) 
            
        logger.info(f"All external emergency channels successfully notified for incident {dossier.get('incident_id')}")
import logging
import asyncio

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
        
        # In a production environment, you would query the PostgreSQL database 
        # to fetch phone numbers associated with this user_id.
        mock_emergency_contacts = ["+919876543210", "+918765432109"]
        
        # Generate a live tracking link for the mobile map interface
        tracking_url = f"https://awaaz-safety.org/track/{incident_id}"
        
        sms_message = (
            f"CRITICAL ALERT: Emergency contact requires assistance. "
            f"Last known location: Lat {last_loc.get('lat')}, Lon {last_loc.get('lon')}. "
            f"View live route track here: {tracking_url}"
        )
        
        # Asynchronously execute notifications so the API layer returns a response instantly
        asyncio.create_task(
            NotificationService._execute_broadcast(mock_emergency_contacts, sms_message, dossier)
        )

    @staticmethod
    async def _execute_broadcast(contacts: list, message: str, dossier: dict):
        """
        Simulates network dispatch to external SMS/Push gateways without blocking the thread.
        """
        logger.warning(f"!!! EMERGENCY ESCALATION INITIATED FOR {dossier.get('user_id')} !!!")
        
        for contact in contacts:
            # This is where your external API client (e.g., Twilio or Fast2SMS) connects:
            # client.messages.create(body=message, to=contact, from_=settings.TWILIO_NUMBER)
            logger.info(f"Sending Emergency SMS to {contact} -> Message: '{message}'")
            await asyncio.sleep(0.05)  # Simulate network propagation delay
            
        logger.info(f"All external emergency channels successfully notified for incident {dossier.get('incident_id')}")
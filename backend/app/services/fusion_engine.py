import logging
from typing import Tuple, List, Dict

logger = logging.getLogger("FusionEngine")

class FusionEngine:
    # Threat Weights: Must cross 100 to trigger an escalation
    WEIGHTS = {
        "route_deviation": 80,   # High confidence, but could be a shortcut
        "motion_anomaly": 60,    # Medium confidence (e.g., dropped phone, running)
        "audio_scream": 90,      # Extremely high confidence
        "duress_pin": 200        # Absolute certainty (Silent SOS override)
    }

    THRESHOLD = 100

    @staticmethod
    def evaluate_threat(user_id: str, flags: Dict[str, bool]) -> Tuple[bool, List[str], int]:
        """
        Evaluates a dictionary of active sensor flags and determines if the 
        threat score crosses the critical escalation threshold.
        """
        total_score = 0
        active_triggers = []

        for sensor, is_active in flags.items():
            if is_active and sensor in FusionEngine.WEIGHTS:
                total_score += FusionEngine.WEIGHTS[sensor]
                active_triggers.append(sensor)

        logger.info(f"User {user_id} | Threat Score: {total_score} | Triggers: {active_triggers}")

        if total_score >= FusionEngine.THRESHOLD:
            logger.warning(f"CRITICAL THRESHOLD MET for {user_id}. Initiating Escalation.")
            return True, active_triggers, total_score
        
        return False, active_triggers, total_score
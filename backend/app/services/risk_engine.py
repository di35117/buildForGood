import joblib
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement
from app.models.route import Incident, ColdStartPrior

# Load the model globally so it doesn't reload on every API request
MODEL_PATH = "app/services/lgbm_risk_model.pkl"
try:
    risk_model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    risk_model = None
    print("Warning: LightGBM model not found. Run training script.")

def calculate_area_risk(db: Session, lat: float, lon: float, radius_m: float = 500.0) -> dict:
    point_wkt = f"POINT({lon} {lat})"
    now = datetime.utcnow()
    
    # 1. Fetch real-time DB states (The Dynamic Features)
    recent_threshold = now - timedelta(days=7)
    recent_incidents = db.query(Incident).filter(
        func.ST_DWithin(
            cast(Incident.location, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography),
            radius_m
        ),
        Incident.created_at >= recent_threshold,
        Incident.is_active == True
    ).count()

    # 2. Fetch Spatial Priors (The Static Features)
    # In production, query your ColdStartPrior table here. 
    # Mocking for the example:
    street_lit = 1 # 1 = Yes, 0 = No
    commercial_density = 0.65 

    # 3. Construct the Feature Vector
    features = pd.DataFrame([{
        'hour_of_day': now.hour,
        'is_weekend': 1 if now.weekday() >= 5 else 0,
        'street_lit': street_lit,
        'commercial_density': commercial_density,
        'recent_incidents_count': recent_incidents
    }])

    # 4. LightGBM Inference
    if risk_model:
        # Predict returns a numpy array, extract the first float
        final_score = float(risk_model.predict(features)[0])
        final_score = max(0.0, min(final_score, 10.0)) # Clamp between 0 and 10
    else:
        # Fallback to heuristic if model fails to load
        final_score = 5.0 

    # 5. Classify for the frontend map colors
    if final_score < 4.0:
        level = "LOW"
    elif final_score < 7.0:
        level = "MODERATE"
    else:
        level = "HIGH"

    return {
        "latitude": lat,
        "longitude": lon,
        "radius_meters": radius_m,
        "risk_score": round(final_score, 1),
        "risk_level": level,
        "contributing_incidents": recent_incidents
    }
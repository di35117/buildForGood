import pandas as pd
import lightgbm as lgb
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement
from app.models.route import Incident, ColdStartPrior

MODEL_PATH = "app/ml/models/risk_v1.txt"
_risk_model = None

def get_model():
    """Lazy loader for the model to ensure it loads natively."""
    global _risk_model
    if _risk_model is None:
        try:
            _risk_model = lgb.Booster(model_file=MODEL_PATH)
        except Exception as e:
            print(f"WARNING: LightGBM model not found. {e}")
    return _risk_model

def reload_model():
    """Called by the ML Feedback Loop after a successful retrain."""
    global _risk_model
    try:
        _risk_model = lgb.Booster(model_file=MODEL_PATH)
        print("SUCCESS: Risk model reloaded in memory.")
    except Exception as e:
        print(f"ERROR: Failed to reload model: {e}")

def calculate_area_risk(db: Session, lat: float, lon: float, radius_m: float = 500.0) -> dict:
    point_wkt = f"POINT({lon} {lat})"
    now = datetime.utcnow()
    
    # 1. Fetch Dynamic Features
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

    # 2. Fetch Spatial Priors 
    prior = db.query(ColdStartPrior).filter(
        func.ST_DWithin(
            cast(ColdStartPrior.geom, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography),
            radius_m
        )
    ).first()

    # 🔥 FIX (Bug 2.1): Corrected attribute names to match DB model
    street_lit = prior.street_lighting_score if prior else 1
    commercial_density = prior.commercial_density_score if prior else 0.65

    # 3. Construct the Feature Vector
    features = pd.DataFrame([{
        'latitude': lat,
        'longitude': lon,
        'hour_of_day': now.hour,
        'is_weekend': 1 if now.weekday() >= 5 else 0,
        'street_lit': street_lit,
        'commercial_density': commercial_density,
        'recent_incidents_count': recent_incidents
    }])

    # 4. LightGBM Inference
    model = get_model()
    if model:
        final_score = float(model.predict(features)[0])
        final_score = max(0.0, min(final_score, 10.0))
    else:
        final_score = 5.0 

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
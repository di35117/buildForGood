import os
import logging
from datetime import datetime
import lightgbm as lgb
import pandas as pd

logger = logging.getLogger("MLFeedbackLoop")

class MLFeedbackService:
    MODEL_PATH = "app/ml/models/risk_v1.txt"
    BATCH_FILE = "app/ml/data/verified_batch.csv"
    BATCH_SIZE = 5

    @staticmethod
    def integrate_verified_incident(lat: float, lon: float, time_of_day_hour: int):
        try:
            logger.info(f"Logging verified incident for Lat {lat}, Lon {lon}")
            is_weekend = 1 if datetime.utcnow().weekday() >= 5 else 0
            
            new_data = pd.DataFrame([{
                'latitude': lat, 
                'longitude': lon, 
                'hour_of_day': time_of_day_hour,
                'is_weekend': is_weekend,
                'street_lit': 0,
                'commercial_density': 0.3,
                'recent_incidents_count': 1,
                'target_risk_score': 9.0  # Slightly nuanced target to prevent absolute skew
            }])
            
            # 1. Append to Batch File
            os.makedirs(os.path.dirname(MLFeedbackService.BATCH_FILE), exist_ok=True)
            new_data.to_csv(
                MLFeedbackService.BATCH_FILE, 
                mode='a', 
                header=not os.path.exists(MLFeedbackService.BATCH_FILE), 
                index=False
            )
            
            # 2. Check if we reached batch threshold to retrain
            df = pd.read_csv(MLFeedbackService.BATCH_FILE)
            if len(df) < MLFeedbackService.BATCH_SIZE:
                logger.info(f"Batch size {len(df)}/{MLFeedbackService.BATCH_SIZE}. Deferring retrain.")
                return True
                
            # 3. We hit the batch size, retrain!
            logger.info("Batch threshold met. Triggering incremental retrain.")
            X_train = df.drop(columns=['target_risk_score'])
            y_train = df['target_risk_score']
            train_data = lgb.Dataset(X_train, label=y_train)
            
            updated_model = lgb.train(
                params={
                    'objective': 'regression',
                    'learning_rate': 0.05,
                    'min_data_in_leaf': 1,
                    'min_data_in_bin': 1,
                    'feature_pre_filter': False
                },
                train_set=train_data,
                num_boost_round=10, 
                init_model=MLFeedbackService.MODEL_PATH
            )
            
            # 4. Save model and clear batch
            updated_model.save_model(MLFeedbackService.MODEL_PATH)
            df.iloc[0:0].to_csv(MLFeedbackService.BATCH_FILE, index=False)
            logger.info("ML Risk Model successfully updated.")
            
            # 5. Tell the server to reload its brain!
            from app.services.risk_engine import reload_model
            reload_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run incremental ML update: {str(e)}")
            return False
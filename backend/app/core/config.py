from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AWAAZ - Women's Safety Lifecycle Platform"
    API_V1_STR: str = "/api/v1"
    
    # Infrastructure URLs (No hardcoded passwords!)
    DATABASE_URL: str
    REDIS_URL: str
    
    # AI Core
    GEMINI_API_KEY: str
    
    # Security (No hardcoded keys!)
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # 🔥 FIX (Bug 2.4): Dedicated salt so forum hashes don't rely on JWT secrets
    ANONYMITY_SALT: str 

    model_config = ConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
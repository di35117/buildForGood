# backend/app/api/deps.py
from typing import Generator
import redis
from app.core.config import settings
from app.db.session import SessionLocal

def get_db() -> Generator:
    """Yields a relational database session, automatically closing it post-request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> Generator[redis.Redis, None, None]:
    """Provides a connection instance to the active Redis cluster."""
    client = redis.Redis.from_url(
        settings.REDIS_URL, 
        decode_responses=True  # Automatically parses raw redis bytes to Python strings
    )
    try:
        yield client
    finally:
        client.close()
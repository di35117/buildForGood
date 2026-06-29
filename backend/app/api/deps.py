from typing import Generator
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User # 🔥 Imported User model for role checking

# This tells FastAPI where the login endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

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
        decode_responses=True
    )
    try:
        yield client
    finally:
        client.close()

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Validates the JWT and returns the user ID (username). Plugs into any route that needs security."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

# ---------------------------------------------------------
# 🔥 NEW: NGO / MODERATOR BOUNCER
# ---------------------------------------------------------
def get_current_ngo_user(
    current_username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the token AND checks if the user has the is_ngo role.
    Use this Depends() on any endpoint that modifies trust scores or views dossiers.
    """
    user = db.query(User).filter(User.username == current_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_ngo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: NGO or Moderator privileges required."
        )
        
    return user
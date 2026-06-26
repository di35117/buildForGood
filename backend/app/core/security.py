# backend/app/core/security.py
from passlib.context import CryptContext

# Configuration block for standard password/PIN obfuscation
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compares a raw input string against an existing hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Transforms raw credentials or PINs into a secure, reproducible cryptographic string."""
    return pwd_context.hash(password)
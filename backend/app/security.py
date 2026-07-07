"""
Admin authentication: bcrypt password hashing + JWT stored in an httpOnly
cookie (never in localStorage, so it can't be read by injected JS / other
tabs, and never sent to the client in plaintext).
"""
import datetime as dt

import jwt
from fastapi import Cookie, HTTPException, status
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

COOKIE_NAME = "ac_admin_session"


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)


def create_admin_token(email: str) -> str:
    payload = {
        "sub": email,
        "role": "admin",
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_admin_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")


def require_admin(ac_admin_session: str | None = Cookie(default=None)) -> dict:
    """FastAPI dependency - protects every /api/admin/* route."""
    if not ac_admin_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    payload = decode_admin_token(ac_admin_session)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return payload

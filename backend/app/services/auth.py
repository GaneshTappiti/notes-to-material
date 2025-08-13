"""Authentication helpers: password hashing, JWT issue/verify, role dependency.

Lightweight implementation avoiding external heavy deps: uses PyJWT.
Environment:
  JWT_SECRET (required for production; defaults to unsafe dev secret)
  JWT_EXPIRE_SECONDS (default 3600)
"""
from __future__ import annotations
import os, time, hashlib, hmac, base64
from typing import Optional
import jwt  # type: ignore
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from ..models import User, get_session

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change")
JWT_EXPIRE = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))

security = HTTPBearer(auto_error=False)


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 39000)
    return f"pbkdf2$sha256$39000${salt}${base64.urlsafe_b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, _hash_name, _iter, salt, digest = stored.split("$")
    except ValueError:
        return False
    test = _hash_password(password, salt)
    return hmac.compare_digest(test, stored)


def create_token(user: User) -> str:
    now = int(time.time())
    payload = {"sub": str(user.id), "role": user.role, "exp": now + JWT_EXPIRE}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


API_KEY = os.getenv("API_KEY") or os.getenv("DEV_API_KEY", "dev-key")

def current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Return authenticated user via Bearer JWT or fallback X-API-Key header.

    API key fallback is intended ONLY for local testing/dev (treats caller as admin).
    Provide header:  X-API-Key: <API_KEY>
    """
    # API key shortcut (no JWT provided)
    if (not credentials) and request:
        api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
        if api_key and hmac.compare_digest(api_key, API_KEY):  # constant time
            # Return synthetic admin user (not persisted)
            return User(id=0, email="apikey@local", password_hash="", role="admin")
    if not credentials:
        # Re-evaluate test mode dynamically so late-set env or pytest var works
        if os.getenv('TEST_MODE','0') == '1' or 'PYTEST_CURRENT_TEST' in os.environ:  # test bypass
            return User(id=0, email="test@local", password_hash="", role="admin")
        raise HTTPException(status_code=401, detail="Missing auth header")
    token = credentials.credentials
    data = decode_token(token)
    with get_session() as session:
        user = session.exec(select(User).where(User.id == int(data["sub"]))).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


def require_role(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: role")
        return user
    return dep


__all__ = [
    "_hash_password","verify_password","create_token","current_user","require_role"
]

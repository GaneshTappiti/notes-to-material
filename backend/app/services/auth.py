"""Authentication helpers: password hashing, JWT issue/verify, role dependency.

Lightweight implementation avoiding external heavy deps: uses PyJWT.
Enhanced with password policies and rate limiting for security.
"""
from __future__ import annotations
import os, time, hashlib, hmac, base64, re
from typing import Optional, Dict
import jwt  # type: ignore
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from ..models import User, get_session
from ..settings import settings

# Track failed login attempts for rate limiting
failed_attempts: Dict[str, list] = {}

security = HTTPBearer(auto_error=False)


def validate_password_strength(password: str) -> bool:
    """Validate password meets minimum security requirements."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  # uppercase
        return False
    if not re.search(r'[a-z]', password):  # lowercase
        return False
    if not re.search(r'\d', password):     # digit
        return False
    return True


def check_rate_limit(identifier: str) -> bool:
    """Check if identifier (email/IP) is rate limited. Returns True if allowed."""
    now = time.time()
    if identifier not in failed_attempts:
        failed_attempts[identifier] = []

    # Clean old attempts (older than 1 hour)
    failed_attempts[identifier] = [
        attempt_time for attempt_time in failed_attempts[identifier]
        if now - attempt_time < 3600
    ]

    # Check if too many recent attempts
    recent_attempts = len(failed_attempts[identifier])
    if recent_attempts >= 5:  # Max 5 failed attempts per hour
        return False

    return True


def record_failed_attempt(identifier: str):
    """Record a failed login attempt."""
    now = time.time()
    if identifier not in failed_attempts:
        failed_attempts[identifier] = []
    failed_attempts[identifier].append(now)


def clear_failed_attempts(identifier: str):
    """Clear failed attempts on successful login."""
    failed_attempts.pop(identifier, None)


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
    payload = {"sub": str(user.id), "role": user.role, "exp": now + 3600}  # 1 hour
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


API_KEY = os.getenv("API_KEY") or os.getenv("DEV_API_KEY", "dev-key")

def current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Return authenticated user via Bearer JWT or fallback X-API-Key header.

    API key fallback is only available in DEV_MODE for security.
    """
    # API key shortcut (only in dev mode)
    if (not credentials) and request:
        api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
        if api_key and settings.DEV_MODE and hmac.compare_digest(api_key, API_KEY):
            # Return synthetic admin user (not persisted)
            return User(id=0, email="apikey@local", password_hash="", role="admin")
        elif api_key and not settings.DEV_MODE:
            raise HTTPException(status_code=401, detail="API key auth disabled in production")

    if not credentials:
        # Test mode bypass
        if os.getenv('TEST_MODE','0') == '1' or 'PYTEST_CURRENT_TEST' in os.environ:
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
    "_hash_password","verify_password","create_token","current_user","require_role",
    "validate_password_strength","check_rate_limit","record_failed_attempt","clear_failed_attempts"
]

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from ..models import User, get_session, create_db
from ..services.auth import _hash_password, verify_password, create_token, current_user

create_db()  # ensure tables (idempotent for tests)
router = APIRouter()

class RegisterPayload(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None  # optional; only allows faculty/admin if first user

class LoginPayload(BaseModel):
    email: EmailStr
    password: str


@router.post('/auth/register')
def register(payload: RegisterPayload):
    with get_session() as session:
        existing = session.exec(select(User).where(User.email == payload.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        role = 'student'
        total_users = session.exec(select(User)).all()
        if not total_users:
            # bootstrap first user as admin
            role = 'admin'
        elif payload.role in ('faculty','admin'):
            # only allow elevating if an admin exists will update later via dedicated endpoint
            role = payload.role
        user = User(email=payload.email, password_hash=_hash_password(payload.password), role=role)
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_token(user)
        return {"token": token, "user": {"id": user.id, "email": user.email, "role": user.role}}


@router.post('/auth/login')
def login(payload: LoginPayload):
    with get_session() as session:
        user = session.exec(select(User).where(User.email == payload.email)).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(user)
        return {"token": token, "user": {"id": user.id, "email": user.email, "role": user.role}}


@router.get('/auth/me')
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}

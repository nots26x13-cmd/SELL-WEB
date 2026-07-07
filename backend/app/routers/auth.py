"""
Customer-facing signup / login, separate from /api/admin/*.

Storefront pages opened inside Telegram already have an identity for free
(getCurrentUserId() in the frontend uses the Telegram user id, no password
needed). This router is for people using the site as a normal website
outside Telegram, who need an email + password account instead.

Same building blocks as admin auth (bcrypt hash, JWT in an httpOnly cookie)
but on its own cookie name / role, so a customer session can never pass the
require_admin check and vice versa.
"""
import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..firebase_client import get_db
from ..schemas import LoginRequest, SignupRequest, UserPublic
from ..security import (
    USER_COOKIE_NAME,
    create_user_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _find_user_by_email(db, email: str):
    docs = db.collection("users").where("email", "==", email).limit(1).get()
    return docs[0] if docs else None


def _set_session_cookie(response: Response, user_id: str):
    token = create_user_token(user_id)
    response.set_cookie(
        key=USER_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,   # requires HTTPS in production (Render gives you this)
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )


@router.post("/signup", response_model=UserPublic)
def signup(payload: SignupRequest, response: Response):
    email = payload.email.strip().lower()
    name = payload.name.strip() or "Player"

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    db = get_db()
    if _find_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user_id = f"web-{uuid.uuid4().hex[:12]}"
    db.collection("users").document(user_id).set({
        "name": name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "wallet_balance": 0,
        "created_at": dt.datetime.utcnow().isoformat(),
    })

    _set_session_cookie(response, user_id)
    return UserPublic(id=user_id, name=name, email=email, wallet_balance=0)


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response):
    email = payload.email.strip().lower()
    db = get_db()
    doc = _find_user_by_email(db, email)
    if not doc:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    data = doc.to_dict()
    if not data.get("password_hash") or not verify_password(payload.password, data["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    _set_session_cookie(response, doc.id)
    return UserPublic(
        id=doc.id,
        name=data.get("name", "Player"),
        email=email,
        wallet_balance=data.get("wallet_balance", 0),
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(USER_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
def me(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = doc.to_dict()
    return UserPublic(
        id=user_id,
        name=data.get("name", "Player"),
        email=data.get("email", ""),
        wallet_balance=data.get("wallet_balance", 0),
    )

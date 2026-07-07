from fastapi import APIRouter, HTTPException, Response, status

from ..firebase_client import get_db
from ..schemas import AdminLoginRequest
from ..security import COOKIE_NAME, create_admin_token, hash_password, verify_password
from ..config import settings

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


def _ensure_bootstrap_admin():
    """Creates the first admin account from env vars if no admin exists yet.
    Run once - after that, change the password from the admin panel and the
    bootstrap env vars are no longer used."""
    db = get_db()
    admins = db.collection("admins").limit(1).get()
    if len(admins) == 0:
        db.collection("admins").document(settings.admin_bootstrap_email).set({
            "email": settings.admin_bootstrap_email,
            "password_hash": hash_password(settings.admin_bootstrap_password),
        })


@router.post("/login")
def login(payload: AdminLoginRequest, response: Response):
    _ensure_bootstrap_admin()
    db = get_db()
    doc = db.collection("admins").document(payload.email).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    data = doc.to_dict()
    if not verify_password(payload.password, data["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_admin_token(payload.email)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,       # requires HTTPS in production
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return {"ok": True, "email": payload.email}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}

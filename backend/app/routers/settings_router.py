from fastapi import APIRouter, Depends

from ..firebase_client import get_db
from ..schemas import AdminSettingsUpdate, PublicSettings
from ..security import require_admin

router = APIRouter(tags=["settings"])

DEFAULTS = {
    "binance_pay_id": "881496930",
    "min_deposit_usdt": 0.01,
    "payment_methods": {"binance": True, "bkash": False, "nagad": False},
    "nickname_api_base_url": "https://ff-info-api-weld.vercel.app",
    "nickname_api_enabled": True,
}


def _get_settings_doc():
    db = get_db()
    ref = db.collection("settings").document("global")
    doc = ref.get()
    if not doc.exists:
        ref.set(DEFAULTS)
        return DEFAULTS
    data = doc.to_dict()
    merged = {**DEFAULTS, **data}
    return merged


@router.get("/api/settings/public", response_model=PublicSettings)
def get_public_settings():
    data = _get_settings_doc()
    return PublicSettings(
        binance_pay_id=data["binance_pay_id"],
        min_deposit_usdt=data["min_deposit_usdt"],
        payment_methods=data["payment_methods"],
    )


@router.get("/api/admin/settings", dependencies=[Depends(require_admin)])
def get_admin_settings():
    return _get_settings_doc()


@router.put("/api/admin/settings", dependencies=[Depends(require_admin)])
def update_settings(update: AdminSettingsUpdate):
    db = get_db()
    ref = db.collection("settings").document("global")
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    ref.set(changes, merge=True)
    return _get_settings_doc()

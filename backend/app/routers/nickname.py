"""
Proxies the "check nickname" lookup to a third-party endpoint that you
configure in Settings (default matches what you were already using). This
backend does not implement any of Garena's protocol itself, it just calls
whatever URL is configured and forwards back the nickname field.

Worth knowing before you rely on this in production: it's an unofficial,
third-party endpoint with no published SLA, so treat outages/format changes
as expected, not exceptional - the try/except below fails soft (returns
nickname: null) instead of breaking checkout when that happens.
"""
import httpx
from fastapi import APIRouter, HTTPException

from .settings_router import _get_settings_doc

router = APIRouter(tags=["nickname"])


@router.get("/api/nickname")
def check_nickname(uid: str):
    cfg = _get_settings_doc()
    if not cfg.get("nickname_api_enabled", True):
        raise HTTPException(status_code=503, detail="Nickname lookup is currently disabled")

    base_url = cfg["nickname_api_base_url"].rstrip("/")
    url = f"{base_url}/nickname"

    try:
        resp = httpx.get(url, params={"uid": uid}, timeout=8.0)
        data = resp.json()
    except Exception:
        return {"success": False, "uid": uid, "nickname": None}

    return {
        "success": bool(data.get("success")),
        "uid": data.get("uid", uid),
        "nickname": data.get("nickname"),
    }

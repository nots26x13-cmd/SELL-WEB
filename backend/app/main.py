from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .firebase_client import init_firebase
from .routers import admin_auth, auth, nickname, orders, products, wallet, settings_router

app = FastAPI(title="S26X CODEX SHOP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,  # needed so the admin session cookie is sent
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_firebase()


app.include_router(admin_auth.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(settings_router.router)
app.include_router(wallet.router)
app.include_router(orders.router)
app.include_router(nickname.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Serve the frontend (Telegram Mini App pages) from this same service ---
# Layout on disk: <repo>/backend/app/main.py  and  <repo>/frontend/*
# This mount MUST stay last: FastAPI/Starlette matches routes in the order
# they were registered, so every /api/* route above still wins over this
# catch-all. html=True lets "/" serve frontend/index.html and lets
# "/checkout.html", "/admin/login.html" etc. resolve as written in the HTML.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

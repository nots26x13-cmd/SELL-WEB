from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .firebase_client import init_firebase
from .routers import admin_auth, nickname, orders, products, wallet, settings_router

app = FastAPI(title="Arafat Codex API")

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
app.include_router(products.router)
app.include_router(settings_router.router)
app.include_router(wallet.router)
app.include_router(orders.router)
app.include_router(nickname.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

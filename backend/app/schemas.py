from typing import Optional

from pydantic import BaseModel, Field


class PackageOption(BaseModel):
    id: str
    label: str          # e.g. "220 likes / 7day"
    price_bdt: float
    duration_days: Optional[int] = None
    quantity_per_day: Optional[int] = None
    in_stock: bool = True


class Product(BaseModel):
    id: Optional[str] = None
    name: str                       # e.g. "FREE FIRE LIKES"
    subtitle: Optional[str] = None  # e.g. "UID TOPUP"
    image_url: Optional[str] = None
    category: str = "general"
    requires_uid: bool = True
    packages: list[PackageOption] = Field(default_factory=list)
    active: bool = True


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    wallet_balance: float = 0


class DepositIntentRequest(BaseModel):
    amount_usdt: float


class BinanceDepositVerifyRequest(BaseModel):
    tx_id: str
    expected_amount_usdt: float


class OrderCreateRequest(BaseModel):
    product_id: str
    package_id: str
    player_uid: str


class OrderStatusUpdateRequest(BaseModel):
    status: str  # "fulfilled" | "rejected" | "pending_fulfillment"
    admin_note: Optional[str] = None


class PublicSettings(BaseModel):
    binance_pay_id: str
    min_deposit_usdt: float
    payment_methods: dict[str, bool]  # {"binance": True, "bkash": True, "nagad": False}


class AdminSettingsUpdate(BaseModel):
    binance_pay_id: Optional[str] = None
    min_deposit_usdt: Optional[float] = None
    payment_methods: Optional[dict[str, bool]] = None
    nickname_api_base_url: Optional[str] = None
    nickname_api_enabled: Optional[bool] = None

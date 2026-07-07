"""
Central configuration. Everything sensitive comes from environment variables
(see .env.example) - nothing secret is ever hardcoded in source.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Firebase
    firebase_credentials_path: str = "./secrets/firebase-service-account.json"
    firebase_database_url: str = ""

    # Admin bootstrap
    admin_bootstrap_email: str = "admin@example.com"
    admin_bootstrap_password: str = "change-me-immediately"

    # Auth
    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_expire_minutes: int = 720

    # Binance Pay
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # bKash
    bkash_app_key: str = ""
    bkash_app_secret: str = ""
    bkash_username: str = ""
    bkash_password: str = ""

    # Nagad
    nagad_merchant_id: str = ""
    nagad_merchant_private_key: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()

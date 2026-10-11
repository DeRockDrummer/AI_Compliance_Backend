from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # ============================================================
    # DATABASE
    # ============================================================
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database connection string"
    )

    # ============================================================
    # SECURITY / JWT
    # ============================================================
    jwt_secret_key: str = Field(
        default="CHANGE_ME_IN_ENV",
        description="JWT signing key"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(default=60)
    refresh_token_expire_days: int = Field(default=30)

    # ============================================================
    # ENVIRONMENT
    # ============================================================
    env: str = Field(
        default=os.getenv("ENV", "development"),
        description="Environment mode: development | production"
    )

    # ============================================================
    # CORS
    # ============================================================
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origin for frontend"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # ⭐ THIS IS THE MAGIC FIX ⭐
        # Allow uppercase environment variables to map to lowercase fields
        case_sensitive = False

settings = Settings()

print(f"[CONFIG] Loaded environment: {settings.env}")
print(f"[CONFIG] JWT key loaded: {settings.jwt_secret_key[:8]}********")

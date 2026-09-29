from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # ============================================================
    # DATABASE
    # ============================================================
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database connection string"
    )

    # ============================================================
    # SECURITY / JWT
    # ============================================================
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_ENV",
        description="JWT signing key"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # ============================================================
    # ENVIRONMENT
    # ============================================================
    ENV: str = Field(
        default=os.getenv("ENV", "development"),
        description="Environment mode: development | production"
    )

    # ============================================================
    # CORS
    # ============================================================
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origin for frontend"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

print(f"[CONFIG] Loaded environment: {settings.ENV}")
print(f"[CONFIG] SECRET_KEY loaded: {settings.SECRET_KEY[:8]}********")

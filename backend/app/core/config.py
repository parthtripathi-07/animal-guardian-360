"""
Core application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # General
    APP_NAME: str = "Animal Guardian 360°"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "animal-guardian-360-dev-secret-key-super-secure-change-in-prod-32bytes"
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/animal_guardian_db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Authentication & Security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    MOCK_OTP_MODE: bool = True  # Logs OTP to console/response for local dev/testing

    # External Integrations
    GOOGLE_MAPS_API_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Storage (Cloudflare R2 / AWS S3)
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "animal-guardian-media"
    S3_PUBLIC_DOMAIN: str = ""

    # Communications
    EMAIL_PROVIDER: str = "mock"
    FROM_EMAIL: str = "support@animalguardian360.org"
    FROM_NAME: str = "Animal Guardian 360°"
    SENDGRID_API_KEY: str = ""
    SMS_API_KEY: str = ""

    # Observability & Monitoring
    SENTRY_DSN: str = ""


settings = Settings()

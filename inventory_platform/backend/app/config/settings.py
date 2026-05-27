"""
Application settings — Supabase edition.

Supabase provides:
  - Managed PostgreSQL (connected via SQLAlchemy asyncpg)
  - Auth (JWT issued by Supabase, verified locally using SUPABASE_JWT_SECRET)
  - Realtime (frontend subscribes directly; backend publishes via DB writes)
  - Storage (future: attachment uploads)
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "Bus Inventory Platform"
    APP_VERSION: str = "1.0.0"
    APP_SECRET_KEY: str = "dev-secret-change-in-production"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ---- Supabase ----
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    # JWT secret from Supabase dashboard → Settings → API → JWT Secret
    # Used to verify Supabase-issued tokens locally (no network roundtrip)
    SUPABASE_JWT_SECRET: str

    # ---- Database (Supabase PostgreSQL via Transaction Pooler) ----
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ---- Redis (optional — caching + rate limiting) ----
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300
    RATE_LIMIT_PER_MINUTE: int = 100

    # ---- RabbitMQ (optional — background workers) ----
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # ---- Webhook ----
    WEBHOOK_SIGNING_SECRET: str = "dev-webhook-secret"
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_RETRY_DELAYS: str = "1,5,30,120,600"

    # ---- Alert thresholds ----
    ALERT_LOW_STOCK_THRESHOLD_PCT: float = 0.20
    ALERT_CRITICAL_STOCK_THRESHOLD_PCT: float = 0.05
    ALERT_DEPLETION_WARNING_DAYS: int = 7

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @property
    def webhook_retry_delays_list(self) -> List[int]:
        return [int(d) for d in self.WEBHOOK_RETRY_DELAYS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

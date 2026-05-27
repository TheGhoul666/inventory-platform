"""
FastAPI application factory.

Startup sequence:
  1. Configure structured logging
  2. Connect Redis
  3. Connect RabbitMQ publisher
  4. Register Prometheus instrumentation
  5. Mount routers
  6. Apply middleware stack
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.settings import get_settings
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.queue.publisher import event_publisher
from app.infrastructure.logging.structured_logger import configure_logging
from app.infrastructure.webhooks.webhook_engine import webhook_engine
from app.api.middleware.request_context import RequestContextMiddleware, SecurityHeadersMiddleware
from app.api.routes import auth, inventory, analytics, alerts, health, warehouses, buses, audit

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    configure_logging()

    try:
        await redis_client.connect()
    except Exception as exc:
        logger.warning("Redis unavailable — caching and rate-limiting disabled: %s", exc)

    try:
        await event_publisher.connect()
    except Exception as exc:
        logger.warning("RabbitMQ unavailable — background workers disabled: %s", exc)

    await webhook_engine.connect()

    yield  # application is running

    await webhook_engine.disconnect()
    await event_publisher.disconnect()
    await redis_client.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ---- Middleware (applied in reverse order) ----
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )

    # ---- Prometheus metrics ----
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/health", "/ready"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ---- Routers ----
    prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(inventory.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(warehouses.router, prefix=prefix)
    app.include_router(buses.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)

    return app


app = create_app()

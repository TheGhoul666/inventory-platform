"""
Async SQLAlchemy engine and session factory.

Connection pooling is tuned for production PostgreSQL workloads.
The async engine uses asyncpg under the hood.

CONCURRENCY NOTE:
  AsyncSession is NOT thread-safe. Each request handler gets its
  own session via get_db(). Never share a session across coroutines.
"""
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings

settings = get_settings()

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite (unit tests): no connection pool tuning, no TLS.
    _engine_kwargs: dict = {"echo": settings.DATABASE_ECHO}
else:
    _engine_kwargs = {
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "echo": settings.DATABASE_ECHO,
        "connect_args": {"ssl": _ssl_ctx},
    }

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # prevent lazy-load after commit in async ctx
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """
    FastAPI dependency that yields a transactional async DB session.
    Yields None if the DB is unreachable so callers can degrade gracefully.
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("DB connection failed: %s", exc)
        raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context-manager version for use outside FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

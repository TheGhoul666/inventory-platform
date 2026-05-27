"""
SQLAlchemy declarative base and shared column mixins.

All ORM models inherit from Base. AuditMixin provides the
standard created_at / updated_at / is_deleted columns that
every enterprise table must carry.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Project-wide declarative base."""
    pass


class AuditMixin:
    """
    Standard audit columns.

    created_at  — set once on INSERT, never changed.
    updated_at  — updated by the DB on every UPDATE via server_onupdate.
    is_deleted  — soft-delete flag; hard deletes are prohibited in production.
    deleted_at  — timestamp of soft-delete, null if row is alive.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class UUIDPKMixin:
    """UUID primary key — preferred over integer PKs for distributed systems."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

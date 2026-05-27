"""
Alert and Webhook delivery models.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SAEnum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, AuditMixin, UUIDPKMixin


class AlertType(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    CRITICAL_STOCK = "CRITICAL_STOCK"
    PREDICTED_DEPLETION = "PREDICTED_DEPLETION"
    ABNORMAL_USAGE = "ABNORMAL_USAGE"
    WEBHOOK_FAILURE = "WEBHOOK_FAILURE"
    WAREHOUSE_ANOMALY = "WAREHOUSE_ANOMALY"
    SYSTEM = "SYSTEM"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class Alert(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "alerts"

    alert_type: Mapped[AlertType] = mapped_column(SAEnum(AlertType), nullable=False, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(SAEnum(AlertSeverity), nullable=False, index=True)
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus), nullable=False, default=AlertStatus.OPEN, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    alert_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True, name="metadata")

    # Optional references
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=True
    )
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True
    )

    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    webhook_dispatched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class WebhookEndpoint(UUIDPKMixin, AuditMixin, Base):
    """A registered external endpoint that receives event payloads."""
    __tablename__ = "webhook_endpoints"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False, comment="HMAC signing secret")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    event_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="Extra headers to include")

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan"
    )


class WebhookDelivery(UUIDPKMixin, Base):
    """
    Delivery attempt record.

    Every attempt (including retries) is recorded here.
    idempotency_key prevents duplicate processing on retry.
    """
    __tablename__ = "webhook_deliveries"

    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_dead_letter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    endpoint: Mapped[WebhookEndpoint] = relationship("WebhookEndpoint", back_populates="deliveries")

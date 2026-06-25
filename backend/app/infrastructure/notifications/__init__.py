"""Notification infrastructure — SMS / email delivery providers."""
from app.infrastructure.notifications.service import (
    NotificationService,
    get_notification_service,
    NotificationResult,
)

__all__ = ["NotificationService", "get_notification_service", "NotificationResult"]

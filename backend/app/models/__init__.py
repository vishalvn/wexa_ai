# Import all models here so Alembic can detect them for migrations
from app.models.user import User, Organization, UserRole
from app.models.event import Event
from app.models.dashboard import Dashboard, Widget, WidgetType
from app.models.alert import Alert, AlertHistory, AlertStatus, AlertCondition

__all__ = [
    "User", "Organization", "UserRole",
    "Event",
    "Dashboard", "Widget", "WidgetType",
    "Alert", "AlertHistory", "AlertStatus", "AlertCondition",
]

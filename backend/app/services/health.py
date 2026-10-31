from app.core.config import get_settings
from app.schemas.health import HealthResponse


def get_health_status() -> HealthResponse:
    """Build the health response without checking external services."""
    return HealthResponse(status="ok", service=get_settings().app_name)

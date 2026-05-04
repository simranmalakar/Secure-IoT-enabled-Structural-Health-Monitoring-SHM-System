"""
Alerts Router — /alerts
=========================
Provides access to anomaly detection alerts.
"""

from fastapi import APIRouter, Depends, Query
from backend.auth import get_current_user
from backend.database import get_alerts
from backend.models import AlertsResponse

router = APIRouter(tags=["Alerts"])


@router.get("/alerts", response_model=AlertsResponse)
async def get_alert_data(
    limit: int = Query(default=50, ge=1, le=500, description="Number of alerts to fetch"),
    severity: str = Query(default=None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    user: dict = Depends(get_current_user),
):
    """Fetch recent anomaly alerts. Requires JWT authentication."""
    alerts = get_alerts(limit)

    # Optional filter by severity
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.upper()]

    return AlertsResponse(count=len(alerts), alerts=alerts)


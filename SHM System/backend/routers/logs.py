"""
Security Logs Router — /logs
===============================
Provides access to IDS security event logs.
"""

from fastapi import APIRouter, Depends, Query
from backend.auth import get_current_user
from backend.database import get_security_logs
from backend.models import SecurityLogsResponse

router = APIRouter(tags=["Security Logs"])


@router.get("/logs", response_model=SecurityLogsResponse)
async def get_log_data(
    limit: int = Query(default=50, ge=1, le=500, description="Number of logs to fetch"),
    event_type: str = Query(default=None, description="Filter by event type"),
    user: dict = Depends(get_current_user),
):
    """Fetch recent security logs. Requires JWT authentication."""
    logs = get_security_logs(limit)

    # Optional filter by event type
    if event_type:
        logs = [l for l in logs if l["event_type"] == event_type.upper()]

    return SecurityLogsResponse(count=len(logs), logs=logs)


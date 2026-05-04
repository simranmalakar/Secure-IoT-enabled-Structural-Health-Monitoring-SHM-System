"""
Sensor Data Router — /sensor-data
====================================
Provides access to stored sensor readings.
"""

from fastapi import APIRouter, Depends, Query
from backend.auth import get_current_user
from backend.database import get_recent_readings
from backend.models import SensorDataResponse

router = APIRouter(tags=["Sensor Data"])


@router.get("/sensor-data", response_model=SensorDataResponse)
async def get_sensor_data(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of readings to fetch"),
    sensor_id: str = Query(default=None, description="Filter by sensor ID"),
    user: dict = Depends(get_current_user),
):
    """Fetch recent sensor readings. Requires JWT authentication."""
    readings = get_recent_readings(limit)

    # Optional filter by sensor_id
    if sensor_id:
        readings = [r for r in readings if r["sensor_id"] == sensor_id]

    return SensorDataResponse(count=len(readings), readings=readings)


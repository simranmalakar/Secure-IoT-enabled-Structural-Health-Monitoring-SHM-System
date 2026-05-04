"""
Pydantic Models — FastAPI Backend
===================================
Request/response schemas for the API endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    username: str
    role: str


# --- Sensor Data ---
class SensorReading(BaseModel):
    id: int
    sensor_id: str
    timestamp: str
    vibration: float
    tilt: float
    strain: float
    hash: str
    anomaly_score: float = 0.0
    anomaly_class: str = "NORMAL"
    prediction: float = 0.0
    explanation: str = ""
    received_at: str


class SensorDataResponse(BaseModel):
    count: int
    readings: List[dict]


# --- Alerts ---
class Alert(BaseModel):
    id: int
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    value: Optional[float]
    threshold: Optional[float]
    timestamp: str


class AlertsResponse(BaseModel):
    count: int
    alerts: List[dict]


# --- Security Logs ---
class SecurityLog(BaseModel):
    id: int
    event_type: str
    source: Optional[str]
    details: Optional[str]
    severity: str
    timestamp: str


class SecurityLogsResponse(BaseModel):
    count: int
    logs: List[dict]


# --- Health ---
class HealthResponse(BaseModel):
    status: str
    total_readings: int
    total_alerts: int
    total_security_events: int
    critical_alerts: int
    active_sensors: int


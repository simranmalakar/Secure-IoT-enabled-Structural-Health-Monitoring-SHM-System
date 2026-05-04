"""
FastAPI Main Application — Secure IoT SHM Backend
====================================================
REST API server with JWT authentication, CORS support,
and endpoints for sensor data, alerts, and security logs.

Usage:
    uvicorn backend.main:app --reload --port 8000
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth import verify_credentials, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models import LoginRequest, TokenResponse, HealthResponse
from backend.database import get_stats, init_database, insert_security_log
from backend.routers import sensor, alerts, logs, simulate

# --- Initialize ---
init_database()

app = FastAPI(
    title="Secure IoT SHM API",
    description="REST API for Structural Health Monitoring with JWT authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Serve Dashboard Static Files ---
dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

# --- Include Routers ---
app.include_router(sensor.router)
app.include_router(alerts.router)
app.include_router(logs.router)
app.include_router(simulate.router)


# --- Auth Endpoint ---
@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = verify_credentials(request.username, request.password)
    if not user:
        insert_security_log(
            event_type="UNAUTHORIZED_ACCESS",
            source="127.0.0.1",
            details=f"Failed login attempt for user: {request.username}",
            severity="MEDIUM"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        username=user["username"],
        role=user["role"],
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# --- Health Check ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check — no authentication required."""
    stats = get_stats()
    return HealthResponse(status="healthy", **stats)


# --- Root ---
@app.get("/")
async def root():
    """API root — basic info."""
    return {
        "name": "Secure IoT SHM API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/health",
    }


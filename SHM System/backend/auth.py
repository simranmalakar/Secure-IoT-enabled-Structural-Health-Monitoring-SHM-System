"""
JWT Authentication — FastAPI Backend
=======================================
Handles user login and JWT token creation/validation.
Uses HS256 algorithm with 60-minute token expiry.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# --- Configuration ---
SECRET_KEY = "shm-iot-jwt-secret-key-2024-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Demo Credentials ---
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password": "shm@secure2024",
        "role": "administrator",
    }
}

# --- Security scheme ---
security = HTTPBearer()


def verify_credentials(username: str, password: str) -> Optional[dict]:
    """Verify user credentials against the demo user store."""
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return {"username": user["username"], "role": user["role"]}
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency: extract and validate the current user from JWT."""
    token = credentials.credentials
    payload = decode_token(token)
    return {
        "username": payload.get("sub"),
        "role": payload.get("role", "user"),
    }


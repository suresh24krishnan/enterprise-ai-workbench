"""
Health check endpoint.
Used by Docker Compose, load balancers, and monitoring systems.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    environment: str
    timestamp: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
    )

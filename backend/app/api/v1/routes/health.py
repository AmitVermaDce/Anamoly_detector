"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """Return application health status.

    Returns:
        HealthResponse: Health status, version, and current timestamp.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )

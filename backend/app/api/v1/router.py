"""V1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1.routes import anomaly, health

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(anomaly.router)

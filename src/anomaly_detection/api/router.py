from fastapi import APIRouter

from anomaly_detection.api.endpoints import anomaly, health

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(anomaly.router)

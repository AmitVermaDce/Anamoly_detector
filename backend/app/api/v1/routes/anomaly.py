"""Anomaly detection API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config_service import ConfigService
from app.core.exceptions import ApplicationException
from app.models.schemas import (
    AlgorithmListResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    DetectionLevelListResponse,
    QueryListResponse,
)
from app.services.anomaly_service import AnomalyDetectionService
from app.services.data_service import DataService

router = APIRouter()


def get_data_service() -> DataService:
    """Dependency injection for DataService.

    Returns:
        DataService: Data service instance.
    """
    cfg = ConfigService()
    return DataService(config_service=cfg)


def get_anomaly_service() -> AnomalyDetectionService:
    """Dependency injection for AnomalyDetectionService.

    Returns:
        AnomalyDetectionService: Anomaly detection service instance.
    """
    cfg = ConfigService()
    return AnomalyDetectionService(config_service=cfg)


@router.get(
    "/queries",
    response_model=QueryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available queries",
    tags=["Queries"],
)
async def list_queries(
    data_service: DataService = Depends(get_data_service),
) -> QueryListResponse:
    """Return all available named SQL queries.

    Returns:
        QueryListResponse: List of query names.

    Raises:
        HTTPException: If the query file cannot be found or read.
    """
    try:
        queries = data_service.list_queries()
        return QueryListResponse(queries=queries)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query file not found: {exc}. Ensure the queries directory is present and config.yaml paths are correct.",
        ) from exc


@router.get(
    "/algorithms",
    response_model=AlgorithmListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available algorithms",
    tags=["Algorithms"],
)
async def list_algorithms(
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service),
) -> AlgorithmListResponse:
    """Return all available anomaly detection algorithms.

    Returns:
        AlgorithmListResponse: List of algorithm metadata.
    """
    algorithms = anomaly_service.list_algorithms()
    return AlgorithmListResponse(algorithms=algorithms)


@router.get(
    "/levels",
    response_model=DetectionLevelListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available detection levels",
    tags=["Detection Levels"],
)
async def list_detection_levels(
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service),
) -> DetectionLevelListResponse:
    """Return all configured detection levels from config.yaml.

    Returns:
        DetectionLevelListResponse: List of detection level metadata.
    """
    levels = anomaly_service.list_detection_levels()
    return DetectionLevelListResponse(levels=levels)


@router.post(
    "/detect",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run anomaly detection",
    tags=["Anomaly Detection"],
)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    anomaly_service: AnomalyDetectionService = Depends(get_anomaly_service),
) -> AnomalyDetectionResponse:
    """Execute a query and run anomaly detection on the results.

    Args:
        request: Anomaly detection request parameters.
        anomaly_service: Injected anomaly detection service.

    Returns:
        AnomalyDetectionResponse: Detection results with records and summary.

    Raises:
        HTTPException: If an application error occurs.
    """
    try:
        params: dict[str, Any] = request.parameters.copy()
        if request.start_date:
            params["start_date"] = request.start_date.isoformat()
            params["start_timestamp"] = request.start_date.isoformat()
        if request.end_date:
            params["end_date"] = request.end_date.isoformat()
            params["end_timestamp"] = request.end_date.isoformat()

        result = anomaly_service.detect(
            query_name=request.query_name,
            algorithm=request.algorithm,
            columns=request.columns or None,
            parameters=request.parameters or {},
            query_parameters=params,
            detection_level=request.detection_level,
        )
        return AnomalyDetectionResponse(**result)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(exc)}",
        ) from exc

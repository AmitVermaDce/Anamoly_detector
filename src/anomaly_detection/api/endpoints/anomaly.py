from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from anomaly_detection.api.schemas import (
    AlgorithmListResponse,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    DetectionLevelListResponse,
    QueryListResponse,
)
from anomaly_detection.config import Config
from anomaly_detection.exceptions import ApplicationException
from anomaly_detection.services.data import DataService
from anomaly_detection.services.detection import DetectionService
from anomaly_detection import state

router = APIRouter()


def _get_config() -> Config:
    return state.config


def get_data_service() -> DataService:
    return DataService(config=_get_config(), query_loader=state.query_loader)


def get_detection_service() -> DetectionService:
    return DetectionService(config=_get_config(), data_service=get_data_service())


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
    try:
        queries = data_service.list_queries()
        return QueryListResponse(queries=queries)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query file not found: {exc}",
        ) from exc


@router.get(
    "/algorithms",
    response_model=AlgorithmListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available algorithms",
    tags=["Algorithms"],
)
async def list_algorithms(
    detection_service: DetectionService = Depends(get_detection_service),
) -> AlgorithmListResponse:
    algorithms = detection_service.list_algorithms()
    return AlgorithmListResponse(algorithms=algorithms)


@router.get(
    "/levels",
    response_model=DetectionLevelListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available detection levels",
    tags=["Detection Levels"],
)
async def list_detection_levels(
    detection_service: DetectionService = Depends(get_detection_service),
) -> DetectionLevelListResponse:
    levels = detection_service.list_detection_levels()
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
    detection_service: DetectionService = Depends(get_detection_service),
) -> AnomalyDetectionResponse:
    try:
        params: dict[str, Any] = request.parameters.copy()
        if request.start_date:
            params["start_date"] = request.start_date.isoformat()
            params["start_timestamp"] = request.start_date.isoformat()
        if request.end_date:
            params["end_date"] = request.end_date.isoformat()
            params["end_timestamp"] = request.end_date.isoformat()

        result = detection_service.detect(
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

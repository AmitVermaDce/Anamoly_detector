from typing import Any, Dict, List, Optional
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryListResponse(BaseModel):
    queries: List[str] = Field(..., description="List of available query names")


class AnomalyDetectionRequest(BaseModel):
    query_name: str = Field(..., description="Name of the SQL query to execute")
    algorithm: Literal["isolation_forest", "zscore", "dbscan"] = Field(
        default="isolation_forest", description="Anomaly detection algorithm"
    )
    detection_level: Optional[str] = Field(
        None, description="Detection level name from config (e.g. by_client)"
    )
    columns: List[str] = Field(
        default_factory=list, description="Columns to include in anomaly detection"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Detector-specific parameters"
    )
    start_date: Optional[date] = Field(None, description="Start date for data filtering")
    end_date: Optional[date] = Field(None, description="End date for data filtering")


class AnomalyRecord(BaseModel):
    is_anomaly: bool = Field(..., description="Whether the record is an anomaly")
    anomaly_score: Optional[float] = Field(None, description="Anomaly score")
    algorithm: str = Field(..., description="Algorithm used for detection")


class AnomalyDetectionResponse(BaseModel):
    query_name: str = Field(..., description="Name of the executed query")
    algorithm: str = Field(..., description="Algorithm used")
    detection_level: Optional[str] = Field(None, description="Detection level used")
    total_records: int = Field(..., description="Total number of records processed")
    anomaly_count: int = Field(..., description="Number of anomalies detected")
    anomaly_rate: float = Field(..., description="Percentage of records flagged as anomalies")
    records: List[Dict[str, Any]] = Field(..., description="Records with anomaly flags")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


class AlgorithmInfo(BaseModel):
    name: str = Field(..., description="Algorithm identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Algorithm description")


class DetectionLevelInfo(BaseModel):
    name: str = Field(..., description="Level identifier")
    group_cols: List[str] = Field(..., description="Columns used for grouping/aggregation")
    description: str = Field(..., description="Level description")


class DetectionLevelListResponse(BaseModel):
    levels: List[DetectionLevelInfo] = Field(..., description="List of available detection levels")


class AlgorithmListResponse(BaseModel):
    algorithms: List[AlgorithmInfo] = Field(..., description="List of available algorithms")

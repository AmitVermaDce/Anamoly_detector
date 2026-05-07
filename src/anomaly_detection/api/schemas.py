from typing import Any, Dict, List, Optional
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryListResponse(BaseModel):
    queries: List[str]


class ArtifactInfo(BaseModel):
    name: str
    filename: str
    size_bytes: int
    modified: float


class ArtifactListResponse(BaseModel):
    artifacts: List[ArtifactInfo]


class AnomalyDetectionRequest(BaseModel):
    query_name: str
    algorithm: Literal["isolation_forest", "zscore", "dbscan"] = "isolation_forest"
    fetch: bool = False
    detection_level: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AnomalyDetectionResponse(BaseModel):
    query_name: str
    algorithm: str
    fetch: bool = False
    detection_level: Optional[str] = None
    total_records: int
    anomaly_count: int
    anomaly_rate: float
    records: List[Dict[str, Any]]
    summary: Dict[str, Any] = Field(default_factory=dict)


class AlgorithmInfo(BaseModel):
    name: str
    display_name: str
    description: str


class DetectionLevelInfo(BaseModel):
    name: str
    group_cols: List[str]
    description: str


class DetectionLevelListResponse(BaseModel):
    levels: List[DetectionLevelInfo]


class AlgorithmListResponse(BaseModel):
    algorithms: List[AlgorithmInfo]

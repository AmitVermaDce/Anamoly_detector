from __future__ import annotations

from typing import Any

from anomaly_detection.detection.base import BaseDetector
from anomaly_detection.detection.dbscan import DBSCANDetector
from anomaly_detection.detection.isolation_forest import IsolationForestDetector
from anomaly_detection.detection.zscore import ZScoreDetector
from anomaly_detection.exceptions import InvalidAlgorithmError

_REGISTRY: dict[str, type[BaseDetector]] = {
    "isolation_forest": IsolationForestDetector,
    "zscore": ZScoreDetector,
    "dbscan": DBSCANDetector,
}


def create_detector(name: str, runtime: dict[str, Any] | None = None) -> BaseDetector:
    if name not in _REGISTRY:
        raise InvalidAlgorithmError(name)
    cls = _REGISTRY[name]
    params = cls.default_params()
    if runtime:
        params.update(runtime)
    return cls(params)

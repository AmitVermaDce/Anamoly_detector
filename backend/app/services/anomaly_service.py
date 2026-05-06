from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.config import ApplicationSettings, get_settings
from app.core.config_service import ConfigService
from app.core.exceptions import InvalidAlgorithmError
from app.core.logger import get_application_logger
from app.models.detectors.base_detector import BaseDetector
from app.models.detectors.dbscan_detector import DBSCANDetector
from app.models.detectors.isolation_forest import IsolationForestDetector
from app.models.detectors.zscore_detector import ZScoreDetector
from app.services.data_service import DataService
from app.utils.helpers import DataFrameSerializer


class AnomalyDetectionService:
    """Orchestrates data fetching and anomaly detection."""

    _registry: dict[str, type[BaseDetector]] = {
        "isolation_forest": IsolationForestDetector,
        "zscore": ZScoreDetector,
        "dbscan": DBSCANDetector,
    }

    def __init__(
        self,
        settings: ApplicationSettings | None = None,
        data_service: DataService | None = None,
        config_service: ConfigService | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._logger = get_application_logger()
        self._config = config_service or ConfigService()
        self._data_service = data_service or DataService(
            settings=self._settings, config_service=self._config
        )

    def list_algorithms(self) -> list[dict[str, str]]:
        return [
            {
                "name": "isolation_forest",
                "display_name": "Isolation Forest",
                "description": (
                    "Isolates anomalies by randomly selecting features and split values. "
                    "Anomalies are few and different, making them more susceptible to isolation."
                ),
            },
            {
                "name": "zscore",
                "display_name": "Z-Score",
                "description": (
                    "Standardizes each data point and flags records where the absolute "
                    "Z-Score exceeds a configurable threshold. Best for normally distributed data."
                ),
            },
            {
                "name": "dbscan",
                "display_name": "DBSCAN",
                "description": (
                    "Density-Based Spatial Clustering marks points in low-density regions "
                    "as anomalies. Does not assume a particular distribution."
                ),
            },
        ]

    def list_detection_levels(self) -> list[dict[str, Any]]:
        levels = self._config.detection_levels()
        return [
            {
                "name": name,
                "group_cols": cfg.get("group_cols", []),
                "description": cfg.get("description", f"Aggregate by {', '.join(cfg.get('group_cols', []))}"),
            }
            for name, cfg in levels.items()
        ]

    def get_detector(self, algorithm: str, parameters: dict[str, Any] | None = None) -> BaseDetector:
        if algorithm not in self._registry:
            raise InvalidAlgorithmError(algorithm)
        return self._registry[algorithm](parameters)

    def detect(
        self,
        query_name: str,
        algorithm: str,
        columns: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        query_parameters: dict[str, Any] | None = None,
        detection_level: str | None = None,
    ) -> dict[str, Any]:
        self._logger.info(
            "Detecting anomalies: query={query}, algorithm={algorithm}, level={level}",
            query=query_name,
            algorithm=algorithm,
            level=detection_level or "default",
        )

        merged = self._config.detection_params().copy()
        if parameters:
            merged.update(parameters)

        dataframe = self._data_service.fetch_data(query_name, query_parameters)
        detector = self.get_detector(algorithm, merged)
        result = detector.detect(dataframe, columns)

        total = len(result)
        anomalies = int(result["is_anomaly"].sum())
        rate = round((anomalies / total * 100), 2) if total > 0 else 0.0

        self._logger.info(
            "Detection complete: {anomalies}/{total} anomalies ({rate}%)",
            anomalies=anomalies,
            total=total,
            rate=rate,
        )

        return {
            "query_name": query_name,
            "algorithm": algorithm,
            "detection_level": detection_level,
            "total_records": total,
            "anomaly_count": anomalies,
            "anomaly_rate": rate,
            "records": DataFrameSerializer.to_records(result),
            "summary": self._compute_summary(result),
        }

    def _compute_summary(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "total_records": len(dataframe),
            "anomaly_count": int(dataframe["is_anomaly"].sum()),
            "normal_count": int((~dataframe["is_anomaly"]).sum()),
        }

        if "anomaly_score" in dataframe.columns:
            scores = dataframe.loc[dataframe["is_anomaly"], "anomaly_score"]
            if not scores.empty:
                summary["mean_anomaly_score"] = round(float(scores.mean()), 4)
                summary["max_anomaly_score"] = round(float(scores.max()), 4)

            bins = [0, 0.33, 0.66, 1.0]
            labels = ["low", "medium", "high"]
            severity = pd.cut(
                dataframe.loc[dataframe["is_anomaly"], "anomaly_score"].fillna(0),
                bins=bins,
                labels=labels,
                include_lowest=True,
            )
            summary["severity_distribution"] = severity.value_counts().to_dict()
        else:
            summary["severity_distribution"] = {}

        return summary

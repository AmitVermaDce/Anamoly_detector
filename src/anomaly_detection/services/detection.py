from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger

from anomaly_detection.config import Config, Settings, get_settings
from anomaly_detection.detection.factory import create_detector
from anomaly_detection.services.data import DataService
from anomaly_detection import state


def _records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    return dataframe.replace({pd.NA: None, pd.NaT: None}).to_dict(orient="records")


_ALGORITHMS: list[dict[str, str]] = [
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


class DetectionService:
    def __init__(
        self,
        settings: Settings | None = None,
        data_service: DataService | None = None,
        config: Config | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._config = config or state.config
        self._data_service = data_service or DataService(
            settings=self._settings, config=self._config
        )

    def list_algorithms(self) -> list[dict[str, str]]:
        return _ALGORITHMS

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

    def detect(
        self,
        query_name: str,
        algorithm: str,
        columns: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        query_parameters: dict[str, Any] | None = None,
        detection_level: str | None = None,
        fetch: bool = False,
    ) -> dict[str, Any]:
        logger.info(
            "Detecting anomalies: query={query}, algorithm={algorithm}, fetch={fetch}",
            query=query_name,
            algorithm=algorithm,
            fetch=fetch,
        )

        merged = self._config.detection_params().copy()
        if parameters:
            merged.update(parameters)

        dataframe = self._data_service.fetch_data(query_name, query_parameters, fetch=fetch)
        detector = create_detector(algorithm, merged)
        result = detector.detect(dataframe, columns)

        total = len(result)
        anomalies = int(result["is_anomaly"].sum())
        rate = round((anomalies / total * 100), 2) if total > 0 else 0.0

        logger.info(
            "Detection complete: {anomalies}/{total} anomalies ({rate}%)",
            anomalies=anomalies,
            total=total,
            rate=rate,
        )

        return {
            "query_name": query_name,
            "algorithm": algorithm,
            "fetch": fetch,
            "detection_level": detection_level,
            "total_records": total,
            "anomaly_count": anomalies,
            "anomaly_rate": rate,
            "records": _records(result),
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

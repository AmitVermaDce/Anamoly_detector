from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

from app.core.config import get_settings
from app.core.exceptions import DetectionAlgorithmError
from app.core.logger import get_application_logger
from app.models.detectors.base_detector import BaseDetector


class DBSCANDetector(BaseDetector):
    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        settings = get_settings()
        merged = {
            "eps": settings.dbscan_eps,
            "min_samples": settings.dbscan_min_samples,
        }
        if parameters:
            merged.update(parameters)
        super().__init__(name="dbscan", parameters=merged)
        self._logger = get_application_logger()

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric_columns(data, columns)
            if numeric.empty:
                raise DetectionAlgorithmError("No numeric columns available for detection.")

            clean = numeric.fillna(numeric.mean())
            scaled = StandardScaler().fit_transform(clean)
            model = DBSCAN(eps=self.parameters["eps"], min_samples=self.parameters["min_samples"])
            labels = model.fit_predict(scaled)
            is_anomaly = labels == -1

            if hasattr(model, "components_") and model.components_ is not None:
                distances = pairwise_distances(scaled, model.components_, metric="euclidean")
                min_dist = distances.min(axis=1)
                max_dist = min_dist.max()
                score = min_dist / max_dist if max_dist > 0 else np.zeros_like(min_dist)
            else:
                score = is_anomaly.astype(float)

            result = data.copy()
            result["is_anomaly"] = is_anomaly
            result["anomaly_score"] = score
            result["algorithm"] = self.name

            self._logger.info(
                "DBSCAN detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except DetectionAlgorithmError:
            raise
        except Exception as exc:
            self._logger.error("DBSCAN failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"DBSCAN detection failed: {exc}") from exc

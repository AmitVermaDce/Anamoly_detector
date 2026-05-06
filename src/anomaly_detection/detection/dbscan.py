from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler
from loguru import logger

from anomaly_detection.config import get_settings
from anomaly_detection.detection.base import BaseDetector
from anomaly_detection.exceptions import DetectionAlgorithmError


class DBSCANDetector(BaseDetector):
    @classmethod
    def default_params(cls) -> dict[str, Any]:
        s = get_settings()
        return {
            "eps": s.dbscan_eps,
            "min_samples": s.dbscan_min_samples,
        }

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric(data, columns)
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

            result = self._build_result(data, is_anomaly, score)
            logger.info(
                "DBSCAN detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except Exception as exc:
            logger.error("DBSCAN failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"DBSCAN detection failed: {exc}") from exc

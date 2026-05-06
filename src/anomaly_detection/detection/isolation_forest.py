from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.ensemble import IsolationForest
from loguru import logger

from anomaly_detection.config import get_settings
from anomaly_detection.detection.base import BaseDetector
from anomaly_detection.exceptions import DetectionAlgorithmError


class IsolationForestDetector(BaseDetector):
    @classmethod
    def default_params(cls) -> dict[str, Any]:
        s = get_settings()
        return {
            "contamination": s.isolation_forest_contamination,
            "random_state": s.isolation_forest_random_state,
            "n_estimators": 100,
        }

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric(data, columns)
            if numeric.empty:
                raise DetectionAlgorithmError("No numeric columns available for detection.")

            clean = numeric.fillna(numeric.mean())
            model = IsolationForest(
                contamination=self.parameters["contamination"],
                random_state=self.parameters["random_state"],
                n_estimators=self.parameters["n_estimators"],
            )
            predictions = model.fit_predict(clean)
            scores = model.decision_function(clean)

            result = self._build_result(data, predictions == -1, -scores)
            logger.info(
                "Isolation Forest detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except Exception as exc:
            logger.error("Isolation Forest failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"Isolation Forest detection failed: {exc}") from exc

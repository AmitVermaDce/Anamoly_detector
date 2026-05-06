from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.core.config import get_settings
from app.core.exceptions import DetectionAlgorithmError
from app.core.logger import get_application_logger
from app.models.detectors.base_detector import BaseDetector


class IsolationForestDetector(BaseDetector):
    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        settings = get_settings()
        merged = {
            "contamination": settings.isolation_forest_contamination,
            "random_state": settings.isolation_forest_random_state,
            "n_estimators": 100,
        }
        if parameters:
            merged.update(parameters)
        super().__init__(name="isolation_forest", parameters=merged)
        self._logger = get_application_logger()

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric_columns(data, columns)
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

            result = data.copy()
            result["is_anomaly"] = predictions == -1
            result["anomaly_score"] = -scores
            result["algorithm"] = self.name

            self._logger.info(
                "Isolation Forest detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except DetectionAlgorithmError:
            raise
        except Exception as exc:
            self._logger.error("Isolation Forest failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"Isolation Forest detection failed: {exc}") from exc

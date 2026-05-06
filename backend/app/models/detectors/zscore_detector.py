from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import DetectionAlgorithmError
from app.core.logger import get_application_logger
from app.models.detectors.base_detector import BaseDetector


class ZScoreDetector(BaseDetector):
    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        settings = get_settings()
        merged = {"threshold": settings.zscore_threshold}
        if parameters:
            merged.update(parameters)
        super().__init__(name="zscore", parameters=merged)
        self._logger = get_application_logger()

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric_columns(data, columns)
            if numeric.empty:
                raise DetectionAlgorithmError("No numeric columns available for detection.")

            means = numeric.mean()
            stds = numeric.std(ddof=0).replace(0, np.nan)
            z_scores = ((numeric - means) / stds).abs()
            max_z = z_scores.max(axis=1)

            result = data.copy()
            result["is_anomaly"] = (max_z > self.parameters["threshold"]).fillna(False)
            result["anomaly_score"] = max_z.fillna(0.0)
            result["algorithm"] = self.name

            self._logger.info(
                "Z-Score detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except DetectionAlgorithmError:
            raise
        except Exception as exc:
            self._logger.error("Z-Score failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"Z-Score detection failed: {exc}") from exc

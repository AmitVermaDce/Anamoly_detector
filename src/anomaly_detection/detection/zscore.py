from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from anomaly_detection.config import get_settings
from anomaly_detection.detection.base import BaseDetector
from anomaly_detection.exceptions import DetectionAlgorithmError


class ZScoreDetector(BaseDetector):
    @classmethod
    def default_params(cls) -> dict[str, Any]:
        s = get_settings()
        return {"threshold": s.zscore_threshold}

    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        try:
            numeric = self._select_numeric(data, columns)
            if numeric.empty:
                raise DetectionAlgorithmError("No numeric columns available for detection.")

            means = numeric.mean()
            stds = numeric.std(ddof=0).replace(0, np.nan)
            z_scores = ((numeric - means) / stds).abs()
            max_z = z_scores.max(axis=1)

            result = self._build_result(
                data,
                (max_z > self.parameters["threshold"]).fillna(False),
                max_z.fillna(0.0),
            )
            logger.info(
                "Z-Score detected {count}/{total} anomalies",
                count=int(result["is_anomaly"].sum()),
                total=len(result),
            )
            return result
        except Exception as exc:
            logger.error("Z-Score failed: {error}", error=str(exc))
            raise DetectionAlgorithmError(f"Z-Score detection failed: {exc}") from exc

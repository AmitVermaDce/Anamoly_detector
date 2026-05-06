from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseDetector(ABC):
    def __init__(self, name: str, parameters: dict[str, Any] | None = None) -> None:
        self.name = name
        self.parameters = parameters or {}

    @abstractmethod
    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """Run detection and return DataFrame with is_anomaly, anomaly_score, algorithm columns."""

    @staticmethod
    def _select_numeric(data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        selected = data[columns] if columns else data
        return selected.select_dtypes(include=["number"])

    def _build_result(self, data: pd.DataFrame, is_anomaly, anomaly_score) -> pd.DataFrame:
        result = data.copy()
        result["is_anomaly"] = is_anomaly
        result["anomaly_score"] = anomaly_score
        result["algorithm"] = self.name
        return result

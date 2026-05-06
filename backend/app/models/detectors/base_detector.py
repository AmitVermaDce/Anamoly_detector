from __future__ import annotations
"""Abstract base class for anomaly detection algorithms."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseDetector(ABC):
    """Abstract base class for anomaly detection strategies.

    Implementations must provide the detect method which accepts a pandas DataFrame
    and returns a DataFrame augmented with anomaly flags and scores.
    """

    def __init__(self, name: str, parameters: dict[str, Any] | None = None) -> None:
        self.name = name
        self.parameters = parameters or {}

    @abstractmethod
    def detect(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """Run anomaly detection on the provided data.

        Args:
            data: Input DataFrame with numeric columns.
            columns: Optional list of column names to include. If None, all numeric columns are used.

        Returns:
            pd.DataFrame: The original DataFrame with added 'is_anomaly' and 'anomaly_score' columns.
        """

    def _select_numeric_columns(self, data: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """Select numeric columns from the DataFrame.

        Args:
            data: Input DataFrame.
            columns: Optional list of columns to include.

        Returns:
            pd.DataFrame: Numeric columns only.
        """
        if columns:
            selected = data[columns]
        else:
            selected = data

        numeric = selected.select_dtypes(include=["number"])
        return numeric

    def get_parameters(self) -> dict[str, Any]:
        """Return the detector's configured parameters.

        Returns:
            dict[str, Any]: Parameter dictionary.
        """
        return self.parameters.copy()

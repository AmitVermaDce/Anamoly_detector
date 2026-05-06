"""Utility helpers for the application."""

import json
from datetime import date, datetime
from typing import Any

import pandas as pd


class JSONEncoder(json.JSONEncoder):
    """Extended JSON encoder supporting pandas timestamps and numpy types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, "item"):
            return obj.item()
        return super().default(obj)


class DataFrameSerializer:
    """Serializes pandas DataFrames to JSON-compatible structures."""

    @staticmethod
    def to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a DataFrame to a list of dictionaries.

        Args:
            dataframe: The pandas DataFrame.

        Returns:
            list[dict[str, Any]]: Records as dictionaries.
        """
        return dataframe.replace({pd.NA: None, pd.NaT: None}).to_dict(orient="records")

    @staticmethod
    def to_json(dataframe: pd.DataFrame) -> str:
        """Convert a DataFrame to a JSON string.

        Args:
            dataframe: The pandas DataFrame.

        Returns:
            str: JSON string representation.
        """
        records = DataFrameSerializer.to_records(dataframe)
        return json.dumps(records, cls=JSONEncoder)

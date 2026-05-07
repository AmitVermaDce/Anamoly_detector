from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from anomaly_detection.config import Config, Settings, get_settings
from anomaly_detection.database.credentials import CredentialManager
from anomaly_detection.database.queries import SQLQueryLoader
from anomaly_detection.database.snowflake import SnowflakeClient
from anomaly_detection.exceptions import QueryExecutionError
from anomaly_detection import state


class DataService:
    """Loads base data once (Snowflake or CSV) and aggregates per detection level."""

    def __init__(
        self,
        settings: Settings | None = None,
        snowflake_client: SnowflakeClient | None = None,
        query_loader: SQLQueryLoader | None = None,
        config: Config | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._snowflake_client = snowflake_client
        self._config = config or state.config
        self._query_loader = query_loader or state.query_loader
        self._base_df: pd.DataFrame | None = None

    def list_queries(self) -> list[str]:
        """Return detection level names (used as virtual query names)."""
        return list(self._config.detection_levels().keys())

    def _get_client(self) -> SnowflakeClient:
        if self._snowflake_client is None:
            from anomaly_detection import state
            if state.snowflake_client is not None:
                self._snowflake_client = state.snowflake_client
            else:
                self._snowflake_client = SnowflakeClient(self._settings)
        return self._snowflake_client

    def _load_local_csv(self) -> pd.DataFrame | None:
        local_csv = self._config.get("local_csv")
        if not local_csv:
            return None
        csv_path = Path(__file__).resolve().parent.parent.parent / local_csv
        if not csv_path.exists():
            return None
        logger.info("Loading local CSV: {path}", path=str(csv_path))
        df = pd.read_csv(csv_path, parse_dates=["DT"])
        logger.info("CSV loaded: {rows} rows", rows=len(df))
        return df

    def _fetch_base(self) -> pd.DataFrame:
        """Fetch base data from Snowflake or CSV fallback."""
        if self._base_df is not None:
            return self._base_df

        # Try CSV first (for dev/testing)
        df = self._load_local_csv()
        if df is not None:
            self._base_df = df
            return df

        query_key = self._config.get("query_key", "base")
        if self._query_loader is None:
            raise QueryExecutionError("Query loader not available.")
        sql = self._query_loader.get_query(query_key)

        logger.info("Executing base query '{key}' against Snowflake", key=query_key)
        cred_mgr = CredentialManager()
        conn = cred_mgr.get_snowflake_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            df = cur.fetch_pandas_all()
            logger.info("Base query returned {rows} rows", rows=len(df))
        finally:
            conn.close()

        if "DT" in df.columns:
            df["DT"] = pd.to_datetime(df["DT"])

        self._base_df = df
        return df

    def aggregate(self, level_name: str) -> pd.DataFrame:
        """Aggregate base data by detection level."""
        levels = self._config.detection_levels()
        if level_name not in levels:
            raise QueryExecutionError(
                f"Detection level '{level_name}' not found. "
                f"Available: {list(levels.keys())}"
            )

        group_cols = levels[level_name]["group_cols"]
        base = self._fetch_base()

        agg = (
            base.groupby(["DT"] + group_cols, as_index=False)["ISSUE_VOLUME"]
            .sum()
        )
        logger.info(
            "Level '{level}': aggregated to {rows} rows (groups: {cols})",
            level=level_name,
            rows=len(agg),
            cols=group_cols,
        )
        return agg

    def fetch_data(
        self,
        query_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Fetch data for a virtual query (maps to detection level aggregation)."""
        try:
            return self.aggregate(query_name)
        except Exception as exc:
            logger.error("Data fetch failed: {error}", error=str(exc))
            raise QueryExecutionError(f"Failed to fetch data for '{query_name}': {exc}") from exc

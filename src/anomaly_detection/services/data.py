from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from anomaly_detection.config import Config, Settings, get_settings
from anomaly_detection.database.queries import SQLQueryLoader
from anomaly_detection.database.snowflake import SnowflakeClient
from anomaly_detection.exceptions import QueryExecutionError
from anomaly_detection import state


class DataService:
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

        if query_loader is None:
            from anomaly_detection import state
            self._query_loader = state.query_loader or SQLQueryLoader(self._resolve_query_path())
        else:
            self._query_loader = query_loader

    def _resolve_query_path(self) -> Path:
        queries_dir = self._config.queries_dir()
        query_file = self._config.query_file()
        if queries_dir and query_file:
            package_root = Path(__file__).resolve().parent.parent.parent
            return package_root / queries_dir / query_file
        return Path(__file__).parent.parent / "sql" / "queries.sql"

    def list_queries(self) -> list[str]:
        return self._query_loader.list_queries()

    def fetch_data(
        self,
        query_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        try:
            query = self._query_loader.get_query(query_name)
            params = parameters or {}
            logger.info("Executing query '{name}'", name=query_name)

            dataframe = self._get_client().execute_query(query, params)

            logger.info("Query '{name}' returned {rows} rows", name=query_name, rows=len(dataframe))
            return dataframe
        except Exception as exc:
            logger.error("Query '{name}' failed: {error}", name=query_name, error=str(exc))
            raise QueryExecutionError(f"Failed to fetch data for query '{query_name}': {exc}") from exc

    def _get_client(self) -> SnowflakeClient:
        if self._snowflake_client is None:
            from anomaly_detection import state
            if state.snowflake_client is not None:
                self._snowflake_client = state.snowflake_client
            else:
                self._snowflake_client = SnowflakeClient(self._settings)
        return self._snowflake_client

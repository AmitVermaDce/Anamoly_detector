from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import ApplicationSettings, get_settings
from app.core.config_service import ConfigService
from app.core.exceptions import QueryExecutionError
from app.core.logger import get_application_logger
from app.db.query_loader import SQLQueryLoader
from app.db.snowflake_client import SnowflakeClient
from app.utils.helpers import DataFrameSerializer


class DataService:
    """Loads queries and fetches data from Snowflake."""

    def __init__(
        self,
        settings: ApplicationSettings | None = None,
        snowflake_client: SnowflakeClient | None = None,
        query_loader: SQLQueryLoader | None = None,
        config_service: ConfigService | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._logger = get_application_logger()
        self._snowflake_client = snowflake_client

        if query_loader is None:
            cfg = config_service or ConfigService()
            self._query_loader = SQLQueryLoader(self._resolve_query_path(cfg))
        else:
            self._query_loader = query_loader

    def _resolve_query_path(self, config: ConfigService) -> Path:
        queries_dir = config.queries_dir()
        query_file = config.query_file()
        if queries_dir and query_file:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            return project_root / queries_dir / query_file
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
            self._logger.info("Executing query '{name}'", name=query_name)

            client = self._get_client()
            with client:
                dataframe = client.execute_query(query, params)

            self._logger.info("Query '{name}' returned {rows} rows", name=query_name, rows=len(dataframe))
            return dataframe
        except Exception as exc:
            self._logger.error("Query '{name}' failed: {error}", name=query_name, error=str(exc))
            raise QueryExecutionError(f"Failed to fetch data for query '{query_name}': {exc}") from exc

    def fetch_data_as_records(
        self,
        query_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return DataFrameSerializer.to_records(self.fetch_data(query_name, parameters))

    def _get_client(self) -> SnowflakeClient:
        if self._snowflake_client is None:
            self._snowflake_client = SnowflakeClient(self._settings)
        return self._snowflake_client

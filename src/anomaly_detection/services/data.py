from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from anomaly_detection.config import Config, Settings, get_settings
from anomaly_detection.database.credentials import CredentialManager
from anomaly_detection.database.queries import SQLQueryLoader
from anomaly_detection.exceptions import QueryExecutionError
from anomaly_detection import state


class DataService:
    """Fetches query data from Snowflake or loads cached artifacts."""

    def __init__(
        self,
        settings: Settings | None = None,
        query_loader: SQLQueryLoader | None = None,
        config: Config | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._config = config or state.config
        self._query_loader = query_loader or state.query_loader

    # ------------------------------------------------------------------ paths
    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    def _artifacts_dir(self) -> Path:
        rel = self._config.artifacts_dir() or "artifacts"
        return self._project_root() / rel

    def _artifact_path(self, query_name: str) -> Path:
        mapping = self._config.query_artifacts()
        filename = mapping.get(query_name, f"{query_name}.csv")
        return self._artifacts_dir() / filename

    # ------------------------------------------------------------------ lists
    def list_queries(self) -> list[str]:
        """Return actual SQL query names from the query file."""
        if self._query_loader is None:
            return []
        return self._query_loader.list_queries()

    def list_artifacts(self) -> list[dict[str, Any]]:
        """Return existing artifact files with metadata."""
        artifacts: list[dict[str, Any]] = []
        art_dir = self._artifacts_dir()
        if not art_dir.exists():
            return artifacts
        for path in sorted(art_dir.glob("*.csv")):
            artifacts.append({
                "name": path.stem,
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "modified": path.stat().st_mtime,
            })
        return artifacts

    # ------------------------------------------------------------------ fetch
    def fetch_data(
        self,
        query_name: str,
        parameters: dict[str, Any] | None = None,
        fetch: bool = False,
    ) -> pd.DataFrame:
        """
        Fetch data for a query.
        If fetch=True: run Snowflake query and save to artifacts.
        If fetch=False: load from existing artifact CSV.
        """
        if fetch:
            return self._fetch_from_snowflake(query_name)
        return self._load_artifact(query_name)

    def _load_artifact(self, query_name: str) -> pd.DataFrame:
        path = self._artifact_path(query_name)
        if not path.exists():
            raise QueryExecutionError(
                f"Artifact not found for '{query_name}': {path.name}. "
                f"Enable 'Fetch new data' to generate it."
            )
        logger.info("Loading artifact: {path}", path=str(path))
        df = pd.read_csv(path)
        if "DT" in df.columns:
            df["DT"] = pd.to_datetime(df["DT"])
        logger.info("Artifact loaded: {rows} rows", rows=len(df))
        return df

    def _fetch_from_snowflake(self, query_name: str) -> pd.DataFrame:
        if self._query_loader is None:
            raise QueryExecutionError("Query loader not available.")
        sql = self._query_loader.get_query(query_name)

        logger.info("Executing query '{key}' against Snowflake", key=query_name)
        cred_mgr = CredentialManager()
        conn = cred_mgr.get_snowflake_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            df = cur.fetch_pandas_all()
            logger.info("Query returned {rows} rows", rows=len(df))
        finally:
            conn.close()

        if "DT" in df.columns:
            df["DT"] = pd.to_datetime(df["DT"])

        # Save to artifacts
        art_path = self._artifact_path(query_name)
        art_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(art_path, index=False)
        logger.info("Saved artifact: {path}", path=str(art_path))

        return df

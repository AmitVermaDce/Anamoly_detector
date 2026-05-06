from __future__ import annotations
"""SQL query loader that parses named queries from a single SQL file."""

import re
from pathlib import Path
from typing import Any

from app.core.exceptions import QueryNotFoundError
from app.core.logger import get_application_logger


class SQLQueryLoader:
    """Parses a SQL file containing named queries separated by comment tags.

    Supports both ``-- name: query_name`` and ``-- @query query_name`` markers.
    """

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        self._logger = get_application_logger()
        self._queries: dict[str, str] = {}
        self._load_queries()

    def _load_queries(self) -> None:
        """Read the SQL file and parse named queries."""
        if not self._file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self._file_path}")

        raw_content = self._file_path.read_text(encoding="utf-8")
        self._queries = self._parse_queries(raw_content)
        self._logger.info(
            "Loaded {count} queries from {path}",
            count=len(self._queries),
            path=str(self._file_path),
        )

    def _parse_queries(self, content: str) -> dict[str, str]:
        """Parse named queries from raw SQL content.

        Supported formats:
            -- name: query_name
            -- @query query_name

        Args:
            content: Raw SQL file content.

        Returns:
            dict[str, str]: Mapping of query names to SQL strings.
        """
        queries: dict[str, str] = {}

        # Pattern 1: -- name: query_name
        name_pattern = re.compile(
            r"^\s*--\s*name:\s*(\w+)\s*\n(.*?)(?=^\s*--\s*name:|^\s*--\s*@query|\Z)",
            re.DOTALL | re.MULTILINE,
        )

        # Pattern 2: -- @query query_name
        at_pattern = re.compile(
            r"^\s*--\s*@query\s+(\w+)\s*\n(.*?)(?=^\s*--\s*@query|^\s*--\s*name:|\Z)",
            re.DOTALL | re.MULTILINE,
        )

        for match in name_pattern.finditer(content):
            name = match.group(1).strip()
            query = self._clean_query(match.group(2))
            queries[name] = query

        for match in at_pattern.finditer(content):
            name = match.group(1).strip()
            query = self._clean_query(match.group(2))
            queries[name] = query

        return queries

    @staticmethod
    def _clean_query(raw: str) -> str:
        """Strip trailing semicolons and surrounding whitespace."""
        query = raw.strip()
        if query.endswith(";"):
            query = query[:-1].strip()
        return query

    def get_query(self, name: str) -> str:
        """Retrieve a named query by name.

        Args:
            name: The query name as defined by the tag marker.

        Returns:
            str: The SQL query string.

        Raises:
            QueryNotFoundError: If the named query does not exist.
        """
        if name not in self._queries:
            self._logger.warning(
                "Query '{name}' not found in {path}",
                name=name,
                path=str(self._file_path),
            )
            raise QueryNotFoundError(name)
        return self._queries[name]

    def list_queries(self) -> list[str]:
        """Return a list of all available query names.

        Returns:
            list[str]: Sorted list of query names.
        """
        return sorted(self._queries.keys())

    def get_query_with_params(
        self, name: str, parameters: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Retrieve a named query with bound parameters.

        Args:
            name: The query name.
            parameters: Dictionary of parameters to bind.

        Returns:
            tuple[str, dict[str, Any]]: The query string and parameters.
        """
        query = self.get_query(name)
        return query, parameters

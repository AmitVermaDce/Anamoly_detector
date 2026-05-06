from __future__ import annotations

import re
from pathlib import Path
from loguru import logger

from anomaly_detection.exceptions import QueryNotFoundError


class SQLQueryLoader:
    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        self._queries: dict[str, str] = {}
        self._load_queries()

    def _load_queries(self) -> None:
        if not self._file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self._file_path}")

        raw_content = self._file_path.read_text(encoding="utf-8")
        self._queries = self._parse_queries(raw_content)
        logger.info(
            "Loaded {count} queries from {path}",
            count=len(self._queries),
            path=str(self._file_path),
        )

    def _parse_queries(self, content: str) -> dict[str, str]:
        queries: dict[str, str] = {}

        pattern = re.compile(
            r"^\s*--\s*(?:name:\s*|@query\s+)(\w+)\s*\n(.*?)(?=^\s*--\s*(?:name:|@query)|\Z)",
            re.DOTALL | re.MULTILINE,
        )

        for match in pattern.finditer(content):
            name = match.group(1).strip()
            query = self._clean_query(match.group(2))
            queries[name] = query

        return queries

    @staticmethod
    def _clean_query(raw: str) -> str:
        query = raw.strip()
        if query.endswith(";"):
            query = query[:-1].strip()
        return query

    def get_query(self, name: str) -> str:
        if name not in self._queries:
            logger.warning(
                "Query '{name}' not found in {path}",
                name=name,
                path=str(self._file_path),
            )
            raise QueryNotFoundError(name)
        return self._queries[name]

    def list_queries(self) -> list[str]:
        return sorted(self._queries.keys())

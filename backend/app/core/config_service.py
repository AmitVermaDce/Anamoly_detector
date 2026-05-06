from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.core.exceptions import ConfigurationError
from app.core.logger import get_application_logger


class ConfigService:
    """Loads and exposes config.yaml with dot-notation access."""

    _instance: ConfigService | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> ConfigService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Path | str | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self._logger = get_application_logger()
        self._config: dict[str, Any] = {}
        path = Path(config_path or Path(__file__).resolve().parent.parent / "config" / "config.yaml")
        self._load(path)
        self._initialized = True

    def _load(self, config_path: Path) -> None:
        if not config_path.exists():
            self._logger.warning("config.yaml not found at {path}", path=str(config_path))
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            self._logger.info("Loaded config from {path}", path=str(config_path))
        except Exception as exc:
            raise ConfigurationError(f"Failed to load config.yaml: {exc}") from exc

    def get(self, key: str, default: Any | None = None) -> Any:
        parts = key.split(".")
        value: Any = self._config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def key_vault(self) -> dict[str, Any]:
        return self.get("key_vault", {})

    def snowflake(self) -> dict[str, Any]:
        return self.get("snowflake", {})

    def paths(self) -> dict[str, Any]:
        return self.get("paths", {})

    def query_file(self) -> str | None:
        return self.get("query_file")

    def query_key(self) -> str | None:
        return self.get("query_key")

    def detection_levels(self) -> dict[str, dict[str, Any]]:
        return self.get("detection_levels", {})

    def detection_params(self) -> dict[str, Any]:
        return self.get("detection_params", {})

    def get_detection_level(self, name: str) -> dict[str, Any] | None:
        return self.detection_levels().get(name)

    def artifacts_dir(self) -> str | None:
        return self.get("paths.artifacts_dir")

    def queries_dir(self) -> str | None:
        return self.get("paths.queries_dir")

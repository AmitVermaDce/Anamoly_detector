from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

from anomaly_detection.exceptions import ApplicationException


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Anomaly Detection API"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: list[str] = ["http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_database: str = ""
    snowflake_schema: str = ""
    snowflake_warehouse: str = ""
    snowflake_role: str = ""
    snowflake_private_key_path: str = ""
    snowflake_private_key_passphrase: str = ""
    snowflake_authenticator: Literal["snowflake", "keypair"] = "snowflake"

    default_algorithm: Literal["isolation_forest", "zscore", "dbscan"] = "isolation_forest"
    isolation_forest_contamination: float = 0.1
    isolation_forest_random_state: int = 42
    zscore_threshold: float = 3.0
    dbscan_eps: float = 0.5
    dbscan_min_samples: int = 5

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


class Config:
    _instance: Config | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Path | str | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self._config: dict[str, Any] = {}
        path = Path(
            config_path or Path(__file__).resolve().parent / "config" / "config.yaml"
        )
        self._load(path)
        self._initialized = True

    def _load(self, config_path: Path) -> None:
        if not config_path.exists():
            logger.warning("config.yaml not found at {path}", path=str(config_path))
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info("Loaded config from {path}", path=str(config_path))
        except Exception as exc:
            raise ApplicationException(f"Failed to load config.yaml: {exc}", status_code=500) from exc

    def get(self, key: str, default: Any | None = None) -> Any:
        parts = key.split(".")
        value: Any = self._config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def detection_levels(self) -> dict[str, dict[str, Any]]:
        return self.get("detection_levels", {})

    def detection_params(self) -> dict[str, Any]:
        return self.get("detection_params", {})

    def queries_dir(self) -> str | None:
        return self.get("paths.queries_dir")

    def artifacts_dir(self) -> str | None:
        return self.get("paths.artifacts_dir")

    def query_file(self) -> str | None:
        return self.get("query_file")

    def query_artifacts(self) -> dict[str, str]:
        return self.get("query_artifacts", {})

"""Pydantic settings for the application."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Anomaly Detection API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Snowflake
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

    # Anomaly Detection
    default_algorithm: Literal["isolation_forest", "zscore", "dbscan"] = "isolation_forest"
    isolation_forest_contamination: float = 0.1
    isolation_forest_random_state: int = 42
    zscore_threshold: float = 3.0
    dbscan_eps: float = 0.5
    dbscan_min_samples: int = 5

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


@lru_cache
def get_settings() -> ApplicationSettings:
    """Return cached application settings singleton.

    Returns:
        ApplicationSettings: The application configuration instance.
    """
    return ApplicationSettings()

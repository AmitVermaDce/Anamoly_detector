from __future__ import annotations
"""Snowflake client with connection pooling, Azure Key Vault support, and context managers."""

from contextlib import contextmanager
from typing import Any, Generator

import pandas as pd
from snowflake.connector import SnowflakeConnection

from app.core.config import ApplicationSettings, get_settings
from app.core.exceptions import ConfigurationError, DatabaseConnectionError, QueryExecutionError
from app.core.logger import get_application_logger


class SnowflakeClient:
    """Manages Snowflake connections with pooling, reuse, and graceful error handling.

    Supports two credential sources:
      1. A ``credential_manager`` instance (e.g., Azure Key Vault) – production
      2. ``ApplicationSettings`` loaded from environment variables – local dev
    """

    def __init__(
        self,
        settings: ApplicationSettings | None = None,
        credential_manager: Any | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._credential_manager = credential_manager
        self._logger = get_application_logger()
        self._connection: SnowflakeConnection | None = None

        if self._credential_manager is None:
            self._validate_settings()

    def _validate_settings(self) -> None:
        """Validate that required Snowflake configuration is present in settings."""
        required_fields = [
            self._settings.snowflake_account,
            self._settings.snowflake_user,
            self._settings.snowflake_database,
            self._settings.snowflake_schema,
            self._settings.snowflake_warehouse,
        ]
        if not all(required_fields):
            raise ConfigurationError("Missing required Snowflake connection parameters in settings.")

    def _build_connection(self) -> SnowflakeConnection:
        """Obtain a live Snowflake connection.

        Uses the ``credential_manager`` if provided, otherwise falls back to
        environment-based ``ApplicationSettings``.

        Returns:
            SnowflakeConnection: An active Snowflake connection.

        Raises:
            DatabaseConnectionError: If connection fails.
        """
        try:
            if self._credential_manager is not None:
                connection = self._credential_manager.get_snowflake_connection()
            else:
                connection = self._connect_from_settings()

            self._logger.info("Snowflake connection active.")
            return connection
        except Exception as exc:
            self._logger.error("Failed to connect to Snowflake: {error}", error=str(exc))
            raise DatabaseConnectionError(f"Snowflake connection failed: {str(exc)}") from exc

    def _connect_from_settings(self) -> SnowflakeConnection:
        """Connect using ApplicationSettings (local dev / container fallback).

        Returns:
            SnowflakeConnection: Live connection.
        """
        import snowflake.connector

        params: dict[str, Any] = {
            "account": self._settings.snowflake_account,
            "user": self._settings.snowflake_user,
            "database": self._settings.snowflake_database,
            "schema": self._settings.snowflake_schema,
            "warehouse": self._settings.snowflake_warehouse,
            "role": self._settings.snowflake_role or None,
            "client_session_keep_alive": True,
        }

        if self._settings.snowflake_authenticator == "keypair":
            pk = self._get_private_key_from_settings()
            if pk is None:
                raise ConfigurationError("Key-pair auth selected but private key not found.")
            params["private_key"] = pk
        else:
            if not self._settings.snowflake_password:
                raise ConfigurationError("Password auth selected but password is missing.")
            params["password"] = self._settings.snowflake_password

        return snowflake.connector.connect(**params)

    def _get_private_key_from_settings(self) -> bytes | None:
        """Load private key from disk when using settings-based auth."""
        import os

        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        key_path = self._settings.snowflake_private_key_path
        if not key_path or not os.path.exists(key_path):
            return None

        with open(key_path, "rb") as f:
            p_key = serialization.load_pem_private_key(
                f.read(),
                password=(
                    self._settings.snowflake_private_key_passphrase.encode()
                    if self._settings.snowflake_private_key_passphrase
                    else None
                ),
                backend=default_backend(),
            )

        return p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def get_active_connection(self) -> SnowflakeConnection:
        """Return the active Snowflake connection, creating one if necessary.

        Handles connection reuse. If an existing connection is dead, a new
        one is established automatically.

        Returns:
            SnowflakeConnection: An active, ready-to-use connection.

        Raises:
            DatabaseConnectionError: If a new connection cannot be established.
        """
        if self._connection is None or not self._is_connection_alive():
            self._connection = self._build_connection()
        return self._connection

    def _is_connection_alive(self) -> bool:
        """Check whether the existing connection is still alive.

        Returns:
            bool: True if the connection is open and responsive.
        """
        if self._connection is None:
            return False
        try:
            self._connection.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        """Close the active Snowflake connection."""
        if self._connection is not None:
            try:
                self._connection.close()
                self._logger.info("Snowflake connection closed.")
            except Exception as exc:
                self._logger.warning("Error closing connection: {error}", error=str(exc))
            finally:
                self._connection = None

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Context manager for database cursors.

        Yields:
            Any: A Snowflake cursor from the active connection.

        Raises:
            DatabaseConnectionError: If no healthy connection is available.
        """
        connection = self.get_active_connection()
        cursor = None
        try:
            cursor = connection.cursor()
            yield cursor
        except Exception as exc:
            self._logger.error("Cursor operation failed: {error}", error=str(exc))
            raise DatabaseConnectionError(f"Cursor operation failed: {str(exc)}") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame.

        Args:
            query: The SQL query string.
            parameters: Optional query parameters for safe binding.

        Returns:
            pd.DataFrame: Query results.

        Raises:
            QueryExecutionError: If the query fails.
        """
        try:
            with self.get_cursor() as cursor:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                return pd.DataFrame(data, columns=columns)
        except Exception as exc:
            self._logger.error("Query execution failed: {error}", error=str(exc))
            raise QueryExecutionError(f"Query execution failed: {str(exc)}") from exc

    def __enter__(self) -> "SnowflakeClient":
        """Enter context manager and ensure an active connection exists."""
        self.get_active_connection()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and disconnect."""
        self.disconnect()

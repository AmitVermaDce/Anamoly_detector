from __future__ import annotations

from anomaly_detection.database.credentials import CredentialManager
from anomaly_detection.database.queries import SQLQueryLoader
from anomaly_detection.database.snowflake import SnowflakeClient
from anomaly_detection.config import Config

config: Config | None = None
credential_manager: CredentialManager | None = None
snowflake_client: SnowflakeClient | None = None
query_loader: SQLQueryLoader | None = None

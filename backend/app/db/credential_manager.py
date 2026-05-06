from __future__ import annotations
"""Credential Manager — secure credential retrieval from Azure Key Vault.

Uses Managed Identity authentication. Credentials are lazy-loaded and cached.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
import snowflake.connector
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.core.exceptions import ConfigurationError
from app.core.logger import get_application_logger

logger = logging.getLogger(__name__)


class CredentialManager:
    """Retrieves and caches secrets from Azure Key Vault for Snowflake authentication."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config: dict[str, Any] | None = None
        self._credentials: dict[str, dict[str, str]] | None = None
        self._initialized = False
        self._logger = get_application_logger()

        if config_path is None:
            self._config_path = (
                Path(__file__).resolve().parent.parent / "config" / "config.yaml"
            )
        else:
            self._config_path = Path(config_path)

    # ------------------------------------------------------------------ init
    def _initialize(self) -> None:
        if self._initialized:
            return
        self._config = self._load_config()
        self._initialized = True
        self._logger.info("CredentialManager initialised")

    def _load_config(self) -> dict[str, Any]:
        if not self._config_path.exists():
            raise ConfigurationError(f"Config file not found: {self._config_path}")
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def config(self) -> dict[str, Any]:
        if not self._initialized:
            self._initialize()
        if self._config is None:
            raise ConfigurationError("Configuration failed to load.")
        return self._config

    # ----------------------------------------------------------- Key Vault
    def _get_all_credentials(self) -> dict[str, dict[str, str]]:
        if not self._initialized:
            self._initialize()
        if self._credentials is not None:
            return self._credentials

        kv_cfg = self._config["key_vault"]
        credential = ManagedIdentityCredential(client_id=kv_cfg["managed_identity_client_id"])
        kv_url = f"https://{kv_cfg['name']}.vault.azure.net"
        client = SecretClient(vault_url=kv_url, credential=credential)

        self._credentials = {
            "snowflake": {
                "user": self._safe_get(client, "snowflake-secret-user"),
                "private_key": self._safe_get(client, "snowflake-private-key"),
                "private_key_passphrase": self._safe_get(client, "snowflake-key-passphrase"),
                "account": self._safe_get(client, "snowflake-secret-account"),
                "role": self._safe_get(client, "snowflake-secret-role"),
            },
        }
        self._logger.info("Credentials retrieved from Key Vault")
        return self._credentials

    @staticmethod
    def _safe_get(client: SecretClient, secret_name: str) -> str:
        """Retrieve a secret, returning empty string if missing."""
        try:
            return client.get_secret(secret_name).value or ""
        except Exception as exc:
            logger.warning("Secret '%s' not found in Key Vault: %s", secret_name, exc)
            return ""

    # -------------------------------------------------------- Snowflake
    def get_snowflake_credentials(self) -> dict[str, str]:
        """Return cached Snowflake credentials.

        Returns:
            dict[str, str]: Credential dictionary.
        """
        return self._get_all_credentials()["snowflake"]

    def get_snowflake_private_key_bytes(self) -> bytes:
        """Load and convert the private key PEM into DER bytes.

        Returns:
            bytes: Private key in DER format.

        Raises:
            ConfigurationError: If the key is missing or invalid.
        """
        creds = self.get_snowflake_credentials()
        pem = creds.get("private_key", "").replace("\\n", "\n")
        if not pem:
            raise ConfigurationError("Snowflake private key is missing in Key Vault.")

        passphrase = creds.get("private_key_passphrase", "")
        passphrase_bytes = passphrase.encode("utf-8") if passphrase else None

        try:
            p_key = serialization.load_pem_private_key(
                pem.encode("utf-8"),
                password=passphrase_bytes,
                backend=default_backend(),
            )
        except Exception as exc:
            raise ConfigurationError(f"Failed to load private key: {str(exc)}") from exc

        return p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def get_snowflake_connection(self) -> Any:
        """Return a live Snowflake connection using Key Vault credentials.

        Returns:
            snowflake.connector.SnowflakeConnection: Active connection.

        Raises:
            ConfigurationError: If required config or credentials are missing.
        """
        if not self._initialized:
            self._initialize()

        sf_creds = self.get_snowflake_credentials()
        pk_bytes = self.get_snowflake_private_key_bytes()
        sf_cfg = self._config.get("snowflake", {})

        # Validate required fields
        required = ["account", "user"]
        missing = [k for k in required if not sf_creds.get(k)]
        if missing:
            raise ConfigurationError(f"Missing Key Vault secrets: {', '.join(missing)}")

        # Build user with domain if your org requires it
        user = sf_creds["user"]
        if "@" not in user and sf_cfg.get("user_domain"):
            user = f"{user}@{sf_cfg['user_domain']}"

        connection = snowflake.connector.connect(
            account=sf_creds["account"],
            user=user,
            private_key=pk_bytes,
            role=sf_creds.get("role") or sf_cfg.get("role", ""),
            database=sf_cfg.get("database", ""),
            warehouse=sf_cfg.get("warehouse", ""),
            schema=sf_cfg.get("schema", ""),
            client_session_keep_alive=True,
        )

        self._logger.info("Snowflake connection established via Key Vault credentials.")
        return connection

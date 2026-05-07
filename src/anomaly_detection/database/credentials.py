from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from loguru import logger

from anomaly_detection.exceptions import ConfigurationError


class CredentialManager:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config: dict[str, Any] | None = None
        self._credentials: dict[str, dict[str, str]] | None = None
        self._initialized = False

        if config_path is None:
            self._config_path = (
                Path(__file__).resolve().parent.parent / "config" / "config.yaml"
            )
        else:
            self._config_path = Path(config_path)

    def _initialize(self) -> None:
        if self._initialized:
            return
        self._config = self._load_config()
        self._initialized = True
        logger.info("CredentialManager initialised")

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
        logger.info("Credentials retrieved from Key Vault")
        return self._credentials

    def _safe_get(self, client: SecretClient, secret_name: str) -> str:
        try:
            return client.get_secret(secret_name).value or ""
        except Exception as exc:
            logger.warning("Secret '{name}' not found in Key Vault: {error}", name=secret_name, error=exc)
            return ""

    def get_snowflake_credentials(self) -> dict[str, str]:
        return self._get_all_credentials()["snowflake"]

    def get_snowflake_private_key_bytes(self) -> bytes:
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
        if not self._initialized:
            self._initialize()

        sf_creds = self.get_snowflake_credentials()
        pk_bytes = self.get_snowflake_private_key_bytes()
        sf_cfg = self._config.get("snowflake", {})

        required = ["account", "user"]
        missing = [k for k in required if not sf_creds.get(k)]
        if missing:
            raise ConfigurationError(f"Missing Key Vault secrets: {', '.join(missing)}")

        import snowflake.connector

        connection = snowflake.connector.connect(
            account=sf_creds["account"],
            user=f"{sf_creds['user']}@optum.com",
            private_key=pk_bytes,
            role=sf_creds.get("role", ""),
            database=sf_cfg.get("database", ""),
            warehouse=sf_cfg.get("warehouse", ""),
            schema=sf_cfg.get("schema", ""),
            client_session_keep_alive=True,
        )

        logger.info("Snowflake connection established via Key Vault credentials.")
        return connection

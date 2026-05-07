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
    """Retrieves and caches secrets from Azure Key Vault."""

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
                "user": client.get_secret("snowflake-secret-user").value,
                "private_key": client.get_secret("snowflake-private-key").value,
                "private_key_passphrase": client.get_secret("snowflake-key-passphrase").value,
                "account": client.get_secret("snowflake-secret-account").value,
                "role": client.get_secret("snowflake-secret-role").value,
            },
        }
        logger.info("Credentials retrieved from Key Vault")
        return self._credentials

    def get_snowflake_credentials(self) -> dict[str, str]:
        return self._get_all_credentials()["snowflake"]

    def get_snowflake_private_key_bytes(self) -> bytes:
        creds = self.get_snowflake_credentials()
        pem = creds["private_key"].replace("\\n", "\n")
        passphrase = creds.get("private_key_passphrase", "")
        passphrase_bytes = passphrase.encode("utf-8") if passphrase else None

        p_key = serialization.load_pem_private_key(
            pem.encode("utf-8"),
            password=passphrase_bytes,
            backend=default_backend(),
        )
        return p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def get_snowflake_connection(self) -> Any:
        """Return a live Snowflake connection using Key Vault credentials."""
        if not self._initialized:
            self._initialize()

        sf_creds = self.get_snowflake_credentials()
        pk_bytes = self.get_snowflake_private_key_bytes()
        sf_cfg = self._config["snowflake"]

        import snowflake.connector

        connect_params: dict[str, Any] = {
            "account": sf_creds["account"],
            "user": f"{sf_creds['user']}@optum.com",
            "private_key": pk_bytes,
            "role": sf_creds.get("role") or sf_cfg.get("role", ""),
        }

        for key in ("database", "warehouse", "schema"):
            val = sf_cfg.get(key)
            if val and not val.startswith("your-"):
                connect_params[key] = val

        return snowflake.connector.connect(**connect_params)

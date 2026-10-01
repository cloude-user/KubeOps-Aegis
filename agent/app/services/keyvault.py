import asyncio
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from agent.app.core.config import settings

logger = logging.getLogger("aegis.keyvault")


class KeyVaultService:
    def __init__(self, keyvault_url: Optional[str] = None):
        self.keyvault_url = keyvault_url or settings.AZURE_KEYVAULT_URL
        self._client: Optional[SecretClient] = None

    def _get_client(self) -> Optional[SecretClient]:
        if self._client:
            return self._client
        try:
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self.keyvault_url, credential=credential)
            logger.info("Initialized Azure Key Vault SecretClient for: %s", self.keyvault_url)
            return self._client
        except Exception as e:
            logger.warning("Could not initialize Azure Key Vault client: %s", e)
            return None

    def _get_secret_sync(self, secret_name: str, fallback_value: Optional[str]) -> Optional[str]:
        client = self._get_client()
        if not client:
            return fallback_value
        try:
            retrieved_secret = client.get_secret(secret_name)
            logger.info("Successfully fetched secret '%s' from Key Vault", secret_name)
            return retrieved_secret.value
        except Exception as e:
            logger.warning("KeyVault get_secret failed for key '%s': %s. Returning fallback.", secret_name, e)
            return fallback_value

    def _set_secret_sync(self, secret_name: str, secret_value: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            client.set_secret(secret_name, secret_value)
            logger.info("Successfully stored secret '%s' in Key Vault", secret_name)
            return True
        except Exception as e:
            logger.error("Failed to set secret '%s' in Key Vault: %s", secret_name, e)
            return False

    async def get_secret(self, secret_name: str, fallback_value: Optional[str] = None) -> Optional[str]:
        """Asynchronous fetch of secret from Azure Key Vault."""
        return await asyncio.to_thread(self._get_secret_sync, secret_name, fallback_value)

    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """Asynchronous store of secret in Azure Key Vault."""
        return await asyncio.to_thread(self._set_secret_sync, secret_name, secret_value)


keyvault_service = KeyVaultService()

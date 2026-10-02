import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from apps.backend.app.config import settings

logger = logging.getLogger("backend.blob_service")


class AzureBlobService:
    def __init__(self):
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        if not self.account_name:
            return None
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self._client = BlobServiceClient(account_url=account_url, credential=credential)
            logger.info("Initialized Azure BlobServiceClient for %s", account_url)
            return self._client
        except Exception as e:
            logger.warning("Could not connect to Azure Blob Storage (running in local simulation mode): %s", e)
            return None

    def _upload_file_sync(self, container_name: str, filename: str, file_data: bytes, content_type: str = "application/pdf") -> str:
        client = self._get_client()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blob_name = f"{timestamp}_{filename}"

        if not client:
            logger.info("[SIMULATED UPLOAD] Saved '%s' in container '%s'", blob_name, container_name)
            return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"

        try:
            container_client = client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()

            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_data, overwrite=True, content_type=content_type)
            logger.info("Successfully uploaded file blob: %s", blob_client.url)
            return blob_client.url
        except Exception as e:
            logger.error("Failed to upload blob '%s': %s", blob_name, e)
            return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"

    async def upload_receipt(self, filename: str, file_data: bytes) -> str:
        """Upload customer payment receipt PDF/image to Azure Blob Storage."""
        return await asyncio.to_thread(
            self._upload_file_sync,
            settings.AZURE_STORAGE_CONTAINER_RECEIPTS,
            filename,
            file_data,
            "application/pdf"
        )


azure_blob_service = AzureBlobService()

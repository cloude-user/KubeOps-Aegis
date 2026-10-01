import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from agent.app.core.config import settings

logger = logging.getLogger("aegis.blob")


class BlobStorageService:
    def __init__(self):
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.container_name = settings.AZURE_STORAGE_CONTAINER
        self._blob_service_client: Optional[BlobServiceClient] = None

    def _get_service_client(self) -> Optional[BlobServiceClient]:
        if self._blob_service_client:
            return self._blob_service_client
        if not self.account_name:
            return None
        try:
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self._blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
            logger.info("Initialized BlobServiceClient for: %s", account_url)
            return self._blob_service_client
        except Exception as e:
            logger.warning("Could not initialize Blob Storage Service Client: %s", e)
            return None

    def _upload_incident_log_sync(self, incident_id: str, log_data: Dict[str, Any]) -> str:
        client = self._get_service_client()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        blob_name = f"incidents/{timestamp}_{incident_id}.json"
        content = json.dumps(log_data, indent=2)

        if not client:
            logger.info("[SIMULATED BLOB UPLOAD] Logged incident %s locally.", incident_id)
            return f"https://local-simulated-blob/{self.container_name}/{blob_name}"

        try:
            container_client = client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()

            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(content, overwrite=True)
            logger.info("Successfully uploaded incident log blob: %s", blob_name)
            return blob_client.url
        except Exception as e:
            logger.error("Failed to upload blob '%s': %s", blob_name, e)
            return f"failed-upload://{blob_name}"

    def _list_incident_logs_sync(self) -> List[str]:
        client = self._get_service_client()
        if not client:
            return ["simulated-incident-001.json", "simulated-incident-002.json"]
        try:
            container_client = client.get_container_client(self.container_name)
            if not container_client.exists():
                return []
            blobs = container_client.list_blobs(name_starts_with="incidents/")
            return [b.name for b in blobs]
        except Exception as e:
            logger.error("Error listing blobs: %s", e)
            return []

    async def upload_incident_log(self, incident_id: str, log_data: Dict[str, Any]) -> str:
        """Asynchronous upload of incident audit log JSON to Azure Blob Storage."""
        return await asyncio.to_thread(self._upload_incident_log_sync, incident_id, log_data)

    async def list_incident_logs(self) -> List[str]:
        """Asynchronous listing of incident audit logs in Azure Blob Storage."""
        return await asyncio.to_thread(self._list_incident_logs_sync)


blob_service = BlobStorageService()

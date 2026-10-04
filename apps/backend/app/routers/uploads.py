import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

try:
    from backend.app.dependencies import get_blob_service, get_request_id
    from backend.app.services.blob_service import AzureBlobService
except ModuleNotFoundError:
    from apps.backend.app.dependencies import get_blob_service, get_request_id
    from apps.backend.app.services.blob_service import AzureBlobService

logger = logging.getLogger("backend.routers.uploads")

router = APIRouter(prefix="/uploads", tags=["Azure Blob File Uploads"])


class UploadReceiptRequest(BaseModel):
    filename: str
    content_b64: str
    content_type: str = "application/pdf"


@router.post("/receipt", status_code=status.HTTP_201_CREATED)
async def upload_receipt_data(
    request: UploadReceiptRequest,
    blob_service: AzureBlobService = Depends(get_blob_service),
    request_id: str = Depends(get_request_id)
):
    """
    Upload customer payment receipt PDF or image to Azure Blob Storage.
    FastAPI injects AzureBlobService instance via Dependency Injection.
    """
    logger.info("[%s] AUDIT_UPLOADS: File upload request - filename='%s', type='%s'", request_id, request.filename, request.content_type)

    if not request.filename:
        logger.warning("[%s] AUDIT_UPLOADS: Rejected - missing filename", request_id)
        raise HTTPException(status_code=400, detail="Filename missing.")

    try:
        file_bytes = request.content_b64.encode("utf-8")
        size_bytes = len(file_bytes)
        logger.info("[%s] AUDIT_UPLOADS: Uploading %d bytes to Azure Blob Storage...", request_id, size_bytes)

        blob_url = await blob_service.upload_receipt(filename=request.filename, file_data=file_bytes)

        logger.info("[%s] AUDIT_UPLOADS: Upload success! URL: %s", request_id, blob_url)
        return {
            "status": "SUCCESS",
            "filename": request.filename,
            "content_type": request.content_type,
            "size_bytes": size_bytes,
            "blob_url": blob_url,
            "request_id": request_id
        }
    except Exception as e:
        logger.error("[%s] AUDIT_UPLOADS: Failed uploading file '%s': %s", request_id, request.filename, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload to Azure Blob Storage: {str(e)}")

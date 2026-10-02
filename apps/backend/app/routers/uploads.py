from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from apps.backend.app.services.blob_service import azure_blob_service

router = APIRouter(prefix="/uploads", tags=["Azure Blob File Uploads"])


class UploadReceiptRequest(BaseModel):
    filename: str
    content_b64: str
    content_type: str = "application/pdf"


@router.post("/receipt", status_code=status.HTTP_201_CREATED)
async def upload_receipt_data(request: UploadReceiptRequest):
    """Upload customer payment receipt PDF or image to Azure Blob Storage."""
    if not request.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")
    
    file_bytes = request.content_b64.encode("utf-8")
    blob_url = await azure_blob_service.upload_receipt(filename=request.filename, file_data=file_bytes)
    
    return {
        "status": "SUCCESS",
        "filename": request.filename,
        "content_type": request.content_type,
        "size_bytes": len(file_bytes),
        "blob_url": blob_url
    }

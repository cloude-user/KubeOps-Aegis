from fastapi import APIRouter, UploadFile, File, HTTPException, status
from apps.backend.app.services.blob_service import azure_blob_service

router = APIRouter(prefix="/uploads", tags=["Azure Blob File Uploads"])


@router.post("/receipt", status_code=status.HTTP_201_CREATED)
async def upload_receipt(file: UploadFile = File(...)):
    """Upload customer payment receipt PDF or image to Azure Blob Storage."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")
    
    contents = await file.read()
    blob_url = await azure_blob_service.upload_receipt(filename=file.filename, file_data=contents)
    
    return {
        "status": "SUCCESS",
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "blob_url": blob_url
    }

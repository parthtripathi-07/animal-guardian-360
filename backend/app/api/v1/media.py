"""
Media Upload API:
- Secure multipart file upload with automatic EXIF metadata stripping
- Anti-malware file validation
- S3 / Cloudflare R2 persistence with fallback
- Presigned direct-upload URL generation
"""
import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.services.media_service import media_service

router = APIRouter(prefix="/media", tags=["Media Upload & Storage"])


class PresignRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern=r"^(image/(jpeg|png|webp|gif)|video/(mp4|quicktime|webm))$")
    folder: Optional[str] = Field("reports", max_length=32)


class PresignResponse(BaseModel):
    upload_url: str
    method: str
    storage_key: str
    public_url: str
    expires_in: int
    is_mock: bool


class UploadMediaResponse(BaseModel):
    storage_key: str
    public_url: str
    original_filename: str
    mime_type: str
    media_type: str
    file_size_bytes: int
    exif_stripped: bool
    virus_scan_status: str


@router.post(
    "/upload",
    response_model=UploadMediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and sanitize an image or video file"
)
async def upload_media(
    file: UploadFile = File(...),
    folder: str = Form("reports")
):
    """
    Accepts an uploaded image or video, validates against malware signatures,
    strips sensitive EXIF GPS metadata if it is an image, and uploads to cloud storage.
    """
    MAX_SIZE = 25 * 1024 * 1024  # 25 MB limit
    content = await file.read()

    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 25 MB maximum allowed limit."
        )

    content_type = file.content_type or "application/octet-stream"
    allowed_types = (
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "video/mp4", "video/quicktime", "video/webm"
    )
    if content_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed types: JPG, PNG, WEBP, GIF, MP4, MOV, WEBM."
        )

    try:
        result = await media_service.process_and_upload(
            filename=file.filename or "uploaded_media.jpg",
            content=content,
            content_type=content_type,
            folder=folder
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    media_type = "video" if content_type.startswith("video/") else "image"

    return UploadMediaResponse(
        storage_key=result["storage_key"],
        public_url=result["public_url"],
        original_filename=result["original_filename"],
        mime_type=result["content_type"],
        media_type=media_type,
        file_size_bytes=result["file_size_bytes"],
        exif_stripped=result["exif_stripped"],
        virus_scan_status=result["virus_scan_status"],
    )


@router.post(
    "/presign",
    response_model=PresignResponse,
    summary="Generate pre-signed direct upload URL for cloud storage"
)
async def generate_presigned_url(payload: PresignRequest):
    """
    Generates a pre-signed PUT URL for client-side direct upload to AWS S3 or Cloudflare R2.
    """
    import uuid
    ext = os.path.splitext(payload.filename)[1].lower() or ".jpg"
    key = f"{payload.folder}/{uuid.uuid4().hex}{ext}"

    info = media_service.generate_presigned_upload_url(
        storage_key=key,
        content_type=payload.content_type,
        expires_in=3600
    )
    return PresignResponse(**info)


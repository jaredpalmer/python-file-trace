"""File schemas."""
from typing import Optional
from .common import BaseSchema


class FileUploadResponse(BaseSchema):
    """Schema for file upload response."""
    id: str
    upload_url: str


class FileMetadataResponse(BaseSchema):
    """Schema for file metadata response."""
    id: str
    name: str
    size: int
    mime_type: Optional[str] = None
    is_public: bool = False

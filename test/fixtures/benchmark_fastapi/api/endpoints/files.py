"""File upload/download endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from schemas.file import FileUploadResponse, FileMetadataResponse
from models.file import File
from models.user import User


router = Router()


@router.get("/")
async def list_files(user: User, session):
    files = []  # Would query from database
    return [FileMetadataResponse.from_model(f) for f in files]


@router.get("/{file_id}")
async def get_file(file_id: str, session):
    file = File(id=file_id)
    return FileMetadataResponse.from_model(file)


@router.post("/upload")
async def upload_file(user: User, session):
    # Handle file upload
    file = File(
        id="new_file",
        name="uploaded_file.txt",
        size=1024,
        owner_id=user.id,
    )
    return FileUploadResponse(
        id=file.id,
        upload_url="https://storage.example.com/upload",
    )


@router.get("/{file_id}/download")
async def get_download_url(file_id: str, session):
    file = File(id=file_id)
    return {
        "download_url": f"https://storage.example.com/download/{file_id}",
        "expires_in": 3600,
    }

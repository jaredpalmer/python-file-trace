"""File model."""
from db.base import Base


class File(Base):
    """File model for uploaded files."""
    __tablename__ = "files"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.size = kwargs.get("size")
        self.mime_type = kwargs.get("mime_type")
        self.storage_key = kwargs.get("storage_key")
        self.owner_id = kwargs.get("owner_id")
        self.organization_id = kwargs.get("organization_id")
        self.is_public = kwargs.get("is_public", False)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")

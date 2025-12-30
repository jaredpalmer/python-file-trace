"""Common schemas."""
from typing import Optional, Any


class BaseSchema:
    """Base schema class."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_model(cls, model):
        return cls(**model.__dict__) if model else None


class ErrorResponse(BaseSchema):
    """Error response schema."""
    def __init__(self, error: str, message: str, details: Optional[Any] = None):
        self.error = error
        self.message = message
        self.details = details


class SuccessResponse(BaseSchema):
    """Success response schema."""
    def __init__(self, message: str = "Success", data: Optional[Any] = None):
        self.message = message
        self.data = data

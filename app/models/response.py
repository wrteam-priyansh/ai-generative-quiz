from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    error: bool
    data: Optional[T] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response format"""
    error: bool = True
    data: None = None
    message: str

class SuccessResponse(BaseModel, Generic[T]):
    """Success response format"""
    error: bool = False
    data: T
    message: Optional[str] = None

# Helper functions to create standardized responses
def success_response(data: Any, message: Optional[str] = None) -> dict:
    """Create a success response"""
    return {
        "error": False,
        "data": data,
        "message": message
    }

def error_response(message: str, data: Any = None) -> dict:
    """Create an error response"""
    return {
        "error": True,
        "data": data,
        "message": message
    }
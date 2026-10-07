"""
Common shared Pydantic v2 schemas across the application.
"""
from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorDetail(BaseModel):
    loc: Optional[List[str]] = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """Standard RFC-style error payload."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Any] = None


class GeoPoint(BaseModel):
    """Latitude and Longitude representation with standard range constraints."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in degrees")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool

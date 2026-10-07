"""
Pydantic v2 schemas for Animal Cruelty & Illegal Activity Reporting,
Nearest Police Station Finder, Media Sanitization, and Admin Review.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ReportMediaCreate(BaseModel):
    media_type: str = Field(default="image", pattern="^(image|video)$")
    storage_key: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    public_url: Optional[str] = None


class ReportMediaResponse(BaseModel):
    id: str
    media_type: str
    original_filename: str
    public_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PoliceStationResponse(BaseModel):
    name: str
    address: str
    phone: str
    distance_meters: Optional[float] = None


class ReportCreate(BaseModel):
    category: str = Field(
        ...,
        pattern="^(cruelty|illegal_trade|abandonment|illegal_breeding|other)$",
        description="Cruelty category"
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Detailed description of observed animal abuse or illegal activity"
    )
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address_text: Optional[str] = Field(None, description="Street address or landmark")
    is_anonymous: bool = Field(default=False, description="Whether to conceal reporter identity")
    media: List[ReportMediaCreate] = Field(default=[], max_length=5, description="Up to 5 photos or videos")


class ReportResponse(BaseModel):
    id: str
    reporter_id: Optional[str] = None
    is_anonymous: bool
    category: str
    description: str
    latitude: float
    longitude: float
    address_text: Optional[str] = None
    status: str
    nearest_police_station: Optional[PoliceStationResponse] = None
    complaint_pdf_url: Optional[str] = None
    shareable_summary: str
    media: List[ReportMediaResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminReviewReportRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(verified|dismissed|action_taken|fake)$",
        description="'verified', 'dismissed', 'action_taken', or 'fake'"
    )
    admin_notes: Optional[str] = Field(None, description="Internal review notes")
    strike_reason: Optional[str] = Field(
        None,
        description="Required if status is 'fake' to issue a strike to the user"
    )

    @field_validator("strike_reason")
    @classmethod
    def validate_strike_reason(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get("status") == "fake" and not v:
            raise ValueError("strike_reason is mandatory when marking a report as fake")
        return v


class AdminReviewResponse(BaseModel):
    success: bool = True
    report_id: str
    status: str
    admin_notes: Optional[str] = None
    strike_issued: bool = False
    strike_number: Optional[int] = None
    user_suspended: bool = False
    message: str

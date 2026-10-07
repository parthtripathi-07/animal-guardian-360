"""
Pydantic v2 schemas for Road Accident SOS flow, Hospital Dispatches, and Case Tracking.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AccidentSOSCreate(BaseModel):
    animal_type: str = Field(..., description="Species of injured animal: dog, cat, cow, bird, etc.")
    condition_description: Optional[str] = Field(None, description="Observable injuries: bleeding, fracture, unconscious, etc.")
    photo_url: Optional[str] = Field(None, description="Optional photo URL of injured animal")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address_text: Optional[str] = Field(None, description="Street address or nearby landmark")
    reporter_phone: Optional[str] = Field(None, description="Contact phone of reporter for hospital follow-up")


class AlertDispatchResponse(BaseModel):
    id: str
    hospital_id: str
    hospital_name: str
    hospital_phone: str
    escalation_round: int
    status: str
    expires_at: datetime
    dispatched_at: datetime

    model_config = {"from_attributes": True}


class AccidentAlertResponse(BaseModel):
    id: str
    reporter_id: Optional[str] = None
    reporter_phone: Optional[str] = None
    animal_type: str
    condition_description: Optional[str] = None
    photo_url: Optional[str] = None
    latitude: float
    longitude: float
    address_text: Optional[str] = None
    status: str
    accepted_hospital_id: Optional[str] = None
    accepted_hospital_name: Optional[str] = None
    accepted_hospital_phone: Optional[str] = None
    eta_minutes: Optional[int] = None
    created_at: datetime
    dispatches: List[AlertDispatchResponse] = []

    model_config = {"from_attributes": True}


class DispatchActionRequest(BaseModel):
    action: str = Field(..., pattern="^(accept|decline)$", description="'accept' or 'decline'")
    eta_minutes: Optional[int] = Field(15, ge=1, le=180, description="Estimated arrival time in minutes (if accepting)")
    decline_reason: Optional[str] = Field(None, description="Reason if declining the dispatch")


class DispatchActionResponse(BaseModel):
    success: bool
    message: str
    alert_status: str
    alert_id: str
    eta_minutes: Optional[int] = None


class HospitalCaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(reached|closed)$", description="Update status to 'reached' or 'closed'")
    notes: Optional[str] = None


class AccidentLiveStatusResponse(BaseModel):
    alert_id: str
    status: str
    animal_type: str
    accepted_hospital_name: Optional[str] = None
    accepted_hospital_phone: Optional[str] = None
    eta_minutes: Optional[int] = None
    escalation_round: int
    dispatches_count: int
    dispatches: List[AlertDispatchResponse] = []
    accepted_at: Optional[datetime] = None
    reached_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


"""
Pydantic schemas for the consolidated Admin Panel: Statistics, Hospital Verification,
Strikes Management, and Audit Trail.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AdminStatsResponse(BaseModel):
    total_users: int
    total_hospitals: int
    pending_hospitals: int
    total_accidents: int
    active_accidents: int
    total_cruelty_reports: int
    pending_reports: int
    total_lost_found_posts: int
    reunited_pets: int
    total_donations_raised_inr: float
    total_funds_allocated_inr: float
    active_strikes_count: int


class HospitalVerifyRequest(BaseModel):
    is_verified: bool
    notes: Optional[str] = None


class HospitalAdminResponse(BaseModel):
    id: str
    name: str
    phone: str
    emergency_phone: Optional[str] = None
    email: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    is_24x7: bool
    is_verified: bool
    is_active: bool
    ambulance_available: bool
    rating: float
    created_at: datetime

    model_config = {"from_attributes": True}


class StrikeAdminResponse(BaseModel):
    id: str
    user_id: str
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    strike_number: int
    reason: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: str
    entity_name: str
    entity_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}

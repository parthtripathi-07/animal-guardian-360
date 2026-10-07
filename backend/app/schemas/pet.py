"""
Pydantic v2 schemas for Pets, Lost & Found Listings, AI Vector Matching, and Sightings Map.
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class PetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    species: str = Field(..., min_length=2, max_length=64)
    breed: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    gender: Optional[str] = None
    microchip_id: Optional[str] = None
    photo_url: Optional[str] = None


class PetResponse(PetCreate):
    id: str
    owner_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LostFoundPostCreate(BaseModel):
    pet_id: Optional[str] = None
    post_type: str = Field(..., pattern="^(lost|found|sighting)$")
    species: str = Field(..., min_length=2, max_length=64)
    breed: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    gender: Optional[str] = None
    distinctive_marks: Optional[str] = None
    collar_info: Optional[str] = None
    incident_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address_text: Optional[str] = None
    photo_urls: List[str] = Field(default=[], max_length=5)
    masked_contact_enabled: bool = True


class MatchSummaryResponse(BaseModel):
    match_id: str
    matched_post_id: str
    matched_post_type: str
    similarity_score: float
    confidence_percent: float
    distance_km: float
    matched_photo_url: Optional[str] = None
    species: str
    breed: Optional[str] = None
    address_text: Optional[str] = None
    incident_date: datetime


class LostFoundPostResponse(BaseModel):
    id: str
    user_id: str
    post_type: str
    species: str
    breed: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    gender: Optional[str] = None
    distinctive_marks: Optional[str] = None
    collar_info: Optional[str] = None
    incident_date: datetime
    latitude: float
    longitude: float
    address_text: Optional[str] = None
    photo_urls: List[str] = []
    status: str
    masked_contact_enabled: bool
    created_at: datetime
    matches: List[MatchSummaryResponse] = []

    model_config = {"from_attributes": True}


class PostFilterQuery(BaseModel):
    post_type: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    color: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = 25.0
    status: Optional[str] = "active"

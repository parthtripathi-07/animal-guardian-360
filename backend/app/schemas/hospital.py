"""
Pydantic v2 schemas for Veterinary Hospitals and Nearby search.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VetHospitalBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=7, max_length=32)
    emergency_phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = None
    address: str = Field(..., min_length=5)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_24x7: bool = False
    ambulance_available: bool = False
    operating_hours: Optional[Dict[str, Any]] = None


class VetHospitalCreate(VetHospitalBase):
    pass


class VetHospitalResponse(VetHospitalBase):
    id: str
    place_id: Optional[str] = None
    is_verified: bool = True
    is_active: bool = True
    rating: float = 4.5
    total_ratings: int = 0
    distance_meters: Optional[float] = None
    open_now: Optional[bool] = None

    model_config = {"from_attributes": True}


class NearbyVetsResponse(BaseModel):
    success: bool = True
    latitude: float
    longitude: float
    radius_km: float
    count: int
    cached: bool = False
    source: str = "database"  # "google_places" or "database"
    vets: List[VetHospitalResponse]

"""
Veterinary Hospitals API: Nearby Search with 10-min caching, Hospital Registration, and Profiles.
"""
import json
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.redis import cache_service
from app.models.hospital import VetHospital
from app.schemas.hospital import (
    NearbyVetsResponse,
    VetHospitalResponse,
    VetHospitalCreate
)
from app.services.google_maps import (
    google_maps_service,
    calculate_haversine_distance
)

router = APIRouter(prefix="/vets", tags=["Vet Hospitals"])


@router.get(
    "/nearby",
    response_model=NearbyVetsResponse,
    status_code=status.HTTP_200_OK,
    summary="Find veterinary hospitals near GPS coordinates (cached for 10 minutes)"
)
async def get_nearby_vets(
    lat: Annotated[float, Query(ge=-90.0, le=90.0, description="User latitude")],
    lng: Annotated[float, Query(ge=-180.0, le=180.0, description="User longitude")],
    radius: Annotated[float, Query(ge=1.0, le=100.0, description="Radius in kilometers")] = 10.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Finds veterinary hospitals near the user's location.
    1. Checks Redis cache for recent queries (10-minute TTL).
    2. Calls Google Places API (type=veterinary_care).
    3. Merges with registered local veterinary hospitals from PostgreSQL.
    4. Computes exact distance in meters, sorts ascending, and caches for 10 minutes.
    """
    cache_key = f"vets:nearby:{round(lat, 3)}:{round(lng, 3)}:{radius}"
    cached_payload = await cache_service.get(cache_key)
    if cached_payload:
        try:
            data = json.loads(cached_payload)
            data["cached"] = True
            return data
        except Exception:
            pass

    # Fetch from registered database hospitals
    stmt = select(VetHospital).where(
        VetHospital.is_active == True,
        VetHospital.is_verified == True
    )
    result = await db.execute(stmt)
    db_hospitals = result.scalars().all()

    combined_results = []
    seen_names = set()

    radius_meters = radius * 1000

    for h in db_hospitals:
        dist = calculate_haversine_distance(lat, lng, h.latitude, h.longitude)
        if dist <= radius_meters:
            seen_names.add(h.name.lower().strip())
            combined_results.append(
                VetHospitalResponse(
                    id=h.id,
                    place_id=h.place_id,
                    name=h.name,
                    phone=h.phone,
                    emergency_phone=h.emergency_phone,
                    email=h.email,
                    address=h.address,
                    latitude=h.latitude,
                    longitude=h.longitude,
                    is_24x7=h.is_24x7,
                    is_verified=h.is_verified,
                    is_active=h.is_active,
                    ambulance_available=h.ambulance_available,
                    rating=h.rating,
                    total_ratings=h.total_ratings,
                    operating_hours=h.operating_hours,
                    distance_meters=dist,
                    open_now=True
                )
            )

    # If no hospital in tight radius, fallback to closest registered hospitals
    if not combined_results and db_hospitals:
        for h in db_hospitals:
            dist = calculate_haversine_distance(lat, lng, h.latitude, h.longitude)
            combined_results.append(
                VetHospitalResponse(
                    id=h.id,
                    place_id=h.place_id,
                    name=h.name,
                    phone=h.phone,
                    emergency_phone=h.emergency_phone,
                    email=h.email,
                    address=h.address,
                    latitude=h.latitude,
                    longitude=h.longitude,
                    is_24x7=h.is_24x7,
                    is_verified=h.is_verified,
                    is_active=h.is_active,
                    ambulance_available=h.ambulance_available,
                    rating=h.rating,
                    total_ratings=h.total_ratings,
                    operating_hours=h.operating_hours,
                    distance_meters=dist,
                    open_now=True
                )
            )

    # Fetch external Google Places results if available
    google_places = await google_maps_service.get_nearby_places(
        lat=lat,
        lng=lng,
        radius_km=radius,
        place_type="veterinary_care"
    )

    for gp in google_places:
        name_clean = gp.get("name", "").lower().strip()
        if name_clean not in seen_names:
            combined_results.append(
                VetHospitalResponse(
                    id=f"gp_{gp.get('place_id', 'unknown')}",
                    place_id=gp.get("place_id"),
                    name=gp.get("name"),
                    phone=gp.get("phone", "+911800100200"),
                    emergency_phone=None,
                    email=None,
                    address=gp.get("address", ""),
                    latitude=gp.get("latitude"),
                    longitude=gp.get("longitude"),
                    is_24x7=gp.get("is_24x7", False),
                    is_verified=True,
                    is_active=True,
                    ambulance_available=gp.get("ambulance_available", False),
                    rating=gp.get("rating", 4.0),
                    total_ratings=gp.get("total_ratings", 0),
                    distance_meters=gp.get("distance_meters"),
                    open_now=gp.get("open_now", True)
                )
            )

    # Sort ascending by distance
    combined_results.sort(key=lambda x: x.distance_meters if x.distance_meters is not None else float("inf"))

    response_data = NearbyVetsResponse(
        success=True,
        latitude=lat,
        longitude=lng,
        radius_km=radius,
        count=len(combined_results),
        cached=False,
        source="database" if not google_places else "google_places",
        vets=combined_results
    )

    # Cache response in Redis for 10 minutes (600 seconds)
    await cache_service.set(
        cache_key,
        response_data.model_dump_json(),
        expire_seconds=600
    )

    return response_data


@router.post(
    "/register",
    response_model=VetHospitalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new veterinary hospital or clinic"
)
async def register_vet_hospital(
    payload: VetHospitalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new veterinary hospital into the platform directory."""
    hospital = VetHospital(
        name=payload.name,
        phone=payload.phone,
        emergency_phone=payload.emergency_phone,
        email=payload.email,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_24x7=payload.is_24x7,
        ambulance_available=payload.ambulance_available,
        operating_hours=payload.operating_hours,
        is_verified=True,
        is_active=True,
        rating=4.8,
        total_ratings=1
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)

    return VetHospitalResponse.model_validate(hospital)


@router.get(
    "/{hospital_id}",
    response_model=VetHospitalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific vet hospital"
)
async def get_hospital_details(
    hospital_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VetHospital).where(VetHospital.id == hospital_id)
    res = await db.execute(stmt)
    hospital = res.scalar_one_or_none()
    if not hospital:
        raise NotFoundError(f"Vet hospital with ID {hospital_id} not found")

    return VetHospitalResponse.model_validate(hospital)

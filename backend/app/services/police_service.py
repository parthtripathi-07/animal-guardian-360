"""
Police Station Finder Service.
Finds the nearest police station to an incident location using Google Places API (type=police)
or realistic geo-referenced police station defaults across Indian districts.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.schemas.report import PoliceStationResponse
from app.services.google_maps import calculate_haversine_distance

logger = logging.getLogger(__name__)

# Fallback regional police stations across major Indian cities
FALLBACK_POLICE_STATIONS = [
    {
        "name": "Connaught Place Police Station",
        "address": "Shaheed Bhagat Singh Marg, Connaught Place, New Delhi - 110001",
        "phone": "+911123340058",
        "latitude": 28.6304,
        "longitude": 77.2177,
    },
    {
        "name": "Parliament Street Police Station",
        "address": "Sansad Marg, New Delhi - 110001",
        "phone": "+911123712330",
        "latitude": 28.6234,
        "longitude": 77.2115,
    },
    {
        "name": "Bandra Police Station",
        "address": "Hill Road, Bandra West, Mumbai, Maharashtra 400050",
        "phone": "+912226422055",
        "latitude": 19.0544,
        "longitude": 72.8360,
    },
    {
        "name": "Cubbon Park Police Station",
        "address": "Kasturba Road, Bengaluru, Karnataka 560001",
        "phone": "+918022942548",
        "latitude": 12.9760,
        "longitude": 77.5990,
    },
]


class PoliceService:
    @staticmethod
    async def find_nearest_police_station(lat: float, lng: float) -> PoliceStationResponse:
        """
        Locates the nearest police station to the given coordinates.
        Uses Google Places API if key is available; otherwise chooses the closest fallback station.
        """
        # Try Google Places API
        if settings.GOOGLE_MAPS_API_KEY:
            try:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lng}",
                    "radius": 5000,  # 5 km search radius
                    "type": "police",
                    "key": settings.GOOGLE_MAPS_API_KEY,
                }
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            closest = results[0]
                            loc = closest.get("geometry", {}).get("location", {})
                            p_lat = loc.get("lat", lat)
                            p_lng = loc.get("lng", lng)
                            dist = calculate_haversine_distance(lat, lng, p_lat, p_lng)
                            return PoliceStationResponse(
                                name=closest.get("name", "Local Police Station"),
                                address=closest.get("vicinity", "Near Incident Area"),
                                phone="112",
                                distance_meters=dist
                            )
            except Exception as e:
                logger.warning("Google Places Police lookup failed (%s). Using fallback station.", e)

        # Fallback calculation
        best_station = None
        min_dist = float("inf")

        for station in FALLBACK_POLICE_STATIONS:
            dist = calculate_haversine_distance(lat, lng, station["latitude"], station["longitude"])
            if dist < min_dist:
                min_dist = dist
                best_station = station

        if best_station:
            return PoliceStationResponse(
                name=best_station["name"],
                address=best_station["address"],
                phone=best_station["phone"],
                distance_meters=min_dist
            )

        return PoliceStationResponse(
            name="District Police Headquarters",
            address="Contact local authorities via 112",
            phone="112",
            distance_meters=0.0
        )


police_service = PoliceService()

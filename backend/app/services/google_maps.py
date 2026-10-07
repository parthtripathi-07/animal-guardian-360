"""
Google Maps & Places API Service.
Handles Nearby Search (vets, police), distance calculations, and 10-minute caching in Redis.
Provides seamless fallback to registered DB hospitals when API key is not configured.
"""
import json
import logging
import math
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.redis import cache_service

logger = logging.getLogger(__name__)


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS points in meters on the WGS 84 ellipsoid.
    """
    r_earth = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r_earth * c, 1)


class GoogleMapsService:
    CACHE_TTL_SECONDS = 600  # 10 minutes cache as specified

    @staticmethod
    def _make_cache_key(place_type: str, lat: float, lng: float, radius_km: float) -> str:
        # Round lat/lng to 3 decimal places (~110 meters) for high cache hit rates
        lat_rounded = round(lat, 3)
        lng_rounded = round(lng, 3)
        return f"places:{place_type}:{lat_rounded}:{lng_rounded}:{radius_km}"

    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        place_type: str = "veterinary_care"
    ) -> List[Dict[str, Any]]:
        """
        Retrieves nearby places from Google Places API or returns cached response.
        If Google API key is missing or call fails, returns an empty list so DB fallback takes over.
        """
        cache_key = self._make_cache_key(place_type, lat, lng, radius_km)
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except Exception:
                pass

        radius_meters = int(radius_km * 1000)

        # If API key is present, call Google Places API
        if settings.GOOGLE_MAPS_API_KEY:
            try:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lng}",
                    "radius": radius_meters,
                    "type": place_type,
                    "key": settings.GOOGLE_MAPS_API_KEY
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("results", [])
                        parsed = []
                        for item in results:
                            geom = item.get("geometry", {}).get("location", {})
                            item_lat = geom.get("lat", lat)
                            item_lng = geom.get("lng", lng)
                            dist = calculate_haversine_distance(lat, lng, item_lat, item_lng)
                            parsed.append({
                                "place_id": item.get("place_id"),
                                "name": item.get("name"),
                                "address": item.get("vicinity", ""),
                                "latitude": item_lat,
                                "longitude": item_lng,
                                "rating": float(item.get("rating", 4.0)),
                                "total_ratings": int(item.get("user_ratings_total", 0)),
                                "open_now": item.get("opening_hours", {}).get("open_now", True),
                                "distance_meters": dist,
                                "phone": "+911800100200",  # default placeholder until Place Details fetch
                                "is_24x7": False,
                                "ambulance_available": False
                            })
                        # Store in cache for 10 minutes
                        await cache_service.set(cache_key, json.dumps(parsed), expire_seconds=self.CACHE_TTL_SECONDS)
                        return parsed
            except Exception as e:
                logger.warning("Google Places API call failed (%s). Falling back to database.", e)

        return []


google_maps_service = GoogleMapsService()

"""
Yandex Maps integration for hospital routing and navigation.

Provides route finding from patient location to nearest hospital/pharmacy
using Yandex Static API, including distance, duration, and turn-by-turn directions.
"""
from __future__ import annotations

import requests
from app.core.config import settings


class YandexMapsClient:
    """Client for Yandex Maps Static API."""

    BASE_URL = "https://api.maps.yandex.net/services/route"
    STATIC_URL = "https://static-maps.yandex.ru/1.x"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.YANDEX_API_KEY

    def get_route(
        self, start_lat: float, start_lon: float, end_lat: float, end_lon: float
    ) -> dict | None:
        """
        Get route between two points using Yandex Maps.
        Returns route info including distance (km), duration (minutes), and polyline.
        """
        if not self.api_key:
            return None

        params = {
            "apikey": self.api_key,
            "start": f"{start_lon},{start_lat}",
            "end": f"{end_lon},{end_lat}",
            "format": "json",
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "distance_km": round(route["distance"] / 1000, 2),
                    "duration_minutes": round(route["time"] / 60, 2),
                    "polyline": self._extract_polyline(route),
                }
        except Exception:
            return None

        return None

    def get_static_map_url(
        self,
        user_lat: float,
        user_lon: float,
        hospital_lat: float,
        hospital_lon: float,
        width: int = 400,
        height: int = 400,
    ) -> str | None:
        """
        Generate a static map image URL showing user location and nearest hospital.
        """
        if not self.api_key:
            return None

        # Yandex Static Maps format: ll=lon,lat&size=width,height&z=zoom&pt=points
        points = f"{user_lon},{user_lat},pm2lbm~{hospital_lon},{hospital_lat},pm2rdm"
        url = f"{self.STATIC_URL}?apikey={self.api_key}&ll={user_lon},{user_lat}&size={width},{height}&z=15&pt={points}"

        return url

    @staticmethod
    def _extract_polyline(route: dict) -> list[tuple[float, float]] | None:
        """Extract polyline coordinates from Yandex route."""
        try:
            if "legs" in route:
                polyline = []
                for leg in route["legs"]:
                    for point in leg.get("points", []):
                        polyline.append((point["lat"], point["lon"]))
                return polyline if polyline else None
        except Exception:
            pass
        return None


def get_yandex_client() -> YandexMapsClient:
    """Get or create Yandex Maps client singleton."""
    return YandexMapsClient()

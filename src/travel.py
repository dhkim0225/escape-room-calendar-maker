"""
Travel time calculation using Naver Maps API.
"""
import requests
from typing import Optional, Tuple
from functools import lru_cache
from config import Config


class NaverMapsClient:
    """Client for Naver Maps API to calculate travel times."""

    GEOCODE_URL = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    DIRECTIONS_URL = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"

    def __init__(self):
        """Initialize Naver Maps client with API credentials."""
        self.client_id = Config.NAVER_MAPS_CLIENT_ID
        self.client_secret = Config.NAVER_MAPS_CLIENT_SECRET

        if not self.client_id or not self.client_secret:
            raise ValueError("Naver Maps API credentials are not set")

    def _get_headers(self) -> dict:
        """Get headers for Naver Maps API requests."""
        return {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
        }

    @lru_cache(maxsize=128)
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates (longitude, latitude).

        Args:
            address: Korean address string

        Returns:
            Tuple of (longitude, latitude) or None if geocoding fails
        """
        try:
            response = requests.get(
                self.GEOCODE_URL,
                headers=self._get_headers(),
                params={"query": address},
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "OK" and data.get("addresses"):
                first_result = data["addresses"][0]
                longitude = float(first_result["x"])
                latitude = float(first_result["y"])
                return (longitude, latitude)

            return None

        except Exception as e:
            print(f"Geocoding error for '{address}': {str(e)}")
            return None

    @lru_cache(maxsize=256)
    def get_travel_time(
        self, start_address: str, end_address: str
    ) -> Optional[int]:
        """
        Calculate travel time between two addresses.

        Args:
            start_address: Starting address
            end_address: Destination address

        Returns:
            Travel time in minutes, or None if calculation fails
        """
        # Geocode addresses
        start_coords = self.geocode(start_address)
        end_coords = self.geocode(end_address)

        if not start_coords or not end_coords:
            print(f"Failed to geocode: {start_address} -> {end_address}")
            return None

        # Get directions
        try:
            start_str = f"{start_coords[0]},{start_coords[1]}"
            goal_str = f"{end_coords[0]},{end_coords[1]}"

            response = requests.get(
                self.DIRECTIONS_URL,
                headers=self._get_headers(),
                params={
                    "start": start_str,
                    "goal": goal_str,
                    "option": "trafast",  # Real-time fastest route
                },
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 0 and data.get("route"):
                # Get the first route's duration
                trafast_route = data["route"].get("trafast")
                if trafast_route and len(trafast_route) > 0:
                    duration_ms = trafast_route[0]["summary"]["duration"]
                    duration_minutes = duration_ms // (1000 * 60)
                    return int(duration_minutes)

            return None

        except Exception as e:
            print(f"Directions error: {start_address} -> {end_address}: {str(e)}")
            return None

    def get_travel_time_matrix(
        self, addresses: list[str], progress_callback=None
    ) -> dict[Tuple[str, str], int]:
        """
        Calculate travel times between all pairs of addresses.

        Args:
            addresses: List of addresses
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            Dictionary mapping (start_address, end_address) to travel time in minutes
        """
        matrix = {}
        total_pairs = len(addresses) * (len(addresses) - 1)
        current = 0

        for i, start in enumerate(addresses):
            for j, end in enumerate(addresses):
                if i == j:
                    matrix[(start, end)] = 0
                else:
                    travel_time = self.get_travel_time(start, end)
                    if travel_time is not None:
                        matrix[(start, end)] = travel_time
                    else:
                        # Fallback: estimate based on location keywords
                        matrix[(start, end)] = self._estimate_travel_time(
                            start, end
                        )

                    current += 1
                    if progress_callback:
                        progress_callback(current, total_pairs)

        return matrix

    @staticmethod
    def _estimate_travel_time(start: str, end: str) -> int:
        """
        Estimate travel time based on address keywords (fallback).

        Args:
            start: Starting address
            end: Destination address

        Returns:
            Estimated travel time in minutes
        """
        # Extract districts (구)
        start_district = None
        end_district = None

        for district in ["강남구", "서초구", "송파구", "강동구", "마포구", "용산구", "성동구"]:
            if district in start:
                start_district = district
            if district in end:
                end_district = district

        # Same district: 20-30 minutes
        if start_district and start_district == end_district:
            return 25

        # Different districts: 30-60 minutes
        return 45

import time
from geopy.distance import geodesic
from geopy.point import Point
import googlemaps
import requests


class GPSService:
    def __init__(
        self,
        location_choice,
        google_maps_api_key,
        cache_seconds=2,
        static_coords=(19.230154, 72.839063),
    ):
        self.location_choice = location_choice
        self.google_maps_api_key = google_maps_api_key
        self.cache_seconds = cache_seconds
        self.static_coords = static_coords

        self._previous_coords = None
        self._gps_cache = None
        self._last_fetch_time = 0.0
        self._address_cache = {}
        self._session = requests.Session()
        self._gmaps = googlemaps.Client(key=google_maps_api_key) if google_maps_api_key else None

    def get_coordinates(self):
        now = time.time()
        if self._gps_cache and (now - self._last_fetch_time < self.cache_seconds):
            return self._gps_cache

        if self.location_choice == "2":
            coords = self.static_coords
            self._update_cache(coords, now)
            return coords

        try:
            response = self._session.post(
                "https://www.googleapis.com/geolocation/v1/geolocate",
                json={"considerIp": True},
                params={"key": self.google_maps_api_key},
                timeout=5,
            )
            if response.status_code != 200:
                return self._gps_cache

            data = response.json()
            coords = (data["location"]["lat"], data["location"]["lng"])
            self._update_cache(coords, now)
            return coords
        except Exception:
            return self._gps_cache

    def _update_cache(self, coords, now):
        if coords != self._previous_coords:
            print(f"Retrieved GPS coordinates: Latitude {coords[0]}, Longitude {coords[1]}")
            self._previous_coords = coords
        self._gps_cache = coords
        self._last_fetch_time = now

    def get_location_details(self, lat, lng):
        cache_key = (round(lat, 5), round(lng, 5))
        if cache_key in self._address_cache:
            return self._address_cache[cache_key]

        if not self._gmaps:
            return "Unknown Location"

        try:
            reverse_geocode_result = self._gmaps.reverse_geocode((lat, lng))
            address = (
                reverse_geocode_result[0]["formatted_address"]
                if reverse_geocode_result
                else "Unknown Location"
            )
            self._address_cache[cache_key] = address
            return address
        except Exception:
            return "Unknown Location"

    @staticmethod
    def calculate_target_coordinates(drone_coords, distance_meters, bearing_degrees):
        origin = Point(latitude=drone_coords[0], longitude=drone_coords[1])
        destination = geodesic(kilometers=distance_meters / 1000.0).destination(
            origin,
            bearing_degrees,
        )
        return destination.latitude, destination.longitude

    @staticmethod
    def generate_google_maps_link(lat, lng):
        return f"https://www.google.com/maps?q={lat},{lng}"

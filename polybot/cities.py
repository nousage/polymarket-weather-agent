"""City definitions and aliases."""
from __future__ import annotations

from typing import Dict, Tuple

CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "New York": (40.7128, -74.0060),
    "London": (51.5074, -0.1278),
    "Tokyo": (35.6762, 139.6503),
    "Singapore": (1.3521, 103.8198),
    "Hong Kong": (22.3193, 114.1694),
    "Dubai": (25.2048, 55.2708),
    "Shanghai": (31.2304, 121.4737),
    "Sydney": (-33.8688, 151.2093),
    "Mumbai": (19.0760, 72.8777),
    "Sao Paulo": (-23.5505, -46.6333),
    "Chicago": (41.8781, -87.6298),
    "Toronto": (43.65107, -79.347015),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.5200, 13.4050),
    "Seoul": (37.5665, 126.9780),
    "Beijing": (39.9042, 116.4074),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
    "Chongqing": (29.4316, 106.9123),
}

CITY_ALIASES: Dict[str, str] = {city.lower(): city for city in CITY_COORDS}

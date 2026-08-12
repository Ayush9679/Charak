import math
from typing import Optional, Tuple

def calculate_haversine_distance(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float]
) -> Optional[float]:
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in kilometers (rounded to 1 decimal place).
    Returns None if any coordinate is missing or invalid.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    try:
        # Earth radius in kilometers
        R = 6371.0

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        distance = R * c

        return round(distance, 1)
    except Exception:
        return None

def estimate_travel_time_mins(distance_km: Optional[float]) -> Optional[int]:
    """
    Estimates travel time in minutes based on distance.
    Assumes average urban traffic speed of 25 km/h.
    """
    if distance_km is None or distance_km < 0:
        return None

    # 25 km/h -> 1 km takes 2.4 minutes + 3 min base buffer
    time_mins = int(round((distance_km / 25.0) * 60.0 + 3.0))
    return max(4, time_mins)

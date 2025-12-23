"""Location and distance calculation for deals."""

import math
from typing import Optional

# Rickman, TN coordinates (home base)
HOME_LAT = 36.2667
HOME_LNG = -85.4167
LOCAL_RADIUS_MILES = 100

# Known city coordinates for distance calculation
# Focus on areas within reasonable driving distance of Rickman, TN
CITY_COORDS: dict[str, tuple[float, float]] = {
    # Tennessee
    "rickman": (36.2667, -85.4167),
    "cookeville": (36.1628, -85.5016),
    "nashville": (36.1627, -86.7816),
    "knoxville": (35.9606, -83.9207),
    "chattanooga": (35.0456, -85.3097),
    "memphis": (35.1495, -90.0490),
    "murfreesboro": (35.8456, -86.3903),
    "clarksville": (36.5298, -87.3595),
    "jackson": (35.6145, -88.8139),
    "johnson city": (36.3134, -82.3535),
    "kingsport": (36.5484, -82.5618),
    "franklin": (35.9251, -86.8689),
    "hendersonville": (36.3048, -86.6200),
    "lebanon": (36.2081, -86.2911),
    "gallatin": (36.3884, -86.4467),
    "columbia": (35.6151, -87.0353),
    "crossville": (35.9489, -85.0269),
    "sparta": (35.9256, -85.4641),
    "livingston": (36.3834, -85.3230),
    "gainesboro": (36.3556, -85.6583),
    "carthage": (36.2523, -85.9517),
    "smithville": (35.9606, -85.8142),
    "mcminnville": (35.6834, -85.7697),
    "manchester": (35.4817, -86.0886),
    "tullahoma": (35.3620, -86.2094),
    "shelbyville": (35.4834, -86.4603),

    # Kentucky
    "bowling green": (36.9685, -86.4808),
    "lexington": (38.0406, -84.5037),
    "louisville": (38.2527, -85.7585),
    "owensboro": (37.7719, -87.1112),
    "elizabethtown": (37.6939, -85.8591),
    "glasgow": (36.9959, -85.9119),
    "somerset": (37.0920, -84.6041),
    "london": (37.1290, -84.0833),
    "corbin": (36.9487, -84.0969),

    # Alabama
    "huntsville": (34.7304, -86.5861),
    "birmingham": (33.5207, -86.8025),
    "decatur": (34.6059, -86.9833),
    "florence": (34.7998, -87.6772),
    "athens": (34.8026, -86.9717),

    # Georgia
    "atlanta": (33.7490, -84.3880),
    "rome": (34.2570, -85.1647),
    "dalton": (34.7698, -84.9702),

    # Virginia
    "bristol": (36.5951, -82.1887),

    # North Carolina
    "asheville": (35.5951, -82.5515),
}


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def parse_location(location: str) -> Optional[tuple[float, float]]:
    """
    Parse a location string and return coordinates.

    Handles formats like:
    - "Nashville, TN"
    - "Cookeville"
    - "Nashville TN"
    """
    if not location:
        return None

    # Normalize: lowercase, remove extra whitespace
    location_lower = location.lower().strip()

    # Try to extract city name (before comma or state abbreviation)
    city = location_lower.split(",")[0].strip()
    city = city.split(" tn")[0].strip()
    city = city.split(" ky")[0].strip()
    city = city.split(" al")[0].strip()
    city = city.split(" ga")[0].strip()

    # Look up in our city database
    if city in CITY_COORDS:
        return CITY_COORDS[city]

    # Try the full location string too
    if location_lower in CITY_COORDS:
        return CITY_COORDS[location_lower]

    return None


def calculate_distance_from_home(location: str) -> Optional[int]:
    """
    Calculate distance in miles from home (Rickman, TN) to a location.

    Returns None if location cannot be parsed.
    """
    coords = parse_location(location)
    if not coords:
        return None

    distance = haversine_distance(HOME_LAT, HOME_LNG, coords[0], coords[1])
    return round(distance)


def is_within_pickup_range(location: str) -> bool:
    """Check if a location is within local pickup range (100 miles)."""
    distance = calculate_distance_from_home(location)
    if distance is None:
        return False
    return distance <= LOCAL_RADIUS_MILES

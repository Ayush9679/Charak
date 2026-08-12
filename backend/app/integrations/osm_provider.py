import httpx
import time
from typing import List, Dict, Any, Optional
from app.core.distance import calculate_haversine_distance, estimate_travel_time_mins

# Simple in-memory cache for Overpass queries (TTL: 15 mins)
_OSM_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 15 * 60

class OSMHospitalProvider:
    def __init__(self, overpass_url: str = "https://overpass-api.de/api/interpreter", timeout_seconds: float = 12.0):
        self.overpass_url = overpass_url
        self.timeout_seconds = timeout_seconds

    def _get_cache_key(self, lat: float, lng: float, radius_km: float) -> str:
        return f"{round(lat, 2)}:{round(lng, 2)}:{round(radius_km, 1)}"

    async def fetch_nearby_hospitals(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Queries OpenStreetMap via Overpass API for real local hospital facilities around coordinates.
        Returns normalized hospital dictionaries with EXTERNAL_DISCOVERY provenance.
        """
        if lat is None or lng is None:
            return []

        cache_key = self._get_cache_key(lat, lng, radius_km)
        now = time.time()

        if cache_key in _OSM_CACHE:
            cached_entry = _OSM_CACHE[cache_key]
            if now - cached_entry["timestamp"] < CACHE_TTL_SECONDS:
                return cached_entry["data"]

        radius_meters = int(radius_km * 1000)
        query = f"""
        [out:json][timeout:12];
        (
          node["amenity"="hospital"](around:{radius_meters},{lat},{lng});
          way["amenity"="hospital"](around:{radius_meters},{lat},{lng});
          relation["amenity"="hospital"](around:{radius_meters},{lat},{lng});
          node["healthcare"="hospital"](around:{radius_meters},{lat},{lng});
          way["healthcare"="hospital"](around:{radius_meters},{lat},{lng});
        );
        out center tags;
        """

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.overpass_url, data={"data": query})
                if response.status_code != 200:
                    print(f"[OSM PROVIDER WARNING] Status {response.status_code}: Overpass API unavailable.")
                    return []

                data = response.json()
                elements = data.get("elements", [])
                
                hospitals = []
                for elem in elements:
                    tags = elem.get("tags", {})
                    name = tags.get("name") or tags.get("name:en") or tags.get("official_name")
                    if not name:
                        continue

                    # Determine center coordinates
                    elem_lat = elem.get("lat") or elem.get("center", {}).get("lat")
                    elem_lng = elem.get("lon") or elem.get("center", {}).get("lon")

                    if elem_lat is None or elem_lng is None:
                        continue

                    dist_km = calculate_haversine_distance(lat, lng, elem_lat, elem_lng)
                    if dist_km is not None and dist_km > radius_km + 1.0:
                        continue

                    travel_mins = estimate_travel_time_mins(dist_km)

                    # Extract address
                    addr_parts = [
                        tags.get("addr:full"),
                        tags.get("addr:street"),
                        tags.get("addr:suburb") or tags.get("addr:district"),
                        tags.get("addr:city")
                    ]
                    address = ", ".join([p for p in addr_parts if p]) or f"Near {name}"
                    city = tags.get("addr:city") or "Local area"

                    # Emergency status
                    emergency_tag = tags.get("emergency")
                    emergency_ready = True if emergency_tag in ["yes", "24/7"] else (False if emergency_tag == "no" else True)

                    # Sanitize website
                    website = tags.get("website") or tags.get("contact:website")
                    if website and not (website.startswith("http://") or website.startswith("https://")):
                        website = f"https://{website}"

                    phone = tags.get("phone") or tags.get("contact:phone")

                    # Extract specialty signals if available in tags
                    spec_list = ["General Medicine"]
                    if tags.get("healthcare:speciality"):
                        raw_spec = tags.get("healthcare:speciality", "").replace(";", ",").split(",")
                        spec_list.extend([s.strip().title() for s in raw_spec if len(s.strip()) > 2])

                    hospitals.append({
                        "id": f"osm-{elem.get('id')}",
                        "name": name.strip(),
                        "hfr_id": f"OSM-{elem.get('id')}",
                        "address": address,
                        "city": city,
                        "state": tags.get("addr:state") or "Local State",
                        "lat": elem_lat,
                        "lng": elem_lng,
                        "distance_km": dist_km,
                        "travel_time_mins": travel_mins,
                        "specialties": list(set(spec_list)),
                        "emergency_ready": emergency_ready,
                        "insurance_supported": ["Public / Direct Consultation"],
                        "estimated_cost_range": None,
                        "pricing": {
                            "min": None,
                            "max": None,
                            "currency": "INR",
                            "status": "UNAVAILABLE",
                            "source": None,
                            "source_url": None,
                            "last_verified_at": None
                        },
                        "data_provenance": "EXTERNAL_DISCOVERY",
                        "source": "OpenStreetMap",
                        "verification_status": "EXTERNAL_SOURCE",
                        "data_freshness": "DISCOVERED",
                        "availability": None, # Never fabricate fake bed availability for OSM discovery
                        "doctors": [], # Never fabricate fake doctors for OSM discovery
                        "rating": None, # Never fabricate fake ratings
                        "suitability": None, # Will be computed by merge service
                        "recommendation_reasons": ["🌐 Discovered via OpenStreetMap local network"],
                        "phone": phone,
                        "website": website
                    })

                _OSM_CACHE[cache_key] = {"timestamp": now, "data": hospitals}
                return hospitals
        except Exception as e:
            print(f"[OSM PROVIDER EXCEPTION] {e}")
            return []

osm_provider = OSMHospitalProvider()

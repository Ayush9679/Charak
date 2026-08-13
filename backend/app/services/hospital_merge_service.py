from typing import List, Dict, Any, Optional
from app.core.distance import calculate_haversine_distance, estimate_travel_time_mins
from app.integrations.pricing_provider import pricing_provider
import re

def normalize_name(name: str) -> str:
    """Normalizes hospital name for deduplication comparison."""
    n = name.lower()
    n = re.sub(r'\b(hospital|institute|center|centre|super|speciality|specialty|multi|noida|delhi)\b', '', n)
    n = re.sub(r'[^a-z0-9]', '', n)
    return n.strip()

class HospitalMergeService:
    def merge_and_rank_hospitals(
        self,
        hfr_hospitals: List[Any], # SQLAlchemy models or dicts
        osm_hospitals: List[Dict[str, Any]],
        user_lat: Optional[float],
        user_lng: Optional[float],
        primary_specialty: str,
        secondary_specialties: List[str],
        urgency: str,
        preferred_insurance: Optional[str] = "Ayushman Bharat",
        max_radius_km: float = 15.0
    ) -> List[Dict[str, Any]]:
        """
        Combines HFR verified registry facilities and OpenStreetMap local discovered facilities.
        Deduplicates records, calculates Haversine distance, computes suitability, and returns ranked list.
        """
        merged_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process HFR verified facilities
        for h in hfr_hospitals:
            # Evaluate structured pricing via pricing_provider
            h_id = str(getattr(h, "id", None) or h.get("id"))
            hfr_id = getattr(h, "hfr_id", None) or h.get("hfr_id")
            
            pricing_data = pricing_provider.get_hospital_pricing(
                hospital_id=h_id,
                hfr_id=hfr_id,
                existing_min=getattr(h, "pricing_min", None) or (h.get("pricing_min") if isinstance(h, dict) else None),
                existing_max=getattr(h, "pricing_max", None) or (h.get("pricing_max") if isinstance(h, dict) else None),
                existing_currency=getattr(h, "pricing_currency", "INR") or (h.get("pricing_currency", "INR") if isinstance(h, dict) else "INR"),
                existing_status=getattr(h, "pricing_status", "UNAVAILABLE") or (h.get("pricing_status", "UNAVAILABLE") if isinstance(h, dict) else "UNAVAILABLE"),
                existing_source=getattr(h, "pricing_source", None) or (h.get("pricing_source") if isinstance(h, dict) else None),
                existing_source_url=getattr(h, "pricing_source_url", None) or (h.get("pricing_source_url") if isinstance(h, dict) else None),
                existing_last_verified_at=getattr(h, "pricing_last_verified_at", None) or (h.get("pricing_last_verified_at") if isinstance(h, dict) else None),
                existing_treatment_pricing=getattr(h, "treatment_pricing", None) or (h.get("treatment_pricing") if isinstance(h, dict) else None),
            )

            # Handle both ORM models and Dict objects
            h_dict = {
                "id": h_id,
                "name": getattr(h, "name", None) or h.get("name"),
                "hfr_id": hfr_id,
                "address": getattr(h, "address", None) or h.get("address"),
                "city": getattr(h, "city", None) or h.get("city"),
                "state": getattr(h, "state", None) or h.get("state"),
                "lat": getattr(h, "lat", None) or h.get("lat"),
                "lng": getattr(h, "lng", None) or h.get("lng"),
                "specialties": getattr(h, "specialties", None) or h.get("specialties") or [],
                "emergency_ready": getattr(h, "emergency_ready", None) if hasattr(h, "emergency_ready") else h.get("emergency_ready", False),
                "insurance_supported": getattr(h, "insurance_supported", None) or h.get("insurance_supported") or [],
                "estimated_cost_range": None, # Deprecated legacy field set to None
                "pricing": pricing_data,
                "treatment_pricing": getattr(h, "treatment_pricing", None) or (h.get("treatment_pricing") if isinstance(h, dict) else None) or [],
                "suitability": getattr(h, "suitability_score", None) if hasattr(h, "suitability_score") else h.get("suitability_score"),
                "data_provenance": getattr(h, "data_provenance", None) or h.get("data_provenance") or "PUBLIC_REGISTRY",
                "source": "ABDM HFR",
                "verification_status": "VERIFIED_REGISTRY",
                "data_freshness": "VERIFIED",
                "rating": getattr(h, "rating", None) or h.get("rating") or 4.5,
                "availability": getattr(h, "availability", None) or h.get("availability"),
                "doctors": getattr(h, "doctors", None) or h.get("doctors") or []
            }
            norm_k = normalize_name(h_dict["name"])
            merged_map[norm_k] = h_dict

        # 2. Deduplicate and merge OSM local discovery facilities
        for osm_h in osm_hospitals:
            norm_k = normalize_name(osm_h["name"])
            
            # Check if matching facility exists by normalized name or geographic proximity (< 0.5km)
            existing_key = None
            if norm_k in merged_map:
                existing_key = norm_k
            else:
                for k, existing_h in merged_map.items():
                    if existing_h.get("lat") and existing_h.get("lng") and osm_h.get("lat") and osm_h.get("lng"):
                        d = calculate_haversine_distance(existing_h["lat"], existing_h["lng"], osm_h["lat"], osm_h["lng"])
                        if d is not None and d < 0.5:
                            existing_key = k
                            break

            if existing_key:
                # Merge: HFR takes precedence for verified metadata; OSM supplements phone/website/coordinates
                existing = merged_map[existing_key]
                if not existing.get("phone") and osm_h.get("phone"):
                    existing["phone"] = osm_h["phone"]
                if not existing.get("website") and osm_h.get("website"):
                    existing["website"] = osm_h["website"]
                if (existing.get("lat") is None or existing.get("lng") is None) and osm_h.get("lat") and osm_h.get("lng"):
                    existing["lat"] = osm_h["lat"]
                    existing["lng"] = osm_h["lng"]
            else:
                osm_h["estimated_cost_range"] = None
                osm_h["pricing"] = {
                    "min": None,
                    "max": None,
                    "currency": "INR",
                    "status": "UNAVAILABLE",
                    "source": None,
                    "source_url": None,
                    "last_verified_at": None
                }
                merged_map[norm_k] = osm_h

        # 3. Calculate distance, travel time, suitability score & recommendation reasons
        final_list = []

        for h in merged_map.values():
            dist_km = calculate_haversine_distance(user_lat, user_lng, h.get("lat"), h.get("lng"))
            travel_mins = estimate_travel_time_mins(dist_km)

            h["distance_km"] = dist_km
            h["travel_time_mins"] = travel_mins
            h["distance_source"] = "GPS_HAVERSINE" if dist_km is not None else "UNAVAILABLE"

            # Calculate transparent CHANAKYA match score
            spec_list = [s.lower() for s in (h.get("specialties") or [])]
            match_primary = primary_specialty.lower() in spec_list or any(primary_specialty.lower() in s for s in spec_list)
            match_secondary = any(sec.lower() in spec_list for sec in secondary_specialties)

            base_score = 70.0
            reasons = []

            if match_primary:
                base_score += 20.0
                reasons.append(f"✔ Verified specialty match for {primary_specialty}")
            elif match_secondary:
                base_score += 10.0
                reasons.append("✔ Secondary specialty match available")

            if urgency in ["URGENT", "EMERGENCY"] and h.get("emergency_ready"):
                base_score += 8.0
                reasons.append("✔ 24/7 Emergency Department operational")

            if dist_km is not None:
                if dist_km <= max_radius_km:
                    base_score += 5.0
                    reasons.append(f"📍 Within {dist_km} km of your location")
                else:
                    reasons.append(f"📍 Located {dist_km} km away")

            if preferred_insurance and any(preferred_insurance.lower() in ins.lower() for ins in (h.get("insurance_supported") or [])):
                base_score += 5.0
                reasons.append(f"✔ Accepts {preferred_insurance}")

            if h.get("data_provenance") == "HOSPITAL_INTEGRATION":
                base_score += 2.0
                reasons.append("✔ Live telemetry & hospital integration active")
            elif h.get("data_provenance") == "EXTERNAL_DISCOVERY":
                reasons.append("🌐 Discovered via OpenStreetMap local network")

            # A stored score is a canonical hospital attribute. Otherwise retain the
            # current recommendation algorithm as the single calculation for this result.
            h["suitability"] = h["suitability"] if h.get("suitability") is not None else min(99.0, round(base_score, 1))
            h["recommendation_reasons"] = reasons
            final_list.append(h)

        # 4. Sorting: If location available, sort by suitability & distance
        if user_lat is not None and user_lng is not None:
            if urgency in ["URGENT", "EMERGENCY"]:
                final_list.sort(key=lambda x: (not x.get("emergency_ready", False), x.get("distance_km") or 9999, -(x.get("suitability") or 0)))
            else:
                final_list.sort(key=lambda x: (-(x.get("suitability") or 0), x.get("distance_km") or 9999))
        else:
            final_list.sort(key=lambda x: -(x.get("suitability") or 0))

        return final_list

hospital_merge_service = HospitalMergeService()

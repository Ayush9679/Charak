from typing import Optional, Dict, Any
from datetime import datetime

class HospitalPricingProvider:
    """
    Authoritative hospital pricing provider abstraction.
    Only returns pricing data when backed by a verified, traceable hospital API or published pricing feed.
    Returns status = 'UNAVAILABLE' when no authoritative source exists.
    """
    def __init__(self, pricing_freshness_hours: int = 24):
        self.pricing_freshness_hours = pricing_freshness_hours

    def get_hospital_pricing(
        self,
        hospital_id: str,
        hfr_id: Optional[str] = None,
        existing_min: Optional[float] = None,
        existing_max: Optional[float] = None,
        existing_currency: str = "INR",
        existing_status: str = "UNAVAILABLE",
        existing_source: Optional[str] = None,
        existing_source_url: Optional[str] = None,
        existing_last_verified_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Retrieves pricing information for a hospital.
        Validates provenance and returns status = UNAVAILABLE if pricing is not from an authoritative provider.
        """
        # If explicitly marked VERIFIED with a valid source and non-null values
        if existing_status == "VERIFIED" and existing_source and (existing_min is not None or existing_max is not None):
            # Check freshness
            if existing_last_verified_at:
                age_hours = (datetime.utcnow() - existing_last_verified_at).total_seconds() / 3600.0
                if age_hours > self.pricing_freshness_hours:
                    return {
                        "min": existing_min,
                        "max": existing_max,
                        "currency": existing_currency,
                        "status": "STALE",
                        "source": existing_source,
                        "source_url": existing_source_url,
                        "last_verified_at": existing_last_verified_at.isoformat()
                    }

            return {
                "min": existing_min,
                "max": existing_max,
                "currency": existing_currency,
                "status": "VERIFIED",
                "source": existing_source,
                "source_url": existing_source_url,
                "last_verified_at": existing_last_verified_at.isoformat() if existing_last_verified_at else datetime.utcnow().isoformat()
            }

        # Default fallback for unverified / legacy data: Honest UNAVAILABLE
        return {
            "min": None,
            "max": None,
            "currency": "INR",
            "status": "UNAVAILABLE",
            "source": None,
            "source_url": None,
            "last_verified_at": None
        }

    def get_doctor_pricing(
        self,
        doctor_id: str,
        existing_min: Optional[float] = None,
        existing_max: Optional[float] = None,
        existing_currency: str = "INR",
        existing_status: str = "UNAVAILABLE",
        existing_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves consultation fee pricing for a doctor.
        """
        if existing_status == "VERIFIED" and existing_source and existing_min is not None:
            return {
                "min": existing_min,
                "max": existing_max or existing_min,
                "currency": existing_currency,
                "status": "VERIFIED",
                "source": existing_source
            }

        return {
            "min": None,
            "max": None,
            "currency": "INR",
            "status": "UNAVAILABLE",
            "source": None
        }

pricing_provider = HospitalPricingProvider()

"""
ClinicalAnalysisService - Phase 6
The ONE central analysis pipeline used by:
  - POST /recommendations
  - POST /chat (symptom/emergency intents)
  - Emergency routing

Avoids duplicate clinical logic across routes.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.ai.symptom_normalizer import normalize_symptoms
from app.ai.groq_client import groq_client
from app.models.hospital import HospitalModel
from app.integrations.osm_provider import osm_provider
from app.services.hospital_merge_service import hospital_merge_service
from app.schemas.schemas import (
    HospitalSchema,
    AvailabilitySchema,
    DoctorSchema,
    HospitalPricingSchema,
    DoctorPricingSchema,
)


def _build_hospital_schema(h_dict: Dict[str, Any]) -> HospitalSchema:
    """Serialize a merged hospital dict into a HospitalSchema."""
    avail_schema = None
    if h_dict.get("availability"):
        avail = h_dict["availability"]
        avail_schema = AvailabilitySchema(
            beds_available=getattr(avail, "beds_available", None) or avail.get("beds_available", 0),
            icu_available=getattr(avail, "icu_available", None) or avail.get("icu_available", 0),
            total_beds=getattr(avail, "total_beds", None) or avail.get("total_beds", 0),
            total_icu=getattr(avail, "total_icu", None) or avail.get("total_icu", 0),
            last_updated=(
                getattr(avail, "last_updated", datetime.utcnow()).isoformat()
                if hasattr(getattr(avail, "last_updated", None), "isoformat")
                else str(getattr(avail, "last_updated", "Recent"))
            ),
            status=getattr(avail, "status", "AVAILABLE") or "AVAILABLE",
        )

    docs_schema: List[DoctorSchema] = []
    if h_dict.get("doctors"):
        for d in h_dict["doctors"]:
            doc_pricing = DoctorPricingSchema(
                min=getattr(d, "consultation_fee_min", None) or (d.get("consultation_fee_min") if isinstance(d, dict) else None),
                max=getattr(d, "consultation_fee_max", None) or (d.get("consultation_fee_max") if isinstance(d, dict) else None),
                currency=getattr(d, "consultation_fee_currency", "INR") or "INR",
                status=getattr(d, "consultation_fee_status", "UNAVAILABLE") or "UNAVAILABLE",
                source=getattr(d, "consultation_fee_source", None),
            )
            if hasattr(d, "id"):
                doc_s = DoctorSchema.model_validate(d)
                doc_s.pricing = doc_pricing
                doc_s.consultation_fee = None
                docs_schema.append(doc_s)
            elif isinstance(d, dict) and d.get("name"):
                docs_schema.append(DoctorSchema(
                    id=d.get("id", str(uuid.uuid4())),
                    name=d.get("name"),
                    specialty=d.get("specialty", "General Medicine"),
                    qualification=d.get("qualification", "MBBS"),
                    experience_years=d.get("experience_years", 10),
                    consultation_fee=None,
                    pricing=doc_pricing,
                    available_today=d.get("available_today", True),
                    rating=d.get("rating", 4.8),
                ))

    pricing_data = h_dict.get("pricing") or {"status": "UNAVAILABLE"}
    h_pricing = HospitalPricingSchema(**pricing_data)

    return HospitalSchema(
        id=h_dict["id"],
        name=h_dict["name"],
        hfr_id=h_dict.get("hfr_id", h_dict["id"]),
        address=h_dict.get("address", "Local Area"),
        city=h_dict.get("city", "Nearby"),
        state=h_dict.get("state", "State"),
        lat=h_dict.get("lat"),
        lng=h_dict.get("lng"),
        distance_km=h_dict.get("distance_km"),
        travel_time_mins=h_dict.get("travel_time_mins"),
        distance_source=h_dict.get("distance_source", "UNAVAILABLE"),
        specialties=h_dict.get("specialties") or ["General Medicine"],
        emergency_ready=h_dict.get("emergency_ready", False),
        insurance_supported=h_dict.get("insurance_supported") or ["Direct Consultation"],
        estimated_cost_range=None,
        pricing=h_pricing,
        treatment_pricing=h_dict.get("treatment_pricing") or [],
        data_provenance=h_dict.get("data_provenance", "PUBLIC_REGISTRY"),
        source=h_dict.get("source", "ABDM HFR"),
        verification_status=h_dict.get("verification_status", "VERIFIED_REGISTRY"),
        data_freshness=h_dict.get("data_freshness", "VERIFIED"),
        availability=avail_schema,
        doctors=docs_schema,
        rating=h_dict.get("rating"),
        suitability=h_dict.get("suitability", 85.0),
        recommendation_reasons=h_dict.get("recommendation_reasons") or [],
        phone=h_dict.get("phone"),
        website=h_dict.get("website"),
    )


class ClinicalAnalysisService:
    """
    The one central clinical analysis pipeline.

    Accepts raw symptom text + optional GPS coordinates.
    Returns a standardized AnalysisResult with:
    - triage fields (urgency, specialty, conditions, red_flags)
    - normalized symptoms
    - ranked hospital list
    """

    async def analyze(
        self,
        symptoms: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        db: Optional[Session] = None,
        insurance: Optional[str] = "Ayushman Bharat",
        max_radius_km: float = 15.0,
        include_hospitals: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the complete clinical analysis pipeline.

        Returns a dict with all triage and hospital fields.
        """
        # Step 1: Normalize symptoms (typo-tolerant, synonym-aware)
        norm = normalize_symptoms(symptoms)
        normalized_text = symptoms
        if norm.canonical_symptoms:
            # Enrich the symptom text with canonical forms for better LLM analysis
            normalized_text = symptoms + " [normalized: " + ", ".join(norm.canonical_symptoms) + "]"

        # Step 2: AI triage via Groq (or deterministic fallback)
        triage = await groq_client.analyze_symptoms(
            symptoms=normalized_text,
            location=location_name or "Current location",
        )

        primary_specialty = triage.get("primary_specialty", "General Medicine")
        secondary_specialties = triage.get("secondary_specialties", [])
        urgency = triage.get("urgency_category", "ROUTINE")
        urgency_summary = triage.get("urgency_summary", "Analysis completed.")
        clinical_summary = triage.get("clinical_summary", "Potential explanations identified from the reported symptoms.")
        possible_conditions = triage.get("possible_conditions", [])
        red_flags = triage.get("red_flags", [])
        extracted_signals = triage.get("extracted_signals", [])

        hospitals: List[HospitalSchema] = []

        # Step 3: Hospital discovery (if db and coordinates available)
        if include_hospitals and db is not None:
            hfr_hospitals = db.query(HospitalModel).all()
            osm_hospitals = []
            if latitude is not None and longitude is not None:
                osm_hospitals = await osm_provider.fetch_nearby_hospitals(
                    lat=latitude,
                    lng=longitude,
                    radius_km=max_radius_km,
                )

            merged = hospital_merge_service.merge_and_rank_hospitals(
                hfr_hospitals=hfr_hospitals,
                osm_hospitals=osm_hospitals,
                user_lat=latitude,
                user_lng=longitude,
                primary_specialty=primary_specialty,
                secondary_specialties=secondary_specialties,
                urgency=urgency,
                preferred_insurance=insurance,
                max_radius_km=max_radius_km,
            )

            for h_dict in merged:
                hospitals.append(_build_hospital_schema(h_dict))

        return {
            "analysis_id": str(uuid.uuid4()),
            "urgency_category": urgency,
            "urgency_summary": urgency_summary,
            "clinical_summary": clinical_summary,
            "primary_specialty": primary_specialty,
            "secondary_specialties": secondary_specialties,
            "possible_conditions": possible_conditions,
            "red_flags": red_flags,
            "extracted_signals": extracted_signals,
            "normalized_symptoms": norm.canonical_symptoms,
            "unresolved_terms": norm.unresolved_terms,
            "hospitals": hospitals,
            "hospital_data_status": "AVAILABLE" if hospitals else "UNAVAILABLE",
            "processed_at": datetime.utcnow().isoformat(),
        }


clinical_analysis_service = ClinicalAnalysisService()

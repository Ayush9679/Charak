from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.db.database import get_db
from app.models.hospital import HospitalModel, RecommendationRecord
from app.schemas.schemas import (
    SymptomInputSchema,
    RecommendationResponseSchema,
    HospitalSchema,
    AvailabilitySchema,
    DoctorSchema,
    HospitalPricingSchema,
    DoctorPricingSchema
)
from app.ai.groq_client import groq_client

from app.core.distance import calculate_haversine_distance, estimate_travel_time_mins

router = APIRouter()

from app.integrations.osm_provider import osm_provider
from app.services.hospital_merge_service import hospital_merge_service

@router.post("/recommendations", response_model=RecommendationResponseSchema)
async def create_recommendation(
    payload: SymptomInputSchema,
    db: Session = Depends(get_db)
):
    # 1. AI Triage Pipeline (Groq or Deterministic Triage Fallback)
    triage = await groq_client.analyze_symptoms(
        symptoms=payload.symptoms,
        location=payload.location or "Current location"
    )

    primary_specialty = triage.get("primary_specialty", "General Medicine")
    secondary_specialties = triage.get("secondary_specialties", [])
    urgency = triage.get("urgency_category", "ROUTINE")
    urgency_summary = triage.get("urgency_summary", "Analysis completed.")
    clinical_summary = triage.get("clinical_summary", "Potential explanations identified from the reported symptoms.")
    possible_conditions = triage.get("possible_conditions", [])
    red_flags = triage.get("red_flags", [])
    extracted_signals = triage.get("extracted_signals", [])

    # 2. Fetch HFR hospital records from SQLite DB
    hfr_hospitals = db.query(HospitalModel).all()

    # 3. Fetch local discovery hospital facilities via OpenStreetMap (if user coordinates exist)
    osm_hospitals = []
    if payload.latitude is not None and payload.longitude is not None:
        search_radius = payload.distance or 10.0
        osm_hospitals = await osm_provider.fetch_nearby_hospitals(
            lat=payload.latitude,
            lng=payload.longitude,
            radius_km=search_radius
        )

    # 4. Merge HFR + OSM facilities, deduplicate, calculate Haversine distance & rank
    merged_results = hospital_merge_service.merge_and_rank_hospitals(
        hfr_hospitals=hfr_hospitals,
        osm_hospitals=osm_hospitals,
        user_lat=payload.latitude,
        user_lng=payload.longitude,
        primary_specialty=primary_specialty,
        secondary_specialties=secondary_specialties,
        urgency=urgency,
        preferred_insurance=payload.insurance,
        max_radius_km=payload.distance or 15.0
    )

    ranked_schemas: list[HospitalSchema] = []

    for h_dict in merged_results:
        avail_schema = None
        if h_dict.get("availability"):
            avail = h_dict["availability"]
            avail_schema = AvailabilitySchema(
                beds_available=getattr(avail, "beds_available", None) or avail.get("beds_available", 0),
                icu_available=getattr(avail, "icu_available", None) or avail.get("icu_available", 0),
                total_beds=getattr(avail, "total_beds", None) or avail.get("total_beds", 0),
                total_icu=getattr(avail, "total_icu", None) or avail.get("total_icu", 0),
                last_updated=getattr(avail, "last_updated", datetime.utcnow()).isoformat() if hasattr(getattr(avail, "last_updated", None), "isoformat") else str(getattr(avail, "last_updated", "Recent")),
                status=getattr(avail, "status", "AVAILABLE") or "AVAILABLE"
            )

        docs_schema = []
        if h_dict.get("doctors"):
            for d in h_dict["doctors"]:
                doc_pricing = DoctorPricingSchema(
                    min=getattr(d, "consultation_fee_min", None) or (d.get("consultation_fee_min") if isinstance(d, dict) else None),
                    max=getattr(d, "consultation_fee_max", None) or (d.get("consultation_fee_max") if isinstance(d, dict) else None),
                    currency=getattr(d, "consultation_fee_currency", "INR") or (d.get("consultation_fee_currency", "INR") if isinstance(d, dict) else "INR"),
                    status=getattr(d, "consultation_fee_status", "UNAVAILABLE") or (d.get("consultation_fee_status", "UNAVAILABLE") if isinstance(d, dict) else "UNAVAILABLE"),
                    source=getattr(d, "consultation_fee_source", None) or (d.get("consultation_fee_source") if isinstance(d, dict) else None)
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
                        rating=d.get("rating", 4.8)
                    ))

        h_pricing = HospitalPricingSchema(**(h_dict.get("pricing") or {"status": "UNAVAILABLE"}))

        ranked_schemas.append(
            HospitalSchema(
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
                website=h_dict.get("website")
            )
        )

    # Save recommendation record to DB
    rec_id = str(uuid.uuid4())
    rec_record = RecommendationRecord(
        id=rec_id,
        symptoms=payload.symptoms,
        urgency_category=urgency,
        primary_specialty=primary_specialty,
        secondary_specialties=secondary_specialties,
        recommended_hospital_ids=[h.id for h in ranked_schemas]
    )
    try:
        db.add(rec_record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[RECOMMENDATIONS SAVE ERROR] {e}")

    return RecommendationResponseSchema(
        id=rec_id,
        urgency_category=urgency,
        urgency_summary=urgency_summary,
        clinical_summary=clinical_summary,
        primary_specialty=primary_specialty,
        secondary_specialties=secondary_specialties,
        possible_conditions=possible_conditions,
        red_flags=red_flags,
        extracted_signals=extracted_signals,
        hospitals=ranked_schemas,
        hospital_data_status="AVAILABLE" if ranked_schemas else "UNAVAILABLE",
        disclaimer="AI-generated information is for healthcare navigation and education only. It is not a medical diagnosis and should not replace evaluation by a qualified healthcare professional.",
        processed_at=datetime.utcnow().isoformat()
    )

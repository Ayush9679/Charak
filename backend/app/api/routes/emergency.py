from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.hospital import HospitalModel
from app.schemas.schemas import EmergencyRequestSchema, EmergencyResponseSchema, HospitalSchema, AvailabilitySchema, HospitalPricingSchema
from app.integrations.pricing_provider import pricing_provider

router = APIRouter()

@router.post("/emergency", response_model=EmergencyResponseSchema)
def trigger_emergency_route(
    payload: EmergencyRequestSchema,
    db: Session = Depends(get_db)
):
    nearest = db.query(HospitalModel).filter(HospitalModel.emergency_ready == True).first()

    nearest_schema = None
    if nearest:
        avail_schema = None
        if nearest.availability:
            avail_schema = AvailabilitySchema(
                beds_available=nearest.availability.beds_available,
                icu_available=nearest.availability.icu_available,
                total_beds=nearest.availability.total_beds,
                total_icu=nearest.availability.total_icu,
                last_updated=nearest.availability.last_updated.isoformat(),
                status=nearest.availability.status
            )

        h_pricing = HospitalPricingSchema(**pricing_provider.get_hospital_pricing(
            hospital_id=nearest.id,
            hfr_id=nearest.hfr_id,
            existing_min=nearest.pricing_min,
            existing_max=nearest.pricing_max,
            existing_currency=nearest.pricing_currency or "INR",
            existing_status=nearest.pricing_status or "UNAVAILABLE",
            existing_source=nearest.pricing_source,
            existing_source_url=nearest.pricing_source_url,
            existing_last_verified_at=nearest.pricing_last_verified_at
        ))

        nearest_schema = HospitalSchema(
            id=nearest.id,
            name=nearest.name,
            hfr_id=nearest.hfr_id,
            address=nearest.address,
            city=nearest.city,
            state=nearest.state,
            lat=nearest.lat,
            lng=nearest.lng,
            distance_km=3.5,
            travel_time_mins=10,
            specialties=nearest.specialties or [],
            emergency_ready=True,
            insurance_supported=nearest.insurance_supported or [],
            estimated_cost_range=None,
            pricing=h_pricing,
            data_provenance=nearest.data_provenance,
            availability=avail_schema,
            rating=nearest.rating,
            suitability=99.0
        )

    return EmergencyResponseSchema(
        status="EMERGENCY_ROUTED",
        urgency="EMERGENCY",
        nearest_hospital=nearest_schema,
        emergency_contact="102 / 108 (National Ambulance Services)",
        instructions=[
            "Call emergency services immediately if patient is unconscious or unresponsive.",
            "Do not give food or liquids if surgery or acute intervention may be required.",
            "Proceed immediately to the nearest 24/7 Emergency Department."
        ]
    )

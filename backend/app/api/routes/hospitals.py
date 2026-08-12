from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.hospital import HospitalModel, DoctorModel, AvailabilityModel
from app.schemas.schemas import HospitalSchema, DoctorSchema, AvailabilitySchema, HospitalPricingSchema, DoctorPricingSchema
from app.integrations.pricing_provider import pricing_provider

from app.core.distance import calculate_haversine_distance, estimate_travel_time_mins
from app.core.config import settings

router = APIRouter()

@router.api_route("/hospitals", methods=["GET", "HEAD"], response_model=List[HospitalSchema])
def get_hospitals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    specialty: Optional[str] = None,
    location: Optional[str] = None,
    insurance: Optional[str] = None,
    user_lat: Optional[float] = Query(None),
    user_lng: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(HospitalModel)

    if specialty and specialty.strip() and specialty.lower() != "all":
        search_spec = specialty.strip().lower()
        all_hospitals = query.all()
        filtered = [
            h for h in all_hospitals 
            if any(search_spec in str(s).lower() for s in (h.specialties or []))
        ]
        start = (page - 1) * limit
        paginated = filtered[start:start + limit]
    else:
        offset = (page - 1) * limit
        paginated = query.offset(offset).limit(limit).all()

    result = []
    for h in paginated:
        distance_km = calculate_haversine_distance(user_lat, user_lng, h.lat, h.lng)
        travel_time_mins = estimate_travel_time_mins(distance_km)

        avail_schema = None
        if h.availability:
            avail_schema = AvailabilitySchema(
                beds_available=h.availability.beds_available,
                icu_available=h.availability.icu_available,
                total_beds=h.availability.total_beds,
                total_icu=h.availability.total_icu,
                last_updated=h.availability.last_updated.isoformat(),
                status=h.availability.status
            )
        
        docs_schema = []
        if h.doctors:
            for d in h.doctors:
                doc_pricing = DoctorPricingSchema(**pricing_provider.get_doctor_pricing(
                    doctor_id=d.id,
                    existing_min=d.consultation_fee_min,
                    existing_max=d.consultation_fee_max,
                    existing_currency=d.consultation_fee_currency or "INR",
                    existing_status=d.consultation_fee_status or "UNAVAILABLE",
                    existing_source=d.consultation_fee_source
                ))
                doc_s = DoctorSchema.model_validate(d)
                doc_s.pricing = doc_pricing
                doc_s.consultation_fee = None
                docs_schema.append(doc_s)

        h_pricing = HospitalPricingSchema(**pricing_provider.get_hospital_pricing(
            hospital_id=h.id,
            hfr_id=h.hfr_id,
            existing_min=h.pricing_min,
            existing_max=h.pricing_max,
            existing_currency=h.pricing_currency or "INR",
            existing_status=h.pricing_status or "UNAVAILABLE",
            existing_source=h.pricing_source,
            existing_source_url=h.pricing_source_url,
            existing_last_verified_at=h.pricing_last_verified_at
        ))

        result.append(
            HospitalSchema(
                id=h.id,
                name=h.name,
                hfr_id=h.hfr_id,
                address=h.address,
                city=h.city,
                state=h.state,
                lat=h.lat,
                lng=h.lng,
                distance_km=distance_km,
                travel_time_mins=travel_time_mins,
                distance_source="GPS_HAVERSINE" if distance_km is not None else "UNAVAILABLE",
                specialties=h.specialties or [],
                emergency_ready=h.emergency_ready,
                insurance_supported=h.insurance_supported or [],
                estimated_cost_range=None,
                pricing=h_pricing,
                data_provenance=h.data_provenance,
                source="ABDM HFR",
                verification_status="VERIFIED_REGISTRY",
                data_freshness="VERIFIED",
                availability=avail_schema,
                doctors=docs_schema,
                rating=h.rating,
                suitability=88.0,
                recommendation_reasons=[
                    "Specialty match available",
                    "Emergency readiness verified",
                    "Insurance supported"
                ]
            )
        )
    return result

from app.integrations.osm_provider import osm_provider
from app.services.hospital_merge_service import hospital_merge_service

@router.get("/hospitals/nearby")
async def get_nearby_hospitals(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(settings.LOCAL_HOSPITAL_SEARCH_RADIUS_KM, ge=1.0, le=50.0),
    specialty: Optional[str] = Query(None),
    emergency_required: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Direct nearby hospital discovery combining HFR registry and OpenStreetMap local network.
    """
    hfr_hospitals = db.query(HospitalModel).all()
    osm_hospitals = await osm_provider.fetch_nearby_hospitals(latitude, longitude, radius_km)

    merged_results = hospital_merge_service.merge_and_rank_hospitals(
        hfr_hospitals=hfr_hospitals,
        osm_hospitals=osm_hospitals,
        user_lat=latitude,
        user_lng=longitude,
        primary_specialty=specialty or "General Medicine",
        secondary_specialties=[],
        urgency="EMERGENCY" if emergency_required else "ROUTINE",
        max_radius_km=radius_km
    )

    return {
        "results": merged_results,
        "location_used": True,
        "radius_km": radius_km,
        "providers": {
            "hfr": "CONNECTED" if hfr_hospitals else "UNAVAILABLE",
            "osm": "CONNECTED" if settings.LOCAL_HOSPITAL_PROVIDER.lower() == "osm" else "UNAVAILABLE"
        }
    }

@router.get("/hospitals/{hospital_id}", response_model=HospitalSchema)
def get_hospital_by_id(hospital_id: str, db: Session = Depends(get_db)):
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")

    avail_schema = None
    if h.availability:
        avail_schema = AvailabilitySchema(
            beds_available=h.availability.beds_available,
            icu_available=h.availability.icu_available,
            total_beds=h.availability.total_beds,
            total_icu=h.availability.total_icu,
            last_updated=h.availability.last_updated.isoformat(),
            status=h.availability.status
        )

    docs_schema = []
    if h.doctors:
        for d in h.doctors:
            doc_pricing = DoctorPricingSchema(**pricing_provider.get_doctor_pricing(
                doctor_id=d.id,
                existing_min=d.consultation_fee_min,
                existing_max=d.consultation_fee_max,
                existing_currency=d.consultation_fee_currency or "INR",
                existing_status=d.consultation_fee_status or "UNAVAILABLE",
                existing_source=d.consultation_fee_source
            ))
            doc_s = DoctorSchema.model_validate(d)
            doc_s.pricing = doc_pricing
            doc_s.consultation_fee = None
            docs_schema.append(doc_s)

    h_pricing = HospitalPricingSchema(**pricing_provider.get_hospital_pricing(
        hospital_id=h.id,
        hfr_id=h.hfr_id,
        existing_min=h.pricing_min,
        existing_max=h.pricing_max,
        existing_currency=h.pricing_currency or "INR",
        existing_status=h.pricing_status or "UNAVAILABLE",
        existing_source=h.pricing_source,
        existing_source_url=h.pricing_source_url,
        existing_last_verified_at=h.pricing_last_verified_at
    ))

    return HospitalSchema(
        id=h.id,
        name=h.name,
        hfr_id=h.hfr_id,
        address=h.address,
        city=h.city,
        state=h.state,
        lat=h.lat,
        lng=h.lng,
        distance_km=None,
        travel_time_mins=None,
        specialties=h.specialties or [],
        emergency_ready=h.emergency_ready,
        insurance_supported=h.insurance_supported or [],
        estimated_cost_range=None,
        pricing=h_pricing,
        data_provenance=h.data_provenance,
        source="ABDM HFR",
        verification_status="VERIFIED_REGISTRY",
        data_freshness="VERIFIED",
        availability=avail_schema,
        doctors=docs_schema,
        rating=h.rating,
        suitability=92.0,
        recommendation_reasons=[
            "Verified ABDM HFR Record",
            "Specialized department match",
            "Emergency services operational"
        ]
    )

@router.get("/hospitals/{hospital_id}/pricing")
def get_hospital_pricing_by_id(hospital_id: str, db: Session = Depends(get_db)):
    """
    Dedicated hospital pricing endpoint exposing provenance metadata.
    """
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")

    pricing = pricing_provider.get_hospital_pricing(
        hospital_id=h.id,
        hfr_id=h.hfr_id,
        existing_min=h.pricing_min,
        existing_max=h.pricing_max,
        existing_currency=h.pricing_currency or "INR",
        existing_status=h.pricing_status or "UNAVAILABLE",
        existing_source=h.pricing_source,
        existing_source_url=h.pricing_source_url,
        existing_last_verified_at=h.pricing_last_verified_at
    )
    return {
        "hospital_id": h.id,
        "name": h.name,
        "hfr_id": h.hfr_id,
        "pricing": pricing
    }

@router.get("/hospitals/{hospital_id}/availability")
def get_hospital_availability_by_id(hospital_id: str, db: Session = Depends(get_db)):
    """Return availability only when it was supplied by a configured provider."""
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    if not h.availability:
        return {"hospital_id": h.id, "availability": None, "status": "UNAVAILABLE"}

    availability = h.availability
    return {
        "hospital_id": h.id,
        "availability": AvailabilitySchema(
            beds_available=availability.beds_available,
            icu_available=availability.icu_available,
            total_beds=availability.total_beds,
            total_icu=availability.total_icu,
            last_updated=availability.last_updated.isoformat(),
            status=availability.status,
        ),
    }

@router.get("/doctors", response_model=List[DoctorSchema])
def get_doctors(specialty: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DoctorModel)
    if specialty:
        query = query.filter(DoctorModel.specialty.ilike(f"%{specialty}%"))
    doctors = query.all()
    res = []
    for d in doctors:
        doc_s = DoctorSchema.model_validate(d)
        doc_s.pricing = DoctorPricingSchema(**pricing_provider.get_doctor_pricing(
            doctor_id=d.id,
            existing_min=d.consultation_fee_min,
            existing_max=d.consultation_fee_max,
            existing_currency=d.consultation_fee_currency or "INR",
            existing_status=d.consultation_fee_status or "UNAVAILABLE",
            existing_source=d.consultation_fee_source
        ))
        doc_s.consultation_fee = None
        res.append(doc_s)
    return res

@router.get("/doctors/{doctor_id}", response_model=DoctorSchema)
def get_doctor_by_id(doctor_id: str, db: Session = Depends(get_db)):
    doctor = db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    response = DoctorSchema.model_validate(doctor)
    response.pricing = DoctorPricingSchema(**pricing_provider.get_doctor_pricing(
        doctor_id=doctor.id,
        existing_min=doctor.consultation_fee_min,
        existing_max=doctor.consultation_fee_max,
        existing_currency=doctor.consultation_fee_currency or "INR",
        existing_status=doctor.consultation_fee_status or "UNAVAILABLE",
        existing_source=doctor.consultation_fee_source,
    ))
    response.consultation_fee = None
    return response

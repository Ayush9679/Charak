from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

class AvailabilitySchema(BaseModel):
    beds_available: int
    icu_available: int
    total_beds: int
    total_icu: int
    last_updated: str
    status: str = "AVAILABLE"

    model_config = ConfigDict(from_attributes=True)

class HospitalPricingSchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "INR"
    status: str = "UNAVAILABLE" # VERIFIED, DEMO, UNAVAILABLE, STALE, PROVIDER_UNAVAILABLE
    source_type: str = "unavailable" # verified, demo, unavailable
    source: Optional[str] = None
    source_url: Optional[str] = None
    last_verified_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TreatmentPriceSchema(BaseModel):
    treatment: str
    min_price: float
    max_price: float
    currency: str = "INR"
    source_type: str = "demo" # verified, demo, unavailable

class DoctorPricingSchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "INR"
    status: str = "UNAVAILABLE" # VERIFIED, UNAVAILABLE
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DoctorSchema(BaseModel):
    id: str
    name: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_fee: Optional[int] = None # Legacy field - deprecated
    pricing: Optional[DoctorPricingSchema] = Field(default_factory=lambda: DoctorPricingSchema(status="UNAVAILABLE"))
    available_today: bool
    rating: float

    model_config = ConfigDict(from_attributes=True)

class HospitalSchema(BaseModel):
    id: str
    name: str
    hfr_id: str
    address: str
    city: str
    state: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    distance_km: Optional[float] = None
    travel_time_mins: Optional[int] = None
    distance_source: Optional[str] = "UNAVAILABLE"
    specialties: List[str]
    emergency_ready: bool
    insurance_supported: List[str]
    estimated_cost_range: Optional[str] = None # Legacy field - deprecated
    pricing: Optional[HospitalPricingSchema] = Field(default_factory=lambda: HospitalPricingSchema(status="UNAVAILABLE"))
    treatment_pricing: List[TreatmentPriceSchema] = Field(default_factory=list)
    data_provenance: str
    source: Optional[str] = "ABDM HFR"
    verification_status: Optional[str] = "VERIFIED_REGISTRY"
    data_freshness: Optional[str] = "VERIFIED"
    availability: Optional[AvailabilitySchema] = None
    doctors: Optional[List[DoctorSchema]] = None
    rating: Optional[float] = 4.5
    suitability: Optional[float] = None
    recommendation_reasons: Optional[List[str]] = Field(default_factory=list)
    phone: Optional[str] = None
    website: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SymptomInputSchema(BaseModel):
    symptoms: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance: Optional[float] = 15.0
    insurance: Optional[str] = "Ayushman Bharat"
    budget_level: Optional[str] = "Moderate"
    report_file: Optional[str] = None

class PossibleConditionSchema(BaseModel):
    name: str
    relevance: str = "Possible"
    explanation: str
    supporting_symptoms: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence_label: str = "Possible"

    model_config = ConfigDict(from_attributes=True)

class RecommendationResponseSchema(BaseModel):
    id: str
    urgency_category: str # ROUTINE, MODERATE, URGENT, EMERGENCY
    urgency_summary: str
    clinical_summary: Optional[str] = None
    primary_specialty: str
    secondary_specialties: List[str]
    possible_conditions: List[PossibleConditionSchema] = Field(default_factory=list)
    red_flags: List[str]
    extracted_signals: List[str]
    hospitals: List[HospitalSchema]
    hospital_data_status: str = "AVAILABLE"
    disclaimer: str = "AI-generated information is for healthcare navigation and education only. It is not a medical diagnosis and should not replace evaluation by a qualified healthcare professional."
    processed_at: str

class ChatRequestSchema(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SuggestedActionSchema(BaseModel):
    type: str # NAVIGATE_SPECIALTY, EMERGENCY_ALERT, FIND_HOSPITALS, FIND_EMERGENCY_HOSPITALS
    label: str
    specialty: Optional[str] = None
    route: Optional[str] = None
    emergency_required: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None

class ChatResponseSchema(BaseModel):
    conversation_id: str
    response: str
    urgency: str = "ROUTINE"
    specialties: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    suggested_action: Optional[SuggestedActionSchema] = None
    analysis_id: Optional[str] = None
    intent_type: Optional[str] = None
    hospitals: Optional[List[HospitalSchema]] = None
    extraction: Optional[Dict[str, Any]] = None


class MedicationExtractionSchema(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    confidence: str = "LOW"
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PrescriptionExtractionSchema(BaseModel):
    document_type: str = "UNKNOWN"
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    date: Optional[str] = None
    medications: List[MedicationExtractionSchema] = Field(default_factory=list)
    diagnoses_or_conditions: List[str] = Field(default_factory=list)
    lab_tests: List[str] = Field(default_factory=list)
    follow_up: Optional[str] = None
    uncertain_fields: List[str] = Field(default_factory=list)
    confidence_notes: List[str] = Field(default_factory=list)
    extraction_method: str = "VISION"
    safety_notice: str = (
        "This extraction is for informational purposes only. "
        "CHANAKYA does not provide medical advice."
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentChatResponseSchema(ChatResponseSchema):
    document_type: Optional[str] = None
    prescription_extraction: Optional[PrescriptionExtractionSchema] = None

class EmergencyRequestSchema(BaseModel):
    location: str
    symptoms: str
    contact_number: Optional[str] = None

class EmergencyResponseSchema(BaseModel):
    status: str
    urgency: str = "EMERGENCY"
    nearest_hospital: Optional[HospitalSchema] = None
    emergency_contact: str = "102 / 108"
    instructions: List[str]

class AppointmentRequestSchema(BaseModel):
    hospital_id: str
    doctor_id: str
    patient_name: str
    patient_phone: str
    preferred_date: str
    preferred_slot: str

class AppointmentResponseSchema(BaseModel):
    appointment_id: str
    status: str = "REQUEST_RECEIVED"
    hospital_name: str
    doctor_name: str
    date: str
    slot: str
    message: str

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class HospitalModel(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, default=generate_uuid)
    hfr_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, index=True, nullable=False)
    state = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    specialties = Column(JSON, nullable=False) # List of strings e.g. ["Cardiology", "Emergency Medicine"]
    emergency_ready = Column(Boolean, default=True)
    insurance_supported = Column(JSON, nullable=False) # List of strings e.g. ["Ayushman Bharat", "CGHS"]
    estimated_cost_range = Column(String, nullable=True) # Legacy field - deprecated in favor of structured pricing
    pricing_min = Column(Float, nullable=True)
    pricing_max = Column(Float, nullable=True)
    pricing_currency = Column(String, default="INR")
    pricing_status = Column(String, default="UNAVAILABLE") # VERIFIED, UNAVAILABLE, STALE, PROVIDER_UNAVAILABLE
    pricing_source = Column(String, nullable=True)
    pricing_source_url = Column(String, nullable=True)
    pricing_last_verified_at = Column(DateTime, nullable=True)
    data_provenance = Column(String, nullable=False) # PUBLIC_REGISTRY, PUBLISHED_AGGREGATED, HOSPITAL_INTEGRATION
    rating = Column(Float, default=4.5)

    availability = relationship("AvailabilityModel", back_populates="hospital", uselist=False, cascade="all, delete-orphan")
    doctors = relationship("DoctorModel", back_populates="hospital", cascade="all, delete-orphan")

class AvailabilityModel(Base):
    __tablename__ = "availabilities"

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), unique=True, nullable=False)
    beds_available = Column(Integer, default=0)
    icu_available = Column(Integer, default=0)
    total_beds = Column(Integer, default=100)
    total_icu = Column(Integer, default=20)
    last_updated = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="AVAILABLE") # AVAILABLE, UNAVAILABLE

    hospital = relationship("HospitalModel", back_populates="availability")

class DoctorModel(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String, nullable=False)
    specialty = Column(String, index=True, nullable=False)
    qualification = Column(String, nullable=False)
    experience_years = Column(Integer, default=5)
    consultation_fee = Column(Integer, nullable=True) # Legacy field - deprecated
    consultation_fee_min = Column(Float, nullable=True)
    consultation_fee_max = Column(Float, nullable=True)
    consultation_fee_currency = Column(String, default="INR")
    consultation_fee_status = Column(String, default="UNAVAILABLE") # VERIFIED, UNAVAILABLE
    consultation_fee_source = Column(String, nullable=True)
    available_today = Column(Boolean, default=True)
    rating = Column(Float, default=4.8)

    hospital = relationship("HospitalModel", back_populates="doctors")

class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    symptoms = Column(Text, nullable=False)
    urgency_category = Column(String, nullable=False)
    primary_specialty = Column(String, nullable=False)
    secondary_specialties = Column(JSON, nullable=False)
    recommended_hospital_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, index=True, nullable=False)
    sender = Column(String, nullable=False) # user, currado
    message = Column(Text, nullable=False)
    urgency = Column(String, nullable=True)
    specialties = Column(JSON, nullable=True)
    analysis_context = Column(Text, nullable=True)  # JSON string with analysis_id, specialty, urgency
    intent_type = Column(String, nullable=True)      # SYMPTOM_REPORT, EMERGENCY_SYMPTOM, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


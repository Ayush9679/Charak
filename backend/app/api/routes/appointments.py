from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.db.database import get_db
from app.models.hospital import HospitalModel, DoctorModel
from app.schemas.schemas import AppointmentRequestSchema, AppointmentResponseSchema

router = APIRouter()

@router.post("/appointments", response_model=AppointmentResponseSchema)
def book_appointment(
    payload: AppointmentRequestSchema,
    db: Session = Depends(get_db)
):
    hospital = db.query(HospitalModel).filter(HospitalModel.id == payload.hospital_id).first()
    doctor = db.query(DoctorModel).filter(DoctorModel.id == payload.doctor_id).first()

    h_name = hospital.name if hospital else "Selected Hospital"
    d_name = doctor.name if doctor else "Specialist Doctor"

    app_id = f"APP-{str(uuid.uuid4())[:8].upper()}"

    return AppointmentResponseSchema(
        appointment_id=app_id,
        status="REQUEST_RECEIVED",
        hospital_name=h_name,
        doctor_name=d_name,
        date=payload.preferred_date,
        slot=payload.preferred_slot,
        message=(
            f"Appointment request received for {payload.patient_name} with {d_name} at {h_name}. "
            "A confirmed booking requires a participating hospital appointment integration."
        )
    )


@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: str):
    """Explicitly report that no persistent booking provider is configured."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Appointment lookup requires a configured hospital booking integration.",
    )


@router.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: str):
    """Do not claim cancellation without an upstream booking integration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Appointment cancellation requires a configured hospital booking integration.",
    )

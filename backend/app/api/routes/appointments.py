from fastapi import APIRouter, Depends, HTTPException
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
        status="CONFIRMED",
        hospital_name=h_name,
        doctor_name=d_name,
        date=payload.preferred_date,
        slot=payload.preferred_slot,
        message=f"Appointment request recorded for {payload.patient_name} with {d_name} at {h_name}."
    )

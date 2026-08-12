"""Operational-only endpoints protected by a server-side token."""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.hospital import AvailabilityModel, DoctorModel, HospitalModel

router = APIRouter()


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoint is not configured.",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.get("/admin/data-summary", dependencies=[Depends(require_admin_token)])
def data_summary(db: Session = Depends(get_db)):
    """Return aggregate operational counts without exposing patient data or secrets."""
    return {
        "hospitals": db.query(HospitalModel).count(),
        "doctors": db.query(DoctorModel).count(),
        "availability_records": db.query(AvailabilityModel).count(),
        "hospital_provider": settings.LOCAL_HOSPITAL_PROVIDER,
    }

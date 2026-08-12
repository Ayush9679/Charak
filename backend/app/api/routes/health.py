from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.db.database import get_db
from app.ai.groq_client import groq_client

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    groq_status = "configured" if groq_client.is_configured() else "unconfigured"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "service": "CHANAKYA Backend API",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "groq": groq_status,
        "providers": {
            "hospital_data": "available",
            "doctor_data": "available",
            "availability_data": "available"
        }
    }

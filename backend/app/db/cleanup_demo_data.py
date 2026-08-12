import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import engine, SessionLocal
from app.models.hospital import HospitalModel, AvailabilityModel, DoctorModel

DEMO_HOSPITAL_IDS = [
    "meridian-heart",
    "civic-general",
    "northstar-cardiac",
    "asha-multispecialty"
]

def cleanup_demo_data():
    db = SessionLocal()
    try:
        print("[CLEANUP] Checking database for legacy demo records...")
        deleted_count = 0
        for demo_id in DEMO_HOSPITAL_IDS:
            h = db.query(HospitalModel).filter(
                (HospitalModel.id == demo_id) | (HospitalModel.hfr_id == demo_id)
            ).first()
            if h:
                # Delete related availability & doctors
                db.query(AvailabilityModel).filter(AvailabilityModel.hospital_id == h.id).delete()
                db.query(DoctorModel).filter(DoctorModel.hospital_id == h.id).delete()
                db.delete(h)
                deleted_count += 1

        db.commit()
        print(f"[CLEANUP] Done. Removed {deleted_count} demo hospital records.")
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_demo_data()

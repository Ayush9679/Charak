import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import Base, engine, SessionLocal
from app.models.hospital import HospitalModel, AvailabilityModel, DoctorModel
from datetime import datetime

INITIAL_HOSPITALS = [
  {
    "hfr_id": "IN-UP-HFR-10492",
    "name": "Fortis Hospital Noida",
    "address": "B-22, Sector 62, Noida, Uttar Pradesh 201301",
    "city": "Noida",
    "state": "Uttar Pradesh",
    "lat": 28.6219,
    "lng": 77.3639,
    "specialties": ["Cardiology", "Emergency Medicine", "Neurology", "Orthopedics", "Oncology"],
    "emergency_ready": True,
    "insurance_supported": ["Ayushman Bharat", "CGHS", "Star Health", "Max Bupa", "HDFC ERGO"],
    "data_provenance": "HOSPITAL_INTEGRATION",
    "rating": 4.8,
    "beds_available": 18,
    "icu_available": 5,
    "total_beds": 200,
    "total_icu": 30,
    "doctors": [
      {
        "name": "Dr. Sanjeev Gera",
        "specialty": "Cardiology",
        "qualification": "MD, DM (Cardiology), FACC",
        "experience_years": 22,
        "available_today": True,
        "rating": 4.9
      },
      {
        "name": "Dr. Rahul Gupta",
        "specialty": "Neurology",
        "qualification": "MD, DM (Neurology)",
        "experience_years": 16,
        "available_today": True,
        "rating": 4.8
      }
    ]
  },
  {
    "hfr_id": "IN-UP-HFR-20831",
    "name": "Jaypee Hospital Noida",
    "address": "Sector 128, Noida, Uttar Pradesh 201304",
    "city": "Noida",
    "state": "Uttar Pradesh",
    "lat": 28.5173,
    "lng": 77.3694,
    "specialties": ["Cardiology", "Gastroenterology", "Pulmonology", "Orthopedics", "Emergency Medicine"],
    "emergency_ready": True,
    "insurance_supported": ["Ayushman Bharat", "CGHS", "Reliance General", "Star Health"],
    "data_provenance": "PUBLISHED_AGGREGATED",
    "rating": 4.7,
    "beds_available": 32,
    "icu_available": 8,
    "total_beds": 500,
    "total_icu": 60,
    "doctors": [
      {
        "name": "Dr. Rajesh Sharma",
        "specialty": "Cardiology",
        "qualification": "MD, DM",
        "experience_years": 18,
        "available_today": True,
        "rating": 4.7
      },
      {
        "name": "Dr. Meena Agarwal",
        "specialty": "Gastroenterology",
        "qualification": "MD, DNB (Gastroenterology)",
        "experience_years": 14,
        "available_today": True,
        "rating": 4.6
      }
    ]
  },
  {
    "hfr_id": "IN-UP-HFR-30114",
    "name": "Kailash Hospital & Heart Institute",
    "address": "H-33, Sector 27, Noida, Uttar Pradesh 201301",
    "city": "Noida",
    "state": "Uttar Pradesh",
    "lat": 28.5744,
    "lng": 77.3276,
    "specialties": ["Cardiology", "Emergency Medicine", "General Surgery", "Pediatrics", "Obstetrics"],
    "emergency_ready": True,
    "insurance_supported": ["Ayushman Bharat", "CGHS", "EHS", "Max Bupa"],
    "data_provenance": "PUBLIC_REGISTRY",
    "rating": 4.6,
    "beds_available": 12,
    "icu_available": 3,
    "total_beds": 150,
    "total_icu": 25,
    "doctors": [
      {
        "name": "Dr. R.K. Bhan",
        "specialty": "Cardiology",
        "qualification": "MD, FACC",
        "experience_years": 25,
        "available_today": True,
        "rating": 4.8
      }
    ]
  },
  {
    "hfr_id": "IN-UP-HFR-40992",
    "name": "Metro Hospital & Heart Institute",
    "address": "X-1, Sector 12, Noida, Uttar Pradesh 201301",
    "city": "Noida",
    "state": "Uttar Pradesh",
    "lat": 28.5912,
    "lng": 77.3385,
    "specialties": ["Cardiology", "Pulmonology", "Emergency Medicine", "Nephrology"],
    "emergency_ready": True,
    "insurance_supported": ["Ayushman Bharat", "Star Health", "ICICI Lombard"],
    "data_provenance": "PUBLISHED_AGGREGATED",
    "rating": 4.5,
    "beds_available": 20,
    "icu_available": 4,
    "total_beds": 180,
    "total_icu": 20,
    "doctors": [
      {
        "name": "Dr. Purshotam Lal",
        "specialty": "Cardiology",
        "qualification": "MD, FRCP, FACC",
        "experience_years": 30,
        "available_today": True,
        "rating": 4.9
      }
    ]
  },
  {
    "hfr_id": "IN-UP-HFR-50221",
    "name": "Yatharth Super Speciality Hospital",
    "address": "Omega 1, Greater Noida, Uttar Pradesh 201308",
    "city": "Greater Noida",
    "state": "Uttar Pradesh",
    "lat": 28.4721,
    "lng": 77.5132,
    "specialties": ["Orthopedics", "Neurology", "Cardiology", "Emergency Medicine", "Urology"],
    "emergency_ready": True,
    "insurance_supported": ["Ayushman Bharat", "CGHS", "Care Health", "Star Health"],
    "data_provenance": "HOSPITAL_INTEGRATION",
    "rating": 4.6,
    "beds_available": 45,
    "icu_available": 10,
    "total_beds": 400,
    "total_icu": 50,
    "doctors": [
      {
        "name": "Dr. Amit Kumar",
        "specialty": "Orthopedics",
        "qualification": "MS (Orthopedics)",
        "experience_years": 15,
        "available_today": True,
        "rating": 4.7
      }
    ]
  }
]

def import_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("[HFR IMPORTER] Seeding HFR hospital records into database...")
        for data in INITIAL_HOSPITALS:
            existing = db.query(HospitalModel).filter(HospitalModel.hfr_id == data["hfr_id"]).first()
            if existing:
                # Clean up existing record pricing fields if unverified
                existing.estimated_cost_range = None
                existing.pricing_min = None
                existing.pricing_max = None
                existing.pricing_status = "UNAVAILABLE"
                existing.pricing_source = None
                continue

            h = HospitalModel(
                hfr_id=data["hfr_id"],
                name=data["name"],
                address=data["address"],
                city=data["city"],
                state=data["state"],
                lat=data["lat"],
                lng=data["lng"],
                specialties=data["specialties"],
                emergency_ready=data["emergency_ready"],
                insurance_supported=data["insurance_supported"],
                estimated_cost_range=None,
                pricing_min=None,
                pricing_max=None,
                pricing_currency="INR",
                pricing_status="UNAVAILABLE",
                pricing_source=None,
                data_provenance=data["data_provenance"],
                rating=data["rating"]
            )
            db.add(h)
            db.flush()

            avail = AvailabilityModel(
                hospital_id=h.id,
                beds_available=data["beds_available"],
                icu_available=data["icu_available"],
                total_beds=data["total_beds"],
                total_icu=data["total_icu"],
                last_updated=datetime.utcnow(),
                status="AVAILABLE"
            )
            db.add(avail)

            for doc_data in data["doctors"]:
                doc = DoctorModel(
                    hospital_id=h.id,
                    name=doc_data["name"],
                    specialty=doc_data["specialty"],
                    qualification=doc_data["qualification"],
                    experience_years=doc_data["experience_years"],
                    consultation_fee=None,
                    consultation_fee_min=None,
                    consultation_fee_max=None,
                    consultation_fee_currency="INR",
                    consultation_fee_status="UNAVAILABLE",
                    consultation_fee_source=None,
                    available_today=doc_data["available_today"],
                    rating=doc_data["rating"]
                )
                db.add(doc)

        # Migration cleanup: Set all legacy estimated_cost_range / consultation_fee values to UNAVAILABLE
        db.query(HospitalModel).update({
            HospitalModel.estimated_cost_range: "Pricing unavailable from verified source",
            HospitalModel.pricing_min: None,
            HospitalModel.pricing_max: None,
            HospitalModel.pricing_status: "UNAVAILABLE",
            HospitalModel.pricing_source: None
        })
        db.query(DoctorModel).update({
            DoctorModel.consultation_fee: None,
            DoctorModel.consultation_fee_min: None,
            DoctorModel.consultation_fee_max: None,
            DoctorModel.consultation_fee_status: "UNAVAILABLE",
            DoctorModel.consultation_fee_source: None
        })

        db.commit()
        print("[HFR IMPORTER] Successfully seeded and migrated DB pricing records to honest UNAVAILABLE status!")
    except Exception as e:
        db.rollback()
        print(f"[HFR IMPORTER ERROR] Failed to seed database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_data()

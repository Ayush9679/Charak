import sqlite3
import os
import json


def migrate_sqlite_db(db_path: str = "chanakya.db"):
    if not os.path.exists(db_path):
        print(f"[DB MIGRATION] Database file {db_path} does not exist yet.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # -----------------------------------------------------------------------
    # 1. Add new columns to hospitals table (idempotent)
    # -----------------------------------------------------------------------
    cursor.execute("PRAGMA table_info(hospitals)")
    hospital_cols = [col[1] for col in cursor.fetchall()]

    h_new_cols = [
        ("pricing_min",              "REAL"),
        ("pricing_max",              "REAL"),
        ("pricing_currency",         "TEXT DEFAULT 'INR'"),
        ("pricing_status",           "TEXT DEFAULT 'UNAVAILABLE'"),
        ("pricing_source",           "TEXT"),
        ("pricing_source_url",       "TEXT"),
        ("pricing_last_verified_at", "TIMESTAMP"),
        ("treatment_pricing",        "JSON"),
        ("suitability_score",        "REAL"),
    ]

    for col_name, col_type in h_new_cols:
        if col_name not in hospital_cols:
            try:
                cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}")
                print(f"[DB MIGRATION] Added '{col_name}' to hospitals table.")
            except Exception as e:
                print(f"[DB MIGRATION NOTICE] {e}")

    # -----------------------------------------------------------------------
    # 2. Add new columns to doctors table (idempotent)
    # -----------------------------------------------------------------------
    cursor.execute("PRAGMA table_info(doctors)")
    doctor_cols = [col[1] for col in cursor.fetchall()]

    d_new_cols = [
        ("consultation_fee_min",      "REAL"),
        ("consultation_fee_max",      "REAL"),
        ("consultation_fee_currency", "TEXT DEFAULT 'INR'"),
        ("consultation_fee_status",   "TEXT DEFAULT 'UNAVAILABLE'"),
        ("consultation_fee_source",   "TEXT"),
    ]

    for col_name, col_type in d_new_cols:
        if col_name not in doctor_cols:
            try:
                cursor.execute(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_type}")
                print(f"[DB MIGRATION] Added '{col_name}' to doctors table.")
            except Exception as e:
                print(f"[DB MIGRATION NOTICE] {e}")

    # -----------------------------------------------------------------------
    # 3. Deterministic DEMO pricing seed for all demo hospitals.
    #
    #    Rules (idempotent):
    #      - NEVER overwrite a hospital whose existing treatment_pricing
    #        contains ANY item with source_type = 'verified'.
    #      - If treatment_pricing is NULL or all items are 'demo',
    #        replace with the canonical DEMO dataset below.
    #      - suitability_score is only set when the column is NULL
    #        (first-time) or was previously unset — it is idempotent.
    #
    #    These values are DEMO / INDICATIVE ONLY.
    #    source_type = "demo" is set throughout.
    #    They must NOT be presented as actual hospital tariffs.
    # -----------------------------------------------------------------------

    DEMO_HOSPITALS = [
        # ---------------------------------------------------------------
        # Yatharth Super Speciality Hospital — IN-UP-HFR-50221
        # Specialties: General Medicine, Orthopedics, Neurology,
        #              Cardiology, Urology, Emergency Medicine
        # Canonical suitability_score: 82 (single DB source of truth)
        # ---------------------------------------------------------------
        {
            "hfr_id": "IN-UP-HFR-50221",
            "suitability_score": 82.0,
            "total_beds": 350,
            "total_icu": 40,
            "treatment_pricing": [
                # General Medicine
                {"treatment": "General Consultation",   "min_price": 500,    "max_price": 1000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Follow-up Consultation", "min_price": 300,    "max_price": 700,    "currency": "INR", "source_type": "demo"},
                # Orthopedics
                {"treatment": "Orthopedic Consultation","min_price": 800,    "max_price": 1500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "X-Ray",                  "min_price": 300,    "max_price": 800,    "currency": "INR", "source_type": "demo"},
                {"treatment": "MRI Scan",               "min_price": 4000,   "max_price": 7000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "CT Scan",                "min_price": 2500,   "max_price": 5000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Knee Replacement",       "min_price": 120000, "max_price": 200000, "currency": "INR", "source_type": "demo"},
                {"treatment": "Hip Replacement",        "min_price": 150000, "max_price": 250000, "currency": "INR", "source_type": "demo"},
                {"treatment": "Fracture Surgery",       "min_price": 50000,  "max_price": 120000, "currency": "INR", "source_type": "demo"},
                # Neurology
                {"treatment": "Neurology Consultation", "min_price": 1000,   "max_price": 2000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "EEG",                    "min_price": 1500,   "max_price": 3000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Brain MRI",              "min_price": 4000,   "max_price": 8000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Stroke Evaluation",      "min_price": 5000,   "max_price": 15000,  "currency": "INR", "source_type": "demo"},
                # Cardiology
                {"treatment": "Cardiology Consultation","min_price": 1000,   "max_price": 2000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "ECG",                    "min_price": 300,    "max_price": 700,    "currency": "INR", "source_type": "demo"},
                {"treatment": "Echocardiogram",         "min_price": 1500,   "max_price": 3500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "TMT",                    "min_price": 1500,   "max_price": 3000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Coronary Angiography",   "min_price": 15000,  "max_price": 30000,  "currency": "INR", "source_type": "demo"},
                {"treatment": "Angioplasty",            "min_price": 150000, "max_price": 300000, "currency": "INR", "source_type": "demo"},
                # Urology
                {"treatment": "Urology Consultation",   "min_price": 800,    "max_price": 1500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Ultrasound KUB",         "min_price": 1000,   "max_price": 2000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Kidney Stone Treatment", "min_price": 40000,  "max_price": 90000,  "currency": "INR", "source_type": "demo"},
                {"treatment": "Lithotripsy",            "min_price": 30000,  "max_price": 70000,  "currency": "INR", "source_type": "demo"},
                # Emergency Medicine
                {"treatment": "Emergency Consultation", "min_price": 1000,   "max_price": 2500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Emergency Observation",  "min_price": 2000,   "max_price": 5000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Critical Care / ICU per day", "min_price": 5000, "max_price": 15000, "currency": "INR", "source_type": "demo"},
            ],
        },

        # ---------------------------------------------------------------
        # Fortis Hospital Noida — IN-UP-HFR-10492
        # Specialties: Cardiology, Orthopedics, Emergency Medicine
        # Canonical suitability_score: 88
        # ---------------------------------------------------------------
        {
            "hfr_id": "IN-UP-HFR-10492",
            "suitability_score": 88.0,
            "total_beds": None,
            "total_icu": None,
            "treatment_pricing": [
                # Cardiology
                {"treatment": "Cardiology Consultation","min_price": 1200,   "max_price": 2500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "ECG",                    "min_price": 400,    "max_price": 800,    "currency": "INR", "source_type": "demo"},
                {"treatment": "Echocardiogram",         "min_price": 2000,   "max_price": 4000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "TMT",                    "min_price": 1800,   "max_price": 3500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Coronary Angiography",   "min_price": 18000,  "max_price": 35000,  "currency": "INR", "source_type": "demo"},
                {"treatment": "Angioplasty",            "min_price": 175000, "max_price": 350000, "currency": "INR", "source_type": "demo"},
                # Orthopedics
                {"treatment": "Orthopedic Consultation","min_price": 1000,   "max_price": 1800,   "currency": "INR", "source_type": "demo"},
                {"treatment": "MRI Scan",               "min_price": 4500,   "max_price": 8000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Knee Replacement",       "min_price": 140000, "max_price": 240000, "currency": "INR", "source_type": "demo"},
                # Emergency Medicine
                {"treatment": "Emergency Consultation", "min_price": 1500,   "max_price": 3000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Critical Care / ICU per day", "min_price": 6000, "max_price": 18000, "currency": "INR", "source_type": "demo"},
            ],
        },

        # ---------------------------------------------------------------
        # Jaypee Hospital Noida — IN-UP-HFR-20831
        # Specialties: Orthopedics, General Medicine, Neurology
        # Canonical suitability_score: 85
        # ---------------------------------------------------------------
        {
            "hfr_id": "IN-UP-HFR-20831",
            "suitability_score": 85.0,
            "total_beds": None,
            "total_icu": None,
            "treatment_pricing": [
                # Orthopedics
                {"treatment": "Orthopedic Consultation","min_price": 900,    "max_price": 1600,   "currency": "INR", "source_type": "demo"},
                {"treatment": "X-Ray",                  "min_price": 300,    "max_price": 700,    "currency": "INR", "source_type": "demo"},
                {"treatment": "MRI Scan",               "min_price": 4000,   "max_price": 7500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "CT Scan",                "min_price": 2800,   "max_price": 5500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Knee Replacement",       "min_price": 130000, "max_price": 220000, "currency": "INR", "source_type": "demo"},
                {"treatment": "Hip Replacement",        "min_price": 160000, "max_price": 260000, "currency": "INR", "source_type": "demo"},
                {"treatment": "Fracture Surgery",       "min_price": 55000,  "max_price": 130000, "currency": "INR", "source_type": "demo"},
                # General Medicine
                {"treatment": "General Consultation",   "min_price": 600,    "max_price": 1200,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Follow-up Consultation", "min_price": 400,    "max_price": 800,    "currency": "INR", "source_type": "demo"},
                # Neurology
                {"treatment": "Neurology Consultation", "min_price": 1100,   "max_price": 2200,   "currency": "INR", "source_type": "demo"},
                {"treatment": "EEG",                    "min_price": 1600,   "max_price": 3200,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Brain MRI",              "min_price": 4500,   "max_price": 8500,   "currency": "INR", "source_type": "demo"},
            ],
        },

        # ---------------------------------------------------------------
        # Kailash Hospital & Heart Institute — IN-UP-HFR-30114
        # Specialties: Cardiology, Emergency Medicine
        # Canonical suitability_score: 83
        # ---------------------------------------------------------------
        {
            "hfr_id": "IN-UP-HFR-30114",
            "suitability_score": 83.0,
            "total_beds": None,
            "total_icu": None,
            "treatment_pricing": [
                # Cardiology
                {"treatment": "Cardiology Consultation","min_price": 1000,   "max_price": 2000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "ECG",                    "min_price": 350,    "max_price": 700,    "currency": "INR", "source_type": "demo"},
                {"treatment": "Echocardiogram",         "min_price": 1800,   "max_price": 3500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "TMT",                    "min_price": 1600,   "max_price": 3000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Coronary Angiography",   "min_price": 16000,  "max_price": 30000,  "currency": "INR", "source_type": "demo"},
                {"treatment": "Angioplasty",            "min_price": 160000, "max_price": 310000, "currency": "INR", "source_type": "demo"},
                # Emergency Medicine
                {"treatment": "Emergency Consultation", "min_price": 1000,   "max_price": 2500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Emergency Observation",  "min_price": 2000,   "max_price": 5000,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Critical Care / ICU per day", "min_price": 5500, "max_price": 16000, "currency": "INR", "source_type": "demo"},
            ],
        },

        # ---------------------------------------------------------------
        # Metro Hospital & Heart Institute — IN-UP-HFR-40992
        # Specialties: Cardiology, Emergency Medicine, General Medicine
        # Canonical suitability_score: 80
        # ---------------------------------------------------------------
        {
            "hfr_id": "IN-UP-HFR-40992",
            "suitability_score": 80.0,
            "total_beds": None,
            "total_icu": None,
            "treatment_pricing": [
                # Cardiology
                {"treatment": "Cardiology Consultation","min_price": 900,    "max_price": 1800,   "currency": "INR", "source_type": "demo"},
                {"treatment": "ECG",                    "min_price": 300,    "max_price": 650,    "currency": "INR", "source_type": "demo"},
                {"treatment": "Echocardiogram",         "min_price": 1500,   "max_price": 3200,   "currency": "INR", "source_type": "demo"},
                {"treatment": "TMT",                    "min_price": 1400,   "max_price": 2800,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Coronary Angiography",   "min_price": 14000,  "max_price": 28000,  "currency": "INR", "source_type": "demo"},
                {"treatment": "Angioplasty",            "min_price": 145000, "max_price": 290000, "currency": "INR", "source_type": "demo"},
                # Emergency Medicine
                {"treatment": "Emergency Consultation", "min_price": 1000,   "max_price": 2500,   "currency": "INR", "source_type": "demo"},
                {"treatment": "Critical Care / ICU per day", "min_price": 5000, "max_price": 14000, "currency": "INR", "source_type": "demo"},
                # General Medicine
                {"treatment": "General Consultation",   "min_price": 500,    "max_price": 1100,   "currency": "INR", "source_type": "demo"},
            ],
        },
    ]

    for hospital_data in DEMO_HOSPITALS:
        hfr_id = hospital_data["hfr_id"]
        suitability = hospital_data["suitability_score"]
        new_pricing = hospital_data["treatment_pricing"]
        total_beds = hospital_data["total_beds"]
        total_icu = hospital_data["total_icu"]

        # Fetch current hospital row
        cursor.execute(
            "SELECT id, treatment_pricing, suitability_score FROM hospitals WHERE hfr_id = ?",
            (hfr_id,)
        )
        row = cursor.fetchone()
        if not row:
            print(f"[DB MIGRATION] Hospital {hfr_id} not found — skipping.")
            continue

        hospital_id, existing_tp_raw, existing_suitability = row

        # Check whether existing treatment_pricing contains verified data
        # If it does, NEVER overwrite it.
        skip_pricing = False
        if existing_tp_raw:
            try:
                existing_tp = json.loads(existing_tp_raw) if isinstance(existing_tp_raw, str) else existing_tp_raw
                if isinstance(existing_tp, list):
                    has_verified = any(
                        isinstance(item, dict) and item.get("source_type") == "verified"
                        for item in existing_tp
                    )
                    if has_verified:
                        skip_pricing = True
                        print(f"[DB MIGRATION] {hfr_id}: skipping treatment_pricing update — VERIFIED data present.")
            except (json.JSONDecodeError, TypeError):
                pass  # malformed existing data — treat as absent

        if not skip_pricing:
            new_tp_json = json.dumps(new_pricing)
            cursor.execute(
                "UPDATE hospitals SET treatment_pricing = ? WHERE hfr_id = ?",
                (new_tp_json, hfr_id)
            )
            if cursor.rowcount:
                print(f"[DB MIGRATION] Seeded {len(new_pricing)} DEMO treatment prices for {hfr_id}.")

        # suitability_score: set unconditionally (it's a canonical demo value we own)
        cursor.execute(
            "UPDATE hospitals SET suitability_score = ? WHERE hfr_id = ? AND (suitability_score IS NULL OR suitability_score != ?)",
            (suitability, hfr_id, suitability)
        )
        if cursor.rowcount:
            print(f"[DB MIGRATION] Set suitability_score={suitability} for {hfr_id}.")

        # Correct bed/ICU capacity to canonical demo values (Yatharth only)
        if total_beds is not None:
            cursor.execute(
                """UPDATE availabilities
                   SET total_beds = ?,
                       total_icu  = ?
                   WHERE hospital_id = ?""",
                (total_beds, total_icu, hospital_id)
            )
            if cursor.rowcount:
                print(f"[DB MIGRATION] Set total_beds={total_beds}, total_icu={total_icu} for {hfr_id}.")

    conn.commit()
    conn.close()
    print("[DB MIGRATION COMPLETE] Schema ready. Canonical demo data applied.")


if __name__ == "__main__":
    migrate_sqlite_db()

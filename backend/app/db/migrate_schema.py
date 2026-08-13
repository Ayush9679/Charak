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
    # 3. Seed canonical demo data for Yatharth Super Speciality Hospital
    #    (HFR ID: IN-UP-HFR-50221)
    #
    #    DEMO / INDICATIVE values only.
    #    source_type="demo" — clearly labelled throughout.
    #    Replace with source_type="verified" when authoritative data arrives.
    #
    #    Canonical values:
    #      suitability_score = 82   ← single source of truth for BOTH
    #                                  recommendation card AND detail page
    #      total_beds        = 350
    #      total_icu         = 40
    # -----------------------------------------------------------------------
    yatharth_treatment_pricing = json.dumps([
        {"treatment": "General Consultation",    "min_price": 500,    "max_price": 1000,   "currency": "INR", "source_type": "demo"},
        {"treatment": "Orthopedic Consultation", "min_price": 800,    "max_price": 1500,   "currency": "INR", "source_type": "demo"},
        {"treatment": "MRI Scan",                "min_price": 4000,   "max_price": 7000,   "currency": "INR", "source_type": "demo"},
        {"treatment": "CT Scan",                 "min_price": 2500,   "max_price": 5000,   "currency": "INR", "source_type": "demo"},
        {"treatment": "Knee Replacement",        "min_price": 120000, "max_price": 200000, "currency": "INR", "source_type": "demo"},
        {"treatment": "Cataract Surgery",        "min_price": 25000,  "max_price": 50000,  "currency": "INR", "source_type": "demo"},
    ])

    cursor.execute(
        """UPDATE hospitals
           SET suitability_score = 82,
               treatment_pricing = ?
           WHERE hfr_id = 'IN-UP-HFR-50221'""",
        (yatharth_treatment_pricing,),
    )
    if cursor.rowcount:
        print("[DB MIGRATION] Seeded suitability_score=82 and demo treatment_pricing for Yatharth (IN-UP-HFR-50221).")
    else:
        print("[DB MIGRATION] Yatharth (IN-UP-HFR-50221) not found — no hospital row updated.")

    # Correct bed/ICU capacity to canonical demo values
    cursor.execute(
        """UPDATE availabilities
           SET total_beds = 350,
               total_icu  = 40
           WHERE hospital_id = (
               SELECT id FROM hospitals WHERE hfr_id = 'IN-UP-HFR-50221'
           )""",
    )
    if cursor.rowcount:
        print("[DB MIGRATION] Set total_beds=350, total_icu=40 for Yatharth availability record.")
    else:
        print("[DB MIGRATION] No availability row found for Yatharth — nothing to update.")

    conn.commit()
    conn.close()
    print("[DB MIGRATION COMPLETE] Schema ready. Canonical demo data applied.")


if __name__ == "__main__":
    migrate_sqlite_db()

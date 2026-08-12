import sqlite3
import os

def migrate_sqlite_db(db_path: str = "chanakya.db"):
    if not os.path.exists(db_path):
        print(f"[DB MIGRATION] Database file {db_path} does not exist yet.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing hospital table columns
    cursor.execute("PRAGMA table_info(hospitals)")
    hospital_cols = [col[1] for col in cursor.fetchall()]

    h_new_cols = [
        ("pricing_min", "REAL"),
        ("pricing_max", "REAL"),
        ("pricing_currency", "TEXT DEFAULT 'INR'"),
        ("pricing_status", "TEXT DEFAULT 'UNAVAILABLE'"),
        ("pricing_source", "TEXT"),
        ("pricing_source_url", "TEXT"),
        ("pricing_last_verified_at", "TIMESTAMP")
    ]

    for col_name, col_type in h_new_cols:
        if col_name not in hospital_cols:
            try:
                cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}")
                print(f"[DB MIGRATION] Added {col_name} to hospitals table.")
            except Exception as e:
                print(f"[DB MIGRATION NOTICE] {e}")

    # Get existing doctor table columns
    cursor.execute("PRAGMA table_info(doctors)")
    doctor_cols = [col[1] for col in cursor.fetchall()]

    d_new_cols = [
        ("consultation_fee_min", "REAL"),
        ("consultation_fee_max", "REAL"),
        ("consultation_fee_currency", "TEXT DEFAULT 'INR'"),
        ("consultation_fee_status", "TEXT DEFAULT 'UNAVAILABLE'"),
        ("consultation_fee_source", "TEXT")
    ]

    for col_name, col_type in d_new_cols:
        if col_name not in doctor_cols:
            try:
                cursor.execute(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_type}")
                print(f"[DB MIGRATION] Added {col_name} to doctors table.")
            except Exception as e:
                print(f"[DB MIGRATION NOTICE] {e}")

    # Set all existing hospital & doctor pricing to NULL / UNAVAILABLE
    cursor.execute("UPDATE hospitals SET estimated_cost_range = 'Pricing unavailable from verified source', pricing_min = NULL, pricing_max = NULL, pricing_status = 'UNAVAILABLE', pricing_source = NULL")
    cursor.execute("UPDATE doctors SET consultation_fee = NULL, consultation_fee_min = NULL, consultation_fee_max = NULL, consultation_fee_status = 'UNAVAILABLE', consultation_fee_source = NULL")

    conn.commit()
    conn.close()
    print("[DB MIGRATION COMPLETE] All hospital and doctor pricing records migrated to honest UNAVAILABLE status!")

if __name__ == "__main__":
    migrate_sqlite_db()

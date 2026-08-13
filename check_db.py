import sqlite3, json

conn = sqlite3.connect('backend/chanakya.db')
c = conn.cursor()

c.execute("SELECT id, name, hfr_id, rating, suitability_score FROM hospitals WHERE hfr_id='IN-UP-HFR-50221'")
rows = c.fetchall()
for r in rows:
    print('ID:', r[0])
    print('Name:', r[1])
    print('HFR_ID:', r[2])
    print('Rating:', r[3])
    print('Suitability Score:', r[4])

if rows:
    hospital_id = rows[0][0]
    c.execute("SELECT treatment_pricing FROM hospitals WHERE id=?", (hospital_id,))
    tp_row = c.fetchone()
    tp = json.loads(tp_row[0]) if tp_row and tp_row[0] else None
    print('Treatment Pricing count:', len(tp) if tp else 0)
    if tp:
        for item in tp:
            print(f"  {item['treatment']}: {item['min_price']} - {item['max_price']} ({item['source_type']})")

    c.execute("SELECT total_beds, total_icu, status FROM availabilities WHERE hospital_id=?", (hospital_id,))
    avail = c.fetchone()
    print('Availability (total_beds, total_icu, status):', avail)

conn.close()
print("DB verification complete.")

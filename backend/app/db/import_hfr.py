"""Verified HFR data ingestion entrypoint.

This module deliberately contains no embedded hospital, clinician, pricing, or
availability data. Importing a verified ABDM/HFR export must be an explicit
operational task backed by an authenticated data source and provenance checks;
it must not run at application startup or on a Vercel request.
"""

from app.db.database import Base, engine


def import_data() -> None:
    """Prepare database tables without generating any healthcare records.

    Retained as the administrative import hook used by local tooling. A real
    HFR importer should validate source provenance before inserting records.
    """
    Base.metadata.create_all(bind=engine)
    print("[HFR IMPORTER] Schema ready. No embedded records were imported.")


if __name__ == "__main__":
    import_data()

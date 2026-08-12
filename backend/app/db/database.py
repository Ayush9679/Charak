import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

database_url = settings.DATABASE_URL
if database_url == "sqlite:///./chanakya.db":
    # Keep local SQLite data beside the backend regardless of the command's
    # working directory (for example, `pytest backend/tests` at repo root).
    sqlite_path = Path(__file__).resolve().parents[2] / "chanakya.db"
    database_url = f"sqlite:///{sqlite_path.as_posix()}"
elif database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]

if os.getenv("VERCEL") and database_url.startswith("sqlite"):
    raise RuntimeError(
        "DATABASE_URL must point to a persistent PostgreSQL database on Vercel; "
        "SQLite files are ephemeral in serverless deployments."
    )

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

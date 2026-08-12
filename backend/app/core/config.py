from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CHANAKYA Healthcare Navigation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8082",
        "http://127.0.0.1:8082",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    DATABASE_URL: str = "sqlite:///./chanakya.db"
    ADMIN_TOKEN: str = ""

    LOCAL_HOSPITAL_PROVIDER: str = "osm"
    LOCAL_HOSPITAL_SEARCH_RADIUS_KM: float = 10.0
    OSM_OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_DISCOVERY_CACHE_MINUTES: int = 15
    
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"
    
    # Timeouts in seconds
    GROQ_TIMEOUT_SECONDS: float = 30.0
    GROQ_VISION_TIMEOUT_SECONDS: float = 45.0
    PROVIDER_TIMEOUT_SECONDS: float = 15.0
    AVAILABILITY_TIMEOUT_SECONDS: float = 10.0

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            # Support comma-separated string from .env
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        # Support the existing backend/.env and a project-root .env without
        # requiring secrets to be copied into source control. Runtime
        # environment variables take precedence over both files.
        env_file=(
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[3] / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

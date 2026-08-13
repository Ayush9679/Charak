import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import engine, Base
from app.db.migrate_schema import migrate_sqlite_db
from app.api.routes import admin, appointments, chat, emergency, health, hospitals, recommendations

# Create database tables
Base.metadata.create_all(bind=engine)
migrate_sqlite_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request duration logging middleware
@app.middleware("http")
async def log_request_duration(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    print(f"[CHANAKYA BACKEND] {request.method} {request.url.path} {response.status_code} - {duration_ms}ms")
    return response

@app.on_event("startup")
def startup_event():
    # Database schema creation is idempotent. Hospital records must be loaded
    # through a verified HFR ingestion process, never generated at startup.
    print("[CHANAKYA BACKEND] Server started. Verified hospital data is managed externally.")

# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(hospitals.router, tags=["Hospitals"])
app.include_router(recommendations.router, tags=["Recommendations"])
app.include_router(chat.router, tags=["Currado Chat"])
app.include_router(emergency.router, tags=["Emergency"])
app.include_router(appointments.router, tags=["Appointments"])
app.include_router(admin.router, tags=["Admin"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[UNHANDLED ERROR] {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": "SERVER_ERROR",
            "message": "An internal server error occurred.",
            "details": str(exc) if app.debug else None
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

"""Vercel entrypoint that exposes the existing FastAPI application.

The deployment sends requests under /api/* to this function. The middleware
below removes that hosting prefix before FastAPI matches the existing routes;
no second FastAPI app or duplicate routers are created.
"""

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


@app.middleware("http")
async def strip_vercel_api_prefix(request, call_next):
    path = request.scope.get("path", "")
    if path == "/api":
        request.scope["path"] = "/"
    elif path.startswith("/api/"):
        request.scope["path"] = path[4:]
    return await call_next(request)

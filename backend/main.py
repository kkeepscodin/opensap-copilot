"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "MVP API for structured understanding of safe, synthetic SAP ABAP source files."
    ),
)
app.include_router(router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": "OpenSAP Copilot API is running.",
        "documentation": "/docs",
    }

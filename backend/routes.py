"""HTTP routes for the MVP backend."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.analysis import AnalysisResponse, HealthResponse
from app.services.analyzer import analyze_abap

router = APIRouter()
_ALLOWED_EXTENSIONS = {".abap", ".txt"}


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )


@router.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    tags=["analysis"],
    status_code=status.HTTP_200_OK,
)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    filename = file.filename or ""
    suffix = "." + filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""

    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .abap and .txt files are accepted in v0.1.",
        )

    raw = await file.read(settings.max_upload_size_bytes + 1)
    await file.close()

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )
    if len(raw) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_bytes}-byte MVP limit.",
        )

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file must be UTF-8 encoded.",
        ) from exc

    return analyze_abap(source)

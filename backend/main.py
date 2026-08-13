from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from analyzer import (
    build_call_flow,
    build_grounded_conclusion,
    build_risks,
    extract_dependencies,
    extract_tables,
    find_program_name,
)
from llm_service import enrich_with_ai
from models import AnalysisResponse

APP_VERSION = "0.4.0"
MAX_FILE_SIZE_BYTES = 1_000_000
ALLOWED_EXTENSIONS = {".abap", ".txt"}

app = FastAPI(
    title="OpenSAP Copilot API",
    description=(
        "Hybrid evidence-grounded ABAP program comprehension MVP with "
        "optional structured LLM enrichment."
    ),
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "OpenSAP Copilot API",
        "version": APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "opensap-copilot-backend",
        "version": APP_VERSION,
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
):
    filename = file.filename or "uploaded.abap"
    suffix = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Only .abap and .txt files are accepted.",
        )

    raw = await file.read(MAX_FILE_SIZE_BYTES + 1)

    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The uploaded file exceeds the 1 MB MVP limit.",
        )

    if not raw.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The file must be UTF-8 encoded.",
        ) from exc

    program_name = find_program_name(source)
    tables = extract_tables(source)
    dependencies = extract_dependencies(source)
    grounded = build_grounded_conclusion(tables, dependencies)
    call_flow = build_call_flow(source, dependencies)
    risks = build_risks(source, tables, dependencies)
    ai_analysis = enrich_with_ai(source, grounded, requested=use_ai)

    if ai_analysis.available:
        business_summary = ai_analysis.business_summary or grounded.conclusion
        analysis_mode = "hybrid-static-plus-llm"
    else:
        business_summary = (
            f"{program_name} was analyzed using deterministic static extraction "
            "with explicit evidence and uncertainty."
        )
        analysis_mode = "evidence-grounded-deterministic-mvp"

    return AnalysisResponse(
        program_name=program_name,
        purpose=grounded.conclusion,
        business_summary=business_summary,
        grounded_conclusion=grounded,
        tables=tables,
        dependencies=dependencies,
        call_flow=call_flow,
        risks=risks,
        ai_analysis=ai_analysis,
        analysis_mode=analysis_mode,
    )

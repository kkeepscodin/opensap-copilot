from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from analyzer import analyze_abap
from models import AnalysisResponse

APP_VERSION = "0.2.1"
MAX_FILE_SIZE_BYTES = 1_000_000
ALLOWED_EXTENSIONS = {".abap", ".txt"}

app = FastAPI(title="OpenSAP Copilot API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "OpenSAP Copilot API", "version": APP_VERSION, "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "opensap-copilot-backend", "version": APP_VERSION}

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)):
    filename = file.filename or "uploaded.abap"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only .abap and .txt files are accepted.")
    raw = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="The uploaded file exceeds the 1 MB MVP limit.")
    if not raw.strip():
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="The file must be UTF-8 encoded.") from exc
    return analyze_abap(source)

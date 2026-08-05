# OpenSAP Copilot Backend

This folder contains the FastAPI backend for the v0.1 demo.

## What works in this milestone

- `GET /health`
- `POST /api/v1/analyze`
- `.abap` and `.txt` validation
- upload-size validation
- deterministic extraction of program name, tables, dependencies, call flow, and visible risks
- automated tests

No source code is sent to an external AI provider yet.

## Run on Windows PowerShell

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Run tests

```powershell
cd backend
pytest
```

Expected result:

```text
3 passed
```

## Test the analyzer manually

In the Swagger page at `/docs`:

1. Open `POST /api/v1/analyze`.
2. Click **Try it out**.
3. Upload `samples/z_inventory_demo.abap` from the repository root.
4. Click **Execute**.

## Security rule

Never test this public project with proprietary production ABAP. Use only synthetic, anonymized, or explicitly permitted source files.

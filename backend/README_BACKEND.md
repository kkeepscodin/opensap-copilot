# OpenSAP Copilot Backend v0.2

This is the web-upload-safe backend foundation. All Python files intentionally live directly inside `backend/`, so GitHub's browser uploader cannot destroy nested Python package paths.

## Run on Windows

Open PowerShell or Command Prompt inside the `backend` directory:

```powershell
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

Or double-click:

```text
run_backend.bat
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Test

```powershell
py -m pytest -q
```

Expected result:

```text
3 passed
```

## Endpoints

- `GET /`
- `GET /health`
- `POST /api/v1/analyze`

## Important

The current analyzer is deterministic and intentionally lightweight. It proves the end-to-end product flow before an LLM provider is connected.

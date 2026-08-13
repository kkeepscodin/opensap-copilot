import json

import httpx
from fastapi.testclient import TestClient

import llm_service
from main import app

client = TestClient(app)

SAMPLE = b"""
REPORT z_inventory_demo.
PARAMETERS p_matnr TYPE matnr.
START-OF-SELECTION.
  SELECT SINGLE matnr
    FROM mara
    INTO @DATA(lv_matnr)
    WHERE matnr = @p_matnr.
  CALL FUNCTION 'BAPI_GOODSMVT_CREATE'.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'.
"""


def _post(use_ai: str):
    return client.post(
        "/api/v1/analyze",
        files={"file": ("z_inventory_demo.abap", SAMPLE, "text/plain")},
        data={"use_ai": use_ai},
    )


def _mock_ollama(monkeypatch, enrichment: dict):
    def fake_request(base_url, request_payload):
        request = httpx.Request("POST", f"{base_url}/api/generate")
        return httpx.Response(
            200,
            request=request,
            json={"response": json.dumps(enrichment)},
        )

    monkeypatch.setattr(llm_service, "_request_ollama", fake_request)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.5.0"


def test_static_mode_without_ai():
    response = _post("false")

    assert response.status_code == 200
    payload = response.json()

    assert payload["program_name"] == "Z_INVENTORY_DEMO"
    assert payload["grounded_conclusion"]["confidence"] == "high"
    assert payload["ai_analysis"]["requested"] is False
    assert payload["ai_analysis"]["available"] is False
    assert payload["analysis_mode"] == "evidence-grounded-deterministic-mvp"


def test_local_ai_success(monkeypatch):
    enrichment = {
        "technical_summary": "Reads MARA and invokes goods-movement BAPIs.",
        "business_summary": "Participates in a goods-movement workflow.",
        "change_considerations": ["Inspect BAPI input construction before changes."],
        "unknowns": ["Runtime customizing is not visible in static source."],
        "used_evidence": ["SELECT MARA", "BAPI_GOODSMVT_CREATE"],
    }
    _mock_ollama(monkeypatch, enrichment)

    response = _post("true")
    assert response.status_code == 200
    payload = response.json()

    assert payload["ai_analysis"]["requested"] is True
    assert payload["ai_analysis"]["available"] is True
    assert payload["ai_analysis"]["provider"] == "ollama-local"
    assert payload["ai_analysis"]["model"] == "qwen2.5-coder:3b"
    assert payload["ai_analysis"]["grounding_guard_applied"] is False
    assert payload["analysis_mode"] == "hybrid-static-plus-local-llm"
    assert "SELECT MARA" in payload["ai_analysis"]["used_evidence"]


def test_grounding_guard_blocks_unsupported_inventory_scenario(monkeypatch):
    enrichment = {
        "technical_summary": "The code performs an inventory transfer.",
        "business_summary": "This is used for inventory adjustments or transfers.",
        "change_considerations": ["Inspect BAPI input construction before changes."],
        "unknowns": [],
        "used_evidence": ["SELECT MARA", "BAPI_GOODSMVT_CREATE"],
    }
    _mock_ollama(monkeypatch, enrichment)

    response = _post("true")
    assert response.status_code == 200
    payload = response.json()
    ai = payload["ai_analysis"]

    assert ai["available"] is True
    assert ai["grounding_guard_applied"] is True
    assert "transfer" not in ai["business_summary"].lower()
    assert "adjustment" not in ai["business_summary"].lower()
    assert ai["grounding_notes"]
    assert "specific business scenario cannot be established" in ai["business_summary"].lower()


def test_local_ai_connection_failure_falls_back(monkeypatch):
    def fake_request(base_url, request_payload):
        request = httpx.Request("POST", f"{base_url}/api/generate")
        raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(llm_service, "_request_ollama", fake_request)

    response = _post("true")
    assert response.status_code == 200
    payload = response.json()

    assert payload["ai_analysis"]["requested"] is True
    assert payload["ai_analysis"]["available"] is False
    assert "could not reach Ollama" in payload["ai_analysis"]["message"]
    assert payload["analysis_mode"] == "evidence-grounded-deterministic-mvp"
    assert payload["grounded_conclusion"]["evidence"]


def test_reject_wrong_extension():
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("bad.exe", b"x", "application/octet-stream")},
    )

    assert response.status_code == 415

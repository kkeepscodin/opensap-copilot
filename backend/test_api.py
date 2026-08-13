from fastapi.testclient import TestClient

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


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.4.0"


def test_static_mode_without_ai():
    response = client.post(
        "/api/v1/analyze",
        files={
            "file": (
                "z_inventory_demo.abap",
                SAMPLE,
                "text/plain",
            )
        },
        data={"use_ai": "false"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["program_name"] == "Z_INVENTORY_DEMO"
    assert payload["grounded_conclusion"]["confidence"] == "high"
    assert payload["ai_analysis"]["requested"] is False
    assert payload["ai_analysis"]["available"] is False
    assert payload["analysis_mode"] == "evidence-grounded-deterministic-mvp"


def test_ai_requested_without_key_falls_back(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/api/v1/analyze",
        files={
            "file": (
                "z_inventory_demo.abap",
                SAMPLE,
                "text/plain",
            )
        },
        data={"use_ai": "true"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["ai_analysis"]["requested"] is True
    assert payload["ai_analysis"]["available"] is False
    assert "OPENAI_API_KEY" in payload["ai_analysis"]["message"]
    assert payload["grounded_conclusion"]["evidence"]


def test_reject_wrong_extension():
    response = client.post(
        "/api/v1/analyze",
        files={
            "file": (
                "bad.exe",
                b"x",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 415

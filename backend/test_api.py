from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

SAMPLE_ABAP = b"""
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


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_abap_file() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("z_inventory_demo.abap", SAMPLE_ABAP, "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["program_name"] == "Z_INVENTORY_DEMO"
    assert any(item["name"] == "MARA" for item in payload["tables"])
    assert any(
        item["name"] == "BAPI_GOODSMVT_CREATE"
        for item in payload["dependencies"]
    )


def test_rejects_wrong_extension() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("secret.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 415

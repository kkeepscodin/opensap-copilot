from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE = b"""
REPORT z_inventory_demo.
START-OF-SELECTION.
  SELECT * FROM mara INTO TABLE @DATA(lt_materials) UP TO 5 ROWS.
  CALL FUNCTION 'BAPI_GOODSMVT_CREATE'.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'.
"""


def test_analyze_returns_structured_result() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("z_inventory_demo.abap", SAMPLE, "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["program_name"] == "Z_INVENTORY_DEMO"
    assert any(table["name"] == "MARA" for table in body["tables"])
    assert any(
        dependency["name"] == "BAPI_GOODSMVT_CREATE"
        for dependency in body["dependencies"]
    )
    assert "Transaction commit" in body["call_flow"]


def test_analyze_rejects_unsupported_extension() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("program.pdf", b"not abap", "application/pdf")},
    )

    assert response.status_code == 415

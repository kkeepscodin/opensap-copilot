from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE_ABAP = b'''
REPORT z_inventory_demo.
PARAMETERS p_matnr TYPE matnr.
START-OF-SELECTION.
  SELECT SINGLE matnr FROM mara INTO @DATA(lv_matnr) WHERE matnr = @p_matnr.
  CALL FUNCTION 'BAPI_GOODSMVT_CREATE'.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'.
'''

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_analyze():
    r = client.post("/api/v1/analyze", files={"file": ("z_inventory_demo.abap", SAMPLE_ABAP, "text/plain")})
    assert r.status_code == 200
    data = r.json()
    assert data["program_name"] == "Z_INVENTORY_DEMO"
    assert any(x["name"] == "MARA" for x in data["tables"])

def test_reject_wrong_extension():
    r = client.post("/api/v1/analyze", files={"file": ("bad.exe", b"x", "application/octet-stream")})
    assert r.status_code == 415

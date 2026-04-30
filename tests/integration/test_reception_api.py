import pytest
from datetime import datetime, timezone
from httpx import AsyncClient


# ── POST /reception/upload ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    """Upload endpoint should reject empty HL7 files with 422."""
    response = await client.post(
        "/reception/upload",
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    # Should return HTTP 422 for empty file
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()

@pytest.mark.asyncio
async def test_upload_invalid_hl7_format(client: AsyncClient):
    """Upload endpoint should reject file missing MSH segment with 422."""
    content = b"Some random text without HL7 headers"
    response = await client.post(
        "/reception/upload",
        files={"file": ("invalid.txt", content, "text/plain")}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "MSH" in data["detail"].upper() or "format" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_hl7_batch_file(client: AsyncClient, stub_broker):
    """Upload endpoint should accept HL7 batch file and enqueue for processing."""
    # Create a minimal valid HL7 batch-like content with MLLP framing
    # Simple HL7 message wrapped with MLLP framing chars
    hl7_batch = (
        b'\x0bMSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n'
        b'PID|1|||TEST^PATIENT||19800101|M|||123 MAIN ST\r\n'
        b'OBR|1|||TEST^TEST|||20260414120000|||||||\r\n'
        b'OBX|1|ST|PARAM^Parameter||value|unit|ref|||F\r\n'
        b'\x1c\r'
    )
    
    response = await client.post(
        "/reception/upload",
        files={"file": ("batch.hl7", hl7_batch, "text/plain")}
    )
    # Should redirect to /taller/
    assert response.status_code == 200  # Followed redirect
    assert "/taller" in str(response.url)
    
    # Check that message was enqueued in stub broker
    q = stub_broker.queues["default"]
    assert q.qsize() >= 1


@pytest.mark.asyncio
async def test_upload_hl7_multiple_messages(client: AsyncClient, stub_broker):
    """Upload endpoint should handle batch file with multiple messages."""
    hl7_batch = (
        b'\x0bMSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n'
        b'PID|1|||FIRST^PATIENT||19800101|M|||123 ST\r\n'
        b'OBX|1|ST|PARAM^P||val|u|ref|||F\r\n'
        b'\x1c\r'
        b'\x0bMSH|^~\\&|TEST|LAB|||20260414120001||ORU^R01|2|P|2.3.1\r\n'
        b'PID|1|||SECOND^PATIENT||19900101|M|||456 ST\r\n'
        b'OBX|1|ST|PARAM^P||val|u|ref|||F\r\n'
        b'\x1c\r'
    )
    
    response = await client.post(
        "/reception/upload",
        files={"file": ("batch.hl7", hl7_batch, "text/plain")}
    )
    assert response.status_code == 200
    assert "/taller" in str(response.url)


# ── POST /reception/receive ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_receive_new_patient(client: AsyncClient):
    response = await client.post("/reception/receive", json={
        # Use unique name to avoid collision with other tests using "kitty felina 2a Laura Cepeda"
        "raw_string": "luna felina 3a Ana Gomez",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 200
    data = response.json()
    assert data["created"] is True
    assert data["patient_id"] > 0
    assert data["patient"]["name"] == "Luna"
    assert data["patient"]["species"] == "Felino"
    assert data["patient"]["sex"] == "Hembra"
    assert data["patient"]["owner_name"] == "Ana Gomez"

@pytest.mark.asyncio
async def test_receive_duplicate_patient(client: AsyncClient):
    payload = {
        "raw_string": "rocky canino 3a Juan Pérez",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    r1 = await client.post("/reception/receive", json=payload)
    r2 = await client.post("/reception/receive", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["created"] is True
    assert r2.json()["created"] is False
    assert r1.json()["patient_id"] == r2.json()["patient_id"]

@pytest.mark.asyncio
async def test_receive_invalid_species_returns_422(client: AsyncClient):
    response = await client.post("/reception/receive", json={
        "raw_string": "rocky perro 2a Juan",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_receive_coproscopic_no_age(client: AsyncClient):
    response = await client.post("/reception/receive", json={
        "raw_string": "luna felina Laura García",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["has_age"] is False
    assert data["patient"]["age_display"] is None

@pytest.mark.asyncio
async def test_receive_lis_file_source(client: AsyncClient):
    response = await client.post("/reception/receive", json={
        "raw_string": "max canino 5a Pedro Gómez",
        "source": "LIS_FILE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 200
    assert response.json()["patient"]["source"] == "LIS_FILE"


# ── GET /reception/patients ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_patients_empty(client: AsyncClient):
    response = await client.get("/reception/patients")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "patients" in data
    assert isinstance(data["patients"], list)

@pytest.mark.asyncio
async def test_list_patients_after_register(client: AsyncClient):
    await client.post("/reception/receive", json={
        "raw_string": "nala canina 1a Sofia Ruiz",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    response = await client.get("/reception/patients")
    assert response.status_code == 200
    assert response.json()["total"] >= 1

@pytest.mark.asyncio
async def test_list_patients_filter_by_species(client: AsyncClient):
    response = await client.get("/reception/patients?species=Felino")
    assert response.status_code == 200
    for p in response.json()["patients"]:
        assert p["species"] == "Felino"


# ── GET /reception/patients/{id} ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_patient_by_id(client: AsyncClient):
    create = await client.post("/reception/receive", json={
        "raw_string": "simba felino 4a Carlos Vera",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    patient_id = create.json()["patient_id"]
    response = await client.get(f"/reception/patients/{patient_id}")
    assert response.status_code == 200
    assert response.json()["id"] == patient_id
    assert response.json()["name"] == "Simba"

@pytest.mark.asyncio
async def test_get_patient_not_found(client: AsyncClient):
    response = await client.get("/reception/patients/99999")
    assert response.status_code == 404

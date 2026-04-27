import pytest
from datetime import datetime, timezone
from httpx import AsyncClient


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

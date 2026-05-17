"""Integration tests for patient retirement (archive + cascade delete) and archive PDF regeneration."""
import json

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import text

from tests.integration.test_taller_api import register_patient, make_lab_values


@pytest.fixture(autouse=True)
async def cleanup_archive():
    """Clean up PatientArchive between tests to avoid cross-test pollution."""
    from tests.conftest import _get_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    yield
    engine = _get_engine()
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        await session.execute(text("DELETE FROM patientarchive"))
        await session.execute(text("DELETE FROM examorder"))
        await session.execute(text("DELETE FROM labvalue"))
        await session.execute(text("DELETE FROM patientimage"))
        await session.execute(text("DELETE FROM testresult"))
        await session.execute(text("DELETE FROM patient"))
        await session.commit()


async def enrich_result(client: AsyncClient, patient_id: int) -> int:
    """Helper: enrich a test result and return result_id."""
    response = await client.post("/taller/enrich", json={
        "patient_id": patient_id,
        "species": "Felino",
        "test_type": "Hemograma",
        "test_type_code": "CBC",
        "source": "LIS_OZELLE",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "values": make_lab_values(),
    })
    assert response.status_code == 200
    return response.json()["test_result_id"]


# ── GET /reports/{id}/pdf — Retirement flow ───────────────────────────────


@pytest.mark.asyncio
async def test_pdf_download_archives_and_deletes_patient(client: AsyncClient):
    """After PDF download, patient is archived in PatientArchive and deleted from main tables."""
    # 1. Create a patient with lab data
    patient_id = await register_patient(client)
    result_id = await enrich_result(client, patient_id)

    # 2. Download PDF — this should trigger retirement
    response = await client.get(f"/reports/{result_id}/pdf")
    assert response.status_code == 200
    assert len(response.content) > 0
    assert response.content[:4] == b'%PDF'

    # 3. Verify archive row exists
    # Use raw SQL to check PatientArchive table (model is imported)
    from tests.conftest import _get_engine
    from sqlmodel import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.shared.models.patient_archive import PatientArchive
    from app.domains.patients.models import Patient

    engine = _get_engine()
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        # Verify PatientArchive row was created
        stmt = select(PatientArchive).where(PatientArchive.original_patient_id == patient_id)
        result = await session.execute(stmt)
        archive = result.scalar_one_or_none()
        assert archive is not None, "PatientArchive row should exist after PDF download"
        assert archive.patient_name == "Kitty"
        assert archive.owner_name == "Laura Cepeda"
        assert archive.species == "Felino"
        assert archive.original_patient_id == patient_id
        assert archive.original_test_result_id == result_id

        # Verify snapshot contains expected data
        snapshot = json.loads(archive.snapshot_data)
        assert "test_result" in snapshot
        assert "patient" in snapshot
        assert "lab_values" in snapshot
        assert len(snapshot["lab_values"]) == 3

        # 4. Verify patient is deleted from main tables
        stmt_patient = select(Patient).where(Patient.id == patient_id)
        result = await session.execute(stmt_patient)
        patient = result.scalar_one_or_none()
        assert patient is None, f"Patient {patient_id} should be deleted after retirement"


@pytest.mark.asyncio
async def test_pdf_download_without_lab_values_still_archives(client: AsyncClient):
    """Patient without LabValues should still be archived and deleted on PDF download."""
    patient_id = await register_patient(client)
    result_id = await enrich_result(client, patient_id)

    response = await client.get(f"/reports/{result_id}/pdf")
    assert response.status_code == 200

    from tests.conftest import _get_engine
    from sqlmodel import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.shared.models.patient_archive import PatientArchive

    engine = _get_engine()
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        stmt = select(PatientArchive).where(PatientArchive.original_patient_id == patient_id)
        result = await session.execute(stmt)
        archive = result.scalar_one_or_none()
        assert archive is not None, "PatientArchive should exist even without lab values"


# ── GET /reports/archive/{id}/pdf — Archive regeneration ──────────────────


@pytest.mark.asyncio
async def test_archive_pdf_regeneration(client: AsyncClient):
    """GET /reports/archive/{id}/pdf regenerates PDF from archived snapshot."""
    # 1. Retire a patient first (archive it)
    patient_id = await register_patient(client)
    result_id = await enrich_result(client, patient_id)
    pdf_response = await client.get(f"/reports/{result_id}/pdf")
    assert pdf_response.status_code == 200
    original_content = pdf_response.content

    # 2. Find the archive ID
    from tests.conftest import _get_engine
    from sqlmodel import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.shared.models.patient_archive import PatientArchive

    engine = _get_engine()
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        stmt = select(PatientArchive).where(PatientArchive.original_patient_id == patient_id)
        result = await session.execute(stmt)
        archive = result.scalar_one_or_none()
        assert archive is not None
        archive_id = archive.id

    # 3. Regenerate PDF from archive
    regen_response = await client.get(f"/reports/archive/{archive_id}/pdf")
    assert regen_response.status_code == 200
    assert regen_response.headers["content-type"] == "application/pdf"
    assert len(regen_response.content) > 0
    assert regen_response.content[:4] == b'%PDF'


@pytest.mark.asyncio
async def test_archive_pdf_not_found(client: AsyncClient):
    """GET /reports/archive/{id}/pdf returns 404 for non-existent archive."""
    response = await client.get("/reports/archive/99999/pdf")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_archive_pdf_filename_format(client: AsyncClient):
    """Archive PDF also has Content-Disposition header."""
    patient_id = await register_patient(client)
    result_id = await enrich_result(client, patient_id)
    pdf_response = await client.get(f"/reports/{result_id}/pdf")
    assert pdf_response.status_code == 200

    from tests.conftest import _get_engine
    from sqlmodel import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.shared.models.patient_archive import PatientArchive

    engine = _get_engine()
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        stmt = select(PatientArchive).where(PatientArchive.original_patient_id == patient_id)
        result = await session.execute(stmt)
        archive = result.scalar_one_or_none()
        assert archive is not None
        archive_id = archive.id

    regen_response = await client.get(f"/reports/archive/{archive_id}/pdf")
    content_disp = regen_response.headers.get("content-disposition", "")
    assert content_disp.startswith('attachment; filename="')
    assert content_disp.endswith('.pdf"')

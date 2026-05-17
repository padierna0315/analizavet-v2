"""Tests for ProvenanceRecorder — capture and linking facade."""
import pytest
from datetime import datetime, timezone

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.provenance_recorder import ProvenanceRecorder
from app.shared.models.raw_data_log import RawDataLog, RawDataSource


class TestRecordSync:
    """record_sync reuses the caller's DB session; never raises on failure."""

    @pytest.mark.asyncio
    async def test_creates_raw_data_log_row(self, session: AsyncSession):
        """Happy path: a RawDataLog row is persisted with correct values."""
        raw_json = '{"patients": [{"name": "Firulais"}]}'
        received = datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)

        await ProvenanceRecorder.record_sync(
            session=session,
            source=RawDataSource.APPSHEET,
            raw_data=raw_json,
            received_at=received,
            session_code="A1-20260501",
            metadata='{"content_type": "application/json"}',
        )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM rawdatalog WHERE session_code = :sc"),
            {"sc": "A1-20260501"},
        )
        rows = result.fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row.source == "appsheet"
        assert row.raw_data == raw_json
        # SQLite stores datetime as string — compare values
        assert row.session_code == "A1-20260501"
        assert row.status == "pending"
        assert row.patient_id is None
        assert row.test_result_id is None

    @pytest.mark.asyncio
    async def test_survives_db_error(self, monkeypatch, session: AsyncSession):
        """When the DB write fails, error is swallowed — no exception propagates."""
        original_add = session.add

        def failing_add(instance):
            raise RuntimeError("simulated DB failure")

        monkeypatch.setattr(session, "add", failing_add)

        # Must NOT raise
        await ProvenanceRecorder.record_sync(
            session=session,
            source=RawDataSource.OZELLE,
            raw_data="MSH|...",
            received_at=datetime.now(timezone.utc),
        )
        # Restore for cleanup
        monkeypatch.setattr(session, "add", original_add)

    @pytest.mark.asyncio
    async def test_optional_fields_omitted(self, session: AsyncSession):
        """session_code and metadata are optional — row is still created."""
        now = datetime.now(timezone.utc)

        await ProvenanceRecorder.record_sync(
            session=session,
            source=RawDataSource.FUJIFILM,
            raw_data="FUJI|20260517|CBC",
            received_at=now,
        )
        await session.commit()

        result = await session.execute(
            select(RawDataLog).where(RawDataLog.source == "fujifilm")
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.raw_data == "FUJI|20260517|CBC"
        assert row.session_code is None


class TestRecordAsync:
    """record_async also uses a session; returns the new record ID."""

    @pytest.mark.asyncio
    async def test_returns_record_id(self, session: AsyncSession):
        """Returns the integer ID of the newly created RawDataLog."""
        log_id = await ProvenanceRecorder.record_async(
            session=session,
            source=RawDataSource.APPSHEET,
            raw_data="{}",
            received_at=datetime.now(timezone.utc),
        )

        assert log_id is not None
        assert isinstance(log_id, int)
        assert log_id > 0

    @pytest.mark.asyncio
    async def test_row_persisted_correctly(self, session: AsyncSession):
        """The returned ID corresponds to a row with matching fields."""
        raw_data = "MSH|...|OBX|1|"
        log_id = await ProvenanceRecorder.record_async(
            session=session,
            source=RawDataSource.OZELLE,
            raw_data=raw_data,
            received_at=datetime.now(timezone.utc),
            session_code="B2-20260517",
            metadata='{"encoding": "HL7"}',
        )

        result = await session.execute(
            select(RawDataLog).where(RawDataLog.id == log_id)
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.source == "ozelle"
        assert row.raw_data == raw_data
        assert row.session_code == "B2-20260517"
        assert row.status == "pending"

    @pytest.mark.asyncio
    async def test_survives_db_error(self, monkeypatch, session: AsyncSession):
        """Returns None when DB write fails — no exception propagates."""
        original_add = session.add

        def failing_add(instance):
            raise OSError("connection lost")

        monkeypatch.setattr(session, "add", failing_add)

        log_id = await ProvenanceRecorder.record_async(
            session=session,
            source=RawDataSource.FUJIFILM,
            raw_data="bad-data",
            received_at=datetime.now(timezone.utc),
        )

        monkeypatch.setattr(session, "add", original_add)
        assert log_id is None


class TestLinkToPatient:
    """link_to_patient updates RawDataLog rows by session_code."""

    @pytest.mark.asyncio
    async def test_updates_patient_id_and_status(self, session: AsyncSession):
        """Sets patient_id, test_result_id, processed_at, and status='linked'."""
        now = datetime.now(timezone.utc)
        log = RawDataLog(
            source=RawDataSource.APPSHEET,
            raw_data="{}",
            received_at=now,
            session_code="C3-20260501",
            status="pending",
        )
        session.add(log)
        await session.commit()

        await ProvenanceRecorder.link_to_patient(
            session=session,
            session_code="C3-20260501",
            patient_id=42,
            test_result_id=99,
        )
        await session.commit()

        result = await session.execute(
            select(RawDataLog).where(RawDataLog.session_code == "C3-20260501")
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.patient_id == 42
        assert row.test_result_id == 99
        assert row.status == "linked"
        assert row.processed_at is not None

    @pytest.mark.asyncio
    async def test_non_existent_session_code_is_noop(self, session: AsyncSession):
        """Updating a non-existent session_code does nothing, no error raised."""
        await ProvenanceRecorder.link_to_patient(
            session=session,
            session_code="NONEXISTENT",
            patient_id=1,
        )
        # No exception = pass
        assert True

    @pytest.mark.asyncio
    async def test_survives_db_error(self, monkeypatch, session: AsyncSession):
        """DB error during the update is swallowed."""
        original_execute = session.execute

        async def failing_execute(*args, **kwargs):
            raise RuntimeError("connection lost")

        monkeypatch.setattr(session, "execute", failing_execute)

        await ProvenanceRecorder.link_to_patient(
            session=session,
            session_code="ANY",
            patient_id=1,
        )

        monkeypatch.setattr(session, "execute", original_execute)
        # No exception = pass
        assert True

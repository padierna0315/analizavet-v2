"""Tests for RawDataLog model and enums."""
import pytest
from datetime import datetime, timezone
from app.shared.models.raw_data_log import RawDataLog, RawDataSource, RawDataStatus


class TestRawDataLogModel:
    """RawDataLog SQLModel validation and defaults."""

    def test_instantiation_with_all_fields(self):
        """RawDataLog is created with explicit values for every field."""
        now = datetime.now(timezone.utc)
        log = RawDataLog(
            source=RawDataSource.APPSHEET,
            raw_data='{"patients": [{"name": "Kitty"}]}',
            received_at=now,
            session_code="A1-20260501",
            status=RawDataStatus.PENDING,
            patient_id=None,
            test_result_id=None,
            processed_at=None,
            error_message=None,
            raw_metadata=None,
        )

        assert log.source == "appsheet"
        assert "Kitty" in log.raw_data
        assert log.received_at == now
        assert log.captured_at is not None
        assert log.session_code == "A1-20260501"
        assert log.status == "pending"
        assert log.patient_id is None
        assert log.test_result_id is None
        assert log.processed_at is None
        assert log.error_message is None
        assert log.raw_metadata is None

    def test_default_values_for_optional_fields(self):
        """Optional fields default to None; status defaults to 'pending'."""
        now = datetime.now(timezone.utc)
        log = RawDataLog(
            source=RawDataSource.OZELLE,
            raw_data="MSH|^~\\&|LAB|FACILITY|...",
            received_at=now,
        )

        assert log.status == "pending"
        assert log.captured_at is not None
        assert log.patient_id is None
        assert log.test_result_id is None
        assert log.session_code is None
        assert log.processed_at is None
        assert log.error_message is None
        assert log.raw_metadata is None

    def test_large_raw_data_stored(self):
        """Text column supports payloads ≥ 100 KB."""
        now = datetime.now(timezone.utc)
        large_payload = "X" * 100_000  # 100 KB

        log = RawDataLog(
            source=RawDataSource.FUJIFILM,
            raw_data=large_payload,
            received_at=now,
        )

        assert len(log.raw_data) == 100_000
        assert log.source == "fujifilm"

    def test_captured_at_auto_set(self):
        """captured_at default_factory sets UTC timestamp on creation."""
        before = datetime.now(timezone.utc)
        log = RawDataLog(
            source=RawDataSource.APPSHEET,
            raw_data="{}",
            received_at=datetime.now(timezone.utc),
        )
        after = datetime.now(timezone.utc)

        assert before <= log.captured_at <= after

    def test_table_name_is_rawdatalog(self):
        """Tablename matches the Alembic migration target."""
        assert RawDataLog.__tablename__ == "rawdatalog"


class TestRawDataSourceEnum:
    """RawDataSource discriminates capture sources."""

    def test_enum_values(self):
        assert RawDataSource.APPSHEET.value == "appsheet"
        assert RawDataSource.OZELLE.value == "ozelle"
        assert RawDataSource.FUJIFILM.value == "fujifilm"

    def test_enum_count(self):
        sources = list(RawDataSource)
        assert len(sources) == 3


class TestRawDataStatusEnum:
    """RawDataStatus tracks lifecycle state."""

    def test_enum_values(self):
        assert RawDataStatus.PENDING.value == "pending"
        assert RawDataStatus.LINKED.value == "linked"
        assert RawDataStatus.ARCHIVED.value == "archived"

    def test_enum_count(self):
        statuses = list(RawDataStatus)
        assert len(statuses) == 3

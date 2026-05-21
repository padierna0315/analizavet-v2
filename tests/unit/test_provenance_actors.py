"""Tests for provenance capture Dramatiq actors — fire-and-forget, no retry."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.shared.models.raw_data_log import RawDataSource


class TestRecordOzelleRawActor:
    """record_ozelle_raw — fire-and-forget HL7 capture."""

    def test_max_retries_is_zero(self):
        """max_retries=0 ensures fire-and-forget (no retry on failure)."""
        from app.tasks.provenance_actors import record_ozelle_raw

        assert record_ozelle_raw.options["max_retries"] == 0

    @pytest.mark.asyncio
    async def test_calls_provenance_recorder_with_correct_args(self):
        """Actor calls ProvenanceRecorder.record_async with source=ozelle."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
            ) as mock_record:
                from app.tasks.provenance_actors import _record_ozelle_async

                await _record_ozelle_async("MSH|^~\\&|OZELLE|LAB|||20260520||ORU^R01|", None)

                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args.kwargs["source"] == RawDataSource.OZELLE
                assert call_args.kwargs["raw_data"] == "MSH|^~\\&|OZELLE|LAB|||20260520||ORU^R01|"

    @pytest.mark.asyncio
    async def test_survives_db_error(self):
        """When record_async raises, _record_ozelle_async swallows exception."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
                side_effect=RuntimeError("DB failure"),
            ):
                from app.tasks.provenance_actors import _record_ozelle_async

                # Must NOT raise
                await _record_ozelle_async("MSH|bad", None)
                # Test passes if no exception propagated

    @pytest.mark.asyncio
    async def test_parses_received_at_iso(self):
        """When received_at_iso is provided, it is parsed into datetime."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
            ) as mock_record:
                from app.tasks.provenance_actors import _record_ozelle_async

                iso = "2026-05-20T10:30:00+00:00"
                await _record_ozelle_async("MSH|test", iso)

                call_kwargs = mock_record.call_args.kwargs
                received = call_kwargs["received_at"]
                assert received == datetime(2026, 5, 20, 10, 30, 0, tzinfo=timezone.utc)

    def test_sync_wrapper_survives_anyio_error(self, monkeypatch):
        """The Dramatiq actor wrapper swallows anyio.run exceptions."""
        def _raise(*args, **kwargs):
            raise OSError("anyio crash")

        monkeypatch.setattr("app.tasks.provenance_actors.anyio.run", _raise)

        from app.tasks.provenance_actors import record_ozelle_raw

        # Must not raise — fire-and-forget
        record_ozelle_raw("MSH|anything")
        # Test passes if no exception


class TestRecordFujifilmRawActor:
    """record_fujifilm_raw — fire-and-forget TCP capture."""

    def test_max_retries_is_zero(self):
        """max_retries=0 ensures fire-and-forget (no retry on failure)."""
        from app.tasks.provenance_actors import record_fujifilm_raw

        assert record_fujifilm_raw.options["max_retries"] == 0

    @pytest.mark.asyncio
    async def test_calls_provenance_recorder_with_correct_args(self):
        """Actor calls ProvenanceRecorder.record_async with source=fujifilm."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
            ) as mock_record:
                from app.tasks.provenance_actors import _record_fujifilm_async

                await _record_fujifilm_async("FUJI|STX|DRI-CHEM|20260520|CBC", None)

                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args.kwargs["source"] == RawDataSource.FUJIFILM
                assert "FUJI" in call_args.kwargs["raw_data"]

    @pytest.mark.asyncio
    async def test_survives_db_error(self):
        """When record_async raises, _record_fujifilm_async swallows exception."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
                side_effect=RuntimeError("DB failure"),
            ):
                from app.tasks.provenance_actors import _record_fujifilm_async

                await _record_fujifilm_async("FUJI|bad", None)
                # No exception = pass

    @pytest.mark.asyncio
    async def test_parses_received_at_iso(self):
        """When received_at_iso is provided, it is parsed into datetime."""
        mock_session = AsyncMock()
        mock_session_local = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        with patch(
            "app.tasks.provenance_actors.AsyncSessionLocal", return_value=mock_session_local
        ):
            with patch(
                "app.tasks.provenance_actors.ProvenanceRecorder.record_async",
                new_callable=AsyncMock,
            ) as mock_record:
                from app.tasks.provenance_actors import _record_fujifilm_async

                iso = "2026-05-20T15:45:00+00:00"
                await _record_fujifilm_async("FUJI|test", iso)

                call_kwargs = mock_record.call_args.kwargs
                received = call_kwargs["received_at"]
                assert received == datetime(2026, 5, 20, 15, 45, 0, tzinfo=timezone.utc)

    def test_sync_wrapper_survives_anyio_error(self, monkeypatch):
        """The Dramatiq actor wrapper swallows anyio.run exceptions."""
        def _raise(*args, **kwargs):
            raise OSError("anyio crash")

        monkeypatch.setattr("app.tasks.provenance_actors.anyio.run", _raise)

        from app.tasks.provenance_actors import record_fujifilm_raw

        record_fujifilm_raw("FUJI|anything")
        # No exception = pass

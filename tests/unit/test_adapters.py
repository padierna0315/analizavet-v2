import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock

from app.satellites.base import SourceAdapter
from app.satellites.ozelle import OzelleAdapter
from app.satellites.fujifilm import FujifilmAdapter


def test_ozelle_adapter_implements_interface():
    adapter = OzelleAdapter()
    assert isinstance(adapter, SourceAdapter)
    assert adapter.get_source_name() == "LIS_OZELLE"


def test_fujifilm_adapter_implements_interface():
    adapter = FujifilmAdapter()
    assert isinstance(adapter, SourceAdapter)
    assert adapter.get_source_name() == "LIS_FUJIFILM"


@pytest.mark.asyncio
async def test_fujifilm_stub_receives_data():
    """Test that the Fujifilm stub can start, receive a connection, and stop cleanly."""
    adapter = FujifilmAdapter(host="127.0.0.1", port=0)
    await adapter.start()

    # Get actual port
    actual_port = adapter._server.sockets[0].getsockname()[1]

    # Connect and send data
    reader, writer = await asyncio.open_connection("127.0.0.1", actual_port)
    writer.write(b"HELLO FUJIFILM")
    await writer.drain()

    # Wait a tiny bit for the server to process it
    await asyncio.sleep(0.1)

    writer.close()
    await writer.wait_closed()

    await adapter.stop()


# ── Fujifilm provenance capture hook tests (Task 2.5) ───────────────────


TEST_FUJI_MSG = (
    "R,NORMAL,20-05-2026,10:30,908,POLO,CRE-PS,=,0.87,mg/dL\n"
)


@pytest.mark.asyncio
async def test_fujifilm_enqueues_provenance_actor(monkeypatch):
    """When a valid Fujifilm message arrives, record_fujifilm_raw.send is called BEFORE parsing."""
    mock_send = MagicMock()
    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_fujifilm_raw.send", mock_send
    )

    adapter = FujifilmAdapter(host="127.0.0.1", port=0)
    await adapter.start()
    actual_port = adapter._server.sockets[0].getsockname()[1]

    # Send valid Fujifilm message (newline-terminated → live mode)
    reader, writer = await asyncio.open_connection("127.0.0.1", actual_port)
    writer.write(TEST_FUJI_MSG.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    # Wait for processing
    await asyncio.sleep(0.1)

    await adapter.stop()

    # Provenance was triggered with the raw message
    mock_send.assert_called_once()
    call_arg = mock_send.call_args[0][0]
    assert "POLO" in call_arg
    assert "CRE" in call_arg


@pytest.mark.asyncio
async def test_fujifilm_provenance_failure_does_not_block(monkeypatch):
    """When record_fujifilm_raw.send raises, parsing still completes."""
    def _raise(*args, **kwargs):
        raise RuntimeError("broker down")

    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_fujifilm_raw.send", _raise
    )

    adapter = FujifilmAdapter(host="127.0.0.1", port=0)
    await adapter.start()
    actual_port = adapter._server.sockets[0].getsockname()[1]

    reader, writer = await asyncio.open_connection("127.0.0.1", actual_port)
    writer.write(TEST_FUJI_MSG.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    # Must not crash — adapter continues processing
    await asyncio.sleep(0.1)
    await adapter.stop()
    # Test passes if no exception


@pytest.mark.asyncio
async def test_fujifilm_captures_even_invalid_messages(monkeypatch):
    """Non-parseable messages are still captured BEFORE parsing fails."""
    mock_send = MagicMock()
    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_fujifilm_raw.send", mock_send
    )

    adapter = FujifilmAdapter(host="127.0.0.1", port=0)
    await adapter.start()
    actual_port = adapter._server.sockets[0].getsockname()[1]

    junk_msg = b"HELLO FUJIFILM GARBAGE DATA\n"
    reader, writer = await asyncio.open_connection("127.0.0.1", actual_port)
    writer.write(junk_msg)
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    await asyncio.sleep(0.1)
    await adapter.stop()

    # Should still capture the raw message even though it won't parse
    mock_send.assert_called_once()
    assert "GARBAGE" in mock_send.call_args[0][0]

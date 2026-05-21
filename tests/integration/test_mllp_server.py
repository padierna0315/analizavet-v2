"""
Integration tests for Ozelle MLLP Server — Phase 14

Acts as the Ozelle EHVT-50 machine: connects via TCP, sends MLLP-framed messages,
and reads back the MLLP-framed ACKs.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock

from app.satellites.ozelle.mllp_server import OzelleMLLPServer, SB, EB, CR


# Heartbeat message
TEST_ZHB = "MSH|^~\\&|HEARTBEAT|SENDER|RECEIVER|SYSTEM|20260416211909||ZHB^H00|HB000001|P|2.3.1\r"

# Valid ORU^R01
TEST_ORU = """MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|MSG001|P|2.3.1
PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG||||
OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||
OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F
"""


@pytest_asyncio.fixture
async def mllp_server():
    """Start server on a random free port for tests."""
    server = OzelleMLLPServer(host="127.0.0.1", port=0)
    await server.start()
    # Get the actual port assigned
    actual_port = server._server.sockets[0].getsockname()[1]
    server.port = actual_port

    yield server

    await server.stop()


async def send_mllp_message(port: int, hl7_msg: str) -> str:
    """Helper to act as the Ozelle machine."""
    reader, writer = await asyncio.open_connection("127.0.0.1", port)

    # Frame and send
    framed = SB + hl7_msg.encode("utf-8") + EB + CR
    writer.write(framed)
    await writer.drain()

    # Read ACK
    buffer = bytearray()
    while True:
        chunk = await reader.read(1024)
        if not chunk:
            break
        buffer.extend(chunk)
        if EB + CR in buffer:
            break

    writer.close()
    await writer.wait_closed()

    # Extract HL7 from ACK
    start_idx = buffer.find(SB)
    end_idx = buffer.find(EB + CR)
    ack_hl7 = buffer[start_idx + 1 : end_idx].decode("utf-8")
    return ack_hl7


@pytest.mark.asyncio
async def test_mllp_server_heartbeat_ack(mllp_server):
    ack = await send_mllp_message(mllp_server.port, TEST_ZHB)

    assert "MSH|^~\\&|ANALIZAVET" in ack
    assert "MSA|AA|HB000001" in ack  # Control ID matches


@pytest.mark.asyncio
async def test_mllp_server_oru_ack(mllp_server):
    ack = await send_mllp_message(mllp_server.port, TEST_ORU)

    assert "MSH|^~\\&|ANALIZAVET" in ack
    assert "MSA|AA|MSG001" in ack


@pytest.mark.asyncio
async def test_mllp_server_invalid_message_returns_ae(mllp_server):
    # Missing PID segment (causes HL7ParsingError)
    invalid_msg = "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|ERR001|P|2.3.1\rOBR|1|||CBC"
    ack = await send_mllp_message(mllp_server.port, invalid_msg)

    assert "MSA|AE|ERR001" in ack  # Application Error


# ── Provenance capture hook tests (Task 2.3) ────────────────────────────


@pytest.mark.asyncio
async def test_valid_oru_enqueues_provenance_actor(mllp_server, monkeypatch):
    """When a valid ORU message arrives, record_ozelle_raw.send is called BEFORE parsing."""
    mock_send = MagicMock()
    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_ozelle_raw.send", mock_send
    )

    ack = await send_mllp_message(mllp_server.port, TEST_ORU)

    # ACK still works normally
    assert "MSA|AA|MSG001" in ack

    # Provenance capture was triggered with the raw HL7
    mock_send.assert_called_once()
    call_arg = mock_send.call_args[0][0]
    assert "ORU^R01" in call_arg
    assert "kitty felina" in call_arg


@pytest.mark.asyncio
async def test_provenance_enqueue_failure_does_not_block_parsing(mllp_server, monkeypatch):
    """When record_ozelle_raw.send raises, parsing still completes and ACK is AA."""
    def _raise(*args, **kwargs):
        raise RuntimeError("broker down")

    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_ozelle_raw.send", _raise
    )

    ack = await send_mllp_message(mllp_server.port, TEST_ORU)

    # Must still get AA ACK — processing succeeded despite capture failure
    assert "MSA|AA|MSG001" in ack


@pytest.mark.asyncio
async def test_invalid_message_still_triggers_provenance(mllp_server, monkeypatch):
    """Even invalid messages are captured for debugging before parse error."""
    mock_send = MagicMock()
    monkeypatch.setattr(
        "app.tasks.provenance_actors.record_ozelle_raw.send", mock_send
    )

    invalid_msg = "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|ERR002|P|2.3.1\rOBR|1|||CBC"
    ack = await send_mllp_message(mllp_server.port, invalid_msg)

    # Gets AE because it fails parsing, but provenance was captured first
    assert "MSA|AE|ERR002" in ack
    mock_send.assert_called_once()
    assert "ERR002" in mock_send.call_args[0][0]

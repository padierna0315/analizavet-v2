"""
Integration tests for Dramatiq HL7 Processor — Phase 15

Uses the StubBroker configured in conftest (set BEFORE any app imports)
so actors are registered with the stub broker, not a real Redis broker.
"""

import pytest
import dramatiq

from app.tasks.hl7_processor import process_hl7_message
from app.schemas.reception import PatientSource


# Sample valid ORU message
TEST_ORU = (
    "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|MSG001|P|2.3.1\r"
    "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG||||\r"
    "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\r"
    "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\r"
)


def test_enqueue_hl7_message(stub_broker):
    """Test that a valid HL7 message is enqueued in the stub broker."""
    process_hl7_message.send(TEST_ORU, PatientSource.LIS_OZELLE.value)

    # StubBroker in Dramatiq 2.x stores messages in queues['default']
    q = stub_broker.queues["default"]
    assert q.qsize() == 1


def test_actor_processes_valid_message(monkeypatch):
    """Test that the actor processes a valid HL7 message without raising.
    Mocks the async pipeline to avoid needing a real DB connection.
    (Full pipeline is tested in test_pipeline.py).
    """
    import app.tasks.hl7_processor
    
    # Mock the inner async pipeline so we just test the parsing/dispatching
    async def mock_pipeline(*args, **kwargs):
        pass
    
    monkeypatch.setattr(app.tasks.hl7_processor, "_async_process_pipeline", mock_pipeline)
    
    # Direct invocation (synchronous) to test the full logic
    process_hl7_message(TEST_ORU, PatientSource.LIS_OZELLE.value)


def test_actor_handles_malformed_message():
    """Test that the actor handles a malformed HL7 message gracefully.

    A message without PID should raise HL7ParsingError, which the actor
    catches and logs without re-raising — so it shouldn't raise.
    """
    malformed = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|ERR001|P|2.3.1\r"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\r"
    )

    # Should NOT raise — HL7ParsingError is caught internally
    process_hl7_message(malformed, PatientSource.LIS_OZELLE.value)


def test_actor_handles_heartbeat():
    """Test that the actor handles a ZHB heartbeat message gracefully.

    A heartbeat raises HeartbeatMessageException during parsing,
    which is caught by the actor as a fatal non-retryable error.
    """
    heartbeat = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ZHB^H00|HB001|P|2.3.1\r"
    )

    # Should NOT raise — HeartbeatMessageException is caught internally
    process_hl7_message(heartbeat, PatientSource.LIS_OZELLE.value)

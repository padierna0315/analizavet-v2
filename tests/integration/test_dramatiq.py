"""
Integration tests for Dramatiq HL7 Processor — Phase 15

Verifies that HL7 messages are correctly processed through the Dramatiq pipeline
with appropriate PatientSource values based on upload type.
"""

import pytest
import dramatiq

from app.tasks.hl7_processor import process_hl7_message, process_uploaded_batch
from app.schemas.reception import PatientSource
from app.satellites.ozelle.batch_splitter import BatchSplitter


# ── Sample HL7 fixtures ────────────────────────────────────────────────────────

TEST_ORU = (
    "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|MSG001|P|2.3.1\r"
    "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\r"
    "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017|||||||\r"
    "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\r"
)


# ── Unit-level actor tests ────────────────────────────────────────────────────

def test_enqueue_hl7_message(stub_broker):
    """Test that a valid HL7 message is enqueued in the stub broker."""
    process_hl7_message.send(TEST_ORU, PatientSource.LIS_OZELLE.value)

    q = stub_broker.queues["default"]
    assert q.qsize() == 1


def test_actor_handles_malformed_message():
    """Test that the actor handles a malformed HL7 message gracefully."""
    malformed = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01|ERR001|P|2.3.1\r"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017|||||||\r"
    )
    process_hl7_message(malformed, PatientSource.LIS_OZELLE.value)


def test_actor_handles_heartbeat():
    """Test that the actor handles a ZHB heartbeat message gracefully."""
    heartbeat = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ZHB^H00|HB000001|P|2.3.1\r"
    )
    process_hl7_message(heartbeat, PatientSource.LIS_OZELLE.value)
def test_process_uploaded_batch_uses_lis_file_source(monkeypatch):
    """Verify process_uploaded_batch calls process_hl7_message with LIS_FILE source."""
    import app.tasks.hl7_processor as hp_module
    
    calls = []
    
    def mock_send(*args, **kwargs):
        # args[0] = self (actor instance), args[1] = message, args[2] = source (if present)
        calls.append({"args": args})
        # Don't actually enqueue to avoid broker complications
    
    monkeypatch.setattr(hp_module, "process_hl7_message", type('MockActor', (), {'send': mock_send})())
    
    mllp_msg_bytes = (
        b"\x0bMSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n"
        b"PID|1|||UPLOAD_PATIENT|\r\n"
        b"\x1c\r"
    )
    mllp_msg = mllp_msg_bytes.decode('utf-8')
    
    # Call the underlying function directly (bypass actor wrapper)
    # process_uploaded_batch is a Dramatiq actor; use .fn to access raw function
    hp_module.process_uploaded_batch.fn(mllp_msg)
    
    assert len(calls) >= 1
    # Each call: args[0]=self, args[1]=message, args[2]=source
    for call in calls:
        actual_source = call["args"][2] if len(call["args"]) > 2 else None
        assert actual_source == PatientSource.LIS_FILE.value, f"Expected LIS_FILE but got {actual_source}, raw args: {call['args']}"


def test_process_uploaded_batch_plain_hl7_uses_lis_file(monkeypatch):
    """Verify plain HL7 from file upload calls process_hl7_message with LIS_FILE."""
    import app.tasks.hl7_processor as hp_module
    
    calls = []
    
    def mock_send(*args, **kwargs):
        calls.append({"args": args})
    
    monkeypatch.setattr(hp_module, "process_hl7_message", type('MockActor', (), {'send': mock_send})())
    
    plain_batch_bytes = (
        b"MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n"
        b"PID|1|||PLAIN_PATIENT|\r\n"
    )
    plain_batch = plain_batch_bytes.decode('utf-8')
    
    hp_module.process_uploaded_batch.fn(plain_batch)
    
    assert len(calls) >= 1
    for call in calls:
        actual_source = call["args"][2] if len(call["args"]) > 2 else None
        assert actual_source == PatientSource.LIS_FILE.value

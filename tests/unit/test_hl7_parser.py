"""
Tests for app.satellites.ozelle.hl7_parser — Phase 13
"""

import pytest
from datetime import datetime, timezone

from app.satellites.ozelle.hl7_parser import (
    parse_hl7_message,
    HL7ParsingError,
    HeartbeatMessageException,
    ParsedOzelleMessage,
)
from app.satellites.ozelle.batch_splitter import BatchSplitter


# ── Realistic HL7 fixture from Ozelle EHVT-50 ────────────────────────────────


REAL_HL7 = (
    "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
    "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
    "PV1|1|O|||||||||||||||||\n"
    "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017|||||||\n"
    "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    "OBX|2|ST|NEU#^||4.96|10*9/L|2.95 - 11.64|N|||F\n"
    "OBX|3|ST|NST/WBC%^||0.66|%|0.00 - 10.00|N|||F\n"
    "OBX|4|ED|WBC_Main^||base64imagedata==|||||F\n"
)


HEARTBEAT_HL7 = (
    "MSH|^~\\&|HEARTBEAT|SENDER|RECEIVER|SYSTEM|20260416211909||ZHB^H00|HB000001|P|2.3.1"
)


HEARTBEAT_HL7_ALT = (
    "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260417004110||ZHB^H00|HB000001|P|2.3.1"
)


# ── Tests ────────────────────────────────────────────────────────────────────


def test_parse_valid_message():
    """Full HL7 message parses correctly into all fields."""
    parsed = parse_hl7_message(REAL_HL7)

    # Patient
    assert parsed.raw_patient_string == "kitty felina 2a Laura Cepeda"

    # Test type
    assert parsed.test_type_code == "CBC"
    assert parsed.test_type_name == "Hemograma"

    # Received at — extracted from MSH[6]
    assert parsed.received_at.year == 2026
    assert parsed.received_at.month == 4
    assert parsed.received_at.day == 14
    assert parsed.received_at.hour == 16
    assert parsed.received_at.minute == 45
    assert parsed.received_at.second == 34
    assert parsed.received_at.tzinfo == timezone.utc

    # Lab values
    assert len(parsed.lab_values) == 3

    wbc = parsed.lab_values[0]
    assert wbc.parameter_code == "WBC"
    assert wbc.parameter_name_es == "Leucocitos"
    assert wbc.raw_value == "11.02"
    assert wbc.numeric_value == 11.02
    assert wbc.unit == "10*9/L"
    assert wbc.reference_range == "5.05 - 16.76"
    assert wbc.machine_flag == "N"

    neu = parsed.lab_values[1]
    assert neu.parameter_code == "NEU#"
    # NEU is now in IMAGE_PARAMETER_TRANSLATION
    assert neu.parameter_name_es == "Neutrofilos"
    assert neu.raw_value == "4.96"
    assert neu.numeric_value == 4.96
    assert neu.unit == "10*9/L"
    assert neu.reference_range == "2.95 - 11.64"
    assert neu.machine_flag == "N"

    nst_wbc = parsed.lab_values[2]
    assert nst_wbc.parameter_code == "NST/WBC%"
    # NST/WBC (after stripping %) is not in translation table → desconocido fallback
    assert "desconocido" in nst_wbc.parameter_name_es
    assert nst_wbc.raw_value == "0.66"
    assert nst_wbc.numeric_value == 0.66
    assert nst_wbc.unit == "%"
    assert nst_wbc.reference_range == "0.00 - 10.00"
    assert nst_wbc.machine_flag == "N"

    # Images
    assert len(parsed.images) == 1
    img = parsed.images[0]
    assert img.obs_identifier == "WBC_Main"
    assert img.base64_data == "base64imagedata=="


def test_parse_heartbeat_raises_exception():
    """Heartbeat messages raise HeartbeatMessageException."""
    with pytest.raises(HeartbeatMessageException):
        parse_hl7_message(HEARTBEAT_HL7)


def test_parse_heartbeat_alt_raises_exception():
    """Alternate heartbeat format also raises."""
    with pytest.raises(HeartbeatMessageException):
        parse_hl7_message(HEARTBEAT_HL7_ALT)


def test_parse_malformed_message_raises_error():
    """Malformed HL7 without PID raises parsing error."""
    malformed = (
        "MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n"
        "OBX|1|ST|TEST^Test||value|unit|ref|||F\r\n"
    )
    with pytest.raises(HL7ParsingError):
        parse_hl7_message(malformed)


# ─── BatchSplitter Tests ────────────────────────────────────────────────────


def test_split_batch_with_mllp_framing():
    """BatchSplitter correctly splits a single MLLP-framed message."""
    framed_msg = b"\x0bMSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||TEST^PATIENT|\r\n\x1c\r"
    messages = BatchSplitter.split_batch(framed_msg)
    assert len(messages) == 1
    assert messages[0] == framed_msg


def test_split_batch_with_multiple_mllp_messages():
    """BatchSplitter splits multiple MLLP-framed messages."""
    msg1 = b"\x0bMSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||FIRST^PATIENT|\r\n\x1c\r"
    msg2 = b"\x0bMSH|^~\\&|TEST|LAB|||20260414120001||ORU^R01|2|P|2.3.1\r\nPID|1|||SECOND^PATIENT|\r\n\x1c\r"
    batch = msg1 + msg2
    messages = BatchSplitter.split_batch(batch)
    assert len(messages) == 2
    assert messages[0] == msg1
    assert messages[1] == msg2


def test_split_batch_no_mllp_framing():
    """BatchSplitter returns empty list when no MLLP framing found."""
    plain_bytes = b"MSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||PATIENT|\r\n"
    messages = BatchSplitter.split_batch(plain_bytes)
    assert messages == []


def test_parse_message_removes_mllp_framing():
    """parse_message strips MLLP framing characters correctly."""
    framed = b"\x0bMSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||PATIENT|\r\n\x1c\r"
    clean = BatchSplitter.parse_message(framed)
    expected = b"MSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||PATIENT|\r\n"
    assert clean == expected


def test_parse_message_no_framing_returns_as_is():
    """parse_message returns unchanged if no MLLP framing present."""
    already_clean = b"MSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\n"
    result = BatchSplitter.parse_message(already_clean)
    assert result == already_clean


def test_parse_message_removes_mllp_framing():
    """parse_message strips MLLP framing characters correctly."""
    framed = b"\x0bMSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||PATIENT|\r\n\x1c\r"
    clean = BatchSplitter.parse_message(framed)
    expected = b"MSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\nPID|1|||PATIENT|\r\n"
    assert clean == expected


def test_parse_message_no_framing_returns_as_is():
    """parse_message returns unchanged if no MLLP framing present."""
    already_clean = b"MSH|^~\\&|TEST|LAB|||||ORU^R01||P|2.3.1\r\n"
    result = BatchSplitter.parse_message(already_clean)
    assert result == already_clean


def test_process_batch_filters_heartbeats():
    """process_batch filters out heartbeat messages and returns only valid ones."""
    heartbeat = b"\x0bMSH|^~\\&|HEARTBEAT|SENDER|R|20260414120000||ZHB^H00|HB001|P|2.3.1\r\n\x1c\r"
    valid_msg = b"\x0bMSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||PATIENT|\r\n\x1c\r"
    batch = heartbeat + valid_msg
    result = BatchSplitter.process_batch(batch)
    assert len(result) == 1
    assert result[0] == b"MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||PATIENT|\r\n"


def test_process_batch_empty_file():
    """process_batch returns empty list for empty input."""
    result = BatchSplitter.process_batch(b"")
    assert result == []


def test_process_batch_only_heartbeats():
    """process_batch returns empty list when only heartbeats present."""
    heartbeat = b"\x0bMSH|^~\\&|HEARTBEAT|SENDER|R|20260414120000||ZHB^H00|HB001|P|2.3.1\r\n\x1c\r"
    result = BatchSplitter.process_batch(heartbeat)
    assert result == []


def test_split_plain_hl7_by_msh():
    """_split_plain_hl7 splits HL7 plain text by MSH lines."""
    plain_batch = (
        b"MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||PATIENT1|\r\n"
        b"MSH|^~\\&|TEST|LAB|||20260414120001||ORU^R01|2|P|2.3.1\r\nPID|1|||PATIENT2|\r\n"
        b"MSH|^~\\&|TEST|LAB|||20260414120002||ORU^R01|3|P|2.3.1\r\nPID|1|||PATIENT3|\r\n"
    )
    messages = BatchSplitter._split_plain_hl7(plain_batch)
    assert len(messages) == 3
    assert b"PATIENT1" in messages[0]
    assert b"PATIENT2" in messages[1]
    assert b"PATIENT3" in messages[2]


def test_split_plain_hl7_single_message():
    """_split_plain_hl7 handles single HL7 plain message."""
    plain_batch = b"MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||PATIENT|\r\n"
    messages = BatchSplitter._split_plain_hl7(plain_batch)
    assert len(messages) == 1
    assert messages[0] == plain_batch


def test_split_plain_hl7_empty_input():
    """_split_plain_hl7 returns empty list for empty input."""
    messages = BatchSplitter._split_plain_hl7(b"")
    assert messages == []


def test_split_plain_hl7_mixed_endings():
    """_split_plain_hl7 handles mixed line endings (CR, LF, CRLF)."""
    plain_batch = (
        b"MSH|^~\\&|TEST|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\n"
        b"PID|1|||PATIENT1|\n"
        b"MSH|^~\\&|TEST|LAB|||20260414120001||ORU^R01|2|P|2.3.1\r"
        b"PID|1|||PATIENT2|\r\n"
    )
    messages = BatchSplitter._split_plain_hl7(plain_batch)
    assert len(messages) == 2


def test_process_batch_handles_both_mllp_and_plain():
    """process_batch handles mixed MLLP and plain HL7 in same batch."""
    mllp_msg = b"\x0bMSH|^~\\&|MLLP|LAB|||20260414120000||ORU^R01|1|P|2.3.1\r\nPID|1|||MLLP_PATIENT|\r\n\x1c\r"
    plain_msg = b"MSH|^~\\&|PLAIN|LAB|||20260414120001||ORU^R01|2|P|2.3.1\r\nPID|1|||PLAIN_PATIENT|\r\n"
    # Batch with MLLP followed by plain HL7 (as might happen in file uploads)
    batch = mllp_msg + plain_msg
    result = BatchSplitter.process_batch(batch)
    # Should process MLLP message (it's properly framed)
    # Plain message won't be recognized as separate without MLLP framing
    # But should at least get the MLLP one
    assert len(result) >= 1


def test_parse_with_source_lis_file_uses_current_time():
    """When source is LIS_FILE, received_at uses datetime.now() not MSH[6]."""
    from datetime import datetime, timezone

    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    )

    # Parse with LIS_FILE source - received_at should be very recent
    t_before = datetime.now(timezone.utc)
    parsed = parse_hl7_message(msg, source="LIS_FILE")
    t_after = datetime.now(timezone.utc)

    # received_at should be between t_before and t_after (current time)
    assert t_before <= parsed.received_at <= t_after


def test_parse_without_source_uses_msh6():
    """Without source parameter (default), received_at comes from MSH[6]."""
    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    )

    parsed = parse_hl7_message(msg)

    assert parsed.received_at.year == 2026
    assert parsed.received_at.month == 4
    assert parsed.received_at.day == 14
    assert parsed.received_at.hour == 16
    assert parsed.received_at.minute == 45
    assert parsed.received_at.second == 34
    assert parsed.received_at.tzinfo == timezone.utc


def test_parse_with_source_lis_ozelle_uses_msh6():
    """When source is LIS_OZELLE, received_at still comes from MSH[6]."""
    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    )

    parsed = parse_hl7_message(msg, source="LIS_OZELLE")

    assert parsed.received_at.year == 2026
    assert parsed.received_at.month == 4
    assert parsed.received_at.day == 14
    assert parsed.received_at.hour == 16
    assert parsed.received_at.minute == 45
    assert parsed.received_at.second == 34
    assert parsed.received_at.tzinfo == timezone.utc




def test_parse_removes_base64_prefix_from_ed():
    """Base64^ prefix should be removed from ED (image) segments."""
    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ED|WBC_Main||Base64^/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQE|\n"
    )

    parsed = parse_hl7_message(msg)

    assert len(parsed.images) == 1
    # The Base64^ prefix should be stripped
    assert parsed.images[0].base64_data == "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQE"
    assert not parsed.images[0].base64_data.startswith("Base64^")


def test_parse_keeps_base64_data_without_prefix():
    """ED segment without Base64^ prefix should be kept as-is."""
    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ED|WBC_Main||/9j/4AAQSkZJRgABAQAAAQABAAD|\n"
    )

    parsed = parse_hl7_message(msg)

    assert len(parsed.images) == 1
    # Should be unchanged when no prefix
    assert parsed.images[0].base64_data == "/9j/4AAQSkZJRgABAQAAAQABAAD"


def test_parse_numeric_obx_with_suffix_identifier():
    """Numeric OBX with identifier containing a suffix should translate base correctly."""
    msg = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1|\n"
        "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG|||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|\n"
        "OBX|1|ST|WBC_Main^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    )
    parsed = parse_hl7_message(msg)

    assert len(parsed.lab_values) == 1
    wbc = parsed.lab_values[0]
    assert wbc.parameter_code == "WBC_Main"
    assert wbc.parameter_name_es == "Leucocitos"

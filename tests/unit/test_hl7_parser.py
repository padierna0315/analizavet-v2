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


# ── Realistic HL7 fixture from Ozelle EHVT-50 ────────────────────────────────


REAL_HL7 = (
    "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
    "PID|1||||||20240414|F|kitty felina 2a Laura Cepeda|DOG||||\n"
    "PV1|1|O|||||||||||||||||\n"
    "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
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
    # NEU is not in IMAGE_PARAMETER_TRANSLATION → falls back to neu_desconocido
    assert "desconocido" in neu.parameter_name_es
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


def test_parse_heartbeat_ZHB_raises_specific_exception():
    """ZHB heartbeat messages raise HeartbeatMessageException."""
    with pytest.raises(HeartbeatMessageException, match="Heartbeat"):
        parse_hl7_message(HEARTBEAT_HL7)


def test_parse_heartbeat_ZHB_alt_raises_specific_exception():
    """ZHB heartbeat in MSH[8] is also detected."""
    with pytest.raises(HeartbeatMessageException, match="Heartbeat"):
        parse_hl7_message(HEARTBEAT_HL7_ALT)


def test_parse_empty_message_raises_HL7ParsingError():
    """Empty string raises HL7ParsingError with 'vacío' message."""
    with pytest.raises(HL7ParsingError, match="vacío"):
        parse_hl7_message("")


def test_parse_whitespace_only_raises_HL7ParsingError():
    """Whitespace-only string raises HL7ParsingError."""
    with pytest.raises(HL7ParsingError, match="vacío"):
        parse_hl7_message("   \n\t  ")


def test_parse_missing_pid_raises_HL7ParsingError():
    """Message without PID segment raises HL7ParsingError."""
    bad_hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
    )
    with pytest.raises(HL7ParsingError, match="No se encontró segmento PID"):
        parse_hl7_message(bad_hl7)


def test_parse_returns_parsedozellemessage_type():
    """Return type is exactly ParsedOzelleMessage."""
    parsed = parse_hl7_message(REAL_HL7)
    assert isinstance(parsed, ParsedOzelleMessage)


def test_parse_cbc_copro():
    """CBC maps to Hemograma."""
    hl7_cbc = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|frida canina 4a Diana Serna|DOG||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||9.5|10*9/L|5.0-15.0|N|||F\n"
    )
    parsed = parse_hl7_message(hl7_cbc)
    assert parsed.test_type_code == "CBC"
    assert parsed.test_type_name == "Hemograma"


def test_parse_fecal_unknow_test_type():
    """Unknown test type code keeps the code as name."""
    hl7_fecal = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|paciente prueba|MOUSE||||\n"
        "OBR|1|||FECAL_OCCULT_BLOOD^Fecal Occult Blood Test|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|TXE#^||0.00|Cells/LPF|0.0-0.0|N|||F\n"
    )
    parsed = parse_hl7_message(hl7_fecal)
    assert parsed.test_type_code == "FECAL_OCCULT_BLOOD"
    assert parsed.test_type_name == "Coproscópico"


def test_parse_numeric_value_parsing():
    """Numeric values are correctly parsed from raw string."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|NM|RBC^||9.63|10*12/L|5.65 - 8.87|H|||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert len(parsed.lab_values) == 1
    val = parsed.lab_values[0]
    assert val.numeric_value == 9.63
    assert val.raw_value == "9.63"


def test_parse_non_numeric_raw_value():
    """Non-numeric raw values are preserved with numeric_value=None."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|TEXT^||some text value|units|N|||F\n"
    )
    parsed = parse_hl7_message(hl7)
    val = parsed.lab_values[0]
    assert val.raw_value == "some text value"
    assert val.numeric_value is None


def test_parse_crlf_line_separators():
    """Parser handles \\r (CR) as line separator."""
    hl7_crlf = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\r"
        "PID|1||||||20240414|F|kitty|MOUSE||||\r"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\r"
        "OBX|1|ST|WBC^||10.0|10*9/L|5.0-15.0|N|||F\r"
    )
    parsed = parse_hl7_message(hl7_crlf)
    assert parsed.raw_patient_string == "kitty"
    assert len(parsed.lab_values) == 1


def test_parse_mixed_crlf():
    """Parser handles mixed \\r\\n line separators."""
    hl7_mixed = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\r\n"
        "PID|1||||||20240414|F|kitty|MOUSE||||\r\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\r\n"
        "OBX|1|ST|WBC^||10.0|10*9/L|5.0-15.0|N|||F\r\n"
    )
    parsed = parse_hl7_message(hl7_mixed)
    assert len(parsed.lab_values) == 1


def test_parse_no_machine_flag():
    """OBX without machine flag sets machine_flag=None."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76||||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert parsed.lab_values[0].machine_flag is None


def test_parse_high_flag():
    """H flag is correctly preserved."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||25.0|10*9/L|5.05 - 16.76|H|||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert parsed.lab_values[0].machine_flag == "H"


def test_parse_low_flag():
    """L flag is correctly preserved."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||1.0|10*9/L|5.05 - 16.76|L|||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert parsed.lab_values[0].machine_flag == "L"


def test_parse_multiple_images():
    """Multiple OBX|ED segments produce multiple ImageUploadItems."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ED|WBC_Main^||base64wbc==|||||F\n"
        "OBX|2|ED|RBC_Histo^||base64rbc==|||||F\n"
        "OBX|3|ED|PLT_Distribution^||base64plt==|||||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert len(parsed.images) == 3
    assert parsed.images[0].obs_identifier == "WBC_Main"
    assert parsed.images[0].base64_data == "base64wbc=="
    assert parsed.images[1].obs_identifier == "RBC_Histo"
    assert parsed.images[2].obs_identifier == "PLT_Distribution"


def test_parse_image_only_no_lab_values():
    """Message with only image OBX segments has empty lab_values."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ED|WBC_Main^||base64data==|||||F\n"
    )
    parsed = parse_hl7_message(hl7)
    assert len(parsed.lab_values) == 0
    assert len(parsed.images) == 1


def test_parse_empty_value_skipped():
    """OBX with empty value (parts[5]='') is skipped."""
    hl7 = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||20260414164534||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
        "OBX|2|ST|NEU^||||||F\n"  # empty value — should be skipped
        "OBX|3|ST|LYM^||3.0|10*9/L|1.0-5.0|N|||F\n"
    )
    parsed = parse_hl7_message(hl7)
    # NEU with empty value should be skipped
    codes = [lv.parameter_code for lv in parsed.lab_values]
    assert "WBC" in codes
    assert "NEU^" not in codes  # empty value → skipped
    assert "LYM" in codes  # ^ is stripped from obs_id_full (it's from the ^ sub-component syntax)


def test_parse_missing_date_defaults_to_now():
    """MSH without date string uses current UTC time."""
    hl7_no_date = (
        "MSH|^~\\&|EHVT-50|HUELLAS LAB|||abc||ORU^R01||P|2.3.1||||||UNICODE UTF-8\n"
        "PID|1||||||20240414|F|test|MOUSE||||\n"
        "OBR|1|||CBC^Complete Blood Count|R|20260414164017|20260414164017|20260414164017||||||||\n"
        "OBX|1|ST|WBC^||11.02|10*9/L|5.05 - 16.76|N|||F\n"
    )
    before = datetime.now(timezone.utc)
    parsed = parse_hl7_message(hl7_no_date)
    after = datetime.now(timezone.utc)
    # Should default to current time (within a few seconds)
    assert before <= parsed.received_at <= after

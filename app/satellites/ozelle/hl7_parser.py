"""
Ozelle HL7 Parser — Phase 13

Converts raw HL7 strings from the Ozelle EHVT-50 into structured Pydantic models.
Pure logic — no database, no FastAPI.
"""

from datetime import datetime, timezone
from pydantic import BaseModel
import re
from loguru import logger

from app.schemas.taller import RawLabValueInput, ImageUploadItem
from app.core.taller.images import _translate_base_code


# ── Exceptions ────────────────────────────────────────────────────────────────


class HL7ParsingError(Exception):
    """Raised when the HL7 message cannot be parsed or is malformed."""
    pass


class HeartbeatMessageException(Exception):
    """Raised when the message is a ZHB heartbeat, so the server can ignore it silently."""
    pass


# ── Output Model ──────────────────────────────────────────────────────────────


class ParsedOzelleMessage(BaseModel):
    """The fully parsed result of an Ozelle HL7 message."""

    received_at: datetime
    """When the message was received (UTC). Extracted from MSH[6]."""

    raw_patient_string: str
    """Raw patient string from PID[9]: 'kitty felina 2a Laura Cepeda'."""

    test_type_code: str
    """Test type code: 'CBC', 'FECAL_OCCULT_BLOOD', etc."""

    test_type_name: str
    """Human-readable test name: 'Hemograma', 'Coproscópico', etc."""

    lab_values: list[RawLabValueInput]
    """Numeric/string lab results extracted from OBX segments."""

    images: list[ImageUploadItem]
    """Base64 images extracted from OBX|ED segments."""


# ── Test Type Mapping ──────────────────────────────────────────────────────────


_TEST_TYPE_MAP = {
    "CBC": "Hemograma",
    "FECAL_OCCULT_BLOOD": "Coproscópico",
    # Add more as needed
}


# ── Parser ───────────────────────────────────────────────────────────────────


def parse_hl7_message(raw_message: str) -> ParsedOzelleMessage:
    """Parse raw HL7 string from Ozelle into a structured Pydantic model.

    Args:
        raw_message: Raw HL7 message string (may use \\r, \\n, or both as separators).

    Returns:
        ParsedOzelleMessage with all extracted data.

    Raises:
        HL7ParsingError: If the message is empty or missing required segments.
        HeartbeatMessageException: If the message is a ZHB heartbeat.
    """
    if not raw_message or not raw_message.strip():
        raise HL7ParsingError("Mensaje HL7 vacío")

    # Split by \r or \n (handle both)
    lines = re.split(r"[\r\n]+", raw_message.strip())

    received_at = datetime.now(timezone.utc)
    raw_patient_string = ""
    test_type_code = "UNKNOWN"
    test_type_name = "Desconocido"
    lab_values: list[RawLabValueInput] = []
    images: list[ImageUploadItem] = []

    for line in lines:
        if not line.strip():
            continue

        parts = line.split("|")
        segment_type = parts[0]

        # ── MSH: Message Header ──────────────────────────────────────────────
        if segment_type == "MSH":
            if len(parts) > 8:
                segment_8 = parts[8]
                # Check for heartbeat: ZHB^H00 or HEARTBEAT
                if "ZHB" in segment_8 or "HEARTBEAT" in segment_8 or "HEARTBEAT" in parts[2]:
                    raise HeartbeatMessageException(
                        "Mensaje Heartbeat ZHB detectado"
                    )

            # Extract message date from MSH[6] (index 6)
            if len(parts) > 6 and parts[6]:
                date_str = parts[6]
                # Format: YYYYMMDDHHMMSS
                if len(date_str) == 14 and date_str.isdigit():
                    try:
                        received_at = datetime.strptime(date_str, "%Y%m%d%H%M%S").replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        logger.warning(f"No se pudo parsear fecha MSH: {date_str}")

        # ── PID: Patient Identification ────────────────────────────────────
        elif segment_type == "PID":
            # Patient string is in PID[9] (index 9)
            if len(parts) > 9:
                raw_patient_string = parts[9].strip()

        # ── OBR: Observation Request (test type) ────────────────────────────
        elif segment_type == "OBR":
            if len(parts) > 4:
                obr_4 = parts[4].split("^")
                test_type_code = obr_4[0].strip() if obr_4 else parts[4].strip()
                test_type_name = _TEST_TYPE_MAP.get(test_type_code, test_type_code)

        # ── OBX: Observation Result ─────────────────────────────────────────
        elif segment_type == "OBX":
            if len(parts) < 6:
                continue

            value_type = parts[2].strip()
            # obs_id_full includes the ^ subcomponent syntax
            obs_id_full = parts[3].split("^")[0].strip()
            obs_value = parts[5].strip()

            if not obs_value:
                continue

            # ── Numeric or String Result (ST or NM) ────────────────────────
            if value_type in ("ST", "NM"):
                unit = parts[6].strip() if len(parts) > 6 else ""
                ref_range = parts[7].strip() if len(parts) > 7 else ""
                machine_flag = parts[8].strip() if len(parts) > 8 else None

                # Try to parse numeric value
                try:
                    numeric_val: float | None = float(obs_value)
                except ValueError:
                    numeric_val = None

                # Extract base parameter code (strip #, %, etc. for translation)
                base_code = obs_id_full.replace("#", "").replace("%", "")
                parameter_name_es = _translate_base_code(base_code)

                lab_values.append(
                    RawLabValueInput(
                        parameter_code=obs_id_full,
                        parameter_name_es=parameter_name_es,
                        raw_value=obs_value,
                        numeric_value=numeric_val,
                        unit=unit,
                        reference_range=ref_range,
                        machine_flag=machine_flag or None,
                    )
                )

            # ── Image (ED type) ─────────────────────────────────────────────
            elif value_type == "ED":
                images.append(
                    ImageUploadItem(
                        obs_identifier=obs_id_full,
                        base64_data=obs_value,
                    )
                )

    # ── Validation ─────────────────────────────────────────────────────────────
    if not raw_patient_string:
        raise HL7ParsingError(
            "No se encontró segmento PID con datos del paciente"
        )

    return ParsedOzelleMessage(
        received_at=received_at,
        raw_patient_string=raw_patient_string,
        test_type_code=test_type_code,
        test_type_name=test_type_name,
        lab_values=lab_values,
        images=images,
    )

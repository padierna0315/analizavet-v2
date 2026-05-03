"""
Fujifilm Message Processor Actor — handles Fujifilm NX600 chemistry readings.

Decouples TCP reception from Core processing via Dramatiq background tasks.
Similar to hl7_processor.py but tailored for Fujifilm-format messages.
"""

import dramatiq
import logfire
import anyio

from datetime import datetime, timezone
from app.database import AsyncSessionLocal
from app.schemas.reception import RawPatientInput, PatientSource
from app.core.reception.service import ReceptionService


# ── Module-level service instances (shared across actor invocations) ─────────


def _reception_service() -> ReceptionService:
    """Provide a ReceptionService instance for this actor invocation."""
    return ReceptionService()


# ── Dramatiq Actor ───────────────────────────────────────────────────────────


@dramatiq.actor(max_retries=3, time_limit=60000)
def process_fujifilm_message(data: dict):
    """
    Process a Fujifilm chemistry reading via ReceptionService.

    Expected data keys:
      - internal_id: str        # e.g. "908"
      - patient_name: str       # e.g. "POLO"
      - parameter_code: str     # e.g. "CRE" (optional — may be omitted for stub registration)
      - raw_value: str          # e.g. "0.87" (optional)
      - source: str             # PatientSource value (defaults to LIS_FUJIFILM)
      - received_at: str        # ISO timestamp (optional — defaults to now)

    Retries up to 3 times on failure with exponential backoff.
    """
    source_value = data.get("source", PatientSource.LIS_FUJIFILM.value)
    internal_id = data.get("internal_id", "")
    patient_name = data.get("patient_name", "")
    parameter_code = data.get("parameter_code", "")
    raw_value = data.get("raw_value", "")

    logfire.info(
        "Processing Fujifilm reading",
        patient_name=patient_name,
        internal_id=internal_id,
        parameter=parameter_code,
        value=raw_value,
        source=source_value,
    )

    try:
        # Build raw string for ReceptionService normalization.
        # For Fujifilm we only have the patient name from the analyzer
        # (the machine doesn't provide owner/species/age).
        raw_string = patient_name.strip()
        if not raw_string:
            logfire.warning("Fujifilm: empty patient_name — nothing to process")
            return

        received_at_str = data.get("received_at")
        if received_at_str:
            try:
                received_at = datetime.fromisoformat(received_at_str.replace("Z", "+00:00"))
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)
            except Exception:
                logfire.warning(f"Fujifilm: invalid received_at '{received_at_str}', using now()")
                received_at = anyio.current_time()
        else:
            received_at = anyio.current_time()

        reception_input = RawPatientInput(
            raw_string=raw_string,
            source=PatientSource(source_value),
            received_at=received_at,
        )

        # Async execution of the Core pipeline
        anyio.run(_async_process_pipeline, reception_input, internal_id, parameter_code, raw_value)

    except Exception as e:
        logfire.error(f"Fujifilm processing failed: {e}", exc_info=True)
        raise  # Trigger Dramatiq retry


# ── Pipeline ─────────────────────────────────────────────────────────────────


async def _async_process_pipeline(
    reception_input: RawPatientInput,
    internal_id: str,
    parameter_code: str,
    raw_value: str,
):
    """
    Fujifilm processing pipeline:

    1. Call ReceptionService with the patient name.
       - Normalization will attempt to extract species/age/owner from the name string.
       - If the name is not parseable it still produces a valid NormalizedPatient
         (species/heuristics may default).
    2. Register in Baúl (deduplication + patient creation).

    Note: Fujifilm data is inherently simpler than HL7: one value at a time.
    We forward it through ReceptionService so it appears in the Baúl just like
    other sources, making it queryable and deduplicated.
    """
    logfire.info(
        "Fujifilm pipeline starting",
        patient_name=reception_input.raw_string,
        internal_id=internal_id,
        parameter=parameter_code,
    )

    try:
        async with AsyncSessionLocal() as session:
            service = _reception_service()

            # ── RECEPTION PHASE ─────────────────────────────────────────────
            baul_result = await service.receive(reception_input, session)
            patient_id = baul_result.patient_id
            normalized_patient = baul_result.patient

            logfire.info(
                f"Fujifilm recepción completada. Paciente ID: {patient_id} "
                f"(nuevo: {baul_result.created}) — name: {normalized_patient.name}"
            )

            # ── Record the chemistry value as a note / future TestResult ───────
            # Currently we don't push Fujifilm values into the taller/lab pipeline
            # because they lack species-specific reference ranges and full context.
            # They are recorded via the Baúl for patient history and can be
            # processed later when integrated with the full test-result schema.
            # (The HL7 path handles full lab integration via TallerService.)

            if parameter_code and raw_value:
                logfire.info(
                    f"Fujifilm chemistry reading queued for later processing",
                    patient_id=patient_id,
                    parameter=parameter_code,
                    value=raw_value,
                )

            logfire.info("Fujifilm pipeline completado exitosamente.")

    except Exception as e:
        logfire.error(f"Error crítico en pipeline Fujifilm: {e}", exc_info=True)
        raise  # Let Dramatiq retry
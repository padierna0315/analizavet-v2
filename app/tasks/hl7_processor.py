"""
HL7 Message Processor Actor — Phase 15/16

Dramatiq actor que procesa mensajes HL7 del Ozelle en background.
Decouple la recepción TCP del procesamiento pesado del Core.
"""

import dramatiq
from loguru import logger
import anyio

from app.database import AsyncSessionLocal
from app.schemas.reception import RawPatientInput, PatientSource
from app.schemas.taller import EnrichRequest, ImageUploadRequest
from app.satellites.ozelle.hl7_parser import parse_hl7_message, HL7ParsingError, HeartbeatMessageException, ParsedOzelleMessage
from app.core.reception.service import ReceptionService
from app.core.taller.service import TallerService
from app.satellites.ozelle.batch_splitter import BatchSplitter


# ── Module-level service instances (shared across actor invocations) ────────────


def _reception_service() -> ReceptionService:
    return ReceptionService()


def _taller_service() -> TallerService:
    return TallerService()


# ── Dramatiq Actor ─────────────────────────────────────────────────────────────


@dramatiq.actor(max_retries=3, time_limit=60000)
def process_hl7_message(raw_hl7: str, source: str):
    """
    Dramatiq actor to process an incoming HL7 message.
    Retries up to 3 times on failure with exponential backoff.
    """
    logger.info(f"Procesando mensaje HL7 en background (fuente: {source})")
    try:
        parsed = parse_hl7_message(raw_hl7)
        logger.info(
            f"Mensaje parseado correctamente: {parsed.test_type_name} "
            f"para '{parsed.raw_patient_string}'"
        )

        # Async execution wrapper
        anyio.run(_async_process_pipeline, parsed, source)

    except (HL7ParsingError, HeartbeatMessageException) as e:
        # Fatal errors: malformed message or heartbeat. Neither should retry.
        logger.error(f"Error fatal procesando HL7. Se descarta. {e}")
        # Not raising so it doesn't trigger Dramatiq retry
    except Exception as e:
        logger.error(f"Error procesando mensaje. Se reintentará. Error: {e}")
        raise  # Raise to trigger Dramatiq retry


# ── Pipeline ───────────────────────────────────────────────────────────────────


async def _async_process_pipeline(parsed_msg: ParsedOzelleMessage, source: str):
    """
    The actual async pipeline that connects the Satellite to the Core.

    1. Send raw patient string to Reception (normalize + deduplicate → Baúl)
    2. Send lab values to Taller (Enrichment: create TestResult + flag values)
    3. Send images to Taller (Image Storage)
    """
    logger.info(f"Iniciando pipeline para paciente: '{parsed_msg.raw_patient_string}'")

    source_enum = PatientSource(source)

    # 1. Prepare Reception Input
    reception_input = RawPatientInput(
        raw_string=parsed_msg.raw_patient_string,
        source=source_enum,
        received_at=parsed_msg.received_at,
    )

    async with AsyncSessionLocal() as session:
        try:
            # ── RECEPTION PHASE ──────────────────────────────────────────────
            logger.debug("Llamando a ReceptionService...")
            baul_result = await _reception_service().receive(reception_input, session)
            patient_id = baul_result.patient_id
            normalized_patient = baul_result.patient

            logger.info(
                f"Recepción completada. Paciente ID: {patient_id} "
                f"(Nuevo: {baul_result.created})"
            )

            # ── TALLER PHASE — Enrichment ────────────────────────────────────
            logger.debug("Llamando a TallerService (Enrichment)...")

            # Create TestResult
            tr = await _taller_service().create_test_result(
                patient_id=patient_id,
                test_type=parsed_msg.test_type_name,
                test_type_code=parsed_msg.test_type_code,
                source=source,
                received_at=parsed_msg.received_at,
                session=session,
            )

            # Flag + store lab values
            flag_result = await _taller_service().flag_and_store(
                test_result_id=tr.id,
                species=normalized_patient.species,
                values=parsed_msg.lab_values,
                session=session,
            )

            logger.info(
                f"Taller Enrichment completado. TestResult ID: {tr.id}. "
                f"Resumen: {flag_result.summary}"
            )

            # ── TALLER PHASE — Images ─────────────────────────────────────────
            if parsed_msg.images:
                logger.debug(f"Procesando {len(parsed_msg.images)} imágenes...")
                image_req = ImageUploadRequest(
                    test_result_id=tr.id,
                    patient_name=normalized_patient.name,
                    owner_name=normalized_patient.owner_name,
                    received_at=parsed_msg.received_at,
                    images=parsed_msg.images,
                )

                img_result = await _taller_service().save_images(image_req, session)
                logger.info(
                    f"Imágenes guardadas: {img_result.total_saved} "
                    f"(Fallaron: {img_result.total_failed})"
                )
            else:
                logger.info("El mensaje no contiene imágenes.")

            logger.info("Pipeline completado exitosamente.")

        except Exception as e:
            logger.error(f"Error crítico en pipeline asíncrono: {e}")
            # Re-raise so the Dramatiq actor knows it failed and can retry
            raise


# ── Batch Processing Actor ─────────────────────────────────────────────────────


@dramatiq.actor(max_retries=3, time_limit=120000)
def process_uploaded_batch(file_content: str):
    """
    Dramatiq actor to process an uploaded HL7 batch file.
    This actor handles the complete batch processing pipeline:
    1. Split the batch file into individual messages
    2. Filter out heartbeat messages
    3. Process each valid message through the existing pipeline
    """
    logger.info("Procesando archivo HL7 batch en background")
    try:
        # Convert string back to bytes for processing
        file_bytes = file_content.encode('utf-8')
        # Split the batch file into individual messages
        valid_messages = BatchSplitter.process_batch(file_bytes)
        logger.info(f"Archivo dividido en {len(valid_messages)} mensajes válidos")
        
        # Process each message
        for i, message in enumerate(valid_messages):
            try:
                # Decode message to string for processing
                message_str = message.decode('utf-8', errors='ignore')
                logger.info(f"Procesando mensaje {i+1} de {len(valid_messages)}")
                
                # Process the message using the existing actor
                process_hl7_message.send(message_str, "OZELLE")
            except Exception as e:
                logger.error(f"Error procesando mensaje {i+1}: {e}")
                # Continue with the next message even if one fails
                continue
                
        logger.info("Procesamiento de archivo HL7 batch completado")
    except Exception as e:
        logger.error(f"Error fatal procesando archivo HL7 batch: {e}")
        raise  # Raise to trigger Dramatiq retry

"""Provenance capture Dramatiq actors — fire-and-forget, no retry.

Each actor captures raw data from a different external source BEFORE parsing happens.
These actors must never block the main processing flow — failures are logged and swallowed.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import anyio
import dramatiq
import logfire

from app.database import AsyncSessionLocal
from app.services.provenance_recorder import ProvenanceRecorder
from app.shared.models.raw_data_log import RawDataSource

logger = logging.getLogger(__name__)


# ── Ozelle ──────────────────────────────────────────────────────────────────────


@dramatiq.actor(max_retries=0)
def record_ozelle_raw(raw_hl7: str, received_at_iso: Optional[str] = None) -> None:
    """Fire-and-forget capture of raw Ozelle HL7 message.

    Called from the MLLP server BEFORE parse_hl7_message(). Must never block
    or raise — if capture fails, the main flow continues unaffected.
    """
    try:
        anyio.run(_record_ozelle_async, raw_hl7, received_at_iso)
    except Exception:
        logfire.exception("record_ozelle_raw: anyio.run failed")


async def _record_ozelle_async(raw_hl7: str, received_at_iso: Optional[str]) -> None:
    """Internal async helper for record_ozelle_raw."""
    try:
        received_at = (
            datetime.fromisoformat(received_at_iso)
            if received_at_iso
            else datetime.now(timezone.utc)
        )

        async with AsyncSessionLocal() as session:
            await ProvenanceRecorder.record_async(
                session=session,
                source=RawDataSource.OZELLE,
                raw_data=raw_hl7,
                received_at=received_at,
            )
    except Exception:
        logger.exception("record_ozelle_raw: capture failed")
        logfire.exception("record_ozelle_raw: capture failed")


# ── Fujifilm ────────────────────────────────────────────────────────────────────


@dramatiq.actor(max_retries=0)
def record_fujifilm_raw(raw_message: str, received_at_iso: Optional[str] = None) -> None:
    """Fire-and-forget capture of raw Fujifilm TCP message.

    Called from the Fujifilm adapter BEFORE parse_fujifilm_message(). Must never
    block or raise — if capture fails, the main flow continues unaffected.
    """
    try:
        anyio.run(_record_fujifilm_async, raw_message, received_at_iso)
    except Exception:
        logfire.exception("record_fujifilm_raw: anyio.run failed")


async def _record_fujifilm_async(raw_message: str, received_at_iso: Optional[str]) -> None:
    """Internal async helper for record_fujifilm_raw."""
    try:
        received_at = (
            datetime.fromisoformat(received_at_iso)
            if received_at_iso
            else datetime.now(timezone.utc)
        )

        async with AsyncSessionLocal() as session:
            await ProvenanceRecorder.record_async(
                session=session,
                source=RawDataSource.FUJIFILM,
                raw_data=raw_message,
                received_at=received_at,
            )
    except Exception:
        logger.exception("record_fujifilm_raw: capture failed")
        logfire.exception("record_fujifilm_raw: capture failed")
